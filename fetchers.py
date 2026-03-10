import streamlit as st
import time
import requests
import io
import random
from typing import List, Dict, Optional
from datetime import datetime
import concurrent.futures
from urllib.parse import urljoin

from utils import deduplicate_papers

# Robust import for Streamlit utility (varies by version)
try:
    from streamlit.runtime.scriptrunner import add_script_run_context
except ImportError:
    try:
        from streamlit.runtime.script_run_context import add_script_run_context
    except ImportError:
        try:
            from streamlit.scriptrunner import add_script_run_context
        except ImportError:
            add_script_run_context = None


# Try to import optional libraries
try:
    import arxiv
    ARXIV_AVAILABLE = True
except ImportError:
    ARXIV_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False

try:
    from PyPDF2 import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


# ==================== INTELLIGENT PAPER ACCESS DETECTOR ====================
class IntelligentPaperAccessor:
    """Intelligently detects and accesses papers from various sources"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def check_and_extract_paper_content(self, paper: Dict) -> Dict:
        paper = paper.copy()
        access_methods = []
        pdf_url = paper.get('pdf_url')
        if pdf_url:
            access_methods.append(('direct_pdf', pdf_url))
        paper_url = paper.get('url', '')
        if paper_url:
            access_methods.append(('paper_landing', paper_url))  # For indirect links
        semantic_id = paper.get('semantic_scholar_id')
        if semantic_id:
            access_methods.append(('semantic_alternative', f"https://www.semanticscholar.org/paper/{semantic_id}"))
        doi = paper.get('doi', '')
        if doi:
            access_methods.append(('doi_pdf', f"https://doi.org/{doi}"))  # DOI resolver
        extracted_content = None
        working_url = None
        access_type = None
        for method_name, url in access_methods:
            try:
                content = self.try_extract_content(url, method_name)
                if content and len(content) > 200:
                    extracted_content = content[:3000]  # Your length limit
                    working_url = url
                    access_type = method_name
                    break
            except:
                continue
        if extracted_content:
            paper['extracted_content'] = extracted_content
            paper['working_url'] = working_url
            paper['access_type'] = access_type
            paper['pdf_available'] = True
        return paper

    def try_extract_content(self, url: str, method_name: str) -> Optional[str]:
        try:
            response = self.session.get(url, timeout=10, allow_redirects=True)
            if response.status_code != 200:
                return None
            content_type = response.headers.get('Content-Type', '').lower()
            if 'application/pdf' in content_type:
                content_len = len(response.content)
                if content_len < 500 * 1024:  # Small PDF limit
                    if PYPDF_AVAILABLE:
                        try:
                            reader = PdfReader(io.BytesIO(response.content))
                            text = ''
                            for page in reader.pages[:5]:
                                text += (page.extract_text() or '') + '\n'
                            text = text.strip()[:4000]
                            if len(text) > 200:
                                return text
                        except Exception:
                            pass
                    return f"PDF content available ({content_len / 1024:.0f} KB) - Install pypdf for extraction: pip install pypdf"
                return f"PDF content available for download ({content_len / 1024:.0f} KB)"
            elif 'text/html' in content_type:
                if not BEAUTIFULSOUP_AVAILABLE:
                    return "HTML content (install BeautifulSoup for scraping: pip install beautifulsoup4)"
                soup = BeautifulSoup(response.content, 'html.parser')
                for tag in soup(['script', 'style']):
                    tag.decompose()
                pdf_links = []
                cues = ['pdf', 'download', 'full text', 'access pdf', 'view pdf']
                for a in soup.find_all('a', href=True, limit=20):
                    href = a['href'].lower()
                    text = a.get_text(strip=True).lower()
                    if href.endswith('.pdf') or any(cue in href or cue in text for cue in cues) or 'doi.org' in href:
                        full_href = urljoin(url, a['href'])
                        pdf_links.append(full_href)
                        if len(pdf_links) >= 3:
                            break
                for candidate in pdf_links:
                    try:
                        cand_resp = self.session.get(candidate, timeout=8, allow_redirects=True)
                        if cand_resp.status_code == 200 and 'application/pdf' in cand_resp.headers.get('Content-Type', ''):
                            content_len = len(cand_resp.content)
                            if content_len < 500 * 1024:
                                if PYPDF_AVAILABLE:
                                    try:
                                        reader = PdfReader(io.BytesIO(cand_resp.content))
                                        text = ''
                                        for page in reader.pages[:5]:
                                            text += (page.extract_text() or '') + '\n'
                                        text = text.strip()[:4000]
                                        if len(text) > 200:
                                            return text
                                    except Exception:
                                        pass
                                return f"Indirect PDF found ({content_len / 1024:.0f} KB) - Install pypdf for extraction"
                            return f"Indirect PDF accessed via {method_name} ({content_len / 1024:.0f} KB)"
                    except:
                        continue
                # Fallback HTML extraction
                main_content = soup.find('main') or soup.find('article') or soup.body
                if main_content:
                    text = main_content.get_text(separator=' ', strip=True)[:3000]
                    if len(text) > 200:
                        return text
                return soup.get_text(separator=' ', strip=True)[:2000]
            return None
        except requests.exceptions.Timeout:
            return "Timeout accessing content"
        except Exception:
            return None

# ==================== REAL ARXIV FETCHER (SAME AS BEFORE) ====================
class ArxivFetcher:
    """REAL ArXiv fetcher using arxiv-py library"""
    
    def __init__(self):
        self.rate_limit_delay = 0.5
        self.last_request_time = 0.0
    
    def _rate_limit(self):
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    def search_papers(self, query: str, max_results: int = 50) -> List[Dict]:
        if not ARXIV_AVAILABLE:
            return []
        
        try:
            search_query = f"all:{query}"
            
            search = arxiv.Search(
                query=search_query,
                max_results=min(max_results, 100),
                sort_by=arxiv.SortCriterion.Relevance,
                sort_order=arxiv.SortOrder.Descending
            )
            
            papers = []
            count = 0
            
            for result in arxiv.Client().results(search):
                if count % 10 == 0:
                    self._rate_limit()
                
                paper = {
                    'id': result.entry_id,
                    'arxiv_id': result.entry_id.split('/')[-1],
                    'title': result.title,
                    'abstract': result.summary[:1000] if result.summary else '',
                    'authors': [author.name for author in result.authors],
                    'published_date': result.published.isoformat(),
                    'updated_date': result.updated.isoformat(),
                    'year': int(result.published.year) if result.published else int(datetime.now().year),
                    'month': result.published.month,
                    'categories': result.categories,
                    'primary_category': result.primary_category,
                    'url': result.entry_id,
                    'pdf_url': result.pdf_url,
                    'doi': result.doi,
                    'journal_ref': result.journal_ref,
                    'source': 'arXiv',
                    'citations': None,
                    'pdf_available': True,
                    'full_text': True
                }
                
                papers.append(paper)
                count += 1
                
                if count >= max_results:
                    break
            
            return papers
            
        except Exception as e:
            st.warning(f"ArXiv fetch error: {str(e)}")
            return []

# ==================== SEMANTIC SCHOLAR FETCHER WITH API KEY ====================
class SemanticScholarFetcher:
    """Semantic Scholar fetcher using your FREE API key - No rate limiting issues!"""
    
    def __init__(self):
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.api_key = None
        
        # Try to get API key from Streamlit secrets or environment
        try:
            if "SEMANTIC_SCHOLAR_API_KEY" in st.secrets:
                self.api_key = st.secrets["SEMANTIC_SCHOLAR_API_KEY"]
        except (FileNotFoundError, AttributeError):
            pass

        if not self.api_key:
            import os
            self.api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY") or "DiHAxNAV2Q9BrBDSeGK2W3r5dqegv4S86gdaD70Z"

        # API rate limit: 1 request per second
        self.rate_limit_delay = 1.0  # Exactly 1 second per request
        self.last_request_time = 0.0
        self.max_retries = 3  # Standard retries
    
    def _rate_limit(self):
        """Enforce 1 request/second rate limit with small jitter"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last + random.uniform(0.1, 0.3)  # Jitter for safety
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def search_papers(self, query: str, max_results: int = 50) -> List[Dict]:
        """Full search using API key - Reliable and unlimited within rate limits"""
        
        if not query:
            return []
        
        # Use full max_results (no artificial limits)
        max_results = min(max_results, 100)  # API allows up to 100
        
        for attempt in range(self.max_retries):
            try:
                self._rate_limit()  # 1 second delay
                
                search_url = f"{self.base_url}/paper/search"
                params = {
                    'query': query,
                    'limit': max_results,
                    'fields': 'paperId,title,abstract,authors,year,citationCount,url,venue,openAccessPdf,externalIds,isOpenAccess'
                }
                
                headers = {
                    'User-Agent': 'Research Assistant (B.Tech Project)',
                    'Accept': 'application/json'
                }
                if self.api_key:
                    headers['x-api-key'] = self.api_key

                response = requests.get(search_url, params=params, headers=headers, timeout=30)
                
                # Handle API responses
                if response.status_code == 429:
                    wait_time = 2 + (attempt * 2)  # Short backoff for rate limit
                    st.warning(f"**Semantic Scholar API**: Rate limited! Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                elif response.status_code != 200:
                    if response.status_code in [401, 403] and self.api_key:
                        st.warning("Semantic Scholar API Key rejected. Retrying without authentication...")
                        self.api_key = None # Clear key and try one more time
                        continue
                        
                    if attempt == self.max_retries - 1:
                        st.error(f"**Semantic Scholar API**: Failed (Status {response.status_code}). Check internet.")
                        return []
                    continue
                
                # Success
                data = response.json()
                papers = []
                
                for paper_data in data.get('data', []):
                    if not paper_data.get('title'):
                        continue
                    
                    authors = [author.get('name', 'Unknown') for author in paper_data.get('authors', [])[:5]]
                    
                    # PDF and open access detection
                    pdf_url = None
                    pdf_available = False
                    is_open_access = paper_data.get('isOpenAccess', False)
                    
                    open_access_pdf = paper_data.get('openAccessPdf')
                    if open_access_pdf and open_access_pdf.get('url'):
                        pdf_url = open_access_pdf['url']
                        pdf_available = True
                    
                    # External IDs for alternative access
                    external_ids = paper_data.get('externalIds', {})
                    arxiv_id = external_ids.get('ArXiv')
                    doi = external_ids.get('DOI')
                    
                    paper_id = paper_data.get('paperId', '')
                    url = f"https://www.semanticscholar.org/paper/{paper_id}" if paper_id else ''
                    
                    alternative_urls = []
                    if arxiv_id:
                        alternative_urls.append(f"https://arxiv.org/abs/{arxiv_id}")
                        if not pdf_url:
                            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                            pdf_available = True
                    if doi:
                        alternative_urls.append(f"https://doi.org/{doi}")
                    
                    paper = {
                        'id': paper_id,
                        'semantic_scholar_id': paper_id,
                        'title': paper_data.get('title', ''),
                        'abstract': paper_data.get('abstract', '')[:1000] if paper_data.get('abstract') else '',
                        'authors': authors,
                        'year': int(paper_data.get('year') or datetime.now().year),
                        'citations': int(paper_data.get('citationCount') or 0),
                        'url': url,
                        'pdf_url': pdf_url,
                        'alternative_urls': alternative_urls,
                        'venue': paper_data.get('venue', ''),
                        'source': 'Semantic Scholar (API)',
                        'pdf_available': pdf_available,
                        'full_text': pdf_available or is_open_access,
                        'arxiv_id': arxiv_id,
                        'doi': doi,
                        'is_open_access': is_open_access
                    }
                    
                    papers.append(paper)
                
                # Sort by year (recent first)
                papers.sort(key=lambda x: x.get('year') or 0, reverse=True)
                
                if not papers:
                    st.info("**Semantic Scholar API**: No papers found for this query")
                
                return papers
                
            except requests.exceptions.Timeout:
                st.warning(f"**Semantic Scholar API**: Timeout on attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 * (attempt + 1))
                continue
            
            except Exception as e:
                st.error(f"**Semantic Scholar API**: Error - {str(e)}")
                break
        
        # Fallback if all fails
        st.warning("**Semantic Scholar API**: Search failed. Check internet/API key.")
        return []

# ==================== INTELLIGENT MULTI-SOURCE FETCHER ====================
class IntelligentMultiSourceFetcher:
    """Multi-source paper fetcher with intelligent access detection"""
    
    def __init__(self):
        self.fetchers = {
            'arxiv': ArxivFetcher(),
            'semantic_scholar': SemanticScholarFetcher()
        }
        self.accessor = IntelligentPaperAccessor()
    
    def fetch_papers(self, query: str, sources: List[str], papers_per_source: int) -> List[Dict]:
        """Fetch papers with intelligent access detection"""
        all_papers = []
        source_results = {}
        
        # --- FIX: PARALLEL FETCHING ---
        # We define a helper function to run a single fetcher
        def run_fetcher(source_name):
            if add_script_run_context:
                add_script_run_context()
                
            if source_name not in self.fetchers:
                return source_name, [], 0.0
            
            start = time.time()
            fetcher = self.fetchers[source_name]
            # Run the search
            found_papers = fetcher.search_papers(query, papers_per_source)
            
            # Tag the papers
            display_name = source_name.replace('_', ' ').title()
            for p in found_papers:
                p['source'] = display_name
                p['fetch_source'] = source_name
                
            duration = time.time() - start
            return source_name, found_papers, duration
    
        # Execute fetchers in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(sources)) as executor:
            # Fix Streamlit threading context
            futures = {}
            for src in sources:
                f = executor.submit(run_fetcher, src)
                futures[f] = src
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    src_name, papers_list, duration = future.result()
                    
                    if papers_list:
                        all_papers.extend(papers_list)
                        source_results[src_name] = len(papers_list)
                        
                        # Display result immediately
                        display_name = src_name.replace('_', ' ').title()
                        st.success(f"**{display_name}**: {len(papers_list)} papers in {duration:.1f}s")
                    else:
                        source_results[src_name] = 0
                        display_name = src_name.replace('_', ' ').title()
                        st.warning(f"**{display_name}**: No papers found")
                except Exception as e:
                    st.error(f"Fetcher error: {e}")
        # -----------------------------

        # Phase 2: Parallel Intelligent access detection (Keep your existing Phase 2 code)
        if all_papers:
            st.write("2️⃣ **Access Check:** Verifying which papers have downloadable PDFs...")
            
            processed_papers = []
            accessible_count = 0
            extracted_count = 0
            
            progress_bar = st.progress(0)
            status_text = st.empty()

            def check_paper(paper):
                if add_script_run_context:
                    add_script_run_context()
                return self.accessor.check_and_extract_paper_content(paper)

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                future_to_paper = {}
                for p in all_papers:
                    f = executor.submit(check_paper, p)
                    future_to_paper[f] = p
                total_papers = len(all_papers)
                completed = 0

                for future in concurrent.futures.as_completed(future_to_paper):
                    enhanced_paper = future.result()
                    processed_papers.append(enhanced_paper)
                    
                    if enhanced_paper.get('extracted_content'):
                        extracted_count += 1
                    if enhanced_paper.get('pdf_available') or enhanced_paper.get('working_url'):
                        accessible_count += 1
                        
                    completed += 1
                    progress_bar.progress(completed / total_papers)
                    status_text.text(f"Analyzing access: {completed}/{total_papers} papers...")

            progress_bar.empty()
            status_text.empty()
            st.markdown(f"""
            <div class="extraction-status">
            <strong> Analysis Complete:</strong><br>
            Total Papers: {len(processed_papers)}<br>
            Accessible Papers: {accessible_count}<br>
            Content Extracted: {extracted_count}
            </div>
            """, unsafe_allow_html=True)
            
            all_papers = processed_papers

        # Phase 3: Deduplication
        unique_papers = deduplicate_papers(all_papers)
        unique_papers.sort(key=lambda x: (x.get('year', 0), x.get('month', 0)), reverse=True)
        
        self._show_source_breakdown(source_results, len(all_papers), len(unique_papers))
        
        return unique_papers
    
    def _show_source_breakdown(self, source_results: Dict, total_before: int, total_after: int):
        """Show detailed source breakdown"""        
        duplicates_removed = total_before - total_after
        st.info(f"**Final Summary:** {total_before} papers fetched, {total_after} unique papers (removed {duplicates_removed} duplicates)")
