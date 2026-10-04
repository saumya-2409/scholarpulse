import concurrent.futures
import logging
from collections import Counter
from typing import Dict, List, Optional

from clustering import PaperClusterer
from config import RETRIEVAL
from database import (
    get_cached_search,
    save_search,
    save_to_cache,
)
from embedding_utils import (
    compute_relevance_embedding_score,
    load_embedding_model,
)
from fetchers import IntelligentMultiSourceFetcher
from summarizer import FullPaperSummarizer
from utils.utility import rank_papers


logger = logging.getLogger(__name__)

def run_research(
    query: str,
    papers_per_source: int = 30,
    user_id: Optional[int] = None,
    ) -> Dict:
    """
    Run the complete research pipeline for a query.

    Returns:
        {
            "query": str,
            "papers": list,
            "full_text_papers": list,
            "restricted": list,
            "clusters": dict,
            "total_fetched": int,
        }
    """

    query = query.strip()

    if not query:
        raise ValueError("Research query cannot be empty.")

    if papers_per_source < 1:
        raise ValueError("papers_per_source must be at least 1.")

    logger.info(
        "Starting research pipeline | query=%r | papers_per_source=%d",
        query,
        papers_per_source,
    )

    # ---------------------------------------------------------
    # 1. Fetch papers from multiple sources
    # ---------------------------------------------------------
    fetcher = IntelligentMultiSourceFetcher()

    raw_papers, total_fetched = fetcher.fetch_papers(
        query,
        sources=None,
        papers_per_source=papers_per_source,
        user_requested=None,
    )

    logger.info(
        "Fetched %d unique papers",
        len(raw_papers),
    )

    # ---------------------------------------------------------
    # 2. Separate accessible and restricted papers
    # ---------------------------------------------------------
    accessible = []
    restricted = []

    for paper in raw_papers:
        has_content = (
            paper.get("pdf_available")
            or paper.get("extracted_content")
            or paper.get("is_open_access")
            or len(paper.get("abstract", "")) > 50
        )

        if has_content:
            accessible.append(paper)
        else:
            restricted.append(paper)

    logger.info(
        "Accessibility filtering | accessible=%d | restricted=%d",
        len(accessible),
        len(restricted),
    )

    # ---------------------------------------------------------
    # 3. Calculate embedding relevance scores
    # ---------------------------------------------------------
    embedding_model = load_embedding_model()

    query_embedding = None

    if embedding_model:
        query_embedding = embedding_model.encode(
            query,
            convert_to_tensor=True,
        )

    scored = []
    source_stats = {}

    for paper in accessible:
        score = compute_relevance_embedding_score(
            query,
            paper,
            query_embedding=query_embedding,
        )

        paper["relevance_score"] = round(score, 3)

        source = paper.get("source", "unknown")

        source_stats.setdefault(
            source,
            {
                "total": 0,
                "passed": 0,
            },
        )

        source_stats[source]["total"] += 1

        if score >= RETRIEVAL["relevance_threshold"]:
            scored.append(paper)
            source_stats[source]["passed"] += 1

    logger.info(
        "Relevance filtering | passed=%d | threshold=%s",
        len(scored),
        RETRIEVAL["relevance_threshold"],
    )

    # ---------------------------------------------------------
    # 4. Rank papers and limit results
    # ---------------------------------------------------------
    ranked = rank_papers(scored)

    final_papers = ranked[:papers_per_source]

    logger.info(
        "Ranking complete | returning=%d papers",
        len(final_papers),
    )

    # ---------------------------------------------------------
    # 5. Generate AI summaries
    # ---------------------------------------------------------
    summarizer = FullPaperSummarizer()

    def process_paper(paper):
        try:
            summary = summarizer.summarize_paper(
                paper,
                use_full_text=True,
                query=query,
            )

            paper["ai_summary"] = summary

            explicit_accessibility = summary.get(
                "accessibility"
            )

            paper["accessibility"] = (
                "inaccessible"
                if (
                    explicit_accessibility == "inaccessible"
                    and not paper.get("abstract")
                )
                else "accessible"
            )

            paper["abstract_summary_status"] = summary.get(
                "abstract_summary_status",
                "extractive_fallback",
            )

        except Exception as exc:
            logger.exception(
                "Failed to summarize paper: %s",
                paper.get("title", "Unknown"),
            )

            paper["ai_summary"] = {
                "error": str(exc)
            }

            paper["accessibility"] = "accessible"
            paper["abstract_summary_status"] = (
                "extractive_fallback"
            )

        return paper

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=3
    ) as executor:
        papers = list(
            executor.map(
                process_paper,
                final_papers,
            )
        )

    logger.info(
        "Summarization complete | papers=%d",
        len(papers),
    )

    # ---------------------------------------------------------
    # 6. Identify papers with full text
    # ---------------------------------------------------------
    full_text_papers = [
        paper
        for paper in papers
        if (
            paper.get("pdf_available")
            or paper.get("extracted_content")
        )
    ]

    # ---------------------------------------------------------
    # 7. Cluster the research results
    # ---------------------------------------------------------
    clusters = {}

    if len(papers) >= 3:
        try:
            clusterer = PaperClusterer()
            clusters = clusterer.cluster_papers(papers)

            logger.info(
                "Clustering complete | clusters=%d",
                len(clusters) if isinstance(clusters, dict) else 0,
            )

        except Exception:
            logger.exception(
                "Clustering failed; continuing without clusters."
            )
            clusters = {}

    # ---------------------------------------------------------
    # 8. Persist search information
    # ---------------------------------------------------------
    try:
        if user_id is not None:
            save_search(
                user_id=user_id,
                query=query,
                paper_count=len(papers),
                cluster_count=(
                    len(clusters)
                    if isinstance(clusters, dict)
                    else 0
                ),
            )

        save_to_cache(
            query=query,
            papers=papers,
            clusters=clusters,
        )

    except Exception:
        logger.exception(
            "Failed to persist research results."
        )

    # ---------------------------------------------------------
    # 9. Return API-friendly result
    # ---------------------------------------------------------
    return {
        "query": query,
        "papers": papers,
        "full_text_papers": full_text_papers,
        "restricted": restricted,
        "clusters": clusters,
        "total_fetched": total_fetched,
        "source_stats": source_stats,
    }

