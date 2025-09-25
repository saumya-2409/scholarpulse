"""
Session State Management
"""

import streamlit as st
from datetime import datetime
import uuid

def initialize_session_state():
    """Initialize all session state variables"""
    
    # Core data
    if 'papers_data' not in st.session_state:
        st.session_state.papers_data = []
    
    if 'embeddings' not in st.session_state:
        st.session_state.embeddings = None
        
    if 'clusters' not in st.session_state:
        st.session_state.clusters = {}
        
    if 'gap_analyses' not in st.session_state:
        st.session_state.gap_analyses = {}
        
    if 'reading_order' not in st.session_state:
        st.session_state.reading_order = []
    
    # UI state
    if 'selected_page' not in st.session_state:
        st.session_state.selected_page = 'hub'
        
    if 'paper_filters' not in st.session_state:
        st.session_state.paper_filters = {
            'search': '',
            'source': 'All',
            'year': 'All'
        }
    
    # Analysis state
    if 'analysis_running' not in st.session_state:
        st.session_state.analysis_running = False
        
    if 'analysis_progress' not in st.session_state:
        st.session_state.analysis_progress = 0
        
    if 'analysis_step' not in st.session_state:
        st.session_state.analysis_step = 'Ready'
    
    # Session metadata
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        
    if 'session_started' not in st.session_state:
        st.session_state.session_started = datetime.now()
        
    if 'last_analysis' not in st.session_state:
        st.session_state.last_analysis = None

def get_session_stats():
    """Get current session statistics"""
    return {
        'papers': len(st.session_state.papers_data),
        'clusters': len(st.session_state.clusters),
        'analyses': len(st.session_state.gap_analyses),
        'embeddings': st.session_state.embeddings is not None,
        'reading_order': len(st.session_state.reading_order),
        'session_duration': (datetime.now() - st.session_state.session_started).total_seconds() / 3600
    }

def has_active_analysis():
    """Check if there's an active analysis"""
    return len(st.session_state.papers_data) > 0

def clear_analysis_data():
    """Clear all analysis data"""
    st.session_state.papers_data = []
    st.session_state.embeddings = None
    st.session_state.clusters = {}
    st.session_state.gap_analyses = {}
    st.session_state.reading_order = []
    st.session_state.analysis_running = False
    st.session_state.analysis_progress = 0

def save_analysis_config(config):
    """Save analysis configuration"""
    st.session_state.last_analysis_config = {
        **config,
        'timestamp': datetime.now(),
        'session_id': st.session_state.session_id
    }

def get_last_analysis_config():
    """Get last analysis configuration"""
    return st.session_state.get('last_analysis_config', None)

def update_papers_data(papers):
    """Update papers data"""
    st.session_state.papers_data = papers
    st.session_state.last_analysis = datetime.now()

def update_embeddings(embeddings):
    """Update embeddings data"""
    st.session_state.embeddings = embeddings

def update_clusters(clusters):
    """Update clusters data"""
    st.session_state.clusters = clusters

def update_gap_analyses(analyses):
    """Update gap analyses"""
    st.session_state.gap_analyses = analyses

def update_reading_order(reading_order):
    """Update reading order"""
    st.session_state.reading_order = reading_order

def get_papers_data():
    """Get current papers data"""
    return st.session_state.papers_data

def get_embeddings():
    """Get current embeddings"""
    return st.session_state.embeddings

def get_clusters():
    """Get current clusters"""
    return st.session_state.clusters

def get_gap_analyses():
    """Get current gap analyses"""
    return st.session_state.gap_analyses

def get_reading_order():
    """Get current reading order"""
    return st.session_state.reading_order

def set_analysis_progress(progress, step):
    """Set analysis progress"""
    st.session_state.analysis_progress = progress
    st.session_state.analysis_step = step

def set_analysis_running(running):
    """Set analysis running state"""
    st.session_state.analysis_running = running