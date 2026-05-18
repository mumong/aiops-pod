======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 5d6b4b4f30ca45e0]

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
name: rc-pending-missing-pvc
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  41m                default-scheduler  0/3 nodes are available: p
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                     READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-missing-pvc   0/1     Pending   0          41m   <none>   <none>   <n
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 表格摘要: rows=1 abnormal=1 status_counts={'Pending': 1}
NAME                     READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   L
   💭 [问题定位] {
  "layer": "L1",
  "derived_layer": "L1",
  "layers": [
    "L1"
  ],
  "layer_name": "PendingUnschedulable",
  "confidence": 0.95,
  "reasoning": "当前 Pod rc-pending-missing-pvc 处于 Pending 状态，且调度失败事件显示 PVC 未找到，属于典型的调度失败问题。Pod 无法绑定 PVC 是导致调度失败的关键原因。",
  "abnormal_pods": [
    "rc-pending-missing-pvc"
  ],
  "abnormal_groups": [
    "PendingUnschedulable"
  ],
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "PendingUnschedulable",
  "status_category": "Scheduling",
  "key_entities": [
    "rc-pending-missing-pvc",
    "persistentvolumeclaim \"rc-pending-definitely-missing-pvc\""
  ],
  "possible_scenarios": [
    "PVC \"rc-pending-definitely-missing-pvc\" 不存在或未绑定，导致 Pod 调度失败。",
    "Pod 的 PVC 依赖未满足，导致调度器无法分配节点。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (46.1s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'PVC "rc-pending-definitely-missing-pvc" 不存在或未绑定，导致 Pod 调度失败。', 'probability': 'High', 'reason': 'FailedScheduling 事件明确指出 PVC 未找到。'}, {'scenario': 'Pod 的 PVC 依赖未满足，导致调度器无法分配节点。', 'probability': 'High', 'reason': 'Pod 调度失败事件与 PVC 未绑定直接相关。'}]
   entities=[{"type": "Pod", "name": "rc-pending-missing-pvc", "namespace": "aiops-e2e"}, {"type": "PersistentVolumeClaim", "name": "rc-pending-definitely-missing-pvc", "namespace": "aiops-e2e"}]
   reasoning=当前 Pod rc-pending-missing-pvc 处于 Pending 状态，且调度失败事件显示 PVC 未找到，属于典型的调度失败问题。Pod 无法绑定 PVC 是导致调度失败的关键原因。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "当前 Pod rc-pending-missing-pvc 处于 Pending 状态，且调度失败事件显示 PVC 未找到，属于典型的调度失败问题。Pod 无法绑定 PVC 是导致调度失败的关键原因。", "abnormal_pods": [{"name": "rc-pending-missing-pvc", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "Scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-missing-pvc", "namespace": "aiops-e2e"}, {"type": "PersistentVolumeClaim", "name": "rc-pending-definitely-missing-pvc", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "PVC \"rc-pending-definitely-missing-pvc\" 不存在或未绑定，导致 Pod 调度失败。", "probability": "High", "reason": "FailedScheduling 事件明确指出 PVC 未找到。"}, {"scenario": "Pod 的 PVC 依赖未满足，导致调度器无法分配节点。", "probability": "High", "reason": "Pod 调度失败事件与 PVC 未绑定直接相关。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-missing-pvc"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-missing-pvc"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-missing-pvc                              0/1     Pending     0             41m    <none>           <none>   <none>           <none>            app=rc-pending-missing-pvc,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/5d6b4b4f30ca45e0/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/5d6b4b4f30ca45e0/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/5d6b4b4f30ca45e0/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=227 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide persistentvolumeclaim rc-pending-definitely-missing-pvc -n aiops-e2e
Error from server (NotFo
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (1m 46.7s)
   📤 → 下游数据: evidence_items=7/8
   evidence_analysis={"evidence_plan":[{"id":"pvc-existence-check","description":"确认 PVC 'rc-pending-definitely-missing-pvc' 是否存在于命名空间 'aiops-e2e' 中。","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get persistentvolumeclaim rc-pending-definitely-missing-pvc -n aiops-e2e","tool_args":{"kind":"persistentvolumeclaim","name":"rc-pending-definitely-missing-pvc","namespace":"aiops-e2e"},"purpose":"验证 PVC 是否存在并已被绑定。","evidence_type":"existence","target_scope":"aiops-e2e","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true},{"id":"pod-scheduling-events","description":"获取 Pod 'rc-pending-missing-pvc' 的调度事件，确认调度失败原因。","level":"critical","tool":"kubectl_events","command":"kubectl describe pod rc-pending-missing-pvc -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-pending-missing-pvc","namespace":"aiops-e2e"},"purpose":"确认 Pod 是否因 PVC 未找到而无法调度。","evidence_type":"event","target_scope":"aiops-e2e","acceptable_tools":["kubectl_events","kubectl_describe"],"counts_for_completeness":true},{"id":"pvc-status","description":"检查 PVC 'rc-pending-definitely-missing-pvc' 的状态和绑定情况。","level":"important","tool":"kubectl_get_by_name","command":"kubectl get persistentvolumeclaim rc-pending-definitely-missing-pvc -n aiops-e2e -o json","tool_args":{"kind":"persistentvolumeclaim","name":"rc-pending-definitely-missing-pvc","namespace":"aiops-e2e","output":"json"},"purpose":"验证 PVC 是否存在以及其状态是否为 Bound。","evidence_type":"status","target_scope":"aiops-e2e","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=227 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide persistentvolumeclaim rc-pending-definitely-missing-pvc -n aiops-e2e\nError from server (NotFound): persistentvolumeclaims \"rc-pending-definitely-missing-pvc\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/5d6b4b4f30ca45e0/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/5d6b4b4f30ca45e0/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/5d6b4b4f30ca45e0/tools/001-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 3 项，实际采集 2 项，未采集 1 项，完整度 67%；其中真实环境证据 7/8 项，完整度 88%；实际执行工具 5 个，匹配计划 2 个，未规划证据 3 个","plan_total":3,"plan_collected":2,"plan_completeness":0.6666666666666666,"environment_evidence_total":8,"environment_evidence_collected":7,"environment_evidence_completeness":0.875,"executed_tool_count":5,"matched_tool_count":2,"unplanned_tool_count":3,"evidence_inventory":[{"id":"pvc-existence-check","description":"确认 PVC 'rc-pending-definitely-missing-pvc' 是否存在于命名空间 'aiops-e2e' 中。","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get persistentvolumeclaim rc-pending-definitely-missing-pvc -n aiops-e2e","purpose":"验证 PVC 是否存在并已被绑定。","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"pod-scheduling-events","description":"获取 Pod 'rc-pending-missing-pvc' 的调度事件，确认调度失败原因。","level":"critical","tool":"kubectl_events","command":"kubectl describe pod rc-pending-missing-pvc -n aiops-e2e","purpose":"确认 Pod 是否因 PVC 未找到而无法调度。","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"pvc-status","description":"检查 PVC 'rc-pending-definitely-missing-pvc' 的状态和绑定情况。","level":"important","tool":"kubectl_get_by_name","command":"kubectl get persistentvolumeclaim rc-pending-definitely-missing-pvc -n aiops-e2e -o json","purpose":"验证 PVC 是否存在以及其状态是否为 Bound。","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["pvc-status(检查 PVC 'rc-pending-definitely-missing-pvc' 的状态和绑定情况。): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/3 项, 完整度: 88%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | pvc-existence... | critical | ✅ | kubectl_get_by_name | 确认 PVC 'rc-pending-definitely-missing-pvc' 是否... | `kubectl get persistentvolumeclaim rc-pending-definitely-missing-pvc -n aiops-e2e` |
   | pod-schedulin... | critical | ✅ | kubectl_events | 获取 Pod 'rc-pending-missing-pvc' 的调度事件，确认调度失败原因。 | `kubectl describe pod rc-pending-missing-pvc -n aiops-e2e` |
   | pvc-status | important | ❌ | kubectl_get_by_name | 检查 PVC 'rc-pending-definitely-missing-pvc' 的状... | `kubectl get persistentvolumeclaim rc-pending-definitely-missing-pvc -n aiops-...` |

   ⚠️ 未采集原因:
   - pvc-status(检查 PVC 'rc-pending-definitely-missing-pvc' 的状态和绑定情况。): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (36.0s)
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
   ✅ [汇总总结] 完成 (1m 31.1s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4196 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 39.9s
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
| **问题分类** | PVC 未绑定导致调度失败 |
| **置信度** | 高 (95%) |
| **证据完整度** | 2/3 (67%) |

---

## 🔍 现象描述

**用户报告**：  
> 我的集群有什么问题

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | rc-pending-missing-pvc |
| Namespace | aiops-e2e |
| 错误信息 | persistentvolumeclaim "rc-pending-definitely-missing-pvc" not found |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: Pending, REASON: PendingUnschedulable` | Pod 无法调度 |
| 2 | 调度事件 | `kubectl describe pod` | `Warning  FailedScheduling  41m                default-scheduler  0/3 nodes are available: persistentvolumeclaim "rc-pending-definitely-missing-pvc" not found` | 调度失败原因明确为 PVC 未找到 |
| 3 | PVC 存在性 | `kubectl get pvc` | `Error from server (NotFound): persistentvolumeclaim "rc-pending-definitely-missing-pvc" not found` | PVC 不存在，导致 Pod 无法调度 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 处于 Pending 状态，且调度失败事件明确指出 PVC 未找到 → 问题根源在于 PVC 未绑定。
- **证据链**：Pod 依赖的 PVC 不存在 → 调度器无法为 Pod 分配节点 → Pod 持续处于 Pending 状态。
- **关键信号**：`Warning  FailedScheduling` 中明确指出 `persistentvolumeclaim "rc-pending-definitely-missing-pvc" not found`，表明 PVC 缺失是调度失败的直接原因。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| PVC 状态和绑定情况 | critical | 无法确认 PVC 是否已创建或绑定，但根据事件可推断其缺失 |

---

## 🎯 根因分析

### 因果链

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                   │
│ PVC "rc-pending-definitely-missing-pvc" 不存在或未绑定，导致调度失败         │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                   │
│ Pod 依赖的 PVC 不存在 → 调度器无法为 Pod 分配节点 → Pod 无法启动              │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                   │
│ 调度失败事件：`persistentvolumeclaim "rc-pending-definitely-missing-pvc" not found` │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                               │
│ Pod rc-pending-missing-pvc 处于 Pending 状态，调度失败，无法启动              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Pod 状态为 Pending)、证据 #2 (调度失败事件) 和证据 #3 (PVC 未找到)，问题的根本原因是 **Pod 依赖的 PVC "rc-pending-definitely-missing-pvc" 不存在或未绑定**，导致调度器无法为 Pod 分配节点。

**置信度**：高 (95%)

- ✅ Pod 状态为 Pending，且调度失败事件明确指出 PVC 未找到。
- ✅ PVC 不存在的证据明确（`kubectl get pvc` 返回 Not Found）。
- ⚠️ 缺少 PVC 状态和绑定情况的进一步验证。

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 创建缺失的 PVC**

```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: rc-pending-definitely-missing-pvc
  namespace: aiops-e2e
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
EOF
```

*依据*：调度失败事件明确指出 PVC 缺失，需先创建 PVC 并绑定到 Pod。

**2. [可选] 确认 PVC 是否已成功绑定**

```bash
kubectl get pvc rc-pending-definitely-missing-pvc -n aiops-e2e
```

*目的*：确认 PVC 已创建并处于 Bound 状态。

### 后续优化

1. **验证 Pod 状态**：确认 Pod 是否已调度并启动。
2. **配置 PVC 自动绑定机制**：确保 PVC 和 PV 的命名/存储类匹配。
3. **监控 PVC/PV 状态**：使用监控工具（如 Prometheus）监控 PVC 的绑定状态。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 PVC 存在 | `kubectl get pvc rc-pending-definitely-missing-pvc -n aiops-e2e` | PVC 存在，状态为 Bound |
| 2. 确认 Pod 状态 | `kubectl get pod rc-pending-missing-pvc -n aiops-e2e` | STATUS: Running |
| 3. 确认调度事件 | `kubectl describe pod rc-pending-missing-pvc -n aiops-e2e` | 无 FailedScheduling 事件 |

---

## ⚠️ 注意事项

- 如果 PVC 已存在但状态为 `Pending`，需要检查 PV 是否已正确绑定。
- 如果 PVC 已绑定但 Pod 仍无法启动，请检查 Pod 的其他依赖（如 nodeSelector、affinity、taints 等）。
- 建议为 PVC 配置合理的存储类和访问模式，确保调度器能正确绑定。

---

## 📊 性能统计

├─ 总耗时: 4.7m
├─ 问题定位: 46.1s (16%) ✅
├─ 证据链采集: 106.7s (38%) ✅
├─ 根因分析: 36.0s (13%) ✅
├─ 汇总总结: 91.1s (33%) ✅
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
