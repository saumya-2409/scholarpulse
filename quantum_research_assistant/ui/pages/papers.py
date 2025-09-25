"""
Enhanced Papers Page with Advanced Filtering and UI
"""

import streamlit as st
from ui.components import render_paper_card
from data.processors.filtering import filter_papers_safe, get_filter_options, sort_papers, create_filter_summary
from data.storage.session_manager import get_papers_data
from config.settings import PAPERS_PER_PAGE, MAX_DISPLAY_TITLE_LENGTH

def render():
    """Render the papers page with advanced filtering"""
    
    papers = get_papers_data()
    
    if not papers:
        render_no_papers_message()
        return
    
    # Header
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h1 style="color: var(--primary-color); margin: 0;">📄 Research Papers Collection</h1>
        <p style="color: var(--text-secondary-light); margin: 0.5rem 0 0 0;">
            Browse, search, and analyze your collected research papers
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get filter options
    filter_options = get_filter_options(papers)
    
    # Render filter interface
    filters = render_filter_interface(filter_options)
    
    # Apply filters
    filtered_papers = filter_papers_safe(
        papers,
        filters['search'],
        filters['source'],
        filters['year'],
        filters.get('venue')
    )
    
    # Sort papers
    filtered_papers = sort_papers(
        filtered_papers,
        filters['sort_by'],
        filters['ascending']
    )
    
    # Show filter summary
    render_filter_summary(papers, filtered_papers, filters)
    
    # Render papers
    render_papers_list(filtered_papers, filters['page'])

def render_no_papers_message():
    """Render message when no papers are available"""
    st.markdown("""
    <div class="quantum-card" style="text-align: center; padding: 3rem;">
        <div style="font-size: 4rem; margin-bottom: 1rem;">📚</div>
        <h2 style="color: var(--primary-color);">No Papers Found</h2>
        <p style="color: var(--text-secondary-light); margin: 1rem 0;">
            Start a new research analysis to collect papers from academic sources.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚀 Start New Analysis", type="primary", use_container_width=True):
        st.session_state.selected_page = 'hub'
        st.rerun()

def render_filter_interface(filter_options):
    """Render comprehensive filter interface"""
    
    st.markdown("""
    <div class="quantum-card" style="margin-bottom: 1.5rem;">
        <h3 style="margin: 0 0 1rem 0; color: var(--primary-color);">🔍 Filter & Search Papers</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Main filter row
    col1, col2, col3, col4 = st.columns([3, 1.5, 1.5, 1.5])
    
    with col1:
        search_query = st.text_input(
            "🔍 Search papers",
            placeholder="Search by title, authors, abstract, or keywords...",
            key="paper_search_query",
            help="Enter keywords to search across titles, abstracts, authors, and venues"
        )
    
    with col2:
        source_filter = st.selectbox(
            "📚 Source",
            ["All"] + filter_options['sources'],
            key="source_filter",
            help="Filter by publication source"
        )
    
    with col3:
        year_filter = st.selectbox(
            "📅 Year",
            ["All"] + filter_options['years'],
            key="year_filter",
            help="Filter by publication year"
        )
    
    with col4:
        venue_filter = st.selectbox(
            "🏛️ Venue",
            ["All"] + filter_options['venues'][:20],  # Limit venues to prevent UI overflow
            key="venue_filter",
            help="Filter by publication venue"
        )
    
    # Advanced filters (collapsible)
    with st.expander("⚙️ Advanced Filters & Sort Options", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Citation filters
            st.markdown("**Citation Count**")
            min_citations = st.number_input("Minimum citations", 0, 1000, 0, step=1)
            max_citations = st.number_input("Maximum citations", 0, 10000, 10000, step=10)
        
        with col2:
            # Content filters
            st.markdown("**Content Requirements**")
            has_pdf = st.checkbox("Has PDF link", False)
            has_abstract = st.checkbox("Has abstract", False)
            min_abstract_length = st.slider("Min abstract length", 0, 500, 50)
        
        with col3:
            # Sorting options
            st.markdown("**Sort Options**")
            sort_by = st.selectbox("Sort by", [
                "relevance", "year", "citations", "title", "authors"
            ])
            ascending = st.checkbox("Ascending order", False)
    
    # Results per page
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        results_per_page = st.selectbox(
            "Papers per page",
            [10, 20, 50, 100],
            index=1,
            key="results_per_page"
        )
    
    with col2:
        # Export filtered results
        if st.button("📥 Export Filtered", help="Export current filtered results"):\n            export_filtered_papers()\n    \n    with col3:\n        # Clear filters\n        if st.button("🗑️ Clear Filters", help="Reset all filters"):\n            clear_all_filters()\n    \n    # Calculate current page\n    current_page = st.session_state.get('papers_page', 1)\n    \n    return {\n        'search': search_query,\n        'source': source_filter,\n        'year': year_filter,\n        'venue': venue_filter,\n        'min_citations': min_citations,\n        'max_citations': max_citations,\n        'has_pdf': has_pdf,\n        'has_abstract': has_abstract,\n        'min_abstract_length': min_abstract_length,\n        'sort_by': sort_by,\n        'ascending': ascending,\n        'results_per_page': results_per_page,\n        'page': current_page\n    }\n\ndef render_filter_summary(original_papers, filtered_papers, filters):\n    \"\"\"Render filter results summary\"\"\"\n    \n    summary = create_filter_summary(original_papers, len(original_papers), filters)\n    \n    # Results count\n    col1, col2 = st.columns([3, 1])\n    \n    with col1:\n        if summary['active_filters']:\n            st.markdown(f\"\"\"\n            <div class=\"quantum-card\" style=\"background: rgba(74, 144, 226, 0.1); border-color: var(--primary-color);\">\n                <div style=\"display: flex; justify-content: between; align-items: center;\">\n                    <div>\n                        <strong>Showing {summary['filtered_count']} of {summary['original_count']} papers</strong>\n                        ({summary['reduction_percentage']:.1f}% filtered)\n                    </div>\n                </div>\n                <div style=\"margin-top: 0.5rem; font-size: 0.9rem; color: var(--text-secondary-light);\">\n                    🔍 Active filters: {' • '.join(summary['active_filters'])}\n                </div>\n            </div>\n            \"\"\", unsafe_allow_html=True)\n        else:\n            st.markdown(f\"\"\"\n            <div class=\"quantum-card\">\n                <strong>Showing all {len(filtered_papers)} papers</strong>\n            </div>\n            \"\"\", unsafe_allow_html=True)\n    \n    with col2:\n        # Quick stats\n        if filtered_papers:\n            avg_year = sum(int(str(p.get('year', 2020))) for p in filtered_papers if p.get('year')) / len(filtered_papers)\n            avg_citations = sum(p.get('citation_count', 0) or 0 for p in filtered_papers) / len(filtered_papers)\n            \n            st.markdown(f\"\"\"\n            <div class=\"quantum-card\" style=\"text-align: center;\">\n                <div style=\"font-size: 0.8rem; color: var(--text-secondary-light);\">Quick Stats</div>\n                <div><strong>Avg Year:</strong> {avg_year:.0f}</div>\n                <div><strong>Avg Citations:</strong> {avg_citations:.1f}</div>\n            </div>\n            \"\"\", unsafe_allow_html=True)\n\ndef render_papers_list(papers, current_page):\n    \"\"\"Render paginated list of papers\"\"\"\n    \n    if not papers:\n        st.markdown(\"\"\"\n        <div class=\"quantum-card\" style=\"text-align: center; padding: 2rem;\">\n            <div style=\"font-size: 3rem; margin-bottom: 1rem;\">🔍</div>\n            <h3>No papers match your filters</h3>\n            <p style=\"color: var(--text-secondary-light);\">Try adjusting your search criteria or clearing some filters.</p>\n        </div>\n        \"\"\", unsafe_allow_html=True)\n        return\n    \n    # Calculate pagination\n    results_per_page = st.session_state.get('results_per_page', PAPERS_PER_PAGE)\n    total_pages = (len(papers) - 1) // results_per_page + 1\n    current_page = max(1, min(current_page, total_pages))\n    \n    start_idx = (current_page - 1) * results_per_page\n    end_idx = min(start_idx + results_per_page, len(papers))\n    page_papers = papers[start_idx:end_idx]\n    \n    # Pagination controls (top)\n    render_pagination_controls(current_page, total_pages, len(papers), \"top\")\n    \n    # Render papers\n    for i, paper in enumerate(page_papers, start=start_idx + 1):\n        render_enhanced_paper_card(paper, i)\n    \n    # Pagination controls (bottom)\n    if total_pages > 1:\n        render_pagination_controls(current_page, total_pages, len(papers), \"bottom\")\n\ndef render_enhanced_paper_card(paper, index):\n    \"\"\"Render enhanced paper card with more details\"\"\"\n    \n    title = str(paper.get('title', 'Untitled Research Paper'))\n    authors = paper.get('authors', []) or []\n    year = paper.get('year', 'Unknown')\n    source = str(paper.get('source', 'unknown')).replace('_', ' ').title()\n    citations = paper.get('citation_count', 0) or 0\n    venue = str(paper.get('venue', ''))\n    abstract = str(paper.get('abstract', ''))\n    \n    # Format display title\n    display_title = title[:MAX_DISPLAY_TITLE_LENGTH] + '...' if len(title) > MAX_DISPLAY_TITLE_LENGTH else title\n    \n    # Format authors\n    author_list = ', '.join([str(a) for a in authors[:3] if a])\n    if len(authors) > 3:\n        author_list += f\" et al. (+{len(authors) - 3})\"\n    \n    # Create expandable card\n    with st.container():\n        st.markdown(f\"\"\"\n        <div class=\"paper-card\">\n            <div style=\"display: flex; justify-content: space-between; align-items: start;\">\n                <div style=\"flex: 1;\">\n                    <h4 class=\"paper-title\">📑 {index}. {display_title}</h4>\n                    <div class=\"paper-authors\">👥 {author_list}</div>\n                    \n                    <div class=\"paper-meta\">\n                        <span class=\"paper-tag\">📅 {year}</span>\n                        <span class=\"paper-tag\">🏷️ {source}</span>\n                        {f'<span class=\"paper-tag\">📊 {citations} citations</span>' if citations > 0 else ''}\n                        {f'<span class=\"paper-tag\">🏛️ {venue[:30]}...</span>' if venue and len(venue) > 5 else ''}\n                    </div>\n                </div>\n                \n                <div style=\"margin-left: 1rem;\">\n                    <div style=\"font-size: 0.8rem; color: var(--text-secondary-light); text-align: right;\">\n                        Relevance: {paper.get('_relevance_score', 0.8):.1%}\n                    </div>\n                </div>\n            </div>\n        </div>\n        \"\"\", unsafe_allow_html=True)\n        \n        # Expandable details\n        details_key = f\"paper_details_{index}\"\n        if details_key not in st.session_state:\n            st.session_state[details_key] = False\n        \n        col1, col2 = st.columns([1, 6])\n        \n        with col1:\n            if st.button(\n                \"🔽 Details\" if not st.session_state[details_key] else \"🔼 Hide\",\n                key=f\"toggle_details_{index}\",\n                help=\"Show/hide paper details\"\n            ):\n                st.session_state[details_key] = not st.session_state[details_key]\n        \n        # Show details if expanded\n        if st.session_state[details_key]:\n            render_paper_details(paper)\n        \n        st.markdown(\"<div style='margin-bottom: 1rem;'></div>\", unsafe_allow_html=True)\n\ndef render_paper_details(paper):\n    \"\"\"Render detailed paper information\"\"\"\n    \n    abstract = str(paper.get('abstract', ''))\n    links = paper.get('links', {}) or {}\n    ai_summary = paper.get('ai_summary', {})\n    \n    col1, col2 = st.columns([3, 2])\n    \n    with col1:\n        # Abstract\n        if abstract and len(abstract) > 50:\n            st.markdown(\"**📄 Abstract:**\")\n            st.markdown(f\"<div style='background: var(--bg-card-light); padding: 1rem; border-radius: 8px; border-left: 4px solid var(--primary-color);'>{abstract}</div>\", unsafe_allow_html=True)\n        \n        # AI Summary\n        if ai_summary:\n            st.markdown(\"**🤖 AI Analysis:**\")\n            \n            if ai_summary.get('key_contribution'):\n                st.markdown(f\"**🎯 Key Contribution:** {ai_summary['key_contribution']}\")\n            \n            if ai_summary.get('methodology'):\n                st.markdown(f\"**🔬 Methodology:** {ai_summary['methodology']}\")\n            \n            if ai_summary.get('main_findings'):\n                st.markdown(f\"**📈 Findings:** {ai_summary['main_findings']}\")\n    \n    with col2:\n        # Paper metadata\n        st.markdown(\"**📊 Paper Information:**\")\n        \n        metadata_items = []\n        \n        if paper.get('doi'):\n            metadata_items.append(f\"**DOI:** {paper['doi']}\")\n        \n        if paper.get('venue'):\n            metadata_items.append(f\"**Venue:** {paper['venue'][:50]}...\" if len(str(paper['venue'])) > 50 else f\"**Venue:** {paper['venue']}\")\n        \n        citation_count = paper.get('citation_count', 0) or 0\n        if citation_count > 0:\n            metadata_items.append(f\"**Citations:** {citation_count}\")\n        \n        for item in metadata_items:\n            st.markdown(item)\n        \n        # Access links\n        if links:\n            st.markdown(\"**🔗 Access Links:**\")\n            \n            link_emojis = {\n                'pdf': '📄 PDF',\n                'arxiv': '🔬 arXiv',\n                'doi': '🔗 DOI',\n                'semantic_scholar': '🧠 Semantic Scholar',\n                'google_scholar': '🔍 Google Scholar',\n                'ieee': '⚡ IEEE',\n                'acm': '💻 ACM',\n                'pubmed': '🏥 PubMed',\n                'web': '🌐 Web'\n            }\n            \n            for link_type, url in links.items():\n                if url:\n                    label = link_emojis.get(link_type, f'🔗 {link_type.title()}')\n                    st.markdown(f\"[{label}]({url})\")\n\ndef render_pagination_controls(current_page, total_pages, total_results, position):\n    \"\"\"Render pagination controls\"\"\"\n    \n    if total_pages <= 1:\n        return\n    \n    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])\n    \n    with col1:\n        if st.button(\"⬅️ First\", disabled=current_page == 1, key=f\"first_{position}\"):\n            st.session_state.papers_page = 1\n            st.rerun()\n    \n    with col2:\n        if st.button(\"◀️ Prev\", disabled=current_page == 1, key=f\"prev_{position}\"):\n            st.session_state.papers_page = current_page - 1\n            st.rerun()\n    \n    with col3:\n        st.markdown(f\"\"\"\n        <div style=\"text-align: center; padding: 0.5rem;\">\n            <strong>Page {current_page} of {total_pages}</strong><br>\n            <span style=\"color: var(--text-secondary-light); font-size: 0.8rem;\">({total_results} total results)</span>\n        </div>\n        \"\"\", unsafe_allow_html=True)\n    \n    with col4:\n        if st.button(\"▶️ Next\", disabled=current_page == total_pages, key=f\"next_{position}\"):\n            st.session_state.papers_page = current_page + 1\n            st.rerun()\n    \n    with col5:\n        if st.button(\"➡️ Last\", disabled=current_page == total_pages, key=f\"last_{position}\"):\n            st.session_state.papers_page = total_pages\n            st.rerun()\n\ndef export_filtered_papers():\n    \"\"\"Export filtered papers\"\"\"\n    st.info(\"Export functionality will be implemented in the Export page.\")\n    # TODO: Implement export of filtered results\n\ndef clear_all_filters():\n    \"\"\"Clear all filter states\"\"\"\n    filter_keys = [\n        'paper_search_query', 'source_filter', 'year_filter', 'venue_filter',\n        'papers_page', 'results_per_page'\n    ]\n    \n    for key in filter_keys:\n        if key in st.session_state:\n            del st.session_state[key]\n    \n    st.rerun()