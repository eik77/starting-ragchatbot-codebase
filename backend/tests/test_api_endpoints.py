import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ---------------------------------------------------------------------------
# /api/query
# ---------------------------------------------------------------------------

def test_query_returns_200_with_valid_payload(api_client):
    response = api_client.post("/api/query", json={"query": "What is Python?"})
    assert response.status_code == 200


def test_query_response_contains_required_fields(api_client):
    response = api_client.post("/api/query", json={"query": "What is Python?"})
    body = response.json()
    assert "answer" in body
    assert "sources" in body
    assert "session_id" in body


def test_query_answer_is_string(api_client):
    response = api_client.post("/api/query", json={"query": "What is Python?"})
    assert isinstance(response.json()["answer"], str)


def test_query_sources_is_list(api_client):
    response = api_client.post("/api/query", json={"query": "What is Python?"})
    assert isinstance(response.json()["sources"], list)


def test_query_with_explicit_session_id(api_client, mock_rag_system):
    response = api_client.post(
        "/api/query",
        json={"query": "What is Python?", "session_id": "my-session"},
    )
    assert response.status_code == 200
    assert response.json()["session_id"] == "my-session"
    mock_rag_system.query.assert_called_once_with("What is Python?", "my-session")


def test_query_without_session_id_creates_new_session(api_client, mock_rag_system):
    response = api_client.post("/api/query", json={"query": "What is Python?"})
    assert response.status_code == 200
    assert response.json()["session_id"] == "test-session-id"
    mock_rag_system.session_manager.create_session.assert_called_once()


def test_query_missing_query_field_returns_422(api_client):
    response = api_client.post("/api/query", json={})
    assert response.status_code == 422


def test_query_delegates_to_rag_system(api_client, mock_rag_system):
    api_client.post("/api/query", json={"query": "Tell me about loops", "session_id": "s1"})
    mock_rag_system.query.assert_called_once_with("Tell me about loops", "s1")


def test_query_returns_500_when_rag_raises(api_client, mock_rag_system):
    mock_rag_system.query.side_effect = RuntimeError("DB offline")
    response = api_client.post("/api/query", json={"query": "Anything", "session_id": "s2"})
    assert response.status_code == 500


def test_query_500_detail_contains_error_message(api_client, mock_rag_system):
    mock_rag_system.query.side_effect = RuntimeError("DB offline")
    response = api_client.post("/api/query", json={"query": "Anything", "session_id": "s2"})
    assert "DB offline" in response.json()["detail"]


# ---------------------------------------------------------------------------
# /api/courses
# ---------------------------------------------------------------------------

def test_courses_returns_200(api_client):
    response = api_client.get("/api/courses")
    assert response.status_code == 200


def test_courses_response_contains_required_fields(api_client):
    body = api_client.get("/api/courses").json()
    assert "total_courses" in body
    assert "course_titles" in body


def test_courses_total_courses_is_int(api_client):
    body = api_client.get("/api/courses").json()
    assert isinstance(body["total_courses"], int)


def test_courses_titles_is_list(api_client):
    body = api_client.get("/api/courses").json()
    assert isinstance(body["course_titles"], list)


def test_courses_count_matches_titles_length(api_client):
    body = api_client.get("/api/courses").json()
    assert body["total_courses"] == len(body["course_titles"])


def test_courses_delegates_to_rag_system(api_client, mock_rag_system):
    api_client.get("/api/courses")
    mock_rag_system.get_course_analytics.assert_called_once()


def test_courses_returns_500_when_analytics_raises(api_client, mock_rag_system):
    mock_rag_system.get_course_analytics.side_effect = RuntimeError("Analytics error")
    response = api_client.get("/api/courses")
    assert response.status_code == 500


def test_courses_500_detail_contains_error_message(api_client, mock_rag_system):
    mock_rag_system.get_course_analytics.side_effect = RuntimeError("Analytics error")
    response = api_client.get("/api/courses")
    assert "Analytics error" in response.json()["detail"]
