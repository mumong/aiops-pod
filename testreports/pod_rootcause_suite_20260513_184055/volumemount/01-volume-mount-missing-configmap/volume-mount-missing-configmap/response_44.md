======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 77d3a577fb4c4d42]

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
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-missing-configmap
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  12m (x50 over 97m)    kubelet  MountVolume.SetUp failed
   💭 [问题定位] {
  "layer": "L0",
  "derived_layer": "L0",
  "layers": ["L0"],
  "layer_name": "VolumeMountFailed",
  "confidence": "high",
  "reasoning": "Pod rc-volume-missing-configmap 处于 ContainerCreating 状态，且 Events 中出现 MountVolume.SetUp failed 和 configmap not found 的警告，符合 VolumeMountFailed 异常类型。异常归因于配置缺失，属于 L0 层级，因为涉及卷挂载失败的基础问题。",
  "abnormal_pods": [
    {
      "name": "rc-volume-missing-configmap",
      "namespace": "aiops-e2e",
      "status": "Pending",
      "key_events": [
        "MountVolume.SetUp failed for volume 'missing-config': configmap 'rc-definitely-missing-configmap' not found",
        "Unable to attach or mount volumes: unmounted volumes=[missing-config], unattached volumes=[kube-api-access-n5pfx missing-config]: timed out waiting for the condition"
      ],
      "status_keyword": "ContainerCreating",
      "abnormal_type": "VolumeMountFailed"
    }
  ],
  "abnormal_groups": [
    {
      "type": "VolumeMountFailed",
      "count": 1,
      "pods": ["rc-volume-missing-configmap"]
    }
  ],
  "key_entities": [
    {
      "kind": "ConfigMap",
      "name": "rc-definitely-missing-configmap",
      "namespace": "aiops-e2e"
    }
  ],
  "possible_scenarios": [
    "配置缺失：Pod 引用了不存在的 ConfigMap 'rc-definitely-missing-configmap'，导致挂载失败。",
    "卷配置错误：Pod 的 volumes 配置中引用了无效的 ConfigMap，导致 MountVolume 失败。",
    "资源未创建：ConfigMap 'rc-definitely-missing-configmap' 未被创建或未正确配置。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (52.7s)
   📤 → 下游数据: layer=Layer.L0, layers=L0
   scenarios=[{'scenario': "配置缺失：Pod 引用了不存在的 ConfigMap 'rc-definitely-missing-configmap'，导致挂载失败。", 'probability': 'high', 'reason': 'Events 明确提到 configmap not found，且 Pod spec 中引用了该 ConfigMap。'}, {'scenario': '卷配置错误：Pod 的 volumes 配置中引用了无效的 ConfigMap，导致 MountVolume 失败。', 'probability': 'medium', 'reason': 'Pod spec 中的 volume 配置可能错误地引用了不存在的 ConfigMap。'}, {'scenario': "资源未创建：ConfigMap 'rc-definitely-missing-configmap' 未被创建或未正确配置。", 'probability': 'high', 'reason': 'Events 明确指出该 ConfigMap 不存在，表明资源未被创建。'}]
   entities=[{"type": "ConfigMap", "name": "rc-definitely-missing-configmap", "namespace": "aiops-e2e"}]
   reasoning=Pod rc-volume-missing-configmap 处于 ContainerCreating 状态，且 Events 中出现 MountVolume.SetUp failed 和 configmap not found 的警告，符合 VolumeMountFailed 异常类型。异常归因于配置缺失，属于 L0 层级，因为涉及卷挂载失败的基础问题。
   layer_analysis={"layer": "L0", "derived_layer": "L0", "layers": ["L0"], "layer_name": "VolumeMountFailed", "confidence": 1.0, "reasoning": "Pod rc-volume-missing-configmap 处于 ContainerCreating 状态，且 Events 中出现 MountVolume.SetUp failed 和 configmap not found 的警告，符合 VolumeMountFailed 异常类型。异常归因于配置缺失，属于 L0 层级，因为涉及卷挂载失败的基础问题。", "abnormal_pods": [{"name": "rc-volume-missing-configmap", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "storage_volume", "key_entities": [{"type": "ConfigMap", "name": "rc-definitely-missing-configmap", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "配置缺失：Pod 引用了不存在的 ConfigMap 'rc-definitely-missing-configmap'，导致挂载失败。", "probability": "high", "reason": "Events 明确提到 configmap not found，且 Pod spec 中引用了该 ConfigMap。"}, {"scenario": "卷配置错误：Pod 的 volumes 配置中引用了无效的 ConfigMap，导致 MountVolume 失败。", "probability": "medium", "reason": "Pod spec 中的 volume 配置可能错误地引用了不存在的 ConfigMap。"}, {"scenario": "资源未创建：ConfigMap 'rc-definitely-missing-configmap' 未被创建或未正确配置。", "probability": "high", "reason": "Events 明确指出该 ConfigMap 不存在，表明资源未被创建。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-configmap"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-configmap"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-volume-missing-configmap                         0/1     ContainerCreating   0                97m     <none>           node1    <none>           <none>            app=rc-volume-missing-configmap,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/77d3a577fb4c4d42/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/77d3a577fb4c4d42/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/77d3a577fb4c4d42/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L0
   置信度: 100%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                          READY   STATUS              RESTARTS   AGE   IP       NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-volume-missing-configmap   0/1     ContainerCreating   0       
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-missing-configmap
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  13m (x50 over 99m)    kubelet  MountVolume.SetUp failed
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=199 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide configmap rc-definitely-missing-configmap -n aiops-e2e
Error from server (NotFound): configma
   💭 [证据链采集] 已采集证据：
1. Pod `rc-volume-missing-configmap` 处于 `ContainerCreating` 状态，Events 显示 `MountVolume.SetUp failed for volume "missing-config"`，且明确提示 `configmap "rc-definitely-missing-configmap" not found`。
2. `kubectl describe pod` 显示多次 `FailedMount` 事件，表明卷挂载失败。
3. `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` 返回 `NotFound`，确认 ConfigMap 不存在。

未采集证据：无（当前证据已覆盖主异常组的关键验证）。

冲突证据：无。
   ✅ [证据链采集] 完成 (1m 16.5s)
   📤 → 下游数据: evidence_items=3/3
   evidence_analysis={"evidence_plan":[{"id":"ep1","description":"验证 Pod rc-volume-missing-configmap 的 volume 配置是否引用了不存在的 ConfigMap","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-volume-missing-configmap -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-volume-missing-configmap","namespace":"aiops-e2e"},"purpose":"确认 Pod spec 中的 volume 配置是否引用了不存在的 ConfigMap","evidence_type":"configuration","target_scope":"Pod","acceptable_tools":["kubectl_get_by_name","kubectl_get_by_kind_in_namespace","kubectl_get_yaml"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                          READY   STATUS              RESTARTS   AGE   IP       NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-volume-missing-configmap   0/1     ContainerCreating   0          99m   <none>   node1   <none>           <none>            app=rc-volume-missing-configmap,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/77d3a577fb4c4d42/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/77d3a577fb4c4d42/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/77d3a577fb4c4d42/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-missing-configmap\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  13m (x50 over 99m)    kubelet  MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found\n  Warning  FailedMount  29m (x10 over 90m)    kubelet  Unable to attach or mount volumes: unmounted volumes=[missing-config], unattached volumes=[kube-api-access-n5pfx missing-config]: timed out waiting for the condition\n  Warning  FailedMount  4m22s (x28 over 97m)  kubelet  Unable to attach or mount volumes: unmounted volumes=[missing-config], unattached volumes=[missing-config kube-api-access-n5pfx]: timed out waiting for the condition\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed\n    State:          Waiting\n      Reason:       ContainerCreating","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/77d3a577fb4c4d42/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/77d3a577fb4c4d42/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/77d3a577fb4c4d42/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=199 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide configmap rc-definitely-missing-configmap -n aiops-e2e\nError from server (NotFound): configmaps \"rc-definitely-missing-configmap\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/77d3a577fb4c4d42/tools/003-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/77d3a577fb4c4d42/tools/003-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/77d3a577fb4c4d42/tools/003-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"已采集证据：\n1. Pod `rc-volume-missing-configmap` 处于 `ContainerCreating` 状态，Events 显示 `MountVolume.SetUp failed for volume \"missing-config\"`，且明确提示 `configmap \"rc-definitely-missing-configmap\" not found`。\n2. `kubectl describe pod` 显示多次 `FailedMount` 事件，表明卷挂载失败。\n3. `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` 返回 `NotFound`，确认 ConfigMap 不存在。\n\n未采集证据：无（当前证据已覆盖主异常组的关键验证）。\n\n冲突证据：无。","collection_summary":"计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%；其中真实环境证据 3/3 项，完整度 100%；实际执行工具 5 个，匹配计划 1 个，未规划证据 4 个","plan_total":1,"plan_collected":1,"plan_completeness":1.0,"environment_evidence_total":3,"environment_evidence_collected":3,"environment_evidence_completeness":1.0,"executed_tool_count":5,"matched_tool_count":1,"unplanned_tool_count":4,"evidence_inventory":[{"id":"ep1","description":"验证 Pod rc-volume-missing-configmap 的 volume 配置是否引用了不存在的 ConfigMap","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-volume-missing-configmap -n aiops-e2e -o yaml","purpose":"确认 Pod spec 中的 volume 配置是否引用了不存在的 ConfigMap","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/1 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | ep1 | critical | ✅ | kubectl_get_by_name | 验证 Pod rc-volume-missing-configmap 的 volume 配... | `kubectl get pod rc-volume-missing-configmap -n aiops-e2e -o yaml` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (28.9s)
   📤 → 下游数据: root_cause=Pod 'rc-volume-missing-configmap' 无法创建容器，因为其引用的 ConfigMap 'rc-definitely-missing-configmap' 不存在。证据包括：kubectl describe pod 显示 'MountVolume.SetUp failed for volume "missing-config" : configmap "rc-definitely-missing-configmap" not found'，以及 kubectl get configmap 明确返回 'NotFound'。
   confidence=100%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [], "causal_chain": {}, "root_cause": "Pod 'rc-volume-missing-configmap' 无法创建容器，因为其引用的 ConfigMap 'rc-definitely-missing-configmap' 不存在。证据包括：kubectl describe pod 显示 'MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found'，以及 kubectl get configmap 明确返回 'NotFound'。", "root_cause_summary": "Pod 'rc-volume-missing-configmap' 无法创建容器，因为其引用的 ConfigMap 'rc-definitely-missing-configmap' 不存在。证据包括：kubectl describe pod 显示 'MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found'，以及 kubectl get configmap 明确返回 'NotFound'。", "confidence": 1.0, "confidence_reason": "有直接证据表明 ConfigMap 不存在，且多次 FailedMount 事件明确指向该 ConfigMap 缺失。因果链清晰，置信度为 1.0。", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [], "limitations": "", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'rc-volume-missing-configmap' 无法创建容器，因为其引用的 ConfigMap 'rc-definitely-missing-configmap' 不存在。证据包括：kubectl describe pod 显示 'MountVolume.SetUp failed...
   置信度: 100%

📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 23.6s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4060 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 1.7s
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
| **兼容归因层** | L0 - 基础问题层 |
| **问题分类** | VolumeMountFailed（卷挂载失败） |
| **置信度** | 高（100%） |
| **证据完整度** | 1/1 (100%) |

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
| 1 | Pod 状态 | `kubectl describe pod rc-volume-missing-configmap -n aiops-e2e` | `Warning  FailedMount  12m (x50 over 97m) kubelet MountVolume.SetUp failed for volume "missing-config" : configmap "rc-definitely-missing-configmap" not found` | Pod 引用了不存在的 ConfigMap，导致挂载失败 |
| 2 | ConfigMap 存在性 | `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` | `Error from server (NotFound): configmap not found` | 确认 ConfigMap 不存在 |
| 3 | Pod 列表状态 | `kubectl get pod -n aiops-e2e` | `rc-volume-missing-configmap 0/1 ContainerCreating` | Pod 处于 ContainerCreating 状态 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 试图挂载一个不存在的 ConfigMap，导致挂载失败，容器无法创建。
- **证据链**：Pod spec 中引用了不存在的 ConfigMap → kubelet 无法完成 MountVolume → Pod 状态为 ContainerCreating，持续失败。

### 缺失证据（无）

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ ConfigMap 'rc-definitely-missing-configmap' 未被创建            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ kubelet 无法挂载缺失的 ConfigMap → MountVolume 失败             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Pod 无法创建容器，状态为 ContainerCreating                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 无法启动，处于 ContainerCreating 状态                       │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 和 #2，问题的根本原因是 **ConfigMap `rc-definitely-missing-configmap` 未被创建**，导致 Pod `rc-volume-missing-configmap` 无法挂载该 ConfigMap，容器无法启动，状态为 `ContainerCreating`。

**置信度**：高（100%）
- ✅ `kubectl describe pod` 明确指出 ConfigMap 不存在
- ✅ `kubectl get configmap` 返回 `NotFound`，确认 ConfigMap 未创建

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 创建缺失的 ConfigMap**

```bash
kubectl create configmap rc-definitely-missing-configmap -n aiops-e2e --from-literal=key1=value1 --from-literal=key2=value2
```

*依据*：Events 明确指出 ConfigMap 不存在，需创建该资源

**2. [可选] 验证 ConfigMap 是否创建成功**

```bash
kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e
```

*目的*：确认 ConfigMap 是否成功创建

**3. [可选] 删除并重新启动 Pod（如果自动重启无效）**

```bash
kubectl delete pod rc-volume-missing-configmap -n aiops-e2e
```

*目的*：触发调度器重新拉起 Pod，挂载新的 ConfigMap

### 后续优化

1. **Pod spec 验证**：确保 volumes 和 volumeMounts 配置正确，避免引用不存在的资源
2. **自动化检查**：使用 Helm 或 Kustomize 部署时，确保 ConfigMap 与 Pod 一起部署
3. **监控告警**：配置 Pod 状态监控，如 `Pending`、`ContainerCreating` 状态的告警

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 ConfigMap 是否存在 | `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` | NAME: rc-definitely-missing-configmap |
| 2. 确认 Pod 是否启动 | `kubectl get pod rc-volume-missing-configmap -n aiops-e2e` | STATUS: Running |
| 3. 检查 Pod 是否正常运行 | `kubectl describe pod rc-volume-missing-configmap -n aiops-e2e` | No FailedMount events |

---

## ⚠️ 注意事项

- 如果 ConfigMap 已存在，但 Pod 仍然无法挂载，请检查命名空间是否正确。
- 如果问题涉及多个 Pod，建议统一使用 Helm 模板管理 ConfigMap 与 Pod 的依赖关系。
- 确保 ConfigMap 的 `data` 字段与 Pod 中的 `volumeMounts` 配置一致，避免路径错误。

---

## 📊 性能统计

├─ 总耗时: 4.0m
├─ 问题定位: 52.7s (22%) ✅
├─ 证据链采集: 76.5s (32%) ✅
├─ 根因分析: 28.9s (12%) ✅
├─ 汇总总结: 83.6s (35%) ✅
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
