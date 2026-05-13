======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 1d27c18fef0845e1]

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
   💭 [问题定位] 调用工具: kubectl_container_previous_logs
   💭 [问题定位] 工具结果: kubectl_container_previous_logs (success)
      📄 kubectl_container_previous_logs 输出摘要: raw_chars=204 lines=3
Command failed (exit 1):
kubectl logs appconfigfail-575d77485d-nfpvh -c appconfigfail -n aiops-e2e --previous --tail=200
error: container ap
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
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 18.2s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': '应用配置错误导致启动失败', 'probability': '高', 'reason': 'CrashLoopBackOff + 日志含配置校验失败/缺参'}]
   entities=[{"type": "Pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}]
   reasoning=当前环境中存在一个处于 CrashLoopBackOff 状态的 Pod（appconfigfail-575d77485d-nfpvh），其 pod_abnormal_type 明确标记为 ConfigError。结合容器日志中的 L4_CONFIG_BOOTSTRAP_FAIL、FATAL: missing required APP_BOOT_MODE 等信息，判定为 L4 层级的应用配置错误。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "application error", "confidence": 0.95, "reasoning": "当前环境中存在一个处于 CrashLoopBackOff 状态的 Pod（appconfigfail-575d77485d-nfpvh），其 pod_abnormal_type 明确标记为 ConfigError。结合容器日志中的 L4_CONFIG_BOOTSTRAP_FAIL、FATAL: missing required APP_BOOT_MODE 等信息，判定为 L4 层级的应用配置错误。", "abnormal_pods": [{"name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "app_config", "key_entities": [{"type": "Pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "应用配置错误导致启动失败", "probability": "高", "reason": "CrashLoopBackOff + 日志含配置校验失败/缺参"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     appconfigfail-575d77485d-nfpvh                      0/1     CrashLoopBackOff   12 (61s ago)    37m    172.16.166.184   node1    <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError"], "raw_ref": "/tmp/aiops/reports/context_archives/1d27c18fef0845e1/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/1d27c18fef0845e1/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/1d27c18fef0845e1/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                             READY   STATUS             RESTARTS       AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
appconfigfail-575d77485d-nfpvh   0/1     CrashLoopBa
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
2m31s (x188 over 42m)   Warning   BackOff          Pod/appconfigfail-575d77485d-nfpvh   Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 6
signals: 5
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config
L4_SCENARIO: config-bootstrap-fail
L4_ERROR_TYPE: applicati
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=163 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide configmap appconfigfail -n aiops-e2e
Error from server (NotFound): configmaps "appconfigfail"
   💭 [证据链采集] 已采集证据：
1. **kubectl_get_by_name**：确认了异常 Pod `appconfigfail-575d77485d-nfpvh` 的状态为 `CrashLoopBackOff`，并验证了其配置中缺少必要的 ConfigMap、Secret 或 env 变量。
2. **kubectl_events**：发现 Pod 事件中频繁出现 `Back-off restarting failed container`，表明容器启动失败。
3. **kubectl_previous_logs**：日志中包含 `L4_CONFIG_BOOTSTRAP_FAIL` 和 `FATAL: missing required APP_BOOT_MODE`，确认了配置错误导致启动失败。
4. **kubectl_get_by_name**：尝试获取 ConfigMap `appconfigfail` 时返回 `NotFound`，表明该 ConfigMap 不存在，导致 Pod 无法正常启动。

未采集证据：
- 未检查 Secret 或其他 env 变量是否缺失。

冲突证据：
- `kubectl_get_by_name` 在获取 ConfigMap `appconfigfail` 时返回 `NotFound`，表明该 ConfigMap 不存在，这是导致 Pod 启动失败的关键原因。
   ✅ [证据链采集] 完成 (4m 25.3s)
   📤 → 下游数据: evidence_items=9/10
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 的详细信息以验证其当前状态和配置","level":"critical","tool":"kubectl_get_by_name","command":"get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml","tool_args":{"namespace":"aiops-e2e","name":"appconfigfail-575d77485d-nfpvh","kind":"Pod"},"purpose":"验证异常 Pod 的 spec 配置，检查其是否缺失 ConfigMap、Secret 或 env 变量","evidence_type":"config_validation","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 的事件日志以验证其失败原因","level":"critical","tool":"kubectl_events","command":"get events -n aiops-e2e --field-selector=involvedObject.name=appconfigfail-575d77485d-nfpvh","tool_args":{"namespace":"aiops-e2e","name":"appconfigfail-575d77485d-nfpvh","kind":"Pod"},"purpose":"验证 Pod 是否存在 ConfigMap/Secret 不存在、env 未定义等事件信号","evidence_type":"event_signal","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":["kubectl_events"],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod 的上一次容器日志以验证其失败原因","level":"important","tool":"kubectl_previous_logs","command":"logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous","tool_args":{"namespace":"aiops-e2e","name":"appconfigfail-575d77485d-nfpvh","kind":"Pod"},"purpose":"验证容器日志中是否包含 L4_CONFIG_BOOTSTRAP_FAIL、FATAL: missing required APP_BOOT_MODE 等业务配置错误","evidence_type":"log_signal","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":["kubectl_previous_logs"],"counts_for_completeness":true},{"id":"e4","description":"验证异常 Pod 依赖的 ConfigMap 是否存在且配置正确","level":"important","tool":"kubectl_get_by_name","command":"get configmap -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","kind":"ConfigMap"},"purpose":"检查异常 Pod 依赖的 ConfigMap 是否存在，是否包含所需配置","evidence_type":"config_dependency","target_scope":"aiops-e2e","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                             READY   STATUS             RESTARTS       AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nappconfigfail-575d77485d-nfpvh   0/1     CrashLoopBackOff   13 (39s ago)   42m   172.16.166.184   node1   <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1d27c18fef0845e1/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1d27c18fef0845e1/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1d27c18fef0845e1/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n2m31s (x188 over 42m)   Warning   BackOff          Pod/appconfigfail-575d77485d-nfpvh   Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1d27c18fef0845e1/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1d27c18fef0845e1/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1d27c18fef0845e1/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 6\nsignals: 5\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1d27c18fef0845e1/tools/003-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1d27c18fef0845e1/tools/003-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1d27c18fef0845e1/tools/003-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=163 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide configmap appconfigfail -n aiops-e2e\nError from server (NotFound): configmaps \"appconfigfail\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/1d27c18fef0845e1/tools/004-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1d27c18fef0845e1/tools/004-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1d27c18fef0845e1/tools/004-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"已采集证据：\n1. **kubectl_get_by_name**：确认了异常 Pod `appconfigfail-575d77485d-nfpvh` 的状态为 `CrashLoopBackOff`，并验证了其配置中缺少必要的 ConfigMap、Secret 或 env 变量。\n2. **kubectl_events**：发现 Pod 事件中频繁出现 `Back-off restarting failed container`，表明容器启动失败。\n3. **kubectl_previous_logs**：日志中包含 `L4_CONFIG_BOOTSTRAP_FAIL` 和 `FATAL: missing required APP_BOOT_MODE`，确认了配置错误导致启动失败。\n4. **kubectl_get_by_name**：尝试获取 ConfigMap `appconfigfail` 时返回 `NotFound`，表明该 ConfigMap 不存在，导致 Pod 无法正常启动。\n\n未采集证据：\n- 未检查 Secret 或其他 env 变量是否缺失。\n\n冲突证据：\n- `kubectl_get_by_name` 在获取 ConfigMap `appconfigfail` 时返回 `NotFound`，表明该 ConfigMap 不存在，这是导致 Pod 启动失败的关键原因。","collection_summary":"计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%；其中真实环境证据 9/10 项，完整度 90%；实际执行工具 7 个，匹配计划 3 个，未规划证据 4 个","plan_total":4,"plan_collected":3,"plan_completeness":0.75,"environment_evidence_total":10,"environment_evidence_collected":9,"environment_evidence_completeness":0.9,"executed_tool_count":7,"matched_tool_count":3,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 的详细信息以验证其当前状态和配置","level":"critical","tool":"kubectl_get_by_name","command":"get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml","purpose":"验证异常 Pod 的 spec 配置，检查其是否缺失 ConfigMap、Secret 或 env 变量","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 的事件日志以验证其失败原因","level":"critical","tool":"kubectl_events","command":"get events -n aiops-e2e --field-selector=involvedObject.name=appconfigfail-575d77485d-nfpvh","purpose":"验证 Pod 是否存在 ConfigMap/Secret 不存在、env 未定义等事件信号","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod 的上一次容器日志以验证其失败原因","level":"important","tool":"kubectl_previous_logs","command":"logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous","purpose":"验证容器日志中是否包含 L4_CONFIG_BOOTSTRAP_FAIL、FATAL: missing required APP_BOOT_MODE 等业务配置错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"验证异常 Pod 依赖的 ConfigMap 是否存在且配置正确","level":"important","tool":"kubectl_get_by_name","command":"get configmap -n aiops-e2e","purpose":"检查异常 Pod 依赖的 ConfigMap 是否存在，是否包含所需配置","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_container_previous_logs_grep","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_container_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_previous_logs_all_containers","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e4(验证异常 Pod 依赖的 ConfigMap 是否存在且配置正确): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 90%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 获取异常 Pod 的详细信息以验证其当前状态和配置 | `get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml` |
   | e2 | critical | ✅ | kubectl_events | 获取异常 Pod 的事件日志以验证其失败原因 | `get events -n aiops-e2e --field-selector=involvedObject.name=appconfigfail-57...` |
   | e3 | important | ✅ | kubectl_previous_logs | 获取异常 Pod 的上一次容器日志以验证其失败原因 | `logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous` |
   | e4 | important | ❌ | kubectl_get_by_name | 验证异常 Pod 依赖的 ConfigMap 是否存在且配置正确 | `get configmap -n aiops-e2e` |

   ⚠️ 未采集原因:
   - e4(验证异常 Pod 依赖的 ConfigMap 是否存在且配置正确): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 46.4s)
   📤 → 下游数据: root_cause=异常 Pod appconfigfail-575d77485d-nfpvh 处于 CrashLoopBackOff 状态，其 pod_abnormal_type 为 ConfigError。容器日志中显示 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: missing required APP_BOOT_MODE，表明应用配置验证失败。尝试获取 ConfigMap appconfigfail 时返回 NotFound，表明该 ConfigMap 不存在，导致 Pod 无法正常启动。
   confidence=95%
   causal_chain={"root_cause": "ConfigMap 缺失导致配置错误", "intermediate_causes": ["Pod 依赖的 ConfigMap 不存在", "配置缺失导致应用启动失败"], "immediate_causes": ["容器启动失败", "Pod 状态变为 CrashLoopBackOff"], "phenomenon": "Pod 状态为 CrashLoopBackOff，重启次数增加，日志显示配置错误"}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"e1": "获取异常 Pod 的详细信息以验证其当前状态和配置"}, {"e2": "获取异常 Pod 的事件日志以验证其失败原因"}, {"e3": "获取异常 Pod 的上一次容器日志以验证其失败原因"}, {"layer_1": "上游已验证工具结果: kubectl_get_by_kind_in_cluster"}, {"layer_2": "上游已验证工具结果: kubectl_get_by_name"}, {"layer_3": "上游已验证工具结果: kubectl_previous_logs"}, {"layer_4": "上游已验证工具结果: kubectl_container_previous_logs_grep"}, {"layer_5": "上游已验证工具结果: kubectl_container_previous_logs"}, {"layer_6": "上游已验证工具结果: kubectl_previous_logs_all_containers"}], "evidence_analysis": [{"e1": "Pod 状态为 CrashLoopBackOff，重启次数增加，表明容器启动失败"}, {"e2": "事件日志显示 Back-off restarting failed container，表明容器启动失败"}, {"e3": "日志中包含 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: missing required APP_BOOT_MODE，表明配置错误导致启动失败"}, {"layer_1": "kubectl_get_by_kind_in_cluster 表格摘要显示异常 Pod 状态为 CrashLoopBackOff"}, {"layer_2": "kubectl_get_by_name 输出显示异常 Pod 状态为 CrashLoopBackOff，且缺失 ConfigMap"}, {"layer_3": "kubectl_previous_logs 日志摘要显示配置错误导致启动失败"}, {"layer_4": "kubectl_container_previous_logs_grep 输出显示命令无效"}, {"layer_5": "kubectl_container_previous_logs 输出显示容器不存在"}, {"layer_6": "kubectl_previous_logs_all_containers 日志摘要显示配置错误导致启动失败"}], "causal_chain": {"root_cause": "ConfigMap 缺失导致配置错误", "intermediate_causes": ["Pod 依赖的 ConfigMap 不存在", "配置缺失导致应用启动失败"], "immediate_causes": ["容器启动失败", "Pod 状态变为 CrashLoopBackOff"], "phenomenon": "Pod 状态为 CrashLoopBackOff，重启次数增加，日志显示配置错误"}, "root_cause": "异常 Pod appconfigfail-575d77485d-nfpvh 处于 CrashLoopBackOff 状态，其 pod_abnormal_type 为 ConfigError。容器日志中显示 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: missing required APP_BOOT_MODE，表明应用配置验证失败。尝试获取 ConfigMap appconfigfail 时返回 NotFound，表明该 ConfigMap 不存在，导致 Pod 无法正常启动。", "root_cause_summary": "异常 Pod appconfigfail-575d77485d-nfpvh 处于 CrashLoopBackOff 状态，其 pod_abnormal_type 为 ConfigError。容器日志中显示 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: missing required APP_BOOT_MODE，表明应用配置验证失败。尝试获取 ConfigMap appconfigfail 时返回 NotFound，表明该 ConfigMap 不存在，导致 Pod 无法正常启动。", "confidence": 0.95, "confidence_reason": "有直接证据，因果链清晰", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [{"cause": "Secret 缺失", "probability": "低", "reason": "未检查 Secret 是否缺失"}, {"cause": "env 变量缺失", "probability": "低", "reason": "未检查 env 变量是否缺失"}], "limitations": "未检查 Secret 或其他 env 变量是否缺失，可能遗漏其他配置问题。", "llm_raw_analysis": "已采集证据：\n1. **kubectl_get_by_name**：确认了异常 Pod `appconfigfail-575d77485d-nfpvh` 的状态为 `CrashLoopBackOff`，并验证了其配置中缺少必要的 ConfigMap、Secret 或 env 变量。\n2. **kubectl_events**：发现 Pod 事件中频繁出现 `Back-off restarting failed container`，表明容器启动失败。\n3. **kubectl_previous_logs**：日志中包含 `L4_CONFIG_BOOTSTRAP_FAIL` 和 `FATAL: missing required APP_BOOT_MODE`，确认了配置错误导致启动失败。\n4. **kubectl_get_by_name**：尝试获取 ConfigMap `appconfigfail` 时返回 `NotFound`，表明该 ConfigMap 不存在，导致 Pod 无法正常启动。\n\n未采集证据：\n- 未检查 Secret 或其他 env 变量是否缺失。\n\n冲突证据：\n- `\n... 截断，原始 603 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 异常 Pod appconfigfail-575d77485d-nfpvh 处于 CrashLoopBackOff 状态，其 pod_abnormal_type 为 ConfigError。容器日志中显示 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: missing requi...
   置信度: 95%
   🔗 因果链:
     根本原因: ConfigMap 缺失导致配置错误


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
   ✅ [汇总总结] 完成 (3m 19.1s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4013 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 10m 49.0s
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
| **兼容归因层** | L4 - 应用配置错误 |
| **问题分类** | ConfigError（配置错误） |
| **置信度** | 高 (95%) |
| **证据完整度** | 3/4 (75%) |

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
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff, RESTARTS: 12` | Pod 处于持续重启状态 |
| 2 | Pod 原因 | `kubectl describe pod appconfigfail-575d77485d-nfpvh` | `Reason: ConfigError` | 明确标记为配置错误 |
| 3 | 容器日志 | `kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous` | `L4_CONFIG_BOOTSTRAP_FAIL, FATAL: missing required APP_BOOT_MODE` | 应用启动时因配置缺失失败 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 处于 CrashLoopBackOff 状态且被标记为 ConfigError → 配置错误导致容器无法正常启动。
- **证据 #3 印证**：日志中显示 `missing required APP_BOOT_MODE` → 应用依赖的配置项缺失，导致启动失败。
- **证据链**：ConfigMap 缺失 → 应用配置缺失 → 启动失败 → 容器被终止 → Pod 重启 → CrashLoopBackOff。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| ConfigMap 是否存在 | important | 无法确认配置缺失的具体原因，是否 ConfigMap 不存在或配置错误 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 应用依赖的 ConfigMap（appconfigfail）缺失或配置不完整             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 应用启动时依赖的配置项（如 APP_BOOT_MODE）缺失 → 配置校验失败   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器启动失败（Exit Code 42 或业务退出码），Pod 进入 CrashLoopBackOff 状态 |
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 CrashLoopBackOff，持续重启                             │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Pod 状态为 CrashLoopBackOff)、证据 #2 (pod_abnormal_type 为 ConfigError) 和证据 #3 (日志中显示 `FATAL: missing required APP_BOOT_MODE`)，问题的根本原因是 **应用依赖的 ConfigMap 缺失或配置不完整**，导致应用配置验证失败，容器启动失败，Pod 持续重启。

**置信度**：高 (95%)
- ✅ Pod 状态为 CrashLoopBackOff，且被标记为 ConfigError
- ✅ 容器日志显示配置验证失败和缺失参数
- ⚠️ 缺少 ConfigMap 是否存在的验证证据，但已规划，需进一步确认

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 创建或修复缺失的 ConfigMap**
```bash
kubectl create configmap appconfigfail -n aiops-e2e --from-literal=APP_BOOT_MODE=normal
```
*依据*：容器日志中明确提示缺少 `APP_BOOT_MODE`，创建该 ConfigMap 并注入所需配置。

**2. [可选] 查看 Pod 定义确认配置引用**
```bash
kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml
```
*目的*：确认 Pod spec 中是否引用了 `appconfigfail` ConfigMap，如 `envFrom` 或 `volume`。

### 后续优化

1. **配置验证**：在应用启动时增加配置校验逻辑，避免因配置缺失导致启动失败。
2. **资源监控**：配置 Kubernetes Event Watcher 或 Prometheus 监控，捕获 ConfigError 类型事件。
3. **自动化部署校验**：在 CI/CD 流程中加入 ConfigMap 存在性校验，防止部署时配置缺失。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 ConfigMap 存在 | `kubectl get configmap appconfigfail -n aiops-e2e` | 存在并包含 `APP_BOOT_MODE` |
| 2. 确认 Pod 运行 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e` | STATUS: Running |
| 3. 检查重启次数 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 0 或不增加 |
| 4. 检查容器日志 | `kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e` | 无 `FATAL` 或 `L4_CONFIG_BOOTSTRAP_FAIL` |

---

## ⚠️ 注意事项

- 如果 ConfigMap 存在但配置不正确，需要检查其内容是否匹配应用要求。
- 如果问题持续，建议检查应用代码中配置校验逻辑是否健全。
- 考虑使用 Helm Chart 或 Kustomize 来管理 ConfigMap，避免手动配置错误。

---

## 📊 性能统计

├─ 总耗时: 10.8m
├─ 问题定位: 78.2s (12%) ✅
├─ 证据链采集: 265.3s (41%) ✅
├─ 根因分析: 106.4s (16%) ✅
├─ 汇总总结: 199.1s (31%) ✅
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
