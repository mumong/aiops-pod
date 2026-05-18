======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 5370a3fad71c4653]

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
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          93m   <none>   <none>   
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          93m   <none>   <none>   
   💭 [问题定位] {
  "layer": "L1",
  "derived_layer": "L1",
  "layers": [
    "L1"
  ],
  "layer_name": "PendingUnschedulable",
  "confidence": 0.95,
  "reasoning": "Pod 'rc-pending-nodeselector' 处于 Pending 状态，Events 显示 'FailedScheduling'，且原因 '3 node(s) didn't match Pod's node affinity/selector'，表明 Pod 无法调度到节点，符合 L1 问题类型。节点状态均正常，但调度失败可能与 nodeSelector 或 affinity 不匹配有关。",
  "abnormal_pods": [
    {
      "name": "rc-pending-nodeselector",
      "namespace": "aiops-e2e",
      "status": "Pending",
      "reason": "FailedScheduling",
      "message": "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling."
    }
  ],
  "abnormal_groups": {
    "PendingUnschedulable": 1
  },
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "PendingUnschedulable",
  "status_category": "Scheduling",
  "key_entities": [
    "Pod: rc-pending-nodeselector (aiops-e2e)",
    "Event: FailedScheduling"
  ],
  "possible_scenarios": [
    "Pod 的 nodeSelector 或 affinity 设置不匹配任何节点",
    "节点上没有足够的资源或配置不符合要求",
    "节点上存在 taint 且 Pod 未配置 toleration"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 36.3s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'Pod 的 nodeSelector 或 affinity 设置不匹配任何节点', 'probability': 'high', 'reason': "事件描述显示 '3 node(s) didn't match Pod's node affinity/selector'"}, {'scenario': '节点上没有足够的资源或配置不符合要求', 'probability': 'medium', 'reason': '节点状态正常，但未匹配调度条件'}, {'scenario': '节点上存在 taint 且 Pod 未配置 toleration', 'probability': 'medium', 'reason': '事件未显示 taint 信息，但未排除此可能性'}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}]
   reasoning=Pod 'rc-pending-nodeselector' 处于 Pending 状态，Events 显示 'FailedScheduling'，且原因 '3 node(s) didn't match Pod's node affinity/selector'，表明 Pod 无法调度到节点，符合 L1 问题类型。节点状态均正常，但调度失败可能与 nodeSelector 或 affinity 不匹配有关。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "Pod 'rc-pending-nodeselector' 处于 Pending 状态，Events 显示 'FailedScheduling'，且原因 '3 node(s) didn't match Pod's node affinity/selector'，表明 Pod 无法调度到节点，符合 L1 问题类型。节点状态均正常，但调度失败可能与 nodeSelector 或 affinity 不匹配有关。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "Scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Pod 的 nodeSelector 或 affinity 设置不匹配任何节点", "probability": "high", "reason": "事件描述显示 '3 node(s) didn't match Pod's node affinity/selector'"}, {"scenario": "节点上没有足够的资源或配置不符合要求", "probability": "medium", "reason": "节点状态正常，但未匹配调度条件"}, {"scenario": "节点上存在 taint 且 Pod 未配置 toleration", "probability": "medium", "reason": "事件未显示 taint 信息，但未排除此可能性"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                93m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/5370a3fad71c4653/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/5370a3fad71c4653/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/5370a3fad71c4653/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
  Warning  FailedScheduling  22m (x15 over 92m)  default-scheduler  0/3 nodes are available:
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
22m (x15 over 92m)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 
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
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。
   💭 [证据链采集] 已采集关键证据：
1. **critical**: `kubectl describe pod` 显示 Pod 处于 Pending 状态，且调度失败原因为所有节点不匹配 nodeSelector/affinity。
2. **critical**: `kubectl events` 显示事件 `FailedScheduling`，描述 `3 node(s) didn't match Pod's node affinity/selector`，确认调度失败。
3. **important**: `kubectl get pod -o yaml` 显示 Pod 的 `nodeSelector` 设置了不存在的标签 `aiops.e2e/nonexistent-node-label="true"`，导致无法匹配任何节点。
4. **important**: `kubectl get nodes` 显示所有节点状态为 Ready，且无 Unschedulable 标志，确认调度失败不是节点状态问题。
5. **important**: `kubectl get pvc` 未发现 PVC 资源，排除 PVC 未绑定的可能性。

结论：Pod 无法调度的根本原因是其 `nodeSelector` 设置了不存在的标签，导致所有节点均不匹配。建议修正 Pod 的 `nodeSelector` 或为节点添加对应标签。
   ✅ [证据链采集] 完成 (2m 26.6s)
   📤 → 下游数据: evidence_items=10/11
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod 'rc-pending-nodeselector' 的详细描述信息，确认调度失败的具体原因。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"pod":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"验证 Pod 的 FailedScheduling 事件和调度失败的详细原因","evidence_type":"diagnostic_events","target_scope":"specific_pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod 'rc-pending-nodeselector' 的事件记录，确认调度失败的上下文信息。","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-pending-nodeselector","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-pending-nodeselector"},"purpose":"确认调度失败的事件上下文","evidence_type":"event_logs","target_scope":"specific_pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"检查 Pod 'rc-pending-nodeselector' 的 nodeSelector 和 affinity 配置，确认其调度条件。","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"pod":"rc-pending-nodeselector","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"验证 Pod 的 nodeSelector 和 affinity 配置","evidence_type":"pod_spec","target_scope":"specific_pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"检查集群中所有节点的状态和标签，确认是否有节点匹配 Pod 的调度条件。","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{","tool_args":{},"purpose":"","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e5","description":"检查集群中所有节点的 taint 配置，确认是否有与 Pod 不兼容的 taint。","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{","tool_args":{},"purpose":"","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e6","description":"检查 Pod 'rc-pending-nodeselector' 是否引用了未绑定的 PVC，确认是否涉及存储问题。","level":"optional","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get pvc -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","kind":"PersistentVolumeClaim"},"purpose":"确认 PVC 是否绑定","evidence_type":"storage_dependency","target_scope":"namespace","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  22m (x15 over 92m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/5370a3fad71c4653/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/5370a3fad71c4653/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/5370a3fad71c4653/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n22m (x15 over 92m)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/5370a3fad71c4653/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/5370a3fad71c4653/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/5370a3fad71c4653/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-fsdjk\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/5370a3fad71c4653/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/5370a3fad71c4653/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/5370a3fad71c4653/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/5370a3fad71c4653/tools/004-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/5370a3fad71c4653/tools/004-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/5370a3fad71c4653/tools/004-evidence-kubectl_get_by_kind_in_cluster.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/5370a3fad71c4653/tools/005-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/5370a3fad71c4653/tools/005-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/5370a3fad71c4653/tools/005-evidence-kubectl_get_by_kind_in_namespace.summary.txt"}],"llm_analysis":"已采集关键证据：\n1. **critical**: `kubectl describe pod` 显示 Pod 处于 Pending 状态，且调度失败原因为所有节点不匹配 nodeSelector/affinity。\n2. **critical**: `kubectl events` 显示事件 `FailedScheduling`，描述 `3 node(s) didn't match Pod's node affinity/selector`，确认调度失败。\n3. **important**: `kubectl get pod -o yaml` 显示 Pod 的 `nodeSelector` 设置了不存在的标签 `aiops.e2e/nonexistent-node-label=\"true\"`，导致无法匹配任何节点。\n4. **important**: `kubectl get nodes` 显示所有节点状态为 Ready，且无 Unschedulable 标志，确认调度失败不是节点状态问题。\n5. **important**: `kubectl get pvc` 未发现 PVC 资源，排除 PVC 未绑定的可能性。\n\n结论：Pod 无法调度的根本原因是其 `nodeSelector` 设置了不存在的标签，导致所有节点均不匹配。建议修正 Pod 的 `nodeSelector` 或为节点添加对应标签。","collection_summary":"计划 5 项，实际采集 4 项，未采集 1 项，完整度 80%；其中真实环境证据 9/10 项，完整度 90%；实际执行工具 9 个，匹配计划 5 个，未规划证据 4 个","plan_total":5,"plan_collected":4,"plan_completeness":0.8,"environment_evidence_total":10,"environment_evidence_collected":9,"environment_evidence_completeness":0.9,"executed_tool_count":9,"matched_tool_count":5,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"获取 Pod 'rc-pending-nodeselector' 的详细描述信息，确认调度失败的具体原因。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"验证 Pod 的 FailedScheduling 事件和调度失败的详细原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod 'rc-pending-nodeselector' 的事件记录，确认调度失败的上下文信息。","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-pending-nodeselector","purpose":"确认调度失败的事件上下文","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"检查 Pod 'rc-pending-nodeselector' 的 nodeSelector 和 affinity 配置，确认其调度条件。","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"验证 Pod 的 nodeSelector 和 affinity 配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"检查集群中所有节点的状态和标签，确认是否有节点匹配 Pod 的调度条件。","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{","purpose":"","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5","description":"检查集群中所有节点的 taint 配置，确认是否有与 Pod 不兼容的 taint。","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{","purpose":"","collected":false,"source":"planned","outcome":"unknown"},{"id":"e6","description":"检查 Pod 'rc-pending-nodeselector' 是否引用了未绑定的 PVC，确认是否涉及存储问题。","level":"optional","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get pvc -n aiops-e2e","purpose":"确认 PVC 是否绑定","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e5(检查集群中所有节点的 taint 配置，确认是否有与 Pod 不兼容的 taint。): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/5 项, 完整度: 90%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取 Pod 'rc-pending-nodeselector' 的详细描述信息，确认调度... | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_events | 获取 Pod 'rc-pending-nodeselector' 的事件记录，确认调度失败... | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-pendi...` |
   | e3 | important | ✅ | kubectl_get_yaml | 检查 Pod 'rc-pending-nodeselector' 的 nodeSelect... | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e4 | important | ✅ | kubectl_get_by_kind_in_cl... | 检查集群中所有节点的状态和标签，确认是否有节点匹配 Pod 的调度条件。 | `kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{` |
   | e5 | important | ❌ | kubectl_get_by_kind_in_cl... | 检查集群中所有节点的 taint 配置，确认是否有与 Pod 不兼容的 taint。 | `kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{` |
   | e6 | optional | ✅ | kubectl_get_by_kind_in_na... | 检查 Pod 'rc-pending-nodeselector' 是否引用了未绑定的 PV... | `kubectl get pvc -n aiops-e2e` |

   ⚠️ 未采集原因:
   - e5(检查集群中所有节点的 taint 配置，确认是否有与 Pod 不兼容的 taint。): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (3m 33.3s)
   📤 → 下游数据: root_cause=Pod 'rc-pending-nodeselector' 处于 Pending 状态，调度失败的根本原因是其 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label=true'，导致所有节点均不匹配。
   confidence=95%
   causal_chain={"root_cause": "Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label=true'，导致所有节点均不匹配，无法调度。", "intermediate_causes": ["Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label=true'。", "集群中所有节点均未设置 'aiops.e2e/nonexistent-node-label=true' 标签。"], "immediate_causes": ["Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label=true'。", "集群中所有节点均未设置 'aiops.e2e/nonexistent-node-label=true' 标签。"], "manifestations": ["Pod 'rc-pending-nodeselector' 的状态为 Pending。", "事件记录显示 '3 node(s) didn't match Pod's node affinity/selector'。"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"description": "获取 Pod 'rc-pending-nodeselector' 的详细描述信息，确认调度失败的具体原因。", "level": "critical", "value": "kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  22m (x15 over 92m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:"}, {"description": "获取 Pod 'rc-pending-nodeselector' 的事件记录，确认调度失败的上下文信息。", "level": "critical", "value": "kubectl_events 摘要:\n关键诊断行:\n22m (x15 over 92m)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.."}, {"description": "检查 Pod 'rc-pending-nodeselector' 的 nodeSelector 和 affinity 配置，确认其调度条件。", "level": "important", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSe"}, {"description": "检查集群中所有节点的状态和标签，确认是否有节点匹配 Pod 的调度条件。", "level": "important", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubern"}, {"description": "检查 Pod 'rc-pending-nodeselector' 是否引用了未绑定的 PVC，确认是否涉及存储问题。", "level": "optional", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Pending': 1, 'Running': 46}\nNAMESPACE     NAME                                                READY   STATUS      RESTARTS         AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\n# 异常行\naiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                93m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type"}, {"description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "level": "important", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Pending': 1, 'Running': 46}\nNAMESPACE     NAME                                                READY   STATUS      RESTARTS         AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\n# 异常行\naiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                93m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type"}, {"description": "上游已验证工具结果: kubectl_describe", "level": "important", "value": "kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  18m (x15 over 88m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:"}, {"description": "上游已验证工具结果: kubectl_get_by_name", "level": "important", "value": "NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS\nrc-pending-nodeselector   0/1     Pending   0          93m   <none>   <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"}, {"description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "level": "important", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubern"}, {"description": "上游已验证工具结果: kubectl_get_by_name", "level": "important", "value": "NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS\nrc-pending-nodeselector   0/1     Pending   0          93m   <none>   <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"}], "evidence_analysis": [{"description": "获取 Pod 'rc-pending-nodeselector' 的详细描述信息，确认调度失败的具体原因。", "level": "critical", "value": "Pod 'rc-pending-nodeselector' 的状态为 Pending，调度失败的具体原因为 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'，表明所有节点均不匹配 Pod 的 nodeSelector/affinity 条件。"}, {"description": "获取 Pod 'rc-pending-nodeselector' 的事件记录，确认调度失败的上下文信息。", "level": "critical", "value": "事件记录显示 '3 node(s) didn't match Pod's node affinity/selector'，表明调度失败是由于 Pod 的 nodeSelector/affinity 与节点不匹配。"}, {"description": "检查 Pod 'rc-pending-nodeselector' 的 nodeSelector 和 affinity 配置，确认其调度条件。", "level": "important", "value": "Pod 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，但集群中所有节点均未设置该标签，导致调度失败。"}, {"description": "检查集群中所有节点的状态和标签，确认是否有节点匹配 Pod 的调度条件。", "level": "important", "value": "所有节点状态为 Ready，但无节点设置 'aiops.e2e/nonexistent-node-label=true'，导致 Pod 无法调度。"}, {"description": "检查 Pod 'rc-pending-nodeselector' 是否引用了未绑定的 PVC，确认是否涉及存储问题。", "level": "optional", "value": "未发现 PVC 资源，排除 PVC 未绑定的可能性。"}, {"description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "level": "important", "value": "所有节点状态为 Ready，但无节点设置 'aiops.e2e/nonexistent-node-label=true'，导致 Pod 无法调度。"}, {"description": "上游已验证工具结果: kubectl_describe", "level": "important", "value": "Pod 'rc-pending-nodeselector' 的状态为 Pending，调度失败的具体原因为 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'，表明所有节点均不匹配 Pod 的 nodeSelector/affinity 条件。"}, {"description": "上游已验证工具结果: kubectl_get_by_name", "level": "important", "value": "Pod 'rc-pending-nodeselector' 的状态为 Pending，且未被调度到任何节点。"}, {"description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "level": "important", "value": "所有节点状态为 Ready，但无节点设置 'aiops.e2e/nonexistent-node-label=true'，导致 Pod 无法调度。"}, {"description": "上游已验证工具结果: kubectl_get_by_name", "level": "important", "value": "Pod 'rc-pending-nodeselector' 的状态为 Pending，且未被调度到任何节点。"}], "causal_chain": {"root_cause": "Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label=true'，导致所有节点均不匹配，无法调度。", "intermediate_causes": ["Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label=true'。", "集群中所有节点均未设置 'aiops.e2e/nonexistent-node-label=true' 标签。"], "immediate_causes": ["Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label=true'。", "集群中所有节点均未设置 'aiops.e2e/nonexistent-node-label=true' 标签。"], "manifestations": ["Pod 'rc-pending-nodeselector' 的状态为 Pending。", "事件记录显示 '3 node(s) didn't match Pod's node affinity/selector'。"]}, "root_cause": "Pod 'rc-pending-nodeselector' 处于 Pending 状态，调度失败的根本原因是其 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label=true'，导致所有节点均不匹配。", "root_cause_summary": "Pod 'rc-pending-nodeselector' 处于 Pending 状态，调度失败的根本原因是其 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label=true'，导致所有节点均不匹配。", "confidence": 0.95, "confidence_reason": "有直接证据表明调度失败是由于 nodeSelector 不匹配，因果链清晰。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [], "limitations": "未检查集群中所有节点的 taint 配置，但事件未显示 taint 信息，因此未排除 taint 不兼容的可能性。", "llm_raw_analysis": "已采集关键证据：\n1. **critical**: `kubectl describe pod` 显示 Pod 处于 Pending 状态，且调度失败原因为所有节点不匹配 nodeSelector/affinity。\n2. **critical**: `kubectl events` 显示事件 `FailedScheduling`，描述 `3 node(s) didn't match Pod's node affinity/selector`，确认调度失败。\n3. **important**: `kubectl get pod -o yaml` 显示 Pod 的 `nodeSelector` 设置了不存在的标签 `aiops.e2e/nonexistent-node-label=\"true\"`，导致无法匹配任何节点。\n4. **important**: `kubectl get nodes` 显示所有节点状态为 Ready，且无 Unschedulable 标志，确认调度失败不是节点状态问题。\n5. **important**: `kubectl get pvc` 未发现 PVC 资源\n... 截断，原始 610 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'rc-pending-nodeselector' 处于 Pending 状态，调度失败的根本原因是其 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label=true'，导致所有节点均不匹配。
   置信度: 95%
   🔗 因果链:
     根本原因: Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label=true'，导致所有节点均不匹配，无法调度。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 11.4s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4094 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 8m 47.6s
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
| **兼容归因层** | L1 - Scheduling |
| **问题分类** | 调度失败（nodeSelector/affinity 不匹配） |
| **置信度** | 高 (95%) |
| **证据完整度** | 4/5 (80%) |

---

## 🔍 现象描述

**用户报告**：  
> 我的集群有什么问题

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | `rc-pending-nodeselector` |
| Namespace | `aiops-e2e` |
| Node | `<none>` |
| 错误信息 | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: Pending, REASON: FailedScheduling` | Pod 无法调度 |
| 2 | 事件记录 | `kubectl describe pod rc-pending-nodeselector` | `Warning  FailedScheduling  18m (x15 over 88m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 明确指出调度失败原因是 nodeSelector 不匹配 |
| 3 | Pod spec | `kubectl get pod -o yaml` | `nodeSelector: aiops.e2e/nonexistent-node-label: "true"` | Pod 指定了不存在的节点标签 |
| 4 | 节点状态 | `kubectl get node` | `3 nodes are Ready, no node has label 'aiops.e2e/nonexistent-node-label'` | 所有节点均不匹配 Pod 的 nodeSelector |
| 5 | PVC 状态 | `kubectl get pvc` | 无匹配 PVC | 排除 PVC 未绑定问题 |

### 证据关联分析

- **证据 #2 + #3 印证**：调度失败事件明确指出 nodeSelector 不匹配，且 Pod 的 nodeSelector 设置了不存在的标签 `aiops.e2e/nonexistent-node-label=true`。
- **证据链**：Pod 指定了不存在的标签 → 无节点匹配 → 调度失败 → Pod 处于 Pending 状态。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 节点 taint 配置 | important | 未确认是否存在 taint 不兼容问题，但事件中未提及 taint，影响较小 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label=true'，导致所有节点均不匹配。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 调度器尝试将 Pod 调度到匹配 nodeSelector 的节点，但所有节点均不满足条件。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Pod 被标记为 'Pending'，事件显示 'FailedScheduling'，原因是 '3 node(s) didn't match Pod's node affinity/selector'。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 'rc-pending-nodeselector' 处于 'Pending' 状态，且长时间未调度成功。 │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2（`FailedScheduling` 事件）和证据 #3（Pod 的 nodeSelector 设置了不存在的标签 `aiops.e2e/nonexistent-node-label=true`），问题的根本原因是 **Pod 指定了一个不存在的节点标签，导致所有节点均不匹配**。

**置信度**：高 (95%)
- ✅ 事件明确指出调度失败原因
- ✅ Pod spec 明确显示 nodeSelector 设置了不存在的标签
- ⚠️ 未采集节点 taint 配置，但事件未提及 taint，影响较小

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 修正 Pod 的 nodeSelector 设置**

```bash
kubectl edit pod rc-pending-nodeselector -n aiops-e2e
```

*操作*：删除或修改 `nodeSelector` 中的 `aiops.e2e/nonexistent-node-label: "true"`，改为一个存在的节点标签（如 `kubernetes.io/os: linux`），保存后 Pod 会重新调度。

**2. [可选] 检查节点标签，确认是否符合需求**

```bash
kubectl get node --show-labels
```

*目的*：确认节点是否具备你希望 Pod 调度的标签。

### 后续优化

1. **标签管理**：确保 nodeSelector 中使用的标签在节点上真实存在。
2. **使用节点 affinity 或 toleration**：如需更灵活调度，可考虑使用 nodeAffinity 替代 nodeSelector，或添加 toleration 以容忍节点 taint。
3. **自动调度验证**：在部署前验证调度条件是否满足，避免调度失败。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running |
| 2. 检查调度事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | No FailedScheduling events |
| 3. 检查节点标签 | `kubectl get node --show-labels` | 确认 nodeSelector 中的标签存在 |

---

## ⚠️ 注意事项

- 如果你希望 Pod 调度到特定硬件配置的节点（如 GPU、SSD），请确保这些节点已正确打标签。
- 如果集群中节点存在 taint，建议同时检查 Pod 的 toleration 配置。

---

## 📊 性能统计

├─ 总耗时: 8.8m
├─ 问题定位: 96.3s (18%) ✅
├─ 证据链采集: 146.6s (28%) ✅
├─ 根因分析: 213.3s (40%) ✅
├─ 汇总总结: 71.4s (14%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 11 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 11 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
