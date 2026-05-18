======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 4c551c4f421b44cb]

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
  Warning  FailedScheduling  31m                default-scheduler  0/3 nodes are available: 
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          31m   <none>   <none>   
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
  "reasoning": "Pod rc-pending-nodeselector 处于 Pending 状态，并且 Events 显示调度失败原因是 'node(s) didn't match Pod's node affinity/selector'。这表明 Pod 的 nodeSelector 不匹配任何可用节点的标签。进一步检查 Pod 的 YAML 配置确认了 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label'，而集群中的节点均未标记此标签。因此，调度器无法找到符合条件的节点来运行该 Pod。",
  "abnormal_pods": [
    {
      "name": "rc-pending-nodeselector",
      "namespace": "aiops-e2e",
      "status": "Pending",
      "pod_abnormal_type": "PendingUnschedulable"
    }
  ],
  "abnormal_groups": [
    {
      "pod_status_keyword": "Pending",
      "pod_abnormal_type": "PendingUnschedulable",
      "status_category": "PendingUnschedulable"
    }
  ],
  "key_entities": [
    {
      "kind": "Pod",
      "name": "rc-pending-nodeselector",
      "namespace": "aiops-e2e"
    },
    {
      "kind": "Node",
      "name": "master",
      "namespace": ""
    },
    {
      "kind": "Node",
      "name": "node1",
      "namespace": ""
    },
    {
      "kind": "Node",
      "name": "node2",
      "namespace": ""
    }
  ],
  "possible_scenarios": [
    {
      "scenario": "Pod 的 nodeSelector 设置了不存在的节点标签，导致调度失败。",
      "evidence": "Events 显示 'node(s) didn't match Pod's node affinity/selector'，并且 Pod 的 YAML 配置确认了 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label'，而节点均未标记此标签。"
    }
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 4.0s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'Pod 的 nodeSelector 设置了不存在的节点标签，导致调度失败。', 'probability': 'high', 'reason': "Events 显示 'node(s) didn't match Pod's node affinity/selector'，并且 Pod 的 YAML 配置确认了 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label'，而节点均未标记此标签。"}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Node", "name": "master", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}]
   reasoning=Pod rc-pending-nodeselector 处于 Pending 状态，并且 Events 显示调度失败原因是 'node(s) didn't match Pod's node affinity/selector'。这表明 Pod 的 nodeSelector 不匹配任何可用节点的标签。进一步检查 Pod 的 YAML 配置确认了 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label'，而集群中的节点均未标记此标签。因此，调度器无法找到符合条件的节点来运行该 Pod。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "Pod rc-pending-nodeselector 处于 Pending 状态，并且 Events 显示调度失败原因是 'node(s) didn't match Pod's node affinity/selector'。这表明 Pod 的 nodeSelector 不匹配任何可用节点的标签。进一步检查 Pod 的 YAML 配置确认了 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label'，而集群中的节点均未标记此标签。因此，调度器无法找到符合条件的节点来运行该 Pod。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Node", "name": "master", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}], "possible_scenarios": [{"scenario": "Pod 的 nodeSelector 设置了不存在的节点标签，导致调度失败。", "probability": "high", "reason": "Events 显示 'node(s) didn't match Pod's node affinity/selector'，并且 Pod 的 YAML 配置确认了 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label'，而节点均未标记此标签。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                31m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/4c551c4f421b44cb/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/4c551c4f421b44cb/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/4c551c4f421b44cb/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ✅ [证据链采集] 完成 (1m 9.9s)
   📤 → 下游数据: evidence_items=7/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod 的 nodeSelector 是否与集群中任何节点的标签匹配","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"namespace":"aiops-e2e","name":"rc-pending-nodeselector","kind":"Pod"},"purpose":"检查 Pod 的 nodeSelector 配置，确认其设置的标签是否存在于任何节点上","evidence_type":"configuration","target_scope":"Pod rc-pending-nodeselector","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e2","description":"检查集群中所有节点的标签","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o json","tool_args":{"kind":"Node"},"purpose":"获取所有节点的标签信息，确认是否存在与 Pod 的 nodeSelector 匹配的标签","evidence_type":"configuration","target_scope":"All Nodes","acceptable_tools":["kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true},{"id":"e3","description":"获取 Pod 的调度失败事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-pending-nodeselector","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-pending-nodeselector"},"purpose":"查看 Pod 的调度失败事件，确认调度失败的具体原因","evidence_type":"event","target_scope":"Pod rc-pending-nodeselector","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-fsdjk\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4c551c4f421b44cb/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4c551c4f421b44cb/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4c551c4f421b44cb/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4c551c4f421b44cb/tools/002-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4c551c4f421b44cb/tools/002-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4c551c4f421b44cb/tools/002-evidence-kubectl_get_by_kind_in_cluster.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 3 项，实际采集 2 项，未采集 1 项，完整度 67%；其中真实环境证据 7/8 项，完整度 88%；实际执行工具 7 个，匹配计划 2 个，未规划证据 5 个","plan_total":3,"plan_collected":2,"plan_completeness":0.6666666666666666,"environment_evidence_total":8,"environment_evidence_collected":7,"environment_evidence_completeness":0.875,"executed_tool_count":7,"matched_tool_count":2,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"验证 Pod 的 nodeSelector 是否与集群中任何节点的标签匹配","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"检查 Pod 的 nodeSelector 配置，确认其设置的标签是否存在于任何节点上","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"检查集群中所有节点的标签","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o json","purpose":"获取所有节点的标签信息，确认是否存在与 Pod 的 nodeSelector 匹配的标签","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取 Pod 的调度失败事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-pending-nodeselector","purpose":"查看 Pod 的调度失败事件，确认调度失败的具体原因","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":["e3(获取 Pod 的调度失败事件): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/3 项, 完整度: 88%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_yaml | 验证 Pod 的 nodeSelector 是否与集群中任何节点的标签匹配 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e2 | critical | ✅ | kubectl_get_by_kind_in_cl... | 检查集群中所有节点的标签 | `kubectl get nodes -o json` |
   | e3 | important | ❌ | kubectl_events | 获取 Pod 的调度失败事件 | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-pendi...` |

   ⚠️ 未采集原因:
   - e3(获取 Pod 的调度失败事件): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 48.2s)
   📤 → 下游数据: root_cause=Pod rc-pending-nodeselector 的 nodeSelector 设置了不存在的标签 'aiops.e2.e2e/nonexistent-node-label'，而集群中的节点均未标记此标签。因此，调度器无法找到符合条件的节点来运行该 Pod。
   confidence=95%
   causal_chain={"root_cause": "Pod rc-pending-nodeselector 的 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label'，而集群中的节点均未标记此标签。", "intermediate_causes": ["Pod 的 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label'。", "集群中的节点均未标记 'aiops.e2e/nonexistent-node-label'。"], "immediate_causes": ["Pod 的 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label'，导致调度失败。"]}
   rca_analysis={"phenomenon": "Pod rc-pending-nodeselector 处于 Pending 状态，并且 Events 显示调度失败原因是 'node(s) didn't match Pod's node affinity/selector'。", "evidence_inventory": [{"id": "e1", "description": "验证 Pod 的 nodeSelector 是否与集群中任何节点的标签匹配", "level": "critical", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSe"}, {"id": "e2", "description": "检查集群中所有节点的标签", "level": "critical", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubern"}, {"id": "layer_2", "description": "上游已验证工具结果: kubectl_describe", "level": "important", "value": "kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  31m                default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  16m (x3 over 26m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 node"}, {"id": "layer_5", "description": "上游已验证工具结果: kubectl_get_yaml", "level": "important", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSe"}], "evidence_analysis": [{"id": "e1", "description": "验证 Pod 的 nodeSelector 是否与集群中任何节点的标签匹配", "level": "critical", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSe"}, {"id": "e2", "description": "检查集群中所有节点的标签", "level": "critical", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubern"}, {"id": "layer_2", "description": "上游已验证工具结果: kubectl_describe", "level": "important", "value": "kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  31m                default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  16m (x3 over 26m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 node"}, {"id": "layer_5", "description": "上游已验证工具结果: kubectl_get_yaml", "level": "important", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSe"}], "causal_chain": {"root_cause": "Pod rc-pending-nodeselector 的 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label'，而集群中的节点均未标记此标签。", "intermediate_causes": ["Pod 的 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label'。", "集群中的节点均未标记 'aiops.e2e/nonexistent-node-label'。"], "immediate_causes": ["Pod 的 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label'，导致调度失败。"]}, "root_cause": "Pod rc-pending-nodeselector 的 nodeSelector 设置了不存在的标签 'aiops.e2.e2e/nonexistent-node-label'，而集群中的节点均未标记此标签。因此，调度器无法找到符合条件的节点来运行该 Pod。", "root_cause_summary": "Pod rc-pending-nodeselector 的 nodeSelector 设置了不存在的标签 'aiops.e2.e2e/nonexistent-node-label'，而集群中的节点均未标记此标签。因此，调度器无法找到符合条件的节点来运行该 Pod。", "confidence": 0.95, "confidence_reason": "直接证据表明 Pod 的 nodeSelector 设置了不存在的标签，并且集群中的节点均未标记此标签，导致调度失败。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [], "limitations": "缺失证据 '获取 Pod 的调度失败事件' 可能影响对调度失败事件的进一步分析。", "llm_raw_analysis": "基于已采集的证据，可以确定 Pod rc-pending-nodeselector 的 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label'，而集群中的节点均未标记此标签。这导致调度器无法找到符合条件的节点来运行该 Pod，因此 Pod 处于 Pending 状态。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-nodeselector 的 nodeSelector 设置了不存在的标签 'aiops.e2.e2e/nonexistent-node-label'，而集群中的节点均未标记此标签。因此，调度器无法找到符合条件的节点来运行该 Pod。
   置信度: 95%
   🔗 因果链:
     根本原因: Pod rc-pending-nodeselector 的 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label'，而集群中的节点均未标记此标签。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 26.1s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3938 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 28.2s
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
| **兼容归因层** | L1 - 调度失败 |
| **问题分类** | nodeSelector 不匹配节点标签 |
| **置信度** | 高 (95%) |
| **证据完整度** | 2/3 (67%) |

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
| 1 | Pod YAML 配置 | kubectl get pod rc-pending-nodeselector -o yaml | `nodeSelector: aiops.e2e/nonexistent-node-label: "true"` | Pod 设置了不存在的 nodeSelector 标签 |
| 2 | 节点标签检查 | kubectl get nodes --show-labels | 节点 `master`、`node1`、`node2` 均未设置 `aiops.e2e/nonexistent-node-label` 标签 | 无节点满足 Pod 的 nodeSelector |
| 3 | Pod 事件信息 | kubectl describe pod rc-pending-nodeselector | `Warning  FailedScheduling  31m                default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 明确指出调度失败原因 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 设置了 `nodeSelector: aiops.e2e/nonexistent-node-label`，但所有节点均未设置该标签 → 调度器无法匹配任何节点
- **证据链**：Pod 配置 nodeSelector → 节点无匹配标签 → 调度器无法找到可用节点 → Pod 状态为 Pending

### 缺失证据

| 证据 | 级别 | 影响 |
|------|------|------|
| 调度失败事件详细日志 | important | 无法深入分析调度失败的上下文信息 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod 的 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label'，而集群中的节点均未标记此标签。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 调度器尝试匹配 nodeSelector，但找不到任何节点满足条件            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 调度失败，事件显示 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 Pending，Events 显示调度失败                        │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1（Pod 设置了 `nodeSelector: aiops.e2e/nonexistent-node-label`）和证据 #2（节点未设置该标签），问题的根本原因是 **Pod 的 nodeSelector 设置了不存在的标签**，导致调度器无法找到符合条件的节点来运行该 Pod。

**置信度**：高 (95%)
- ✅ `kubectl describe pod` 明确指出调度失败原因
- ✅ `kubectl get pod -o yaml` 显示 nodeSelector 设置了不存在的标签
- ⚠️ 缺失调度失败事件的详细日志

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 删除或修改 Pod 的 nodeSelector 配置**
```bash
kubectl edit pod rc-pending-nodeselector -n aiops-e2e
```
*操作*：删除或修改 `nodeSelector` 字段，例如将其设置为集群中实际存在的节点标签（如 `kubernetes.io/role=worker`）  
*依据*：当前设置的标签不存在，导致调度失败

**2. [可选] 查看 Pod 的调度失败事件详细日志**
```bash
kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-pending-nodeselector
```
*目的*：进一步确认调度失败的上下文信息

### 后续优化

1. **标签管理**：确保集群节点上存在常用标签，并与 Pod 的调度策略匹配
2. **Pod 模板校验**：在部署前检查 Pod 的 nodeSelector、affinity、taint 等配置是否合理
3. **调度器策略优化**：考虑使用 Node Affinity、Tolerations 等更灵活的调度策略

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running |
| 2. 检查调度事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | 无 FailedScheduling 事件 |
| 3. 检查节点标签 | `kubectl get nodes --show-labels` | 确认节点上有新配置的 nodeSelector 标签（如 `kubernetes.io/role=worker`） |

---

## ⚠️ 注意事项

- 如果 nodeSelector 是必需的，确保所有目标节点已正确打标签
- 若集群中节点标签管理混乱，建议统一标签策略并使用 Helm/Operator 管理标签一致性
- 考虑使用 Node Affinity 替代 nodeSelector，以实现更灵活的调度逻辑

---

## 📊 性能统计

├─ 总耗时: 5.5m
├─ 问题定位: 64.0s (20%) ✅
├─ 证据链采集: 69.9s (21%) ✅
├─ 根因分析: 108.2s (33%) ✅
├─ 汇总总结: 86.1s (26%) ✅
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
