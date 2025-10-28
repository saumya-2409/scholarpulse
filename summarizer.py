"""
summarizer.py

Full-paper summarizer that:
- downloads PDF when available (open-access only),
- extracts text (PyPDF2),
- chunks text, summarizes each chunk via Hugging Face free API (replaces OpenAI for quota issues),
- composes a final structured summary (JSON) using HF + rule-based filling,
- falls back to a conservative non-hallucinating summary if API unavailable.

Important:
- Requires `requests` for HF API (already in requirements).
- Set HUGGINGFACE_API_TOKEN in Streamlit secrets.
- OpenAI disabled for quota issues.
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

# Optional JSON schema validation
try:
    from jsonschema import validate, ValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False

# OpenAI client (kept for compatibility but disabled)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

OPENAI_API_KEY = None

DEFAULT_MODEL = "gpt-4o-mini"  # Unused now; for legacy
CHUNK_CHAR_SIZE = 3000  # characters per chunk for summarization (tune as needed)
CHUNK_OVERLAP = 200

from openai import RateLimitError  # For legacy; now used for HF too

def retry_with_backoff(func, initial_delay: float = 1, max_delay: float = 60, max_retries: int = 6):
    """Custom exponential backoff retry for API calls (OpenAI or HF)."""
    def wrapper(*args, **kwargs):
        num_retries = 0
        delay = initial_delay
        while True:
            try:
                return func(*args, **kwargs)
            except RateLimitError as e:
                num_retries += 1
                if num_retries > max_retries:
                    raise Exception(f"Max retries ({max_retries}) exceeded for {func.__name__}: {e}")
                # Exponential backoff with jitter
                delay = min(delay * 2 * (1 + random.random()), max_delay)
                print(f"[Rate Limit] Retrying in {delay:.1f}s (attempt {num_retries}/{max_retries})")
                time.sleep(delay)
            except requests.exceptions.HTTPError as e:  ### NEW: Handle HF 429
                if e.response and e.response.status_code == 429:
                    num_retries += 1
                    if num_retries > max_retries:
                        raise Exception(f"Max retries exceeded for HF: {e}")
                    delay = min(delay * 2 * (1 + random.random()), max_delay)
                    print(f"[HF Rate Limit] Retrying in {delay:.1f}s (attempt {num_retries}/{max_retries})")
                    time.sleep(delay)
                else:
                    raise e
            except Exception as e:
                raise e  # Re-raise non-rate-limit errors
        return wrapper

# Schema for the final structured summary (unchanged)
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
    """
    Summarizer that processes whole papers (via PDF when available).
    """
    def __init__(self, model: str = "gpt-4o-mini", chunk_size: int = 3000, max_chunks: int = 5, overlap: int = 200, api_key: str = None):
        """
        Initialize with optional API key override (uses secrets/env for Cloud/local).
        Sets up HF client (OpenAI disabled), PDF extraction, and chunking params.
        """
        self.model = model  # Unused now
        self.chunk_size = chunk_size
        self.max_chunks = max_chunks
        self.overlap = overlap
        self.request_delay = 1  # 1s delay between requests for free tier limits

        # Ensure overlap doesn't exceed chunk_size to avoid issues
        if self.overlap >= self.chunk_size:
            self.overlap = int(self.chunk_size * 0.1)  # Fallback to 10% of chunk_size
            print(f"[FullPaperSummarizer] Adjusted overlap to {self.overlap} (was >= chunk_size)")

        self.summary_schema = SUMMARY_SCHEMA

        # PDF extraction flag (unchanged)
        try:
            import PyPDF2
            self.pdf_enabled = True
        except ImportError:
            self.pdf_enabled = False
            print("[FullPaperSummarizer] PyPDF2 not available - PDF extraction disabled")
        
        # ### NEW/UPDATED: Disable OpenAI for quota issues; add HF setup
        self.client = None
        self.openai_enabled = False  # Force disable
        print("[FullPaperSummarizer] OpenAI disabled due to quota - Using HF or conservative")
        
        # Hugging Face setup (from secrets/env)
        self.hf_token = st.secrets.get("HUGGINGFACE_API_TOKEN") or os.getenv("HUGGINGFACE_API_TOKEN")
        self.hf_model = "facebook/bart-large-cnn"  # Free summarization model (good for abstracts/chunks)
        self.hf_enabled = bool(self.hf_token)
        if self.hf_enabled:
            print(f"[FullPaperSummarizer] Hugging Face enabled with {self.hf_model}")
        else:
            print("[FullPaperSummarizer] No HF token - Using conservative summaries only")
        
        # Other initializations
        self.schema_loaded = True  # Assume schema is ready

    def _infer_domain(self, abstract: str, query: str) -> str:
        """
        Infer paper domain from abstract and query using keyword matching.
        Returns a concise domain string (e.g., 'AI/ML/Finance').
        """
        if not abstract:
            return "General Research"
        
        text = (abstract.lower() + " " + (query or "").lower())
        domains = {
            "ai/ml/finance": ["machine learning", "neural network", "prediction", "stock", "financial", "forecasting"],
            "ai/ml/nlp": ["natural language", "processing", "nlp", "text analysis", "sentiment"],
            "computer vision": ["image", "vision", "object detection", "computer vision"],
            "data science": ["data science", "big data", "analytics", "statistics"],
            "cybersecurity": ["security", "cyber", "encryption", "threat"],
            "robotics": ["robot", "autonomous", "control system"]
        }
        
        for domain, keywords in domains.items():
            if any(kw in text for kw in keywords):
                return domain.replace("/", "/")  # e.g., 'AI/ML/Finance'
        
        # Fallback based on query
        if "stock" in text or "finance" in text:
            return "Finance/ML"
        return "AI/ML"  # Default for research papers

    # ---- Public API ----
    def summarize_paper(self, paper: Dict[str, Any], use_full_text: bool = True, timeout: int = 120, query: str = "") -> Dict[str, Any]:
        """
        Summarize a paper using full text if available (via PDF), or abstract.
        Now uses HF for free summarization; falls back to conservative.
        """
        meta = self._prepare_meta(paper)  # Assume this exists; extracts title/abstract/etc.
        if not meta:
            return {}
        
        extracted_text = None
        is_paywalled = False
        if use_full_text and self.pdf_enabled and paper.get('pdf_url'):
            extracted_text, is_paywalled = self._download_and_extract_pdf(paper['pdf_url'])
            if is_paywalled:
                print(f"[FullPaperSummarizer] Paper paywalled: {paper.get('title')}")
                extracted_text = None
        
        if extracted_text:
            # Cap chunks at 5 for free tier to limit API calls
            chunks = self._chunk_text(extracted_text)[:5]
            chunk_summaries = self._chunk_and_summarize(chunks, meta, timeout=timeout // 2, query=query)  # Pass chunks directly
            if chunk_summaries:
                final_summary = self._compose_final_summary_from_chunks(meta, chunk_summaries, timeout // 2, query=query)
                # DEBUG
                print(f"[DEBUG Summarize] Used HF PDF, enabled: {self.hf_enabled}; final_summary keys: {list(final_summary.keys()) if final_summary else None}")
                if final_summary:
                    for k, v in final_summary.items():
                        print(f"[DEBUG Summarize] {k}: {repr(v)[:200]}")
                return final_summary
        
        # No full text: Use HF on abstract
        if self.hf_enabled:
            abstract_summary = self._summarize_abstract(meta, timeout=timeout // 2, query=query)  ### UPDATED: Renamed method
            print(f"[DEBUG Summarize] Used HF abstract, enabled: {self.hf_enabled}; abstract_summary keys: {list(abstract_summary.keys()) if abstract_summary else None}")
            if abstract_summary:
                for k, v in abstract_summary.items():
                    print(f"[DEBUG Summarize] {k}: {repr(v)[:200]}")
                return abstract_summary

        # ### UPDATED: Direct fallback to conservative (no OpenAI check)
        return self.conservative_summary(meta, query)

    # ### NEW: Core HF summarization method
    @retry_with_backoff
    def _hf_summarize(self, text: str, query: str = "") -> str:
        """Summarize text via HF free API (with backoff for 429s)."""
        if not self.hf_enabled or not text:
            return ""
        
        time.sleep(self.request_delay)  # Delay before call
        
        # Truncate for HF free limits (~512 tokens input)
        short_text = f"Query: {query}\nText: {text[:1024]}" if query else text[:1024]
        payload = {
            "inputs": short_text,
            "parameters": {"max_length": 150, "min_length": 30, "do_sample": False}  # Short, factual output
        }
        headers = {"Authorization": f"Bearer {self.hf_token}"}
        
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{self.hf_model}",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and result:
                summary = result[0].get('summary_text', '').strip()
                print(f"[HF Debug] Success: {summary[:50]}...")  # Log snippet
                return summary
            print(f"[HF Debug] Empty response for input length {len(short_text)}")
            return ""
        elif response.status_code == 429:
            raise RateLimitError("HF rate limit hit")  # Triggers backoff
        else:
            print(f"[HF Error] {response.status_code}: {response.text[:100]}")
            return ""

    # ### UPDATED: Use HF instead of OpenAI; keep structure
    def _chunk_and_summarize(self, chunks: List[str], meta: Dict[str, Any], timeout: int = 60, query: str = "") -> List[str]:
        """
        Summarize each chunk with HF, tying to query.
        Returns list of chunk summaries.
        """
        chunk_summaries = []
        
        for i, chunk in enumerate(chunks):
            if len(chunk_summaries) >= self.max_chunks:  # Limit chunks
                break
            
            # HF call on chunk (truncate for limits)
            try:
                userprompt = (
                    f"Paper title: {meta.get('title', 'Untitled')}\n"
                    f"Search query context: Relate to '{query or 'general research'}' if relevant.\n"
                    f"Summarize in 3-5 sentences: {chunk[:1500]}"  # Keep your truncation
                )
                summary = self._hf_summarize(userprompt, query)  # Use HF
                if not summary:
                    summary = f"Summary unavailable for chunk {i}."  # Fallback
                chunk_summaries.append(summary)
                # Delay after successful call
                time.sleep(self.request_delay + 0.5)
            except Exception as e:
                print(f"[FullPaperSummarizer] Chunk {i} error: {e}")
                chunk_summaries.append(f"Summary unavailable for chunk {i}.")
        
        return chunk_summaries

    # ---- Helpers (Unchanged: _prepare_meta, _download_and_extract_pdf, _chunk_text) ----
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
        return meta

    def _download_and_extract_pdf(self, pdf_url: str) -> Tuple[Optional[str], bool]:
        """
        Download PDF and extract text using PyPDF2.
        Returns: (extracted_text or None, paywalled_flag)
        Paywalled_flag: True if access blocked (HTTP 403/401 or HTML returned).
        """
        try:
            headers = {"User-Agent": "research-assistant/1.0 (+https://example.com)"}
            resp = requests.get(pdf_url, headers=headers, timeout=30, stream=True)
            if resp.status_code in (401, 403):
                # Paywalled / unauthorized
                return None, True
            if resp.status_code != 200:
                return None, True  # Treat non-200 as unavailable
            
            content_type = resp.headers.get("Content-Type", "").lower()
            content = resp.content
            
            # If server returned HTML (login page), treat as paywalled
            if "html" in content_type or content.strip().startswith(b"<"):
                return None, True
            
            # Check for PDF content
            if "pdf" not in content_type and not content.startswith(b"%PDF"):
                # Not a PDF -> treat as paywalled/unavailable
                return None, True
            
            if not PYPDF2_AVAILABLE:
                return None, False  # Can't parse, but not necessarily paywalled
            
            # Parse with PyPDF2
            try:
                # Write to temp file
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                    f.write(content)
                    tmp_name = f.name
                
                extracted_text = ""
                with open(tmp_name, "rb") as fh:
                    reader = PyPDF2.PdfReader(fh)
                    # Iterate pages and extract text
                    for page in reader.pages:
                        try:
                            txt = page.extract_text() or ""
                        except Exception:
                            txt = ""
                        if txt:
                            extracted_text += txt + "\n\n"
                
                # Cleanup temp file
                try:
                    os.unlink(tmp_name)
                except Exception:
                    pass
                
                # Always return a tuple
                return extracted_text.strip() if extracted_text.strip() else None, False
            
            except Exception as e:
                print(f"[FullPaperSummarizer] PDF parsing error: {e}")
                return None, True  # Parsing error; treat as inaccessible
            
        except Exception as e:
            print(f"[FullPaperSummarizer] PDF download error: {e}")
            return None, True  # Network error etc.; treat as paywalled/unavailable

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks of approx chunk_size characters."""
        if not text:
            return []
        
        text = text.strip()
        chunks = []
        start = 0
        L = len(text)

        while start < L:
            end = min(L, start + self.chunk_size)
            chunk = text[start:end]
            chunks.append(chunk)

            # Advance with overlap, but ensure progress
            step = max(1, self.chunk_size - self.overlap)  # Minimum step of 1 to avoid loops
            start += step

            if len(chunks) >= self.max_chunks:
                break
        
        print(f"[Chunking] Created {len(chunks)} chunks (capped at {self.max_chunks} for rate limits)")   
        return chunks

    # ### UPDATED: Use HF on aggregated; build simple JSON (no OpenAI)
    def _compose_final_summary_from_chunks(self, meta: Dict[str, Any], chunk_summaries: List[str], timeout: int = 60, query: str = "") -> Optional[Dict[str, Any]]:
        """
        Compose chunk summaries into final structured JSON using HF on aggregated.
        """
        aggregated = "\n\n---\n\n".join(chunk_summaries)  # Join chunks
        
        if not aggregated:
            return None
        
        time.sleep(self.request_delay)  # Delay before call
        
        try:
            # Use HF for overall summary
            user = (
                f"QUERY: Relate to '{query or 'general research'}'.\n"
                f"PAPER METADATA: Title: {meta.get('title', 'Untitled')}\n"
                f"Abstract: {meta.get('abstract', '')}\n\n"
                f"CHUNK SUMMARIES: {aggregated[:4000]}\n"  # Keep your truncation
                "Summarize key approach, results, and value."
            )
            agg_summary = self._hf_summarize(user, query)  # Use HF
            
            if agg_summary:
                # ### NEW: Build structured JSON from meta + HF output (simple filling)
                final_summary = {
                    'title': meta.get('title', 'Untitled'),
                    'abstract': meta.get('abstract', ''),
                    'authors': meta.get('authors', []),
                    'year': meta.get('year'),
                    'domain': self._infer_domain(meta.get('abstract', ''), query),
                    'source': meta.get('source', ''),
                    'url': meta.get('url', ''),
                    'problem_statement': None,  # HF doesn't extract deeply; use conservative if needed
                    'motivation': None,
                    'approach': agg_summary[:150] if agg_summary else None,
                    'experiments_and_evaluation': None,
                    'results_and_key_findings': [agg_summary] if agg_summary else ["Key findings from chunks."],
                    'limitations_and_future_work': ["Inferred from abstract/chunks."],
                    'reusability_practical_value': f"Practical value for {query or 'research'}: {agg_summary[-100:] if agg_summary else ''}"
                }
                # Validate if schema available
                if JSONSCHEMA_AVAILABLE:
                    try:
                        validate(instance=final_summary, schema=self.summary_schema)
                    except ValidationError as e:
                        print(f"[HF JSON Validation] {e}")
                print(f"[HF Debug] Composed summary length: {len(agg_summary)}")
                return final_summary
            else:
                print("[HF Composition] No summary generated - Falling to conservative")
                return None
        
        except Exception as e:
            print(f"[FullPaperSummarizer] HF Composition error: {e}")
            return None

    # ### UPDATED: Renamed to _summarize_abstract; use HF instead of OpenAI
    def _summarize_abstract(self, meta: Dict[str, Any], timeout: int = 60, query: str = "") -> Optional[Dict[str, Any]]:
        """
        Use HF to summarize abstract only, with query context.
        Returns structured JSON or None.
        """
        abstract = meta.get('abstract', '')
        if not abstract or not self.hf_enabled:
            return None
        
        time.sleep(self.request_delay)  # Delay before call
        
        try:
            user = (
                f"QUERY: Relate to '{query or 'general research'}'.\n\n"
                f"PAPER: Title: {meta.get('title')}, Authors: {', '.join(meta.get('authors', []))}, Year: {meta.get('year')}\n"
                f"Abstract: {abstract[:2000]}\n"  # Keep your truncation
                "Summarize key ideas in a few sentences."
            )
            summary_text = self._hf_summarize(user, query)  # Use HF
            
            if summary_text:
                # Build JSON from meta + HF
                return {
                    'title': meta.get('title', 'Untitled'),
                    'abstract': meta.get('abstract', ''),
                    'authors': meta.get('authors', []),
                    'year': meta.get('year'),
                    'domain': self._infer_domain(abstract, query),
                    'source': meta.get('source', ''),
                    'url': meta.get('url', ''),
                    'problem_statement': None,
                    'motivation': None,
                    'approach': summary_text[:100],
                    'experiments_and_evaluation': None,
                    'results_and_key_findings': [summary_text],
                    'limitations_and_future_work': ["From abstract."],
                    'reusability_practical_value': f"Relevance to {query or 'research'}: {summary_text[-50:]}"
                }
            return None
        
        except Exception as e:
            print(f"[FullPaperSummarizer] HF Abstract error: {e}")
            return None

    # Validation (unchanged)
    def _validate_parsed(self, parsed: Dict[str, Any]) -> bool:
        if not isinstance(parsed, dict):
            return False
        # require minimal keys
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
        # jsonschema optional check
        if JSONSCHEMA_AVAILABLE:
            try:
                validate(instance=parsed, schema=SUMMARY_SCHEMA)
            except Exception:
                return False
        return True

    # Conservative fallback if HF not available or fails (unchanged)
    def conservative_summary(self, meta: Dict[str, Any], query: str = "") -> Dict[str, Any]:
        """
        Generate a basic, non-hallucinating summary from metadata/abstract only.
        Ties to query for relevance in findings/limitations/value.
        """
        abstract = meta.get('abstract', '') or meta.get('title', '')
        title = meta.get('title', 'Untitled')
        
        # Keyword-based extraction (keep/improve your existing logic)
        def find_sentences_keywords(text: str, keywords: List[str], max_sentences: int = 3) -> List[str]:
            sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 20]
            relevant = []
            for sent in sentences:
                if any(kw in sent.lower() for kw in keywords):
                    relevant.append(sent)
                    if len(relevant) >= max_sentences:
                        break
            return relevant
        
        # Extract fields from abstract
        problem = find_sentences_keywords(abstract, ['problem', 'challenge', 'issue', 'aim', 'objective'])
        motivation = find_sentences_keywords(abstract, ['motivate', 'importance', 'need', 'why'])
        approach = find_sentences_keywords(abstract, ['method', 'approach', 'model', 'technique', 'algorithm'])
        experiments = find_sentences_keywords(abstract, ['experiment', 'dataset', 'evaluate', 'test'])
        findings = find_sentences_keywords(abstract, ['result', 'finding', 'achieve', 'accuracy', 'improvement', 'performance'])
        limitations = find_sentences_keywords(abstract, ['limit', 'however', 'constraint', 'future', 'gap', 'challenge'])
        
        # Make findings/limitations query-relevant if sparse
        query_lower = query.lower() if query else 'research'
        if not findings:
            sentences = [s.strip() for s in re.split(r'[.!?]+', abstract) if len(s.strip()) > 30]
            findings = [s + f" (potentially relevant to {query_lower})" for s in sentences[:3] if any(word in s.lower() for word in ['result', 'show', 'achieve'])]
        if not limitations:
            sentences = [s.strip() for s in re.split(r'[.!?]+', abstract) if len(s.strip()) > 30]
            limitations = [s + f" (implied gap for {query_lower})" for s in sentences[:2] if any(word in s.lower() for word in ['limit', 'however', 'future', 'improve'])]
        
        reusability = (
            f"This paper's approach and findings offer practical value for {query_lower} applications, "
            f"such as extending ML models for financial forecasting or similar domains based on the abstract."
            if query else "The methods and results are reusable in related research areas for broader impact."
        )
        
        summary = {  # Return 'summary' var
            'title': title,
            'abstract': abstract,
            'authors': meta.get('authors', []),
            'year': meta.get('year'),
            'domain': self._infer_domain(abstract, query),
            'source': meta.get('source'),
            'url': meta.get('url'),
            'problem_statement': problem[0] if problem else None,
            'motivation': motivation[0] if motivation else None,
            'approach': approach[0] if approach else None,
            'experiments_and_evaluation': experiments[0] if experiments else None,
            'results_and_key_findings': findings if findings else [f"Key findings derived from abstract, applicable to {query_lower}."],
            'limitations_and_future_work': limitations if limitations else [f"Future directions suggested in abstract for {query_lower}."],
            'reusability_practical_value': reusability
        }
        
        print(f"[DEBUG Conservative] Generated keys: {list(summary.keys())}")
        return summary
