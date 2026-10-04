from typing import Any, Dict
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from summarizer import FullPaperSummarizer
from utils.auth import get_current_user

from database import (
    save_paper,
    get_saved_papers,
    delete_saved_paper,
)

router = APIRouter(
    prefix="/api/paper",
    tags=["Paper"],
)

class PaperChatRequest(BaseModel):
    paper_id: str
    question: str
    paper: Dict[str, Any]

class SavePaperRequest(BaseModel):
    paper: Dict[str, Any]
    query: str = ""
    note: str = ""

@router.post("/save")
def save_paper_endpoint(
    request: SavePaperRequest,
    current_user=Depends(get_current_user),
    ):
    if not request.paper:
        raise HTTPException(
            status_code=400,
            detail="paper data is required.",
        )

    try:
        result = save_paper(
            user_id=current_user["id"],
            paper=request.paper,
            query=request.query.strip(),
            note=request.note.strip(),
        )

        return {
            "message": "Paper saved successfully.",
            "saved": result,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not save paper: {str(e)}",
        )

@router.get("/saved")
def get_saved_papers_endpoint(current_user=Depends(get_current_user)):
    try:
        papers = get_saved_papers(
            user_id=current_user["id"]
        )

        result = []

        for paper in papers:
            result.append({
                **paper,
                "saved_id": paper.get("_saved_id"),
                "saved_query": paper.get("_saved_query", ""),
                "saved_at": paper.get("_saved_at"),
            })

        return {
            "papers": result
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not load saved papers: {str(e)}",
        )

@router.post("/chat")
def paper_chat(request: PaperChatRequest, current_user=Depends(get_current_user),):
    paper_id = request.paper_id.strip()
    question = request.question.strip()

    if not paper_id:
        raise HTTPException(
            status_code=400,
            detail="paper_id is required.",
        )

    if not question:
        raise HTTPException(
            status_code=400,
            detail="question is required.",
        )

    paper = request.paper

    if not paper:
        raise HTTPException(
            status_code=400,
            detail="paper data is required.",
        )

    title = paper.get("title", "Unknown paper")

    abstract = paper.get("abstract", "").strip()

    # Support both the backend's older ai_summary field
    # and the frontend's summary field.
    ai_summary = paper.get("ai_summary", "")
    summary = paper.get("summary", "")

    if ai_summary:
        if isinstance(ai_summary, dict):
            ai_summary = "\n".join(
                f"{key}: {value}"
                for key, value in ai_summary.items()
                if value
            )
        elif isinstance(ai_summary, list):
            ai_summary = "\n".join(
                f"{item.get('title', 'Summary')}: {item.get('text', '')}"
                if isinstance(item, dict)
                else str(item)
                for item in ai_summary
            )

        ai_summary = str(ai_summary).strip()

    if summary:
        if isinstance(summary, dict):
            summary = "\n".join(
                f"{key}: {value}"
                for key, value in summary.items()
                if value
            )
        elif isinstance(summary, list):
            summary = "\n".join(
                f"{item.get('title', 'Summary')}: {item.get('text', '')}"
                if isinstance(item, dict)
                else str(item)
                for item in summary
            )

        summary = str(summary).strip()

    paper_context_parts = []

    if abstract:
        paper_context_parts.append(
            f"Abstract:\n{abstract}"
        )

    if ai_summary:
        paper_context_parts.append(
            f"AI Summary:\n{ai_summary}"
        )

    if summary:
        paper_context_parts.append(
            f"Paper Summary:\n{summary}"
        )

    paper_context = "\n\n".join(paper_context_parts)

    # If the frontend does not have enough text, try the paper PDF.
    if not paper_context:
        pdf_url = paper.get("pdf_url") or paper.get("pdfUrl")

        # If the paper has an arXiv identifier, construct its PDF URL.
        if not pdf_url:
            arxiv_id = str(paper.get("arxiv", "")).strip()

            if arxiv_id.lower().startswith("arxiv:"):
                arxiv_id = arxiv_id.split(":", 1)[1].strip()

            if arxiv_id:
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

        if pdf_url:
            summarizer = FullPaperSummarizer()

            try:
                extracted_text, _ = summarizer._download_and_extract_pdf(
                    pdf_url
                )

                if extracted_text:
                    limited_text = extracted_text[:12000]
                    paper_context = (
                        f"Full paper text:\n{limited_text}"
                    )

            except Exception as e:
                print(
                    f"PDF extraction failed for {paper_id}: {e}"
                )

    if not paper_context:
        raise HTTPException(
            status_code=400,
            detail="This paper does not have enough text available for grounded Q&A.",
        )

    prompt = f"""
    You are a research assistant answering a question about ONE specific academic paper.

    Answer ONLY using information contained in the paper context below.

    If the paper context does not contain enough information to answer the question,
    say that the information is not available in the provided paper context.

    Do not invent facts, results, methods, citations, or claims.

    Paper title:
    {title}

    Authors:
    {paper.get("authors", [])}

    Year:
    {paper.get("year", "")}

    Source:
    {paper.get("source", "")}

    Paper context:
    {paper_context}

    Question:
    {question}

    Return ONLY valid JSON in exactly this structure:

    {{
    "answer": "A concise, evidence-grounded answer to the question.",
    "evidence": "The specific part of the provided paper context that supports the answer."
    }}
    """

    summarizer = FullPaperSummarizer()

    print(
        f"[Paper Chat] Sending {len(paper_context)} characters to the LLM "
        f"for paper: {paper_id}"
    )

    raw = summarizer._llm_call(prompt)

    if not raw:
        raise HTTPException(
            status_code=502,
            detail="The language model did not return an answer.",
        )

    try:
        result = json.loads(raw)
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="The language model returned an invalid response.",
        )

    return {
        "paper_id": paper_id,
        "question": question,
        "answer": result.get("answer", ""),
        "evidence": result.get("evidence", ""),
    }

@router.delete("/saved/{saved_id}")
def delete_saved_paper_endpoint(saved_id: int, current_user=Depends(get_current_user),):
    try:
        deleted = delete_saved_paper(
            user_id=current_user["id"],
            saved_id=saved_id,
        )

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Saved paper not found.",
            )

        return {
            "message": "Paper removed from your library."
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not remove saved paper: {str(e)}",
        )

