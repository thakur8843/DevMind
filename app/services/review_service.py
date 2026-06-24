import uuid
import logging
from sqlalchemy.orm import Session
from app.models.review import CodeReview, ChatHistory, ReviewStatus
from app.schemas.review import CodeReviewRequest, ChatRequest
from app.services.rag.chain import get_review_chain, get_rag_chain_with_context
from langchain.schema.messages import HumanMessage, AIMessage
from app.services.rag.embeddings import get_vector_store


logger = logging.getLogger("devmind.service")


async def run_code_review(
    request: CodeReviewRequest, db: Session,user_id: int, request_id: str = ""
) -> CodeReview:
    session_id = request.session_id or str(uuid.uuid4())
    logger.info(f"Starting review for session={session_id} lang={request.language} [{request_id[:8]}]")

    record = CodeReview(
        session_id=session_id,
        language=request.language,
        code_snippet=request.code,
        status=ReviewStatus.PENDING,
        user_id=user_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    try:
        chain = get_review_chain()
        result: str = await chain.ainvoke({
            "code": request.code,
            "language": request.language,
        })

        # Ingest code + review into Qdrant so the user can RAG-chat over it
        vector_store = get_vector_store()
        chunks = vector_store.ingest(
            session_id,
            f"CODE ({request.language}):\n{request.code}\n\nREVIEW:\n{result}",
            metadata={"type": "code_review", "language": request.language},
        )
        logger.info(f"Ingested {chunks} chunks into Qdrant for session={session_id}")

        record.review_result = result
        record.status = ReviewStatus.COMPLETED

    except Exception as exc:
        logger.error(f"Review failed for session={session_id}: {exc}", exc_info=True)
        record.status = ReviewStatus.FAILED
        record.review_result = f"Review failed: {str(exc)}"

    db.commit()
    db.refresh(record)
    return record


async def run_rag_chat(
    request: ChatRequest, db: Session,user_id: int, request_id: str = ""
) -> dict:
    logger.info(f"RAG chat session={request.session_id} [{request_id[:8]}]")

    # 1. save user message
    db.add(ChatHistory(
        session_id=request.session_id,
        role="user",
        content=request.question,
        user_id=user_id,
    ))
    db.commit()

    # 2. load last 10 chat turns from PostgreSQL
    history_rows = (
        db.query(ChatHistory)
        .filter(ChatHistory.session_id == request.session_id, ChatHistory.user_id == user_id)
        .order_by(ChatHistory.created_at)
        .limit(10)
        .all()
    )

    # 3. convert DB rows → LangChain message objects
    chat_history = [
        HumanMessage(content=r.content) if r.role == "user"
        else AIMessage(content=r.content)
        for r in history_rows
    ]

    # 4. ONE similarity search — results used for both context and sources
    vector_store = get_vector_store()
    docs = vector_store.similarity_search(
        request.session_id, request.question, k=4
    )
    sources = [doc.metadata.get("type", "unknown") for doc in docs]
    context = "\n\n---\n\n".join(
        f"[{doc.metadata.get('type', 'snippet')}]\n{doc.page_content}"
        for doc in docs
    ) if docs else "No prior code context found for this session."

    # 5. call LLM with context + memory — no second Qdrant call
    answer = await get_rag_chain_with_context(
        context=context,
        question=request.question,
        chat_history=chat_history,
    )

    # 6. save assistant reply
    db.add(ChatHistory(
        session_id=request.session_id,
        role="assistant",
        content=answer,
        user_id=user_id,
    ))
    db.commit()

    return {
        "answer": answer,
        "session_id": request.session_id,
        "sources": sources,
    }
