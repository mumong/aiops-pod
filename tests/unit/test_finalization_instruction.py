"""The finalization prompt states the real stop reason; voluntary stops are not 'budget exhausted'."""

from app.core.prompts import STRUCTURED_FINALIZATION_INSTRUCTION, finalization_instruction


def test_each_reason_gets_its_own_header_and_shared_body():
    body = STRUCTURED_FINALIZATION_INSTRUCTION.split("\n", 1)[1]
    voluntary = finalization_instruction("no_structured_output")
    assert voluntary.startswith("# 收卷：本阶段调查已由你自行结束")
    assert "预算并未耗尽" in voluntary and voluntary.endswith(body)
    assert finalization_instruction("step_limit").startswith("# 收卷：本阶段调查步数预算已用尽")
    assert finalization_instruction("repeat_limit").startswith(
        "# 收卷：本阶段因同一调用反复重复而停止"
    )
    assert finalization_instruction("unknown-reason") == finalization_instruction("step_limit")
    assert "推导、估算" in voluntary  # draft numbers stay non-data in every variant
