"""Characterize legacy compaction before moving its user instruction."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.core.prompts import LEGACY_CONTEXT_COMPRESSION_PROMPT
from app.core.workflow.nodes.base import WorkflowNode


@pytest.mark.parametrize("text,limit", [("abcdef", 3), ("中文\n{原文}", 2)])
def test_compaction_preserves_full_input_and_instruction(text, limit):
    call = Mock(return_value="短")
    node = SimpleNamespace(
        node_id="test", ai_call=SimpleNamespace(call_simple=call), metrics=None,
    )

    result = WorkflowNode._compact_context(node, text, limit)

    assert result == "短"
    call.assert_called_once_with(
        system_prompt=LEGACY_CONTEXT_COMPRESSION_PROMPT,
        question=f"请压缩以下内容（原始 {len(text)} 字符，目标 {limit} 字符以内）：\n\n{text}",
        max_tokens=4096,
    )


@pytest.mark.parametrize("limit", [3, 4])
def test_compaction_at_or_below_limit_skips_model(limit):
    call = Mock()
    node = SimpleNamespace(ai_call=SimpleNamespace(call_simple=call))

    result = WorkflowNode._compact_context(node, "abc", limit)

    assert result == "abc"
    call.assert_not_called()


@pytest.mark.parametrize("response", [None, "abcdef", RuntimeError("offline")])
def test_failed_or_ineffective_compaction_keeps_existing_fallback(response):
    call = Mock()
    if isinstance(response, Exception):
        call.side_effect = response
    else:
        call.return_value = response
    node = SimpleNamespace(
        node_id="test", ai_call=SimpleNamespace(call_simple=call), metrics=None,
    )

    result = WorkflowNode._compact_context(node, "abcdef", 3)

    assert result == "abc\n... (截断，原始 6 字符)"
