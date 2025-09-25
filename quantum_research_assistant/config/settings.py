"""
Application Settings and Configuration
"""

# Application Information
APP_NAME = "Quantum Field: Academic Research Assistant"
APP_TAGLINE = "Unveiling Knowledge, Accelerating Discovery"
VERSION = "2.0.0"

# Data Sources Configuration
DEFAULT_ARXIV_CATEGORIES = [
    'cs.AI', 'cs.CL', 'cs.CV', 'cs.LG', 'cs.NE', 
    'stat.ML', 'physics.comp-ph', 'math.OC'
]

AVAILABLE_SOURCES = {
    'arxiv': {
        'name': 'arXiv',
        'icon': '🔬',
        'description': 'Preprint repository for physics, mathematics, CS, etc.',
        'max_papers_default': 50,
        'enabled': True
    },
    'semantic_scholar': {
        'name': 'Semantic Scholar',
        'icon': '🧠',
        'description': 'AI-powered academic search engine',
        'max_papers_default': 50,
        'enabled': True
    },
    'google_scholar': {
        'name': 'Google Scholar',
        'icon': '🔍',
        'description': 'Comprehensive academic search',
        'max_papers_default': 30,
        'enabled': True
    },
    'ieee': {
        'name': 'IEEE Xplore',
        'icon': '⚡',
        'description': 'Engineering and technology research',
        'max_papers_default': 25,
        'enabled': True
    },
    'acm': {
        'name': 'ACM Digital Library',
        'icon': '💻',
        'description': 'Computing and IT research',
        'max_papers_default': 25,
        'enabled': True
    },
    'pubmed': {
        'name': 'PubMed',
        'icon': '🏥',
        'description': 'Biomedical and life sciences',
        'max_papers_default': 30,
        'enabled': True
    }
}

# Analysis Configuration
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CLUSTERING_METHODS = ['kmeans', 'hierarchical', 'dbscan']
DEFAULT_CLUSTER_COUNT = 5
MAX_PAPERS_PER_ANALYSIS = 200

# UI Configuration
PAPERS_PER_PAGE = 20
MAX_DISPLAY_TITLE_LENGTH = 120
MAX_ABSTRACT_PREVIEW_LENGTH = 500

# Export Configuration
SUPPORTED_EXPORT_FORMATS = ['json', 'csv', 'pdf', 'markdown']
MAX_EXPORT_SIZE_MB = 50

# Rate Limiting
RATE_LIMITS = {
    'arxiv': 3.0,  # requests per second
    'semantic_scholar': 1.0,
    'google_scholar': 0.5,
    'ieee': 1.0,
    'acm': 1.0,
    'pubmed': 3.0
}

# File Paths
DATA_DIR = "data"
CACHE_DIR = "cache"
EXPORT_DIR = "exports"
ASSETS_DIR = "assets"

# Feature Flags
FEATURES = {
    'auto_analysis': True,
    'reading_order': True,
    'gap_analysis': True,
    'pdf_processing': False,  # Future feature
    'collaborative_mode': False,  # Future feature
    'real_time_updates': False  # Future feature
}