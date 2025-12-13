"""
Utility functions for paper processing
"""

import hashlib
import requests
import re
from datetime import datetime
from typing import List, Dict, Set
from collections import Counter

# utils.py additions (append to file)

def is_paywalled_response(response: requests.Response) -> bool:
    """
    Heuristic: True if response indicates paywall or HTML content instead of PDF.
    """
    if response.status_code in (401, 403):
        return True
    ctype = response.headers.get("Content-Type", "").lower()
    if "html" in ctype:
        return True
    if "pdf" not in ctype and not response.content.startswith(b"%PDF"):
        return True
    return False

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,;:!?-]', ' ', text)
    
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract important keywords from text"""
    if not text:
        return []
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove common stop words
    stop_words = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
        'after', 'above', 'below', 'between', 'among', 'is', 'are', 'was',
        'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
        'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
        'can', 'shall', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
        'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
    }
    
    # Extract words
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
    
    # Filter stop words and short words
    meaningful_words = [word for word in words if word not in stop_words and len(word) >= 3]
    
    # Count frequency
    word_counts = Counter(meaningful_words)
    
    # Return most common words
    return [word for word, count in word_counts.most_common(max_keywords)]

def categorize_papers(papers: List[Dict]) -> Dict[str, List[Dict]]:
    """Categorize papers by availability of full text"""
    full_text_papers = []
    abstract_only_papers = []
    
    for paper in papers:
        if (paper.get('full_text') or 
            paper.get('pdf_available') or 
            paper.get('pdf_url') or 
            'arxiv' in paper.get('source', '').lower()):
            full_text_papers.append(paper)
        else:
            abstract_only_papers.append(paper)
    
    return {
        'full_text': full_text_papers,
        'abstract_only': abstract_only_papers
    }

def validate_paper_data(paper: Dict) -> Dict:
    """Validate and clean paper data"""
    cleaned_paper = {}
    
    # Required fields with defaults
    cleaned_paper['id'] = str(paper.get('id', ''))
    cleaned_paper['title'] = clean_text(paper.get('title', 'Untitled'))
    cleaned_paper['source'] = paper.get('source', 'unknown')
    
    # Optional fields
    authors = paper.get('authors', [])
    if isinstance(authors, list):
        cleaned_paper['authors'] = [clean_text(str(author)) for author in authors if author]
    else:
        cleaned_paper['authors'] = []
    
    # Year validation
    year = paper.get('year')
    if year and isinstance(year, (int, str)):
        try:
            year_int = int(year)
            if 1900 <= year_int <= 2030:  # Reasonable year range
                cleaned_paper['year'] = year_int
        except (ValueError, TypeError):
            pass
    
    # Clean abstract
    abstract = paper.get('abstract', '')
    if abstract:
        cleaned_paper['abstract'] = clean_text(str(abstract))
    
    # URLs
    for url_field in ['url', 'pdf_url']:
        url = paper.get(url_field)
        if url and isinstance(url, str) and url.startswith(('http://', 'https://')):
            cleaned_paper[url_field] = url
    
    # Venue
    venue = paper.get('venue')
    if venue:
        cleaned_paper['venue'] = clean_text(str(venue))
    
    # Citations (ensure it's a number)
    citations = paper.get('citations', 0)
    try:
        cleaned_paper['citations'] = max(0, int(citations))
    except (ValueError, TypeError):
        cleaned_paper['citations'] = 0
    
    # Boolean fields
    for bool_field in ['pdf_available', 'full_text_available']:
        if bool_field in paper:
            cleaned_paper[bool_field] = bool(paper[bool_field])
    
    # Full text content
    full_text = paper.get('full_text')
    if full_text and len(str(full_text).strip()) > 0:
        cleaned_paper['full_text'] = clean_text(str(full_text))
    
    return cleaned_paper

def format_authors(authors: List[str], max_authors: int = 3) -> str:
    """Format author list for display"""
    if not authors:
        return "Unknown Authors"
    
    clean_authors = [author.strip() for author in authors if author and author.strip()]
    
    if not clean_authors:
        return "Unknown Authors"
    
    if len(clean_authors) <= max_authors:
        return ", ".join(clean_authors)
    else:
        return f"{', '.join(clean_authors[:max_authors])} et al."

def generate_paper_id(paper: Dict) -> str:
    """Generate a unique ID for a paper"""
    title = paper.get('title', '')
    authors = paper.get('authors', [])
    year = paper.get('year', '')
    
    # Create hash from title + first author + year
    id_string = f"{title}_{authors[0] if authors else ''}_{year}"
    return hashlib.md5(id_string.encode()).hexdigest()[:16]

def merge_paper_data(paper1: Dict, paper2: Dict) -> Dict:
    """Merge two paper dictionaries, keeping the most complete information"""
    merged = paper1.copy()
    
    # Merge fields, preferring non-empty values
    for key, value in paper2.items():
        if key not in merged or not merged[key]:
            merged[key] = value
        elif key == 'authors':
            # Merge author lists
            existing_authors = set(merged.get('authors', []))
            new_authors = paper2.get('authors', [])
            all_authors = list(merged.get('authors', []))
            
            for author in new_authors:
                if author not in existing_authors:
                    all_authors.append(author)
            
            merged['authors'] = all_authors
        elif key == 'citations':
            # Keep higher citation count
            merged[key] = max(merged.get(key, 0), value or 0)
        elif key in ['abstract', 'full_text']:
            # Keep longer text
            if len(str(value or '')) > len(str(merged.get(key, ''))):
                merged[key] = value
    
    return merged

def deduplicate_papers(papers: List[Dict]) -> List[Dict]:
    """
    Remove duplicate papers based on normalized title similarity.
    Keeps the version with the highest 'information score'.
    """
    if not papers:
        return []
    
    unique_papers = []
    seen_titles = set()
    
    for paper in papers:
        # Normalize title
        title = paper.get('title', '').lower().strip()
        title_key = re.sub(r'[^\w\s]', '', title)
        title_key = re.sub(r'\s+', ' ', title_key)
        
        if not title_key:
            continue

        if title_key not in seen_titles:
            unique_papers.append(paper)
            seen_titles.add(title_key)
        else:
            # Duplicate found! Decide which to keep.
            _handle_duplicate(unique_papers, paper, title_key)
    
    return unique_papers

def _handle_duplicate(unique_papers, new_paper, title_key):
    """Helper to swap papers if the new one is better."""
    for i, p in enumerate(unique_papers):
        p_title = re.sub(r'[^\w\s]', '', p.get('title', '').lower())
        p_title = re.sub(r'\s+', ' ', p_title)
        if p_title == title_key:
            if _calculate_paper_score(new_paper) > _calculate_paper_score(p):
                unique_papers[i] = new_paper
            break

def _calculate_paper_score(paper: Dict) -> int:
    """Scoring heuristic for paper quality."""
    score = 0
    if paper.get('extracted_content'): score += 50
    if paper.get('pdf_url'): score += 20
    if paper.get('abstract') and len(paper['abstract']) > 100: score += 10
    if paper.get('authors'): score += min(len(paper['authors']), 5)
    if paper.get('year'): score += 5
    return score