from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage

from app.core.aicall.client import AICall


def test_call_simple_creates_fresh_chat_model_per_invocation():
    model_instances = []

    def _new_model(**kwargs):
        model = MagicMock()
        model.invoke.return_value = MagicMock(content=f"resp-{len(model_instances)}")
        model_instances.append(model)
        return model

    with patch("app.core.aicall.client.ChatOpenAI", side_effect=_new_model):
        ai = AICall(model="deepseek/deepseek-chat", api_key="sk-test")

        first = ai.call_simple("sys", "q1")
        second = ai.call_simple("sys", "q2")

    assert first == "resp-0"
    assert second == "resp-1"
    assert len(model_instances) == 2
    assert model_instances[0] is not model_instances[1]
    model_instances[0].invoke.assert_called_once()
    model_instances[1].invoke.assert_called_once()


def test_call_with_tools_creates_fresh_chat_model_per_invocation():
    model_instances = []
    create_agent_calls = []

    def _new_model(**kwargs):
        model = MagicMock()
        model_instances.append(model)
        return model

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

    class _Agent:
        async def astream(self, *args, **kwargs):
            if False:
                yield None

    def _capture_agent(model=None, tools=None, system_prompt=None):
        create_agent_calls.append(model)
        return _Agent()

    tool = MagicMock()
    tool.name = "tool_a"
    tool.description = "tool"
    tool.args_schema = None

    with patch("app.core.aicall.client.ChatOpenAI", side_effect=_new_model), \
         patch("langchain.agents.create_agent", side_effect=_capture_agent), \
         patch("concurrent.futures.ThreadPoolExecutor", return_value=_Executor()):
        ai = AICall(model="deepseek/deepseek-chat", api_key="sk-test")
        ai.call("sys", "q1", tools=[tool])
        ai.call("sys", "q2", tools=[tool])

    assert len(model_instances) == 2
    assert len(create_agent_calls) == 2
    assert create_agent_calls[0] is model_instances[0]
    assert create_agent_calls[1] is model_instances[1]
    assert create_agent_calls[0] is not create_agent_calls[1]


def test_call_simple_json_parses_fenced_json_output():
    def _new_model(**kwargs):
        model = MagicMock()
        model.invoke.return_value = MagicMock(
            content='```json\n{"layer":"QUERY","confidence":0.9,"reasoning":"ok"}\n```'
        )
        return model

    with patch("app.core.aicall.client.ChatOpenAI", side_effect=_new_model):
        ai = AICall(model="deepseek/deepseek-chat", api_key="sk-test")
        parsed, raw = ai.call_simple_json("sys", "q")

    assert parsed == {"layer": "QUERY", "confidence": 0.9, "reasoning": "ok"}
    assert "```json" in raw


def test_call_with_expect_json_interrupts_on_valid_json_message():
    model_instances = []

    def _new_model(**kwargs):
        model = MagicMock()
        model_instances.append(model)
        return model

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

    class _Agent:
        async def astream(self, *args, **kwargs):
            yield (
                "updates",
                {
                    "model": {
                        "messages": [
                            AIMessage(content='{"layer":"QUERY","confidence":0.9,"reasoning":"ok"}')
                        ]
                    }
                },
            )

    tool = MagicMock()
    tool.name = "tool_a"
    tool.description = "tool"
    tool.args_schema = None

    with patch("app.core.aicall.client.ChatOpenAI", side_effect=_new_model), \
         patch("langchain.agents.create_agent", return_value=_Agent()), \
         patch("concurrent.futures.ThreadPoolExecutor", return_value=_Executor()):
        ai = AICall(model="deepseek/deepseek-chat", api_key="sk-test")
        result, _ = ai.call(
            "sys",
            "q1",
            tools=[tool],
            expect_json=True,
            json_validator=lambda data: data.get("layer") == "QUERY",
        )

    assert result.result == '{"layer": "QUERY", "confidence": 0.9, "reasoning": "ok"}'
