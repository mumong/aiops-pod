import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.service import HolmesService
from app.core.prompts import (
    CONCLUSION_FORMATTER_PROMPT,
    EVIDENCE_COLLECTOR_PROMPT,
    LAYER_CLASSIFIER_PROMPT,
    REMEDIATION_PLAN_PROMPT,
    ROOT_CAUSE_ANALYZER_PROMPT,
    get_query_evidence_normalization_prompt,
    get_conclusion_mode_instruction,
    get_workflow_prompt,
)

























































def test_layer_prompt_is_diagnosis_and_healthy_only():
    expected_phrases = [
        "# 唯一职责：定位当前异常实体",
        "`HEALTHY / ABNORMAL`",
        "不分析根因",
        "交给 Evidence 节点",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT
    assert "QUERY direct" not in LAYER_CLASSIFIER_PROMPT


def test_layer_prompt_requires_event_validation_against_current_state():
    expected_phrases = [
        "以当前 Pod 状态为准",
        "事件只用于辅助定位",
        "不能把已消失或已恢复对象加入当前异常列表",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT


def test_layer_prompt_defines_health_baseline_and_efficiency_rules():
    expected_phrases = [
        "不能仅凭 STATUS 判健康",
        "同时检查 Ready",
        "得到全部目标的当前状态",
        "立即停止",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT


def test_layer_prompt_is_pod_abnormal_first():
    expected_phrases = [
        "哪些 Pod 当前异常",
        "abnormal_pods",
        "abnormal_groups",
        "pod_status_keyword",
        "pod_abnormal_type",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT


def test_layer_prompt_requires_global_abnormal_pod_scan_first():
    expected_phrases = [
        "未指定范围时先获取集群 Pod 列表",
        "`Running / Completed / Succeeded`",
        "其余当前非正常状态均保留",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT


def test_layer_prompt_keeps_explicit_pod_request_in_scope():
    expected_phrases = [
        "指定 namespace/Pod 时只处理这些目标",
        "尊重用户范围",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT
























def test_layer_prompt_defines_pod_abnormal_type_taxonomy_and_derived_layer():
    expected_phrases = [
        "pod_status_keyword",
        "status_category",
        "轻量 `pod_abnormal_type` 归一化",
        "状态之外证据不足时保持通用类型",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT


def test_layer_extract_prompt_preserves_pod_abnormal_type_taxonomy():
    extract_prompt = get_workflow_prompt("layer_extract")
    expected_phrases = [
        "只做当前状态提取",
        "`ABNORMAL`",
        "`HEALTHY`",
        "`pod_abnormal_type`",
        "无法细分时保留通用状态类型",
    ]

    for phrase in expected_phrases:
        assert phrase in extract_prompt


def test_layer_prompt_does_not_rely_on_general_health_runbooks():
    assert "private-k8s-health-reference.md" not in LAYER_CLASSIFIER_PROMPT
    assert "l4-dependency-503" not in LAYER_CLASSIFIER_PROMPT


def test_layer_extract_prompt_is_current_state_first():
    extract_prompt = get_workflow_prompt("layer_extract")
    expected_phrases = [
        "当前仍异常的全部 Pod",
        "状态关键字",
        "`pod_abnormal_type`",
        "历史事件",
        "`HEALTHY`",
    ]

    for phrase in expected_phrases:
        assert phrase in extract_prompt


def test_rca_prompt_delegates_shape_to_small_runtime_schema():
    rca_prompt = get_workflow_prompt("rca")
    expected_phrases = [
        "# 输出",
        "运行时 Pydantic schema",
        "关键证据字段",
        "少量真实原始观察",
        "不为了结构完整生成假设清单",
        "不输出 Markdown、代码块或额外说明",
    ]

    for phrase in expected_phrases:
        assert phrase in rca_prompt


def test_query_direct_prompt_boundaries_are_explicit():
    direct_prompt = get_workflow_prompt("layer_query_direct")
    expected_phrases = [
        "如果是 QUERY，你必须调用工具采集真实数据，并在本轮最终 JSON 中直接输出 `query_result`",
        "最终输出必须是纯 JSON",
        "`query_result` 必须可直接被 conclusion 节点本地渲染",
        "先把用户明确询问的查询项逐项列为采集清单",
        "每个查询项最终必须只有两种状态：已由真实 tool_result 支撑，或明确写入缺失项",
        "禁止把“已经发出的工具调用都返回了”当成“用户问题已完整回答”",
        "只采集用户明确询问的对象、维度和指标，不扩展无关指标",
        "优先调用 `fetch_runbook` 获取 `private-k8s-query-promql-reference.md` 作为查询参考",
        "涉及 Prometheus 指标查询时，必须先调用 `fetch_runbook`",
        "禁止跳过 runbook 直接调用 Prometheus 探索或自创 PromQL",
        "runbook 中已有直接适用模板时，必须优先逐字复用标准 PromQL",
        "execute_prometheus_instant_query",
        "execute_prometheus_range_query",
        "execute_pod_promql",
        "一旦已经获得回答用户问题所需的关键数据，立即停止采集并输出 JSON",
    ]

    for phrase in expected_phrases:
        assert phrase in direct_prompt


def test_query_prometheus_runbook_declares_query_and_pod_diagnosis_tool_boundary():
    configmap = yaml.safe_load(
        Path("deploy/configmap/runbooks.yaml").read_text(encoding="utf-8")
    )
    query_runbook = configmap["data"]["private-k8s-query-promql-reference.md"]

    assert "/query" in query_runbook
    assert "/ask" in query_runbook
    assert "execute_prometheus_instant_query" in query_runbook
    assert "execute_prometheus_range_query" in query_runbook
    assert "execute_pod_promql" in query_runbook


def test_deployed_workflow_disables_layer_early_stop_by_default():
    configmap = yaml.safe_load(
        Path("deploy/configmap/config.yaml").read_text(encoding="utf-8")
    )
    app_config = yaml.safe_load(configmap["data"]["config.yaml"])

    layer_early_stop = app_config["workflow"]["layer"]["early_stop"]
    assert layer_early_stop["enabled"] is False
    assert layer_early_stop["explicit_pod_enabled"] is True


def test_deployed_workflow_disables_rca_validation():
    configmap = yaml.safe_load(
        Path("deploy/configmap/config.yaml").read_text(encoding="utf-8")
    )
    app_config = yaml.safe_load(configmap["data"]["config.yaml"])

    assert app_config["workflow"]["rca_validation"]["enabled"] is False
    assert (
        app_config["workflow"]["rca_context"]["fact_ledger_enabled"]
        is False
    )
    assert (
        app_config["workflow"]["rca_context"]
        ["include_evidence_llm_analysis"]
        is True
    )
    assert app_config["workflow"]["rca_structured_output"]["schema"] == "compact"
    assert (
        app_config["workflow"]["evidence"]
        ["observability_first_round_gate"]["retry_failed_once"]
        is True
    )
    assert (
        app_config["workflow"]["evidence"]
        ["pre_react_observability_baseline"]["enabled"]
        is True
    )


def test_oom_and_liveness_runbooks_contain_scoped_query_shape_examples():
    configmap = yaml.safe_load(
        Path("deploy/configmap/runbooks.yaml").read_text(encoding="utf-8")
    )
    oom = configmap["data"]["pod-oomkilled.md"]
    crashloop = configmap["data"]["pod-crashloop-runtime.md"]
    terminating = configmap["data"]["pod-terminating-stuck.md"]

    for runbook in (oom, crashloop):
        assert '"tool":"execute_pod_promql"' in runbook
        assert '"query_type":"range"' in runbook
        assert '"tool":"query_pod_logs"' in runbook
        assert '"tool":"query_pod_tracing"' in runbook
        assert '"purpose":' in runbook
    assert "container_memory_working_set_bytes" in oom
    assert "kube_pod_container_resource_limits" in oom
    assert "kube_pod_container_status_last_terminated_reason" in oom
    assert '"trace_id":"<trace_id>"' in oom
    assert '"request_resource":"<probe-path>"' in crashloop
    assert "不同 endpoint" in crashloop
    assert "8100 专项查询参考（非强制）" in terminating
    assert "kube_pod_deletion_timestamp" in terminating
    assert '"tool":"query_pod_topology"' in terminating


def test_deployed_config_enables_autonomous_observability_and_disables_compatibility_servers():
    configmap = yaml.safe_load(
        Path("deploy/configmap/config.yaml").read_text(encoding="utf-8")
    )
    app_config = yaml.safe_load(configmap["data"]["config.yaml"])

    autonomous = app_config["mcp_servers"]["aiops-observability-query"]
    assert autonomous["enabled"] is True
    assert autonomous["config"]["url"] == "http://mcp-server-manager.mcp.svc.cluster.local:8100/sse"
    assert autonomous["config"]["mode"] == "sse"

    prometheus = app_config["mcp_servers"]["prometheus_tool"]
    assert prometheus["enabled"] is True
    assert (
        prometheus["config"]["url"]
        == "http://mcp-server-manager.mcp.svc.cluster.local:8095/sse"
    )
    assert prometheus["config"]["mode"] == "sse"
    assert "/query" in prometheus["description"]
    assert "/ask" in prometheus["description"]
    assert "execute_pod_promql" in prometheus["description"]

    coarse = app_config["mcp_servers"]["aiops-case-coarse"]
    assert coarse["enabled"] is False
    assert coarse["config"]["url"] == "http://mcp-server-manager.mcp.svc.cluster.local:8089/sse"
    assert coarse["config"]["mode"] == "sse"

    fine = app_config["mcp_servers"]["aiops-observability-fine"]
    assert fine["enabled"] is False
    assert fine["config"]["url"] == "http://mcp-server-manager.mcp.svc.cluster.local:8090/sse"
    assert fine["config"]["mode"] == "sse"
    assert app_config["workflow"]["evidence"]["observability_mode"] == "autonomous"
    assert (
        app_config["workflow"]["evidence"]["observability_first_round_gate"]["enabled"]
        is True
    )


def test_query_evidence_normalization_prompt_is_disabled():
    assert get_query_evidence_normalization_prompt("zh") == ""


def test_layer_prompts_prioritize_runbook_as_high_priority_reference():
    expected_phrases = [
        "# Runbook",
        "只为已定位的异常类型选择直接相关 Runbook",
        "Runbook 只提供待验证问题",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT


def test_layer_prompt_delegates_distinct_runbook_selection_to_qwen_without_duplicates():
    expected_phrases = [
        "只为已定位的异常类型选择",
        "同一 Runbook 最多获取一次",
        "无法可靠匹配时不强行选择",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT


def test_evidence_prompt_requires_pod_handoff_and_autonomous_observability_contract():
    expected_phrases = [
        "# 唯一职责：为当前作用域采集根因证据",
        "`layer_handoff` 指定的实体",
        "真实工具结果",
        "Kubernetes、Metrics、Logging、Tracing、Topology",
        "每次补证必须有新的明确 `purpose`",
        "NotFound、空结果、命令失败和身份冲突也要保留",
        "不为了维度齐全",
    ]

    for phrase in expected_phrases:
        assert phrase in EVIDENCE_COLLECTOR_PROMPT

    assert "collect_aiops_case" not in EVIDENCE_COLLECTOR_PROMPT
    assert "get_aiops_case_evidence" not in EVIDENCE_COLLECTOR_PROMPT
    assert "recommended_runbooks" not in EVIDENCE_COLLECTOR_PROMPT
    assert "evidence_plan 第一项应为 `fetch_runbook`" not in EVIDENCE_COLLECTOR_PROMPT


def test_workflow_prompts_default_to_chinese_and_support_english_switch():
    zh_prompt = get_workflow_prompt("layer")
    en_prompt = get_workflow_prompt("layer", prompt_language="en")

    assert "唯一职责：定位当前异常实体" in zh_prompt
    assert en_prompt == zh_prompt


def test_english_layer_prompt_is_diagnosis_and_healthy_only():
    en_prompt = get_workflow_prompt("layer", prompt_language="en")

    assert "唯一职责：定位当前异常实体" in en_prompt
    assert "If QUERY" not in en_prompt
    assert '"layer": "HEALTHY/L0/L1/L2/L3/L4/QUERY"' not in en_prompt


def test_workflow_prompts_do_not_contain_json_output_templates():
    prompt_names = [
        "layer",
        "layer_extract",
        "layer_query_direct",
        "layer_query_direct_extract",
        "evidence",
        "tool_observation_summarizer",
        "rca",
    ]
    forbidden = [
        "```json",
        "只输出 JSON",
        "输出 JSON",
        "纯 JSON",
        "最终 JSON",
        "evidence_plan JSON",
        "JSON 模板",
        "手写 JSON",
        "手写结构化示例",
    ]
    for name in prompt_names:
        prompt = get_workflow_prompt(name)
        if name in {"rca", "layer_query_direct"}:
            # RCA keeps a JSON text-fallback contract. `/query` direct also
            # intentionally uses JSON text output to avoid a second Pydantic
            # extraction call on the fast query path.
            continue
        for phrase in forbidden:
            assert phrase not in prompt


def test_remediation_plan_prompt_centralizes_workload_verify_rules():
    assert "REMEDIATION_PLAN_PROMPT" not in get_workflow_prompt("conclusion")
    assert "verify_command 禁止使用当前异常 Pod 的固定名称" in REMEDIATION_PLAN_PROMPT
    assert "kubectl rollout status deployment/<name>" in REMEDIATION_PLAN_PROMPT
    assert "仅因为探测命令返回某个常见名称 NotFound" in REMEDIATION_PLAN_PROMPT
    assert "查询 workload 模板" in REMEDIATION_PLAN_PROMPT
    assert "TerminatingStuck" in REMEDIATION_PLAN_PROMPT
    assert "kubectl patch pod <pod>" in REMEDIATION_PLAN_PROMPT
    assert "metadata.finalizers" in REMEDIATION_PLAN_PROMPT
    assert "remediation_available\": false" in REMEDIATION_PLAN_PROMPT


def test_conclusion_prompt_supports_independent_response_language():
    prompt = get_workflow_prompt(
        "conclusion",
        prompt_language="en",
        response_language="en",
    )

    assert "## 📊 异常概览与现象" in prompt
    assert "All user-facing final report text must be in English." in prompt


def test_conclusion_mode_instructions_are_centrally_managed():
    query_instruction = get_conclusion_mode_instruction("query", "查询 CPU", prompt_language="zh")
    healthy_instruction = get_conclusion_mode_instruction("healthy", "我的集群健康吗", prompt_language="zh")
    query_instruction_en = get_conclusion_mode_instruction("query", "show CPU", prompt_language="en")

    assert "只回答用户明确询问的对象、维度和指标" in query_instruction
    assert "绝对不要猜测" in query_instruction
    assert healthy_instruction == ""
    assert "绝对不要猜测" in query_instruction_en
    assert "show CPU" in query_instruction_en


def test_holmes_service_i18n_getters_preserve_default_behavior_and_allow_override():
    service = HolmesService()
    assert service.get_prompt_language() == "zh"
    assert service.get_response_language() == "zh"

    service.i18n_config = {"prompt_language": "en", "response_language": "en"}
    assert service.get_prompt_language() == "en"
    assert service.get_response_language() == "en"




def test_aiops_prompts_preserve_exact_observability_and_causality():
    assert "facts、samples、query、原始错误和 evidence_refs" in EVIDENCE_COLLECTOR_PROMPT
    assert "DeepFlow flow 与 Tempo span 分开解释" in EVIDENCE_COLLECTOR_PROMPT
    assert "`coverage=present` 只表示命中数据" in EVIDENCE_COLLECTOR_PROMPT
    assert "`empty/absent/weak/error` 表示数据边界" in EVIDENCE_COLLECTOR_PROMPT
    assert "原始数值、单位、状态、错误文本和标识符保持原意" in ROOT_CAUSE_ANALYZER_PROMPT
    assert "完整 trace_id" in ROOT_CAUSE_ANALYZER_PROMPT
    assert "查询成功、coverage、完整度和计划状态本身不是证据" in ROOT_CAUSE_ANALYZER_PROMPT
    assert "只有状态、coverage 或普通成功请求时不能确诊" in ROOT_CAUSE_ANALYZER_PROMPT
    # 结论富模板：只依赖真实数据，不复述旧版事实合同措辞
    assert "只用真实" in CONCLUSION_FORMATTER_PROMPT
    assert "禁止编造" in CONCLUSION_FORMATTER_PROMPT


def test_conclusion_prompt_is_human_focused_and_grounded():
    prompt = CONCLUSION_FORMATTER_PROMPT

    for heading in (
        "## 📊 异常概览与现象",
        "## 🕵️ 证据内容 · <组号>",
        "## 🎯 根因分析",
    ):
        assert heading in prompt
    assert "## 🛠️ 修复建议" not in prompt
    assert "## 📋 验证步骤" not in prompt
    assert "只用真实" in prompt
    assert "禁止编造" in prompt
    assert "含 `numeric_fields` 时，必须展示 first/last 或 min/max" in prompt
    assert "每个维度至少展示一条代表证据" in prompt
    assert "不得仅因与 Kubernetes 部分重复而整维省略" in prompt
    assert "不得写成“单个请求内部”" in prompt


def test_active_workflow_prompts_stay_within_attention_budgets():
    budgets = {
        "layer": 2600,
        "layer_extract": 1400,
        "layer_query_direct": 1900,
        "evidence": 4000,
        "rca": 4300,
    }

    for name, ceiling in budgets.items():
        assert len(get_workflow_prompt(name)) <= ceiling


def test_runtime_prompts_encode_tasks_not_prompt_methodology():
    active = "\n".join(
        get_workflow_prompt(name)
        for name in (
            "layer",
            "layer_extract",
            "layer_query_direct",
            "evidence",
            "rca",
            "conclusion",
        )
    )

    for phrase in ("第一性原理", "隐性提纯", "负向配平", "高维潜空间"):
        assert phrase not in active


def test_rca_and_conclusion_prompts_require_verbatim_per_pod_observability():
    rca_phrases = [
        "锁定当前 namespace/Pod/UID",
        "只使用该实体的真实工具结果",
        "来源工具 + 真实值/原文 + 诊断作用",
        "原始数值、单位、状态、错误文本和标识符保持原意",
    ]

    for phrase in rca_phrases:
        assert phrase in ROOT_CAUSE_ANALYZER_PROMPT


def test_active_rca_and_conclusion_prompts_are_fixture_free():
    active_prompts = ROOT_CAUSE_ANALYZER_PROMPT + CONCLUSION_FORMATTER_PROMPT
    for forbidden in (
        "PAYMENT_GATEWAY_TOKEN",
        "/allocate",
        "trace-oom",
        "trace-config",
        "aiops-traced",
        "required config PAYMENT_GATEWAY_TOKEN is missing",
    ):
        assert forbidden not in active_prompts

    for phrase in (
        "原始数值、单位、状态、错误文本和标识符保持原意",
        "只有完整 trace_id 相同时",
        "输入中存在 fact_id 时一并保留",
    ):
        assert phrase in ROOT_CAUSE_ANALYZER_PROMPT


def test_active_rca_and_conclusion_prompts_have_no_fault_specific_anchor():
    active = ROOT_CAUSE_ANALYZER_PROMPT + CONCLUSION_FORMATTER_PROMPT
    for fault_specific in (
        "OOMKilled",
        "ImagePullBackOff",
        "CrashLoopBackOff",
        "Exit Code 137",
        "96Mi",
        "finalizer",
    ):
        assert fault_specific not in active
    assert "明确原因、失败事件和原始错误优先" in active
    assert "Runbook、候选场景" in active


def test_prompts_refine_runbooks_after_live_evidence_and_preserve_topology_semantics():
    assert "计划、Runbook 和归档不是证据" in EVIDENCE_COLLECTOR_PROMPT
    assert "不为了维度齐全" in EVIDENCE_COLLECTOR_PROMPT
    assert "补充更具体的 runbook" not in EVIDENCE_COLLECTOR_PROMPT
    assert "拿到 `collect_aiops_case` 的真实结果后" not in EVIDENCE_COLLECTOR_PROMPT
    assert "通用 CrashLoop runbook" not in EVIDENCE_COLLECTOR_PROMPT


def test_diagnostic_prompts_are_focused_and_bounded():
    assert len(LAYER_CLASSIFIER_PROMPT) < 1200
    assert len(EVIDENCE_COLLECTOR_PROMPT) < 1200
    assert len(ROOT_CAUSE_ANALYZER_PROMPT) < 2000
    assert "最终根因报告或修复方案" in EVIDENCE_COLLECTOR_PROMPT
    assert "根本原因 → 失败机制 → 直接失败 → 当前现象" in ROOT_CAUSE_ANALYZER_PROMPT


def test_deployment_enables_autonomous_evidence_context_stop():
    manifest_path = Path(__file__).resolve().parents[3] / "deploy" / "configmap" / "config.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    config = yaml.safe_load(manifest["data"]["config.yaml"])

    assert config["workflow"]["evidence"]["observability_mode"] == "autonomous"
    assert config["workflow"]["evidence"]["early_stop"]["enabled"] is True






