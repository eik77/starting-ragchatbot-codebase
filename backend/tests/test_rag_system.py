import pytest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rag_system import RAGSystem


def make_mock_rag_system():
    """Create a RAGSystem with all heavy dependencies mocked out."""
    config = MagicMock()
    config.CHUNK_SIZE = 800
    config.CHUNK_OVERLAP = 100
    config.CHROMA_PATH = "./test_chroma"
    config.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    config.MAX_RESULTS = 5
    config.MAX_HISTORY = 2
    config.ANTHROPIC_API_KEY = "test-key"
    config.ANTHROPIC_MODEL = "claude-test"

    with patch("rag_system.DocumentProcessor"), \
         patch("rag_system.VectorStore"), \
         patch("rag_system.AIGenerator"), \
         patch("rag_system.SessionManager"), \
         patch("rag_system.ToolManager"), \
         patch("rag_system.CourseSearchTool"), \
         patch("rag_system.CourseOutlineTool"):
        system = RAGSystem(config)

    # Replace with fresh mocks for test control
    system.ai_generator = MagicMock()
    system.ai_generator.generate_response.return_value = "Test response"
    system.tool_manager = MagicMock()
    system.tool_manager.get_tool_definitions.return_value = []
    system.tool_manager.get_last_sources.return_value = []
    system.session_manager = MagicMock()
    system.session_manager.get_conversation_history.return_value = None

    return system


def test_query_returns_response_and_sources():
    system = make_mock_rag_system()
    system.tool_manager.get_last_sources.return_value = []

    response, sources = system.query("What is Python?")

    assert isinstance(response, str)
    assert isinstance(sources, list)


def test_query_with_tool_use_returns_sources():
    system = make_mock_rag_system()
    system.tool_manager.get_last_sources.return_value = [
        "Python Basics - Lesson 1||http://example.com/lesson1"
    ]

    _, sources = system.query("What is Python?")

    assert len(sources) == 1
    assert "Python Basics" in sources[0]


def test_query_with_session_id_fetches_history():
    system = make_mock_rag_system()

    system.query("What is Python?", session_id="session-123")

    system.session_manager.get_conversation_history.assert_called_once_with("session-123")


def test_query_with_session_id_saves_exchange():
    system = make_mock_rag_system()
    system.ai_generator.generate_response.return_value = "Python is a language."

    system.query("What is Python?", session_id="session-456")

    system.session_manager.add_exchange.assert_called_once_with(
        "session-456", "What is Python?", "Python is a language."
    )


def test_query_without_session_id_skips_history():
    system = make_mock_rag_system()

    system.query("What is Python?")

    system.session_manager.get_conversation_history.assert_not_called()


def test_query_resets_sources_after_retrieval():
    system = make_mock_rag_system()
    system.tool_manager.get_last_sources.return_value = ["Python Basics - Lesson 1"]

    system.query("What is Python?")

    system.tool_manager.reset_sources.assert_called_once()
