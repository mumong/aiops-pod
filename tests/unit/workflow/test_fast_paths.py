import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.service import HolmesService
from app.core.prompts import (
    EVIDENCE_COLLECTOR_PROMPT,
    LAYER_CLASSIFIER_PROMPT,
    QUERY_EVIDENCE_NORMALIZATION_PROMPT_ZH,
    get_conclusion_mode_instruction,
    get_workflow_prompt,
)
from app.core.skills.models import Layer
from app.core.workflow.nodes.conclusion_formatter import ConclusionFormatterNode
from app.core.workflow.nodes.layer_classifier import LayerClassifierNode
from app.core.workflow.nodes.evidence_collector import EvidenceCollectorNode
from app.core.workflow.nodes.root_cause_analyzer import RootCauseAnalyzerNode


class _RecordingAICall:
    def __init__(self, content: str):
        self.content = content
        self.calls = []

    def call_simple(self, *args, **kwargs):
        self.calls.append({"args": args, "kwargs": kwargs})
        return self.content


def test_query_conclusion_uses_llm_structured_summary():
    node = ConclusionFormatterNode()
    node.ai_call = _RecordingAICall(
        """## 📊 查询结果

- **查询目标**: 查询当前异常 Pod 列表

## 📈 数据摘要
| 项目 | 数值 |
|------|------|
| 异常 Pod 数量 | 1 |

## 🔎 详情
- default/pod-a: CrashLoopBackOff
"""
    )

    state = {
        "question": "查询当前异常 Pod 列表",
        "layer": Layer.QUERY,
        "evidence_analysis": (
            '{"collection_summary":"计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%",'
            '"tool_data": [{"tool": "kubectl_get_by_kind_in_cluster", '
            '"data": "NAMESPACE NAME STATUS\\ndefault pod-a CrashLoopBackOff"}],'
            '"evidence_plan": [{"tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get pods -A"}]}'
        ),
        "thinking_events": [],
    }

    result = node.execute(state)

    assert len(node.ai_call.calls) == 1
    assert "查询结果" in result["conclusion"]
    assert "数据摘要" in result["conclusion"]
    assert "异常 Pod 数量" in result["conclusion"]
    assert "CrashLoopBackOff" in result["conclusion"]

def test_healthy_conclusion_uses_deterministic_fast_path():
    node = ConclusionFormatterNode()
    class _FailingAICall:
        def call_simple(self, *args, **kwargs):
            raise AssertionError("call_simple should not be called")

    node.ai_call = _FailingAICall()

    state = {
        "question": "我的集群现在健康吗",
        "layer": Layer.HEALTHY,
        "layer_full_analysis": "所有 Pod Running，节点 Ready，未发现异常事件。",
        "thinking_events": [],
    }

    result = node.execute(state)

    assert "健康检查结果" in result["conclusion"]
    assert "当前集群运行正常" in result["conclusion"]
    assert "所有 Pod Running" in result["conclusion"]


def test_layer_stage1_structured_output_skips_second_extraction_and_keeps_full_analysis():
    node = LayerClassifierNode()
    structured_json = """
```json
{
  "layer": "QUERY",
  "layers": ["QUERY"],
  "layer_name": "直接查询",
  "confidence": 0.95,
  "reasoning": "用户在直接查询异常 Pod 列表",
  "key_entities": [{"type": "Resource", "value": "Pod"}],
  "possible_scenarios": [{"scenario": "直接查询", "probability": "高", "reason": "请求状态列表"}]
}
```
""".strip()

    thinking_events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_by_kind_in_cluster",
            "result": "NAMESPACE NAME STATUS\ndefault pod-a CrashLoopBackOff",
        }
    ]

    node._call_llm = lambda question, prompt, **kwargs: (SimpleNamespace(result=structured_json), thinking_events)
    node._extract_classification = lambda analysis_text: (_ for _ in ()).throw(
        AssertionError("stage2 extraction should not run")
    )

    result, returned_events = node._analyze_with_llm("查询异常 Pod")

    assert result["layer"] == "QUERY"
    assert "full_analysis" in result
    assert "kubectl_get_by_kind_in_cluster" in result["full_analysis"]
    assert "CrashLoopBackOff" in result["full_analysis"]
    assert returned_events == thinking_events


def test_layer_stage1_non_json_output_uses_lite_extraction():
    node = LayerClassifierNode()
    non_json_text = "分析结果：检测到 OOMKilled，根因更接近 L2 工作负载层。"
    thinking_events = []

    node._call_llm = lambda question, prompt, **kwargs: (SimpleNamespace(result=non_json_text), thinking_events)

    class _RecordingAICall:
        def __init__(self):
            self.calls = []

        def call_simple_json(self, system_prompt, question, **kwargs):
            self.calls.append({"system_prompt": system_prompt, "question": question, "kwargs": kwargs})
            return ({
                "layer": "L2",
                "layers": ["L2"],
                "layer_name": "工作负载层",
                "confidence": 0.78,
                "reasoning": "基于已采集到的工具与分析文本，当前问题更符合 L2 工作负载层。",
                "key_entities": [{"type": "Pod", "value": "nginx-1"}],
                "possible_scenarios": [{"scenario": "OOMKilled", "probability": "高", "reason": "分析文本明确提到 OOMKilled"}],
            }, '{"layer":"L2"}')

    node.ai_call = _RecordingAICall()

    result, returned_events = node._analyze_with_llm("我的服务为什么 OOM 了")

    assert result["layer"] == "L2"
    assert "工作负载层" == result["layer_name"]
    assert result["confidence"] == 0.78
    assert "full_analysis" in result
    assert len(node.ai_call.calls) == 1
    assert "分析文本" in node.ai_call.calls[0]["question"]
    assert returned_events == thinking_events


def test_layer_normalizes_event_only_anomalies_to_healthy():
    node = LayerClassifierNode()
    result = {
        "layer": "L2",
        "layers": ["L2"],
        "layer_name": "工作负载层",
        "confidence": 0.72,
        "reasoning": "发现 Warning 事件，怀疑工作负载异常",
        "key_entities": [],
        "possible_scenarios": [],
    }
    thinking_events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubernetes_jq_query",
            "result": "aiops-e2e Warning BackOff Pod/appconfigfail-123: Back-off restarting failed container app",
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_by_kind_in_namespace",
            "result": "No resources found in aiops-e2e namespace.",
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_by_kind_in_cluster",
            "result": "NAME     STATUS   ROLES\nmaster   Ready    control-plane\nnode1    Ready    <none>",
        },
    ]

    normalized = node._normalize_result_from_runtime_signals(result, thinking_events)

    assert normalized["layer"] == "HEALTHY"
    assert normalized["layers"] == ["HEALTHY"]
    assert normalized["confidence"] <= 0.72
    assert "历史事件" in normalized["reasoning"]


def test_layer_keeps_non_healthy_when_live_abnormal_signal_exists():
    node = LayerClassifierNode()
    result = {
        "layer": "L2",
        "layers": ["L2"],
        "layer_name": "工作负载层",
        "confidence": 0.88,
        "reasoning": "发现当前存在 CrashLoopBackOff Pod",
        "key_entities": [],
        "possible_scenarios": [],
    }
    thinking_events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_by_kind_in_namespace",
            "result": "NAME READY STATUS RESTARTS\nappconfigfail-123 0/1 CrashLoopBackOff 5",
        }
    ]

    normalized = node._normalize_result_from_runtime_signals(result, thinking_events)

    assert normalized["layer"] == "L2"
    assert normalized["reasoning"] == "发现当前存在 CrashLoopBackOff Pod"


def test_layer_should_stop_when_only_stale_events_remain_after_healthy_snapshots():
    node = LayerClassifierNode()
    thinking_events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_by_kind_in_cluster",
            "result": "NAMESPACE NAME READY STATUS RESTARTS\ndefault app 1/1 Running 0\nkube-system coredns 1/1 Running 0",
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_by_kind_in_cluster",
            "result": "NAME STATUS ROLES\nmaster Ready control-plane\nnode1 Ready <none>",
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "run_bash_command",
            "result": '{"success": true, "stdout": "NAMESPACE   LAST SEEN   TYPE      REASON    OBJECT                               MESSAGE\\naiops-e2e   48m         Warning   BackOff   pod/appconfigfail-123               Back-off restarting failed container app"}',
        },
    ]

    assert node._should_stop_collection_early(thinking_events) is True


def test_layer_should_not_stop_for_recent_events():
    node = LayerClassifierNode()
    thinking_events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_by_kind_in_cluster",
            "result": "NAMESPACE NAME READY STATUS RESTARTS\ndefault app 1/1 Running 0",
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_by_kind_in_cluster",
            "result": "NAME STATUS ROLES\nmaster Ready control-plane",
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "run_bash_command",
            "result": '{"success": true, "stdout": "NAMESPACE   LAST SEEN   TYPE      REASON    OBJECT                               MESSAGE\\naiops-e2e   2m          Warning   BackOff   pod/appconfigfail-123               Back-off restarting failed container app"}',
        },
    ]

    assert node._should_stop_collection_early(thinking_events) is False


def test_layer_should_not_stop_when_live_abnormal_object_exists():
    node = LayerClassifierNode()
    thinking_events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_by_kind_in_cluster",
            "result": "NAMESPACE NAME READY STATUS RESTARTS\ndefault app 0/1 CrashLoopBackOff 3",
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "run_bash_command",
            "result": '{"success": true, "stdout": "NAMESPACE   LAST SEEN   TYPE      REASON    OBJECT                               MESSAGE\\ndefault     48m         Warning   BackOff   pod/app               Back-off restarting failed container app"}',
        },
    ]

    assert node._should_stop_collection_early(thinking_events) is False


def test_layer_uses_llm_for_clear_query_requests():
    node = LayerClassifierNode()
    called = {"llm": False}

    def _fake_llm(question):
        called["llm"] = True
        return (
            {
                "layer": "QUERY",
                "layers": ["QUERY"],
                "layer_name": "直接查询",
                "confidence": 0.95,
                "reasoning": "LLM 判定用户在直接查询指标",
                "key_entities": [],
                "possible_scenarios": [],
            },
            [],
        )

    node.ai_call = object()
    node._analyze_with_llm = _fake_llm

    result = node.execute({"question": "查询集群每个节点 CPU 和内存使用率"})

    assert called["llm"] is True
    assert result["layer"] == Layer.QUERY
    assert result["layer_reasoning"]


def test_layer_does_not_lightweight_route_diagnosis_questions():
    node = LayerClassifierNode()

    called = {"llm": False}

    def _fake_llm(question):
        called["llm"] = True
        return (
            {
                "layer": "L2",
                "layers": ["L2"],
                "layer_name": "工作负载层",
                "confidence": 0.91,
                "reasoning": "用户在询问集群问题原因，属于诊断请求",
                "key_entities": [],
                "possible_scenarios": [],
            },
            [],
        )

    node.ai_call = object()
    node._analyze_with_llm = _fake_llm

    result = node.execute({"question": "我的集群有什么问题？分析下原因"})

    assert called["llm"] is True
    assert result["layer"] == Layer.L2


def test_layer_does_not_lightweight_route_cluster_status_diagnosis_wording():
    node = LayerClassifierNode()

    called = {"llm": False}

    def _fake_llm(question):
        called["llm"] = True
        return (
            {
                "layer": "L1",
                "layers": ["L1"],
                "layer_name": "集群与节点层",
                "confidence": 0.83,
                "reasoning": "‘集群什么情况’属于整体状态诊断，不是明确数据查询",
                "key_entities": [],
                "possible_scenarios": [],
            },
            [],
        )

    node.ai_call = object()
    node._analyze_with_llm = _fake_llm

    result = node.execute({"question": "我的集群现在什么情况？"})

    assert called["llm"] is True
    assert result["layer"] == Layer.L1


def test_query_conclusion_uses_llm_even_when_query_result_present():
    node = ConclusionFormatterNode()

    node.ai_call = _RecordingAICall(
        """## 📊 查询结果

- **查询目标**: 查询集群每个节点 CPU 和内存使用率

## 📈 数据摘要
| 节点 | CPU 使用率 | 内存使用率 |
|------|------------|------------|
| master | 13.7% | 26.2% |
"""
    )

    state = {
        "question": "查询集群每个节点 CPU 和内存使用率",
        "layer": Layer.QUERY,
        "query_result": {
            "query_target": "查询集群每个节点 CPU 和内存使用率",
            "collection_summary": "计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%",
            "columns": [
                {"key": "node", "label": "节点"},
                {"key": "cpu", "label": "CPU 使用率"},
                {"key": "memory", "label": "内存使用率"},
            ],
            "rows": [
                {"node": "master", "cpu": "13.7%", "memory": "26.2%"},
                {"node": "node1", "cpu": "9.8%", "memory": "19.3%"},
            ],
            "notes": ["数据来自 Prometheus 查询。"],
            "sources": [
                {"tool": "execute_prometheus_instant_query", "query": "cpu_query"},
                {"tool": "execute_prometheus_instant_query", "query": "mem_query"},
            ],
        },
        "thinking_events": [],
    }

    result = node.execute(state)

    assert len(node.ai_call.calls) == 1
    assert "## 📊 查询结果" in result["conclusion"]
    assert "master" in result["conclusion"]


def test_query_conclusion_falls_back_to_llm_when_query_result_missing():
    node = ConclusionFormatterNode()

    node.ai_call = _RecordingAICall(
        """## 📊 查询结果

- **查询目标**: 查询集群每个节点 CPU 和内存使用率

## 📈 数据摘要
| 工具 | 结果摘要 |
|------|----------|
| execute_prometheus_instant_query | master=13.7%,node1=9.8% |
"""
    )

    state = {
        "question": "查询集群每个节点 CPU 和内存使用率",
        "layer": Layer.QUERY,
        "query_result": None,
        "evidence_analysis": (
            '{"collection_summary":"计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%",'
            '"tool_data":[{"tool":"execute_prometheus_instant_query","data":"master=13.7%,node1=9.8%"}],'
            '"evidence_plan":[{"tool":"execute_prometheus_instant_query","command":"cpu_query"}],'
            '"missing_reasons":[]}'
        ),
        "thinking_events": [],
    }

    result = node.execute(state)

    assert len(node.ai_call.calls) == 1
    assert "## 📊 查询结果" in result["conclusion"]
    assert "execute_prometheus_instant_query" in result["conclusion"]


def test_query_evidence_execute_builds_structured_query_result():
    node = EvidenceCollectorNode()
    node._save_thinking = lambda state, new_state, thinking_events: None
    node._extract_tool_data_from_thinking = lambda events: [
        {"tool": "execute_prometheus_instant_query", "data": '{"status":"success"}', "duration_s": 0}
    ]
    node._plan_evidence_with_llm = lambda **kwargs: (
        [
            {"id": "e1", "description": "查询 CPU", "level": "critical", "tool": "execute_prometheus_instant_query", "command": "cpu_query", "purpose": "cpu"},
            {"id": "e2", "description": "查询内存", "level": "critical", "tool": "execute_prometheus_instant_query", "command": "mem_query", "purpose": "memory"},
        ],
        [
            {"type": "tool_result", "status": "success", "tool_name": "execute_prometheus_instant_query", "result_preview": '{"status":"success"}', "result": '{"status":"success"}'},
        ],
        "已完成查询",
    )

    class _NormalizeAICall:
        def __init__(self):
            self.calls = []

        def call_simple_json(self, system_prompt, question, **kwargs):
            self.calls.append({"system_prompt": system_prompt, "question": question})
            raw = """```json
{
  "query_target": "查询集群每个节点 CPU 和内存使用率",
  "collection_summary": "计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%",
  "columns": [
    {"key": "node", "label": "节点"},
    {"key": "cpu", "label": "CPU 使用率"},
    {"key": "memory", "label": "内存使用率"}
  ],
  "rows": [
    {"node": "master", "cpu": "13.7%", "memory": "26.2%"}
  ],
  "notes": ["数据来自 Prometheus。"],
  "sources": [
    {"tool": "execute_prometheus_instant_query", "query": "cpu_query"}
  ]
}
```"""
            return ({
                "query_target": "查询集群每个节点 CPU 和内存使用率",
                "collection_summary": "计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%",
                "columns": [
                    {"key": "node", "label": "节点"},
                    {"key": "cpu", "label": "CPU 使用率"},
                    {"key": "memory", "label": "内存使用率"},
                ],
                "rows": [
                    {"node": "master", "cpu": "13.7%", "memory": "26.2%"},
                ],
                "notes": ["数据来自 Prometheus。"],
                "sources": [
                    {"tool": "execute_prometheus_instant_query", "query": "cpu_query"},
                ],
            }, raw)

    node.ai_call = _NormalizeAICall()

    result = node.execute({
        "question": "查询集群每个节点 CPU 和内存使用率",
        "layer": Layer.QUERY,
        "layer_analysis": "{}",
        "possible_scenarios": [],
        "key_entities": [],
        "thinking_events": [],
    })

    assert result["query_result"]["query_target"] == "查询集群每个节点 CPU 和内存使用率"
    assert result["query_result"]["rows"][0]["node"] == "master"
    assert len(node.ai_call.calls) == 1


def test_extract_tool_data_prefers_full_result_over_preview():
    node = EvidenceCollectorNode()

    tool_data = node._extract_tool_data_from_thinking([
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "execute_prometheus_instant_query",
            "result_preview": '{"status":"success","data":"truncated"}',
            "result": '{"status":"success","data":{"result":[{"metric":{"node":"master"},"value":[1,"13.7"]}]}}',
            "duration_seconds": 1.2,
        }
    ])

    assert tool_data == [
        {
            "tool": "execute_prometheus_instant_query",
            "data": '{"status":"success","data":{"result":[{"metric":{"node":"master"},"value":[1,"13.7"]}]}}',
            "duration_s": 1.2,
        }
    ]


def test_rca_lite_mode_no_output_uses_generic_llm_fallback():
    node = RootCauseAnalyzerNode()

    class _EmptyAICall:
        def call_simple_json(self, *args, **kwargs):
            return None, ""

    node.ai_call = _EmptyAICall()

    result, thinking_events = node._analyze_with_llm_lite(
        question="我的服务为什么异常",
        layer=Layer.L2,
        evidence_summary="1. [✅ 已采集] pod 重启",
    )

    assert result["confidence"] <= 0.2
    assert "LLM 未返回有效结果" in result["confidence_reason"]
    assert result["root_cause"]
    assert thinking_events == []


def test_rca_lite_mode_exception_uses_generic_llm_fallback_without_rules():
    node = RootCauseAnalyzerNode()

    class _FailingAICall:
        def call_simple_json(self, *args, **kwargs):
            raise RuntimeError("llm timeout")

    node.ai_call = _FailingAICall()

    result, thinking_events = node._analyze_with_llm_lite(
        question="我的服务为什么异常",
        layer=Layer.L2,
        evidence_summary="1. [✅ 已采集] pod 重启",
    )

    assert result["confidence"] <= 0.2
    assert "llm timeout" in result["confidence_reason"]
    assert thinking_events == []


def test_layer_prompts_prioritize_user_intent_for_query_requests():
    expected_phrases = [
        "先判断用户意图",
        "如果用户明确是在查询指标/状态/列表/资源使用率，优先判定为 QUERY",
        "QUERY 场景下，不要因为集群中存在其他异常 Pod 就自动转入故障诊断",
        "只有当用户明确问“有什么问题 / 为什么异常 / 帮我排查 / 根因是什么”时，才进入 L0-L4 定层诊断流程",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT


def test_layer_prompt_requires_event_validation_against_current_state():
    expected_phrases = [
        "events 只能作为辅助证据，不能单独作为当前故障的判定依据",
        "如果 Warning 事件指向某个 Pod/Node/Workload，必须再用当前状态查询确认该对象仍然存在且当前仍异常",
        "如果事件对应对象已经不存在，或当前状态已恢复正常，则该事件视为历史噪音，不得据此判定当前存在故障",
        "对于陈旧事件，应降低优先级；如果事件时间明显早于当前诊断窗口，默认视为历史线索而非当前故障",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT


def test_query_prompt_boundaries_are_explicit_between_layer_and_evidence():
    layer_phrases = [
        "如果当前请求是 QUERY，你的任务只是在阶段1识别查询意图、提取查询对象、指标、范围和维度",
        "不要在 layer 节点中尝试直接回答用户问题",
        "不要在 layer 节点中做指标计算、结果聚合、脚本拼接、jq 处理、bash 推导或资源估算",
        "QUERY 模式下，真实数据采集统一交给 evidence 节点完成",
    ]
    evidence_phrases = [
        "layer=QUERY：你负责真实数据采集和返回查询结果所需的数据",
        "不要把 QUERY 请求再退回给 layer 节点处理",
        "在本节点内完成查询语义归一化，输出给下游可直接渲染的结构化结果",
        "只保留用户明确询问的对象、维度和指标，不扩展无关指标",
    ]

    for phrase in layer_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT

    for phrase in evidence_phrases:
        assert phrase in EVIDENCE_COLLECTOR_PROMPT


def test_query_evidence_normalization_prompt_defines_json_only_contract():
    expected_phrases = [
        "把 QUERY 请求整理成一个稳定的结构化 JSON",
        "你不负责重新查询，不负责诊断，不负责根因分析，只负责把真实结果归一化",
        "只保留用户明确询问的对象、维度和指标",
        "输出必须是可解析 JSON，不要输出 Markdown，不要输出解释性前言",
    ]

    for phrase in expected_phrases:
        assert phrase in QUERY_EVIDENCE_NORMALIZATION_PROMPT_ZH


def test_layer_prompts_prioritize_runbook_as_high_priority_reference():
    expected_phrases = [
        "如果当前问题与某个 runbook 明显相关，优先调用 fetch_runbook 获取参考",
        "runbook 是额外知识储备和诊断参考，优先级高于你自己的泛化经验判断",
        "在 DIAGNOSIS 场景下，只要已出现明确场景信号，就应尽早查看相关 runbook",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT


def test_workflow_prompts_default_to_chinese_and_support_english_switch():
    zh_prompt = get_workflow_prompt("layer")
    en_prompt = get_workflow_prompt("layer", prompt_language="en")

    assert "角色：K8s 问题分层专家" in zh_prompt
    assert "Role: Kubernetes issue layer classifier" in en_prompt
    assert "先判断用户意图" not in en_prompt


def test_conclusion_prompt_supports_independent_response_language():
    prompt = get_workflow_prompt(
        "conclusion",
        prompt_language="en",
        response_language="en",
    )

    assert "You are a senior Kubernetes diagnostic report expert." in prompt
    assert "All user-facing final report text must be in English." in prompt


def test_conclusion_mode_instructions_are_centrally_managed():
    query_instruction = get_conclusion_mode_instruction("query", "查询 CPU", prompt_language="zh")
    healthy_instruction = get_conclusion_mode_instruction("healthy", "我的集群健康吗", prompt_language="zh")
    query_instruction_en = get_conclusion_mode_instruction("query", "show CPU", prompt_language="en")

    assert "只回答用户明确询问的对象、维度和指标" in query_instruction
    assert "绝对不要猜测" in query_instruction
    assert "集群当前运行正常，未发现异常" in healthy_instruction
    assert "Never guess" in query_instruction_en
    assert "show CPU" in query_instruction_en


def test_holmes_service_i18n_getters_preserve_default_behavior_and_allow_override():
    service = HolmesService()
    assert service.get_prompt_language() == "zh"
    assert service.get_response_language() == "zh"

    service.i18n_config = {"prompt_language": "en", "response_language": "en"}
    assert service.get_prompt_language() == "en"
    assert service.get_response_language() == "en"
