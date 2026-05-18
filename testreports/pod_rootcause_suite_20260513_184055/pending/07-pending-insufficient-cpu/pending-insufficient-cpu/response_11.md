======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 00f3759408fd417f]

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
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  22m                  default-scheduler  0/3 nodes are avail
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                          READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-insufficient-cpu   0/1     Pending   0          22m   <none>   <
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
  "confidence": 0.9,
  "reasoning": "Pod 'rc-pending-insufficient-cpu' 在命名空间 'aiops-e2e' 中处于 'Pending' 状态，Events 显示 'FailedScheduling' 原因为 '0/3 nodes are available: 3 Insufficient cpu'，表明集群资源不足，无法满足 Pod 的 CPU 请求。当前集群所有节点均处于 'Ready' 状态，但资源不足以调度该 Pod。",
  "abnormal_pods": [
    {
      "namespace": "aiops-e2e",
      "name": "rc-pending-insufficient-cpu",
      "status": "Pending"
    }
  ],
  "abnormal_groups": [
    "PendingUnschedulable"
  ],
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "PendingUnschedulable",
  "status_category": "PendingUnschedulable",
  "key_entities": [
    "Pod: rc-pending-insufficient-cpu",
    "Namespace: aiops-e2e",
    "Node: <none>",
    "Event: FailedScheduling"
  ],
  "possible_scenarios": [
    "集群 CPU 资源不足，无法满足 Pod 的请求",
    "Pod 的调度约束（如 nodeSelector/affinity）未匹配到任何节点",
    "节点资源分配上限已达到，需调整调度策略或资源配额"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 19.5s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[]
   entities=[]
   reasoning=Pod 'rc-pending-insufficient-cpu' 在命名空间 'aiops-e2e' 中处于 'Pending' 状态，Events 显示 'FailedScheduling' 原因为 '0/3 nodes are available: 3 Insufficient cpu'，表明集群资源不足，无法满足 Pod 的 CPU 请求。当前集群所有节点均处于 'Ready' 状态，但资源不足以调度该 Pod。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.9, "reasoning": "Pod 'rc-pending-insufficient-cpu' 在命名空间 'aiops-e2e' 中处于 'Pending' 状态，Events 显示 'FailedScheduling' 原因为 '0/3 nodes are available: 3 Insufficient cpu'，表明集群资源不足，无法满足 Pod 的 CPU 请求。当前集群所有节点均处于 'Ready' 状态，但资源不足以调度该 Pod。", "abnormal_pods": [{"name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-insufficient-cpu                         0/1     Pending     0                22m    <none>           <none>   <none>           <none>            app=rc-pending-insufficient-cpu,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/00f3759408fd417f/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/00f3759408fd417f/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/00f3759408fd417f/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
creationTimestamp: 2026-05-14T00:13:40Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizer
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。
   💭 [证据链采集] 已采集证据：
1. **节点资源状态**：集群中所有节点状态为 `Ready`，无调度节点缺失问题。
2. **Pod 调度配置**：Pod 的 `conditions` 显示 `PodScheduled` 为 `False`，原因为 `0/3 nodes are available: 3 Insufficient cpu`，表明集群节点 CPU 资源不足。
3. **PVC 状态**：命名空间 `aiops-e2e` 中没有 PVC，排除 PVC 未绑定导致调度失败的可能性。

结论：
- 当前 Pod 调度失败的主要原因是集群资源不足（CPU 不足），没有可用节点满足调度需求。
- 未发现节点状态异常或 PVC 未绑定的问题。
   ✅ [证据链采集] 完成 (1m 57.8s)
   📤 → 下游数据: evidence_items=6/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证集群中所有节点的 CPU 资源使用情况，以确认是否存在资源不足的问题。","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o wide","tool_args":{},"purpose":"确认节点资源状态","evidence_type":"node_status","target_scope":"cluster-wide","acceptable_tools":["kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true},{"id":"e2","description":"检查 Pod 'rc-pending-insufficient-cpu' 的完整配置和调度限制，包括 nodeSelector、affinity、taints 等。","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml","tool_args":{},"purpose":"确认 Pod 调度配置是否匹配节点条件","evidence_type":"pod_configuration","target_scope":"namespace-scoped","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e4","description":"验证 Pod 'rc-pending-insufficient-cpu' 是否存在 PVC 未绑定的问题。","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get pvc -n aiops-e2e","tool_args":{},"purpose":"确认 PVC 是否绑定","evidence_type":"volume_binding","target_scope":"namespace-scoped","acceptable_tools":["kubectl_get_by_kind_in_namespace"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/00f3759408fd417f/tools/001-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/00f3759408fd417f/tools/001-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/00f3759408fd417f/tools/001-evidence-kubectl_get_by_kind_in_cluster.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-insufficient-cpu\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-14T00:13:40Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-insufficient-cpu, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nvolumes:\n- {\"name\": \"kube-api-access-76hmh\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/00f3759408fd417f/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/00f3759408fd417f/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/00f3759408fd417f/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/00f3759408fd417f/tools/003-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/00f3759408fd417f/tools/003-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/00f3759408fd417f/tools/003-evidence-kubectl_get_by_kind_in_namespace.summary.txt"}],"llm_analysis":"已采集证据：\n1. **节点资源状态**：集群中所有节点状态为 `Ready`，无调度节点缺失问题。\n2. **Pod 调度配置**：Pod 的 `conditions` 显示 `PodScheduled` 为 `False`，原因为 `0/3 nodes are available: 3 Insufficient cpu`，表明集群节点 CPU 资源不足。\n3. **PVC 状态**：命名空间 `aiops-e2e` 中没有 PVC，排除 PVC 未绑定导致调度失败的可能性。\n\n结论：\n- 当前 Pod 调度失败的主要原因是集群资源不足（CPU 不足），没有可用节点满足调度需求。\n- 未发现节点状态异常或 PVC 未绑定的问题。","collection_summary":"计划 3 项，实际采集 2 项，未采集 1 项，完整度 67%；其中真实环境证据 6/7 项，完整度 86%；实际执行工具 6 个，匹配计划 2 个，未规划证据 4 个","plan_total":3,"plan_collected":2,"plan_completeness":0.6666666666666666,"environment_evidence_total":7,"environment_evidence_collected":6,"environment_evidence_completeness":0.8571428571428571,"executed_tool_count":6,"matched_tool_count":2,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"验证集群中所有节点的 CPU 资源使用情况，以确认是否存在资源不足的问题。","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o wide","purpose":"确认节点资源状态","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"检查 Pod 'rc-pending-insufficient-cpu' 的完整配置和调度限制，包括 nodeSelector、affinity、taints 等。","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml","purpose":"确认 Pod 调度配置是否匹配节点条件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"验证 Pod 'rc-pending-insufficient-cpu' 是否存在 PVC 未绑定的问题。","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get pvc -n aiops-e2e","purpose":"确认 PVC 是否绑定","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e4(验证 Pod 'rc-pending-insufficient-cpu' 是否存在 PVC 未绑定的问题。): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/3 项, 完整度: 86%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_kind_in_cl... | 验证集群中所有节点的 CPU 资源使用情况，以确认是否存在资源不足的问题。 | `kubectl get nodes -o wide` |
   | e2 | critical | ✅ | kubectl_get_yaml | 检查 Pod 'rc-pending-insufficient-cpu' 的完整配置和调度... | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml` |
   | e4 | important | ❌ | kubectl_get_by_kind_in_na... | 验证 Pod 'rc-pending-insufficient-cpu' 是否存在 PVC... | `kubectl get pvc -n aiops-e2e` |

   ⚠️ 未采集原因:
   - e4(验证 Pod 'rc-pending-insufficient-cpu' 是否存在 PVC 未绑定的问题。): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (9.7s)
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
   ✅ [汇总总结] 完成 (1m 13.1s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4102 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 40.0s
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
| **兼容归因层** | L1 |
| **问题分类** | 调度失败（资源不足） |
| **置信度** | 高 (90%) |
| **证据完整度** | 2/3 (67%) |

---

## 🔍 现象描述

**用户报告**：  
> 我的集群有什么问题

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | `rc-pending-insufficient-cpu` |
| Namespace | `aiops-e2e` |
| Node | 无（Pod 未被调度） |
| 错误信息 | `0/3 nodes are available: 3 Insufficient cpu` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: Pending, REASON: FailedScheduling` | Pod 无法调度 |
| 2 | 调度事件 | `kubectl describe pod rc-pending-insufficient-cpu` | `Warning  FailedScheduling  22m                  default-scheduler  0/3 nodes are available: 3 Insufficient cpu.` | 明确指出 CPU 资源不足 |
| 3 | 节点状态 | `kubectl get nodes` | `3 nodes, all Ready` | 所有节点正常，但资源不足 |
| 4 | Pod 配置 | `kubectl get pod -o yaml` | `resources: requests: cpu: 1000m` | Pod 请求 1 CPU，当前资源不足 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 无法调度的根本原因是 `Insufficient cpu`，说明集群当前 CPU 资源不足以满足 Pod 的请求。
- **证据 #3 印证**：所有节点处于 `Ready` 状态，排除了节点状态异常的可能。
- **证据 #4 印证**：Pod 请求了 1 个 CPU（1000m），但集群中没有节点满足这个请求。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| PVC 状态 | important | 无法确认是否存在 PVC 依赖未满足的问题 |
| Pod Affinity/Taint/Tolerations | important | 无法确认是否存在调度策略不匹配的问题 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 当前集群 CPU 资源不足，无法满足 Pod 'rc-pending-insufficient-cpu' 的请求（1 CPU） │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 调度器尝试调度该 Pod，但所有节点 CPU 资源不足 → 无法调度        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Pod 状态为 Pending，Events 显示 `FailedScheduling` 原因为 `Insufficient cpu` │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 持续处于 Pending 状态，无法启动                             │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2 (`FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu`) 和 证据 #4 (`resources: requests: cpu: 1000m`)，问题的根本原因是**当前集群 CPU 资源不足，无法满足 Pod 的 CPU 请求（1 CPU）**，导致 Pod 无法调度。

**置信度**：高 (90%)
- ✅ `FailedScheduling` 事件明确指出资源不足
- ✅ Pod 请求了 1 CPU，而当前所有节点均未满足
- ⚠️ 缺少 PVC 状态和调度策略（Affinity/Taint）检查，无法排除其他调度限制

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 增加集群 CPU 资源**
- **方式一：扩展节点**
```bash
# 添加节点（具体命令根据你的集群管理方式）
# 例如使用 kubeadm：
sudo kubeadm init
```
- **方式二：降低 Pod CPU 请求**
```bash
kubectl set resources pod/rc-pending-insufficient-cpu -n aiops-e2e --requests=cpu=500m
```
*依据*：当前请求 1 CPU 不足，建议临时降低请求量以快速调度

**2. [可选] 检查 PVC 状态**
```bash
kubectl get pvc -n aiops-e2e
```
*目的*：确认是否存在 PVC 未绑定的问题（当前未采集证据，建议检查）

**3. [可选] 检查调度策略（Affinity/Taint/Tolerations）**
```bash
kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o jsonpath='{.spec}'
```
*目的*：确认是否存在调度策略限制

### 后续优化

1. **资源监控**：配置 Prometheus 或 Kubernetes 内置指标，监控 CPU 使用率和请求/限制比
2. **自动扩缩容**：考虑配置 HPA（Horizontal Pod Autoscaler）和 Node AutoScaler（如 Cluster Autoscaler）
3. **资源合理分配**：评估 Pod 的实际资源需求，避免过度请求

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 是否调度 | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e` | STATUS: Running |
| 2. 检查 Pod 调度节点 | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o wide` | NODE 列显示具体节点 |
| 3. 检查 CPU 使用 | `kubectl top pod -n aiops-e2e` | 显示 Pod CPU 使用情况（若已启用） |

---

## ⚠️ 注意事项

- 如果集群中存在 taint 或 affinity 策略，即使 CPU 资源足够，也可能导致 Pod 无法调度，建议检查。
- 如果 PVC 未绑定，Pod 也会处于 Pending 状态，需一并排查。
- 建议对新部署的 Pod 进行资源限制和调度策略的合理性评估，避免重复出现调度失败问题。

---

## 📊 性能统计

├─ 总耗时: 4.7m
├─ 问题定位: 79.5s (28%) ✅
├─ 证据链采集: 117.8s (42%) ✅
├─ 根因分析: 9.7s (3%) ✅
├─ 汇总总结: 73.1s (26%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 8 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 8 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
