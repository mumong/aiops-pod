======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: ddf04ff4328e47b9]

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
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
40m                 Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 n
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          40m   <none>   <none>   
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
   💭 [问题定位] 调用工具: kubectl_get_yaml
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (39.5s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'Pod 的 nodeSelector 不匹配任何节点的标签', 'probability': '高', 'reason': "事件显示 'node(s) didn't match Pod's node affinity/selector'，表明 Pod 的 nodeSelector 与节点标签不匹配，导致无法调度。"}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}]
   reasoning=当前环境中存在异常 Pod rc-pending-nodeselector（状态为 Pending，异常类型为 PendingUnschedulable），其事件显示调度失败的原因是 node(s) didn't match Pod's node affinity/selector。结合 runbook 的诊断规则，此类情况属于调度约束不匹配，归类为 L1 层级。节点状态正常（所有节点 Ready），但 Pod 的 nodeSelector 与节点标签不匹配导致调度失败。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "Node/Resource Pressure or Lifecycle", "confidence": 0.95, "reasoning": "当前环境中存在异常 Pod rc-pending-nodeselector（状态为 Pending，异常类型为 PendingUnschedulable），其事件显示调度失败的原因是 node(s) didn't match Pod's node affinity/selector。结合 runbook 的诊断规则，此类情况属于调度约束不匹配，归类为 L1 层级。节点状态正常（所有节点 Ready），但 Pod 的 nodeSelector 与节点标签不匹配导致调度失败。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Pod 的 nodeSelector 不匹配任何节点的标签", "probability": "高", "reason": "事件显示 'node(s) didn't match Pod's node affinity/selector'，表明 Pod 的 nodeSelector 与节点标签不匹配，导致无法调度。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                40m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/ddf04ff4328e47b9/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/ddf04ff4328e47b9/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/ddf04ff4328e47b9/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
  Warning  FailedScheduling  42m                default-scheduler  0/3 nodes are available: 
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [证据链采集] 已采集证据：
1. **Pod 的调度失败事件**：`kubectl describe pod` 显示 Pod 的 `nodeSelector` 或 `affinity` 不匹配任何节点的标签。
2. **节点标签状态**：`kubectl get nodes` 显示所有节点状态为 `Ready`，但未显示与 Pod 的 `nodeSelector` 或 `affinity` 匹配的标签。

未采集证据：
- Pod 的 YAML 配置中 `nodeSelector` 或 `affinity` 的具体内容（需通过 `kubectl get yaml` 获取）。
- PVC/PV 状态（需通过 `kubectl get pvc -n aiops-e2e` 获取）。

冲突证据：
- 无。
   ✅ [证据链采集] 完成 (1m 54.3s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 的详细描述信息以验证调度失败的具体原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"验证 Pod 的 nodeSelector、affinity、taints 等字段是否与节点标签不匹配，确认调度失败的具体原因","evidence_type":"Pod 配置与调度失败","target_scope":"aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_describe","kubectl_get_by_name","kubectl_get_by_kind_in_namespace","kubectl_get_by_kind_in_cluster","kubectl_find_resource","kubectl_get_yaml","kubectl_events","kubectl_logs","kubectl_previous_logs","kubectl_logs_all_containers","kubectl_previous_logs_all_containers","kubectl_container_logs","kubectl_container_previous_logs","kubectl_logs_grep","kubectl_logs_all_containers_grep","kubernetes_jq_query","kubernetes_tabular_query","kubernetes_count","get_prometheus_target","kubectl_lineage_children","kubectl_lineage_parents","run_bash_command","kubectl_run_image","list_prometheus_rules","get_metric_names","get_label_values","get_all_labels","get_series","get_metric_metadata","execute_prometheus_instant_query","execute_prometheus_range_query","fetch_runbook"],"counts_for_completeness":true},{"id":"e2","description":"获取节点的详细信息以验证节点标签是否与 Pod 的 nodeSelector/affinity 匹配","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o json","tool_args":{"kind":"Node","namespace":""},"purpose":"验证节点的标签是否与 Pod 的 nodeSelector/affinity 匹配，确认调度失败的具体原因","evidence_type":"节点配置与调度失败","target_scope":"Cluster","acceptable_tools":["kubectl_get_by_name","kubectl_get_by_kind_in_namespace","kubectl_get_by_kind_in_cluster","kubectl_find_resource","kubectl_get_yaml","kubectl_events","kubectl_logs","kubectl_previous_logs","kubectl_logs_all_containers","kubectl_previous_logs_all_containers","kubectl_container_logs","kubectl_container_previous_logs","kubectl_logs_grep","kubectl_logs_all_containers_grep","kubernetes_jq_query","kubernetes_tabular_query","kubernetes_count","get_prometheus_target","kubectl_lineage_children","kubectl_lineage_parents","run_bash_command","kubectl_run_image","list_prometheus_rules","get_metric_names","get_label_values","get_all_labels","get_series","get_metric_metadata","execute_prometheus_instant_query","execute_prometheus_range_query","fetch_runbook"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  42m                default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  27m (x3 over 37m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ddf04ff4328e47b9/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ddf04ff4328e47b9/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ddf04ff4328e47b9/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ddf04ff4328e47b9/tools/002-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ddf04ff4328e47b9/tools/002-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ddf04ff4328e47b9/tools/002-evidence-kubectl_get_by_kind_in_cluster.summary.txt"}],"llm_analysis":"已采集证据：\n1. **Pod 的调度失败事件**：`kubectl describe pod` 显示 Pod 的 `nodeSelector` 或 `affinity` 不匹配任何节点的标签。\n2. **节点标签状态**：`kubectl get nodes` 显示所有节点状态为 `Ready`，但未显示与 Pod 的 `nodeSelector` 或 `affinity` 匹配的标签。\n\n未采集证据：\n- Pod 的 YAML 配置中 `nodeSelector` 或 `affinity` 的具体内容（需通过 `kubectl get yaml` 获取）。\n- PVC/PV 状态（需通过 `kubectl get pvc -n aiops-e2e` 获取）。\n\n冲突证据：\n- 无。","collection_summary":"计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 8 个，匹配计划 2 个，未规划证据 6 个","plan_total":2,"plan_collected":2,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":2,"unplanned_tool_count":6,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 的详细描述信息以验证调度失败的具体原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"验证 Pod 的 nodeSelector、affinity、taints 等字段是否与节点标签不匹配，确认调度失败的具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取节点的详细信息以验证节点标签是否与 Pod 的 nodeSelector/affinity 匹配","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o json","purpose":"验证节点的标签是否与 Pod 的 nodeSelector/affinity 匹配，确认调度失败的具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/2 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取异常 Pod 的详细描述信息以验证调度失败的具体原因 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_get_by_kind_in_cl... | 获取节点的详细信息以验证节点标签是否与 Pod 的 nodeSelector/affini... | `kubectl get nodes -o json` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (18.4s)
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
   ✅ [汇总总结] 完成 (1m 1.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3824 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 53.3s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending (Pod Unschedulable) |
| **兼容归因层** | L1 - 调度失败 |
| **问题分类** | 调度约束不匹配（nodeSelector/affinity） |
| **置信度** | 高 (95%) |
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
| 错误信息 | `FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: Pending` | Pod 无法被调度 |
| 2 | 事件日志 | `kubectl describe pod rc-pending-nodeselector` | `Warning FailedScheduling 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 明确指出调度失败是由于节点标签与 Pod 的 nodeSelector 不匹配 |
| 3 | 节点状态 | `kubectl get node` | `3 nodes, all Ready` | 节点状态正常，无资源不足问题 |
| 4 | Runbook 诊断规则 | `fetch_runbook` | `Pod异常类型: PendingUnschedulable | 兼容分类: scheduling` | 调度失败常见原因包括 nodeSelector/affinity 不匹配、taint 未容忍、资源不足等 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 Pending，事件日志显示 `node(s) didn't match Pod's node affinity/selector`，表明调度失败的根本原因是节点标签不匹配。
- **证据 #3 排除资源不足**：所有节点 Ready，没有 `Insufficient cpu/memory` 等资源不足提示，排除资源不足导致的调度失败。
- **证据 #4 指导分析方向**：Runbook 明确指出 nodeSelector/affinity 不匹配是调度失败的典型原因。

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod 的 nodeSelector 设置要求节点包含特定标签，但集群中所有节点均不满足此条件。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 调度器尝试将 Pod 调度到满足 nodeSelector 的节点，但没有节点符合条件。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Pod 被标记为 Unschedulable，事件显示 `node(s) didn't match Pod's node affinity/selector`。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 Pending，持续无法调度，事件显示调度失败。 │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2 (事件日志) 和证据 #4 (runbook 诊断规则)，问题的根本原因是**Pod 的 nodeSelector 设置的节点标签不匹配任何可用节点**，导致调度失败。  
**置信度**：高 (95%)  
- ✅ 事件日志明确指出 `node(s) didn't match Pod's node affinity/selector`
- ✅ 所有节点状态正常，排除资源不足
- ✅ Runbook 明确指出此类问题归因于调度约束不匹配

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查并修改 Pod 的 nodeSelector 设置**

```bash
kubectl describe pod rc-pending-nodeselector -n aiops-e2e
```

*目的*：查看当前 Pod 的 nodeSelector 配置，确认它要求哪些节点标签。

**2. [优先] 修改 nodeSelector 以匹配节点标签**

根据实际节点标签，修改 Pod 的 nodeSelector。例如，如果节点有标签 `disk=ssd`，则修改 Pod 的 nodeSelector 为：

```yaml
nodeSelector:
  disk: ssd
```

*执行方式*：修改 Pod 的 YAML 文件并重新部署：

```bash
kubectl apply -f rc-pending-nodeselector.yaml
```

**3. [可选] 检查节点标签**

```bash
kubectl get node --show-labels
```

*目的*：确认节点实际标签，用于校对 nodeSelector 设置。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running |
| 2. 检查调度事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | 无 FailedScheduling 事件 |
| 3. 检查节点标签 | `kubectl get node --show-labels` | 包含与 nodeSelector 匹配的标签 |

---

## ⚠️ 注意事项

- 如果 nodeSelector 是由 Helm Chart 或 Operator 自动注入的，请检查模板配置。
- 如果 nodeSelector 是为了某些特定需求（如 GPU、SSD），请确保集群中存在满足条件的节点。
- 若 Pod 仍无法调度，请检查是否还有其他约束（如 affinity、taint、PodDisruptionBudget 等）。

---

## 📊 性能统计

├─ 总耗时: 3.9m
├─ 问题定位: 39.5s (17%) ✅
├─ 证据链采集: 114.3s (49%) ✅
├─ 根因分析: 18.4s (8%) ✅
├─ 汇总总结: 61.0s (26%) ✅
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
