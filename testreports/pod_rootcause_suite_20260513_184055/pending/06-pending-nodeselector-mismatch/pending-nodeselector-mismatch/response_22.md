======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: a5b99f7d3d5c4456]

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
53m                   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          53m   <none>   <none>   
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
  "confidence": 0.9,
  "reasoning": "Pod 'rc-pending-nodeselector' 处于 Pending 状态，且事件显示 'FailedScheduling'，原因为 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。进一步检查该 Pod 的 YAML 配置，发现其 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，但集群中的节点并没有这个标签。这表明 Pod 的调度约束不匹配，导致无法调度。因此，该异常归类为 L1 层次的 PendingUnschedulable。",
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
    "PendingUnschedulable"
  ],
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "PendingUnschedulable",
  "status_category": "Scheduling",
  "key_entities": [
    "rc-pending-nodeselector",
    "aiops-e2e/nonexistent-node-label"
  ],
  "possible_scenarios": [
    "Pod 的 nodeSelector 设置了不存在的节点标签，导致无法调度。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 40.1s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'Pod 的 nodeSelector 设置了不存在的节点标签，导致无法调度。', 'probability': 'high', 'reason': '事件信息明确指出调度失败原因为节点标签不匹配，且 Pod 的 YAML 确认了 nodeSelector 设置了不存在的标签。'}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Label", "name": "aiops.e2e/nonexistent-node-label", "namespace": ""}]
   reasoning=Pod 'rc-pending-nodeselector' 处于 Pending 状态，且事件显示 'FailedScheduling'，原因为 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。进一步检查该 Pod 的 YAML 配置，发现其 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，但集群中的节点并没有这个标签。这表明 Pod 的调度约束不匹配，导致无法调度。因此，该异常归类为 L1 层次的 PendingUnschedulable。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.9, "reasoning": "Pod 'rc-pending-nodeselector' 处于 Pending 状态，且事件显示 'FailedScheduling'，原因为 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。进一步检查该 Pod 的 YAML 配置，发现其 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，但集群中的节点并没有这个标签。这表明 Pod 的调度约束不匹配，导致无法调度。因此，该异常归类为 L1 层次的 PendingUnschedulable。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Label", "name": "aiops.e2e/nonexistent-node-label", "namespace": ""}], "possible_scenarios": [{"scenario": "Pod 的 nodeSelector 设置了不存在的节点标签，导致无法调度。", "probability": "high", "reason": "事件信息明确指出调度失败原因为节点标签不匹配，且 Pod 的 YAML 确认了 nodeSelector 设置了不存在的标签。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                53m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/a5b99f7d3d5c4456/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/a5b99f7d3d5c4456/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/a5b99f7d3d5c4456/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 90%

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
   💭 [证据链采集] 已采集证据：
1. Pod `rc-pending-nodeselector` 的 `nodeSelector` 设置了 `aiops.e2e/nonexistent-node-label=true`。
2. 集群中的所有节点（master、node1、node2）均未设置标签 `aiops.e2e/nonexistent-node-label`。
3. Pod 的调度状态为 `Pending`，且事件显示调度失败的原因是节点标签不匹配。

结论：
- Pod 无法调度的原因是其 `nodeSelector` 设置了不存在的节点标签 `aiops.e2e/nonexistent-node-label=true`。
- 集群中没有节点具备该标签，因此调度器无法找到合适的节点来运行该 Pod。
   ✅ [证据链采集] 完成 (1m 1.3s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod 'rc-pending-nodeselector' 的 YAML 配置，以确认其 nodeSelector 设置了不存在的标签","level":"critical","tool":"kubectl_get_yaml","command":"get pods rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{},"purpose":"确认 Pod 的 nodeSelector 设置了不存在的标签","evidence_type":"configuration","target_scope":"aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e2","description":"检查集群中节点的标签，以确认是否存在 'aiops.e2e/nonexistent-node-label=true'","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"get nodes --show-labels","tool_args":{},"purpose":"确认节点是否具有 Pod 所需的标签","evidence_type":"node_configuration","target_scope":"cluster/nodes","acceptable_tools":["kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-fsdjk\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a5b99f7d3d5c4456/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a5b99f7d3d5c4456/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a5b99f7d3d5c4456/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a5b99f7d3d5c4456/tools/002-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a5b99f7d3d5c4456/tools/002-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a5b99f7d3d5c4456/tools/002-evidence-kubectl_get_by_kind_in_cluster.summary.txt"}],"llm_analysis":"已采集证据：\n1. Pod `rc-pending-nodeselector` 的 `nodeSelector` 设置了 `aiops.e2e/nonexistent-node-label=true`。\n2. 集群中的所有节点（master、node1、node2）均未设置标签 `aiops.e2e/nonexistent-node-label`。\n3. Pod 的调度状态为 `Pending`，且事件显示调度失败的原因是节点标签不匹配。\n\n结论：\n- Pod 无法调度的原因是其 `nodeSelector` 设置了不存在的节点标签 `aiops.e2e/nonexistent-node-label=true`。\n- 集群中没有节点具备该标签，因此调度器无法找到合适的节点来运行该 Pod。","collection_summary":"计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 7 个，匹配计划 2 个，未规划证据 5 个","plan_total":2,"plan_collected":2,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":7,"matched_tool_count":2,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"验证 Pod 'rc-pending-nodeselector' 的 YAML 配置，以确认其 nodeSelector 设置了不存在的标签","level":"critical","tool":"kubectl_get_yaml","command":"get pods rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"确认 Pod 的 nodeSelector 设置了不存在的标签","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"检查集群中节点的标签，以确认是否存在 'aiops.e2e/nonexistent-node-label=true'","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"get nodes --show-labels","purpose":"确认节点是否具有 Pod 所需的标签","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/2 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_yaml | 验证 Pod 'rc-pending-nodeselector' 的 YAML 配置，以确... | `get pods rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e2 | critical | ✅ | kubectl_get_by_kind_in_cl... | 检查集群中节点的标签，以确认是否存在 'aiops.e2e/nonexistent-nod... | `get nodes --show-labels` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (29.3s)
   📤 → 下游数据: root_cause=Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的节点标签 'aiops.e2e/nonexistent-node-label=true'，导致调度失败。事件信息显示 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'，表明集群中没有节点满足该标签要求。
   confidence=90%
   causal_chain={"root_cause": "Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的节点标签 'aiops.e2e/nonexistent-node-label=true'，导致无法找到匹配的节点进行调度。", "intermediate_causes": ["nodeSelector 设置的标签 'aiops.e2e/nonexistent-node-label=true' 不存在于集群中的任何节点。", "调度器无法找到满足 nodeSelector 条件的节点，导致 Pod 无法调度。"], "immediate_causes": ["Pod 'rc-pending-nodeselector' 的调度失败事件 'FailedScheduling' 明确指出节点标签不匹配。", "Pod 的状态为 'Pending'，且事件信息显示调度失败。"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [{"e1": "kubectl_get_yaml 关键字段摘要: nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，表明 Pod 的调度约束要求节点有该标签。", "e2": "kubectl_get_by_kind_in_cluster 表格摘要: 集群中所有节点均未设置 'aiops.e2e/nonexistent-node-label=true' 标签，导致节点无法满足调度条件。", "layer_2": "kubectl_events 摘要: 事件信息显示 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'，明确指出调度失败的原因。"}], "causal_chain": {"root_cause": "Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的节点标签 'aiops.e2e/nonexistent-node-label=true'，导致无法找到匹配的节点进行调度。", "intermediate_causes": ["nodeSelector 设置的标签 'aiops.e2e/nonexistent-node-label=true' 不存在于集群中的任何节点。", "调度器无法找到满足 nodeSelector 条件的节点，导致 Pod 无法调度。"], "immediate_causes": ["Pod 'rc-pending-nodeselector' 的调度失败事件 'FailedScheduling' 明确指出节点标签不匹配。", "Pod 的状态为 'Pending'，且事件信息显示调度失败。"]}, "root_cause": "Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的节点标签 'aiops.e2e/nonexistent-node-label=true'，导致调度失败。事件信息显示 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'，表明集群中没有节点满足该标签要求。", "root_cause_summary": "Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的节点标签 'aiops.e2e/nonexistent-node-label=true'，导致调度失败。事件信息显示 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'，表明集群中没有节点满足该标签要求。", "confidence": 0.9, "confidence_reason": "", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [], "limitations": "未验证其他可能的调度约束（如 affinity、taint）是否也导致了调度失败。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的节点标签 'aiops.e2e/nonexistent-node-label=true'，导致调度失败。事件信息显示 '0/3 nodes are available: 3 node(s) did...
   置信度: 90%
   🔗 因果链:
     根本原因: Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的节点标签 'aiops.e2e/nonexistent-node-label=true'，导致无法找到匹配的节点进行调度。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 14.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4124 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 25.5s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending |
| **兼容归因层** | L1 |
| **问题分类** | PendingUnschedulable |
| **置信度** | 高 (90%) |
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
| Node | <none> |
| 错误信息 | 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: Pending, REASON: FailedScheduling` | Pod 无法调度 |
| 2 | Pod 事件 | `kubectl events` | `Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 明确指出标签不匹配 |
| 3 | Pod YAML 配置 | `kubectl get pod -o yaml` | `nodeSelector: aiops.e2e/nonexistent-node-label: "true"` | Pod 设置了不存在的标签 |
| 4 | Node 标签 | `kubectl get nodes` | 未发现标签 `aiops.e2e/nonexistent-node-label=true` | 集群中无匹配节点 |
| 5 | Runbook 匹配 | `fetch_runbook` | `# Pod PendingUnschedulable / 调度失败` | 与调度失败场景匹配 |
| 6 | 集群节点状态 | `kubectl get nodes` | `STATUS: Ready`，共 3 个节点 | 所有节点可用但不匹配 |
| 7 | Pod 创建时间 | `kubectl get pod` | `AGE: 53m` | Pod 已尝试调度 53 分钟 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 `Pending`，且事件显示 `FailedScheduling`，表明调度失败。
- **证据 #3 + #4 印证**：Pod 中设置了 `nodeSelector: aiops.e2e/nonexistent-node-label=true`，但集群中无节点有此标签，导致调度失败。
- **证据链完整**：调度失败 → 标签不匹配 → Pod 无法找到可用节点 → 持续 Pending。

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod 'rc-pending-nodeselector' 设置了不存在的标签 'aiops.e2e/nonexistent-node-label=true'，导致调度失败。│
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Kubernetes 调度器尝试将 Pod 调度到匹配的节点，但找不到任何节点满足 nodeSelector 条件。│
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 调度器无法找到匹配 nodeSelector 的节点，Pod 一直处于 Pending 状态。│
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 Pending，且事件显示调度失败。                        │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2 (`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`) 和证据 #3 (`nodeSelector: aiops.e2e/nonexistent-node-label=true`)，问题的根本原因是 **Pod 设置了不存在的标签 `aiops.e2e/nonexistent-node-label=true`，导致调度失败**。

**置信度**：高 (90%)  
- ✅ `kubectl events` 明确指出调度失败原因  
- ✅ `kubectl get pod -o yaml` 显示了无效的 nodeSelector  
- ⚠️ 未验证其他调度策略（如 affinity、taint）是否也导致失败，但当前证据已足够说明问题

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 移除或更正 nodeSelector**
```bash
kubectl edit pod rc-pending-nodeselector -n aiops-e2e
```
*操作*：在 `spec.nodeSelector` 中删除或修改 `aiops.e2e/nonexistent-node-label=true`，保存后 Kubernetes 将重新尝试调度。

**2. [可选] 添加缺失的标签到节点（若确实需要该标签）**
```bash
kubectl label nodes <node-name> aiops.e2e/nonexistent-node-label=true
```
*操作*：将 `<node-name>` 替换为一个或多个节点名称，添加标签后 Pod 将可调度。

### 后续优化

1. **标签管理规范**：建立标签命名规范，避免使用不存在的标签导致调度失败。
2. **自动化验证**：在部署前验证 nodeSelector 是否匹配集群节点标签。
3. **监控调度事件**：配置 Kubernetes 事件监控，及时发现调度失败。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running |
| 2. 检查调度事件 | `kubectl events -n aiops-e2e` | 无 `FailedScheduling` 事件 |
| 3. 检查 nodeSelector | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o jsonpath='{.spec.nodeSelector}'` | 不包含 `aiops.e2e/nonexistent-node-label` |

---

## ⚠️ 注意事项

- 如果需要保留 `aiops.e2e/nonexistent-node-label` 标签，请确保至少一个节点已添加该标签。
- 请避免使用未在集群中定义的标签，这将导致调度失败。
- 如果集群中有多个调度策略（如 affinity、taint），建议逐一排查。

---

---

## 📊 性能统计

├─ 总耗时: 4.4m
├─ 问题定位: 100.1s (38%) ✅
├─ 证据链采集: 61.3s (23%) ✅
├─ 根因分析: 29.3s (11%) ✅
├─ 汇总总结: 74.8s (28%) ✅
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
