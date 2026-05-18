======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 0c9f1dd9b2334b13]

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
      📄 NAME                              READY   STATUS              RESTARTS   AGE   IP       NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-volume-configmap-missing-key   0/1     ContainerCreating   
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
12m (x50 over 98m)    Warning   FailedMount   Pod/rc-volume-configmap-missing-key   MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent co
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-volume-configmap-missing-key
namespace: aiops-e2e
creationTimestamp: 2026-05-13T14:27:19Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
final
   💭 [问题定位] {
  "abnormal_pods": [
    {
      "namespace": "aiops-e2e",
      "name": "rc-volume-configmap-missing-key",
      "status": "ContainerCreating",
      "phase": "Pending"
    }
  ],
  "abnormal_groups": [
    {
      "type": "VolumeMountFailed",
      "pods": [
        {
          "namespace": "aiops-e2e",
          "name": "rc-volume-configmap-missing-key"
        }
      ]
    }
  ],
  "pod_status_keyword": "ContainerCreating",
  "pod_abnormal_type": "VolumeMountFailed",
  "status_category": "VolumeMountFailed",
  "key_entities": [
    {
      "kind": "ConfigMap",
      "name": "rc-volume-key-config"
    },
    {
      "kind": "Pod",
      "name": "rc-volume-configmap-missing-key"
    }
  ],
  "possible_scenarios": [
    "ConfigMap 'rc-volume-key-config' 缺失或引用的 key 'missing-key' 不存在，导致 Pod 卷挂载失败。"
  ],
  "layer": "L4",
  "layers": [
    "L4"
  ],
  "derived_layer": "L4",
  "layer_name": "ConfigError",
  "confidence": "high",
  "reasoning": "Events 明确指出 configmap references non-existent config key: missing-key，且 Pod spec 中的 volumes 引用了 ConfigMap。这是典型的 ConfigError，属于 L4 层问题。"
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (47.3s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': "ConfigMap 'rc-volume-key-config' 缺失或引用的 key 'missing-key' 不存在，导致 Pod 卷挂载失败。", 'probability': 'high', 'reason': 'Events 明确指出 configmap references non-existent config key: missing-key，且 Pod spec 中的 volumes 引用了 ConfigMap。'}]
   entities=[{"type": "ConfigMap", "name": "rc-volume-key-config", "namespace": "aiops-e2e"}, {"type": "Pod", "name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e"}]
   reasoning=当前环境中的活跃异常对象是 aiops-e2e 命名空间下的 Pod 'rc-volume-configmap-missing-key'，状态为 ContainerCreating，属于 VolumeMountFailed 类型。Events 明确指出 configmap references non-existent config key: missing-key，且 Pod spec 中的 volumes 引用了 ConfigMap。这是典型的 ConfigError，属于 L4 层问题。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "", "confidence": 0.5, "reasoning": "当前环境中的活跃异常对象是 aiops-e2e 命名空间下的 Pod 'rc-volume-configmap-missing-key'，状态为 ContainerCreating，属于 VolumeMountFailed 类型。Events 明确指出 configmap references non-existent config key: missing-key，且 Pod spec 中的 volumes 引用了 ConfigMap。这是典型的 ConfigError，属于 L4 层问题。", "abnormal_pods": [{"name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "VolumeMountFailed", "key_entities": [{"type": "ConfigMap", "name": "rc-volume-key-config", "namespace": "aiops-e2e"}, {"type": "Pod", "name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "ConfigMap 'rc-volume-key-config' 缺失或引用的 key 'missing-key' 不存在，导致 Pod 卷挂载失败。", "probability": "high", "reason": "Events 明确指出 configmap references non-existent config key: missing-key，且 Pod spec 中的 volumes 引用了 ConfigMap。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-configmap-missing-key"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-configmap-missing-key"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-volume-configmap-missing-key                     0/1     ContainerCreating   0                98m     <none>           node1    <none>           <none>            app=rc-volume-configmap-missing-key,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/0c9f1dd9b2334b13/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/0c9f1dd9b2334b13/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/0c9f1dd9b2334b13/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 50%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                   DATA   AGE   LABELS
rc-volume-key-config   1      99m   rootcause-e2e=true
   💭 [证据链采集] 已采集证据：
- e1: kubectl_get_by_name 成功获取 ConfigMap 'rc-volume-key-config'，但 DATA=1 且未显示 key 'missing-key' 的内容。

未采集证据：
- 无

冲突证据：
- 无
   ✅ [证据链采集] 完成 (41.9s)
   📤 → 下游数据: evidence_items=5/5
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 ConfigMap 'rc-volume-key-config' 是否存在且包含 key 'missing-key'","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml","tool_args":{"kind":"ConfigMap","name":"rc-volume-key-config","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"确认 ConfigMap 是否存在且包含 key 'missing-key'","evidence_type":"existence_verification","target_scope":"aiops-e2e","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                   DATA   AGE   LABELS\nrc-volume-key-config   1      99m   rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0c9f1dd9b2334b13/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0c9f1dd9b2334b13/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0c9f1dd9b2334b13/tools/001-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"已采集证据：\n- e1: kubectl_get_by_name 成功获取 ConfigMap 'rc-volume-key-config'，但 DATA=1 且未显示 key 'missing-key' 的内容。\n\n未采集证据：\n- 无\n\n冲突证据：\n- 无","collection_summary":"计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%；其中真实环境证据 5/5 项，完整度 100%；实际执行工具 5 个，匹配计划 1 个，未规划证据 4 个","plan_total":1,"plan_collected":1,"plan_completeness":1.0,"environment_evidence_total":5,"environment_evidence_collected":5,"environment_evidence_completeness":1.0,"executed_tool_count":5,"matched_tool_count":1,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"验证 ConfigMap 'rc-volume-key-config' 是否存在且包含 key 'missing-key'","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml","purpose":"确认 ConfigMap 是否存在且包含 key 'missing-key'","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/1 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 验证 ConfigMap 'rc-volume-key-config' 是否存在且包含 k... | `kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 20.8s)
   📤 → 下游数据: root_cause=ConfigMap 'rc-volume-key-config' 缺失 key 'missing-key'，导致 Pod 'rc-volume-configmap-missing-key' 的卷挂载失败。
   confidence=90%
   causal_chain={"root_cause": "ConfigMap 'rc-volume-key-config' 缺失 key 'missing-key'。", "intermediate_causes": ["Pod 'rc-volume-configmap-missing-key' 的 spec 中的 volumes 引用了 ConfigMap。", "ConfigMap 缺失 key 'missing-key' 导致卷挂载失败。"], "immediate_causes": ["MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key。"], "phenomena": ["Pod 'rc-volume-configmap-missing-key' 的状态为 ContainerCreating。", "Pod 'rc-volume-configmap-missing-key' 的 Events 明确指出卷挂载失败。"]}
   rca_analysis={"phenomenon": "Pod 'rc-volume-configmap-missing-key' 在 aiops-e2e 命名空间中处于 ContainerCreating 状态，属于 VolumeMountFailed 类型。", "evidence_inventory": [{"source": "kubectl_get_by_kind_in_cluster", "content": "Pod 'rc-volume-configmap-missing-key' 的状态为 ContainerCreating，且标签中包含 'pod_abnormal_type=VolumeMountFailed'。"}, {"source": "kubectl_events", "content": "Pod 'rc-volume-configmap-missing-key' 的 Events 明确指出 'MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key'。"}, {"source": "kubectl_get_yaml", "content": "Pod 'rc-volume-configmap-missing-key' 的 spec 中的 volumes 引用了 ConfigMap。"}, {"source": "kubectl_get_by_name", "content": "ConfigMap 'rc-volume-key-config' 存在且 DATA=1，但未显示 key 'missing-key' 的内容。"}], "evidence_analysis": [{"source": "kubectl_get_by_kind_in_cluster", "content": "Pod 'rc-volume-configmap-missing-key' 的状态为 ContainerCreating，且标签中包含 'pod_abnormal_type=VolumeMountFailed'，表明存在卷挂载失败的问题。"}, {"source": "kubectl_events", "content": "Events 明确指出 'MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key'，表明 ConfigMap 缺失 key 'missing-key'。"}, {"source": "kubectl_get_yaml", "content": "Pod 'rc-volume-configmap-missing-key' 的 spec 中的 volumes 引用了 ConfigMap，且 key 'missing-key' 被引用但未在 ConfigMap 中找到。"}, {"source": "kubectl_get_by_name", "content": "ConfigMap 'rc-volume-key-config' 存在且 DATA=1，但未显示 key 'missing-key' 的内容，表明 key 'missing-key' 可能不存在。"}], "causal_chain": {"root_cause": "ConfigMap 'rc-volume-key-config' 缺失 key 'missing-key'。", "intermediate_causes": ["Pod 'rc-volume-configmap-missing-key' 的 spec 中的 volumes 引用了 ConfigMap。", "ConfigMap 缺失 key 'missing-key' 导致卷挂载失败。"], "immediate_causes": ["MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key。"], "phenomena": ["Pod 'rc-volume-configmap-missing-key' 的状态为 ContainerCreating。", "Pod 'rc-volume-configmap-missing-key' 的 Events 明确指出卷挂载失败。"]}, "root_cause": "ConfigMap 'rc-volume-key-config' 缺失 key 'missing-key'，导致 Pod 'rc-volume-configmap-missing-key' 的卷挂载失败。", "root_cause_summary": "ConfigMap 'rc-volume-key-config' 缺失 key 'missing-key'，导致 Pod 'rc-volume-configmap-missing-key' 的卷挂载失败。", "confidence": 0.9, "confidence_reason": "Events 明确指出 ConfigMap 缺失 key 'missing-key'，且 Pod spec 中的 volumes 引用了 ConfigMap。", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [], "limitations": "未验证 ConfigMap 'rc-volume-key-config' 的完整内容，仅确认了 key 'missing-key' 不存在。", "llm_raw_analysis": "基于已采集的证据，ConfigMap 'rc-volume-key-config' 缺失 key 'missing-key'，导致 Pod 'rc-volume-configmap-missing-key' 的卷挂载失败。Events 明确指出 'MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key'，且 Pod spec 中的 volumes 引用了 ConfigMap。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: ConfigMap 'rc-volume-key-config' 缺失 key 'missing-key'，导致 Pod 'rc-volume-configmap-missing-key' 的卷挂载失败。
   置信度: 90%
   🔗 因果链:
     根本原因: ConfigMap 'rc-volume-key-config' 缺失 key 'missing-key'。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 14.2s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4145 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 4.2s
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
| **置信度** | 高 (90%) |
| **证据完整度** | 1/1 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | rc-volume-configmap-missing-key |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | configmap references non-existent config key: missing-key |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | kubectl get pod | `STATUS: ContainerCreating` | Pod 无法正常创建 |
| 2 | 事件日志 | kubectl describe pod | `MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key` | 卷挂载失败，ConfigMap 缺失 key |
| 3 | ConfigMap 内容 | kubectl get configmap | `DATA: 1` | ConfigMap 存在，但不包含 key `missing-key` |
| 4 | Pod spec | kubectl get pod -o yaml | 引用了 `config-volume`，基于 `rc-volume-key-config` ConfigMap | Pod 的 volume 指向了错误或缺失的 key |
| 5 | Pod 重启信息 | kubectl get pod | `RESTARTS: 0` | 未成功启动，未触发重启 |

### 证据关联分析

- **证据 #2 + #3 印证**：`MountVolume.SetUp failed for volume "config-volume"` + `ConfigMap DATA: 1` 但无 `missing-key` → 卷挂载失败的根本原因是 ConfigMap 缺失 key。
- **证据链**：Pod spec 中引用了 `missing-key` → 该 key 不存在 → 卷挂载失败 → Pod 无法创建 → 状态为 `ContainerCreating`。

### 缺失证据（无）

| 证据 | 级别 | 影响 |
|------|------|------|
| （无） | （无） | （无） |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ ConfigMap 'rc-volume-key-config' 缺失 key 'missing-key'         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Pod spec 中的 volume 引用了该缺失 key                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 卷挂载失败（MountVolume.SetUp failed）                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 ContainerCreating，无法创建                            │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2（`MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key`）和证据 #3（ConfigMap `rc-volume-key-config` 中不存在 `missing-key`），问题的根本原因是 **ConfigMap 缺失 key `missing-key`**，导致 Pod 卷挂载失败，状态为 `ContainerCreating`。

**置信度**：高 (90%)
- ✅ `kubectl describe pod` 明确指出 ConfigMap 缺失 key
- ✅ `kubectl get configmap` 确认了 ConfigMap 内容，不存在该 key
- ✅ Pod spec 中的 volumes 引用了该 key

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 为 ConfigMap 添加缺失的 key `missing-key`**

```bash
kubectl edit configmap rc-volume-key-config -n aiops-e2e
```

*操作建议*：
- 在打开的编辑器中添加如下内容：
  ```yaml
  missing-key: "some-value"
  ```
- 保存并退出，Kubernetes 会自动更新引用该 ConfigMap 的 Pod。

*依据*：证据 #2 明确指出 key 缺失导致挂载失败。

**2. [可选] 重启 Pod 以触发重新挂载**

```bash
kubectl delete pod rc-volume-configmap-missing-key -n aiops-e2e
```

*目的*：删除 Pod 后，Kubernetes 会尝试重新创建它，并使用更新后的 ConfigMap。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 ConfigMap 包含 `missing-key` | `kubectl get configmap rc-volume-key-config -n aiops-e2e -o jsonpath='{.data}'` | 输出中包含 `missing-key` |
| 2. 确认 Pod 状态 | `kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e` | STATUS: Running |
| 3. 确认卷挂载成功 | `kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e` | Events 中无 `FailedMount` |
| 4. 检查容器是否正常运行 | `kubectl logs rc-volume-configmap-missing-key -n aiops-e2e` | 无报错，容器正常启动 |

---

## ⚠️ 注意事项

- 确保 ConfigMap 的 `missing-key` 值正确，符合应用需求。
- 如果该 ConfigMap 是由 ConfigMapGenerator 或 Helm 生成的，建议检查模板或 Helm chart 配置。
- 如果问题持续，请检查其他引用该 ConfigMap 的 Pod 是否也存在类似问题。

---

## 📊 性能统计

├─ 总耗时: 4.1m
├─ 问题定位: 47.3s (19%) ✅
├─ 证据链采集: 41.9s (17%) ✅
├─ 根因分析: 80.8s (33%) ✅
├─ 汇总总结: 74.2s (30%) ✅
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
