import streamlit as st
from typing import List, Dict

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


# ==================== RENDER FUNCTIONS ====================
def render_paper_ui(paper: dict):
    """
    Render a clean, user-friendly view (no JSON) showing only non-empty LLM-extracted fields.
    Matches the requested format (header, metadata, content status, numbered Research Paper Summary,
    and access links). Ignores empty fields.
    """
    # Helpers
    def safe_str(x):
        return "" if x is None else str(x)

    # --- 1. Data Preparation ---
    
    #Header 
    title = safe_str(paper.get("title") or (paper.get("ai_summary") or {}).get("Title") or "Research Paper Summary")
    year = safe_str(paper.get("year") or (paper.get("ai_summary") or {}).get("Year",""))
    cites = safe_str(paper.get("citations") or paper.get("citation_count") or (paper.get("ai_summary") or {}).get("Citations",""))
    source = safe_str(paper.get("source") or paper.get("fetch_source") or (paper.get("ai_summary") or {}).get("Source",""))
       
    # Status Badges
    is_abstract_only = paper.get("abstract_summary_status") == "generated_from_abstract"
    status_emoji = "⚡" if is_abstract_only else "📄"

    # Author Formatting
    authors_list = paper.get("authors") or (paper.get("ai_summary") or {}).get("Authors") or []
    if isinstance(authors_list, list):
        authors = ", ".join(authors_list)
    else:
        authors = safe_str(authors_list)   

    # Extract AI Summary Data
    summary = paper.get("ai_summary") or paper.get("abstract_summary") or {}

    # Data extraction with fallbacks
    problem = summary.get("Research_Problem") or summary.get("problem_statement") or summary.get("Purpose") or ""
    objective = summary.get("Research_Objective") or summary.get("objective") or ""
    implications = summary.get("Aim_of_Study") or summary.get("reusability_practical_value") or ""
    limitations = summary.get("limitations_and_future_work") or summary.get("limitations") or []     
    # Methodology
    mma = summary.get("Methodology_Approach") or {}  
    method = mma.get("Method") if isinstance(mma, dict) else summary.get("Methodology_Approach", {}).get("Method") or ""
    process = mma.get("Process") if isinstance(mma, dict) else summary.get("Methodology_Approach", {}) or ""
    data_handling = mma.get("Data_Handling") if isinstance(mma, dict) else summary.get("Methodology_Approach", {}).get("Data_handling") or ""
    results_format = mma.get("Results_Format") if isinstance(mma, dict) else summary.get("Methodology_Approach", {}).get("Results_Format") or ""          
    #Key Findings
    findings = summary.get("Key_Findings") or summary.get("key_findings") or []
    if isinstance(findings, str): findings = [findings]

    # Button Links
    working_url = paper.get('working_url') or paper.get('url')
    pdf_url = paper.get('pdf_url')

    # --- 2. UI Render ---
    with st.expander(f"{status_emoji} {title}", expanded=False):

        # --- A. Header Badges ---
        if is_abstract_only:
            st.markdown("""<span style="background: #fef3c7; color: #b45309; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 500;">⚡ Generated from Abstract (Full Text Unavailable)</span>""", unsafe_allow_html=True)
        else:
            st.markdown("""<span style="background: #dcfce7; color: #15803d; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 500;">📄 Full Content Analysis</span>""", unsafe_allow_html=True)
                
 
        # Top Row: Metadata Badges
        c1, c2, c3 = st.columns([1, 1, 2])
        c1.markdown(f"**📅 Year:** {year}")
        c2.markdown(f"**🎓 Citations:** {cites}")
        c3.markdown(f"**🏛️ Source:** {source}")
        st.markdown(f"**✍️ Authors:** {authors}")
        st.divider()

        # --- B. The 6-Block Grid ---

        # ROW 1: The "Why" (Context & Goal)
        r1c1, r1c2 = st.columns(2, gap="medium")
        with r1c1:
            #Problem Statement
            if problem:
                st.info(f"**🧐 Problem Statement**\n\n{problem}")
            else:
                st.info("**🧐 Problem Statement**\n\n*Not explicitly extracted.*")

        with r1c2:
            # Objective
            if objective:
                st.success(f"**🎯 Research Objective**\n\n{objective}")
            else:
                st.success("**🎯 Research Objective**\n\n*Not explicitly extracted.*")

        # ROW 2: The "What" (Method & Findings)
        r2c1, r2c2 = st.columns(2, gap="medium")
        with r2c1:
            # Methodology 
            with st.container(border=True):   
                st.markdown("#### ⚙️ Methodology")                    
                if method or process or data_handling or results_format:
                    if method: st.markdown(f"- **Method:** {method}")
                    if process: st.markdown(f"- **Process:** {process}")
                    if data_handling: st.markdown(f"- **Data handling:** {data_handling}")
                    if results_format: st.markdown(f"- **Results format:** {results_format}")       
                else:
                    st.write(str(mma) if mma else "No details extracted.")
        with r2c2:
            with st.container(border=True):
                st.markdown("#### 💡 Key Findings")
                if findings:
                    for f in findings:
                        st.markdown(f"- {f}")
                else:
                    st.write("No specific findings extracted.")
        
        # ROW 3: The "So What" (Value & Limits)
        r3c1, r3c2 = st.columns(2, gap="medium")
        with r3c1:
            with st.container(border=True):
                st.markdown("#### 🚀 Implications & Value")
                if implications:
                    st.write(implications)
                else:
                    st.caption("No specific implications extracted.")

        with r3c2:
            if limitations:
                with st.container(border=True):
                    st.markdown("#### ⚠️ Limitations & Future Work ")
                    if isinstance(limitations, list):
                        for l in limitations: st.markdown(f"- {l}")
                    else:
                        st.write(limitations)
            else:
                st.caption("No limitations extracted.")
                       
        # Keywords
        keywords = summary.get("Keywords") or paper.get("keywords") or []
        if isinstance(keywords, str) and keywords.strip():
            st.caption(f"**Keywords:** {keywords}")
        elif isinstance(keywords, list) and keywords:
            st.caption(f"**Keywords:** {', '.join([str(k) for k in keywords[:20]])}")

        
        # --- C. Action Buttons ---
        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        working_url = paper.get('working_url') or paper.get('url')
        access_type = paper.get('access_type', 'direct')
        
        button_label = (
            "Access Paper (PDF)"
            if access_type == 'direct_pdf' 
            else "Access Full Paper"
        )

        if working_url:
            with col1:
                st.link_button(
                    button_label, 
                    working_url,
                    use_container_width=True
                )

        # Direct PDF fallback
        pdf_url = paper.get('pdf_url')
        if pdf_url and pdf_url != working_url:
            with col2:
                st.link_button(
                    "Direct PDF Download", 
                    pdf_url,
                    use_container_width=True
                )

def render_suggested_paper(paper: Dict):
    """Render truly restricted paper card"""
    
    st.markdown(f"""
    <div class="suggested-card">
        <h4 style="margin-bottom: 0.5rem; color: #1e293b;">{paper.get('title', 'Unknown Title')}</h4>
        <p style="color: #64748b; font-size: 0.9rem; margin-bottom: 0.8rem;">
            <strong>Authors:</strong> {', '.join(paper.get('authors', ['Unknown'])[:3])}
            {' et al.' if len(paper.get('authors', [])) > 3 else ''}<br>
            <strong>Source:</strong> {paper.get('source', 'Unknown')} | 
            <strong>Year:</strong> {paper.get('year', 0)} | 
            <strong>Citations:</strong> {paper.get('citations', 0)}
        </p>
        <a href="{paper.get('url', '#')}" target="_blank" style="color: #667eea; text-decoration: none; font-weight: 500;">
            Requires Subscription Access
        </a>
    </div>
    """, unsafe_allow_html=True)

def render_welcome_screen():
    # Enhanced welcome screen
    st.markdown("### Intelligent Research Analysis")
    
    steps = [
        {
            'title': 'Enter Research Topic',
            'description': 'Type your research keywords for intelligent multi-source analysis',
            'expected': 'Focused topics yield better content extraction results'
        },
        {
            'title': 'Select Enhanced Sources', 
            'description': 'Choose from real APIs with intelligent access detection capabilities',
            'expected': f'ArXiv: {"" if ARXIV_AVAILABLE else ""}, Semantic Scholar:'
        },
        {
            'title': 'Set Paper Count',
            'description': 'Choose papers per source (15-100) - system will intelligently analyze accessibility',
            'expected': 'More papers = comprehensive analysis but longer processing time'
        },
        {
            'title': 'Start Intelligent Analysis',
            'description': 'AI system will fetch, extract content, detect access, and generate enhanced summaries',
            'expected': '30-90 seconds for complete intelligent analysis with content extraction'
        }
    ]

    col1, col2 = st.columns(2)

    for idx, step in enumerate(steps):
        column = col1 if idx % 2 == 0 else col2
        with column:
            st.markdown(f"""
            <div class="welcome-step">
                <div style="display: flex; align-items: flex-start;">
                    <div class="step-number">{idx + 1}</div>
                    <div>
                        <h4 style="margin: 0 0 0.5rem 0; color: #1e293b;">{step['title']}</h4>
                        <p style="color: #64748b; margin: 0 0 0.8rem 0; line-height: 1.5;">
                            {step['description']}
                        </p>
                        <div style="background: #f1f5f9; padding: 0.5rem 0.8rem; border-radius: 6px; font-size: 0.9rem; color: #475569;">
                            <strong>Expected:</strong> {step['expected']}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Dependencies and capabilities
    st.markdown("### System Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if ARXIV_AVAILABLE:
            st.success(" **ArXiv API** - Real papers available")
        else:
            st.error("**ArXiv** - Install: `pip install arxiv`")
    
    with col2:
        st.success("**Semantic Scholar** - Enhanced API ready")
    
    with col3:
        if BEAUTIFULSOUP_AVAILABLE:
            st.success("**Content Extraction** - Advanced parsing")
        else:
            st.warning("**Install BeautifulSoup** - `pip install beautifulsoup4`")
    
    st.markdown("### Example Results")
    st.markdown("**Query:** `deep learning transformers` ")
    st.markdown("**Expected:** 60-300 papers ")
    st.markdown("**Intelligent Analysis:** Content extraction, access detection, enhanced summaries ")
    st.markdown("**Time:** 30-90 seconds ")
