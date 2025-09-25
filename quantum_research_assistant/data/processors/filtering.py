"""
Advanced Paper Filtering System
"""

import streamlit as st
import re
from datetime import datetime

def filter_papers_safe(papers, search_query, source_filter, year_filter, venue_filter=None):
    """
    Advanced filtering system with multiple criteria
    
    Args:
        papers: List of paper dictionaries
        search_query: Search string for title/abstract/authors
        source_filter: Source filter (All, Arxiv, etc.)
        year_filter: Year filter (All, 2023, etc.)
        venue_filter: Optional venue filter
    
    Returns:
        List of filtered papers
    """
    try:
        filtered_papers = papers.copy()
        
        # Search filter - comprehensive text search
        if search_query and search_query.strip():
            filtered_papers = apply_search_filter(filtered_papers, search_query.strip())
        
        # Source filter
        if source_filter and source_filter != "All":
            filtered_papers = apply_source_filter(filtered_papers, source_filter)
        
        # Year filter
        if year_filter and year_filter != "All":
            filtered_papers = apply_year_filter(filtered_papers, year_filter)
        
        # Venue filter (optional)
        if venue_filter and venue_filter != "All":
            filtered_papers = apply_venue_filter(filtered_papers, venue_filter)
        
        return filtered_papers
        
    except Exception as e:
        st.error(f"Filtering error: {str(e)}")
        return papers[:20]  # Return first 20 as fallback

def apply_search_filter(papers, search_query):
    """Apply comprehensive search filtering"""
    search_terms = search_query.lower().split()
    filtered = []
    
    for paper in papers:
        try:
            # Searchable text fields
            searchable_text = []
            
            # Title
            title = str(paper.get('title', '')).lower()
            searchable_text.append(title)
            
            # Abstract
            abstract = str(paper.get('abstract', '')).lower()
            searchable_text.append(abstract)
            
            # Authors
            authors = paper.get('authors', []) or []
            author_text = ' '.join([str(author).lower() for author in authors if author])
            searchable_text.append(author_text)
            
            # Venue
            venue = str(paper.get('venue', '')).lower()
            searchable_text.append(venue)
            
            # Keywords (if available)
            keywords = paper.get('keywords', []) or []
            keyword_text = ' '.join([str(kw).lower() for kw in keywords if kw])
            searchable_text.append(keyword_text)
            
            # Combine all searchable text
            combined_text = ' '.join(searchable_text)
            
            # Check if all search terms are present
            match_score = 0
            for term in search_terms:
                if term in combined_text:
                    match_score += 1
            
            # Include paper if at least 70% of search terms match
            match_threshold = max(1, len(search_terms) * 0.7)
            if match_score >= match_threshold:
                # Add relevance score for sorting
                paper['_relevance_score'] = match_score / len(search_terms)
                filtered.append(paper)
                
        except Exception:
            continue  # Skip paper on error
    
    # Sort by relevance score if search was applied
    if search_terms:
        filtered.sort(key=lambda p: p.get('_relevance_score', 0), reverse=True)
    
    return filtered

def apply_source_filter(papers, source_filter):
    """Apply source filtering"""
    filtered = []
    
    # Normalize source filter
    source_filter_normalized = source_filter.lower().replace(' ', '_')
    
    for paper in papers:
        try:
            paper_source = str(paper.get('source', '')).lower().replace('_', ' ')
            
            # Handle different source name formats
            if source_filter.lower() in paper_source or source_filter_normalized == paper.get('source', ''):
                filtered.append(paper)
            elif source_filter.lower() == 'arxiv' and 'arxiv' in paper_source:
                filtered.append(paper)
            elif source_filter.lower() == 'google scholar' and 'google' in paper_source:
                filtered.append(paper)
            elif source_filter.lower() == 'semantic scholar' and 'semantic' in paper_source:
                filtered.append(paper)
                
        except Exception:
            continue
    
    return filtered

def apply_year_filter(papers, year_filter):
    """Apply year filtering"""
    filtered = []
    
    try:
        target_year = int(year_filter)
    except ValueError:
        return papers  # Invalid year filter
    
    for paper in papers:
        try:
            paper_year = paper.get('year')
            
            if paper_year and str(paper_year).isdigit():
                if int(paper_year) == target_year:
                    filtered.append(paper)
            elif paper_year == year_filter:  # String match as fallback
                filtered.append(paper)
                
        except Exception:
            continue
    
    return filtered

def apply_venue_filter(papers, venue_filter):
    """Apply venue filtering"""
    filtered = []
    
    for paper in papers:
        try:
            venue = str(paper.get('venue', '')).lower()
            
            if venue_filter.lower() in venue:
                filtered.append(paper)
                
        except Exception:
            continue
    
    return filtered

def get_filter_options(papers):
    """Extract available filter options from papers"""
    options = {
        'sources': set(),
        'years': set(),
        'venues': set()
    }
    
    for paper in papers:
        try:
            # Sources
            source = str(paper.get('source', 'unknown')).replace('_', ' ').title()
            if source and source != 'Unknown':
                options['sources'].add(source)
            
            # Years
            year = paper.get('year')
            if year and str(year).isdigit():
                options['years'].add(str(year))
            
            # Venues
            venue = str(paper.get('venue', ''))
            if venue and len(venue) > 3:
                # Truncate very long venue names
                venue_short = venue[:50] + '...' if len(venue) > 50 else venue
                options['venues'].add(venue_short)
                
        except Exception:
            continue
    
    return {
        'sources': sorted(list(options['sources'])),
        'years': sorted(list(options['years']), reverse=True),
        'venues': sorted(list(options['venues']))
    }

def apply_advanced_filters(papers, filters):
    """
    Apply advanced filtering with multiple criteria
    
    Args:
        papers: List of papers
        filters: Dictionary of filter criteria
    
    Returns:
        Filtered papers list
    """
    filtered = papers.copy()
    
    # Citation count range
    if filters.get('min_citations'):
        filtered = [p for p in filtered 
                   if (p.get('citation_count', 0) or 0) >= filters['min_citations']]
    
    if filters.get('max_citations'):
        filtered = [p for p in filtered 
                   if (p.get('citation_count', 0) or 0) <= filters['max_citations']]
    
    # Date range
    if filters.get('start_year'):
        filtered = [p for p in filtered 
                   if p.get('year') and int(str(p['year'])) >= filters['start_year']]
    
    if filters.get('end_year'):
        filtered = [p for p in filtered 
                   if p.get('year') and int(str(p['year'])) <= filters['end_year']]
    
    # Has PDF
    if filters.get('has_pdf'):
        filtered = [p for p in filtered 
                   if p.get('pdf_url') or (p.get('links', {}) or {}).get('pdf')]
    
    # Has abstract
    if filters.get('has_abstract'):
        filtered = [p for p in filtered 
                   if p.get('abstract') and len(str(p['abstract'])) > 50]
    
    return filtered

def sort_papers(papers, sort_by='relevance', ascending=False):
    """
    Sort papers by various criteria
    
    Args:
        papers: List of papers
        sort_by: Sorting criteria (relevance, year, citations, title)
        ascending: Sort order
    
    Returns:
        Sorted papers list
    """
    try:
        if sort_by == 'relevance':
            # Sort by relevance score if available, otherwise by citations
            papers.sort(
                key=lambda p: p.get('_relevance_score', p.get('citation_count', 0) or 0),
                reverse=not ascending
            )
        elif sort_by == 'year':
            papers.sort(
                key=lambda p: int(str(p.get('year', 0))) if p.get('year') else 0,
                reverse=not ascending
            )
        elif sort_by == 'citations':
            papers.sort(
                key=lambda p: p.get('citation_count', 0) or 0,
                reverse=not ascending
            )
        elif sort_by == 'title':
            papers.sort(
                key=lambda p: str(p.get('title', '')).lower(),
                reverse=not ascending
            )
        elif sort_by == 'authors':
            papers.sort(
                key=lambda p: str(p.get('authors', [''])[0]).lower() if p.get('authors') else 'zzz',
                reverse=not ascending
            )
        
        return papers
        
    except Exception as e:
        st.warning(f"Sorting error: {str(e)}")
        return papers

def create_filter_summary(papers, original_count, filters):
    """Create a summary of applied filters"""
    summary = {
        'original_count': original_count,
        'filtered_count': len(papers),
        'reduction_percentage': ((original_count - len(papers)) / original_count * 100) if original_count > 0 else 0,
        'active_filters': []
    }
    
    # Track active filters
    if filters.get('search'):
        summary['active_filters'].append(f"Search: '{filters['search']}'")
    
    if filters.get('source') != 'All':
        summary['active_filters'].append(f"Source: {filters['source']}")
    
    if filters.get('year') != 'All':
        summary['active_filters'].append(f"Year: {filters['year']}")
    
    if filters.get('venue') != 'All':
        summary['active_filters'].append(f"Venue: {filters['venue']}")
    
    return summary