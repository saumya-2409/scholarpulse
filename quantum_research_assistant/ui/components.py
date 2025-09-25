"""
Reusable UI Components
"""

import streamlit as st
from config.settings import APP_NAME, APP_TAGLINE, AVAILABLE_SOURCES
from data.storage.session_manager import get_session_stats

def render_header():
    """Render the main application header"""
    st.markdown("""
    <div class="quantum-header">
        <h1>🔬 Quantum Field: Academic Research Assistant</h1>
        <p class="tagline">Unveiling Knowledge, Accelerating Discovery</p>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Render the navigation sidebar"""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0 2rem 0;">
            <h2 style="color: var(--primary-color); margin: 0;">🔬 Hub</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation Menu
        st.markdown("### Navigation")
        
        # Main navigation items
        nav_items = [
            {"key": "hub", "icon": "⭐", "label": "Hub", "desc": "Main dashboard"},
            {"key": "overview", "icon": "📊", "label": "Overview", "desc": "Analysis overview"},
            {"key": "papers", "icon": "📄", "label": "Papers", "desc": "Browse papers"},
            {"key": "reading_order", "icon": "📚", "label": "Reading Order", "desc": "Optimized sequence"},
            {"key": "research_gaps", "icon": "🎯", "label": "Research Gaps", "desc": "Gap analysis"},
            {"key": "export", "icon": "📁", "label": "Export", "desc": "Download results"}
        ]
        
        selected_page = st.session_state.get('selected_page', 'hub')
        
        for item in nav_items:
            if st.button(
                f"{item['icon']} {item['label']}", 
                key=f"nav_{item['key']}",
                help=item['desc'],
                use_container_width=True
            ):
                st.session_state.selected_page = item['key']
                selected_page = item['key']
        
        st.divider()
        
        # Quick Actions
        st.markdown("### Quick Actions")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔖\nBookmarks", key="bookmarks", help="Saved papers"):
                st.info("Feature coming soon!")
        
        with col2:
            if st.button("🔍\nHelp", key="help", help="Get help"):
                show_help_dialog()
        
        st.divider()
        
        # Session Stats
        render_session_stats()
        
        return selected_page

def render_session_stats():
    """Render current session statistics"""
    stats = get_session_stats()
    
    st.markdown("### 📊 Session Stats")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📄 Papers", stats.get('papers', 0))
        st.metric("🔬 Clusters", stats.get('clusters', 0))
    
    with col2:
        st.metric("🧠 Embeddings", "✅" if stats.get('embeddings') else "❌")
        st.metric("🎯 Analyses", stats.get('analyses', 0))

def render_status_card(title, current, previous=None, icon="📊", color="primary"):
    """Render a status card with metrics"""
    color_map = {
        "primary": "var(--primary-color)",
        "secondary": "var(--secondary-color)", 
        "success": "var(--success-color)",
        "warning": "var(--warning-color)",
        "error": "var(--error-color)"
    }
    
    delta_html = ""
    if previous is not None:
        delta = current - previous
        delta_color = "var(--success-color)" if delta >= 0 else "var(--error-color)"
        delta_symbol = "+" if delta >= 0 else ""
        delta_html = f"""
        <div style="color: {delta_color}; font-size: 0.8rem; margin-top: 0.25rem;">
            {delta_symbol}{delta} from last analysis
        </div>
        """
    
    st.markdown(f"""
    <div class="quantum-card status-card" style="background: {color_map[color]};">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <div style="font-size: 0.9rem; opacity: 0.9;">{title}</div>
                <div style="font-size: 2rem; font-weight: 700; margin: 0.25rem 0;">{current}</div>
                {delta_html}
            </div>
            <div style="font-size: 2rem; opacity: 0.7;">{icon}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_progress_card(title, current_step, total_steps, percentage, description=""):
    """Render a progress card"""
    st.markdown(f"""
    <div class="quantum-card">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
            <h3 style="margin: 0;">{title}</h3>
            <span style="font-weight: 600; color: var(--primary-color);">{percentage}%</span>
        </div>
        
        <div class="quantum-progress" style="margin-bottom: 1rem;">
            <div class="quantum-progress-fill" style="width: {percentage}%;"></div>
        </div>
        
        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: var(--text-secondary-light);">
            <span>Phase {current_step}/{total_steps}: {description}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_knowledge_stream():
    """Render the knowledge stream component"""
    st.markdown("""
    <div class="quantum-card knowledge-stream">
        <h3 style="margin: 0 0 1rem 0; color: var(--primary-color);">🧠 Knowledge Stream</h3>
        
        <div class="stream-item">
            <div style="display: flex; align-items: center;">
                <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIGZpbGw9IiM0QTkwRTIiIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJDNi40OCAyIDIgNi40OCAyIDEyczQuNDggMTAgMTAgMTAgMTAtNC40OCAxMC0xMFMxNy41MiAyIDEyIDJ6bTEgMTVoLTJ2LTZoMnY2em0wLThoLTJWN2gybTJ6Ii8+PC9zdmc+" class="stream-avatar" />
                <div>
                    <div style="font-weight: 500;">Anna Novak (like Rousseau)</div>
                    <div style="font-size: 0.85rem; color: var(--text-secondary-light);">AI nunc risus eget maximus ante potentia...</div>
                </div>
            </div>
        </div>
        
        <div class="stream-item">
            <div style="display: flex; align-items: center;">
                <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIGZpbGw9IiM3QjY4RUUiIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJDNi40OCAyIDIgNi40OCAyIDEyczQuNDggMTAgMTAgMTAgMTAtNC40OCAxMC0xMFMxNy41MiAyIDEyIDJ6bTEgMTVoLTJ2LTZoMnY2em0wLThoLTJWN2gybTJ6Ii8+PC9zdmc+" class="stream-avatar" />
                <div>
                    <div style="font-weight: 500;">Whales gyri bittend dune raverat fag und</div>
                    <div style="font-size: 0.85rem; color: var(--text-secondary-light);">Utrum falcilit itsg og na poerition</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_quick_start_card():
    """Render quick start suggestions"""
    st.markdown("""
    <div class="quantum-card">
        <h3 style="margin: 0 0 1rem 0; color: var(--primary-color);">🚀 Quick Start</h3>
        
        <div style="margin: 0.75rem 0;">
            <div style="font-weight: 500; margin-bottom: 0.25rem;">I arters Identiveer</div>
            <div style="font-size: 0.85rem; color: var(--text-secondary-light);">Dulemßion</div>
        </div>
        
        <div style="margin: 0.75rem 0;">
            <div style="font-weight: 500; margin-bottom: 0.25rem;">Cuseniat</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_analysis_running():
    """Render running analysis indicator"""
    st.markdown("""
    <div class="quantum-card" style="background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)); color: white;">
        <h3 style="margin: 0 0 1rem 0;">⚡ Running Analysis...</h3>
        
        <div class="quantum-progress" style="margin: 1rem 0;">
            <div class="quantum-progress-fill" style="width: 37%;"></div>
        </div>
        
        <div style="font-size: 0.9rem; opacity: 0.9;">Phase 3/6: Clustering Papers</div>
    </div>
    """, unsafe_allow_html=True)

def render_project_summary():
    """Render current project summary"""
    stats = get_session_stats()
    
    st.markdown("""
    <div class="quantum-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h3 style="margin: 0;">📋 Current Project / Last Analysis</h3>
            <button class="quantum-btn-secondary" style="font-size: 0.8rem; padding: 0.25rem 0.5rem;">⚙️</button>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin: 1rem 0;">
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div>
            <div style="color: var(--text-secondary-light); font-size: 0.85rem;">Papers Fetched:</div>
            <div style="font-size: 1.5rem; font-weight: 600; color: var(--primary-color);">{stats.get('papers', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div>
            <div style="color: var(--text-secondary-light); font-size: 0.85rem;">Clusters identified:</div>
            <div style="font-size: 1.5rem; font-weight: 600; color: var(--primary-color);">{stats.get('clusters', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div>
            <div style="color: var(--text-secondary-light); font-size: 0.85rem;">Gaps Discovered</div>
            <div style="font-size: 1.5rem; font-weight: 600; color: var(--primary-color);">{stats.get('analyses', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

def render_search_interface():
    """Render the main search interface"""
    st.markdown("""
    <div class="quantum-card">
        <h2 style="text-align: center; margin: 0 0 1.5rem 0; color: var(--primary-color);">🔍 Start New Research Analysis</h2>
    """, unsafe_allow_html=True)
    
    # Search input
    query = st.text_input(
        "Research Query",
        placeholder="Enter your research topic (e.g., 'machine learning transformers', 'quantum computing algorithms')",
        help="Describe your research interest in keywords",
        key="main_search_query"
    )
    
    # Source selection
    st.markdown("### 📚 Select Research Sources")
    
    source_cols = st.columns(3)
    selected_sources = []
    
    for i, (key, source) in enumerate(AVAILABLE_SOURCES.items()):
        if source['enabled']:
            with source_cols[i % 3]:
                if st.checkbox(
                    f"{source['icon']} {source['name']}", 
                    value=True,
                    key=f"source_{key}",
                    help=source['description']
                ):
                    selected_sources.append(key)
    
    # Analysis parameters
    with st.expander("⚙️ Advanced Settings", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            max_papers = st.slider("Papers per source", 10, 100, 50)
            cluster_method = st.selectbox("Clustering method", ["kmeans", "hierarchical", "dbscan"])
        
        with col2:
            enable_gap_analysis = st.checkbox("Enable gap analysis", True)
            enable_reading_order = st.checkbox("Generate reading order", True)
    
    # Start analysis button
    if st.button("🚀 Start Complete Analysis", type="primary", use_container_width=True):
        if query.strip() and selected_sources:
            st.session_state.start_analysis = True
            st.session_state.analysis_config = {
                'query': query.strip(),
                'sources': selected_sources,
                'max_papers': max_papers,
                'cluster_method': cluster_method,
                'enable_gap_analysis': enable_gap_analysis,
                'enable_reading_order': enable_reading_order
            }
            st.rerun()
        else:
            st.error("Please enter a research query and select at least one source.")
    
    st.markdown("</div>", unsafe_allow_html=True)

def show_help_dialog():
    """Show help dialog"""
    with st.expander("🔍 Help & Documentation", expanded=True):
        st.markdown("""
        ### 🚀 Getting Started
        
        1. **Enter Research Query**: Use specific keywords related to your research interest
        2. **Select Sources**: Choose from arXiv, Google Scholar, IEEE, ACM, PubMed, and Semantic Scholar
        3. **Start Analysis**: The system will automatically fetch, analyze, and cluster papers
        4. **Explore Results**: Browse papers, view clusters, analyze gaps, and get reading suggestions
        
        ### 📚 Features
        
        - **Multi-source Fetching**: Comprehensive paper collection from 6+ academic sources
        - **AI Clustering**: Intelligent grouping of related research papers
        - **Gap Analysis**: Identify research opportunities and unexplored areas
        - **Reading Order**: Optimized sequence for maximum learning efficiency
        - **Professional Export**: Download results in multiple formats
        
        ### 💡 Tips
        
        - Use specific technical terms for better results
        - Select multiple sources for comprehensive coverage
        - Let the analysis complete fully for best insights
        - Use filters in Papers tab to find specific content
        - Export your results for future reference
        
        ### 🆘 Need Help?
        
        Contact support or check our documentation for detailed guides.
        """)

def render_paper_card(paper, index):
    """Render an individual paper card"""
    title = str(paper.get('title', 'Untitled Research Paper'))
    authors = paper.get('authors', []) or []
    year = paper.get('year', 'Unknown')
    source = str(paper.get('source', 'unknown')).replace('_', ' ').title()
    citations = paper.get('citation_count', 0) or 0
    
    # Truncate title if too long
    display_title = title[:120] + '...' if len(title) > 120 else title
    
    # Format authors
    author_list = ', '.join([str(a) for a in authors[:3] if a])
    if len(authors) > 3:
        author_list += f" et al. (+{len(authors) - 3})"
    
    st.markdown(f"""
    <div class="paper-card">
        <div style="display: flex; justify-content: between; align-items: start;">
            <div style="flex: 1;">
                <div class="paper-title">📑 {index}. {display_title}</div>
                <div class="paper-authors">👥 {author_list}</div>
                
                <div class="paper-meta">
                    <span class="paper-tag">📅 {year}</span>
                    <span class="paper-tag">🏷️ {source}</span>
                    {f'<span class="paper-tag">📊 {citations} citations</span>' if citations > 0 else ''}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    return paper