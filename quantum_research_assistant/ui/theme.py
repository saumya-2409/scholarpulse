"""
Advanced CSS Theme System - Quantum Field UI
"""

import streamlit as st
from pathlib import Path

def load_css_theme():
    """Load the complete CSS theme system"""
    
    css = """
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@400;500;600;700&display=swap');
    
    /* CSS Variables for Theme */
    :root {
        /* Colors */
        --primary-color: #4A90E2;
        --secondary-color: #7B68EE;
        --accent-color: #00D2FF;
        --success-color: #4CAF50;
        --warning-color: #FF9800;
        --error-color: #F44336;
        
        /* Backgrounds */
        --bg-light: #FFFFFF;
        --bg-dark: #1E1E2E;
        --bg-card-light: #FFFFFF;
        --bg-card-dark: #2D3748;
        --bg-sidebar-light: rgba(255, 255, 255, 0.95);
        --bg-sidebar-dark: rgba(30, 30, 46, 0.95);
        
        /* Text Colors */
        --text-primary-light: #1A202C;
        --text-primary-dark: #F7FAFC;
        --text-secondary-light: #4A5568;
        --text-secondary-dark: #A0AEC0;
        
        /* Borders */
        --border-light: #E2E8F0;
        --border-dark: #4A5568;
        
        /* Shadows */
        --shadow-light: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --shadow-dark: 0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2);
        --shadow-card: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        
        /* Fonts */
        --font-primary: 'Inter', 'Segoe UI', 'Roboto', sans-serif;
        --font-display: 'Poppins', 'Inter', sans-serif;
        --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
        
        /* Layout */
        --border-radius: 12px;
        --border-radius-sm: 8px;
        --transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* Global Styles */
    .main {
        font-family: var(--font-primary);
        background: var(--bg-light);
        color: var(--text-primary-light);
    }
    
    /* Dark Mode */
    @media (prefers-color-scheme: dark) {
        .main {
            background: var(--bg-dark);
            color: var(--text-primary-dark);
        }
    }
    
    /* Neural Network Background Pattern */
    .main::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            radial-gradient(circle at 20% 80%, rgba(74, 144, 226, 0.03) 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, rgba(123, 104, 238, 0.03) 0%, transparent 50%),
            radial-gradient(circle at 40% 40%, rgba(0, 210, 255, 0.02) 0%, transparent 50%);
        z-index: -1;
        pointer-events: none;
    }
    
    /* Header Styling */
    .quantum-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem 2rem;
        border-radius: 0 0 20px 20px;
        margin: -1rem -1rem 2rem -1rem;
        box-shadow: var(--shadow-card);
        position: relative;
        overflow: hidden;
    }
    
    .quantum-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%);
        animation: shimmer 3s infinite;
    }
    
    .quantum-header h1 {
        font-family: var(--font-display);
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        position: relative;
        z-index: 1;
    }
    
    .quantum-header .tagline {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.1rem;
        font-weight: 400;
        margin: 0.5rem 0 0 0;
        position: relative;
        z-index: 1;
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background: var(--bg-sidebar-light);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 0 20px 20px 0;
        box-shadow: var(--shadow-card);
    }
    
    @media (prefers-color-scheme: dark) {
        .css-1d391kg {
            background: var(--bg-sidebar-dark);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
    }
    
    /* Navigation Items */
    .nav-item {
        display: flex;
        align-items: center;
        padding: 0.75rem 1rem;
        margin: 0.25rem 0;
        border-radius: var(--border-radius-sm);
        cursor: pointer;
        transition: var(--transition);
        border: 1px solid transparent;
    }
    
    .nav-item:hover {
        background: rgba(74, 144, 226, 0.1);
        border-color: rgba(74, 144, 226, 0.2);
        transform: translateX(2px);
    }
    
    .nav-item.active {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        color: white;
        box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
    }
    
    .nav-item .icon {
        margin-right: 0.75rem;
        font-size: 1.2rem;
    }
    
    /* Card System */
    .quantum-card {
        background: var(--bg-card-light);
        border: 1px solid var(--border-light);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        box-shadow: var(--shadow-light);
        transition: var(--transition);
        position: relative;
        overflow: hidden;
    }
    
    .quantum-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        opacity: 0;
        transition: var(--transition);
    }
    
    .quantum-card:hover::before {
        opacity: 1;
    }
    
    .quantum-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 25px rgba(0, 0, 0, 0.15);
    }
    
    @media (prefers-color-scheme: dark) {
        .quantum-card {
            background: var(--bg-card-dark);
            border-color: var(--border-dark);
            box-shadow: var(--shadow-dark);
        }
    }
    
    /* Status Cards */
    .status-card {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        color: white;
        border-radius: var(--border-radius);
        padding: 1.5rem;
        position: relative;
        overflow: hidden;
    }
    
    .status-card::after {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 100%;
        height: 100%;
        background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
        animation: statusShine 2s infinite;
    }
    
    .status-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    
    /* Progress Bar */
    .quantum-progress {
        width: 100%;
        height: 8px;
        background: rgba(74, 144, 226, 0.2);
        border-radius: 4px;
        overflow: hidden;
        position: relative;
    }
    
    .quantum-progress-fill {
        height: 100%;
        background: linear-gradient(90deg, var(--primary-color), var(--accent-color));
        border-radius: 4px;
        transition: width 0.3s ease;
        position: relative;
    }
    
    .quantum-progress-fill::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        animation: progressShine 1.5s infinite;
    }
    
    /* Button System */
    .quantum-btn {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: var(--border-radius-sm);
        font-weight: 500;
        cursor: pointer;
        transition: var(--transition);
        position: relative;
        overflow: hidden;
    }
    
    .quantum-btn::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s;
    }
    
    .quantum-btn:hover::before {
        left: 100%;
    }
    
    .quantum-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 16px rgba(74, 144, 226, 0.3);
    }
    
    .quantum-btn-secondary {
        background: transparent;
        color: var(--primary-color);
        border: 2px solid var(--primary-color);
    }
    
    .quantum-btn-secondary:hover {
        background: var(--primary-color);
        color: white;
    }
    
    /* Paper Cards */
    .paper-card {
        background: var(--bg-card-light);
        border: 1px solid var(--border-light);
        border-radius: var(--border-radius);
        padding: 1.25rem;
        margin: 1rem 0;
        transition: var(--transition);
        position: relative;
    }
    
    .paper-card:hover {
        border-color: var(--primary-color);
        box-shadow: 0 8px 25px rgba(74, 144, 226, 0.15);
        transform: translateY(-1px);
    }
    
    .paper-title {
        font-family: var(--font-display);
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-primary-light);
        margin: 0 0 0.5rem 0;
    }
    
    .paper-authors {
        color: var(--text-secondary-light);
        font-size: 0.9rem;
        margin: 0.25rem 0;
    }
    
    .paper-meta {
        display: flex;
        gap: 1rem;
        margin: 0.75rem 0;
        font-size: 0.85rem;
    }
    
    .paper-tag {
        background: rgba(74, 144, 226, 0.1);
        color: var(--primary-color);
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    
    /* Cluster Visualization */
    .cluster-header {
        background: linear-gradient(135deg, #FF6B6B, #4ECDC4);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: var(--border-radius);
        margin: 1rem 0;
        position: relative;
        overflow: hidden;
    }
    
    .cluster-header::after {
        content: '';
        position: absolute;
        top: 0;
        right: -50px;
        width: 50px;
        height: 100%;
        background: linear-gradient(45deg, transparent, rgba(255,255,255,0.2), transparent);
        animation: clusterShine 3s infinite;
    }
    
    /* Knowledge Stream */
    .knowledge-stream {
        background: var(--bg-card-light);
        border: 1px solid var(--border-light);
        border-radius: var(--border-radius);
        padding: 1rem;
        margin: 1rem 0;
        position: relative;
    }
    
    .knowledge-stream::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(180deg, var(--accent-color), var(--primary-color));
        border-radius: 2px;
    }
    
    .stream-item {
        padding: 0.75rem 0;
        border-bottom: 1px solid rgba(74, 144, 226, 0.1);
    }
    
    .stream-item:last-child {
        border-bottom: none;
    }
    
    .stream-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        margin-right: 0.75rem;
        display: inline-block;
    }
    
    /* Quick Actions */
    .quick-actions {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.5rem;
        margin: 1rem 0;
    }
    
    .quick-action {
        background: rgba(74, 144, 226, 0.05);
        border: 1px solid rgba(74, 144, 226, 0.2);
        border-radius: var(--border-radius-sm);
        padding: 0.75rem;
        text-align: center;
        cursor: pointer;
        transition: var(--transition);
    }
    
    .quick-action:hover {
        background: rgba(74, 144, 226, 0.1);
        transform: scale(1.02);
    }
    
    /* Animations */
    @keyframes shimmer {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
    
    @keyframes statusShine {
        0% { transform: translate(-100%, -100%); }
        100% { transform: translate(100%, 100%); }
    }
    
    @keyframes progressShine {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(200%); }
    }
    
    @keyframes clusterShine {
        0% { transform: translateX(-100%); }
        50% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes slideUp {
        from { transform: translateY(20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    @keyframes glow {
        from { box-shadow: 0 0 5px var(--primary-color); }
        to { box-shadow: 0 0 20px var(--primary-color); }
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .quantum-header h1 {
            font-size: 1.8rem;
        }
        
        .status-grid {
            grid-template-columns: 1fr;
        }
        
        .quick-actions {
            grid-template-columns: 1fr;
        }
    }
    
    /* Streamlit Specific Overrides */
    .stSelectbox > div > div {
        background: var(--bg-card-light);
        border: 1px solid var(--border-light);
        border-radius: var(--border-radius-sm);
    }
    
    .stTextInput > div > div > input {
        background: var(--bg-card-light);
        border: 1px solid var(--border-light);
        border-radius: var(--border-radius-sm);
        color: var(--text-primary-light);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        color: white;
        border: none;
        border-radius: var(--border-radius-sm);
        transition: var(--transition);
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 16px rgba(74, 144, 226, 0.3);
    }
    
    /* Dark mode overrides */
    @media (prefers-color-scheme: dark) {
        .paper-title {
            color: var(--text-primary-dark);
        }
        
        .paper-authors {
            color: var(--text-secondary-dark);
        }
        
        .paper-card {
            background: var(--bg-card-dark);
            border-color: var(--border-dark);
        }
        
        .knowledge-stream {
            background: var(--bg-card-dark);
            border-color: var(--border-dark);
        }
    }
    </style>
    """
    
    st.markdown(css, unsafe_allow_html=True)