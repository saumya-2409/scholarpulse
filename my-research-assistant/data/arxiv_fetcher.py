"""
Optimized arXiv fetcher for faster paper collection
"""
import arxiv
import time
import json
from typing import List, Dict, Optional
from datetime import datetime
import logging
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import (
    DEFAULT_MAX_PAPERS, DEFAULT_ARXIV_CATEGORIES, PAPERS_DIR
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArxivFetcher:
    """
    Optimized arXiv fetcher with faster processing
    """
    
    def __init__(self):
        self.client = arxiv.Client()
        self.rate_limit_delay = 0.5  # Reduced from 2.0 seconds to 0.5 for speed
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Enforce minimal rate limiting for speed"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    def search_papers(
        self, 
        query: str = None,
        categories: List[str] = None,
        max_results: int = DEFAULT_MAX_PAPERS,
        sort_by: str = "submittedDate"
    ) -> List[Dict]:
        """
        Search for papers on arXiv with optimized processing
        """
        logger.info(f"Searching arXiv for papers with query: {query}")
        
        try:
            # Build search query with limited categories for speed
            search_query = self._build_search_query(query, categories or DEFAULT_ARXIV_CATEGORIES[:2])
            
            # Use arxiv-py library with timeout
            search = arxiv.Search(
                query=search_query,
                max_results=min(max_results, 50),  # Limit max for speed
                sort_by=getattr(arxiv.SortCriterion, sort_by, arxiv.SortCriterion.SubmittedDate)
            )
            
            papers = []
            count = 0
            
            for result in self.client.results(search):
                # Minimal rate limiting
                if count % 5 == 0:  # Only rate limit every 5 papers
                    self._rate_limit()
                
                paper_data = {
                    'id': result.entry_id,
                    'arxiv_id': result.entry_id.split('/')[-1],
                    'title': result.title,
                    'abstract': result.summary,
                    'authors': [author.name for author in result.authors],
                    'published_date': result.published.isoformat(),
                    'updated_date': result.updated.isoformat(),
                    'categories': result.categories,
                    'primary_category': result.primary_category,
                    'pdf_url': result.pdf_url,
                    'doi': result.doi,
                    'journal_ref': result.journal_ref,
                    'source': 'arxiv',
                    'year': result.published.year
                }
                papers.append(paper_data)
                count += 1
                
                # Progress update every 10 papers
                if len(papers) % 10 == 0:
                    logger.info(f"Fetched {len(papers)} papers...")
            
            logger.info(f"Successfully fetched {len(papers)} papers from arXiv")
            return papers
            
        except Exception as e:
            logger.error(f"Error fetching papers from arXiv: {str(e)}")
            return []
    
    def _build_search_query(self, query: str, categories: List[str]) -> str:
        """Build optimized arXiv search query string"""
        query_parts = []
        
        # Add text query
        if query:
            # Clean query for better results
            clean_query = query.replace("'", "").replace('"', '')
            query_parts.append(f"all:{clean_query}")
        
        # Add limited categories for speed (max 2)
        if categories:
            limited_cats = categories[:2]  # Limit to 2 categories for speed
            category_query = " OR ".join([f"cat:{cat}" for cat in limited_cats])
            query_parts.append(f"({category_query})")
        
        # Combine with AND
        final_query = " AND ".join(query_parts)
        logger.info(f"Built search query: {final_query}")
        return final_query
    
    def save_papers(self, papers: List[Dict], filename: str = None) -> str:
        """Save papers to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"arxiv_papers_{timestamp}.json"
        
        filepath = PAPERS_DIR / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(papers, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(papers)} papers to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error saving papers: {str(e)}")
            raise