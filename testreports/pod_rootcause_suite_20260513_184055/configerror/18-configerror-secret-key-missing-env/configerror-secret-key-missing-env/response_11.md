======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 7f28c80afa1e4fd3]

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
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                           READY   STATUS                       RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-config-secret-key-missing   0/1     CreateCon
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 输出摘要: raw_chars=218 lines=3
Command failed (exit 1):
kubectl logs rc-config-secret-key-missing -n aiops-e2e --previous --tail=200
Error from server (BadRequest): previous termina
   💭 [问题定位] 调用工具: kubectl_container_previous_logs
   💭 [问题定位] 工具结果: kubectl_container_previous_logs (success)
      📄 kubectl_container_previous_logs 输出摘要: raw_chars=225 lines=3
Command failed (exit 1):
kubectl logs rc-config-secret-key-missing -c app -n aiops-e2e --previous --tail=200
Error from server (BadRequest):
   💭 [问题定位] 调用工具: kubectl_logs
   💭 [问题定位] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 输出摘要: raw_chars=225 lines=3
Command failed (exit 1):
kubectl logs rc-config-secret-key-missing -n aiops-e2e --tail=200
Error from server (BadRequest): container "app" in pod "rc-config-se
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-secret-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          18m (x12 over 20m)  kubelet            Error: could
   💭 [问题定位] 调用工具: kubectl_get_by_name
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (37.0s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'Secret 键缺失', 'probability': '高', 'reason': 'Pod 的事件描述明确指出找不到 Secret 中的 key APP_SECRET_TOKEN。'}, {'scenario': 'ConfigMap 或 Secret 引用错误', 'probability': '中', 'reason': 'Pod 配置可能引用了错误的 ConfigMap 或 Secret 名称，或键名拼写错误。'}]
   entities=[{"type": "Pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}]
   reasoning=当前异常 Pod 状态为 CreateContainerConfigError，且标签中 pod_abnormal_type=ConfigError，符合 L4 的判定规则。关键证据：Pod 状态为 CreateContainerConfigError，事件描述指出找不到 Secret 中的 key APP_SECRET_TOKEN，属于配置错误。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "", "confidence": 0.5, "reasoning": "当前异常 Pod 状态为 CreateContainerConfigError，且标签中 pod_abnormal_type=ConfigError，符合 L4 的判定规则。关键证据：Pod 状态为 CreateContainerConfigError，事件描述指出找不到 Secret 中的 key APP_SECRET_TOKEN，属于配置错误。", "abnormal_pods": [{"name": "rc-config-secret-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}], "pod_status_keyword": "CreateContainerConfigError", "pod_abnormal_type": "ConfigError", "status_category": "app_config", "key_entities": [{"type": "Pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Secret 键缺失", "probability": "高", "reason": "Pod 的事件描述明确指出找不到 Secret 中的 key APP_SECRET_TOKEN。"}, {"scenario": "ConfigMap 或 Secret 引用错误", "probability": "中", "reason": "Pod 配置可能引用了错误的 ConfigMap 或 Secret 名称，或键名拼写错误。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-secret-key-missing                        0/1     CreateContainerConfigError   0             19m     172.16.166.188   node1    <none>           <none>            app=rc-config-secret-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/7f28c80afa1e4fd3/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/7f28c80afa1e4fd3/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/7f28c80afa1e4fd3/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                           READY   STATUS                       RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-config-secret-key-missing   0/1     CreateCon
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (1m 38.5s)
   📤 → 下游数据: evidence_items=7/10
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod rc-config-secret-key-missing 是否仍存在且处于异常状态","level":"important","tool":"kubectl_get_by_name","command":"kubectl get pod rc-config-secret-key-missing -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-config-secret-key-missing","namespace":"aiops-e2e"},"purpose":"确认目标 Pod 当前状态是否仍为 CreateContainerConfigError","evidence_type":"status_verification","target_scope":"aiops-e2e/rc-config-secret-key-missing","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e2","description":"验证 Pod rc-config-secret-key-missing 的详细事件记录","level":"critical","tool":"kubectl_events","command":"kubectl get events --field-selector=involvedObject.name=rc-config-secret-key-missing -n aiops-e2e","tool_args":{"kind":"Event","field_selector":"involvedObject.name=rc-config-secret-key-missing","namespace":"aiops-e2e"},"purpose":"获取 Pod 的事件记录，验证是否有 Secret 键缺失相关的错误信息","evidence_type":"event_verification","target_scope":"aiops-e2e/rc-config-secret-key-missing","acceptable_tools":["kubectl_events"],"counts_for_completeness":true},{"id":"e3","description":"验证 Secret aiops-e2e/rc-app-secret 是否存在并包含 APP_SECRET_TOKEN 键","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get secret rc-app-secret -n aiops-e2e -o jsonpath='{.data}'","tool_args":{"kind":"Secret","name":"rc-app-secret","namespace":"aiops-e2e","output_format":"jsonpath={.data}"},"purpose":"确认 Secret 是否存在并包含 APP_SECRET_TOKEN 键，验证配置错误的具体原因","evidence_type":"config_verification","target_scope":"aiops-e2e/rc-app-secret","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e4","description":"验证 Pod rc-config-secret-key-missing 的 YAML 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-config-secret-key-missing -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-config-secret-key-missing","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"获取 Pod 的完整 YAML 配置，检查其是否引用了错误的 Secret 或键名","evidence_type":"config_verification","target_scope":"aiops-e2e/rc-config-secret-key-missing","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                           READY   STATUS                       RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-config-secret-key-missing   0/1     CreateContainerConfigError   0          22m   172.16.166.188   node1   <none>           <none>            app=rc-config-secret-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/7f28c80afa1e4fd3/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/7f28c80afa1e4fd3/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/7f28c80afa1e4fd3/tools/001-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 4 项，实际采集 1 项，未采集 3 项，完整度 25%；其中真实环境证据 7/10 项，完整度 70%；实际执行工具 6 个，匹配计划 1 个，未规划证据 5 个","plan_total":4,"plan_collected":1,"plan_completeness":0.25,"environment_evidence_total":10,"environment_evidence_collected":7,"environment_evidence_completeness":0.7,"executed_tool_count":6,"matched_tool_count":1,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"验证 Pod rc-config-secret-key-missing 是否仍存在且处于异常状态","level":"important","tool":"kubectl_get_by_name","command":"kubectl get pod rc-config-secret-key-missing -n aiops-e2e","purpose":"确认目标 Pod 当前状态是否仍为 CreateContainerConfigError","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"验证 Pod rc-config-secret-key-missing 的详细事件记录","level":"critical","tool":"kubectl_events","command":"kubectl get events --field-selector=involvedObject.name=rc-config-secret-key-missing -n aiops-e2e","purpose":"获取 Pod 的事件记录，验证是否有 Secret 键缺失相关的错误信息","collected":false,"source":"planned","outcome":"unknown"},{"id":"e3","description":"验证 Secret aiops-e2e/rc-app-secret 是否存在并包含 APP_SECRET_TOKEN 键","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get secret rc-app-secret -n aiops-e2e -o jsonpath='{.data}'","purpose":"确认 Secret 是否存在并包含 APP_SECRET_TOKEN 键，验证配置错误的具体原因","collected":false,"source":"planned","outcome":"unknown"},{"id":"e4","description":"验证 Pod rc-config-secret-key-missing 的 YAML 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-config-secret-key-missing -n aiops-e2e -o yaml","purpose":"获取 Pod 的完整 YAML 配置，检查其是否引用了错误的 Secret 或键名","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_container_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e2(验证 Pod rc-config-secret-key-missing 的详细事件记录): 已规划但工具执行失败或无匹配结果","e3(验证 Secret aiops-e2e/rc-app-secret 是否存在并包含 APP_SECRET_TOKEN 键): 已规划但工具执行失败或无匹配结果","e4(验证 Pod rc-config-secret-key-missing 的 YAML 配置): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/4 项, 完整度: 70%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | important | ✅ | kubectl_get_by_name | 验证 Pod rc-config-secret-key-missing 是否仍存在且处于异常状态 | `kubectl get pod rc-config-secret-key-missing -n aiops-e2e` |
   | e2 | critical | ❌ | kubectl_events | 验证 Pod rc-config-secret-key-missing 的详细事件记录 | `kubectl get events --field-selector=involvedObject.name=rc-config-secret-key-...` |
   | e3 | critical | ❌ | kubectl_get_by_name | 验证 Secret aiops-e2e/rc-app-secret 是否存在并包含 APP... | `kubectl get secret rc-app-secret -n aiops-e2e -o jsonpath='{.data}'` |
   | e4 | important | ❌ | kubectl_get_yaml | 验证 Pod rc-config-secret-key-missing 的 YAML 配置 | `kubectl get pod rc-config-secret-key-missing -n aiops-e2e -o yaml` |

   ⚠️ 未采集原因:
   - e2(验证 Pod rc-config-secret-key-missing 的详细事件记录): 已规划但工具执行失败或无匹配结果
   - e3(验证 Secret aiops-e2e/rc-app-secret 是否存在并包含 APP_SECRET_TOKEN 键): 已规划但工具执行失败或无匹配结果
   - e4(验证 Pod rc-config-secret-key-missing 的 YAML 配置): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (43.4s)
   📤 → 下游数据: root_cause=Pod rc-config-secret-key-missing 无法启动的原因是 Secret aiops-e2e/rc-app-secret 中缺少 APP_SECRET_TOKEN 键。根据 kubectl describe 的输出，Pod 事件中显示了 'Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret'，这表明容器在启动时无法找到所需的 Secret 键。
   confidence=80%
   causal_chain={"root_cause": "Secret aiops-e2e/rc-app-secret 中缺少 APP_SECRET_TOKEN 键", "direct_causes": ["Pod rc-config-secret-key-missing 的容器在启动时需要访问 APP_SECRET_TOKEN 键，但该键在指定的 Secret 中不存在。"], "consequences": ["Pod rc-config-secret-key-missing 无法正常启动，其状态为 CreateContainerConfigError。", "这可能导致应用程序无法正常运行，因为缺少必要的环境变量。"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [{"id": "layer_6", "description": "kubectl_describe 显示了 Pod rc-config-secret-key-missing 的关键事件信息。", "value": "Pod rc-config-secret-key-missing 的事件中显示 'Warning Failed 18m (x12 over 20m) kubelet Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret'，这表明 Pod 在启动容器时无法找到 Secret 中的 APP_SECRET_TOKEN 键。"}], "causal_chain": {"root_cause": "Secret aiops-e2e/rc-app-secret 中缺少 APP_SECRET_TOKEN 键", "direct_causes": ["Pod rc-config-secret-key-missing 的容器在启动时需要访问 APP_SECRET_TOKEN 键，但该键在指定的 Secret 中不存在。"], "consequences": ["Pod rc-config-secret-key-missing 无法正常启动，其状态为 CreateContainerConfigError。", "这可能导致应用程序无法正常运行，因为缺少必要的环境变量。"]}, "root_cause": "Pod rc-config-secret-key-missing 无法启动的原因是 Secret aiops-e2e/rc-app-secret 中缺少 APP_SECRET_TOKEN 键。根据 kubectl describe 的输出，Pod 事件中显示了 'Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret'，这表明容器在启动时无法找到所需的 Secret 键。", "root_cause_summary": "Pod rc-config-secret-key-missing 无法启动的原因是 Secret aiops-e2e/rc-app-secret 中缺少 APP_SECRET_TOKEN 键。根据 kubectl describe 的输出，Pod 事件中显示了 'Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret'，这表明容器在启动时无法找到所需的 Secret 键。", "confidence": 0.8, "confidence_reason": "有直接证据表明 Secret 中缺少 APP_SECRET_TOKEN 键，这是导致 Pod 无法启动的直接原因。然而，为了更全面地确认这一原因，需要进一步验证 Secret aiops-e2e/rc-app-secret 的内容。", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [{"description": "ConfigMap 或 Secret 引用错误", "probability": "中", "reason": "Pod 配置可能引用了错误的 ConfigMap 或 Secret 名称，或键名拼写错误。"}], "limitations": "缺少对 Secret aiops-e2e/rc-app-secret 的直接验证，因此不能完全排除其他可能的配置错误。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-config-secret-key-missing 无法启动的原因是 Secret aiops-e2e/rc-app-secret 中缺少 APP_SECRET_TOKEN 键。根据 kubectl describe 的输出，Pod 事件中显示了 'Error: couldn't fi...
   置信度: 80%
   🔗 因果链:
     根本原因: Secret aiops-e2e/rc-app-secret 中缺少 APP_SECRET_TOKEN 键


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (2m 22.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6207 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 20.9s
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
| **兼容归因层** | L4 - 配置错误 |
| **问题分类** | 配置错误（ConfigError） |
| **置信度** | 高 (80%) |
| **证据完整度** | 1/4 (25%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-config-secret-key-missing |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | kubectl describe pod rc-config-secret-key-missing | `Warning Failed: Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret` | Pod 无法启动，原因是引用的 Secret 缺失指定键 |

### 证据关联分析

- **证据 #1 印证**：`Warning Failed: Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret` 明确指出容器启动失败是由于 Secret 缺失指定键。
- **证据链**：Pod 配置引用了 Secret aiops-e2e/rc-app-secret 中的 `APP_SECRET_TOKEN` 键 → Secret 中不存在该键 → 容器无法启动 → Pod 状态为 `CreateContainerConfigError`

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| Secret aiops-e2e/rc-app-secret 是否存在并包含 APP_SECRET_TOKEN | critical | 无法确认 Secret 是否存在或键名是否正确 |
| Pod rc-config-secret-key-missing 的详细事件记录 | critical | 无法确认是否有其他相关错误或配置问题 |
| Pod rc-config-secret-key-missing 的 YAML 配置 | important | 无法确认 Pod 是否引用了正确的 Secret 或键名 |

---

## 🎯 根因分析

### 因果链

```
┌──────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                             │
│ Secret aiops-e2e/rc-app-secret 中缺失键 APP_SECRET_TOKEN              │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                             │
│ Pod 配置引用了 Secret 中的 APP_SECRET_TOKEN 键，但键不存在            │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                             │
│ 容器启动失败，提示找不到 Secret 中的 APP_SECRET_TOKEN 键               │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                         │
│ Pod 状态为 CreateContainerConfigError，无法正常启动                    │
└──────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 中的 `Warning Failed: Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret`，问题的根本原因是 **Secret `aiops-e2e/rc-app-secret` 中缺少键 `APP_SECRET_TOKEN`**，导致容器无法启动，Pod 状态为 `CreateContainerConfigError`。

**置信度**：高 (80%)
- ✅ `kubectl describe` 明确指出缺少指定键
- ⚠️ 缺少对 Secret 的直接验证，无法确认 Secret 是否存在或键名是否拼写错误

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 确认并修复 Secret**
```bash
kubectl get secret rc-app-secret -n aiops-e2e -o yaml
```
*依据*：确认 Secret `rc-app-secret` 是否存在，并检查其中是否包含键 `APP_SECRET_TOKEN`

**2. [必要] 添加缺失的键**
```bash
kubectl create secret generic rc-app-secret \
  -n aiops-e2e \
  --from-literal=APP_SECRET_TOKEN="your-secret-value"
```
*依据*：如果 Secret 不存在或缺失键，则创建或更新 Secret

**3. [可选] 查看 Pod 配置**
```bash
kubectl get pod rc-config-secret-key-missing -n aiops-e2e -o yaml
```
*目的*：确认 Pod 是否引用了正确的 Secret 名称和键名

### 后续优化

1. **配置验证**：在部署前使用 `kubectl apply --dry-run=client` 检查配置是否正确
2. **自动化检查**：集成 CI/CD 流程中加入 Secret 验证步骤
3. **Secret 管理**：使用工具如 HashiCorp Vault 或 Kubernetes 的 ExternalSecret 进行更安全的密钥管理

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Secret 是否存在并包含键 | `kubectl get secret rc-app-secret -n aiops-e2e -o yaml` | 包含键 `APP_SECRET_TOKEN` |
| 2. 确认 Pod 是否仍处于异常状态 | `kubectl get pod rc-config-secret-key-missing -n aiops-e2e` | STATUS: Running |
| 3. 检查 Pod 事件是否仍有错误 | `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` | 无 `Failed` 事件 |

---

## ⚠️ 注意事项

- 如果 Secret 存在但键名拼写错误，需要修正键名
- 如果 Secret 存在且键名正确，但 Pod 仍无法启动，可能需要检查其他配置项（如环境变量绑定、Volume 挂载等）
- 修复后建议监控一段时间，确认问题不再复现

---

## 📄 附录：工具采集原始数据

**kubectl describe pod**:
```
Warning  Failed          18m (x12 over 20m)  kubelet            Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret
```

**kubectl get pod**:
```
NAME                           READY   STATUS                       RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-config-secret-key-missing   0/1     CreateContainerConfigError   0          19m   172.16.166.188   node1   <none>           <none>            app=rc-config-secret-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true
```

**kubectl get pod -n aiops-e2e**:
```
NAMESPACE     NAME                                                READY   STATUS                       RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     rc-config-secret-key-missing                        0/1     CreateContainerConfigError   0          19m   172.16.166.188   node1   <none>           <none>            app=rc-config-secret-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true
```

**kubectl logs**:
```
Error from server (BadRequest): container "app" in pod "rc-config-secret-key-missing" is waiting to start: CreateContainerConfigError
```

---

## 🧾 证据采集统计（系统数据，必须原样引用）

**collection_summary**: 计划 4 项，实际采集 1 项，未采集 3 项，完整度 25%；其中真实环境证据 7/10 项，完整度 70%；实际执行工具 6 个，匹配计划 1 个，未规划证据 5 个

**已采集 (7 项)**:
  ✅ e1: 验证 Pod rc-config-secret-key-missing 是否仍存在且处于异常状态  
  ✅ layer_1: 上游已验证工具结果: kubectl_get_by_kind_in_cluster  
  ✅ layer_2: 上游已验证工具结果: kubectl_get_by_name  
  ✅ layer_3: 上游已验证工具结果: kubectl_previous_logs  
  ✅ layer_4: 上游已验证工具结果: kubectl_container_previous_logs  
  ✅ layer_5: 上游已验证工具结果: kubectl_logs  
  ✅ layer_6: 上游已验证工具结果: kubectl_describe  

**未采集 (3 项)**:
  ❌ e2: 验证 Pod rc-config-secret-key-missing 的详细事件记录  
  ❌ e3: 验证 Secret aiops-e2e/rc-app-secret 是否存在并包含 APP_SECRET_TOKEN 键  
  ❌ e4: 验证 Pod rc-config-secret-key-missing 的 YAML 配置  

**未采集原因**:
  - e2: 已规划但工具执行失败或无匹配结果  
  - e3: 已规划但工具执行失败或无匹配结果  
  - e4: 已规划但工具执行失败或无匹配结果

---

## 📊 性能统计

├─ 总耗时: 5.3m
├─ 问题定位: 37.0s (12%) ✅
├─ 证据链采集: 98.4s (31%) ✅
├─ 根因分析: 43.4s (14%) ✅
├─ 汇总总结: 142.0s (44%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 10 次
```

📋 诊断追踪

- **核心 Runbook**: pod-config-error
- **参考 Runbook**: pod-config-error
- **工具调用**: 10 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
