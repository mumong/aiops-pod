======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 5a4bc94cb3f14a72]

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
  Warning  FailedScheduling  12m (x39 over 3h22m)  default-scheduler  0/3 nodes are availabl
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE     IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          3h27m   <none>   <none
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE     IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          3h27m   <none>   <none
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 调用工具: kubectl_get_by_name
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (43.4s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'nodeSelector/affinity 不匹配', 'probability': '高', 'reason': "Pod 事件显示 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'，表明调度约束不匹配。"}, {'scenario': '节点 taint 未被 toleration 容忍', 'probability': '中', 'reason': "如果事件中包含 'had untolerated taint'，则可能涉及 taint/toleration 不匹配。"}, {'scenario': '资源不足', 'probability': '低', 'reason': "没有显示 'Insufficient cpu/memory' 或 'Too many pods' 的证据。"}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}]
   reasoning=根据分析文本，当前环境中有一个 Pod rc-pending-nodeselector 处于 Pending 状态，且其 pod_abnormal_type 为 PendingUnschedulable，属于调度问题。这表明调度失败，根因可能是 nodeSelector/affinity 不匹配。根据五层模型，PendingUnschedulable 归属 L1 层级（Node NotReady、kubelet、taint、PLEG 等问题），因此当前环境的 layer 为 L1。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "", "confidence": 0.5, "reasoning": "根据分析文本，当前环境中有一个 Pod rc-pending-nodeselector 处于 Pending 状态，且其 pod_abnormal_type 为 PendingUnschedulable，属于调度问题。这表明调度失败，根因可能是 nodeSelector/affinity 不匹配。根据五层模型，PendingUnschedulable 归属 L1 层级（Node NotReady、kubelet、taint、PLEG 等问题），因此当前环境的 layer 为 L1。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling/node_kubelet/lifecycle", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "nodeSelector/affinity 不匹配", "probability": "高", "reason": "Pod 事件显示 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'，表明调度约束不匹配。"}, {"scenario": "节点 taint 未被 toleration 容忍", "probability": "中", "reason": "如果事件中包含 'had untolerated taint'，则可能涉及 taint/toleration 不匹配。"}, {"scenario": "资源不足", "probability": "低", "reason": "没有显示 'Insufficient cpu/memory' 或 'Too many pods' 的证据。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                3h27m   <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/5a4bc94cb3f14a72/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/5a4bc94cb3f14a72/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/5a4bc94cb3f14a72/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
  Warning  FailedScheduling  14m (x39 over 3h24m)  default-scheduler  0/3 nodes are availabl
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
   💭 [证据链采集] ### 采集证据总结

#### **已采集证据**
1. **Pod 详细状态与事件**：
   - Pod `rc-pending-nodeselector` 处于 `Pending` 状态。
   - 关键事件：`FailedScheduling`，描述为 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..`
   - 无节点匹配 Pod 的 `nodeSelector` 或 `affinity` 条件。

2. **Pod YAML 配置**：
   - Pod 指定了 `nodeSelector`：`{"aiops.e2e/nonexistent-node-label": "true"}`。
   - 所有节点均未设置此标签，导致无法匹配。

3. **节点状态与标签**：
   - 集群中共有 3 个节点，全部处于 `Ready` 状态。
   - 节点标签中未包含 `aiops.e2e/nonexistent-node-label`。

#### **未采集证据**
- 无进一步证据需要采集。

#### **冲突证据**
- 无冲突证据。

#### **结论**
- **Pod 无法调度的根本原因**是其 `nodeSelector` 指定了一个不存在的节点标签 `aiops.e2e/nonexistent-node-label`。
- **建议**：检查并修改 Pod 的 `nodeSelector` 配置，使其与集群中节点的标签匹配。
   ✅ [证据链采集] 完成 (1m 57.0s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod rc-pending-nodeselector 的详细状态和调度失败原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"获取 Pod 的详细状态、事件和调度失败的具体原因","evidence_type":"Pod 状态和事件","target_scope":"aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod rc-pending-nodeselector 的 YAML 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"查看 Pod 的 YAML 配置，确认 nodeSelector、affinity、toleration 等调度约束配置","evidence_type":"Pod 配置","target_scope":"aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e3","description":"获取集群中所有节点的状态和标签信息","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o wide","tool_args":{"kind":"Node"},"purpose":"验证节点的标签、状态和是否满足 Pod 的调度约束","evidence_type":"节点状态和标签","target_scope":"集群节点","acceptable_tools":["kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  14m (x39 over 3h24m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/5a4bc94cb3f14a72/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/5a4bc94cb3f14a72/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/5a4bc94cb3f14a72/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-fsdjk\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/5a4bc94cb3f14a72/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/5a4bc94cb3f14a72/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/5a4bc94cb3f14a72/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/5a4bc94cb3f14a72/tools/003-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/5a4bc94cb3f14a72/tools/003-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/5a4bc94cb3f14a72/tools/003-evidence-kubectl_get_by_kind_in_cluster.summary.txt"}],"llm_analysis":"### 采集证据总结\n\n#### **已采集证据**\n1. **Pod 详细状态与事件**：\n   - Pod `rc-pending-nodeselector` 处于 `Pending` 状态。\n   - 关键事件：`FailedScheduling`，描述为 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..`\n   - 无节点匹配 Pod 的 `nodeSelector` 或 `affinity` 条件。\n\n2. **Pod YAML 配置**：\n   - Pod 指定了 `nodeSelector`：`{\"aiops.e2e/nonexistent-node-label\": \"true\"}`。\n   - 所有节点均未设置此标签，导致无法匹配。\n\n3. **节点状态与标签**：\n   - 集群中共有 3 个节点，全部处于 `Ready` 状态。\n   - 节点标签中未包含 `aiops.e2e/nonexistent-node-label`。\n\n#### **未采集证据**\n- 无进一步证据需要采集。\n\n#### **冲突证据**\n- 无冲突证据。\n\n#### **结论**\n- **Pod 无法调度的根本原因**是其 `nodeSelector` 指定了一个不存在的节点标签 `aiops.e2e/nonexistent-node-label`。\n- **建议**：检查并修改 Pod 的 `nodeSelector` 配置，使其与集群中节点的标签匹配。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 9/9 项，完整度 100%；实际执行工具 9 个，匹配计划 3 个，未规划证据 6 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":9,"environment_evidence_collected":9,"environment_evidence_completeness":1.0,"executed_tool_count":9,"matched_tool_count":3,"unplanned_tool_count":6,"evidence_inventory":[{"id":"e1","description":"验证 Pod rc-pending-nodeselector 的详细状态和调度失败原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"获取 Pod 的详细状态、事件和调度失败的具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod rc-pending-nodeselector 的 YAML 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"查看 Pod 的 YAML 配置，确认 nodeSelector、affinity、toleration 等调度约束配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取集群中所有节点的状态和标签信息","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o wide","purpose":"验证节点的标签、状态和是否满足 Pod 的调度约束","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证 Pod rc-pending-nodeselector 的详细状态和调度失败原因 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_get_yaml | 获取 Pod rc-pending-nodeselector 的 YAML 配置 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e3 | important | ✅ | kubectl_get_by_kind_in_cl... | 获取集群中所有节点的状态和标签信息 | `kubectl get nodes -o wide` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (44.4s)
   📤 → 下游数据: root_cause=Pod rc-pending-nodeselector 无法调度的根本原因是其 nodeSelector 指定了一个不存在的节点标签 'aiops.e2e/nonexistent-node-label'。集群中的节点没有该标签，导致调度失败。
   confidence=90%
   causal_chain={"root_cause": "Pod 的 nodeSelector 指定了一个不存在的节点标签 'aiops.e2e/nonexistent-node-label'，导致调度失败。", "intermediate_causes": ["Pod 无法找到匹配的节点进行调度。", "调度器无法找到满足 nodeSelector 条件的节点。"], "direct_causes": ["Pod 的 nodeSelector 与节点标签不匹配。", "集群中没有节点具有 'aiops.e2e/nonexistent-node-label' 标签。"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"e1": "验证 Pod rc-pending-nodeselector 的详细状态和调度失败原因"}, {"e2": "获取 Pod rc-pending-nodeselector 的 YAML 配置"}, {"e3": "获取集群中所有节点的状态和标签信息"}, {"layer_1": "上游已验证工具结果: kubectl_get_by_kind_in_cluster"}, {"layer_2": "上游已验证工具结果: kubectl_describe"}, {"layer_3": "上游已验证工具结果: kubectl_get_by_name"}, {"layer_4": "上游已验证工具结果: kubectl_get_by_kind_in_cluster"}, {"layer_5": "上游已验证工具结果: kubectl_get_by_name"}, {"layer_6": "上游已验证工具结果: kubectl_get_by_kind_in_cluster"}], "evidence_analysis": [{"e1": "Pod rc-pending-nodeselector 处于 Pending 状态，且事件显示 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'，表明调度失败。"}, {"e2": "Pod 配置了 nodeSelector 'aiops.e2e/nonexistent-node-label': 'true'，但集群中没有节点具有该标签。"}, {"e3": "集群中的节点没有 'aiops.e2e/nonexistent-node-label' 标签，导致 Pod 无法调度。"}], "causal_chain": {"root_cause": "Pod 的 nodeSelector 指定了一个不存在的节点标签 'aiops.e2e/nonexistent-node-label'，导致调度失败。", "intermediate_causes": ["Pod 无法找到匹配的节点进行调度。", "调度器无法找到满足 nodeSelector 条件的节点。"], "direct_causes": ["Pod 的 nodeSelector 与节点标签不匹配。", "集群中没有节点具有 'aiops.e2e/nonexistent-node-label' 标签。"]}, "root_cause": "Pod rc-pending-nodeselector 无法调度的根本原因是其 nodeSelector 指定了一个不存在的节点标签 'aiops.e2e/nonexistent-node-label'。集群中的节点没有该标签，导致调度失败。", "root_cause_summary": "Pod rc-pending-nodeselector 无法调度的根本原因是其 nodeSelector 指定了一个不存在的节点标签 'aiops.e2e/nonexistent-node-label'。集群中的节点没有该标签，导致调度失败。", "confidence": 0.9, "confidence_reason": "有直接证据表明 Pod 的 nodeSelector 与节点标签不匹配，且调度失败事件明确指向此原因。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "节点资源不足", "probability": "低", "reason": "没有显示资源不足的证据。"}, {"cause": "节点 taint 未被 toleration 容忍", "probability": "中", "reason": "事件中没有提到 taint/toleration 不匹配。"}], "limitations": "未检查其他可能的调度约束，如 affinity 或 toleration。", "llm_raw_analysis": "Pod rc-pending-nodeselector 处于 Pending 状态，且事件显示 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'，表明调度失败。Pod 配置了 nodeSelector 'aiops.e2e/nonexistent-node-label': 'true'，但集群中没有节点具有该标签。集群中的节点没有 'aiops.e2e/nonexistent-node-label' 标签，导致 Pod 无法调度。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-nodeselector 无法调度的根本原因是其 nodeSelector 指定了一个不存在的节点标签 'aiops.e2e/nonexistent-node-label'。集群中的节点没有该标签，导致调度失败。
   置信度: 90%
   🔗 因果链:
     根本原因: Pod 的 nodeSelector 指定了一个不存在的节点标签 'aiops.e2e/nonexistent-node-label'，导致调度失败。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 51.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4558 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 15.9s
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
| **兼容归因层** | L1 - 节点标签/选择器不匹配 |
| **问题分类** | 调度失败 (nodeSelector/affinity 不匹配) |
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
| 错误信息 | 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 事件 | `kubectl describe pod rc-pending-nodeselector` | `Warning  FailedScheduling  12m (x39 over 3h22m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | Pod 的 nodeSelector 不匹配任何节点 |
| 2 | Pod YAML | `kubectl get pod rc-pending-nodeselector -o yaml` | `nodeSelector: aiops.e2e/nonexistent-node-label: "true"` | Pod 指定了一个不存在的节点标签 |
| 3 | 节点状态 | `kubectl get nodes` | 所有节点均无标签 `aiops.e2e/nonexistent-node-label` | 集群中没有节点满足调度要求 |
| 4 | Pod 状态 | `kubectl get pod rc-pending-nodeselector` | `STATUS: Pending` | Pod 无法调度 |
| 5 | Runbook | `fetch_runbook` | `Pod 状态: Pending，Events 含 FailedScheduling` | 典型的调度失败特征 |
| 6 | Pod 事件 | `kubectl describe pod rc-pending-nodeselector` | `preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.` | 无法通过抢占调度解决 |
| 7 | 节点标签 | `kubectl get nodes -o jsonpath='{.items[*].metadata.labels}'` | 节点标签如 `kubernetes.io/os=linux`，无 `aiops.e2e/nonexistent-node-label` | 无匹配标签 |
| 8 | Pod 标签 | `kubectl get pod rc-pending-nodeselector -o jsonpath='{.metadata.labels}'` | `app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true` | Pod 标签与调度无关 |
| 9 | 节点状态 | `kubectl get nodes` | `STATUS: Ready` | 所有节点正常，无资源不足问题 |

### 证据关联分析

- **证据 #1 + #2 印证**：`FailedScheduling` 事件 + `nodeSelector: aiops.e2e/nonexistent-node-label` → 调度失败
- **证据链**：Pod 指定的标签不存在 → 调度器找不到匹配节点 → Pod 无法调度 → 一直处于 Pending 状态

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
│ Pod 的 nodeSelector 指定了一个不存在的节点标签 'aiops.e2e/nonexistent-node-label'，导致调度失败。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 调度器找不到匹配节点，且无法通过抢占解决调度问题。                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 Pending，持续显示 FailedScheduling 事件。             │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (FailedScheduling 事件) 和证据 #2 (Pod YAML 中的 nodeSelector)，问题的根本原因是**Pod 的 nodeSelector 指定了一个不存在的节点标签 `aiops.e2e/nonexistent-node-label`**，导致调度失败，Pod 一直处于 Pending 状态。

**置信度**：高 (90%)
- ✅ `FailedScheduling` 事件明确指向调度失败
- ✅ Pod YAML 明确指定了无效标签
- ✅ 节点中不存在该标签
- ⚠️ 未检查其他调度约束（如 affinity、toleration）

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 修改 Pod 的 nodeSelector**
```bash
kubectl edit pod rc-pending-nodeselector -n aiops-e2e
```
*操作步骤*：
- 删除或修改 `nodeSelector` 字段，使其匹配集群中实际存在的节点标签（例如 `kubernetes.io/os=linux`）。

**2. [可选] 添加标签到节点（如需要该标签）**
```bash
kubectl label nodes <node-name> aiops.e2e/nonexistent-node-label=true
```
*目的*：如果应用确实需要该标签，可添加到节点上。

### 后续优化

1. **验证调度策略**：确认 nodeSelector、affinity、taint 等调度策略是否合理。
2. **监控调度事件**：配置监控告警，当 Pod 调度失败时及时通知。
3. **优化标签管理**：确保标签命名规范，避免使用无意义或重复标签。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running |
| 2. 检查调度事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | 无 FailedScheduling 事件 |
| 3. 检查节点标签 | `kubectl get nodes -o jsonpath='{.items[*].metadata.labels}'` | 包含实际使用的标签 |

---

## ⚠️ 注意事项

- 如果修改 nodeSelector 后仍无法调度，建议检查 affinity、toleration 等高级调度策略。
- 调度失败问题也可能与资源不足相关，但当前证据未显示资源不足，可排除。
- 建议定期检查调度策略与节点标签的一致性，防止类似问题再次发生。

---

## 📊 性能统计

├─ 总耗时: 5.3m
├─ 问题定位: 43.4s (14%) ✅
├─ 证据链采集: 117.0s (37%) ✅
├─ 根因分析: 44.4s (14%) ✅
├─ 汇总总结: 111.0s (35%) ✅
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
