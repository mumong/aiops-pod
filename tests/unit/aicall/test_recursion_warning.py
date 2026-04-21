from unittest.mock import MagicMock, patch

from langgraph.errors import GraphRecursionError

from app.core.aicall.client import AICall


def test_call_recursion_limit_is_logged_as_warning_not_error():
    class _FailingFuture:
        def result(self, timeout=None):
            raise GraphRecursionError(
                "Recursion limit of 10 reached without hitting a stop condition."
            )

    class _FailingExecutor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def submit(self, fn):
            return _FailingFuture()

    tool = MagicMock()
    tool.name = "loop_tool"
    tool.description = "loop tool"
    tool.args_schema = None

    with patch("app.core.aicall.client.ChatOpenAI"), \
         patch("app.core.aicall.client.logger") as mock_logger, \
         patch("langchain.agents.create_agent", return_value=MagicMock()), \
         patch("concurrent.futures.ThreadPoolExecutor", return_value=_FailingExecutor()):
        ai = AICall(model="deepseek/deepseek-chat", api_key="sk-test")
        result, _ = ai.call("sys", "q", tools=[tool], max_steps=10)

    assert "达到最大工具执行步数限制" in result.result
    mock_logger.warning.assert_any_call(
        "⚠️ [AICall] agent 达到递归/步数上限 (%d): %s",
        10,
        "Recursion limit of 10 reached without hitting a stop condition.",
    )
    mock_logger.error.assert_not_called()
