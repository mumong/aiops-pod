======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 70fb0472900945eb]

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
56m                 Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 n
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          56m   <none>   <none>   
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
  "layers": ["L1"],
  "layer_name": "PendingUnschedulable",
  "confidence": 0.95,
  "reasoning": "Pod rc-pending-nodeselector 处于 Pending 状态，Events 显示调度失败原因是 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。Pod 的 nodeSelector 设置了一个不存在的标签 aiops.e2e/nonexistent-node-label=true，而集群中的所有节点都没有这个标签，导致调度失败。节点状态正常，无资源不足或 Taint 问题。这是典型的调度约束不匹配问题。",
  "abnormal_pods": ["aiops-e2e/rc-pending-nodeselector"],
  "abnormal_groups": {
    "PendingUnschedulable": {
      "count": 1,
      "members": ["aiops-e2e/rc-pending-nodeselector"]
    }
  },
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "PendingUnschedulable",
  "status_category": "Scheduling",
  "key_entities": {
    "Pod": "aiops-e2e/rc-pending-nodeselector",
    "NodeSelector": "aiops.e2e/nonexistent-node-label=true",
    "Nodes": ["master", "node1", "node2"]
  },
  "possible_scenarios": [
    "Pod 的 nodeSelector 设置了一个不存在的标签 aiops.e2e/nonexistent-node-label=true，导致调度失败",
    "集群中所有节点都没有这个标签，因此调度器找不到合适的节点",
    "需要检查 Pod 的 nodeSelector 是否正确，或者添加对应的标签到节点上"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 0.1s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'Pod 的 nodeSelector 设置了一个不存在的标签 aiops.e2e/nonexistent-node-label=true，导致调度失败', 'probability': 'high', 'reason': "Events 明确指出 3 node(s) didn't match Pod's node affinity/selector，且 nodeSelector 设置了不存在的标签"}, {'scenario': '集群中所有节点都没有这个标签，因此调度器找不到合适的节点', 'probability': 'high', 'reason': '所有节点均无标签 aiops.e2e/nonexistent-node-label=true，导致调度失败'}, {'scenario': '需要检查 Pod 的 nodeSelector 是否正确，或者添加对应的标签到节点上', 'probability': 'high', 'reason': '解决调度失败的关键是修复 nodeSelector 或为节点添加标签'}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "NodeSelector", "name": "aiops.e2e/nonexistent-node-label=true", "namespace": ""}, {"type": "Node", "name": "master", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}]
   reasoning=Pod rc-pending-nodeselector 处于 Pending 状态，Events 显示调度失败原因是 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。Pod 的 nodeSelector 设置了一个不存在的标签 aiops.e2e/nonexistent-node-label=true，而集群中的所有节点都没有这个标签，导致调度失败。节点状态正常，无资源不足或 Taint 问题。这是典型的调度约束不匹配问题。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "Pod rc-pending-nodeselector 处于 Pending 状态，Events 显示调度失败原因是 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。Pod 的 nodeSelector 设置了一个不存在的标签 aiops.e2e/nonexistent-node-label=true，而集群中的所有节点都没有这个标签，导致调度失败。节点状态正常，无资源不足或 Taint 问题。这是典型的调度约束不匹配问题。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "Scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "NodeSelector", "name": "aiops.e2e/nonexistent-node-label=true", "namespace": ""}, {"type": "Node", "name": "master", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}], "possible_scenarios": [{"scenario": "Pod 的 nodeSelector 设置了一个不存在的标签 aiops.e2e/nonexistent-node-label=true，导致调度失败", "probability": "high", "reason": "Events 明确指出 3 node(s) didn't match Pod's node affinity/selector，且 nodeSelector 设置了不存在的标签"}, {"scenario": "集群中所有节点都没有这个标签，因此调度器找不到合适的节点", "probability": "high", "reason": "所有节点均无标签 aiops.e2e/nonexistent-node-label=true，导致调度失败"}, {"scenario": "需要检查 Pod 的 nodeSelector 是否正确，或者添加对应的标签到节点上", "probability": "high", "reason": "解决调度失败的关键是修复 nodeSelector 或为节点添加标签"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                56m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/70fb0472900945eb/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/70fb0472900945eb/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/70fb0472900945eb/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
58m                 Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 n
   💭 [证据链采集] # 证据结论

## 已采集证据
1. **Pod rc-pending-nodeselector 的配置验证**：
   - Pod 的 `nodeSelector` 设置为 `{"aiops.e2e/nonexistent-node-label": "true"}`，这是一个不存在的标签。
   - Pod 的状态为 `Pending`，`phase: Pending`。
   - `conditions` 中 `PodScheduled: status=False`，`reason=Unschedulable`，`message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`。

2. **集群节点标签验证**：
   - 集群中有 3 个节点：`master`、`node1`、`node2`，状态均为 `Ready`。
   - 所有节点的标签中没有 `aiops.e2e/nonexistent-node-label=true`。

3. **Pod 的 FailedScheduling 事件**：
   - 事件显示 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`。
   - Preemption 也无法帮助调度。

## 未采集证据
- 无。

## 冲突证据
- 无。

## 总结
- **问题原因**：Pod `rc-pending-nodeselector` 的 `nodeSelector` 设置了不存在的标签 `aiops.e2e/nonexistent-node-label=true`，导致调度失败。
- **建议解决方案**：需要检查 Pod 的 `nodeSelector` 设置是否正确，或者在集群节点上添加该标签。
   ✅ [证据链采集] 完成 (1m 32.1s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod 的 nodeSelector 是否设置了一个不存在的标签","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"name":"rc-pending-nodeselector","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"检查 Pod 的 nodeSelector 是否包含不存在的标签 aiops.e2e/nonexistent-node-label=true","evidence_type":"configuration","target_scope":"aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e2","description":"验证集群中的节点是否拥有标签 aiops.e2e/nonexistent-node-label=true","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o json","tool_args":{"kind":"Node","output_format":"json"},"purpose":"检查集群中的节点是否拥有标签 aiops.e2e/nonexistent-node-label=true","evidence_type":"node_configuration","target_scope":"cluster/nodes","acceptable_tools":["kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true},{"id":"e3","description":"验证 Pod 的 FailedScheduling 事件","level":"important","tool":"kubectl_events","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"检查 Pod 的 FailedScheduling 事件，确认调度失败的具体原因","evidence_type":"event_log","target_scope":"aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-fsdjk\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/70fb0472900945eb/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/70fb0472900945eb/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/70fb0472900945eb/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/70fb0472900945eb/tools/002-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/70fb0472900945eb/tools/002-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/70fb0472900945eb/tools/002-evidence-kubectl_get_by_kind_in_cluster.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n58m                 Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n13m (x9 over 53m)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/70fb0472900945eb/tools/003-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/70fb0472900945eb/tools/003-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/70fb0472900945eb/tools/003-evidence-kubectl_events.summary.txt"}],"llm_analysis":"# 证据结论\n\n## 已采集证据\n1. **Pod rc-pending-nodeselector 的配置验证**：\n   - Pod 的 `nodeSelector` 设置为 `{\"aiops.e2e/nonexistent-node-label\": \"true\"}`，这是一个不存在的标签。\n   - Pod 的状态为 `Pending`，`phase: Pending`。\n   - `conditions` 中 `PodScheduled: status=False`，`reason=Unschedulable`，`message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`。\n\n2. **集群节点标签验证**：\n   - 集群中有 3 个节点：`master`、`node1`、`node2`，状态均为 `Ready`。\n   - 所有节点的标签中没有 `aiops.e2e/nonexistent-node-label=true`。\n\n3. **Pod 的 FailedScheduling 事件**：\n   - 事件显示 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`。\n   - Preemption 也无法帮助调度。\n\n## 未采集证据\n- 无。\n\n## 冲突证据\n- 无。\n\n## 总结\n- **问题原因**：Pod `rc-pending-nodeselector` 的 `nodeSelector` 设置了不存在的标签 `aiops.e2e/nonexistent-node-label=true`，导致调度失败。\n- **建议解决方案**：需要检查 Pod 的 `nodeSelector` 设置是否正确，或者在集群节点上添加该标签。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 8 个，匹配计划 3 个，未规划证据 5 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":3,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"验证 Pod 的 nodeSelector 是否设置了一个不存在的标签","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"检查 Pod 的 nodeSelector 是否包含不存在的标签 aiops.e2e/nonexistent-node-label=true","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"验证集群中的节点是否拥有标签 aiops.e2e/nonexistent-node-label=true","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o json","purpose":"检查集群中的节点是否拥有标签 aiops.e2e/nonexistent-node-label=true","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"验证 Pod 的 FailedScheduling 事件","level":"important","tool":"kubectl_events","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"检查 Pod 的 FailedScheduling 事件，确认调度失败的具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_yaml | 验证 Pod 的 nodeSelector 是否设置了一个不存在的标签 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e2 | critical | ✅ | kubectl_get_by_kind_in_cl... | 验证集群中的节点是否拥有标签 aiops.e2e/nonexistent-node-lab... | `kubectl get nodes -o json` |
   | e3 | important | ✅ | kubectl_events | 验证 Pod 的 FailedScheduling 事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 4.8s)
   📤 → 下游数据: root_cause=Pod rc-pending-nodeselector 的 nodeSelector 设置了一个不存在的标签 aiops.e2e/nonexistent-node-label=true，导致调度失败。集群中的所有节点都没有这个标签，因此调度器找不到合适的节点。
   confidence=95%
   causal_chain={"root_cause": "Pod 的 nodeSelector 设置了不存在的标签 aiops.e2e/nonexistent-node-label=true", "intermediate_causes": ["调度器找不到匹配的节点", "导致 Pod 一直处于 Pending 状态"], "immediate_effects": ["Pod 无法调度", "FailedScheduling 事件频繁出现"]}
   rca_analysis={"phenomenon": "Pod rc-pending-nodeselector 处于 Pending 状态，调度失败", "evidence_inventory": [{"description": "Pod rc-pending-nodeselector 的配置验证", "value": "nodeSelector 设置了不存在的标签 aiops.e2e/nonexistent-node-label=true，状态为 Pending"}, {"description": "集群节点标签验证", "value": "所有节点的标签中没有 aiops.e2e/nonexistent-node-label=true"}, {"description": "Pod 的 FailedScheduling 事件", "value": "事件显示 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"}], "evidence_analysis": [{"description": "Pod rc-pending-nodeselector 的配置验证", "value": "Pod 的 nodeSelector 设置了不存在的标签，导致调度失败"}, {"description": "集群节点标签验证", "value": "集群中所有节点均无 aiops.e2e/nonexistent-node-label=true 标签"}, {"description": "Pod 的 FailedScheduling 事件", "value": "事件显示调度失败，因为没有节点匹配 nodeSelector"}], "causal_chain": {"root_cause": "Pod 的 nodeSelector 设置了不存在的标签 aiops.e2e/nonexistent-node-label=true", "intermediate_causes": ["调度器找不到匹配的节点", "导致 Pod 一直处于 Pending 状态"], "immediate_effects": ["Pod 无法调度", "FailedScheduling 事件频繁出现"]}, "root_cause": "Pod rc-pending-nodeselector 的 nodeSelector 设置了一个不存在的标签 aiops.e2e/nonexistent-node-label=true，导致调度失败。集群中的所有节点都没有这个标签，因此调度器找不到合适的节点。", "root_cause_summary": "Pod rc-pending-nodeselector 的 nodeSelector 设置了一个不存在的标签 aiops.e2e/nonexistent-node-label=true，导致调度失败。集群中的所有节点都没有这个标签，因此调度器找不到合适的节点。", "confidence": 0.95, "confidence_reason": "有直接证据表明 Pod 的 nodeSelector 设置了不存在的标签，并且集群中的所有节点都没有这个标签，导致调度失败。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [], "limitations": "未发现其他潜在的异常情况，所有节点状态正常，无资源不足或 Taint 问题。", "llm_raw_analysis": "基于证据分析，Pod rc-pending-nodeselector 的 nodeSelector 设置了一个不存在的标签 aiops.e2e/nonexistent-node-label=true，导致调度失败。集群中的所有节点都没有这个标签，因此调度器找不到合适的节点。这是典型的调度约束不匹配问题。建议检查 Pod 的 nodeSelector 设置是否正确，或者在集群节点上添加该标签。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-nodeselector 的 nodeSelector 设置了一个不存在的标签 aiops.e2e/nonexistent-node-label=true，导致调度失败。集群中的所有节点都没有这个标签，因此调度器找不到合适的节点。
   置信度: 95%
   🔗 因果链:
     根本原因: Pod 的 nodeSelector 设置了不存在的标签 aiops.e2e/nonexistent-node-label=true


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 37.4s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3833 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 14.4s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | PendingUnschedulable |
| **兼容归因层** | L1 - 调度问题 |
| **问题分类** | 调度约束不匹配（NodeSelector 不匹配） |
| **置信度** | 高 (95%) |
| **证据完整度** | 3/3 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-pending-nodeselector |
| Namespace | aiops-e2e |
| Node | 无匹配节点 |
| 错误信息 | 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod -n aiops-e2e` | `STATUS: Pending` | Pod 无法调度 |
| 2 | Pod Events | `kubectl events` | `Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 调度失败，原因明确为 nodeSelector 不匹配 |
| 3 | Pod YAML | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` | `nodeSelector: aiops.e2e/nonexistent-node-label=true` | Pod 设置了不存在的 nodeSelector 标签 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 处于 `Pending` 状态，Events 明确指出调度失败原因是 nodeSelector 不匹配。
- **证据 #3 印证**：Pod 的 nodeSelector 设置了 `aiops.e2e/nonexistent-node-label=true`，而所有节点均无此标签。
- **证据链**：Pod 设置了不存在的 nodeSelector → 无节点满足调度条件 → Pod 无法调度 → 持续处于 Pending 状态。

### 缺失证据（无）

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod 的 nodeSelector 设置了一个不存在的标签 aiops.e2e/nonexistent-node-label=true │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 无节点具有该标签 → 调度器无法选择合适节点 → Pod 无法调度        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Pod 无法调度，状态为 PendingUnschedulable                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod rc-pending-nodeselector 处于 Pending 状态                   │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2 (`FailedScheduling` 事件) 和证据 #3 (Pod YAML 中的 `nodeSelector`)，问题的根本原因是 **Pod 设置了不存在的标签 `aiops.e2e/nonexistent-node-label=true`**，导致调度器无法找到合适的节点，从而无法调度 Pod。

**置信度**：高 (95%)
- ✅ `FailedScheduling` 事件明确指出调度失败
- ✅ Pod YAML 明确设置了不存在的标签
- ✅ 所有节点均无此标签，证据链完整

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 修复 Pod 的 nodeSelector**
```bash
kubectl edit pod rc-pending-nodeselector -n aiops-e2e
```
*操作*：删除或修改 `nodeSelector: aiops.e2e/nonexistent-node-label=true` 为合法标签或移除该字段

**2. [可选] 为节点添加缺失标签**
```bash
kubectl label nodes <node-name> aiops.e2e/nonexistent-node-label=true
```
*目的*：如果 nodeSelector 设置是合理的，可为节点添加该标签以满足调度条件

### 后续优化

1. **验证修复**：执行 `kubectl get pod rc-pending-nodeselector -n aiops-e2e`，确认状态变为 `Running`。
2. **标签管理**：确保 nodeSelector 使用的标签在节点上存在，避免未来调度失败。
3. **Pod 配置审查**：定期审查 Pod 的 nodeSelector、affinity、taint 等配置，确保与集群配置一致。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running |
| 2. 检查 Events | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | 无 FailedScheduling 事件 |
| 3. 检查 nodeSelector | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o jsonpath='{.spec.nodeSelector}'` | 不包含 `aiops.e2e/nonexistent-node-label=true` |

---

## ⚠️ 注意事项

- 如果 nodeSelector 是必要的，应为节点添加对应标签，而不是删除 nodeSelector。
- 调度失败问题可能影响整个部署流程，建议在修复后进行全集群调度策略审查。
- 如果集群中有其他 Pod 使用了类似配置，建议一并检查和修复。

---

---

## 📊 性能统计

├─ 总耗时: 5.2m
├─ 问题定位: 60.1s (19%) ✅
├─ 证据链采集: 92.1s (29%) ✅
├─ 根因分析: 64.8s (21%) ✅
├─ 汇总总结: 97.4s (31%) ✅
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
