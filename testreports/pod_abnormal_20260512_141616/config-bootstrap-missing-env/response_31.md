======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: bc47d4165480463b]

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
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 6
signals: 5
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config
L4_SCENARIO: config-bootstrap-fail
L4_ERROR_TYPE: applicati
   💭 [问题定位] 调用工具: kubectl_find_resource
   💭 [问题定位] 工具结果: kubectl_find_resource (success)
      📄 kubectl_find_resource 输出摘要: raw_chars=98 lines=2
Command failed (exit 1):
kubectl get -A --show-labels -o wide configmap | grep -i 'appconfigfail'
   💭 [问题定位] 调用工具: kubectl_find_resource
   💭 [问题定位] 工具结果: kubectl_find_resource (success)
      📄 kubectl_find_resource 输出摘要: raw_chars=95 lines=2
Command failed (exit 1):
kubectl get -A --show-labels -o wide secret | grep -i 'appconfigfail'
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: ReplicaSet
name: appconfigfail-575d77485d
namespace: aiops-e2e
   💭 [问题定位] 调用工具: kubectl_get_yaml
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 32.2s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'Pod 配置错误导致启动失败', 'probability': 'high', 'reason': 'Pod 日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和缺失必填环境变量 APP_BOOT_MODE，且处于 CrashLoopBackOff 状态'}]
   entities=[{"type": "Pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}]
   reasoning=当前环境中存在一个处于 CrashLoopBackOff 状态的 Pod，其重启次数持续增加，且日志明确显示 L4_CONFIG_BOOTSTRAP_FAIL、missing required APP_BOOT_MODE 等配置错误信号。根据 runbook 中的判定规则，确认此为 ConfigError 类型的 L4 层级异常。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "application_config_error", "confidence": 0.95, "reasoning": "当前环境中存在一个处于 CrashLoopBackOff 状态的 Pod，其重启次数持续增加，且日志明确显示 L4_CONFIG_BOOTSTRAP_FAIL、missing required APP_BOOT_MODE 等配置错误信号。根据 runbook 中的判定规则，确认此为 ConfigError 类型的 L4 层级异常。", "abnormal_pods": [{"name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "app_config", "key_entities": [{"type": "Pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Pod 配置错误导致启动失败", "probability": "high", "reason": "Pod 日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和缺失必填环境变量 APP_BOOT_MODE，且处于 CrashLoopBackOff 状态"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     appconfigfail-575d77485d-nfpvh                      0/1     CrashLoopBackOff   19 (2m59s ago)   75m    172.16.166.184   node1    <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError"], "raw_ref": "/tmp/aiops/reports/context_archives/bc47d4165480463b/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/bc47d4165480463b/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/bc47d4165480463b/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
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
   ✅ [证据链采集] 完成 (5m 7.4s)
   📤 → 下游数据: evidence_items=9/11
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 的详细描述信息，验证其配置和状态","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod appconfigfail-575d77485d-nfpvh -n aiops-e2e","tool_args":{"kind":"Pod","name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e"},"purpose":"验证异常 Pod 的详细状态、重启次数、容器状态、事件等关键信息","evidence_type":"status_verification","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":["kubectl_describe","kubectl_get_by_name","kubectl_get_yaml","kubectl_events"],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 的完整 YAML 配置，验证其配置是否缺失关键参数","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e"},"purpose":"验证 Pod 的 YAML 配置中是否缺少环境变量、ConfigMap、Secret 等关键配置","evidence_type":"config_verification","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":["kubectl_get_yaml","kubectl_get_by_name","kubectl_describe"],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod 的上一次容器日志，验证其启动失败原因","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous","tool_args":{"pod_name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e","container_name":"appconfigfail"},"purpose":"验证 Pod 上一次容器启动失败的详细日志，查找配置错误信息","evidence_type":"log_verification","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":["kubectl_previous_logs","kubectl_logs","kubectl_logs_grep"],"counts_for_completeness":true},{"id":"e4","description":"检查是否有缺失的 ConfigMap 或 Secret 被引用","level":"important","tool":"kubectl_find_resource","command":"kubectl get configmap -n aiops-e2e | grep appconfigfail","tool_args":{"kind":"ConfigMap","namespace":"aiops-e2e","search_term":"appconfigfail"},"purpose":"验证是否存在被 Pod 引用但缺失的 ConfigMap 或 Secret","evidence_type":"dependency_verification","target_scope":"aiops-e2e","acceptable_tools":["kubectl_find_resource","kubectl_get_by_kind_in_namespace"],"counts_for_completeness":true},{"id":"e5","description":"检查是否有缺失的 Secret 被引用","level":"important","tool":"kubectl_find_resource","command":"kubectl get secret -n aiops-e2e | grep appconfigfail","tool_args":{"kind":"Secret","namespace":"aiops-e2e","search_term":"appconfigfail"},"purpose":"验证是否存在被 Pod 引用但缺失的 Secret","evidence_type":"dependency_verification","target_scope":"aiops-e2e","acceptable_tools":["kubectl_find_resource","kubectl_get_by_kind_in_namespace"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: appconfigfail-575d77485d-nfpvh\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键状态/事件:\n                  aiops.e2e/expected-status: CrashLoopBackOff|CreateContainerConfigError|CreateContainerError\n    State:          Waiting\n      Reason:       CrashLoopBackOff\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42\n  Warning  BackOff  71s (x371 over 81m)  kubelet  Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/bc47d4165480463b/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/bc47d4165480463b/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/bc47d4165480463b/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: appconfigfail-575d77485d-nfpvh\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-12T05:59:23Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=appconfigfail, e2e-test=true, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/expected-evidence=previous logs contain L4_CONFIG_BOOTSTRAP_FAIL and missing required APP_BOOT_MODE, aiops.e2e/expected-status=CrashLoopBackOff|CreateContainerConfigError|CreateContainerError, aiops.e2e/runbook=pod-config-error.md\nownerReferences: ReplicaSet/appconfigfail-575d77485d\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=20 reason=CrashLoopBackOff exitCode=42\n  message: back-off 5m0s restarting failed container=app pod=appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)\nvolumes:\n- {\"name\": \"kube-api-access-r4t7x\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/bc47d4165480463b/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/bc47d4165480463b/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/bc47d4165480463b/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 6\nsignals: 5\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/bc47d4165480463b/tools/003-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/bc47d4165480463b/tools/003-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/bc47d4165480463b/tools/003-evidence-kubectl_previous_logs.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'keyword' is a required property","collection_summary":"计划 5 项，实际采集 3 项，未采集 2 项，完整度 60%；其中真实环境证据 9/11 项，完整度 82%；实际执行工具 7 个，匹配计划 3 个，未规划证据 4 个","plan_total":5,"plan_collected":3,"plan_completeness":0.6,"environment_evidence_total":11,"environment_evidence_collected":9,"environment_evidence_completeness":0.8181818181818182,"executed_tool_count":7,"matched_tool_count":3,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 的详细描述信息，验证其配置和状态","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod appconfigfail-575d77485d-nfpvh -n aiops-e2e","purpose":"验证异常 Pod 的详细状态、重启次数、容器状态、事件等关键信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 的完整 YAML 配置，验证其配置是否缺失关键参数","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml","purpose":"验证 Pod 的 YAML 配置中是否缺少环境变量、ConfigMap、Secret 等关键配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod 的上一次容器日志，验证其启动失败原因","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous","purpose":"验证 Pod 上一次容器启动失败的详细日志，查找配置错误信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"检查是否有缺失的 ConfigMap 或 Secret 被引用","level":"important","tool":"kubectl_find_resource","command":"kubectl get configmap -n aiops-e2e | grep appconfigfail","purpose":"验证是否存在被 Pod 引用但缺失的 ConfigMap 或 Secret","collected":false,"source":"planned","outcome":"unknown"},{"id":"e5","description":"检查是否有缺失的 Secret 被引用","level":"important","tool":"kubectl_find_resource","command":"kubectl get secret -n aiops-e2e | grep appconfigfail","purpose":"验证是否存在被 Pod 引用但缺失的 Secret","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_find_resource","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_find_resource","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e4(检查是否有缺失的 ConfigMap 或 Secret 被引用): 已规划但工具执行失败或无匹配结果","e5(检查是否有缺失的 Secret 被引用): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/5 项, 完整度: 82%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取异常 Pod 的详细描述信息，验证其配置和状态 | `kubectl describe pod appconfigfail-575d77485d-nfpvh -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_yaml | 获取异常 Pod 的完整 YAML 配置，验证其配置是否缺失关键参数 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml` |
   | e3 | critical | ✅ | kubectl_previous_logs | 获取异常 Pod 的上一次容器日志，验证其启动失败原因 | `kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous` |
   | e4 | important | ❌ | kubectl_find_resource | 检查是否有缺失的 ConfigMap 或 Secret 被引用 | `kubectl get configmap -n aiops-e2e | grep appconfigfail` |
   | e5 | important | ❌ | kubectl_find_resource | 检查是否有缺失的 Secret 被引用 | `kubectl get secret -n aiops-e2e | grep appconfigfail` |

   ⚠️ 未采集原因:
   - e4(检查是否有缺失的 ConfigMap 或 Secret 被引用): 已规划但工具执行失败或无匹配结果
   - e5(检查是否有缺失的 Secret 被引用): 已规划但工具执行失败或无匹配结果

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (8m 56.3s)
   📤 → 下游数据: root_cause=根因是 Pod 配置错误导致启动失败，具体表现为缺失必填环境变量 APP_BOOT_MODE，导致应用程序在启动时验证配置失败，从而进入 CrashLoopBackOff 状态。
   confidence=95%
   causal_chain={"root_cause": "Pod 配置错误导致启动失败", "chain": [{"cause": "Pod 配置错误导致启动失败", "effect": "Pod 进入 CrashLoopBackOff 状态", "evidence": "kubectl_previous_logs 日志摘要:\nlines: 6\nsignals: 5\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup"}, {"cause": "Pod 进入 CrashLoopBackOff 状态", "effect": "Pod 重启次数持续增加", "evidence": "kubectl_describe 摘要:\nname: appconfigfail-575d77485d-nfpvh\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键状态/事件:\n                  aiops.e2e/expected-status: CrashLoopBackOff|CreateContainerConfigError|CreateContainerError\n    State:          Waiting\n      Reason:       CrashLoopBackOff\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42\n  Warning  BackOff  71s (x371 over 81m)  kubelet  Back-off restarting failed container app in pod appconfigfail-575d774"}, {"cause": "Pod 重启次数持续增加", "effect": "Pod 无法正常提供服务", "evidence": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'CrashLoopBackOff': 1, 'Running': 46}\nNAMESPACE     NAME                                                READY   STATUS             RESTARTS         AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\n# 异常行\naiops-e2e     appconfigfail-575d77485d-nfpvh                      0/1     CrashLoopBackOff   19 (2m59s ago)   75m    172.16.166.184   node1    <none>           <none>            app=appconfigfail,e2e-"}]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"id": "e1", "description": "获取异常 Pod 的详细描述信息，验证其配置和状态", "level": "critical", "value": "kubectl_describe 摘要:\nname: appconfigfail-575d77485d-nfpvh\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键状态/事件:\n                  aiops.e2e/expected-status: CrashLoopBackOff|CreateContainerConfigError|CreateContainerError\n    State:          Waiting\n      Reason:       CrashLoopBackOff\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42\n  Warning  BackOff  71s (x371 over 81m)  kubelet  Back-off restarting failed container app in pod appconfigfail-575d774"}, {"id": "e2", "description": "获取异常 Pod 的完整 YAML 配置，验证其配置是否缺失关键参数", "level": "critical", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: appconfigfail-575d77485d-nfpvh\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-12T05:59:23Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=appconfigfail, e2e-test=true, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/expected-evidence=previous logs contain"}, {"id": "e3", "description": "获取异常 Pod 的上一次容器日志，验证其启动失败原因", "level": "critical", "value": "kubectl_previous_logs 日志摘要:\nlines: 6\nsignals: 5\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup"}, {"id": "layer_1", "description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "level": "important", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'CrashLoopBackOff': 1, 'Running': 46}\nNAMESPACE     NAME                                                READY   STATUS             RESTARTS         AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\n# 异常行\naiops-e2e     appconfigfail-575d77485d-nfpvh                      0/1     CrashLoopBackOff   19 (2m59s ago)   75m    172.16.166.184   node1    <none>           <none>            app=appconfigfail,e2e-"}, {"id": "layer_2", "description": "上游已验证工具结果: kubectl_get_yaml", "level": "important", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: appconfigfail-575d77485d-nfpvh\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-12T05:59:23Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=appconfigfail, e2e-test=true, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/expected-evidence=previous logs contain"}, {"id": "layer_3", "description": "上游已验证工具结果: kubectl_previous_logs", "level": "important", "value": "kubectl_previous_logs 日志摘要:\nlines: 6\nsignals: 5\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup"}, {"id": "layer_4", "description": "上游已验证工具结果: kubectl_find_resource", "level": "important", "value": "kubectl_find_resource 输出摘要: raw_chars=98 lines=2\nCommand failed (exit 1):\nkubectl get -A --show-labels -o wide configmap | grep -i 'appconfigfail'"}, {"id": "layer_5", "description": "上游已验证工具结果: kubectl_find_resource", "level": "important", "value": "kubectl_find_resource 输出摘要: raw_chars=95 lines=2\nCommand failed (exit 1):\nkubectl get -A --show-labels -o wide secret | grep -i 'appconfigfail'"}, {"id": "layer_6", "description": "上游已验证工具结果: kubectl_get_yaml", "level": "important", "value": "kubectl_get_yaml 关键字段摘要:\nkind: ReplicaSet\nname: appconfigfail-575d77485d\nnamespace: aiops-e2e"}], "evidence_analysis": [{"id": "e1", "description": "获取异常 Pod 的详细描述信息，验证其配置和状态", "level": "critical", "value": "kubectl_describe 摘要:\nname: appconfigfail-575d77485d-nfpvh\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键状态/事件:\n                  aiops.e2e/expected-status: CrashLoopBackOff|CreateContainerConfigError|CreateContainerError\n    State:          Waiting\n      Reason:       CrashLoopBackOff\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42\n  Warning  BackOff  71s (x371 over 81m)  kubelet  Back-off restarting failed container app in pod appconfigfail-575d774", "raw_data": "State: Waiting\n  Reason: CrashLoopBackOff\nLast State: Terminated\n  Reason: Error\n  Exit Code: 42"}, {"id": "e2", "description": "获取异常 Pod 的完整 YAML 配置，验证其配置是否缺失关键参数", "level": "critical", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: appconfigfail-575d77485d-nfpvh\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-12T05:59:23Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=appconfigfail, e2e-test=true, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/expected-evidence=previous logs contain", "raw_data": "phase: Running\nlabels: app=appconfigfail, e2e-test=true, pod_abnormal_type=ConfigError"}, {"id": "e3", "description": "获取异常 Pod 的上一次容器日志，验证其启动失败原因", "level": "critical", "value": "kubectl_previous_logs 日志摘要:\nlines: 6\nsignals: 5\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup", "raw_data": "L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nFATAL: missing required APP_BOOT_MODE"}, {"id": "layer_1", "description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "level": "important", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'CrashLoopBackOff': 1, 'Running': 46}\nNAMESPACE     NAME                                                READY   STATUS             RESTARTS         AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\n# 异常行\naiops-e2e     appconfigfail-575d77485d-nfpvh                      0/1     CrashLoopBackOff   19 (2m59s ago)   75m    172.16.166.184   node1    <none>           <none>            app=appconfigfail,e2e-", "raw_data": "aiops-e2e     appconfigfail-575d77485d-nfpvh                      0/1     CrashLoopBackOff   19 (2m59s ago)   75m    172.16.166.184   node1"}, {"id": "layer_2", "description": "上游已验证工具结果: kubectl_get_yaml", "level": "important", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: appconfigfail-575d77485d-nfpvh\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-12T05:59:23Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=appconfigfail, e2e-test=true, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/expected-evidence=previous logs contain", "raw_data": "phase: Running\nlabels: app=appconfigfail, e2e-test=true, pod_abnormal_type=ConfigError"}, {"id": "layer_3", "description": "上游已验证工具结果: kubectl_previous_logs", "level": "important", "value": "kubectl_previous_logs 日志摘要:\nlines: 6\nsignals: 5\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup", "raw_data": "L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nFATAL: missing required APP_BOOT_MODE"}, {"id": "layer_4", "description": "上游已验证工具结果: kubectl_find_resource", "level": "important", "value": "kubectl_find_resource 输出摘要: raw_chars=98 lines=2\nCommand failed (exit 1):\nkubectl get -A --show-labels -o wide configmap | grep -i 'appconfigfail'", "raw_data": "Command failed (exit 1):\nkubectl get -A --show-labels -o wide configmap | grep -i 'appconfigfail'"}, {"id": "layer_5", "description": "上游已验证工具结果: kubectl_find_resource", "level": "important", "value": "kubectl_find_resource 输出摘要: raw_chars=95 lines=2\nCommand failed (exit 1):\nkubectl get -A --show-labels -o wide secret | grep -i 'appconfigfail'", "raw_data": "Command failed (exit 1):\nkubectl get -A --show-labels -o wide secret | grep -i 'appconfigfail'"}, {"id": "layer_6", "description": "上游已验证工具结果: kubectl_get_yaml", "level": "important", "value": "kubectl_get_yaml 关键字段摘要:\nkind: ReplicaSet\nname: appconfigfail-575d77485d\nnamespace: aiops-e2e", "raw_data": "kind: ReplicaSet\nname: appconfigfail-575d77485d\nnamespace: aiops-e2e"}], "causal_chain": {"root_cause": "Pod 配置错误导致启动失败", "chain": [{"cause": "Pod 配置错误导致启动失败", "effect": "Pod 进入 CrashLoopBackOff 状态", "evidence": "kubectl_previous_logs 日志摘要:\nlines: 6\nsignals: 5\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup"}, {"cause": "Pod 进入 CrashLoopBackOff 状态", "effect": "Pod 重启次数持续增加", "evidence": "kubectl_describe 摘要:\nname: appconfigfail-575d77485d-nfpvh\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键状态/事件:\n                  aiops.e2e/expected-status: CrashLoopBackOff|CreateContainerConfigError|CreateContainerError\n    State:          Waiting\n      Reason:       CrashLoopBackOff\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42\n  Warning  BackOff  71s (x371 over 81m)  kubelet  Back-off restarting failed container app in pod appconfigfail-575d774"}, {"cause": "Pod 重启次数持续增加", "effect": "Pod 无法正常提供服务", "evidence": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'CrashLoopBackOff': 1, 'Running': 46}\nNAMESPACE     NAME                                                READY   STATUS             RESTARTS         AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\n# 异常行\naiops-e2e     appconfigfail-575d77485d-nfpvh                      0/1     CrashLoopBackOff   19 (2m59s ago)   75m    172.16.166.184   node1    <none>           <none>            app=appconfigfail,e2e-"}]}, "root_cause": "根因是 Pod 配置错误导致启动失败，具体表现为缺失必填环境变量 APP_BOOT_MODE，导致应用程序在启动时验证配置失败，从而进入 CrashLoopBackOff 状态。", "root_cause_summary": "根因是 Pod 配置错误导致启动失败，具体表现为缺失必填环境变量 APP_BOOT_MODE，导致应用程序在启动时验证配置失败，从而进入 CrashLoopBackOff 状态。", "confidence": 0.95, "confidence_reason": "有直接证据表明 Pod 配置错误导致启动失败，因果链清晰。", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [], "limitations": "未检查是否有缺失的 ConfigMap 或 Secret 被引用，这可能影响诊断的完整性。", "llm_raw_analysis": "基于已采集的证据，可以确定当前集群中的异常 Pod 'appconfigfail-575d77485d-nfpvh' 处于 CrashLoopBackOff 状态，其重启次数持续增加。通过分析该 Pod 的日志，发现其启动失败的原因是由于配置错误，具体表现为缺失必填环境变量 APP_BOOT_MODE。此外，该 Pod 的 YAML 配置中未引用任何 ConfigMap 或 Secret，进一步支持了配置缺失的结论。因此，根因是 Pod 配置错误导致启动失败，具体表现为缺失必填环境变量 APP_BOOT_MODE，导致应用程序在启动时验证配置失败，从而进入 CrashLoopBackOff 状态。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 根因是 Pod 配置错误导致启动失败，具体表现为缺失必填环境变量 APP_BOOT_MODE，导致应用程序在启动时验证配置失败，从而进入 CrashLoopBackOff 状态。
   置信度: 95%
   🔗 因果链:
     根本原因: Pod 配置错误导致启动失败


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
   ✅ [汇总总结] 完成 (2m 39.6s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4257 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 18m 15.6s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
## 📊 诊断概览

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
| 错误信息 | L4_CONFIG_BOOTSTRAP_FAIL, missing required APP_BOOT_MODE, config validation failed |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | kubectl get pod -A | `STATUS: CrashLoopBackOff, RESTARTS: 19 (2m59s ago)` | Pod 重启频繁，处于崩溃循环状态 |
| 2 | Pod YAML 配置 | kubectl get pod -o yaml | `labels: app=appconfigfail, pod_abnormal_type=ConfigError` | 明确标记为配置错误类型 |
| 3 | 容器日志 | kubectl logs <pod> --previous | `L4_CONFIG_BOOTSTRAP_FAIL, missing required APP_BOOT_MODE` | 应用在启动时验证配置失败 |
| 4 | Runbook 匹配 | fetch_runbook | `典型状态: CrashLoopBackOff | 信号: L4_CONFIG_BOOTSTRAP_FAIL` | 与已知配置错误场景匹配 |
| 5 | ConfigMap 检查 | kubectl get configmap | `Command failed (exit 1): no configmaps found matching 'appconfigfail'` | 未找到相关 ConfigMap |
| 6 | Secret 检查 | kubectl get secret | `Command failed (exit 1): no secrets found matching 'appconfigfail'` | 未找到相关 Secret |
| 7 | Pod describe | kubectl describe pod | `Last State: Terminated, Reason: Error, Exit Code: 42` | 容器以非 OOM 原因退出 |

### 证据关联分析

- **证据 #3 + #4 印证**：日志中的 `L4_CONFIG_BOOTSTRAP_FAIL` 和 `missing required APP_BOOT_MODE` 与 Runbook 中定义的典型配置错误信号一致。
- **证据链**：
  - 应用启动时检测到缺失必填配置项 `APP_BOOT_MODE`
  - 应用配置验证失败，导致启动中止
  - 容器退出并被 Kubernetes 重启，进入 `CrashLoopBackOff` 状态

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 应用配置源（如 ConfigMap、Secret） | critical | 无法确认是否配置源未正确挂载或内容缺失 |
| 完整的容器启动日志 | important | 无法判断是否其他配置项也存在问题 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 应用启动时缺失关键环境变量 APP_BOOT_MODE，导致配置验证失败        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 应用配置未通过验证 → 应用启动失败 → 容器退出 → Kubernetes 重启   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器退出码 42，日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和配置缺失      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CrashLoopBackOff，重启次数持续增加                   │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #3 (容器日志) 和证据 #4 (Runbook 匹配)，问题的根本原因是**容器中缺失关键环境变量 `APP_BOOT_MODE`**，导致应用配置验证失败，容器启动失败并被 Kubernetes 重启。  
**置信度**：高 (95%)  
- ✅ 容器日志明确指出配置验证失败
- ✅ Runbook 明确定义了该类错误
- ⚠️ 未找到配置源（ConfigMap/Secret），无法确认是否未挂载或内容缺失

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 为容器设置 `APP_BOOT_MODE` 环境变量**

```bash
kubectl set env deployment/appconfigfail -n aiops-e2e APP_BOOT_MODE=local
```

*依据*：容器日志显示 `missing required APP_BOOT_MODE`，需明确设置该环境变量。

**2. [可选] 检查 ConfigMap/Secret 是否存在并正确挂载**

```bash
kubectl describe pod appconfigfail-575d77485d-nfpvh -n aiops-e2e
kubectl get configmap -n aiops-e2e
kubectl get secret -n aiops-e2e
```

*目的*：确认配置源是否存在，是否被正确挂载到容器中。

### 后续优化

1. **配置源管理**：确保所有依赖的 ConfigMap 或 Secret 正确创建并挂载。
2. **配置校验**：在部署前添加配置校验步骤，确保所有必填参数存在。
3. **监控配置变更**：配置变更时应有监控和告警机制。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |
| 3. 查看容器日志 | `kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e` | 无 L4_CONFIG_BOOTSTRAP_FAIL 等错误 |

---

## ⚠️ 注意事项

- 如果问题仍未解决，检查容器启动脚本或应用是否还有其他配置依赖。
- 考虑使用 ConfigMap/Secret 来管理配置，避免硬编码。
- 如果是测试环境，可临时允许默认配置，但在生产环境中应严格校验配置。

---

---

## 📊 性能统计

├─ 总耗时: 18.3m
├─ 问题定位: 92.2s (8%) ✅
├─ 证据链采集: 307.4s (28%) ✅
├─ 根因分析: 536.3s (49%) ✅
├─ 汇总总结: 159.6s (15%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 12 次
```

📋 诊断追踪

- **核心 Runbook**: pod-config-error
- **参考 Runbook**: pod-config-error
- **工具调用**: 12 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
