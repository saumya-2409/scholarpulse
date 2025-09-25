"""
Quantum Field: Academic Research Assistant
Advanced multi-source literature analysis with AI-powered insights
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Import modules
from config.settings import *
from config.ui_config import setup_page_config
from ui.theme import load_css_theme
from ui.components import render_header, render_sidebar
from ui.pages import hub, papers, reading_order, research_gaps, export
from data.storage.session_manager import initialize_session_state
from utils.helpers import check_dependencies

def main():
    """Main application entry point"""
    try:
        # Setup page configuration
        setup_page_config()
        
        # Load CSS theme
        load_css_theme()
        
        # Initialize session state
        initialize_session_state()
        
        # Check dependencies
        if not check_dependencies():
            st.error("⚠️ Missing required dependencies. Please check installation.")
            return
        
        # Render main layout
        render_header()
        
        # Sidebar navigation
        page = render_sidebar()
        
        # Route to appropriate page
        if page == "hub":
            hub.render()
        elif page == "papers":
            papers.render()
        elif page == "reading_order":
            reading_order.render()
        elif page == "research_gaps":
            research_gaps.render()
        elif page == "export":
            export.render()
        else:
            hub.render()  # Default to hub
            
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.info("Please refresh the page or contact support.")

if __name__ == "__main__":
    main()