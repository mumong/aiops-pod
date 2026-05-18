======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 32ab71055ef2455a]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Running': 46}
NAMESPACE     NAME                                                READY   STATUS              RESTARTS        AGE 
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
      📄 NAME                          READY   STATUS              RESTARTS   AGE   IP       NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-volume-missing-configmap   0/1     ContainerCreating   0       
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
43m (x10 over 47m)    Warning   FailedMount   Pod/rc-volume-missing-configmap   MountVolume.SetUp failed for volume "missing-config" : configmap "rc-definitely-missing-config
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=199 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide configmap rc-definitely-missing-configmap -n aiops-e2e
Error from server (NotFound): configma
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "ConfigError",
  "confidence": 0.95,
  "reasoning": "Pod rc-volume-missing-configmap 的 VolumeMountFailed 异常归因于 ConfigMap 'rc-definitely-missing-configmap' 未找到。这是典型的配置错误（ConfigError），属于 L4 层级。Events 显示 MountVolume.SetUp failed 的具体原因是 configmap not found，且 kubectl get configmap 明确返回 Not Found。此问题需要检查 ConfigMap 是否定义或引用正确。",
  "abnormal_pods": [
    {
      "name": "rc-volume-missing-configmap",
      "namespace": "aiops-e2e",
      "status": "ContainerCreating",
      "reason": "FailedMount",
      "message": "MountVolume.SetUp failed for volume 'missing-config': configmap 'rc-definitely-missing-configmap' not found"
    }
  ],
  "abnormal_groups": {
    "VolumeMountFailed": 1
  },
  "pod_status_keyword": "ContainerCreating",
  "pod_abnormal_type": "VolumeMountFailed",
  "status_category": "VolumeMountFailed",
  "key_entities": [
    "ConfigMap/rc-definitely-missing-configmap",
    "Pod/rc-volume-missing-configmap"
  ],
  "possible_scenarios": [
    "ConfigMap rc-definitely-missing-configmap 未定义",
    "ConfigMap 被错误命名或引用",
    "Pod 定义中 volumes[].configMap.name 字段错误"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 0.7s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'ConfigMap rc-definitely-missing-configmap 未定义', 'probability': 'high', 'reason': 'Events 明确指出 configmap not found'}, {'scenario': 'ConfigMap 被错误命名或引用', 'probability': 'medium', 'reason': 'Pod 中的 volume 定义可能拼写错误'}, {'scenario': 'Pod 定义中 volumes[].configMap.name 字段错误', 'probability': 'medium', 'reason': 'Pod spec 中引用了错误的 configMap 名称'}]
   entities=[{"type": "ConfigMap", "name": "rc-definitely-missing-configmap", "namespace": ""}, {"type": "Pod", "name": "rc-volume-missing-configmap", "namespace": ""}]
   reasoning=Pod rc-volume-missing-configmap 的 VolumeMountFailed 异常归因于 ConfigMap 'rc-definitely-missing-configmap' 未找到。这是典型的配置错误（ConfigError），属于 L4 层级。Events 显示 MountVolume.SetUp failed 的具体原因是 configmap not found，且 kubectl get configmap 明确返回 Not Found。此问题需要检查 ConfigMap 是否定义或引用正确。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.95, "reasoning": "Pod rc-volume-missing-configmap 的 VolumeMountFailed 异常归因于 ConfigMap 'rc-definitely-missing-configmap' 未找到。这是典型的配置错误（ConfigError），属于 L4 层级。Events 显示 MountVolume.SetUp failed 的具体原因是 configmap not found，且 kubectl get configmap 明确返回 Not Found。此问题需要检查 ConfigMap 是否定义或引用正确。", "abnormal_pods": [{"name": "rc-volume-missing-configmap", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "VolumeMountFailed", "key_entities": [{"type": "ConfigMap", "name": "rc-definitely-missing-configmap", "namespace": ""}, {"type": "Pod", "name": "rc-volume-missing-configmap", "namespace": ""}], "possible_scenarios": [{"scenario": "ConfigMap rc-definitely-missing-configmap 未定义", "probability": "high", "reason": "Events 明确指出 configmap not found"}, {"scenario": "ConfigMap 被错误命名或引用", "probability": "medium", "reason": "Pod 中的 volume 定义可能拼写错误"}, {"scenario": "Pod 定义中 volumes[].configMap.name 字段错误", "probability": "medium", "reason": "Pod spec 中引用了错误的 configMap 名称"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-configmap"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-configmap"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-volume-missing-configmap                         0/1     ContainerCreating   0               16m    <none>           node1    <none>           <none>            app=rc-volume-missing-configmap,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/32ab71055ef2455a/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/32ab71055ef2455a/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/32ab71055ef2455a/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 95%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=199 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide configmap rc-definitely-missing-configmap -n aiops-e2e
Error from server (NotFound): configma
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                          READY   STATUS              RESTARTS   AGE   IP       NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-volume-missing-configmap   0/1     ContainerCreating   0       
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (1m 19.9s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 ConfigMap rc-definitely-missing-configmap 是否存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e","tool_args":{"name":"rc-definitely-missing-configmap","kind":"ConfigMap","namespace":"aiops-e2e"},"purpose":"确认 ConfigMap 是否缺失，这是 VolumeMountFailed 的直接原因。","evidence_type":"negative","target_scope":"aiops-e2e","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e2","description":"检查 Pod rc-volume-missing-configmap 的 volume 配置","level":"important","tool":"kubectl_get_by_name","command":"kubectl get pod rc-volume-missing-configmap -n aiops-e2e -o yaml","tool_args":{"name":"rc-volume-missing-configmap","kind":"Pod","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"确认 Pod 中的 volume 引用了 ConfigMap，并验证引用的 ConfigMap 名称是否正确。","evidence_type":"configuration","target_scope":"aiops-e2e","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e3","description":"获取 Pod rc-volume-missing-configmap 的 Events 信息","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-missing-configmap --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","involved_object_name":"rc-volume-missing-configmap","sort_by":".lastTimestamp"},"purpose":"获取 Pod 的事件记录，确认是否有 FailedMount 等异常事件。","evidence_type":"event","target_scope":"aiops-e2e","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=199 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide configmap rc-definitely-missing-configmap -n aiops-e2e\nError from server (NotFound): configmaps \"rc-definitely-missing-configmap\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/32ab71055ef2455a/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/32ab71055ef2455a/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/32ab71055ef2455a/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                          READY   STATUS              RESTARTS   AGE   IP       NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-volume-missing-configmap   0/1     ContainerCreating   0          18m   <none>   node1   <none>           <none>            app=rc-volume-missing-configmap,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/32ab71055ef2455a/tools/002-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/32ab71055ef2455a/tools/002-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/32ab71055ef2455a/tools/002-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 6 个，匹配计划 3 个，未规划证据 3 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":3,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1","description":"验证 ConfigMap rc-definitely-missing-configmap 是否存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e","purpose":"确认 ConfigMap 是否缺失，这是 VolumeMountFailed 的直接原因。","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"e2","description":"检查 Pod rc-volume-missing-configmap 的 volume 配置","level":"important","tool":"kubectl_get_by_name","command":"kubectl get pod rc-volume-missing-configmap -n aiops-e2e -o yaml","purpose":"确认 Pod 中的 volume 引用了 ConfigMap，并验证引用的 ConfigMap 名称是否正确。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取 Pod rc-volume-missing-configmap 的 Events 信息","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-missing-configmap --sort-by='.lastTimestamp'","purpose":"获取 Pod 的事件记录，确认是否有 FailedMount 等异常事件。","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 验证 ConfigMap rc-definitely-missing-configmap ... | `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_get_by_name | 检查 Pod rc-volume-missing-configmap 的 volume 配置 | `kubectl get pod rc-volume-missing-configmap -n aiops-e2e -o yaml` |
   | e3 | critical | ✅ | kubectl_events | 获取 Pod rc-volume-missing-configmap 的 Events 信息 | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volum...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (15.6s)
   📤 → 下游数据: root_cause=Pod rc-volume-missing-configmap 的 VolumeMountFailed 异常归因于 ConfigMap 'rc-definitely-missing-configmap' 未找到。Events 显示 MountVolume.SetUp failed 的具体原因是 configmap not found，且 kubectl get configmap 明确返回 Not Found。此问题需要检查 ConfigMap 是否定义或引用正确。
   confidence=95%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [], "causal_chain": {}, "root_cause": "Pod rc-volume-missing-configmap 的 VolumeMountFailed 异常归因于 ConfigMap 'rc-definitely-missing-configmap' 未找到。Events 显示 MountVolume.SetUp failed 的具体原因是 configmap not found，且 kubectl get configmap 明确返回 Not Found。此问题需要检查 ConfigMap 是否定义或引用正确。", "root_cause_summary": "Pod rc-volume-missing-configmap 的 VolumeMountFailed 异常归因于 ConfigMap 'rc-definitely-missing-configmap' 未找到。Events 显示 MountVolume.SetUp failed 的具体原因是 configmap not found，且 kubectl get configmap 明确返回 Not Found。此问题需要检查 ConfigMap 是否定义或引用正确。", "confidence": 0.95, "confidence_reason": "", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [], "limitations": "无", "llm_raw_analysis": "根因分析表明，Pod rc-volume-missing-configmap 的异常状态 ContainerCreating 是由于其依赖的 ConfigMap rc-definitely-missing-configmap 不存在。证据显示，kubectl_get_by_name 命令返回 Not Found，而 Events 明确指出 MountVolume.SetUp failed 的原因是 configmap not found。因此，问题的根本原因是 ConfigMap 未定义或引用错误。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-volume-missing-configmap 的 VolumeMountFailed 异常归因于 ConfigMap 'rc-definitely-missing-configmap' 未找到。Events 显示 MountVolume.SetUp failed 的具体原因是 co...
   置信度: 95%

📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 44.9s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4170 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 21.1s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | ContainerCreating |
| **兼容归因层** | L4 |
| **问题分类** | VolumeMountFailed |
| **置信度** | 高 (95%) |
| **证据完整度** | 3/3 (100%) |

---

## 🔍 现象描述

**用户报告**：  
> 我的集群有什么问题？

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | rc-volume-missing-configmap |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | configmap "rc-definitely-missing-configmap" not found |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: ContainerCreating` | Pod 处于创建中状态，无法启动 |
| 2 | Events 信息 | `kubectl describe pod rc-volume-missing-configmap` | `MountVolume.SetUp failed for volume "missing-config": configmap "rc-definitely-missing-configmap" not found` | 明确指出卷挂载失败的原因是 ConfigMap 不存在 |
| 3 | ConfigMap 存在性验证 | `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` | `Error from server (NotFound): configmaps "rc-definitely-missing-configmap" not found` | 证明确实没有这个 ConfigMap |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 处于 ContainerCreating 状态，且 Events 明确指出 `configmap not found`，说明 Pod 无法完成容器创建是因为依赖的 ConfigMap 不存在。
- **证据链**：Pod 挂载配置依赖 ConfigMap → ConfigMap 不存在 → 卷挂载失败 → Pod 无法启动 → 一直停留在 ContainerCreating 状态。

### 缺失证据（无）

| 证据 | 级别 | 影响 |
|------|------|------|
| 无 | - | - |

---

## 🎯 根因分析

### 因果链

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                   │
│ ConfigMap 'rc-definitely-missing-configmap' 未在命名空间 aiops-e2e 中定义    │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                   │
│ Pod 尝试挂载缺失的 ConfigMap → 卷挂载失败 → 容器无法创建 → Pod 处于 ContainerCreating 状态 │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                   │
│ 卷挂载失败，事件显示 `MountVolume.SetUp failed for volume "missing-config"` │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                               │
│ Pod rc-volume-missing-configmap 一直停留在 ContainerCreating 状态          │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Pod 状态为 ContainerCreating)、证据 #2 (Events 显示 `configmap not found`) 和证据 #3 (kubectl get configmap 明确返回 Not Found)，问题的根本原因是 **ConfigMap `rc-definitely-missing-configmap` 未在命名空间 `aiops-e2e` 中定义**，导致 Pod 无法完成容器创建。

**置信度**：高 (95%)
- ✅ Pod 状态为 ContainerCreating
- ✅ Events 明确指出 `MountVolume.SetUp failed`
- ✅ kubectl get configmap 明确返回 Not Found

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 创建缺失的 ConfigMap**

```bash
kubectl create configmap rc-definitely-missing-configmap -n aiops-e2e --from-literal=key1=value1 --from-literal=key2=value2
```

*依据*：Events 明确指出 ConfigMap 不存在，需要手动创建。

**2. [可选] 重新创建 Pod**

```bash
kubectl delete pod rc-volume-missing-configmap -n aiops-e2e
```

*目的*：删除后，Kubernetes 会自动重新调度并使用已创建的 ConfigMap。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 ConfigMap 存在 | `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` | 应显示 ConfigMap 详情 |
| 2. 确认 Pod 状态 | `kubectl get pod rc-volume-missing-configmap -n aiops-e2e` | STATUS: Running |
| 3. 检查 Events | `kubectl describe pod rc-volume-missing-configmap -n aiops-e2e` | 无 FailedMount 事件 |

---

## ⚠️ 注意事项

- 如果 ConfigMap 是由其他工具（如 Helm、Operator）自动创建的，请检查其配置是否正确，是否部署到正确的命名空间。
- 如果问题出现在多个 Pod 上，建议使用 `kubectl get all -n aiops-e2e` 检查是否还有其他 ConfigMap 缺失问题。
- 确保 ConfigMap 的名称与 Pod 中引用的名称完全一致（包括大小写和拼写）。

---

## 📄 附录

- **Runbook 引用**：`pod-volume-mount-failed.md`
- **诊断上下文归档**：`/tmp/aiops/reports/context_archives/32ab71055ef2455a/layer/full_analysis.md`

---

---

## 📊 性能统计

├─ 总耗时: 4.4m
├─ 问题定位: 60.7s (23%) ✅
├─ 证据链采集: 79.9s (31%) ✅
├─ 根因分析: 15.6s (6%) ✅
├─ 汇总总结: 104.9s (40%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 8 次
```

📋 诊断追踪

- **核心 Runbook**: pod-volume-mount-failed
- **参考 Runbook**: pod-volume-mount-failed
- **工具调用**: 8 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
