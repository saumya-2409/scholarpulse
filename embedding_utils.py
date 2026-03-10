import streamlit as st
from sentence_transformers import SentenceTransformer, util

# 1. Singleton Loader with Caching (Prevents memory bloat)
@st.cache_resource
def load_embedding_model():
    try:
        return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    except Exception as e:
        print(f"Error loading embedding model: {e}")
        return None

def compute_relevance_embedding_score(query: str, paper: dict) -> float:
    # 2. Use the shared model
    model = load_embedding_model()
    if not model:
        return 0.0
    
    text = (paper.get("title","") + " " + paper.get("abstract",""))
    if not text.strip():
        return 0.0
    
    query_emb = model.encode(query, convert_to_tensor=True)
    text_emb = model.encode(text, convert_to_tensor=True)
    
    # Fast cosine similarity
    sim = float(util.pytorch_cos_sim(query_emb, text_emb)[0][0])
    return sim
