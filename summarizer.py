"""
summarizer.py

Full-paper summarizer using Google Gemini API (free tier):
- Auto-picks available model (e.g., gemini-2.5-pro from logs).
- No calls on skips; single init only.
- On fail: Explicit message (no quota waste).
"""

import os
import io
import json
import time
import tempfile
import requests
import re
from typing import Dict, Any, Optional, List, Tuple
import streamlit as st

# Text extraction
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
    print("[Debug] PyPDF2 available")
except ImportError:
    PYPDF2_AVAILABLE = False
    print("[Debug] PyPDF2 missing")

# JSON schema
try:
    from jsonschema import validate, ValidationError
    JSONSCHEMA_AVAILABLE = True
    print("[Debug] JSONSchema available")
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    print("[Debug] JSONSchema missing")

# Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    print("[Debug] google-generativeai loaded")
except ImportError:
    GEMINI_AVAILABLE = False
    print("[Debug] google-generativeai missing - Add to requirements.txt")

# Defaults (your logs show 2.5 series available)
PREFERRED_MODELS = ["gemini-2.5-pro", "gemini-2.0-flash", "gemini-pro-latest"]  # From logs
CHUNK_CHAR_SIZE = 3000
CHUNK_OVERLAP = 200

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
    _instance = None  # Singleton enforcement (prevents multiple inits)

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, chunk_size: int = 3000, max_chunks: int = 5, overlap: int = 200, api_key: str = None):
        if hasattr(self, 'initialized'):  # Skip re-init
            return
        self.initialized = True
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.max_chunks = min(max_chunks, 3)
        self.request_delay = 5  # Slower for quota

        self.current_model = None  # FIXED: None until success

        self.summary_schema = SUMMARY_SCHEMA
        self.pdf_enabled = PYPDF2_AVAILABLE

        # Gemini setup (auto-pick from available)
        self.gemini_model = None
        self.gemini_enabled = False
        
        api_key = api_key or st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
        print(f"[Gemini Debug] Key loaded: {'Yes' if api_key else 'No'}")
        print(f"[Gemini Debug] Package: {GEMINI_AVAILABLE}")

        if api_key and GEMINI_AVAILABLE:
            try:
                genai.configure(api_key=api_key)
                # List models once (1 API call)
                print("[Gemini Debug] Available models:")
                available = []
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        model_name = m.name.split('/')[-1]  # e.g., "gemini-2.5-pro"
                        available.append(model_name)
                        print(f"  - {m.name}")

                if not available:
                    raise Exception("No models")

                # FIXED: Auto-pick first preferred/available (no skips)
                selected_model = None
                for pref in PREFERRED_MODELS:
                    if pref in available:
                        selected_model = pref
                        break
                if not selected_model:
                    # Fallback to first pro/flash
                    for mod in available:
                        if 'pro' in mod or 'flash' in mod:
                            selected_model = mod
                            break
                if not selected_model:
                    selected_model = available[0]  # Last resort

                print(f"[Gemini Debug] Selected available model: {selected_model}")

                # Instantiate (no test - saves quota)
                try:
                    self.gemini_model = genai.GenerativeModel(selected_model)
                    self.current_model = selected_model
                    self.gemini_enabled = True
                    print(f"[Summarizer] Enabled with {self.current_model} (auto-selected from available)")
                except Exception as e:
                    error = str(e)[:100]
                    print(f"[Gemini Debug] Selected model failed: {error}")
                    self.gemini_enabled = False

                if not self.gemini_enabled:
                    print("[Summarizer] No working model - Check key/project quotas")

            except Exception as e:
                print(f"[Summarizer Init Error] {str(e)[:150]}")
        else:
            print("[Summarizer] No key/package - Fails explicit")

    def summarize_paper(self, paper: Dict[str, Any], use_full_text: bool = True, query: str = "") -> Dict[str, Any]:
        print(f"[Debug] Summarizing: {paper.get('title', '')[:50]}")
        meta = self._prepare_meta(paper)
        if not meta:
            return {"summary": "Failed: Invalid metadata"}

        extracted_text = None
        is_paywalled = False
        if use_full_text and self.pdf_enabled and paper.get('pdf_url'):
            extracted_text, is_paywalled = self._download_and_extract_pdf(paper['pdf_url'])
            if is_paywalled:
                print("[Debug] Paywalled PDF")
                extracted_text = None

        if extracted_text:
            chunks = self._chunk_text(extracted_text)[:self.max_chunks]
            chunk_summaries = self._chunk_and_summarize(chunks, meta, query)
            if chunk_summaries:
                final = self._compose_final_summary_from_chunks(meta, chunk_summaries, query)
                if final:
                    return final

        if self.gemini_enabled and self.current_model:
            print("-----")
            abstract_summary = self._summarize_abstract(meta, query)
            if abstract_summary:
                return abstract_summary
            else:
                return {"summary": "API call failed (check logs: quota/empty response)"}
        return {"summary": f"Gemini not enabled: Model '{self.current_model}' unavailable - Use AI Studio models"}

    def _gemini_call(self, prompt: str) -> str:
        if not self.gemini_enabled or not self.current_model:
            print("[API Failed] No model enabled - Skipping call")
            return ""
        print(f"[Debug] Call with {self.current_model}: {len(prompt)} chars")
        time.sleep(self.request_delay)
        try:
            response = self.gemini_model.generate_content(
                prompt,
                generation_config={"temperature": 0.3, "max_output_tokens": 800}
            )
            # FIX: Check if candidates exist and are not blocked before accessing response.text
            if not response.candidates:
                # The response object is likely a wrapper for an empty/blocked result
                raise Exception("Response candidates list is empty (API or Safety Block)")
            # Use response.text which is now safer
            text = response.text

            if text and text.strip():
                print("[Debug] Call success")
                return text.strip()
            raise Exception("Response text is empty or None")
        except Exception as e:
            error = str(e)[:100].lower()
            print(f"[API Failed] {error}")
            if "404" in error:
                print("[API Failed] Model unavailable - Regenerate key")
            elif "429" in error or "quota" in error:
                print("[API Failed] Rate limit - Wait/reduce papers")
            elif "invalid operation" in error or "safety block" in error:
                print("[API Failed] Response text failed (blocked/malformed)")
            return ""

    def _chunk_and_summarize(self, chunks: List[str], meta: Dict[str, Any], query: str = "") -> List[str]:
        summaries = []
        for i, chunk in enumerate(chunks[:self.max_chunks]):
            prompt = f"Paper: {meta['title']}\nQuery: {query}\nSummarize chunk in 4-6 sentences with details:\n{chunk[:2000]}"
            summary = self._gemini_call(prompt)
            summaries.append(summary if summary else f"Chunk {i} failed")
        return summaries

    def _prepare_meta(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "title": paper.get("title", "").strip(),
            "abstract": paper.get("abstract", "").strip(),
            "authors": paper.get("authors", []),
            "year": paper.get("year"),
            "domain": self._infer_domain(paper.get("abstract", ""), ""),
            "source": paper.get("source", ""),
            "url": paper.get("url", "")
        }

    def _infer_domain(self, abstract: str, query: str) -> str:
        text = (abstract or query or "").lower()
        if any(kw in text for kw in ["stock", "financial", "prediction"]):
            return "AI/ML/Finance"
        return "AI/ML"

    def _download_and_extract_pdf(self, pdf_url: str) -> Tuple[Optional[str], bool]:
        try:
            resp = requests.get(pdf_url, timeout=30)
            if resp.status_code != 200 or not resp.content.startswith(b"%PDF"):
                return None, True
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(resp.content)
                tmp = f.name
            text = ""
            with open(tmp, "rb") as fh:
                reader = PyPDF2.PdfReader(fh)
                for page in reader.pages:
                    text += page.extract_text() or "" + "\n\n"
            os.unlink(tmp)
            return text.strip() or None, False
        except:
            return None, True

    def _chunk_text(self, text: str) -> List[str]:
        if not text:
            return []
        chunks = []
        start = 0
        L = len(text)
        while start < L:
            end = min(L, start + self.chunk_size)
            chunks.append(text[start:end])
            start += self.chunk_size - self.overlap
            if len(chunks) >= self.max_chunks:
                break
        return chunks

    def _compose_final_summary_from_chunks(self, meta: Dict[str, Any], chunk_summaries: List[str], query: str = "") -> Optional[Dict[str, Any]]:
        aggregated = "\n\n".join(chunk_summaries)
        prompt = f"""Metadata: Title {meta['title']}, Abstract {meta['abstract'][:1000]}...\nChunks: {aggregated[:4000]}
Output JSON only (use schema below for keys):\n{json.dumps(SUMMARY_SCHEMA['properties'], indent=2)}"""
        json_str = self._gemini_call(prompt)
        if not json_str:
            return None
        json_str = re.sub(r'``````', '', json_str).strip()
        try:
            summary = json.loads(json_str)
            return summary
        except:
            return None

    def _summarize_abstract(self, meta: Dict[str, Any], query: str = "") -> Optional[Dict[str, Any]]:
        abstract = meta['abstract']
        if not abstract:
            return None
        prompt = f"""Query: {query}\nTitle: {meta['title']}\nAbstract: {abstract[:2500]}
JSON summary (use schema for keys, extract sections from abstract)"""
        json_str = self._gemini_call(prompt)
        if not json_str:
            return None
        json_str = re.sub(r'``````', '', json_str).strip()
        try:
            return json.loads(json_str)
        except:
            return None

    def _validate_parsed(self, parsed: Dict[str, Any]) -> bool:
        required = ["title", "abstract", "authors", "source", "url", "results_and_key_findings", "limitations_and_future_work"]
        for k in required:
            if k not in parsed:
                return False
        return isinstance(parsed.get("authors"), list) and isinstance(parsed.get("results_and_key_findings"), list)

    def conservative_summary(self, meta: Dict[str, Any], query: str = "") -> Dict[str, Any]:
        return {"summary": "API unavailable"}
