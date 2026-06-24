from fastapi import APIRouter, Depends, Request
from app.models.review import ChatHistory, CodeReview
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.review import (
    CodeReviewRequest, CodeReviewResponse,
    ChatRequest, ChatResponse,
)
from app.services.review_service import run_code_review, run_rag_chat
# from app.middleware.auth import verify_api_key
from app.middleware.auth import get_current_user
from app.models.user import User
from app.middleware.rate_limit import limiter

router = APIRouter(
    prefix="/review",
    tags=["Code Review"],
    dependencies=[Depends(get_current_user)],  # all routes require valid JWT
)


@router.post("/", response_model=CodeReviewResponse)
@limiter.limit("10/minute")   # tighter limit — each call hits Groq
async def create_review(
    request: Request,
    body: CodeReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit code for AI review.
    - Sends code to Groq LLM for structured feedback
    - Ingests result into Qdrant for later RAG queries
    - Persists everything in PostgreSQL
    """
    request_id = getattr(request.state, "request_id", "")
    record = await run_code_review(body, db,user_id=current_user.id, request_id=request_id)
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
    current_user: User = Depends(get_current_user)
):
    """
    Ask questions about your code using RAG over the session's Qdrant collection.
    Example questions: "What bugs did you find?", "Show me the fixed version"
    """
    request_id = getattr(request.state, "request_id", "")
    result = await run_rag_chat(body, db,user_id=current_user.id, request_id=request_id)
    return ChatResponse(**result)

@router.get("/history/{session_id}")
@limiter.limit("30/minute")
async def get_history(
    request: Request,
    session_id: str,
    page: int = 1,               # ← ADD
    page_size: int = 20,         # ← ADD
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve reviews and chat turns for a session — paginated."""
    offset = (page - 1) * page_size

    total_reviews = db.query(CodeReview)\
        .filter(CodeReview.session_id == session_id,
                CodeReview.user_id == current_user.id)\
        .count()

    total_chats = db.query(ChatHistory)\
        .filter(ChatHistory.session_id == session_id,
                ChatHistory.user_id == current_user.id)\
        .count()

    reviews = (
        db.query(CodeReview)
        .filter(CodeReview.session_id == session_id,
                CodeReview.user_id == current_user.id)
        .order_by(CodeReview.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    chats = (
        db.query(ChatHistory)
        .filter(ChatHistory.session_id == session_id,
                ChatHistory.user_id == current_user.id)
        .order_by(ChatHistory.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return {
        "session_id": session_id,
        "page": page,
        "page_size": page_size,
        "total_reviews": total_reviews,   # ← ADD
        "total_chats": total_chats,       # ← ADD
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
            {
                "role": c.role,
                "content": c.content,
                "created_at": str(c.created_at)
            }
            for c in chats
        ],
    }
# @router.get("/history/{session_id}")
# @limiter.limit("30/minute")
# async def get_history(
#     request: Request,
#     session_id: str,
#     db: Session = Depends(get_db),
# ):
#     """Retrieve all reviews and chat turns for a session."""
    
#     reviews = (
#         db.query(CodeReview)
#         .filter(CodeReview.session_id == session_id)
#         .order_by(CodeReview.created_at)
#         .all()
#     )
#     chats = (
#         db.query(ChatHistory)
#         .filter(ChatHistory.session_id == session_id)
#         .order_by(ChatHistory.created_at)
#         .all()
#     )
#     return {
#         "session_id": session_id,
#         "reviews": [
#             {
#                 "id": r.id,
#                 "language": r.language,
#                 "status": r.status,
#                 "review": r.review_result,
#                 "created_at": str(r.created_at),
#             }
#             for r in reviews
#         ],
#         "chats": [
#             {"role": c.role, "content": c.content, "created_at": str(c.created_at)}
#             for c in chats
#         ],
#     }


@router.delete("/session/{session_id}")
async def delete_session(
    request: Request,
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.review import ChatHistory, CodeReview
    from app.services.rag.embeddings import get_vector_store

    # ← ADD THIS: check ownership before deleting
    review = db.query(CodeReview).filter(
        CodeReview.session_id == session_id,
        CodeReview.user_id == current_user.id,
    ).first()

    if not review:
        raise HTTPException(
            status_code=404,
            detail="Session not found or doesn't belong to you"
        )

    # now safe to delete — confirmed it belongs to this user
    db.query(CodeReview).filter(
        CodeReview.session_id == session_id,
        CodeReview.user_id == current_user.id,
    ).delete()

    db.query(ChatHistory).filter(
        ChatHistory.session_id == session_id,
        ChatHistory.user_id == current_user.id,
    ).delete()

    db.commit()
    get_vector_store().delete_session(session_id)
    return {"deleted": True, "session_id": session_id}