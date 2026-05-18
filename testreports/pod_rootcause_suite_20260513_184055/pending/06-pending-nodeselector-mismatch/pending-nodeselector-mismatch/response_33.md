======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 4f921903d0b648bf]

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
  Warning  FailedScheduling  6m2s (x15 over 76m)  default-scheduler  0/3 nodes are available
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
   ✅ [问题定位] 完成 (48.7s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'nodeSelector/affinity 不匹配', 'probability': '高', 'reason': 'Pod 的 nodeSelector 中指定的 aiops.e2e/nonexistent-node-label=true 与节点标签不匹配，导致调度失败。'}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}]
   reasoning=当前环境中存在一个仍处于异常状态的 Pod（rc-pending-nodeselector），其状态为 Pending，且事件中显示 FailedScheduling，原因为 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。结合 runbook 中的判定规则，这种情形属于调度约束不匹配，归类为 L1 层级的异常，其根因是 nodeSelector/affinity 不匹配。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "Node/Node-Scheduling", "confidence": 0.9, "reasoning": "当前环境中存在一个仍处于异常状态的 Pod（rc-pending-nodeselector），其状态为 Pending，且事件中显示 FailedScheduling，原因为 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。结合 runbook 中的判定规则，这种情形属于调度约束不匹配，归类为 L1 层级的异常，其根因是 nodeSelector/affinity 不匹配。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "nodeSelector/affinity 不匹配", "probability": "高", "reason": "Pod 的 nodeSelector 中指定的 aiops.e2e/nonexistent-node-label=true 与节点标签不匹配，导致调度失败。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                80m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/4f921903d0b648bf/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/4f921903d0b648bf/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/4f921903d0b648bf/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 90%

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
7m44s (x15 over 77m)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/
   💭 [证据链采集] 已采集证据：
- Pod `rc-pending-nodeselector` 的 spec 中指定了 `nodeSelector: aiops.e2e/nonexistent-node-label=true`。
- 集群中的所有节点（master、node1、node2）均未设置标签 `aiops.e2e/nonexistent-node-label=true`。
- Pod 的事件显示调度失败，原因为 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`。

结论：
当前 Pod 无法调度的根本原因是其 `nodeSelector` 中指定的标签 `aiops.e2e/nonexistent-node-label=true` 在所有节点上均不存在，导致调度器无法找到合适的节点来运行该 Pod。
   ✅ [证据链采集] 完成 (1m 18.5s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod 的 nodeSelector/affinity 是否与 Node 标签不匹配","level":"critical","tool":"kubectl_get_yaml","command":"get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{},"purpose":"确认 Pod spec 中的 nodeSelector 或 affinity 是否与节点标签不匹配","evidence_type":"nodeSelector/affinity 不匹配","target_scope":"Pod","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e2","description":"验证节点是否具有与 Pod nodeSelector/affinity 匹配的标签","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"get nodes -o wide","tool_args":{},"purpose":"确认节点标签是否匹配 Pod 的 nodeSelector/affinity","evidence_type":"nodeSelector/affinity 不匹配","target_scope":"Node","acceptable_tools":["kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true},{"id":"e3","description":"验证 Pod 的 FailedScheduling 事件","level":"important","tool":"kubectl_events","command":"get events -n aiops-e2e --field-selector=involvedObject.name=rc-pending-nodeselector","tool_args":{"resource_type":"pod","resource_name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"确认 Pod 的 FailedScheduling 事件的具体原因","evidence_type":"FailedScheduling 事件","target_scope":"Event","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-fsdjk\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4f921903d0b648bf/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4f921903d0b648bf/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4f921903d0b648bf/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4f921903d0b648bf/tools/002-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4f921903d0b648bf/tools/002-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4f921903d0b648bf/tools/002-evidence-kubectl_get_by_kind_in_cluster.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n7m44s (x15 over 77m)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4f921903d0b648bf/tools/003-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4f921903d0b648bf/tools/003-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4f921903d0b648bf/tools/003-evidence-kubectl_events.summary.txt"}],"llm_analysis":"已采集证据：\n- Pod `rc-pending-nodeselector` 的 spec 中指定了 `nodeSelector: aiops.e2e/nonexistent-node-label=true`。\n- 集群中的所有节点（master、node1、node2）均未设置标签 `aiops.e2e/nonexistent-node-label=true`。\n- Pod 的事件显示调度失败，原因为 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`。\n\n结论：\n当前 Pod 无法调度的根本原因是其 `nodeSelector` 中指定的标签 `aiops.e2e/nonexistent-node-label=true` 在所有节点上均不存在，导致调度器无法找到合适的节点来运行该 Pod。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 9/9 项，完整度 100%；实际执行工具 9 个，匹配计划 3 个，未规划证据 6 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":9,"environment_evidence_collected":9,"environment_evidence_completeness":1.0,"executed_tool_count":9,"matched_tool_count":3,"unplanned_tool_count":6,"evidence_inventory":[{"id":"e1","description":"验证 Pod 的 nodeSelector/affinity 是否与 Node 标签不匹配","level":"critical","tool":"kubectl_get_yaml","command":"get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"确认 Pod spec 中的 nodeSelector 或 affinity 是否与节点标签不匹配","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"验证节点是否具有与 Pod nodeSelector/affinity 匹配的标签","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"get nodes -o wide","purpose":"确认节点标签是否匹配 Pod 的 nodeSelector/affinity","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"验证 Pod 的 FailedScheduling 事件","level":"important","tool":"kubectl_events","command":"get events -n aiops-e2e --field-selector=involvedObject.name=rc-pending-nodeselector","purpose":"确认 Pod 的 FailedScheduling 事件的具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_yaml | 验证 Pod 的 nodeSelector/affinity 是否与 Node 标签不匹配 | `get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e2 | critical | ✅ | kubectl_get_by_kind_in_cl... | 验证节点是否具有与 Pod nodeSelector/affinity 匹配的标签 | `get nodes -o wide` |
   | e3 | important | ✅ | kubectl_events | 验证 Pod 的 FailedScheduling 事件 | `get events -n aiops-e2e --field-selector=involvedObject.name=rc-pending-nodes...` |

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (11.6s)
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
   ✅ [汇总总结] 完成 (1m 11.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4310 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 30.4s
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
| **问题分类** | 调度约束不匹配（nodeSelector/affinity 不匹配） |
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
| 错误信息 | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: Pending, REASON: FailedScheduling` | Pod 无法调度 |
| 2 | Pod 事件 | `kubectl describe pod rc-pending-nodeselector` | `Warning FailedScheduling 6m2s (x15 over 76m): 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 明确指出 nodeSelector/affinity 不匹配 |
| 3 | Pod YAML | `kubectl get pod -o yaml` | `nodeSelector: aiops.e2e/nonexistent-node-label: true` | Pod 的 nodeSelector 中指定了不存在的节点标签 |

### 证据关联分析

- **证据 #2 + #3 印证**：Pod 的 `nodeSelector` 中指定了 `aiops.e2e/nonexistent-node-label: true`，但集群中没有节点拥有该标签，导致调度失败。
- **证据链**：Pod 指定 nodeSelector → 节点无对应标签 → 无法匹配 → 调度失败 → Pod 始终处于 Pending 状态。

---

## 🎯 根因分析

### 因果链

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                      │
│ Pod 的 nodeSelector 中指定了不存在的节点标签 aiops.e2e/nonexistent-node-label: true │
└───────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                      │
│ 集群中没有节点具有该标签，导致调度器无法找到匹配的节点                         │
└───────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                      │
│ Pod 无法调度，状态为 PendingUnschedulable                                     │
└───────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                  │
│ Pod 一直处于 Pending 状态，且事件中持续显示 FailedScheduling                  │
└───────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2（`kubectl describe pod` 显示 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`）和证据 #3（Pod 的 `nodeSelector` 指定了 `aiops.e2e/nonexistent-node-label: true`，但该标签在节点中不存在），问题的根本原因是 **Pod 的 nodeSelector 指定了集群中不存在的节点标签**，导致调度失败。

**置信度**：高 (90%)  
- ✅ `kubectl describe` 明确显示调度失败原因
- ✅ `kubectl get pod -o yaml` 显示 nodeSelector 指定了不存在的标签
- ⚠️ 无缺失证据

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 移除或修改 nodeSelector**
```bash
kubectl edit pod rc-pending-nodeselector -n aiops-e2e
```
*操作*：在 `spec.nodeSelector` 中删除或修改 `aiops.e2e/nonexistent-node-label: true` 为集群中实际存在的节点标签，保存后重新调度。

**2. [可选] 添加缺失节点标签**
```bash
kubectl label nodes <node-name> aiops.e2e/nonexistent-node-label=true
```
*操作*：如果希望保留此 nodeSelector，则可为集群中一个或多个节点添加该标签，以满足调度条件。

### 后续优化

1. **标签管理**：确保 nodeSelector 中的标签在集群中存在，或使用 nodeAffinity 实现更灵活的调度策略。
2. **调度器策略验证**：在部署 Pod 之前，使用 `kubectl explain` 或文档确认调度策略的可行性。
3. **监控调度失败事件**：配置事件监控，及时发现调度失败的 Pod。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running |
| 2. 查看调度事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | 无 FailedScheduling 事件 |
| 3. 确认 nodeSelector 已修改 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` | nodeSelector 不再包含 `aiops.e2e/nonexistent-node-label: true` |

---

## ⚠️ 注意事项

- 如果 nodeSelector 是由 Helm chart 或 Operator 自动生成，请检查模板配置，确保标签正确。
- 调度失败的 Pod 通常不会自动恢复，必须手动修复其配置。
- 如果 nodeSelector 是为了特定用途（如 GPU、SSD），请确保集群中有节点满足这些硬件要求并正确打上标签。

---

## ✅ 总结

当前集群中存在一个异常 Pod `rc-pending-nodeselector`，其状态为 `PendingUnschedulable`，根本原因是 Pod 的 `nodeSelector` 指定了集群中不存在的节点标签。修复方法包括移除或修改 nodeSelector，或为节点添加缺失的标签。建议在部署前验证调度策略，以避免类似问题。

---

## 📊 性能统计

├─ 总耗时: 3.5m
├─ 问题定位: 48.7s (23%) ✅
├─ 证据链采集: 78.5s (37%) ✅
├─ 根因分析: 11.6s (6%) ✅
├─ 汇总总结: 71.5s (34%) ✅
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
