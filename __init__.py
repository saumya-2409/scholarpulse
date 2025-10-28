"""
Module initialization for src package
"""

# Import main classes
from .fetchers import PaperFetcher
from .summarizer import PaperSummarizer  
from .clustering import PaperClusterer
from .utils import deduplicate_papers, categorize_papers, validate_paper_data

__all__ = [
    'PaperFetcher',
    'PaperSummarizer', 
    'PaperClusterer',
    'deduplicate_papers',
    'categorize_papers',
    'validate_paper_data'
]
