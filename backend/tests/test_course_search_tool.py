import pytest
from unittest.mock import MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from search_tools import CourseSearchTool
from vector_store import SearchResults


def test_execute_returns_formatted_results(mock_vector_store, sample_search_results):
    mock_vector_store.search.return_value = sample_search_results
    mock_vector_store.get_lesson_link.return_value = "http://example.com/lesson"

    tool = CourseSearchTool(mock_vector_store)
    result = tool.execute(query="what is Python")

    assert "[Python Basics - Lesson 1]" in result
    assert "[Python Basics - Lesson 2]" in result
    assert "Python is a high-level" in result


def test_execute_no_results_returns_message(mock_vector_store, empty_search_results):
    mock_vector_store.search.return_value = empty_search_results

    tool = CourseSearchTool(mock_vector_store)
    result = tool.execute(query="unknown topic")

    assert "No relevant content found" in result


def test_execute_with_course_name_filter(mock_vector_store, empty_search_results):
    mock_vector_store.search.return_value = empty_search_results

    tool = CourseSearchTool(mock_vector_store)
    tool.execute(query="functions", course_name="Python")

    mock_vector_store.search.assert_called_once_with(
        query="functions",
        course_name="Python",
        lesson_number=None
    )


def test_execute_with_lesson_filter(mock_vector_store, empty_search_results):
    mock_vector_store.search.return_value = empty_search_results

    tool = CourseSearchTool(mock_vector_store)
    tool.execute(query="loops", lesson_number=2)

    mock_vector_store.search.assert_called_once_with(
        query="loops",
        course_name=None,
        lesson_number=2
    )


def test_execute_populates_last_sources(mock_vector_store, sample_search_results):
    mock_vector_store.search.return_value = sample_search_results
    mock_vector_store.get_lesson_link.return_value = "http://example.com/lesson"

    tool = CourseSearchTool(mock_vector_store)
    tool.execute(query="what is Python")

    assert len(tool.last_sources) > 0
    assert any("Python Basics" in s for s in tool.last_sources)
    assert any("Lesson" in s for s in tool.last_sources)


def test_execute_error_state_returns_error_string(mock_vector_store, error_search_results):
    mock_vector_store.search.return_value = error_search_results

    tool = CourseSearchTool(mock_vector_store)
    result = tool.execute(query="something")

    assert "Search error" in result
