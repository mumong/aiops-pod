======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: ccc325140a0f4e19]

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
  Warning  FailedScheduling  18m (x15 over 88m)  default-scheduler  0/3 nodes are available:
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
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] {
  "layer": "L1",
  "derived_layer": "L1",
  "layers": [
    "L1"
  ],
  "layer_name": "PendingUnschedulable",
  "confidence": 0.95,
  "reasoning": "Pod rc-pending-nodeselector 处于 Pending 状态，Events 显示 FailedScheduling 原因为 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。Pod 的 nodeSelector 指定了一个不存在的标签 aiops.e2e/nonexistent-node-label=true，而所有节点均未携带该标签，导致无节点可调度。节点状态均正常，无资源不足或不可调度的情况。此问题属于调度约束不匹配，归为 L1 层。",
  "abnormal_pods": [
    {
      "namespace": "aiops-e2e",
      "name": "rc-pending-nodeselector",
      "status": "Pending",
      "key_events": [
        {
          "type": "Warning",
          "reason": "FailedScheduling",
          "message": "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling."
        }
      ],
      "pod_abnormal_type": "PendingUnschedulable"
    }
  ],
  "abnormal_groups": [
    {
      "pod_status_keyword": "Pending",
      "pod_abnormal_type": "PendingUnschedulable",
      "status_category": "scheduling"
    }
  ],
  "key_entities": [
    "Pod: rc-pending-nodeselector (aiops-e2e)",
    "nodeSelector: aiops.e2e/nonexistent-node-label=true",
    "Nodes: master, node1, node2"
  ],
  "possible_scenarios": [
    "Pod 的 nodeSelector 指定了一个不存在的标签，导致无节点可调度。",
    "节点上未配置与 nodeSelector 匹配的标签。",
    "集群中没有节点满足调度条件，且无资源不足问题。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (52.5s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}]
   reasoning=Pod rc-pending-nodeselector 处于 Pending 状态，Events 显示 FailedScheduling 原因为 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。Pod 的 nodeSelector 指定了一个不存在的标签 aiops.e2e/nonexistent-node-label=true，而所有节点均未携带该标签，导致无节点可调度。节点状态均正常，无资源不足或不可调度的情况。此问题属于调度约束不匹配，归为 L1 层。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "Pod rc-pending-nodeselector 处于 Pending 状态，Events 显示 FailedScheduling 原因为 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。Pod 的 nodeSelector 指定了一个不存在的标签 aiops.e2e/nonexistent-node-label=true，而所有节点均未携带该标签，导致无节点可调度。节点状态均正常，无资源不足或不可调度的情况。此问题属于调度约束不匹配，归为 L1 层。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                93m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/ccc325140a0f4e19/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/ccc325140a0f4e19/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/ccc325140a0f4e19/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

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
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [证据链采集] ### 已采集证据
- **critical**: Pod `rc-pending-nodeselector` 的 `nodeSelector` 指定了一个不存在的标签 `aiops.e2e/nonexistent-node-label=true`，导致调度失败。
- **important**: 所有节点均未携带该标签，且状态均为 `Ready`，无资源不足或不可调度的情况。

### 未采集证据
- 无。

### 冲突证据
- 无。
   ✅ [证据链采集] 完成 (59.6s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod rc-pending-nodeselector 的 nodeSelector 是否与集群节点标签匹配","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"检查 Pod 的 nodeSelector 是否指定未在节点上存在的标签","evidence_type":"configuration","target_scope":"Pod rc-pending-nodeselector","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e2","description":"检查集群节点的标签是否满足 Pod rc-pending-nodeselector 的调度需求","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o wide","tool_args":{"kind":"Node"},"purpose":"验证节点标签是否匹配 Pod 的 nodeSelector","evidence_type":"resource_status","target_scope":"All Nodes","acceptable_tools":["kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-fsdjk\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ccc325140a0f4e19/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ccc325140a0f4e19/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ccc325140a0f4e19/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ccc325140a0f4e19/tools/002-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ccc325140a0f4e19/tools/002-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ccc325140a0f4e19/tools/002-evidence-kubectl_get_by_kind_in_cluster.summary.txt"}],"llm_analysis":"### 已采集证据\n- **critical**: Pod `rc-pending-nodeselector` 的 `nodeSelector` 指定了一个不存在的标签 `aiops.e2e/nonexistent-node-label=true`，导致调度失败。\n- **important**: 所有节点均未携带该标签，且状态均为 `Ready`，无资源不足或不可调度的情况。\n\n### 未采集证据\n- 无。\n\n### 冲突证据\n- 无。","collection_summary":"计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%；其中真实环境证据 6/6 项，完整度 100%；实际执行工具 6 个，匹配计划 2 个，未规划证据 4 个","plan_total":2,"plan_collected":2,"plan_completeness":1.0,"environment_evidence_total":6,"environment_evidence_collected":6,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":2,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"验证 Pod rc-pending-nodeselector 的 nodeSelector 是否与集群节点标签匹配","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"检查 Pod 的 nodeSelector 是否指定未在节点上存在的标签","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"检查集群节点的标签是否满足 Pod rc-pending-nodeselector 的调度需求","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o wide","purpose":"验证节点标签是否匹配 Pod 的 nodeSelector","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/2 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_yaml | 验证 Pod rc-pending-nodeselector 的 nodeSelector... | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e2 | important | ✅ | kubectl_get_by_kind_in_cl... | 检查集群节点的标签是否满足 Pod rc-pending-nodeselector 的调度需求 | `kubectl get nodes -o wide` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (24.1s)
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
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (2m 45.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4462 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 1.9s
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
| **问题分类** | PendingUnschedulable |
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
| 1 | Pod 状态 | kubectl get pod -n aiops-e2e | `STATUS: Pending, REASON: FailedScheduling` | Pod 无法调度，处于 Pending 状态 |
| 2 | 事件信息 | kubectl describe pod rc-pending-nodeselector -n aiops-e2e | `Warning  FailedScheduling  18m (x15 over 88m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 明确指出调度失败的原因 |
| 3 | Pod spec 配置 | kubectl get pod rc-pending-nodeselector -o yaml -n aiops-e2e | `nodeSelector: aiops.e2e/nonexistent-node-label: "true"` | Pod 指定了不存在的 nodeSelector |
| 4 | 节点标签 | kubectl get nodes -o jsonpath='{.items[*].metadata.labels}' | `所有节点均未携带 aiops.e2e/nonexistent-node-label=true` | 无节点满足调度条件 |
| 5 | 节点状态 | kubectl get nodes | `所有节点状态为 Ready` | 节点正常，无资源不足或不可调度问题 |
| 6 | 节点标签详细信息 | kubectl get node -o jsonpath='{.items[*].metadata.labels}' | `节点标签为 beta.kubernetes.io/arch=amd64, kubernetes.io/os=linux 等，无 aiops.e2e/nonexistent-node-label` | 无节点满足 nodeSelector 条件 |

### 证据关联分析

- **证据 #2 + #3 印证**：FailedScheduling 原因明确指出 nodeSelector 不匹配，且 Pod 指定了不存在的标签。
- **证据链**：Pod 指定了 `aiops.e2e/nonexistent-node-label=true` → 所有节点均未携带该标签 → 无节点满足调度条件 → Pod 无法调度，处于 Pending 状态。

### 缺失证据（无）

| 证据 | 级别 | 影响 |
|------|------|------|
| - | - | - |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod 指定了不存在的 nodeSelector 标签 aiops.e2e/nonexistent-node-label=true，导致无节点可调度。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 无节点满足 nodeSelector 条件 → 无节点可调度 → Pod 无法被调度     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ default-scheduler 报告 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod rc-pending-nodeselector 处于 Pending 状态，无法调度。         │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2 (FailedScheduling 事件) 和证据 #3 (Pod 指定了不存在的 nodeSelector)，问题的根本原因是**Pod 指定了一个不存在的标签 aiops.e2e/nonexistent-node-label=true**，导致无节点可调度，Pod 一直处于 Pending 状态。

**置信度**：高 (95%)
- ✅ 事件明确指出调度失败的原因
- ✅ Pod spec 明确指定了不存在的 nodeSelector
- ✅ 节点标签信息显示无节点满足该条件

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 修正 Pod 的 nodeSelector**

```bash
kubectl edit pod rc-pending-nodeselector -n aiops-e2e
```

*操作*：在 `spec.nodeSelector` 中删除或修改 `aiops.e2e/nonexistent-node-label: "true"`，或将其替换为集群中实际存在的标签（例如 `kubernetes.io/os=linux`）。

*依据*：当前 nodeSelector 不匹配任何节点，需修正为有效标签。

**2. [可选] 为节点添加标签（如需保留原 nodeSelector）**

```bash
kubectl label nodes <node-name> aiops.e2e/nonexistent-node-label=true
```

*操作*：将该标签添加到一个或多个节点上，使 Pod 可以调度。

*依据*：如果希望保留原 nodeSelector，则需确保有节点满足条件。

### 后续优化

1. **标签管理**：定期审查 Pod 的 nodeSelector 和节点标签，确保调度策略与集群实际标签匹配。
2. **调度策略验证**：在部署 Pod 前，验证 nodeSelector、affinity、taint 等调度策略是否与集群节点匹配。
3. **文档更新**：记录所有 nodeSelector 的含义和使用场景，便于团队统一调度策略。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running |
| 2. 检查调度事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | 无 FailedScheduling 事件 |
| 3. 检查节点标签 | `kubectl get node -o jsonpath='{.items[*].metadata.labels}'` | 至少有一个节点带有新添加的标签（如 aiops.e2e/nonexistent-node-label=true） |

---

## ⚠️ 注意事项

- 如果 nodeSelector 是测试或调试时误加的，建议删除或改为更通用的标签（如 `kubernetes.io/os=linux`）。
- 若集群中存在多个节点，可考虑为多个节点添加标签以提高调度灵活性。
- 确保所有调度策略（nodeSelector、affinity、taint）与集群节点标签一致，避免调度失败。

---

## 📊 性能统计

├─ 总耗时: 5.0m
├─ 问题定位: 52.5s (17%) ✅
├─ 证据链采集: 59.6s (20%) ✅
├─ 根因分析: 24.1s (8%) ✅
├─ 汇总总结: 165.6s (55%) ✅
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
