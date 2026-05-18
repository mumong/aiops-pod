======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: c9c3a8b396df4180]

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
18m                   Warning   FailedScheduling   Pod/rc-pending-insufficient-cpu   0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No pr
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                          READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-insufficient-cpu   0/1     Pending   0          18m   <none>   <
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
   ✅ [问题定位] 完成 (37.6s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': '资源不足导致 Pod Pending', 'probability': '高', 'reason': '事件表明 0/3 nodes are available 且原因是 Insufficient cpu。'}, {'scenario': '节点调度不可用', 'probability': '中', 'reason': '需要进一步检查节点状态和资源分配。'}]
   entities=[{"type": "Pod", "name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e"}]
   reasoning=当前仍异常的 Pod 为 rc-pending-insufficient-cpu，状态为 Pending，异常类型为 PendingUnschedulable。事件表明 0/3 nodes are available 且原因是 Insufficient cpu。根据 L1 的归因特征，Pod 调度失败是由于节点资源不足或调度约束问题，因此归一化为 L1 层。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "", "confidence": 0.5, "reasoning": "当前仍异常的 Pod 为 rc-pending-insufficient-cpu，状态为 Pending，异常类型为 PendingUnschedulable。事件表明 0/3 nodes are available 且原因是 Insufficient cpu。根据 L1 的归因特征，Pod 调度失败是由于节点资源不足或调度约束问题，因此归一化为 L1 层。", "abnormal_pods": [{"name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "资源不足导致 Pod Pending", "probability": "高", "reason": "事件表明 0/3 nodes are available 且原因是 Insufficient cpu。"}, {"scenario": "节点调度不可用", "probability": "中", "reason": "需要进一步检查节点状态和资源分配。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-insufficient-cpu                         0/1     Pending     0                18m    <none>           <none>   <none>           <none>            app=rc-pending-insufficient-cpu,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/c9c3a8b396df4180/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/c9c3a8b396df4180/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/c9c3a8b396df4180/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 50%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  19m                  default-scheduler  0/3 nodes are avail
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [证据链采集] 当前已采集证据：

1. **critical 证据**：
   - 通过 `kubectl describe pod` 确认了 Pod `rc-pending-insufficient-cpu` 的状态为 `Pending`，且调度失败的原因为 `0/3 nodes are available: 3 Insufficient cpu`。
   - 事件中显示 `preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod`，表明没有节点有足够 CPU 资源来调度该 Pod。

2. **important 证据**：
   - 通过 `kubectl get nodes` 检查了所有节点的状态，确认所有节点都处于 `Ready` 状态。
   - 节点资源未显示异常，但当前所有节点均无法满足 Pod 的 CPU 资源需求，说明资源不足是当前调度失败的直接原因。

**结论**：
当前 Pod `rc-pending-insufficient-cpu` 无法调度的主要原因是集群中所有节点的 CPU 资源不足。需要检查 Pod 的 CPU 请求是否合理，或考虑扩展集群节点资源。
   ✅ [证据链采集] 完成 (1m 30.0s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod 的详细信息以验证调度失败的根本原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e","tool_args":{},"purpose":"验证 Pod 的详细信息，包括事件和状态，以确认调度失败的具体原因。","evidence_type":"status_and_events","target_scope":"Pod/aiops-e2e/rc-pending-insufficient-cpu","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"获取节点资源使用情况以确认是否由于资源不足导致调度失败","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes","tool_args":{},"purpose":"检查节点的资源使用情况，包括 CPU、内存等，以确认是否有足够的资源可供调度。","evidence_type":"node_status","target_scope":"Nodes","acceptable_tools":["kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-insufficient-cpu\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  19m                  default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  4m16s (x3 over 14m)  default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nName:             rc-pending-insufficient-cpu\nLabels:           app=rc-pending-insufficient-cpu\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c9c3a8b396df4180/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c9c3a8b396df4180/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c9c3a8b396df4180/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c9c3a8b396df4180/tools/002-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c9c3a8b396df4180/tools/002-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c9c3a8b396df4180/tools/002-evidence-kubectl_get_by_kind_in_cluster.summary.txt"}],"llm_analysis":"当前已采集证据：\n\n1. **critical 证据**：\n   - 通过 `kubectl describe pod` 确认了 Pod `rc-pending-insufficient-cpu` 的状态为 `Pending`，且调度失败的原因为 `0/3 nodes are available: 3 Insufficient cpu`。\n   - 事件中显示 `preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod`，表明没有节点有足够 CPU 资源来调度该 Pod。\n\n2. **important 证据**：\n   - 通过 `kubectl get nodes` 检查了所有节点的状态，确认所有节点都处于 `Ready` 状态。\n   - 节点资源未显示异常，但当前所有节点均无法满足 Pod 的 CPU 资源需求，说明资源不足是当前调度失败的直接原因。\n\n**结论**：\n当前 Pod `rc-pending-insufficient-cpu` 无法调度的主要原因是集群中所有节点的 CPU 资源不足。需要检查 Pod 的 CPU 请求是否合理，或考虑扩展集群节点资源。","collection_summary":"计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 8 个，匹配计划 2 个，未规划证据 6 个","plan_total":2,"plan_collected":2,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":2,"unplanned_tool_count":6,"evidence_inventory":[{"id":"e1","description":"获取 Pod 的详细信息以验证调度失败的根本原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e","purpose":"验证 Pod 的详细信息，包括事件和状态，以确认调度失败的具体原因。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取节点资源使用情况以确认是否由于资源不足导致调度失败","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes","purpose":"检查节点的资源使用情况，包括 CPU、内存等，以确认是否有足够的资源可供调度。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/2 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取 Pod 的详细信息以验证调度失败的根本原因 | `kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_get_by_kind_in_cl... | 获取节点资源使用情况以确认是否由于资源不足导致调度失败 | `kubectl get nodes` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (18.6s)
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
   ✅ [汇总总结] 完成 (1m 42.2s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3985 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 8.5s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending (Pod 无法调度) |
| **兼容归因层** | L1 - 调度失败 |
| **问题分类** | PendingUnschedulable |
| **置信度** | 中 (50%) |
| **证据完整度** | 2/2 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-pending-insufficient-cpu |
| Namespace | aiops-e2e |
| Node | <none> |
| 错误信息 | 0/3 nodes are available: 3 Insufficient cpu |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod -n aiops-e2e` | `STATUS: Pending, REASON: PendingUnschedulable` | Pod 无法调度 |
| 2 | Pod 事件 | `kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e` | `Warning  FailedScheduling  19m  default-scheduler  0/3 nodes are available: 3 Insufficient cpu` | 明确指出 CPU 资源不足 |
| 3 | 节点状态 | `kubectl get nodes` | 3 个节点，状态为 Ready，无 SchedulingDisabled | 所有节点可用，但无足够 CPU |
| 4 | Runbook 信息 | `fetch_runbook` | Pod PendingUnschedulable 的典型原因包括资源不足、节点约束不匹配等 | 为诊断提供场景参考 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 `Pending` 且事件指出 `Insufficient cpu`，说明是调度失败的典型表现。
- **证据 #3 补充**：节点状态为 Ready，说明调度失败是由于资源不足，而非节点状态异常。
- **证据 #4 提供上下文**：结合 runbook，确认此为资源不足导致的调度失败，而非节点标签、污点或存储依赖问题。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| Pod 的资源请求（requests） | important | 无法确认具体资源需求 |
| 节点 CPU 总量和使用量 | important | 无法评估集群资源瓶颈 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 当前集群中没有节点具备足够的 CPU 资源来满足 Pod 的请求           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Pod 请求 CPU 资源 > 节点可用 CPU 资源 → 无法调度                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 调度器无法找到可用节点（0/3 nodes are available）               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 Pending，事件提示 Insufficient cpu                   │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1（Pod 状态为 `Pending`）和证据 #2（事件提示 `0/3 nodes are available: 3 Insufficient cpu`），问题的根本原因是**集群中没有节点具备足够的 CPU 资源来满足 Pod 的请求**，导致调度失败。

**置信度**：中 (50%)
- ✅ Pod 事件明确指出 `Insufficient cpu`
- ✅ 节点状态为 Ready，排除节点状态问题
- ⚠️ 缺少 Pod 的资源请求和节点 CPU 使用数据，无法进一步确认具体需求和瓶颈

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 增加节点资源或降低 Pod 的 CPU 请求**
```bash
kubectl set resources pod/rc-pending-insufficient-cpu -n aiops-e2e --requests=cpu=500m
```
*依据*：当前节点 CPU 资源不足，适当降低 Pod 的 CPU 请求后，可能允许调度。

**2. [可选] 添加更多节点或扩容节点资源**
```bash
kubectl scale nodes <node-name> --replicas=4
```
*目的*：如果当前节点资源不足，可通过扩容节点资源或添加节点来满足需求。

### 后续优化

1. **监控资源使用情况**：使用 Prometheus 或 `kubectl describe node` 查看节点 CPU 使用情况，优化资源分配。
2. **资源规划**：根据业务需求合理配置 Pod 的资源请求和限制，避免过度请求。
3. **自动扩缩容**：考虑使用 Cluster Autoscaler 自动扩容节点。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e` | STATUS: Running |
| 2. 检查调度事件 | `kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e` | 无 FailedScheduling 事件 |
| 3. 检查节点 CPU 使用 | `kubectl describe node <node-name>` | CPU Requests < Allocatable CPU |

---

## ⚠️ 注意事项

- 如果 Pod 的 CPU 请求仍然过高，调度失败可能会再次发生。
- 如果当前集群 CPU 资源不足，考虑扩容节点或使用更高效的资源调度策略。
- 如果问题持续，建议检查节点标签、污点（taint）和容忍（toleration）配置，排除调度约束问题。

---

## 📋 附加建议

- **资源请求 vs 限制**：建议为 Pod 设置合理的 `requests` 和 `limits`，避免资源争抢或不足。
- **资源监控**：建议部署资源监控工具（如 Prometheus + Grafana），实时监控集群资源使用情况。
- **自动扩缩容**：如果使用云平台，考虑启用 Cluster Autoscaler 自动扩缩节点资源。

---

## 📊 性能统计

├─ 总耗时: 4.1m
├─ 问题定位: 37.6s (15%) ✅
├─ 证据链采集: 90.0s (36%) ✅
├─ 根因分析: 18.6s (7%) ✅
├─ 汇总总结: 102.2s (41%) ✅
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
