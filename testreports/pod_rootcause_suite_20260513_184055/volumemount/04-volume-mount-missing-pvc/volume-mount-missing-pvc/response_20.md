======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 6f98150f197e445e]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Pending': 1, 'Running': 46}
NAMESPACE     NAME                                                READY   STATUS      RESTARTS      
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod VolumeMountFailed / 卷挂载失败

> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume

## 使用原则（给模型）
- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。
- `kubectl
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                    READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-volume-missing-pvc   0/1     Pending   0          45m   <none>   <none>   <non
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
45m                 Warning   FailedScheduling   Pod/rc-volume-missing-pvc   0/3 nodes are available: persistentvolumeclaim "rc-definitely-missing-pvc" not found. preemption:
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=211 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide persistentvolumeclaim rc-definitely-missing-pvc -n aiops-e2e
Error from server (NotFound): pe
   💭 [问题定位] {
  "layer": "L0",
  "derived_layer": "L0",
  "layers": ["L0"],
  "layer_name": "VolumeMountFailed",
  "confidence": 0.95,
  "reasoning": "Pod 'rc-volume-missing-pvc' 处于 Pending 状态，Events 显示 'persistentvolumeclaim "rc-definitely-missing-pvc" not found'。kubectl get pvc 显示该 PVC 不存在。这表明 PVC 缺失导致 Pod 无法调度，属于 L0 层次的问题。",
  "abnormal_pods": ["rc-volume-missing-pvc"],
  "abnormal_groups": ["VolumeMountFailed"],
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "VolumeMountFailed",
  "status_category": "Pending",
  "key_entities": ["rc-volume-missing-pvc", "rc-definitely-missing-pvc"],
  "possible_scenarios": ["PVC 'rc-definitely-missing-pvc' 未创建或配置错误，导致 Pod 'rc-volume-missing-pvc' 无法调度。"]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 20.9s)
   📤 → 下游数据: layer=Layer.L0, layers=L0
   scenarios=[]
   entities=[]
   reasoning=Pod 'rc-volume-missing-pvc' 处于 Pending 状态，Events 显示 'persistentvolumeclaim "rc-definitely-missing-pvc" not found'。kubectl get pvc 显示该 PVC 不存在。这表明 PVC 缺失导致 Pod 无法调度，属于 L0 层次的问题。
   layer_analysis={"layer": "L0", "derived_layer": "L0", "layers": ["L0"], "layer_name": "VolumeMountFailed", "confidence": 0.95, "reasoning": "Pod 'rc-volume-missing-pvc' 处于 Pending 状态，Events 显示 'persistentvolumeclaim \"rc-definitely-missing-pvc\" not found'。kubectl get pvc 显示该 PVC 不存在。这表明 PVC 缺失导致 Pod 无法调度，属于 L0 层次的问题。", "abnormal_pods": [{"name": "rc-volume-missing-pvc", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "VolumeMountFailed", "status_category": "Pending", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-pvc"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-pvc"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-volume-missing-pvc                               0/1     Pending     0                45m     <none>           <none>   <none>           <none>            app=rc-volume-missing-pvc,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/6f98150f197e445e/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/6f98150f197e445e/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/6f98150f197e445e/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L0
   置信度: 95%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-missing-pvc
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  47m                  default-scheduler  0/3 nodes are available: 
   💭 [证据链采集] 已采集证据：
- Pod `rc-volume-missing-pvc` 处于 Pending 状态，且调度失败的事件显示 PVC `rc-definitely-missing-pvc` 不存在。
- 事件信息表明这是典型的 VolumeMountFailed 问题，因为 PVC 缺失导致 Pod 无法被调度。

未采集证据：
- 无。

冲突证据：
- 无。

结论：
Pod `rc-volume-missing-pvc` 无法调度的原因是它引用的 PVC `rc-definitely-missing-pvc` 不存在。建议检查 PVC 是否存在，或者确认 Pod 的配置是否引用了正确的 PVC。
   ✅ [证据链采集] 完成 (44.3s)
   📤 → 下游数据: evidence_items=5/5
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取Pod 'rc-volume-missing-pvc' 的详细信息以验证Pending状态的原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-missing-pvc -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-volume-missing-pvc","kind":"pod"},"purpose":"验证Pod的Pending状态的具体原因，例如FailedMount或FailedScheduling事件","evidence_type":"event","target_scope":"aiops-e2e/rc-volume-missing-pvc","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-missing-pvc\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  47m                  default-scheduler  0/3 nodes are available: persistentvolumeclaim \"rc-definitely-missing-pvc\" not found. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  2m32s (x9 over 42m)  default-scheduler  0/3 nodes are available: persistentvolumeclaim \"rc-definitely-missing-pvc\" not found. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6f98150f197e445e/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6f98150f197e445e/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6f98150f197e445e/tools/001-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"已采集证据：\n- Pod `rc-volume-missing-pvc` 处于 Pending 状态，且调度失败的事件显示 PVC `rc-definitely-missing-pvc` 不存在。\n- 事件信息表明这是典型的 VolumeMountFailed 问题，因为 PVC 缺失导致 Pod 无法被调度。\n\n未采集证据：\n- 无。\n\n冲突证据：\n- 无。\n\n结论：\nPod `rc-volume-missing-pvc` 无法调度的原因是它引用的 PVC `rc-definitely-missing-pvc` 不存在。建议检查 PVC 是否存在，或者确认 Pod 的配置是否引用了正确的 PVC。","collection_summary":"计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%；其中真实环境证据 5/5 项，完整度 100%；实际执行工具 5 个，匹配计划 1 个，未规划证据 4 个","plan_total":1,"plan_collected":1,"plan_completeness":1.0,"environment_evidence_total":5,"environment_evidence_collected":5,"environment_evidence_completeness":1.0,"executed_tool_count":5,"matched_tool_count":1,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"获取Pod 'rc-volume-missing-pvc' 的详细信息以验证Pending状态的原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-missing-pvc -n aiops-e2e","purpose":"验证Pod的Pending状态的具体原因，例如FailedMount或FailedScheduling事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/1 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取Pod 'rc-volume-missing-pvc' 的详细信息以验证Pending... | `kubectl describe pod rc-volume-missing-pvc -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (50.8s)
   📤 → 下游数据: root_cause=Pod 'rc-volume-missing-pvc' 无法调度的原因是它引用的 PVC 'rc-definitely-missing-pvc' 不存在。根据 kubectl_events 和 kubectl_get_by_name 的证据，PVC 'rc-definitely-missing-pvc' 不存在，导致调度失败。
   confidence=95%
   causal_chain={"root_cause": "PVC 'rc-definitely-missing-pvc' 不存在", "intermediate_causes": ["Pod 'rc-volume-missing-pvc' 引用了不存在的 PVC 'rc-definitely-missing-pvc'", "调度器无法找到 PVC 'rc-definitely-missing-pvc'，导致 Pod 无法调度"], "immediate_effects": ["Pod 'rc-volume-missing-pvc' 处于 Pending 状态"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"tool": "kubectl_describe", "description": "Pod 'rc-volume-missing-pvc' 处于 Pending 状态，Events 显示 'persistentvolumeclaim \"rc-definitely-missing-pvc\" not found'"}, {"tool": "kubectl_get_by_kind_in_cluster", "description": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Pending': 1, 'Running': 46}"}, {"tool": "kubectl_get_by_name", "description": "kubectl_get_by_name 输出摘要: NAME READY STATUS RESTARTS AGE IP NODE NOMINATED NODE READINESS GATES LABELS rc-volume-missing-pvc 0/1 Pending 0 45m <none> <none> <none> <none> app=rc-volume-missing-pvc,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"}, {"tool": "kubectl_events", "description": "kubectl_events 摘要: 关键诊断行: 45m Warning FailedScheduling Pod/rc-volume-missing-pvc 0/3 nodes are available: persistentvolumeclaim \"rc-definitely-missing-pvc\" not found. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.. 58s (x9 over 40m) Warning FailedScheduling Pod/rc-volume-missing-pvc 0/3 nodes are available: persistentvolumeclaim \"rc-definitely-missing-pvc\" not found. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.."}, {"tool": "kubectl_get_by_name", "description": "kubectl_get_by_name 输出摘要: raw_chars=211 lines=3 Command failed (exit 1): kubectl get --show-labels -o wide persistentvolumeclaim rc-definitely-missing-pvc -n aiops-e2e Error from server (NotFound): persistentvolumeclaims \"rc-definitely-missing-pvc\" not found"}], "evidence_analysis": [{"tool": "kubectl_describe", "description": "Pod 'rc-volume-missing-pvc' 的事件显示 PVC 'rc-definitely-missing-pvc' 不存在，导致调度失败"}, {"tool": "kubectl_get_by_kind_in_cluster", "description": "Pod 'rc-volume-missing-pvc' 处于 Pending 状态，确认存在异常"}, {"tool": "kubectl_get_by_name", "description": "Pod 'rc-volume-missing-pvc' 处于 Pending 状态，确认存在异常"}, {"tool": "kubectl_events", "description": "Pod 'rc-volume-missing-pvc' 的事件显示 PVC 'rc-definitely-missing-pvc' 不存在，导致调度失败"}, {"tool": "kubectl_get_by_name", "description": "PVC 'rc-definitely-missing-pvc' 不存在，确认了调度失败的原因"}], "causal_chain": {"root_cause": "PVC 'rc-definitely-missing-pvc' 不存在", "intermediate_causes": ["Pod 'rc-volume-missing-pvc' 引用了不存在的 PVC 'rc-definitely-missing-pvc'", "调度器无法找到 PVC 'rc-definitely-missing-pvc'，导致 Pod 无法调度"], "immediate_effects": ["Pod 'rc-volume-missing-pvc' 处于 Pending 状态"]}, "root_cause": "Pod 'rc-volume-missing-pvc' 无法调度的原因是它引用的 PVC 'rc-definitely-missing-pvc' 不存在。根据 kubectl_events 和 kubectl_get_by_name 的证据，PVC 'rc-definitely-missing-pvc' 不存在，导致调度失败。", "root_cause_summary": "Pod 'rc-volume-missing-pvc' 无法调度的原因是它引用的 PVC 'rc-definitely-missing-pvc' 不存在。根据 kubectl_events 和 kubectl_get_by_name 的证据，PVC 'rc-definitely-missing-pvc' 不存在，导致调度失败。", "confidence": 0.95, "confidence_reason": "有直接证据表明 PVC 'rc-definitely-missing-pvc' 不存在，因果链清晰。", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [], "limitations": "无", "llm_raw_analysis": "已采集证据：\n- Pod `rc-volume-missing-pvc` 处于 Pending 状态，且调度失败的事件显示 PVC `rc-definitely-missing-pvc` 不存在。\n- 事件信息表明这是典型的 VolumeMountFailed 问题，因为 PVC 缺失导致 Pod 无法被调度。\n\n未采集证据：\n- 无。\n\n冲突证据：\n- 无。\n\n结论：\nPod `rc-volume-missing-pvc` 无法调度的原因是它引用的 PVC `rc-definitely-missing-pvc` 不存在。建议检查 PVC 是否存在，或者确认 Pod 的配置是否引用了正确的 PVC。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'rc-volume-missing-pvc' 无法调度的原因是它引用的 PVC 'rc-definitely-missing-pvc' 不存在。根据 kubectl_events 和 kubectl_get_by_name 的证据，PVC 'rc-definitely-missing-pv...
   置信度: 95%
   🔗 因果链:
     根本原因: PVC 'rc-definitely-missing-pvc' 不存在


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 27.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3731 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 23.7s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending |
| **兼容归因层** | L0 |
| **问题分类** | VolumeMountFailed |
| **置信度** | 高 (95%) |
| **证据完整度** | 1/1 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | rc-volume-missing-pvc |
| Namespace | aiops-e2e |
| Node | <none> |
| 错误信息 | `persistentvolumeclaim "rc-definitely-missing-pvc" not found` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | kubectl get pod | `STATUS: Pending` | Pod 无法调度 |
| 2 | Events | kubectl events | `Warning FailedScheduling Pod/rc-volume-missing-pvc 0/3 nodes are available: persistentvolumeclaim "rc-definitely-missing-pvc" not found` | PVC 缺失导致调度失败 |
| 3 | PVC 状态 | kubectl get pvc | `Error from server (NotFound): persistentvolumeclaims "rc-definitely-missing-pvc" not found` | PVC 确实不存在 |
| 4 | Pod 详细信息 | kubectl describe pod | `persistentvolumeclaim "rc-definitely-missing-pvc" not found` | Pod 依赖的 PVC 不存在 |
| 5 | Runbook | fetch_runbook | `VolumeMountFailed | 典型状态: Pending | 兼容分类: storage_volume` | 问题属于 VolumeMountFailed 类型 |

### 证据关联分析

- **证据 #2 + #3 印证**：Events 明确指出 PVC 不存在，而 kubectl get pvc 确认该 PVC 确实不存在。
- **证据链**：Pod 指定了一个 PVC → 但该 PVC 不存在 → 调度器无法为 Pod 分配节点 → Pod 保持 Pending 状态。

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ PVC 'rc-definitely-missing-pvc' 不存在                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Pod 指定了该 PVC 作为卷，但调度器无法找到该 PVC → 无法调度       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Pod 保持 Pending 状态，调度失败                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 'rc-volume-missing-pvc' 状态为 Pending，Events 显示 PVC 不存在 |
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2 (Events 显示 `persistentvolumeclaim "rc-definitely-missing-pvc" not found`) 和证据 #3 (`kubectl get pvc` 明确显示 PVC 不存在)，问题的根本原因是**Pod 'rc-volume-missing-pvc' 依赖的 PVC 'rc-definitely-missing-pvc' 不存在**，导致调度失败。
**置信度**：高 (95%)
- ✅ Events 明确指出 PVC 不存在
- ✅ `kubectl get pvc` 确认 PVC 不存在
- ✅ 无缺失关键证据

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 创建缺失的 PVC**
```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: rc-definitely-missing-pvc
  namespace: aiops-e2e
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
EOF
```
*依据*：证据 #3 显示 PVC 不存在，需创建该 PVC

**2. [可选] 验证 PVC 是否创建成功**
```bash
kubectl get pvc rc-definitely-missing-pvc -n aiops-e2e
```
*目的*：确认 PVC 是否成功创建并绑定

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 PVC 存在 | `kubectl get pvc rc-definitely-missing-pvc -n aiops-e2e` | STATUS: Bound |
| 2. 确认 Pod 运行 | `kubectl get pod rc-volume-missing-pvc -n aiops-e2e` | STATUS: Running |
| 3. 检查调度器事件 | `kubectl events -n aiops-e2e` | 无 `FailedScheduling` 事件 |

---

## ⚠️ 注意事项

- 如果 PVC 创建后 Pod 仍为 Pending，需检查 PVC 是否绑定成功，或检查 StorageClass 是否配置正确。
- 如果 PVC 需要绑定到特定存储后端（如 NFS、AWS EBS 等），确保相关存储配置正确。
- 如果 PVC 需要手动审批（如 `WaitForFirstConsumer` 模式），需确认调度器已正确处理。

---

## 📊 性能统计

├─ 总耗时: 4.4m
├─ 问题定位: 80.9s (31%) ✅
├─ 证据链采集: 44.3s (17%) ✅
├─ 根因分析: 50.8s (19%) ✅
├─ 汇总总结: 87.8s (33%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 6 次
```

📋 诊断追踪

- **核心 Runbook**: pod-volume-mount-failed
- **参考 Runbook**: pod-volume-mount-failed
- **工具调用**: 6 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
