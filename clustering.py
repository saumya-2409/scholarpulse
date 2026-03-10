"""
Paper Clustering - IMPROVED VERSION
Changes made vs original:
  1. UMAP dimensionality reduction before clustering (reduces 384-dim embeddings to 10-dim)
  2. Silhouette score to automatically pick the best number of clusters (no more guessing)
  3. LLM-based cluster naming via Groq API (replaces hardcoded keyword dictionary)
"""

import os
import re
import time
import numpy as np
from typing import List, Dict, Optional
from collections import Counter

from sklearn.cluster import AgglomerativeClustering
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score

from embedding_utils import load_embedding_model

# Try to import UMAP - gracefully skip if not installed
try:
    import umap
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False
    print("[Clustering] umap-learn not installed. Skipping dimensionality reduction.")

# Try to import Groq for LLM-based naming
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("[Clustering] groq not installed. LLM naming disabled.")


def _get_groq_client():
    """Load Groq client using the same API key as summarizer.py"""
    if not GROQ_AVAILABLE:
        return None
    api_key = None
    try:
        import streamlit as st
        if "GROQ_API_KEY" in st.secrets:
            api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        pass
    if not api_key:
        api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)


def _llm_generate_cluster_name(titles: List[str], groq_client) -> str:
    """
    Ask the LLM (LLaMA via Groq) to generate a short, meaningful research theme name
    based on the top paper titles in this cluster.

    WHY THIS IS BETTER:
      The old code had a hardcoded Python dictionary mapping keywords like 'neural' → 'Machine Learning'.
      That means if a cluster was about 'federated learning on medical devices', it would just say
      'Machine Learning' — not very helpful or specific. The LLM reads the actual titles and
      comes up with a tailored, context-aware name like 'Federated Learning for Healthcare IoT'.
    """
    if not groq_client or not titles:
        return _fallback_keyword_name(titles)

    # Only send top 5 titles to save tokens / avoid rate limits
    sample_titles = titles[:5]
    titles_text = "\n".join(f"- {t}" for t in sample_titles)

    prompt = (
        "You are a research taxonomy expert. Given the following research paper titles, "
        "identify the single most specific research theme that covers ALL of them. "
        "Reply with ONLY a short 3-7 word theme name. No explanation, no punctuation at the end.\n\n"
        f"Paper titles:\n{titles_text}\n\n"
        "Theme name:"
    )

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a concise research taxonomy assistant. Reply only with the theme name."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=20,
        )
        name = response.choices[0].message.content.strip()
        # Clean up any stray quotes or punctuation
        name = re.sub(r'^[\"\']|[\"\']$', '', name).strip(" .")
        if name:
            return name
    except Exception as e:
        print(f"[Clustering] LLM naming failed: {e}. Falling back to keywords.")
        time.sleep(1)  # Brief pause to avoid hammering rate limits

    return _fallback_keyword_name(titles)


def _fallback_keyword_name(titles: List[str]) -> str:
    """
    Simple keyword-based fallback for when Groq is unavailable.
    Better than the old version because it uses actual title words instead of a hardcoded map.
    """
    if not titles:
        return "Research Cluster"

    stop_words = {
        'the', 'and', 'for', 'are', 'with', 'this', 'that', 'from', 'they',
        'have', 'been', 'were', 'using', 'based', 'approach', 'method', 'study',
        'analysis', 'research', 'paper', 'work', 'results', 'novel', 'deep', 'via'
    }
    all_words = []
    for title in titles:
        words = re.findall(r'\b[a-zA-Z]{4,}\b', title.lower())
        all_words.extend([w for w in words if w not in stop_words])

    if not all_words:
        return "Research Cluster"

    counts = Counter(all_words)
    top_words = [w.title() for w, _ in counts.most_common(3)]
    return " & ".join(top_words) if top_words else "Research Cluster"


class PaperClusterer:
    """
    Improved research paper clustering system.

    Three key improvements over the original:
    -------------------------------------------
    1. UMAP Dimensionality Reduction
       - The sentence transformer produces 384-number vectors (embeddings) for each paper.
       - 384 is a very high number of dimensions, and in high-dimensional space, all points
         start to look equally distant from each other (curse of dimensionality).
       - UMAP compresses those 384 numbers to just 10 while keeping the relationships
         between similar papers intact. This makes clustering much more accurate.

    2. Silhouette Score for Optimal Cluster Count
       - Old code: n_clusters = min(max(2, len(papers) // 5), 8)  ← just a formula, not data-driven
       - New code: Try k=2,3,4,...,8 and pick the k that maximises the silhouette score.
       - Silhouette score measures how well each paper fits inside its cluster vs. others.
       - A higher score = clusters are tighter and more separated = better grouping.

    3. LLM-Generated Cluster Names via Groq
       - Old code: hardcoded dict that checked if 'neural' → 'Machine Learning'
       - New code: sends the top 5 paper titles in each cluster to LLaMA-3.1-8b-instant
         and asks it to name the research theme. The result is specific and context-aware.
    """

    def __init__(self):
        self.model = None
        self.embedding_available = False
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english', ngram_range=(1, 2))
        self.groq_client = _get_groq_client()

        try:
            self.model = load_embedding_model()
            if self.model:
                self.embedding_available = True
        except Exception as e:
            print(f"[Clustering] Could not load embedding model: {e}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def cluster_papers(self, papers: List[Dict], n_clusters: Optional[int] = None) -> Dict[int, Dict]:
        """
        Main entry point. Takes a list of paper dicts, returns cluster info dict.
        """
        # Filter out papers that couldn't be fetched at all
        papers = [p for p in papers if p.get("accessibility") != "inaccessible"]

        if len(papers) < 2:
            return {0: {
                'name': 'All Papers',
                'description': 'Single cluster — only one paper found.',
                'papers': papers,
                'paper_count': len(papers),
                'avg_year': 0,
                'avg_citations': 0.0,
                'top_venues': [],
                'silhouette_score': None
            }}

        # Step 1: Build text representations
        texts = self._build_texts(papers)

        # Step 2: Generate embeddings (or TF-IDF fallback)
        raw_embeddings = self._get_embeddings(texts)

        # Step 3: UMAP — compress to lower dimensions for better clustering
        embeddings = self._apply_umap(raw_embeddings)

        # Step 4: Pick best cluster count automatically using silhouette score
        if n_clusters is None:
            n_clusters, best_score = self._find_optimal_clusters(embeddings, papers)
        else:
            best_score = None

        # Step 5: Run Agglomerative Clustering
        labels = self._run_clustering(embeddings, n_clusters)

        # Step 6: Attach labels to papers
        for paper, label in zip(papers, labels):
            paper['cluster'] = int(label)

        # Step 7: Build cluster info dicts with LLM-generated names
        clusters = {}
        for cid in range(n_clusters):
            cluster_papers = [p for p, lbl in zip(papers, labels) if lbl == cid]
            if cluster_papers:
                clusters[cid] = self._build_cluster_info(cid, cluster_papers, best_score)

        return clusters

    # ------------------------------------------------------------------
    # Internal Steps
    # ------------------------------------------------------------------

    def _build_texts(self, papers: List[Dict]) -> List[str]:
        """Combine title + abstract + venue into one string per paper for embedding."""
        texts = []
        for p in papers:
            parts = []
            if p.get('title'):
                parts.append(p['title'])
            if p.get('abstract'):
                parts.append(p['abstract'][:500])  # Limit to avoid very long inputs
            if p.get('venue'):
                parts.append(p['venue'])
            texts.append(' '.join(parts))
        return texts

    def _get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate 384-dim sentence embeddings, falling back to TF-IDF if model unavailable."""
        if self.embedding_available:
            try:
                return self.model.encode(texts, show_progress_bar=False)
            except Exception as e:
                print(f"[Clustering] Embedding failed: {e}. Using TF-IDF fallback.")
        try:
            return self.vectorizer.fit_transform(texts).toarray()
        except Exception as e:
            print(f"[Clustering] TF-IDF also failed: {e}. Using random vectors.")
            return np.random.rand(len(texts), 100)

    def _apply_umap(self, embeddings: np.ndarray) -> np.ndarray:
        """
        IMPROVEMENT 1: UMAP Dimensionality Reduction
        ---------------------------------------------
        Reduces high-dimensional embeddings (384-dim) to 10-dim while preserving
        the geometric relationships between similar papers.

        Think of it like this: if you have a map of 384 cities, UMAP keeps the
        same neighbourhood relationships but squishes the map so it only needs
        10 coordinates instead of 384. Clustering then works much better on 10-dim
        data than 384-dim data.

        If UMAP is not installed (pip install umap-learn), we skip this step.
        """
        if not UMAP_AVAILABLE:
            return embeddings

        n_samples = embeddings.shape[0]

        # UMAP needs at least n_neighbors+1 samples; adjust if dataset is small
        n_neighbors = min(15, max(2, n_samples - 1))
        n_components = min(10, n_samples - 1)

        if n_components < 2:
            return embeddings  # Not enough data to reduce

        try:
            reducer = umap.UMAP(
                n_components=n_components,
                n_neighbors=n_neighbors,
                min_dist=0.1,
                metric='cosine',
                random_state=42  # For reproducibility
            )
            reduced = reducer.fit_transform(embeddings)
            print(f"[Clustering] UMAP: {embeddings.shape[1]}-dim → {n_components}-dim")
            return reduced
        except Exception as e:
            print(f"[Clustering] UMAP failed: {e}. Using original embeddings.")
            return embeddings

    def _find_optimal_clusters(self, embeddings: np.ndarray, papers: List[Dict]):
        """
        IMPROVEMENT 2: Silhouette Score for Optimal Cluster Count
        ----------------------------------------------------------
        Instead of hardcoding n_clusters = len(papers)//5, this method tries
        every value of k from 2 to max_k, and picks the one with the highest
        silhouette score.

        Silhouette score ranges from -1 to 1:
          - Close to 1: paper is well inside its cluster and far from others (good)
          - Close to 0: paper is near the boundary between clusters
          - Negative: paper might be in the wrong cluster

        We pick the k that gives the highest average silhouette across all papers.
        """
        n = len(papers)
        max_k = min(8, n - 1)  # Can't have more clusters than papers - 1

        if max_k < 2:
            return 1, None

        best_k = 2
        best_score = -1.0

        for k in range(2, max_k + 1):
            try:
                clusterer = AgglomerativeClustering(n_clusters=k, linkage='ward')
                labels = clusterer.fit_predict(embeddings)
                # Silhouette score requires at least 2 distinct labels
                if len(set(labels)) < 2:
                    continue
                score = silhouette_score(embeddings, labels)
                print(f"[Clustering] k={k}, silhouette={score:.4f}")
                if score > best_score:
                    best_score = score
                    best_k = k
            except Exception as e:
                print(f"[Clustering] Error at k={k}: {e}")
                continue

        print(f"[Clustering] Best k={best_k} with silhouette score={best_score:.4f}")
        return best_k, best_score

    def _run_clustering(self, embeddings: np.ndarray, n_clusters: int) -> np.ndarray:
        """Run Agglomerative Clustering with Ward linkage."""
        if embeddings.shape[0] <= n_clusters:
            return np.arange(len(embeddings))
        try:
            clusterer = AgglomerativeClustering(n_clusters=n_clusters, linkage='ward')
            return clusterer.fit_predict(embeddings)
        except Exception as e:
            print(f"[Clustering] Clustering failed: {e}")
            return np.zeros(len(embeddings), dtype=int)

    def _build_cluster_info(self, cluster_id: int, papers: List[Dict], silhouette: Optional[float]) -> Dict:
        """
        IMPROVEMENT 3: LLM-Generated Cluster Names
        -------------------------------------------
        Old code: checked if title contained keywords like 'neural' → name = 'Machine Learning'
        New code: sends paper titles to LLaMA (Groq) and asks for a specific theme name.

        This produces names like:
          Before: 'Machine Learning' (same for everything with 'neural' in it)
          After:  'Federated Learning for Medical Imaging' (actual research topic)
        """
        titles = [p['title'] for p in papers if p.get('title')]
        abstracts = [p.get('abstract', '') for p in papers]
        venues = [p.get('venue', '') for p in papers if p.get('venue')]
        years = [p.get('year') for p in papers if p.get('year')]

        # Get LLM-generated cluster name (or fallback to keyword extraction)
        cluster_name = _llm_generate_cluster_name(titles, self.groq_client)

        # Build description
        if years:
            year_range = f"{min(years)}–{max(years)}" if min(years) != max(years) else str(min(years))
        else:
            year_range = "recent years"

        description = (
            f"{len(papers)} papers spanning {year_range}, "
            f"covering the theme: {cluster_name}."
        )
        if silhouette is not None:
            description += f" (Cluster quality score: {silhouette:.2f})"

        citation_counts = [p.get('citations', 0) or 0 for p in papers]
        avg_citations = round(float(np.mean(citation_counts)), 1) if citation_counts else 0.0
        avg_year = int(np.mean(years)) if years else 0
        top_venues = [v for v, _ in Counter(venues).most_common(3)]

        return {
            'name': cluster_name,
            'description': description,
            'paper_count': len(papers),
            'papercount': len(papers),
            'avg_year': avg_year,
            'avg_citations': avg_citations,
            'top_venues': top_venues,
            'silhouette_score': round(silhouette, 4) if silhouette is not None else None,
            'papers': papers
        }
