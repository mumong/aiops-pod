======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 8a26dec1a8ec4ee6]

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
  Warning  FailedScheduling  25m                default-scheduler  0/3 nodes are available: 
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          25m   <none>   <none>   
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
  "reasoning": "当前 Pod rc-pending-nodeselector 处于 Pending 状态，且调度失败事件显示 0/3 nodes are available，原因为 3 node(s) didn't match Pod's node affinity/selector。这表明 Pod 的 nodeSelector 或 nodeAffinity 设置与集群中所有节点不匹配，导致调度失败。根据 runbook 和描述信息，此问题属于 L1 层，归因于调度失败。此外，Pod 的 nodeSelector 指定了一个不存在的标签 aiops.e2e/nonexistent-node-label，进一步确认了调度失败的原因。",
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
      "count": 1
    }
  ],
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "PendingUnschedulable",
  "status_category": "scheduling",
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
      "scenario": "nodeSelector 不匹配",
      "evidence": "Pod 的 nodeSelector 指定了一个不存在的标签 aiops.e2e/nonexistent-node-label，导致调度失败。"
    },
    {
      "scenario": "节点资源不足",
      "evidence": "调度失败事件中提到 0/3 nodes are available，且所有节点都未匹配 Pod 的 nodeSelector 或 nodeAffinity。"
    },
    {
      "scenario": "预抢占失败",
      "evidence": "调度失败事件中提到 preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.."
    }
  ]
}
   ✅ [问题定位] 完成 (1m 7.0s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[]
   entities=[]
   reasoning=当前 Pod rc-pending-nodeselector 处于 Pending 状态，且调度失败事件显示 0/3 nodes are available，原因为 3 node(s) didn't match Pod's node affinity/selector。这表明 Pod 的 nodeSelector 或 nodeAffinity 设置与集群中所有节点不匹配，导致调度失败。根据 runbook 和描述信息，此问题属于 L1 层，归因于调度失败。此外，Pod 的 nodeSelector 指定了一个不存在的标签 aiops.e2e/nonexistent-node-label，进一步确认了调度失败的原因。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.5, "reasoning": "当前 Pod rc-pending-nodeselector 处于 Pending 状态，且调度失败事件显示 0/3 nodes are available，原因为 3 node(s) didn't match Pod's node affinity/selector。这表明 Pod 的 nodeSelector 或 nodeAffinity 设置与集群中所有节点不匹配，导致调度失败。根据 runbook 和描述信息，此问题属于 L1 层，归因于调度失败。此外，Pod 的 nodeSelector 指定了一个不存在的标签 aiops.e2e/nonexistent-node-label，进一步确认了调度失败的原因。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                25m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/8a26dec1a8ec4ee6/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/8a26dec1a8ec4ee6/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/8a26dec1a8ec4ee6/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 50%

📍 [证据链采集] 执行中...
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
  Warning  FailedScheduling  27m                default-scheduler  0/3 nodes are available: 
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
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
   💭 [证据链采集] 已采集证据总结：
- `kubectl_describe` 显示 Pod `rc-pending-nodeselector` 无法调度，因为 0/3 节点匹配其 nodeSelector。
- `kubectl_get_by_kind_in_cluster` 显示所有节点状态正常，但没有节点具有 `aiops.e2e/nonexistent-node-label` 标签。
- `kubectl_get_yaml` 确认 Pod 的 `nodeSelector` 指定了一个不存在的标签 `aiops.e2e/nonexistent-node-label`，这是导致调度失败的根本原因。

关键证据：
1. **Pod 事件**：Pod 的 `FailedScheduling` 事件明确指出 0/3 节点匹配其 nodeSelector。
2. **节点标签**：集群中所有节点都没有 `aiops.e2e/nonexistent-node-label` 标签。
3. **Pod 配置**：Pod 的 `nodeSelector` 指定了一个不存在的标签，导致调度失败。

结论：
Pod `rc-pending-nodeselector` 无法调度的根本原因是其 `nodeSelector` 指定了一个不存在的标签 `aiops.e2e/nonexistent-node-label`，导致集群中没有任何节点可以满足其调度需求。
   ✅ [证据链采集] 完成 (1m 23.5s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证异常 Pod 'rc-pending-nodeselector' 的详细调度失败原因及 nodeSelector 配置","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"pod":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"获取 Pod 详细事件和调度失败的完整原因，确认 nodeSelector 是否与节点标签不匹配","evidence_type":"status_event","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"检查集群节点标签，确认是否有节点匹配 Pod 的 nodeSelector","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes --show-labels","tool_args":{"kind":"nodes"},"purpose":"验证是否存在节点拥有与 Pod 'rc-pending-nodeselector' 的 nodeSelector 中指定的标签（如 aiops.e2e/nonexistent-node-label）","evidence_type":"node_label_match","target_scope":"Nodes","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"验证 Pod 'rc-pending-nodeselector' 的完整 YAML 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"pod":"rc-pending-nodeselector","namespace":"aiops-e2e","output":"yaml"},"purpose":"确认 Pod 的 nodeSelector、nodeAffinity、taints 等配置，判断是否与集群节点配置冲突","evidence_type":"config","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  27m                default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  12m (x3 over 22m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/8a26dec1a8ec4ee6/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/8a26dec1a8ec4ee6/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/8a26dec1a8ec4ee6/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/8a26dec1a8ec4ee6/tools/002-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/8a26dec1a8ec4ee6/tools/002-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/8a26dec1a8ec4ee6/tools/002-evidence-kubectl_get_by_kind_in_cluster.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-fsdjk\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/8a26dec1a8ec4ee6/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/8a26dec1a8ec4ee6/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/8a26dec1a8ec4ee6/tools/003-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"已采集证据总结：\n- `kubectl_describe` 显示 Pod `rc-pending-nodeselector` 无法调度，因为 0/3 节点匹配其 nodeSelector。\n- `kubectl_get_by_kind_in_cluster` 显示所有节点状态正常，但没有节点具有 `aiops.e2e/nonexistent-node-label` 标签。\n- `kubectl_get_yaml` 确认 Pod 的 `nodeSelector` 指定了一个不存在的标签 `aiops.e2e/nonexistent-node-label`，这是导致调度失败的根本原因。\n\n关键证据：\n1. **Pod 事件**：Pod 的 `FailedScheduling` 事件明确指出 0/3 节点匹配其 nodeSelector。\n2. **节点标签**：集群中所有节点都没有 `aiops.e2e/nonexistent-node-label` 标签。\n3. **Pod 配置**：Pod 的 `nodeSelector` 指定了一个不存在的标签，导致调度失败。\n\n结论：\nPod `rc-pending-nodeselector` 无法调度的根本原因是其 `nodeSelector` 指定了一个不存在的标签 `aiops.e2e/nonexistent-node-label`，导致集群中没有任何节点可以满足其调度需求。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 8 个，匹配计划 3 个，未规划证据 5 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":3,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"验证异常 Pod 'rc-pending-nodeselector' 的详细调度失败原因及 nodeSelector 配置","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"获取 Pod 详细事件和调度失败的完整原因，确认 nodeSelector 是否与节点标签不匹配","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"检查集群节点标签，确认是否有节点匹配 Pod 的 nodeSelector","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes --show-labels","purpose":"验证是否存在节点拥有与 Pod 'rc-pending-nodeselector' 的 nodeSelector 中指定的标签（如 aiops.e2e/nonexistent-node-label）","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"验证 Pod 'rc-pending-nodeselector' 的完整 YAML 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"确认 Pod 的 nodeSelector、nodeAffinity、taints 等配置，判断是否与集群节点配置冲突","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证异常 Pod 'rc-pending-nodeselector' 的详细调度失败原因及... | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_get_by_kind_in_cl... | 检查集群节点标签，确认是否有节点匹配 Pod 的 nodeSelector | `kubectl get nodes --show-labels` |
   | e3 | important | ✅ | kubectl_get_yaml | 验证 Pod 'rc-pending-nodeselector' 的完整 YAML 配置 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 4.1s)
   📤 → 下游数据: root_cause=Pod 'rc-pending-nodeselector' 无法调度的根本原因是其 'nodeSelector' 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label'，导致集群中没有任何节点可以满足其调度需求。
   confidence=90%
   causal_chain={"根本原因": "Pod 的 'nodeSelector' 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label'", "传导": "由于没有节点具有该标签，调度器无法找到合适的节点来调度该 Pod", "直接原因": "0/3 节点匹配 Pod 的 nodeSelector，导致调度失败", "现象": "Pod 'rc-pending-nodeselector' 处于 Pending 状态，无法调度"}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"kubectl_describe": "Pod 'rc-pending-nodeselector' 无法调度，因为 0/3 节点匹配其 nodeSelector"}, {"kubectl_get_by_kind_in_cluster": "所有节点状态正常，但没有节点具有 'aiops.e2e/nonexistent-node-label' 标签"}, {"kubectl_get_yaml": "Pod 的 'nodeSelector' 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label'"}], "evidence_analysis": [{"Pod 事件": "Pod 的 'FailedScheduling' 事件明确指出 0/3 节点匹配其 nodeSelector"}, {"节点标签": "集群中所有节点都没有 'aiops.e2e/nonexistent-node-label' 标签"}, {"Pod 配置": "Pod 的 'nodeSelector' 指定了一个不存在的标签，导致调度失败"}], "causal_chain": {"根本原因": "Pod 的 'nodeSelector' 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label'", "传导": "由于没有节点具有该标签，调度器无法找到合适的节点来调度该 Pod", "直接原因": "0/3 节点匹配 Pod 的 nodeSelector，导致调度失败", "现象": "Pod 'rc-pending-nodeselector' 处于 Pending 状态，无法调度"}, "root_cause": "Pod 'rc-pending-nodeselector' 无法调度的根本原因是其 'nodeSelector' 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label'，导致集群中没有任何节点可以满足其调度需求。", "root_cause_summary": "Pod 'rc-pending-nodeselector' 无法调度的根本原因是其 'nodeSelector' 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label'，导致集群中没有任何节点可以满足其调度需求。", "confidence": 0.9, "confidence_reason": "有直接证据，因果链清晰，证据充分支持结论", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"场景": "资源不足导致无法调度", "概率": "中", "原因": "需验证 FailedScheduling 事件"}, {"场景": "taint/nodeSelector/affinity 不匹配", "概率": "中", "原因": "需验证 Pod spec 和 Node 条件"}, {"场景": "PVC 未绑定或卷依赖未满足", "概率": "中", "原因": "需验证 PVC/PV 状态"}], "limitations": "无", "llm_raw_analysis": "已采集证据总结：\n- `kubectl_describe` 显示 Pod `rc-pending-nodeselector` 无法调度，因为 0/3 节点匹配其 nodeSelector。\n- `kubectl_get_by_kind_in_cluster` 显示所有节点状态正常，但没有节点具有 `aiops.e2e/nonexistent-node-label` 标签。\n- `kubectl_get_yaml` 确认 Pod 的 `nodeSelector` 指定了一个不存在的标签 `aiops.e2e/nonexistent-node-label`，这是导致调度失败的根本原因。\n\n关键证据：\n1. **Pod 事件**：Pod 的 `FailedScheduling` 事件明确指出 0/3 节点匹配其 nodeSelector。\n2. **节点标签**：集群中所有节点都没有 `aiops.e2e/nonexistent-node-label` 标签。\n3. **Pod 配置**：Pod 的 `nodeSelector` 指定了一个不存在的标签，导致调度失败。\n\n结论：\nPod `r\n... 截断，原始 619 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'rc-pending-nodeselector' 无法调度的根本原因是其 'nodeSelector' 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label'，导致集群中没有任何节点可以满足其调度需求。
   置信度: 90%
   🔗 因果链:


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 43.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3944 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 18.3s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | `PendingUnschedulable` |
| **兼容归因层** | `L1` |
| **问题分类** | `调度失败（NodeSelector/NodeAffinity 不匹配）` |
| **置信度** | 高 (90%) |
| **证据完整度** | 3/3 (100%) |

---

## 🔍 现象描述

**用户报告**：  
> 我的集群有什么问题？

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
| 1 | Pod 状态 | `kubectl get pod -n aiops-e2e` | `STATUS: Pending` | Pod 无法调度 |
| 2 | FailedScheduling 事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 调度失败，无节点匹配 |
| 3 | nodeSelector 配置 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` | `nodeSelector: aiops.e2e/nonexistent-node-label: "true"` | 指定了不存在的标签，导致无节点匹配 |

### 证据关联分析

- **证据 #2 + #3 印证**：Pod 的 `nodeSelector` 指定了一个不存在的标签 `aiops.e2e/nonexistent-node-label`，导致调度器无法找到匹配的节点。
- **证据链**：Pod 指定了无效标签 → 调度器找不到匹配节点 → Pod 一直处于 Pending 状态。

### 缺失证据（无）

| 证据 | 级别 | 影响 |
|------|------|------|
| （无） | （无） | （无） |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod 的 nodeSelector 指定了不存在的标签 aiops.e2e/nonexistent-node-label │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 调度器无法找到匹配此 nodeSelector 的节点                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Pod rc-pending-nodeselector 一直处于 Pending 状态               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 无法调度，用户看到状态为 Pending                            │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2（FailedScheduling 事件）和证据 #3（nodeSelector 配置），问题的根本原因是**Pod 的 `nodeSelector` 指定了一个不存在的标签 `aiops.e2e/nonexistent-node-label`**，导致调度器无法找到匹配节点，从而无法调度 Pod。

**置信度**：高 (90%)
- ✅ 事件 `FailedScheduling` 明确指出无节点匹配
- ✅ YAML 配置确认 nodeSelector 指定了不存在的标签
- ✅ 无缺失关键证据

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 修正 nodeSelector 配置**

```bash
kubectl delete pod rc-pending-nodeselector -n aiops-e2e
```

```bash
# 修改 Deployment 或 Pod YAML，删除或替换 nodeSelector
# 示例（如果使用 Deployment）：
kubectl edit deployment <deployment-name> -n aiops-e2e
```

在 YAML 中移除或修改如下配置：

```yaml
nodeSelector:
  aiops.e2e/nonexistent-node-label: "true"
```

**2. [可选] 添加合理的 nodeSelector**

如果应用需要特定节点，确保标签已存在于集群中：

```bash
kubectl label nodes <node-name> aiops.e2e/some-valid-label=true
```

再在 Pod YAML 中配置：

```yaml
nodeSelector:
  aiops.e2e/some-valid-label: "true"
```

### 后续优化

1. **验证标签一致性**：定期检查节点标签与调度需求是否一致。
2. **使用 nodeAffinity 替代 nodeSelector**：更灵活的调度策略。
3. **部署监控**：监控调度失败事件，及时发现异常。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running |
| 2. 检查事件日志 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | 无 FailedScheduling 事件 |
| 3. 验证 nodeSelector | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` | nodeSelector 字段已修正 |

---

## ⚠️ 注意事项

- 如果 nodeSelector 是为了特定需求（如 GPU、SSD 等），确保节点已正确打标签。
- 如果不确定 nodeSelector 是否必要，建议移除或使用 nodeAffinity 提高灵活性。
- 避免硬编码 nodeSelector，建议使用 nodeAffinity 或 Taints/Labels 策略管理调度。

---

## 📊 性能统计

├─ 总耗时: 5.3m
├─ 问题定位: 67.0s (21%) ✅
├─ 证据链采集: 83.5s (26%) ✅
├─ 根因分析: 64.1s (20%) ✅
├─ 汇总总结: 103.7s (33%) ✅
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
