"""
Paper Clustering - Group papers by research themes using embeddings
"""

import numpy as np
from typing import List, Dict, Optional
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from embedding_utils import load_embedding_model
from collections import Counter
import re

class PaperClusterer:
    """Cluster research papers by topic and theme"""
    
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.embedding_available = False
        
        # Using the shared singleton model
        try:
            self.model = load_embedding_model()
            if self.model:
                self.embedding_available = True
        except Exception as e:
            print(f"Clustering could not load model: {e}")
            self.embedding_available = False
        
        # Fallback to TF-IDF
        if not self.embedding_available:
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
    
    def cluster_papers(self, papers: List[Dict], n_clusters: Optional[int] = None) -> Dict[int, Dict]:
        """
        Cluster papers and return cluster information
        
        Returns:
            Dict mapping cluster_id to cluster info with name, description, etc.
        """
        papers = [p for p in papers if p.get("accessibility") != "inaccessible"]
        
        if len(papers) < 2:
            return {0: {'name': 'All Papers', 'description': 'Single cluster with all papers', 'papers': papers}}
        
        # Prepare text for clustering
        texts = []
        for paper in papers:
            # Combine title, abstract, and keywords for clustering
            text_parts = []
            
            if paper.get('title'):
                text_parts.append(paper['title'])
            
            if paper.get('abstract'):
                text_parts.append(paper['abstract'][:500])  # Limit abstract length
            
            if paper.get('venue'):
                text_parts.append(paper['venue'])
            
            texts.append(' '.join(text_parts))
        
        # Generate embeddings or TF-IDF vectors
        if self.embedding_available:
            embeddings = self._generate_embeddings(texts)
        else:
            embeddings = self._generate_tfidf_vectors(texts)
        
        # Determine optimal number of clusters
        if n_clusters is None:
            n_clusters = min(max(2, len(papers) // 5), 8)  # 2-8 clusters based on paper count
        
        # Perform clustering
        if embeddings.shape[0] > n_clusters:
            clusterer = AgglomerativeClustering(n_clusters=n_clusters, linkage='ward')
            cluster_labels = clusterer.fit_predict(embeddings)
        else:
            # If too few papers, assign each to its own cluster
            cluster_labels = list(range(len(papers)))
            n_clusters = len(papers)
        
        # Assign cluster labels to papers
        for paper, label in zip(papers, cluster_labels):
            paper['cluster'] = int(label)
        
        # Generate cluster information
        clusters = {}
        for cluster_id in range(n_clusters):
            cluster_papers = [p for p, label in zip(papers, cluster_labels) if label == cluster_id]
            
            if cluster_papers:
                cluster_info = self._analyze_cluster(cluster_id, cluster_papers)
                clusters[cluster_id] = cluster_info
        
        return clusters
    
    def _generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate sentence embeddings using SentenceTransformer"""
        try:
            embeddings = self.model.encode(texts, show_progress_bar=False)
            return embeddings
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            # Fallback to TF-IDF
            return self._generate_tfidf_vectors(texts)
    
    def _generate_tfidf_vectors(self, texts: List[str]) -> np.ndarray:
        """Generate TF-IDF vectors as fallback"""
        try:
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            return tfidf_matrix.toarray()
        except Exception as e:
            print(f"Error generating TF-IDF vectors: {e}")
            # Return random vectors as last resort
            return np.random.rand(len(texts), 100)
    
    def _analyze_cluster(self, cluster_id: int, papers: List[Dict]) -> Dict:
        """Analyze a cluster to generate name and description"""
        
        # Extract all text from papers in cluster
        all_text = []
        titles = []
        abstracts = []
        venues = []
        years = []
        
        for paper in papers:
            if paper.get('title'):
                titles.append(paper['title'])
                all_text.append(paper['title'])
            
            if paper.get('abstract'):
                abstracts.append(paper['abstract'])
                all_text.append(paper['abstract'])
            
            if paper.get('venue'):
                venues.append(paper['venue'])
            
            if paper.get('year'):
                years.append(paper['year'])
        
        # Find common themes and keywords
        cluster_name = self._generate_cluster_name(titles, all_text)
        cluster_description = self._generate_cluster_description(papers, all_text, self.query if hasattr(self, 'query') else "")
        
        # Calculate cluster statistics
        avg_year = np.mean(years) if years else None
        citation_counts = [p.get('citations', 0) for p in papers]
        avg_citations = np.mean(citation_counts) if citation_counts else 0
        
        return {
            'name': cluster_name,
            'description': cluster_description,
            'paper_count': len(papers),
            'avg_year': int(avg_year) if avg_year else 0,
            'avg_citations': round(avg_citations, 1),
            'top_venues': self._get_top_venues(venues),
            'papers': papers
        }
    
    def _generate_cluster_name(self, titles: List[str], all_text: List[str]) -> str:
        """Generate a descriptive name for the cluster"""
        
        # Extract common keywords from titles
        title_text = ' '.join(titles).lower()
        
        # Define research area keywords
        research_areas = {
            'Machine Learning': ['machine learning', 'neural', 'deep learning', 'training', 'model', 'algorithm'],
            'Computer Vision': ['image', 'vision', 'visual', 'detection', 'recognition', 'computer vision'],
            'Natural Language Processing': ['language', 'text', 'nlp', 'semantic', 'linguistic', 'bert', 'gpt'],
            'Artificial Intelligence': ['ai', 'intelligence', 'cognitive', 'reasoning', 'artificial'],
            'Data Science': ['data', 'mining', 'analysis', 'pattern', 'big data', 'analytics'],
            'Robotics': ['robot', 'autonomous', 'control', 'manipulation', 'robotics'],
            'Healthcare AI': ['medical', 'health', 'clinical', 'diagnosis', 'healthcare'],
            'Cybersecurity': ['security', 'cyber', 'encryption', 'privacy', 'malware'],
            'Human-Computer Interaction': ['hci', 'interaction', 'interface', 'user', 'usability'],
            'Software Engineering': ['software', 'engineering', 'development', 'programming']
        }
        
        # Score each area
        area_scores = {}
        for area, keywords in research_areas.items():
            score = sum(1 for keyword in keywords if keyword in title_text)
            if score > 0:
                area_scores[area] = score
        
        if area_scores:
            # Return highest scoring area
            best_area = max(area_scores.items(), key=lambda x: x[1])[0]
            return best_area
        
        # Fallback: extract most common meaningful words from titles
        common_words = self._extract_common_words(title_text)
        if common_words:
            return f"{common_words[0].title()} Research"
        
        return "Research Cluster"
    
    def generate_cluster_description(self, papers: List[Dict], all_text: List[str], query: str = "") -> str:
        paper_count = len(papers)
        # Get time range...
        years = [p.get('year') for p in papers if p.get('year')]
        if years:
            min_year = min(years)
            max_year = max(years)
            year_range = f"{min_year}-{max_year}" if min_year != max_year else str(min_year)
        else:
            year_range = "recent"
        # Get common research focus, biased toward query...
        combined_text = ' '.join(all_text[:3])  # Use first 3 texts
        focus_keywords = self._extract_common_words(combined_text.lower())
        if query:
            # Incorporate query keywords for relevance
            query_words = re.findall(r'\w+', query.lower())
            focus_keywords = [kw for kw in focus_keywords if any(qw in kw for qw in query_words)] or focus_keywords
            focus = f"relevant to '{query}' by {' '.join(focus_keywords[:3])}"
        else:
            focus = f"focusing on {' '.join(focus_keywords[:3])}" if focus_keywords else "covering various research aspects"
        return f"Collection of {paper_count} papers from {year_range}, {focus}"

    def _extract_common_words(self, text: str, min_length: int = 4) -> List[str]:
        """Extract common meaningful words from text"""
        
        # Remove common stop words and short words
        stop_words = {
            'the', 'and', 'for', 'are', 'with', 'this', 'that', 'from', 'they', 'have',
            'been', 'were', 'said', 'each', 'which', 'their', 'time', 'will', 'about',
            'using', 'based', 'approach', 'method', 'study', 'analysis', 'research',
            'paper', 'work', 'results', 'system', 'systems', 'new', 'novel'
        }
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        
        # Filter words
        meaningful_words = [
            word for word in words 
            if len(word) >= min_length and word not in stop_words
        ]
        
        # Count frequency
        word_counts = Counter(meaningful_words)
        
        # Return most common words
        return [word for word, count in word_counts.most_common(10) if count > 1]
    
    def _get_top_venues(self, venues: List[str], top_n: int = 3) -> List[str]:
        """Get most common venues in the cluster"""
        if not venues:
            return []
        
        venue_counts = Counter(venues)
        return [venue for venue, count in venue_counts.most_common(top_n)]
