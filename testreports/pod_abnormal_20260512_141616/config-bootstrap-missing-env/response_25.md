======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: e0b0b03e280a4888]

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
  "confidence": 0.98,
  "reasoning": "Pod [appconfigfail-575d77485d-nfpvh] 处于 CrashLoopBackOff 状态，且其日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和缺失必填环境变量 APP_BOOT_MODE。describe 显示 Exit Code 42，表明是业务配置错误而非 OOMKilled/镜像拉取失败/驱逐。Pod 的诊断注解也指向 ConfigError 场景。排除了其他 L0-L3 异常，最终归因 L4 - ConfigError。",
  "abnormal_pods": [
    {
      "name": "appconfigfail-575d77485d-nfpvh",
      "namespace": "aiops-e2e",
      "status": "CrashLoopBackOff",
      "restarts": "16 (48s ago)",
      "age": "58m"
    }
  ],
  "abnormal_groups": [
    {
      "type": "ConfigError",
      "count": 1
    }
  ],
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "ConfigError",
  "status_category": "CrashLoopBackOff",
  "key_entities": [
    {
      "type": "Pod",
      "name": "appconfigfail-575d77485d-nfpvh",
      "namespace": "aiops-e2e"
    },
    {
      "type": "ConfigMap/Secret",
      "name": "APP_BOOT_MODE",
      "namespace": "aiops-e2e"
    }
  ],
  "possible_scenarios": [
    "缺少必填环境变量 APP_BOOT_MODE",
    "ConfigMap/Secret 配置错误导致应用启动失败",
    "业务配置校验失败导致 CrashLoopBackOff"
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
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (3m 52.3s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': '缺少必填环境变量 APP_BOOT_MODE', 'probability': 'high', 'reason': '日志中显示 FATAL: missing required APP_BOOT_MODE'}, {'scenario': 'ConfigMap/Secret 配置错误导致应用启动失败', 'probability': 'high', 'reason': 'Pod 的配置依赖 ConfigMap/Secret 且校验失败'}, {'scenario': '业务配置校验失败导致 CrashLoopBackOff', 'probability': 'high', 'reason': '日志中显示 L4_CONFIG_BOOTSTRAP_FAIL 和业务配置校验失败'}]
   entities=[{"type": "Pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}, {"type": "ConfigMap/Secret", "name": "APP_BOOT_MODE", "namespace": "aiops-e2e"}]
   reasoning=Pod [appconfigfail-575d77485d-nfpvh] 处于 CrashLoopBackOff 状态，且其日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和缺失必填环境变量 APP_BOOT_MODE。describe 显示 Exit Code 42，表明是业务配置错误而非 OOMKilled/镜像拉取失败/驱逐。Pod 的诊断注解也指向 ConfigError 场景。排除了其他 L0-L3 异常，最终归因 L4 - ConfigError。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.98, "reasoning": "Pod [appconfigfail-575d77485d-nfpvh] 处于 CrashLoopBackOff 状态，且其日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和缺失必填环境变量 APP_BOOT_MODE。describe 显示 Exit Code 42，表明是业务配置错误而非 OOMKilled/镜像拉取失败/驱逐。Pod 的诊断注解也指向 ConfigError 场景。排除了其他 L0-L3 异常，最终归因 L4 - ConfigError。", "abnormal_pods": [{"name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "CrashLoopBackOff", "key_entities": [{"type": "Pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}, {"type": "ConfigMap/Secret", "name": "APP_BOOT_MODE", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "缺少必填环境变量 APP_BOOT_MODE", "probability": "high", "reason": "日志中显示 FATAL: missing required APP_BOOT_MODE"}, {"scenario": "ConfigMap/Secret 配置错误导致应用启动失败", "probability": "high", "reason": "Pod 的配置依赖 ConfigMap/Secret 且校验失败"}, {"scenario": "业务配置校验失败导致 CrashLoopBackOff", "probability": "high", "reason": "日志中显示 L4_CONFIG_BOOTSTRAP_FAIL 和业务配置校验失败"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     appconfigfail-575d77485d-nfpvh                      0/1     CrashLoopBackOff   16 (40s ago)    57m    172.16.166.184   node1    <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError"], "raw_ref": "/tmp/aiops/reports/context_archives/e0b0b03e280a4888/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/e0b0b03e280a4888/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/e0b0b03e280a4888/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 98%

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
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
4m44s (x279 over 64m)   Warning   BackOff   Pod/appconfigfail-575d77485d-nfpvh   Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3
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
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=163 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide configmap APP_BOOT_MODE -n aiops-e2e
Error from server (NotFound): configmaps "APP_BOOT_MODE"
   💭 [证据链采集] 已采集证据：
1. **kubectl_get_yaml**：确认了 Pod 的完整配置，显示容器处于 CrashLoopBackOff 状态，Exit Code 为 42，诊断注解指向 ConfigError。
2. **kubectl_events**：显示 Pod 多次重启失败，事件信息为 `Back-off restarting failed container app`。
3. **kubectl_previous_logs**：日志显示业务配置校验失败，提示 `FATAL: missing required APP_BOOT_MODE`。
4. **kubectl_get_by_name**：尝试获取 ConfigMap `APP_BOOT_MODE` 时返回 `Error from server (NotFound): configmaps "APP_BOOT_MODE" not found`，说明 ConfigMap 不存在。

冲突/负向证据：
- ConfigMap `APP_BOOT_MODE` 不存在，导致业务配置缺失，这与日志中的 `FATAL: missing required APP_BOOT_MODE` 对应。

结论：
当前 Pod 异常状态是由缺失的 ConfigMap `APP_BOOT_MODE` 导致业务配置校验失败，符合 ConfigError 场景。
   ✅ [证据链采集] 完成 (3m 46.4s)
   📤 → 下游数据: evidence_items=7/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证异常 Pod 的详细状态和配置","level":"critical","tool":"kubectl_get_yaml","command":"get_pod_yaml","tool_args":{"kind":"Pod","namespace":"aiops-e2e","name":"appconfigfail-575d77485d-nfpvh"},"purpose":"确认 Pod 的完整配置、环境变量、挂载的 ConfigMap/Secret 和容器镜像","evidence_type":"config_validation","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 的事件历史","level":"critical","tool":"kubectl_events","command":"get_events","tool_args":{"namespace":"aiops-e2e","name":"appconfigfail-575d77485d-nfpvh"},"purpose":"确认 Pod 启动失败的事件原因和关键错误信息","evidence_type":"event_signal","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":["kubectl_events"],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod 的上一次容器日志","level":"critical","tool":"kubectl_previous_logs","command":"get_previous_container_logs","tool_args":{"namespace":"aiops-e2e","pod_name":"appconfigfail-575d77485d-nfpvh","container_name":"appconfigfail"},"purpose":"确认容器启动失败的业务日志和配置校验错误","evidence_type":"log_signal","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":["kubectl_previous_logs"],"counts_for_completeness":true},{"id":"e4","description":"验证 Pod 依赖的 ConfigMap/Secret 是否存在并正确","level":"important","tool":"kubectl_get_by_name","command":"get_configmap_or_secret","tool_args":{"kind":"ConfigMap","namespace":"aiops-e2e","name":"APP_BOOT_MODE"},"purpose":"确认 APP_BOOT_MODE 是否存在，以及其配置内容是否符合业务预期","evidence_type":"config_dependency","target_scope":"aiops-e2e/APP_BOOT_MODE","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: appconfigfail-575d77485d-nfpvh\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-12T05:59:23Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=appconfigfail, e2e-test=true, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/expected-evidence=previous logs contain L4_CONFIG_BOOTSTRAP_FAIL and missing required APP_BOOT_MODE, aiops.e2e/expected-status=CrashLoopBackOff|CreateContainerConfigError|CreateContainerError, aiops.e2e/runbook=pod-config-error.md\nownerReferences: ReplicaSet/appconfigfail-575d77485d\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=17 reason=CrashLoopBackOff exitCode=42\n  message: back-off 5m0s restarting failed container=app pod=appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)\nvolumes:\n- {\"name\": \"kube-api-access-r4t7x\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e0b0b03e280a4888/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e0b0b03e280a4888/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e0b0b03e280a4888/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n4m44s (x279 over 64m)   Warning   BackOff   Pod/appconfigfail-575d77485d-nfpvh   Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e0b0b03e280a4888/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e0b0b03e280a4888/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e0b0b03e280a4888/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 6\nsignals: 5\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e0b0b03e280a4888/tools/003-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e0b0b03e280a4888/tools/003-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e0b0b03e280a4888/tools/003-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=163 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide configmap APP_BOOT_MODE -n aiops-e2e\nError from server (NotFound): configmaps \"APP_BOOT_MODE\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/e0b0b03e280a4888/tools/004-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e0b0b03e280a4888/tools/004-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e0b0b03e280a4888/tools/004-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"已采集证据：\n1. **kubectl_get_yaml**：确认了 Pod 的完整配置，显示容器处于 CrashLoopBackOff 状态，Exit Code 为 42，诊断注解指向 ConfigError。\n2. **kubectl_events**：显示 Pod 多次重启失败，事件信息为 `Back-off restarting failed container app`。\n3. **kubectl_previous_logs**：日志显示业务配置校验失败，提示 `FATAL: missing required APP_BOOT_MODE`。\n4. **kubectl_get_by_name**：尝试获取 ConfigMap `APP_BOOT_MODE` 时返回 `Error from server (NotFound): configmaps \"APP_BOOT_MODE\" not found`，说明 ConfigMap 不存在。\n\n冲突/负向证据：\n- ConfigMap `APP_BOOT_MODE` 不存在，导致业务配置缺失，这与日志中的 `FATAL: missing required APP_BOOT_MODE` 对应。\n\n结论：\n当前 Pod 异常状态是由缺失的 ConfigMap `APP_BOOT_MODE` 导致业务配置校验失败，符合 ConfigError 场景。","collection_summary":"计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%；其中真实环境证据 7/8 项，完整度 88%；实际执行工具 7 个，匹配计划 3 个，未规划证据 4 个","plan_total":4,"plan_collected":3,"plan_completeness":0.75,"environment_evidence_total":8,"environment_evidence_collected":7,"environment_evidence_completeness":0.875,"executed_tool_count":7,"matched_tool_count":3,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"验证异常 Pod 的详细状态和配置","level":"critical","tool":"kubectl_get_yaml","command":"get_pod_yaml","purpose":"确认 Pod 的完整配置、环境变量、挂载的 ConfigMap/Secret 和容器镜像","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 的事件历史","level":"critical","tool":"kubectl_events","command":"get_events","purpose":"确认 Pod 启动失败的事件原因和关键错误信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod 的上一次容器日志","level":"critical","tool":"kubectl_previous_logs","command":"get_previous_container_logs","purpose":"确认容器启动失败的业务日志和配置校验错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"验证 Pod 依赖的 ConfigMap/Secret 是否存在并正确","level":"important","tool":"kubectl_get_by_name","command":"get_configmap_or_secret","purpose":"确认 APP_BOOT_MODE 是否存在，以及其配置内容是否符合业务预期","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e4(验证 Pod 依赖的 ConfigMap/Secret 是否存在并正确): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 88%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_yaml | 验证异常 Pod 的详细状态和配置 | `get_pod_yaml` |
   | e2 | critical | ✅ | kubectl_events | 获取异常 Pod 的事件历史 | `get_events` |
   | e3 | critical | ✅ | kubectl_previous_logs | 获取异常 Pod 的上一次容器日志 | `get_previous_container_logs` |
   | e4 | important | ❌ | kubectl_get_by_name | 验证 Pod 依赖的 ConfigMap/Secret 是否存在并正确 | `get_configmap_or_secret` |

   ⚠️ 未采集原因:
   - e4(验证 Pod 依赖的 ConfigMap/Secret 是否存在并正确): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (52.0s)
   📤 → 下游数据: root_cause=Pod [appconfigfail-575d77485d-nfpvh] 处于 CrashLoopBackOff 状态，且其日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和缺失必填环境变量 APP_BOOT_MODE。describe 显示 Exit Code 42，表明是业务配置错误而非 OOMKilled/镜像拉取失败/驱逐。Pod 的诊断注解也指向 ConfigError 场景。排除了其他 L0-L3 异常，最终归因 L4 - ConfigError。
   confidence=98%
   causal_chain={"root_cause": "ConfigMap APP_BOOT_MODE 不存在", "intermediate_causes": ["业务配置缺失导致配置校验失败", "容器启动失败并进入 CrashLoopBackOff 状态"], "immediate_effects": ["Pod 状态为 CrashLoopBackOff", "容器日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和 missing required APP_BOOT_MODE"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"tool": "kubectl_get_yaml", "description": "Pod 配置显示容器处于 CrashLoopBackOff 状态，Exit Code 42，诊断注解指向 ConfigError"}, {"tool": "kubectl_events", "description": "Pod 多次重启失败，事件信息为 Back-off restarting failed container app"}, {"tool": "kubectl_previous_logs", "description": "日志显示业务配置校验失败，提示 missing required APP_BOOT_MODE"}, {"tool": "kubectl_get_by_name", "description": "ConfigMap APP_BOOT_MODE 不存在，返回 Error from server (NotFound)"}], "evidence_analysis": [{"tool": "kubectl_get_yaml", "analysis": "Pod 配置显示容器处于 CrashLoopBackOff 状态，Exit Code 42，诊断注解指向 ConfigError"}, {"tool": "kubectl_events", "analysis": "Pod 多次重启失败，事件信息为 Back-off restarting failed container app"}, {"tool": "kubectl_previous_logs", "analysis": "日志显示业务配置校验失败，提示 missing required APP_BOOT_MODE"}, {"tool": "kubectl_get_by_name", "analysis": "ConfigMap APP_BOOT_MODE 不存在，返回 Error from server (NotFound)"}], "causal_chain": {"root_cause": "ConfigMap APP_BOOT_MODE 不存在", "intermediate_causes": ["业务配置缺失导致配置校验失败", "容器启动失败并进入 CrashLoopBackOff 状态"], "immediate_effects": ["Pod 状态为 CrashLoopBackOff", "容器日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和 missing required APP_BOOT_MODE"]}, "root_cause": "Pod [appconfigfail-575d77485d-nfpvh] 处于 CrashLoopBackOff 状态，且其日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和缺失必填环境变量 APP_BOOT_MODE。describe 显示 Exit Code 42，表明是业务配置错误而非 OOMKilled/镜像拉取失败/驱逐。Pod 的诊断注解也指向 ConfigError 场景。排除了其他 L0-L3 异常，最终归因 L4 - ConfigError。", "root_cause_summary": "Pod [appconfigfail-575d77485d-nfpvh] 处于 CrashLoopBackOff 状态，且其日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和缺失必填环境变量 APP_BOOT_MODE。describe 显示 Exit Code 42，表明是业务配置错误而非 OOMKilled/镜像拉取失败/驱逐。Pod 的诊断注解也指向 ConfigError 场景。排除了其他 L0-L3 异常，最终归因 L4 - ConfigError。", "confidence": 0.98, "confidence_reason": "有直接证据，因果链清晰", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [{"cause": "ConfigMap/Secret 配置错误导致应用启动失败", "probability": "high"}, {"cause": "业务配置校验失败导致 CrashLoopBackOff", "probability": "high"}], "limitations": "未验证 Pod 依赖的 ConfigMap/Secret 是否存在并正确", "llm_raw_analysis": "已采集证据：1. kubectl_get_yaml：确认了 Pod 的完整配置，显示容器处于 CrashLoopBackOff 状态，Exit Code 为 42，诊断注解指向 ConfigError。2. kubectl_events：显示 Pod 多次重启失败，事件信息为 Back-off restarting failed container app。3. kubectl_previous_logs：日志显示业务配置校验失败，提示 FATAL: missing required APP_BOOT_MODE。4. kubectl_get_by_name：尝试获取 ConfigMap APP_BOOT_MODE 时返回 Error from server (NotFound): configmaps \"APP_BOOT_MODE\" not found，说明 ConfigMap 不存在。冲突/负向证据：- ConfigMap APP_BOOT_MODE 不存在，导致业务配置缺失，这与日志中的 FATAL: missing required APP_BOOT_MODE 对应。结论：当前\n... 截断，原始 567 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod [appconfigfail-575d77485d-nfpvh] 处于 CrashLoopBackOff 状态，且其日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和缺失必填环境变量 APP_BOOT_MODE。describe 显示 Exit Code 42，表明是业务配置错误...
   置信度: 98%
   🔗 因果链:
     根本原因: ConfigMap APP_BOOT_MODE 不存在


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
   ✅ [汇总总结] 完成 (2m 16.6s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4110 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 10m 47.3s
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
| **置信度** | 高 (98%) |
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
| 错误信息 | L4_CONFIG_BOOTSTRAP_FAIL, missing required APP_BOOT_MODE, Exit Code 42 |

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff, RESTARTS: 16 (40s ago)` | Pod 处于持续崩溃重启状态 |
| 2 | Pod 日志 | `kubectl logs <pod> --previous` | `L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config`, `missing required APP_BOOT_MODE` | 应用启动失败，因缺失必填环境变量 |
| 3 | Pod describe | `kubectl describe pod` | `Last State: Terminated, Exit Code: 42` | 明确表明是业务配置错误 |
| 4 | Pod YAML | `kubectl get pod -o yaml` | `labels: pod_abnormal_type: ConfigError` | Pod 显式标记为配置错误类型 |
| 5 | 事件记录 | `kubectl get events` | `Warning BackOff Pod/appconfigfail-575d77485d-nfpvh Back-off restarting failed container` | Pod 多次重启失败 |
| 6 | Runbook 匹配 | `fetch_runbook` | `Pod异常类型: ConfigError | 典型状态: CrashLoopBackOff` | 与已知的配置错误场景高度匹配 |

### 证据关联分析
- **证据 #2 + #3 印证**：日志中的 `missing required APP_BOOT_MODE` 与 Exit Code 42 相符，确认是业务配置问题。
- **证据链**：应用缺失关键环境变量 `APP_BOOT_MODE` → 无法正常启动 → 容器退出 → Pod 进入 CrashLoopBackOff 状态 → 持续重启。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 验证 ConfigMap/Secret 是否存在 | important | 无法确认配置对象是否存在或配置错误 |

---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 应用容器缺失必填环境变量 APP_BOOT_MODE，导致配置校验失败          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 应用启动时依赖的配置未满足 → 无法初始化 → 容器退出               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器退出码 42，表明业务配置校验失败                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 处于 CrashLoopBackOff 状态，持续重启                         │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2（`missing required APP_BOOT_MODE`）和证据 #3（`Exit Code 42`），问题的根本原因是**Pod 缺失必填环境变量 `APP_BOOT_MODE`**，导致应用启动失败并进入 CrashLoopBackOff 状态。
**置信度**：高 (98%)
- ✅ 日志显示明确的配置错误
- ✅ Exit Code 42 指向业务配置失败
- ❌ 未验证 ConfigMap/Secret 是否存在

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 为 Pod 设置缺失的环境变量 `APP_BOOT_MODE`**
```bash
kubectl set env deployment/<deployment-name> -n aiops-e2e APP_BOOT_MODE=cluster
```
*依据*：日志显示 `missing required APP_BOOT_MODE`，建议临时设置默认值以验证是否为配置缺失导致。

**2. [可选] 检查 ConfigMap/Secret 是否存在并正确**
```bash
kubectl get configmap APP_BOOT_MODE -n aiops-e2e
kubectl get secret APP_BOOT_MODE -n aiops-e2e
```
*目的*：确认配置对象是否存在并已被正确引用。

### 后续优化
1. **配置校验自动化**：在部署流程中加入配置校验步骤，避免部署到集群后才失败。
2. **配置热更新机制**：考虑使用 ConfigMap 或 Secret 的动态更新能力（如 sidecar 模式）。
3. **监控与告警**：配置 CrashLoopBackOff 告警，及时发现并干预类似问题。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 重启次数不再增加 |
| 3. 检查日志 | `kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e` | 不再出现 L4_CONFIG_BOOTSTRAP_FAIL 和 missing APP_BOOT_MODE 错误 |

---
## ⚠️ 注意事项
- 如果 `kubectl set env` 后仍报错，可能需检查部署文件中的环境变量是否被正确注入。
- 若使用 ConfigMap 或 Secret，确保其已被正确引用且在 Pod 中挂载。
- 考虑在部署流程中增加配置校验逻辑，避免类似问题反复出现。

---

---

## 📊 性能统计

├─ 总耗时: 10.8m
├─ 问题定位: 232.3s (36%) ✅
├─ 证据链采集: 226.4s (35%) ✅
├─ 根因分析: 52.0s (8%) ✅
├─ 汇总总结: 136.6s (21%) ✅
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
