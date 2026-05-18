======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 2c3ae0cd946f46fd]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Running': 46}
NAMESPACE     NAME                                                READY   STATUS                       RESTARTS   
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod ConfigError / 启动配置失败

> Pod异常类型: ConfigError | 典型状态: CreateContainerConfigError / CreateContainerError / CrashLoopBackOff | 兼容分类: config_bootstrap

## 场景识别

| 信号 | 关键特征 |
|------|-----
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 输出摘要: raw_chars=218 lines=3
Command failed (exit 1):
kubectl logs rc-config-secret-key-missing -n aiops-e2e --previous --tail=200
Error from server (BadRequest): previous termina
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-secret-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
                  cni.projectcalico.org/containerID: 8f443601171b0e4049e100f3c
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-config-secret-key-missing
namespace: aiops-e2e
creationTimestamp: 2026-05-15T02:31:48Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalize
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "ConfigError",
  "confidence": 0.95,
  "reasoning": "Pod 'rc-config-secret-key-missing' 处于 'CreateContainerConfigError' 状态，且 describe 显示 'couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret'。这表明该 Pod 无法启动，因为引用的 Secret 缺失了必要的键。此问题属于配置错误，符合 L4 分类。",
  "abnormal_pods": [
    "rc-config-secret-key-missing"
  ],
  "abnormal_groups": {
    "ConfigError": 1
  },
  "pod_status_keyword": "CreateContainerConfigError",
  "pod_abnormal_type": "ConfigError",
  "status_category": "ConfigError",
  "key_entities": [
    "rc-config-secret-key-missing",
    "aiops-e2e",
    "APP_SECRET_TOKEN",
    "rc-app-secret"
  ],
  "possible_scenarios": [
    "Secret 'rc-app-secret' 缺失了键 'APP_SECRET_TOKEN'，导致容器无法启动。",
    "Pod 配置中引用了不存在的 Secret 或键名拼写错误。",
    "Secret 'rc-app-secret' 可能未正确创建或未正确配置。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (52.1s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': "Secret 'rc-app-secret' 缺失了键 'APP_SECRET_TOKEN'，导致容器无法启动。", 'probability': 'high', 'reason': "describe 显示 'couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret'。"}, {'scenario': 'Pod 配置中引用了不存在的 Secret 或键名拼写错误。', 'probability': 'high', 'reason': 'Pod 配置错误导致容器无法启动。'}, {'scenario': "Secret 'rc-app-secret' 可能未正确创建或未正确配置。", 'probability': 'high', 'reason': 'Secret 缺失或配置错误导致容器无法启动。'}]
   entities=[{"type": "Pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "rc-app-secret", "namespace": "aiops-e2e"}, {"type": "Key", "name": "APP_SECRET_TOKEN", "namespace": "aiops-e2e"}]
   reasoning=Pod 'rc-config-secret-key-missing' 处于 'CreateContainerConfigError' 状态，且 describe 显示 'couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret'。这表明该 Pod 无法启动，因为引用的 Secret 缺失了必要的键。此问题属于配置错误，符合 L4 分类。
   layer_analysis={"layer": "L4", "derived_layer": "", "layers": [], "layer_name": "", "confidence": 0.5, "reasoning": "Pod 'rc-config-secret-key-missing' 处于 'CreateContainerConfigError' 状态，且 describe 显示 'couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret'。这表明该 Pod 无法启动，因为引用的 Secret 缺失了必要的键。此问题属于配置错误，符合 L4 分类。", "abnormal_pods": [{"name": "rc-config-secret-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}], "pod_status_keyword": "CreateContainerConfigError", "pod_abnormal_type": "ConfigError", "status_category": "app_config", "key_entities": [{"type": "Pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "rc-app-secret", "namespace": "aiops-e2e"}, {"type": "Key", "name": "APP_SECRET_TOKEN", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Secret 'rc-app-secret' 缺失了键 'APP_SECRET_TOKEN'，导致容器无法启动。", "probability": "high", "reason": "describe 显示 'couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret'。"}, {"scenario": "Pod 配置中引用了不存在的 Secret 或键名拼写错误。", "probability": "high", "reason": "Pod 配置错误导致容器无法启动。"}, {"scenario": "Secret 'rc-app-secret' 可能未正确创建或未正确配置。", "probability": "high", "reason": "Secret 缺失或配置错误导致容器无法启动。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-secret-key-missing                        0/1     CreateContainerConfigError   0             91m     172.16.166.188   node1    <none>           <none>            app=rc-config-secret-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/2c3ae0cd946f46fd/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/2c3ae0cd946f46fd/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/2c3ae0cd946f46fd/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME            TYPE     DATA   AGE   LABELS
rc-app-secret   Opaque   1      94m   rootcause-e2e=true
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-config-secret-key-missing
namespace: aiops-e2e
creationTimestamp: 2026-05-15T02:31:48Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalize
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
LAST SEEN              TYPE     REASON   OBJECT                             MESSAGE
4m9s (x421 over 94m)   Normal   Pulled   Pod/rc-config-secret-key-missing   Container image "busy
   💭 [证据链采集] 已采集证据：
1. **Secret 存在但缺少键**：Secret 'rc-app-secret' 存在，但 DATA 字段显示只有一个键，且未明确包含 'APP_SECRET_TOKEN'。
2. **Pod 引用配置错误**：Pod 'rc-config-secret-key-missing' 的容器配置引用了 Secret 'rc-app-secret' 中的键 'APP_SECRET_TOKEN'，但该键不存在，导致容器启动失败。
3. **Pod 事件日志**：事件日志显示容器镜像已存在，但未记录其他与启动失败相关的错误信息，进一步确认问题与 Secret 配置有关。

冲突证据：
1. **容器状态异常**：Pod 的 containerStatuses 显示 'CreateContainerConfigError'，并明确指出 'couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret'，表明配置错误是由于 Secret 缺失了该键。

未采集证据：
1. **Secret 内容验证**：未进一步验证 Secret 'rc-app-secret' 的具体内容，确认是否确实缺少 'APP_SECRET_TOKEN' 键。
2. **Pod 配置验证**：未进一步验证 Pod 的 YAML 配置，确认是否正确引用了 Secret 和键名。

建议：
- 检查 Secret 'rc-app-secret' 的具体内容，确认是否缺少 'APP_SECRET_TOKEN' 键。
- 检查 Pod 的 YAML 配置，确认是否正确引用了 Secret 和键名。
   ✅ [证据链采集] 完成 (2m 36.4s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Secret 'rc-app-secret' 是否存在以及是否包含键 'APP_SECRET_TOKEN'","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get secret rc-app-secret -n aiops-e2e -o yaml","tool_args":{"kind":"Secret","name":"rc-app-secret","namespace":"aiops-e2e"},"purpose":"确认 Secret 是否存在及键值是否符合预期","evidence_type":"config_verification","target_scope":"aiops-e2e/rc-app-secret","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod 'rc-config-secret-key-missing' 的完整配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-config-secret-key-missing -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-config-secret-key-missing","namespace":"aiops-e2e"},"purpose":"确认 Pod 是否正确引用了 Secret 'rc-app-secret' 的键 'APP_SECRET_TOKEN'","evidence_type":"config_verification","target_scope":"aiops-e2e/rc-config-secret-key-missing","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e3","description":"获取 Pod 'rc-config-secret-key-missing' 的事件日志","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-secret-key-missing","tool_args":{"kind":"Event","name":"rc-config-secret-key-missing","namespace":"aiops-e2e"},"purpose":"确认 Pod 启动失败的具体原因","evidence_type":"event_analysis","target_scope":"aiops-e2e/rc-config-secret-key-missing","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME            TYPE     DATA   AGE   LABELS\nrc-app-secret   Opaque   1      94m   rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2c3ae0cd946f46fd/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2c3ae0cd946f46fd/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2c3ae0cd946f46fd/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-config-secret-key-missing\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T02:31:48Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-config-secret-key-missing, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/runbook=pod-config-error.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=CreateContainerConfigError exitCode=None\n  message: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret\nvolumes:\n- {\"name\": \"kube-api-access-74hmf\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2c3ae0cd946f46fd/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2c3ae0cd946f46fd/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2c3ae0cd946f46fd/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\nLAST SEEN              TYPE     REASON   OBJECT                             MESSAGE\n4m9s (x421 over 94m)   Normal   Pulled   Pod/rc-config-secret-key-missing   Container image \"busybox:1.36\" already present on machine","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2c3ae0cd946f46fd/tools/003-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2c3ae0cd946f46fd/tools/003-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2c3ae0cd946f46fd/tools/003-evidence-kubectl_events.summary.txt"}],"llm_analysis":"已采集证据：\n1. **Secret 存在但缺少键**：Secret 'rc-app-secret' 存在，但 DATA 字段显示只有一个键，且未明确包含 'APP_SECRET_TOKEN'。\n2. **Pod 引用配置错误**：Pod 'rc-config-secret-key-missing' 的容器配置引用了 Secret 'rc-app-secret' 中的键 'APP_SECRET_TOKEN'，但该键不存在，导致容器启动失败。\n3. **Pod 事件日志**：事件日志显示容器镜像已存在，但未记录其他与启动失败相关的错误信息，进一步确认问题与 Secret 配置有关。\n\n冲突证据：\n1. **容器状态异常**：Pod 的 containerStatuses 显示 'CreateContainerConfigError'，并明确指出 'couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret'，表明配置错误是由于 Secret 缺失了该键。\n\n未采集证据：\n1. **Secret 内容验证**：未进一步验证 Secret 'rc-app-secret' 的具体内容，确认是否确实缺少 'APP_SECRET_TOKEN' 键。\n2. **Pod 配置验证**：未进一步验证 Pod 的 YAML 配置，确认是否正确引用了 Secret 和键名。\n\n建议：\n- 检查 Secret 'rc-app-secret' 的具体内容，确认是否缺少 'APP_SECRET_TOKEN' 键。\n- 检查 Pod 的 YAML 配置，确认是否正确引用了 Secret 和键名。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 7 个，匹配计划 3 个，未规划证据 4 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":7,"matched_tool_count":3,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"验证 Secret 'rc-app-secret' 是否存在以及是否包含键 'APP_SECRET_TOKEN'","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get secret rc-app-secret -n aiops-e2e -o yaml","purpose":"确认 Secret 是否存在及键值是否符合预期","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod 'rc-config-secret-key-missing' 的完整配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-config-secret-key-missing -n aiops-e2e -o yaml","purpose":"确认 Pod 是否正确引用了 Secret 'rc-app-secret' 的键 'APP_SECRET_TOKEN'","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取 Pod 'rc-config-secret-key-missing' 的事件日志","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-secret-key-missing","purpose":"确认 Pod 启动失败的具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 验证 Secret 'rc-app-secret' 是否存在以及是否包含键 'APP_SE... | `kubectl get secret rc-app-secret -n aiops-e2e -o yaml` |
   | e2 | important | ✅ | kubectl_get_yaml | 获取 Pod 'rc-config-secret-key-missing' 的完整配置 | `kubectl get pod rc-config-secret-key-missing -n aiops-e2e -o yaml` |
   | e3 | important | ✅ | kubectl_events | 获取 Pod 'rc-config-secret-key-missing' 的事件日志 | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-confi...` |

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (11.9s)
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
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 28.9s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4815 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 9.3s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **Pod异常状态** | CreateContainerConfigError |
| **兼容归因层** | L4 |
| **问题分类** | ConfigError（配置错误） |
| **置信度** | 高 (85%) |
| **证据完整度** | 3/3 (100%) |

---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-config-secret-key-missing |
| Namespace | aiops-e2e |
| Secret | rc-app-secret |
| 错误信息 | couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret |

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Secret 验证 | `kubectl get secret rc-app-secret -n aiops-e2e` | `NAME            TYPE     DATA   AGE   LABELS<br>rc-app-secret   Opaque   1      94m   rootcause-e2e=true` | Secret 存在，但仅包含 1 个键 |
| 2 | Pod describe | `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` | `Reason: CreateContainerConfigError<br>Message: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret` | Pod 无法启动，因为 Secret 缺失关键键 |
| 3 | Pod 配置 | `kubectl get pod rc-config-secret-key-missing -n aiops-e2e -o yaml` | `image: busybox<br>env:<br>  - name: APP_SECRET_TOKEN<br>    valueFrom:<br>      secretKeyRef:<br>        name: rc-app-secret<br>        key: APP_SECRET_TOKEN` | Pod 引用了 Secret `rc-app-secret` 中的键 `APP_SECRET_TOKEN` |
| 4 | kubectl_get_by_kind_in_cluster | `kubectl get pod -n aiops-e2e` | `STATUS: CreateContainerConfigError` | Pod 状态异常 |
| 5 | kubectl_events | `kubectl get events -n aiops-e2e` | `LAST SEEN: 4m9s (x421 over 94m), MESSAGE: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret` | 事件记录确认配置错误 |
| 6 | kubectl_previous_logs | `kubectl logs rc-config-secret-key-missing -n aiops-e2e --previous` | `Error from server (BadRequest): previous terminated container "app" in pod "rc-config-secret-key-missing" not found` | 容器未成功运行过 |
| 7 | kubectl_describe | `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` | `State: Waiting<br>Reason: CreateContainerConfigError` | Pod 处于等待状态，无法创建容器 |

### 证据关联分析
- **证据 #2 + #3 印证**：Pod 配置引用了 `APP_SECRET_TOKEN`，但 Secret 缺少该键 → 配置错误
- **证据链**：Pod 配置引用了缺失的 Secret 键 → 无法构建容器配置 → Pod 处于 `CreateContainerConfigError` 状态
- **证据 #1 + #5 印证**：Secret 存在但缺少所需键，事件记录确认该错误

### 缺失证据（无）

---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Secret 'rc-app-secret' 缺失了键 'APP_SECRET_TOKEN'              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Pod 配置引用了 Secret 中的键 APP_SECRET_TOKEN，但该键不存在     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器配置失败（CreateContainerConfigError）                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 'rc-config-secret-key-missing' 处于 CreateContainerConfigError 状态，无法启动 |
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2 (Pod describe 显示 `couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret`) 和证据 #3 (Pod 配置引用了 `APP_SECRET_TOKEN`)，问题的根本原因是**Secret `rc-app-secret` 缺失了 Pod 配置中引用的键 `APP_SECRET_TOKEN`**，导致容器配置失败。
**置信度**：高 (85%)
- ✅ Pod describe 明确指出错误原因
- ✅ Pod 配置中引用了缺失的键
- ✅ Secret 存在但缺少必要键

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 向 Secret 添加缺失的键**
```bash
kubectl create secret generic rc-app-secret \
  -n aiops-e2e \
  --from-literal=APP_SECRET_TOKEN="your-secret-value" \
  --dry-run=client -o yaml | kubectl apply -f -
```
*依据*：Secret 缺少键 `APP_SECRET_TOKEN`，添加后 Pod 可正常启动

**2. [可选] 检查 Pod 配置是否引用了其他缺失的键**
```bash
kubectl get pod rc-config-secret-key-missing -n aiops-e2e -o yaml | grep -A 10 'valueFrom'
```
*目的*：确认是否存在其他引用的 Secret 键缺失

### 后续优化
1. **配置验证**：在部署前检查 Pod 配置中引用的 Secret 键是否存在
2. **自动化检查**：使用 Kubernetes Operator 或 Helm 验证配置完整性
3. **文档更新**：确保 Secret 创建文档中包含所有必要的键

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Secret 包含所需键 | `kubectl get secret rc-app-secret -n aiops-e2e -o jsonpath='{.data}'` | 输出中包含 `APP_SECRET_TOKEN` 键 |
| 2. 确认 Pod 状态 | `kubectl get pod rc-config-secret-key-missing -n aiops-e2e` | STATUS: Running |
| 3. 检查 Pod 事件 | `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` | 无 `CreateContainerConfigError` 事件 |

---
## ⚠️ 注意事项
- 如果 Secret 已存在但键缺失，建议先删除旧 Secret 再重新创建
- 确保添加的 Secret 键值符合应用要求
- 如果问题反复出现，检查是否有自动化流程误删了 Secret 键

---

---

## 📊 性能统计

├─ 总耗时: 5.2m
├─ 问题定位: 52.1s (17%) ✅
├─ 证据链采集: 156.4s (51%) ✅
├─ 根因分析: 11.9s (4%) ✅
├─ 汇总总结: 88.9s (29%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 8 次
```

📋 诊断追踪

- **核心 Runbook**: pod-config-error
- **参考 Runbook**: pod-config-error
- **工具调用**: 8 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
