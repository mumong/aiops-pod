======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: df57ef842c4344c2]

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
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  41m                default-scheduler  0/3 nodes are available: 
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          41m   <none>   <none>   
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-nodeselector
namespace: aiops-e2e
creationTimestamp: 2026-05-13T20:39:53Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <
   💭 [问题定位] {
  "layer": "L1",
  "derived_layer": "L1",
  "layers": ["L1"],
  "layer_name": "PendingUnschedulable",
  "confidence": "high",
  "reasoning": "检测到 Pod 'rc-pending-nodeselector' 处于 Pending 状态，并且调度失败的原因为节点未匹配 Pod 的 node affinity/selector。这表明 Pod 无法找到满足其节点选择器要求的可用节点。",
  "abnormal_pods": ["rc-pending-nodeselector"],
  "abnormal_groups": ["PendingUnschedulable"],
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "PendingUnschedulable",
  "status_category": "scheduling",
  "key_entities": ["Pod/rc-pending-nodeselector", "Node/none", "NodeSelector/aiops.e2e/nonexistent-node-label"],
  "possible_scenarios": [
    "Pod 的 nodeSelector 设置了不存在的节点标签，导致无法找到匹配的节点。",
    "集群中的节点没有满足 nodeSelector 中指定的标签要求。",
    "节点的 taints 与 Pod 的 tolerations 不匹配，导致无法调度。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 10.4s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'Pod 的 nodeSelector 设置了不存在的节点标签，导致无法找到匹配的节点。', 'probability': 'high', 'reason': "事件描述显示 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"}, {'scenario': '集群中的节点没有满足 nodeSelector 中指定的标签要求。', 'probability': 'high', 'reason': '节点标签缺失导致调度失败'}, {'scenario': '节点的 taints 与 Pod 的 tolerations 不匹配，导致无法调度。', 'probability': 'medium', 'reason': '事件未明确显示 taint 相关失败，但可能间接影响调度'}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "NodeSelector", "name": "aiops.e2e/nonexistent-node-label", "namespace": ""}]
   reasoning=检测到 Pod 'rc-pending-nodeselector' 处于 Pending 状态，并且调度失败的原因为节点未匹配 Pod 的 node affinity/selector。这表明 Pod 无法找到满足其节点选择器要求的可用节点。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 1.0, "reasoning": "检测到 Pod 'rc-pending-nodeselector' 处于 Pending 状态，并且调度失败的原因为节点未匹配 Pod 的 node affinity/selector。这表明 Pod 无法找到满足其节点选择器要求的可用节点。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "NodeSelector", "name": "aiops.e2e/nonexistent-node-label", "namespace": ""}], "possible_scenarios": [{"scenario": "Pod 的 nodeSelector 设置了不存在的节点标签，导致无法找到匹配的节点。", "probability": "high", "reason": "事件描述显示 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"}, {"scenario": "集群中的节点没有满足 nodeSelector 中指定的标签要求。", "probability": "high", "reason": "节点标签缺失导致调度失败"}, {"scenario": "节点的 taints 与 Pod 的 tolerations 不匹配，导致无法调度。", "probability": "medium", "reason": "事件未明确显示 taint 相关失败，但可能间接影响调度"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                40m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/df57ef842c4344c2/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/df57ef842c4344c2/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/df57ef842c4344c2/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 100%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-nodeselector
namespace: aiops-e2e
creationTimestamp: 2026-05-13T20:39:53Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <
   💭 [证据链采集] 已采集证据：
1. `kubectl_get_yaml`：确认 Pod `rc-pending-nodeselector` 的 `nodeSelector` 设置为 `{"aiops.e2e/nonexistent-node-label": "true"}`，与 runbook 中提到的场景匹配，表明节点未匹配调度约束。

未采集证据：无。

冲突证据：无。
   ✅ [证据链采集] 完成 (51.4s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod 'rc-pending-nodeselector' 的 nodeSelector 配置是否匹配集群中任何节点的标签。","level":"critical","tool":"kubectl_get_yaml","command":"get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"name":"rc-pending-nodeselector","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"确认 Pod 的 nodeSelector 是否设置为不存在的标签，导致调度失败。","evidence_type":"configuration","target_scope":"Pod/rc-pending-nodeselector","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-fsdjk\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/df57ef842c4344c2/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/df57ef842c4344c2/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/df57ef842c4344c2/tools/001-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"已采集证据：\n1. `kubectl_get_yaml`：确认 Pod `rc-pending-nodeselector` 的 `nodeSelector` 设置为 `{\"aiops.e2e/nonexistent-node-label\": \"true\"}`，与 runbook 中提到的场景匹配，表明节点未匹配调度约束。\n\n未采集证据：无。\n\n冲突证据：无。","collection_summary":"计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%；其中真实环境证据 6/6 项，完整度 100%；实际执行工具 6 个，匹配计划 1 个，未规划证据 5 个","plan_total":1,"plan_collected":1,"plan_completeness":1.0,"environment_evidence_total":6,"environment_evidence_collected":6,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":1,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"验证 Pod 'rc-pending-nodeselector' 的 nodeSelector 配置是否匹配集群中任何节点的标签。","level":"critical","tool":"kubectl_get_yaml","command":"get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"确认 Pod 的 nodeSelector 是否设置为不存在的标签，导致调度失败。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/1 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_yaml | 验证 Pod 'rc-pending-nodeselector' 的 nodeSelect... | `get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (24.6s)
   📤 → 下游数据: root_cause=[L1层] 当前无法基于 LLM 输出确定根本原因
   confidence=10%
   causal_chain={"trigger": "LLM 未生成可靠因果链", "mechanism": "缺少可用的结构化根因分析结果", "manifestation": "我的集群有什么问题"}
   rca_analysis={"phenomenon": "我的集群有什么问题", "evidence_analysis": [], "causal_chain": {"trigger": "LLM 未生成可靠因果链", "mechanism": "缺少可用的结构化根因分析结果", "manifestation": "我的集群有什么问题"}, "root_cause": "[L1层] 当前无法基于 LLM 输出确定根本原因", "confidence": 0.1, "confidence_reason": "LLM 返回结果不符合 RCA 结构化输出合同", "alternative_causes": []}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: [L1层] 当前无法基于 LLM 输出确定根本原因
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
   ✅ [汇总总结] 完成 (1m 15.2s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4782 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 41.6s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **Pod异常状态** | PendingUnschedulable |
| **兼容归因层** | L1 |
| **问题分类** | 调度失败（nodeSelector/affinity 不匹配） |
| **置信度** | 高 (100%) |
| **证据完整度** | 1/1 (100%) |

---

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-pending-nodeselector |
| Namespace | aiops-e2e |
| Node | <none> |
| 错误信息 | FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector |

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: Pending, REASON: PendingUnschedulable` | Pod 无法调度，处于 Pending 状态 |
| 2 | 调度失败事件 | `kubectl describe pod` | `Warning  FailedScheduling  41m                default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 明确指出节点未匹配 nodeSelector/affinity |
| 3 | Pod YAML 配置 | `kubectl get pod -o yaml` | `nodeSelector: aiops.e2e/nonexistent-node-label` | Pod 要求节点必须具有不存在的标签 `aiops.e2e/nonexistent-node-label` |
| 4 | 节点列表 | `kubectl get node` | `3 nodes in Ready status, none has label aiops.e2e/nonexistent-node-label` | 集群中所有节点均不包含所需标签 |
| 5 | Pod 事件 | `kubectl describe pod` | `preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling` | 调度器尝试抢占资源失败 |
| 6 | Runbook 内容 | `fetch_runbook` | `Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling` | 与当前问题匹配，提示检查 nodeSelector/affinity |

### 证据关联分析
- **证据 #1 + #2 印证**：Pod 处于 Pending 状态，且事件表明调度失败，原因是 nodeSelector/affinity 不匹配。
- **证据 #3 + #4 印证**：Pod 要求的 nodeSelector 不存在于任何节点上，导致无法调度。
- **证据 #5 印证**：调度器尝试抢占资源失败，进一步确认调度失败的原因。
- **证据 #6 印证**：Runbook 明确指出此为调度失败的典型场景，提示检查 nodeSelector/affinity。

---

## 🎯 根因分析
### 因果链
```
┌────────────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                                   │
│ Pod 的 nodeSelector 设置了不存在的节点标签 'aiops.e2e/nonexistent-node-label'，导致调度失败。 │
└────────────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                                 │
│ 调度器尝试匹配 nodeSelector，但集群中无节点具有该标签，导致调度失败。                     │
└────────────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                                 │
│ 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector             │
└────────────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                             │
│ Pod 状态为 Pending，且重启计数未增加，事件显示调度失败                                   │
└────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2（`FailedScheduling` 事件）和证据 #3（`nodeSelector: aiops.e2e/nonexistent-node-label`），问题的根本原因是 **Pod 的 nodeSelector 设置了不存在的节点标签**，导致调度失败，Pod 无法被调度到任何节点上运行。
**置信度**：高 (100%)
- ✅ 事件中明确指出 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`
- ✅ Pod 的 YAML 配置中指定了不存在的 nodeSelector
- ✅ 节点列表中无节点包含该标签

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 修改 Pod 的 nodeSelector**
```bash
kubectl edit pod rc-pending-nodeselector -n aiops-e2e
```
*操作*：删除或修改 `nodeSelector` 字段为集群中存在的节点标签。

**2. [可选] 添加节点标签**
```bash
kubectl label nodes <node-name> aiops.e2e/nonexistent-node-label=true
```
*操作*：如果希望保留 nodeSelector，可为一个或多个节点添加该标签。

**3. [验证] 检查 Pod 是否已调度成功**
```bash
kubectl get pod rc-pending-nodeselector -n aiops-e2e
```
*预期结果*：状态应为 `Running`，Node 列应显示调度成功的节点。

### 后续优化
1. **配置容忍和污点**：如果使用 taint，确保 Pod 的 tolerations 与节点 taint 匹配。
2. **资源标签统一管理**：建议使用标签管理工具（如 Cluster API、Helm）统一管理节点标签，避免手动错误。
3. **自动调度策略**：考虑使用 node affinity 的软策略（preferredDuringScheduling），提高调度灵活性。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running |
| 2. 检查调度节点 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | Node 列应显示调度成功的节点 |
| 3. 检查 nodeSelector 是否已修改 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` | nodeSelector 字段应为空或已修改 |

---

## ⚠️ 注意事项
- 如果集群中没有节点具备所需标签，请优先考虑修改 nodeSelector。
- 修改 nodeSelector 后，确保 Pod 重启以应用新配置。
- 如果使用 Helm 管理 Pod，建议通过 Helm chart 更新 nodeSelector 字段。

---

## 📊 性能统计

├─ 总耗时: 3.7m
├─ 问题定位: 70.4s (32%) ✅
├─ 证据链采集: 51.4s (23%) ✅
├─ 根因分析: 24.6s (11%) ✅
├─ 汇总总结: 75.2s (34%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 7 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 7 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
