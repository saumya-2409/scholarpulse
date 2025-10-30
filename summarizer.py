"""
summarizer.py

Full-paper summarizer using Google Gemini API (free tier):
- downloads PDF when available (open-access only),
- extracts text (PyPDF2),
- chunks text, summarizes each chunk via Gemini,
- composes a final structured summary (JSON) using Gemini,
- falls back to "Summary couldn't be generated" if API unavailable (no conservative).

Important:
- Requires `google-generativeai` package + GEMINI_API_KEY in secrets.
- Free tier: 15 RPM, 1M tokens/day, 1500 RPD (plenty for research).
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
except ImportError:
    PYPDF2_AVAILABLE = False

# JSON schema validation
try:
    from jsonschema import validate, ValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False

# Google Gemini client
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

DEFAULT_MODEL = "gemini-1.5-flash"  # Free model
CHUNK_CHAR_SIZE = 3000
CHUNK_OVERLAP = 200

def retry_with_backoff(func, initial_delay: float = 1, max_delay: float = 60, max_retries: int = 6):
    """Exponential backoff for API rate limits."""
    def wrapper(*args, **kwargs):
        num_retries = 0
        delay = initial_delay
        while True:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_str = str(e).lower()
                # Check for rate limit errors (429 or quota exceeded)
                if "429" in error_str or "quota" in error_str or "rate" in error_str:
                    num_retries += 1
                    if num_retries > max_retries:
                        raise Exception(f"Max retries ({max_retries}) exceeded: {e}")
                    delay = min(delay * 2 * (1 + random.random()), max_delay)
                    print(f"[Rate Limit] Retrying in {delay:.1f}s (attempt {num_retries}/{max_retries})")
                    time.sleep(delay)
                else:
                    raise e
    return wrapper

# Schema
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
    def __init__(self, model: str = "gemini-1.5-flash", chunk_size: int = 3000, max_chunks: int = 5, overlap: int = 200, api_key: str = None):
        self.model = model
        self.chunk_size = chunk_size
        self.max_chunks = max_chunks
        self.overlap = overlap
        self.request_delay = 1  # 1s for free tier (15 RPM = 4s/req, but we're safe)

        if self.overlap >= self.chunk_size:
            self.overlap = int(self.chunk_size * 0.1)
            print(f"[Summarizer] Adjusted overlap to {self.overlap}")

        self.summary_schema = SUMMARY_SCHEMA

        # PDF flag
        try:
            import PyPDF2
            self.pdf_enabled = True
        except ImportError:
            self.pdf_enabled = False
            print("[Summarizer] PyPDF2 not available")

        # Gemini setup
        self.gemini_model = None
        self.gemini_enabled = False
        
        api_key = api_key or st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        if api_key and GEMINI_AVAILABLE:
            try:
                genai.configure(api_key=api_key)
                self.gemini_model = genai.GenerativeModel(self.model)
                self.gemini_enabled = True
                print(f"[Summarizer] Gemini enabled with {self.model} (free tier)")
            except Exception as e:
                print(f"[Summarizer] Gemini init error: {e}")
                self.gemini_enabled = False
        else:
            print("[Summarizer] No Gemini key - Summaries will fail")

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
        meta = self._prepare_meta(paper)
        if not meta:
            return {"summary": "Summary couldn't be generated"}

        extracted_text = None
        is_paywalled = False
        if use_full_text and self.pdf_enabled and paper.get('pdf_url'):
            extracted_text, is_paywalled = self._download_and_extract_pdf(paper['pdf_url'])
            if is_paywalled:
                print(f"[Summarizer] Paywalled: {paper.get('title')}")
                extracted_text = None

        # Try PDF summary
        if extracted_text:
            chunks = self._chunk_text(extracted_text)[:self.max_chunks]
            chunk_summaries = self._chunk_and_summarize(chunks, meta, query=query)
            if chunk_summaries:
                final_summary = self._compose_final_summary_from_chunks(meta, chunk_summaries, query=query)
                if final_summary:
                    print(f"[DEBUG] PDF summary keys: {list(final_summary.keys())}")
                    return final_summary

        # Try abstract summary
        if self.gemini_enabled:
            abstract_summary = self._summarize_abstract(meta, query=query)
            if abstract_summary:
                print(f"[DEBUG] Abstract summary keys: {list(abstract_summary.keys())}")
                return abstract_summary

        # Fail explicitly (no conservative)
        return {"summary": "Summary couldn't be generated"}

    @retry_with_backoff
    def _gemini_call(self, prompt: str) -> str:
        """Core Gemini API call with retry."""
        if not self.gemini_enabled:
            return ""
        time.sleep(self.request_delay)
        try:
            response = self.gemini_model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 800
                }
            )
            return response.text.strip()
        except Exception as e:
            print(f"[Gemini Error] {e}")
            raise e

    def _chunk_and_summarize(self, chunks: List[str], meta: Dict[str, Any], query: str = "") -> List[str]:
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            if len(chunk_summaries) >= self.max_chunks:
                break
            try:
                prompt = (
                    f"Paper: {meta.get('title', 'Untitled')}\n"
                    f"Query: {query or 'general research'}\n\n"
                    f"Summarize this chunk in 4-6 detailed sentences, extracting key methods, results, and relevance to the query. "
                    f"Use specific details/numbers from the text:\n\n{chunk[:2000]}"
                )
                summary = self._gemini_call(prompt)
                if not summary:
                    summary = f"Chunk {i} summary unavailable."
                chunk_summaries.append(summary)
                time.sleep(self.request_delay + 0.5)
            except Exception as e:
                print(f"[Chunk {i} Error] {e}")
                chunk_summaries.append(f"Chunk {i} error.")
        return chunk_summaries

    def _prepare_meta(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "title": (paper.get("title") or "").strip(),
            "abstract": (paper.get("abstract") or "").strip(),
            "authors": paper.get("authors") or [],
            "year": paper.get("year"),
            "domain": paper.get("domain") or "",
            "source": paper.get("source") or "",
            "url": paper.get("url") or "",
            "full_text": paper.get("full_text")
        }

    def _download_and_extract_pdf(self, pdf_url: str) -> Tuple[Optional[str], bool]:
        try:
            headers = {"User-Agent": "research-assistant/1.0"}
            resp = requests.get(pdf_url, headers=headers, timeout=30, stream=True)
            if resp.status_code in (401, 403):
                return None, True
            if resp.status_code != 200:
                return None, True
            content_type = resp.headers.get("Content-Type", "").lower()
            content = resp.content
            if "html" in content_type or content.strip().startswith(b"<"):
                return None, True
            if "pdf" not in content_type and not content.startswith(b"%PDF"):
                return None, True
            if not PYPDF2_AVAILABLE:
                return None, False
            try:
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                    f.write(content)
                    tmp_name = f.name
                extracted_text = ""
                with open(tmp_name, "rb") as fh:
                    reader = PyPDF2.PdfReader(fh)
                    for page in reader.pages:
                        try:
                            txt = page.extract_text() or ""
                        except:
                            txt = ""
                        if txt:
                            extracted_text += txt + "\n\n"
                try:
                    os.unlink(tmp_name)
                except:
                    pass
                return extracted_text.strip() if extracted_text.strip() else None, False
            except Exception as e:
                print(f"[PDF Parse Error] {e}")
                return None, True
        except Exception as e:
            print(f"[PDF Download Error] {e}")
            return None, True

    def _chunk_text(self, text: str) -> List[str]:
        if not text:
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
        print(f"[Chunking] {len(chunks)} chunks (capped at {self.max_chunks})")
        return chunks

    @retry_with_backoff
    def _compose_final_summary_from_chunks(self, meta: Dict[str, Any], chunk_summaries: List[str], query: str = "") -> Optional[Dict[str, Any]]:
        aggregated = "\n\n---\n\n".join(chunk_summaries)
        if not aggregated:
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
            # Clean potential code block markers (raw string to avoid escape issues)
            json_str = json_str.replace("```json", "").replace("```", "").strip()
            
            final_summary = json.loads(json_str)
            if JSONSCHEMA_AVAILABLE:
                try:
                    validate(instance=final_summary, schema=self.summary_schema)
                except ValidationError as e:
                    print(f"[JSON Validation] {e}")
            return final_summary
        except json.JSONDecodeError as e:
            print(f"[JSON Parse Error] {e}\nResponse: {json_str[:200]}")
            return None
        except Exception as e:
            print(f"[Composition Error] {e}")
            return None

    @retry_with_backoff
    def _summarize_abstract(self, meta: Dict[str, Any], query: str = "") -> Optional[Dict[str, Any]]:
        abstract = meta.get('abstract', '')
        if not abstract or not self.gemini_enabled:
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
            # Clean potential code block markers
            json_str = json_str.replace("```json", "").replace("```", "").strip()
            
            summary = json.loads(json_str)
            return summary
        except Exception as e:
            print(f"[Abstract Summary Error] {e}")
            return None

    def _validate_parsed(self, parsed: Dict[str, Any]) -> bool:
        if not isinstance(parsed, dict):
            return False
        required = ["title", "abstract", "authors", "source", "url", "results_and_key_findings", "limitations_and_future_work"]
        for k in required:
            if k not in parsed:
                return False
        if not isinstance(parsed.get("authors"), list):
            return False
        if not isinstance(parsed.get("results_and_key_findings"), list):
            return False
        if not isinstance(parsed.get("limitations_and_future_work"), list):
            return False
        if JSONSCHEMA_AVAILABLE:
            try:
                validate(instance=parsed, schema=SUMMARY_SCHEMA)
            except:
                return False
        return True

    def conservative_summary(self, meta: Dict[str, Any], query: str = "") -> Dict[str, Any]:
        """Not used - we fail explicitly instead."""
        return {"summary": "Summary couldn't be generated"}
