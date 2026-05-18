======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: c178f8ed74c8465b]

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
  Warning  FailedScheduling  11m                   default-scheduler  0/3 nodes are availabl
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          11m   <none>   <none>   
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
  "confidence": 0.95,
  "reasoning": "Pod 'rc-pending-nodeselector' 无法调度，原因是节点选择器不匹配。Pod 的 nodeSelector 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label'，而集群中的节点都没有这个标签。因此，调度器无法找到合适的节点来运行该 Pod。",
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
      "reasons": ["nodeSelector 不匹配"]
    }
  ],
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "PendingUnschedulable",
  "status_category": "PendingUnschedulable",
  "key_entities": [
    {
      "name": "rc-pending-nodeselector",
      "kind": "Pod",
      "namespace": "aiops-e2e",
      "reason": "Unschedulable",
      "message": "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.."
    }
  ],
  "possible_scenarios": [
    "节点选择器不匹配导致 Pod 无法调度",
    "集群中没有节点满足 Pod 的 nodeSelector 要求"
  ]
}
   ✅ [问题定位] 完成 (43.9s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[]
   entities=[]
   reasoning=Pod 'rc-pending-nodeselector' 无法调度，原因是节点选择器不匹配。Pod 的 nodeSelector 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label'，而集群中的节点都没有这个标签。因此，调度器无法找到合适的节点来运行该 Pod。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.5, "reasoning": "Pod 'rc-pending-nodeselector' 无法调度，原因是节点选择器不匹配。Pod 的 nodeSelector 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label'，而集群中的节点都没有这个标签。因此，调度器无法找到合适的节点来运行该 Pod。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "", "status_category": "", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                11m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/c178f8ed74c8465b/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/c178f8ed74c8465b/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/c178f8ed74c8465b/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  13m                    default-scheduler  0/3 nodes are availab
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
   💭 [证据链采集] # 证据结论

## 已采集证据
1. **Pod 事件和状态**：`kubectl describe pod` 显示 Pod `rc-pending-nodeselector` 处于 `Pending` 状态，事件 `FailedScheduling` 明确指出 `3 node(s) didn't match Pod's node affinity/selector`。
2. **Pod 配置**：`kubectl get pod -o yaml` 显示 Pod 的 `nodeSelector` 指定了一个不存在的标签 `aiops.e2e/nonexistent-node-label`。
3. **节点标签**：`kubectl get nodes -o jsonpath='{.items[*].metadata.labels}'` 显示集群中的节点都没有 `aiops.e2e/nonexistent-node-label` 这个标签。

## 未采集证据
- 无。

## 冲突证据
- 无。

## 总结
Pod `rc-pending-nodeselector` 无法调度的根本原因是其 `nodeSelector` 指定了一个不存在的标签 `aiops.e2e/nonexistent-node-label`，而集群中的节点都没有这个标签。因此，调度器无法找到合适的节点来运行该 Pod。建议修改 Pod 的 `nodeSelector`，使其与集群中节点的标签匹配。
   ✅ [证据链采集] 完成 (1m 35.1s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod 'rc-pending-nodeselector' 的调度失败原因，重点关注 nodeSelector/affinity 不匹配的信号。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{},"purpose":"验证 Pod 的 nodeSelector 是否与节点标签不匹配","evidence_type":"event","target_scope":"aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"检查 Pod 'rc-pending-nodeselector' 的 nodeSelector 配置，确认其指定的标签是否在集群中存在。","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{},"purpose":"确认 nodeSelector 指定的标签是否在集群中存在","evidence_type":"configuration","target_scope":"aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e3","description":"检查集群节点的标签，确认是否存在与 Pod 'rc-pending-nodeselector' 的 nodeSelector 匹配的标签。","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o jsonpath='{.items[*].metadata.labels}'","tool_args":{},"purpose":"确认节点上是否存在与 nodeSelector 匹配的标签","evidence_type":"node_configuration","target_scope":"all-nodes","acceptable_tools":["kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  13m                    default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  3m42s (x2 over 8m42s)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c178f8ed74c8465b/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c178f8ed74c8465b/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c178f8ed74c8465b/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-fsdjk\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c178f8ed74c8465b/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c178f8ed74c8465b/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c178f8ed74c8465b/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c178f8ed74c8465b/tools/003-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c178f8ed74c8465b/tools/003-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c178f8ed74c8465b/tools/003-evidence-kubectl_get_by_kind_in_cluster.summary.txt"}],"llm_analysis":"# 证据结论\n\n## 已采集证据\n1. **Pod 事件和状态**：`kubectl describe pod` 显示 Pod `rc-pending-nodeselector` 处于 `Pending` 状态，事件 `FailedScheduling` 明确指出 `3 node(s) didn't match Pod's node affinity/selector`。\n2. **Pod 配置**：`kubectl get pod -o yaml` 显示 Pod 的 `nodeSelector` 指定了一个不存在的标签 `aiops.e2e/nonexistent-node-label`。\n3. **节点标签**：`kubectl get nodes -o jsonpath='{.items[*].metadata.labels}'` 显示集群中的节点都没有 `aiops.e2e/nonexistent-node-label` 这个标签。\n\n## 未采集证据\n- 无。\n\n## 冲突证据\n- 无。\n\n## 总结\nPod `rc-pending-nodeselector` 无法调度的根本原因是其 `nodeSelector` 指定了一个不存在的标签 `aiops.e2e/nonexistent-node-label`，而集群中的节点都没有这个标签。因此，调度器无法找到合适的节点来运行该 Pod。建议修改 Pod 的 `nodeSelector`，使其与集群中节点的标签匹配。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 8 个，匹配计划 3 个，未规划证据 5 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":3,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"验证 Pod 'rc-pending-nodeselector' 的调度失败原因，重点关注 nodeSelector/affinity 不匹配的信号。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"验证 Pod 的 nodeSelector 是否与节点标签不匹配","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"检查 Pod 'rc-pending-nodeselector' 的 nodeSelector 配置，确认其指定的标签是否在集群中存在。","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"确认 nodeSelector 指定的标签是否在集群中存在","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"检查集群节点的标签，确认是否存在与 Pod 'rc-pending-nodeselector' 的 nodeSelector 匹配的标签。","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o jsonpath='{.items[*].metadata.labels}'","purpose":"确认节点上是否存在与 nodeSelector 匹配的标签","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证 Pod 'rc-pending-nodeselector' 的调度失败原因，重点关注... | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_get_yaml | 检查 Pod 'rc-pending-nodeselector' 的 nodeSelect... | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e3 | important | ✅ | kubectl_get_by_kind_in_cl... | 检查集群节点的标签，确认是否存在与 Pod 'rc-pending-nodeselecto... | `kubectl get nodes -o jsonpath='{.items[*].metadata.labels}'` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 58.1s)
   📤 → 下游数据: root_cause=Pod 'rc-pending-nodeselector' 无法调度的根本原因是其 nodeSelector 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label'，而集群中的节点都没有这个标签。因此，调度器无法找到合适的节点来运行该 Pod。
   confidence=90%
   causal_chain={"root_cause": "Pod 'rc-pending-nodeselector' 无法调度，原因是节点选择器不匹配。Pod 的 nodeSelector 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label'，而集群中的节点都没有这个标签。因此，调度器无法找到合适的节点来运行该 Pod。", "intermediate_causes": ["Pod 'rc-pending-nodeselector' 的 nodeSelector 指定了 'aiops.e2e/nonexistent-node-label' 标签。", "集群中的节点没有 'aiops.e2e/nonexistent-node-label' 标签。"], "direct_causes": ["调度器无法找到匹配 'aiops.e2e/nonexistent-node-label' 标签的节点。"], "symptoms": ["Pod 'rc-pending-nodeselector' 的状态为 'Pending'。", "调度器事件显示 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"e1": "验证 Pod 'rc-pending-nodeselector' 的调度失败原因，重点关注 nodeSelector/affinity 不匹配的信号。"}, {"e2": "检查 Pod 'rc-pending-nodeselector' 的 nodeSelector 配置，确认其指定的标签是否在集群中存在。"}, {"e3": "检查集群节点的标签，确认是否存在与 Pod 'rc-pending-nodeselector' 的 nodeSelector 匹配的标签。"}, {"layer_1": "上游已验证工具结果: kubectl_get_by_kind_in_cluster"}, {"layer_2": "上游已验证工具结果: kubectl_describe"}, {"layer_3": "上游已验证工具结果: kubectl_get_by_name"}, {"layer_4": "上游已验证工具结果: kubectl_get_by_kind_in_cluster"}, {"layer_5": "上游已验证工具结果: kubectl_get_yaml"}], "evidence_analysis": [{"e1": "kubectl_describe 摘要: name: rc-pending-nodeselector namespace: aiops-e2e node: <none> status: Pending 关键诊断行:  Warning  FailedScheduling  13m                    default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..  Warning  FailedScheduling  3m42s (x2 over 8m42s)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/\n... 截断，原始 567 字符"}, {"e2": "kubectl_get_yaml 关键字段摘要: kind: Pod name: rc-pending-nodeselector namespace: aiops-e2e creationTimestamp: 2026-05-13T20:39:53Z deletionTimestamp: <absent> deletionGracePeriodSeconds: None finalizers: <none> serviceAccountName: default nodeName: None restartPolicy: Always terminationGracePeriodSeconds: 30 imagePullSecrets: <absent> phase: Pending labels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable diagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md nodeSe"}, {"e3": "kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3} NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS # 样例行 master   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubern"}, {"layer_1": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Pending': 1, 'Running': 46} NAMESPACE     NAME                                                READY   STATUS      RESTARTS         AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS # 异常行 aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                11m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type"}, {"layer_2": "kubectl_describe 摘要: name: rc-pending-nodeselector namespace: aiops-e2e node: <none> status: Pending 关键诊断行:  Warning  FailedScheduling  11m                   default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..  Warning  FailedScheduling  109s (x2 over 6m49s)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3\n... 截断，原始 565 字符"}, {"layer_3": "NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS rc-pending-nodeselector   0/1     Pending   0          11m   <none>   <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"}, {"layer_4": "kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3} NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS # 样例行 master   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubern"}, {"layer_5": "kubectl_get_yaml 关键字段摘要: kind: Pod name: rc-pending-nodeselector namespace: aiops-e2e creationTimestamp: 2026-05-13T20:39:53Z deletionTimestamp: <absent> deletionGracePeriodSeconds: None finalizers: <none> serviceAccountName: default nodeName: None restartPolicy: Always terminationGracePeriodSeconds: 30 imagePullSecrets: <absent> phase: Pending labels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable diagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md nodeSe"}], "causal_chain": {"root_cause": "Pod 'rc-pending-nodeselector' 无法调度，原因是节点选择器不匹配。Pod 的 nodeSelector 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label'，而集群中的节点都没有这个标签。因此，调度器无法找到合适的节点来运行该 Pod。", "intermediate_causes": ["Pod 'rc-pending-nodeselector' 的 nodeSelector 指定了 'aiops.e2e/nonexistent-node-label' 标签。", "集群中的节点没有 'aiops.e2e/nonexistent-node-label' 标签。"], "direct_causes": ["调度器无法找到匹配 'aiops.e2e/nonexistent-node-label' 标签的节点。"], "symptoms": ["Pod 'rc-pending-nodeselector' 的状态为 'Pending'。", "调度器事件显示 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。"]}, "root_cause": "Pod 'rc-pending-nodeselector' 无法调度的根本原因是其 nodeSelector 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label'，而集群中的节点都没有这个标签。因此，调度器无法找到合适的节点来运行该 Pod。", "root_cause_summary": "Pod 'rc-pending-nodeselector' 无法调度的根本原因是其 nodeSelector 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label'，而集群中的节点都没有这个标签。因此，调度器无法找到合适的节点来运行该 Pod。", "confidence": 0.9, "confidence_reason": "有直接证据表明 Pod 的 nodeSelector 指定了一个不存在的标签，而集群中的节点都没有这个标签。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "资源不足导致无法调度", "probability": "低", "reason": "没有证据表明资源不足导致无法调度。"}, {"cause": "PVC 未绑定或卷依赖未满足", "probability": "低", "reason": "没有证据表明 PVC 未绑定或卷依赖未满足。"}], "limitations": "没有发现其他异常 Pod 或节点，因此无法确认是否存在其他问题。", "llm_raw_analysis": "已采集证据\n1. **Pod 事件和状态**：`kubectl describe pod` 显示 Pod `rc-pending-nodeselector` 处于 `Pending` 状态，事件 `FailedScheduling` 明确指出 `3 node(s) didn't match Pod's node affinity/selector`。\n2. **Pod 配置**：`kubectl get pod -o yaml` 显示 Pod 的 `nodeSelector` 指定了一个不存在的标签 `aiops.e2e/nonexistent-node-label`。\n3. **节点标签**：`kubectl get nodes -o jsonpath='{.items[*].metadata.labels}'` 显示集群中的节点都没有 `aiops.e2e/nonexistent-node-label` 这个标签。\n\n## 未采集证据\n- 无。\n\n## 冲突证据\n- 无。\n\n## 总结\nPod `rc-pending-nodeselector` 无法调度的根本原因是其 `nodeS\n... 截断，原始 635 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'rc-pending-nodeselector' 无法调度的根本原因是其 nodeSelector 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label'，而集群中的节点都没有这个标签。因此，调度器无法找到合适的节点来运行该 Pod。
   置信度: 90%
   🔗 因果链:
     根本原因: Pod 'rc-pending-nodeselector' 无法调度，原因是节点选择器不匹配。Pod 的 nodeSelector 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label'，而集群中的节点都没有这个标签。因此，调度器无法找到合适的节点来运行该 Pod。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (2m 44.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4643 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 7m 1.8s
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
| **问题分类** | 调度失败（NodeSelector 不匹配） |
| **置信度** | 高 (90%) |
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
| 错误信息 | nodeSelector 不匹配，无法调度 |

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 调度失败事件 | `kubectl describe pod rc-pending-nodeselector` | `Warning FailedScheduling 11m: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | Pod 的 nodeSelector 不匹配任何节点 |
| 2 | Pod 的 nodeSelector 配置 | `kubectl get pod rc-pending-nodeselector -o yaml` | `nodeSelector: aiops.e2e/nonexistent-node-label: "true"` | Pod 指定了一个不存在的标签 |
| 3 | 集群节点标签 | `kubectl get nodes --show-labels` | 未发现 `aiops.e2e/nonexistent-node-label` 标签 | 节点没有匹配的标签，导致调度失败 |
| 4 | Pod 状态 | `kubectl get pod rc-pending-nodeselector` | `STATUS: Pending` | Pod 无法调度，处于 Pending 状态 |
| 5 | 节点状态 | `kubectl get node` | `STATUS: Ready` | 节点状态正常，但无匹配标签 |
| 6 | Pod 调度失败重复事件 | `kubectl describe pod rc-pending-nodeselector` | `Warning FailedScheduling 109s (x2 over 6m49s)` | 问题持续存在，调度器多次尝试失败 |
| 7 | Pod 未绑定节点 | `kubectl get pod rc-pending-nodeselector -o jsonpath='{.spec.nodeName}'` | `<none>` | Pod 未被分配到任何节点 |
| 8 | 调度失败原因总结 | `kubectl describe pod rc-pending-nodeselector` | `3 node(s) didn't match Pod's node affinity/selector` | 明确指出 nodeSelector 不匹配 |

### 证据关联分析
- **证据 #1 + #2 + #3 印证**：Pod 指定了一个不存在的标签 `aiops.e2e/nonexistent-node-label`，而节点上没有该标签，导致调度失败。
- **证据链**：Pod 的 nodeSelector 不匹配任何节点 → 调度器无法找到合适节点 → Pod 持续处于 Pending 状态。
- **证据 #6 印证**：调度失败事件多次发生，表明调度失败并非偶发。

### 缺失证据
| 证据 | 级别 | 影响 |
|------|------|------|
| Pod 的 Affinity/AntiAffinity 配置 | 中 | 无法确认是否存在其他调度约束 |
| PVC/PV 状态 | 中 | 无法确认是否存在存储依赖问题 |

---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod 的 nodeSelector 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label'，而集群中的节点都没有该标签，导致调度失败。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 调度器尝试为 Pod 分配节点，但所有节点均不满足 nodeSelector 条件。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Pod 无法被调度，处于 Pending 状态。                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 Pending，且调度失败事件持续出现。                    │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (FailedScheduling 事件)、证据 #2 (nodeSelector 配置) 和证据 #3 (节点标签)，问题的根本原因是**Pod 的 nodeSelector 指定了一个不存在的标签 `aiops.e2e/nonexistent-node-label`**，而集群中没有任何节点具有该标签，导致调度器无法找到合适的节点来运行该 Pod。

**置信度**：高 (90%)
- ✅ 事件日志明确指出调度失败原因
- ✅ nodeSelector 配置与节点标签不匹配
- ✅ 问题在多次调度尝试中持续出现
- ⚠️ 缺少 Affinity/AntiAffinity 信息，无法确认是否存在其他调度限制

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 移除或修改 nodeSelector 配置**
```bash
kubectl patch pod rc-pending-nodeselector -n aiops-e2e -p '{"spec":{"nodeSelector":{}}}' --type=merge
```
*依据*：当前 nodeSelector 不匹配任何节点，建议移除或修改为存在标签的节点选择器

**2. [可选] 在节点上添加匹配标签**
```bash
kubectl label nodes <node-name> aiops.e2e/nonexistent-node-label=true
```
*目的*：如果希望保留 nodeSelector 配置，可手动为节点添加匹配标签

**3. [可选] 查看调度失败事件详细日志**
```bash
kubectl describe pod rc-pending-nodeselector -n aiops-e2e | grep -A 5 "FailedScheduling"
```
*目的*：确认调度失败的详细原因

### 后续优化
1. **验证调度器行为**：确认调度器是否正确处理其他调度约束（如 affinity、taint）
2. **标签管理规范**：确保 nodeSelector 使用的标签在节点上存在，或考虑使用更灵活的调度策略（如 nodeAffinity）
3. **文档更新**：记录该问题作为调度配置的典型案例

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 是否调度成功 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running |
| 2. 确认 Pod 是否分配到节点 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o jsonpath='{.spec.nodeName}'` | 返回节点名称 |
| 3. 检查调度失败事件是否消失 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | 无 FailedScheduling 事件 |

---
## ⚠️ 注意事项
- 如果问题仍然存在，请检查是否还有其他调度约束（如 affinity、taint）影响调度
- 如果使用 nodeAffinity，建议使用更灵活的 `preferredDuringSchedulingIgnoredDuringExecution` 策略
- 建议对调度器配置进行审查，确保调度策略符合实际环境需求

---

## 📊 性能统计

├─ 总耗时: 7.0m
├─ 问题定位: 43.9s (10%) ✅
├─ 证据链采集: 95.1s (23%) ✅
├─ 根因分析: 118.1s (28%) ✅
├─ 汇总总结: 164.8s (39%) ✅
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
