======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 3c8a18d7a7eb4cbf]

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
  Warning  FailedMount  16m (x50 over 101m)   kubelet  MountVolume.SetUp failed
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                          READY   STATUS              RESTARTS   AGE    IP       NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-volume-missing-configmap   0/1     ContainerCreating   0      
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
  "reasoning": "Pod 'rc-volume-missing-configmap' 处于 Pending 状态，且 Events 显示 'configmap \"rc-definitely-missing-configmap\" not found'。进一步确认 'kubectl get configmap rc-definitely-missing-configmap' 返回 'Error from server (NotFound)'，表明引用的 ConfigMap 缺失。这属于 ConfigError 类型，兼容归因 L4。",
  "abnormal_pods": [
    {
      "name": "rc-volume-missing-configmap",
      "namespace": "aiops-e2e",
      "status": "Pending",
      "reason": "ContainerCreating",
      "events": [
        {
          "type": "Warning",
          "reason": "FailedMount",
          "message": "MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found"
        },
        {
          "type": "Warning",
          "reason": "FailedMount",
          "message": "Unable to attach or mount volumes: unmounted volumes=[missing-config], unattached volumes=[kube-api-access-n5pfx missing-config]: timed out waiting for the condition"
        }
      ]
    }
  ],
  "abnormal_groups": [
    {
      "type": "VolumeMountFailed",
      "pods": [
        "rc-volume-missing-configmap"
      ]
    }
  ],
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "VolumeMountFailed",
  "status_category": "ConfigError",
  "key_entities": [
    "ConfigMap rc-definitely-missing-configmap",
    "Pod rc-volume-missing-configmap"
  ],
  "possible_scenarios": [
    "ConfigMap rc-definitely-missing-configmap 未创建或命名错误",
    "Pod rc-volume-missing-configmap 引用了错误的 ConfigMap 名称或命名空间"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (56.5s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'ConfigMap rc-definitely-missing-configmap 未创建或命名错误', 'probability': 'high', 'reason': 'Events 明确提示 ConfigMap 不存在'}, {'scenario': 'Pod rc-volume-missing-configmap 引用了错误的 ConfigMap 名称或命名空间', 'probability': 'medium', 'reason': '配置名称或命名空间不匹配可能导致引用失败'}]
   entities=[{"type": "ConfigMap", "name": "rc-definitely-missing-configmap", "namespace": "aiops-e2e"}, {"type": "Pod", "name": "rc-volume-missing-configmap", "namespace": "aiops-e2e"}]
   reasoning=Pod 'rc-volume-missing-configmap' 处于 Pending 状态，且 Events 显示 'configmap "rc-definitely-missing-configmap" not found'。进一步确认 'kubectl get configmap rc-definitely-missing-configmap' 返回 'Error from server (NotFound)'，表明引用的 ConfigMap 缺失。这属于 ConfigError 类型，兼容归因 L4。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.95, "reasoning": "Pod 'rc-volume-missing-configmap' 处于 Pending 状态，且 Events 显示 'configmap \"rc-definitely-missing-configmap\" not found'。进一步确认 'kubectl get configmap rc-definitely-missing-configmap' 返回 'Error from server (NotFound)'，表明引用的 ConfigMap 缺失。这属于 ConfigError 类型，兼容归因 L4。", "abnormal_pods": [{"name": "rc-volume-missing-configmap", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "VolumeMountFailed", "status_category": "ConfigError", "key_entities": [{"type": "ConfigMap", "name": "rc-definitely-missing-configmap", "namespace": "aiops-e2e"}, {"type": "Pod", "name": "rc-volume-missing-configmap", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "ConfigMap rc-definitely-missing-configmap 未创建或命名错误", "probability": "high", "reason": "Events 明确提示 ConfigMap 不存在"}, {"scenario": "Pod rc-volume-missing-configmap 引用了错误的 ConfigMap 名称或命名空间", "probability": "medium", "reason": "配置名称或命名空间不匹配可能导致引用失败"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-configmap"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-configmap"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-volume-missing-configmap                         0/1     ContainerCreating   0                101m    <none>           node1    <none>           <none>            app=rc-volume-missing-configmap,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/3c8a18d7a7eb4cbf/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/3c8a18d7a7eb4cbf/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/3c8a18d7a7eb4cbf/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
      📄 kubectl_get_by_name 输出摘要: raw_chars=199 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide configmap rc-definitely-missing-configmap -n aiops-e2e
Error from server (NotFound): configma
   💭 [证据链采集] 已采集证据：
- `kubectl_get_by_name` 确认 ConfigMap `rc-definitely-missing-configmap` 在 namespace `aiops-e2e` 中不存在，与 Pod Events 中的错误提示一致。

冲突证据：
- 无。

未采集证据：
- 无。

结论：
ConfigMap `rc-definitely-missing-configmap` 不存在，导致 Pod `rc-volume-missing-configmap` 无法创建，属于典型的 ConfigError。建议创建缺失的 ConfigMap 或检查 Pod 中的配置引用是否正确。
   ✅ [证据链采集] 完成 (44.1s)
   📤 → 下游数据: evidence_items=5/5
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"Verify if the referenced ConfigMap 'rc-definitely-missing-configmap' exists in namespace 'aiops-e2e'","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e","tool_args":{"name":"rc-definitely-missing-configmap","namespace":"aiops-e2e","kind":"ConfigMap"},"purpose":"Confirm whether the referenced ConfigMap is missing as indicated in Pod Events","evidence_type":"negative","target_scope":"aiops-e2e","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=199 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide configmap rc-definitely-missing-configmap -n aiops-e2e\nError from server (NotFound): configmaps \"rc-definitely-missing-configmap\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/3c8a18d7a7eb4cbf/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/3c8a18d7a7eb4cbf/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/3c8a18d7a7eb4cbf/tools/001-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"已采集证据：\n- `kubectl_get_by_name` 确认 ConfigMap `rc-definitely-missing-configmap` 在 namespace `aiops-e2e` 中不存在，与 Pod Events 中的错误提示一致。\n\n冲突证据：\n- 无。\n\n未采集证据：\n- 无。\n\n结论：\nConfigMap `rc-definitely-missing-configmap` 不存在，导致 Pod `rc-volume-missing-configmap` 无法创建，属于典型的 ConfigError。建议创建缺失的 ConfigMap 或检查 Pod 中的配置引用是否正确。","collection_summary":"计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%；其中真实环境证据 5/5 项，完整度 100%；实际执行工具 5 个，匹配计划 1 个，未规划证据 4 个","plan_total":1,"plan_collected":1,"plan_completeness":1.0,"environment_evidence_total":5,"environment_evidence_collected":5,"environment_evidence_completeness":1.0,"executed_tool_count":5,"matched_tool_count":1,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"Verify if the referenced ConfigMap 'rc-definitely-missing-configmap' exists in namespace 'aiops-e2e'","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e","purpose":"Confirm whether the referenced ConfigMap is missing as indicated in Pod Events","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/1 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | Verify if the referenced ConfigMap 'rc-defini... | `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 0.1s)
   📤 → 下游数据: root_cause=The Pod 'rc-volume-missing-configmap' is in 'ContainerCreating' state due to a missing ConfigMap 'rc-definitely-missing-configmap' in the namespace 'aiops-e2e'. The kubectl_get_by_name command confirms the ConfigMap is not found, and the kubectl_describe output shows 'FailedMount' events indicating the issue. This is a classic ConfigError scenario where the referenced ConfigMap is missing, preventing the Pod from proceeding with volume setup and container creation.
   confidence=95%
   causal_chain={"root_cause": "ConfigMap 'rc-definitely-missing-configmap' is missing in the namespace 'aiops-e2e'.", "intermediate_causes": ["Pod 'rc-volume-missing-configmap' references the missing ConfigMap as part of its volume setup.", "Kubelet fails to mount the volume due to the missing ConfigMap, leading to 'FailedMount' events."], "immediate_causes": ["MountVolume.SetUp failed for volume 'missing-config' due to the missing ConfigMap.", "Pod remains in 'ContainerCreating' state as it cannot proceed without the mounted volume."], "symptoms": ["Pod 'rc-volume-missing-configmap' is in 'ContainerCreating' state.", "Events show 'FailedMount' warnings related to the missing ConfigMap."]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"description": "Verify if the referenced ConfigMap 'rc-definitely-missing-configmap' exists in namespace 'aiops-e2e'", "level": "critical", "value": "kubectl_get_by_name outputs: Command failed (exit 1):\nkubectl get --show-labels -o wide configmap rc-definitely-missing-configmap -n aiops-e2e\nError from server (NotFound): configmaps \"rc-definitely-missing-configmap\" not found"}, {"description": "kubectl_get_by_kind_in_cluster", "level": "important", "value": "kubectl_get_by_kind_in_cluster table summary: rows=49 abnormal=1 status_counts={'Running': 46} with the following abnormal entry:\naiops-e2e     rc-volume-missing-configmap                         0/1     ContainerCreating   0                101m    <none>           node1    <none>           <none>            app=rc-volume-missing-configmap,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"}, {"description": "kubectl_describe", "level": "important", "value": "kubectl_describe summary: Pod 'rc-volume-missing-configmap' in namespace 'aiops-e2e' is in 'Pending' state with the following key events:\n  Warning  FailedMount  16m (x50 over 101m)   kubelet  MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found\n  Warning  FailedMount  31m (x10 over 92m)    kubelet  Unable to attach or mount volumes: unmounted volumes=[missing-config], unattached volumes=[kube-api-access-n5pfx missing-config]: timed out wai\n... 截断，原始 522 字符"}, {"description": "kubectl_get_by_name", "level": "important", "value": "kubectl_get_by_name output summary: rc-volume-missing-configmap is in 'ContainerCreating' state with 'VolumeMountFailed' label"}], "evidence_analysis": [{"description": "ConfigMap 'rc-definitely-missing-configmap' missing in namespace 'aiops-e2e'", "level": "critical", "value": "kubectl_get_by_name confirms the ConfigMap 'rc-definitely-missing-configmap' is not found in the namespace 'aiops-e2e', aligning with the error in Pod 'rc-volume-missing-configmap' events."}, {"description": "Pod 'rc-volume-missing-configmap' in 'ContainerCreating' state due to volume mount failure", "level": "important", "value": "kubectl_get_by_kind_in_cluster and kubectl_describe indicate the Pod 'rc-volume-missing-configmap' is in 'ContainerCreating' state with 'VolumeMountFailed' label and events showing 'FailedMount' for the missing ConfigMap."}], "causal_chain": {"root_cause": "ConfigMap 'rc-definitely-missing-configmap' is missing in the namespace 'aiops-e2e'.", "intermediate_causes": ["Pod 'rc-volume-missing-configmap' references the missing ConfigMap as part of its volume setup.", "Kubelet fails to mount the volume due to the missing ConfigMap, leading to 'FailedMount' events."], "immediate_causes": ["MountVolume.SetUp failed for volume 'missing-config' due to the missing ConfigMap.", "Pod remains in 'ContainerCreating' state as it cannot proceed without the mounted volume."], "symptoms": ["Pod 'rc-volume-missing-configmap' is in 'ContainerCreating' state.", "Events show 'FailedMount' warnings related to the missing ConfigMap."]}, "root_cause": "The Pod 'rc-volume-missing-configmap' is in 'ContainerCreating' state due to a missing ConfigMap 'rc-definitely-missing-configmap' in the namespace 'aiops-e2e'. The kubectl_get_by_name command confirms the ConfigMap is not found, and the kubectl_describe output shows 'FailedMount' events indicating the issue. This is a classic ConfigError scenario where the referenced ConfigMap is missing, preventing the Pod from proceeding with volume setup and container creation.", "root_cause_summary": "The Pod 'rc-volume-missing-configmap' is in 'ContainerCreating' state due to a missing ConfigMap 'rc-definitely-missing-configmap' in the namespace 'aiops-e2e'. The kubectl_get_by_name command confirms the ConfigMap is not found, and the kubectl_describe output shows 'FailedMount' events indicating the issue. This is a classic ConfigError scenario where the referenced ConfigMap is missing, preventing the Pod from proceeding with volume setup and container creation.", "confidence": 0.95, "confidence_reason": "The root cause is directly supported by the evidence showing the missing ConfigMap and the corresponding 'FailedMount' events in the Pod's description. The confidence is high as the evidence is clear and directly points to the missing ConfigMap as the cause of the Pod's issue.", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [{"description": "Pod 'rc-volume-missing-configmap' might be referencing a ConfigMap with an incorrect name or namespace.", "probability": "medium", "reason": "If the ConfigMap exists but with a different name or in a different namespace, the Pod would fail to find it. However, the evidence confirms the ConfigMap is not found at all, making this less likely."}], "limitations": "The analysis is based on the current state of the cluster and assumes that the missing ConfigMap is the only issue. If there are other issues related to the Pod's configuration or the volume setup, they may not be addressed in this analysis.", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: The Pod 'rc-volume-missing-configmap' is in 'ContainerCreating' state due to a missing ConfigMap 'rc-definitely-missing-configmap' in the namespace 'a...
   置信度: 95%
   🔗 因果链:
     根本原因: ConfigMap 'rc-definitely-missing-configmap' is missing in the namespace 'aiops-e2e'.


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 47.4s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4219 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 28.1s
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
| **问题分类** | ConfigError（ConfigMap 缺失） |
| **置信度** | 高 (95%) |
| **证据完整度** | 1/1 (100%) |

---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-volume-missing-configmap |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | `MountVolume.SetUp failed for volume "missing-config": configmap "rc-definitely-missing-configmap" not found` |

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: ContainerCreating` | Pod 无法完成容器创建 |
| 2 | Pod Describe | `kubectl describe pod rc-volume-missing-configmap` | `Warning: FailedMount: MountVolume.SetUp failed for volume "missing-config": configmap "rc-definitely-missing-configmap" not found` | 卷挂载失败，明确指向缺失的 ConfigMap |
| 3 | ConfigMap 检查 | `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` | `Error from server (NotFound): configmaps "rc-definitely-missing-configmap" not found` | 确认 ConfigMap 不存在 |
| 4 | Pod 标签 | `kubectl get pod -o wide` | `pod_abnormal_type=VolumeMountFailed` | 确认异常类型 |
| 5 | 事件日志 | `kubectl describe pod` | `Warning: FailedMount (repeated multiple times)` | 事件表明持续失败 |

### 证据关联分析
- **证据 #2 + #3 印证**：Pod Describe 显示卷挂载失败，而 ConfigMap 不存在 → 直接导致 Pod 无法创建容器。
- **证据链**：Pod 引用了不存在的 ConfigMap → 卷挂载失败 → Pod 无法进入 Running 状态 → 持续显示 ContainerCreating 状态。

### 缺失证据（无）
| 证据 | 级别 | 影响 |
|------|------|------|
| （无缺失） | （无缺失） | （无缺失） |

---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ ConfigMap 'rc-definitely-missing-configmap' 未创建或命名错误    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Pod 指定的 ConfigMap 不存在 → 卷挂载失败 → 容器无法创建         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ `MountVolume.SetUp failed for volume "missing-config"`          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod rc-volume-missing-configmap 状态为 ContainerCreating        │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2（`MountVolume.SetUp failed`）和证据 #3（`kubectl get configmap` 返回 `NotFound`），问题的根本原因是 **ConfigMap `rc-definitely-missing-configmap` 未创建或命名错误**，导致 Pod 无法完成卷挂载并进入 Running 状态。
**置信度**：高 (95%)
- ✅ `kubectl describe pod` 明确提示 ConfigMap 不存在
- ✅ `kubectl get configmap` 证实 ConfigMap 不存在
- ✅ Pod 状态为 `ContainerCreating`，且标签为 `pod_abnormal_type=VolumeMountFailed`

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 创建缺失的 ConfigMap**
```bash
kubectl create configmap rc-definitely-missing-configmap -n aiops-e2e --from-literal=key=value
```
*依据*：ConfigMap 缺失是导致挂载失败的根本原因

**2. [可选] 验证 Pod 是否恢复运行**
```bash
kubectl get pod rc-volume-missing-configmap -n aiops-e2e
```
*目的*：确认 Pod 是否成功进入 Running 状态

**3. [可选] 查看 Pod 日志（如果 ConfigMap 已存在但问题依然存在）**
```bash
kubectl logs rc-volume-missing-configmap -n aiops-e2e
```
*目的*：确认是否存在其他配置错误

### 后续优化
1. **自动化检查 ConfigMap 存在性**：在部署流程中加入 ConfigMap 存在性校验
2. **配置命名规范**：确保引用资源的名称与实际一致，避免拼写错误
3. **配置命名空间一致性**：确认 Pod 与引用资源的命名空间一致

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 ConfigMap 存在 | `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` | 显示 ConfigMap 详细信息 |
| 2. 确认 Pod 状态 | `kubectl get pod rc-volume-missing-configmap -n aiops-e2e` | STATUS: Running |
| 3. 检查事件日志 | `kubectl describe pod rc-volume-missing-configmap -n aiops-e2e` | 无 `FailedMount` 事件 |

---
## ⚠️ 注意事项
- 如果 ConfigMap 已创建但问题仍然存在，请检查 Pod 的 `volumeMounts` 配置是否正确
- 如果 ConfigMap 名称或命名空间拼写错误，建议引入 CI/CD 阶段的静态检查
- 建议为所有关键 ConfigMap 设置 `kubectl kustomize` 或 Helm chart 依赖校验

---

## 📊 性能统计

├─ 总耗时: 4.5m
├─ 问题定位: 56.5s (21%) ✅
├─ 证据链采集: 44.1s (16%) ✅
├─ 根因分析: 60.1s (22%) ✅
├─ 汇总总结: 107.4s (40%) ✅
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
