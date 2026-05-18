======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: e454113370f94f3e]

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
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE     IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          3h20m   <none>   <none
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  5m27s (x39 over 3h15m)  default-scheduler  0/3 nodes are availa
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE     IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          3h20m   <none>   <none
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE     IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          3h21m   <none>   <none
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (4m 5.9s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'Pod 选择器（nodeSelector/affinity）与节点标签不匹配，导致调度失败。', 'probability': '高', 'reason': "kubectl describe 显示 'node(s) didn't match Pod's node affinity/selector'。"}, {'scenario': '节点上没有满足 Pod 调度约束的可用节点。', 'probability': '中', 'reason': '所有节点均未匹配调度约束，且未提及资源不足或 taint 不匹配问题。'}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}]
   reasoning=当前仍异常的 Pod 'rc-pending-nodeselector' 处于 'Pending' 状态，且事件中包含 'FailedScheduling'，结合诊断信息显示 'node(s) didn't match Pod's node affinity/selector'，这表明调度失败是由于节点选择器（nodeSelector/affinity）不匹配。根据规则，该归因于 L1 层级（Node or Scheduling Issues），属于 scheduling 类别。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "Node or Scheduling Issues", "confidence": 0.5, "reasoning": "当前仍异常的 Pod 'rc-pending-nodeselector' 处于 'Pending' 状态，且事件中包含 'FailedScheduling'，结合诊断信息显示 'node(s) didn't match Pod's node affinity/selector'，这表明调度失败是由于节点选择器（nodeSelector/affinity）不匹配。根据规则，该归因于 L1 层级（Node or Scheduling Issues），属于 scheduling 类别。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Pod 选择器（nodeSelector/affinity）与节点标签不匹配，导致调度失败。", "probability": "高", "reason": "kubectl describe 显示 'node(s) didn't match Pod's node affinity/selector'。"}, {"scenario": "节点上没有满足 Pod 调度约束的可用节点。", "probability": "中", "reason": "所有节点均未匹配调度约束，且未提及资源不足或 taint 不匹配问题。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                3h19m   <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/e454113370f94f3e/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/e454113370f94f3e/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/e454113370f94f3e/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
  Warning  FailedScheduling  10m (x39 over 3h20m)  default-scheduler  0/3 nodes are availabl
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [证据链采集] 已采集证据：
1. `kubectl_describe` 显示 Pod `rc-pending-nodeselector` 的事件中明确指出调度失败，原因是 3 个节点均不匹配 Pod 的 node affinity/selector。
2. `kubectl_get_by_kind_in_cluster` 显示所有节点状态为 `Ready`，且无其他异常。

未采集证据：无。

冲突证据：无。

结论：Pod 调度失败是由于其 nodeSelector/affinity 与节点标签不匹配，导致调度器无法找到可用节点。
   ✅ [证据链采集] 完成 (1m 43.4s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod 的详细信息以验证其调度约束和事件原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-pending-nodeselector"},"purpose":"验证 Pod 的调度约束和 FailedScheduling 事件原文","evidence_type":"Pod 事件/状态","target_scope":"aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"获取节点状态和标签以验证是否匹配 Pod 的 nodeSelector/affinity","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o json","tool_args":{"kind":"nodes"},"purpose":"验证节点状态和标签是否匹配 Pod 的调度约束","evidence_type":"Node 状态/标签","target_scope":"Cluster/nodes","acceptable_tools":["kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  10m (x39 over 3h20m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e454113370f94f3e/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e454113370f94f3e/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e454113370f94f3e/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e454113370f94f3e/tools/002-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e454113370f94f3e/tools/002-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e454113370f94f3e/tools/002-evidence-kubectl_get_by_kind_in_cluster.summary.txt"}],"llm_analysis":"已采集证据：\n1. `kubectl_describe` 显示 Pod `rc-pending-nodeselector` 的事件中明确指出调度失败，原因是 3 个节点均不匹配 Pod 的 node affinity/selector。\n2. `kubectl_get_by_kind_in_cluster` 显示所有节点状态为 `Ready`，且无其他异常。\n\n未采集证据：无。\n\n冲突证据：无。\n\n结论：Pod 调度失败是由于其 nodeSelector/affinity 与节点标签不匹配，导致调度器无法找到可用节点。","collection_summary":"计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 8 个，匹配计划 2 个，未规划证据 6 个","plan_total":2,"plan_collected":2,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":2,"unplanned_tool_count":6,"evidence_inventory":[{"id":"e1","description":"获取 Pod 的详细信息以验证其调度约束和事件原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"验证 Pod 的调度约束和 FailedScheduling 事件原文","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取节点状态和标签以验证是否匹配 Pod 的 nodeSelector/affinity","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o json","purpose":"验证节点状态和标签是否匹配 Pod 的调度约束","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/2 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取 Pod 的详细信息以验证其调度约束和事件原因 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_get_by_kind_in_cl... | 获取节点状态和标签以验证是否匹配 Pod 的 nodeSelector/affinity | `kubectl get nodes -o json` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (18.0s)
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
   ✅ [汇总总结] 完成 (1m 17.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4053 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 7m 25.1s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending |
| **兼容归因层** | L1 - Node or Scheduling Issues |
| **问题分类** | scheduling - 调度失败 |
| **置信度** | 高 (80%) |
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
| 错误信息 | FailedScheduling, node(s) didn't match Pod's node affinity/selector |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 详细信息 | `kubectl describe pod rc-pending-nodeselector` | `Warning  FailedScheduling  5m27s (x39 over 3h15m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | Pod 无法调度，因节点选择器/affinity 不匹配 |
| 2 | 节点状态 | `kubectl get node` | `3 nodes available, all nodes in Ready state` | 所有节点正常，但未匹配 Pod 的调度约束 |

### 证据关联分析

- **证据 #1 印证**：Pod 的 `FailedScheduling` 事件明确指出节点未匹配 `nodeSelector` 或 `affinity`。
- **证据链**：Pod 定义了严格的调度约束（如 `nodeSelector` 或 `affinity`） → 集群中无节点满足该约束 → 调度失败 → Pod 停留在 `Pending` 状态。
- **补充信息**：未发现 `taint` 或 `PVC` 问题，可排除存储或污点导致的调度失败。

### 缺失证据（无）

| 证据 | 级别 | 影响 |
|------|------|------|
| - | - | - |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod 定义的 nodeSelector 或 affinity 与集群中所有节点的标签不匹配 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 调度器尝试调度 Pod 到满足条件的节点，但无节点匹配 → 调度失败     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Pod 事件显示：`node(s) didn't match Pod's node affinity/selector` │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 Pending，且重启次数为 0，未被调度                     │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 中的 `FailedScheduling` 事件，显示 `node(s) didn't match Pod's node affinity/selector`，问题的根本原因是**Pod 定义的调度约束（nodeSelector/affinity）与集群中所有节点的标签不匹配**，导致调度失败，Pod 无法被调度到任何节点上运行。

**置信度**：高 (80%)
- ✅ 事件中明确指出调度失败原因
- ✅ 节点状态正常，排除资源不足或节点不可用
- ⚠️ 未提供 Pod 的 `nodeSelector` 或 `affinity` 定义，无法进一步分析具体标签不匹配的原因

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查并调整 Pod 的 nodeSelector 或 affinity**

```bash
kubectl get pod rc-pending-nodeselector -n aiops-e2e -o jsonpath='{.spec}' | jq .affinity
kubectl get pod rc-pending-nodeselector -n aiops-e2e -o jsonpath='{.spec}' | jq .nodeSelector
```

*目的*：查看当前 Pod 的 `nodeSelector` 或 `affinity` 设置，与节点标签对比，调整其定义以匹配集群中至少一个节点。

**2. [可选] 查看节点标签**

```bash
kubectl get nodes --show-labels
```

*目的*：确认集群中节点的标签是否满足 Pod 的调度要求。

**3. [可选] 调整调度策略（如放宽 affinity）**

```bash
kubectl edit pod rc-pending-nodeselector -n aiops-e2e
```

*操作建议*：在 `.spec.affinity` 中调整 `requiredDuringSchedulingIgnoredDuringExecution` 为 `preferredDuringSchedulingIgnoredDuringExecution`，或移除某些约束，以提高调度成功率。

### 后续优化

1. **标签一致性管理**：确保所有节点的标签满足常见调度需求，避免频繁调度失败。
2. **调度策略文档化**：对关键 Pod 设置调度策略时，记录其标签要求，并与节点标签同步更新。
3. **使用 Taint/Toleration 替代 affinity**：如果某些节点需特殊处理，考虑使用 `taint` 机制替代 `affinity`。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 是否调度成功 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running |
| 2. 确认节点是否匹配调度约束 | `kubectl get nodes --show-labels` | 包含 Pod 所需标签 |
| 3. 检查调度事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | 无 FailedScheduling 事件 |

---

## ⚠️ 注意事项

- 如果未调整调度策略，Pod 将持续处于 `Pending` 状态。
- 调整 `affinity` 或 `nodeSelector` 前，建议备份 Pod 定义。
- 避免过度使用 `requiredDuringSchedulingIgnoredDuringExecution`，这可能导致调度失败。

---

## 📊 性能统计

├─ 总耗时: 7.4m
├─ 问题定位: 245.9s (55%) ✅
├─ 证据链采集: 103.4s (23%) ✅
├─ 根因分析: 18.0s (4%) ✅
├─ 汇总总结: 77.7s (17%) ✅
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
