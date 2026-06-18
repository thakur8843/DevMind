import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from app.main import app

# Pass the API key in every request
HEADERS = {"X-API-Key": "devmind-local-api-key"}
client = TestClient(app, raise_server_exceptions=False)


# ── Health ─────────────────────────────────────────────────────────────────

def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ── Auth middleware ────────────────────────────────────────────────────────

def test_missing_api_key_returns_401():
    resp = client.post("/api/v1/review/", json={
        "code": "def foo(): pass",
        "language": "python",
    })
    assert resp.status_code == 401


def test_wrong_api_key_returns_401():
    resp = client.post(
        "/api/v1/review/",
        json={"code": "def foo(): pass", "language": "python"},
        headers={"X-API-Key": "wrong-key"},
    )
    assert resp.status_code == 401


# ── Request ID header ──────────────────────────────────────────────────────

def test_request_id_header_present():
    resp = client.get("/health")
    assert "x-request-id" in resp.headers
    assert len(resp.headers["x-request-id"]) == 36   # UUID format


# ── Validation error returns 422 with clean JSON ──────────────────────────

def test_validation_error_returns_clean_json():
    resp = client.post(
        "/api/v1/review/",
        json={"code": "x"},   # too short (min_length=10)
        headers=HEADERS,
    )
    assert resp.status_code == 422
    body = resp.json()
    assert "errors" in body
    assert "request_id" in body


# ── Code review ────────────────────────────────────────────────────────────

@patch("app.services.review_service.get_review_chain")
@patch("app.services.review_service.get_vector_store")
def test_create_review_success(mock_vs, mock_chain):
    mock_chain.return_value.ainvoke = AsyncMock(
        return_value="## Review\n**Rating: 8/10** — Clean function."
    )
    mock_vs.return_value.ingest = MagicMock(return_value=2)

    resp = client.post(
        "/api/v1/review/",
        json={"code": "def add(a, b):\n    return a + b", "language": "python"},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert "session_id" in data
    assert data["language"] == "python"


# ── RAG chat ───────────────────────────────────────────────────────────────

@patch("app.services.review_service.get_rag_chain")
@patch("app.services.review_service.get_vector_store")
def test_rag_chat_success(mock_vs, mock_chain):
    mock_chain.return_value.ainvoke = AsyncMock(
        return_value="The add function returns the sum of two numbers."
    )
    mock_vs.return_value.similarity_search = MagicMock(return_value=[])

    resp = client.post(
        "/api/v1/review/chat",
        json={"question": "What does the function do?", "session_id": "test-session-abc"},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    assert "answer" in resp.json()
