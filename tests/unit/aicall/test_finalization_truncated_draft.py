"""A max_tokens-truncated draft is not finalization material."""

from langchain_core.messages import AIMessage

from types import SimpleNamespace

from app.core.aicall.client import AICall
from app.core.aicall.output_budget import OutputBudget


def test_truncated_round_text_is_replaced_by_marker():
    ai = AICall(
        model="openai/x",
        api_key="k",
        api_base="http://gw/v1",
        output_budget=OutputBudget(
            agent=6000, delivery=10000, compaction=3000, retry_multiplier=2
        ),
    )
    run = SimpleNamespace(emitted_ai_messages=[], tool_observation_contents=[])
    ok = AIMessage(
        content="CPU 14.6%",
        usage_metadata={"input_tokens": 10, "output_tokens": 50, "total_tokens": 60},
    )
    cut = AIMessage(content="CPU 85.37% ...", response_metadata={"finish_reason": "length"})
    full = AIMessage(
        content="draft",
        usage_metadata={"input_tokens": 10, "output_tokens": 6000, "total_tokens": 6010},
    )
    run.emitted_ai_messages.extend([(ok, "CPU 14.6%"), (cut, "CPU 85.37% ..."), (full, "draft")])
    run.tool_observation_contents.append('{"value": 14.6}')
    material = ai._run_material_for_finalization(run, "q")
    assert material["analysis"][0] == "CPU 14.6%"
    assert "截断" in material["analysis"][1] and "85.37" not in material["analysis"][1]
    assert "截断" in material["analysis"][2]
    assert material["observations"][0]["result"] == '{"value": 14.6}'
