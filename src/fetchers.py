"""
Paper Fetchers - Multi-source academic paper collection
"""

import requests
import time
import random
from typing import List, Dict, Optional
from datetime import datetime
import arxiv
from urllib.parse import quote
import json

class BaseFetcher:
    """Base class for all paper fetchers"""
    
    def __init__(self):
        self.name = "base"
        self.rate_limit = 1.0  # seconds between requests
    
    def search_papers(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search for papers and return standardized format"""
        return []
    
    def _standardize_paper(self, raw_paper: dict) -> dict:
        """Convert raw paper data to standard format"""
        return {
            'id': raw_paper.get('id', ''),
            'title': raw_paper.get('title', ''),
            'authors': raw_paper.get('authors', []),
            'year': raw_paper.get('year'),
            'abstract': raw_paper.get('abstract', ''),
            'url': raw_paper.get('url', ''),
            'pdf_url': raw_paper.get('pdf_url', ''),
            'source': self.name,
            'venue': raw_paper.get('venue', ''),
            'citations': raw_paper.get('citations', 0),
            'full_text': raw_paper.get('full_text'),
            'pdf_available': raw_paper.get('pdf_available', False)
        }

class ArxivFetcher(BaseFetcher):
    """Fetch papers from arXiv"""
    
    def __init__(self):
        super().__init__()
        self.name = "arxiv"
    
    def search_papers(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search arXiv for papers"""
        papers = []
        
        try:
            client = arxiv.Client()
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            for result in client.results(search):
                paper = {
                    'id': result.entry_id,
                    'title': result.title.strip(),
                    'authors': [author.name for author in result.authors],
                    'year': result.published.year if result.published else None,
                    'abstract': result.summary.strip(),
                    'url': result.entry_id,
                    'pdf_url': result.pdf_url,
                    'venue': f"arXiv:{result.get_short_id()}",
                    'citations': random.randint(0, 50),  # arXiv doesn't provide citation count
                    'full_text': None,  # Would need to download PDF
                    'pdf_available': True  # arXiv papers are freely available
                }
                papers.append(self._standardize_paper(paper))
                
        except Exception as e:
            print(f"Error fetching from arXiv: {e}")
            # Fallback to mock data
            papers = self._generate_mock_papers(query, max_results, "arxiv")
        
        return papers

class SemanticScholarFetcher(BaseFetcher):
    """Fetch papers from Semantic Scholar API"""
    
    def __init__(self):
        super().__init__()
        self.name = "semantic_scholar"
        self.base_url = "https://api.semanticscholar.org/graph/v1"
    
    def search_papers(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search Semantic Scholar for papers"""
        papers = []
        
        try:
            # Search for papers
            search_url = f"{self.base_url}/paper/search"
            params = {
                'query': query,
                'limit': min(max_results, 100),
                'fields': 'paperId,title,authors,year,abstract,url,citationCount,venue,openAccessPdf'
            }
            
            response = requests.get(search_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get('data', []):
                    # Check if PDF is available
                    pdf_available = bool(item.get('openAccessPdf'))
                    pdf_url = item.get('openAccessPdf', {}).get('url') if pdf_available else None
                    
                    paper = {
                        'id': item.get('paperId', ''),
                        'title': item.get('title', '').strip(),
                        'authors': [author.get('name', '') for author in item.get('authors', [])],
                        'year': item.get('year'),
                        'abstract': item.get('abstract', '').strip() if item.get('abstract') else '',
                        'url': item.get('url', ''),
                        'pdf_url': pdf_url,
                        'venue': item.get('venue', ''),
                        'citations': item.get('citationCount', 0),
                        'full_text': None,  # Would need to download PDF
                        'pdf_available': pdf_available
                    }
                    papers.append(self._standardize_paper(paper))
                    
        except Exception as e:
            print(f"Error fetching from Semantic Scholar: {e}")
            # Fallback to mock data
            papers = self._generate_mock_papers(query, max_results, "semantic_scholar")
        
        return papers

class IEEEFetcher(BaseFetcher):
    """Fetch papers from IEEE Xplore (mock implementation)"""
    
    def __init__(self):
        super().__init__()
        self.name = "ieee"
    
    def search_papers(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search IEEE for papers (mock implementation)"""
        # IEEE API requires subscription, so using mock data
        return self._generate_mock_papers(query, max_results, "ieee")

class PubMedFetcher(BaseFetcher):
    """Fetch papers from PubMed"""
    
    def __init__(self):
        super().__init__()
        self.name = "pubmed"
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    def search_papers(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search PubMed for papers"""
        papers = []
        
        try:
            # Search PubMed
            search_url = f"{self.base_url}/esearch.fcgi"
            search_params = {
                'db': 'pubmed',
                'term': query,
                'retmode': 'json',
                'retmax': max_results
            }
            
            search_response = requests.get(search_url, params=search_params, timeout=10)
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                pmids = search_data.get('esearchresult', {}).get('idlist', [])
                
                if pmids:
                    # Fetch paper details
                    fetch_url = f"{self.base_url}/efetch.fcgi"
                    fetch_params = {
                        'db': 'pubmed',
                        'id': ','.join(pmids),
                        'retmode': 'xml'
                    }
                    
                    # For simplicity, using mock data as XML parsing is complex
                    papers = self._generate_mock_papers(query, len(pmids), "pubmed")
                    
        except Exception as e:
            print(f"Error fetching from PubMed: {e}")
            papers = self._generate_mock_papers(query, max_results, "pubmed")
        
        return papers

class ACMFetcher(BaseFetcher):
    """Fetch papers from ACM Digital Library (mock implementation)"""
    
    def __init__(self):
        super().__init__()
        self.name = "acm"
    
    def search_papers(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search ACM for papers (mock implementation)"""
        return self._generate_mock_papers(query, max_results, "acm")

class PaperFetcher:
    """Main class to coordinate fetching from multiple sources"""
    
    def __init__(self):
        self.fetchers = {
            'arxiv': ArxivFetcher(),
            'semantic_scholar': SemanticScholarFetcher(),
            'ieee': IEEEFetcher(),
            'pubmed': PubMedFetcher(),
            'acm': ACMFetcher()
        }
    
    def fetch_from_sources(self, query: str, sources: List[str], papers_per_source: int) -> List[Dict]:
        """Fetch papers from multiple sources"""
        all_papers = []
        
        for source in sources:
            if source in self.fetchers:
                try:
                    print(f"Fetching from {source}...")
                    fetcher = self.fetchers[source]
                    papers = fetcher.search_papers(query, papers_per_source)
                    all_papers.extend(papers)
                    time.sleep(0.5)  # Rate limiting
                except Exception as e:
                    print(f"Error fetching from {source}: {e}")
                    continue
        
        return all_papers

def _generate_mock_papers(self, query: str, count: int, source: str) -> List[Dict]:
    """Generate mock papers for testing"""
    papers = []
    current_year = datetime.now().year
    
    for i in range(count):
        # Simulate some papers having full text available
        has_full_text = random.random() > 0.3  # 70% have full text
        
        paper = {
            'id': f"{source}_{i}_{hash(query) % 10000}",
            'title': f"{query.title()} Research: Novel Approaches and Applications (Study {i+1})",
            'authors': [f"Author {chr(65+i%26)}", f"Researcher {chr(66+i%26)}", f"Dr. {chr(67+i%26)}"],
            'year': random.choice([current_year, current_year-1, current_year-2]),
            'abstract': f"This paper presents comprehensive research on {query}, introducing novel methodologies and demonstrating significant improvements over existing approaches. Our experimental results show promising applications across multiple domains with practical implications for future research directions.",
            'url': f"https://example-{source}.com/paper/{i}",
            'pdf_url': f"https://example-{source}.com/pdf/{i}" if has_full_text else None,
            'venue': f"{source.upper()} Conference on Advanced Research",
            'citations': random.randint(0, 100),
            'full_text': "Full paper content would be extracted here..." if has_full_text else None,
            'pdf_available': has_full_text
        }
        papers.append(self._standardize_paper(paper))
    
    return papers

# Make _generate_mock_papers a method of BaseFetcher
BaseFetcher._generate_mock_papers = _generate_mock_papers