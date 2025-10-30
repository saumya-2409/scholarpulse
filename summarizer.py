"""
summarizer.py

Full-paper summarizer using Google Gemini API (free tier):
- downloads PDF when available (open-access only),
- extracts text (PyPDF2),
- chunks text, summarizes each chunk via Gemini,
- composes a final structured summary (JSON) using Gemini,
- On API failure: Logs error visibly (no retries to save calls) and returns explicit message.

Important:
- Requires `google-generativeai` package + GEMINI_API_KEY in secrets.
- Starts with 'gemini-1.5-pro' (your test model), falls back to stable ones.
- Debugging: All logs prefixed for Streamlit Logs visibility.
"""

import os
import io
import json
import time
import tempfile
import requests
import re
import random
from typing import Dict, Any, Optional, List, Tuple
import streamlit as st

# Text extraction
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
    print("[Debug] PyPDF2 available for PDF extraction")
except ImportError:
    PYPDF2_AVAILABLE = False
    print("[Debug] PyPDF2 not available - PDF extraction disabled")

# JSON schema validation
try:
    from jsonschema import validate, ValidationError
    JSONSCHEMA_AVAILABLE = True
    print("[Debug] JSONSchema available for validation")
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    print("[Debug] JSONSchema not available - Skipping validation")

# Google Gemini client
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    print("[Debug] google-generativeai package loaded successfully")
except ImportError:
    GEMINI_AVAILABLE = False
    print("[Debug] google-generativeai package missing - Install via requirements.txt")

DEFAULT_MODEL = "gemini-1.5-pro"  # Your tested model
FALLBACK_MODELS = ["gemini-1.5-pro", "gemini-pro"]  # Stable alternatives
CHUNK_CHAR_SIZE = 3000
CHUNK_OVERLAP = 200

# Schema (unchanged)
SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "abstract": {"type": "string"},
        "authors": {"type": "array", "items": {"type": "string"}},
        "year": {"anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}]},
        "domain": {"type": "string"},
        "source": {"type": "string"},
        "url": {"type": "string"},
        "problem_statement": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "motivation": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "approach": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "experiments_and_evaluation": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "results_and_key_findings": {"type": "array", "items": {"type": "string"}},
        "limitations_and_future_work": {"type": "array", "items": {"type": "string"}},
        "reusability_practical_value": {"anyOf": [{"type": "string"}, {"type": "null"}]}
    },
    "required": ["title", "abstract", "authors", "source", "url", "results_and_key_findings", "limitations_and_future_work"]
}

class FullPaperSummarizer:
    def __init__(self, model: str = DEFAULT_MODEL, chunk_size: int = 3000, max_chunks: int = 5, overlap: int = 200, api_key: str = None):
        self.chunk_size = chunk_size
        self.max_chunks = max_chunks
        self.overlap = overlap
        self.request_delay = 1
        self.current_model = model  # Track current model

        if self.overlap >= self.chunk_size:
            self.overlap = int(self.chunk_size * 0.1)
            print(f"[Debug] Adjusted overlap to {self.overlap}")

        self.summary_schema = SUMMARY_SCHEMA

        # PDF flag
        self.pdf_enabled = PYPDF2_AVAILABLE

        # Gemini setup with fallback (no retries)
        self.gemini_model = None
        self.gemini_enabled = False
        
        api_key = api_key or st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        print(f"[Debug] API key loaded: {'Yes' if api_key else 'No (check secrets/env)'}")
        print(f"[Debug] GEMINI_AVAILABLE: {GEMINI_AVAILABLE}")
        
        if api_key and GEMINI_AVAILABLE:
            try:
                genai.configure(api_key=api_key)
                # List all available models (debug visible in logs)
                available = []
                print("[Gemini Debug] Listing available models for generateContent:")
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        available.append(m.name)
                        print(f"  - {m.name} ({m.display_name})")
                
                if not available:
                    raise Exception("No models available - Enable Generative Language API in Cloud Console")
                
                # Try models one-by-one (no retries, just log failures)
                models_to_try = [self.current_model] + FALLBACK_MODELS + available[:1]  # Default + fallbacks + first available
                self.gemini_enabled = False
                for attempt_model in models_to_try:
                    print(f"[Gemini Debug] Trying model (one shot): {attempt_model}")
                    try:
                        self.gemini_model = genai.GenerativeModel(attempt_model)
                        # Quick test call (only one API call)
                        time.sleep(self.request_delay)
                        test_response = self.gemini_model.generate_content("Test")
                        if test_response and test_response.text and test_response.text.strip():
                            self.current_model = attempt_model
                            self.gemini_enabled = True
                            print(f"[Summarizer] Success: Gemini enabled with {self.current_model} (test: '{test_response.text[:50]}...')")
                            break
                        else:
                            raise Exception("Empty test response")
                    except Exception as model_e:
                        error_detail = str(model_e)[:100]
                        print(f"[Gemini Debug] Model '{attempt_model}' failed: {error_detail}")
                        if "404" in error_detail:
                            print("[Gemini Debug] 404 tip: Model not available for your key/region - Continuing to fallback")
                        continue
                
                if not self.gemini_enabled:
                    print("[Summarizer] All models failed - Check logs above. Summaries will return error messages")
                    
            except Exception as e:
                print(f"[Summarizer Init Error] {str(e)[:200]}")
                self.gemini_enabled = False
        else:
            print("[Summarizer] Setup failed: No key or package - All summaries will fail with message")

        self.schema_loaded = True

    def _infer_domain(self, abstract: str, query: str) -> str:
        if not abstract:
            return "General Research"
        text = (abstract.lower() + " " + (query or "").lower())
        domains = {
            "ai/ml/finance": ["machine learning", "neural network", "prediction", "stock", "financial", "forecasting"],
            "ai/ml/nlp": ["natural language", "processing", "nlp", "text analysis", "sentiment"],
            "computer vision": ["image", "vision", "object detection"],
            "data science": ["data science", "big data", "analytics"],
            "cybersecurity": ["security", "cyber", "encryption"],
            "robotics": ["robot", "autonomous"]
        }
        for domain, keywords in domains.items():
            if any(kw in text for kw in keywords):
                return domain
        if "stock" in text or "finance" in text:
            return "Finance/ML"
        return "AI/ML"

    def summarize_paper(self, paper: Dict[str, Any], use_full_text: bool = True, timeout: int = 120, query: str = "") -> Dict[str, Any]:
        print(f"[Debug] Starting summary for paper: {paper.get('title', 'Untitled')[:50]}...")
        meta = self._prepare_meta(paper)
        if not meta:
            return {"summary": "Failed: Invalid paper metadata"}

        extracted_text = None
        is_paywalled = False
        if use_full_text and self.pdf_enabled and paper.get('pdf_url'):
            print("[Debug] Attempting PDF extraction...")
            extracted_text, is_paywalled = self._download_and_extract_pdf(paper['pdf_url'])
            if is_paywalled:
                print(f"[Debug] PDF paywalled for: {paper.get('title')[:50]}")
                extracted_text = None
            elif extracted_text:
                print(f"[Debug] PDF extracted: {len(extracted_text)} chars")

        # Try PDF summary
        if extracted_text:
            chunks = self._chunk_text(extracted_text)[:self.max_chunks]
            print(f"[Debug] Generated {len(chunks)} chunks for PDF summary")
            chunk_summaries = self._chunk_and_summarize(chunks, meta, query=query)
            if chunk_summaries:
                final_summary = self._compose_final_summary_from_chunks(meta, chunk_summaries, query=query)
                if final_summary:
                    print(f"[Debug] PDF summary success: Keys {list(final_summary.keys())}")
                    return final_summary

        # Try abstract summary
        print("[Debug] Falling back to abstract summary...")
        if self.gemini_enabled:
            abstract_summary = self._summarize_abstract(meta, query=query)
            if abstract_summary:
                print(f"[Debug] Abstract summary success: Keys {list(abstract_summary.keys())}")
                return abstract_summary
            else:
                return {"summary": "Gemini API failed during abstract summary - Check logs for details"}
        else:
            return {"summary": "Gemini not enabled (init failed) - See logs: No key/package or model unavailable"}

        # Explicit fail
        return {"summary": "Summary couldn't be generated - API unavailable"}

    def _gemini_call(self, prompt: str) -> str:
        """Single API call (no retry). Logs error, returns empty on fail."""
        print(f"[Debug] Making Gemini call with model '{self.current_model}': Prompt length {len(prompt)} chars")
        if not self.gemini_enabled or not self.gemini_model:
            print("[API Call Failed] Gemini not enabled - Skipping call")
            return ""
        
        time.sleep(self.request_delay)  # Rate limit safety (no retry)
        try:
            response = self.gemini_model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 800
                }
            )
            if response and response.text and response.text.strip():
                result = response.text.strip()
                print(f"[Debug] Gemini call success: Response length {len(result)} chars")
                return result
            else:
                raise Exception("Empty or invalid response from Gemini")
        except Exception as e:
            error_msg = str(e)[:150]  # Truncate for logs
            print(f"[API Call Failed] {error_msg}")
            if "404" in error_msg.lower():
                print("[API Call Failed] 404: Model '{self.current_model}' unavailable - Try fallback in init")
            elif "429" in error_msg or "quota" in error_msg.lower():
                print("[API Call Failed] Quota/rate limit - Wait and retry manually")
            elif "401" in error_msg or "auth" in error_msg.lower():
                print("[API Call Failed] Auth issue - Check GEMINI_API_KEY in secrets")
            return ""  # Return empty to trigger failure message

    def _chunk_and_summarize(self, chunks: List[str], meta: Dict[str, Any], query: str = "") -> List[str]:
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            if len(chunk_summaries) >= self.max_chunks:
                print(f"[Debug] Capped chunks at {self.max_chunks}")
                break
            print(f"[Debug] Summarizing chunk {i+1}/{len(chunks)}: {len(chunk)} chars")
            try:
                prompt = (
                    f"Paper: {meta.get('title', 'Untitled')}\n"
                    f"Query: {query or 'general research'}\n\n"
                    f"Summarize this chunk in 4-6 detailed sentences, extracting key methods, results, and relevance to the query. "
                    f"Use specific details/numbers from the text:\n\n{chunk[:2000]}"
                )
                summary = self._gemini_call(prompt)
                if summary:
                    chunk_summaries.append(summary)
                    print(f"[Debug] Chunk {i+1} success: {len(summary)} chars")
                else:
                    print(f"[Debug] Chunk {i+1} failed - Skipping")
                    chunk_summaries.append("Chunk summary unavailable due to API error")
            except Exception as e:
                print(f"[Chunk {i+1} Error] {str(e)[:100]}")
                chunk_summaries.append("Chunk error due to API failure")
        return chunk_summaries

    def _prepare_meta(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        meta = {
            "title": (paper.get("title") or "").strip(),
            "abstract": (paper.get("abstract") or "").strip(),
            "authors": paper.get("authors") or [],
            "year": paper.get("year"),
            "domain": paper.get("domain") or "",
            "source": paper.get("source") or "",
            "url": paper.get("url") or "",
            "full_text": paper.get("full_text")
        }
        print(f"[Debug] Prepared meta: Title '{meta['title'][:50]}...', Abstract length {len(meta['abstract'])}")
        return meta

    def _download_and_extract_pdf(self, pdf_url: str) -> Tuple[Optional[str], bool]:
        print(f"[Debug] Downloading PDF: {pdf_url[:100]}...")
        try:
            headers = {"User-Agent": "research-assistant/1.0"}
            resp = requests.get(pdf_url, headers=headers, timeout=30, stream=True)
            if resp.status_code in (401, 403):
                print("[Debug] PDF access denied (paywalled/auth)")
                return None, True
            if resp.status_code != 200:
                print(f"[Debug] PDF download failed: Status {resp.status_code}")
                return None, True
            content_type = resp.headers.get("Content-Type", "").lower()
            content = resp.content
            if "html" in content_type or content.strip().startswith(b"<"):
                print("[Debug] PDF URL returned HTML (paywalled/redirect)")
                return None, True
            if "pdf" not in content_type and not content.startswith(b"%PDF"):
                print("[Debug] Content not PDF")
                return None, True
            if not PYPDF2_AVAILABLE:
                print("[Debug] PyPDF2 missing - Can't extract")
                return None, False
            try:
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                    f.write(content)
                    tmp_name = f.name
                extracted_text = ""
                with open(tmp_name, "rb") as fh:
                    reader = PyPDF2.PdfReader(fh)
                    for page_num, page in enumerate(reader.pages, 1):
                        try:
                            txt = page.extract_text() or ""
                            if txt.strip():
                                extracted_text += txt + "\n\n"
                        except Exception as page_e:
                            print(f"[Debug] Page {page_num} extract error: {str(page_e)[:50]}")
                try:
                    os.unlink(tmp_name)
                except:
                    pass
                result = extracted_text.strip() if extracted_text.strip() else None
                print(f"[Debug] PDF extraction: {len(extracted_text)} chars total")
                return result, False
            except Exception as e:
                print(f"[PDF Parse Error] {str(e)[:100]}")
                return None, True
        except Exception as e:
            print(f"[PDF Download Error] {str(e)[:100]}")
            return None, True

    def _chunk_text(self, text: str) -> List[str]:
        if not text:
            print("[Debug] No text to chunk")
            return []
        text = text.strip()
        chunks = []
        start = 0
        L = len(text)
        while start < L:
            end = min(L, start + self.chunk_size)
            chunks.append(text[start:end])
            step = max(1, self.chunk_size - self.overlap)
            start += step
            if len(chunks) >= self.max_chunks:
                break
        print(f"[Debug] Chunking: {len(chunks)} chunks created (cap {self.max_chunks})")
        return chunks

    def _compose_final_summary_from_chunks(self, meta: Dict[str, Any], chunk_summaries: List[str], query: str = "") -> Optional[Dict[str, Any]]:
        print(f"[Debug] Composing final summary from {len(chunk_summaries)} chunk summaries")
        aggregated = "\n\n---\n\n".join(chunk_summaries)
        if not aggregated:
            print("[Debug] No chunks to aggregate")
            return None
        
        prompt = (
            f"QUERY CONTEXT: Relate summary to '{query or 'general research'}'.\n\n"
            f"PAPER METADATA:\n"
            f"Title: {meta.get('title', 'Untitled')}\n"
            f"Authors: {', '.join(meta.get('authors', []))}\n"
            f"Year: {meta.get('year', 'N/A')}\n"
            f"Source: {meta.get('source', 'Unknown')}\n"
            f"URL: {meta.get('url', '')}\n"
            f"Abstract: {meta.get('abstract', '')}\n\n"
            f"CHUNK SUMMARIES (extract facts from these):\n{aggregated[:5000]}\n\n"
            "Output ONLY valid JSON with these keys (no extra text, no markdown code blocks):\n"
            "{\n"
            '  "title": "string (from metadata)",\n'
            '  "abstract": "string (from metadata)",\n'
            '  "authors": ["array of strings"],\n'
            '  "year": null or integer,\n'
            '  "domain": "string like AI/ML/Finance",\n'
            '  "source": "string (from metadata)",\n'
            '  "url": "string (from metadata)",\n'
            '  "problem_statement": "string or null (2-3 sentences on problem from chunks)",\n'
            '  "motivation": "string or null (why important, query-tied)",\n'
            '  "approach": "string or null (methods/techniques from chunks, 2-4 sentences)",\n'
            '  "experiments_and_evaluation": "string or null (datasets/metrics from chunks)",\n'
            '  "results_and_key_findings": ["array of 3-5 unique findings with metrics, e.g. 92 percent accuracy for stock prediction"],\n'
            '  "limitations_and_future_work": ["array of 2-4 limitations/gaps from chunks"],\n'
            '  "reusability_practical_value": "string or null (1-2 sentences on applications for query domain)"\n'
            "}\n"
            "Use real details from chunks. Set to null/empty array if absent."
        )
        
        try:
            json_str = self._gemini_call(prompt)
            if not json_str:
                print("[Debug] Composition call failed - Returning empty")
                return None
            # Clean potential code block markers
            json_str = json_str.replace("``````", "").strip()
            print(f"[Debug] Raw JSON response length: {len(json_str)}")
            
            final_summary = json.loads(json_str)
            if JSONSCHEMA_AVAILABLE:
                try:
                    validate(instance=final_summary, schema=self.summary_schema)
                    print("[Debug] JSON validated successfully")
                except ValidationError as e:
                    print(f"[Debug] JSON validation warning: {str(e)[:100]}")
            return final_summary
        except json.JSONDecodeError as e:
            print(f"[JSON Parse Error] {str(e)[:100]}\nSample response: {json_str[:200]}")
            return None
        except Exception as e:
            print(f"[Composition Error] {str(e)[:100]}")
            return None

    def _summarize_abstract(self, meta: Dict[str, Any], query: str = "") -> Optional[Dict[str, Any]]:
        abstract = meta.get('abstract', '')
        print(f"[Debug] Abstract summary: Length {len(abstract)} chars")
        if not abstract or not self.gemini_enabled:
            print("[Debug] No abstract or Gemini disabled - Skipping")
            return None
        
        prompt = (
            f"QUERY: Relate to '{query or 'general research'}'.\n\n"
            f"PAPER:\n"
            f"Title: {meta.get('title')}\n"
            f"Authors: {', '.join(meta.get('authors', []))}\n"
            f"Year: {meta.get('year')}\n"
            f"Abstract: {abstract[:2500]}\n\n"
            "Summarize in JSON (same schema as before). Extract problem, approach, results from abstract. "
            "Output ONLY valid JSON (no markdown code blocks, no extra text):\n"
            "{\n"
            '  "title": "...",\n'
            '  "abstract": "...",\n'
            '  "authors": [...],\n'
            '  "year": null or integer,\n'
            '  "domain": "...",\n'
            '  "source": "...",\n'
            '  "url": "...",\n'
            '  "problem_statement": "..." or null,\n'
            '  "motivation": "..." or null,\n'
            '  "approach": "..." or null,\n'
            '  "experiments_and_evaluation": "..." or null,\n'
            '  "results_and_key_findings": [...],\n'
            '  "limitations_and_future_work": [...],\n'
            '  "reusability_practical_value": "..." or null\n'
            "}"
        )
        
        try:
            json_str = self._gemini_call(prompt)
            if not json_str:
                print("[Debug] Abstract call failed")
                return None
            # Clean potential code block markers
            json_str = json_str.replace("``````", "").strip()
            
            summary = json.loads(json_str)
            print(f"[Debug] Abstract summary parsed: Keys {list(summary.keys())}")
            return summary
        except Exception as e:
            print(f"[Abstract Summary Error] {str(e)[:100]}")
            return None

    def _validate_parsed(self, parsed: Dict[str, Any]) -> bool:
        if not isinstance(parsed, dict):
            print("[Debug] Validation: Not a dict")
            return False
        required = ["title", "abstract", "authors", "source", "url", "results_and_key_findings", "limitations_and_future_work"]
        for k in required:
            if k not in parsed:
                print(f"[Debug] Validation: Missing required key {k}")
                return False
        if not isinstance(parsed.get("authors"), list):
            print("[Debug] Validation: Authors not list")
            return False
        if not isinstance(parsed.get("results_and_key_findings"), list):
            print("[Debug] Validation: Results not list")
            return False
        if not isinstance(parsed.get("limitations_and_future_work"), list):
            print("[Debug] Validation: Limitations not list")
            return False
        if JSONSCHEMA_AVAILABLE:
            try:
                validate(instance=parsed, schema=SUMMARY_SCHEMA)
                print("[Debug] Full schema validation passed")
            except Exception as e:
                print(f"[Debug] Schema validation failed: {str(e)[:100]}")
                return False
        return True

    def conservative_summary(self, meta: Dict[str, Any], query: str = "") -> Dict[str, Any]:
        """Not used - Explicit fail only."""
        return {"summary": "Summary couldn't be generated - API unavailable"}
