======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 8a6c90bfd0824152]

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
  Warning  FailedScheduling  36m                default-scheduler  0/3 nodes are available: 
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          36m   <none>   <none>   
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
  "reasoning": "检测到一个Pod处于Pending状态，原因是调度失败。具体错误信息显示0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。这表明Pod的nodeSelector或affinity设置与集群中的节点不匹配，导致无法调度。",
  "abnormal_pods": [
    {
      "name": "rc-pending-nodeselector",
      "namespace": "aiops-e2e",
      "status": "Pending",
      "reason": "FailedScheduling",
      "message": "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.."
    }
  ],
  "abnormal_groups": [
    {
      "type": "PendingUnschedulable",
      "count": 1,
      "pods": [
        "rc-pending-nodeselector"
      ]
    }
  ],
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "PendingUnschedulable",
  "status_category": "scheduling",
  "key_entities": [
    "rc-pending-nodeselector",
    "aiops-e2e",
    "nodeSelector",
    "node affinity/selector"
  ],
  "possible_scenarios": [
    "Pod的nodeSelector或affinity设置与集群中的节点不匹配，导致无法调度。",
    "集群中没有满足Pod调度要求的节点，可能需要检查节点标签或增加节点。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 28.8s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'Pod的nodeSelector或affinity设置与集群中的节点不匹配，导致无法调度。', 'probability': 'high', 'reason': "事件信息显示0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。"}, {'scenario': '集群中没有满足Pod调度要求的节点，可能需要检查节点标签或增加节点。', 'probability': 'medium', 'reason': 'Pod的nodeSelector设置了aiops.e2e/nonexistent-node-label标签，但集群中节点未标记该标签。'}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "nodeSelector", "name": "aiops.e2e/nonexistent-node-label", "namespace": ""}]
   reasoning=检测到一个Pod处于Pending状态，原因是调度失败。具体错误信息显示0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。这表明Pod的nodeSelector或affinity设置与集群中的节点不匹配，导致无法调度。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "检测到一个Pod处于Pending状态，原因是调度失败。具体错误信息显示0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。这表明Pod的nodeSelector或affinity设置与集群中的节点不匹配，导致无法调度。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "nodeSelector", "name": "aiops.e2e/nonexistent-node-label", "namespace": ""}], "possible_scenarios": [{"scenario": "Pod的nodeSelector或affinity设置与集群中的节点不匹配，导致无法调度。", "probability": "high", "reason": "事件信息显示0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。"}, {"scenario": "集群中没有满足Pod调度要求的节点，可能需要检查节点标签或增加节点。", "probability": "medium", "reason": "Pod的nodeSelector设置了aiops.e2e/nonexistent-node-label标签，但集群中节点未标记该标签。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                36m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/8a6c90bfd0824152/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/8a6c90bfd0824152/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/8a6c90bfd0824152/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  38m                default-scheduler  0/3 nodes are available: 
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [证据链采集] - 已采集证据：
  - Pod `rc-pending-nodeselector` 的调度失败事件显示 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`。
  - 集群中所有节点的状态均为 `Ready`，但没有节点的标签匹配 Pod 的 `nodeSelector` `aiops.e2e/nonexistent-node-label`。

- 未采集证据：
  - 无。

- 冲突证据：
  - 无。
   ✅ [证据链采集] 完成 (1m 2.1s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan":[{"id":"verify-pod-scheduler-failure","description":"验证 Pod 的调度失败原因，包括 nodeSelector/affinity 不匹配、资源不足等","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"pod":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"获取 Pod 的详细描述，验证调度失败的具体原因，如 nodeSelector 不匹配或资源不足","evidence_type":"scheduling_failure","target_scope":"aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"verify-node-labels","description":"验证集群中节点的标签，确认是否缺少与 Pod nodeSelector 匹配的标签","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o json","tool_args":{"kind":"nodes"},"purpose":"获取所有节点的标签信息，验证是否存在与 Pod 的 nodeSelector 匹配的标签","evidence_type":"node_label_verification","target_scope":"all_nodes","acceptable_tools":["kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  38m                default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  23m (x3 over 33m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/8a6c90bfd0824152/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/8a6c90bfd0824152/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/8a6c90bfd0824152/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/8a6c90bfd0824152/tools/002-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/8a6c90bfd0824152/tools/002-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/8a6c90bfd0824152/tools/002-evidence-kubectl_get_by_kind_in_cluster.summary.txt"}],"llm_analysis":"- 已采集证据：\n  - Pod `rc-pending-nodeselector` 的调度失败事件显示 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`。\n  - 集群中所有节点的状态均为 `Ready`，但没有节点的标签匹配 Pod 的 `nodeSelector` `aiops.e2e/nonexistent-node-label`。\n\n- 未采集证据：\n  - 无。\n\n- 冲突证据：\n  - 无。","collection_summary":"计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 7 个，匹配计划 2 个，未规划证据 5 个","plan_total":2,"plan_collected":2,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":7,"matched_tool_count":2,"unplanned_tool_count":5,"evidence_inventory":[{"id":"verify-pod-scheduler-failure","description":"验证 Pod 的调度失败原因，包括 nodeSelector/affinity 不匹配、资源不足等","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"获取 Pod 的详细描述，验证调度失败的具体原因，如 nodeSelector 不匹配或资源不足","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"verify-node-labels","description":"验证集群中节点的标签，确认是否缺少与 Pod nodeSelector 匹配的标签","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o json","purpose":"获取所有节点的标签信息，验证是否存在与 Pod 的 nodeSelector 匹配的标签","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/2 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | verify-pod-sc... | critical | ✅ | kubectl_describe | 验证 Pod 的调度失败原因，包括 nodeSelector/affinity 不匹配、资... | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | verify-node-l... | important | ✅ | kubectl_get_by_kind_in_cl... | 验证集群中节点的标签，确认是否缺少与 Pod nodeSelector 匹配的标签 | `kubectl get nodes -o json` |

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (13.7s)
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
   ✅ [汇总总结] 完成 (1m 13.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4413 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 57.9s
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
| **Pod异常状态** | PendingUnschedulable |
| **兼容归因层** | L1 - 调度失败 |
| **问题分类** | 调度失败（NodeSelector/affinity 不匹配） |
| **置信度** | 高 (95%) |
| **证据完整度** | 2/2 (100%) |

---

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-pending-nodeselector |
| Namespace | aiops-e2e |
| 错误信息 | 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector |

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: Pending` | Pod 无法调度 |
| 2 | 调度失败事件 | `kubectl describe pod` | `Warning  FailedScheduling  36m                default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | Pod 的 nodeSelector 与节点标签不匹配 |
| 3 | Pod 的 nodeSelector | `kubectl get pod -o yaml` | `aiops.e2e/nonexistent-node-label` | Pod 要求节点必须包含 `aiops.e2e/nonexistent-node-label` 标签 |
| 4 | 节点标签状态 | `kubectl get node` | `labels: beta.kubernetes.io/arch=amd64, kubernetes.io/hostname=master, node-role.kubernetes.io/control-plane=` | 集群中节点没有 `aiops.e2e/nonexistent-node-label` 标签 |
| 5 | 节点数量 | `kubectl get node` | `3 nodes` | 当前集群只有 3 个节点 |
| 6 | 调度器事件 | `kubectl describe pod` | `preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.` | 调度器尝试预抢占失败 |
| 7 | Pod YAML | `kubectl get pod -o yaml` | `phase: Pending` | Pod 未被调度，状态为 Pending |

### 证据关联分析
- **证据 #2 + #3 印证**：Pod 的 `nodeSelector` 设置为 `aiops.e2e/nonexistent-node-label`，而集群中节点没有该标签 → 无法调度。
- **证据 #4 印证**：集群中节点的标签列表不包含 `aiops.e2e/nonexistent-node-label` → 无法匹配 Pod 要求。
- **证据链**：Pod 设置了不匹配的 nodeSelector → 调度器无法找到符合条件的节点 → Pod 处于 Pending 状态。

---

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod 的 nodeSelector 设置为 aiops.e2e/nonexistent-node-label，但集群中节点未标记该标签。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 调度器无法找到满足 nodeSelector 条件的节点，导致调度失败。         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Pod 被标记为 Pending，Events 显示 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 Pending，且无节点被分配。                             │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2 (调度失败事件) 和证据 #3 (Pod 的 nodeSelector 设置为 `aiops.e2e/nonexistent-node-label`)，问题的根本原因是 **Pod 的 nodeSelector 设置与集群中节点的标签不匹配**，导致调度失败，Pod 一直处于 Pending 状态。
**置信度**：高 (95%)
- ✅ `FailedScheduling` 事件明确指出 0/3 nodes are available
- ✅ Pod 的 nodeSelector 设置为 `aiops.e2e/nonexistent-node-label`
- ✅ 节点标签中未包含该标签
- ⚠️ 无缺失证据

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 为节点添加缺失的标签**
```bash
kubectl label nodes <node-name> aiops.e2e/nonexistent-node-label=true
```
*依据*：Pod 的 nodeSelector 要求节点包含该标签，添加后 Pod 将可调度

**2. [可选] 修改 Pod 的 nodeSelector**
```bash
kubectl set node-selector deployment/<deployment-name> -n aiops-e2e aiops.e2e/nonexistent-node-label=true
```
*目的*：如果节点无法添加标签，修改 Pod 的 nodeSelector 以匹配现有节点

### 后续优化
1. **标签管理**：确保 Pod 的 nodeSelector 与集群中节点的标签保持一致。
2. **调度器日志**：启用 `--v=5` 日志级别查看调度器详细日志（`kubectl logs -n kube-system <kube-scheduler-pod>`）。
3. **监控告警**：配置 Pod 调度失败的监控告警。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 被调度 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running |
| 2. 确认节点已打标签 | `kubectl get node <node-name> --show-labels` | 包含 `aiops.e2e/nonexistent-node-label=true` |
| 3. 检查调度事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | 无 `FailedScheduling` 事件 |

---

## ⚠️ 注意事项
- 如果多个节点需要添加标签，可批量执行 `kubectl label nodes <node1> <node2> aiops.e2e/nonexistent-node-label=true`
- 如果 Pod 是由 Deployment 或 Job 创建的，修改 nodeSelector 后，旧 Pod 会自动重启并应用新标签
- 请确认标签名称和值与 Pod 的 nodeSelector 设置一致

---

---

## 📊 性能统计

├─ 总耗时: 4.0m
├─ 问题定位: 88.8s (37%) ✅
├─ 证据链采集: 62.1s (26%) ✅
├─ 根因分析: 13.7s (6%) ✅
├─ 汇总总结: 73.3s (31%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 8 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 8 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
