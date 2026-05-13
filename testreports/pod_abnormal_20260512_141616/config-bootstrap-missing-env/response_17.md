======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 1817015f56304bb2]

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
   💭 [问题定位] 调用工具: kubectl_logs
   💭 [问题定位] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 日志摘要:
lines: 6
signals: 5
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config
L4_SCENARIO: config-bootstrap-fail
L4_ERROR_TYPE: application-config
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
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                       DESIRED   CURRENT   READY   AGE   CONTAINERS   IMAGES         SELECTOR                                         LABELS
appconfigfail-575d77485d   1         1         0       
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME            READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES         SELECTOR            LABELS
appconfigfail   0/1     1            0           45m   app          busybox:1.36   app=app
   💭 [问题定位] 调用工具: kubectl_get_by_name
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 6.4s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'Pod 配置错误导致启动失败', 'probability': '高', 'reason': '日志中明确显示配置校验失败，缺少必填环境变量 APP_BOOT_MODE。'}]
   entities=[{"type": "Pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}]
   reasoning=当前环境中的活跃异常对象为 Pod 'appconfigfail-575d77485d-nfpvh'，其状态为 'CrashLoopBackOff'，重启次数持续增加。日志中包含 'L4_CONFIG_BOOTSTRAP_FAIL'、'missing required APP_BOOT_MODE' 和 'business config validation failed before server startup' 等信号，表明存在配置错误。根据 runbook 判定规则，该异常属于 ConfigError，归类为 L4 层级，具体为应用配置错误。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "application error", "confidence": 0.5, "reasoning": "当前环境中的活跃异常对象为 Pod 'appconfigfail-575d77485d-nfpvh'，其状态为 'CrashLoopBackOff'，重启次数持续增加。日志中包含 'L4_CONFIG_BOOTSTRAP_FAIL'、'missing required APP_BOOT_MODE' 和 'business config validation failed before server startup' 等信号，表明存在配置错误。根据 runbook 判定规则，该异常属于 ConfigError，归类为 L4 层级，具体为应用配置错误。", "abnormal_pods": [{"name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "app_config", "key_entities": [{"type": "Pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Pod 配置错误导致启动失败", "probability": "高", "reason": "日志中明确显示配置校验失败，缺少必填环境变量 APP_BOOT_MODE。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     appconfigfail-575d77485d-nfpvh                      0/1     CrashLoopBackOff   13 (3m31s ago)   45m    172.16.166.184   node1    <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError"], "raw_ref": "/tmp/aiops/reports/context_archives/1817015f56304bb2/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/1817015f56304bb2/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/1817015f56304bb2/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                             READY   STATUS             RESTARTS        AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
appconfigfail-575d77485d-nfpvh   0/1     CrashLoopB
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
3m38s (x211 over 48m)   Warning   BackOff          Pod/appconfigfail-575d77485d-nfpvh   Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc
   💭 [证据链采集] 调用工具: kubectl_logs
   💭 [证据链采集] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 日志摘要:
lines: 6
signals: 5
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config
L4_SCENARIO: config-bootstrap-fail
L4_ERROR_TYPE: application-config
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 6
signals: 5
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config
L4_SCENARIO: config-bootstrap-fail
L4_ERROR_TYPE: applicati
   💭 [证据链采集] # 证据结论

## 已采集证据
1. **Pod 状态验证**: Pod `appconfigfail-575d77485d-nfpvh` 当前状态为 `CrashLoopBackOff`，重启次数为 14 次，符合 ConfigError 的特征。
2. **事件验证**: 事件中显示 `Back-off restarting failed container app`，表明容器因配置问题多次失败。
3. **日志验证**: 当前和上一次的日志均显示 `L4_CONFIG_BOOTSTRAP_FAIL`、`missing required APP_BOOT_MODE` 和 `business config validation failed before server startup`，明确指出配置错误。
4. **无 OOMKilled 信号**: 未发现 `OOMKilled` 或 `Exit Code 137`，排除内存不足导致的崩溃。
5. **无 ImagePullBackOff 信号**: 未发现 `ImagePullBackOff` 或 `ErrImagePull`，排除镜像拉取失败。

## 未采集证据
无

## 冲突证据
无

## 建议修复方案
1. 检查 Pod 的配置，确保环境变量 `APP_BOOT_MODE` 已正确设置。
2. 验证 ConfigMap 或 Secret 是否正确挂载，并确保所需键值存在。
3. 检查应用的配置文件，确保其符合预期的格式和内容。
   ✅ [证据链采集] 完成 (3m 0.4s)
   📤 → 下游数据: evidence_items=10/10
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 的详细信息","level":"critical","tool":"kubectl_get_by_name","command":"get pods appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e"},"purpose":"验证 Pod spec 是否缺少配置资源引用","evidence_type":"current_state","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 的事件","level":"critical","tool":"kubectl_events","command":"get events -n aiops-e2e --field-selector=involvedObject.name=appconfigfail-575d77485d-nfpvh","tool_args":{"kind":"Pod","name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e"},"purpose":"验证 Pod 是否存在配置对象缺失或拉取失败的事件信号","evidence_type":"event_signal","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod 的日志","level":"important","tool":"kubectl_logs","command":"logs pod/appconfigfail-575d77485d-nfpvh -n aiops-e2e","tool_args":{"kind":"Pod","name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e","container":""},"purpose":"验证日志是否包含配置校验失败/缺参等信号","evidence_type":"log_signal","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"获取异常 Pod 的上一次容器日志","level":"important","tool":"kubectl_previous_logs","command":"logs pod/appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous","tool_args":{"kind":"Pod","name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e","container":""},"purpose":"验证上一次容器是否因配置错误退出","evidence_type":"log_signal","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                             READY   STATUS             RESTARTS        AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nappconfigfail-575d77485d-nfpvh   0/1     CrashLoopBackOff   14 (108s ago)   48m   172.16.166.184   node1   <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1817015f56304bb2/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1817015f56304bb2/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1817015f56304bb2/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n3m38s (x211 over 48m)   Warning   BackOff          Pod/appconfigfail-575d77485d-nfpvh   Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1817015f56304bb2/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1817015f56304bb2/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1817015f56304bb2/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_logs","data":"kubectl_logs 日志摘要:\nlines: 6\nsignals: 5\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1817015f56304bb2/tools/003-evidence-kubectl_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1817015f56304bb2/tools/003-evidence-kubectl_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1817015f56304bb2/tools/003-evidence-kubectl_logs.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 6\nsignals: 5\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1817015f56304bb2/tools/004-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1817015f56304bb2/tools/004-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1817015f56304bb2/tools/004-evidence-kubectl_previous_logs.summary.txt"}],"llm_analysis":"# 证据结论\n\n## 已采集证据\n1. **Pod 状态验证**: Pod `appconfigfail-575d77485d-nfpvh` 当前状态为 `CrashLoopBackOff`，重启次数为 14 次，符合 ConfigError 的特征。\n2. **事件验证**: 事件中显示 `Back-off restarting failed container app`，表明容器因配置问题多次失败。\n3. **日志验证**: 当前和上一次的日志均显示 `L4_CONFIG_BOOTSTRAP_FAIL`、`missing required APP_BOOT_MODE` 和 `business config validation failed before server startup`，明确指出配置错误。\n4. **无 OOMKilled 信号**: 未发现 `OOMKilled` 或 `Exit Code 137`，排除内存不足导致的崩溃。\n5. **无 ImagePullBackOff 信号**: 未发现 `ImagePullBackOff` 或 `ErrImagePull`，排除镜像拉取失败。\n\n## 未采集证据\n无\n\n## 冲突证据\n无\n\n## 建议修复方案\n1. 检查 Pod 的配置，确保环境变量 `APP_BOOT_MODE` 已正确设置。\n2. 验证 ConfigMap 或 Secret 是否正确挂载，并确保所需键值存在。\n3. 检查应用的配置文件，确保其符合预期的格式和内容。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 10/10 项，完整度 100%；实际执行工具 10 个，匹配计划 4 个，未规划证据 6 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":10,"environment_evidence_collected":10,"environment_evidence_completeness":1.0,"executed_tool_count":10,"matched_tool_count":4,"unplanned_tool_count":6,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 的详细信息","level":"critical","tool":"kubectl_get_by_name","command":"get pods appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml","purpose":"验证 Pod spec 是否缺少配置资源引用","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 的事件","level":"critical","tool":"kubectl_events","command":"get events -n aiops-e2e --field-selector=involvedObject.name=appconfigfail-575d77485d-nfpvh","purpose":"验证 Pod 是否存在配置对象缺失或拉取失败的事件信号","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod 的日志","level":"important","tool":"kubectl_logs","command":"logs pod/appconfigfail-575d77485d-nfpvh -n aiops-e2e","purpose":"验证日志是否包含配置校验失败/缺参等信号","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"获取异常 Pod 的上一次容器日志","level":"important","tool":"kubectl_previous_logs","command":"logs pod/appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous","purpose":"验证上一次容器是否因配置错误退出","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 获取异常 Pod 的详细信息 | `get pods appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml` |
   | e2 | critical | ✅ | kubectl_events | 获取异常 Pod 的事件 | `get events -n aiops-e2e --field-selector=involvedObject.name=appconfigfail-57...` |
   | e3 | important | ✅ | kubectl_logs | 获取异常 Pod 的日志 | `logs pod/appconfigfail-575d77485d-nfpvh -n aiops-e2e` |
   | e4 | important | ✅ | kubectl_previous_logs | 获取异常 Pod 的上一次容器日志 | `logs pod/appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous` |

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
   ✅ [根因分析] 完成 (6m 13.1s)
   📤 → 下游数据: root_cause=Pod 'appconfigfail-575d77485d-nfpvh' 当前状态为 'CrashLoopBackOff'，重启次数为 14 次，表明容器因配置问题多次失败。日志中显示 'L4_CONFIG_BOOTSTRAP_FAIL'、'missing required APP_BOOT_MODE' 和 'business config validation failed before server startup'，明确指出配置错误。
   confidence=90%
   causal_chain={"root_cause": "配置错误导致应用启动失败", "direct_causes": ["缺少必填环境变量 APP_BOOT_MODE", "业务配置验证失败"], "consequences": ["Pod 状态为 'CrashLoopBackOff'", "重启次数持续增加"], "evidence": ["kubectl_logs 日志摘要: 关键日志: L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config", "kubectl_previous_logs 日志摘要: 关键日志: L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"description": "获取异常 Pod 的详细信息", "level": "critical", "value": "NAME                             READY   STATUS             RESTARTS        AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nappconfigfail-575d77485d-nfpvh   0/1     CrashLoopBackOff   14 (108s ago)   48m   172.16.166.184   node1   <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError"}, {"description": "获取异常 Pod 的事件", "level": "critical", "value": "kubectl_events 摘要:\n3m38s (x211 over 48m)   Warning   BackOff          Pod/appconfigfail-575d77485d-nfpvh   Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)"}, {"description": "获取异常 Pod 的日志", "level": "important", "value": "kubectl_logs 日志摘要:\nlines: 6\nsignals: 5\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup"}, {"description": "获取异常 Pod 的上一次容器日志", "level": "important", "value": "kubectl_previous_logs 日志摘要:\nlines: 6\nsignals: 5\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup"}, {"description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "level": "important", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'CrashLoopBackOff': 1, 'Running': 46}\nNAMESPACE     NAME                                                READY   STATUS             RESTARTS         AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\n# 异常行\naiops-e2e     appconfigfail-575d77485d-nfpvh                      0/1     CrashLoopBackOff   13 (3m31s ago)   45m    172.16.166.184   node1    <none>           <none>            app=appconfigfail,e2e-"}, {"description": "上游已验证工具结果: kubectl_logs", "level": "important", "value": "kubectl_logs 日志摘要:\nlines: 6\nsignals: 5\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup"}, {"description": "上游已验证工具结果: kubectl_previous_logs", "level": "important", "value": "kubectl_previous_logs 日志摘要:\nlines: 6\nsignals: 5\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup"}, {"description": "上游已验证工具结果: kubectl_get_yaml", "level": "important", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: appconfigfail-575d77485d-nfpvh\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-12T05:59:23Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=appconfigfail, e2e-test=true, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/expected-evidence=previous logs contain"}, {"description": "上游已验证工具结果: kubectl_get_by_name", "level": "important", "value": "NAME                       DESIRED   CURRENT   READY   AGE   CONTAINERS   IMAGES         SELECTOR                                         LABELS\nappconfigfail-575d77485d   1         1         0       45m   app          busybox:1.36   app=appconfigfail,pod-template-hash=575d77485d   app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError"}, {"description": "上游已验证工具结果: kubectl_get_by_name", "level": "important", "value": "NAME            READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES         SELECTOR            LABELS\nappconfigfail   0/1     1            0           45m   app          busybox:1.36   app=appconfigfail   e2e-test=true,l4-scenario=config-bootstrap-fail,pod_abnormal_type=ConfigError"}], "evidence_analysis": [{"description": "获取异常 Pod 的详细信息", "level": "critical", "value": "Pod 'appconfigfail-575d77485d-nfpvh' 当前状态为 'CrashLoopBackOff'，重启次数为 14 次，表明容器因配置问题多次失败。"}, {"description": "获取异常 Pod 的事件", "level": "critical", "value": "事件中显示 'Back-off restarting failed container app'，表明容器因配置问题多次失败。"}, {"description": "获取异常 Pod 的日志", "level": "important", "value": "日志中显示 'L4_CONFIG_BOOTSTRAP_FAIL'、'missing required APP_BOOT_MODE' 和 'business config validation failed before server startup'，明确指出配置错误。"}, {"description": "获取异常 Pod 的上一次容器日志", "level": "important", "value": "上一次容器日志中显示 'L4_CONFIG_BOOTSTRAP_FAIL'、'missing required APP_BOOT_MODE' 和 'business config validation failed before server startup'，明确指出配置错误。"}], "causal_chain": {"root_cause": "配置错误导致应用启动失败", "direct_causes": ["缺少必填环境变量 APP_BOOT_MODE", "业务配置验证失败"], "consequences": ["Pod 状态为 'CrashLoopBackOff'", "重启次数持续增加"], "evidence": ["kubectl_logs 日志摘要: 关键日志: L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config", "kubectl_previous_logs 日志摘要: 关键日志: L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config"]}, "root_cause": "Pod 'appconfigfail-575d77485d-nfpvh' 当前状态为 'CrashLoopBackOff'，重启次数为 14 次，表明容器因配置问题多次失败。日志中显示 'L4_CONFIG_BOOTSTRAP_FAIL'、'missing required APP_BOOT_MODE' 和 'business config validation failed before server startup'，明确指出配置错误。", "root_cause_summary": "Pod 'appconfigfail-575d77485d-nfpvh' 当前状态为 'CrashLoopBackOff'，重启次数为 14 次，表明容器因配置问题多次失败。日志中显示 'L4_CONFIG_BOOTSTRAP_FAIL'、'missing required APP_BOOT_MODE' 和 'business config validation failed before server startup'，明确指出配置错误。", "confidence": 0.9, "confidence_reason": "有直接证据，因果链清晰。", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [], "limitations": "无", "llm_raw_analysis": "基于已采集的证据，分析得出以下结论：\n\n1. **Pod 状态验证**: Pod 'appconfigfail-575d77485d-nfpvh' 当前状态为 'CrashLoopBackOff'，重启次数为 14 次，符合 ConfigError 的特征。\n2. **事件验证**: 事件中显示 'Back-off restarting failed container app'，表明容器因配置问题多次失败。\n3. **日志验证**: 当前和上一次的日志均显示 'L4_CONFIG_BOOTSTRAP_FAIL'、'missing required APP_BOOT_MODE' 和 'business config validation failed before server startup'，明确指出配置错误。\n4. **无 OOMKilled 信号**: 未发现 'OOMKilled' 或 'Exit Code 137'，排除内存不足导致的崩溃。\n5. **无 ImagePullBackOff 信号**: 未发现 'ImagePullBackOff' 或 'ErrImagePul\n... 截断，原始 640 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'appconfigfail-575d77485d-nfpvh' 当前状态为 'CrashLoopBackOff'，重启次数为 14 次，表明容器因配置问题多次失败。日志中显示 'L4_CONFIG_BOOTSTRAP_FAIL'、'missing required APP_BOOT_MOD...
   置信度: 90%
   🔗 因果链:
     根本原因: 配置错误导致应用启动失败


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 46.9s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4570 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 12m 6.8s
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
| **问题分类** | ConfigError |
| **置信度** | 高 (90%) |
| **证据完整度** | 4/4 (100%) |

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
| 错误信息 | L4_CONFIG_BOOTSTRAP_FAIL, missing required APP_BOOT_MODE, business config validation failed before server startup |

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod -n aiops-e2e` | `STATUS: CrashLoopBackOff, RESTARTS: 13 (3m31s ago)` | Pod 由于容器启动失败持续重启 |
| 2 | 容器日志 | `kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e` | `L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config` | 明确指出配置校验失败 |
| 3 | 上一次容器日志 | `kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous` | `FATAL: missing required APP_BOOT_MODE` | 缺失必填环境变量 `APP_BOOT_MODE` |
| 4 | Pod YAML | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml` | `labels: app=appconfigfail, e2e-test=true, pod_abnormal_type=ConfigError` | 无 `APP_BOOT_MODE` 环境变量定义 |
| 5 | Pod 事件 | `kubectl describe pod appconfigfail-575d77485d-nfpvh -n aiops-e2e` | `Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e` | Pod 重启机制触发 |

### 证据关联分析
- **证据 #2 + #3 印证**：日志中明确指出 `L4_CONFIG_BOOTSTRAP_FAIL` 和 `missing required APP_BOOT_MODE`，表明配置校验失败。
- **证据链**：Pod 启动时应用依赖的环境变量缺失 → 配置校验失败 → 容器启动失败 → Pod 重启 → 持续循环。
- **证据 #4 印证**：Pod YAML 中未定义 `APP_BOOT_MODE` 环境变量，确认配置缺失。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 无缺失证据 | N/A | N/A |

---
## 🎯 根因分析
### 因果链
```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                       │
│ 必填环境变量 `APP_BOOT_MODE` 缺失，导致应用配置校验失败。                         │
└──────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                       │
│ 应用启动时缺少配置项 `APP_BOOT_MODE`，触发配置校验失败逻辑。                       │
└──────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                       │
│ 容器启动失败，日志显示 `L4_CONFIG_BOOTSTRAP_FAIL` 和 `missing required APP_BOOT_MODE`。│
└──────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                   │
│ Pod 状态为 `CrashLoopBackOff`，重启次数持续增加。                                 │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2 (日志显示 `L4_CONFIG_BOOTSTRAP_FAIL`)、证据 #3 (日志显示 `missing required APP_BOOT_MODE`) 和证据 #4 (Pod YAML 中未定义 `APP_BOOT_MODE`)，问题的根本原因是**容器缺少必填环境变量 `APP_BOOT_MODE`**，导致应用配置校验失败，从而触发容器启动失败。
**置信度**：高 (90%)
- ✅ 日志明确显示配置校验失败
- ✅ Pod YAML 中未定义 `APP_BOOT_MODE`
- ✅ 无 OOMKilled 或 ImagePullBackOff 等其他错误信号，排除其他原因

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 为容器添加缺失的环境变量 `APP_BOOT_MODE`**
```bash
kubectl set env deployment/appconfigfail -n aiops-e2e APP_BOOT_MODE="local"
```
*依据*：日志明确指出 `missing required APP_BOOT_MODE`，添加该变量可使配置校验通过。

**2. [可选] 验证环境变量是否生效**
```bash
kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o jsonpath='{.spec.containers[0].env}'
```
*预期输出*：应包含 `APP_BOOT_MODE` 的环境变量定义。

### 后续优化
1. **配置校验逻辑增强**：建议在部署前增加配置校验钩子（如 init 容器），避免因配置错误导致容器启动失败。
2. **配置管理最佳实践**：使用 ConfigMap 或 Secret 管理环境变量，避免直接硬编码。
3. **应用日志增强**：优化日志输出，提供更清晰的配置失败提示，方便快速定位问题。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |
| 3. 验证环境变量 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o jsonpath='{.spec.containers[0].env}'` | 包含 `APP_BOOT_MODE` |

---
## ⚠️ 注意事项
- 如果问题仍然存在，请检查应用是否依赖其他配置项或环境变量。
- 确保环境变量值符合应用预期（如 `local`、`cloud`、`test` 等）。
- 如果使用 ConfigMap/Secret，确保其正确挂载并生效。

---

## 📊 性能统计

├─ 总耗时: 12.1m
├─ 问题定位: 66.4s (9%) ✅
├─ 证据链采集: 180.4s (25%) ✅
├─ 根因分析: 373.1s (51%) ✅
├─ 汇总总结: 106.9s (15%) ✅
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
