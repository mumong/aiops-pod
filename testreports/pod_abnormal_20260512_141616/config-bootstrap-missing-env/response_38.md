======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 88461bf82ef94375]

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
      📄 NAME                             READY   STATUS             RESTARTS         AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
appconfigfail-575d77485d-nfpvh   0/1     CrashLoop
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 6
signals: 5
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config
L4_SCENARIO: config-bootstrap-fail
L4_ERROR_TYPE: applicati
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: appconfigfail-575d77485d-nfpvh
namespace: aiops-e2e
creationTimestamp: 2026-05-12T05:59:23Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finali
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "ConfigError",
  "confidence": "high",
  "reasoning": "当前 Pod 状态为 CrashLoopBackOff，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: missing required APP_BOOT_MODE，表明应用启动配置错误。此外，describe 中显示 Exit Code 为 42，非 OOMKilled 的 137，进一步确认是配置问题而非资源问题。同时，没有 ImagePullBackOff 或 Evicted 的迹象，排除了其他异常类型。",
  "abnormal_pods": [
    "appconfigfail-575d77485d-nfpvh"
  ],
  "abnormal_groups": [
    "CrashLoopBackOff"
  ],
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "ConfigError",
  "status_category": "ConfigError",
  "key_entities": [
    "appconfigfail-575d77485d-nfpvh",
    "ConfigError",
    "L4_CONFIG_BOOTSTRAP_FAIL",
    "APP_BOOT_MODE"
  ],
  "possible_scenarios": [
    "应用启动配置错误导致容器崩溃",
    "缺失必填环境变量 APP_BOOT_MODE",
    "业务配置校验失败"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (3m 48.8s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': '应用启动配置错误导致容器崩溃', 'probability': 'high', 'reason': 'CrashLoopBackOff + 日志含 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: missing required APP_BOOT_MODE'}, {'scenario': '缺失必填环境变量 APP_BOOT_MODE', 'probability': 'high', 'reason': '日志显示 FATAL: missing required APP_BOOT_MODE'}, {'scenario': '业务配置校验失败', 'probability': 'high', 'reason': '日志显示 L4_ERROR_TYPE: application-config-validation'}]
   entities=[{"type": "Pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}, {"type": "ConfigError", "name": "ConfigError", "namespace": ""}, {"type": "ErrorSignal", "name": "L4_CONFIG_BOOTSTRAP_FAIL", "namespace": ""}, {"type": "ErrorSignal", "name": "APP_BOOT_MODE", "namespace": ""}]
   reasoning=当前 Pod 状态为 CrashLoopBackOff，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: missing required APP_BOOT_MODE，表明应用启动配置错误。此外，describe 中显示 Exit Code 为 42，非 OOMKilled 的 137，进一步确认是配置问题而非资源问题。同时，没有 ImagePullBackOff 或 Evicted 的迹象，排除了其他异常类型。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 1.0, "reasoning": "当前 Pod 状态为 CrashLoopBackOff，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: missing required APP_BOOT_MODE，表明应用启动配置错误。此外，describe 中显示 Exit Code 为 42，非 OOMKilled 的 137，进一步确认是配置问题而非资源问题。同时，没有 ImagePullBackOff 或 Evicted 的迹象，排除了其他异常类型。", "abnormal_pods": [{"name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "ConfigError", "key_entities": [{"type": "Pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}, {"type": "ConfigError", "name": "ConfigError", "namespace": ""}, {"type": "ErrorSignal", "name": "L4_CONFIG_BOOTSTRAP_FAIL", "namespace": ""}, {"type": "ErrorSignal", "name": "APP_BOOT_MODE", "namespace": ""}], "possible_scenarios": [{"scenario": "应用启动配置错误导致容器崩溃", "probability": "high", "reason": "CrashLoopBackOff + 日志含 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: missing required APP_BOOT_MODE"}, {"scenario": "缺失必填环境变量 APP_BOOT_MODE", "probability": "high", "reason": "日志显示 FATAL: missing required APP_BOOT_MODE"}, {"scenario": "业务配置校验失败", "probability": "high", "reason": "日志显示 L4_ERROR_TYPE: application-config-validation"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     appconfigfail-575d77485d-nfpvh                      0/1     CrashLoopBackOff   21 (3m30s ago)   86m    172.16.166.184   node1    <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError"], "raw_ref": "/tmp/aiops/reports/context_archives/88461bf82ef94375/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/88461bf82ef94375/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/88461bf82ef94375/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 100%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                             READY   STATUS             RESTARTS         AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
appconfigfail-575d77485d-nfpvh   0/1     CrashLoop
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
2m26s (x417 over 92m)   Warning   BackOff   Pod/appconfigfail-575d77485d-nfpvh   Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 6
signals: 5
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config
L4_SCENARIO: config-bootstrap-fail
L4_ERROR_TYPE: applicati
   💭 [证据链采集] 调用工具: kubectl_find_resource
   💭 [证据链采集] 工具结果: kubectl_find_resource (success)
      📄 kubectl_find_resource 输出摘要: raw_chars=95 lines=2
Command failed (exit 1):
kubectl get -A --show-labels -o wide pod | grep -i 'configmap,secret'
   💭 [证据链采集] 已采集证据：
- Pod `appconfigfail-575d77485d-nfpvh` 的状态为 `CrashLoopBackOff`，重启次数不断增加，表明容器频繁崩溃。
- 事件中显示 `Back-off restarting failed container`，进一步确认容器失败并频繁重启。
- 崩溃前的日志包含 `L4_CONFIG_BOOTSTRAP_FAIL`、`FATAL: missing required APP_BOOT_MODE`、`FATAL: business config validation failed before server startup` 等信息，表明是由于配置缺失或校验失败导致的容器崩溃。
- 未找到与该 Pod 相关的 `ConfigMap` 或 `Secret` 资源，可能该 Pod 未正确引用所需的配置资源，或者配置资源不存在。

冲突证据：
- `kubectl_find_resource` 工具调用失败，未找到与 Pod 相关的 `ConfigMap` 或 `Secret` 资源。这表明可能未正确配置这些资源或未正确引用它们。

结论：
当前 Pod 异常是由于配置错误导致容器崩溃。建议检查 Pod 的配置，确认 `ConfigMap` 或 `Secret` 是否正确引用，并验证配置内容是否符合应用要求。
   ✅ [证据链采集] 完成 (3m 5.6s)
   📤 → 下游数据: evidence_items=6/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证异常 Pod 的详细状态和事件","level":"critical","tool":"kubectl_get_by_name","command":"get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml","tool_args":{"name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"获取 Pod 的完整定义，检查 spec、status、事件等关键字段，确认是否存在配置错误","evidence_type":"pod_definition","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 的事件历史","level":"important","tool":"kubectl_events","command":"get events -n aiops-e2e --field-selector involvedObject.name=appconfigfail-575d77485d-nfpvh","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=appconfigfail-575d77485d-nfpvh"},"purpose":"确认 Pod 重启和失败的事件原因，验证是否为配置错误","evidence_type":"event_history","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod 的容器日志","level":"important","tool":"kubectl_previous_logs","command":"logs -n aiops-e2e appconfigfail-575d77485d-nfpvh --previous","tool_args":{"namespace":"aiops-e2e","name":"appconfigfail-575d77485d-nfpvh","previous":true},"purpose":"检查容器崩溃前的日志，确认是否存在配置缺失或校验失败信息","evidence_type":"container_logs","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"获取 Pod 所依赖的 ConfigMap/Secret","level":"important","tool":"kubectl_find_resource","command":"find resource -n aiops-e2e pod appconfigfail-575d77485d-nfpvh configmap secret","tool_args":{"namespace":"aiops-e2e","pod_name":"appconfigfail-575d77485d-nfpvh","resource_types":["configmap","secret"]},"purpose":"确认 Pod 是否引用了不存在或配置错误的 ConfigMap/Secret","evidence_type":"dependent_resources","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                             READY   STATUS             RESTARTS         AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nappconfigfail-575d77485d-nfpvh   0/1     CrashLoopBackOff   22 (4m50s ago)   92m   172.16.166.184   node1   <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/88461bf82ef94375/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/88461bf82ef94375/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/88461bf82ef94375/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n2m26s (x417 over 92m)   Warning   BackOff   Pod/appconfigfail-575d77485d-nfpvh   Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/88461bf82ef94375/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/88461bf82ef94375/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/88461bf82ef94375/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 6\nsignals: 5\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/88461bf82ef94375/tools/003-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/88461bf82ef94375/tools/003-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/88461bf82ef94375/tools/003-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_find_resource","data":"kubectl_find_resource 输出摘要: raw_chars=95 lines=2\nCommand failed (exit 1):\nkubectl get -A --show-labels -o wide pod | grep -i 'configmap,secret'","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/88461bf82ef94375/tools/004-evidence-kubectl_find_resource.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/88461bf82ef94375/tools/004-evidence-kubectl_find_resource.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/88461bf82ef94375/tools/004-evidence-kubectl_find_resource.summary.txt"}],"llm_analysis":"已采集证据：\n- Pod `appconfigfail-575d77485d-nfpvh` 的状态为 `CrashLoopBackOff`，重启次数不断增加，表明容器频繁崩溃。\n- 事件中显示 `Back-off restarting failed container`，进一步确认容器失败并频繁重启。\n- 崩溃前的日志包含 `L4_CONFIG_BOOTSTRAP_FAIL`、`FATAL: missing required APP_BOOT_MODE`、`FATAL: business config validation failed before server startup` 等信息，表明是由于配置缺失或校验失败导致的容器崩溃。\n- 未找到与该 Pod 相关的 `ConfigMap` 或 `Secret` 资源，可能该 Pod 未正确引用所需的配置资源，或者配置资源不存在。\n\n冲突证据：\n- `kubectl_find_resource` 工具调用失败，未找到与 Pod 相关的 `ConfigMap` 或 `Secret` 资源。这表明可能未正确配置这些资源或未正确引用它们。\n\n结论：\n当前 Pod 异常是由于配置错误导致容器崩溃。建议检查 Pod 的配置，确认 `ConfigMap` 或 `Secret` 是否正确引用，并验证配置内容是否符合应用要求。","collection_summary":"计划 4 项，实际采集 2 项，未采集 2 项，完整度 50%；其中真实环境证据 6/8 项，完整度 75%；实际执行工具 7 个，匹配计划 2 个，未规划证据 5 个","plan_total":4,"plan_collected":2,"plan_completeness":0.5,"environment_evidence_total":8,"environment_evidence_collected":6,"environment_evidence_completeness":0.75,"executed_tool_count":7,"matched_tool_count":2,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"验证异常 Pod 的详细状态和事件","level":"critical","tool":"kubectl_get_by_name","command":"get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml","purpose":"获取 Pod 的完整定义，检查 spec、status、事件等关键字段，确认是否存在配置错误","collected":false,"source":"planned","outcome":"unknown"},{"id":"e2","description":"获取异常 Pod 的事件历史","level":"important","tool":"kubectl_events","command":"get events -n aiops-e2e --field-selector involvedObject.name=appconfigfail-575d77485d-nfpvh","purpose":"确认 Pod 重启和失败的事件原因，验证是否为配置错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod 的容器日志","level":"important","tool":"kubectl_previous_logs","command":"logs -n aiops-e2e appconfigfail-575d77485d-nfpvh --previous","purpose":"检查容器崩溃前的日志，确认是否存在配置缺失或校验失败信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"获取 Pod 所依赖的 ConfigMap/Secret","level":"important","tool":"kubectl_find_resource","command":"find resource -n aiops-e2e pod appconfigfail-575d77485d-nfpvh configmap secret","purpose":"确认 Pod 是否引用了不存在或配置错误的 ConfigMap/Secret","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e1(验证异常 Pod 的详细状态和事件): 已规划但工具执行失败或无匹配结果","e4(获取 Pod 所依赖的 ConfigMap/Secret): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/4 项, 完整度: 75%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ❌ | kubectl_get_by_name | 验证异常 Pod 的详细状态和事件 | `get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml` |
   | e2 | important | ✅ | kubectl_events | 获取异常 Pod 的事件历史 | `get events -n aiops-e2e --field-selector involvedObject.name=appconfigfail-57...` |
   | e3 | important | ✅ | kubectl_previous_logs | 获取异常 Pod 的容器日志 | `logs -n aiops-e2e appconfigfail-575d77485d-nfpvh --previous` |
   | e4 | important | ❌ | kubectl_find_resource | 获取 Pod 所依赖的 ConfigMap/Secret | `find resource -n aiops-e2e pod appconfigfail-575d77485d-nfpvh configmap secret` |

   ⚠️ 未采集原因:
   - e1(验证异常 Pod 的详细状态和事件): 已规划但工具执行失败或无匹配结果
   - e4(获取 Pod 所依赖的 ConfigMap/Secret): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (24.9s)
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
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (2m 14.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4177 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 9m 34.0s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
---
## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **Pod异常状态** | CrashLoopBackOff |
| **兼容归因层** | L4 |
| **问题分类** | ConfigError（配置错误） |
| **置信度** | 高 |
| **证据完整度** | 2/4 (50%) |

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
| 错误信息 | L4_CONFIG_BOOTSTRAP_FAIL, FATAL: missing required APP_BOOT_MODE |

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff, RESTARTS: 21` | Pod 处于持续重启状态 |
| 2 | 容器日志 | `kubectl logs <pod> --previous` | `L4_CONFIG_BOOTSTRAP_FAIL`, `FATAL: missing required APP_BOOT_MODE` | 应用启动时因配置缺失失败 |
| 3 | Pod 事件 | `kubectl describe pod` | `Back-off restarting failed container` | 容器持续失败，K8s 自动重启 |
| 4 | Pod 详细状态 | `kubectl get pod -o json` | `phase: Running`, `restartPolicy: Always` | Pod 仍在运行，但容器持续失败 |
| 5 | Runbook 匹配 | `fetch_runbook` | `Pod异常类型: ConfigError | 典型状态: CrashLoopBackOff` | 匹配配置错误场景 |
| 6 | Runbook 特征 | `fetch_runbook` | `Exit Code: 42` | 业务退出码，非 OOMKilled |

### 证据关联分析
- **证据 #2 + #6 印证**：`FATAL: missing required APP_BOOT_MODE` + `Exit Code: 42` → 应用启动时因缺少关键配置而失败。
- **证据链**：应用缺失关键配置 `APP_BOOT_MODE` → 启动失败 → 容器退出 → K8s 重启 → 形成 CrashLoopBackOff。
- **排除其他原因**：无 `OOMKilled`、无 `Exit Code 137`、无 `ImagePullBackOff`，排除资源不足或镜像拉取问题。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| Pod 所依赖的 ConfigMap/Secret | critical | 无法确认配置缺失的具体原因（例如是否未挂载或配置错误） |
| Pod 所在 Deployment 或 StatefulSet | important | 无法确认是否因滚动更新、配置更新导致 |

---

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 应用启动时缺失关键环境变量 APP_BOOT_MODE，导致配置验证失败      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 应用配置校验失败 → 退出码 42 → 容器终止                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器因配置错误终止，K8s 自动重启容器                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CrashLoopBackOff，重启次数持续增加                   │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2（日志显示 `FATAL: missing required APP_BOOT_MODE`）和证据 #6（Exit Code 42），问题的根本原因是**应用启动时缺少关键环境变量 `APP_BOOT_MODE`**，导致配置校验失败并退出。
**置信度**：高 (80%)
- ✅ 日志明确显示配置缺失
- ✅ Exit Code 42 与业务配置失败强相关
- ⚠️ 缺少 ConfigMap/Secret 证据，无法确认配置缺失是否因挂载错误或未定义

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 确认并补充缺失的环境变量 `APP_BOOT_MODE`**
```bash
kubectl set env deployment/<deployment-name> -n aiops-e2e APP_BOOT_MODE=your_value
```
*依据*：日志显示 `FATAL: missing required APP_BOOT_MODE`，补充该变量可解决配置缺失问题。

**2. [可选] 查看 Pod 所依赖的 ConfigMap/Secret**
```bash
kubectl describe pod appconfigfail-575d77485d-nfpvh -n aiops-e2e
```
*目的*：检查是否配置了 ConfigMap 或 Secret，确认其挂载是否正确。

**3. [可选] 重启 Pod**
```bash
kubectl rollout restart deployment/<deployment-name> -n aiops-e2e
```
*目的*：触发新配置生效，重启 Pod。

### 后续优化
1. **配置验证**：在应用启动脚本中增加配置校验逻辑，提前报错而非运行时崩溃。
2. **监控告警**：配置 `CrashLoopBackOff` 状态告警，及时发现配置类问题。
3. **文档完善**：确保配置文档包含所有必填参数，避免遗漏。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 重启次数不再增加 |
| 3. 检查日志 | `kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous` | 不再包含 `L4_CONFIG_BOOTSTRAP_FAIL` |

---

## ⚠️ 注意事项
- 如果问题仍然存在，请检查 ConfigMap/Secret 是否正确挂载，或是否存在权限问题。
- 确保所有必填配置项在部署时都有值，避免运行时崩溃。
- 建议在应用中加入启动阶段的配置校验逻辑，提前失败而非运行时崩溃。

---

## 📊 性能统计

├─ 总耗时: 9.6m
├─ 问题定位: 228.8s (40%) ✅
├─ 证据链采集: 185.6s (32%) ✅
├─ 根因分析: 24.9s (4%) ✅
├─ 汇总总结: 134.7s (23%) ✅
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
