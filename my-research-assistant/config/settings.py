"""
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
ENABLE_CACHING = True