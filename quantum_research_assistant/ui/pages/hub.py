"""
Hub Page - Main Dashboard
"""

import streamlit as st
from ui.components import (
    render_project_summary, render_analysis_running, render_quick_start_card,
    render_knowledge_stream, render_search_interface, render_status_card
)
from data.storage.session_manager import get_session_stats, has_active_analysis
from analysis.pipeline import start_complete_analysis

def render():
    """Render the main hub page"""
    
    # Check if we should start analysis
    if st.session_state.get('start_analysis', False):
        run_analysis()
        return
    
    # Check if analysis is running
    if st.session_state.get('analysis_running', False):
        render_analysis_page()
        return
    
    # Check if we have previous results
    stats = get_session_stats()
    if stats['papers'] > 0:
        render_results_hub(stats)
    else:
        render_welcome_hub()

def render_welcome_hub():
    """Render welcome hub for new users"""
    
    # Welcome message
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="color: var(--primary-color); margin-bottom: 1rem;">Welcome to Quantum Field 🔬</h1>
        <p style="font-size: 1.2rem; color: var(--text-secondary-light);">
            Your advanced academic research assistant powered by AI
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main search interface
    render_search_interface()
    
    # Feature highlights
    st.markdown("---")
    
    st.markdown("""
    <div style="text-align: center; margin: 2rem 0;">
        <h2 style="color: var(--primary-color);">🚀 Powerful Research Features</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="quantum-card" style="text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🔍</div>
            <h3>Multi-Source Search</h3>
            <p>Fetch papers from arXiv, Google Scholar, IEEE, ACM, PubMed, and Semantic Scholar simultaneously.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="quantum-card" style="text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🧠</div>
            <h3>AI Analysis</h3>
            <p>Advanced clustering, gap analysis, and intelligent insights powered by machine learning.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="quantum-card" style="text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
            <h3>Smart Insights</h3>
            <p>Get reading order suggestions, research gaps, and comprehensive analysis reports.</p>
        </div>
        """, unsafe_allow_html=True)

def render_results_hub(stats):
    """Render hub with existing results"""
    
    # Project summary
    render_project_summary()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Status cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        render_analysis_running()
    
    with col2:
        render_quick_start_card()
    
    with col3:
        render_knowledge_stream()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Recent activity
    st.markdown("""
    <div class="quantum-card">
        <h3 style="margin: 0 0 1rem 0; color: var(--primary-color);">📈 Recent Searches</h3>
        <div style="color: var(--text-secondary-light);">
            <div style="padding: 0.5rem 0; border-bottom: 1px solid var(--border-light);">
                Computer & System Architecture → 47 papers found
            </div>
            <div style="padding: 0.5rem 0; color: var(--text-secondary-light);">
                Last analysis: 2 hours ago
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Action buttons
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Start New Research", type="primary", use_container_width=True):
            st.session_state.start_new_analysis = True
            st.rerun()
    
    with col2:
        if st.button("📊 View Analysis", use_container_width=True):
            st.session_state.selected_page = 'overview'
            st.rerun()
    
    with col3:
        if st.button("📄 Browse Papers", use_container_width=True):
            st.session_state.selected_page = 'papers'
            st.rerun()

def render_analysis_page():
    """Render page during analysis"""
    
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="color: var(--primary-color);">⚡ Analysis in Progress</h1>
        <p style="font-size: 1.1rem; color: var(--text-secondary-light);">
            Processing your research query with AI-powered analysis...
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Progress display
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    
    # Show progress
    progress = st.session_state.get('analysis_progress', 0)
    current_step = st.session_state.get('analysis_step', 'Initializing...')
    
    with progress_placeholder:
        st.markdown(f"""
        <div class="quantum-card">
            <div style="text-align: center; margin-bottom: 2rem;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">🔬</div>
                <h2>Processing Research Analysis</h2>
                
                <div class="quantum-progress" style="margin: 2rem auto; max-width: 400px;">
                    <div class="quantum-progress-fill" style="width: {progress}%;"></div>
                </div>
                
                <div style="margin: 1rem 0;">
                    <strong>{current_step}</strong>
                </div>
                
                <div style="color: var(--text-secondary-light);">{progress}% complete</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Analysis steps
    steps = [
        "🔍 Fetching papers from sources",
        "🧠 Generating AI embeddings", 
        "🔬 Clustering related papers",
        "🎯 Analyzing research gaps",
        "📚 Optimizing reading order",
        "✅ Finalizing results"
    ]
    
    with status_placeholder:
        st.markdown("### Analysis Pipeline")
        
        for i, step in enumerate(steps, 1):
            if progress >= (i * 100 / len(steps)):
                st.success(f"{step} ✅")
            elif progress >= ((i-1) * 100 / len(steps)):
                st.info(f"{step} ⏳")
            else:
                st.write(f"{step} ⏸️")
    
    # Cancel button
    if st.button("❌ Cancel Analysis", key="cancel_analysis"):
        st.session_state.analysis_running = False
        st.session_state.start_analysis = False
        st.rerun()

def run_analysis():
    """Run the complete analysis pipeline"""
    
    config = st.session_state.get('analysis_config', {})
    
    if not config:
        st.error("No analysis configuration found")
        return
    
    # Set analysis as running
    st.session_state.analysis_running = True
    st.session_state.start_analysis = False
    
    try:
        # Run analysis pipeline
        success = start_complete_analysis(
            query=config['query'],
            sources=config['sources'],
            max_papers=config['max_papers'],
            cluster_method=config.get('cluster_method', 'kmeans'),
            enable_gap_analysis=config.get('enable_gap_analysis', True),
            enable_reading_order=config.get('enable_reading_order', True),
            progress_callback=update_analysis_progress
        )
        
        if success:
            st.session_state.analysis_running = False
            st.session_state.analysis_complete = True
            st.success("🎉 Analysis completed successfully!")
            st.balloons()
        else:
            st.session_state.analysis_running = False
            st.error("❌ Analysis failed. Please try again.")
            
    except Exception as e:
        st.session_state.analysis_running = False
        st.error(f"Analysis error: {str(e)}")

def update_analysis_progress(step, progress, message):
    """Update analysis progress"""
    st.session_state.analysis_progress = progress
    st.session_state.analysis_step = message
    
    # Force refresh
    if hasattr(st, 'rerun'):
        st.rerun()

# Handle new analysis request
if st.session_state.get('start_new_analysis', False):
    st.session_state.start_new_analysis = False
    st.session_state.clear()  # Clear previous results
    st.rerun()