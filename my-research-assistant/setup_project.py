#!/usr/bin/env python3
"""
Academic Research Assistant - Automated Project Setup Script (Windows Compatible)
This script creates the complete project structure and all necessary files.

Usage: python setup_project.py
"""

import os
import sys
from pathlib import Path

def create_directory_structure():
    """Create the complete project directory structure"""
    
    directories = [
        "config",
        "data", 
        "models",
        "dashboard",
        "dashboard/components",
        "storage",
        "storage/papers",
        "storage/embeddings", 
        "storage/models"
    ]
    
    print("Creating directory structure...")
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  Created: {directory}/")
    
    # Create __init__.py files
    init_files = [
        "config/__init__.py",
        "data/__init__.py", 
        "models/__init__.py",
        "dashboard/__init__.py",
        "dashboard/components/__init__.py"
    ]
    
    for init_file in init_files:
        Path(init_file).touch()
        print(f"  Created: {init_file}")

def create_requirements_txt():
    """Create requirements.txt file"""
    requirements_content = """# Core dependencies
streamlit>=1.28.0
pandas>=1.5.0
numpy>=1.24.0
scikit-learn>=1.3.0

# APIs and data fetching
requests>=2.31.0
feedparser>=6.0.10
semanticscholar>=0.7.0
arxiv>=1.4.8

# NLP and embeddings
sentence-transformers>=2.2.2
transformers>=4.33.0
torch>=2.0.0

# Vector search and clustering  
faiss-cpu>=1.7.4
# faiss-gpu>=1.7.4  # Uncomment for GPU support

# Language models
huggingface-hub>=0.16.0
accelerate>=0.21.0
bitsandbytes>=0.41.0

# Visualization
plotly>=5.15.0
seaborn>=0.12.0
matplotlib>=3.7.0
altair>=5.0.0

# Utilities
python-dotenv>=1.0.0
tqdm>=4.65.0
pathlib>=1.0.0"""
    
    with open("requirements.txt", "w", encoding='utf-8') as f:
        f.write(requirements_content)
    print("Created: requirements.txt")

def create_env_example():
    """Create .env.example file"""
    env_content = """# Academic Research Assistant - Environment Configuration
# Copy this file to .env and customize as needed

# API Keys (Optional - increases rate limits)
# Get from: https://www.semanticscholar.org/product/api
SEMANTIC_SCHOLAR_API_KEY=your_api_key_here

# Model Configuration
SBERT_MODEL_NAME=all-MiniLM-L6-v2
LLAMA_MODEL_NAME=meta-llama/Llama-2-7b-chat-hf

# Performance Settings
USE_GPU=true
QUANTIZE_LLAMA=true
EMBEDDING_BATCH_SIZE=32

# Search Configuration
DEFAULT_MAX_PAPERS=50
DEFAULT_DAYS_BACK=365
ARXIV_RATE_LIMIT=30
SEMANTIC_SCHOLAR_RATE_LIMIT=100

# Storage Settings
CACHE_RESULTS=true
CACHE_EXPIRY_DAYS=7

# Clustering Settings
FAISS_INDEX_TYPE=IndexFlatL2
MIN_CLUSTER_SIZE=3
CLUSTERING_THRESHOLD=0.75

# Dashboard Settings
STREAMLIT_PORT=8501
DASHBOARD_THEME=light"""
    
    with open(".env.example", "w", encoding='utf-8') as f:
        f.write(env_content)
    print("Created: .env.example")

def create_config_settings():
    """Create config/settings.py file"""
    settings_content = '''"""
Configuration settings for Academic Research Assistant
"""
import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "storage"
PAPERS_DIR = DATA_DIR / "papers"
EMBEDDINGS_DIR = DATA_DIR / "embeddings"
MODELS_DIR = DATA_DIR / "models"

# Create directories if they don't exist
for dir_path in [DATA_DIR, PAPERS_DIR, EMBEDDINGS_DIR, MODELS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# API Configuration
ARXIV_BASE_URL = "http://export.arxiv.org/api/query"
SEMANTIC_SCHOLAR_BASE_URL = "https://api.semanticscholar.org/graph/v1"

# Default search parameters
DEFAULT_MAX_PAPERS = 100
DEFAULT_ARXIV_CATEGORIES = [
    "cs.AI",  # Artificial Intelligence
    "cs.LG",  # Machine Learning
    "cs.CL",  # Computation and Language
    "cs.CV",  # Computer Vision
    "cs.IR",  # Information Retrieval
    "stat.ML"  # Statistics - Machine Learning
]

# Model configurations
SBERT_MODEL_NAME = "all-MiniLM-L6-v2"  # 384 dimensions, good for clustering
LLAMA_MODEL_NAME = "meta-llama/Llama-2-7b-chat-hf"

# FAISS settings
FAISS_INDEX_TYPE = "IndexFlatL2"  # Use L2 distance for similarity
CLUSTERING_MIN_CLUSTER_SIZE = 3
CLUSTERING_THRESHOLD = 0.75

# Streamlit configuration
STREAMLIT_THEME = {
    "base": "light",
    "primaryColor": "#FF6B6B",
    "backgroundColor": "#FFFFFF",
    "secondaryBackgroundColor": "#F0F2F6",
    "textColor": "#262730"
}

# Research gap analysis prompts
RESEARCH_GAP_PROMPT = """
Analyze the following cluster of research papers and identify potential research gaps:

Papers in cluster:
{papers}

Please provide:
1. A brief summary of the main research themes in this cluster
2. Identify 3-5 potential research gaps or unexplored areas
3. Suggest novel research directions
4. Rate the novelty potential (1-10) for each suggested direction

Format your response as:
SUMMARY: [brief summary]
GAPS: [numbered list of gaps]
SUGGESTIONS: [numbered list with novelty ratings]
"""

PAPER_SUMMARY_PROMPT = """
Provide a concise academic summary of this paper:

Title: {title}
Abstract: {abstract}
Authors: {authors}

Summary should include:
- Main contribution
- Methodology
- Key findings
- Limitations mentioned
"""

# File extensions and formats
SUPPORTED_FORMATS = [".pdf", ".txt", ".json"]
EMBEDDINGS_FILE_FORMAT = "npy"
PAPERS_FILE_FORMAT = "json"

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Rate limiting (requests per minute)
ARXIV_RATE_LIMIT = 30
SEMANTIC_SCHOLAR_RATE_LIMIT = 100

# Cache settings
CACHE_EXPIRY_DAYS = 7
ENABLE_CACHING = True'''
    
    with open("config/settings.py", "w", encoding='utf-8') as f:
        f.write(settings_content)
    print("Created: config/settings.py")

def create_main_py():
    """Create main.py CLI interface"""
    main_content = '''"""
Main CLI application for Academic Research Assistant
Command-line interface for running the complete pipeline
"""
import argparse
import logging
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Import will be handled in the actual functions
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AcademicResearchPipeline:
    """
    Main pipeline class that orchestrates the complete research assistant workflow
    """
    
    def __init__(self):
        """Initialize the research pipeline"""
        print("Academic Research Assistant initialized!")
        print("Note: This is a demo version. Full implementation requires all component files.")
        
    def run_complete_pipeline(self, query: str, **kwargs) -> Dict:
        """Run complete pipeline (demo version)"""
        print(f"Running pipeline for query: {query}")
        print("Step 1: Would fetch papers from arXiv and Semantic Scholar")
        print("Step 2: Would generate SBERT embeddings")
        print("Step 3: Would cluster papers using FAISS")
        print("Step 4: Would analyze research gaps using Llama2")
        print("Step 5: Would save results")
        
        return {
            "query": query,
            "status": "demo_completed",
            "message": "This is a demo run. Install all components for full functionality."
        }

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description='Academic Research Assistant CLI')
    
    # Required arguments
    parser.add_argument('query', help='Research query string')
    
    # Optional arguments
    parser.add_argument('--max-papers', type=int, default=50,
                       help='Maximum papers per source (default: 50)')
    parser.add_argument('--no-arxiv', action='store_true',
                       help='Skip arXiv search')
    parser.add_argument('--no-semantic-scholar', action='store_true', 
                       help='Skip Semantic Scholar search')
    parser.add_argument('--clustering-method', choices=['kmeans', 'community', 'hierarchical'],
                       default='kmeans', help='Clustering method (default: kmeans)')
    parser.add_argument('--no-gap-analysis', action='store_true',
                       help='Skip research gap analysis')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize pipeline
    pipeline = AcademicResearchPipeline()
    
    try:
        results = pipeline.run_complete_pipeline(
            query=args.query,
            max_papers=args.max_papers,
            use_arxiv=not args.no_arxiv,
            use_semantic_scholar=not args.no_semantic_scholar,
            clustering_method=args.clustering_method,
            analyze_gaps=not args.no_gap_analysis
        )
        
        # Print results
        print("\\n" + "="*60)
        print("RESULTS SUMMARY")
        print("="*60)
        print(f"Query: {results['query']}")
        print(f"Status: {results['status']}")
        print(f"Message: {results['message']}")
        print("\\nDemo completed successfully!")
        print("\\nTo get full functionality:")
        print("1. Install all dependencies: pip install -r requirements.txt")
        print("2. Copy all component files to their respective directories")
        print("3. Run: streamlit run dashboard/app.py")
        
    except KeyboardInterrupt:
        print("\\nPipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\\nPipeline failed: {str(e)}")
        print("This is expected in demo mode. Copy all files for full functionality.")
        sys.exit(1)

if __name__ == "__main__":
    main()'''
    
    with open("main.py", "w", encoding='utf-8') as f:
        f.write(main_content)
    print("Created: main.py")

def create_dashboard_app():
    """Create dashboard/app.py - Streamlit interface"""
    dashboard_content = '''"""
Academic Research Assistant - Streamlit Dashboard
"""
import streamlit as st
import pandas as pd
import plotly.express as px

# Configure page
st.set_page_config(
    page_title="Academic Research Assistant",
    page_icon="📊",
    layout="wide"
)

def main():
    """Main dashboard function"""
    
    # Header
    st.markdown("""
    <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 10px; margin-bottom: 2rem;">
        <h1 style="color: white; margin: 0;">Academic Research Assistant</h1>
        <p style="color: white; margin: 0;">Semi-autonomous literature survey with clustering and gap analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("Control Panel")
        
        search_query = st.text_input(
            "Research Query",
            value="machine learning transformers",
            help="Enter keywords for paper search"
        )
        
        max_papers = st.slider("Max Papers per Source", 20, 200, 50)
        
        use_arxiv = st.checkbox("arXiv", value=True)
        use_semantic = st.checkbox("Semantic Scholar", value=True)
        
        if st.button("Fetch Papers", type="primary"):
            st.info("Demo Mode: This would fetch papers from APIs")
        
        if st.button("Process All"):
            st.info("Demo Mode: This would run the complete pipeline")
    
    # Main content
    st.subheader("Dashboard Overview")
    
    # Demo metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Papers", "127")
    with col2:
        st.metric("Authors", "342") 
    with col3:
        st.metric("Clusters", "8")
    with col4:
        st.metric("Gap Analyses", "8")
    
    # Demo content
    st.info("""
    **Demo Mode Active**
    
    This is a demo version of the Academic Research Assistant dashboard.
    
    **To activate full functionality:**
    1. Install dependencies: `pip install -r requirements.txt`
    2. Copy all component files (arxiv_fetcher.py, embedding_generator.py, etc.)
    3. Restart the dashboard
    
    **Full Features Include:**
    - Real paper fetching from arXiv and Semantic Scholar
    - SBERT embedding generation
    - FAISS clustering
    - Llama2 research gap analysis
    - Interactive visualizations
    - Result export and saving
    """)
    
    # Demo visualization
    st.subheader("Sample Results")
    
    # Sample data for demo
    demo_data = pd.DataFrame({
        'year': [2018, 2019, 2020, 2021, 2022, 2023, 2024],
        'papers': [15, 23, 31, 28, 42, 35, 18]
    })
    
    fig = px.line(demo_data, x='year', y='papers', 
                  title='Papers by Year (Demo Data)')
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.markdown("**Built with Streamlit • Academic Research Assistant v1.0**")

if __name__ == "__main__":
    main()'''
    
    with open("dashboard/app.py", "w", encoding='utf-8') as f:
        f.write(dashboard_content)
    print("Created: dashboard/app.py")

def create_readme():
    """Create README.md file"""
    readme_content = """# Academic Research Paper Assistant

**Semi-autonomous literature survey tool with clustering and research gap analysis**

A comprehensive AI-powered research assistant that fetches academic papers, clusters them semantically, and identifies research gaps using modern NLP techniques.

## Features

- **Multi-source Paper Fetching**: Integrates arXiv and Semantic Scholar APIs
- **Semantic Embeddings**: Uses SBERT for high-quality paper representations
- **Intelligent Clustering**: FAISS-powered similarity search and clustering
- **Research Gap Analysis**: Llama2-based analysis for identifying unexplored areas
- **Interactive Dashboard**: Streamlit-powered web interface
- **CLI Interface**: Command-line tool for automated processing

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch Dashboard
```bash
streamlit run dashboard/app.py
```

### 3. Or Use CLI
```bash
python main.py "machine learning transformers" --max-papers 50
```

## Technology Stack

- **Paper Sources**: arXiv API, Semantic Scholar API
- **Embeddings**: SBERT (all-MiniLM-L6-v2)
- **Clustering**: FAISS + scikit-learn
- **Gap Analysis**: Llama2-7B (quantized)
- **Dashboard**: Streamlit
- **Data Processing**: pandas, numpy

## Project Structure

```
Academic-Research-Assistant/
├── README.md
├── requirements.txt
├── main.py                    # CLI interface
├── config/
│   └── settings.py           # Configuration
├── data/                     # Data fetching modules
├── models/                   # AI/ML components  
├── dashboard/
│   └── app.py               # Streamlit dashboard
└── storage/                 # Data storage
```

## Usage Examples

### Web Dashboard
1. Launch: `streamlit run dashboard/app.py`
2. Enter query: "transformer attention mechanisms"
3. Configure parameters
4. Click "Process All"
5. Explore results

### Command Line
```bash
# Basic usage
python main.py "computer vision deep learning"

# Advanced options
python main.py "NLP transformers" \\
  --max-papers 100 \\
  --clustering-method kmeans \\
  --no-gap-analysis
```

## Expected Results

The system generates:
- **Paper Collections**: Deduplicated papers from multiple sources
- **Semantic Clusters**: Groups of related research papers
- **Research Gap Analysis**: Identified unexplored research directions
- **Novelty Ratings**: Potential impact scores for suggested research

## Configuration

Customize settings in `config/settings.py`:
- API endpoints and rate limits
- Model configurations (SBERT, Llama2)
- Clustering parameters
- Output formats

## Prerequisites

- Python 3.8+
- 4GB+ RAM (8GB+ recommended)
- Internet connection for APIs and model downloads
- Optional: CUDA GPU for faster processing

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Submit pull request

## License

MIT License - see LICENSE file for details.

## Educational Value

This project demonstrates:
- Modern NLP pipeline development
- API integration and data processing
- Machine learning model deployment
- Full-stack application development
- Academic research automation

---

**Star this repository if you find it useful!**

**Happy researching!**"""
    
    with open("README.md", "w", encoding='utf-8') as f:
        f.write(readme_content)
    print("Created: README.md")

def create_component_files_info():
    """Create information file about missing components"""
    info_content = """# Component Files Information

This project setup script has created the basic structure and core files.

## Files Created:
- requirements.txt
- .env.example
- config/settings.py
- main.py (demo version)
- dashboard/app.py (demo version)
- README.md
- Directory structure

## Additional Files Needed for Full Functionality:

To get the complete system working, you'll also need these component files:

### Data Collection:
- `data/arxiv_fetcher.py` - arXiv API integration
- `data/semantic_scholar_fetcher.py` - Semantic Scholar API
- `data/data_processor.py` - Data cleaning utilities

### AI/ML Models:
- `models/embedding_generator.py` - SBERT embeddings
- `models/clustering.py` - FAISS clustering
- `models/llm_analyzer.py` - Llama2 analysis

## Next Steps:

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Test Current Setup:**
   ```bash
   python main.py "test query" --verbose
   streamlit run dashboard/app.py
   ```

3. **Add Component Files:**
   - Copy the additional Python files from the previous conversation
   - Place them in their respective directories

4. **Full Testing:**
   ```bash
   python main.py "machine learning" --max-papers 20
   ```

## Demo Mode Features:

The current setup includes demo versions that show:
- Project structure
- CLI argument parsing  
- Streamlit dashboard layout
- Basic functionality flow
- Installation verification

This gives you a working foundation to build upon!
"""
    
    with open("COMPONENT_INFO.md", "w", encoding='utf-8') as f:
        f.write(info_content)
    print("Created: COMPONENT_INFO.md")

def main():
    """Main setup function"""
    print("Academic Research Assistant - Project Setup")
    print("=" * 50)
    
    try:
        # Create directory structure
        create_directory_structure()
        
        # Create core files
        create_requirements_txt()
        create_env_example()
        create_config_settings()
        create_main_py()
        create_dashboard_app()
        create_readme()
        create_component_files_info()
        
        print("\n" + "=" * 50)
        print("PROJECT SETUP COMPLETE!")
        print("=" * 50)
        
        print("\nCreated project structure with:")
        print("  - Complete directory structure")
        print("  - requirements.txt with all dependencies")
        print("  - Configuration system")
        print("  - Demo CLI interface")
        print("  - Demo Streamlit dashboard")
        print("  - Documentation")
        
        print("\nNext Steps:")
        print("1. Install dependencies:")
        print("   pip install -r requirements.txt")
        print("\n2. Test the demo:")
        print("   python main.py 'test query'")
        print("   streamlit run dashboard/app.py")
        print("\n3. Read COMPONENT_INFO.md for full setup instructions")
        
        print("\nFull documentation available in README.md")
        print("\nHappy researching!")
        
    except Exception as e:
        print(f"\nSetup failed: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())