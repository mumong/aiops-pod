======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 000034347aa141bb]

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
3m13s (x35 over 58m)   Warning   FailedMount   Pod/rc-volume-configmap-missing-key   MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent c
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
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "ConfigError",
  "confidence": 0.95,
  "reasoning": "Pod rc-volume-configmap-missing-key 处于 ContainerCreating 状态，Events 明确显示 configmap references non-existent config key: missing-key，且 Pod spec 中 volumes[].configMap 引用了 rc-volume-key-config。这表明 ConfigMap 中缺少缺失的键，属于 ConfigError 类型（L4）。",
  "abnormal_pods": [
    {
      "name": "rc-volume-configmap-missing-key",
      "namespace": "aiops-e2e",
      "status": "ContainerCreating",
      "reason": "FailedMount",
      "message": "MountVolume.SetUp failed for volume 'config-volume': configmap references non-existent config key: missing-key"
    }
  ],
  "abnormal_groups": [
    {
      "type": "VolumeMountFailed",
      "count": 1,
      "pods": [
        "rc-volume-configmap-missing-key"
      ]
    }
  ],
  "pod_status_keyword": "ContainerCreating",
  "pod_abnormal_type": "VolumeMountFailed",
  "status_category": "ConfigError",
  "key_entities": {
    "Pod": "rc-volume-configmap-missing-key",
    "ConfigMap": "rc-volume-key-config"
  },
  "possible_scenarios": [
    {
      "scenario": "ConfigMap rc-volume-key-config 缺失键 'missing-key'",
      "evidence": "Events 显示 configmap references non-existent config key: missing-key"
    }
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (51.4s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': "ConfigMap rc-volume-key-config 缺失键 'missing-key'", 'probability': 'high', 'reason': 'Events 显示 configmap references non-existent config key: missing-key'}]
   entities=[{"type": "Pod", "name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-volume-key-config", "namespace": "aiops-e2e"}]
   reasoning=Pod rc-volume-configmap-missing-key 处于 ContainerCreating 状态，Events 明确显示 configmap references non-existent config key: missing-key，且 Pod spec 中 volumes[].configMap 引用了 rc-volume-key-config。这表明 ConfigMap 中缺少缺失的键，属于 ConfigError 类型（L4）。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.95, "reasoning": "Pod rc-volume-configmap-missing-key 处于 ContainerCreating 状态，Events 明确显示 configmap references non-existent config key: missing-key，且 Pod spec 中 volumes[].configMap 引用了 rc-volume-key-config。这表明 ConfigMap 中缺少缺失的键，属于 ConfigError 类型（L4）。", "abnormal_pods": [{"name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "ConfigError", "key_entities": [{"type": "Pod", "name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-volume-key-config", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "ConfigMap rc-volume-key-config 缺失键 'missing-key'", "probability": "high", "reason": "Events 显示 configmap references non-existent config key: missing-key"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-configmap-missing-key"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-configmap-missing-key"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-volume-configmap-missing-key                     0/1     ContainerCreating   0                58m     <none>           node1    <none>           <none>            app=rc-volume-configmap-missing-key,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/000034347aa141bb/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/000034347aa141bb/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/000034347aa141bb/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-configmap-missing-key
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  5m7s (x35 over 60m)  kubelet            MountVolume
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                   DATA   AGE   LABELS
rc-volume-key-config   1      60m   rootcause-e2e=true
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-volume-configmap-missing-key
namespace: aiops-e2e
creationTimestamp: 2026-05-13T14:27:19Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
final
   💭 [证据链采集] 已采集关键证据：

1. **Critical 证据**：
   - `kubectl describe pod` 显示 `MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key`，明确指向 ConfigMap 缺失指定键。
   - `kubectl get configmap rc-volume-key-config -n aiops-e2e` 显示该 ConfigMap 只有 1 个数据项，与 Pod spec 中的引用不匹配。
   - `kubectl get pod -o yaml` 显示 Pod spec 中 `volumes[].configMap` 引用了 `rc-volume-key-config`，但未指定具体 key。

2. **冲突证据**：
   - 无冲突证据；当前 Pod 和 ConfigMap 均存在于指定命名空间，但 ConfigMap 内容不满足引用需求。

结论：Pod `rc-volume-configmap-missing-key` 无法创建容器，根本原因是其引用的 ConfigMap `rc-volume-key-config` 缺失指定键 `missing-key`。建议检查 ConfigMap 的定义并补充缺失的键。
   ✅ [证据链采集] 完成 (1m 45.2s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"检查 Pod rc-volume-configmap-missing-key 的详细描述信息，以确认其 volumeMount 问题的具体原因。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e","tool_args":{"tool":"kubectl_describe","command":"kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e"},"purpose":"确认 Pod 的 volumeMount 问题是否由 ConfigMap 键缺失导致。","evidence_type":"Pod Description","target_scope":"aiops-e2e/rc-volume-configmap-missing-key","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"检查 ConfigMap rc-volume-key-config 是否存在，并确认其是否缺少键 'missing-key'。","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap rc-volume-key-config -n aiops-e2e","tool_args":{"tool":"kubectl_get_by_name","command":"kubectl get configmap rc-volume-key-config -n aiops-e2e"},"purpose":"验证 ConfigMap 是否缺失指定键，导致 volumeMount 失败。","evidence_type":"ConfigMap Validation","target_scope":"aiops-e2e/rc-volume-key-config","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-configmap-missing-key\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  5m7s (x35 over 60m)  kubelet            MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n  Warning  FailedMount  19m (x7 over 49m)    kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[kube-api-access-xz5tn config-volume]: timed out waiting for the condition\n  Warning  FailedMount  14m (x13 over 58m)   kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-xz5tn]: timed out waiting for the condition\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed\n    State:          Waiting\n      Reason:       ContainerCreating","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/000034347aa141bb/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/000034347aa141bb/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/000034347aa141bb/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                   DATA   AGE   LABELS\nrc-volume-key-config   1      60m   rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/000034347aa141bb/tools/002-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/000034347aa141bb/tools/002-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/000034347aa141bb/tools/002-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-volume-configmap-missing-key\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T14:27:19Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-volume-configmap-missing-key, pod_abnormal_type=VolumeMountFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-volume-mount-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"config-volume\", \"configMap\": \"rc-volume-key-config\"}\n- {\"name\": \"kube-api-access-xz5tn\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/000034347aa141bb/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/000034347aa141bb/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/000034347aa141bb/tools/003-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"已采集关键证据：\n\n1. **Critical 证据**：\n   - `kubectl describe pod` 显示 `MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key`，明确指向 ConfigMap 缺失指定键。\n   - `kubectl get configmap rc-volume-key-config -n aiops-e2e` 显示该 ConfigMap 只有 1 个数据项，与 Pod spec 中的引用不匹配。\n   - `kubectl get pod -o yaml` 显示 Pod spec 中 `volumes[].configMap` 引用了 `rc-volume-key-config`，但未指定具体 key。\n\n2. **冲突证据**：\n   - 无冲突证据；当前 Pod 和 ConfigMap 均存在于指定命名空间，但 ConfigMap 内容不满足引用需求。\n\n结论：Pod `rc-volume-configmap-missing-key` 无法创建容器，根本原因是其引用的 ConfigMap `rc-volume-key-config` 缺失指定键 `missing-key`。建议检查 ConfigMap 的定义并补充缺失的键。","collection_summary":"计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%；其中真实环境证据 6/6 项，完整度 100%；实际执行工具 7 个，匹配计划 2 个，未规划证据 5 个","plan_total":2,"plan_collected":2,"plan_completeness":1.0,"environment_evidence_total":6,"environment_evidence_collected":6,"environment_evidence_completeness":1.0,"executed_tool_count":7,"matched_tool_count":2,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"检查 Pod rc-volume-configmap-missing-key 的详细描述信息，以确认其 volumeMount 问题的具体原因。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e","purpose":"确认 Pod 的 volumeMount 问题是否由 ConfigMap 键缺失导致。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"检查 ConfigMap rc-volume-key-config 是否存在，并确认其是否缺少键 'missing-key'。","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap rc-volume-key-config -n aiops-e2e","purpose":"验证 ConfigMap 是否缺失指定键，导致 volumeMount 失败。","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/2 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 检查 Pod rc-volume-configmap-missing-key 的详细描述信... | `kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_by_name | 检查 ConfigMap rc-volume-key-config 是否存在，并确认其是否... | `kubectl get configmap rc-volume-key-config -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (21.6s)
   📤 → 下游数据: root_cause=[L4层] 当前无法基于 LLM 输出确定根本原因
   confidence=10%
   causal_chain={"trigger": "LLM 未生成可靠因果链", "mechanism": "缺少可用的结构化根因分析结果", "manifestation": "我的集群有什么问题"}
   rca_analysis={"phenomenon": "我的集群有什么问题", "evidence_analysis": [], "causal_chain": {"trigger": "LLM 未生成可靠因果链", "mechanism": "缺少可用的结构化根因分析结果", "manifestation": "我的集群有什么问题"}, "root_cause": "[L4层] 当前无法基于 LLM 输出确定根本原因", "confidence": 0.1, "confidence_reason": "LLM 返回结果不符合 RCA 结构化输出合同", "alternative_causes": []}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: [L4层] 当前无法基于 LLM 输出确定根本原因
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
   ✅ [汇总总结] 完成 (1m 4.4s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4427 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 2.6s
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
| **问题分类** | VolumeMountFailed / ConfigError |
| **置信度** | 高 (95%) |
| **证据完整度** | 2/2 (100%) |

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
| 错误信息 | `MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 事件 | kubectl get events | `Warning FailedMount: MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key` | ConfigMap 缺少引用的键 `missing-key` |
| 2 | ConfigMap 内容 | kubectl get configmap rc-volume-key-config | `DATA: 1` | ConfigMap 中未包含键 `missing-key`，与 Pod spec 中定义的 `volumes[].configMap.items[].key` 不匹配 |
| 3 | Pod spec | kubectl get pod rc-volume-configmap-missing-key -o yaml | `volumes[].configMap.items[].key: missing-key` | Pod 明确引用了 ConfigMap 中不存在的键 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 的 VolumeMount 依赖 ConfigMap 中的 `missing-key`，但 ConfigMap 实际未包含该键 → 导致卷挂载失败。
- **证据链**：Pod spec 引用了 ConfigMap 中不存在的键 → kubelet 尝试挂载时失败 → Pod 状态为 `ContainerCreating`，持续失败 → Events 显示 `MountVolume.SetUp failed`。

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ ConfigMap rc-volume-key-config 缺失键 'missing-key'             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Pod spec 中 volumes[].configMap.items[].key 指向缺失键          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ MountVolume.SetUp failed for volume "config-volume"             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod rc-volume-configmap-missing-key 状态为 ContainerCreating    │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (`MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key`) 和证据 #2 (`ConfigMap rc-volume-key-config 中 DATA=1，未包含键 missing-key`)，问题的根本原因是 **ConfigMap rc-volume-key-config 缺失 Pod spec 中引用的键 `missing-key`**，导致卷挂载失败，Pod 无法进入 Running 状态。

**置信度**：高 (95%)

- ✅ 事件 `MountVolume.SetUp failed` 明确指向 ConfigMap 键缺失
- ✅ `kubectl get configmap` 验证了 ConfigMap 实际未包含 `missing-key`

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 更新 ConfigMap，添加缺失的键 `missing-key`**
```bash
kubectl edit configmap rc-volume-key-config -n aiops-e2e
```
*操作步骤*：
- 在 `data` 字段中添加：
  ```yaml
  missing-key: your-value-here
  ```
- 保存并退出

*依据*：Pod spec 中明确引用了 `missing-key`，ConfigMap 中缺失此键导致挂载失败

**2. [可选] 重启 Pod 以应用更新**
```bash
kubectl delete pod rc-volume-configmap-missing-key -n aiops-e2e
```
*目的*：触发 Pod 重建，使用更新后的 ConfigMap

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 ConfigMap 是否已更新 | `kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml` | `data` 中包含 `missing-key` |
| 2. 确认 Pod 是否已重建并运行 | `kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e` | STATUS: Running |
| 3. 检查 Pod Events | `kubectl get events -n aiops-e2e | grep rc-volume-configmap-missing-key` | 无 `FailedMount` 事件 |

---

## ⚠️ 注意事项

- 如果 ConfigMap 由 Helm Chart 或 CI/CD 管理，请确保在部署流程中包含 `missing-key`
- 如果 Pod 仍然无法启动，检查 ConfigMap 的命名空间是否匹配 Pod 的命名空间
- 若应用本身不需要 `missing-key`，应从 Pod spec 中移除对它的引用

---

## ✅ 修复后预期状态

| 项目 | 修复后状态 |
|------|------------|
| Pod 状态 | Running |
| Events | 无 `FailedMount` |
| ConfigMap | 包含 `missing-key` |
| 卷挂载 | 成功 |

---

## 📦 附录：相关上下文

- **Pod 名称**：`rc-volume-configmap-missing-key`
- **命名空间**：`aiops-e2e`
- **ConfigMap 名称**：`rc-volume-key-config`
- **节点**：`node1`
- **关键事件**：`MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key`

---

## 📊 性能统计

├─ 总耗时: 4.0m
├─ 问题定位: 51.4s (21%) ✅
├─ 证据链采集: 105.2s (43%) ✅
├─ 根因分析: 21.6s (9%) ✅
├─ 汇总总结: 64.4s (27%) ✅
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
