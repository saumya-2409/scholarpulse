from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from services.research_service import run_research
from database import (
    get_cached_search,
    get_search_history,
)
from utils.auth import get_current_user


router = APIRouter(prefix="/api/research", tags=["Research"])


class ResearchRequest(BaseModel):
    query: str
    papers_per_source: int = 30


@router.post("")
def research(request: ResearchRequest, current_user=Depends(get_current_user),):
    try:
        result = run_research(
            query=request.query,
            papers_per_source=request.papers_per_source,
            user_id=current_user["id"],
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cache")
def get_research_cache(query: str, current_user=Depends(get_current_user),):
    query = query.strip()

    if not query:
        raise HTTPException(status_code=400, detail="query is required.")

    cached = get_cached_search(query)

    if not cached:
        raise HTTPException(
            status_code=404,
            detail="No cached research results found for this query.",
        )

    return {
        "query": query,
        "papers": cached.get("papers", []),
        "clusters": cached.get("clusters", {}),
    }

@router.get("/recent")
def get_recent_research(current_user=Depends(get_current_user),):
    return {
        "searches": get_search_history(
            user_id=current_user["id"],
            limit=10,
        )
    }