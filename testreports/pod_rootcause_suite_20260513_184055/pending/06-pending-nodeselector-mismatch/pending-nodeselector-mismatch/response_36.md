======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 45b0d9849d234542]

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
  Warning  FailedScheduling  13m (x15 over 83m)  default-scheduler  0/3 nodes are available:
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
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Pending': 1, 'Running': 46}
NAMESPACE     NAME                                                READY   STATUS      RESTARTS      
   💭 [问题定位] {
  "layer": "L1",
  "derived_layer": "L1",
  "layers": [
    "L1"
  ],
  "layer_name": "PendingUnschedulable",
  "confidence": 0.95,
  "reasoning": "Pod 'rc-pending-nodeselector' 处于 Pending 状态，且事件显示 'FailedScheduling'，原因是 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。进一步检查发现 Pod 的 nodeSelector 指定了不存在的标签 'aiops.e2e/nonexistent-node-label'，而所有节点均未配置此标签，导致调度失败。",
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
      "type": "PendingUnschedulable",
      "count": 1,
      "reasons": [
        "nodeSelector 不匹配"
      ]
    }
  ],
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "PendingUnschedulable",
  "status_category": "调度失败",
  "key_entities": [
    "rc-pending-nodeselector",
    "aiops-e2e",
    "nodeSelector",
    "aiops.e2e/nonexistent-node-label"
  ],
  "possible_scenarios": [
    "Pod 的 nodeSelector 指定了不存在的标签，导致无法调度。",
    "集群中所有节点均未配置该标签，导致调度失败。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (57.3s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'Pod 的 nodeSelector 指定了不存在的标签，导致无法调度。', 'probability': '高', 'reason': "事件显示 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'"}, {'scenario': '集群中所有节点均未配置该标签，导致调度失败。', 'probability': '高', 'reason': "nodeSelector 指定的标签 'aiops.e2e/nonexistent-node-label' 不存在于所有节点的标签列表中。"}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Label", "name": "aiops.e2e/nonexistent-node-label", "namespace": ""}]
   reasoning=Pod 'rc-pending-nodeselector' 处于 Pending 状态，且事件显示 'FailedScheduling'，原因是 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。进一步检查发现 Pod 的 nodeSelector 指定了不存在的标签 'aiops.e2e/nonexistent-node-label'，而所有节点均未配置此标签，导致调度失败。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "Pod 'rc-pending-nodeselector' 处于 Pending 状态，且事件显示 'FailedScheduling'，原因是 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。进一步检查发现 Pod 的 nodeSelector 指定了不存在的标签 'aiops.e2e/nonexistent-node-label'，而所有节点均未配置此标签，导致调度失败。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "调度失败", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Label", "name": "aiops.e2e/nonexistent-node-label", "namespace": ""}], "possible_scenarios": [{"scenario": "Pod 的 nodeSelector 指定了不存在的标签，导致无法调度。", "probability": "高", "reason": "事件显示 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'"}, {"scenario": "集群中所有节点均未配置该标签，导致调度失败。", "probability": "高", "reason": "nodeSelector 指定的标签 'aiops.e2e/nonexistent-node-label' 不存在于所有节点的标签列表中。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                88m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/45b0d9849d234542/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/45b0d9849d234542/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/45b0d9849d234542/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
15m (x15 over 85m)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 
   💭 [证据链采集] # 证据结论

## 已采集证据
1. **Pod `rc-pending-nodeselector` 的 YAML 配置**：
   - nodeSelector 指定了标签 `aiops.e2e/nonexistent-node-label=true`。
   - 当前状态为 `Pending`，且调度失败的原因是 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`。

2. **集群中所有节点的标签信息**：
   - 所有节点（`master`、`node1`、`node2`）均未配置标签 `aiops.e2e/nonexistent-node-label`。

3. **Pod `rc-pending-nodeselector` 的事件记录**：
   - 显示调度失败的具体原因：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`。

## 未采集证据
- 无。

## 冲突证据
- 无。

## 分析总结
Pod `rc-pending-nodeselector` 无法调度的根本原因是其 `nodeSelector` 指定了一个不存在的标签 `aiops.e2e/nonexistent-node-label`，而集群中所有节点均未配置该标签。因此，调度器找不到匹配的节点来运行该 Pod，导致其一直处于 `Pending` 状态。
   ✅ [证据链采集] 完成 (1m 30.1s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod 'rc-pending-nodeselector' 的 nodeSelector 是否与集群节点标签不匹配","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"namespace":"aiops-e2e","name":"rc-pending-nodeselector","kind":"Pod"},"purpose":"确认 Pod 的 nodeSelector 是否指定了不存在的标签","evidence_type":"configuration","target_scope":"aiops-e2e/rc-pending-nodeselector","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"验证集群节点是否配置了 Pod 'rc-pending-nodeselector' 所需的标签","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o wide","tool_args":{},"purpose":"确认所有节点的标签是否包含 'aiops.e2e/nonexistent-node-label'","evidence_type":"node_configuration","target_scope":"nodes","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"验证 Pod 'rc-pending-nodeselector' 的 FailedScheduling 事件详情","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-pending-nodeselector","tool_args":{"namespace":"aiops-e2e","pod_name":"rc-pending-nodeselector"},"purpose":"确认调度失败的具体原因","evidence_type":"event_logs","target_scope":"aiops-e2e/rc-pending-nodeselector","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-fsdjk\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/45b0d9849d234542/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/45b0d9849d234542/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/45b0d9849d234542/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/45b0d9849d234542/tools/002-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/45b0d9849d234542/tools/002-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/45b0d9849d234542/tools/002-evidence-kubectl_get_by_kind_in_cluster.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n15m (x15 over 85m)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/45b0d9849d234542/tools/003-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/45b0d9849d234542/tools/003-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/45b0d9849d234542/tools/003-evidence-kubectl_events.summary.txt"}],"llm_analysis":"# 证据结论\n\n## 已采集证据\n1. **Pod `rc-pending-nodeselector` 的 YAML 配置**：\n   - nodeSelector 指定了标签 `aiops.e2e/nonexistent-node-label=true`。\n   - 当前状态为 `Pending`，且调度失败的原因是 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`。\n\n2. **集群中所有节点的标签信息**：\n   - 所有节点（`master`、`node1`、`node2`）均未配置标签 `aiops.e2e/nonexistent-node-label`。\n\n3. **Pod `rc-pending-nodeselector` 的事件记录**：\n   - 显示调度失败的具体原因：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`。\n\n## 未采集证据\n- 无。\n\n## 冲突证据\n- 无。\n\n## 分析总结\nPod `rc-pending-nodeselector` 无法调度的根本原因是其 `nodeSelector` 指定了一个不存在的标签 `aiops.e2e/nonexistent-node-label`，而集群中所有节点均未配置该标签。因此，调度器找不到匹配的节点来运行该 Pod，导致其一直处于 `Pending` 状态。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 8 个，匹配计划 3 个，未规划证据 5 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":3,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"验证 Pod 'rc-pending-nodeselector' 的 nodeSelector 是否与集群节点标签不匹配","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"确认 Pod 的 nodeSelector 是否指定了不存在的标签","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"验证集群节点是否配置了 Pod 'rc-pending-nodeselector' 所需的标签","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o wide","purpose":"确认所有节点的标签是否包含 'aiops.e2e/nonexistent-node-label'","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"验证 Pod 'rc-pending-nodeselector' 的 FailedScheduling 事件详情","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-pending-nodeselector","purpose":"确认调度失败的具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_yaml | 验证 Pod 'rc-pending-nodeselector' 的 nodeSelect... | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e2 | critical | ✅ | kubectl_get_by_kind_in_cl... | 验证集群节点是否配置了 Pod 'rc-pending-nodeselector' 所需的标签 | `kubectl get nodes -o wide` |
   | e3 | important | ✅ | kubectl_events | 验证 Pod 'rc-pending-nodeselector' 的 FailedSche... | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-pendi...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 14.0s)
   📤 → 下游数据: root_cause=Pod 'rc-pending-nodeselector' 无法调度的根本原因是其 nodeSelector 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label'，而集群中所有节点均未配置该标签。因此，调度器找不到匹配的节点来运行该 Pod，导致其一直处于 Pending 状态。
   confidence=95%
   causal_chain={"root_cause": "Pod 'rc-pending-nodeselector' 的 nodeSelector 指定了不存在的标签 'aiops.e2e/nonexistent-node-label'，导致调度失败。", "intermediate_causes": ["调度器无法找到匹配 'aiops.e2e/nonexistent-node-label' 标签的节点", "集群中所有节点均未配置 'aiops.e2e/nonexistent-node-label' 标签"], "immediate_causes": ["Pod 的 nodeSelector 指定了不存在的标签", "事件记录显示 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'"], "symptoms": ["Pod 'rc-pending-nodeselector' 处于 Pending 状态", "调度失败的事件记录"]}
   rca_analysis={"phenomenon": "Pod 'rc-pending-nodeselector' 处于 Pending 状态，调度失败", "evidence_inventory": [{"description": "Pod 'rc-pending-nodeselector' 的 YAML 配置", "value": "nodeSelector 指定了标签 'aiops.e2e/nonexistent-node-label=true'，当前状态为 Pending，调度失败的原因是 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。"}, {"description": "集群中所有节点的标签信息", "value": "所有节点（master、node1、node2）均未配置标签 'aiops.e2e/nonexistent-node-label'。"}, {"description": "Pod 'rc-pending-nodeselector' 的事件记录", "value": "显示调度失败的具体原因：'0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。"}], "evidence_analysis": [{"description": "Pod 'rc-pending-nodeselector' 的 YAML 配置", "value": "Pod 的 nodeSelector 指定了不存在的标签 'aiops.e2e/nonexistent-node-label'，导致调度失败。"}, {"description": "集群中所有节点的标签信息", "value": "所有节点均未配置 'aiops.e2e/nonexistent-node-label'，导致调度器无法找到匹配的节点。"}, {"description": "Pod 'rc-pending-nodeselector' 的事件记录", "value": "事件记录确认了调度失败的具体原因，与 nodeSelector 不匹配的标签有关。"}], "causal_chain": {"root_cause": "Pod 'rc-pending-nodeselector' 的 nodeSelector 指定了不存在的标签 'aiops.e2e/nonexistent-node-label'，导致调度失败。", "intermediate_causes": ["调度器无法找到匹配 'aiops.e2e/nonexistent-node-label' 标签的节点", "集群中所有节点均未配置 'aiops.e2e/nonexistent-node-label' 标签"], "immediate_causes": ["Pod 的 nodeSelector 指定了不存在的标签", "事件记录显示 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'"], "symptoms": ["Pod 'rc-pending-nodeselector' 处于 Pending 状态", "调度失败的事件记录"]}, "root_cause": "Pod 'rc-pending-nodeselector' 无法调度的根本原因是其 nodeSelector 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label'，而集群中所有节点均未配置该标签。因此，调度器找不到匹配的节点来运行该 Pod，导致其一直处于 Pending 状态。", "root_cause_summary": "Pod 'rc-pending-nodeselector' 无法调度的根本原因是其 nodeSelector 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label'，而集群中所有节点均未配置该标签。因此，调度器找不到匹配的节点来运行该 Pod，导致其一直处于 Pending 状态。", "confidence": 0.95, "confidence_reason": "有直接证据表明 Pod 的 nodeSelector 指定了不存在的标签，且事件记录和节点标签信息均支持此结论。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [], "limitations": "无", "llm_raw_analysis": "分析总结：\n\nPod 'rc-pending-nodeselector' 无法调度的根本原因是其 'nodeSelector' 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label'，而集群中所有节点均未配置该标签。因此，调度器找不到匹配的节点来运行该 Pod，导致其一直处于 'Pending' 状态。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'rc-pending-nodeselector' 无法调度的根本原因是其 nodeSelector 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label'，而集群中所有节点均未配置该标签。因此，调度器找不到匹配的节点来运行该 Pod，导致其一直处于 P...
   置信度: 95%
   🔗 因果链:
     根本原因: Pod 'rc-pending-nodeselector' 的 nodeSelector 指定了不存在的标签 'aiops.e2e/nonexistent-node-label'，导致调度失败。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 16.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3851 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 57.4s
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
| **兼容归因层** | L1 |
| **问题分类** | 调度失败 |
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
| Node | <none> |
| 错误信息 | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` |

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: Pending, REASON: FailedScheduling` | Pod 无法调度，处于 Pending 状态 |
| 2 | Pod 的 nodeSelector | `kubectl get pod -o yaml` | `nodeSelector: aiops.e2e/nonexistent-node-label` | Pod 指定了不存在的标签 |
| 3 | 节点标签 | `kubectl get node` | 节点未配置标签 `aiops.e2e/nonexistent-node-label` | 无匹配节点，调度失败 |
| 4 | FailedScheduling 事件 | `kubectl describe pod` | `Warning  FailedScheduling  13m (x15 over 83m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 事件明确表明调度失败原因 |

### 证据关联分析
- **证据 #1 + #2 印证**：Pod 状态为 Pending，且 nodeSelector 指定了不存在的标签 → 调度失败
- **证据 #3 印证**：集群节点未配置该标签 → 调度器无法找到匹配节点
- **证据 #4 印证**：事件日志明确显示调度失败的详细原因

### 缺失证据（无）
| 证据 | 级别 | 影响 |
|------|------|------|
| 无 | 无 | 无 |

---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod 的 nodeSelector 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label'，导致调度失败。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 调度器尝试匹配 nodeSelector，但所有节点均无此标签 → 无可用节点。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Pod 被标记为 'PendingUnschedulable'，且事件显示 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 Pending，且持续显示 'FailedScheduling' 事件。        │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (Pod 状态为 Pending)、证据 #2 (nodeSelector 指定的标签不存在) 和证据 #3 (节点未配置该标签)，问题的根本原因是 **Pod `rc-pending-nodeselector` 的 nodeSelector 指定了一个不存在的标签 `aiops.e2e/nonexistent-node-label`**，导致调度器无法找到匹配的节点，从而调度失败。
**置信度**：高 (95%)
- ✅ Pod 状态为 Pending
- ✅ nodeSelector 指定了不存在的标签
- ✅ 节点未配置该标签
- ✅ 事件日志明确显示调度失败原因

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 移除或修改 Pod 的 nodeSelector**
```bash
kubectl edit pod rc-pending-nodeselector -n aiops-e2e
```
*操作步骤*：
1. 打开 `nodeSelector` 字段
2. 删除或修改为集群中实际存在的标签
3. 保存并退出

**2. [可选] 在节点上添加对应标签（如果标签是合理需求）**
```bash
kubectl label nodes <node-name> aiops.e2e/nonexistent-node-label=enabled
```
*目的*：如果 `aiops.e2e/nonexistent-node-label` 是必要的调度标签，则添加该标签至节点以允许 Pod 调度。

### 后续优化
1. **验证调度标签一致性**：确保所有 Pod 的 nodeSelector、nodeAffinity 与节点标签匹配。
2. **监控调度失败事件**：配置事件告警，及时发现调度失败。
3. **文档化调度标签策略**：明确哪些标签可用于调度，避免误配置。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 被调度 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running |
| 2. 检查事件日志 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | 无 `FailedScheduling` 事件 |
| 3. 检查 nodeSelector | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o jsonpath='{.spec.nodeSelector}'` | 输出应为空或合法标签 |

---
## ⚠️ 注意事项
- 如果 nodeSelector 是必要的调度策略，请确保标签在节点上存在。
- 如果多个 Pod 使用相同标签，建议统一管理调度标签以避免冲突。
- 调度失败事件可能会影响整体集群稳定性，建议及时处理。

---

## 📊 性能统计

├─ 总耗时: 5.0m
├─ 问题定位: 57.3s (19%) ✅
├─ 证据链采集: 90.1s (30%) ✅
├─ 根因分析: 74.0s (25%) ✅
├─ 汇总总结: 76.0s (26%) ✅
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
