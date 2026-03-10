import os
import json
import time
import tempfile
import requests
import re
import logging
from typing import Dict, Any, Optional, Tuple
from groq import Groq, RateLimitError
import streamlit as st

# Setup logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

# Text extraction
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    logger.warning("PyPDF2 missing - PDF extraction will fail.")

# --- CONFIGURATION ---
# We use llama-3.1-8b-instant for speed.
MODEL_NAME = "llama-3.1-8b-instant" 

# Groq Free Tier Limit = 6,000 Tokens/min. 
# We reduce MAX_CONTEXT_CHARS further to leave more room for the output generation.
MAX_CONTEXT_CHARS = 12000  

# ---------- Strict Output Schema Template ----------
STRICT_SCHEMA_TEMPLATE = {
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
def _try_fix_common_json_issues(s: str) -> str:
    """Small repairs to common model-produced JSON issues."""
    if not s:
        return s
    s = s.replace('\u201c', '"').replace('\u201d', '"').replace('\u2018', "'").replace('\u2019', "'")
    s = re.sub(r'^[^\{]*\{', '{', s, count=1)
    s = re.sub(r',(\s*[\}\]])', r'\1', s)
    return s

def _parse_json_with_repair(raw: str) -> Optional[Dict[str, Any]]:
    """Extract + repair JSON and return parsed object or None."""
    if not raw:
        return None
    
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    start = raw.find('{')
    end = raw.rfind('}')
    if start != -1 and end != -1:
        candidate = raw[start:end+1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
        
        repaired = _try_fix_common_json_issues(candidate)
        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            pass

    return None

def _fill_strict_schema(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure parsed dict contains EXACT keys and types."""
    out = {}
    for k in ["Title", "Research_Problem", "Research_Objective", "Aim_of_Study", "limitations_and_future_work"]:
        val = parsed.get(k) if isinstance(parsed, dict) else None
        out[k] = val if isinstance(val, str) and val.strip() else ""
        
    for k in ["Keywords", "Key_Findings"]:
        val = parsed.get(k) if isinstance(parsed, dict) else None
        if isinstance(val, list):
            out[k] = [str(x) for x in val]
        else:
            out[k] = []

    mma = parsed.get("Methodology_Approach") if isinstance(parsed, dict) else None
    out["Methodology_Approach"] = {}
    for sk in ["Method", "Process", "Data_Handling", "Results_Format"]:
        sv = mma.get(sk) if isinstance(mma, dict) else None
        out["Methodology_Approach"][sk] = sv if isinstance(sv, str) and sv.strip() else ""
        
    return out

# ---------- Main class ----------
class FullPaperSummarizer:
    _instance = None 

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.api_key = None
        try:
            if "GROQ_API_KEY" in st.secrets:
                self.api_key = st.secrets["GROQ_API_KEY"]
        except (FileNotFoundError, AttributeError):
            pass 
        
        if not self.api_key:
            self.api_key = os.getenv("GROQ_API_KEY")

        if not self.api_key:
            logger.error("GROQ_API_KEY not found!")
            self.client = None
        else:
            self.client = Groq(api_key=self.api_key)
            logger.info(f"[Init] Groq Client initialized with model: {MODEL_NAME}")

    def _groq_call(self, prompt: str) -> str:
        """Call Groq API with robust Rate Limit handling."""
        if not self.client:
            logger.error("Groq client not initialized.")
            return ""

        max_retries = 3
        attempt = 0

        while attempt < max_retries:
            try:
                completion = self.client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are a research assistant. Output strictly valid JSON."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    temperature=0.1, 
                    max_tokens=4000, 
                    response_format={"type": "json_object"}
                )
                return completion.choices[0].message.content.strip()

            except RateLimitError as e:
                error_msg = str(e)
                wait_time = 5 
                match = re.search(r"try again in (\d+\.?\d*)s", error_msg)
                if match:
                    wait_time = float(match.group(1)) + 1.0 
                
                logger.warning(f"Rate limit hit. Waiting {wait_time:.2f}s...")
                time.sleep(wait_time)
                attempt += 1

            except Exception as e:
                # Catch 413 (Payload Too Large) specifically
                if "413" in str(e) or "Request too large" in str(e):
                    logger.error("Request exceeded Groq context limit. Trying to truncate further.")
                    return "CONTEXT_ERROR"
                logger.error(f"Groq API call failed: {e}")
                return ""
        
        return ""

    def _generate_strict_summary(self, text_content: str, meta: Dict[str, Any], query: str, content_label: str = "Abstract") -> Optional[Dict[str, Any]]:
        if not text_content.strip():
            return None

        # Hard truncation to prevent 413 errors
        truncated_text = text_content[:MAX_CONTEXT_CHARS]
        
        # If text is extremely long, we try to take the first half and last half 
        # to capture Intro + Conclusion, which is better than just the first half.
        if len(text_content) > MAX_CONTEXT_CHARS:
             half_limit = int(MAX_CONTEXT_CHARS / 2)
             truncated_text = text_content[:half_limit] + "\n\n...[content skipped]...\n\n" + text_content[-half_limit:]

        prompt = f"""
        Analyze the following academic paper content ({content_label}) and extract specific details into JSON.
        
        CONTEXT:
        Title: {meta.get('title', 'Unknown')}
        Query: {query}

        TEXT ({content_label}):
        {truncated_text}

        INSTRUCTIONS:
        1. Return ONLY a single valid JSON object.
        2. "Methodology_Approach" must include Method, Process, Data_Handling, Results_Format.
        3. Provide a CONCISE, SHARP summary in "Research_Problem" and "Key_Findings". Keep each finding under 2 sentences.
        4. If the content is insufficient, provide a brief placeholder.
        
        REQUIRED JSON SCHEMA:
        {{
            "Title": "Paper Title",
            "Keywords": ["k1", "k2"],
            "Research_Problem": "Detailed problem statement...",
            "Research_Objective": "Main objective...",
            "Methodology_Approach": {{
                "Method": "...",
                "Process": "...",
                "Data_Handling": "...",
                "Results_Format": "..."
            }},
            "Aim_of_Study": "...",
            "Key_Findings": ["Detailed finding 1", "Detailed finding 2"],
            "limitations_and_future_work": "..."
        }}
        """

        raw = self._groq_call(prompt)
        
        if raw == "CONTEXT_ERROR":
            # Emergency fallback: Try with just the abstract if full text failed strictly
            logger.warning("Full text failed due to size. Retrying with abstract only.")
            return self._generate_strict_summary(meta.get('abstract',''), meta, query, "Abstract Fallback")

        parsed = _parse_json_with_repair(raw)
        
        if not parsed:
            return _fill_strict_schema({}) 

        return _fill_strict_schema(parsed)
    
    def _is_summary_useful(self, summary: Dict[str, Any]) -> bool:
        if not summary:
            return False
        has_problem = bool(summary.get("Research_Problem", "").strip())
        has_findings = bool(summary.get("Key_Findings") and len(summary["Key_Findings"]) > 0)
        return has_problem or has_findings

    def summarize_paper(self, paper: Dict[str, Any], use_full_text: bool = True, query: str = "") -> Dict[str, Any]:
        logger.info(f"[Summarizing] {paper.get('title', '')[:50]}")
        
        if paper.get("accessibility") == "inaccessible":
            return {"accessibility": "inaccessible", "abstract_summary_status": "inaccessible"}

        meta = {
            "title": paper.get("title", "").strip(),
            "abstract": paper.get("abstract", "").strip(),
            "source": paper.get("source", "")
        }

        extracted_text = None
        if use_full_text and PYPDF2_AVAILABLE and paper.get('pdf_url'):
            extracted_text, is_paywalled = self._download_and_extract_pdf(paper['pdf_url'])
            
            if extracted_text:
                logger.info(f"[Full Text] Extracted {len(extracted_text)} chars. Processing...")
                full_summary = self._generate_strict_summary(extracted_text, meta, query, "Full Text")
                
                if full_summary and self._is_summary_useful(full_summary):
                    full_summary['accessibility'] = "accessible"
                    full_summary['abstract_summary_status'] = "generated_from_fulltext"
                    return full_summary

        logger.info("[Abstract] Summarizing abstract.")
        abstract_summary = self._generate_strict_summary(meta.get('abstract', ''), meta, query, "Abstract")
        
        if abstract_summary and self._is_summary_useful(abstract_summary):
            abstract_summary['accessibility'] = "accessible"
            abstract_summary['abstract_summary_status'] = "generated_from_abstract"
            return abstract_summary

        return {
            "accessibility": "inaccessible",
            "abstract_summary_status": "api_failure"
        }

    def _download_and_extract_pdf(self, pdf_url: str) -> Tuple[Optional[str], bool]:
        if not PYPDF2_AVAILABLE:
             return None, False

        try:
            resp = requests.get(pdf_url, timeout=20)
            if resp.status_code != 200 or not resp.content.startswith(b"%PDF"):
                return None, True 

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(resp.content)
                tmp = f.name
            
            text = ""
            with open(tmp, "rb") as fh:
                reader = PyPDF2.PdfReader(fh)
                # Limit pages to avoid wasting time processing data we will delete anyway
                for page in reader.pages[:30]: 
                    text += (page.extract_text() or "") + "\n\n"
            
            try:
                os.unlink(tmp)
            except Exception:
                pass
                
            return text.strip() or None, False
        except Exception as e:
            logger.warning(f"[PDF Extract Fail] {e}")
            return None, True
