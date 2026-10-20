"""``llm.loop_tool_choice`` can differ per node.

A string applies to every tool loop; a mapping gives each node its own value with
``default`` for the rest, so the lightweight route can run ``auto`` while diagnosis
and repair stay ``required`` until they are verified on real cases.
"""

from app.core.aicall.client import (
    AICall,
    AutoToolChoiceChatOpenAI,
    ChatOpenAI,
    LoopToolChoice,
)
from app.core.aicall.output_budget import OutputBudget


def _client(setting):
    return AICall(
        model="openai/qwen",
        api_key="k",
        api_base="http://gateway.local/v1",
        output_budget=OutputBudget(agent=100, delivery=100, compaction=100, router=100),
        loop_tool_choice=setting,
    )


def test_string_setting_applies_to_every_node():
    choice = LoopToolChoice.parse("auto")
    assert choice.for_node("query_collect") == "auto"
    assert choice.for_node("remediation") == "auto"
    assert LoopToolChoice.parse(None).for_node("evidence") == "required"
    assert LoopToolChoice.parse("bogus").for_node("evidence") == "required"


def test_mapping_setting_resolves_per_node_with_default():
    choice = LoopToolChoice.parse({"default": "required", "query_collect": "auto", "rca": "x"})
    assert choice.for_node("query_collect") == "auto"
    assert choice.for_node("remediation") == "required"
    assert choice.for_node("rca") == "required"  # invalid value falls back to default
    assert choice.for_node("") == "required"
    assert LoopToolChoice.parse({"evidence": "auto"}).for_node("layer") == "required"
    assert LoopToolChoice.parse({"default": "auto"}).for_node("layer") == "auto"


def test_agent_model_class_follows_the_node():
    client = _client({"default": "required", "query_collect": "auto"})
    assert client._agent_model_class("query_collect") is AutoToolChoiceChatOpenAI
    assert client._agent_model_class("evidence") is ChatOpenAI
    assert _client("auto")._agent_model_class("evidence") is AutoToolChoiceChatOpenAI
    assert str(client.loop_tool_choice) == "default=required, query_collect=auto"


def test_service_passes_mapping_through():
    from app.core.service import HolmesService

    read = HolmesService.get_loop_tool_choice_config
    assert (
        read(None, {"loop_tool_choice": {"query_collect": "auto"}}).for_node("query_collect")
        == "auto"
    )
    assert read(None, {"loop_tool_choice": "auto"}).for_node("layer") == "auto"
    assert read(None, {}).for_node("layer") == "required"
