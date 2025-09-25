"""
SBERT embeddings generator for research papers
"""
from sentence_transformers import SentenceTransformer
import numpy as np
import torch
from typing import List, Dict, Optional, Tuple
import logging
from pathlib import Path
from tqdm import tqdm
import sys
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import SBERT_MODEL_NAME, EMBEDDINGS_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """
    Generates semantic embeddings for research papers using SBERT
    """
    
    def __init__(self, model_name: str = SBERT_MODEL_NAME, device: str = None):
        self.model_name = model_name
        
        if device is None:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.device = device
        
        logger.info(f"Loading SBERT model: {model_name} on device: {device}")
        
        try:
            self.model = SentenceTransformer(model_name, device=device)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded successfully. Embedding dimension: {self.embedding_dim}")
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise
    
    def generate_paper_embeddings(self, papers: List[Dict], text_field: str = 'combined_text') -> Tuple[np.ndarray, List[str]]:
        """
        Generate embeddings for a list of papers
        """
        logger.info(f"Generating embeddings for {len(papers)} papers using field: {text_field}")
        
        texts = []
        paper_ids = []
        
        for paper in papers:
            text = self._extract_text(paper, text_field)
            if text.strip():
                texts.append(text)
                paper_ids.append(paper.get('id', paper.get('arxiv_id', paper.get('semantic_scholar_id', str(len(paper_ids))))))
        
        if not texts:
            logger.warning("No valid texts found for embedding generation")
            return np.array([]), []
        
        logger.info(f"Processing {len(texts)} valid papers")
        
        try:
            # Generate embeddings in batches
            batch_size = 32
            embeddings = []
            
            for i in tqdm(range(0, len(texts), batch_size), desc="Generating embeddings"):
                batch_texts = texts[i:i + batch_size]
                batch_embeddings = self.model.encode(
                    batch_texts,
                    convert_to_numpy=True,
                    show_progress_bar=False,
                    normalize_embeddings=True
                )
                embeddings.append(batch_embeddings)
            
            all_embeddings = np.vstack(embeddings)
            
            logger.info(f"Generated embeddings shape: {all_embeddings.shape}")
            return all_embeddings, paper_ids
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    def _extract_text(self, paper: Dict, text_field: str) -> str:
        """Extract text from paper based on specified field"""
        if text_field == 'title':
            return paper.get('title', '')
        
        elif text_field == 'abstract':
            return paper.get('abstract', '')
        
        elif text_field == 'combined_text':
            title = paper.get('title', '')
            abstract = paper.get('abstract', '')
            combined = f"{title}. {abstract}" if abstract else title
            return combined
        
        else:
            return paper.get(text_field, '')
    
    def save_embeddings(self, embeddings: np.ndarray, paper_ids: List[str], filename: str = None) -> str:
        """Save embeddings to disk"""
        if filename is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"embeddings_{self.model_name.replace('/', '_')}_{timestamp}"
        
        embeddings_path = EMBEDDINGS_DIR / f"{filename}.npz"
        
        metadata = {
            'model_name': self.model_name,
            'embedding_dim': self.embedding_dim,
            'num_papers': len(paper_ids),
            'paper_ids': paper_ids,
            'device': self.device
        }
        
        try:
            np.savez_compressed(
                embeddings_path,
                embeddings=embeddings,
                **metadata
            )
            
            logger.info(f"Saved embeddings to {embeddings_path}")
            return str(embeddings_path)
            
        except Exception as e:
            logger.error(f"Error saving embeddings: {str(e)}")
            raise
    
    def load_embeddings(self, filepath: str) -> Tuple[np.ndarray, List[str], Dict]:
        """Load embeddings from disk"""
        try:
            data = np.load(filepath, allow_pickle=True)
            
            embeddings = data['embeddings']
            paper_ids = data['paper_ids'].tolist() if 'paper_ids' in data else []
            
            metadata = {}
            for key in data.files:
                if key not in ['embeddings', 'paper_ids']:
                    metadata[key] = data[key].item() if data[key].ndim == 0 else data[key]
            
            logger.info(f"Loaded embeddings from {filepath}: shape {embeddings.shape}")
            return embeddings, paper_ids, metadata
            
        except Exception as e:
            logger.error(f"Error loading embeddings from {filepath}: {str(e)}")
            raise