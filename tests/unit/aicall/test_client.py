"""Tests for AICall client"""
import queue
from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage, ToolMessage

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
    @patch("app.core.aicall.client.ChatOpenAI")
    def test_call_simple_returns_content(self, mock_chat_openai):
        model = MagicMock()
        model.invoke.return_value = MagicMock(content="Hello from LLM")
        mock_chat_openai.return_value = model

        ai = AICall(model="deepseek/deepseek-chat", api_key="sk-test")
        result = ai.call_simple("You are helpful.", "Hi")

        assert result == "Hello from LLM"
        mock_chat_openai.assert_called_once()
        model.invoke.assert_called_once()
        messages = model.invoke.call_args.args[0]
        assert messages[0].content == "You are helpful."
        assert messages[1].content == "Hi"


class TestCallWithTools:
    def _make_tool(self, name="test_tool", result="tool output"):
        """Create a mock LangChain BaseTool."""
        tool = MagicMock()
        tool.name = name
        tool.description = f"A test tool: {name}"
        tool.args_schema = None
        tool.invoke.return_value = result
        return tool

    @patch("app.core.aicall.client.ChatOpenAI")
    def test_call_no_tools_single_turn(self, mock_chat_openai):
        model = MagicMock()
        model.invoke.return_value = MagicMock(content="Direct answer")
        mock_chat_openai.return_value = model

        ai = AICall(model="deepseek/deepseek-chat", api_key="sk-test")
        result, events = ai.call("system", "question")

        assert isinstance(result, AICallResult)
        assert result.result == "Direct answer"
        assert result.tool_call_count == 0
        assert result.iterations == 1

    def _run_agent_inline(self):
        class _CompletedFuture:
            def result(self, timeout=None):
                return None

        class _Executor:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def submit(self, fn):
                fn()
                return _CompletedFuture()

        return _Executor()

    @patch("app.core.aicall.client.ChatOpenAI", return_value=MagicMock())
    @patch("concurrent.futures.ThreadPoolExecutor")
    @patch("langchain.agents.create_agent")
    def test_call_with_tool_execution(self, mock_create_agent, mock_executor, _mock_chat_openai):
        class _Agent:
            async def astream(self, *args, **kwargs):
                yield (
                    "updates",
                    {
                        "model": {
                            "messages": [
                                AIMessage(
                                    content="",
                                    tool_calls=[
                                        {
                                            "id": "tc_1",
                                            "name": "kubectl_get",
                                            "args": {},
                                        }
                                    ],
                                )
                            ]
                        }
                    },
                )
                yield (
                    "updates",
                    {
                        "tools": {
                            "messages": [
                                ToolMessage(
                                    content="NAME  STATUS\npod1  Running",
                                    name="kubectl_get",
                                    tool_call_id="tc_1",
                                )
                            ]
                        }
                    },
                )
                yield (
                    "updates",
                    {"model": {"messages": [AIMessage(content="Pod is running fine")]}},
                )

        tool = self._make_tool(name="kubectl_get", result="NAME  STATUS\npod1  Running")
        mock_create_agent.return_value = _Agent()
        mock_executor.return_value = self._run_agent_inline()

        ai = AICall(model="deepseek/deepseek-chat", api_key="sk-test")
        result, events = ai.call("system", "check pod", tools=[tool], max_steps=5)

        assert result.result == "Pod is running fine"
        assert result.tool_call_count == 1
        assert result.iterations == 1
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0]["tool_name"] == "kubectl_get"
        mock_create_agent.assert_called_once()

    @patch("app.core.aicall.client.ChatOpenAI", return_value=MagicMock())
    @patch("concurrent.futures.ThreadPoolExecutor")
    @patch("langchain.agents.create_agent")
    def test_call_pushes_events_to_queue(self, mock_create_agent, mock_executor, _mock_chat_openai):
        class _Agent:
            async def astream(self, *args, **kwargs):
                yield (
                    "updates",
                    {
                        "model": {
                            "messages": [
                                AIMessage(
                                    content="thinking...",
                                    tool_calls=[{"id": "tc_1", "name": "my_tool", "args": {}}],
                                )
                            ]
                        }
                    },
                )
                yield (
                    "updates",
                    {
                        "tools": {
                            "messages": [
                                ToolMessage(
                                    content="tool output",
                                    name="my_tool",
                                    tool_call_id="tc_1",
                                )
                            ]
                        }
                    },
                )
                yield ("updates", {"model": {"messages": [AIMessage(content="done")]}})

        tool = self._make_tool(name="my_tool")
        q = queue.Queue()
        mock_create_agent.return_value = _Agent()
        mock_executor.return_value = self._run_agent_inline()

        ai = AICall(model="deepseek/deepseek-chat", api_key="sk-test")
        ai.call("sys", "q", tools=[tool], stream_queue=q, node_id="layer")

        events = []
        while not q.empty():
            events.append(q.get_nowait())

        # Should have: ai_message, tool_start, tool_result, iteration_end, ai_message
        event_types = [e[1]["type"] for e in events]
        assert "tool_start" in event_types
        assert "tool_result" in event_types
        # All events tagged with node
        for _, evt in events:
            assert evt["node"] == "layer"

    @patch("app.core.aicall.client.ChatOpenAI", return_value=MagicMock())
    @patch("concurrent.futures.ThreadPoolExecutor")
    @patch("langchain.agents.create_agent")
    def test_call_max_steps_limit(self, mock_create_agent, mock_executor, _mock_chat_openai):
        """Agent recursion errors are surfaced as bounded final content."""
        from langgraph.errors import GraphRecursionError

        class _Agent:
            async def astream(self, *args, **kwargs):
                raise GraphRecursionError("Recursion limit of 3 reached")
                yield

        tool = self._make_tool(name="loop_tool")
        mock_create_agent.return_value = _Agent()
        mock_executor.return_value = self._run_agent_inline()

        ai = AICall(model="deepseek/deepseek-chat", api_key="sk-test")
        result, _ = ai.call("sys", "q", tools=[tool], max_steps=3)

        assert "达到最大工具执行步数限制" in result.result
        assert result.iterations == 1
