import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.core.service import HolmesService


def test_workflow_request_uses_fresh_aicall_instance(monkeypatch):
    service = HolmesService()

    class _SharedAICall:
        model_str = "deepseek/deepseek-chat"
        api_key = "test-key"
        api_base = "https://example.invalid/v1"

    created = []
    captured = []

    class _FreshAICall:
        def __init__(self, model, api_key, api_base="", **kwargs):
            self.model_str = model
            self.api_key = api_key
            self.api_base = api_base
            self.kwargs = kwargs
            created.append(self)

    class _DummyExecutor:
        def __init__(self, holmes_service=None):
            self.holmes_service = holmes_service
            self.ai_call = None
            self.mcp_tools = []

        def execute_stream(self, question, cancel_event=None):
            captured.append(self.ai_call)
            yield {
                "type": "final",
                "answer": "ok",
                "metrics": {},
                "elapsed_seconds": 0.01,
            }

    monkeypatch.setattr("app.core.aicall.client.AICall", _FreshAICall)
    monkeypatch.setattr("app.core.workflow.executor.WorkflowExecutor", _DummyExecutor)

    service.ai_call = _SharedAICall()
    service.mcp_tools = ["tool-a"]
    service.raw_config = {
        "llm": {
            "extra_body": {
                "chat_template_kwargs": {"enable_thinking": False},
            },
        },
    }

    list(service._execute_query_stream_workflow("q1", output_format="sse"))
    list(service._execute_query_stream_workflow("q2", output_format="sse"))

    assert len(created) == 2
    assert captured == created
    assert created[0] is not created[1]
    assert all(instance is not service.ai_call for instance in created)
    assert all(instance.model_str == service.ai_call.model_str for instance in created)
    assert all(instance.api_key == service.ai_call.api_key for instance in created)
    assert all(instance.api_base == service.ai_call.api_base for instance in created)
    assert all(
        instance.kwargs["chat_model_extra_body"]["chat_template_kwargs"]["enable_thinking"] is False
        for instance in created
    )
