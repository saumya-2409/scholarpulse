"""
¬ INTELLIGENT Research Assistant - Smart Paper Access & Content Extraction
- Intelligently detects which papers are actually accessible
- Fetches full text content from accessible papers
- Provides direct paper links (not just search links)
- Only truly paywalled papers go to "suggested reading"
- Enhanced content extraction and summarization
- Beautiful design preserved
"""

import streamlit as st
import warnings
import os
import logging
import time
import plotly.express as px
import concurrent.futures
from typing import List, Dict
from datetime import datetime
from dotenv import load_dotenv

from embedding_utils import compute_relevance_embedding_score
from summarizer import FullPaperSummarizer
from fetchers import IntelligentMultiSourceFetcher
from utils import deduplicate_papers
from ui import render_welcome_screen, render_suggested_paper, render_paper_ui
from clustering import PaperClusterer

load_dotenv()

# Optional Imports
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

PYPDF_AVAILABLE = False  # Default; not used in main.py

# Suppress all warnings
warnings.filterwarnings("ignore")
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
logging.getLogger().setLevel(logging.ERROR)

st.set_page_config(
    page_title="AI Research Assistant",
    page_icon=" § ",
    layout="wide",
    initial_sidebar_state="expanded"
)


if 'summarizer' not in st.session_state:
    st.session_state.summarizer = FullPaperSummarizer()
    print("[App Debug] Summarizer singleton created")

# BEAUTIFUL DESIGN CSS (PRESERVED)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        font-weight: 400;
    }
    
    .stApp {
        background: linear-gradient(135deg, #fafbfc 0%, #f4f6f8 100%);
    }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 16px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.12);
        border: 1px solid rgba(255, 255, 255, 0.15);
    }
    
    .main-header h1 {
        font-size: 2.2rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    .main-header p {
        font-size: 1rem;
        opacity: 0.9;
        font-weight: 300;
    }
    
    .css-1d391kg {
        background: white;
        border-right: 1px solid #e2e8f0;
        box-shadow: 2px 0 8px rgba(0, 0, 0, 0.03);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: white;
        padding: 6px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        margin-bottom: 1.5rem;
        border: 1px solid #f1f5f9;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 44px;
        padding: 0 20px;
        background: transparent;
        border-radius: 8px;
        color: #64748b;
        font-weight: 400;
        transition: all 0.2s ease;
        border: none;
        font-size: 0.95rem;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
    }
    
    .metric-card {
        background: white;
        border: 1px solid #f1f5f9;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
        transition: transform 0.15s ease;
        margin: 6px;
    }
    
    .metric-card:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.08);
    }
    
    .metric-number {
        font-size: 2.2rem;
        font-weight: 500;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        color: #64748b;
        font-weight: 400;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }
    
    .summary-section {
        background: linear-gradient(135deg, #fafbfc 0%, #f8fafc 100%);
        border-left: 3px solid #667eea;
        padding: 1rem;
        margin: 0.6rem 0;
        border-radius: 0 8px 8px 0;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.02);
    }
    
    .summary-section strong {
        color: #1e293b;
        font-weight: 500;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border: 1px solid #f59e0b;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(245, 158, 11, 0.06);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
        font-size: 0.95rem;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.25);
    }
    
    .status-full {
        background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
        color: #15803d;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 500;
        border: 1px solid #86efac;
    }
    
    .status-abstract {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        color: #a16207;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 500;
        border: 1px solid #facc15;
    }
    
    .status-extracted {
        background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
        color: #3730a3;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 500;
        border: 1px solid #a5b4fc;
    }
    
    .cluster-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
        border: 1px solid #f1f5f9;
        transition: all 0.2s ease;
        margin: 1rem 0;
    }
    
    .cluster-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.08);
    }
    
    .cluster-title {
        font-size: 1.1rem;
        font-weight: 500;
        color: #1e293b;
        margin-bottom: 0.5rem;
    }
    
    .welcome-step {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
    }
    
    .step-number {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 500;
        font-size: 0.9rem;
        margin-right: 0.8rem;
    }
    
    .gap-card {
        background: white;
        border: 1px solid #f1f5f9;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
        border-left: 4px solid #8b5cf6;
    }
    
    .suggested-card {
        background: white;
        border: 1px solid #f1f5f9;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.02);
        border-left: 3px solid #f59e0b;
    }
    
    .stTextInput input {
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        padding: 0.7rem;
        font-size: 0.95rem;
        font-weight: 400;
        transition: all 0.2s ease;
    }
    
    .stTextInput input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
    }
    
    .source-status {
        background: #f0f9ff;
        border: 1px solid #38bdf8;
        padding: 0.5rem;
        border-radius: 6px;
        font-size: 0.85rem;
        margin: 0.5rem 0;
    }
    
    .extraction-status {
        background: #f0f4ff;
        border: 1px solid #6366f1;
        padding: 0.5rem;
        border-radius: 6px;
        font-size: 0.85rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'papers_data' not in st.session_state:
    st.session_state.papers_data = []
if 'full_text_papers' not in st.session_state:
    st.session_state.full_text_papers = []
if 'suggested_papers' not in st.session_state:
    st.session_state.suggested_papers = []
if 'clusters' not in st.session_state:
    st.session_state.clusters = {}
if 'processing' not in st.session_state:
    st.session_state.processing = False

# ==================== GAP ANALYSIS ====================
# NOTE: ImprovedClusterer (keyword-based) removed.
# Clustering is now handled by PaperClusterer from clustering.py
# which uses UMAP + silhouette score + LLM naming.

class ResearchGapAnalyzer:
    def analyze_gaps(self, papers: List[Dict]) -> Dict[str, List[str]]:
        gaps = {
            'methodological_gaps': [],
            'evaluation_gaps': [], 
            'application_gaps': [],
            'theoretical_gaps': []
        }
        
        # Use extracted content for better gap analysis
        all_content = []
        for paper in papers:
            content = paper.get('extracted_content', '') or paper.get('abstract', '')
            all_content.append(content)
        
        combined_content = ' '.join(all_content).lower()
        
        if 'dataset' in combined_content or 'limited' in combined_content:
            gaps['methodological_gaps'].extend([
                'Limited dataset diversity across different domains and applications',
                'Lack of standardized evaluation protocols for cross-method comparison',
                'Insufficient attention to computational efficiency and scalability issues'
            ])
        
        if 'experiment' in combined_content or 'evaluation' in combined_content:
            gaps['evaluation_gaps'].extend([
                'Need for more comprehensive real-world testing scenarios',
                'Lack of longitudinal studies assessing long-term performance',
                'Limited evaluation on edge cases and adversarial conditions'
            ])
        
        if 'application' in combined_content or 'real-world' in combined_content:
            gaps['application_gaps'].extend([
                'Gap between laboratory results and industrial deployment',
                'Limited integration with existing systems and workflows',
                'Insufficient consideration of regulatory and ethical constraints'
            ])
        
        if 'theoretical' in combined_content or 'analysis' in combined_content:
            gaps['theoretical_gaps'].extend([
                'Lack of theoretical foundations for empirical observations',
                'Limited understanding of failure modes and boundary conditions',
                'Insufficient mathematical analysis of convergence properties'
            ])
        
        return gaps

# ==================== MAIN APPLICATION ====================

# Beautiful Header
st.markdown("""
<div class="main-header">
    <h1>AI Research Assistant</h1>
    <p>Extract, Analyze, and Summarize Research Papers</p>
</div>
""", unsafe_allow_html=True)

# Enhanced Sidebar
with st.sidebar:
    st.markdown("### 🔍 Research Parameters")
    
    query = st.text_input(
        "Research Topic",
        placeholder="e.g., Generative AI in Healthcare",
        help="Enter the specific topic you want to analyze"
    )
    
    st.markdown("### 📚 Data Sources")
    st.caption("Select at least one source to fetch papers from.")

    # Create two columns for the checkboxes
    col_arxiv, col_semantic = st.columns(2)

    with col_arxiv:
        use_arxiv = st.checkbox("arXiv", value=True)
        if use_arxiv and not ARXIV_AVAILABLE:
            st.error("⚠️ ArXiv library missing!")
            
    with col_semantic:
        use_semantic = st.checkbox("Semantic Scholar", value=True) 

    

    st.markdown("### ⚙️ Configuration")
    papers_per_source = st.slider(
        "**Papers to Fetch (per source)**",
        min_value=10, max_value=100, value=30, step=10,
        help="Higher values provide more comprehensive results but take longer to process."
    )
    
    # Build source list
    sources = []
    if use_arxiv: sources.append('arxiv')
    if use_semantic: sources.append('semantic_scholar')
    
    if sources:
        expected_total = papers_per_source * len(sources)
        st.info(f"📊 **Estimate:** Analyzing up to **{expected_total}** papers.")
    else:
        st.error("❌ Please select at least one source!")
    
    # --- Buttons Layout (Side-by-Side) ---
    col_start, col_clear = st.columns(2)

    with col_start:
        # Start Analysis Button
        start_btn = st.button(
            "🚀 Start", 
            type="primary", 
            disabled=st.session_state.processing or not sources or not query,
            use_container_width=True,
            help="Begin the intelligent research analysis."
        )

    with col_clear:
        # Clear Results Button
        clear_btn = st.button(
            "🗑️ Clear", 
            type="secondary",
            use_container_width=True,
            help="Reset all results and start fresh."
        )

    # --- Logic Handling ---
    
    # Handle Start Logic
    if start_btn:
        if query.strip() and sources:
            st.session_state.processing = True
        
        # Create the status container
        with st.status("🚀 Initiating Research Sequence...", expanded=True) as status:
            try:
                # Step 1: Fetching
                st.write("1️⃣ **Scouting Sources:** Fetching latest research from Sources...")
                start_time = time.time()
                fetcher = IntelligentMultiSourceFetcher()
                papers = fetcher.fetch_papers(query, sources, papers_per_source)
                fetch_time = time.time() - start_time

                if len(papers) == 0:
                    status.update(label="❌ No papers found! Try distinct keywords.", state="error")
                    st.session_state.processing = False
                    st.stop()

                # Step 2: Filtering
                st.write("3️⃣ **Smart Filter:** Removing duplicates and irrelevant results...")
                valid_papers = []
                for p in papers:
                    # 1. Compute Score
                    score = compute_relevance_embedding_score(query, p)
                    p['relevance_score'] = round(score, 3)                    
                    # 2. Strict Filter (Threshold 0.25)
                    # Lowered from 0.35 to 0.25 to prevent valid papers from being dropped
                    if score >= 0.25: 
                        valid_papers.append(p)

                if not valid_papers:
                    status.update(label="⚠️ No relevant papers found after filtering.", state="error")
                    st.warning("Try broader terms or check spelling.")
                    st.session_state.processing = False
                    st.stop()
                
                # 3. Sort by Relevance + Year (Newest & Most Relevant first)
                valid_papers.sort(key=lambda x: (x.get('relevance_score', 0.0), x.get('year') or 0), reverse=True)
                st.info(f"Processing {len(valid_papers)} highly relevant papers...")
                
                summarizer_instance = st.session_state.summarizer

                def process_single_paper(p):
                    summary = summarizer_instance.summarize_paper(p, use_full_text=True, query=query)
                    p['ai_summary'] = summary if isinstance(summary, dict) else {"summary": str(summary)}
                    p['accessibility'] = summary.get('accessibility') if isinstance(summary, dict) else 'inaccessible'
                    p['abstract_summary_status'] = summary.get('abstract_summary_status', 'inaccessible') if isinstance(summary, dict) else 'inaccessible'
                    return p
                
                # Step 4: Summary Generation
                with st.spinner("3️⃣ **Deep Reading:** Generating AI summaries..."):
                    starttime = time.time()
                    papers_data = []
                    full_text_papers = []
                    suggested_papers = []

                    # PARALLEL EXECUTION (Max 3 workers to respect rate limits)
                    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                        results = list(executor.map(process_single_paper, valid_papers))

                    for paper in results:
                        if paper.get('accessibility') == 'accessible':
                            papers_data.append(paper)
                            if paper.get('extracted_content') or paper.get('abstract_summary_status') == 'generated_from_fulltext':
                                full_text_papers.append(paper)
                        else:
                            suggested_papers.append(paper)

                    # Save timings and state
                    summarytime = time.time() - starttime
                    status.update(label="✅ Research Analysis Complete!", state="complete", expanded=False)

                    # Update State
                    st.session_state.papers_data = papers_data
                    st.session_state.full_text_papers = full_text_papers
                    st.session_state.suggested_papers = suggested_papers
                    st.session_state.processing = False

                    # ---- Run improved clustering ----
                    if papers_data:
                        st.write("4️⃣ **Smart Clustering:** Grouping papers by research theme...")
                        try:
                            clusterer = PaperClusterer()
                            st.session_state.clusters = clusterer.cluster_papers(papers_data)
                        except Exception as ce:
                            st.warning(f"Clustering skipped: {ce}")
                            st.session_state.clusters = {}
                    else:
                        st.session_state.clusters = {}

                    st.balloons()
                    
            except Exception as e:
                status.update(label="❌ An error occurred during analysis.", state="error")
                st.error(f"Error during analysis: {str(e)}")
                st.session_state.processing = False

    # Handle Clear Logic
    if clear_btn:
        st.session_state.papers_data = []
        st.session_state.full_text_papers = []
        st.session_state.suggested_papers = []
        st.session_state.clusters = {}
        st.session_state.current_page = 1  # Reset pagination
        st.rerun()
    
    # Footer
    st.markdown("---")
    if not BEAUTIFULSOUP_AVAILABLE:
        st.caption("⚠️ **Note:** Install `beautifulsoup4` for better web scraping.")
    st.caption("© 2025 Intelligent Research Assistant")

# ==================== MAIN CONTENT ====================
if st.session_state.papers_data:
    # Enhanced metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{len(st.session_state.papers_data)}</div>
            <div class="metric-label">Papers Analyzed</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        accessible_count = len(st.session_state.full_text_papers)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{accessible_count}</div>
            <div class="metric-label">Accessible Papers</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        extracted_count = len([p for p in st.session_state.papers_data if p.get('extracted_content')])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{extracted_count}</div>
            <div class="metric-label">Content Extracted</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        sources_count = len(set([p.get('source', 'unknown') for p in st.session_state.papers_data]))
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{sources_count}</div>
            <div class="metric-label">Sources Used</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Clean tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        " Dashboard", 
        " Papers & Summaries", 
        " Research Gaps",
        " Restricted Reading"
    ])
    
    with tab1:
        st.markdown("### Research Dashboard")
        st.markdown("*Intelligent analysis with enhanced content extraction*")
        
        if st.session_state.clusters:
            col1, col2 = st.columns(2)
            
            with col1:
                cluster_names = []
                cluster_counts = []
                for cluster_id, cluster_info in st.session_state.clusters.items():
                    cluster_names.append(cluster_info['name'])
                    cluster_counts.append(cluster_info.get('papercount', len(cluster_info.get('papers', []))))

                
                colors = ['#8b5cf6', '#a78bfa', '#c4b5fd', '#ddd6fe', '#ede9fe', '#667eea', '#764ba2']
                
                fig = px.pie(
                    values=cluster_counts,
                    names=cluster_names,
                    title="Research Areas Distribution",
                    color_discrete_sequence=colors
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(
                    font_family="Inter",
                    title_font_size=16,
                    font_size=12,
                    showlegend=True
                )
                st.plotly_chart(fig, width='stretch')
            
            with col2:
                citation_data = []
                area_names = []
                for cluster_info in st.session_state.clusters.values():
                    citation_data.append(cluster_info.get('avg_citations', 0))
                    area_names.append(cluster_info['name'])
                
                fig = px.bar(
                    x=citation_data,
                    y=area_names,
                    orientation='h',
                    title="Average Citations by Research Area",
                    color=citation_data,
                    color_continuous_scale=["#f8fafc", "#667eea", "#764ba2"]
                )
                fig.update_layout(
                    font_family="Inter",
                    title_font_size=16,
                    font_size=12,
                    xaxis_title="Average Citations",
                    yaxis_title="Research Area"
                )
                st.plotly_chart(fig, width='stretch')
            
            # Enhanced cluster cards
            st.markdown("### Research Themes")
            
            for cluster_id, cluster_info in st.session_state.clusters.items():
                # Filter papers to those relevant to query (simple keyword match for safety)
                relevant_papers = [p for p in cluster_info['papers'] if any(word in (p.get('title', '') + p.get('abstract', '')).lower() for word in query.lower().split())]
                paper_count = len(relevant_papers)  # Safe count from filtered papers list
                extracted_in_cluster = len([p for p in relevant_papers if p.get('extracted_content')])  # Update count
                cluster_info['papers'] = relevant_papers  # Override for display
                
                st.markdown(f"""
                <div class="cluster-card">
                    <div class="cluster-title">{cluster_info['name']}</div>
                    <p style="color: #64748b; margin-bottom: 1rem;">{cluster_info['description']}</p>
                    <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
                        <span style="background: #f1f5f9; padding: 6px 10px; border-radius: 6px; font-size: 0.85rem; color: #475569;">
                            {paper_count} papers
                        </span>
                        <span style="background: #f1f5f9; padding: 6px 10px; border-radius: 6px; font-size: 0.85rem; color: #475569;">
                            {extracted_in_cluster} content extracted
                        </span>
                        <span style="background: #f1f5f9; padding: 6px 10px; border-radius: 6px; font-size: 0.85rem; color: #475569;">
                            {cluster_info.get('avg_citations', 0)} avg citations
                        </span>
                        <span style="background: #f1f5f9; padding: 6px 10px; border-radius: 6px; font-size: 0.85rem; color: #475569;">
                            {cluster_info.get('avg_year', 2024)}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Complete analysis to see research themes and dashboard metrics.")
   
    with tab2:
        st.markdown("### Papers & Summaries")
        papers_data = st.session_state.get("papers_data", [])
        
        if not papers_data:
            st.info("No accessible papers available. Try another query or enable more sources.")
        else:
            # --- PAGINATION CONFIG ---
            ITEMS_PER_PAGE = 10
            
            if 'current_page' not in st.session_state:
                st.session_state.current_page = 1
                
            total_count = len(papers_data)
            total_pages = max(1, (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
            
            if st.session_state.current_page > total_pages:
                st.session_state.current_page = 1

            # --- INFO TEXT (TOP) ---
            # Just text, no buttons here
            st.markdown(f"""
            <div style="color: #64748b; margin-bottom: 15px; font-size: 0.95rem;">
                Showing Page <strong>{st.session_state.current_page}</strong> of <strong>{total_pages}</strong> 
                <span style="color: #94a3b8;">({total_count} total papers)</span>
            </div>
            """, unsafe_allow_html=True)

            # --- DISPLAY CURRENT PAGE ---
            start_idx = (st.session_state.current_page - 1) * ITEMS_PER_PAGE
            end_idx = start_idx + ITEMS_PER_PAGE
            
            current_batch = papers_data[start_idx:end_idx]
            
            for paper in current_batch:
                render_paper_ui(paper)
            
            st.markdown("---")

            # --- PAGINATION CONTROLS (BOTTOM ONLY) ---
            c1, c2, c3 = st.columns([1, 3, 1])
            
            with c1:
                if st.button("← Previous", key="btn_prev", disabled=(st.session_state.current_page == 1), use_container_width=True):
                    st.session_state.current_page -= 1
                    st.rerun()
            
            with c2:
                # Centered page indicator for easy reading at bottom
                st.markdown(f"""
                <div style="text-align: center; padding-top: 8px; color: #64748b; font-weight: 500;">
                    Page {st.session_state.current_page}
                </div>
                """, unsafe_allow_html=True)

            with c3:
                if st.button("Next →", key="btn_next", disabled=(st.session_state.current_page == total_pages), use_container_width=True):
                    st.session_state.current_page += 1
                    st.rerun()

    with tab3:
        st.markdown("### Research Gaps Analysis")
        st.markdown("*Enhanced gap analysis using extracted content*")
        
        if st.session_state.papers_data:
            gap_analyzer = ResearchGapAnalyzer()
            gaps = gap_analyzer.analyze_gaps(st.session_state.papers_data)
            
            for gap_type, gap_list in gaps.items():
                if gap_list:
                    gap_title = gap_type.replace('_', ' ').title()
                    
                    st.markdown(f"""
                    <div class="gap-card">
                        <h4 style="margin-bottom: 0.8rem; color: #7c3aed;">{gap_title}</h4>
                        <ul style="color: #374151; margin: 0; padding-left: 1.5rem;">
                    """, unsafe_allow_html=True)
                    
                    for gap in gap_list:
                        st.markdown(f"<li style='margin-bottom: 0.5rem;'>{gap}</li>", unsafe_allow_html=True)
                    
                    st.markdown("</ul></div>", unsafe_allow_html=True)
        else:
            st.info("Complete paper analysis to identify research gaps and opportunities.")
    
    with tab4:
        st.markdown("### Restricted Reading")

        
        st.markdown("""
        <div class="warning-box">
            <strong>Restricted Access:</strong> Access to these papers requires a subscription or paid access.
        </div>
        """, unsafe_allow_html=True)
        
        if not st.session_state.suggested_papers:
            st.success("Excellent! All papers are accessible. Check 'Papers & Summaries' for complete analysis with extracted content.")
        else:
            st.markdown(f"**{len(st.session_state.suggested_papers)} papers requiring paid/institutional access**")
            
            for i, paper in enumerate(st.session_state.suggested_papers, 1):
                render_suggested_paper(paper)

else:
    render_welcome_screen()


# Clean footer
if not st.session_state.processing:
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: #94a3b8; font-size: 0.9rem;'> Intelligent research assistant with content extraction</div>", unsafe_allow_html=True)
