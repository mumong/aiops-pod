======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 30fe1c2c2ac746f9]

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
      📄 NAME                         READY   STATUS              RESTARTS   AGE   IP       NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-volume-hostpath-missing   0/1     ContainerCreating   0         
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
5m20s (x35 over 60m)   Warning   FailedMount   Pod/rc-volume-hostpath-missing   MountVolume.SetUp failed for volume "missing-hostpath" : hostPath type check failed: /tmp/aiop
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-volume-hostpath-missing
namespace: aiops-e2e
creationTimestamp: 2026-05-13T18:26:26Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers
   💭 [问题定位] {
  "layer": "L3",
  "derived_layer": "L3",
  "layers": ["L3"],
  "layer_name": "VolumeMountFailed",
  "confidence": "high",
  "reasoning": "Pod rc-volume-hostpath-missing 处于 ContainerCreating 状态，且 Events 显示 hostPath 类型检查失败，表明卷挂载失败。此问题与 StorageVolume 相关，归类为 L3 层。",
  "abnormal_pods": ["rc-volume-hostpath-missing"],
  "abnormal_groups": ["VolumeMountFailed"],
  "pod_status_keyword": "ContainerCreating",
  "pod_abnormal_type": "VolumeMountFailed",
  "status_category": "storage_volume",
  "key_entities": {
    "Pod": "rc-volume-hostpath-missing",
    "Volume": "missing-hostpath",
    "Node": "node1"
  },
  "possible_scenarios": [
    "hostPath 路径 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 不存在或不是目录",
    "hostPath 权限不足导致挂载失败",
    "节点 node1 上的路径配置错误"
  ]
}
   ✅ [问题定位] 完成 (32.0s)
   📤 → 下游数据: layer=Layer.L3, layers=L3
   scenarios=[]
   entities=[]
   reasoning=Pod rc-volume-hostpath-missing 处于 ContainerCreating 状态，且 Events 显示 hostPath 类型检查失败，表明卷挂载失败。此问题与 StorageVolume 相关，归类为 L3 层。
   layer_analysis={"layer": "L3", "derived_layer": "", "layers": [], "layer_name": "", "confidence": 0.5, "reasoning": "Pod rc-volume-hostpath-missing 处于 ContainerCreating 状态，且 Events 显示 hostPath 类型检查失败，表明卷挂载失败。此问题与 StorageVolume 相关，归类为 L3 层。", "abnormal_pods": [{"name": "rc-volume-hostpath-missing", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "storage_volume", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-hostpath-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-hostpath-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-volume-hostpath-missing                          0/1     ContainerCreating   0                60m    <none>           node1    <none>           <none>            app=rc-volume-hostpath-missing,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/30fe1c2c2ac746f9/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/30fe1c2c2ac746f9/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/30fe1c2c2ac746f9/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L3
   置信度: 50%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-volume-hostpath-missing
namespace: aiops-e2e
creationTimestamp: 2026-05-13T18:26:26Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
6m49s (x35 over 61m)   Warning   FailedMount   Pod/rc-volume-hostpath-missing   MountVolume.SetUp failed for volume "missing-hostpath" : hostPath type check failed: /tmp/aiop
   💭 [证据链采集] 已采集证据:
- kubectl_get_yaml: 确认 Pod 的 spec.volumes 配置，特别是 hostPath 路径是否正确
- kubectl_events: 确认 Pod 的 FailedMount 事件，以识别 VolumeMountFailed 的具体原因

未采集证据: 无

冲突证据: 无

结论: Pod `rc-volume-hostpath-missing` 处于 `ContainerCreating` 状态，且 Events 显示 `MountVolume.SetUp failed for volume "missing-hostpath"`，具体错误是 `hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory`。这表明该 Pod 无法挂载指定的 hostPath 卷，因为目标路径不存在或类型不匹配。
   ✅ [证据链采集] 完成 (1m 16.2s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod rc-volume-hostpath-missing 的详细信息以诊断 VolumeMountFailed 问题","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-hostpath-missing -n aiops-e2e -o yaml","tool_args":{"namespace":"aiops-e2e","name":"rc-volume-hostpath-missing","output":"yaml"},"purpose":"确认 Pod 的 spec.volumes 配置，特别是 hostPath 路径是否正确","evidence_type":"configuration","target_scope":"Pod/aiops-e2e/rc-volume-hostpath-missing","acceptable_tools":["kubectl_get_yaml","kubectl_get_by_name","kubectl_get_by_kind_in_namespace"],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod rc-volume-hostpath-missing 的事件信息以诊断 VolumeMountFailed 问题","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-hostpath-missing --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","pod_name":"rc-volume-hostpath-missing","sort_by":".lastTimestamp"},"purpose":"确认 Pod 的 FailedMount 事件，以识别 VolumeMountFailed 的具体原因","evidence_type":"event","target_scope":"Pod/aiops-e2e/rc-volume-hostpath-missing","acceptable_tools":["kubectl_events","kubectl_get_by_kind_in_namespace"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-volume-hostpath-missing\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T18:26:26Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-volume-hostpath-missing, pod_abnormal_type=VolumeMountFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-volume-mount-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"missing-hostpath\"}\n- {\"name\": \"kube-api-access-42crm\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/30fe1c2c2ac746f9/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/30fe1c2c2ac746f9/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/30fe1c2c2ac746f9/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n6m49s (x35 over 61m)   Warning   FailedMount   Pod/rc-volume-hostpath-missing   MountVolume.SetUp failed for volume \"missing-hostpath\" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory\n48m (x2 over 55m)      Warning   FailedMount   Pod/rc-volume-hostpath-missing   Unable to attach or mount volumes: unmounted volumes=[missing-hostpath], unattached volumes=[kube-api-access-42crm missing-hostpath]: timed out waiting for the condition\n50s (x22 over 59m)     Warning   FailedMount   Pod/rc-volume-hostpath-missing   Unable to attach or mount volumes: unmounted volumes=[missing-hostpath], unattached volumes=[missing-hostpath kube-api-access-42crm]: timed out waiting for the condition","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/30fe1c2c2ac746f9/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/30fe1c2c2ac746f9/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/30fe1c2c2ac746f9/tools/002-evidence-kubectl_events.summary.txt"}],"llm_analysis":"已采集证据:\n- kubectl_get_yaml: 确认 Pod 的 spec.volumes 配置，特别是 hostPath 路径是否正确\n- kubectl_events: 确认 Pod 的 FailedMount 事件，以识别 VolumeMountFailed 的具体原因\n\n未采集证据: 无\n\n冲突证据: 无\n\n结论: Pod `rc-volume-hostpath-missing` 处于 `ContainerCreating` 状态，且 Events 显示 `MountVolume.SetUp failed for volume \"missing-hostpath\"`，具体错误是 `hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory`。这表明该 Pod 无法挂载指定的 hostPath 卷，因为目标路径不存在或类型不匹配。","collection_summary":"计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%；其中真实环境证据 6/6 项，完整度 100%；实际执行工具 6 个，匹配计划 2 个，未规划证据 4 个","plan_total":2,"plan_collected":2,"plan_completeness":1.0,"environment_evidence_total":6,"environment_evidence_collected":6,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":2,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"获取 Pod rc-volume-hostpath-missing 的详细信息以诊断 VolumeMountFailed 问题","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-hostpath-missing -n aiops-e2e -o yaml","purpose":"确认 Pod 的 spec.volumes 配置，特别是 hostPath 路径是否正确","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod rc-volume-hostpath-missing 的事件信息以诊断 VolumeMountFailed 问题","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-hostpath-missing --sort-by='.lastTimestamp'","purpose":"确认 Pod 的 FailedMount 事件，以识别 VolumeMountFailed 的具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/2 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_yaml | 获取 Pod rc-volume-hostpath-missing 的详细信息以诊断 Vo... | `kubectl get pod rc-volume-hostpath-missing -n aiops-e2e -o yaml` |
   | e2 | critical | ✅ | kubectl_events | 获取 Pod rc-volume-hostpath-missing 的事件信息以诊断 Vo... | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volum...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 32.1s)
   📤 → 下游数据: root_cause=Pod rc-volume-hostpath-missing 处于 ContainerCreating 状态，Events 显示 MountVolume.SetUp 失败，具体错误为 hostPath 类型检查失败: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory。这表明指定的 hostPath 路径不存在或类型不匹配，导致卷无法挂载。
   confidence=80%
   causal_chain={"root_cause": "hostPath 类型检查失败", "intermediate_causes": ["MountVolume.SetUp 失败", "Pod 处于 ContainerCreating 状态"], "immediate_effects": ["Pod 无法完成创建", "卷无法挂载"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"tool": "kubectl_get_yaml", "description": "Pod rc-volume-hostpath-missing 的详细信息，显示 hostPath 卷配置和状态为 Pending"}, {"tool": "kubectl_events", "description": "Pod rc-volume-hostpath-missing 的事件，显示 MountVolume.SetUp 失败，hostPath 类型检查失败"}, {"tool": "kubectl_get_by_kind_in_cluster", "description": "集群中 Pod 状态摘要，显示 1 个异常 Pod 处于 ContainerCreating 状态"}, {"tool": "kubectl_get_by_name", "description": "Pod rc-volume-hostpath-missing 的基本信息，显示状态为 ContainerCreating"}, {"tool": "kubectl_get_yaml", "description": "Pod rc-volume-hostpath-missing 的 YAML 配置摘要，显示 volumes 配置和 phase: Pending"}], "evidence_analysis": [{"tool": "kubectl_get_yaml", "summary": "Pod 配置显示 hostPath 卷缺失或类型不匹配，导致 phase: Pending"}, {"tool": "kubectl_events", "summary": "MountVolume.SetUp 失败事件表明 hostPath 路径不存在或类型不匹配"}, {"tool": "kubectl_get_by_kind_in_cluster", "summary": "1 个 Pod 处于 ContainerCreating 状态，表明卷挂载失败是当前主要问题"}], "causal_chain": {"root_cause": "hostPath 类型检查失败", "intermediate_causes": ["MountVolume.SetUp 失败", "Pod 处于 ContainerCreating 状态"], "immediate_effects": ["Pod 无法完成创建", "卷无法挂载"]}, "root_cause": "Pod rc-volume-hostpath-missing 处于 ContainerCreating 状态，Events 显示 MountVolume.SetUp 失败，具体错误为 hostPath 类型检查失败: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory。这表明指定的 hostPath 路径不存在或类型不匹配，导致卷无法挂载。", "root_cause_summary": "Pod rc-volume-hostpath-missing 处于 ContainerCreating 状态，Events 显示 MountVolume.SetUp 失败，具体错误为 hostPath 类型检查失败: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory。这表明指定的 hostPath 路径不存在或类型不匹配，导致卷无法挂载。", "confidence": 0.8, "confidence_reason": "有直接证据表明 hostPath 路径问题，且因果链清晰。", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [{"cause": "Pod 配置错误", "evidence": "Pod YAML 配置显示 volumes 配置可能不正确"}, {"cause": "节点存储问题", "evidence": "nodeName 为 node1，但未采集节点存储状态"}], "limitations": "未采集节点存储状态，无法确认是否为节点存储问题。", "llm_raw_analysis": "已采集证据表明，Pod rc-volume-hostpath-missing 处于 ContainerCreating 状态，且 Events 显示 MountVolume.SetUp 失败，具体错误为 hostPath 类型检查失败: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory。这表明指定的 hostPath 路径不存在或类型不匹配，导致卷无法挂载。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-volume-hostpath-missing 处于 ContainerCreating 状态，Events 显示 MountVolume.SetUp 失败，具体错误为 hostPath 类型检查失败: /tmp/aiops-rootcause-definitely-missing-h...
   置信度: 80%
   🔗 因果链:
     根本原因: hostPath 类型检查失败


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 24.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4130 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 44.3s
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
| **兼容归因层** | L3 - storage_volume |
| **问题分类** | VolumeMountFailed |
| **置信度** | 高 (80%) |
| **证据完整度** | 2/2 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | rc-volume-hostpath-missing |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 事件 | kubectl events | `Warning FailedMount Pod/rc-volume-hostpath-missing MountVolume.SetUp failed for volume "missing-hostpath" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory` | 卷挂载失败，路径不存在或类型不匹配 |
| 2 | Pod 详细信息 | kubectl get pod -o yaml | `kind: Pod, name: rc-volume-hostpath-missing, namespace: aiops-e2e, phase: Pending` | Pod 无法进入 Running 状态，处于 ContainerCreating 阶段 |

### 证据关联分析

- **证据 #1 印证**：`MountVolume.SetUp failed for volume "missing-hostpath"` 明确指出卷挂载失败，错误信息为 `hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory`，说明指定的 hostPath 路径不存在或不是目录。
- **证据链**：Pod 配置中引用了 hostPath 类型的卷，但节点上路径不存在或类型不匹配 → 挂载失败 → Pod 无法创建 → 状态为 `ContainerCreating`。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 节点上路径是否存在 | critical | 无法确认路径实际状态 |
| 节点存储日志 | important | 无法确认是否为节点存储问题 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ hostPath 路径 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 不存在或不是目录 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ hostPath 类型检查失败 → 挂载失败 → Pod 无法创建                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Pod rc-volume-hostpath-missing 无法完成 VolumeMount，处于 ContainerCreating 状态 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 ContainerCreating，Events 显示 FailedMount 错误      │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1（`MountVolume.SetUp failed for volume "missing-hostpath"`）和证据 #2（Pod 状态为 ContainerCreating），问题的根本原因是**hostPath 路径 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 不存在或不是目录**，导致卷挂载失败，Pod 无法创建。

**置信度**：高 (80%)
- ✅ `FailedMount` 事件明确指向卷挂载失败
- ✅ 错误信息 `hostPath type check failed` 明确指出路径类型不匹配或路径不存在
- ⚠️ 未采集节点存储状态，无法确认是否为节点存储问题

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 确保 hostPath 路径存在且类型匹配**
```bash
# 登录到 node1 节点
ssh node1
mkdir -p /tmp/aiops-rootcause-definitely-missing-hostpath-dir
```
*依据*：错误信息指出 hostPath 路径不存在或不是目录，需创建路径或确保其为目录

**2. [可选] 重启 Pod 以重新尝试挂载**
```bash
kubectl delete pod rc-volume-hostpath-missing -n aiops-e2e
```
*目的*：删除 Pod 后，K8s 会重新创建 Pod 并尝试挂载卷

**3. [可选] 检查节点存储状态（如适用）**
```bash
ls -ld /tmp/aiops-rootcause-definitely-missing-hostpath-dir
```
*目的*：确认路径存在且是目录

### 后续优化

1. **路径检查自动化**：在部署前确保所有 hostPath 路径存在
2. **使用 PersistentVolumeClaim**：避免直接使用 hostPath，改用 PVC，提升兼容性和可移植性
3. **监控与告警**：配置卷挂载失败的事件监控，及时发现类似问题

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-volume-hostpath-missing -n aiops-e2e` | STATUS: Running |
| 2. 检查挂载状态 | `kubectl describe pod rc-volume-hostpath-missing -n aiops-e2e | grep -i mount` | 无 FailedMount 事件 |
| 3. 检查节点路径 | `ls -ld /tmp/aiops-rootcause-definitely-missing-hostpath-dir` | 路径存在且是目录 |

---

## ⚠️ 注意事项

- 如果问题持续，建议检查节点的存储配置，确保 hostPath 路径在所有节点上都可用
- 如果使用的是 hostPath，确保路径在所有节点上一致，避免调度问题
- 避免在生产环境中使用 hostPath，改用 PVC 或动态卷插件

---

## 📊 性能统计

├─ 总耗时: 4.7m
├─ 问题定位: 32.0s (11%) ✅
├─ 证据链采集: 76.2s (27%) ✅
├─ 根因分析: 92.1s (32%) ✅
├─ 汇总总结: 84.0s (30%) ✅
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
