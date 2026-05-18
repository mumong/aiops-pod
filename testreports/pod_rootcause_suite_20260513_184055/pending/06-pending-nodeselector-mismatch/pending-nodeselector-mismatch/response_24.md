======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 4ca37e72a2744f7c]

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
58m                 Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 n
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          58m   <none>   <none>   
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
  "layer_name": "Pod 调度失败",
  "confidence": 0.95,
  "reasoning": "当前 Pod 'rc-pending-nodeselector' 处于 Pending 状态，Events 显示 'FailedScheduling'，且原因明确指向 'node(s) didn't match Pod's node affinity/selector'。进一步检查发现，该 Pod 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，而所有节点均未定义该标签，导致无节点满足调度要求。集群中的所有节点均处于 Ready 状态，且无资源不足或 taint 相关问题。因此，异常归因于调度约束不匹配。",
  "abnormal_pods": [
    {
      "name": "rc-pending-nodeselector",
      "namespace": "aiops-e2e",
      "status": "Pending",
      "reason": "Unschedulable",
      "message": "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.."
    }
  ],
  "abnormal_groups": [
    {
      "pod_status_keyword": "Pending",
      "pod_abnormal_type": "PendingUnschedulable",
      "status_category": "调度失败"
    }
  ],
  "key_entities": [
    {
      "type": "Pod",
      "name": "rc-pending-nodeselector",
      "namespace": "aiops-e2e",
      "status": "Pending"
    },
    {
      "type": "Node",
      "name": "master",
      "status": "Ready"
    },
    {
      "type": "Node",
      "name": "node1",
      "status": "Ready"
    },
    {
      "type": "Node",
      "name": "node2",
      "status": "Ready"
    }
  ],
  "possible_scenarios": [
    "Pod 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，但集群中所有节点均未定义该标签，导致调度失败。",
    "集群中所有节点均处于 Ready 状态，无资源不足或 taint 问题，但 Pod 的调度约束不匹配导致无法调度。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 53.4s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': "Pod 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，但集群中所有节点均未定义该标签，导致调度失败。", 'probability': '高', 'reason': "Events 明确指出 node(s) didn't match Pod's node affinity/selector。"}, {'scenario': '集群中所有节点均处于 Ready 状态，无资源不足或 taint 问题，但 Pod 的调度约束不匹配导致无法调度。', 'probability': '高', 'reason': 'Pod 无法调度的原因与节点状态无关，而是调度约束不匹配。'}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Node", "name": "master", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}]
   reasoning=当前 Pod 'rc-pending-nodeselector' 处于 Pending 状态，Events 显示 'FailedScheduling'，且原因明确指向 'node(s) didn't match Pod's node affinity/selector'。进一步检查发现，该 Pod 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，而所有节点均未定义该标签，导致无节点满足调度要求。集群中的所有节点均处于 Ready 状态，且无资源不足或 taint 相关问题。因此，异常归因于调度约束不匹配。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "Pod 调度失败", "confidence": 0.95, "reasoning": "当前 Pod 'rc-pending-nodeselector' 处于 Pending 状态，Events 显示 'FailedScheduling'，且原因明确指向 'node(s) didn't match Pod's node affinity/selector'。进一步检查发现，该 Pod 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，而所有节点均未定义该标签，导致无节点满足调度要求。集群中的所有节点均处于 Ready 状态，且无资源不足或 taint 相关问题。因此，异常归因于调度约束不匹配。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "调度失败", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Node", "name": "master", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}], "possible_scenarios": [{"scenario": "Pod 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，但集群中所有节点均未定义该标签，导致调度失败。", "probability": "高", "reason": "Events 明确指出 node(s) didn't match Pod's node affinity/selector。"}, {"scenario": "集群中所有节点均处于 Ready 状态，无资源不足或 taint 问题，但 Pod 的调度约束不匹配导致无法调度。", "probability": "高", "reason": "Pod 无法调度的原因与节点状态无关，而是调度约束不匹配。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                57m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/4ca37e72a2744f7c/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/4ca37e72a2744f7c/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/4ca37e72a2744f7c/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
15m (x9 over 55m)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 n
   💭 [证据链采集] 已采集证据：
1. `kubectl_get_yaml`：确认 Pod `rc-pending-nodeselector` 设置了 `nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}`，这是导致调度失败的关键配置。
2. `kubectl_get_by_kind_in_cluster`：确认所有节点均未定义 `aiops.e2e/nonexistent-node-label=true` 标签，导致无节点匹配调度约束。
3. `kubectl_events`：确认调度失败事件包含 `node(s) didn't match Pod's node affinity/selector`，明确指出调度约束不匹配。

冲突证据：
- 无。

未采集证据：
- 无。

结论：当前 Pod 无法调度的根因是其 `nodeSelector` 设置了不存在的标签 `aiops.e2e/nonexistent-node-label=true`，而集群中所有节点均未定义该标签。建议移除或更正 `nodeSelector` 配置以匹配可用节点的标签。
   ✅ [证据链采集] 完成 (1m 34.7s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod 'rc-pending-nodeselector' 的 nodeSelector 与集群节点标签是否匹配","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"pod":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"确认 Pod 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，导致调度失败","evidence_type":"configuration","target_scope":"Pod/rc-pending-nodeselector","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e2","description":"检查集群中所有节点的标签，确认是否缺少 'aiops.e2e/nonexistent-node-label=true'","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o json","tool_args":{"kind":"Node","scope":"cluster"},"purpose":"确认集群中所有节点均未定义 'aiops.e2e/nonexistent-node-label=true' 标签","evidence_type":"configuration","target_scope":"Nodes","acceptable_tools":["kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true},{"id":"e3","description":"检查 Pod 'rc-pending-nodeselector' 的调度事件，确认调度失败原因","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-pending-nodeselector","tool_args":{"kind":"Pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"确认调度失败事件包含 'node(s) didn't match Pod's node affinity/selector' 原因","evidence_type":"event","target_scope":"Pod/rc-pending-nodeselector","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-fsdjk\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4ca37e72a2744f7c/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4ca37e72a2744f7c/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4ca37e72a2744f7c/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4ca37e72a2744f7c/tools/002-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4ca37e72a2744f7c/tools/002-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4ca37e72a2744f7c/tools/002-evidence-kubectl_get_by_kind_in_cluster.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n15m (x9 over 55m)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4ca37e72a2744f7c/tools/003-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4ca37e72a2744f7c/tools/003-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4ca37e72a2744f7c/tools/003-evidence-kubectl_events.summary.txt"}],"llm_analysis":"已采集证据：\n1. `kubectl_get_yaml`：确认 Pod `rc-pending-nodeselector` 设置了 `nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}`，这是导致调度失败的关键配置。\n2. `kubectl_get_by_kind_in_cluster`：确认所有节点均未定义 `aiops.e2e/nonexistent-node-label=true` 标签，导致无节点匹配调度约束。\n3. `kubectl_events`：确认调度失败事件包含 `node(s) didn't match Pod's node affinity/selector`，明确指出调度约束不匹配。\n\n冲突证据：\n- 无。\n\n未采集证据：\n- 无。\n\n结论：当前 Pod 无法调度的根因是其 `nodeSelector` 设置了不存在的标签 `aiops.e2e/nonexistent-node-label=true`，而集群中所有节点均未定义该标签。建议移除或更正 `nodeSelector` 配置以匹配可用节点的标签。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 8 个，匹配计划 3 个，未规划证据 5 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":3,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"验证 Pod 'rc-pending-nodeselector' 的 nodeSelector 与集群节点标签是否匹配","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"确认 Pod 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，导致调度失败","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"检查集群中所有节点的标签，确认是否缺少 'aiops.e2e/nonexistent-node-label=true'","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o json","purpose":"确认集群中所有节点均未定义 'aiops.e2e/nonexistent-node-label=true' 标签","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"检查 Pod 'rc-pending-nodeselector' 的调度事件，确认调度失败原因","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-pending-nodeselector","purpose":"确认调度失败事件包含 'node(s) didn't match Pod's node affinity/selector' 原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_yaml | 验证 Pod 'rc-pending-nodeselector' 的 nodeSelect... | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e2 | critical | ✅ | kubectl_get_by_kind_in_cl... | 检查集群中所有节点的标签，确认是否缺少 'aiops.e2e/nonexistent-no... | `kubectl get nodes -o json` |
   | e3 | important | ✅ | kubectl_events | 检查 Pod 'rc-pending-nodeselector' 的调度事件，确认调度失败原因 | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-pendi...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 38.5s)
   📤 → 下游数据: root_cause=当前 Pod 'rc-pending-nodeselector' 处于 Pending 状态，Events 显示 'FailedScheduling'，且原因明确指向 'node(s) didn't match Pod's node affinity/selector'。进一步检查发现，该 Pod 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，而所有节点均未定义该标签，导致无节点满足调度要求。集群中的所有节点均处于 Ready 状态，且无资源不足或 taint 相关问题。因此，异常归因于调度约束不匹配。
   confidence=95%
   causal_chain={"root_cause": "Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，而集群中所有节点均未定义该标签，导致调度失败。", "intermediate_causes": ["Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'。", "集群中所有节点均未定义 'aiops.e2e/nonexistent-node-label=true' 标签。", "调度失败事件显示 'node(s) didn't match Pod's node affinity/selector'。"], "direct_causes": ["Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'。"], "phenomenon": "Pod 'rc-pending-nodeselector' 处于 Pending 状态，Events 显示 'FailedScheduling'，且原因明确指向 'node(s) didn't match Pod's node affinity/selector'。"}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"id": "e1", "description": "验证 Pod 'rc-pending-nodeselector' 的 nodeSelector 与集群节点标签是否匹配", "level": "critical", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSe"}, {"id": "e2", "description": "检查集群中所有节点的标签，确认是否缺少 'aiops.e2e/nonexistent-node-label=true'", "level": "critical", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubern"}, {"id": "e3", "description": "检查 Pod 'rc-pending-nodeselector' 的调度事件，确认调度失败原因", "level": "important", "value": "kubectl_events 摘要:\n关键诊断行:\n15m (x9 over 55m)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.."}], "evidence_analysis": [{"id": "e1", "description": "Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，这是导致调度失败的关键配置。", "level": "critical", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSe"}, {"id": "e2", "description": "集群中所有节点均未定义 'aiops.e2e/nonexistent-node-label=true' 标签，导致无节点匹配调度约束。", "level": "critical", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubern"}, {"id": "e3", "description": "调度失败事件显示 'node(s) didn't match Pod's node affinity/selector'，明确指出调度约束不匹配。", "level": "important", "value": "kubectl_events 摘要:\n关键诊断行:\n15m (x9 over 55m)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.."}], "causal_chain": {"root_cause": "Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，而集群中所有节点均未定义该标签，导致调度失败。", "intermediate_causes": ["Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'。", "集群中所有节点均未定义 'aiops.e2e/nonexistent-node-label=true' 标签。", "调度失败事件显示 'node(s) didn't match Pod's node affinity/selector'。"], "direct_causes": ["Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'。"], "phenomenon": "Pod 'rc-pending-nodeselector' 处于 Pending 状态，Events 显示 'FailedScheduling'，且原因明确指向 'node(s) didn't match Pod's node affinity/selector'。"}, "root_cause": "当前 Pod 'rc-pending-nodeselector' 处于 Pending 状态，Events 显示 'FailedScheduling'，且原因明确指向 'node(s) didn't match Pod's node affinity/selector'。进一步检查发现，该 Pod 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，而所有节点均未定义该标签，导致无节点满足调度要求。集群中的所有节点均处于 Ready 状态，且无资源不足或 taint 相关问题。因此，异常归因于调度约束不匹配。", "root_cause_summary": "当前 Pod 'rc-pending-nodeselector' 处于 Pending 状态，Events 显示 'FailedScheduling'，且原因明确指向 'node(s) didn't match Pod's node affinity/selector'。进一步检查发现，该 Pod 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，而所有节点均未定义该标签，导致无节点满足调度要求。集群中的所有节点均处于 Ready 状态，且无资源不足或 taint 相关问题。因此，异常归因于调度约束不匹配。", "confidence": 0.95, "confidence_reason": "", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [], "limitations": "", "llm_raw_analysis": "已采集证据：\n1. `kubectl_get_yaml`：确认 Pod `rc-pending-nodeselector` 设置了 `nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}`，这是导致调度失败的关键配置。\n2. `kubectl_get_by_kind_in_cluster`：确认所有节点均未定义 `aiops.e2e/nonexistent-node-label=true` 标签，导致无节点匹配调度约束。\n3. `kubectl_events`：确认调度失败事件包含 `node(s) didn't match Pod's node affinity/selector`，明确指出调度约束不匹配。\n\n冲突证据：\n- 无。\n\n未采集证据：\n- 无。\n\n结论：当前 Pod 无法调度的根因是其 `nodeSelector` 设置了不存在的标签 `aiops.e2e/nonexistent-node-label=true`，而集群中所有节点均未定义该标签。建议移除或更正 `nodeSelector` 配置以匹配可用节点\n... 截断，原始 504 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 当前 Pod 'rc-pending-nodeselector' 处于 Pending 状态，Events 显示 'FailedScheduling'，且原因明确指向 'node(s) didn't match Pod's node affinity/selector'。进一步检查发现，该 Pod ...
   置信度: 95%
   🔗 因果链:
     根本原因: Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，而集群中所有节点均未定义该标签，导致调度失败。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 59.6s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3790 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 7m 6.3s
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
| **兼容归因层** | L1 - 问题定位 |
| **问题分类** | 调度失败 |
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
| Node | <none> |
| 错误信息 | node(s) didn't match Pod's node affinity/selector |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: Pending, REASON: FailedScheduling` | Pod 无法调度 |
| 2 | Pod 事件 | `kubectl events` | `Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 明确调度约束不匹配 |
| 3 | Pod spec | `kubectl get pod -o yaml` | `nodeSelector: aiops.e2e/nonexistent-node-label=true` | Pod 依赖一个不存在的节点标签 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 `Pending`，且事件显示 `node(s) didn't match Pod's node affinity/selector`，说明调度失败与节点标签不匹配有关。
- **证据 #3 印证**：Pod 明确设置了 `nodeSelector: aiops.e2e/nonexistent-node-label=true`，但集群中所有节点均未定义该标签（证据 #4）。
- **证据链**：Pod 设置了调度约束 → 集群中无节点满足该标签 → 调度失败 → Pod 保持 Pending 状态。

### 缺失证据（无）

| 证据 | 级别 | 影响 |
|------|------|------|
| 无缺失证据 | 无 | 无 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod 'rc-pending-nodeselector' 设置了 nodeSelector: aiops.e2e/nonexistent-node-label=true，而集群中所有节点均未定义该标签，导致调度失败。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 调度器无法找到满足 nodeSelector 的节点 → 无法调度 → Pod 保持 Pending 状态。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 调度失败事件：`node(s) didn't match Pod's node affinity/selector`。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 处于 Pending 状态，无法调度，Events 显示调度失败原因。        │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Pod 状态为 Pending)、证据 #2 (调度失败事件) 和证据 #3 (Pod nodeSelector 设置了不存在的标签)，问题的根本原因是 **Pod 设置了 `nodeSelector: aiops.e2e/nonexistent-node-label=true`，而集群中所有节点均未定义该标签，导致调度失败**。

**置信度**：高 (95%)
- ✅ Pod 状态为 Pending
- ✅ 事件显示 `node(s) didn't match Pod's node affinity/selector`
- ✅ Pod spec 明确设置了不存在的标签
- ✅ 所有节点均未定义该标签

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 移除或修改 nodeSelector**
```bash
kubectl edit pod rc-pending-nodeselector -n aiops-e2e
```
*操作*：删除或修改 `spec.nodeSelector` 中的 `aiops.e2e/nonexistent-node-label=true`。

**2. [替代方案] 添加标签到节点**
```bash
kubectl label nodes <node-name> aiops.e2e/nonexistent-node-label=true
```
*操作*：为至少一个节点添加该标签，使其满足 Pod 的调度要求。

### 后续优化

1. **检查所有 Pod 的 nodeSelector/affinity**：确保调度约束合理，标签存在。
2. **添加标签管理策略**：通过命名规范或自动标签机制，避免使用不存在的标签。
3. **使用节点污点（Taint）替代 nodeSelector**（如需限制某些节点）：提高调度灵活性和可维护性。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 调度 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running |
| 2. 检查调度事件 | `kubectl events -n aiops-e2e` | 无 `FailedScheduling` |
| 3. 检查节点标签 | `kubectl get nodes --show-labels` | 至少一个节点包含 `aiops.e2e/nonexistent-node-label=true` |

---

## ⚠️ 注意事项

- 如果需要保留 `nodeSelector`，请确保节点上已定义对应的标签。
- 避免使用自定义标签命名冲突，建议遵循命名规范（如 `app=xxx`, `env=xxx`）。
- 调度失败时，`kubectl describe pod` 和 `kubectl events` 是快速定位问题的关键命令。

---

## 📊 性能统计

├─ 总耗时: 7.1m
├─ 问题定位: 113.4s (27%) ✅
├─ 证据链采集: 94.7s (22%) ✅
├─ 根因分析: 98.5s (23%) ✅
├─ 汇总总结: 119.6s (28%) ✅
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
