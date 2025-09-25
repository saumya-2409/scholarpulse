"""
FAISS-based clustering for research papers
"""
import faiss
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging
from pathlib import Path
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import pickle
from datetime import datetime
import sys
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import (
    FAISS_INDEX_TYPE, CLUSTERING_MIN_CLUSTER_SIZE, 
    CLUSTERING_THRESHOLD, EMBEDDINGS_DIR
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FaissClusterer:
    """
    FAISS-based clustering system for research papers
    """
    
    def __init__(self, embedding_dim: int, index_type: str = FAISS_INDEX_TYPE):
        self.embedding_dim = embedding_dim
        self.index_type = index_type
        self.index = None
        self.paper_ids = []
        self.clusters = {}
        
        logger.info(f"Initializing FAISS clusterer with dimension {embedding_dim}")
        self._initialize_index()
    
    def _initialize_index(self):
        """Initialize FAISS index"""
        try:
            if self.index_type == "IndexFlatL2":
                self.index = faiss.IndexFlatL2(self.embedding_dim)
            else:
                self.index = faiss.IndexFlatL2(self.embedding_dim)
            
            # Wrap with ID map for tracking paper IDs
            self.index = faiss.IndexIDMap(self.index)
            
            logger.info(f"Initialized FAISS index: {self.index_type}")
            
        except Exception as e:
            logger.error(f"Error initializing FAISS index: {str(e)}")
            raise
    
    def add_embeddings(self, embeddings: np.ndarray, paper_ids: List[str]):
        """Add embeddings to FAISS index"""
        if embeddings.shape[0] != len(paper_ids):
            raise ValueError("Number of embeddings must match number of paper IDs")
        
        try:
            embeddings = embeddings.astype(np.float32)
            
            start_id = len(self.paper_ids)
            ids = np.arange(start_id, start_id + len(paper_ids)).astype(np.int64)
            
            self.index.add_with_ids(embeddings, ids)
            self.paper_ids.extend(paper_ids)
            
            logger.info(f"Added {len(embeddings)} embeddings to FAISS index. Total: {self.index.ntotal}")
            
        except Exception as e:
            logger.error(f"Error adding embeddings to index: {str(e)}")
            raise
    
    def cluster_papers(
        self, 
        embeddings: np.ndarray,
        paper_ids: List[str],
        method: str = 'kmeans',
        n_clusters: int = None,
        **kwargs
    ) -> Dict[int, List[str]]:
        """Cluster papers using various methods"""
        logger.info(f"Clustering {len(embeddings)} papers using method: {method}")
        
        if method == 'kmeans':
            return self._cluster_kmeans(embeddings, paper_ids, n_clusters, **kwargs)
        else:
            return self._cluster_kmeans(embeddings, paper_ids, n_clusters, **kwargs)
    
    def _cluster_kmeans(
        self, 
        embeddings: np.ndarray, 
        paper_ids: List[str],
        n_clusters: int = None,
        **kwargs
    ) -> Dict[int, List[str]]:
        """K-means clustering with automatic cluster number selection"""
        if n_clusters is None:
            n_clusters = self._find_optimal_clusters(embeddings)
        
        try:
            kmeans = KMeans(
                n_clusters=n_clusters, 
                random_state=42,
                n_init=10,
                **kwargs
            )
            
            cluster_labels = kmeans.fit_predict(embeddings)
            
            # Calculate silhouette score
            if len(set(cluster_labels)) > 1:
                silhouette_avg = silhouette_score(embeddings, cluster_labels)
                logger.info(f"K-means clustering completed. Silhouette score: {silhouette_avg:.3f}")
            
            # Organize results
            clusters = {}
            for i, label in enumerate(cluster_labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(paper_ids[i])
            
            # Filter out small clusters
            filtered_clusters = {
                k: v for k, v in clusters.items() 
                if len(v) >= CLUSTERING_MIN_CLUSTER_SIZE
            }
            
            logger.info(f"Created {len(filtered_clusters)} clusters (min size: {CLUSTERING_MIN_CLUSTER_SIZE})")
            self.clusters = filtered_clusters
            
            return filtered_clusters
            
        except Exception as e:
            logger.error(f"Error in K-means clustering: {str(e)}")
            raise
    
    def _find_optimal_clusters(self, embeddings: np.ndarray, max_clusters: int = None) -> int:
        """Find optimal number of clusters using elbow method"""
        n_samples = len(embeddings)
        
        if max_clusters is None:
            max_clusters = min(20, n_samples // 5)
        
        min_clusters = 2
        max_clusters = max(min_clusters, min(max_clusters, n_samples // CLUSTERING_MIN_CLUSTER_SIZE))
        
        if max_clusters <= min_clusters:
            return min_clusters
        
        logger.info(f"Finding optimal clusters between {min_clusters} and {max_clusters}")
        
        try:
            silhouette_scores = []
            cluster_range = range(min_clusters, max_clusters + 1)
            
            for n_clusters in cluster_range:
                kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                cluster_labels = kmeans.fit_predict(embeddings)
                
                score = silhouette_score(embeddings, cluster_labels)
                silhouette_scores.append(score)
            
            optimal_idx = np.argmax(silhouette_scores)
            optimal_clusters = list(cluster_range)[optimal_idx]
            
            logger.info(f"Optimal number of clusters: {optimal_clusters} (silhouette score: {silhouette_scores[optimal_idx]:.3f})")
            return optimal_clusters
            
        except Exception as e:
            logger.warning(f"Error finding optimal clusters, using default: {str(e)}")
            return min(10, n_samples // 5)
    
    def search_similar_papers(self, query_embedding: np.ndarray, k: int = 10) -> List[Tuple[str, float]]:
        """Search for similar papers using FAISS index"""
        try:
            if self.index.ntotal == 0:
                logger.warning("FAISS index is empty")
                return []
            
            query = query_embedding.reshape(1, -1).astype(np.float32)
            distances, indices = self.index.search(query, k)
            
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx != -1 and idx < len(self.paper_ids):
                    paper_id = self.paper_ids[idx]
                    results.append((paper_id, float(distance)))
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar papers: {str(e)}")
            return []
    
    def save_clusters(self, filepath: str = None) -> str:
        """Save clustering results to disk"""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = EMBEDDINGS_DIR / f"clusters_{timestamp}.pkl"
        
        try:
            cluster_data = {
                'clusters': self.clusters,
                'paper_ids': self.paper_ids,
                'embedding_dim': self.embedding_dim,
                'index_type': self.index_type,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(cluster_data, f)
            
            logger.info(f"Saved clustering results to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error saving clusters: {str(e)}")
            raise