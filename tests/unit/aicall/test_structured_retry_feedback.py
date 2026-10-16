"""A structured output that failed validation is retried with the error in the prompt."""

from pydantic import BaseModel, field_validator

from app.core.aicall.client import AICall
from app.core.aicall.output_budget import OutputBudget


class _Plan(BaseModel):
    command: str

    @field_validator("command")
    @classmethod
    def no_pipes(cls, value):
        if "|" in value:
            raise ValueError("不支持 shell 管道、重定向或组合；请拆为可单独审阅的动作")
        return value


class _Structured:
    def __init__(self, seen):
        self.seen = seen

    def invoke(self, messages, config=None):
        question = messages[-1].content
        self.seen.append(question)
        # First attempt: the model emits a piped command (schema rejects it). Second
        # attempt, after reading the validation feedback, it complies.
        return {"command": "kubectl get pods | grep x"} if len(self.seen) == 1 else {"command": "kubectl get pods"}


class _Model:
    def __init__(self, seen):
        self.seen = seen

    def with_structured_output(self, schema, method=None):
        return _Structured(self.seen)


def test_validation_error_is_fed_back_on_the_single_retry(monkeypatch):
    seen = []
    ai = AICall(model="openai/x", api_key="k", api_base="http://gw/v1",
                internal_extra_body={"chat_template_kwargs": {"enable_thinking": False}},
                output_budget=OutputBudget(agent=4000, delivery=10000, compaction=3000, retry_multiplier=2))
    monkeypatch.setattr(ai, "_create_chat_model", lambda **kw: _Model(seen))
    monkeypatch.setattr(ai, "_bind_session_metadata", lambda model, *a, **k: model)
    guard = {"context_window": 54000, "final_input_tokens": 14000, "safety_tokens": 2000}
    monkeypatch.setattr(ai, "_prepare_structured_call_context",
                        lambda **kw: (kw["system_prompt"], kw["question"], guard, {}, {}))
    parsed, _raw = ai.call_structured("sys", "make a plan", _Plan, node_id="t", internal_model=True)
    assert parsed is not None and parsed.command == "kubectl get pods"
    assert len(seen) == 2
    assert "上次结构化输出未通过校验" in seen[1] and "shell 管道" in seen[1]
    assert "上次结构化输出未通过校验" not in seen[0]
