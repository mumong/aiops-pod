======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 13fb38683f064ff4]

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
name: rc-volume-configmap-missing-key
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  3m2s (x19 over 25m)  kubelet            MountVolume
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": ["L4"],
  "layer_name": "ConfigError",
  "confidence": 0.95,
  "reasoning": "Pod rc-volume-configmap-missing-key 的状态为 Pending，且事件显示 FailedMount 与 configmap references non-existent config key: missing-key。这表明配置错误导致卷挂载失败，属于 L4 异常。",
  "abnormal_pods": ["rc-volume-configmap-missing-key"],
  "abnormal_groups": ["VolumeMountFailed"],
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "VolumeMountFailed",
  "status_category": "ConfigError",
  "key_entities": {
    "Pod": "rc-volume-configmap-missing-key",
    "ConfigMap": "config-volume"
  },
  "possible_scenarios": [
    "ConfigMap 'config-volume' 缺失键 'missing-key'，导致 Pod 无法挂载卷",
    "Pod 'rc-volume-configmap-missing-key' 的卷配置错误，引用了不存在的 ConfigMap 键"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 7.2s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': "ConfigMap 'config-volume' 缺失键 'missing-key'，导致 Pod 无法挂载卷", 'probability': 'high', 'reason': 'Pod 事件显示 configmap references non-existent config key: missing-key'}]
   entities=[{"type": "Pod", "name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "config-volume", "namespace": "aiops-e2e"}]
   reasoning=Pod rc-volume-configmap-missing-key 的状态为 Pending，且事件显示 FailedMount 与 configmap references non-existent config key: missing-key。这表明配置错误导致卷挂载失败，属于 L4 异常。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.95, "reasoning": "Pod rc-volume-configmap-missing-key 的状态为 Pending，且事件显示 FailedMount 与 configmap references non-existent config key: missing-key。这表明配置错误导致卷挂载失败，属于 L4 异常。", "abnormal_pods": [{"name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "VolumeMountFailed", "status_category": "ConfigError", "key_entities": [{"type": "Pod", "name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "config-volume", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "ConfigMap 'config-volume' 缺失键 'missing-key'，导致 Pod 无法挂载卷", "probability": "high", "reason": "Pod 事件显示 configmap references non-existent config key: missing-key"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-configmap-missing-key"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-configmap-missing-key"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-volume-configmap-missing-key                     0/1     ContainerCreating   0                25m     <none>           node1    <none>           <none>            app=rc-volume-configmap-missing-key,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/13fb38683f064ff4/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/13fb38683f064ff4/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/13fb38683f064ff4/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 95%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=163 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide configmap config-volume -n aiops-e2e
Error from server (NotFound): configmaps "config-volume"
   💭 [证据链采集] 已采集证据:
- e1: ConfigMap "config-volume" 不存在，确认了 configmap "<name>" not found 的错误，符合 runbook 的 ConfigMap/Secret volume 缺失分支的预期根因。

结论：当前异常由 ConfigMap 缺失导致，无需继续检查 PVC/PV/StorageClass 等其他资源。建议创建缺失的 ConfigMap 或修正 Pod 的 volume 引用。
   ✅ [证据链采集] 完成 (48.1s)
   📤 → 下游数据: evidence_items=3/3
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 ConfigMap 'config-volume' 是否缺失键 'missing-key'","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap config-volume -n aiops-e2e -o yaml","tool_args":{"kind":"ConfigMap","name":"config-volume","namespace":"aiops-e2e"},"purpose":"确认 config-volume 是否缺失键 'missing-key'","evidence_type":"config_validation","target_scope":"aiops-e2e/ConfigMap/config-volume","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=163 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide configmap config-volume -n aiops-e2e\nError from server (NotFound): configmaps \"config-volume\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/13fb38683f064ff4/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/13fb38683f064ff4/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/13fb38683f064ff4/tools/001-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"已采集证据:\n- e1: ConfigMap \"config-volume\" 不存在，确认了 configmap \"<name>\" not found 的错误，符合 runbook 的 ConfigMap/Secret volume 缺失分支的预期根因。\n\n结论：当前异常由 ConfigMap 缺失导致，无需继续检查 PVC/PV/StorageClass 等其他资源。建议创建缺失的 ConfigMap 或修正 Pod 的 volume 引用。","collection_summary":"计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%；其中真实环境证据 3/3 项，完整度 100%；实际执行工具 3 个，匹配计划 1 个，未规划证据 2 个","plan_total":1,"plan_collected":1,"plan_completeness":1.0,"environment_evidence_total":3,"environment_evidence_collected":3,"environment_evidence_completeness":1.0,"executed_tool_count":3,"matched_tool_count":1,"unplanned_tool_count":2,"evidence_inventory":[{"id":"e1","description":"验证 ConfigMap 'config-volume' 是否缺失键 'missing-key'","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap config-volume -n aiops-e2e -o yaml","purpose":"确认 config-volume 是否缺失键 'missing-key'","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/1 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 验证 ConfigMap 'config-volume' 是否缺失键 'missing-key' | `kubectl get configmap config-volume -n aiops-e2e -o yaml` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 20.2s)
   📤 → 下游数据: root_cause=ConfigMap 'config-volume' 缺失键 'missing-key'，导致 Pod rc-volume-configmap-missing-key 无法挂载卷 config-volume。根据 kubectl_get_by_name 证据，ConfigMap 'config-volume' 不存在，因此确认了配置错误。
   confidence=95%
   causal_chain={"root_cause": "ConfigMap 'config-volume' 缺失键 'missing-key'", "intermediate_causes": [{"cause": "Pod rc-volume-configmap-missing-key 无法挂载卷 config-volume", "effect": "Pod 状态为 Pending"}], "immediate_causes": [{"cause": "MountVolume.SetUp 失败", "effect": "Pod rc-volume-configmap-missing-key 无法启动"}]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"id": "e1", "description": "验证 ConfigMap 'config-volume' 是否缺失键 'missing-key'", "level": "critical", "value": "kubectl_get_by_name 输出摘要: raw_chars=163 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide configmap config-volume -n aiops-e2e\nError from server (NotFound): configmaps \"config-volume\" not found", "source": "thinking_negative_match"}, {"id": "layer_1", "description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "level": "important", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Running': 46}\nNAMESPACE     NAME                                                READY   STATUS              RESTARTS         AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\n# 异常行\naiops-e2e     rc-volume-configmap-missing-key                     0/1     ContainerCreating   0                25m     <none>           node1    <none>           <none>            app=rc-volume-configmap-missing-key,pod_a", "source": "layer_verified"}, {"id": "layer_2", "description": "上游已验证工具结果: kubectl_describe", "level": "important", "value": "kubectl_describe 摘要:\nname: rc-volume-configmap-missing-key\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  3m2s (x19 over 25m)  kubelet            MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n  Warning  FailedMount  5m17s (x7 over 23m)  kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-xz5tn]: timed o", "source": "layer_verified"}], "evidence_analysis": [{"id": "e1", "description": "验证 ConfigMap 'config-volume' 是否缺失键 'missing-key'", "level": "critical", "value": "kubectl_get_by_name 输出摘要: raw_chars=163 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide configmap config-volume -n aiops-e2e\nError from server (NotFound): configmaps \"config-volume\" not found", "source": "thinking_negative_match", "raw_data": "Error from server (NotFound): configmaps \"config-volume\" not found"}, {"id": "layer_1", "description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "level": "important", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Running': 46}\nNAMESPACE     NAME                                                READY   STATUS              RESTARTS         AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\n# 异常行\naiops-e2e     rc-volume-configmap-missing-key                     0/1     ContainerCreating   0                25m     <none>           node1    <none>           <none>            app=rc-volume-configmap-missing-key,pod_a", "source": "layer_verified", "raw_data": "Pod rc-volume-configmap-missing-key 的状态为 ContainerCreating"}, {"id": "layer_2", "description": "上游已验证工具结果: kubectl_describe", "level": "important", "value": "kubectl_describe 摘要:\nname: rc-volume-configmap-missing-key\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  3m2s (x19 over 25m)  kubelet            MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n  Warning  FailedMount  5m17s (x7 over 23m)  kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-xz5tn]: timed o", "source": "layer_verified", "raw_data": "MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key"}], "causal_chain": {"root_cause": "ConfigMap 'config-volume' 缺失键 'missing-key'", "intermediate_causes": [{"cause": "Pod rc-volume-configmap-missing-key 无法挂载卷 config-volume", "effect": "Pod 状态为 Pending"}], "immediate_causes": [{"cause": "MountVolume.SetUp 失败", "effect": "Pod rc-volume-configmap-missing-key 无法启动"}]}, "root_cause": "ConfigMap 'config-volume' 缺失键 'missing-key'，导致 Pod rc-volume-configmap-missing-key 无法挂载卷 config-volume。根据 kubectl_get_by_name 证据，ConfigMap 'config-volume' 不存在，因此确认了配置错误。", "root_cause_summary": "ConfigMap 'config-volume' 缺失键 'missing-key'，导致 Pod rc-volume-configmap-missing-key 无法挂载卷 config-volume。根据 kubectl_get_by_name 证据，ConfigMap 'config-volume' 不存在，因此确认了配置错误。", "confidence": 0.95, "confidence_reason": "有直接证据表明 ConfigMap 'config-volume' 缺失键 'missing-key'，因果链清晰。", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [], "limitations": "无", "llm_raw_analysis": "已采集证据:\n- e1: ConfigMap \"config-volume\" 不存在，确认了 configmap \"<name>\" not found 的错误，符合 runbook 的 ConfigMap/Secret volume 缺失分支的预期根因。\n\n结论：当前异常由 ConfigMap 缺失导致，无需继续检查 PVC/PV/StorageClass 等其他资源。建议创建缺失的 ConfigMap 或修正 Pod 的 volume 引用。\n\n工具原始输出\n1. [kubectl_get_by_name]: kubectl_get_by_name 输出摘要: raw_chars=163 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide configmap config-volume -n aiops-e2e\nError from server (NotFound): configmaps \"config-volume\" not found"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: ConfigMap 'config-volume' 缺失键 'missing-key'，导致 Pod rc-volume-configmap-missing-key 无法挂载卷 config-volume。根据 kubectl_get_by_name 证据，ConfigMap 'config-vol...
   置信度: 95%
   🔗 因果链:
     根本原因: ConfigMap 'config-volume' 缺失键 'missing-key'


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 43.6s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4089 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 59.1s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | ContainerCreating / Pending |
| **兼容归因层** | L4 - 配置错误 |
| **问题分类** | VolumeMountFailed / ConfigError |
| **置信度** | 高 (95%) |
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

**集群现状**：
- 1 个 Pod 处于 `Pending` 状态，事件显示 `FailedMount`。
- Pod 名为 `rc-volume-configmap-missing-key`，正在尝试挂载名为 `config-volume` 的 ConfigMap 卷。
- 由于 ConfigMap 中缺少指定的 `missing-key`，挂载失败，导致 Pod 无法启动。

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | kubectl get pod -n aiops-e2e | `STATUS: ContainerCreating, REASON: FailedMount` | Pod 无法完成挂载，处于创建中 |
| 2 | Pod 事件 | kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e | `MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key` | 明确指出 ConfigMap 中缺少 `missing-key` |
| 3 | ConfigMap 检查 | kubectl get configmap config-volume -n aiops-e2e | `Error from server (NotFound): configmaps "config-volume"` | 证实质疑的 ConfigMap 不存在或配置错误 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 `ContainerCreating`，事件明确指出 `MountVolume.SetUp failed`，说明挂载失败。
- **证据 #2 + #3 印证**：ConfigMap 中缺少 `missing-key`，导致挂载失败，直接导致 Pod 无法启动。
- **证据链**：ConfigMap 缺失指定键 → 挂载失败 → Pod 无法创建 → 用户观察到 Pod 持续处于 `Pending` 状态。

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ ConfigMap 'config-volume' 缺失键 'missing-key'                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Pod 挂载 ConfigMap 卷时，发现缺失键，无法继续挂载                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ MountVolume.SetUp failed for volume "config-volume"             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 Pending，且事件显示 FailedMount                      │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2 (`MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key`) 和证据 #3 (`kubectl get configmap config-volume -n aiops-e2e` 返回 `NotFound`)，问题的根本原因是**ConfigMap `config-volume` 缺失键 `missing-key`**，导致卷挂载失败，Pod 无法启动。

**置信度**：高 (95%)
- ✅ Pod 事件明确指出 ConfigMap 缺失键
- ✅ kubectl get 验证 ConfigMap 不存在或配置错误
- ✅ 与 Runbook `pod-volume-mount-failed.md` 中的典型问题匹配

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 修复 ConfigMap，补充缺失的键**

```bash
kubectl create configmap config-volume \
  --from-literal=missing-key="some-value" \
  -n aiops-e2e
```

*依据*：事件明确指出 ConfigMap 缺失 `missing-key`，补充后可解决挂载失败。

**2. [可选] 删除并重新创建 Pod**

```bash
kubectl delete pod rc-volume-configmap-missing-key -n aiops-e2e
```

*目的*：删除后 Kubernetes 会自动根据 Deployment/ReplicationController 重新创建 Pod，挂载新的 ConfigMap。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 ConfigMap 存在 | `kubectl get configmap config-volume -n aiops-e2e` | 应显示 `missing-key` 存在 |
| 2. 确认 Pod 运行 | `kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e` | STATUS: Running |
| 3. 检查 Pod 事件 | `kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e` | 不再出现 `FailedMount` 事件 |

---

## ⚠️ 注意事项

- 如果 ConfigMap 是通过 Deployment/ReplicationController 自动创建的，请检查对应的模板配置是否正确。
- 确保 ConfigMap 的命名空间与 Pod 所在的命名空间一致。
- 如果问题持续，请检查 Pod 的 `volumeMounts` 和 `volumes` 配置是否正确引用 ConfigMap 和键名。

---

## 📊 性能统计

├─ 总耗时: 5.0m
├─ 问题定位: 67.2s (22%) ✅
├─ 证据链采集: 48.1s (16%) ✅
├─ 根因分析: 80.2s (27%) ✅
├─ 汇总总结: 103.6s (35%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 4 次
```

📋 诊断追踪

- **核心 Runbook**: pod-volume-mount-failed
- **参考 Runbook**: pod-volume-mount-failed
- **工具调用**: 4 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
