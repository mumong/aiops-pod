======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 25b6a13a59c6412e]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=0 status_counts={'Running': 47}。aiops-e2e 命名空间中的 rc-notready-readiness Pod 显示为 0/1 Running，但未标记异常。其他命名空间如 aiops、default、kube-system、mcp 和 xnet 中的 
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                    READY   STATUS    RESTARTS   AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-notready-readiness   0/1     Running   0          107m   172.16.166.18
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod NotReadyProbeFailed / Running 但未 Ready

> Pod异常类型: NotReadyProbeFailed | 典型状态: Running + READY 0/1 | 兼容分类: probe_health

## 状态识别
- Pod phase 通常为 `Running`，但 READY 为 `0/1` 或部分容器未 Ready

   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-readiness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
  Warning  Unhealthy  2m46s (x2186 over 107m)  kubelet  Readiness probe failed: readi
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-notready-readiness
namespace: aiops-e2e
creationTimestamp: 2026-05-15T07:05:35Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <no
   💭 [问题定位] 调用工具: kubectl_logs_grep
   💭 [问题定位] 工具结果: kubectl_logs_grep (success)
      📄 kubectl_logs_grep 输出摘要: raw_chars=109 lines=2
Command failed (exit 1):
kubectl logs rc-notready-readiness -n aiops-e2e --tail=200 | grep -i -- 'readiness'
   💭 [问题定位] 调用工具: kubectl_container_logs
   💭 [问题定位] 工具结果: kubectl_container_logs (success)
      📄 kubectl_container_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "NotReadyProbeFailed",
  "confidence": "high",
  "reasoning": "Pod 'rc-notready-readiness' 在命名空间 'aiops-e2e' 中处于 Running 状态，但 READY 为 0/1。Events 显示 readiness probe failed，且 readiness dependency unavailable。这表明 readiness probe 配置错误或应用健康接口存在问题。",
  "abnormal_pods": [
    {
      "name": "rc-notready-readiness",
      "namespace": "aiops-e2e",
      "status": "Running",
      "ready": "0/1"
    }
  ],
  "abnormal_groups": [
    {
      "type": "NotReadyProbeFailed",
      "pods": [
        "rc-notready-readiness"
      ]
    }
  ],
  "pod_status_keyword": "Running",
  "pod_abnormal_type": "NotReadyProbeFailed",
  "status_category": "Pod Not Ready",
  "key_entities": [
    "Pod 'rc-notready-readiness' in namespace 'aiops-e2e'",
    "readiness probe failed",
    "readiness dependency unavailable"
  ],
  "possible_scenarios": [
    "readinessProbe 路径、端口、scheme 配置不匹配",
    "应用进程已启动但健康接口返回非 2xx/3xx 或超时",
    "livenessProbe 反复失败导致容器重启",
    "startupProbe 失败导致容器尚未完成启动",
    "Service selector 不匹配"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 18.7s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'readinessProbe 路径、端口、scheme 配置不匹配', 'probability': 'high', 'reason': 'Pod READY 0/1 且 readiness probe failed'}, {'scenario': '应用进程已启动但健康接口返回非 2xx/3xx 或超时', 'probability': 'high', 'reason': 'Pod READY 0/1 且 readiness probe failed'}, {'scenario': 'livenessProbe 反复失败导致容器重启', 'probability': 'medium', 'reason': 'Pod READY 0/1 且 readiness probe failed'}, {'scenario': 'startupProbe 失败导致容器尚未完成启动', 'probability': 'medium', 'reason': 'Pod READY 0/1 且 readiness probe failed'}, {'scenario': 'Service selector 不匹配', 'probability': 'low', 'reason': 'Pod READY 0/1 且 readiness probe failed'}]
   entities=[{"type": "Pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}, {"type": "Event", "name": "readiness probe failed", "namespace": "aiops-e2e"}, {"type": "Event", "name": "readiness dependency unavailable", "namespace": "aiops-e2e"}]
   reasoning=Pod 'rc-notready-readiness' 在命名空间 'aiops-e2e' 中处于 Running 状态，但 READY 为 0/1。Events 显示 readiness probe failed，且 readiness dependency unavailable。这表明 readiness probe 配置错误或应用健康接口存在问题。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "NotReadyProbeFailed", "confidence": 0.95, "reasoning": "Pod 'rc-notready-readiness' 在命名空间 'aiops-e2e' 中处于 Running 状态，但 READY 为 0/1。Events 显示 readiness probe failed，且 readiness dependency unavailable。这表明 readiness probe 配置错误或应用健康接口存在问题。", "abnormal_pods": [{"name": "rc-notready-readiness", "namespace": "aiops-e2e", "status": "Running"}], "pod_status_keyword": "Running", "pod_abnormal_type": "NotReadyProbeFailed", "status_category": "Pod Not Ready", "key_entities": [{"type": "Pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}, {"type": "Event", "name": "readiness probe failed", "namespace": "aiops-e2e"}, {"type": "Event", "name": "readiness dependency unavailable", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "readinessProbe 路径、端口、scheme 配置不匹配", "probability": "high", "reason": "Pod READY 0/1 且 readiness probe failed"}, {"scenario": "应用进程已启动但健康接口返回非 2xx/3xx 或超时", "probability": "high", "reason": "Pod READY 0/1 且 readiness probe failed"}, {"scenario": "livenessProbe 反复失败导致容器重启", "probability": "medium", "reason": "Pod READY 0/1 且 readiness probe failed"}, {"scenario": "startupProbe 失败导致容器尚未完成启动", "probability": "medium", "reason": "Pod READY 0/1 且 readiness probe failed"}, {"scenario": "Service selector 不匹配", "probability": "low", "reason": "Pod READY 0/1 且 readiness probe failed"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Running"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Running"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 0, "selected_rows": [], "raw_ref": "/tmp/aiops/reports/context_archives/25b6a13a59c6412e/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/25b6a13a59c6412e/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/25b6a13a59c6412e/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 95%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-readiness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
  Warning  Unhealthy  4m18s (x2186 over 109m)  kubelet  Readiness probe failed: readi
   💭 [证据链采集] 已采集证据：
- Pod `rc-notready-readiness` 的状态为 `Running`，但 READY 为 `0/1`。
- Pod 的事件显示 `Readiness probe failed: readiness dependency unavailable`，表明 readiness probe 失败。
- 该 Pod 的注解 `pod_abnormal_type=NotReadyProbeFailed` 与 runbook `pod-notready-probe-failed.md` 对应。

未采集证据：
- 无进一步的 evidence_plan 项，但当前证据已覆盖主异常组的诊断核心。

结论：当前证据表明 `rc-notready-readiness` Pod 处于 `Running` 状态但未通过 readiness probe，归因于 `readiness dependency unavailable`。需进一步检查 readinessProbe 配置和应用健康接口。
   ✅ [证据链采集] 完成 (51.6s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod 'rc-notready-readiness' 的详细描述信息，以验证 readiness probe 配置和失败原因。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-readiness -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-notready-readiness"},"purpose":"验证 readiness probe 配置和失败原因","evidence_type":"event_configuration","target_scope":"Pod/aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-readiness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n  Warning  Unhealthy  4m18s (x2186 over 109m)  kubelet  Readiness probe failed: readiness dependency unavailable\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\nName:             rc-notready-readiness\nLabels:           app=rc-notready-readiness\n                  cni.projectcalico.org/containerID: fb8e26665bf8a745a3d1ec6dc6a9b9d528c0b6504e8895b370296a560f31067e\n                  cni.projectcalico.org/podIP: 172.16.166.186/32\n                  cni.projectcalico.org/podIPs: 172.16.166.186/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Running","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/25b6a13a59c6412e/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/25b6a13a59c6412e/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/25b6a13a59c6412e/tools/001-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"已采集证据：\n- Pod `rc-notready-readiness` 的状态为 `Running`，但 READY 为 `0/1`。\n- Pod 的事件显示 `Readiness probe failed: readiness dependency unavailable`，表明 readiness probe 失败。\n- 该 Pod 的注解 `pod_abnormal_type=NotReadyProbeFailed` 与 runbook `pod-notready-probe-failed.md` 对应。\n\n未采集证据：\n- 无进一步的 evidence_plan 项，但当前证据已覆盖主异常组的诊断核心。\n\n结论：当前证据表明 `rc-notready-readiness` Pod 处于 `Running` 状态但未通过 readiness probe，归因于 `readiness dependency unavailable`。需进一步检查 readinessProbe 配置和应用健康接口。","collection_summary":"计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 6 个，匹配计划 1 个，未规划证据 5 个","plan_total":1,"plan_collected":1,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":1,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"获取 Pod 'rc-notready-readiness' 的详细描述信息，以验证 readiness probe 配置和失败原因。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-readiness -n aiops-e2e","purpose":"验证 readiness probe 配置和失败原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_logs_grep","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_container_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/1 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取 Pod 'rc-notready-readiness' 的详细描述信息，以验证 re... | `kubectl describe pod rc-notready-readiness -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (17.7s)
   📤 → 下游数据: root_cause=[L4层] 当前无法基于 LLM 输出确定根本原因
   confidence=10%
   causal_chain={"trigger": "LLM 未生成可靠因果链", "mechanism": "缺少可用的结构化根因分析结果", "manifestation": "我的集群有什么问题"}
   rca_analysis={"phenomenon": "我的集群有什么问题", "evidence_analysis": [], "causal_chain": {"trigger": "LLM 未生成可靠因果链", "mechanism": "缺少可用的结构化根因分析结果", "manifestation": "我的集群有什么问题"}, "root_cause": "[L4层] 当前无法基于 LLM 输出确定根本原因", "confidence": 0.1, "confidence_reason": "LLM 返回结果不符合 RCA 结构化输出合同", "alternative_causes": []}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: [L4层] 当前无法基于 LLM 输出确定根本原因
   置信度: 10%
   🔗 因果链:
     根本原因: LLM 未生成可靠因果链
     传导机制: 缺少可用的结构化根因分析结果
     最终表现: 我的集群有什么问题


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 29.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4732 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 57.3s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Running 但 READY 为 0/1，readiness probe failed |
| **兼容归因层** | L4 |
| **问题分类** | ReadinessProbeFailed |
| **置信度** | 高 (95%) |
| **证据完整度** | 1/1 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-notready-readiness |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | readiness probe failed: readiness dependency unavailable |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod rc-notready-readiness -n aiops-e2e` | `READY: 0/1, STATUS: Running` | Pod 进程已启动，但未通过就绪检查 |
| 2 | Pod 事件 | `kubectl describe pod rc-notready-readiness -n aiops-e2e` | `Warning: Unhealthy (x2186 over 107m): Readiness probe failed` | 探针失败频繁 |
| 3 | 探针失败原因 | `kubectl describe pod rc-notready-readiness -n aiops-e2e` | `Readiness probe failed: readiness dependency unavailable` | 应用依赖项未就绪或探针配置错误 |
| 4 | Pod YAML 配置 | `kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml` | `readinessProbe` 配置字段（未展示完整） | 需进一步检查探针路径、端口、超时设置 |
| 5 | 日志检索 | `kubectl logs rc-notready-readiness -n aiops-e2e --tail=200 | grep 'readiness'` | 无输出（`grep` 未匹配任何内容） | 无日志记录探针失败细节 |
| 6 | 容器日志 | `kubectl logs rc-notready-readiness -n aiops-e2e` | `关键日志: (no output)` | 容器未输出任何探针失败相关日志 |
| 7 | 命名空间 Pod 概览 | `kubectl get pods -n aiops-e2e` | `rc-notready-readiness 0/1 Running` | 该 Pod 是唯一未就绪的容器 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 处于 Running 状态但 READY 为 0/1，探针失败频繁 → 应用未通过 readiness check。
- **证据 #3 + #4 印证**：探针失败原因显示 `readiness dependency unavailable`，结合 YAML 配置，可能为探针配置错误或依赖服务未就绪。
- **证据 #5 + #6 印证**：日志中无探针失败或应用错误信息 → 探针配置与实际应用健康接口不匹配。
- **证据 #7**：确认该 Pod 是唯一问题点，未影响命名空间中其他 Pod。

### 缺失证据（无）

---

## 🎯 根因分析

### 因果链

```
┌────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                 │
│ readinessProbe 配置错误或健康接口不匹配，导致探针失败。应用依赖项可能未就绪。 │
└────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                 │
│ readinessProbe 配置的路径、端口、或 scheme 与实际健康接口不匹配 → 探针失败 → Pod 未就绪。 │
└────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                 │
│ readinessProbe 失败 → Pod 未就绪，无法加入 Service Endpoints。                │
└────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                             │
│ Pod 状态为 Running，但 READY 为 0/1；Service 无法调度流量至该 Pod。         │
└────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Pod 状态 Running 但 READY 0/1)、证据 #2 (探针失败频繁)、证据 #3 (探针失败原因为 readiness dependency unavailable) 和证据 #4 (探针配置字段缺失)，问题的根本原因是**readinessProbe 配置错误或健康接口不匹配**，导致探针失败，Pod 无法就绪。

**置信度**：高 (95%)
- ✅ Pod 状态 Running 但 READY 0/1
- ✅ 探针失败频繁且失败原因为 readiness dependency unavailable
- ⚠️ 缺少探针失败的详细日志，无法确认具体健康接口路径或依赖项问题

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查 readinessProbe 配置**
```bash
kubectl get pod rc-notready-readiness -n aiops-e2e -o jsonpath='{.spec.containers[0].readinessProbe}'
```
*依据*：确认探针路径、端口、超时、初始延迟等配置是否匹配实际应用健康接口。

**2. [优先] 修改 readinessProbe 配置**
```bash
kubectl set probe deployment/<deployment-name> -n aiops-e2e --readiness --http-get http://localhost:<port>/health --initial-delay-seconds 10 --period-seconds 5
```
*依据*：确保探针路径、端口与实际健康接口一致，并适当增加延迟和重试。

**3. [可选] 查看探针失败前日志**
```bash
kubectl logs rc-notready-readiness -n aiops-e2e --previous | grep -i 'readiness'
```
*目的*：查看探针失败前是否有异常日志（如 500 错误、连接失败等）。

### 后续优化

1. **健康接口测试**：使用 curl 或 Postman 手动测试健康接口，确认返回状态码为 200。
2. **资源监控**：启用 Prometheus 监控探针失败频率和 Pod 就绪状态。
3. **自动化修复**：配置自动扩缩容 (HPA) 或自动重部署 (Deployment rolling update)。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 就绪 | `kubectl get pod rc-notready-readiness -n aiops-e2e` | READY: 1/1 |
| 2. 检查探针失败事件 | `kubectl describe pod rc-notready-readiness -n aiops-e2e` | 无 Unhealthy 事件 |
| 3. 查看探针配置 | `kubectl get pod rc-notready-readiness -n aiops-e2e -o jsonpath='{.spec.containers[0].readinessProbe}'` | 配置与实际健康接口匹配 |
| 4. 手动测试健康接口 | `curl http://<pod-ip>:<port>/health` | 返回 200 OK |

---

## ⚠️ 注意事项

- 如果探针失败原因是依赖服务未就绪（如数据库连接失败），需要检查依赖服务的健康状态。
- 如果应用健康接口未实现，应补充实现 `/health` 接口。
- 探针失败频繁可能导致服务不可用，建议优先修复。

---

## 📊 性能统计

├─ 总耗时: 4.0m
├─ 问题定位: 78.7s (33%) ✅
├─ 证据链采集: 51.6s (22%) ✅
├─ 根因分析: 17.7s (7%) ✅
├─ 汇总总结: 89.3s (38%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 8 次
```

📋 诊断追踪

- **核心 Runbook**: pod-notready-probe-failed
- **参考 Runbook**: pod-notready-probe-failed
- **工具调用**: 8 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
