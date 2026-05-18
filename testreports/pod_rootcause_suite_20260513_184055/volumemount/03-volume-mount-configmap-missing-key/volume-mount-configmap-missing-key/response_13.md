======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: fbaec1e2ab1f4842]

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
2m33s (x21 over 29m)   Warning   FailedMount   Pod/rc-volume-configmap-missing-key   MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent c
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
  "layers": ["L4"],
  "layer_name": "ConfigError",
  "confidence": "high",
  "reasoning": "Pod rc-volume-configmap-missing-key 处于 ContainerCreating 状态，Events 明确指出 configmap references non-existent config key: missing-key。Pod spec 中的 volumes[].configMap 引用了不存在的 key，符合 ConfigMap volume 错误的典型特征。此问题属于配置错误（ConfigError/L4），因为是由于引用了不存在的 ConfigMap key 导致挂载失败。",
  "abnormal_pods": ["rc-volume-configmap-missing-key"],
  "abnormal_groups": ["VolumeMountFailed"],
  "pod_status_keyword": "ContainerCreating",
  "pod_abnormal_type": "VolumeMountFailed",
  "status_category": "VolumeMountFailed",
  "key_entities": {
    "Pod": "rc-volume-configmap-missing-key",
    "ConfigMap": "rc-volume-key-config"
  },
  "possible_scenarios": [
    "ConfigMap rc-volume-key-config 中缺少指定的 key 'missing-key'",
    "Pod 模板错误地引用了不存在的 key，可能是拼写错误或配置错误",
    "ConfigMap rc-volume-key-config 未正确创建或更新"
  ]
}
   ✅ [问题定位] 完成 (31.4s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[]
   entities=[]
   reasoning=Pod rc-volume-configmap-missing-key 处于 ContainerCreating 状态，Events 明确指出 configmap references non-existent config key: missing-key。Pod spec 中的 volumes[].configMap 引用了不存在的 key，符合 ConfigMap volume 错误的典型特征。此问题属于配置错误（ConfigError/L4），因为是由于引用了不存在的 ConfigMap key 导致挂载失败。
   layer_analysis={"layer": "L4", "derived_layer": "", "layers": [], "layer_name": "", "confidence": 0.5, "reasoning": "Pod rc-volume-configmap-missing-key 处于 ContainerCreating 状态，Events 明确指出 configmap references non-existent config key: missing-key。Pod spec 中的 volumes[].configMap 引用了不存在的 key，符合 ConfigMap volume 错误的典型特征。此问题属于配置错误（ConfigError/L4），因为是由于引用了不存在的 ConfigMap key 导致挂载失败。", "abnormal_pods": [{"name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "", "status_category": "", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-configmap-missing-key"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-configmap-missing-key"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-volume-configmap-missing-key                     0/1     ContainerCreating   0                28m     <none>           node1    <none>           <none>            app=rc-volume-configmap-missing-key,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/fbaec1e2ab1f4842/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/fbaec1e2ab1f4842/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/fbaec1e2ab1f4842/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 50%

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
  Warning  FailedMount  5s (x23 over 30m)    kubelet            MountVolume
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
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                   DATA   AGE   LABELS
rc-volume-key-config   1      30m   rootcause-e2e=true
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\"existing-key\":\"present\"}", "stderr": "", "returncode": 0}
   💭 [证据链采集] # 证据结论

## 已采集证据
1. **Pod 的状态和挂载失败的具体原因**:
   - Pod `rc-volume-configmap-missing-key` 处于 `Pending` 状态。
   - 事件表明挂载失败的原因是 `configmap references non-existent config key: missing-key`。

2. **Pod 的 volumes 配置**:
   - Pod 的 `volumes` 配置引用了 `configmap` `rc-volume-key-config`。
   - 该 ConfigMap 存在，但缺少 `missing-key`。

3. **ConfigMap 的内容**:
   - ConfigMap `rc-volume-key-config` 存在，并且包含键 `existing-key`。
   - 但是，缺少 Pod 挂载所需的 `missing-key`。

## 未采集证据
- 无。

## 冲突证据
- 无。
   ✅ [证据链采集] 完成 (1m 33.1s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod rc-volume-configmap-missing-key 的详细描述，确认其状态和挂载失败的详细原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-volume-configmap-missing-key"},"purpose":"确认 Pod 的当前状态和挂载失败的具体原因","evidence_type":"Pod 状态验证","target_scope":"aiops-e2e/rc-volume-configmap-missing-key","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod rc-volume-configmap-missing-key 的 YAML 配置，检查其 volumes 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml","tool_args":{"namespace":"aiops-e2e","name":"rc-volume-configmap-missing-key","output":"yaml"},"purpose":"确认 Pod 的 volumes 配置，特别是 configmap 的引用","evidence_type":"Pod 配置验证","target_scope":"aiops-e2e/rc-volume-configmap-missing-key","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取 ConfigMap 信息，验证引用的 ConfigMap 是否存在及是否包含缺失的 key","level":"important","tool":"kubectl_get_by_name","command":"kubectl get configmap <configmap-name> -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","kind":"configmap","name":"<configmap-name>"},"purpose":"确认引用的 ConfigMap 是否存在及是否包含缺失的 key","evidence_type":"ConfigMap 存在性验证","target_scope":"aiops-e2e/<configmap-name>","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-configmap-missing-key\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  5s (x23 over 30m)    kubelet            MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n  Warning  FailedMount  10m (x7 over 28m)    kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-xz5tn]: timed out waiting for the condition\n  Warning  FailedMount  8m11s (x3 over 19m)  kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[kube-api-access-xz5tn config-volume]: timed out waiting for the condition\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed\n    State:          Waiting\n      Reason:       ContainerCreating","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fbaec1e2ab1f4842/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fbaec1e2ab1f4842/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fbaec1e2ab1f4842/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-volume-configmap-missing-key\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T14:27:19Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-volume-configmap-missing-key, pod_abnormal_type=VolumeMountFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-volume-mount-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"config-volume\", \"configMap\": \"rc-volume-key-config\"}\n- {\"name\": \"kube-api-access-xz5tn\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fbaec1e2ab1f4842/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fbaec1e2ab1f4842/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fbaec1e2ab1f4842/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                   DATA   AGE   LABELS\nrc-volume-key-config   1      30m   rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fbaec1e2ab1f4842/tools/003-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fbaec1e2ab1f4842/tools/003-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fbaec1e2ab1f4842/tools/003-evidence-kubectl_get_by_name.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\\"existing-key\\\":\\\"present\\\"}\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fbaec1e2ab1f4842/tools/004-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fbaec1e2ab1f4842/tools/004-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fbaec1e2ab1f4842/tools/004-evidence-run_bash_command.summary.txt"}],"llm_analysis":"# 证据结论\n\n## 已采集证据\n1. **Pod 的状态和挂载失败的具体原因**:\n   - Pod `rc-volume-configmap-missing-key` 处于 `Pending` 状态。\n   - 事件表明挂载失败的原因是 `configmap references non-existent config key: missing-key`。\n\n2. **Pod 的 volumes 配置**:\n   - Pod 的 `volumes` 配置引用了 `configmap` `rc-volume-key-config`。\n   - 该 ConfigMap 存在，但缺少 `missing-key`。\n\n3. **ConfigMap 的内容**:\n   - ConfigMap `rc-volume-key-config` 存在，并且包含键 `existing-key`。\n   - 但是，缺少 Pod 挂载所需的 `missing-key`。\n\n## 未采集证据\n- 无。\n\n## 冲突证据\n- 无。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 8 个，匹配计划 3 个，未规划证据 5 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":3,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"验证 Pod rc-volume-configmap-missing-key 的详细描述，确认其状态和挂载失败的详细原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e","purpose":"确认 Pod 的当前状态和挂载失败的具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod rc-volume-configmap-missing-key 的 YAML 配置，检查其 volumes 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml","purpose":"确认 Pod 的 volumes 配置，特别是 configmap 的引用","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取 ConfigMap 信息，验证引用的 ConfigMap 是否存在及是否包含缺失的 key","level":"important","tool":"kubectl_get_by_name","command":"kubectl get configmap <configmap-name> -n aiops-e2e","purpose":"确认引用的 ConfigMap 是否存在及是否包含缺失的 key","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证 Pod rc-volume-configmap-missing-key 的详细描述，... | `kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_get_yaml | 获取 Pod rc-volume-configmap-missing-key 的 YAML... | `kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml` |
   | e3 | important | ✅ | kubectl_get_by_name | 获取 ConfigMap 信息，验证引用的 ConfigMap 是否存在及是否包含缺失的 key | `kubectl get configmap <configmap-name> -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (30.4s)
   📤 → 下游数据: root_cause=Pod rc-volume-configmap-missing-key 处于 ContainerCreating 状态，Events 明确指出 configmap references non-existent config key: missing-key。Pod spec 中的 volumes[].configMap 引用了不存在的 key，符合 ConfigMap volume 错误的典型特征。此问题属于配置错误（ConfigError/L4），因为是由于引用了不存在的 ConfigMap key 导致挂载失败。
   confidence=90%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [], "causal_chain": {}, "root_cause": "Pod rc-volume-configmap-missing-key 处于 ContainerCreating 状态，Events 明确指出 configmap references non-existent config key: missing-key。Pod spec 中的 volumes[].configMap 引用了不存在的 key，符合 ConfigMap volume 错误的典型特征。此问题属于配置错误（ConfigError/L4），因为是由于引用了不存在的 ConfigMap key 导致挂载失败。", "root_cause_summary": "Pod rc-volume-configmap-missing-key 处于 ContainerCreating 状态，Events 明确指出 configmap references non-existent config key: missing-key。Pod spec 中的 volumes[].configMap 引用了不存在的 key，符合 ConfigMap volume 错误的典型特征。此问题属于配置错误（ConfigError/L4），因为是由于引用了不存在的 ConfigMap key 导致挂载失败。", "confidence": 0.9, "confidence_reason": "", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [], "limitations": "无", "llm_raw_analysis": "根因分析：\n\n1. **现象**：Pod rc-volume-configmap-missing-key 处于 ContainerCreating 状态，且多次出现 FailedMount 事件。\n2. **关键证据**：\n   - Events 明确指出 `MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key`。\n   - Pod 的 YAML 配置显示其 `volumes` 配置引用了 ConfigMap `rc-volume-key-config`。\n   - ConfigMap `rc-volume-key-config` 存在，但缺少 `missing-key`。\n3. **分析**：\n   - Pod 无法启动，因为其引用的 ConfigMap 缺少必要的 key `missing-key`。\n   - 这导致 Kubernetes 无法正确挂载 ConfigMap 到 Pod，从而导致 Container\n... 截断，原始 787 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-volume-configmap-missing-key 处于 ContainerCreating 状态，Events 明确指出 configmap references non-existent config key: missing-key。Pod spec 中的 volumes[...
   置信度: 90%

📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (2m 9.1s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4375 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 44.1s
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
| **兼容归因层** | L4 - ConfigError |
| **问题分类** | ConfigMap key 不存在导致 VolumeMountFailed |
| **置信度** | 高 (90%) |
| **证据完整度** | 3/3 (100%) |

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
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: ContainerCreating` | Pod 无法完成容器创建 |
| 2 | Pod 事件 | `kubectl events` | `Warning FailedMount: configmap references non-existent config key: missing-key` | 明确指出 ConfigMap key 不存在 |
| 3 | Pod YAML 配置 | `kubectl get pod -o yaml` | `volumes[].configMap` 引用了 `missing-key` | 说明是 Pod spec 中的配置错误 |
| 4 | ConfigMap 验证 | `kubectl get configmap rc-volume-key-config` | `DATA: 1, 仅包含 existing-key` | 不存在 `missing-key` |
| 5 | Pod 详细描述 | `kubectl describe pod rc-volume-configmap-missing-key` | `MountVolume.SetUp failed for volume "config-volume"` | 挂载失败，因引用了不存在的 key |
| 6 | 其他工具验证 | `kubectl get by kind in cluster` | `status: Pending, reason: ContainerCreating` | Pod 无法正常启动 |
| 7 | Runbook 验证 | `fetch_runbook` | 匹配到 `pod-volume-mount-failed.md` | 说明是典型的 VolumeMountFailed 情况 |

### 证据关联分析

- **证据 #2 + #3 印证**：Events 明确指出 ConfigMap key 不存在，同时 Pod spec 中确实引用了该 key。
- **证据链**：Pod spec 中引用了不存在的 ConfigMap key → 挂载失败 → Pod 无法启动 → 状态为 `ContainerCreating`。
- **证据 #4 印证**：ConfigMap `rc-volume-key-config` 中确实没有 `missing-key`，确认引用错误。

### 缺失证据（无）

无缺失证据。

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod spec 中引用了不存在的 ConfigMap key: missing-key            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Kubernetes 无法挂载不存在的 ConfigMap key → 挂载失败            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ MountVolume.SetUp failed for volume "config-volume"             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 ContainerCreating，Events 显示 FailedMount 错误      │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2（Events 明确指出 `configmap references non-existent config key: missing-key`）和证据 #3（Pod spec 中引用了 `missing-key`）以及证据 #4（ConfigMap 中确实没有该 key），问题的根本原因是 **Pod spec 中引用了不存在的 ConfigMap key**，导致卷挂载失败，Pod 无法启动。

**置信度**：高 (90%)
- ✅ Events 明确提示 ConfigMap key 不存在
- ✅ Pod spec 中确实引用了该 key
- ✅ ConfigMap 验证确认该 key 不存在

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 修复 Pod spec 中的 ConfigMap key 引用**
```bash
# 请手动修改 Pod 或 Deployment YAML，将 missing-key 替换为 existing-key，或创建包含 missing-key 的 ConfigMap

# 示例：更新 Deployment
kubectl edit deployment/<deployment-name> -n aiops-e2e
```
*依据*：当前 ConfigMap 中不存在 `missing-key`，需要确保引用的 key 存在。

**2. [可选] 创建缺失的 ConfigMap key**
```bash
kubectl create configmap rc-volume-key-config \
  --from-literal=existing-key=present \
  --from-literal=missing-key=new-value \
  -n aiops-e2e
```
*依据*：如果需要保留 `missing-key`，可创建它并更新 ConfigMap。

### 后续优化

1. **配置校验**：在 CI/CD 流程中加入 ConfigMap key 存在性校验，避免部署失败
2. **文档记录**：记录 ConfigMap 的结构和用途，方便维护
3. **监控告警**：监控 Pod 启动失败事件（如 `FailedMount`），及时发现配置错误

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e` | STATUS: Running |
| 2. 检查卷挂载状态 | `kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e` | No FailedMount events |
| 3. 检查 ConfigMap 内容 | `kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml` | 包含 `missing-key`（如果创建了） |

---

## ⚠️ 注意事项

- 确保所有引用 ConfigMap 的 Pod 中的 key 存在，避免类似问题
- 如果是 Deployment 管理的 Pod，修改 Deployment 后需等待 Pod 重建
- 如果 ConfigMap 是共享的，修改前请确认不影响其他 Pod

---

## 📊 性能统计

├─ 总耗时: 4.7m
├─ 问题定位: 31.4s (11%) ✅
├─ 证据链采集: 93.1s (33%) ✅
├─ 根因分析: 30.4s (11%) ✅
├─ 汇总总结: 129.1s (45%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 9 次
```

📋 诊断追踪

- **核心 Runbook**: pod-volume-mount-failed
- **参考 Runbook**: pod-volume-mount-failed
- **工具调用**: 9 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
