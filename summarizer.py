# summarizer.py
"""
Full-paper summarizer using Google Gemini API (free tier):
- Auto-picks available model (e.g., gemini-2.5-flash from logs).
- Robust JSON extraction and repair for Gemini outputs.
- Returns strict schema with "" for missing strings and [] for missing arrays.
"""

import os
import io
import json
import time
import tempfile
import requests
import re
import logging
from typing import Dict, Any, Optional, List, Tuple
import streamlit as st

# Setup logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

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

# Defaults
PREFERRED_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-pro-latest"]
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

# ---------- Strict Gemini output schema template ----------
GEMINI_STRICT_SCHEMA_TEMPLATE = {
    "Title": "",
    "Keywords": [],
    "Research_Problem": "",
    "Research_Objective": "",
    "Methodology_Approach": {
            "Method": "",
            "Process": "",
            "Data_Handling": "",
            "Results_Format": ""
    },
    "Aim_of_Study": "",
    "Key_Findings":[],
    "limitations_and_future_work":""
}

# ---------- Helper: Robust JSON extraction & repair ----------
def _extract_first_json_object(raw: str) -> Optional[str]:
    """Return the first balanced JSON object substring from raw text, or None."""
    if not raw:
        return None
    start = raw.find('{')
    if start == -1:
        return None
    i = start
    depth = 0
    in_string = False
    escape = False
    while i < len(raw):
        ch = raw[i]
        if ch == '"' and not escape:
            in_string = not in_string
        if not in_string:
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return raw[start:i+1]
        if ch == '\\' and not escape:
            escape = True
        else:
            escape = False
        i += 1
    return None

def _try_fix_common_json_issues(s: str) -> str:
    """Small repairs to common model-produced JSON issues."""
    if not s:
        return s
    # normalize smart quotes
    s = s.replace('\u201c', '"').replace('\u201d', '"').replace('\u2018', "'").replace('\u2019', "'")
    # remove any leading non-brace characters up to first {
    s = re.sub(r'^[^\{]*\{', '{', s, count=1)
    # remove trailing commas before } or ]
    s = re.sub(r',(\s*[\}\]])', r'\1', s)
    # remove stray control characters
    s = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', s)
    return s

def _parse_json_with_repair(raw: str) -> Optional[Dict[str, Any]]:
    """Extract + repair JSON and return parsed object or None."""
    if not raw:
        return None
    cleaned = re.sub(r'```+', '', raw).strip()
    candidate = _extract_first_json_object(cleaned)
    if candidate is None:
        # attempt repairs then extract again
        repaired = _try_fix_common_json_issues(cleaned)
        candidate = _extract_first_json_object(repaired)
    if candidate is None:
        return None
    # try parse, then one repair attempt
    try:
        return json.loads(candidate)
    except Exception:
        candidate2 = _try_fix_common_json_issues(candidate)
        try:
            return json.loads(candidate2)
        except Exception:
            return None

def _fill_strict_gemini_schema(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure parsed dict contains EXACT keys and types from GEMINI_STRICT_SCHEMA_TEMPLATE.
    """
    out = {}
    # 1. Top-level string fields
    for k in ["Title", "Research_Problem", "Research_Objective", "Aim_of_Study", "limitations_and_future_work"]:
        val = parsed.get(k) if isinstance(parsed, dict) else None
        out[k] = val if isinstance(val, str) and val.strip() else ""
        
    # 2. Lists (Keywords and Key_Findings)
    for k in ["Keywords", "Key_Findings"]:
        val = parsed.get(k) if isinstance(parsed, dict) else None
        if isinstance(val, list):
            out[k] = [str(x) for x in val]
        else:
            out[k] = []

    # 3. Methodology_Approach nested
    mma = parsed.get("Methodology_Approach") if isinstance(parsed, dict) else None
    out["Methodology_Approach"] = {}
    for sk in ["Method", "Process", "Data_Handling", "Results_Format"]:
        sv = mma.get(sk) if isinstance(mma, dict) else None
        out["Methodology_Approach"][sk] = sv if isinstance(sv, str) and sv.strip() else ""
        
    return out

# ---------- Mapper: Convert Gemini strict schema -> your internal SUMMARY_SCHEMA format ----------
def map_gemini_to_internal(gemini: Dict[str, Any]) -> Dict[str, Any]:
    """Map the strict Gemini schema to the internal SUMMARY structure used by the rest of pipeline."""
    out = {
        "title": gemini.get("Title", "") or "",
        "abstract": "",  # do not fabricate; leave blank
        "authors": [],
        "year": "",
        "domain": "",
        "source": "",
        "url": "",
        "problem_statement": gemini.get("Research_Problem", "") or "",
        "motivation": gemini.get("Research_Objective", "") or "",
        "approach": (gemini.get("Methodology_Approach", {}) or {}).get("Method", "") or "",
        "experiments_and_evaluation": (gemini.get("Methodology_Approach", {}) or {}).get("Process", "") or "",
        "results_and_key_findings": [],  # not present in this schema -> keep empty
        "limitations_and_future_work": [],  # not present -> empty
        "reusability_practical_value": gemini.get("Aim_of_Study", "") or ""
    }
    # Domain inference using keywords/title
    kws = gemini.get("Keywords", []) or []
    if kws:
        # quick heuristic
        if any(k.lower() in ["finance", "stock", "market"] for k in kws):
            out["domain"] = "AI/ML/Finance"
    return out

def detect_paper_type(paper: dict) -> str:
    """
    Detect whether a paper is ABSTRACT_ONLY, FULLTEXT_DIRECT, FULLTEXT_INDIRECT, or UNKNOWN.

    Returns one of:
        - "abstract_only"
        - "fulltext_direct"
        - "fulltext_indirect"
        - "unknown"
    """

    abstract = (paper.get("abstract") or "").strip()
    pdf_url = paper.get("pdf_url")
    extracted = paper.get("extracted_content")
    access_type = paper.get("access_type")

    # 1. If full text already extracted earlier
    if extracted and len(extracted) > 500:
        return "fulltext_direct"

    # 2. If Gemini accessor says we found a PDF or indirect link
    if access_type in ("direct_pdf", "doi_pdf", "semantic_alternative"):
        return "fulltext_direct"

    # 3. If paper has NO pdf_url at all
    if not pdf_url:
        return "abstract_only"

    # 4. If abstract exists but is extremely short (< 50 chars)
    #    Often this means the paper is ABSTRACT-ONLY on S2/arXiv summaries
    if len(abstract) < 50:
        return "abstract_only"

    # 5. If it's an arXiv paper → ALWAYS has full text
    if "arxiv" in paper.get("source", "").lower():
        return "fulltext_direct"

    # 6. If Semantic Scholar says it's not open access and no PDF
    if paper.get("source") == "Semantic Scholar (API)" and not paper.get("pdf_available"):
        return "abstract_only"

    # 7. Last resort — unknown. Attempt full-text only if we confirm PDF signature later.
    return "unknown"

# ---------- Main class ----------
class FullPaperSummarizer:
    _instance = None  # Singleton enforcement (prevents multiple inits)

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, api_key: str = None):
        if hasattr(self, 'initialized'):  # Skip re-init
            return
        self.initialized = True
        self.chunk_size = 20000
        self.overlap = 0
        self.max_chunks = 1
        self.request_delay = 0.5  # Slower for quota
        self.current_model = None
        self.summary_schema = SUMMARY_SCHEMA
        self.pdf_enabled = PYPDF2_AVAILABLE

        # Gemini setup
        self.gemini_model = None
        self.gemini_enabled = False
        self.quota_exceeded = False

        api_key = api_key or st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
        print(f"[Gemini Debug] Key loaded: {'Yes' if api_key else 'No'}")
        print(f"[Gemini Debug] Package: {GEMINI_AVAILABLE}")

        if api_key and GEMINI_AVAILABLE:
            try:
                genai.configure(api_key=api_key)
                available_models = [m.name for m in genai.list_models() if 'gemini' in m.name.lower()]
                print(f"[Gemini Debug] Available models: {available_models[:5]}...")
                if any('2.5-flash' in m for m in available_models):
                    self.current_model = "gemini-2.5-flash"
                else:
                    self.current_model = "gemini-2.5-pro"
                print(f"[Gemini Debug] Selected model: {self.current_model}")
                self.gemini_model = genai.GenerativeModel(self.current_model)
                self.gemini_enabled = True
                print(f"[Summarizer] Enabled with {self.current_model}")
            except Exception as e:
                print(f"[Gemini Debug] Setup failed: {e}")
                self.gemini_enabled = False
    
    # ADD this method to FullPaperSummarizer class (e.g., before summarize_paper)
    def _generate_strict_summary(self, text_content: str, meta: Dict[str, Any], query: str, content_label: str = "Abstract") -> Optional[Dict[str, Any]]:
        """
        Generates a strict JSON summary from either Abstract or Full Text.
        """
        if not text_content.strip():
            return None

        # Limit text length to avoid hitting hard limits (300k chars is approx 75k tokens, safe for Gemini Flash)
        # If content_label is Abstract, we limit to 2500 as per your request.
        limit = 2500 if content_label == "Abstract" else 300000
        truncated_text = text_content[:limit]

        prompt = f"""
            SYSTEM INSTRUCTION: You are an assistant whose ONLY job is to extract structured information and return EXACTLY one JSON object that matches the schema below. DO NOT output anything other than a single valid JSON object (no explanations, no markdown, no code fences, no notes). Use only double quotes for strings. Do NOT add, remove, or rename keys. Maintain the exact casing of keys.

            OUTPUT RULES:
            1) Return EXACTLY one JSON object that conforms to this schema. Do NOT include extra keys or metadata.
            2) If a value cannot be confidently extracted, set string fields to an empty string "" and array fields to an empty array [].
            3) For Methodology_Approach, put the primary method name under "Method", a brief step-by-step summary under "Process", how data is sourced/cleaned under "Data_Handling", and how results are presented under "Results_Format".
            4) If multiple short keywords exist, include them in the "Keywords" array. If none, return [].
            5) Do NOT output trailing commas. Ensure JSON is well-formed and parseable by json.loads.
            6) If you cannot produce valid JSON, still return the required schema with empty values (not an error text).
            7) Keep answers factual and grounded in the provided Title and {content_label}. Use the {content_label} to populate fields; do not hallucinate new experimental details.

            INPUT:
            Query: {query}

            Title: {meta['title']}

            {content_label}: {truncated_text}

            OUTPUT: Return a single JSON object using this exact structure and keys (nothing else):
            {{
                "Title": "",
                "Keywords": [],
                "Research_Problem": "",
                "Research_Objective": "",
                "Methodology_Approach": {{
                    "Method": "",
                    "Process": "",
                    "Data_Handling": "",
                    "Results_Format": ""
                }},
                "Aim_of_Study": "",
                "Key_Findings": [],
                "limitations_and_future_work": ""
            }}
        """
        
        raw = self._gemini_call(prompt)
        meta['_last_raw_gemini'] = (raw or "")[:20000]
        
        if not raw:
            return None

        parsed = _parse_json_with_repair(raw)
        if not parsed:
            logger.warning(f"Failed to parse Gemini response into JSON for {content_label}")
            return _fill_strict_gemini_schema({})

        return _fill_strict_gemini_schema(parsed)
    
    def _is_summary_useful(self, summary: Dict[str, Any]) -> bool:
        """Check if the summary actually contains meaningful content."""
        if not summary:
            return False
        
        # Check if we have at least one core field populated
        has_problem = bool(summary.get("Research_Problem", "").strip())
        has_objective = bool(summary.get("Research_Objective", "").strip())
        has_findings = bool(summary.get("Key_Findings") and len(summary["Key_Findings"]) > 0)
        
        # Or if we have methodology details
        method = summary.get("Methodology_Approach", {})
        has_method = any(bool(v.strip()) for v in method.values())
        
        return has_problem or has_objective or has_findings or has_method

    def summarize_paper(self, paper: Dict[str, Any], use_full_text: bool = True, query: str = "") -> Dict[str, Any]:
        logger.info(f"[Debug] Summarizing: {paper.get('title', '')[:50]}")
        
        #inaccessible paper
        if paper.get("accessibility") == "inaccessible":
            logger.info(f"[Skip] {paper.get('title','')} is marked inaccessible — skipping")
            return None

        meta = self._prepare_meta(paper)
        if not meta:
            return {"summary": "Failed: Invalid metadata"}
        
        paper_type = detect_paper_type(paper)

        # --- Abstract Only Path ---
        if paper_type == "abstract_only":
            logger.info("[AutoDetect] Abstract-only paper detected.")
            abstract_summary = self._generate_strict_summary(meta.get('abstract', ''), meta, query, "Abstract")
            

            # Using method with "Abstract" label
            if abstract_summary and self._is_summary_useful(abstract_summary):
                abstract_summary['accessibility'] = "accessible"
                abstract_summary['abstract_summary_status'] = "generated_from_abstract"
                return abstract_summary
            else:
                # Fallback or failure handling
                return {
                    "title": meta.get("title", ""),
                    "accessibility": "inaccessible",
                    "abstract_summary_status": "api_failure"
                }

        # --- Full Text Path ---
        extracted_text = None
        if use_full_text and self.pdf_enabled and paper.get('pdf_url'):
            extracted_text, is_paywalled = self._download_and_extract_pdf(paper['pdf_url'])
            if is_paywalled:
                logger.info("[Debug] Paywalled PDF")
                extracted_text = None

        # If there's no extracted full text AND the abstract itself is empty -> mark inaccessible
        if not extracted_text and not meta.get('abstract', "").strip():
            # Paper likely not accessible: mark and return minimal info
            meta['accessibility'] = "inaccessible"
            # persist/store meta as you normally would (DB save call if present)
            logger.info(f"[Mark] Paper '{meta.get('title','')}' marked as inaccessible (no abstract / no full text).")
            return {
                "title": meta.get("title", ""),
                "accessibility": "inaccessible",
                "abstract_summary_status": "inaccessible"
            }

        #full extracted text
        # REMOVED: Chunking logic (self._chunk_text, self._chunk_and_summarize...)
        # ADDED: Direct full text summarization
        if extracted_text:
            logger.info(f"[Debug] Sending full text ({len(extracted_text)} chars) to Gemini without chunking.")
            
            # Call the new method with "Full Text" label
            full_summary = self._generate_strict_summary(extracted_text, meta, query, "Full Text")
            
            if full_summary and self._is_summary_useful(full_summary):
                # Check if it actually extracted data (not just empty schema)
                    full_summary['accessibility'] = "accessible"
                    full_summary['abstract_summary_status'] = "generated_from_fulltext"
                    return full_summary
                
        # --- Fallback to Abstract if Full Text failed or was empty ---
        if self.gemini_enabled:
            logger.info("Falling back to abstract summarization.")
            abstract_summary = self._generate_strict_summary(meta.get('abstract', ''), meta, query, "Abstract")
            
            if abstract_summary and self._is_summary_useful(abstract_summary):
                abstract_summary['accessibility'] = "accessible"
                abstract_summary['abstract_summary_status'] = "generated_from_abstract"
                return abstract_summary
        
        # If all fails
        return {
            "accessibility": "inaccessible",
            "abstract_summary_status": "api_failure"
        }
                
    def _gemini_call(self, prompt: str, max_retries: int = 3) -> str:
        """
        Call Gemini model and return raw text. This preserves your existing behaviour:
        - Returns "" on quota exceeded or fatal failures
        - Returns textual output otherwise
        """
        if not self.gemini_enabled:
            logger.warning("[API Failed] No model enabled - Skipping call")
            return ""
        logger.info(f"[Debug] Call with {self.current_model}: {len(prompt)} chars")
        time.sleep(self.request_delay)

        for attempt in range(max_retries):
            try:
                # note: your wrapper currently calls generate_content(prompt)
                response = self.gemini_model.generate_content(prompt)
                if response and getattr(response, "parts", None):
                    text_parts = [getattr(part, "text", "") for part in response.parts if getattr(part, "text", None)]
                    if text_parts:
                        full_text = " ".join(text_parts).strip()
                        if full_text:
                            logger.info("[Debug] Call success (parts parsed)")
                            logger.debug(f"full text (truncated): {full_text[:1000]}")
                            return full_text
                        else:
                            logger.warning(f"[API Failed] Empty text parts (attempt {attempt+1})")
                    else:
                        logger.warning(f"[API Failed] No text in parts (safety/blocked? attempt {attempt+1})")
                elif hasattr(response, 'text') and response.text:
                    return response.text.strip()
                else:
                    raise Exception("No valid response structure")
            except Exception as e:
                error_str = str(e)[:200].lower()
                logger.warning(f"[API Failed] {error_str} (attempt {attempt+1})")
                if "429" in error_str or "quota" in error_str:
                    logger.error("[API Failed] Quota exceeded - Disable for session")
                    self.quota_exceeded = True
                    self.gemini_enabled = False
                    return ""
                elif "blocked" in error_str or "safety" in error_str:
                    logger.error("[API Failed] Prompt blocked - Simplify or switch model")
                    return "Summary blocked by safety filters - Try rephrasing query."
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    logger.error("[API Failed] Max retries exceeded")
                    return ""
        return ""

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
                    text += (page.extract_text() or "") + "\n\n"
                logger.info(f"[Debug] Extracted PDF text length: {len(text)}, preview: {text[:200]}")
                with open(f"extracted_{abs(hash(pdf_url))}.txt", "w", encoding="utf-8") as out_f:
                    out_f.write(text)
                logger.info(f"[Debug] Saved extracted text to extracted_*.txt")
            try:
                os.unlink(tmp)
            except Exception:
                pass
            return text.strip() or None, False
        except Exception as e:
            logger.warning(f"[PDF extraction failed] {e}")
            return None, True

    # ---------- Updated robust _summarize_abstract ----------
    def _summarize_abstract(self, meta: Dict[str, Any], query: str = "") -> Optional[Dict[str, Any]]:
        """
        Returns:
          - Strict Gemini schema dict (keys exactly as GEMINI_STRICT_SCHEMA_TEMPLATE) even if fields empty
          - Returns None only if no API response at all (real failure)
        """
        abstract = meta.get('abstract', '') or ''
        print(f"\nabstract: {abstract}\n")
        logger.info(f"[Debug] Summarize abstract len: {len(abstract)}")
        if not abstract.strip():
            return None

        prompt = f"""
SYSTEM INSTRUCTION: You are an assistant whose ONLY job is to extract structured information and return EXACTLY one JSON object that matches the schema below. DO NOT output anything other than a single valid JSON object (no explanations, no markdown, no code fences, no notes). Use only double quotes for strings. Do NOT add, remove, or rename keys. Maintain the exact casing of keys.

OUTPUT RULES:
1) Return EXACTLY one JSON object that conforms to this schema. Do NOT include extra keys or metadata.
2) If a value cannot be confidently extracted, set string fields to an empty string "" and array fields to an empty array [].
3) For Methodology_Approach, put the primary method name under "Method", a brief step-by-step summary under "Process", how data is sourced/cleaned under "Data_Handling", and how results are presented under "Results_Format".
4) If multiple short keywords exist, include them in the "Keywords" array. If none, return [].
5) Do NOT output trailing commas. Ensure JSON is well-formed and parseable by json.loads.
6) If you cannot produce valid JSON, still return the required schema with empty values (not an error text).
7) Keep answers factual and grounded in the provided Title and Abstract. Use the abstract to populate fields; do not hallucinate new experimental details.

INPUT:
Query: {query}

Title: {meta['title']}

Abstract: {abstract[:2500]}

OUTPUT: Return a single JSON object using this exact structure and keys (nothing else):
{{
    "Title": "",
    "Keywords": [],
    "Research_Problem": "",
    "Research_Objective": "",
    "Methodology_Approach": {{
        "Method": "",
        "Process": "",
        "Data_Handling": "",
        "Results_Format": ""
    }},
    "Aim_of_Study": "",
    "Key_Findings":[],
    "limitations_and_future_work":""
}}
"""

        raw = self._gemini_call(prompt)
        print(f"\nraw: {raw}\n")
        # Save raw for debugging (truncated)
        meta['_last_raw_gemini'] = (raw or "")[:20000]
        if not raw:
            # No response / failure
            return None

        parsed = _parse_json_with_repair(raw)
        if not parsed:
            # Parsed failed -> per your requirement return strict template with empty strings (not None)
            logger.warning("Failed to parse Gemini response into JSON; returning strict empty schema")
            return _fill_strict_gemini_schema({})

        strict = _fill_strict_gemini_schema(parsed)
        return strict

    def _validate_parsed(self, parsed: Dict[str, Any]) -> bool:
        required = ["title", "abstract", "authors", "source", "url", "results_and_key_findings", "limitations_and_future_work"]
        for k in required:
            if k not in parsed:
                return False
        return isinstance(parsed.get("authors"), list) and isinstance(parsed.get("results_and_key_findings"), list)

    def conservative_summary(self, meta: Dict[str, Any], query: str = "") -> Dict[str, Any]:
        return {"summary": "API unavailable"}



# End of summarizer.py