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

# ----------------------------
# HARD-CODED API KEY (replace)
# ----------------------------
# WARNING: hardcoding keys is insecure. Use env vars in production.
SEMANTIC_SCHOLAR_API_KEY = "REPLACE_WITH_YOUR_HARDCODED_KEY"

# Semantic Scholar base
SEMANTIC_BASE = "https://api.semanticscholar.org/graph/v1"
SEMANTIC_HEADERS = {"x-api-key": SEMANTIC_SCHOLAR_API_KEY} if SEMANTIC_SCHOLAR_API_KEY else {}

# ----------------------------
# Base fetcher + utilities
# ----------------------------
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
            'year': raw_paper.get('year'),
            'abstract': raw_paper.get('abstract', ''),
            'url': raw_paper.get('url', ''),
            'pdf_url': raw_paper.get('pdf_url'),
            'source': raw_paper.get('source', self.name),
            'venue': raw_paper.get('venue', ''),
            'citations': raw_paper.get('citations', None),
            'full_text': raw_paper.get('full_text', None),
            'pdf_available': bool(raw_paper.get('pdf_url')),
            'arxiv_id': raw_paper.get('arxiv_id')
        }

# ----------------------------
# arXiv fetcher
# ----------------------------
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
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )
            for result in search.results():
                # Build canonical metadata; DO NOT fabricate citations
                arxiv_id = result.get_short_id()
                paper = {
                    'id': result.entry_id,
                    'title': (result.title or "").strip(),
                    'authors': [a.name for a in (result.authors or [])],
                    'year': result.published.year if result.published else None,
                    'abstract': (result.summary or "").strip(),
                    'url': result.entry_id,
                    'pdf_url': getattr(result, "pdf_url", None),
                    'venue': f"arXiv:{arxiv_id}",
                    'citations': None,     # Unknown here; will be enriched if possible
                    'full_text': None,     # Only set if you parse the PDF separately
                    'pdf_available': bool(getattr(result, "pdf_url", None)),
                    'arxiv_id': arxiv_id,
                    'source': "arXiv"
                }
                # Enrich with Semantic Scholar if possible (try, but do not fail if unreachable)
                paper = enrich_with_semanticscholar(paper)
                papers.append(self._standardize_paper(paper))
                time.sleep(self.rate_limit)  # be polite to arXiv API
        except Exception as e:
            # On error, return empty list (do NOT fabricate or return mock results)
            print(f"[ArxivFetcher] Error fetching from arXiv: {e}")
            return []
        return papers

# ----------------------------
# Semantic Scholar fetcher
# ----------------------------
class SemanticScholarFetcher(BaseFetcher):
    """Fetch papers from Semantic Scholar API (search endpoint)."""
    def __init__(self):
        super().__init__()
        self.name = "semantic_scholar"
        self.base_url = SEMANTIC_BASE
        self.headers = SEMANTIC_HEADERS
        # If you have a key you can raise rate_limit constraints; keep polite defaults
        self.rate_limit = 1.0

    def search_papers(self, query: str, max_results: int = 10) -> List[Dict]:
        papers = []
        try:
            search_url = f"{self.base_url}/paper/search"
            params = {
                'query': query,
                'limit': min(max_results, 100),
                # Request the key fields we need
                'fields': 'paperId,title,authors,year,abstract,url,citationCount,venue,openAccessPdf,externalIds'
            }
            resp = requests.get(search_url, params=params, headers=self.headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get('data', []):
                    pdf_available = bool(item.get('openAccessPdf'))
                    pdf_url = item.get('openAccessPdf', {}).get('url') if pdf_available else None
                    paper = {
                        'id': item.get('paperId', ''),
                        'title': (item.get('title') or "").strip(),
                        'authors': [a.get('name', '') for a in item.get('authors', [])] if item.get('authors') else [],
                        'year': item.get('year'),
                        'abstract': (item.get('abstract') or "").strip() if item.get('abstract') else '',
                        'url': item.get('url') or '',
                        'pdf_url': pdf_url,
                        'venue': item.get('venue') or '',
                        'citations': item.get('citationCount') if item.get('citationCount') is not None else None,
                        'full_text': None,
                        'pdf_available': pdf_available,
                        # Try to derive arXiv id if present in externalIds
                        'arxiv_id': None,
                        'source': "SemanticScholar"
                    }
                    ext = item.get('externalIds') or {}
                    # externalIds may contain "ARXIV"
                    if isinstance(ext, dict):
                        arx = ext.get('ARXIV') or ext.get('ArXiv')
                        if arx:
                            paper['arxiv_id'] = str(arx).strip()
                    papers.append(self._standardize_paper(paper))
                    time.sleep(self.rate_limit)
            else:
                print(f"[SemanticScholarFetcher] Non-200 status {resp.status_code}: {resp.text[:200]}")
                return []
        except Exception as e:
            print(f"[SemanticScholarFetcher] Error fetching from Semantic Scholar: {e}")
            return []
        return papers

# ----------------------------
# Enrichment helper (arXiv -> Semantic Scholar)
# ----------------------------
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
                # mild backoff; don't block forever
                time.sleep(1.0)
    except Exception:
        # Swallow exceptions and return original paper unchanged
        pass
    return paper

# ----------------------------
# PaperFetcher orchestrator (only arXiv + Semantic Scholar)
# ----------------------------
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
