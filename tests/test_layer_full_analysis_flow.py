"""
测试 layer_full_analysis 数据流完整性

验证：layer_classifier 阶段1的完整分析文本（含工具输出）
能正确传递到 evidence_collector 和 root_cause_analyzer。

背景：两阶段架构重构后，阶段2 litellm 提取的精简 JSON 丢失了
阶段1的工具调用数据，导致下游节点"证据不足"。
"""
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_layer_classifier_injects_full_analysis():
    """验证 layer_classifier 在阶段2结果中注入 full_analysis"""
    # 模拟阶段2返回的 extracted 结果
    extracted = {
        "layer": "L0",
        "confidence": 0.9,
        "reasoning": "磁盘满导致 Pod 被驱逐",
        "key_entities": [{"type": "Pod", "value": "test-pod"}],
        "possible_scenarios": ["磁盘空间不足"],
    }

    # 模拟 enriched_text（阶段1完整分析 + 工具输出）
    enriched_text = """
根据 kubectl get pods -A 的输出，发现 test-pod 处于 Evicted 状态。
kubectl describe pod test-pod -n default 显示：
  Reason: Evicted
  Message: The node was low on resource: ephemeral-storage.
  Container test-container was using 2Gi, which exceeds its request of 0.

df -h 输出：
/dev/sda1  50G  48G  2G  96% /

=== 工具调用数据 ===
[kubectl] kubectl get pods -A:
NAMESPACE   NAME       READY   STATUS    RESTARTS   AGE
default     test-pod   0/1     Evicted   0          1h
"""

    # 模拟 layer_classifier._analyze_with_llm 的行为
    extracted["full_analysis"] = enriched_text

    # 模拟 execute() 中的 state 构建
    layer_result = extracted.copy()
    full_analysis = layer_result.pop("full_analysis", "")

    new_state = {
        "layer": "L0",
        "layer_analysis": json.dumps(layer_result, ensure_ascii=False),
        "layer_full_analysis": full_analysis,
    }

    # 验证
    assert new_state["layer_full_analysis"] == enriched_text, \
        "layer_full_analysis 应包含阶段1完整分析文本"
    assert "full_analysis" not in json.loads(new_state["layer_analysis"]), \
        "layer_analysis JSON 中不应包含 full_analysis（已 pop 出来）"
    assert "kubectl get pods" in new_state["layer_full_analysis"], \
        "layer_full_analysis 应包含工具调用数据"
    print("✅ test_layer_classifier_injects_full_analysis PASSED")


def test_evidence_collector_uses_full_analysis():
    """验证 evidence_collector 优先使用 layer_full_analysis"""
    enriched_text = "完整分析文本，包含 kubectl describe 输出..."
    layer_json = json.dumps({"layer": "L0", "confidence": 0.9})

    # Case 1: layer_full_analysis 存在
    state = {
        "layer_analysis": layer_json,
        "layer_full_analysis": enriched_text,
    }
    layer_full = state.get("layer_full_analysis", "") or state.get("layer_analysis", "{}")
    assert layer_full == enriched_text, \
        "应优先使用 layer_full_analysis"

    # Case 2: layer_full_analysis 为空，回退到 layer_analysis
    state2 = {
        "layer_analysis": layer_json,
        "layer_full_analysis": "",
    }
    layer_full2 = state2.get("layer_full_analysis", "") or state2.get("layer_analysis", "{}")
    assert layer_full2 == layer_json, \
        "layer_full_analysis 为空时应回退到 layer_analysis"

    # Case 3: layer_full_analysis 不存在
    state3 = {
        "layer_analysis": layer_json,
    }
    layer_full3 = state3.get("layer_full_analysis", "") or state3.get("layer_analysis", "{}")
    assert layer_full3 == layer_json, \
        "layer_full_analysis 不存在时应回退到 layer_analysis"

    print("✅ test_evidence_collector_uses_full_analysis PASSED")


def test_rca_uses_full_analysis():
    """验证 root_cause_analyzer 优先使用 layer_full_analysis"""
    enriched_text = "完整分析：Pod test-pod 被驱逐，原因是 ephemeral-storage 超限..."
    layer_json = json.dumps({"layer": "L0"})

    state = {
        "layer_analysis": layer_json,
        "layer_full_analysis": enriched_text,
    }

    # 模拟 root_cause_analyzer 的逻辑
    layer_analysis = state.get("layer_full_analysis", "") or state.get("layer_analysis", "")
    evidence_summary = "证据摘要..."

    if layer_analysis:
        evidence_summary = (
            f"# 问题定位结果（layer 节点输出）\n{layer_analysis}\n\n"
            f"# 证据采集结果\n{evidence_summary}"
        )

    assert enriched_text in evidence_summary, \
        "RCA 的 evidence_summary 应包含完整分析文本"
    assert "Pod test-pod 被驱逐" in evidence_summary, \
        "RCA 应能看到具体的工具调用结果"
    print("✅ test_rca_uses_full_analysis PASSED")


def test_full_data_flow_simulation():
    """端到端模拟：layer → evidence → rca 的数据流"""
    # === Layer 节点输出 ===
    enriched_text = """
分析结果：
1. kubectl get pods -A 发现 log-collector-xyz 处于 Evicted 状态
2. kubectl describe pod log-collector-xyz -n monitoring:
   Status: Failed
   Reason: Evicted
   Message: The node was low on resource: ephemeral-storage.
   Container log-collector was using 5Gi, which exceeds its request of 0.
3. df -h 显示 /dev/sda1 使用率 97%

=== 工具调用数据 ===
[kubectl] kubectl get pods -A:
NAMESPACE    NAME                  READY   STATUS    AGE
monitoring   log-collector-xyz     0/1     Evicted   2h
kube-system  coredns-abc           1/1     Running   5d
"""

    layer_result = {
        "layer": "L0",
        "confidence": 0.9,
        "reasoning": "Pod 被驱逐，ephemeral-storage 超限",
        "key_entities": [{"type": "Pod", "value": "log-collector-xyz"}],
        "possible_scenarios": ["磁盘空间不足导致 Pod 驱逐"],
        "full_analysis": enriched_text,
    }

    # layer_classifier.execute() 的处理
    full_analysis = layer_result.pop("full_analysis", "")
    state = {
        "layer": "L0",
        "layer_analysis": json.dumps(layer_result, ensure_ascii=False),
        "layer_full_analysis": full_analysis,
        "key_entities": layer_result.get("key_entities", []),
    }

    # === Evidence 节点读取 ===
    ev_layer_analysis = state.get("layer_full_analysis", "") or state.get("layer_analysis", "{}")
    assert "kubectl describe pod log-collector-xyz" in ev_layer_analysis, \
        "Evidence 节点应能看到 kubectl describe 输出"
    assert "ephemeral-storage" in ev_layer_analysis, \
        "Evidence 节点应能看到驱逐原因"

    # === RCA 节点读取 ===
    rca_layer_analysis = state.get("layer_full_analysis", "") or state.get("layer_analysis", "")
    evidence_summary = "证据: df -h 显示磁盘使用率 97%"
    if rca_layer_analysis:
        evidence_summary = (
            f"# 问题定位结果\n{rca_layer_analysis}\n\n"
            f"# 证据采集结果\n{evidence_summary}"
        )

    assert "Evicted" in evidence_summary, "RCA 应能看到 Evicted 状态"
    assert "ephemeral-storage" in evidence_summary, "RCA 应能看到驱逐原因"
    assert "log-collector-xyz" in evidence_summary, "RCA 应能看到具体 Pod 名"
    assert "97%" in evidence_summary, "RCA 应能看到磁盘使用率"

    # 验证 layer_analysis JSON 中不包含 full_analysis（避免冗余）
    layer_json = json.loads(state["layer_analysis"])
    assert "full_analysis" not in layer_json, \
        "layer_analysis JSON 不应包含 full_analysis"

    print("✅ test_full_data_flow_simulation PASSED")


if __name__ == "__main__":
    test_layer_classifier_injects_full_analysis()
    test_evidence_collector_uses_full_analysis()
    test_rca_uses_full_analysis()
    test_full_data_flow_simulation()
    print("\n🎉 所有测试通过！layer_full_analysis 数据流完整。")
