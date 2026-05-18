======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: edbed0d659654783]

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
  Warning  FailedScheduling  7m15s  default-scheduler  0/3 nodes are available: 3 node(s) di
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE     IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          7m18s   <none>   <none
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
  "reasoning": "当前集群中有一个 Pod 处于 Pending 状态，其调度失败原因为 'node(s) didn't match Pod's node affinity/selector'。该 Pod 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label' 标签为 'true'，但集群中所有节点均未设置此标签，导致无节点满足调度条件。节点状态均为 Ready，未发现资源不足或节点不可用问题。此问题属于调度约束不匹配，归类为 L1 层级。",
  "abnormal_pods": [
    {
      "name": "rc-pending-nodeselector",
      "namespace": "aiops-e2e",
      "status": "Pending",
      "reason": "Unschedulable",
      "message": "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.."
    }
  ],
  "abnormal_groups": {
    "PendingUnschedulable": 1
  },
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "PendingUnschedulable",
  "status_category": "scheduling",
  "key_entities": [
    "rc-pending-nodeselector",
    "aiops.e2e/nonexistent-node-label"
  ],
  "possible_scenarios": [
    "Pod 的 nodeSelector 设置了不存在的节点标签 (aiops.e2e/nonexistent-node-label=true)，导致无节点匹配。",
    "集群节点缺少必要的标签，无法满足调度需求。",
    "Pod 的调度策略与集群节点配置不兼容。"
  ]
}
   ✅ [问题定位] 完成 (45.7s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[]
   entities=[]
   reasoning=当前集群中有一个 Pod 处于 Pending 状态，其调度失败原因为 'node(s) didn't match Pod's node affinity/selector'。该 Pod 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label' 标签为 'true'，但集群中所有节点均未设置此标签，导致无节点满足调度条件。节点状态均为 Ready，未发现资源不足或节点不可用问题。此问题属于调度约束不匹配，归类为 L1 层级。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "当前集群中有一个 Pod 处于 Pending 状态，其调度失败原因为 'node(s) didn't match Pod's node affinity/selector'。该 Pod 的 nodeSelector 设置了 'aiops.e2e/nonexistent-node-label' 标签为 'true'，但集群中所有节点均未设置此标签，导致无节点满足调度条件。节点状态均为 Ready，未发现资源不足或节点不可用问题。此问题属于调度约束不匹配，归类为 L1 层级。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                7m11s   <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/edbed0d659654783/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/edbed0d659654783/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/edbed0d659654783/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  9m6s  default-scheduler  0/3 nodes are available: 3 node(s) did
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
1. **kubectl_describe Pod**:
   - Pod `rc-pending-nodeselector` 处于 `Pending` 状态。
   - 事件显示调度失败原因为 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`，预抢占无法帮助调度。
   - 诊断关键行：`FailedScheduling` 事件重复出现，表明调度器无法找到匹配的节点。

2. **kubectl_get_yaml Pod**:
   - Pod 的 `nodeSelector` 设置了 `aiops.e2e/nonexistent-node-label=true`。
   - 集群中无节点具备此标签，导致调度失败。

3. **kubectl_get_by_kind_in_cluster (节点标签)**:
   - 所有节点（`master`、`node1`、`node2`）均未设置标签 `aiops.e2e/nonexistent-node-label`。
   - 节点状态为 `Ready`，未发现资源不足或节点不可用问题。

## 未采集证据
- 无其他待采集证据，因当前证据已充分说明调度失败原因。

## 冲突证据
- 无冲突证据，所有工具调用结果一致。

## 最终诊断
当前 Pod `rc-pending-nodeselector` 无法调度的根本原因是其 `nodeSelector` 指定了一个不存在的标签 `aiops.e2e/nonexistent-node-label=true`，而集群中所有节点均未设置此标签。此问题属于调度约束不匹配，归类为 L1 层级。
   ✅ [证据链采集] 完成 (1m 38.2s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"verify-pod-scheduling-failure","description":"验证 Pod 调度失败的具体原因，确认是否由于 nodeSelector/affinity 不匹配导致","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"pod_name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"获取 Pod 的详细描述信息，查看 FailedScheduling 事件的具体原因","evidence_type":"scheduling_failure","target_scope":"aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"verify-pod-node-selector","description":"验证 Pod 的 nodeSelector 配置，确认其是否与集群节点标签匹配","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"pod_name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"获取 Pod 的 YAML 配置，查看其 nodeSelector 字段是否与集群节点标签匹配","evidence_type":"node_selector_mismatch","target_scope":"aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"verify-node-labels","description":"验证集群中节点的标签，确认是否有节点匹配 Pod 的 nodeSelector","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o jsonpath='{.items[*].metadata.labels}'","tool_args":{},"purpose":"获取所有节点的标签，确认是否有节点具备与 Pod 的 nodeSelector 匹配的标签","evidence_type":"node_label_check","target_scope":"all_nodes","acceptable_tools":["kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  9m6s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  4m    default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/edbed0d659654783/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/edbed0d659654783/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/edbed0d659654783/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-fsdjk\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/edbed0d659654783/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/edbed0d659654783/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/edbed0d659654783/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/edbed0d659654783/tools/003-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/edbed0d659654783/tools/003-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/edbed0d659654783/tools/003-evidence-kubectl_get_by_kind_in_cluster.summary.txt"}],"llm_analysis":"# 证据结论\n\n## 已采集证据\n1. **kubectl_describe Pod**:\n   - Pod `rc-pending-nodeselector` 处于 `Pending` 状态。\n   - 事件显示调度失败原因为 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`，预抢占无法帮助调度。\n   - 诊断关键行：`FailedScheduling` 事件重复出现，表明调度器无法找到匹配的节点。\n\n2. **kubectl_get_yaml Pod**:\n   - Pod 的 `nodeSelector` 设置了 `aiops.e2e/nonexistent-node-label=true`。\n   - 集群中无节点具备此标签，导致调度失败。\n\n3. **kubectl_get_by_kind_in_cluster (节点标签)**:\n   - 所有节点（`master`、`node1`、`node2`）均未设置标签 `aiops.e2e/nonexistent-node-label`。\n   - 节点状态为 `Ready`，未发现资源不足或节点不可用问题。\n\n## 未采集证据\n- 无其他待采集证据，因当前证据已充分说明调度失败原因。\n\n## 冲突证据\n- 无冲突证据，所有工具调用结果一致。\n\n## 最终诊断\n当前 Pod `rc-pending-nodeselector` 无法调度的根本原因是其 `nodeSelector` 指定了一个不存在的标签 `aiops.e2e/nonexistent-node-label=true`，而集群中所有节点均未设置此标签。此问题属于调度约束不匹配，归类为 L1 层级。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 8 个，匹配计划 3 个，未规划证据 5 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":3,"unplanned_tool_count":5,"evidence_inventory":[{"id":"verify-pod-scheduling-failure","description":"验证 Pod 调度失败的具体原因，确认是否由于 nodeSelector/affinity 不匹配导致","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"获取 Pod 的详细描述信息，查看 FailedScheduling 事件的具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"verify-pod-node-selector","description":"验证 Pod 的 nodeSelector 配置，确认其是否与集群节点标签匹配","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"获取 Pod 的 YAML 配置，查看其 nodeSelector 字段是否与集群节点标签匹配","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"verify-node-labels","description":"验证集群中节点的标签，确认是否有节点匹配 Pod 的 nodeSelector","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o jsonpath='{.items[*].metadata.labels}'","purpose":"获取所有节点的标签，确认是否有节点具备与 Pod 的 nodeSelector 匹配的标签","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | verify-pod-sc... | critical | ✅ | kubectl_describe | 验证 Pod 调度失败的具体原因，确认是否由于 nodeSelector/affinity... | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | verify-pod-no... | important | ✅ | kubectl_get_yaml | 验证 Pod 的 nodeSelector 配置，确认其是否与集群节点标签匹配 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | verify-node-l... | important | ✅ | kubectl_get_by_kind_in_cl... | 验证集群中节点的标签，确认是否有节点匹配 Pod 的 nodeSelector | `kubectl get nodes -o jsonpath='{.items[*].metadata.labels}'` |

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (11.3s)
   📤 → 下游数据: root_cause=[L1层] 当前无法基于 LLM 输出确定根本原因
   confidence=10%
   causal_chain={"trigger": "LLM 未生成可靠因果链", "mechanism": "缺少可用的结构化根因分析结果", "manifestation": "我的集群有什么问题"}
   rca_analysis={"phenomenon": "我的集群有什么问题", "evidence_analysis": [], "causal_chain": {"trigger": "LLM 未生成可靠因果链", "mechanism": "缺少可用的结构化根因分析结果", "manifestation": "我的集群有什么问题"}, "root_cause": "[L1层] 当前无法基于 LLM 输出确定根本原因", "confidence": 0.1, "confidence_reason": "LLM 返回结果不符合 RCA 结构化输出合同", "alternative_causes": []}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: [L1层] 当前无法基于 LLM 输出确定根本原因
   置信度: 10%
   🔗 因果链:
     根本原因: LLM 未生成可靠因果链
     传导机制: 缺少可用的结构化根因分析结果
     最终表现: 我的集群有什么问题


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (2m 4.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4726 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 39.3s
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
| Node | <none> |
| 错误信息 | node(s) didn't match Pod's node affinity/selector |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: Pending` | Pod 无法调度 |
| 2 | 调度失败事件 | `kubectl describe pod` | `Warning FailedScheduling 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 明确指出调度失败原因 |
| 3 | nodeSelector 配置 | `kubectl get pod -o yaml` | `nodeSelector: aiops.e2e/nonexistent-node-label: "true"` | Pod 设置了不存在的标签 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 `Pending`，且事件显示 `nodeSelector` 不匹配 → 调度失败
- **证据 #3 印证**：Pod 的 `nodeSelector` 设置了标签 `aiops.e2e/nonexistent-node-label: "true"`，但节点中无此标签 → 无节点可调度

### 缺失证据（无）

| 证据 | 级别 | 影响 |
|------|------|------|
| 无 | - | - |

---

## 🎯 根因分析

### 因果链

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                    │
│ Pod 设置了 nodeSelector: aiops.e2e/nonexistent-node-label: "true"           │
│ 但集群中所有节点均未设置此标签，导致无节点满足调度条件                        │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                    │
│ 调度器尝试匹配 nodeSelector，但无节点满足条件 → 调度失败                     │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                    │
│ Pod 被标记为 PendingUnschedulable，无法调度                                 │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                │
│ Pod 状态为 Pending，事件提示 nodeSelector 不匹配                            │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Pod 状态 Pending)、证据 #2 (调度失败事件) 和证据 #3 (nodeSelector 设置无效标签)，问题的根本原因是 **Pod 的 nodeSelector 设置了不存在的标签 `aiops.e2e/nonexistent-node-label: "true"`，导致调度失败**。

**置信度**：高 (95%)

- ✅ `kubectl describe pod` 明确显示调度失败原因
- ✅ `kubectl get pod -o yaml` 显示了无效的 nodeSelector 设置
- ✅ `kubectl get node` 显示节点无此标签

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 移除或修改 nodeSelector**
```bash
kubectl edit pod rc-pending-nodeselector -n aiops-e2e
```
*操作*：在 `spec.nodeSelector` 中删除或修改 `aiops.e2e/nonexistent-node-label: "true"`，或将其替换为集群中存在的标签。

**2. [可选] 添加缺失的节点标签**
```bash
kubectl label nodes <node-name> aiops.e2e/nonexistent-node-label=true
```
*操作*：将集群中一个或多个节点添加上该标签，以满足 Pod 的调度需求。

### 后续优化

1. **标签管理策略**：
   - 确保所有调度约束使用的标签在节点上存在
   - 建立标签命名规范，避免使用未定义的标签

2. **调度器配置审查**：
   - 检查是否有其他 Pod 使用了无效的 nodeSelector 或 affinity 设置
   - 使用 `kubectl get pods -o jsonpath='{.spec.nodeSelector}'` 批量检查

3. **自动化监控**：
   - 配置监控告警，当 Pod 调度失败时自动通知运维人员
   - 使用 Prometheus + Grafana 监控调度失败事件

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 调度 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running |
| 2. 检查 nodeSelector 是否已修改 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` | `spec.nodeSelector` 中不再包含无效标签 |
| 3. 检查节点标签 | `kubectl get nodes --show-labels` | 节点上存在新添加的标签（如果选择添加） |

---

## ⚠️ 注意事项

- 如果 Pod 使用的是 Deployment/ReplicaSet 管理，修改 Pod 本身不会生效，应修改对应的 Deployment
- 确保修改后的 nodeSelector 与集群中节点标签匹配，否则问题会再次出现
- 如果 nodeSelector 是通过 Helm/Operator 等工具自动生成的，应检查模板配置

---

## ✅ 修复成功示例

```bash
# 修改 Deployment 的 nodeSelector（如果 Pod 由 Deployment 管理）
kubectl edit deployment <deployment-name> -n aiops-e2e
```

```yaml
# 修改前
spec:
  template:
    spec:
      nodeSelector:
        aiops.e2e/nonexistent-node-label: "true"

# 修改后
spec:
  template:
    spec:
      nodeSelector:
        aiops.e2e/existing-label: "true"
```

---

## 📦 附录：相关工具命令

- `kubectl describe pod rc-pending-nodeselector -n aiops-e2e`：查看 Pod 调度失败事件
- `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml`：查看 Pod 的 nodeSelector 配置
- `kubectl get nodes --show-labels`：查看节点标签
- `kubectl label nodes <node-name> aiops.e2e/nonexistent-node-label=true`：给节点添加标签

---

---

## 📊 性能统计

├─ 总耗时: 4.7m
├─ 问题定位: 45.7s (16%) ✅
├─ 证据链采集: 98.2s (35%) ✅
├─ 根因分析: 11.3s (4%) ✅
├─ 汇总总结: 124.0s (44%) ✅
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
