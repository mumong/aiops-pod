"""The tool loop need not force a tool call every round (``llm.loop_tool_choice``).

create_agent binds ToolStrategy tools with ``tool_choice="any"`` (gateway: ``required``),
so the model never has a "stop" move: finishing must itself be a tool call. Live traces
(2026-10-20, 597 identical repeats) show the model deciding "信息已充分，提交最终方案" and
then copying its previous tool call instead of the long schema tool. ``auto`` lets the
loop end with text (the existing finalization then delivers the schema) and keeps vLLM
off grammar decoding for every round. ``required`` keeps today's behaviour.
"""

from langchain_core.tools import tool

from app.core.aicall.client import (
    AICall,
    AutoToolChoiceChatOpenAI,
    ChatOpenAI,
    normalize_loop_tool_choice,
)
from app.core.aicall.output_budget import OutputBudget


@tool
def lookup(item: str) -> str:
    """Look up an item."""
    return item


def _client(**kw):
    return AICall(
        model="openai/qwen",
        api_key="k",
        api_base="http://gateway.local/v1",
        output_budget=OutputBudget(agent=100, delivery=100, compaction=100, router=100),
        **kw,
    )


def test_loop_tool_choice_defaults_to_required_and_accepts_auto():
    assert normalize_loop_tool_choice(None) == "required"
    assert normalize_loop_tool_choice("AUTO ") == "auto"
    assert normalize_loop_tool_choice("named") == "required"
    assert _client().loop_tool_choice.for_node("evidence") == "required"
    assert _client(loop_tool_choice="auto").loop_tool_choice.for_node("evidence") == "auto"


def test_auto_model_turns_forced_tool_choice_into_auto_and_keeps_the_rest():
    model = AutoToolChoiceChatOpenAI(model="qwen", api_key="k", base_url="http://gateway.local/v1")
    assert model.bind_tools([lookup], tool_choice="any").kwargs["tool_choice"] == "auto"
    assert model.bind_tools([lookup], tool_choice="required").kwargs["tool_choice"] == "auto"
    assert model.bind_tools([lookup]).kwargs.get("tool_choice") is None
    named = model.bind_tools([lookup], tool_choice="lookup").kwargs["tool_choice"]
    assert named["function"]["name"] == "lookup"


def test_agent_model_class_follows_the_setting():
    assert type(_client()._create_chat_model(node_id="evidence")) is ChatOpenAI
    auto = _client(loop_tool_choice="auto")._create_chat_model(
        node_id="evidence", model_cls=AutoToolChoiceChatOpenAI
    )
    assert isinstance(auto, AutoToolChoiceChatOpenAI)
    assert _client(loop_tool_choice="auto")._agent_model_class() is AutoToolChoiceChatOpenAI
    assert _client()._agent_model_class() is ChatOpenAI


def test_service_reads_loop_tool_choice_from_llm_config():
    from app.core.service import HolmesService

    read = HolmesService.get_loop_tool_choice_config
    assert read(None, {"loop_tool_choice": "auto"}).for_node("layer") == "auto"
    assert read(None, {}).for_node("layer") == "required"
