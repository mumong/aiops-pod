"""Tests for AICall client"""
import json
import queue
from unittest.mock import MagicMock, patch

import pytest

from app.core.aicall.client import AICall
from app.core.aicall.types import AICallResult


class TestAICallInit:
    def test_init_stores_model(self):
        ai = AICall(model="deepseek/deepseek-chat", api_key="sk-test")
        assert ai.model == "deepseek/deepseek-chat"
        assert ai.api_key == "sk-test"
        assert ai.api_base is None

    def test_init_with_api_base(self):
        ai = AICall(model="openai/gpt-4o", api_key="sk-test", api_base="http://proxy:8080")
        assert ai.api_base == "http://proxy:8080"


class TestCallSimple:
    @patch("app.core.aicall.client.litellm.completion")
    def test_call_simple_returns_content(self, mock_completion):
        mock_msg = MagicMock()
        mock_msg.content = "Hello from LLM"
        mock_choice = MagicMock()
        mock_choice.message = mock_msg
        mock_completion.return_value = MagicMock(choices=[mock_choice])

        ai = AICall(model="deepseek/deepseek-chat", api_key="sk-test")
        result = ai.call_simple("You are helpful.", "Hi")

        assert result == "Hello from LLM"
        mock_completion.assert_called_once()
        call_kwargs = mock_completion.call_args
        msgs = call_kwargs.kwargs["messages"]
        assert msgs[0]["role"] == "system"
        assert msgs[1]["role"] == "user"


class TestCallWithTools:
    def _make_tool(self, name="test_tool", result="tool output"):
        """Create a mock LangChain BaseTool."""
        tool = MagicMock()
        tool.name = name
        tool.description = f"A test tool: {name}"
        tool.args_schema = None
        tool.invoke.return_value = result
        return tool

    def _make_llm_response(self, content="", tool_calls=None):
        msg = MagicMock()
        msg.content = content
        msg.tool_calls = tool_calls
        choice = MagicMock()
        choice.message = msg
        return MagicMock(choices=[choice])

    def _make_tool_call(self, tc_id="tc_1", name="test_tool", args=None):
        tc = MagicMock()
        tc.id = tc_id
        tc.function.name = name
        tc.function.arguments = json.dumps(args or {})
        return tc

    @patch("app.core.aicall.client.litellm.completion")
    def test_call_no_tools_single_turn(self, mock_completion):
        mock_completion.return_value = self._make_llm_response(content="Direct answer")

        ai = AICall(model="deepseek/deepseek-chat", api_key="sk-test")
        result, events = ai.call("system", "question")

        assert isinstance(result, AICallResult)
        assert result.result == "Direct answer"
        assert result.tool_call_count == 0
        assert result.iterations == 1

    @patch("app.core.aicall.client.litellm.completion")
    def test_call_with_tool_execution(self, mock_completion):
        tc = self._make_tool_call(name="kubectl_get")
        # First call: LLM wants to use a tool
        resp1 = self._make_llm_response(content="", tool_calls=[tc])
        # Second call: LLM gives final answer
        resp2 = self._make_llm_response(content="Pod is running fine")
        mock_completion.side_effect = [resp1, resp2]

        tool = self._make_tool(name="kubectl_get", result="NAME  STATUS\npod1  Running")

        ai = AICall(model="deepseek/deepseek-chat", api_key="sk-test")
        result, events = ai.call("system", "check pod", tools=[tool], max_steps=5)

        assert result.result == "Pod is running fine"
        assert result.tool_call_count == 1
        assert result.iterations == 2
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0]["tool_name"] == "kubectl_get"
        tool.invoke.assert_called_once()

    @patch("app.core.aicall.client.litellm.completion")
    def test_call_pushes_events_to_queue(self, mock_completion):
        tc = self._make_tool_call(name="my_tool")
        resp1 = self._make_llm_response(content="thinking...", tool_calls=[tc])
        resp2 = self._make_llm_response(content="done")
        mock_completion.side_effect = [resp1, resp2]

        tool = self._make_tool(name="my_tool")
        q = queue.Queue()

        ai = AICall(model="deepseek/deepseek-chat", api_key="sk-test")
        ai.call("sys", "q", tools=[tool], stream_queue=q, node_id="layer")

        events = []
        while not q.empty():
            events.append(q.get_nowait())

        # Should have: ai_message, tool_start, tool_result, iteration_end, ai_message
        event_types = [e[1]["type"] for e in events]
        assert "tool_start" in event_types
        assert "tool_result" in event_types
        assert "iteration_end" in event_types
        # All events tagged with node
        for _, evt in events:
            assert evt["node"] == "layer"

    @patch("app.core.aicall.client.litellm.completion")
    def test_call_max_steps_limit(self, mock_completion):
        """LLM keeps calling tools — should stop at max_steps."""
        tc = self._make_tool_call(name="loop_tool")
        resp_with_tool = self._make_llm_response(content="", tool_calls=[tc])
        # Always return tool calls — should stop at max_steps
        mock_completion.return_value = resp_with_tool

        tool = self._make_tool(name="loop_tool")
        ai = AICall(model="deepseek/deepseek-chat", api_key="sk-test")
        result, _ = ai.call("sys", "q", tools=[tool], max_steps=3)

        assert result.iterations == 3
        assert mock_completion.call_count == 3
