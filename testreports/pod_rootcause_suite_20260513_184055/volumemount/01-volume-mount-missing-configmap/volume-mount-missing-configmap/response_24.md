======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: a64082f9f2204565]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Running': 46}
NAMESPACE     NAME                                                READY   STATUS              RESTARTS         AGE
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
56m (x12 over 64m)    Warning   FailedMount   Pod/rc-volume-missing-configmap   MountVolume.SetUp failed for volume "missing-config" : configmap "rc-definitely-missing-config
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
  "reasoning": "当前异常 Pod 'rc-volume-missing-configmap' 的状态为 'ContainerCreating'，且 Events 明确指出 'configmap \"rc-definitely-missing-configmap\" not found'。这表明 Pod 的 volume 引用了不存在的 ConfigMap，属于配置错误（ConfigError）。进一步验证显示，尝试获取该 ConfigMap 时返回 'NotFound'。因此，该异常归类为 L4 层级。",
  "abnormal_pods": [
    {
      "name": "rc-volume-missing-configmap",
      "namespace": "aiops-e2e",
      "status": "ContainerCreating",
      "reason": "FailedMount",
      "message": "MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found"
    }
  ],
  "abnormal_groups": [
    {
      "type": "VolumeMountFailed",
      "count": 1
    }
  ],
  "pod_status_keyword": "ContainerCreating",
  "pod_abnormal_type": "VolumeMountFailed",
  "status_category": "VolumeMountFailed",
  "key_entities": [
    "ConfigMap/rc-definitely-missing-configmap",
    "Pod/rc-volume-missing-configmap"
  ],
  "possible_scenarios": [
    "ConfigMap 'rc-definitely-missing-configmap' 不存在，导致 Pod 无法挂载卷。",
    "Pod 配置错误，引用了不存在的 ConfigMap。",
    "需要检查 Pod 的 volume 配置，确认引用的 ConfigMap 是否存在。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (58.5s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': "ConfigMap 'rc-definitely-missing-configmap' 不存在，导致 Pod 无法挂载卷。", 'probability': 'high', 'reason': "Events 明确指出 configmap 'rc-definitely-missing-configmap' not found，且 kubectl get configmap 返回 'NotFound'。"}, {'scenario': 'Pod 配置错误，引用了不存在的 ConfigMap。', 'probability': 'high', 'reason': 'Pod 的 volume 配置引用了不存在的 ConfigMap，导致 MountVolume.SetUp 失败。'}, {'scenario': '需要检查 Pod 的 volume 配置，确认引用的 ConfigMap 是否存在。', 'probability': 'high', 'reason': '当前异常的根本原因是配置错误，建议检查 Pod 的 volume 配置是否引用了正确的 ConfigMap。'}]
   entities=[{"type": "ConfigMap", "name": "rc-definitely-missing-configmap", "namespace": "aiops-e2e"}, {"type": "Pod", "name": "rc-volume-missing-configmap", "namespace": "aiops-e2e"}]
   reasoning=当前异常 Pod 'rc-volume-missing-configmap' 的状态为 'ContainerCreating'，且 Events 明确指出 'configmap "rc-definitely-missing-configmap" not found'。这表明 Pod 的 volume 引用了不存在的 ConfigMap，属于配置错误（ConfigError）。进一步验证显示，尝试获取该 ConfigMap 时返回 'NotFound'。因此，该异常归类为 L4 层级。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.95, "reasoning": "当前异常 Pod 'rc-volume-missing-configmap' 的状态为 'ContainerCreating'，且 Events 明确指出 'configmap \"rc-definitely-missing-configmap\" not found'。这表明 Pod 的 volume 引用了不存在的 ConfigMap，属于配置错误（ConfigError）。进一步验证显示，尝试获取该 ConfigMap 时返回 'NotFound'。因此，该异常归类为 L4 层级。", "abnormal_pods": [{"name": "rc-volume-missing-configmap", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "VolumeMountFailed", "key_entities": [{"type": "ConfigMap", "name": "rc-definitely-missing-configmap", "namespace": "aiops-e2e"}, {"type": "Pod", "name": "rc-volume-missing-configmap", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "ConfigMap 'rc-definitely-missing-configmap' 不存在，导致 Pod 无法挂载卷。", "probability": "high", "reason": "Events 明确指出 configmap 'rc-definitely-missing-configmap' not found，且 kubectl get configmap 返回 'NotFound'。"}, {"scenario": "Pod 配置错误，引用了不存在的 ConfigMap。", "probability": "high", "reason": "Pod 的 volume 配置引用了不存在的 ConfigMap，导致 MountVolume.SetUp 失败。"}, {"scenario": "需要检查 Pod 的 volume 配置，确认引用的 ConfigMap 是否存在。", "probability": "high", "reason": "当前异常的根本原因是配置错误，建议检查 Pod 的 volume 配置是否引用了正确的 ConfigMap。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-configmap"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-configmap"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-volume-missing-configmap                         0/1     ContainerCreating   0                51m    <none>           node1    <none>           <none>            app=rc-volume-missing-configmap,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/a64082f9f2204565/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/a64082f9f2204565/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/a64082f9f2204565/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 95%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-missing-configmap
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  119s (x33 over 52m)  kubelet            MountVolume.Set
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=199 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide configmap rc-definitely-missing-configmap -n aiops-e2e
Error from server (NotFound): configma
   💭 [证据链采集] # 证据结论

## 已采集证据
1. **Pod 'rc-volume-missing-configmap' 的描述信息**:
   - 位于命名空间 `aiops-e2e`。
   - 当前状态为 `Pending`，且 `Reason: ContainerCreating`。
   - 挂载卷失败事件 `MountVolume.SetUp failed for volume "missing-config" : configmap "rc-definitely-missing-configmap" not found` 多次发生。
   - 事件表明，Pod 无法启动，因为其依赖的 ConfigMap `rc-definitely-missing-configmap` 不存在。

2. **ConfigMap 'rc-definitely-missing-configmap' 的获取结果**:
   - 在命名空间 `aiops-e2e` 中未找到该 ConfigMap。
   - `kubectl get` 命令返回 `Error from server (NotFound): configmaps "rc-definitely-missing-configmap" not found`。

## 未采集证据
- 没有进一步检查其他可能的资源或事件。

## 冲突证据
- 无。

## 结论
当前异常的根本原因是 Pod `rc-volume-missing-configmap` 引用了不存在的 ConfigMap `rc-definitely-missing-configmap`，导致其无法成功挂载卷并进入 `ContainerCreating` 状态。建议创建缺失的 ConfigMap 以解决此问题。
   ✅ [证据链采集] 完成 (1m 19.3s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod 'rc-volume-missing-configmap' 的详细描述信息，以确认其 volume 配置和异常原因。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-missing-configmap -n aiops-e2e","tool_args":{"name":"rc-volume-missing-configmap","namespace":"aiops-e2e"},"purpose":"确认 Pod 'rc-volume-missing-configmap' 的 volume 配置以及 MountVolume 失败的具体原因。","evidence_type":"Pod 配置/Events 原文","target_scope":"Pod/aiops-e2e/rc-volume-missing-configmap","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"获取 ConfigMap 'rc-definitely-missing-configmap' 的状态，确认其是否存在。","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e","tool_args":{"name":"rc-definitely-missing-configmap","namespace":"aiops-e2e"},"purpose":"验证 ConfigMap 'rc-definitely-missing-configmap' 是否存在，以确认是否为 Pod 'rc-volume-missing-configmap' 的 volumeMount 失败的直接原因。","evidence_type":"ConfigMap 存在性","target_scope":"ConfigMap/aiops-e2e/rc-definitely-missing-configmap","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-missing-configmap\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  119s (x33 over 52m)  kubelet            MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found\n  Warning  FailedMount  12m (x12 over 50m)   kubelet            Unable to attach or mount volumes: unmounted volumes=[missing-config], unattached volumes=[missing-config kube-api-access-n5pfx]: timed out waiting for the condition\n  Warning  FailedMount  7m41s (x7 over 44m)  kubelet            Unable to attach or mount volumes: unmounted volumes=[missing-config], unattached volumes=[kube-api-access-n5pfx missing-config]: timed out waiting for the condition\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed\n    State:          Waiting\n      Reason:       ContainerCreating","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a64082f9f2204565/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a64082f9f2204565/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a64082f9f2204565/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=199 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide configmap rc-definitely-missing-configmap -n aiops-e2e\nError from server (NotFound): configmaps \"rc-definitely-missing-configmap\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/a64082f9f2204565/tools/002-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a64082f9f2204565/tools/002-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a64082f9f2204565/tools/002-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"# 证据结论\n\n## 已采集证据\n1. **Pod 'rc-volume-missing-configmap' 的描述信息**:\n   - 位于命名空间 `aiops-e2e`。\n   - 当前状态为 `Pending`，且 `Reason: ContainerCreating`。\n   - 挂载卷失败事件 `MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found` 多次发生。\n   - 事件表明，Pod 无法启动，因为其依赖的 ConfigMap `rc-definitely-missing-configmap` 不存在。\n\n2. **ConfigMap 'rc-definitely-missing-configmap' 的获取结果**:\n   - 在命名空间 `aiops-e2e` 中未找到该 ConfigMap。\n   - `kubectl get` 命令返回 `Error from server (NotFound): configmaps \"rc-definitely-missing-configmap\" not found`。\n\n## 未采集证据\n- 没有进一步检查其他可能的资源或事件。\n\n## 冲突证据\n- 无。\n\n## 结论\n当前异常的根本原因是 Pod `rc-volume-missing-configmap` 引用了不存在的 ConfigMap `rc-definitely-missing-configmap`，导致其无法成功挂载卷并进入 `ContainerCreating` 状态。建议创建缺失的 ConfigMap 以解决此问题。","collection_summary":"计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%；其中真实环境证据 6/6 项，完整度 100%；实际执行工具 6 个，匹配计划 2 个，未规划证据 4 个","plan_total":2,"plan_collected":2,"plan_completeness":1.0,"environment_evidence_total":6,"environment_evidence_collected":6,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":2,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"获取 Pod 'rc-volume-missing-configmap' 的详细描述信息，以确认其 volume 配置和异常原因。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-missing-configmap -n aiops-e2e","purpose":"确认 Pod 'rc-volume-missing-configmap' 的 volume 配置以及 MountVolume 失败的具体原因。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 ConfigMap 'rc-definitely-missing-configmap' 的状态，确认其是否存在。","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e","purpose":"验证 ConfigMap 'rc-definitely-missing-configmap' 是否存在，以确认是否为 Pod 'rc-volume-missing-configmap' 的 volumeMount 失败的直接原因。","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/2 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取 Pod 'rc-volume-missing-configmap' 的详细描述信息，... | `kubectl describe pod rc-volume-missing-configmap -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_by_name | 获取 ConfigMap 'rc-definitely-missing-configmap... | `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (22.7s)
   📤 → 下游数据: root_cause=Pod 'rc-volume-missing-configmap' 的 volume 引用了不存在的 ConfigMap 'rc-definitely-missing-configmap'，导致 MountVolume.SetUp 失败。证据包括：kubectl describe 显示 'MountVolume.SetUp failed for volume "missing-config" : configmap "rc-definitely-missing-configmap" not found'，以及 kubectl get configmap 返回 'NotFound'。
   confidence=95%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [], "causal_chain": {}, "root_cause": "Pod 'rc-volume-missing-configmap' 的 volume 引用了不存在的 ConfigMap 'rc-definitely-missing-configmap'，导致 MountVolume.SetUp 失败。证据包括：kubectl describe 显示 'MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found'，以及 kubectl get configmap 返回 'NotFound'。", "root_cause_summary": "Pod 'rc-volume-missing-configmap' 的 volume 引用了不存在的 ConfigMap 'rc-definitely-missing-configmap'，导致 MountVolume.SetUp 失败。证据包括：kubectl describe 显示 'MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found'，以及 kubectl get configmap 返回 'NotFound'。", "confidence": 0.95, "confidence_reason": "证据包括 kubectl describe 和 kubectl get configmap 的输出，明确显示 ConfigMap 不存在，因果链清晰。", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [], "limitations": "未进一步检查其他可能的资源或事件。", "llm_raw_analysis": "当前异常的根本原因是 Pod 'rc-volume-missing-configmap' 引用了不存在的 ConfigMap 'rc-definitely-missing-configmap'，导致其无法成功挂载卷并进入 'ContainerCreating' 状态。建议创建缺失的 ConfigMap 以解决此问题。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'rc-volume-missing-configmap' 的 volume 引用了不存在的 ConfigMap 'rc-definitely-missing-configmap'，导致 MountVolume.SetUp 失败。证据包括：kubectl describe 显示 'Mount...
   置信度: 95%

📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 47.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4602 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 27.6s
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
| **问题分类** | VolumeMountFailed / ConfigMapNotFound |
| **置信度** | 高 (95%) |
| **证据完整度** | 2/2 (100%) |

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

**当前状态总结**：
- Pod `rc-volume-missing-configmap` 处于 `ContainerCreating` 状态
- 事件中多次出现 `MountVolume.SetUp failed for volume "missing-config" : configmap "rc-definitely-missing-configmap" not found`
- 尝试获取 `ConfigMap rc-definitely-missing-configmap` 时返回 `NotFound`
- 问题归类为 L4 层级，属于配置错误（ConfigError）

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: ContainerCreating` | Pod 无法完成容器创建 |
| 2 | 事件记录 | `kubectl get events` | `Warning FailedMount: configmap "rc-definitely-missing-configmap" not found` | 明确指出 ConfigMap 不存在 |
| 3 | ConfigMap 存在性 | `kubectl get configmap` | `Error from server (NotFound): configmaps "rc-definitely-missing-configmap" not found` | 该 ConfigMap 不存在 |
| 4 | Pod 描述 | `kubectl describe pod rc-volume-missing-configmap` | `Warning  FailedMount  119s (x33 over 52m)  kubelet            MountVolume.SetUp failed for volume "missing-config"` | Pod 尝试挂载不存在的 ConfigMap |
| 5 | Runbook 匹配 | `fetch_runbook` | `# Pod VolumeMountFailed / 卷挂载失败` | 匹配 `pod-volume-mount-failed.md` 诊断指南 |
| 6 | 集群上下文 | `kubectl get by kind` | `aiops-e2e rc-volume-missing-configmap 0/1 ContainerCreating` | 确认异常 Pod 存在 |

### 证据关联分析

- **证据 #2 + #3 印证**：`kubectl get events` 明确指出 `configmap not found`，`kubectl get configmap` 验证了该 ConfigMap 确实不存在。
- **证据链**：
  - Pod 配置引用了不存在的 ConfigMap
  - 无法完成卷挂载
  - 导致 Pod 处于 `ContainerCreating` 状态

### 缺失证据（无）

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ ConfigMap 'rc-definitely-missing-configmap' 不存在              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Pod 引用的卷依赖该 ConfigMap，无法挂载导致容器创建失败          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ `MountVolume.SetUp failed for volume "missing-config"`          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 `ContainerCreating`，持续失败                        │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2（`Warning FailedMount: configmap "rc-definitely-missing-configmap" not found`）和证据 #3（`kubectl get configmap` 返回 `NotFound`），问题的根本原因是 **Pod 的 volume 引用了不存在的 ConfigMap `rc-definitely-missing-configmap`**，导致挂载失败，容器无法创建。

**置信度**：高 (95%)
- ✅ 事件明确指出 ConfigMap 不存在
- ✅ `kubectl get configmap` 验证了 ConfigMap 不存在
- ✅ Runbook 匹配 `VolumeMountFailed` 场景

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 创建缺失的 ConfigMap**
```bash
kubectl create configmap rc-definitely-missing-configmap -n aiops-e2e --from-literal=key=value
```
*依据*：ConfigMap 缺失是直接原因，创建后 Pod 可成功挂载

**2. [验证] 确认 ConfigMap 已存在**
```bash
kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e
```
*预期输出*：
```
NAME                        DATA   AGE
rc-definitely-missing-configmap   1      10s
```

**3. [可选] 强制重启 Pod**
```bash
kubectl delete pod rc-volume-missing-configmap -n aiops-e2e
```
*目的*：触发调度器重新创建 Pod，应用新 ConfigMap

### 后续优化

1. **配置检查**：在 CI/CD 或部署流程中加入 ConfigMap 存在性校验
2. **自动化恢复**：使用 Operator 或 Helm Chart 确保 ConfigMap 与 Pod 同步部署
3. **监控告警**：配置事件监控，当出现 `FailedMount` 时触发告警

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 ConfigMap 存在 | `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` | 应返回 ConfigMap 数据 |
| 2. 确认 Pod 状态 | `kubectl get pod rc-volume-missing-configmap -n aiops-e2e` | STATUS: Running |
| 3. 检查事件 | `kubectl get events -n aiops-e2e` | 应无 `FailedMount` 事件 |

---

## ⚠️ 注意事项

- 如果 ConfigMap 已被其他流程创建，可跳过创建步骤
- 建议在生产环境中使用 Helm 或 Kustomize 进行资源管理，避免此类配置错误
- 若问题仍存在，检查 Pod 的 volume 定义是否正确引用 ConfigMap 名称和 namespace

---

## 📊 性能统计

├─ 总耗时: 4.5m
├─ 问题定位: 58.5s (22%) ✅
├─ 证据链采集: 79.3s (30%) ✅
├─ 根因分析: 22.7s (8%) ✅
├─ 汇总总结: 107.0s (40%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 7 次
```

📋 诊断追踪

- **核心 Runbook**: pod-volume-mount-failed
- **参考 Runbook**: pod-volume-mount-failed
- **工具调用**: 7 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
