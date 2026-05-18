======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: ce0104969c37406a]

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
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          69m   <none>   <none>   
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  24m (x9 over 64m)  default-scheduler  0/3 nodes are available: 
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          69m   <none>   <none>   
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  24m (x9 over 64m)  default-scheduler  0/3 nodes are available: 
   💭 [问题定位] 调用工具: kubectl_get_by_name
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (59.1s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'Node selector/affinity 不匹配', 'probability': '高', 'reason': 'Pod 的 node selector/affinity 不匹配任何节点，导致调度失败。'}, {'scenario': '节点 taint 未被容忍', 'probability': '中', 'reason': '如果节点设置了 taint，但 Pod 没有相应的 toleration，也可能导致调度失败。'}, {'scenario': '节点资源不足', 'probability': '低', 'reason': '节点资源不足也可能导致调度失败，但当前分析中没有提到资源不足。'}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}]
   reasoning=根据分析，当前有一个 Pod 处于 Pending 状态，且其事件信息表明调度失败，原因是节点不匹配 Pod 的 node affinity/selector。这表明调度器无法找到符合该 Pod 调度约束的节点，属于 L1 层级问题（Node LostOrUnknown / TerminatingStuck 或调度失败）。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "Node / Scheduling Issues", "confidence": 0.95, "reasoning": "根据分析，当前有一个 Pod 处于 Pending 状态，且其事件信息表明调度失败，原因是节点不匹配 Pod 的 node affinity/selector。这表明调度器无法找到符合该 Pod 调度约束的节点，属于 L1 层级问题（Node LostOrUnknown / TerminatingStuck 或调度失败）。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Node selector/affinity 不匹配", "probability": "高", "reason": "Pod 的 node selector/affinity 不匹配任何节点，导致调度失败。"}, {"scenario": "节点 taint 未被容忍", "probability": "中", "reason": "如果节点设置了 taint，但 Pod 没有相应的 toleration，也可能导致调度失败。"}, {"scenario": "节点资源不足", "probability": "低", "reason": "节点资源不足也可能导致调度失败，但当前分析中没有提到资源不足。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                69m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/ce0104969c37406a/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/ce0104969c37406a/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/ce0104969c37406a/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  26m (x9 over 66m)  default-scheduler  0/3 nodes are available: 
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
   💭 [证据链采集] 已采集证据：
1. **critical**: `kubectl describe pod` 显示 Pod `rc-pending-nodeselector` 的调度失败原因为 `nodeSelector` 不匹配任何节点。
2. **important**: `kubectl get nodes` 显示所有节点状态为 `Ready`，但未发现标签 `aiops.e2e/nonexistent-node-label`。
3. **important**: `kubectl get pod -o yaml` 显示 Pod 配置中 `nodeSelector` 设置了不存在的标签 `aiops.e2e/nonexistent-node-label`。

结论：
- Pod 无法调度的主要原因是其 `nodeSelector` 中指定的标签 `aiops.e2e/nonexistent-node-label` 不存在于任何节点上，导致调度失败。
- 未发现其他并发异常状态，如 Terminating、VolumeMountFailed 等。
- 无冲突证据。
   ✅ [证据链采集] 完成 (1m 31.0s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod 'rc-pending-nodeselector' 的详细调度失败信息，包括 nodeSelector/affinity 是否匹配节点","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-pending-nodeselector"},"purpose":"获取 Pod 调度失败的具体原因，确认 nodeSelector/affinity 是否匹配节点","evidence_type":"Pod Events","target_scope":"aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"验证集群节点状态和标签，确认是否匹配 Pod 的 nodeSelector/affinity","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o json","tool_args":{},"purpose":"获取集群节点的标签和状态，确认是否匹配 Pod 的 nodeSelector/affinity","evidence_type":"Node Labels/Status","target_scope":"Cluster Nodes","acceptable_tools":["kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true},{"id":"e3","description":"验证 Pod 'rc-pending-nodeselector' 的完整 YAML 配置，确认 nodeSelector/affinity/tolerations 等字段","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"namespace":"aiops-e2e","name":"rc-pending-nodeselector"},"purpose":"获取 Pod 的完整配置，确认 nodeSelector/affinity/tolerations 等字段是否正确设置","evidence_type":"Pod YAML Configuration","target_scope":"aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  26m (x9 over 66m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ce0104969c37406a/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ce0104969c37406a/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ce0104969c37406a/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ce0104969c37406a/tools/002-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ce0104969c37406a/tools/002-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ce0104969c37406a/tools/002-evidence-kubectl_get_by_kind_in_cluster.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-fsdjk\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ce0104969c37406a/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ce0104969c37406a/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ce0104969c37406a/tools/003-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"已采集证据：\n1. **critical**: `kubectl describe pod` 显示 Pod `rc-pending-nodeselector` 的调度失败原因为 `nodeSelector` 不匹配任何节点。\n2. **important**: `kubectl get nodes` 显示所有节点状态为 `Ready`，但未发现标签 `aiops.e2e/nonexistent-node-label`。\n3. **important**: `kubectl get pod -o yaml` 显示 Pod 配置中 `nodeSelector` 设置了不存在的标签 `aiops.e2e/nonexistent-node-label`。\n\n结论：\n- Pod 无法调度的主要原因是其 `nodeSelector` 中指定的标签 `aiops.e2e/nonexistent-node-label` 不存在于任何节点上，导致调度失败。\n- 未发现其他并发异常状态，如 Terminating、VolumeMountFailed 等。\n- 无冲突证据。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 9/9 项，完整度 100%；实际执行工具 9 个，匹配计划 3 个，未规划证据 6 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":9,"environment_evidence_collected":9,"environment_evidence_completeness":1.0,"executed_tool_count":9,"matched_tool_count":3,"unplanned_tool_count":6,"evidence_inventory":[{"id":"e1","description":"验证 Pod 'rc-pending-nodeselector' 的详细调度失败信息，包括 nodeSelector/affinity 是否匹配节点","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"获取 Pod 调度失败的具体原因，确认 nodeSelector/affinity 是否匹配节点","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"验证集群节点状态和标签，确认是否匹配 Pod 的 nodeSelector/affinity","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o json","purpose":"获取集群节点的标签和状态，确认是否匹配 Pod 的 nodeSelector/affinity","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"验证 Pod 'rc-pending-nodeselector' 的完整 YAML 配置，确认 nodeSelector/affinity/tolerations 等字段","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"获取 Pod 的完整配置，确认 nodeSelector/affinity/tolerations 等字段是否正确设置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证 Pod 'rc-pending-nodeselector' 的详细调度失败信息，包括... | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_get_by_kind_in_cl... | 验证集群节点状态和标签，确认是否匹配 Pod 的 nodeSelector/affinity | `kubectl get nodes -o json` |
   | e3 | important | ✅ | kubectl_get_yaml | 验证 Pod 'rc-pending-nodeselector' 的完整 YAML 配置，... | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (28.9s)
   📤 → 下游数据: root_cause=Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label'，导致调度失败。所有节点状态为 Ready，但未发现该标签。
   confidence=95%
   causal_chain={"root_cause": "Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label'，导致调度失败", "intermediate_causes": ["调度器无法找到符合 Pod 调度约束的节点", "节点状态为 Ready，但未满足 Pod 的 nodeSelector 条件"], "direct_causes": ["Pod 无法调度的主要原因是其 nodeSelector 中指定的标签不存在于任何节点上"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"e1": "Pod 'rc-pending-nodeselector' 的详细调度失败信息表明 nodeSelector 不匹配任何节点"}, {"e2": "集群节点状态为 Ready，但未发现标签 'aiops.e2e/nonexistent-node-label'"}, {"e3": "Pod 'rc-pending-nodeselector' 的 YAML 配置中 nodeSelector 设置了不存在的标签"}], "evidence_analysis": [{"e1": "Pod 'rc-pending-nodeselector' 的调度失败原因为 nodeSelector 不匹配任何节点"}, {"e2": "所有节点状态为 Ready，但未发现标签 'aiops.e2.e/nonexistent-node-label'"}, {"e3": "Pod 配置中 'nodeSelector' 设置了不存在的标签 'aiops.e2e/nonexistent-node-label'"}], "causal_chain": {"root_cause": "Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label'，导致调度失败", "intermediate_causes": ["调度器无法找到符合 Pod 调度约束的节点", "节点状态为 Ready，但未满足 Pod 的 nodeSelector 条件"], "direct_causes": ["Pod 无法调度的主要原因是其 nodeSelector 中指定的标签不存在于任何节点上"]}, "root_cause": "Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label'，导致调度失败。所有节点状态为 Ready，但未发现该标签。", "root_cause_summary": "Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label'，导致调度失败。所有节点状态为 Ready，但未发现该标签。", "confidence": 0.95, "confidence_reason": "有直接证据表明 Pod 的 nodeSelector 不匹配任何节点，因果链清晰", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [], "limitations": "无冲突证据，所有证据指向同一原因", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label'，导致调度失败。所有节点状态为 Ready，但未发现该标签。
   置信度: 95%
   🔗 因果链:
     根本原因: Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label'，导致调度失败


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 44.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3980 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 43.7s
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
| **兼容归因层** | L1 - 调度失败 |
| **问题分类** | 调度失败（nodeSelector/affinity 不匹配） |
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
| 错误信息 | FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `Status: Pending, Reason: FailedScheduling` | Pod 处于调度失败状态 |
| 2 | 调度失败事件 | `kubectl describe pod` | `Warning  FailedScheduling  24m (x9 over 64m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 明确指出 nodeSelector/affinity 不匹配 |
| 3 | Pod YAML 配置 | `kubectl get pod -o yaml` | `nodeSelector: aiops.e2e/nonexistent-node-label` | Pod 设置了不存在的 nodeSelector 标签 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 Pending，且事件中包含 `FailedScheduling`，说明调度失败。
- **证据 #2 + #3 印证**：调度失败原因是 nodeSelector 不匹配，进一步确认 Pod 配置了不存在的标签 `aiops.e2e/nonexistent-node-label`。
- **证据链**：Pod 设置了不存在的 nodeSelector 标签 → 调度器找不到匹配的节点 → Pod 无法调度 → 状态为 Pending。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 无 | N/A | 无缺失证据，证据完整度为 100% |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label'，导致调度失败。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 调度器检查 nodeSelector 与节点标签匹配失败，无法找到匹配节点。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 Pending，持续失败，无法调度。                        │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2 (`FailedScheduling: 0/3 nodes are available`) 和证据 #3 (`nodeSelector: aiops.e2e/nonexistent-node-label`)，问题的根本原因是**Pod 设置了不存在的 nodeSelector 标签 `aiops.e2e/nonexistent-node-label`**，导致调度器无法找到匹配的节点，从而调度失败。

**置信度**：高 (95%)
- ✅ `kubectl describe pod` 明确显示调度失败
- ✅ `kubectl get pod -o yaml` 显示 nodeSelector 设置了不存在的标签
- ✅ 所有节点状态为 Ready，无资源不足问题

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 移除或修改 nodeSelector**

```bash
kubectl edit pod rc-pending-nodeselector -n aiops-e2e
```

*操作*：将 `nodeSelector: aiops.e2e/nonexistent-node-label` 修改为实际存在的节点标签，或直接删除该字段。

**2. [可选] 查看调度失败事件详细信息**

```bash
kubectl describe pod rc-pending-nodeselector -n aiops-e2e
```

*目的*：确认调度失败的完整信息，用于后续排查。

### 后续优化

1. **标签管理**：确保 nodeSelector 使用的标签在节点上真实存在。
2. **Pod 配置校验**：在提交 Pod 前检查 `nodeSelector`、`affinity` 和 `toleration` 是否合理。
3. **调度策略优化**：使用更灵活的调度策略（如 `preferredDuringSchedulingIgnoredDuringExecution`）以避免调度失败。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running |
| 2. 检查调度事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | 无 FailedScheduling 事件 |
| 3. 检查节点标签 | `kubectl get nodes --show-labels` | 确认 nodeSelector 使用的标签存在 |

---

## ⚠️ 注意事项

- 如果 nodeSelector 非常关键，建议先在测试环境中验证配置。
- 如果节点标签管理混乱，建议统一管理标签策略以避免类似问题。
- 如果 Pod 是由 Deployment 或 StatefulSet 创建的，建议修改控制器配置以避免重复调度失败。

---

---

## 📊 性能统计

├─ 总耗时: 4.7m
├─ 问题定位: 59.1s (21%) ✅
├─ 证据链采集: 91.0s (32%) ✅
├─ 根因分析: 28.9s (10%) ✅
├─ 汇总总结: 104.7s (37%) ✅
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
