======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 15f746ad660742ec]

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
  Warning  FailedScheduling  7m54s  default-scheduler  0/3 nodes are available: 3 node(s) di
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE    IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          8m2s   <none>   <none> 
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
  "reasoning": "Pod 'rc-pending-nodeselector' 处于 Pending 状态且未绑定 nodeName，调度器报告 0/3 个节点可用，原因是 3 个节点不匹配 Pod 的 nodeSelector。Pod 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，但集群中没有任何节点具有该标签，导致调度失败。所有节点状态正常 (Ready)，但因标签不匹配无法调度。符合 L1 分类，因为问题源于调度策略配置不当，而非资源不足或节点不可用。",
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
      "pods": [
        "rc-pending-nodeselector"
      ]
    }
  ],
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "PendingUnschedulable",
  "status_category": "scheduling",
  "key_entities": [
    {
      "name": "rc-pending-nodeselector",
      "kind": "Pod",
      "namespace": "aiops-e2e",
      "status": "Pending",
      "reason": "Unschedulable"
    },
    {
      "name": "aiops.e2e/nonexistent-node-label",
      "kind": "LabelSelector",
      "namespace": "aiops-e2e",
      "status": "Unmatched"
    }
  ],
  "possible_scenarios": [
    {
      "scenario": "Pod 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，但集群中没有任何节点具有该标签，导致调度失败。",
      "confidence": 0.95
    },
    {
      "scenario": "集群中所有节点状态正常，但标签不匹配导致 Pod 无法调度。",
      "confidence": 0.95
    }
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (2m 0.3s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': "Pod 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，但集群中没有任何节点具有该标签，导致调度失败。", 'probability': '0.95', 'reason': 'Pod 的 nodeSelector 设置了不存在的标签，导致调度失败。'}, {'scenario': '集群中所有节点状态正常，但标签不匹配导致 Pod 无法调度。', 'probability': '0.95', 'reason': '集群中所有节点状态正常，但标签不匹配导致 Pod 无法调度。'}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "LabelSelector", "name": "aiops.e2e/nonexistent-node-label", "namespace": "aiops-e2e"}]
   reasoning=Pod 'rc-pending-nodeselector' 处于 Pending 状态且未绑定 nodeName，调度器报告 0/3 个节点可用，原因是 3 个节点不匹配 Pod 的 nodeSelector。Pod 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，但集群中没有任何节点具有该标签，导致调度失败。所有节点状态正常 (Ready)，但因标签不匹配无法调度。符合 L1 分类，因为问题源于调度策略配置不当，而非资源不足或节点不可用。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "Pod 'rc-pending-nodeselector' 处于 Pending 状态且未绑定 nodeName，调度器报告 0/3 个节点可用，原因是 3 个节点不匹配 Pod 的 nodeSelector。Pod 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，但集群中没有任何节点具有该标签，导致调度失败。所有节点状态正常 (Ready)，但因标签不匹配无法调度。符合 L1 分类，因为问题源于调度策略配置不当，而非资源不足或节点不可用。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "LabelSelector", "name": "aiops.e2e/nonexistent-node-label", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Pod 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，但集群中没有任何节点具有该标签，导致调度失败。", "probability": "0.95", "reason": "Pod 的 nodeSelector 设置了不存在的标签，导致调度失败。"}, {"scenario": "集群中所有节点状态正常，但标签不匹配导致 Pod 无法调度。", "probability": "0.95", "reason": "集群中所有节点状态正常，但标签不匹配导致 Pod 无法调度。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                7m50s   <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/15f746ad660742ec/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/15f746ad660742ec/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/15f746ad660742ec/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
10m                   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3
   💭 [证据链采集] 已采集证据：
1. **Pod 配置验证**：`kubectl_get_yaml` 显示 Pod 的 `nodeSelector` 设置了 `aiops.e2e/nonexistent-node-label=true`，且当前 phase 为 `Pending`。
2. **节点标签检查**：`kubectl_get_by_kind_in_cluster` 显示所有节点状态为 `Ready`，但没有任何节点具有 `aiops.e2e/nonexistent-node-label=true` 标签。
3. **调度失败事件**：`kubectl_events` 显示调度器报告 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`。

未采集证据：无。

冲突证据：无。
   ✅ [证据链采集] 完成 (1m 7.2s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证异常 Pod 的 nodeSelector 是否与集群中任何节点的标签匹配","level":"critical","tool":"kubectl_get_yaml","command":"get_pod","tool_args":{"pod_name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"检查 Pod 的 nodeSelector 设置","evidence_type":"configuration","target_scope":"aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e2","description":"检查集群中所有节点的标签是否包含 Pod 所需的 'aiops.e2e/nonexistent-node-label=true'","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"get_nodes","tool_args":{"kind":"Node"},"purpose":"验证节点标签是否匹配 Pod 的 nodeSelector","evidence_type":"configuration","target_scope":"cluster/nodes","acceptable_tools":["kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true},{"id":"e3","description":"检查异常 Pod 的调度事件以确认调度失败的具体原因","level":"important","tool":"kubectl_events","command":"get_pod_events","tool_args":{"pod_name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"检查调度失败事件","evidence_type":"event","target_scope":"aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-fsdjk\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/15f746ad660742ec/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/15f746ad660742ec/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/15f746ad660742ec/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/15f746ad660742ec/tools/002-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/15f746ad660742ec/tools/002-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/15f746ad660742ec/tools/002-evidence-kubectl_get_by_kind_in_cluster.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n10m                   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n40s (x2 over 5m40s)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/15f746ad660742ec/tools/003-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/15f746ad660742ec/tools/003-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/15f746ad660742ec/tools/003-evidence-kubectl_events.summary.txt"}],"llm_analysis":"已采集证据：\n1. **Pod 配置验证**：`kubectl_get_yaml` 显示 Pod 的 `nodeSelector` 设置了 `aiops.e2e/nonexistent-node-label=true`，且当前 phase 为 `Pending`。\n2. **节点标签检查**：`kubectl_get_by_kind_in_cluster` 显示所有节点状态为 `Ready`，但没有任何节点具有 `aiops.e2e/nonexistent-node-label=true` 标签。\n3. **调度失败事件**：`kubectl_events` 显示调度器报告 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`。\n\n未采集证据：无。\n\n冲突证据：无。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 8 个，匹配计划 3 个，未规划证据 5 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":3,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"验证异常 Pod 的 nodeSelector 是否与集群中任何节点的标签匹配","level":"critical","tool":"kubectl_get_yaml","command":"get_pod","purpose":"检查 Pod 的 nodeSelector 设置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"检查集群中所有节点的标签是否包含 Pod 所需的 'aiops.e2e/nonexistent-node-label=true'","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"get_nodes","purpose":"验证节点标签是否匹配 Pod 的 nodeSelector","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"检查异常 Pod 的调度事件以确认调度失败的具体原因","level":"important","tool":"kubectl_events","command":"get_pod_events","purpose":"检查调度失败事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_yaml | 验证异常 Pod 的 nodeSelector 是否与集群中任何节点的标签匹配 | `get_pod` |
   | e2 | critical | ✅ | kubectl_get_by_kind_in_cl... | 检查集群中所有节点的标签是否包含 Pod 所需的 'aiops.e2e/nonexiste... | `get_nodes` |
   | e3 | important | ✅ | kubectl_events | 检查异常 Pod 的调度事件以确认调度失败的具体原因 | `get_pod_events` |

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
   ✅ [根因分析] 完成 (2m 21.4s)
   📤 → 下游数据: root_cause=Pod 'rc-pending-nodeselector' 处于 Pending 状态，原因是其 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，但集群中没有任何节点具有该标签，导致调度失败。
   confidence=95%
   causal_chain={"root_cause": "Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，但集群中没有任何节点具有该标签，导致调度失败。", "intermediate_causes": ["Pod 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，但集群中没有任何节点具有该标签", "调度器报告 0/3 个节点可用，原因是 3 个节点不匹配 Pod 的 nodeSelector"], "immediate_causes": ["Pod 的 nodeSelector 设置了 'aiops.e2.e/nonexistent-node-label=true'，但集群中没有任何节点具有该标签"], "symptoms": ["Pod 'rc-pending-nodeselector' 处于 Pending 状态且未绑定 nodeName", "调度器报告 0/3 个节点可用", "所有节点状态正常 (Ready)，但因标签不匹配无法调度"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"description": "验证异常 Pod 的 nodeSelector 是否与集群中任何节点的标签匹配", "level": "critical", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSe"}, {"description": "检查集群中所有节点的标签是否包含 Pod 所需的 'aiops.e2e/nonexistent-node-label=true'", "level": "critical", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubern"}, {"description": "检查异常 Pod 的调度事件以确认调度失败的具体原因", "level": "important", "value": "kubectl_events 摘要:\n关键诊断行:\n10m                   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n40s (x2 over 5m40s)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for sched"}], "evidence_analysis": [{"description": "验证异常 Pod 的 nodeSelector 是否与集群中任何节点的标签匹配", "level": "critical", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSe", "raw_data": "nodeSelector: aiops.e2e/nonexistent-node-label=true"}, {"description": "检查集群中所有节点的标签是否包含 Pod 所需的 'aiops.e2e/nonexistent-node-label=true'", "level": "critical", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubern", "raw_data": "所有节点状态为 Ready，但没有节点具有 aiops.e2e/nonexistent-node-label=true 标签"}, {"description": "检查异常 Pod 的调度事件以确认调度失败的具体原因", "level": "important", "value": "kubectl_events 摘要:\n关键诊断行:\n10m                   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n40s (x2 over 5m40s)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for sched", "raw_data": "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"}], "causal_chain": {"root_cause": "Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，但集群中没有任何节点具有该标签，导致调度失败。", "intermediate_causes": ["Pod 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，但集群中没有任何节点具有该标签", "调度器报告 0/3 个节点可用，原因是 3 个节点不匹配 Pod 的 nodeSelector"], "immediate_causes": ["Pod 的 nodeSelector 设置了 'aiops.e2.e/nonexistent-node-label=true'，但集群中没有任何节点具有该标签"], "symptoms": ["Pod 'rc-pending-nodeselector' 处于 Pending 状态且未绑定 nodeName", "调度器报告 0/3 个节点可用", "所有节点状态正常 (Ready)，但因标签不匹配无法调度"]}, "root_cause": "Pod 'rc-pending-nodeselector' 处于 Pending 状态，原因是其 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，但集群中没有任何节点具有该标签，导致调度失败。", "root_cause_summary": "Pod 'rc-pending-nodeselector' 处于 Pending 状态，原因是其 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，但集群中没有任何节点具有该标签，导致调度失败。", "confidence": 0.95, "confidence_reason": "", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [], "limitations": "", "llm_raw_analysis": "1. 证据清点：\n   - kubectl_get_yaml 显示 Pod 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'。\n   - kubectl_get_by_kind_in_cluster 显示所有节点状态为 Ready，但没有节点具有该标签。\n   - kubectl_events 显示调度器报告 0/3 个节点可用，原因是 3 个节点不匹配 Pod 的 nodeSelector。\n\n2. 逐条分析：\n   - kubectl_get_yaml 证实 Pod 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'。\n   - kubectl_get_by_kind_in_cluster 证实所有节点状态为 Ready，但没有节点具有该标签。\n   - kubectl_events 证实调度器报告 0/3 个节点可用，原因是 3 个节点不匹配 Pod 的 nodeSelector。\n\n3. 关联分析：\n   - Pod 的 nodeSelector\n... 截断，原始 927 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'rc-pending-nodeselector' 处于 Pending 状态，原因是其 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，但集群中没有任何节点具有该标签，导致调度失败。
   置信度: 95%
   🔗 因果链:
     根本原因: Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，但集群中没有任何节点具有该标签，导致调度失败。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 53.2s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4828 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 7m 22.2s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pod 'rc-pending-nodeselector' 处于 Pending 状态 |
| **兼容归因层** | L1 - 调度问题 |
| **问题分类** | 调度失败（nodeSelector 不匹配） |
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
| 错误信息 | 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod -n aiops-e2e` | `STATUS: Pending` | Pod 无法调度 |
| 2 | 调度事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | `Warning  FailedScheduling  7m54s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | nodeSelector 不匹配 |
| 3 | Pod nodeSelector | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` | `nodeSelector: aiops.e2e/nonexistent-node-label: "true"` | Pod 要求不存在的标签 |
| 4 | 节点标签 | `kubectl get nodes -o yaml` | 节点无 `aiops.e2e/nonexistent-node-label=true` 标签 | 标签不匹配，调度失败 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 Pending，事件显示调度失败，原因为 nodeSelector 不匹配。
- **证据 #3 印证**：Pod 的 nodeSelector 设置了 `aiops.e2e/nonexistent-node-label=true`，而该标签在节点中不存在。
- **证据 #4 印证**：所有节点均未设置该标签，导致调度失败。

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，但集群中没有任何节点具有该标签，导致调度失败。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 调度器尝试调度 Pod 到匹配 nodeSelector 的节点，但无匹配节点。   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 0/3 个节点匹配 nodeSelector，调度失败。                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 Pending，Events 显示 FailedScheduling。              │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2 (FailedScheduling 事件) 和证据 #3 (Pod nodeSelector 设置了不存在的标签)，问题的根本原因是 **Pod 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label=true'，但集群中没有任何节点具有该标签**，导致调度失败。

**置信度**：高 (95%)
- ✅ `kubectl describe pod` 显示调度失败
- ✅ `kubectl get pod -o yaml` 显示 nodeSelector 设置了不存在的标签
- ✅ `kubectl get nodes` 显示所有节点无该标签

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 移除或修改 nodeSelector**
```bash
kubectl edit pod rc-pending-nodeselector -n aiops-e2e
```
*操作*：删除或修改 `spec.nodeSelector.aiops.e2e/nonexistent-node-label` 的值，或确保集群中存在该标签。

**2. [可选] 为节点添加标签（如果 nodeSelector 是有意设置的）**
```bash
kubectl label nodes <node-name> aiops.e2e/nonexistent-node-label=true
```
*目的*：让节点匹配 Pod 的 nodeSelector，从而允许调度。

### 后续优化

1. **标签管理最佳实践**：
   - 确保所有 nodeSelector、affinity、taint 等配置的标签在节点上实际存在。
2. **调度策略验证**：
   - 在部署 Pod 前，验证其 nodeSelector 是否与节点标签匹配。
3. **调度器日志监控**：
   - 通过 `kubectl describe pod` 或 `kubectl logs -n kube-system <scheduler-pod>` 查看调度器日志。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 是否调度成功 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running |
| 2. 检查 Pod 是否绑定到节点 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | Node 字段显示实际节点名 |
| 3. 确认节点标签是否添加成功（如适用） | `kubectl get nodes -o yaml` | 节点有 `aiops.e2e/nonexistent-node-label=true` 标签 |

---

## ⚠️ 注意事项

- 如果 nodeSelector 是有意设置的，确保所有节点中至少有一个节点具备该标签。
- 如果 nodeSelector 是误配置，建议清理或修改调度策略。
- 如果 nodeSelector 是测试用途，可考虑使用 `nodeAffinity` 替代，提供更灵活的调度条件。

---

## 📄 附录：原始数据引用

### 1. Pod 状态
```bash
kubectl get pod -n aiops-e2e rc-pending-nodeselector
NAME                      READY   STATUS    RESTARTS   AGE    IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          8m2s   <none>   <none> 
```

### 2. Pod 调度事件
```bash
kubectl describe pod rc-pending-nodeselector -n aiops-e2e
Warning  FailedScheduling  7m54s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector
```

### 3. Pod nodeSelector 配置
```yaml
kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml
nodeSelector:
  aiops.e2e/nonexistent-node-label: "true"
```

### 4. 节点标签
```bash
kubectl get nodes -o yaml
# 所有节点无 `aiops.e2e/nonexistent-node-label=true` 标签
```

---

✅ 本报告依据真实工具采集的证据生成，所有结论均有据可依。

---

## 📊 性能统计

├─ 总耗时: 7.4m
├─ 问题定位: 120.3s (27%) ✅
├─ 证据链采集: 67.2s (15%) ✅
├─ 根因分析: 141.4s (32%) ✅
├─ 汇总总结: 113.2s (26%) ✅
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
