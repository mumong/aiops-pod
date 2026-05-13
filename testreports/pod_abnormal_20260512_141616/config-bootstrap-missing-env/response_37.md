======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: c9a797439904436f]

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
   💭 [问题定位] 调用工具: kubectl_get_by_name
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (2m 9.0s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': '应用配置缺失', 'probability': '高', 'reason': '容器日志显示 L4_CONFIG_BOOTSTRAP_FAIL，且 missing required APP_BOOT_MODE、business config validation failed before server startup 等信号，确认是应用配置缺失导致的启动失败。'}, {'scenario': 'ConfigMap/Secret 键名错误', 'probability': '中', 'reason': '可能配置的 ConfigMap 或 Secret 中的键名拼写错误，导致应用启动前配置校验失败。'}]
   entities=[{"type": "Pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}]
   reasoning=当前环境中的活跃异常对象为 Pod 'appconfigfail-575d77485d-nfpvh'，状态为 CrashLoopBackOff，重启次数持续增加。容器日志显示 L4_CONFIG_BOOTSTRAP_FAIL、missing required APP_BOOT_MODE、business config validation failed before server startup 等配置错误信号。根据 runbook 和日志分析，这是典型的 ConfigError 类型，符合 L4 层级的应用配置错误。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "application error", "confidence": 0.5, "reasoning": "当前环境中的活跃异常对象为 Pod 'appconfigfail-575d77485d-nfpvh'，状态为 CrashLoopBackOff，重启次数持续增加。容器日志显示 L4_CONFIG_BOOTSTRAP_FAIL、missing required APP_BOOT_MODE、business config validation failed before server startup 等配置错误信号。根据 runbook 和日志分析，这是典型的 ConfigError 类型，符合 L4 层级的应用配置错误。", "abnormal_pods": [{"name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "app_config", "key_entities": [{"type": "Pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "应用配置缺失", "probability": "高", "reason": "容器日志显示 L4_CONFIG_BOOTSTRAP_FAIL，且 missing required APP_BOOT_MODE、business config validation failed before server startup 等信号，确认是应用配置缺失导致的启动失败。"}, {"scenario": "ConfigMap/Secret 键名错误", "probability": "中", "reason": "可能配置的 ConfigMap 或 Secret 中的键名拼写错误，导致应用启动前配置校验失败。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     appconfigfail-575d77485d-nfpvh                      0/1     CrashLoopBackOff   21 (3m16s ago)   85m    172.16.166.184   node1    <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError"], "raw_ref": "/tmp/aiops/reports/context_archives/c9a797439904436f/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/c9a797439904436f/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/c9a797439904436f/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
77s (x417 over 91m)   Warning   BackOff   Pod/appconfigfail-575d77485d-nfpvh   Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: appconfigfail-575d77485d-nfpvh
namespace: aiops-e2e
creationTimestamp: 2026-05-12T05:59:23Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finali
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 6
signals: 5
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config
L4_SCENARIO: config-bootstrap-fail
L4_ERROR_TYPE: applicati
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
- kubectl_events 显示 Pod 持续因配置错误重启（Back-off restarting failed container）。
- kubectl_get_yaml 显示容器状态为 CrashLoopBackOff，Exit Code 为 42，且 Ready 状态为 False。
- kubectl_previous_logs 显示日志中包含 L4_CONFIG_BOOTSTRAP_FAIL 和 missing required APP_BOOT_MODE。
- kubectl_describe 显示容器因 Error 崩溃，Exit Code 为 42，且事件记录显示重启失败。

未采集证据：
- 无。

冲突证据：
- 无。

结论：当前 Pod `appconfigfail-575d77485d-nfpvh` 处于 CrashLoopBackOff 状态，容器因配置错误（缺少 APP_BOOT_MODE）无法启动，符合 L4 层级的应用配置错误。
   ✅ [证据链采集] 完成 (4m 9.3s)
   📤 → 下游数据: evidence_items=10/10
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 的详细事件日志以确认配置错误原因","level":"critical","tool":"kubectl_events","command":"get events --namespace=aiops-e2e --field-selector=involvedObject.name=appconfigfail-575d77485d-nfpvh","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=appconfigfail-575d77485d-nfpvh"},"purpose":"验证异常 Pod 的事件日志，确认配置错误的具体原因","evidence_type":"event_log","target_scope":"aiops-e2e","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 的完整 YAML 配置以检查配置缺失","level":"critical","tool":"kubectl_get_yaml","command":"get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml","tool_args":{"name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e","output":"yaml"},"purpose":"验证异常 Pod 的 YAML 配置，检查是否存在 env/ConfigMap/Secret 配置缺失","evidence_type":"config_yaml","target_scope":"aiops-e2e","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod 的容器上次失败日志以确认配置错误","level":"important","tool":"kubectl_previous_logs","command":"logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous","tool_args":{"name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e","container":"appconfigfail","previous":true},"purpose":"验证异常 Pod 的容器上次失败日志，确认配置错误的具体信息","evidence_type":"container_logs","target_scope":"aiops-e2e","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"获取异常 Pod 的描述信息以确认 CrashLoopBackOff 的详细原因","level":"important","tool":"kubectl_describe","command":"describe pod appconfigfail-575d77485d-nfpvh -n aiops-e2e","tool_args":{"name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e"},"purpose":"验证异常 Pod 的描述信息，确认 CrashLoopBackOff 的详细原因","evidence_type":"describe_pod","target_scope":"aiops-e2e","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_events","data":"kubectl_events 摘要:\n77s (x417 over 91m)   Warning   BackOff   Pod/appconfigfail-575d77485d-nfpvh   Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c9a797439904436f/tools/001-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c9a797439904436f/tools/001-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c9a797439904436f/tools/001-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: appconfigfail-575d77485d-nfpvh\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-12T05:59:23Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=appconfigfail, e2e-test=true, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/expected-evidence=previous logs contain L4_CONFIG_BOOTSTRAP_FAIL and missing required APP_BOOT_MODE, aiops.e2e/expected-status=CrashLoopBackOff|CreateContainerConfigError|CreateContainerError, aiops.e2e/runbook=pod-config-error.md\nownerReferences: ReplicaSet/appconfigfail-575d77485d\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=22 reason=CrashLoopBackOff exitCode=42\n  message: back-off 5m0s restarting failed container=app pod=appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)\nvolumes:\n- {\"name\": \"kube-api-access-r4t7x\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c9a797439904436f/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c9a797439904436f/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c9a797439904436f/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 6\nsignals: 5\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c9a797439904436f/tools/003-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c9a797439904436f/tools/003-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c9a797439904436f/tools/003-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: appconfigfail-575d77485d-nfpvh\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键状态/事件:\n                  aiops.e2e/expected-status: CrashLoopBackOff|CreateContainerConfigError|CreateContainerError\n    State:          Waiting\n      Reason:       CrashLoopBackOff\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42\n  Warning  BackOff  96s (x417 over 91m)  kubelet  Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c9a797439904436f/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c9a797439904436f/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c9a797439904436f/tools/004-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"已采集证据：\n- kubectl_events 显示 Pod 持续因配置错误重启（Back-off restarting failed container）。\n- kubectl_get_yaml 显示容器状态为 CrashLoopBackOff，Exit Code 为 42，且 Ready 状态为 False。\n- kubectl_previous_logs 显示日志中包含 L4_CONFIG_BOOTSTRAP_FAIL 和 missing required APP_BOOT_MODE。\n- kubectl_describe 显示容器因 Error 崩溃，Exit Code 为 42，且事件记录显示重启失败。\n\n未采集证据：\n- 无。\n\n冲突证据：\n- 无。\n\n结论：当前 Pod `appconfigfail-575d77485d-nfpvh` 处于 CrashLoopBackOff 状态，容器因配置错误（缺少 APP_BOOT_MODE）无法启动，符合 L4 层级的应用配置错误。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 10/10 项，完整度 100%；实际执行工具 9 个，匹配计划 4 个，未规划证据 5 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":10,"environment_evidence_collected":10,"environment_evidence_completeness":1.0,"executed_tool_count":9,"matched_tool_count":4,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 的详细事件日志以确认配置错误原因","level":"critical","tool":"kubectl_events","command":"get events --namespace=aiops-e2e --field-selector=involvedObject.name=appconfigfail-575d77485d-nfpvh","purpose":"验证异常 Pod 的事件日志，确认配置错误的具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 的完整 YAML 配置以检查配置缺失","level":"critical","tool":"kubectl_get_yaml","command":"get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml","purpose":"验证异常 Pod 的 YAML 配置，检查是否存在 env/ConfigMap/Secret 配置缺失","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod 的容器上次失败日志以确认配置错误","level":"important","tool":"kubectl_previous_logs","command":"logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous","purpose":"验证异常 Pod 的容器上次失败日志，确认配置错误的具体信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"获取异常 Pod 的描述信息以确认 CrashLoopBackOff 的详细原因","level":"important","tool":"kubectl_describe","command":"describe pod appconfigfail-575d77485d-nfpvh -n aiops-e2e","purpose":"验证异常 Pod 的描述信息，确认 CrashLoopBackOff 的详细原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_container_previous_logs_grep","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_events | 获取异常 Pod 的详细事件日志以确认配置错误原因 | `get events --namespace=aiops-e2e --field-selector=involvedObject.name=appconf...` |
   | e2 | critical | ✅ | kubectl_get_yaml | 获取异常 Pod 的完整 YAML 配置以检查配置缺失 | `get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml` |
   | e3 | important | ✅ | kubectl_previous_logs | 获取异常 Pod 的容器上次失败日志以确认配置错误 | `logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous` |
   | e4 | important | ✅ | kubectl_describe | 获取异常 Pod 的描述信息以确认 CrashLoopBackOff 的详细原因 | `describe pod appconfigfail-575d77485d-nfpvh -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 52.7s)
   📤 → 下游数据: root_cause=应用配置缺失导致容器启动失败，具体表现为 L4_CONFIG_BOOTSTRAP_FAIL 和 missing required APP_BOOT_MODE。
   confidence=90%
   causal_chain={"root_cause": "应用配置缺失", "intermediate_causes": ["容器日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和 missing required APP_BOOT_MODE", "容器状态为 CrashLoopBackOff，Exit Code 为 42"], "direct_causes": ["Pod 持续因配置错误重启，事件显示 Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)"]}
   rca_analysis={"phenomenon": "当前集群中 Pod 'appconfigfail-575d77485d-nfpvh' 处于 CrashLoopBackOff 状态，容器因配置错误无法正常启动。容器日志显示配置缺失和校验失败，导致应用启动失败。", "evidence_inventory": [{"tool": "kubectl_events", "description": "Pod 持续因配置错误重启，事件显示 Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)", "value": "77s (x417 over 91m)   Warning   BackOff   Pod/appconfigfail-575d77485d-nfpvh   Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)"}, {"tool": "kubectl_get_yaml", "description": "Pod 配置显示容器状态为 CrashLoopBackOff，Exit Code 为 42，Ready 状态为 False。", "value": "kind: Pod\nname: appconfigfail-575d77485d-nfpvh\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-12T05:59:23Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=appconfigfail, e2e-test=true, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/expected-evidence=previous logs contain"}, {"tool": "kubectl_previous_logs", "description": "容器上次失败日志显示配置缺失和校验失败，导致应用启动失败。", "value": "lines: 6\nsignals: 5\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup"}, {"tool": "kubectl_describe", "description": "容器因 Error 崩溃，Exit Code 为 42，事件记录显示重启失败。", "value": "name: appconfigfail-575d77485d-nfpvh\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键状态/事件:\n                  aiops.e2e/expected-status: CrashLoopBackOff|CreateContainerConfigError|CreateContainerError\n    State:          Waiting\n      Reason:       CrashLoopBackOff\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42\n  Warning  BackOff  96s (x417 over 91m)  kubelet  Back-off restarting failed container app in pod appconfigfail-575d774"}], "evidence_analysis": [{"tool": "kubectl_events", "analysis": "Pod 持续因配置错误重启，事件显示 Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)"}, {"tool": "kubectl_get_yaml", "analysis": "Pod 配置显示容器状态为 CrashLoopBackOff，Exit Code 为 42，Ready 状态为 False。"}, {"tool": "kubectl_previous_logs", "analysis": "容器上次失败日志显示配置缺失和校验失败，导致应用启动失败。"}, {"tool": "kubectl_describe", "analysis": "容器因 Error 崩溃，Exit Code 为 42，事件记录显示重启失败。"}], "causal_chain": {"root_cause": "应用配置缺失", "intermediate_causes": ["容器日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和 missing required APP_BOOT_MODE", "容器状态为 CrashLoopBackOff，Exit Code 为 42"], "direct_causes": ["Pod 持续因配置错误重启，事件显示 Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)"]}, "root_cause": "应用配置缺失导致容器启动失败，具体表现为 L4_CONFIG_BOOTSTRAP_FAIL 和 missing required APP_BOOT_MODE。", "root_cause_summary": "应用配置缺失导致容器启动失败，具体表现为 L4_CONFIG_BOOTSTRAP_FAIL 和 missing required APP_BOOT_MODE。", "confidence": 0.9, "confidence_reason": "有直接证据表明应用配置缺失导致容器启动失败，因果链清晰。", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [{"cause": "ConfigMap/Secret 键名错误", "probability": "中", "reason": "可能配置的 ConfigMap 或 Secret 中的键名拼写错误，导致应用启动前配置校验失败。"}], "limitations": "无", "llm_raw_analysis": "已采集证据：\n- kubectl_events 显示 Pod 持续因配置错误重启（Back-off restarting failed container）。\n- kubectl_get_yaml 显示容器状态为 CrashLoopBackOff，Exit Code 为 42，且 Ready 状态为 False。\n- kubectl_previous_logs 显示日志中包含 L4_CONFIG_BOOTSTRAP_FAIL 和 missing required APP_BOOT_MODE。\n- kubectl_describe 显示容器因 Error 崩溃，Exit Code 为 42，且事件记录显示重启失败。\n\n未采集证据：\n- 无。\n\n冲突证据：\n- 无。\n\n结论：当前 Pod `appconfigfail-575d77485d-nfpvh` 处于 CrashLoopBackOff 状态，容器因配置错误（缺少 APP_BOOT_MODE）无法启动，符合 L4 层级的应用配置错误。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 应用配置缺失导致容器启动失败，具体表现为 L4_CONFIG_BOOTSTRAP_FAIL 和 missing required APP_BOOT_MODE。
   置信度: 90%
   🔗 因果链:
     根本原因: 应用配置缺失


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (2m 0.6s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3880 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 10m 11.6s
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
| **问题分类** | ConfigError（应用配置缺失） |
| **置信度** | 高 (90%) |
| **证据完整度** | 4/4 (100%) |

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
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff, RESTARTS: 21` | Pod 因配置错误持续重启 |
| 2 | 容器日志 | `kubectl logs <pod> --previous` | `L4_CONFIG_BOOTSTRAP_FAIL`, `missing required APP_BOOT_MODE`, `business config validation failed before server startup` | 应用启动前配置校验失败 |
| 3 | Pod 事件 | `kubectl events` | `Warning: Back-off restarting failed container` | 容器持续失败，触发 CrashLoopBackOff |
| 4 | Pod YAML | `kubectl get pod -o yaml` | `labels: pod_abnormal_type=ConfigError` | 明确标记为配置错误类型 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 持续重启 + 日志显示配置缺失 → 应用配置缺失是根本原因
- **证据链**：应用缺少必须的配置项（如 `APP_BOOT_MODE`） → 启动时校验失败 → 容器退出 → Pod 重启

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 应用缺少必须的配置项（如 APP_BOOT_MODE）                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 应用启动时进行配置校验 → 发现缺失配置 → 抛出 fatal 错误          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器启动失败（Exit Code 42）                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 CrashLoopBackOff，持续重启                             │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2（容器日志显示 `L4_CONFIG_BOOTSTRAP_FAIL`、`missing required APP_BOOT_MODE`）和证据 #4（Pod 标签 `pod_abnormal_type=ConfigError`），问题的根本原因是**应用缺少必要的配置项（如 `APP_BOOT_MODE`）**，导致容器启动失败并持续重启。

**置信度**：高 (90%)
- ✅ 日志明确指出 `L4_CONFIG_BOOTSTRAP_FAIL`
- ✅ Pod 标签标记为 ConfigError
- ✅ 事件显示容器持续重启

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查并补充 ConfigMap/Secret 中的缺失配置项**
```bash
kubectl get configmap -n aiops-e2e
kubectl get secret -n aiops-e2e
```
*依据*：确认配置对象是否存在缺失的 `APP_BOOT_MODE` 或其他关键配置项。

**2. [优先] 编辑 ConfigMap/Secret，补充缺失的配置项**
```bash
kubectl edit configmap <configmap-name> -n aiops-e2e
# 或
kubectl edit secret <secret-name> -n aiops-e2e
```
*依据*：在配置对象中添加缺失的 `APP_BOOT_MODE` 或其他业务所需的配置项。

**3. [可选] 重新部署应用以加载新配置**
```bash
kubectl rollout restart deployment/<deployment-name> -n aiops-e2e
```
*目的*：触发 Pod 重建并加载新的配置。

### 后续优化

1. **配置校验机制**：在应用启动脚本中增加配置校验逻辑，提前报错而非运行时崩溃。
2. **自动化测试**：集成配置完整性检查到 CI/CD 流程。
3. **监控与告警**：监控 `CrashLoopBackOff` 事件，及时发现配置问题。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |
| 3. 检查容器日志 | `kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e` | 无配置错误日志 |

---

## ⚠️ 注意事项

- 如果配置项已存在，可能是键名拼写错误或命名空间不匹配，需进一步排查。
- 建议使用 `kubectl describe pod` 检查容器的 `Last State` 和 `Exit Code` 以确认修复效果。
- 如果问题持续，建议使用 `kubectl logs --previous` 查看最后一次失败日志。

---

## 📊 性能统计

├─ 总耗时: 10.2m
├─ 问题定位: 129.0s (21%) ✅
├─ 证据链采集: 249.3s (41%) ✅
├─ 根因分析: 112.7s (18%) ✅
├─ 汇总总结: 120.6s (20%) ✅
├─ LLM 调用: 5 次
└─ 工具调用: 13 次
```

📋 诊断追踪

- **核心 Runbook**: pod-config-error
- **参考 Runbook**: pod-config-error
- **工具调用**: 13 次
- **LLM 调用**: 5 次


======================================================================
✅ 诊断完成!
======================================================================
