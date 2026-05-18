======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: b533e3f202ca4f2b]

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
  Warning  FailedScheduling  33m (x9 over 73m)  default-scheduler  0/3 nodes are available: 
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
  "reasoning": "Pod 'rc-pending-nodeselector' 在命名空间 'aiops-e2e' 中处于 Pending 状态，调度失败原因为 'node(s) didn't match Pod's node affinity/selector'。Pod 的 nodeSelector 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label=true'，而集群中的所有节点 (master, node1, node2) 都没有这个标签。节点状态正常 (Ready)，但无法满足调度条件，因此归类为 L1 (调度失败)。需要调整 Pod 的 nodeSelector 或节点标签以解决此问题。",
  "abnormal_pods": [
    {
      "name": "rc-pending-nodeselector",
      "namespace": "aiops-e2e",
      "status": "Pending",
      "key_events": [
        {
          "type": "Warning",
          "message": "FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector."
        }
      ],
      "pod_abnormal_type": "PendingUnschedulable"
    }
  ],
  "abnormal_groups": [
    {
      "type": "PendingUnschedulable",
      "count": 1
    }
  ],
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "PendingUnschedulable",
  "status_category": "Scheduling",
  "key_entities": [
    "Pod: rc-pending-nodeselector (aiops-e2e)",
    "NodeSelector: aiops.e2e/nonexistent-node-label=true",
    "Nodes: master, node1, node2 (all Ready)"
  ],
  "possible_scenarios": [
    "Pod 指定了不存在的 nodeSelector，导致无节点可调度",
    "集群节点缺少必要的标签以匹配 Pod 的调度要求",
    "需要检查 nodeSelector 的正确性或调整节点标签"
  ]
}
   ✅ [问题定位] 完成 (1m 1.1s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[]
   entities=[]
   reasoning=Pod 'rc-pending-nodeselector' 在命名空间 'aiops-e2e' 中处于 Pending 状态，调度失败原因为 'node(s) didn't match Pod's node affinity/selector'。Pod 的 nodeSelector 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label=true'，而集群中的所有节点 (master, node1, node2) 都没有这个标签。节点状态正常 (Ready)，但无法满足调度条件，因此归类为 L1 (调度失败)。需要调整 Pod 的 nodeSelector 或节点标签以解决此问题。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "Pod 'rc-pending-nodeselector' 在命名空间 'aiops-e2e' 中处于 Pending 状态，调度失败原因为 'node(s) didn't match Pod's node affinity/selector'。Pod 的 nodeSelector 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label=true'，而集群中的所有节点 (master, node1, node2) 都没有这个标签。节点状态正常 (Ready)，但无法满足调度条件，因此归类为 L1 (调度失败)。需要调整 Pod 的 nodeSelector 或节点标签以解决此问题。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "Scheduling", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                78m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/b533e3f202ca4f2b/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/b533e3f202ca4f2b/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/b533e3f202ca4f2b/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 输出摘要: raw_chars=145 lines=4
Command failed (exit 1):
kubectl get --show-labels -o wide node -n 
error: flag needs an argument: 'n' in -n
See 'kubectl get --help' for u
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 输出摘要: raw_chars=145 lines=4
Command failed (exit 1):
kubectl get --show-labels -o wide node -n 
error: flag needs an argument: 'n' in -n
See 'kubectl get --help' for u
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
5m39s (x15 over 75m)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/
   💭 [证据链采集] 已采集证据：
1. **Pod spec 配置**：通过 `kubectl_get_yaml` 确认 Pod 指定了 `nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}`。
2. **调度失败事件**：通过 `kubectl_events` 确认调度失败原因为 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`。
3. **节点标签验证失败**：尝试获取节点标签的命令失败（因 `-n` 参数错误），但结合上下文，可推断节点未标记 `aiops.e2e/nonexistent-node-label=true`。

结论：Pod 无法调度的根本原因是其 `nodeSelector` 指定了一个不存在的节点标签，导致调度器找不到匹配的节点。需要调整 Pod 的 `nodeSelector` 或在集群节点上添加相应的标签。
   ✅ [证据链采集] 完成 (1m 31.5s)
   📤 → 下游数据: evidence_items=7/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod 'rc-pending-nodeselector' 的调度失败原因，检查 nodeSelector 是否匹配集群节点标签","level":"critical","tool":"kubectl_get_yaml","command":"get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"确认 Pod spec 中的 nodeSelector 是否匹配集群节点的标签","evidence_type":"config","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"检查集群节点的标签，确认是否缺少 'aiops.e2e/nonexistent-node-label=true'","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"get nodes -o jsonpath='{.items[*].metadata.labels}'","tool_args":{"kind":"Node","namespace":""},"purpose":"确认节点是否拥有 Pod 所需的标签 'aiops.e2e/nonexistent-node-label=true'","evidence_type":"config","target_scope":"Node","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取 Pod 'rc-pending-nodeselector' 的调度事件，确认调度失败的具体原因","level":"critical","tool":"kubectl_events","command":"get events -n aiops-e2e --field-selector=involvedObject.name=rc-pending-nodeselector","tool_args":{"namespace":"aiops-e2e","selector":"involvedObject.name=rc-pending-nodeselector"},"purpose":"确认调度失败事件的具体原因，例如 'node(s) didn't match Pod's node affinity/selector'","evidence_type":"event","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-fsdjk\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b533e3f202ca4f2b/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b533e3f202ca4f2b/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b533e3f202ca4f2b/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"kubectl_get_by_kind_in_namespace 输出摘要: raw_chars=145 lines=4\nCommand failed (exit 1):\nkubectl get --show-labels -o wide node -n \nerror: flag needs an argument: 'n' in -n\nSee 'kubectl get --help' for usage.","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/b533e3f202ca4f2b/tools/002-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b533e3f202ca4f2b/tools/002-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b533e3f202ca4f2b/tools/002-evidence-kubectl_get_by_kind_in_namespace.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"kubectl_get_by_kind_in_namespace 输出摘要: raw_chars=145 lines=4\nCommand failed (exit 1):\nkubectl get --show-labels -o wide node -n \nerror: flag needs an argument: 'n' in -n\nSee 'kubectl get --help' for usage.","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/b533e3f202ca4f2b/tools/003-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b533e3f202ca4f2b/tools/003-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b533e3f202ca4f2b/tools/003-evidence-kubectl_get_by_kind_in_namespace.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n5m39s (x15 over 75m)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b533e3f202ca4f2b/tools/004-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b533e3f202ca4f2b/tools/004-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b533e3f202ca4f2b/tools/004-evidence-kubectl_events.summary.txt"}],"llm_analysis":"已采集证据：\n1. **Pod spec 配置**：通过 `kubectl_get_yaml` 确认 Pod 指定了 `nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}`。\n2. **调度失败事件**：通过 `kubectl_events` 确认调度失败原因为 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`。\n3. **节点标签验证失败**：尝试获取节点标签的命令失败（因 `-n` 参数错误），但结合上下文，可推断节点未标记 `aiops.e2e/nonexistent-node-label=true`。\n\n结论：Pod 无法调度的根本原因是其 `nodeSelector` 指定了一个不存在的节点标签，导致调度器找不到匹配的节点。需要调整 Pod 的 `nodeSelector` 或在集群节点上添加相应的标签。","collection_summary":"计划 3 项，实际采集 2 项，未采集 1 项，完整度 67%；其中真实环境证据 7/8 项，完整度 88%；实际执行工具 7 个，匹配计划 2 个，未规划证据 5 个","plan_total":3,"plan_collected":2,"plan_completeness":0.6666666666666666,"environment_evidence_total":8,"environment_evidence_collected":7,"environment_evidence_completeness":0.875,"executed_tool_count":7,"matched_tool_count":2,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"验证 Pod 'rc-pending-nodeselector' 的调度失败原因，检查 nodeSelector 是否匹配集群节点标签","level":"critical","tool":"kubectl_get_yaml","command":"get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"确认 Pod spec 中的 nodeSelector 是否匹配集群节点的标签","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"检查集群节点的标签，确认是否缺少 'aiops.e2e/nonexistent-node-label=true'","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"get nodes -o jsonpath='{.items[*].metadata.labels}'","purpose":"确认节点是否拥有 Pod 所需的标签 'aiops.e2e/nonexistent-node-label=true'","collected":false,"source":"planned","outcome":"unknown"},{"id":"e3","description":"获取 Pod 'rc-pending-nodeselector' 的调度事件，确认调度失败的具体原因","level":"critical","tool":"kubectl_events","command":"get events -n aiops-e2e --field-selector=involvedObject.name=rc-pending-nodeselector","purpose":"确认调度失败事件的具体原因，例如 'node(s) didn't match Pod's node affinity/selector'","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e2(检查集群节点的标签，确认是否缺少 'aiops.e2e/nonexistent-node-label=true'): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/3 项, 完整度: 88%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_yaml | 验证 Pod 'rc-pending-nodeselector' 的调度失败原因，检查 n... | `get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e2 | important | ❌ | kubectl_get_by_kind_in_na... | 检查集群节点的标签，确认是否缺少 'aiops.e2e/nonexistent-node-... | `get nodes -o jsonpath='{.items[*].metadata.labels}'` |
   | e3 | critical | ✅ | kubectl_events | 获取 Pod 'rc-pending-nodeselector' 的调度事件，确认调度失败... | `get events -n aiops-e2e --field-selector=involvedObject.name=rc-pending-nodes...` |

   ⚠️ 未采集原因:
   - e2(检查集群节点的标签，确认是否缺少 'aiops.e2e/nonexistent-node-label=true'): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 24.8s)
   📤 → 下游数据: root_cause=Pod 'rc-pending-nodeselector' in namespace 'aiops-e2e' is in Pending state because its nodeSelector specifies a non-existent label 'aiops.e2e/nonexistent-node-label=true', and none of the cluster nodes (master, node1, node2) have this label.
   confidence=95%
   causal_chain={"root_cause": "Pod 'rc-pending-nodeselector' in namespace 'aiops-e2e' is in Pending state because its nodeSelector specifies a non-existent label 'aiops.e2e/nonexistent-node-label=true', and none of the cluster nodes (master, node1, node2) have this label.", "intermediate_causes": ["The Pod's nodeSelector specifies a non-existent label 'aiops.e2e/nonexistent-node-label=true'.", "None of the cluster nodes have the label 'aiops.e2e/nonexistent-node-label=true'."], "immediate_causes": ["The scheduling failure event '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector' indicates that the Pod cannot be scheduled on any of the available nodes."], "effects": ["Pod 'rc-pending-nodeselector' is in Pending state and cannot be scheduled on any of the available nodes."]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"phenomenon": "Pod 'rc-pending-nodeselector' in namespace 'aiops-e2e' is in Pending state, scheduling failed due to 'node(s) didn't match Pod's node affinity/selector'. The Pod's nodeSelector specified a non-existent label 'aiops.e2e/nonexistent-node-label=true', and none of the cluster nodes (master, node1, node2) have this label. Node status is normal (Ready), but scheduling conditions are not met, thus categorized as L1 (scheduling failure)."}, {"phenomenon": "Pod 'rc-pending-nodeselector' in namespace 'aiops-e2e' is in Pending state, scheduling failed due to 'node(s) didn't match Pod's node affinity/selector'. The Pod's nodeSelector specified a non-existent label 'aiops.e2e/nonexistent-node-label=true', and none of the cluster nodes (master, node1, node2) have this label. Node status is normal (Ready), but scheduling conditions are not met, thus categorized as L1 (scheduling failure)."}], "evidence_analysis": [{"evidence": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSe", "analysis": "The Pod 'rc-pending-nodeselector' in namespace 'aiops-e2e' is in Pending state with a nodeSelector that specifies a non-existent label 'aiops.e2e/nonexistent-node-label=true'. This is confirmed by the 'kubectl_get_yaml' output."}, {"evidence": "kubectl_events 摘要:\n关键诊断行:\n5m39s (x15 over 75m)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..", "analysis": "The scheduling failure is confirmed by the 'kubectl_events' output, which shows that the Pod 'rc-pending-nodeselector' is unable to be scheduled because none of the nodes in the cluster have the required label 'aiops.e2e/nonexistent-node-label=true'."}], "causal_chain": {"root_cause": "Pod 'rc-pending-nodeselector' in namespace 'aiops-e2e' is in Pending state because its nodeSelector specifies a non-existent label 'aiops.e2e/nonexistent-node-label=true', and none of the cluster nodes (master, node1, node2) have this label.", "intermediate_causes": ["The Pod's nodeSelector specifies a non-existent label 'aiops.e2e/nonexistent-node-label=true'.", "None of the cluster nodes have the label 'aiops.e2e/nonexistent-node-label=true'."], "immediate_causes": ["The scheduling failure event '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector' indicates that the Pod cannot be scheduled on any of the available nodes."], "effects": ["Pod 'rc-pending-nodeselector' is in Pending state and cannot be scheduled on any of the available nodes."]}, "root_cause": "Pod 'rc-pending-nodeselector' in namespace 'aiops-e2e' is in Pending state because its nodeSelector specifies a non-existent label 'aiops.e2e/nonexistent-node-label=true', and none of the cluster nodes (master, node1, node2) have this label.", "root_cause_summary": "Pod 'rc-pending-nodeselector' in namespace 'aiops-e2e' is in Pending state because its nodeSelector specifies a non-existent label 'aiops.e2e/nonexistent-node-label=true', and none of the cluster nodes (master, node1, node2) have this label.", "confidence": 0.95, "confidence_reason": "", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [], "limitations": "The evidence for the node labels is not directly available, but it can be inferred from the scheduling failure event and the Pod's nodeSelector configuration.", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'rc-pending-nodeselector' in namespace 'aiops-e2e' is in Pending state because its nodeSelector specifies a non-existent label 'aiops.e2e/nonexist...
   置信度: 95%
   🔗 因果链:
     根本原因: Pod 'rc-pending-nodeselector' in namespace 'aiops-e2e' is in Pending state because its nodeSelector specifies a non-existent label 'aiops.e2e/nonexistent-node-label=true', and none of the cluster nodes (master, node1, node2) have this label.


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 37.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4167 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 34.9s
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
| **问题分类** | 调度约束不匹配（nodeSelector 不匹配） |
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
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: Pending, REASON: nodeSelector 不匹配` | Pod 无法调度，处于 Pending 状态 |
| 2 | 调度事件 | `kubectl describe pod` | `Warning FailedScheduling 33m (x9 over 73m) default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 明确指出 nodeSelector 不匹配 |
| 3 | Pod spec | `kubectl get pod -o yaml` | `nodeSelector: aiops.e2e/nonexistent-node-label=true` | Pod 指定了一个不存在的标签 |
| 4 | 节点状态 | `kubectl get node` | `master, node1, node2 都为 Ready` | 节点状态正常，但无匹配标签 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 Pending，调度失败事件明确指出 nodeSelector 不匹配。
- **证据 #3 + #4 印证**：Pod 的 nodeSelector 指定了一个不存在的标签，而所有节点都没有该标签，导致调度失败。

### 缺失证据

| 证据 | 级别 | 影响 |
|------|------|------|
| 集群节点的完整标签列表 | important | 无法确认是否存在其他节点具有所需标签 |

---

## 🎯 根因分析

### 因果链

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                    │
│ Pod 'rc-pending-nodeselector' 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label=true'，而集群中所有节点均无该标签，导致调度失败。 │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                    │
│ Pod 的 nodeSelector 与节点标签不匹配 → 调度器无法找到匹配的节点 → Pod 保持 Pending 状态。 │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                    │
│ 调度失败事件 `FailedScheduling` 明确指出 0/3 节点匹配 nodeSelector 条件。      │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                │
│ Pod 状态为 Pending，且无法被调度。                                            │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Pod 状态为 Pending)、证据 #2 (调度失败事件)、证据 #3 (nodeSelector 指定不存在的标签) 和证据 #4 (节点无该标签)，问题的根本原因是**Pod 的 nodeSelector 指定的标签 'aiops.e2e/nonexistent-node-label=true' 在集群节点中不存在**，导致调度失败。
**置信度**：高 (95%)
- ✅ 调度失败事件明确指出 nodeSelector 不匹配
- ✅ Pod 指定了不存在的标签
- ⚠️ 缺少节点完整标签列表，无法确认是否存在其他节点具有该标签

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 移除或修改 Pod 的 nodeSelector**

```bash
kubectl edit pod rc-pending-nodeselector -n aiops-e2e
```

*操作步骤*：
- 在 `spec.nodeSelector` 中删除或修改 `aiops.e2e/nonexistent-node-label=true`。
- 保存并退出编辑器后，Pod 会重新尝试调度。

**2. [可选] 在节点上添加指定标签**

如果应用需要特定节点运行，可考虑在某个节点上添加该标签：

```bash
kubectl label nodes <node-name> aiops.e2e/nonexistent-node-label=true
```

*注意*：请根据实际情况替换 `<node-name>`。

### 后续优化

1. **检查 nodeSelector 配置合理性**：确认 nodeSelector 是否确实需要该标签，是否为误配置。
2. **统一标签管理**：建议使用命名规范的标签，避免标签冲突或误用。
3. **自动化调度优化**：考虑使用 node affinity 或污点机制替代 nodeSelector，以获得更灵活的调度控制。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running |
| 2. 确认调度成功 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | `Node: <node-name>` 显示已调度节点 |
| 3. 检查 nodeSelector 是否已修改 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` | `nodeSelector` 不存在或已修改 |

---

## ⚠️ 注意事项

- 如果删除 nodeSelector 后仍调度失败，请检查其他调度限制（如 affinity、taint、资源限制等）。
- 如果需要强制调度到特定节点，请确保 nodeSelector 或 affinity 配置正确，并且节点标签匹配。
- 建议使用 `kubectl describe node` 或 `kubectl get node -o yaml` 查看节点标签列表，以便正确配置调度策略。

---

## 📊 性能统计

├─ 总耗时: 5.6m
├─ 问题定位: 61.1s (18%) ✅
├─ 证据链采集: 91.5s (27%) ✅
├─ 根因分析: 84.8s (25%) ✅
├─ 汇总总结: 97.5s (29%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 10 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 10 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
