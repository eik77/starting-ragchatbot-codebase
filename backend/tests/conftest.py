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
