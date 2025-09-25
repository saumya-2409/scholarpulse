"""
UI Configuration and Theme Settings
"""

import streamlit as st

def setup_page_config():
    """Configure Streamlit page settings"""
    st.set_page_config(
        page_title="Quantum Field: Academic Research Assistant",
        page_icon="🔬",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/quantum-research-assistant',
            'Report a bug': 'https://github.com/quantum-research-assistant/issues',
            'About': """
            # Quantum Field: Academic Research Assistant
            
            Advanced multi-source literature analysis with AI-powered insights.
            
            **Features:**
            - Multi-source paper fetching (arXiv, Google Scholar, IEEE, etc.)
            - AI-powered clustering and analysis
            - Research gap identification
            - Optimized reading order suggestions
            - Professional export capabilities
            
            Version 2.0.0
            """
        }
    )

# Color Palette
COLORS = {
    'primary': '#4A90E2',      # Primary blue
    'secondary': '#7B68EE',    # Secondary purple  
    'accent': '#00D2FF',       # Accent cyan
    'success': '#4CAF50',      # Success green
    'warning': '#FF9800',      # Warning orange
    'error': '#F44336',        # Error red
    'dark': '#1E1E2E',         # Dark background
    'light': '#FFFFFF',        # Light background
    'gray': {
        '50': '#F8FAFC',
        '100': '#F1F5F9', 
        '200': '#E2E8F0',
        '300': '#CBD5E1',
        '400': '#94A3B8',
        '500': '#64748B',
        '600': '#475569',
        '700': '#334155',
        '800': '#1E293B',
        '900': '#0F172A'
    }
}

# Typography
FONTS = {
    'primary': '"Inter", "Segoe UI", "Roboto", sans-serif',
    'monospace': '"JetBrains Mono", "Fira Code", monospace',
    'display': '"Poppins", "Inter", sans-serif'
}

# Layout Constants
LAYOUT = {
    'sidebar_width': 280,
    'content_padding': 32,
    'card_radius': 12,
    'card_shadow': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    'card_shadow_dark': '0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2)',
    'border_radius': 8,
    'transition': 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)'
}

# Component Styles
COMPONENT_STYLES = {
    'sidebar': {
        'background': 'rgba(255, 255, 255, 0.95)',
        'background_dark': 'rgba(30, 30, 46, 0.95)',
        'backdrop_filter': 'blur(10px)',
        'border': '1px solid rgba(255, 255, 255, 0.2)',
        'border_dark': '1px solid rgba(255, 255, 255, 0.1)'
    },
    'header': {
        'height': 80,
        'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'background_dark': 'linear-gradient(135deg, #2D3748 0%, #4A5568 100%)',
        'text_shadow': '0 2px 4px rgba(0, 0, 0, 0.1)'
    },
    'card': {
        'background': '#FFFFFF',
        'background_dark': '#2D3748',
        'hover_background': '#F7FAFC',
        'hover_background_dark': '#4A5568',
        'border': '1px solid #E2E8F0',
        'border_dark': '1px solid #4A5568'
    },
    'button': {
        'primary_bg': COLORS['primary'],
        'primary_hover': '#357ABD',
        'secondary_bg': COLORS['secondary'], 
        'secondary_hover': '#6A5ACD'
    }
}

# Animation Settings
ANIMATIONS = {
    'fade_in': 'fadeIn 0.5s ease-in',
    'slide_up': 'slideUp 0.3s ease-out',
    'pulse': 'pulse 2s infinite',
    'glow': 'glow 1.5s ease-in-out infinite alternate'
}