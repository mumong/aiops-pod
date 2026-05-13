======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 8e2c48f4b87b43ea]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'CrashLoopBackOff': 1, 'Running': 46}
NAMESPACE     NAME                                                READY   STATUS           
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
      📄 NAME                             READY   STATUS             RESTARTS        AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
appconfigfail-575d77485d-nfpvh   0/1     CrashLoopB
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 6
signals: 5
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config
L4_SCENARIO: config-bootstrap-fail
L4_ERROR_TYPE: applicati
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "ConfigError",
  "confidence": 0.95,
  "reasoning": "异常 Pod 明确属于 CrashLoopBackOff 状态，且日志和 describe 信息显示为配置错误导致应用启动失败。具体表现为缺少关键环境变量 APP_BOOT_MODE，以及业务配置校验失败。同时排除了 OOMKilled、ImagePullFailed 和 Evicted 等其他异常类型。"
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (41.5s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': '应用启动配置错误', 'probability': '高', 'reason': 'CrashLoopBackOff + 日志含配置校验失败/缺参'}]
   entities=[{"type": "pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}]
   reasoning=异常 Pod 明确属于 CrashLoopBackOff 状态，且日志和 describe 信息显示为配置错误导致应用启动失败。具体表现为缺少关键环境变量 APP_BOOT_MODE，以及业务配置校验失败。同时排除了 OOMKilled、ImagePullFailed 和 Evicted 等其他异常类型。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.95, "reasoning": "异常 Pod 明确属于 CrashLoopBackOff 状态，且日志和 describe 信息显示为配置错误导致应用启动失败。具体表现为缺少关键环境变量 APP_BOOT_MODE，以及业务配置校验失败。同时排除了 OOMKilled、ImagePullFailed 和 Evicted 等其他异常类型。", "abnormal_pods": [{"name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "app_config", "key_entities": [{"type": "pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "应用启动配置错误", "probability": "高", "reason": "CrashLoopBackOff + 日志含配置校验失败/缺参"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     appconfigfail-575d77485d-nfpvh                      0/1     CrashLoopBackOff   9 (4m27s ago)   25m    172.16.166.184   node1    <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError"], "raw_ref": "/tmp/aiops/reports/context_archives/8e2c48f4b87b43ea/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/8e2c48f4b87b43ea/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/8e2c48f4b87b43ea/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                             READY   STATUS             RESTARTS       AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
appconfigfail-575d77485d-nfpvh   0/1     CrashLoopBa
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
2m30s (x119 over 27m)   Warning   BackOff          Pod/appconfigfail-575d77485d-nfpvh   Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 6
signals: 5
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config
L4_SCENARIO: config-bootstrap-fail
L4_ERROR_TYPE: applicati
   💭 [证据链采集] 已采集证据：
1. `kubectl_get_by_name`：确认了异常 Pod `appconfigfail-575d77485d-nfpvh` 处于 `CrashLoopBackOff` 状态，重启次数增加，标签中包含 `pod_abnormal_type=ConfigError`。
2. `kubectl_events`：发现持续的 `Back-off restarting failed container` 事件，指向容器启动失败。
3. `kubectl_previous_logs`：日志显示 `FATAL: missing required APP_BOOT_MODE` 和 `business config validation failed before server startup`，明确是配置错误导致启动失败。

未采集证据：无。

冲突证据：无。
   ✅ [证据链采集] 完成 (1m 36.8s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 的详细信息","level":"critical","tool":"kubectl_get_by_name","command":"get pods appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml","tool_args":{},"purpose":"获取异常 Pod 的完整配置信息","evidence_type":"pod_configuration","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 的事件信息","level":"important","tool":"kubectl_events","command":"get events -n aiops-e2e --field-selector=involvedObject.name=appconfigfail-575d77485d-nfpvh","tool_args":{"resource_type":"pod","resource_name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e"},"purpose":"查看与异常 Pod 相关的事件","evidence_type":"event_log","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":["kubectl_events"],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod 的日志信息","level":"important","tool":"kubectl_previous_logs","command":"logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous","tool_args":{},"purpose":"查看异常 Pod 上次容器的退出日志","evidence_type":"container_logs","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":["kubectl_previous_logs"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                             READY   STATUS             RESTARTS       AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nappconfigfail-575d77485d-nfpvh   0/1     CrashLoopBackOff   10 (70s ago)   27m   172.16.166.184   node1   <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/8e2c48f4b87b43ea/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/8e2c48f4b87b43ea/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/8e2c48f4b87b43ea/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n2m30s (x119 over 27m)   Warning   BackOff          Pod/appconfigfail-575d77485d-nfpvh   Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/8e2c48f4b87b43ea/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/8e2c48f4b87b43ea/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/8e2c48f4b87b43ea/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 6\nsignals: 5\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/8e2c48f4b87b43ea/tools/003-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/8e2c48f4b87b43ea/tools/003-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/8e2c48f4b87b43ea/tools/003-evidence-kubectl_previous_logs.summary.txt"}],"llm_analysis":"已采集证据：\n1. `kubectl_get_by_name`：确认了异常 Pod `appconfigfail-575d77485d-nfpvh` 处于 `CrashLoopBackOff` 状态，重启次数增加，标签中包含 `pod_abnormal_type=ConfigError`。\n2. `kubectl_events`：发现持续的 `Back-off restarting failed container` 事件，指向容器启动失败。\n3. `kubectl_previous_logs`：日志显示 `FATAL: missing required APP_BOOT_MODE` 和 `business config validation failed before server startup`，明确是配置错误导致启动失败。\n\n未采集证据：无。\n\n冲突证据：无。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 6/6 项，完整度 100%；实际执行工具 6 个，匹配计划 3 个，未规划证据 3 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":6,"environment_evidence_collected":6,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":3,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 的详细信息","level":"critical","tool":"kubectl_get_by_name","command":"get pods appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml","purpose":"获取异常 Pod 的完整配置信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 的事件信息","level":"important","tool":"kubectl_events","command":"get events -n aiops-e2e --field-selector=involvedObject.name=appconfigfail-575d77485d-nfpvh","purpose":"查看与异常 Pod 相关的事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod 的日志信息","level":"important","tool":"kubectl_previous_logs","command":"logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous","purpose":"查看异常 Pod 上次容器的退出日志","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 获取异常 Pod 的详细信息 | `get pods appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml` |
   | e2 | important | ✅ | kubectl_events | 获取异常 Pod 的事件信息 | `get events -n aiops-e2e --field-selector=involvedObject.name=appconfigfail-57...` |
   | e3 | important | ✅ | kubectl_previous_logs | 获取异常 Pod 的日志信息 | `logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (15.3s)
   📤 → 下游数据: root_cause=异常 Pod `appconfigfail-575d77485d-nfpvh` 处于 `CrashLoopBackOff` 状态，日志显示 `FATAL: missing required APP_BOOT_MODE` 和 `business config validation failed before server startup`，表明配置错误导致应用启动失败。容器不断重启，且事件信息显示 `Back-off restarting failed container`，进一步确认了配置错误是根因。
   confidence=95%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [], "causal_chain": {}, "root_cause": "异常 Pod `appconfigfail-575d77485d-nfpvh` 处于 `CrashLoopBackOff` 状态，日志显示 `FATAL: missing required APP_BOOT_MODE` 和 `business config validation failed before server startup`，表明配置错误导致应用启动失败。容器不断重启，且事件信息显示 `Back-off restarting failed container`，进一步确认了配置错误是根因。", "root_cause_summary": "异常 Pod `appconfigfail-575d77485d-nfpvh` 处于 `CrashLoopBackOff` 状态，日志显示 `FATAL: missing required APP_BOOT_MODE` 和 `business config validation failed before server startup`，表明配置错误导致应用启动失败。容器不断重启，且事件信息显示 `Back-off restarting failed container`，进一步确认了配置错误是根因。", "confidence": 0.95, "confidence_reason": "有直接证据支持因果链，包括 Pod 状态、容器事件和日志中的错误信息。", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [], "limitations": "", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 异常 Pod `appconfigfail-575d77485d-nfpvh` 处于 `CrashLoopBackOff` 状态，日志显示 `FATAL: missing required APP_BOOT_MODE` 和 `business config validation failed bef...
   置信度: 95%

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
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (5m 58.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3805 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 8m 32.2s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | `CrashLoopBackOff` |
| **兼容归因层** | L4 |
| **问题分类** | `ConfigError`（配置错误） |
| **置信度** | 高 (95%) |
| **证据完整度** | 3/3 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题？

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | `appconfigfail-575d77485d-nfpvh` |
| Namespace | `aiops-e2e` |
| Node | `node1` |
| 错误信息 | `L4_CONFIG_BOOTSTRAP_FAIL`, `FATAL: missing required APP_BOOT_MODE`, `business config validation failed before server startup` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff`, `RESTARTS: 9` | Pod 由于启动失败持续重启 |
| 2 | Pod 事件 | `kubectl describe pod` | `Warning: Back-off restarting failed container` | 确认容器持续失败并重启 |
| 3 | 容器日志 | `kubectl logs --previous` | `FATAL: missing required APP_BOOT_MODE`, `business config validation failed` | 明确指出配置错误导致启动失败 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 处于 `CrashLoopBackOff` 状态，事件信息表明容器持续失败并重启，指向配置错误。
- **证据 #1 + #3 印证**：日志中显示 `FATAL: missing required APP_BOOT_MODE`，确认了配置错误的具体原因。
- **证据链**：应用缺少关键环境变量 `APP_BOOT_MODE` → 业务配置校验失败 → 容器启动失败 → Pod 进入 `CrashLoopBackOff` 状态。

### 缺失证据

无缺失证据。

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 缺少关键环境变量 APP_BOOT_MODE，导致业务配置校验失败            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 应用启动前需要 APP_BOOT_MODE，但未提供 → 业务配置校验失败       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器启动失败，Exit Code 为业务配置错误（非 OOMKilled）          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 `CrashLoopBackOff`，重启次数持续增加                 │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1（Pod 状态为 `CrashLoopBackOff`）、证据 #2（事件信息为 `Back-off restarting failed container`）、证据 #3（日志中明确指出 `FATAL: missing required APP_BOOT_MODE` 和 `business config validation failed`），问题的根本原因是 **缺少关键环境变量 `APP_BOOT_MODE`，导致业务配置校验失败，容器启动失败**。

**置信度**：高 (95%)
- ✅ 日志中明确指出配置校验失败
- ✅ Pod 状态和事件信息印证了容器持续失败
- ✅ 无 OOMKilled、ImagePullFailed 等干扰因素

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 为 Pod 配置 `APP_BOOT_MODE` 环境变量**
```bash
kubectl set env deployment/appconfigfail APP_BOOT_MODE=local -n aiops-e2e
```
*依据*：日志显示缺少该环境变量，直接添加后重新启动容器。

**2. [可选] 检查业务配置是否依赖其他环境变量**
```bash
kubectl describe pod appconfigfail-575d77485d-nfpvh -n aiops-e2e
```
*目的*：确认是否存在其他缺失的环境变量或配置项。

**3. [可选] 查看崩溃前日志（已采集）**
```bash
kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous
```
*目的*：进一步确认配置错误的具体原因。

### 后续优化

1. **配置健康检查探针（liveness/readiness）**：避免容器因配置错误无限重启。
2. **配置 ConfigMap/Secret 验证机制**：在部署前校验配置是否完整。
3. **增强日志记录和监控**：捕获配置错误并及时告警。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e` | STATUS: `Running` |
| 2. 检查重启次数 | `kubectl get pod appconfigfail-575d77485d-nfpvh -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |
| 3. 检查日志 | `kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e` | 无 `FATAL` 级错误 |

---

## ⚠️ 注意事项

- 如果配置 `APP_BOOT_MODE` 后仍失败，需进一步检查是否还有其他缺失的环境变量或配置。
- 建议在部署流程中加入配置校验步骤，避免类似问题重复发生。
- 如果应用依赖 ConfigMap/Secret，确保其存在并挂载正确。

---

## 📊 性能统计

├─ 总耗时: 8.5m
├─ 问题定位: 41.5s (8%) ✅
├─ 证据链采集: 96.9s (19%) ✅
├─ 根因分析: 15.3s (3%) ✅
├─ 汇总总结: 358.5s (70%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 7 次
```

📋 诊断追踪

- **核心 Runbook**: pod-config-error
- **参考 Runbook**: pod-config-error
- **工具调用**: 7 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
