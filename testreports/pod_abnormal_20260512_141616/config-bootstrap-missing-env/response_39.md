======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: db8dbe8ea586470b]

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
      📄 NAME                             READY   STATUS             RESTARTS       AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
appconfigfail-575d77485d-nfpvh   0/1     CrashLoopBa
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 6
signals: 5
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config
L4_SCENARIO: config-bootstrap-fail
L4_ERROR_TYPE: applicati
   💭 [问题定位] 调用工具: kubectl_container_previous_logs_grep
   💭 [问题定位] 工具结果: kubectl_container_previous_logs_grep (success)
      📄 kubectl_container_previous_logs_grep 输出摘要: raw_chars=851 lines=1
Error: kubectl_container_previous_logs_grep is not a valid tool, try one of [kubectl_describe, kubectl_get_by_name, kubectl_get_by_kind
   💭 [问题定位] 调用工具: kubectl_previous_logs_grep
   💭 [问题定位] 工具结果: kubectl_previous_logs_grep (success)
      📄 kubectl_previous_logs_grep 输出摘要: raw_chars=841 lines=1
Error: kubectl_previous_logs_grep is not a valid tool, try one of [kubectl_describe, kubectl_get_by_name, kubectl_get_by_kind_in_namespace, kubec
   💭 [问题定位] 调用工具: kubectl_logs_grep
   💭 [问题定位] 工具结果: kubectl_logs_grep (success)
      📄 kubectl_logs_grep 日志摘要:
lines: 4
signals: 4
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config
L4_SCENARIO: config-bootstrap-fail
L4_ERROR_TYPE: application-c
   💭 [问题定位] 调用工具: kubectl_container_logs
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 0.8s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': '应用启动配置错误', 'probability': '高', 'reason': 'CrashLoopBackOff + 日志含配置校验失败/缺参'}]
   entities=[{"type": "Pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}]
   reasoning=当前活跃异常对象为 Pod appconfigfail-575d77485d-nfpvh，其状态为 CrashLoopBackOff，且日志中包含 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: business config validation failed before server startup 等特征。根据 runbook 和日志内容，确认该 Pod 的异常类型为 ConfigError，归类至 L4 层，根因为 application error，涉及 app_config/app_health。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "application error", "confidence": 0.5, "reasoning": "当前活跃异常对象为 Pod appconfigfail-575d77485d-nfpvh，其状态为 CrashLoopBackOff，且日志中包含 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: business config validation failed before server startup 等特征。根据 runbook 和日志内容，确认该 Pod 的异常类型为 ConfigError，归类至 L4 层，根因为 application error，涉及 app_config/app_health。", "abnormal_pods": [{"name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "app_config/app_health", "key_entities": [{"type": "Pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "应用启动配置错误", "probability": "高", "reason": "CrashLoopBackOff + 日志含配置校验失败/缺参"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     appconfigfail-575d77485d-nfpvh                      0/1     CrashLoopBackOff   23 (57s ago)    93m    172.16.166.184   node1    <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError"], "raw_ref": "/tmp/aiops/reports/context_archives/db8dbe8ea586470b/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/db8dbe8ea586470b/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/db8dbe8ea586470b/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 50%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: appconfigfail-575d77485d-nfpvh
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键状态/事件:
                  aiops.e2e/expected-status: CrashLoopBackOff|CreateContai
   💭 [证据链采集] 已采集证据：
- `kubectl_describe` 显示 Pod `appconfigfail-575d77485d-nfpvh` 的状态为 `CrashLoopBackOff`，Exit Code 为 42，表明应用启动失败。
- 事件中包含 `Back-off restarting failed container`，进一步确认容器异常退出。
- 无 OOMKilled 或 ImagePullBackOff 等其他异常信号，符合 ConfigError 归因。

未采集证据：
- Pod 的容器日志中是否包含明确的配置校验失败信息（如 `FATAL: business config validation failed`）。

冲突证据：
- 无。
   ✅ [证据链采集] 完成 (47.1s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 的详细描述信息以确认其配置和状态","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod appconfigfail-575d77485d-nfpvh -n aiops-e2e","tool_args":{"kind":"Pod","name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e"},"purpose":"获取异常 Pod 的详细信息，包括事件、状态和配置","evidence_type":"Pod 详细信息","target_scope":"aiops-e2e","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: appconfigfail-575d77485d-nfpvh\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键状态/事件:\n                  aiops.e2e/expected-status: CrashLoopBackOff|CreateContainerConfigError|CreateContainerError\n    State:          Waiting\n      Reason:       CrashLoopBackOff\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42\n  Warning  BackOff  17s (x439 over 95m)  kubelet  Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/db8dbe8ea586470b/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/db8dbe8ea586470b/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/db8dbe8ea586470b/tools/001-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"已采集证据：\n- `kubectl_describe` 显示 Pod `appconfigfail-575d77485d-nfpvh` 的状态为 `CrashLoopBackOff`，Exit Code 为 42，表明应用启动失败。\n- 事件中包含 `Back-off restarting failed container`，进一步确认容器异常退出。\n- 无 OOMKilled 或 ImagePullBackOff 等其他异常信号，符合 ConfigError 归因。\n\n未采集证据：\n- Pod 的容器日志中是否包含明确的配置校验失败信息（如 `FATAL: business config validation failed`）。\n\n冲突证据：\n- 无。","collection_summary":"计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 5 个，匹配计划 1 个，未规划证据 4 个","plan_total":1,"plan_collected":1,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":5,"matched_tool_count":1,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 的详细描述信息以确认其配置和状态","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod appconfigfail-575d77485d-nfpvh -n aiops-e2e","purpose":"获取异常 Pod 的详细信息，包括事件、状态和配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_container_previous_logs_grep","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_previous_logs_grep","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_logs_grep","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/1 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取异常 Pod 的详细描述信息以确认其配置和状态 | `kubectl describe pod appconfigfail-575d77485d-nfpvh -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 51.1s)
   📤 → 下游数据: root_cause=当前活跃异常对象为 Pod appconfigfail-575d77485d-nfpvh，其状态为 CrashLoopBackOff，且日志中包含 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: business config validation failed before server startup 等特征。根据 runbook 和日志内容，确认该 Pod 的异常类型为 ConfigError，归类至 L4 层，根因为 application error，涉及 app_config/app_health。
   confidence=90%
   causal_chain={"root_cause": "application error", "intermediate_causes": [{"cause": "ConfigError", "evidence": "kubectl_get_by_kind_in_cluster 表格摘要显示异常 Pod 状态为 `CrashLoopBackOff`，重启次数为 23 次。kubectl_get_by_name 显示异常 Pod 的详细状态和标签信息，包括 `CrashLoopBackOff` 和 `pod_abnormal_type=ConfigError`。"}, {"cause": "application-config-validation", "evidence": "kubectl_previous_logs 显示日志中包含 `L4_CONFIG_BOOTSTRAP_FAIL` 和 `FATAL: business config validation failed before server startup` 等关键日志。kubectl_logs_grep 显示日志中包含 `L4_CONFIG_BOOTSTRAP_FAIL` 和 `FATAL: business config validation failed before server startup` 等关键日志。"}], "direct_causes": [{"cause": "FATAL: missing required APP_BOOT_MODE", "evidence": "kubectl_previous_logs 显示日志中包含 `FATAL: missing required APP_BOOT_MODE`。"}], "phenomenon": "当前活跃异常对象为 Pod appconfigfail-575d77485d-nfpvh，其状态为 CrashLoopBackOff，且日志中包含 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: business config validation failed before server startup 等特征。根据 runbook 和日志内容，确认该 Pod 的异常类型为 ConfigError，归类至 L4 层，根因为 application error，涉及 app_config/app_health。"}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"e1": "获取异常 Pod 的详细描述信息以确认其配置和状态"}, {"layer_1": "上游已验证工具结果: kubectl_get_by_kind_in_cluster"}, {"layer_2": "上游已验证工具结果: kubectl_get_by_name"}, {"layer_3": "上游已验证工具结果: kubectl_previous_logs"}, {"layer_4": "上游已验证工具结果: kubectl_container_previous_logs_grep"}, {"layer_5": "上游已验证工具结果: kubectl_previous_logs_grep"}, {"layer_6": "上游已验证工具结果: kubectl_logs_grep"}], "evidence_analysis": [{"e1": "kubectl_describe 显示 Pod `appconfigfail-575d77485d-nfpvh` 的状态为 `CrashLoopBackOff`，Exit Code 为 42，表明应用启动失败。事件中包含 `Back-off restarting failed container`，进一步确认容器异常退出。无 OOMKilled 或 ImagePullBackOff 等其他异常信号，符合 ConfigError 归因。"}, {"layer_1": "kubectl_get_by_kind_in_cluster 表格摘要显示异常 Pod 状态为 `CrashLoopBackOff`，重启次数为 23 次。"}, {"layer_2": "kubectl_get_by_name 显示异常 Pod 的详细状态和标签信息，包括 `CrashLoopBackOff` 和 `pod_abnormal_type=ConfigError`。"}, {"layer_3": "kubectl_previous_logs 显示日志中包含 `L4_CONFIG_BOOTSTRAP_FAIL` 和 `FATAL: business config validation failed before server startup` 等关键日志。"}, {"layer_6": "kubectl_logs_grep 显示日志中包含 `L4_CONFIG_BOOTSTRAP_FAIL` 和 `FATAL: business config validation failed before server startup` 等关键日志。"}], "causal_chain": {"root_cause": "application error", "intermediate_causes": [{"cause": "ConfigError", "evidence": "kubectl_get_by_kind_in_cluster 表格摘要显示异常 Pod 状态为 `CrashLoopBackOff`，重启次数为 23 次。kubectl_get_by_name 显示异常 Pod 的详细状态和标签信息，包括 `CrashLoopBackOff` 和 `pod_abnormal_type=ConfigError`。"}, {"cause": "application-config-validation", "evidence": "kubectl_previous_logs 显示日志中包含 `L4_CONFIG_BOOTSTRAP_FAIL` 和 `FATAL: business config validation failed before server startup` 等关键日志。kubectl_logs_grep 显示日志中包含 `L4_CONFIG_BOOTSTRAP_FAIL` 和 `FATAL: business config validation failed before server startup` 等关键日志。"}], "direct_causes": [{"cause": "FATAL: missing required APP_BOOT_MODE", "evidence": "kubectl_previous_logs 显示日志中包含 `FATAL: missing required APP_BOOT_MODE`。"}], "phenomenon": "当前活跃异常对象为 Pod appconfigfail-575d77485d-nfpvh，其状态为 CrashLoopBackOff，且日志中包含 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: business config validation failed before server startup 等特征。根据 runbook 和日志内容，确认该 Pod 的异常类型为 ConfigError，归类至 L4 层，根因为 application error，涉及 app_config/app_health。"}, "root_cause": "当前活跃异常对象为 Pod appconfigfail-575d77485d-nfpvh，其状态为 CrashLoopBackOff，且日志中包含 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: business config validation failed before server startup 等特征。根据 runbook 和日志内容，确认该 Pod 的异常类型为 ConfigError，归类至 L4 层，根因为 application error，涉及 app_config/app_health。", "root_cause_summary": "当前活跃异常对象为 Pod appconfigfail-575d77485d-nfpvh，其状态为 CrashLoopBackOff，且日志中包含 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: business config validation failed before server startup 等特征。根据 runbook 和日志内容，确认该 Pod 的异常类型为 ConfigError，归类至 L4 层，根因为 application error，涉及 app_config/app_health。", "confidence": 0.9, "confidence_reason": "有直接证据，因果链清晰。", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [], "limitations": "无。", "llm_raw_analysis": "已采集证据：\n- `kubectl_describe` 显示 Pod `appconfigfail-575d77485d-nfpvh` 的状态为 `CrashLoopBackOff`，Exit Code 为 42，表明应用启动失败。\n- 事件中包含 `Back-off restarting failed container`，进一步确认容器异常退出。\n- 无 OOMKilled 或 ImagePullBackOff 等其他异常信号，符合 ConfigError 归因。\n\n未采集证据：\n- Pod 的容器日志中是否包含明确的配置校验失败信息（如 `FATAL: business config validation failed`）。\n\n冲突证据：\n- 无。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 当前活跃异常对象为 Pod appconfigfail-575d77485d-nfpvh，其状态为 CrashLoopBackOff，且日志中包含 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: business config validation failed before s...
   置信度: 90%
   🔗 因果链:
     根本原因: application error


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
   ✅ [汇总总结] 完成 (5m 30.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4387 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 9m 8.9s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | CrashLoopBackOff |
| **兼容归因层** | L4 |
| **问题分类** | ConfigError（配置错误） |
| **置信度** | 高 (90%) |
| **证据完整度** | 1/1 (100%) |

---

## 🔍 现象描述

**用户报告**：  
> 我的集群有什么问题

**关键实体**：  
| 类型 | 值 |
|------|-----|
| Pod | appconfigfail-575d77485d-nfpvh |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | L4_CONFIG_BOOTSTRAP_FAIL, FATAL: business config validation failed before server startup |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff`, `RESTARTS: 23`, `L4_SCENARIO: config-bootstrap-fail` | Pod 持续重启，状态为 CrashLoopBackOff，属于 L4_CONFIG_BOOTSTRAP_FAIL 场景 |
| 2 | Pod 日志 | `kubectl previous logs` | `L4_CONFIG_BOOTSTRAP_FAIL`, `FATAL: business config validation failed before server startup` | 应用在启动前配置校验失败 |
| 3 | Describe Pod | `kubectl describe pod` | `Last State: Terminated`, `Exit Code: 42` | 容器启动失败，退出码为 42（非 OOMKilled 或 ImagePullError） |
| 4 | Runbook | `fetch_runbook` | `ConfigError / 启动配置失败`，`兼容分类: config_bootstrap` | 与当前现象匹配，确认问题为配置错误 |
| 5 | 日志摘要 | `kubectl logs grep` | `L4_ERROR_TYPE: application-config-validation` | 应用配置校验失败 |
| 6 | 命令错误 | `kubectl_container_previous_logs_grep` | `Error: kubectl_container_previous_logs_grep is not a valid tool` | 无效命令，忽略 |
| 7 | 命令错误 | `kubectl_previous_logs_grep` | `Error: kubectl_previous_logs_grep is not a valid tool` | 无效命令，忽略 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 重启频繁 + 日志明确指出配置校验失败 → 问题根因是配置错误
- **证据链**：
  - 应用启动前配置校验失败 → 容器启动失败 → Pod 重启 → CrashLoopBackOff

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 应用配置校验失败，缺少必要的配置项（如 APP_BOOT_MODE）           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 配置缺失或校验失败 → 应用启动失败 → 容器退出 → Pod 重启          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器退出码 42，日志显示配置校验失败                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 CrashLoopBackOff，重启次数持续增加                     │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Pod 状态为 CrashLoopBackOff, 重启次数增加) 和证据 #2 (日志显示 `L4_CONFIG_BOOTSTRAP_FAIL` 和 `FATAL: business config validation failed`)，问题的根本原因是**应用缺少必要的配置项或配置校验失败**，导致容器启动失败并持续重启。

**置信度**：高 (90%)
- ✅ 日志中明确指出 `L4_CONFIG_BOOTSTRAP_FAIL`
- ✅ Pod 重启频繁，符合 ConfigError 场景
- ✅ Runbook 明确支持该诊断结论

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查并修复配置**
```bash
kubectl get pod -n aiops-e2e appconfigfail-575d77485d-nfpvh -o jsonpath='{.spec.containers[*].env}' 
kubectl get pod -n aiops-e2e appconfigfail-575d77485d-nfpvh -o jsonpath='{.spec.containers[*].envFrom}'
```
*依据*：检查容器是否缺少 `APP_BOOT_MODE` 或其他关键配置项

**2. [优先] 检查 ConfigMap/Secret 是否挂载正确**
```bash
kubectl get pod -n aiops-e2e appconfigfail-575d77485d-nfpvh -o jsonpath='{.spec.containers[*].volumeMounts}' 
kubectl get configmap -n aiops-e2e
kubectl get secret -n aiops-e2e
```
*依据*：确认应用使用的 ConfigMap/Secret 是否存在、是否正确挂载

**3. [可选] 查看崩溃前日志**
```bash
kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous
```
*目的*：查看容器启动前日志，确认具体错误信息

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |
| 3. 查看日志 | `kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e` | 无 `L4_CONFIG_BOOTSTRAP_FAIL` 错误 |

---

## ⚠️ 注意事项

- 如果配置修复后问题仍存在，建议检查应用代码是否存在配置校验逻辑错误
- 确保 ConfigMap/Secret 的权限和内容正确
- 若应用为多容器 Pod，检查其他容器是否影响启动

---

## 📌 附加建议

- **配置校验机制**：建议在部署前加入配置校验 Hook（如 InitContainer）
- **监控告警**：为 Pod 重启次数配置监控告警
- **文档记录**：记录所有配置项，避免遗漏关键参数

---

---

## 📊 性能统计

├─ 总耗时: 9.1m
├─ 问题定位: 60.8s (11%) ✅
├─ 证据链采集: 47.1s (9%) ✅
├─ 根因分析: 111.1s (20%) ✅
├─ 汇总总结: 330.0s (60%) ✅
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
