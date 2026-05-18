======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: ebe701707ad74988]

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
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-secret-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          33m (x12 over 35m)   kubelet            Error: coul
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME            TYPE     DATA   AGE   LABELS
rc-app-secret   Opaque   1      35m   rootcause-e2e=true
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Secret
name: rc-app-secret
namespace: aiops-e2e
type: Opaque
data_keys: EXISTING_SECRET_KEY
has_dockerconfigjson: False
docker_secret_type_valid: False
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
  "derived_layer": "ConfigError",
  "layers": ["L4"],
  "layer_name": "ConfigError",
  "confidence": 0.95,
  "reasoning": "Pod 'rc-config-secret-key-missing' 处于 'CreateContainerConfigError' 状态，describe 显示 Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret。Secret 'rc-app-secret' 存在，但其 data 中缺少 key 'APP_SECRET_TOKEN'，且该 key 被 Pod 引用。属于典型的配置错误场景，兼容归因 L4。",
  "abnormal_pods": [
    {
      "name": "rc-config-secret-key-missing",
      "namespace": "aiops-e2e",
      "status": "CreateContainerConfigError",
      "reason": "Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret",
      "node": "node1"
    }
  ],
  "abnormal_groups": [
    {
      "pod_abnormal_type": "ConfigError",
      "pod_status_keyword": "CreateContainerConfigError",
      "status_category": "ConfigError",
      "count": 1
    }
  ],
  "key_entities": [
    {
      "kind": "Pod",
      "name": "rc-config-secret-key-missing",
      "namespace": "aiops-e2e"
    },
    {
      "kind": "Secret",
      "name": "rc-app-secret",
      "namespace": "aiops-e2e"
    }
  ],
  "possible_scenarios": [
    "Secret 'rc-app-secret' 缺失 key APP_SECRET_TOKEN，导致容器启动失败。",
    "Pod 配置错误引用了不存在的 Secret key APP_SECRET_TOKEN。",
    "Secret 数据未正确 Base64 编码或 key 名拼写错误。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 49.5s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': "Secret 'rc-app-secret' 缺失 key APP_SECRET_TOKEN，导致容器启动失败。", 'probability': '高', 'reason': 'CreateContainerConfigError + Secret/ConfigMap/env key 缺失'}, {'scenario': 'Pod 配置错误引用了不存在的 Secret key APP_SECRET_TOKEN。', 'probability': '高', 'reason': 'CreateContainerConfigError + Secret/ConfigMap/env key 缺失'}, {'scenario': 'Secret 数据未正确 Base64 编码或 key 名拼写错误。', 'probability': '高', 'reason': 'CreateContainerConfigError + Secret/ConfigMap/env key 缺失'}]
   entities=[{"type": "Pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "rc-app-secret", "namespace": "aiops-e2e"}]
   reasoning=Pod 'rc-config-secret-key-missing' 处于 'CreateContainerConfigError' 状态，describe 显示 Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret。Secret 'rc-app-secret' 存在，但其 data 中缺少 key 'APP_SECRET_TOKEN'，且该 key 被 Pod 引用。属于典型的配置错误场景，兼容归因 L4。
   layer_analysis={"layer": "L4", "derived_layer": "CONFIGERROR", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.95, "reasoning": "Pod 'rc-config-secret-key-missing' 处于 'CreateContainerConfigError' 状态，describe 显示 Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret。Secret 'rc-app-secret' 存在，但其 data 中缺少 key 'APP_SECRET_TOKEN'，且该 key 被 Pod 引用。属于典型的配置错误场景，兼容归因 L4。", "abnormal_pods": [{"name": "rc-config-secret-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}], "pod_status_keyword": "CreateContainerConfigError", "pod_abnormal_type": "ConfigError", "status_category": "ConfigError", "key_entities": [{"type": "Pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "rc-app-secret", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Secret 'rc-app-secret' 缺失 key APP_SECRET_TOKEN，导致容器启动失败。", "probability": "高", "reason": "CreateContainerConfigError + Secret/ConfigMap/env key 缺失"}, {"scenario": "Pod 配置错误引用了不存在的 Secret key APP_SECRET_TOKEN。", "probability": "高", "reason": "CreateContainerConfigError + Secret/ConfigMap/env key 缺失"}, {"scenario": "Secret 数据未正确 Base64 编码或 key 名拼写错误。", "probability": "高", "reason": "CreateContainerConfigError + Secret/ConfigMap/env key 缺失"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-secret-key-missing                        0/1     CreateContainerConfigError   0             35m     172.16.166.188   node1    <none>           <none>            app=rc-config-secret-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/ebe701707ad74988/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/ebe701707ad74988/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/ebe701707ad74988/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME            TYPE     DATA   AGE   LABELS
rc-app-secret   Opaque   1      38m   rootcause-e2e=true
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
关键诊断行:
36m (x12 over 38m)     Warning   Failed           Pod/rc-config-secret-key-missing   Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret
   💭 [证据链采集] 已采集证据：
- Secret `rc-app-secret` 存在，但其 data 中缺少 key `APP_SECRET_TOKEN`。
- Pod `rc-config-secret-key-missing` 的容器配置引用了 `APP_SECRET_TOKEN` key，但该 key 不存在。
- Pod 的事件日志显示错误信息：`Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret`。

未采集证据：无。

冲突证据：无。
   ✅ [证据链采集] 完成 (1m 26.0s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Secret 'rc-app-secret' 是否存在且包含 key 'APP_SECRET_TOKEN'","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get secret rc-app-secret -n aiops-e2e -o yaml","tool_args":{"kind":"Secret","name":"rc-app-secret","namespace":"aiops-e2e"},"purpose":"确认 Secret 是否存在且包含 APP_SECRET_TOKEN key","evidence_type":"config_check","target_scope":"aiops-e2e/rc-app-secret","acceptable_tools":["kubectl_get_by_name","kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e2","description":"验证 Pod 'rc-config-secret-key-missing' 的容器配置是否引用了 Secret key 'APP_SECRET_TOKEN'","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-config-secret-key-missing -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-config-secret-key-missing","namespace":"aiops-e2e"},"purpose":"确认 Pod 的容器配置是否引用了 APP_SECRET_TOKEN key","evidence_type":"config_check","target_scope":"aiops-e2e/rc-config-secret-key-missing","acceptable_tools":["kubectl_get_yaml","kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e3","description":"获取 Pod 'rc-config-secret-key-missing' 的事件日志以确认错误详情","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-secret-key-missing","tool_args":{"kind":"Pod","name":"rc-config-secret-key-missing","namespace":"aiops-e2e"},"purpose":"获取 Pod 的事件日志以确认错误详情","evidence_type":"event_log","target_scope":"aiops-e2e/rc-config-secret-key-missing","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME            TYPE     DATA   AGE   LABELS\nrc-app-secret   Opaque   1      38m   rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ebe701707ad74988/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ebe701707ad74988/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ebe701707ad74988/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-config-secret-key-missing\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T02:31:48Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-config-secret-key-missing, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/runbook=pod-config-error.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=CreateContainerConfigError exitCode=None\n  message: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret\nvolumes:\n- {\"name\": \"kube-api-access-74hmf\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ebe701707ad74988/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ebe701707ad74988/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ebe701707ad74988/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n36m (x12 over 38m)     Warning   Failed           Pod/rc-config-secret-key-missing   Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ebe701707ad74988/tools/003-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ebe701707ad74988/tools/003-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ebe701707ad74988/tools/003-evidence-kubectl_events.summary.txt"}],"llm_analysis":"已采集证据：\n- Secret `rc-app-secret` 存在，但其 data 中缺少 key `APP_SECRET_TOKEN`。\n- Pod `rc-config-secret-key-missing` 的容器配置引用了 `APP_SECRET_TOKEN` key，但该 key 不存在。\n- Pod 的事件日志显示错误信息：`Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret`。\n\n未采集证据：无。\n\n冲突证据：无。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 8 个，匹配计划 3 个，未规划证据 5 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":3,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"验证 Secret 'rc-app-secret' 是否存在且包含 key 'APP_SECRET_TOKEN'","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get secret rc-app-secret -n aiops-e2e -o yaml","purpose":"确认 Secret 是否存在且包含 APP_SECRET_TOKEN key","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"验证 Pod 'rc-config-secret-key-missing' 的容器配置是否引用了 Secret key 'APP_SECRET_TOKEN'","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-config-secret-key-missing -n aiops-e2e -o yaml","purpose":"确认 Pod 的容器配置是否引用了 APP_SECRET_TOKEN key","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取 Pod 'rc-config-secret-key-missing' 的事件日志以确认错误详情","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-secret-key-missing","purpose":"获取 Pod 的事件日志以确认错误详情","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 验证 Secret 'rc-app-secret' 是否存在且包含 key 'APP_SE... | `kubectl get secret rc-app-secret -n aiops-e2e -o yaml` |
   | e2 | critical | ✅ | kubectl_get_yaml | 验证 Pod 'rc-config-secret-key-missing' 的容器配置是否... | `kubectl get pod rc-config-secret-key-missing -n aiops-e2e -o yaml` |
   | e3 | important | ✅ | kubectl_events | 获取 Pod 'rc-config-secret-key-missing' 的事件日志以确... | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-confi...` |

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (8.9s)
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
   ✅ [汇总总结] 完成 (1m 1.9s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3760 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 26.3s
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
| **兼容归因层** | CONFIGERROR - L4 |
| **问题分类** | 配置错误（Secret key 缺失） |
| **置信度** | 高 (95%) |
| **证据完整度** | 3/3 (100%) |

---

## 🔍 现象描述

**用户报告**：  
> 我的集群有什么问题？

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | rc-config-secret-key-missing |
| Namespace | aiops-e2e |
| Secret | rc-app-secret |
| 错误信息 | `Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Secret 数据 | `kubectl get secret rc-app-secret -n aiops-e2e` | `DATA: 1`，`data_keys: EXISTING_SECRET_KEY` | Secret 存在，但缺少 `APP_SECRET_TOKEN` key |
| 2 | Pod 配置 | `kubectl get pod rc-config-secret-key-missing -n aiops-e2e -o yaml` | 引用了 `APP_SECRET_TOKEN` key | Pod 配置中引用了不存在的 key |
| 3 | Pod 事件 | `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` | `Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret` | 容器因缺少 key 无法启动 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 配置中引用了 `APP_SECRET_TOKEN`，但 Secret 中没有该 key → 配置错误
- **证据链**：Pod 引用 key → Secret 缺少 key → 容器启动失败 → Pod 状态 `CreateContainerConfigError`

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Secret 'rc-app-secret' 缺失 key 'APP_SECRET_TOKEN'，但被 Pod 引用 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Pod 引用了不存在的 Secret key，导致容器配置失败                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器启动时找不到 key APP_SECRET_TOKEN，返回 Error                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 'CreateContainerConfigError'，持续失败                 │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Secret 缺少 `APP_SECRET_TOKEN`) 和证据 #2 (Pod 引用了该 key)，问题的根本原因是 **Secret `rc-app-secret` 缺失被引用的 key `APP_SECRET_TOKEN`**，导致容器无法启动，Pod 处于 `CreateContainerConfigError` 状态。

**置信度**：高 (95%)
- ✅ `kubectl describe pod` 明确报错
- ✅ `kubectl get secret` 证实 key 缺失
- ✅ Pod 配置中引用了该 key

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 向 Secret 中添加缺失的 key `APP_SECRET_TOKEN`**
```bash
kubectl patch secret rc-app-secret -n aiops-e2e -p '{"data": {"APP_SECRET_TOKEN": "your-base64-encoded-secret-here"}}'
```
*依据*：Secret 缺少 `APP_SECRET_TOKEN`，必须添加以满足 Pod 配置需求

**2. [可选] 验证 Secret 是否已更新**
```bash
kubectl get secret rc-app-secret -n aiops-e2e -o jsonpath='{.data}'
```
*目的*：确认 `APP_SECRET_TOKEN` 已成功添加

**3. [可选] 重启 Pod 以触发重新拉取 Secret**
```bash
kubectl delete pod rc-config-secret-key-missing -n aiops-e2e
```
*目的*：K8s 会自动重新拉取并启动 Pod

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-config-secret-key-missing -n aiops-e2e` | STATUS: Running |
| 2. 检查容器状态 | `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` | 无 `Error` / `Failed` 事件 |
| 3. 验证 Secret 内容 | `kubectl get secret rc-app-secret -n aiops-e2e -o jsonpath='{.data}'` | 包含 `APP_SECRET_TOKEN` |

---

## ⚠️ 注意事项

- Secret 的 key 必须 Base64 编码
- 如果 Secret 是通过 Helm 或 CI/CD 自动部署的，建议检查部署流程确保 key 不被遗漏
- 为避免此类问题，建议使用 ConfigMap/Secret 的校验机制或使用工具如 Kustomize 管理配置一致性

---

## 📊 性能统计

├─ 总耗时: 4.4m
├─ 问题定位: 109.5s (41%) ✅
├─ 证据链采集: 86.0s (32%) ✅
├─ 根因分析: 8.9s (3%) ✅
├─ 汇总总结: 61.9s (23%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 9 次
```

📋 诊断追踪

- **核心 Runbook**: pod-config-error
- **参考 Runbook**: pod-config-error
- **工具调用**: 9 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
