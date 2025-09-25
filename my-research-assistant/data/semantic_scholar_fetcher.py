"""
Optimized Semantic Scholar fetcher for faster paper collection
"""
import requests
import time
import json
from typing import List, Dict, Optional
from datetime import datetime
import logging
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import (
    SEMANTIC_SCHOLAR_BASE_URL, DEFAULT_MAX_PAPERS, PAPERS_DIR
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SemanticScholarFetcher:
    """
    Optimized Semantic Scholar fetcher for faster processing
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.base_url = SEMANTIC_SCHOLAR_BASE_URL
        self.api_key = api_key
        self.rate_limit_delay = 0.3  # Reduced to 0.3 seconds for speed
        self.last_request_time = 0
        
        self.headers = {
            'User-Agent': 'Academic-Research-Assistant/1.0',
            'Accept': 'application/json'
        }
        if api_key:
            self.headers['x-api-key'] = api_key
    
    def _rate_limit(self):
        """Enforce minimal rate limiting for speed"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    def search_papers(
        self,
        query: str,
        max_results: int = DEFAULT_MAX_PAPERS,
        fields: List[str] = None
    ) -> List[Dict]:
        """
        Search for papers on Semantic Scholar with optimized processing
        """
        if fields is None:
            # Reduced field set for faster processing
            fields = [
                'paperId', 'title', 'abstract', 'authors', 'year', 'venue',
                'citationCount', 'publicationDate', 'url'
            ]
        
        logger.info(f"Searching Semantic Scholar for: {query}")
        
        papers = []
        offset = 0
        limit = min(100, max_results)
        max_attempts = 3  # Limit retry attempts for speed
        
        try:
            attempts = 0
            while len(papers) < max_results and attempts < max_attempts:
                self._rate_limit()
                
                params = {
                    'query': query,
                    'offset': offset,
                    'limit': limit,
                    'fields': ','.join(fields)
                }
                
                url = f"{self.base_url}/paper/search"
                
                try:
                    response = requests.get(
                        url, 
                        headers=self.headers, 
                        params=params,
                        timeout=10  # Add timeout for faster failure
                    )
                    
                    if response.status_code == 429:  # Rate limited
                        logger.warning("Rate limited by Semantic Scholar. Waiting...")
                        time.sleep(2)  # Short wait
                        attempts += 1
                        continue
                    
                    if response.status_code != 200:
                        logger.error(f"API request failed with status {response.status_code}")
                        break
                    
                    data = response.json()
                    batch_papers = data.get('data', [])
                    
                    if not batch_papers:
                        break
                    
                    for paper in batch_papers:
                        processed_paper = self._process_paper(paper)
                        papers.append(processed_paper)
                        
                        if len(papers) >= max_results:
                            break
                    
                    offset += limit
                    
                    # Progress update
                    if len(papers) % 10 == 0:
                        logger.info(f"Fetched {len(papers)} papers so far...")
                    
                    if len(batch_papers) < limit:
                        break
                        
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Request error: {str(e)}")
                    attempts += 1
                    continue
        
        except Exception as e:
            logger.error(f"Error fetching papers from Semantic Scholar: {str(e)}")
        
        logger.info(f"Successfully fetched {len(papers)} papers from Semantic Scholar")
        return papers[:max_results]
    
    def _process_paper(self, paper_data: Dict) -> Dict:
        """Process and normalize paper data from Semantic Scholar - optimized"""
        # Quick author processing
        authors = []
        for author in paper_data.get('authors', [])[:10]:  # Limit to 10 authors for speed
            if isinstance(author, dict):
                authors.append(author.get('name', 'Unknown'))
            else:
                authors.append(str(author))
        
        # Quick external IDs processing
        external_ids = paper_data.get('externalIds', {}) or {}
        
        processed_paper = {
            'id': paper_data.get('paperId', ''),
            'semantic_scholar_id': paper_data.get('paperId', ''),
            'title': paper_data.get('title', ''),
            'abstract': paper_data.get('abstract', ''),
            'authors': authors,
            'year': paper_data.get('year'),
            'publication_date': paper_data.get('publicationDate', ''),
            'venue': paper_data.get('venue', ''),
            'citation_count': paper_data.get('citationCount', 0),
            'url': paper_data.get('url', ''),
            'doi': external_ids.get('DOI', ''),
            'arxiv_id': external_ids.get('ArXiv', ''),
            'source': 'semantic_scholar'
        }
        
        return processed_paper
    
    def save_papers(self, papers: List[Dict], filename: str = None) -> str:
        """Save papers to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"semantic_scholar_papers_{timestamp}.json"
        
        filepath = PAPERS_DIR / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(papers, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(papers)} papers to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error saving papers: {str(e)}")
            raise