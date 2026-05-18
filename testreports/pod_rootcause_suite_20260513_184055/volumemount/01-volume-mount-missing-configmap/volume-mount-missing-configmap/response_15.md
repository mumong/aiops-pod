======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 81e807deacd14ad2]

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
56m (x10 over 60m)     Warning   FailedMount   Pod/rc-volume-missing-configmap   MountVolume.SetUp failed for volume "missing-config" : configmap "rc-definitely-missing-confi
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=199 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide configmap rc-definitely-missing-configmap -n aiops-e2e
Error from server (NotFound): configma
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": ["L4"],
  "layer_name": "ConfigError",
  "confidence": 0.95,
  "reasoning": "Pod rc-volume-missing-configmap 无法启动，因为其引用的 ConfigMap 'rc-definitely-missing-configmap' 不存在。这表明配置错误，导致卷挂载失败，从而阻止了容器的创建。",
  "abnormal_pods": ["rc-volume-missing-configmap"],
  "abnormal_groups": ["VolumeMountFailed"],
  "pod_status_keyword": "ContainerCreating",
  "pod_abnormal_type": "VolumeMountFailed",
  "status_category": "ConfigError",
  "key_entities": ["Pod/rc-volume-missing-configmap", "ConfigMap/rc-definitely-missing-configmap"],
  "possible_scenarios": ["ConfigMap 缺失导致卷挂载失败"]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 17.0s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'ConfigMap 缺失导致卷挂载失败', 'probability': '高', 'reason': "Events 明确指出 configmap 'rc-definitely-missing-configmap' 不存在，且 Pod spec 中引用了该 ConfigMap。"}]
   entities=[{"type": "Pod", "name": "rc-volume-missing-configmap", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-definitely-missing-configmap", "namespace": "aiops-e2e"}]
   reasoning=Pod rc-volume-missing-configmap 无法启动，因为其引用的 ConfigMap 'rc-definitely-missing-configmap' 不存在。这表明配置错误，导致卷挂载失败，从而阻止了容器的创建。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.95, "reasoning": "Pod rc-volume-missing-configmap 无法启动，因为其引用的 ConfigMap 'rc-definitely-missing-configmap' 不存在。这表明配置错误，导致卷挂载失败，从而阻止了容器的创建。", "abnormal_pods": [{"name": "rc-volume-missing-configmap", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "ConfigError", "key_entities": [{"type": "Pod", "name": "rc-volume-missing-configmap", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-definitely-missing-configmap", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "ConfigMap 缺失导致卷挂载失败", "probability": "高", "reason": "Events 明确指出 configmap 'rc-definitely-missing-configmap' 不存在，且 Pod spec 中引用了该 ConfigMap。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-configmap"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-configmap"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-volume-missing-configmap                         0/1     ContainerCreating   0               29m    <none>           node1    <none>           <none>            app=rc-volume-missing-configmap,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/81e807deacd14ad2/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/81e807deacd14ad2/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/81e807deacd14ad2/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 95%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-volume-missing-configmap
namespace: aiops-e2e
creationTimestamp: 2026-05-13T10:41:00Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizer
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=199 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide configmap rc-definitely-missing-configmap -n aiops-e2e
Error from server (NotFound): configma
   💭 [证据链采集] 已采集关键证据：

1. **Pod spec 验证**：Pod `rc-volume-missing-configmap` 的 `.spec.volumes[]` 明确引用了 ConfigMap `rc-definitely-missing-configmap`。
2. **ConfigMap 缺失验证**：`kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` 返回 `Error from server (NotFound)`，确认 ConfigMap 不存在。
3. **Pod 状态验证**：Pod 处于 `Pending` 状态，且容器状态为 `ContainerCreating`，容器 readiness 为 `False`，原因与卷挂载失败有关。
4. **Events 验证**：Events 明确显示 `MountVolume.SetUp failed for volume "missing-config" : configmap "rc-definitely-missing-configmap" not found`。

结论：  
该异常由 ConfigMap 缺失直接导致，符合 `pod-volume-mount-failed.md` runbook 中的典型原因。建议创建缺失的 ConfigMap `rc-definitely-missing-configmap` 以恢复 Pod 正常运行。
   ✅ [证据链采集] 完成 (1m 9.8s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod rc-volume-missing-configmap 的详细信息以验证其配置中的卷引用","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-missing-configmap -n aiops-e2e -o yaml","tool_args":{"namespace":"aiops-e2e","name":"rc-volume-missing-configmap","kind":"Pod","output":"yaml"},"purpose":"确认 Pod 的 spec.volumes 是否引用了 ConfigMap 'rc-definitely-missing-configmap'","evidence_type":"config_verification","target_scope":"specific_pod","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e2","description":"确认 ConfigMap 'rc-definitely-missing-configmap' 是否存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-definitely-missing-configmap","kind":"ConfigMap"},"purpose":"验证 ConfigMap 是否缺失","evidence_type":"resource_absence","target_scope":"specific_configmap","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-volume-missing-configmap\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T10:41:00Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-volume-missing-configmap, pod_abnormal_type=VolumeMountFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-volume-mount-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"missing-config\", \"configMap\": \"rc-definitely-missing-configmap\"}\n- {\"name\": \"kube-api-access-n5pfx\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/81e807deacd14ad2/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/81e807deacd14ad2/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/81e807deacd14ad2/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=199 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide configmap rc-definitely-missing-configmap -n aiops-e2e\nError from server (NotFound): configmaps \"rc-definitely-missing-configmap\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/81e807deacd14ad2/tools/002-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/81e807deacd14ad2/tools/002-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/81e807deacd14ad2/tools/002-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"已采集关键证据：\n\n1. **Pod spec 验证**：Pod `rc-volume-missing-configmap` 的 `.spec.volumes[]` 明确引用了 ConfigMap `rc-definitely-missing-configmap`。\n2. **ConfigMap 缺失验证**：`kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` 返回 `Error from server (NotFound)`，确认 ConfigMap 不存在。\n3. **Pod 状态验证**：Pod 处于 `Pending` 状态，且容器状态为 `ContainerCreating`，容器 readiness 为 `False`，原因与卷挂载失败有关。\n4. **Events 验证**：Events 明确显示 `MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found`。\n\n结论：  \n该异常由 ConfigMap 缺失直接导致，符合 `pod-volume-mount-failed.md` runbook 中的典型原因。建议创建缺失的 ConfigMap `rc-definitely-missing-configmap` 以恢复 Pod 正常运行。","collection_summary":"计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%；其中真实环境证据 6/6 项，完整度 100%；实际执行工具 6 个，匹配计划 2 个，未规划证据 4 个","plan_total":2,"plan_collected":2,"plan_completeness":1.0,"environment_evidence_total":6,"environment_evidence_collected":6,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":2,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"获取 Pod rc-volume-missing-configmap 的详细信息以验证其配置中的卷引用","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-missing-configmap -n aiops-e2e -o yaml","purpose":"确认 Pod 的 spec.volumes 是否引用了 ConfigMap 'rc-definitely-missing-configmap'","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"确认 ConfigMap 'rc-definitely-missing-configmap' 是否存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e","purpose":"验证 ConfigMap 是否缺失","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/2 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_yaml | 获取 Pod rc-volume-missing-configmap 的详细信息以验证其配... | `kubectl get pod rc-volume-missing-configmap -n aiops-e2e -o yaml` |
   | e2 | critical | ✅ | kubectl_get_by_name | 确认 ConfigMap 'rc-definitely-missing-configmap... | `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (19.8s)
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
   ✅ [汇总总结] 完成 (1m 5.1s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4363 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 51.6s
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
| **证据完整度** | 2/2 (100%) |

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
| 1 | Pod 状态 | kubectl get pod | `STATUS: ContainerCreating` | Pod 无法创建容器 |
| 2 | Events 日志 | kubectl describe pod rc-volume-missing-configmap | `Warning: FailedMount: configmap "rc-definitely-missing-configmap" not found` | 卷挂载失败，因引用的 ConfigMap 不存在 |
| 3 | Pod spec | kubectl get pod -o yaml | `volumeSource: configMap: name: rc-definitely-missing-configmap` | Pod 配置中引用了缺失的 ConfigMap |
| 4 | ConfigMap 状态 | kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e | `Error from server (NotFound): configmaps "rc-definitely-missing-configmap" not found` | 该 ConfigMap 确实不存在 |
| 5 | Pod 标签 | kubectl get pod | `pod_abnormal_type=VolumeMountFailed, rootcause-e2e=true` | 标签确认问题类型 |
| 6 | 上游工具验证 | kubectl_get_by_kind_in_cluster | `abnormal=1, status_counts={'Running': 46}` | 集群中只有一个 Pod 异常，其他均正常 |

### 证据关联分析
- **证据 #1 + #2 印证**：Pod 状态为 ContainerCreating，Events 明确指出卷挂载失败，因 ConfigMap 不存在。
- **证据链**：Pod spec 引用了缺失的 ConfigMap → 卷挂载失败 → 容器无法创建 → Pod 持续处于 ContainerCreating 状态。
- **证据 #4 印证**：ConfigMap 不存在，确认问题根源。

### 缺失证据（无）
| 证据 | 级别 | 影响 |
|------|------|------|
| （无） | （无） | （无） |

---
## 🎯 根因分析
### 因果链
```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                   │
│ ConfigMap 'rc-definitely-missing-configmap' 不存在，导致卷挂载失败           │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                   │
│ 卷引用缺失 → MountVolume.SetUp 失败 → 容器无法创建                           │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                   │
│ Pod rc-volume-missing-configmap 无法创建容器，状态为 ContainerCreating       │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                               │
│ Pod rc-volume-missing-configmap 无法启动，持续处于 ContainerCreating 状态    │
└──────────────────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #2 (Events 明确指出 configmap "rc-definitely-missing-configmap" not found) 和证据 #3 (Pod spec 中引用了该 ConfigMap)，
问题的根本原因是**ConfigMap 'rc-definitely-missing-configmap' 不存在**，导致卷挂载失败，从而阻止容器创建。
**置信度**：高 (95%)
- ✅ Events 明确指出 ConfigMap 不存在
- ✅ Pod spec 中引用了缺失的 ConfigMap
- ✅ kubectl get configmap 确认 ConfigMap 不存在

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 创建缺失的 ConfigMap**
```bash
kubectl create configmap rc-definitely-missing-configmap -n aiops-e2e --from-literal=data="example-content"
```
*依据*：Events 明确指出 ConfigMap 不存在，需手动创建或恢复

**2. [可选] 检查 Pod spec 引用是否正确**
```bash
kubectl get pod rc-volume-missing-configmap -n aiops-e2e -o yaml
```
*目的*：确认引用的 ConfigMap 名称和命名空间是否正确

### 后续优化
1. **自动化校验**：部署前校验 ConfigMap 是否存在
2. **配置管理**：使用 Helm/ArgoCD 等工具统一管理配置资源
3. **监控告警**：监控 Pod 状态变化，及时发现类似问题

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 ConfigMap 存在 | `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` | NAME: rc-definitely-missing-configmap |
| 2. 确认 Pod 运行 | `kubectl get pod rc-volume-missing-configmap -n aiops-e2e` | STATUS: Running |
| 3. 检查容器状态 | `kubectl describe pod rc-volume-missing-configmap -n aiops-e2e` | Events 中不应再出现 FailedMount |

---
## ⚠️ 注意事项
- 如果 ConfigMap 是由 CI/CD 管道部署的，需检查部署流水线是否遗漏了该资源
- 若 ConfigMap 由其他系统管理，需确认权限和命名空间是否正确
- 确保 ConfigMap 的命名与 Pod spec 中引用的完全一致，包括大小写和命名空间

---

---

## 📊 性能统计

├─ 总耗时: 3.9m
├─ 问题定位: 77.0s (33%) ✅
├─ 证据链采集: 69.8s (30%) ✅
├─ 根因分析: 19.8s (9%) ✅
├─ 汇总总结: 65.1s (28%) ✅
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
