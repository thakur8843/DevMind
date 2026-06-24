import logging
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    Filter,
    FieldCondition,
    MatchValue,
)
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger("devmind.qdrant")

# Free local embedding model — no API key, runs on CPU
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_SIZE = 384          # all-MiniLM-L6-v2 always outputs 384 floats
COLLECTION_NAME = "devmind_reviews"   # ONE collection for everything


def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=EMBED_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def get_text_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""],
    )


class QdrantVectorDB:
    """
    Single Qdrant collection for ALL sessions.
    Sessions are isolated via metadata filtering — not separate collections.

    WHY ONE COLLECTION:
      - 1000 users × 5 sessions = 5000 collections (old way) = memory disaster
      - 1 collection + metadata filter = scales to millions of sessions
      - Qdrant officially recommends this for multi-tenant systems

    METADATA STORED PER VECTOR:
      {
        "session_id": "abc-123",     ← used to filter at search time
        "type": "code_review",       ← used to label sources in response
        "language": "python",        ← useful for Phase 2 agent context
      }

    Phase 1.5 addition (do not add yet):
      "user_id": 42                  ← will be added when JWT auth is done
    """

    def __init__(self):
        self.embeddings = get_embeddings()
        self.splitter = get_text_splitter()
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
            # `or None` → empty string from .env becomes None
            # local Docker needs no auth → sends no auth header
        )
        # collection check happens ONCE at startup, not per request
        self._ensure_collection()
        logger.info(f"Qdrant ready → {settings.qdrant_url} | collection: {COLLECTION_NAME}")

    def _ensure_collection(self):
        """
        Called ONCE when server starts.
        Creates collection + payload index if they don't exist.
        Never called again — no per-request overhead.
        """
        existing = [c.name for c in self.client.get_collections().collections]

        if COLLECTION_NAME not in existing:
            # create the collection
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )
            logger.info(f"Created Qdrant collection: {COLLECTION_NAME}")

            # create payload index on session_id
            # WITHOUT this: filter scans all vectors (slow at scale)
            # WITH this: Qdrant jumps directly to that session's vectors (fast)
            self.client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="metadata.session_id",
                field_schema="keyword",   # exact string match
            )
            logger.info("Created payload index on metadata.session_id")

        else:
            logger.info(f"Qdrant collection already exists: {COLLECTION_NAME}")

    def _session_filter(self, session_id: str) -> Filter:
        """
        Builds a Qdrant filter for a specific session.
        Used in both similarity_search() and delete_session().
        Kept as a method so filter logic is defined in one place.

        Phase 1.5 extension:
          add user_id condition here when JWT auth is added
        """
        return Filter(
            must=[
                FieldCondition(
                    key="metadata.session_id",
                    match=MatchValue(value=session_id),
                )
            ]
        )

    def ingest(self, session_id: str, text: str, metadata: dict = None,user_id: int = None,) -> int:
        """
        Chunk text → embed → store in single collection with session metadata.

        metadata example:
          {"type": "code_review", "language": "python"}

        session_id is always injected into metadata automatically —
        caller never needs to pass it inside metadata dict.
        """
        # merge caller metadata with session_id
        full_metadata = {
            **(metadata or {}),
            "session_id": session_id,
            **({"user_id": str(user_id)} if user_id else {}),    # always injected, always filterable
        }

        docs = self.splitter.create_documents(
            [text],
            metadatas=[full_metadata],
        )

        store = QdrantVectorStore(
            client=self.client,
            collection_name=COLLECTION_NAME,
            embedding=self.embeddings,
        )
        store.add_documents(docs)
        logger.info(
            f"Ingested {len(docs)} chunks | session={session_id} "
            f"| type={full_metadata.get('type', 'unknown')}"
        )
        return len(docs)

    def similarity_search(
        self, session_id: str, query: str, k: int = 4
    ) -> list[Document]:
        """
        Search ONLY within the given session's vectors.
        Other sessions' vectors are invisible — filter ensures isolation.

        Even with 1 million vectors in the collection,
        this only touches vectors tagged with this session_id.
        """
        store = QdrantVectorStore(
            client=self.client,
            collection_name=COLLECTION_NAME,
            embedding=self.embeddings,
        )
        results = store.similarity_search(
            query,
            k=k,
            filter=self._session_filter(session_id),
        )

        if not results:
            logger.warning(f"No vectors found for session={session_id}")

        return results

    def delete_session(self, session_id: str):
        """
        Delete ALL vectors belonging to a session.
        Does NOT touch other sessions' vectors.
        Does NOT drop the collection.

        Called from DELETE /api/v1/review/session/{session_id}
        alongside PostgreSQL row deletion.
        """
        self.client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=self._session_filter(session_id),
        )
        logger.info(f"Deleted all vectors for session={session_id}")


# ── Singleton ──────────────────────────────────────────────────────────────
# QdrantVectorDB.__init__ does two expensive things:
#   1. loads 90MB HuggingFace model into memory
#   2. opens network connection to Qdrant
#
# Singleton ensures this happens ONCE per server process.
# Every request reuses the same instance.

_qdrant_db: QdrantVectorDB | None = None


def get_vector_store() -> QdrantVectorDB:
    global _qdrant_db
    if _qdrant_db is None:
        _qdrant_db = QdrantVectorDB()
    return _qdrant_db