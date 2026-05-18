======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 36c5a2ce8e8341da]

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
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
11m (x21 over 111m)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE    IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          116m   <none>   <none> 
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   230d   v1.26.8  
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
node1   Ready    <none>   230d   v1.26.8   10.2.0.49     <
   💭 [问题定位] 调用工具: kubectl_get_by_name
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (3m 39.2s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'Pod 节点亲和性/选择器不匹配', 'probability': '高', 'reason': "Events 显示 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector，表明 Pod 的 node affinity/selector 与节点标签不匹配。"}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}]
   reasoning=当前环境中存在一个仍处于 Pending 状态的 Pod，其 pod_abnormal_type 为 PendingUnschedulable，属于 L1 层级的根因。根据事件信息，Pod 无法调度的原因是 node(s) didn't match Pod's node affinity/selector。此外，所有节点状态均为 Ready，未发现 L0 层级的问题。因此，当前异常的根因归类为 L1。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "", "confidence": 0.5, "reasoning": "当前环境中存在一个仍处于 Pending 状态的 Pod，其 pod_abnormal_type 为 PendingUnschedulable，属于 L1 层级的根因。根据事件信息，Pod 无法调度的原因是 node(s) didn't match Pod's node affinity/selector。此外，所有节点状态均为 Ready，未发现 L0 层级的问题。因此，当前异常的根因归类为 L1。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Pod 节点亲和性/选择器不匹配", "probability": "高", "reason": "Events 显示 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector，表明 Pod 的 node affinity/selector 与节点标签不匹配。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                115m   <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/36c5a2ce8e8341da/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/36c5a2ce8e8341da/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/36c5a2ce8e8341da/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE    IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          121m   <none>   <none> 
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
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [证据链采集] ### 证据总结

#### 已采集证据
1. **Pod 配置验证**：通过 `kubectl_get_yaml` 读取了 Pod `rc-pending-nodeselector` 的完整配置，确认其 `nodeSelector` 设置为 `aiops.e2e/nonexistent-node-label: "true"`。此标签在当前节点上不存在，导致 Pod 无法调度。
2. **节点状态验证**：通过 `kubectl_get_by_kind_in_cluster` 检查了所有节点的状态，确认所有节点均为 `Ready`，且没有节点处于 `Unschedulable` 或 `NotReady` 状态。
3. **节点标签验证**：通过 `kubectl_get_by_kind_in_cluster` 检查了节点的标签信息，确认所有节点均没有 `aiops.e2e/nonexistent-node-label: "true"` 这一标签。

#### 未采集证据
- 无进一步的 PVC/PV 验证需求，因为事件中未提示 PVC 未绑定问题。
- 无 taint/toleration 验证需求，因为事件中明确指出问题与 nodeSelector 不匹配有关。

#### 冲突证据
- 无冲突证据，所有工具调用均成功，且结果一致。

### 结论
当前 Pod `rc-pending-nodeselector` 无法调度的根本原因是其 `nodeSelector` 设置的标签 `aiops.e2e/nonexistent-node-label: "true"` 在任何节点上都不存在。建议检查 Pod 的 `nodeSelector` 配置，并确保目标节点上有对应的标签。
   ✅ [证据链采集] 完成 (4m 47.6s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod rc-pending-nodeselector 的详细信息，包括其 nodeSelector 和 affinity 设置","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"name":"rc-pending-nodeselector","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"验证 Pod 的 nodeSelector 和 affinity 设置是否与节点标签匹配","evidence_type":"configuration","target_scope":"Pod/rc-pending-nodeselector","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"检查节点标签是否与 Pod 的 nodeSelector/affinity 匹配","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o json","tool_args":{"kind":"nodes","output_format":"json"},"purpose":"检查节点标签是否与 Pod 的 nodeSelector/affinity 匹配","evidence_type":"configuration","target_scope":"nodes","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                      READY   STATUS    RESTARTS   AGE    IP       NODE     NOMINATED NODE   READINESS GATES   LABELS\nrc-pending-nodeselector   0/1     Pending   0          121m   <none>   <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/36c5a2ce8e8341da/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/36c5a2ce8e8341da/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/36c5a2ce8e8341da/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/36c5a2ce8e8341da/tools/002-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/36c5a2ce8e8341da/tools/002-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/36c5a2ce8e8341da/tools/002-evidence-kubectl_get_by_kind_in_cluster.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-fsdjk\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/36c5a2ce8e8341da/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/36c5a2ce8e8341da/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/36c5a2ce8e8341da/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/36c5a2ce8e8341da/tools/004-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/36c5a2ce8e8341da/tools/004-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/36c5a2ce8e8341da/tools/004-evidence-kubectl_get_by_kind_in_cluster.summary.txt"}],"llm_analysis":"### 证据总结\n\n#### 已采集证据\n1. **Pod 配置验证**：通过 `kubectl_get_yaml` 读取了 Pod `rc-pending-nodeselector` 的完整配置，确认其 `nodeSelector` 设置为 `aiops.e2e/nonexistent-node-label: \"true\"`。此标签在当前节点上不存在，导致 Pod 无法调度。\n2. **节点状态验证**：通过 `kubectl_get_by_kind_in_cluster` 检查了所有节点的状态，确认所有节点均为 `Ready`，且没有节点处于 `Unschedulable` 或 `NotReady` 状态。\n3. **节点标签验证**：通过 `kubectl_get_by_kind_in_cluster` 检查了节点的标签信息，确认所有节点均没有 `aiops.e2e/nonexistent-node-label: \"true\"` 这一标签。\n\n#### 未采集证据\n- 无进一步的 PVC/PV 验证需求，因为事件中未提示 PVC 未绑定问题。\n- 无 taint/toleration 验证需求，因为事件中明确指出问题与 nodeSelector 不匹配有关。\n\n#### 冲突证据\n- 无冲突证据，所有工具调用均成功，且结果一致。\n\n### 结论\n当前 Pod `rc-pending-nodeselector` 无法调度的根本原因是其 `nodeSelector` 设置的标签 `aiops.e2e/nonexistent-node-label: \"true\"` 在任何节点上都不存在。建议检查 Pod 的 `nodeSelector` 配置，并确保目标节点上有对应的标签。","collection_summary":"计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 10 个，匹配计划 2 个，未规划证据 8 个","plan_total":2,"plan_collected":2,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":10,"matched_tool_count":2,"unplanned_tool_count":8,"evidence_inventory":[{"id":"e1","description":"获取 Pod rc-pending-nodeselector 的详细信息，包括其 nodeSelector 和 affinity 设置","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"验证 Pod 的 nodeSelector 和 affinity 设置是否与节点标签匹配","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"检查节点标签是否与 Pod 的 nodeSelector/affinity 匹配","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o json","purpose":"检查节点标签是否与 Pod 的 nodeSelector/affinity 匹配","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/2 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 获取 Pod rc-pending-nodeselector 的详细信息，包括其 node... | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e2 | important | ✅ | kubectl_get_by_kind_in_cl... | 检查节点标签是否与 Pod 的 nodeSelector/affinity 匹配 | `kubectl get nodes -o json` |

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (11m 1.4s)
   📤 → 下游数据: root_cause=当前 Pod rc-pending-nodeselector 无法调度的根本原因是其 nodeSelector 设置为 aiops.e2e/nonexistent-node-label: "true"，但该标签在任何节点上都不存在。建议检查 Pod 的 nodeSelector 配置，并确保目标节点上有对应的标签。
   confidence=90%
   causal_chain={"root_cause": "Pod 的 nodeSelector 设置为 aiops.e2e/nonexistent-node-label: \"true\"，但该标签在任何节点上都不存在，导致 Pod 无法调度。", "intermediate_causes": ["Pod 的 nodeSelector 设置不匹配任何节点的标签。", "所有节点均为 Ready 状态，但没有节点包含 aiops.e2e/nonexistent-node-label: \"true\" 这一标签。"], "immediate_causes": ["kubectl_events 显示 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。"], "symptoms": ["Pod rc-pending-nodeselector 处于 Pending 状态。", "Pod 的 pod_abnormal_type 为 PendingUnschedulable。"]}
   rca_analysis={"phenomenon": "当前环境中存在一个仍处于 Pending 状态的 Pod，其 pod_abnormal_type 为 PendingUnschedulable，属于 L1 层级的根因。", "evidence_inventory": [{"id": "e1", "description": "获取 Pod rc-pending-nodeselector 的详细信息，包括其 nodeSelector 和 affinity 设置", "level": "critical", "value": "NAME                      READY   STATUS    RESTARTS   AGE    IP       NODE     NOMINATED NODE   READINESS GATES   LABELS\nrc-pending-nodeselector   0/1     Pending   0          121m   <none>   <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"}, {"id": "e2", "description": "检查节点标签是否与 Pod 的 nodeSelector/affinity 匹配", "level": "important", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubern"}, {"id": "layer_1", "description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "level": "important", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Pending': 1, 'Running': 46}\nNAMESPACE     NAME                                                READY   STATUS      RESTARTS         AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\n# 异常行\naiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                115m   <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type"}, {"id": "layer_2", "description": "上游已验证工具结果: kubectl_events", "level": "important", "value": "kubectl_events 摘要:\n关键诊断行:\n11m (x21 over 111m)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.."}, {"id": "layer_3", "description": "上游已验证工具结果: kubectl_get_by_name", "level": "important", "value": "NAME                      READY   STATUS    RESTARTS   AGE    IP       NODE     NOMINATED NODE   READINESS GATES   LABELS\nrc-pending-nodeselector   0/1     Pending   0          116m   <none>   <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"}, {"id": "layer_4", "description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "level": "important", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubern"}, {"id": "layer_5", "description": "上游已验证工具结果: kubectl_get_by_name", "level": "important", "value": "NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-"}, {"id": "layer_6", "description": "上游已验证工具结果: kubectl_get_by_name", "level": "important", "value": "NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nnode1   Ready    <none>   230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux"}], "evidence_analysis": [{"id": "e1", "description": "获取 Pod rc-pending-nodeselector 的详细信息，包括其 nodeSelector 和 affinity 设置", "level": "critical", "value": "Pod rc-pending-nodeselector 的 nodeSelector 设置为 aiops.e2e/nonexistent-node-label: \"true\"，但该标签在任何节点上都不存在。"}, {"id": "e2", "description": "检查节点标签是否与 Pod 的 nodeSelector/affinity 匹配", "level": "important", "value": "所有节点均为 Ready 状态，且没有节点包含 aiops.e2e/nonexistent-node-label: \"true\" 这一标签。"}, {"id": "layer_2", "description": "上游已验证工具结果: kubectl_events", "level": "important", "value": "kubectl_events 显示 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector，表明 Pod 的 nodeSelector 与节点标签不匹配。"}], "causal_chain": {"root_cause": "Pod 的 nodeSelector 设置为 aiops.e2e/nonexistent-node-label: \"true\"，但该标签在任何节点上都不存在，导致 Pod 无法调度。", "intermediate_causes": ["Pod 的 nodeSelector 设置不匹配任何节点的标签。", "所有节点均为 Ready 状态，但没有节点包含 aiops.e2e/nonexistent-node-label: \"true\" 这一标签。"], "immediate_causes": ["kubectl_events 显示 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。"], "symptoms": ["Pod rc-pending-nodeselector 处于 Pending 状态。", "Pod 的 pod_abnormal_type 为 PendingUnschedulable。"]}, "root_cause": "当前 Pod rc-pending-nodeselector 无法调度的根本原因是其 nodeSelector 设置为 aiops.e2e/nonexistent-node-label: \"true\"，但该标签在任何节点上都不存在。建议检查 Pod 的 nodeSelector 配置，并确保目标节点上有对应的标签。", "root_cause_summary": "当前 Pod rc-pending-nodeselector 无法调度的根本原因是其 nodeSelector 设置为 aiops.e2e/nonexistent-node-label: \"true\"，但该标签在任何节点上都不存在。建议检查 Pod 的 nodeSelector 配置，并确保目标节点上有对应的标签。", "confidence": 0.9, "confidence_reason": "有直接证据表明 Pod 的 nodeSelector 与节点标签不匹配，因果链清晰。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [], "limitations": "无限制。", "llm_raw_analysis": "当前 Pod rc-pending-nodeselector 无法调度的根本原因是其 nodeSelector 设置为 aiops.e2e/nonexistent-node-label: \"true\"，但该标签在任何节点上都不存在。建议检查 Pod 的 nodeSelector 配置，并确保目标节点上有对应的标签。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 当前 Pod rc-pending-nodeselector 无法调度的根本原因是其 nodeSelector 设置为 aiops.e2e/nonexistent-node-label: "true"，但该标签在任何节点上都不存在。建议检查 Pod 的 nodeSelector 配置，并确保目标节点...
   置信度: 90%
   🔗 因果链:
     根本原因: Pod 的 nodeSelector 设置为 aiops.e2e/nonexistent-node-label: "true"，但该标签在任何节点上都不存在，导致 Pod 无法调度。


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
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (9m 22.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5206 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 28m 50.9s
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
| **兼容归因层** | L1 |
| **问题分类** | Pod 无法调度（NodeSelector 不匹配） |
| **置信度** | 高 (90%) |
| **证据完整度** | 2/2 (100%) |

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
| 错误信息 | 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector |

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: Pending` | Pod 无法调度 |
| 2 | 事件日志 | `kubectl events` | `Warning FailedScheduling Pod/rc-pending-nodeselector 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | Pod 的 nodeSelector 与节点标签不匹配 |
| 3 | Pod YAML 配置 | `kubectl get pod -o yaml` | `nodeSelector: aiops.e2e/nonexistent-node-label: "true"` | Pod 要求一个不存在的节点标签 |
| 4 | 节点标签 | `kubectl get node` | `所有节点标签均不包含 aiops.e2e/nonexistent-node-label` | 无节点满足 nodeSelector 要求 |

### 证据关联分析
- **证据 #2 + #3 印证**：`nodeSelector: aiops.e2e/nonexistent-node-label: "true"` + `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` → 该 Pod 的 nodeSelector 设置为一个不存在的节点标签，导致无法调度
- **证据链**：Pod 的 nodeSelector 设置为不存在的标签 → 无节点满足调度条件 → Pod 保持 Pending 状态

---

## 🎯 根因分析
### 因果链
```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                             │
│ Pod 的 nodeSelector 设置为 aiops.e2e/nonexistent-node-label: "true"，但该标签在任何节点上都不存在。 │
└──────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                             │
│ 无节点满足 nodeSelector 条件，导致调度失败                                           │
└──────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                             │
│ Pod 无法调度（Events 显示 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector） │
└──────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                         │
│ Pod 状态为 Pending，且未调度到任何节点                                               │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2 (`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`) 和证据 #3 (`nodeSelector: aiops.e2e/nonexistent-node-label: "true"`)，问题的根本原因是**Pod 的 nodeSelector 设置为一个不存在的节点标签**，导致无法调度。
**置信度**：高 (90%)
- ✅ 事件日志明确指出 nodeSelector 不匹配
- ✅ Pod YAML 明确指定了不存在的标签
- ✅ 节点标签验证确认该标签不存在

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 修正 Pod 的 nodeSelector**
```bash
kubectl edit pod rc-pending-nodeselector -n aiops-e2e
```
*修改 `nodeSelector` 配置，使用实际存在的节点标签。例如：*
```yaml
spec:
  nodeSelector:
    kubernetes.io/role: worker
```
*依据*：当前 `aiops.e2e/nonexistent-node-label` 不存在，需替换为实际存在的标签

**2. [可选] 添加缺失的节点标签**
```bash
kubectl label nodes <node-name> aiops.e2e/nonexistent-node-label=true
```
*依据*：如果希望保留原配置，可为节点添加缺失的标签

### 后续优化
1. **标签管理规范**：确保 nodeSelector 使用的标签在节点上存在
2. **调度策略检查**：验证其他 Pod 是否也存在 nodeSelector 不匹配的问题
3. **Pod 模板审查**：检查 Deployment/ReplicaSet 中 Pod 模板的 nodeSelector 设置

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 调度 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running |
| 2. 检查节点标签 | `kubectl get node` | 存在 `aiops.e2e/nonexistent-node-label: "true"`（如果选择添加标签） |
| 3. 检查事件日志 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | 无 `FailedScheduling` 事件 |

---

## ⚠️ 注意事项
- 如果修改 nodeSelector 后 Pod 仍处于 Pending 状态，请检查其他调度约束（如 taint、affinity、资源限制等）
- 如果添加标签，请确保标签名称和值与 Pod 的 nodeSelector 严格匹配
- 如果集群中存在多个节点，请确保至少一个节点满足 nodeSelector 条件

---

## 📎 附录：完整证据原始数据
### [layer] kubectl_get_by_kind_in_cluster
```
kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Pending': 1, 'Running': 46}
NAMESPACE     NAME                                                READY   STATUS      RESTARTS      
aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                115m   <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true
```

### [layer] kubectl_events
```
kubectl_events 摘要:
关键诊断行:
11m (x21 over 111m)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3
```

### [evidence] kubectl_get_yaml
```
kind: Pod
name: rc-pending-nodeselector
namespace: aiops-e2e
spec:
  nodeSelector:
    aiops.e2e/nonexistent-node-label: "true"
```

---

## 📊 性能统计

├─ 总耗时: 28.8m
├─ 问题定位: 219.2s (13%) ✅
├─ 证据链采集: 287.6s (17%) ✅
├─ 根因分析: 661.4s (38%) ✅
├─ 汇总总结: 562.7s (33%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 12 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 12 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
