from fastapi import APIRouter, Depends, Request
from app.models.review import ChatHistory, CodeReview
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.review import (
    CodeReviewRequest, CodeReviewResponse,
    ChatRequest, ChatResponse,
)
from app.services.review_service import run_code_review, run_rag_chat
from app.middleware.auth import verify_api_key
from app.middleware.rate_limit import limiter

router = APIRouter(
    prefix="/review",
    tags=["Code Review"],
    dependencies=[Depends(verify_api_key)],  # all routes require X-API-Key
)


@router.post("/", response_model=CodeReviewResponse)
@limiter.limit("10/minute")   # tighter limit — each call hits Groq
async def create_review(
    request: Request,
    body: CodeReviewRequest,
    db: Session = Depends(get_db),
):
    """
    Submit code for AI review.
    - Sends code to Groq LLM for structured feedback
    - Ingests result into Qdrant for later RAG queries
    - Persists everything in PostgreSQL
    """
    request_id = getattr(request.state, "request_id", "")
    record = await run_code_review(body, db, request_id=request_id)
    return CodeReviewResponse(
        id=record.id,
        session_id=record.session_id,
        language=record.language,
        review=record.review_result or "",
        status=record.status,
        created_at=record.created_at,
    )


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("20/minute")
async def chat_with_code(
    request: Request,
    body: ChatRequest,
    db: Session = Depends(get_db),
):
    """
    Ask questions about your code using RAG over the session's Qdrant collection.
    Example questions: "What bugs did you find?", "Show me the fixed version"
    """
    request_id = getattr(request.state, "request_id", "")
    result = await run_rag_chat(body, db, request_id=request_id)
    return ChatResponse(**result)


@router.get("/history/{session_id}")
@limiter.limit("30/minute")
async def get_history(
    request: Request,
    session_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve all reviews and chat turns for a session."""
    
    reviews = (
        db.query(CodeReview)
        .filter(CodeReview.session_id == session_id)
        .order_by(CodeReview.created_at)
        .all()
    )
    chats = (
        db.query(ChatHistory)
        .filter(ChatHistory.session_id == session_id)
        .order_by(ChatHistory.created_at)
        .all()
    )
    return {
        "session_id": session_id,
        "reviews": [
            {
                "id": r.id,
                "language": r.language,
                "status": r.status,
                "review": r.review_result,
                "created_at": str(r.created_at),
            }
            for r in reviews
        ],
        "chats": [
            {"role": c.role, "content": c.content, "created_at": str(c.created_at)}
            for c in chats
        ],
    }


@router.delete("/session/{session_id}")
async def delete_session(
    request: Request,
    session_id: str,
    db: Session = Depends(get_db),
):
    """Delete all data for a session — PostgreSQL rows + Qdrant collection."""
    from app.models.review import ChatHistory, CodeReview
    from app.services.rag.embeddings import get_vector_store

    db.query(CodeReview).filter(CodeReview.session_id == session_id).delete()
    db.query(ChatHistory).filter(ChatHistory.session_id == session_id).delete()
    db.commit()

    get_vector_store().delete_session(session_id)
    return {"deleted": True, "session_id": session_id}
