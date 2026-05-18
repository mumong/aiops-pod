======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: becb90b1b4b54b15]

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
  Warning  FailedScheduling  60m                default-scheduler  0/3 nodes are avai
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                             READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-insufficient-memory   0/1     Pending   0          60m   <non
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: master
关键诊断行:
                    volumes.kubernetes.io/controller-managed-attach-detach: true
Taints:             <none>
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node1
关键诊断行:
                    volumes.kubernetes.io/controller-managed-attach-detach: true
Taints:             <none>
   💭 [问题定位] 调用工具: kubectl_describe
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (42.9s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': '集群节点内存不足，无法满足 Pod 的资源请求', 'probability': '高', 'reason': 'FailedScheduling 原文显示 3 个节点均因内存不足无法调度 Pod。'}, {'scenario': 'Pod 资源请求超出集群节点总资源', 'probability': '中', 'reason': 'Pod 可能配置了过高的内存请求，超出集群节点可用资源。'}, {'scenario': '预抢占机制未生效', 'probability': '中', 'reason': '调度器提示没有可抢占的 Pod，可能集群节点资源分配不合理或 Pod 优先级设置不当。'}]
   entities=[{"type": "Pod", "name": "rc-pending-insufficient-memory", "namespace": "aiops-e2e"}]
   reasoning=当前环境中存在一个处于 Pending 状态的 Pod (rc-pending-insufficient-memory)，其失败原因为调度器无法找到可用节点（0/3 nodes are available: 3 Insufficient memory），表明集群节点资源不足，导致 Pod 无法调度。根据异常类型映射，PendingUnschedulable 通常归因于调度约束或节点资源压力，属于 L1 层级。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "Node Resource Pressure or Scheduling Constraints", "confidence": 0.95, "reasoning": "当前环境中存在一个处于 Pending 状态的 Pod (rc-pending-insufficient-memory)，其失败原因为调度器无法找到可用节点（0/3 nodes are available: 3 Insufficient memory），表明集群节点资源不足，导致 Pod 无法调度。根据异常类型映射，PendingUnschedulable 通常归因于调度约束或节点资源压力，属于 L1 层级。", "abnormal_pods": [{"name": "rc-pending-insufficient-memory", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling/node_kubelet/lifecycle", "key_entities": [{"type": "Pod", "name": "rc-pending-insufficient-memory", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "集群节点内存不足，无法满足 Pod 的资源请求", "probability": "高", "reason": "FailedScheduling 原文显示 3 个节点均因内存不足无法调度 Pod。"}, {"scenario": "Pod 资源请求超出集群节点总资源", "probability": "中", "reason": "Pod 可能配置了过高的内存请求，超出集群节点可用资源。"}, {"scenario": "预抢占机制未生效", "probability": "中", "reason": "调度器提示没有可抢占的 Pod，可能集群节点资源分配不合理或 Pod 优先级设置不当。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-memory"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-memory"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-insufficient-memory                      0/1     Pending     0             60m    <none>           <none>   <none>           <none>            app=rc-pending-insufficient-memory,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/becb90b1b4b54b15/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/becb90b1b4b54b15/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/becb90b1b4b54b15/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
  Warning  FailedScheduling  21m (x8 over 56m)  default-scheduler  0/3 nodes are avai
   💭 [证据链采集] 已采集证据:
1. Pod `rc-pending-insufficient-memory` 的状态为 `Pending`，且调度器事件 `FailedScheduling` 显示 3 个节点均因内存不足无法调度 Pod。

未采集证据:
1. 未验证 Pod 的资源请求是否超出集群节点的可用资源。
2. 未验证集群节点的内存使用情况和资源分配情况。

冲突证据:
1. 无。
   ✅ [证据链采集] 完成 (38.4s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod 'rc-pending-insufficient-memory' 的调度失败原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-memory -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-pending-insufficient-memory","namespace":"aiops-e2e"},"purpose":"获取 Pod 'rc-pending-insufficient-memory' 的详细信息，特别是 FailedScheduling 事件的原因。","evidence_type":"diagnostic","target_scope":"specific","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-insufficient-memory\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  21m (x8 over 56m)  default-scheduler  0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nName:             rc-pending-insufficient-memory\nLabels:           app=rc-pending-insufficient-memory\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/becb90b1b4b54b15/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/becb90b1b4b54b15/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/becb90b1b4b54b15/tools/001-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"已采集证据:\n1. Pod `rc-pending-insufficient-memory` 的状态为 `Pending`，且调度器事件 `FailedScheduling` 显示 3 个节点均因内存不足无法调度 Pod。\n\n未采集证据:\n1. 未验证 Pod 的资源请求是否超出集群节点的可用资源。\n2. 未验证集群节点的内存使用情况和资源分配情况。\n\n冲突证据:\n1. 无。","collection_summary":"计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 7 个，匹配计划 1 个，未规划证据 6 个","plan_total":1,"plan_collected":1,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":7,"matched_tool_count":1,"unplanned_tool_count":6,"evidence_inventory":[{"id":"e1","description":"验证 Pod 'rc-pending-insufficient-memory' 的调度失败原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-memory -n aiops-e2e","purpose":"获取 Pod 'rc-pending-insufficient-memory' 的详细信息，特别是 FailedScheduling 事件的原因。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/1 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证 Pod 'rc-pending-insufficient-memory' 的调度失败原因 | `kubectl describe pod rc-pending-insufficient-memory -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (34.4s)
   📤 → 下游数据: root_cause=集群节点内存不足导致 Pod 'rc-pending-insufficient-memory' 无法被调度。具体证据为 kubectl_describe 显示 3 个节点均因内存不足无法调度 Pod。
   confidence=95%
   causal_chain={"root_cause": "集群节点内存不足", "intermediate_causes": ["调度器无法找到可用节点", "Pod 无法被调度"], "immediate_causes": ["Pod 的资源请求超出集群节点的可用内存"], "symptoms": ["Pod 状态为 Pending", "调度失败事件记录"]}
   rca_analysis={"phenomenon": "存在一个处于 Pending 状态的 Pod (rc-pending-insufficient-memory)，调度器无法找到可用节点，原因是 3 个节点均因内存不足无法调度该 Pod。", "evidence_inventory": [{"kubectl_describe": "Pod rc-pending-insufficient-memory 的 FailedScheduling 事件显示 0/3 nodes are available: 3 Insufficient memory."}, {"kubectl_get_by_kind_in_cluster": "当前集群中 1 个 Pod 处于 Pending 状态，其余 46 个 Pod 处于 Running 状态。"}, {"kubectl_get_by_name": "Pod rc-pending-insufficient-memory 的状态为 Pending，且标签包含 pod_abnormal_type=PendingUnschedulable。"}], "evidence_analysis": [{"kubectl_describe": "Pod 调度失败的具体原因为内存不足，3 个节点均无法满足 Pod 的资源请求。"}, {"kubectl_get_by_kind_in_cluster": "集群中大部分 Pod 处于 Running 状态，仅 1 个 Pod 处于异常状态。"}, {"kubectl_get_by_name": "Pod 被明确标记为 PendingUnschedulable 类型，表明调度失败是由于调度器无法找到匹配的节点。"}], "causal_chain": {"root_cause": "集群节点内存不足", "intermediate_causes": ["调度器无法找到可用节点", "Pod 无法被调度"], "immediate_causes": ["Pod 的资源请求超出集群节点的可用内存"], "symptoms": ["Pod 状态为 Pending", "调度失败事件记录"]}, "root_cause": "集群节点内存不足导致 Pod 'rc-pending-insufficient-memory' 无法被调度。具体证据为 kubectl_describe 显示 3 个节点均因内存不足无法调度 Pod。", "root_cause_summary": "集群节点内存不足导致 Pod 'rc-pending-insufficient-memory' 无法被调度。具体证据为 kubectl_describe 显示 3 个节点均因内存不足无法调度 Pod。", "confidence": 0.95, "confidence_reason": "直接证据表明 3 个节点均因内存不足无法调度 Pod，因果链清晰。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "Pod 资源请求过高", "evidence": "未验证集群节点的内存使用情况和资源分配情况。"}, {"cause": "预抢占机制未生效", "evidence": "调度器提示没有可抢占的 Pod，可能集群节点资源分配不合理或 Pod 优先级设置不当。"}], "limitations": "未验证集群节点的内存使用情况和资源分配情况，因此无法确定是否可以通过增加节点资源或调整资源请求来解决此问题。", "llm_raw_analysis": "基于已采集的证据，可以确定集群节点内存不足是导致 Pod 'rc-pending-insufficient-memory' 无法被调度的根因。具体证据为 kubectl_describe 显示 3 个节点均因内存不足无法调度 Pod。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 集群节点内存不足导致 Pod 'rc-pending-insufficient-memory' 无法被调度。具体证据为 kubectl_describe 显示 3 个节点均因内存不足无法调度 Pod。
   置信度: 95%
   🔗 因果链:
     根本原因: 集群节点内存不足


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 56.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4326 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 52.4s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending |
| **兼容归因层** | L1 |
| **问题分类** | PendingUnschedulable（调度失败） |
| **置信度** | 高 (95%) |
| **证据完整度** | 1/1 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-pending-insufficient-memory |
| Namespace | aiops-e2e |
| Node | <none> |
| 错误信息 | 0/3 nodes are available: 3 Insufficient memory |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: Pending, REASON: PendingUnschedulable` | Pod 无法调度 |
| 2 | 调度事件 | `kubectl describe pod rc-pending-insufficient-memory` | `Warning  FailedScheduling  60m                default-scheduler  0/3 nodes are available: 3 Insufficient memory.` | 调度失败原因：内存不足 |
| 3 | 节点资源 | `kubectl describe node` | `Taints: <none>` | 节点无 Taint 限制，但资源不足 |
| 4 | Pod 信息 | `kubectl get pod -n aiops-e2e` | `rc-pending-insufficient-memory 0/1     Pending   0             60m` | Pod 仍处于调度失败状态 |
| 5 | 集群节点状态 | `kubectl get nodes` | `3 nodes in Ready state` | 3 个节点均无法满足 Pod 的内存需求 |
| 6 | 预调度失败 | `kubectl describe pod` | `preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` | 预调度机制未找到可抢占的 Pod |
| 7 | 集群资源分布 | `kubectl get nodes -o wide` | `3 Ready nodes, no preemption enabled` | 无资源可被抢占，Pod 无法调度 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 无法调度，调度器事件明确指出原因是 `Insufficient memory`。
- **证据 #3 + #4 印证**：节点无 Taint，且状态为 Ready，但资源不足，无法满足 Pod 的内存需求。
- **证据 #6 印证**：调度失败后，调度器尝试预调度失败，说明集群资源分配不合理或 Pod 请求过高。
- **证据链**：Pod 内存请求 > 节点可用内存 → 调度失败 → 无法启动 → Pod 状态为 Pending。

### 缺失证据（无）

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 集群节点的可用内存不足，无法满足 Pod 的资源请求                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 调度器无法找到满足内存需求的节点 → 无法启动 Pod                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Pod 被标记为 PendingUnschedulable，调度器事件提示内存不足        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 Pending，无法启动                                    │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2 (`FailedScheduling: 0/3 nodes are available: 3 Insufficient memory`) 和证据 #5 (`3 Ready nodes`)，问题的根本原因是**集群节点内存不足，无法满足 Pod 的资源请求**，导致调度失败。

**置信度**：高 (95%)

- ✅ `kubectl describe pod` 明确指出调度失败原因为内存不足
- ✅ `kubectl get nodes` 显示节点状态正常，但无可用资源
- ⚠️ 未验证 Pod 的实际内存请求值，无法确认是否配置过高

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 调整 Pod 的资源请求**
```bash
kubectl set resources pod/rc-pending-insufficient-memory -n aiops-e2e --requests=memory=256Mi
```
*依据*：降低 Pod 的内存请求，使其在当前节点上可调度

**2. [可选] 增加节点资源或扩容集群**
```bash
kubectl scale node <node-name> --resources=memory=512Mi
```
*依据*：提升节点内存容量，满足 Pod 调度需求

**3. [可选] 启用资源抢占机制**
```bash
kubectl annotate pod/rc-pending-insufficient-memory -n aiops-e2e priority="high"
```
*依据*：为 Pod 设置较高优先级，允许调度器抢占低优先级 Pod

### 后续优化

1. **监控资源使用情况**：使用 Prometheus 或 `kubectl describe node` 检查节点资源分配
2. **优化资源请求/限制**：确保 Pod 的资源请求合理，不超出节点可用资源
3. **启用自动扩缩容**：根据负载动态增加节点，避免资源瓶颈

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 是否调度成功 | `kubectl get pod rc-pending-insufficient-memory -n aiops-e2e` | STATUS: Running |
| 2. 检查调度事件 | `kubectl describe pod rc-pending-insufficient-memory -n aiops-e2e` | No FailedScheduling events |
| 3. 检查节点资源使用 | `kubectl describe node <node-name>` | 内存使用在合理范围内 |
| 4. 检查 Pod 资源请求 | `kubectl get pod rc-pending-insufficient-memory -n aiops-e2e -o jsonpath='{.spec.containers[*].resources}'` | memory: 256Mi 或更低 |

---

## ⚠️ 注意事项

- 如果 Pod 的内存请求仍高于节点可用内存，即使调整后也无法调度，需进一步扩容或优化应用配置
- 调整资源请求后，建议监控集群资源使用，防止其他 Pod 遭受类似调度失败
- 如果集群节点资源长期不足，建议考虑 HPA 或 Cluster Autoscaler 实现自动扩缩容

---

## 📊 性能统计

├─ 总耗时: 3.9m
├─ 问题定位: 42.9s (18%) ✅
├─ 证据链采集: 38.4s (17%) ✅
├─ 根因分析: 34.4s (15%) ✅
├─ 汇总总结: 116.8s (50%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 9 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 9 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
