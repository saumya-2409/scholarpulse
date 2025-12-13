"""
fetchers.py

Minimal, production-oriented fetchers for:
  - arXiv (via `arxiv` package)
  - Semantic Scholar (via their public REST Graph API)

This version:
  - Only provides arXiv and Semantic Scholar sources (everything else removed)
  - DOES NOT fabricate data (no random citation counts)
  - Enriches arXiv papers with Semantic Scholar citationCount and openAccessPdf when available
  - Uses a HARD-CODED Semantic Scholar API key (WARNING: insecure; see notes below)
  - Returns standardized paper dicts via BaseFetcher._standardize_paper

Replace SEMANTIC_SCHOLAR_API_KEY value with your actual key if you requested a hard-coded key.
**Security note**: Hardcoding API keys is insecure. Prefer environment variables. Rotate key if it was ever committed.
"""

import time
import requests
from typing import List, Dict
from datetime import datetime
import arxiv  # pip install arxiv

# HARD-CODED API KEY (replace)
# WARNING: hardcoding keys is insecure. Use env vars in production.
SEMANTIC_SCHOLAR_API_KEY = "DiHAxNAV2Q9BrBDSeGK2W3r5dqegv4S86gdaD70Z"

# Semantic Scholar base
SEMANTIC_BASE = "https://api.semanticscholar.org/graph/v1"
SEMANTIC_HEADERS = {"x-api-key": SEMANTIC_SCHOLAR_API_KEY} if SEMANTIC_SCHOLAR_API_KEY else {}

# Base fetcher + utilities
class BaseFetcher:
    """Base class for fetchers returning standardized paper dicts."""
    def __init__(self):
        self.name = "base"
        self.rate_limit = 1.0  # seconds between requests

    def search_papers(self, query: str, max_results: int = 10) -> List[Dict]:
        return []

    def _standardize_paper(self, raw_paper: dict) -> dict:
        """
        Standard paper fields:
          id, title, authors (list), year (int|None), abstract, url, pdf_url,
          source, venue, citations (int|None), full_text (None unless parsed),
          pdf_available (bool), arxiv_id (if available)
        """
        return {
            'id': raw_paper.get('id', ''),
            'title': raw_paper.get('title', ''),
            'authors': raw_paper.get('authors', []),
            'year': raw_paper.get('year') or 0,
            'abstract': raw_paper.get('abstract', ''),
            'url': raw_paper.get('url', ''),
            'pdf_url': raw_paper.get('pdf_url'),
            'source': raw_paper.get('source', self.name),
            'venue': raw_paper.get('venue', ''),
            'citations': raw_paper.get('citations') or 0,
            'full_text': raw_paper.get('full_text', None),
            'pdf_available': bool(raw_paper.get('pdf_url')),
            'arxiv_id': raw_paper.get('arxiv_id')
        }

# arXiv fetcher
class ArxivFetcher(BaseFetcher):
    """Fetch papers from arXiv using the arxiv python package."""
    def __init__(self):
        super().__init__()
        self.name = "arxiv"
        # arXiv is open; rate_limit left at 1s by default to be polite
        self.rate_limit = 1.0
    
    def search_papers(self, query: str, max_results: int = 10) -> List[Dict]:
        papers = []
        try:
            import arxiv  # Local import for safety
        except ImportError:
            print("[ArxivFetcher] arXiv library not available")
            return []
        
        def rewrite_arxiv_query(q):
            import re
            words = [w for w in re.findall(r'\w+', q.lower()) if len(w) > 3]
            if not words:
                return q
            # arXiv search uses:
            #   ti:"title words" AND abs:"abstract words"
            title_part = " ".join(words[:4])
            abstract_part = " AND ".join(words[:4])
            return f'ti:"{title_part}" AND abs:"{abstract_part}"'
        
        try:
            arxiv_q = rewrite_arxiv_query(query)
            max_results = min(max_results, 100)  # Cap to 100 as per request
            batch_size = 25  # Safe batch size for pagination
            offset = 0
            retries = 0
            max_retries = 2  # Per batch
            while len(papers) < max_results and retries < (max_retries * 4):
                remaining = max_results - len(papers)
                current_batch = min(batch_size, remaining)
                search = arxiv.Search(
                    query=arxiv_q,
                    max_results=current_batch,
                    start=offset,  # Pagination offset to fix error
                    sort_by=arxiv.SortCriterion.Relevance
                )
                time.sleep(self.rate_limit)  # Your polite sleep before search
                results = []
                try:
                    results_iter = search.results()
                    for _ in range(current_batch):
                        try:
                            result = next(results_iter)
                            results.append(result)
                        except StopIteration:
                            break  # No more results in batch
                except arxiv.UnexpectedEmptyPageError:
                    print(f"[ArxivFetcher] Empty page at offset {offset}; adjusting (query: {query[:50]}...)")
                    offset += 10  # Skip for sparse results
                    retries += 1
                    time.sleep(2)  # Fixed 2s retry pause (adjustable)
                    continue
                except Exception as page_e:
                    print(f"[ArxivFetcher] Pagination error at offset {offset}: {page_e}")
                    retries += 1
                    offset += current_batch // 2
                    time.sleep(2)
                    continue
                if not results:
                    retries += 1
                    offset += 5
                    time.sleep(2)
                    continue
                batch_count = 0
                for result in results:
                    if len(papers) >= max_results:
                        break
                    arxiv_id = result.get_short_id()
                    pdf_url = getattr(result, "pdf_url", None)
                    if not pdf_url and arxiv_id:
                        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                    paper = {
                        'id': result.entry_id,
                        'title': (result.title or "").strip(),
                        'authors': [a.name for a in (result.authors or [])],
                        'year': result.published.year if result.published else None,
                        'abstract': (result.summary or "").strip(),
                        'url': result.entry_id,
                        'pdf_url': pdf_url,
                        'venue': f"arXiv:{arxiv_id}",
                        'citations': None,  # Enrich next
                        'full_text': None,
                        'pdf_available': bool(pdf_url),
                        'arxiv_id': arxiv_id,
                        'source': "arXiv"
                    }
                    # Your exact enrichment call (with timeout)
                    paper = enrich_with_semanticscholar(paper, 10)
                    papers.append(self._standardize_paper(paper))
                    batch_count += 1
                    time.sleep(self.rate_limit)  # Your per-paper sleep
                offset += len(results)
                retries = 0  # Reset on success
                if len(results) < current_batch:
                    break  # End of papers
                time.sleep(2)  # Batch pause
        except Exception as e:
            print(f"[ArxivFetcher] Error fetching from arXiv: {e}")
            return []
        return papers

# Semantic Scholar fetcher
class SemanticScholarFetcher(BaseFetcher):
    """Fetch papers from Semantic Scholar API (search endpoint)."""
    def __init__(self):
        super().__init__()
        self.name = "semantic_scholar"
        self.base_url = SEMANTIC_BASE
        self.headers = SEMANTIC_HEADERS
        # If you have a key you can raise rate_limit constraints; keep polite defaults
        self.rate_limit = 1.1
        self.max_retries = 3

    def _rate_limit(self):
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit:
            time.sleep(self.rate_limit - time_since_last)
        self.last_request_time = time.time()

    def search_papers(self, query: str, max_results: int = 50) -> List[Dict]:
        """Full search using Semantic Scholar API (robust, fault-tolerant)."""
        import streamlit as st
        import requests

        if not query:
            st.warning("Empty query provided to Semantic Scholar.")
            return []

        max_results = min(max_results, 100)
        all_papers = []

        # safety: check API key
        if not self.api_key:
            st.error("Semantic Scholar API key missing. Please set SEMANTIC_SCHOLAR_API_KEY.")
            return []

        for attempt in range(self.max_retries):
            try:
                self._rate_limit()

                params = {
                    "query": query,
                    "limit": max_results,
                    "fields": "paperId,title,abstract,authors,year,citationCount,url,venue,openAccessPdf,externalIds,isOpenAccess"
                }

                # Use headers defined in __init__ or global
                headers = self.headers
                if not headers.get("x-api-key"):
                    headers = {
                        "User-Agent": "Research Assistant (Educational)",
                        "Accept": "application/json",
                    }

                response = requests.get(
                    f"{self.base_url}/paper/search",
                    params=params,
                    headers=headers,
                    timeout=20,
                )

                # Handle non-200 responses
                if response.status_code == 429:
                    wait_time = 2 + attempt
                    st.warning(f"Rate limit hit waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                if response.status_code >= 500:
                    st.warning("Semantic Scholar server error retrying...")
                    time.sleep(2)
                    continue
                if response.status_code != 200:
                    st.error(f"Semantic Scholar failed (status {response.status_code})")
                    return []

                data = response.json()
                raw_papers = data.get("data", [])
                if not raw_papers:
                    st.info("No papers returned from Semantic Scholar.")
                    return []

                for p in raw_papers:
                    # Basic fields with fallbacks
                    paper_id = p.get("paperId", "")
                    title = p.get("title") or "Untitled Paper"

                    # Basic extraction
                    paper = {
                        "id": paper_id,
                        "semantic_scholar_id": paper_id,
                        "title": title,
                        "abstract": (p.get("abstract") or "")[:3000],
                        "authors": [a.get("name", "Unknown") for a in p.get("authors", [])[:5]],
                        "year": int(p.get("year") or datetime.now().year),
                        "citations": int(p.get("citationCount") or 0),
                        "url": p.get("url") or f"https://www.semanticscholar.org/paper/{paper_id}",
                        "pdf_url": (p.get("openAccessPdf") or {}).get("url"),
                        "venue": p.get("venue", ""),
                        "source": "Semantic Scholar (API)",
                        "pdf_available": bool((p.get("openAccessPdf") or {}).get("url")),
                        "full_text": (p.get("isOpenAccess", False)),
                        "arxiv_id": (p.get("externalIds") or {}).get("ArXiv"),
                        "doi": (p.get("externalIds") or {}).get("DOI"),
                    }
                    all_papers.append(paper)
                return all_papers
            
            except Exception as e:
                time.sleep(1)
                
        return []

# Enrichment helper (arXiv -> Semantic Scholar)
def enrich_with_semanticscholar(paper: Dict, timeout: int = 10) -> Dict:
    """
    If paper has arxiv_id, try to fetch its semantic scholar record to get citationCount and OA PDF.
    This function is defensive: it will not raise on errors and will leave fields unchanged if no data.
    """
    if not SEMANTIC_SCHOLAR_API_KEY:
        # No key provided: don't attempt enrichment
        return paper

    arxiv_id = paper.get('arxiv_id')
    # Normalize possible "arXiv:xxxx" format from venue
    if not arxiv_id:
        venue = paper.get('venue') or ""
        if isinstance(venue, str) and venue.startswith("arXiv:"):
            arxiv_id = venue.split("arXiv:")[-1]

    if not arxiv_id:
        return paper

    url = f"{SEMANTIC_BASE}/paper/ARXIV:{arxiv_id}"
    params = {'fields': 'citationCount,openAccessPdf,externalIds'}
    try:
        resp = requests.get(url, params=params, headers=SEMANTIC_HEADERS, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            # citationCount may be zero or an int; treat None vs 0 properly
            if 'citationCount' in data:
                paper['citations'] = data.get('citationCount')
            # openAccessPdf may contain url
            oap = data.get('openAccessPdf') or {}
            if oap.get('url'):
                # fill pdf_url only if we don't already have a pdf_url
                if not paper.get('pdf_url'):
                    paper['pdf_url'] = oap.get('url')
                    paper['pdf_available'] = True
        else:
            # in case of 429, consider sleeping in callers; we simply do no enrichment
            if resp.status_code == 429:
                print("[SemanticScholar] Rate limit hit, sleeping 1.5s...")
                # mild backoff; don't block forever
                time.sleep(1.5)
    except Exception:
        # Swallow exceptions and return original paper unchanged
        pass
    return paper

# PaperFetcher orchestrator (only arXiv + Semantic Scholar)
class PaperFetcher:
    """
    Coordinates fetching from the two supported sources: arXiv and Semantic Scholar.
    Usage:
       pf = PaperFetcher()
       papers = pf.fetch_from_sources("transformer interpretability", sources=['arxiv','semantic_scholar'], papers_per_source=10)
    """
    def __init__(self):
        self.fetchers = {
            'arxiv': ArxivFetcher(),
            'semantic_scholar': SemanticScholarFetcher()
        }

    def fetch_from_sources(self, query: str, sources: List[str], papers_per_source: int = 10) -> List[Dict]:
        """
        Query the selected sources and return a combined list of standardized papers.
        This function does not deduplicate; deduplication should be done in a separate utils module.
        """
        all_papers = []
        for src in sources:
            if src not in self.fetchers:
                print(f"[PaperFetcher] Source '{src}' not supported. Skipping.")
                continue
            fetcher = self.fetchers[src]
            try:
                print(f"[PaperFetcher] Fetching {papers_per_source} results from {src} for query: {query}")
                papers = fetcher.search_papers(query, max_results=papers_per_source)
                all_papers.extend(papers)
            except Exception as e:
                print(f"[PaperFetcher] Error fetching from {src}: {e}")
        return all_papers
