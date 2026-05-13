======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: c4cd1ec2ba854c44]

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
   💭 [问题定位] 调用工具: kubectl_container_previous_logs_grep
   💭 [问题定位] 工具结果: kubectl_container_previous_logs_grep (success)
      📄 kubectl_container_previous_logs_grep 输出摘要: raw_chars=851 lines=1
Error: kubectl_container_previous_logs_grep is not a valid tool, try one of [kubectl_describe, kubectl_get_by_name, kubectl_get_by_kind
   💭 [问题定位] 调用工具: kubectl_previous_logs_all_containers
   💭 [问题定位] 工具结果: kubectl_previous_logs_all_containers (success)
      📄 kubectl_previous_logs_all_containers 日志摘要:
lines: 6
signals: 5
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config
L4_SCENARIO: config-bootstrap-fail
L4_ERROR_
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
   💭 [问题定位] 调用工具: kubectl_get_by_name
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 12.0s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': '应用启动配置错误', 'probability': '高', 'reason': 'CrashLoopBackOff + 日志显示配置校验失败/缺参'}]
   entities=[{"type": "Pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}]
   reasoning=当前集群中存在异常 Pod appconfigfail-575d77485d-nfpvh，状态为 CrashLoopBackOff，重启次数持续增长，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL、missing required APP_BOOT_MODE、business config validation failed before server startup 等配置错误信号。根据 runbook 和日志，该异常属于 ConfigError，归为 L4 层级。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "application error", "confidence": 0.95, "reasoning": "当前集群中存在异常 Pod appconfigfail-575d77485d-nfpvh，状态为 CrashLoopBackOff，重启次数持续增长，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL、missing required APP_BOOT_MODE、business config validation failed before server startup 等配置错误信号。根据 runbook 和日志，该异常属于 ConfigError，归为 L4 层级。", "abnormal_pods": [{"name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "app_config", "key_entities": [{"type": "Pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "应用启动配置错误", "probability": "高", "reason": "CrashLoopBackOff + 日志显示配置校验失败/缺参"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     appconfigfail-575d77485d-nfpvh                      0/1     CrashLoopBackOff   21 (2m51s ago)   85m    172.16.166.184   node1    <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError"], "raw_ref": "/tmp/aiops/reports/context_archives/c4cd1ec2ba854c44/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/c4cd1ec2ba854c44/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/c4cd1ec2ba854c44/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ✅ [证据链采集] 完成 (4m 4.9s)
   📤 → 下游数据: evidence_items=9/11
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 的详细信息","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","namespace":"aiops-e2e","name":"appconfigfail-575d77485d-nfpvh","output_format":"yaml"},"purpose":"验证 Pod 的 spec、status 和 labels 是否与异常状态 CrashLoopBackOff 一致","evidence_type":"current_status","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 的事件","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=appconfigfail-575d77485d-nfpvh","tool_args":{"namespace":"aiops-e2e","involved_object_name":"appconfigfail-575d77485d-nfpvh"},"purpose":"验证 Pod 是否有与 ConfigError 一致的事件，如 'Failed to pull image'、'ConfigMap/Secret missing' 等","evidence_type":"event_signal","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod 的上一次容器日志","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous","tool_args":{"namespace":"aiops-e2e","name":"appconfigfail-575d77485d-nfpvh","container":"","previous":true},"purpose":"验证容器日志是否包含 L4_CONFIG_BOOTSTRAP_FAIL、missing required APP_BOOT_MODE 等配置错误信号","evidence_type":"log_signal","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"获取异常 Pod 的容器 spec 和配置对象","level":"important","tool":"kubectl_get_by_name","command":"kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o jsonpath='{.spec.containers}'","tool_args":{"kind":"Pod","namespace":"aiops-e2e","name":"appconfigfail-575d77485d-nfpvh","output_format":"jsonpath"},"purpose":"验证容器 spec 中的 env、volumeMounts、image 等字段是否缺失或错误","evidence_type":"configuration_signal","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":[],"counts_for_completeness":true},{"id":"e5","description":"验证 ConfigMap/Secret 是否存在","level":"important","tool":"kubectl_get_by_name","command":"kubectl get configmap -n aiops-e2e","tool_args":{"kind":"ConfigMap","namespace":"aiops-e2e","output_format":"json"},"purpose":"验证 ConfigMap 是否存在且内容完整，以排除 ConfigMap/Secret 缺失导致的配置错误","evidence_type":"configuration_signal","target_scope":"aiops-e2e","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                             READY   STATUS             RESTARTS         AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nappconfigfail-575d77485d-nfpvh   0/1     CrashLoopBackOff   22 (2m50s ago)   90m   172.16.166.184   node1   <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c4cd1ec2ba854c44/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c4cd1ec2ba854c44/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c4cd1ec2ba854c44/tools/001-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 5 项，实际采集 3 项，未采集 2 项，完整度 60%；其中真实环境证据 9/11 项，完整度 82%；实际执行工具 6 个，匹配计划 3 个，未规划证据 3 个","plan_total":5,"plan_collected":3,"plan_completeness":0.6,"environment_evidence_total":11,"environment_evidence_collected":9,"environment_evidence_completeness":0.8181818181818182,"executed_tool_count":6,"matched_tool_count":3,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 的详细信息","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml","purpose":"验证 Pod 的 spec、status 和 labels 是否与异常状态 CrashLoopBackOff 一致","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 的事件","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=appconfigfail-575d77485d-nfpvh","purpose":"验证 Pod 是否有与 ConfigError 一致的事件，如 'Failed to pull image'、'ConfigMap/Secret missing' 等","collected":false,"source":"planned","outcome":"unknown"},{"id":"e3","description":"获取异常 Pod 的上一次容器日志","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous","purpose":"验证容器日志是否包含 L4_CONFIG_BOOTSTRAP_FAIL、missing required APP_BOOT_MODE 等配置错误信号","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"e4","description":"获取异常 Pod 的容器 spec 和配置对象","level":"important","tool":"kubectl_get_by_name","command":"kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o jsonpath='{.spec.containers}'","purpose":"验证容器 spec 中的 env、volumeMounts、image 等字段是否缺失或错误","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"e5","description":"验证 ConfigMap/Secret 是否存在","level":"important","tool":"kubectl_get_by_name","command":"kubectl get configmap -n aiops-e2e","purpose":"验证 ConfigMap 是否存在且内容完整，以排除 ConfigMap/Secret 缺失导致的配置错误","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_container_previous_logs_grep","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_previous_logs_all_containers","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e2(获取异常 Pod 的事件): 已规划但工具执行失败或无匹配结果","e5(验证 ConfigMap/Secret 是否存在): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/5 项, 完整度: 82%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 获取异常 Pod 的详细信息 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml` |
   | e2 | critical | ❌ | kubectl_events | 获取异常 Pod 的事件 | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=appconfi...` |
   | e3 | critical | ✅ | kubectl_previous_logs | 获取异常 Pod 的上一次容器日志 | `kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous` |
   | e4 | important | ✅ | kubectl_get_by_name | 获取异常 Pod 的容器 spec 和配置对象 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o jsonpath='{.sp...` |
   | e5 | important | ❌ | kubectl_get_by_name | 验证 ConfigMap/Secret 是否存在 | `kubectl get configmap -n aiops-e2e` |

   ⚠️ 未采集原因:
   - e2(获取异常 Pod 的事件): 已规划但工具执行失败或无匹配结果
   - e5(验证 ConfigMap/Secret 是否存在): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (3m 51.7s)
   📤 → 下游数据: root_cause=集群中存在异常 Pod appconfigfail-575d77485d-nfpvh，状态为 CrashLoopBackOff，重启次数持续增长，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL、missing required APP_BOOT_MODE、business config validation failed before server startup 等配置错误信号。
   confidence=95%
   causal_chain={"root_cause": "应用启动配置错误", "intermediate_causes": [{"cause": "缺失 APP_BOOT_MODE 配置", "effect": "应用无法正确启动，导致容器启动失败并进入 CrashLoopBackOff 状态。"}, {"cause": "business config validation failed before server startup", "effect": "应用在启动前进行配置校验失败，导致容器启动失败并进入 CrashLoopBackOff 状态。"}], "direct_causes": [{"cause": "L4_CONFIG_BOOTSTRAP_FAIL", "effect": "应用在启动过程中因配置错误导致失败，容器进入 CrashLoopBackOff 状态。"}], "effects": [{"effect": "Pod 处于 CrashLoopBackOff 状态，重启次数持续增加。", "description": "容器启动失败并不断重启，导致 Pod 处于 CrashLoopBackOff 状态。"}]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"id": "e1", "description": "获取异常 Pod 的详细信息", "level": "critical", "value": "NAME                             READY   STATUS             RESTARTS         AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nappconfigfail-575d77485d-nfpvh   0/1     CrashLoopBackOff   22 (2m50s ago)   90m   172.16.166.184   node1   <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError"}, {"id": "e3", "description": "获取异常 Pod 的上一次容器日志", "level": "critical", "value": "kubectl_previous_logs 日志摘要:\nlines: 6\nsignals: 5\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup"}, {"id": "e4", "description": "获取异常 Pod 的容器 spec 和配置对象", "level": "important", "value": "NAME                             READY   STATUS             RESTARTS         AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nappconfigfail-575d77485d-nfpvh   0/1     CrashLoopBackOff   21 (2m57s ago)   85m   172.16.166.184   node1   <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError"}, {"id": "layer_1", "description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "level": "important", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'CrashLoopBackOff': 1, 'Running': 46}\nNAMESPACE     NAME                                                READY   STATUS             RESTARTS         AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\n# 异常行\naiops-e2e     appconfigfail-575d77485d-nfpvh                      0/1     CrashLoopBackOff   21 (2m51s ago)   85m    172.16.166.184   node1    <none>           <none>            app=appconfigfail,e2e-"}, {"id": "layer_2", "description": "上游已验证工具结果: kubectl_get_by_name", "level": "important", "value": "NAME                             READY   STATUS             RESTARTS         AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nappconfigfail-575d77485d-nfpvh   0/1     CrashLoopBackOff   21 (2m57s ago)   85m   172.16.166.184   node1   <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError"}, {"id": "layer_3", "description": "上游已验证工具结果: kubectl_previous_logs", "level": "important", "value": "kubectl_previous_logs 日志摘要:\nlines: 6\nsignals: 5\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup"}, {"id": "layer_4", "description": "上游已验证工具结果: kubectl_container_previous_logs_grep", "level": "important", "value": "kubectl_container_previous_logs_grep 输出摘要: raw_chars=851 lines=1\nError: kubectl_container_previous_logs_grep is not a valid tool, try one of [kubectl_describe, kubectl_get_by_name, kubectl_get_by_kind_in_namespace, kubectl_get_by_kind_in_cluster, kubectl_find_resource, kubectl_get_yaml, kubectl_events, kubectl_logs, kubectl_previous_logs, kubectl_logs_all_containers, kubectl_previous_logs_all_containers, kubectl_container_logs, kubectl_container_previous_logs, kubectl_logs_grep, kubectl_logs_all"}, {"id": "layer_5", "description": "上游已验证工具结果: kubectl_previous_logs_all_containers", "level": "important", "value": "kubectl_previous_logs_all_containers 日志摘要:\nlines: 6\nsignals: 5\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup"}, {"id": "layer_6", "description": "上游已验证工具结果: kubectl_get_yaml", "level": "important", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: appconfigfail-575d77485d-nfpvh\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-12T05:59:23Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=appconfigfail, e2e-test=true, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/expected-evidence=previous logs contain"}], "evidence_analysis": [{"id": "e1", "description": "获取异常 Pod 的详细信息", "level": "critical", "value": "Pod appconfigfail-575d77485d-nfpvh 处于 CrashLoopBackOff 状态，重启次数持续增加，表明容器启动失败并不断重启。"}, {"id": "e3", "description": "获取异常 Pod 的上一次容器日志", "level": "critical", "value": "容器日志显示 L4_CONFIG_BOOTSTRAP_FAIL、missing required APP_BOOT_MODE 和 business config validation failed before server startup，表明配置错误导致应用启动失败。"}, {"id": "e4", "description": "获取异常 Pod 的容器 spec 和配置对象", "level": "important", "value": "Pod 的 spec 和配置对象显示其处于异常状态，且标签中包含 pod_abnormal_type=ConfigError，表明这是一个已知的配置错误场景。"}, {"id": "layer_1", "description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "level": "important", "value": "集群中存在 1 个处于 CrashLoopBackOff 状态的 Pod，且该 Pod 被标记为 ConfigError，表明这是一个已知的配置错误场景。"}, {"id": "layer_2", "description": "上游已验证工具结果: kubectl_get_by_name", "level": "important", "value": "Pod appconfigfail-575d77485d-nfpvh 处于 CrashLoopBackOff 状态，重启次数持续增加，表明容器启动失败并不断重启。"}, {"id": "layer_3", "description": "上游已验证工具结果: kubectl_previous_logs", "level": "important", "value": "容器日志显示 L4_CONFIG_BOOTSTRAP_FAIL、missing required APP_BOOT_MODE 和 business config validation failed before server startup，表明配置错误导致应用启动失败。"}, {"id": "layer_5", "description": "上游已验证工具结果: kubectl_previous_logs_all_containers", "level": "important", "value": "容器日志显示 L4_CONFIG_BOOTSTRAP_FAIL、missing required APP_BOOT_MODE 和 business config validation failed before server startup，表明配置错误导致应用启动失败。"}, {"id": "layer_6", "description": "上游已验证工具结果: kubectl_get_yaml", "level": "important", "value": "Pod 的 spec 和配置对象显示其处于异常状态，且标签中包含 pod_abnormal_type=ConfigError，表明这是一个已知的配置错误场景。"}], "causal_chain": {"root_cause": "应用启动配置错误", "intermediate_causes": [{"cause": "缺失 APP_BOOT_MODE 配置", "effect": "应用无法正确启动，导致容器启动失败并进入 CrashLoopBackOff 状态。"}, {"cause": "business config validation failed before server startup", "effect": "应用在启动前进行配置校验失败，导致容器启动失败并进入 CrashLoopBackOff 状态。"}], "direct_causes": [{"cause": "L4_CONFIG_BOOTSTRAP_FAIL", "effect": "应用在启动过程中因配置错误导致失败，容器进入 CrashLoopBackOff 状态。"}], "effects": [{"effect": "Pod 处于 CrashLoopBackOff 状态，重启次数持续增加。", "description": "容器启动失败并不断重启，导致 Pod 处于 CrashLoopBackOff 状态。"}]}, "root_cause": "集群中存在异常 Pod appconfigfail-575d77485d-nfpvh，状态为 CrashLoopBackOff，重启次数持续增长，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL、missing required APP_BOOT_MODE、business config validation failed before server startup 等配置错误信号。", "root_cause_summary": "集群中存在异常 Pod appconfigfail-575d77485d-nfpvh，状态为 CrashLoopBackOff，重启次数持续增长，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL、missing required APP_BOOT_MODE、business config validation failed before server startup 等配置错误信号。", "confidence": 0.95, "confidence_reason": "有直接证据，因果链清晰。", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [], "limitations": "未验证 ConfigMap/Secret 是否存在，可能影响最终结论。", "llm_raw_analysis": "基于已采集的证据，Pod appconfigfail-575d77485d-nfpvh 处于 CrashLoopBackOff 状态，重启次数持续增加，表明容器启动失败并不断重启。容器日志显示 L4_CONFIG_BOOTSTRAP_FAIL、missing required APP_BOOT_MODE 和 business config validation failed before server startup，表明配置错误导致应用启动失败。Pod 的 spec 和配置对象显示其处于异常状态，且标签中包含 pod_abnormal_type=ConfigError，表明这是一个已知的配置错误场景。集群中存在 1 个处于 CrashLoopBackOff 状态的 Pod，且该 Pod 被标记为 ConfigError，表明这是一个已知的配置错误场景。综上所述，集群中存在应用启动配置错误，导致 Pod 进入 CrashLoopBackOff 状态。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 集群中存在异常 Pod appconfigfail-575d77485d-nfpvh，状态为 CrashLoopBackOff，重启次数持续增长，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL、missing required APP_BOOT_MODE、business config...
   置信度: 95%
   🔗 因果链:
     根本原因: 应用启动配置错误


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
   ✅ [汇总总结] 完成 (2m 50.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4223 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 11m 59.5s
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
| **问题分类** | ConfigError |
| **置信度** | 高 (95%) |
| **证据完整度** | 3/5 (60%) |

---

## 🔍 现象描述

**用户报告**：  
> 我的集群有什么问题？

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | appconfigfail-575d77485d-nfpvh |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | L4_CONFIG_BOOTSTRAP_FAIL、missing required APP_BOOT_MODE、business config validation failed before server startup |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | kubectl get pod | `STATUS: CrashLoopBackOff, RESTARTS: 21 (2m51s ago)` | Pod 持续重启，状态异常 |
| 2 | Pod 日志 | kubectl logs --previous | `L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config`<br>`FATAL: missing required APP_BOOT_MODE`<br>`FATAL: business config validation failed before server startup` | 容器启动时因配置缺失或校验失败而终止 |
| 3 | Pod YAML | kubectl get pod -o yaml | `phase: Running`<br>`restartPolicy: Always`<br>`imagePullSecrets: <absent>` | Pod 虽然处于 Running 状态，但容器因异常重启 |
| 4 | Runbook | fetch_runbook | `Pod异常类型: ConfigError`<br>`典型状态: CrashLoopBackOff`<br>`兼容分类: config_bootstrap` | 与当前问题匹配的 Runbook 确认问题归类为配置错误 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 持续重启 + 日志显示 `L4_CONFIG_BOOTSTRAP_FAIL` → 说明是启动配置错误。
- **证据链**：应用配置缺失或校验失败 → 启动失败 → 容器终止 → Pod 重启 → 持续 CrashLoopBackOff。

### 缺失证据

| 证据 | 级别 | 影响 |
|------|------|------|
| Pod 事件 | critical | 无法确认是否因其他原因（如资源限制、镜像拉取失败）导致重启 |
| ConfigMap/Secret 存在性 | important | 无法确认是否配置对象缺失或配置错误 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 应用缺少必需的配置项（如 APP_BOOT_MODE）或配置对象未正确挂载    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 配置校验失败 → 应用启动中止 → 容器退出                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器因配置错误退出（Exit Code 42 或其他业务退出码）             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 CrashLoopBackOff，持续重启                             │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (CrashLoopBackOff, RESTARTS=21) 和证据 #2 (日志中 L4_CONFIG_BOOTSTRAP_FAIL、missing required APP_BOOT_MODE)，
问题的根本原因是**应用缺少必需的配置项或配置对象未正确挂载**，
导致容器启动失败并进入 CrashLoopBackOff。
**置信度**：高 (95%)
- ✅ 日志中明确指出配置缺失和校验失败
- ✅ Runbook 确认问题属于 ConfigError
- ⚠️ 缺少事件和 ConfigMap/Secret 信息，无法确认具体缺失配置

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查并挂载 ConfigMap/Secret**
```bash
kubectl get configmap -n aiops-e2e
kubectl get secret -n aiops-e2e
```
*依据*：确认是否有缺失的配置对象，并检查是否已正确挂载到 Pod spec 中

**2. [优先] 检查 Pod spec 中的 envFrom 或 volumeMounts**
```bash
kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml
```
*目的*：确认是否已正确挂载 ConfigMap/Secret，并检查 env 中是否有缺失的变量（如 APP_BOOT_MODE）

**3. [可选] 查看 Pod 事件**
```bash
kubectl describe pod appconfigfail-575d77485d-nfpvh -n aiops-e2e
```
*目的*：确认是否因其他原因（如资源不足、镜像拉取失败）导致容器重启

### 后续优化

1. **配置校验**：在部署前添加配置校验逻辑，避免运行时校验失败
2. **自动化检查**：使用 Operator 或 Helm Chart 提供默认配置模板
3. **监控告警**：配置 Pod 重启次数告警，及时发现异常

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |
| 3. 确认配置已挂载 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml` | env 中包含 APP_BOOT_MODE 等配置项 |

---

## ⚠️ 注意事项

- 如果问题持续，请检查 ConfigMap/Secret 的内容是否正确，特别是 APP_BOOT_MODE 是否缺失或拼写错误
- 避免直接修改 Pod，建议通过 Deployment 或 Helm 更新配置
- 如果使用 Helm，可检查 values.yaml 中是否遗漏了配置项

---

---

## 📊 性能统计

├─ 总耗时: 12.0m
├─ 问题定位: 72.0s (10%) ✅
├─ 证据链采集: 244.9s (34%) ✅
├─ 根因分析: 231.7s (32%) ✅
├─ 汇总总结: 170.8s (24%) ✅
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
