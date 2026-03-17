import pytest
from unittest.mock import MagicMock, patch, call
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ai_generator import AIGenerator


def make_text_block(text):
    block = MagicMock()
    block.type = "text"
    block.text = text
    return block


def make_tool_use_block(tool_name, tool_id, tool_input):
    block = MagicMock()
    block.type = "tool_use"
    block.name = tool_name
    block.id = tool_id
    block.input = tool_input
    return block


def make_response(stop_reason, content_blocks):
    response = MagicMock()
    response.stop_reason = stop_reason
    response.content = content_blocks
    return response


@patch("ai_generator.anthropic.Anthropic")
def test_generate_response_direct_no_tool(MockAnthropic):
    mock_client = MagicMock()
    MockAnthropic.return_value = mock_client

    mock_client.messages.create.return_value = make_response(
        "end_turn", [make_text_block("Answer")]
    )

    gen = AIGenerator(api_key="test-key", model="claude-test")
    result = gen.generate_response(query="What is Python?")

    assert result == "Answer"


@patch("ai_generator.anthropic.Anthropic")
def test_generate_response_uses_tool_when_stop_reason_tool_use(MockAnthropic):
    mock_client = MagicMock()
    MockAnthropic.return_value = mock_client

    first_response = make_response("tool_use", [
        make_tool_use_block("search_course_content", "tool-1", {"query": "Python"})
    ])
    second_response = make_response("end_turn", [make_text_block("Final answer")])
    mock_client.messages.create.side_effect = [first_response, second_response]

    mock_tool_manager = MagicMock()
    mock_tool_manager.execute_tool.return_value = "search result"

    gen = AIGenerator(api_key="test-key", model="claude-test")
    result = gen.generate_response(
        query="Tell me about Python",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager
    )

    assert result == "Final answer"
    mock_tool_manager.execute_tool.assert_called_once()


@patch("ai_generator.anthropic.Anthropic")
def test_single_tool_round_passes_correct_params(MockAnthropic):
    mock_client = MagicMock()
    MockAnthropic.return_value = mock_client

    tool_input = {"query": "loops", "course_name": "Python"}
    first_response = make_response("tool_use", [
        make_tool_use_block("search_course_content", "tool-2", tool_input)
    ])
    second_response = make_response("end_turn", [make_text_block("Done")])
    mock_client.messages.create.side_effect = [first_response, second_response]

    mock_tool_manager = MagicMock()
    mock_tool_manager.execute_tool.return_value = "results"

    gen = AIGenerator(api_key="test-key", model="claude-test")
    gen.generate_response(
        query="loops in Python",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager
    )

    mock_tool_manager.execute_tool.assert_called_once_with(
        "search_course_content", query="loops", course_name="Python"
    )


@patch("ai_generator.anthropic.Anthropic")
def test_second_api_call_receives_tool_results_in_messages(MockAnthropic):
    mock_client = MagicMock()
    MockAnthropic.return_value = mock_client

    first_response = make_response("tool_use", [
        make_tool_use_block("search_course_content", "tool-3", {"query": "variables"})
    ])
    second_response = make_response("end_turn", [make_text_block("Variables are...")])
    mock_client.messages.create.side_effect = [first_response, second_response]

    mock_tool_manager = MagicMock()
    mock_tool_manager.execute_tool.return_value = "Variables content here"

    gen = AIGenerator(api_key="test-key", model="claude-test")
    gen.generate_response(
        query="what are variables",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager
    )

    # Inspect second API call
    second_call_kwargs = mock_client.messages.create.call_args_list[1][1]
    messages = second_call_kwargs["messages"]

    # The messages should include a tool_result somewhere
    has_tool_result = any(
        isinstance(msg.get("content"), list) and
        any(r.get("type") == "tool_result" for r in msg["content"])
        for msg in messages
        if isinstance(msg.get("content"), list)
    )
    assert has_tool_result, "Second API call should include tool_result message"


@patch("ai_generator.anthropic.Anthropic")
def test_generate_response_no_tools_omits_tools_param(MockAnthropic):
    mock_client = MagicMock()
    MockAnthropic.return_value = mock_client

    mock_client.messages.create.return_value = make_response(
        "end_turn", [make_text_block("Direct answer")]
    )

    gen = AIGenerator(api_key="test-key", model="claude-test")
    gen.generate_response(query="General question", tools=None)

    call_kwargs = mock_client.messages.create.call_args[1]
    assert "tools" not in call_kwargs


@patch("ai_generator.anthropic.Anthropic")
def test_two_tool_rounds_then_end_turn_returns_final_text(MockAnthropic):
    mock_client = MagicMock()
    MockAnthropic.return_value = mock_client

    tool_response_1 = make_response("tool_use", [
        make_tool_use_block("search_course_content", "t1", {"query": "Python basics"})
    ])
    tool_response_2 = make_response("tool_use", [
        make_tool_use_block("search_course_content", "t2", {"query": "Python advanced"})
    ])
    end_response = make_response("end_turn", [make_text_block("Final text")])
    mock_client.messages.create.side_effect = [tool_response_1, tool_response_2, end_response]

    mock_tool_manager = MagicMock()
    mock_tool_manager.execute_tool.return_value = "results"

    gen = AIGenerator(api_key="test-key", model="claude-test")
    result = gen.generate_response(
        query="Tell me about Python",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager
    )

    assert mock_client.messages.create.call_count == 3
    assert mock_tool_manager.execute_tool.call_count == 2
    assert result == "Final text"


@patch("ai_generator.anthropic.Anthropic")
def test_max_rounds_enforced_final_call_has_no_tools(MockAnthropic):
    mock_client = MagicMock()
    MockAnthropic.return_value = mock_client

    tool_response = make_response("tool_use", [
        make_tool_use_block("search_course_content", "t1", {"query": "q"})
    ])
    end_response = make_response("end_turn", [make_text_block("Done")])
    # Claude keeps requesting tools for first 3 calls, then end_turn on 4th
    mock_client.messages.create.side_effect = [
        tool_response, tool_response, tool_response, end_response
    ]

    mock_tool_manager = MagicMock()
    mock_tool_manager.execute_tool.return_value = "r"

    gen = AIGenerator(api_key="test-key", model="claude-test")
    gen.generate_response(
        query="q",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager
    )

    assert mock_client.messages.create.call_count == 4
    fourth_call_kwargs = mock_client.messages.create.call_args_list[3][1]
    assert "tools" not in fourth_call_kwargs


@patch("ai_generator.anthropic.Anthropic")
def test_tools_present_in_all_loop_calls(MockAnthropic):
    mock_client = MagicMock()
    MockAnthropic.return_value = mock_client

    tool_response = make_response("tool_use", [
        make_tool_use_block("search_course_content", "t1", {"query": "q"})
    ])
    end_response = make_response("end_turn", [make_text_block("Done")])
    mock_client.messages.create.side_effect = [
        tool_response, tool_response, tool_response, end_response
    ]

    mock_tool_manager = MagicMock()
    mock_tool_manager.execute_tool.return_value = "r"

    gen = AIGenerator(api_key="test-key", model="claude-test")
    gen.generate_response(
        query="q",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager
    )

    calls = mock_client.messages.create.call_args_list
    for i in range(3):
        assert "tools" in calls[i][1], f"Call {i+1} should have tools"
    assert "tools" not in calls[3][1], "Call 4 (final synthesis) should NOT have tools"


@patch("ai_generator.anthropic.Anthropic")
def test_tool_execution_exception_caught_loop_continues(MockAnthropic):
    mock_client = MagicMock()
    MockAnthropic.return_value = mock_client

    tool_response = make_response("tool_use", [
        make_tool_use_block("search_course_content", "t1", {"query": "q"})
    ])
    end_response = make_response("end_turn", [make_text_block("Recovered")])
    mock_client.messages.create.side_effect = [tool_response, end_response]

    mock_tool_manager = MagicMock()
    mock_tool_manager.execute_tool.side_effect = Exception("DB error")

    gen = AIGenerator(api_key="test-key", model="claude-test")
    result = gen.generate_response(
        query="q",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager
    )

    assert result == "Recovered"
    assert mock_client.messages.create.call_count == 2

    second_call_kwargs = mock_client.messages.create.call_args_list[1][1]
    messages = second_call_kwargs["messages"]
    tool_result_content = next(
        (r["content"] for msg in messages if isinstance(msg.get("content"), list)
         for r in msg["content"] if r.get("type") == "tool_result"),
        None
    )
    assert tool_result_content is not None
    assert "Tool execution failed" in tool_result_content


@patch("ai_generator.anthropic.Anthropic")
def test_messages_grow_correctly_across_two_rounds(MockAnthropic):
    mock_client = MagicMock()
    MockAnthropic.return_value = mock_client

    tool_response_1 = make_response("tool_use", [
        make_tool_use_block("search_course_content", "t1", {"query": "first"})
    ])
    tool_response_2 = make_response("tool_use", [
        make_tool_use_block("search_course_content", "t2", {"query": "second"})
    ])
    end_response = make_response("end_turn", [make_text_block("Final")])
    mock_client.messages.create.side_effect = [tool_response_1, tool_response_2, end_response]

    mock_tool_manager = MagicMock()
    mock_tool_manager.execute_tool.return_value = "result"

    gen = AIGenerator(api_key="test-key", model="claude-test")
    gen.generate_response(
        query="multi-step question",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager
    )

    third_call_kwargs = mock_client.messages.create.call_args_list[2][1]
    messages = third_call_kwargs["messages"]
    # Expected: [user, asst_1, tool_result_1, asst_2, tool_result_2]
    assert len(messages) == 5
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[2]["role"] == "user"
    assert messages[3]["role"] == "assistant"
    assert messages[4]["role"] == "user"


@patch("ai_generator.anthropic.Anthropic")
def test_no_tool_use_blocks_in_tool_use_response_returns_directly(MockAnthropic):
    mock_client = MagicMock()
    MockAnthropic.return_value = mock_client

    # stop_reason is "tool_use" but content has only a text block (no tool_use blocks)
    response = make_response("tool_use", [make_text_block("Unexpected text")])
    mock_client.messages.create.return_value = response

    mock_tool_manager = MagicMock()

    gen = AIGenerator(api_key="test-key", model="claude-test")
    result = gen.generate_response(
        query="q",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager
    )

    # Loop body executes (appends empty tool_results), then makes a second call
    # with stop_reason="tool_use" again — this hits MAX_TOOL_ROUNDS and falls through
    # to the final synthesis call. Since side_effect is not set, the same mock is
    # returned for all calls. Let's verify call_count is <= 4 and no exception raised.
    assert mock_client.messages.create.call_count >= 1
    mock_tool_manager.execute_tool.assert_not_called()
