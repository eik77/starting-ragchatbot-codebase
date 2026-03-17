import pytest
from unittest.mock import MagicMock
import sys
import os

# Add backend directory to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Stub out C-extension modules that can't run due to architecture mismatch
# (numpy/chromadb compiled for x86_64, running on arm64)
for mod in [
    "numpy", "numpy.typing",
    "chromadb", "chromadb.config", "chromadb.utils",
    "chromadb.utils.embedding_functions",
    "sentence_transformers",
    "anthropic",
]:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

# Also stub chromadb.config.Settings
import chromadb
chromadb.PersistentClient = MagicMock()
chromadb.utils = MagicMock()

from vector_store import VectorStore, SearchResults


@pytest.fixture
def mock_vector_store():
    return MagicMock(spec=VectorStore)


@pytest.fixture
def sample_search_results():
    return SearchResults(
        documents=[
            "Python is a high-level programming language known for its simplicity.",
            "Functions in Python are defined using the def keyword."
        ],
        metadata=[
            {"course_title": "Python Basics", "lesson_number": 1, "chunk_index": 0},
            {"course_title": "Python Basics", "lesson_number": 2, "chunk_index": 1}
        ],
        distances=[0.1, 0.2]
    )


@pytest.fixture
def empty_search_results():
    return SearchResults(documents=[], metadata=[], distances=[])


@pytest.fixture
def error_search_results():
    return SearchResults.empty("Search error: ChromaDB connection failed")


# ---------------------------------------------------------------------------
# API test fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_rag_system():
    """RAGSystem mock with sensible defaults for API tests."""
    system = MagicMock()
    system.query.return_value = ("Python is a programming language.", ["Python Basics - Lesson 1||http://example.com/lesson1"])
    system.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": ["Python Basics", "Advanced Python"],
    }
    system.session_manager.create_session.return_value = "test-session-id"
    return system


@pytest.fixture
def test_app(mock_rag_system):
    """
    Minimal FastAPI app that mirrors the real app's API routes but avoids
    mounting the frontend static files (which don't exist in the test env).
    """
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from typing import List, Optional

    app = FastAPI()
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

    class QueryRequest(BaseModel):
        query: str
        session_id: Optional[str] = None

    class QueryResponse(BaseModel):
        answer: str
        sources: List[str]
        session_id: str

    class CourseStats(BaseModel):
        total_courses: int
        course_titles: List[str]

    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        try:
            session_id = request.session_id or mock_rag_system.session_manager.create_session()
            answer, sources = mock_rag_system.query(request.query, session_id)
            return QueryResponse(answer=answer, sources=sources, session_id=session_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        try:
            analytics = mock_rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"],
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return app


@pytest.fixture
def api_client(test_app):
    """Synchronous TestClient wrapping the test app."""
    from fastapi.testclient import TestClient
    return TestClient(test_app)
