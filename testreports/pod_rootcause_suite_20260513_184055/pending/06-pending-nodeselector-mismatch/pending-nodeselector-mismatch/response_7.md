======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 74ee0949a0734058]

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
15m                   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          15m   <none>   <none>   
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
  "reasoning": "Pod 'rc-pending-nodeselector' 在 aiops-e2e 命名空间中处于 Pending 状态，由于 nodeSelector 指定了不存在的标签 'aiops.e2e/nonexistent-node-label'，导致调度失败。事件显示 0/3 个节点符合 Pod 的节点选择器要求，表明调度问题源于节点标签不匹配。所有节点状态为 Ready，但未满足 Pod 的调度约束。",
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
    "PendingUnschedulable"
  ],
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "PendingUnschedulable",
  "status_category": "Scheduling",
  "key_entities": [
    {
      "type": "Pod",
      "name": "rc-pending-nodeselector",
      "namespace": "aiops-e2e"
    },
    {
      "type": "Node",
      "name": "master",
      "namespace": ""
    },
    {
      "type": "Node",
      "name": "node1",
      "namespace": ""
    },
    {
      "type": "Node",
      "name": "node2",
      "namespace": ""
    }
  ],
  "possible_scenarios": [
    "nodeSelector 指定了不存在的节点标签，导致 Pod 无法调度。",
    "集群中没有节点满足 Pod 的调度约束。",
    "所有节点状态为 Ready，但未满足 Pod 的调度需求。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 7.3s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'nodeSelector 指定了不存在的节点标签，导致 Pod 无法调度。', 'probability': 'high', 'reason': "事件中明确指出 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'，且 nodeSelector 包含不存在的标签。"}, {'scenario': '集群中没有节点满足 Pod 的调度约束。', 'probability': 'high', 'reason': '所有节点状态为 Ready，但未满足 nodeSelector 的要求，表明调度约束不匹配。'}, {'scenario': '所有节点状态为 Ready，但未满足 Pod 的调度需求。', 'probability': 'high', 'reason': '节点均处于 Ready 状态，但未匹配 nodeSelector 的标签要求，导致调度失败。'}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Node", "name": "master", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}]
   reasoning=Pod 'rc-pending-nodeselector' 在 aiops-e2e 命名空间中处于 Pending 状态，由于 nodeSelector 指定了不存在的标签 'aiops.e2e/nonexistent-node-label'，导致调度失败。事件显示 0/3 个节点符合 Pod 的节点选择器要求，表明调度问题源于节点标签不匹配。所有节点状态为 Ready，但未满足 Pod 的调度约束。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "Pod 'rc-pending-nodeselector' 在 aiops-e2e 命名空间中处于 Pending 状态，由于 nodeSelector 指定了不存在的标签 'aiops.e2e/nonexistent-node-label'，导致调度失败。事件显示 0/3 个节点符合 Pod 的节点选择器要求，表明调度问题源于节点标签不匹配。所有节点状态为 Ready，但未满足 Pod 的调度约束。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Node", "name": "master", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}], "possible_scenarios": [{"scenario": "nodeSelector 指定了不存在的节点标签，导致 Pod 无法调度。", "probability": "high", "reason": "事件中明确指出 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'，且 nodeSelector 包含不存在的标签。"}, {"scenario": "集群中没有节点满足 Pod 的调度约束。", "probability": "high", "reason": "所有节点状态为 Ready，但未满足 nodeSelector 的要求，表明调度约束不匹配。"}, {"scenario": "所有节点状态为 Ready，但未满足 Pod 的调度需求。", "probability": "high", "reason": "节点均处于 Ready 状态，但未匹配 nodeSelector 的标签要求，导致调度失败。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                15m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/74ee0949a0734058/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/74ee0949a0734058/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/74ee0949a0734058/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   230d   v1.26.8  
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
node1   Ready    <none>   230d   v1.26.8   10.2.0.49     <
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
node2   Ready    <none>   230d   v1.26.8   10.2.0.50     <
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (1m 57.9s)
   📤 → 下游数据: evidence_items=10/10
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod 'rc-pending-nodeselector' 的 nodeSelector 是否指定了不存在的标签，并确认其调度失败的具体原因","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"确认 Pod 的 nodeSelector 是否指定了不存在的标签，并验证调度失败的具体原因","evidence_type":"configuration","target_scope":"aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e2","description":"检查节点 'master', 'node1', 'node2' 的标签，确认是否匹配 Pod 的 nodeSelector","level":"important","tool":"kubectl_get_by_name","command":"kubectl get node master -o jsonpath='{.metadata.labels}'","tool_args":{"kind":"Node","name":"master","namespace":""},"purpose":"确认节点 'master' 的标签是否匹配 Pod 的 nodeSelector","evidence_type":"configuration","target_scope":"master","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e3","description":"检查节点 'node1' 的标签，确认是否匹配 Pod 的 nodeSelector","level":"important","tool":"kubectl_get_by_name","command":"kubectl get node node1 -o jsonpath='{.metadata.labels}'","tool_args":{"kind":"Node","name":"node1","namespace":""},"purpose":"确认节点 'node1' 的标签是否匹配 Pod 的 nodeSelector","evidence_type":"configuration","target_scope":"node1","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e4","description":"检查节点 'node2' 的标签，确认是否匹配 Pod 的 nodeSelector","level":"important","tool":"kubectl_get_by_name","command":"kubectl get node node2 -o jsonpath='{.metadata.labels}'","tool_args":{"kind":"Node","name":"node2","namespace":""},"purpose":"确认节点 'node2' 的标签是否匹配 Pod 的 nodeSelector","evidence_type":"configuration","target_scope":"node2","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e5","description":"检查 Pod 'rc-pending-nodeselector' 的 Events，确认调度失败的具体原因","level":"critical","tool":"kubectl_events","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"确认调度失败的具体原因，例如 nodeSelector 不匹配、taint 不匹配等","evidence_type":"event","target_scope":"aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-fsdjk\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/74ee0949a0734058/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/74ee0949a0734058/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/74ee0949a0734058/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/74ee0949a0734058/tools/002-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/74ee0949a0734058/tools/002-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/74ee0949a0734058/tools/002-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nnode1   Ready    <none>   230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/74ee0949a0734058/tools/003-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/74ee0949a0734058/tools/003-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/74ee0949a0734058/tools/003-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nnode2   Ready    <none>   230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/74ee0949a0734058/tools/004-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/74ee0949a0734058/tools/004-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/74ee0949a0734058/tools/004-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 5 项，实际采集 5 项，未采集 0 项，完整度 100%；其中真实环境证据 10/10 项，完整度 100%；实际执行工具 9 个，匹配计划 5 个，未规划证据 4 个","plan_total":5,"plan_collected":5,"plan_completeness":1.0,"environment_evidence_total":10,"environment_evidence_collected":10,"environment_evidence_completeness":1.0,"executed_tool_count":9,"matched_tool_count":5,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"验证 Pod 'rc-pending-nodeselector' 的 nodeSelector 是否指定了不存在的标签，并确认其调度失败的具体原因","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"确认 Pod 的 nodeSelector 是否指定了不存在的标签，并验证调度失败的具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"检查节点 'master', 'node1', 'node2' 的标签，确认是否匹配 Pod 的 nodeSelector","level":"important","tool":"kubectl_get_by_name","command":"kubectl get node master -o jsonpath='{.metadata.labels}'","purpose":"确认节点 'master' 的标签是否匹配 Pod 的 nodeSelector","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"检查节点 'node1' 的标签，确认是否匹配 Pod 的 nodeSelector","level":"important","tool":"kubectl_get_by_name","command":"kubectl get node node1 -o jsonpath='{.metadata.labels}'","purpose":"确认节点 'node1' 的标签是否匹配 Pod 的 nodeSelector","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"检查节点 'node2' 的标签，确认是否匹配 Pod 的 nodeSelector","level":"important","tool":"kubectl_get_by_name","command":"kubectl get node node2 -o jsonpath='{.metadata.labels}'","purpose":"确认节点 'node2' 的标签是否匹配 Pod 的 nodeSelector","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5","description":"检查 Pod 'rc-pending-nodeselector' 的 Events，确认调度失败的具体原因","level":"critical","tool":"kubectl_events","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"确认调度失败的具体原因，例如 nodeSelector 不匹配、taint 不匹配等","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 5/5 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_yaml | 验证 Pod 'rc-pending-nodeselector' 的 nodeSelect... | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e2 | important | ✅ | kubectl_get_by_name | 检查节点 'master', 'node1', 'node2' 的标签，确认是否匹配 Po... | `kubectl get node master -o jsonpath='{.metadata.labels}'` |
   | e3 | important | ✅ | kubectl_get_by_name | 检查节点 'node1' 的标签，确认是否匹配 Pod 的 nodeSelector | `kubectl get node node1 -o jsonpath='{.metadata.labels}'` |
   | e4 | important | ✅ | kubectl_get_by_name | 检查节点 'node2' 的标签，确认是否匹配 Pod 的 nodeSelector | `kubectl get node node2 -o jsonpath='{.metadata.labels}'` |
   | e5 | critical | ✅ | kubectl_events | 检查 Pod 'rc-pending-nodeselector' 的 Events，确认调... | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (36.3s)
   📤 → 下游数据: root_cause=Pod 'rc-pending-nodeselector' 的 nodeSelector 指定了不存在的标签 'aiops.e2e/nonexistent-node-label'，导致调度失败。事件显示 0/3 个节点符合调度要求，进一步确认了标签不匹配的问题。
   confidence=95%
   causal_chain={"root_cause": "Pod 'rc-pending-nodeselector' 的 nodeSelector 指定了不存在的标签 'aiops.e2e/nonexistent-node-label'，导致调度失败。", "intermediate_causes": ["节点 'master', 'node1', 'node2' 的标签不匹配 Pod 的 nodeSelector 要求。", "Pod 'rc-pending-nodeselector' 的 Events 显示 0/3 个节点符合调度要求。"], "immediate_causes": ["Pod 'rc-pending-nodeselector' 无法找到符合 nodeSelector 要求的节点。", "所有节点的标签不包含 'aiops.e2e/nonexistent-node-label'。"], "symptoms": ["Pod 'rc-pending-nodeselector' 处于 Pending 状态。", "Events 显示调度失败。"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"e1": "Pod 'rc-pending-nodeselector' 的 nodeSelector 指定了不存在的标签 'aiops.e2e/nonexistent-node-label'，导致调度失败。"}, {"e2": "节点 'master', 'node1', 'node2' 的标签不匹配 Pod 的 nodeSelector 要求。"}, {"e5": "Pod 'rc-pending-nodeselector' 的 Events 显示 0/3 个节点符合调度要求，原因是标签不匹配。"}], "evidence_analysis": [{"e1": "Pod 的 nodeSelector 指定了不存在的标签 'aiops.e2e/nonexistent-node-label'，导致调度失败。"}, {"e2": "所有节点 'master', 'node1', 'node2' 的标签不包含 'aiops.e2e/nonexistent-node-label'，因此无法满足 Pod 的调度需求。"}, {"e5": "Events 显示 0/3 个节点符合 Pod 的调度要求，进一步确认了标签不匹配的问题。"}], "causal_chain": {"root_cause": "Pod 'rc-pending-nodeselector' 的 nodeSelector 指定了不存在的标签 'aiops.e2e/nonexistent-node-label'，导致调度失败。", "intermediate_causes": ["节点 'master', 'node1', 'node2' 的标签不匹配 Pod 的 nodeSelector 要求。", "Pod 'rc-pending-nodeselector' 的 Events 显示 0/3 个节点符合调度要求。"], "immediate_causes": ["Pod 'rc-pending-nodeselector' 无法找到符合 nodeSelector 要求的节点。", "所有节点的标签不包含 'aiops.e2e/nonexistent-node-label'。"], "symptoms": ["Pod 'rc-pending-nodeselector' 处于 Pending 状态。", "Events 显示调度失败。"]}, "root_cause": "Pod 'rc-pending-nodeselector' 的 nodeSelector 指定了不存在的标签 'aiops.e2e/nonexistent-node-label'，导致调度失败。事件显示 0/3 个节点符合调度要求，进一步确认了标签不匹配的问题。", "root_cause_summary": "Pod 'rc-pending-nodeselector' 的 nodeSelector 指定了不存在的标签 'aiops.e2e/nonexistent-node-label'，导致调度失败。事件显示 0/3 个节点符合调度要求，进一步确认了标签不匹配的问题。", "confidence": 0.95, "confidence_reason": "有直接证据表明 Pod 的 nodeSelector 指定了不存在的标签，并且 Events 显示调度失败。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [], "limitations": "无", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'rc-pending-nodeselector' 的 nodeSelector 指定了不存在的标签 'aiops.e2e/nonexistent-node-label'，导致调度失败。事件显示 0/3 个节点符合调度要求，进一步确认了标签不匹配的问题。
   置信度: 95%
   🔗 因果链:
     根本原因: Pod 'rc-pending-nodeselector' 的 nodeSelector 指定了不存在的标签 'aiops.e2e/nonexistent-node-label'，导致调度失败。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (2m 11.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4448 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 53.4s
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
| **兼容归因层** | L1 - scheduling |
| **问题分类** | 节点选择器标签不匹配导致调度失败 |
| **置信度** | 高 (95%) |
| **证据完整度** | 5/5 (100%) |

---

## 🔍 现象描述

**用户报告**：  
> 我的集群有什么问题？

**关键实体**：  
| 类型 | 值 |
|------|-----|
| Pod | rc-pending-nodeselector |
| Namespace | aiops-e2e |
| Node | master, node1, node2 |
| 错误信息 | 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | `STATUS: Pending` | Pod 无法调度 |
| 2 | Pod Events | `kubectl events -n aiops-e2e` | `15m Warning FailedScheduling Pod/rc-pending-nodeselector 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 调度失败因 nodeSelector 不匹配 |
| 3 | Pod YAML | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` | `nodeSelector: aiops.e2e/nonexistent-node-label: "true"` | Pod 指定了不存在的节点标签 |
| 4 | Node 标签 | `kubectl get node master -o jsonpath='{.metadata.labels}'` | `{"beta\.kubernetes\.io/arch":"amd64", "beta\.kubernetes\.io/os":"linux", "kubernetes\.io/arch":"amd64", "kubernetes\.io/hostname":"master", "kubernetes\.io/os":"linux", "node\.role\.kubernetes\.io/control-plane":""}` | master 节点无 `aiops.e2e/nonexistent-node-label` 标签 |
| 5 | Node 标签 | `kubectl get node node1 -o jsonpath='{.metadata.labels}'` | `{"beta\.kubernetes\.io/arch":"amd64", "beta\.kubernetes\.io/os":"linux", "kubernetes\.io/arch":"amd64", "kubernetes\.io/hostname":"node1", "kubernetes\.io/os":"linux"}` | node1 节点无 `aiops.e2e/nonexistent-node-label` 标签 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 处于 `Pending` 状态，Events 明确指出调度失败是因为 nodeSelector 不匹配。
- **证据 #3 印证**：Pod 的 `nodeSelector` 指定了 `aiops.e2e/nonexistent-node-label: "true"`，但此标签在所有节点上均未定义。
- **证据 #4 + #5 印证**：所有节点（master、node1、node2）均无该标签，导致调度失败。

### 缺失证据（无）

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod 'rc-pending-nodeselector' 的 nodeSelector 指定了不存在的标签 'aiops.e2e/nonexistent-node-label'，导致调度失败。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Kube-scheduler 无法找到匹配 nodeSelector 的节点，导致 Pod 无法调度。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 Pending，持续无法调度。                              │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1（Pod 状态为 Pending）、证据 #2（Events 显示调度失败）和证据 #3（nodeSelector 指定不存在的标签），问题的根本原因是 **Pod 指定了不存在的节点标签 `aiops.e2e/nonexistent-node-label`**，导致调度失败。  
**置信度**：高 (95%)  
- ✅ Events 明确显示调度失败原因  
- ✅ Pod YAML 显示 nodeSelector 指定不存在的标签  
- ✅ 所有节点均无该标签  

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 移除或修改 Pod 的 nodeSelector**
```bash
kubectl edit pod rc-pending-nodeselector -n aiops-e2e
```
*操作*：删除或修改 `nodeSelector: aiops.e2e/nonexistent-node-label: "true"`，保存后 Pod 会重新调度。

**2. [可选] 为节点添加指定标签**
```bash
kubectl label nodes <node-name> aiops.e2e/nonexistent-node-label=true
```
*操作*：为至少一个节点添加该标签，使 Pod 能够调度到该节点。

### 后续优化

1. **标签管理**：确保所有 nodeSelector 使用的标签在节点上实际存在，避免调度失败。
2. **Pod 配置审查**：定期检查 Pod 的调度配置，确保符合集群标签规范。
3. **调度器日志**：启用 `--v=5` 调试日志，查看调度器的详细决策过程。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 是否调度成功 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running |
| 2. 检查调度事件 | `kubectl events -n aiops-e2e` | 无 `FailedScheduling` 事件 |
| 3. 检查节点标签 | `kubectl get node <node-name> -o jsonpath='{.metadata.labels}'` | 包含 `aiops.e2e/nonexistent-node-label: "true"`（如步骤 2 执行） |

---

## ⚠️ 注意事项

- 如果选择为节点添加标签，请确保标签命名符合集群规范，避免标签混乱。
- 如果 Pod 需要特定硬件/环境，考虑使用 Taint/Label + Node Affinity 的组合方式，而不是单独使用 nodeSelector。

---

## 📊 性能统计

├─ 总耗时: 5.9m
├─ 问题定位: 67.3s (19%) ✅
├─ 证据链采集: 117.9s (33%) ✅
├─ 根因分析: 36.3s (10%) ✅
├─ 汇总总结: 131.8s (37%) ✅
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
