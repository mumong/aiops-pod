"""新版 conclusion 节点核心行为回归测试。

覆盖：
- 诊断路径单次 LLM 调用的 prompt 组装（富模板 + 真实工具数据 + 修复计划指令）
- 工具真实数据注入使用完整 result（而非 200 字符 preview）
- 可观测性事件元数据不全时不被投影过滤静默丢弃
- LLM 返回空时的确定性回退模板
- HEALTHY 快速路径不调 LLM
"""

import json

import pytest

from app.core.skills.models import Layer
from app.core.workflow.nodes.conclusion_formatter import ConclusionFormatterNode


class _CapturingAICall:
    def __init__(self, response="## 📊 异常概览与现象\n\n(模拟报告)"):
        self.response = response
        self.calls = []

    def call_simple(self, system_prompt, question, max_tokens=None):
        self.calls.append({
            "system": system_prompt,
            "user": question,
            "max_tokens": max_tokens,
        })
        return self.response


def _diagnosis_state():
    return {
        "question": "demo namespace 的 pod 为什么一直重启？",
        "layer": Layer.L2,
        "layer_handoff": {"layer": "L2", "primary_problem": "CrashLoopBackOff"},
        "evidence_analysis": json.dumps({
            "plan_total": 4,
            "plan_collected": 3,
            "plan_completeness": 0.75,
            "collection_summary": "计划4项，采集3项",
            "evidence_inventory": [
                {"description": "Pod describe", "tool": "kubectl_describe", "status": "collected"},
            ],
            "diagnostic_evidence_missing": ["崩溃前日志"],
        }),
        "rca_analysis": json.dumps({
            "diagnostic_status": "diagnosed",
            "root_cause": "内存限制 256Mi 不足导致 OOMKilled",
            "supporting_fact_ids": ["fact-source1234"],
            "confidence": 0.85,
            "confidence_reason": "Exit Code 137 + memory limit 证据",
            "causal_chain": {
                "trigger": "内存需求超限",
                "mechanism": "cgroup OOM Killer",
                "manifestation": "CrashLoopBackOff",
            },
            "claim_validation": {
                "valid": True,
                "valid_supporting_fact_ids": ["fact-source1234"],
                "invalid_fact_ids": [],
                "reasons": [],
            },
        }),
        "thinking_events": [
            {
                "type": "tool_result",
                "status": "success",
                "tool_name": "kubectl_describe",
                "node": "evidence",
                "tool_args": {"name": "api-1", "namespace": "demo"},
                "result": "Reason: OOMKilled, Exit Code: 137, memory limit 256Mi, restartCount: 12",
                "result_preview": "Reason: OOMKilled...",
            },
            {
                # 可观测性工具事件，故意缺少 pod target/purpose 元数据：
                # 不应被最终投影过滤静默丢弃
                "type": "tool_result",
                "status": "success",
                "tool_name": "execute_pod_promql",
                "node": "evidence",
                "tool_args": {"query": "container_memory_usage_bytes"},
                "result": "container_memory_usage_bytes{pod='api-1'}: 254Mi (limit 256Mi)",
                "result_preview": "254Mi",
            },
        ],
    }


def test_diagnosis_prompt_contains_rich_template_and_real_tool_data():
    ai = _CapturingAICall()
    node = ConclusionFormatterNode()
    node.ai_call = ai

    new_state = node.execute(_diagnosis_state())

    assert new_state["conclusion"] == "## 📊 异常概览与现象\n\n(模拟报告)"
    assert "修复建议" not in new_state["conclusion"]
    assert len(ai.calls) == 1

    user = ai.calls[0]["user"]
    for section in [
        "# 用户问题",
        "# 阶段1：问题定位",
        "# 阶段2：证据采集摘要",
        "# 阶段3：根因分析",
        "# 工具采集的真实数据",
    ]:
        assert section in user, f"用户消息缺少段落: {section}"
    # 完整 result 注入，而不是截断的 result_preview
    assert "Reason: OOMKilled, Exit Code: 137" in user
    assert "restartCount: 12" in user
    assert "不输出修复建议或验证步骤" in user

    system = ai.calls[0]["system"]
    for section in [
        "## 📊 异常概览与现象",
        "## 🕵️ 证据内容 · <组号>",
        "## 🎯 根因分析",
    ]:
        assert section in system, f"富模板缺少章节: {section}"
    assert "## 🛠️ 修复建议" not in system
    assert "## 📋 验证步骤" not in system


def test_validation_disabled_rca_flows_to_conclusion_prompt():
    ai = _CapturingAICall()
    node = ConclusionFormatterNode()
    node.ai_call = ai
    state = _diagnosis_state()
    state["rca_analysis"] = json.dumps({
        "diagnostic_status": "diagnosed",
        "root_cause": "CONFIG_MISSING 导致 exit 78 和 CrashLoopBackOff",
        "root_cause_summary": "CONFIG_MISSING 导致 exit 78 和 CrashLoopBackOff",
        "supporting_fact_ids": [],
        "hypotheses": [],
        "confidence": 0.95,
        "confidence_reason": "日志、退出码与等待状态一致",
        "claim_validation": {
            "enabled": False,
            "skipped": True,
            "valid": None,
        },
    })

    result = node.execute(state)

    assert result["conclusion"] == "## 📊 异常概览与现象\n\n(模拟报告)"
    assert len(ai.calls) == 1
    assert "CONFIG_MISSING 导致 exit 78" in ai.calls[0]["user"]


def test_observability_data_without_projection_metadata_is_not_dropped():
    ai = _CapturingAICall()
    node = ConclusionFormatterNode()
    node.ai_call = ai

    node.execute(_diagnosis_state())

    user = ai.calls[0]["user"]
    assert "254Mi (limit 256Mi)" in user, "缺少投影元数据的可观测性数据被静默丢弃"


def test_empty_llm_response_falls_back_to_deterministic_template():
    node = ConclusionFormatterNode()
    node.ai_call = _CapturingAICall(response="")

    new_state = node.execute(_diagnosis_state())

    conclusion = new_state["conclusion"]
    assert "确定性回退模板" in conclusion
    assert "内存限制 256Mi 不足" in conclusion


def test_healthy_fast_path_does_not_call_llm():
    ai = _CapturingAICall()
    node = ConclusionFormatterNode()
    node.ai_call = ai

    state = _diagnosis_state()
    state["layer"] = Layer.HEALTHY
    new_state = node.execute(state)

    assert "健康检查结果" in new_state["conclusion"]
    assert ai.calls == []


def test_tool_data_dedup_keeps_followup_queries_with_same_result_prefix():
    """可观测性补采结果与首轮共享相同契约头前缀，不能被去重吞掉。"""
    node = ConclusionFormatterNode()
    shared_prefix = (
        'OBSERVABILITY_QUERY={"tool":"query_pod_tracing","status":"query_succeeded",'
        '"source_system":"deepflow+tempo","dimension":"tracing","coverage":"present"}'
    )
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "query_pod_tracing",
            "node": "evidence",
            "tool_args": {
                "namespace": "demo", "pod": "api",
                "purpose": "首轮广撒网确认流量存在",
            },
            "result": shared_prefix + "\nFLOWS: POST /work 200 x20",
        },
        {
            # 补采：trace_id 定向查询，结果前 80 字符与首轮完全相同
            "type": "tool_result",
            "status": "success",
            "tool_name": "query_pod_tracing",
            "node": "evidence",
            "tool_args": {
                "namespace": "demo", "pod": "api",
                "purpose": "根据日志 trace_id 定向关联应用 span",
                "trace_id": "5ebe49889a2d0d944314138877da7d34",
            },
            "result": shared_prefix + "\nSPAN: trace_id=5ebe49889a2d0d94 GET /work oom_growth",
        },
    ]
    section = node._build_tool_data_section(events)
    assert section.count("query_pod_tracing") >= 2, "补采的 trace_id 定向结果被去重丢弃"
    assert "oom_growth" in section
    assert "POST /work 200 x20" in section


def test_tool_data_truncation_preserves_tail_payload():
    """超长 observability summary 头部是 QUERY 元数据，截断必须保留尾部真实数据。"""
    node = ConclusionFormatterNode()
    head_meta = 'OBSERVABILITY_QUERY={"tool":"query_pod_logs"} QUERY={"dsl":' + "x" * 1400 + "}"
    tail_payload = 'FACT_LEDGER={"records":[{"value":"runtime process exiting path=/work http_status=500"}]}'
    events = [{
        "type": "tool_result",
        "status": "success",
        "tool_name": "query_pod_logs",
        "node": "evidence",
        "tool_args": {"namespace": "demo", "pod": "api", "purpose": "查崩溃日志"},
        "result": head_meta + "\n" + tail_payload,
    }]
    section = node._build_tool_data_section(events)
    assert "runtime process exiting" in section, "尾部真实日志被截断丢弃"
    assert "OBSERVABILITY_QUERY" in section


def test_observability_structured_facts_surface_real_values_not_meta_status():
    """第一性原理修复：从 ev[structured].facts 提取真实值，而非 coverage/status 元状态。"""
    node = ConclusionFormatterNode()
    events = [
        {  # metric: 真实数值 302 必须出现，不能只写 coverage present
            "type": "tool_result", "status": "success",
            "tool_name": "execute_pod_promql", "node": "evidence",
            "tool_args": {"namespace": "demo", "pod": "api", "purpose": "重启趋势"},
            "result": 'OBSERVABILITY_QUERY={"coverage":"present"} QUERY={大段DSL}',  # 拍平文本（旧路径会截断）
            "structured": {
                "dimension": "metrics", "coverage": "present",
                "query": {"promql": "kube_pod_container_status_restarts_total{ns=demo}"},
                "facts": [{
                    "name": "kube_pod_container_status_restarts_total",
                    "value": "302", "unit": "count",
                    "stats": {"first": 100.0, "last": 302.0}, "dimension": "metrics",
                }],
            },
        },
        {  # tracing: 真实请求链路 GET /work → 200 + trace_id
            "type": "tool_result", "status": "success",
            "tool_name": "query_pod_tracing", "node": "evidence",
            "tool_args": {"namespace": "demo", "pod": "api", "purpose": "调用链"},
            "result": 'OBSERVABILITY_QUERY={"status":"query_succeeded"} QUERY={巨大SQL}',
            "structured": {
                "dimension": "tracing", "coverage": "present",
                "query": {"sql": "SELECT ... FROM flow_log ..."},
                "facts": [{
                    "name": "l7_flow", "dimension": "tracing",
                    "trace_id": "abc123def456",
                    "value": {"request_type": "GET", "request_resource": "/work",
                              "response_code": 200, "src_ip": "1.1.1.1", "dst_ip": "2.2.2.2"},
                }],
            },
        },
    ]
    section = node._build_tool_data_section(events)
    # metric 真实值 302 + 趋势，而非 "coverage present"
    assert "302" in section and "count" in section
    assert "趋势 100.0→302.0" in section
    # tracing 真实请求链 + trace_id，而非 "query_succeeded"
    assert "GET /work" in section and "→ 200" in section
    assert "trace_id=abc123def456" in section
    # 巨大 SQL DSL 噪声被丢弃
    assert "SELECT" not in section and "FROM flow_log" not in section


def test_observability_empty_coverage_is_honest_not_fabricated():
    """coverage=empty（如 OOM 后 instant 内存查询）如实呈现，不编造。"""
    node = ConclusionFormatterNode()
    events = [{
        "type": "tool_result", "status": "success",
        "tool_name": "execute_pod_promql", "node": "evidence",
        "tool_args": {"namespace": "demo", "pod": "api", "purpose": "当前内存"},
        "result": "flat",
        "structured": {
            "dimension": "metrics", "coverage": "empty",
            "query": {"promql": "container_memory_working_set_bytes{ns=demo}"},
            "facts": [],
        },
    }]
    section = node._build_tool_data_section(events)
    assert "coverage=empty" in section
    assert "未返回真实数据" in section
    # 没有编造任何数值
    assert "302" not in section


def test_observability_facts_capped_by_count_never_cut_value():
    """事实过多时按条数丢整条，绝不砍断单个真实值。"""
    node = ConclusionFormatterNode()
    facts = [{"name": "log.message", "dimension": "logging",
              "value": f"real log line {i} " + "x" * 100} for i in range(20)]
    events = [{
        "type": "tool_result", "status": "success",
        "tool_name": "query_pod_logs", "node": "evidence",
        "tool_args": {"namespace": "demo", "pod": "api", "purpose": "日志"},
        "result": "flat",
        "structured": {"dimension": "logging", "coverage": "present", "facts": facts},
    }]
    section = node._build_tool_data_section(events)
    # 保留的每条都是完整的（含各自的行号），不是被砍断的半条
    assert "real log line 0" in section
    assert "省略" in section  # 超出条数上限有明确提示
