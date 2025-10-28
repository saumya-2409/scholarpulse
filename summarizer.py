"""
summarizer.py

Full-paper summarizer that:
 - downloads PDF when available (open-access only),
 - extracts text (PyPDF2),
 - chunks text, summarizes each chunk via LLM,
 - composes a final structured summary (JSON) using the LLM,
 - falls back to a conservative non-hallucinating summary if LLM unavailable.

Important:
 - Requires `openai` package + OPENAI_API_KEY for LLM summarization.
 - Requires `PyPDF2` and `requests` to download & parse PDFs.
 - Do not hardcode your OpenAI key in files; use env var OPENAI_API_KEY.
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
except ImportError:
    PYPDF2_AVAILABLE = False

# Optional JSON schema validation
try:
    from jsonschema import validate, ValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False

# OpenAI client
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

OPENAI_API_KEY = None

DEFAULT_MODEL = "gpt-4o-mini"  # change if you have other model access
CHUNK_CHAR_SIZE = 3000  # characters per chunk for LLM summarization (tune as needed)
CHUNK_OVERLAP = 200

# Schema for the final structured summary
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
    def __init__(self, model: str = "gpt-4o-mini", chunk_size: int = 3000, max_chunks: int = 10, api_key: str = None):
        """
        Initialize with optional API key override (uses secrets/env for Cloud/local).
        Sets up OpenAI client, PDF extraction, and chunking params.
        """
        self.model = model
        self.chunk_size = chunk_size
        self.max_chunks = max_chunks
        self.summary_schema = None  # Your existing line
        
        # PDF extraction flag (from global or requirements)
        try:
            import PyPDF2
            self.pdf_enabled = True
        except ImportError:
            self.pdf_enabled = False
            print("[FullPaperSummarizer] PyPDF2 not available - PDF extraction disabled")
        
        # OpenAI setup with multi-fallback key
        self.client = None
        self.openai_enabled = False
        
        # Prioritize: Passed key > Streamlit secrets (Cloud) > Env var (local) > None
        api_key = (api_key or 
                   st.secrets.get("OPENAI_API_KEY") or   # Cloud secrets (secure)
                   os.getenv("OPENAI_API_KEY") or           # Local env var
                   OPENAI_API_KEY)
        
        if api_key and OPENAI_AVAILABLE:  # No longer default hardcoded
            try:
                self.client = openai.OpenAI(api_key=api_key)
                # Validate key non-blockingly
                self.client.models.list()  # Raises AuthenticationError if invalid
                self.openai_enabled = True
                print(f"[FullPaperSummarizer] OpenAI enabled with {self.model} (key valid, ends in {api_key[-4:]})")
            except openai.AuthenticationError:
                print("[FullPaperSummarizer] OpenAI auth failed (invalid key) - Using conservative summaries")
                self.openai_enabled = False
            except Exception as e:
                print(f"[FullPaperSummarizer] OpenAI init error: {e} - Using conservative summaries")
                self.openai_enabled = False
        else:
            print("[FullPaperSummarizer] No OpenAI key provided - Using conservative summaries only")
            self.openai_enabled = False
        
        # Other initializations (add if missing in your class; e.g., for schema)
        self.schema_loaded = False

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
        Now accepts query for relevance highlighting.
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
            chunk_summaries = self._chunk_and_summarize(extracted_text, meta, timeout=timeout // 2, query=query)
            if chunk_summaries:
                final_summary = self._compose_final_summary_from_chunks(meta, chunk_summaries, timeout // 2, query=query)
                # DEBUG
                print(f"[DEBUG Summarize] Used PDF, OpenAI enabled: {self.openai_enabled}; final_summary keys: {list(final_summary.keys()) if final_summary else None}")
                if final_summary:
                    for k, v in final_summary.items():
                        print(f"[DEBUG Summarize] {k}: {repr(v)[:200]}")
                return final_summary
        
        # No full text: Use OpenAI on abstract (your preference)
        if self.openai_enabled:
            abstract_summary = self._call_openai_on_abstract(meta, timeout=timeout // 2, query=query)
            print(f"[DEBUG Summarize] Used abstract LLM, OpenAI enabled: {self.openai_enabled}; abstract_summary keys: {list(abstract_summary.keys()) if abstract_summary else None}")
            if abstract_summary:
                for k, v in abstract_summary.items():
                    print(f"[DEBUG Summarize] {k}: {repr(v)[:200]}")
                return abstract_summary
        

        # Final fallback: Just return a single summary line rather than structured fallback
        return {"summary": "Summary couldn't be extracted"}

    def _chunk_and_summarize(self, text: str, meta: Dict[str, Any], timeout: int = 60, query: str = "") -> List[str]:
        """
        Split text into chunks and summarize each with LLM, tying to query.
        Returns list of chunk summaries.
        """
        # Chunk text (keep your existing logic, e.g., by sentences/words)
        chunks = self._chunk_text(text)
        chunk_summaries = []
        
        for i, chunk in enumerate(chunks):
            if len(chunk_summaries) >= self.max_chunks:  # Limit chunks
                break
            
            # LLM call on chunk with query context
            try:
                userprompt = (
                    f"Paper title: {meta.get('title', 'Untitled')}\n"
                    f"Search query context: Relate to '{query or 'general research'}' if relevant (e.g., highlight stock prediction aspects).\n"
                    f"Summarize this chunk in 3-5 specific sentences: Extract key ideas, methods, results, or limitations. "
                    f"Use real details/numbers from text. No invention or generics."
                    f"\nChunk {i+1}: {chunk}"
                )
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": userprompt}],
                    max_tokens=200,
                    temperature=0.3,
                    timeout=timeout
                )
                summary = response.choices[0].message.content.strip()
                chunk_summaries.append(summary)
                time.sleep(0.5)  # Rate limit
            except Exception as e:
                print(f"[FullPaperSummarizer] Chunk {i} error: {e}")
                chunk_summaries.append(f"Summary unavailable for chunk {i}.")  # Fallback
        
        return chunk_summaries

    # ---- Helpers ----
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
            start = end - self.overlap  # overlap
        return chunks

    def _compose_final_summary_from_chunks(self, meta: Dict[str, Any], chunk_summaries: List[str], timeout: int = 60, query: str = "") -> Optional[Dict[str, Any]]:
        """
        Compose chunk summaries into final structured JSON, with query relevance.
        """
        aggregated = "\n\n---\n\n".join(chunk_summaries)  # Join chunks
        
        if not aggregated:
            return None
        
        try:
            user = (
                f"QUERY CONTEXT: Relate the summary to the search query '{query or 'general research'}'. "
                f"In problem_statement, approach, results_and_key_findings, and reusability_practical_value, "
                f"highlight 2-3 specific connections (e.g., 'This improves stock prediction accuracy by X% via ML methods').\n\n"
                f"PAPER METADATA:\nTitle: {meta.get('title', 'Untitled')}\n"
                f"Authors: {', '.join(meta.get('authors', []))}\nYear: {meta.get('year', 'N/A')}\n"
                f"Source: {meta.get('source', 'arXiv/Semantic')}\nURL: {meta.get('url', '')}\n"
                f"Abstract: {meta.get('abstract', '')}\n\n"
                f"CHUNK SUMMARIES (extract ONLY from these - no external knowledge or invention):\n{aggregated}\n\n"
                "Output ONLY a valid JSON object with these exact keys:\n"
                "- title: string (from metadata)\n"
                "- abstract: string (from metadata)\n"
                "- authors: array of strings\n"
                "- year: integer or null\n"
                "- domain: string (e.g., 'AI/ML/Finance' based on content)\n"
                "- source: string (from metadata)\n"
                "- url: string (from metadata)\n"
                "- problem_statement: string or null (specific problem from chunks/metadata)\n"
                "- motivation: string or null (why important, query-tied)\n"
                "- approach: string or null (methods from chunks, query-relevant)\n"
                "- experiments_and_evaluation: string or null (datasets/metrics from chunks)\n"
                "- results_and_key_findings: array of 3-5 unique strings (bullets with metrics/impacts, query-specific e.g., 'Achieved 92% accuracy for stock forecasting')\n"
                "- limitations_and_future_work: array of 2-4 unique strings (distinct gaps/futures from chunks, no generics like 'future work needed')\n"
                "- reusability_practical_value: string or null (1-2 paragraphs on applications/value for query domain, e.g., 'Reusable for real-time trading tools')\n"
                "Vary phrasing per paper; use real examples/numbers/sentences from chunks/metadata. Set to null/empty array if absent. No extra text."
            )
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": user}],
                max_tokens=800,
                temperature=0.2,  # Low for factual
                timeout=timeout
            )
            
            summary_json_str = response.choices[0].message.content.strip()
            # Parse and validate JSON (keep your existing validation if present)
            try:
                final_summary = json.loads(summary_json_str)
                if JSONSCHEMA_AVAILABLE:  # If you have schema validation
                    validate(instance=final_summary, schema=self.summary_schema)  # Assume schema exists
                return final_summary
            except (json.JSONDecodeError, ValidationError) as e:
                print(f"[FullPaperSummarizer] JSON parse/validation error: {e}")
                return None
        
        except Exception as e:
            print(f"[FullPaperSummarizer] Composition error: {e}")
            return None

    def _call_openai_on_abstract(self, meta: Dict[str, Any], timeout: int = 60, query: str = "") -> Optional[Dict[str, Any]]:
        """
        Use LLM to summarize abstract only, with query context.
        Returns structured JSON or None.
        """
        abstract = meta.get('abstract', '')
        if not abstract or not self.openai_enabled:
            return None
        
        try:
            user = (
                f"QUERY: Relate to '{query or 'general research'}' (e.g., emphasize stock prediction relevance).\n\n"
                f"PAPER: Title: {meta.get('title')}, Authors: {', '.join(meta.get('authors', []))}, Year: {meta.get('year')}\n"
                f"Abstract: {abstract}\n\n"
                "Summarize in JSON: Use same keys as _compose_final_summary_from_chunks (title/authors/etc., problem_statement, etc.). "
                "Extract directly from abstract; vary fields with query ties. JSON only."
            )
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": user}],
                max_tokens=600,
                temperature=0.3,
                timeout=timeout
            )
            
            json_str = response.choices[0].message.content.strip()
            summary = json.loads(json_str)
            return summary
        
        except Exception as e:
            print(f"[FullPaperSummarizer] Abstract LLM error: {e}")
            return None

    # Validation
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

    # Conservative fallback if LLM not available or fails
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
        
        return {
            'title': title,
            'abstract': abstract,
            'authors': meta.get('authors', []),
            'year': meta.get('year'),
            'domain': self._infer_domain(abstract, query),  # Assume you have _infer_domain or use 'AI/ML'
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
     
