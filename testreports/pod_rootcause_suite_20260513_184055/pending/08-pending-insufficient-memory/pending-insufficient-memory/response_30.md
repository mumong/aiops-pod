======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 805c0e80b45c450e]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Pending': 1, 'Running': 46}
NAMESPACE     NAME                                                READY   STATUS      RESTARTS      
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-insufficient-memory
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  28m (x8 over 63m)  default-scheduler  0/3 nodes are avai
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                             READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-insufficient-memory   0/1     Pending   0          68m   <non
   💭 [问题定位] {
  "layer": "L1",
  "derived_layer": "L1",
  "layers": ["L1"],
  "layer_name": "PendingUnschedulable",
  "confidence": 0.95,
  "reasoning": "Pod 'rc-pending-insufficient-memory' 在命名空间 'aiops-e2e' 中处于 'Pending' 状态，并且有 'FailedScheduling' 事件。事件信息显示 0/3 个节点可用，并且原因是 3 个节点的内存不足。这表明该 Pod 无法调度是因为集群中没有足够的内存资源。",
  "abnormal_pods": [
    {
      "name": "rc-pending-insufficient-memory",
      "namespace": "aiops-e2e",
      "status": "Pending",
      "reason": "FailedScheduling",
      "message": "0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod."
    }
  ],
  "abnormal_groups": [
    {
      "type": "PendingUnschedulable",
      "count": 1,
      "pods": [
        {
          "name": "rc-pending-insufficient-memory",
          "namespace": "aiops-e2e"
        }
      ]
    }
  ],
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "PendingUnschedulable",
  "status_category": "scheduling",
  "key_entities": [
    {
      "kind": "Pod",
      "name": "rc-pending-insufficient-memory",
      "namespace": "aiops-e2e"
    }
  ],
  "possible_scenarios": [
    {
      "scenario": "集群中没有足够的内存资源来调度 Pod。",
      "evidence": "Pod 'rc-pending-insufficient-memory' 的 'FailedScheduling' 事件显示 0/3 个节点可用，并且原因是 3 个节点的内存不足。"
    }
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (50.2s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': '集群中没有足够的内存资源来调度 Pod。', 'probability': 'high', 'reason': "Pod 'rc-pending-insufficient-memory' 的 'FailedScheduling' 事件显示 0/3 个节点可用，并且原因是 3 个节点的内存不足。"}]
   entities=[{"type": "Pod", "name": "rc-pending-insufficient-memory", "namespace": "aiops-e2e"}]
   reasoning=Pod 'rc-pending-insufficient-memory' 在命名空间 'aiops-e2e' 中处于 'Pending' 状态，并且有 'FailedScheduling' 事件。事件信息显示 0/3 个节点可用，并且原因是 3 个节点的内存不足。这表明该 Pod 无法调度是因为集群中没有足够的内存资源。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "Pod 'rc-pending-insufficient-memory' 在命名空间 'aiops-e2e' 中处于 'Pending' 状态，并且有 'FailedScheduling' 事件。事件信息显示 0/3 个节点可用，并且原因是 3 个节点的内存不足。这表明该 Pod 无法调度是因为集群中没有足够的内存资源。", "abnormal_pods": [{"name": "rc-pending-insufficient-memory", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-insufficient-memory", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "集群中没有足够的内存资源来调度 Pod。", "probability": "high", "reason": "Pod 'rc-pending-insufficient-memory' 的 'FailedScheduling' 事件显示 0/3 个节点可用，并且原因是 3 个节点的内存不足。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-memory"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-memory"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-insufficient-memory                      0/1     Pending     0             67m    <none>           <none>   <none>           <none>            app=rc-pending-insufficient-memory,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/805c0e80b45c450e/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/805c0e80b45c450e/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/805c0e80b45c450e/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-insufficient-memory
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  29m (x8 over 64m)  default-scheduler  0/3 nodes are avai
   💭 [证据链采集] 已采集证据：
1. `kubectl_describe` 显示 Pod `rc-pending-insufficient-memory` 处于 `Pending` 状态，`node` 为 `<none>`，说明尚未调度到任何节点。
2. 事件 `FailedScheduling` 明确指出调度失败原因是 `0/3 nodes are available: 3 Insufficient memory`，确认集群中没有足够内存资源来调度该 Pod。

未采集证据：
1. 未检查 Pod 的资源请求（`resources.requests.memory`）是否设置过高。
2. 未检查节点的内存使用情况和资源分配，以进一步确认是否真的没有空闲内存。
3. 未验证是否存在其他调度约束（如 `nodeSelector`、`affinity`、`taint`）导致调度失败。

冲突证据：
无。
   ✅ [证据链采集] 完成 (58.6s)
   📤 → 下游数据: evidence_items=4/4
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod 'rc-pending-insufficient-memory' 的详细信息以验证其调度失败原因。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-memory -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-pending-insufficient-memory","kind":"Pod"},"purpose":"验证调度失败的详细原因，如资源不足、taint 不匹配等。","evidence_type":"事件/状态","target_scope":"aiops-e2e/rc-pending-insufficient-memory","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-insufficient-memory\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  29m (x8 over 64m)  default-scheduler  0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nName:             rc-pending-insufficient-memory\nLabels:           app=rc-pending-insufficient-memory\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/805c0e80b45c450e/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/805c0e80b45c450e/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/805c0e80b45c450e/tools/001-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"已采集证据：\n1. `kubectl_describe` 显示 Pod `rc-pending-insufficient-memory` 处于 `Pending` 状态，`node` 为 `<none>`，说明尚未调度到任何节点。\n2. 事件 `FailedScheduling` 明确指出调度失败原因是 `0/3 nodes are available: 3 Insufficient memory`，确认集群中没有足够内存资源来调度该 Pod。\n\n未采集证据：\n1. 未检查 Pod 的资源请求（`resources.requests.memory`）是否设置过高。\n2. 未检查节点的内存使用情况和资源分配，以进一步确认是否真的没有空闲内存。\n3. 未验证是否存在其他调度约束（如 `nodeSelector`、`affinity`、`taint`）导致调度失败。\n\n冲突证据：\n无。","collection_summary":"计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%；其中真实环境证据 4/4 项，完整度 100%；实际执行工具 4 个，匹配计划 1 个，未规划证据 3 个","plan_total":1,"plan_collected":1,"plan_completeness":1.0,"environment_evidence_total":4,"environment_evidence_collected":4,"environment_evidence_completeness":1.0,"executed_tool_count":4,"matched_tool_count":1,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1","description":"获取 Pod 'rc-pending-insufficient-memory' 的详细信息以验证其调度失败原因。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-memory -n aiops-e2e","purpose":"验证调度失败的详细原因，如资源不足、taint 不匹配等。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/1 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取 Pod 'rc-pending-insufficient-memory' 的详细信息... | `kubectl describe pod rc-pending-insufficient-memory -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 1.7s)
   📤 → 下游数据: root_cause=Pod 'rc-pending-insufficient-memory' 无法调度的原因是集群中没有足够的内存资源。kubectl_describe 显示 0/3 个节点可用，原因是 3 个节点的内存不足。
   confidence=95%
   causal_chain={"root_cause": "集群中没有足够的内存资源来调度 Pod", "intermediate_causes": ["Pod 'rc-pending-insufficient-memory' 请求的内存超过了集群中所有节点的可用内存", "调度器无法找到可以满足内存需求的节点"], "immediate_causes": ["Pod 'rc-pending-insufficient-memory' 的调度失败事件显示内存不足", "集群中 3 个节点均无法提供足够的内存"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"tool": "kubectl_get_by_kind_in_cluster", "description": "集群中 Pod 状态概览，显示 1 个 Pod 处于 Pending 状态"}, {"tool": "kubectl_describe", "description": "Pod 'rc-pending-insufficient-memory' 详细信息，显示调度失败原因为内存不足"}, {"tool": "kubectl_get_by_name", "description": "Pod 'rc-pending-insufficient-memory' 信息摘要，确认其处于 Pending 状态"}], "evidence_analysis": [{"tool": "kubectl_get_by_kind_in_cluster", "analysis": "显示 1 个 Pod 处于 Pending 状态，表明存在调度问题"}, {"tool": "kubectl_describe", "analysis": "Pod 'rc-pending-insufficient-memory' 的 FailedScheduling 事件显示 0/3 个节点可用，原因是内存不足，表明集群中没有足够的内存资源"}, {"tool": "kubectl_get_by_name", "analysis": "确认 Pod 'rc-pending-insufficient-memory' 处于 Pending 状态，支持其调度失败的诊断"}], "causal_chain": {"root_cause": "集群中没有足够的内存资源来调度 Pod", "intermediate_causes": ["Pod 'rc-pending-insufficient-memory' 请求的内存超过了集群中所有节点的可用内存", "调度器无法找到可以满足内存需求的节点"], "immediate_causes": ["Pod 'rc-pending-insufficient-memory' 的调度失败事件显示内存不足", "集群中 3 个节点均无法提供足够的内存"]}, "root_cause": "Pod 'rc-pending-insufficient-memory' 无法调度的原因是集群中没有足够的内存资源。kubectl_describe 显示 0/3 个节点可用，原因是 3 个节点的内存不足。", "root_cause_summary": "Pod 'rc-pending-insufficient-memory' 无法调度的原因是集群中没有足够的内存资源。kubectl_describe 显示 0/3 个节点可用，原因是 3 个节点的内存不足。", "confidence": 0.95, "confidence_reason": "kubectl_describe 明确显示调度失败原因为内存不足，且集群中 3 个节点均无法满足内存需求。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [], "limitations": "未检查 Pod 的资源请求和节点的内存使用情况，可能无法完全确认是否真的没有空闲内存。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'rc-pending-insufficient-memory' 无法调度的原因是集群中没有足够的内存资源。kubectl_describe 显示 0/3 个节点可用，原因是 3 个节点的内存不足。
   置信度: 95%
   🔗 因果链:
     根本原因: 集群中没有足够的内存资源来调度 Pod


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 13.4s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4009 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 3.9s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
---
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | `Pending` / `PendingUnschedulable` |
| **兼容归因层** | L1 - 调度问题 |
| **问题分类** | 调度失败（Insufficient memory） |
| **置信度** | 高 (95%) |
| **证据完整度** | 1/1 (100%) |

---

## 🔍 现象描述

**用户报告**：  
> 我的集群有什么问题？

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | `rc-pending-insufficient-memory` |
| Namespace | `aiops-e2e` |
| Node | `<none>` |
| 错误信息 | `0/3 nodes are available: 3 Insufficient memory` |

该 Pod 由于调度失败处于 `Pending` 状态，且调度器指出所有 3 个节点内存不足，无法满足该 Pod 的资源请求。调度器事件显示：

> `Warning  FailedScheduling  28m (x8 over 63m)  default-scheduler  0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.`

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod -A` | `STATUS: Pending, REASON: FailedScheduling` | Pod 无法调度 |
| 2 | Pod 详细信息 | `kubectl describe pod` | `0/3 nodes are available: 3 Insufficient memory` | 明确指出内存不足 |
| 3 | 集群 Pod 概览 | `kubectl get pod -A` | `Running: 46, Pending: 1` | 集群中多数 Pod 正常 |
| 4 | 调度器事件 | `kubectl describe pod` | `FailedScheduling: 3 Insufficient memory` | 3 个节点均不满足内存需求 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 `Pending`，且事件指出 `Insufficient memory`，说明调度失败的直接原因是内存不足。
- **证据链**：Pod 请求的资源 > 节点可用资源 → 调度器无法找到匹配节点 → Pod 保持 `Pending` 状态。

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod 的资源请求（memory）超过集群中所有节点的可用内存资源        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 调度器尝试调度 Pod，但所有节点内存不足 → 无法分配 → 保持 Pending │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 0/3 个节点可用，原因是 3 个节点的内存不足（Insufficient memory） │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 保持 Pending 状态，且调度失败事件频繁记录                   │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2 (`kubectl describe pod` 显示 `3 Insufficient memory`) 和证据 #4 (调度器事件确认)，问题的根本原因是 **集群中所有节点的可用内存资源不足以满足该 Pod 的资源请求**，导致调度失败，Pod 保持 `Pending` 状态。

**置信度**：高 (95%)

- ✅ 事件明确指出 `Insufficient memory`
- ✅ 调度器多次尝试调度失败
- ⚠️ 未检查 Pod 的具体资源请求（requests.memory）和节点实际内存分配情况

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 降低 Pod 的内存请求或增加节点资源**
```bash
kubectl edit pod rc-pending-insufficient-memory -n aiops-e2e
```
*操作*：在 `resources.requests.memory` 中降低内存请求值（例如从 2Gi 降低到 1Gi），保存后重新调度。

**2. [可选] 扩容集群节点**
```bash
kubectl scale node <node-name> --replicas=4
```
*前提*：你有节点管理权限，并且可以添加具有足够内存的新节点。

### 后续优化

1. **监控内存分配**：使用 `kubectl describe node <node-name>` 检查节点的 `Allocatable` 和 `Capacity`，确认实际可用资源。
2. **优化资源请求/限制配置**：确保 Pod 的 `requests.memory` 和 `limits.memory` 合理，避免过度请求。
3. **使用 HPA / VPA**：如果应用负载波动大，考虑使用 Vertical Pod Autoscaler (VPA) 动态调整资源。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 检查 Pod 状态 | `kubectl get pod rc-pending-insufficient-memory -n aiops-e2e` | STATUS: Running |
| 2. 查看调度器事件 | `kubectl describe pod rc-pending-insufficient-memory -n aiops-e2e` | 无 `FailedScheduling` 事件 |
| 3. 检查节点资源 | `kubectl describe node <node-name>` | Allocatable 内存足够满足 Pod 请求 |

---

## ⚠️ 注意事项

- 如果你不确定 Pod 的内存请求值，可以使用以下命令查看：
  ```bash
  kubectl get pod rc-pending-insufficient-memory -n aiops-e2e -o jsonpath='{.spec.containers[*].resources}'
  ```
- 如果节点资源不足是系统性问题，考虑增加节点或使用 `Node Affinity` / `Taints` 控制调度策略。
- 如果问题仍然存在，建议检查节点的资源使用情况（如 `kubectl top node`，若已安装 metrics-server）。

---

## 📊 性能统计

├─ 总耗时: 4.1m
├─ 问题定位: 50.2s (21%) ✅
├─ 证据链采集: 58.6s (24%) ✅
├─ 根因分析: 61.7s (25%) ✅
├─ 汇总总结: 73.4s (30%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 5 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 5 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
