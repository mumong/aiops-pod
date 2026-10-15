"""Final-message characterization captured before runtime policy extraction."""

import json
from types import SimpleNamespace

import pytest

from app.core import prompts
from app.core.workflow.nodes import base, query_answer
from app.core.workflow.nodes.focused import FocusedTaskNode

# Frozen pre-extraction bytes, deliberately independent of production constants.
AUTO_LINE = "当前修复模式为 auto：结构化修复计划中的安全动作可由修复执行器自动审批并执行。"
REVIEW_LINE = "当前修复模式为 review：结构化修复计划中的所有写动作必须先经过人工审批。"
POLICY = (
    "\n\n# 修复计划与审批约束\n"
    "- {mode_line}\n"
    "- 诊断节点不要直接执行 kubectl apply/patch/delete/rollout/scale 等写操作。\n"
    "- 如果当前证据确认存在标准、安全、可验证的修复方式，可以在最终报告中生成结构化 remediation_plan actions。\n"
    "- 写动作是否执行由 workflow.remediation.mode 和修复执行器控制；review 模式必须人工审批。\n"
)
LANGUAGE = (
    "\n\n# 语言与可见输出约束\n"
    "- 默认用简体中文与用户交流：流式进展、分析摘要、计划/待办说明、工具调用目的、结果解释及结构化字段中的自然语言都使用中文，不能只在最终 answer 才切换中文。用户明确要求其他语言时遵从该要求。\n"
    "- 接口返回给用户展示的 reasoning/thinking 摘要也使用简体中文；不要用英文叙述用户意图、查询计划或下一步。只给简短进展和判断依据，不输出详细内部思维链。\n"
    "- 英文工具说明不改变交流语言。工具名、JSON 字段名、资源名称、PromQL、命令、代码以及引用的日志/错误原文保持原样，用中文解释其含义；不翻译标识符或改写证据。\n"
    "- 需要推理时只给结论性、可验证的简短说明，并优先调用工具获取事实。\n"
    "- 调用工具前，用一句简短中文向用户说明本次查询目的；结果返回后若需继续调查，简述当前发现和下一步关注点。使用普通可见文本，不把进展只写进工具参数或最终 JSON。只提供可核实的进展摘要，不展开内部思维链，不重复工具详情，不为展示进展增加查询；最终仍按既定结构输出。\n"
)
CONCLUSION_CONSTRAINT = "\n当前为诊断总结，无新增工具调用。仅在既有真实证据足以核实对象身份和修复参数时附上修复计划；否则 actions 留空并说明需要补查。诊断报告仍是主任务，不因没有计划而省略诊断结论。"


class CapturedModelCall(Exception):
    """Stop at the model boundary: tests never contact a provider."""


@pytest.mark.parametrize(
    "config,mode_line",
    [
        ({"remediation": {"mode": "auto"}}, AUTO_LINE),
        ({"remediation": {"mode": " AUTO "}}, AUTO_LINE),
        ({"remediation": {"mode": "review"}}, REVIEW_LINE),
        ({"remediation": {"mode": "unknown"}}, REVIEW_LINE),
        ({"remediation": {"mode": None}}, REVIEW_LINE),
        ({"remediation": []}, REVIEW_LINE),
        ({}, REVIEW_LINE),
        (None, REVIEW_LINE),
    ],
)
@pytest.mark.parametrize("skip_policy", [False, True])
@pytest.mark.parametrize("with_catalog", [False, True])
def test_final_base_prompt_bytes_and_component_order(
    monkeypatch, config, mode_line, skip_policy, with_catalog
):
    captured = {}

    def call(**kwargs):
        captured.update(kwargs)
        raise CapturedModelCall

    estimator = SimpleNamespace(estimate=lambda **kwargs: {}, log=lambda budget: None)
    monkeypatch.setattr(base, "ContextBudgetEstimator", lambda: estimator)
    node = FocusedTaskNode()
    node.ai_call = SimpleNamespace(call=call)
    node._get_workflow_config = lambda: config
    node.should_inject_runbook_catalog = lambda: True
    if with_catalog:
        node.runbook_catalog = SimpleNamespace(
            catalog=[SimpleNamespace(link="guide/{id}", description="中文\n`quoted`")]
        )
    system = "system {unexpanded}\n中文"
    question = "question {literal}"
    with pytest.raises(CapturedModelCall):
        node._call_llm(question, system, skip_remediation_policy=skip_policy)

    catalog = "# Available Runbooks\nIf one or more runbooks match the issue, use the fetch_runbook tool for each relevant runbook.\n\n- guide/{id}: 中文\n`quoted`"
    expected = (catalog + "\n\n" if with_catalog else "") + system
    if not skip_policy:
        expected += POLICY.format(mode_line=mode_line)
    expected += LANGUAGE
    assert captured["system_prompt"].encode() == expected.encode()
    assert captured["question"] == question
    components = captured["static_context_components"]
    names = (["runbook_catalog"] if with_catalog else []) + ["node_system_prompt"]
    names += ([] if skip_policy else ["remediation_policy"]) + ["language_policy"]
    assert [item["name"] for item in components[: len(names)]] == names
    assert components[len(names) - 1]["content"] == LANGUAGE
    if not skip_policy:
        assert components[len(names) - 2]["content"] == POLICY.format(mode_line=mode_line)


@pytest.mark.parametrize("route", ["full_diagnosis", "focused", "remediation", None])
def test_final_conclusion_prompt_bytes_and_schema_order(monkeypatch, route):
    node = query_answer.QueryConclusionNode()
    node._archive_node_input = lambda payload: None
    captured = {}

    def call(question, system_prompt, **kwargs):
        captured.update(question=question, system_prompt=system_prompt, **kwargs)
        raise CapturedModelCall

    node._call_llm = call
    state = {
        "question": "中文 {question}\n`data`",
        "request_time_utc": "fixed",
        "request_contract": {"route": route},
    }
    with pytest.raises(CapturedModelCall):
        node.execute(state)

    expected = prompts.QUERY_CONCLUSION_PROMPT
    schema = query_answer.QueryAnswer
    if route == "full_diagnosis":
        expected += "\n" + prompts.DEEP_CONCLUSION_PRESENTATION
        expected += "\n本产品深度诊断是 Pod 异常检测，不是全面集群健康评估。若 pod_assessment 为 healthy，简述 Healthy、本次范围/时间/证据与近期线索核实结果，无需异常根因表；只说明本次检查未发现 Pod 异常，不承诺业务全健康。若为 inconclusive，明确检查不完整及缺口，不输出 healthy。不因未采集无关指标日志链路而扩展检查。"
    expected += "\n输出 schema：\n" + json.dumps(schema.model_json_schema(), ensure_ascii=False)
    assert captured["system_prompt"].encode() == expected.encode()
    assert json.loads(captured["question"])["question"] == state["question"]
    assert captured["force_no_tools"] is True
    assert captured["skip_remediation_policy"] is True
    assert captured["expect_json"] is True
