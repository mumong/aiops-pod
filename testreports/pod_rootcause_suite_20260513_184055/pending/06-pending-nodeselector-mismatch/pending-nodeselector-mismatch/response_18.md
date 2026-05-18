======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 6b42d90d8b43445f]

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
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
44m                 Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 n
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          44m   <none>   <none>   
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
  "layers": [
    "L1"
  ],
  "layer_name": "PendingUnschedulable",
  "confidence": 0.95,
  "reasoning": "Pod rc-pending-nodeselector 处于 Pending 状态，调度失败原因为 nodeSelector 不匹配。Pod 指定了不存在的节点标签 aiops.e2e/nonexistent-node-label，而所有节点均未满足此条件。节点状态均正常 (Ready)，但无节点匹配 nodeSelector。此问题属于调度约束不匹配，归类为 L1 层问题。",
  "abnormal_pods": [
    {
      "name": "rc-pending-nodeselector",
      "namespace": "aiops-e2e",
      "status": "Pending",
      "abnormal_type": "PendingUnschedulable"
    }
  ],
  "abnormal_groups": {
    "PendingUnschedulable": [
      "rc-pending-nodeselector"
    ]
  },
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "PendingUnschedulable",
  "status_category": "Unschedulable",
  "key_entities": [
    "rc-pending-nodeselector",
    "aiops.e2e/nonexistent-node-label",
    "nodeSelector"
  ],
  "possible_scenarios": [
    "Pod 指定了不存在的节点标签 aiops.e2e/nonexistent-node-label，导致无节点可调度",
    "集群中所有节点均不满足 nodeSelector 条件，需要检查节点标签或调整 nodeSelector"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 16.6s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'Pod 指定了不存在的节点标签 aiops.e2e/nonexistent-node-label，导致无节点可调度', 'probability': 'high', 'reason': "Events 明确显示 3 nodes didn't match nodeSelector"}, {'scenario': '集群中所有节点均不满足 nodeSelector 条件，需要检查节点标签或调整 nodeSelector', 'probability': 'high', 'reason': '节点状态正常但无节点匹配 Pod 的 nodeSelector'}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "NodeSelector", "name": "aiops.e2e/nonexistent-node-label", "namespace": ""}]
   reasoning=Pod rc-pending-nodeselector 处于 Pending 状态，调度失败原因为 nodeSelector 不匹配。Pod 指定了不存在的节点标签 aiops.e2e/nonexistent-node-label，而所有节点均未满足此条件。节点状态均正常 (Ready)，但无节点匹配 nodeSelector。此问题属于调度约束不匹配，归类为 L1 层问题。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "Pod rc-pending-nodeselector 处于 Pending 状态，调度失败原因为 nodeSelector 不匹配。Pod 指定了不存在的节点标签 aiops.e2e/nonexistent-node-label，而所有节点均未满足此条件。节点状态均正常 (Ready)，但无节点匹配 nodeSelector。此问题属于调度约束不匹配，归类为 L1 层问题。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "Unschedulable", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "NodeSelector", "name": "aiops.e2e/nonexistent-node-label", "namespace": ""}], "possible_scenarios": [{"scenario": "Pod 指定了不存在的节点标签 aiops.e2e/nonexistent-node-label，导致无节点可调度", "probability": "high", "reason": "Events 明确显示 3 nodes didn't match nodeSelector"}, {"scenario": "集群中所有节点均不满足 nodeSelector 条件，需要检查节点标签或调整 nodeSelector", "probability": "high", "reason": "节点状态正常但无节点匹配 Pod 的 nodeSelector"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                44m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/6b42d90d8b43445f/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/6b42d90d8b43445f/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/6b42d90d8b43445f/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
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
  Warning  FailedScheduling  47m                default-scheduler  0/3 nodes are available: 
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (1m 47.7s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod rc-pending-nodeselector 的详细信息以验证调度失败原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-pending-nodeselector","kind":"Pod"},"purpose":"验证 Pod 的调度失败原因，检查 nodeSelector 是否匹配节点标签","evidence_type":"Pod 详细信息","target_scope":"aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"获取所有节点的详细信息以验证它们的标签是否匹配 nodeSelector","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o json","tool_args":{"kind":"Node"},"purpose":"验证节点的标签是否匹配 Pod rc-pending-nodeselector 的 nodeSelector 条件","evidence_type":"节点标签信息","target_scope":"集群范围","acceptable_tools":["kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true},{"id":"e3","description":"获取 Pod rc-pending-nodeselector 的事件以验证调度失败的具体原因","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-pending-nodeselector","tool_args":{"namespace":"aiops-e2e","name":"rc-pending-nodeselector","kind":"Pod"},"purpose":"验证 Pod rc-pending-nodeselector 的事件，检查是否有 FailedScheduling 事件","evidence_type":"Pod 事件","target_scope":"aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  47m                default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  32m (x3 over 42m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6b42d90d8b43445f/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6b42d90d8b43445f/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6b42d90d8b43445f/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6b42d90d8b43445f/tools/002-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6b42d90d8b43445f/tools/002-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6b42d90d8b43445f/tools/002-evidence-kubectl_get_by_kind_in_cluster.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 7 个，匹配计划 3 个，未规划证据 4 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":7,"matched_tool_count":3,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"获取 Pod rc-pending-nodeselector 的详细信息以验证调度失败原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"验证 Pod 的调度失败原因，检查 nodeSelector 是否匹配节点标签","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取所有节点的详细信息以验证它们的标签是否匹配 nodeSelector","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o json","purpose":"验证节点的标签是否匹配 Pod rc-pending-nodeselector 的 nodeSelector 条件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取 Pod rc-pending-nodeselector 的事件以验证调度失败的具体原因","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-pending-nodeselector","purpose":"验证 Pod rc-pending-nodeselector 的事件，检查是否有 FailedScheduling 事件","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取 Pod rc-pending-nodeselector 的详细信息以验证调度失败原因 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_by_kind_in_cl... | 获取所有节点的详细信息以验证它们的标签是否匹配 nodeSelector | `kubectl get nodes -o json` |
   | e3 | critical | ✅ | kubectl_events | 获取 Pod rc-pending-nodeselector 的事件以验证调度失败的具体原因 | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-pendi...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (21.7s)
   📤 → 下游数据: root_cause=Pod rc-pending-nodeselector 处于 Pending 状态，调度失败原因为 nodeSelector 不匹配。Pod 指定了不存在的节点标签 aiops.e2e/nonexistent-node-label，而所有节点均未满足此条件。
   confidence=95%
   causal_chain={"root_cause": "Pod 指定了不存在的节点标签 aiops.e2e/nonexistent-node-label", "conduction": "导致调度器无法找到匹配的节点", "direct_cause": "Pod 无法被调度到任何节点", "phenomenon": "Pod rc-pending-nodeselector 处于 Pending 状态"}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [{"e1": "Pod rc-pending-nodeselector 处于 Pending 状态，Events 显示调度失败原因为 nodeSelector 不匹配。", "e2": "所有节点状态正常 (Ready)，但无节点满足 Pod 的 nodeSelector 条件。", "e3": "Pod 指定了不存在的节点标签 aiops.e2e/nonexistent-node-label，导致无节点可调度。"}], "causal_chain": {"root_cause": "Pod 指定了不存在的节点标签 aiops.e2e/nonexistent-node-label", "conduction": "导致调度器无法找到匹配的节点", "direct_cause": "Pod 无法被调度到任何节点", "phenomenon": "Pod rc-pending-nodeselector 处于 Pending 状态"}, "root_cause": "Pod rc-pending-nodeselector 处于 Pending 状态，调度失败原因为 nodeSelector 不匹配。Pod 指定了不存在的节点标签 aiops.e2e/nonexistent-node-label，而所有节点均未满足此条件。", "root_cause_summary": "Pod rc-pending-nodeselector 处于 Pending 状态，调度失败原因为 nodeSelector 不匹配。Pod 指定了不存在的节点标签 aiops.e2e/nonexistent-node-label，而所有节点均未满足此条件。", "confidence": 0.95, "confidence_reason": "", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [], "limitations": "未发现其他异常", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-nodeselector 处于 Pending 状态，调度失败原因为 nodeSelector 不匹配。Pod 指定了不存在的节点标签 aiops.e2e/nonexistent-node-label，而所有节点均未满足此条件。
   置信度: 95%
   🔗 因果链:
     根本原因: Pod 指定了不存在的节点标签 aiops.e2e/nonexistent-node-label


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 5.9s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3627 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 31.9s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pod rc-pending-nodeselector 处于 Pending 状态，调度失败 |
| **兼容归因层** | L1 - 调度问题 |
| **问题分类** | PodPendingUnschedulable |
| **置信度** | 高 (95%) |
| **证据完整度** | 3/3 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题？

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
| 1 | Pod 状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | `STATUS: Pending` | Pod 无法调度 |
| 2 | Pod 事件 | `kubectl events` | `Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 明确指出 nodeSelector 不匹配 |
| 3 | Pod 配置 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` | `nodeSelector: aiops.e2e/nonexistent-node-label` | Pod 指定了不存在的节点标签 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 Pending，事件显示调度失败原因是 nodeSelector 不匹配。
- **证据 #3 印证**：Pod 的 nodeSelector 指定了不存在的标签 `aiops.e2e/nonexistent-node-label`，而所有节点均未打上此标签。

### 缺失证据

| 证据 | 级别 | 影响 |
|------|------|------|
| 无缺失证据 | - | - |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod 指定了不存在的节点标签 aiops.e2e/nonexistent-node-label     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ nodeSelector 不匹配 → 无节点满足调度条件 → Pod 无法被调度        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Pod 事件显示：0/3 nodes are available: 3 node(s) didn't match nodeSelector |
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod rc-pending-nodeselector 一直处于 Pending 状态                │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Pod 状态为 Pending)、证据 #2 (FailedScheduling 事件) 和证据 #3 (Pod 的 nodeSelector 配置)，问题的根本原因是 **Pod 指定了不存在的节点标签 aiops.e2e/nonexistent-node-label，导致无节点满足调度条件**。

**置信度**：高 (95%)
- ✅ Pod 状态为 Pending
- ✅ 事件明确指出 nodeSelector 不匹配
- ✅ Pod 的 nodeSelector 指定了不存在的标签

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 移除或修改 nodeSelector**
```bash
kubectl edit pod rc-pending-nodeselector -n aiops-e2e
```
*操作*：删除或修改 `nodeSelector: aiops.e2e/nonexistent-node-label` 为已存在的标签。

**2. [可选] 添加缺失的节点标签**
```bash
kubectl label nodes <node-name> aiops.e2e/nonexistent-node-label=true
```
*目的*：为一个或多个节点添加缺失的标签，使 Pod 可以调度。

### 后续优化

1. **标签管理规范**：确保所有调度约束使用的标签都已存在于集群节点上。
2. **Pod 调度策略优化**：考虑使用 `nodeAffinity` 代替 `nodeSelector` 以获得更灵活的调度策略。
3. **事件监控**：启用对 `FailedScheduling` 事件的监控和告警，及时发现调度失败问题。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running |
| 2. 确认调度事件 | `kubectl events -n aiops-e2e` | 无 `FailedScheduling` 事件 |
| 3. 检查节点标签 | `kubectl get nodes --show-labels` | 节点上有 `aiops.e2e/nonexistent-node-label`（如果选择添加） |

---

## ⚠️ 注意事项

- 如果修改 nodeSelector 后问题仍未解决，建议使用 `kubectl describe pod` 查看更详细的调度失败原因。
- 若标签被频繁误用或不存在，建议制定节点标签规范，避免调度失败。

---

## 📊 性能统计

├─ 总耗时: 4.5m
├─ 问题定位: 76.6s (28%) ✅
├─ 证据链采集: 107.7s (40%) ✅
├─ 根因分析: 21.7s (8%) ✅
├─ 汇总总结: 65.9s (24%) ✅
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
