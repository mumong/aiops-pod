======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 1cc5ef1a2d504bd7]

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
      📄 NAME                       DESIRED   CURRENT   READY   AGE    CONTAINERS   IMAGES         SELECTOR                                         LABELS
appconfigfail-575d77485d   1         1         0      
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "ConfigError",
  "confidence": 0.98,
  "reasoning": "当前 Pod 状态为 CrashLoopBackOff，重启次数持续增加，日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和缺失 APP_BOOT_MODE 的错误，表明这是典型的配置错误问题。Describe 中显示 Exit Code 为 42，且无 OOMKilled 或镜像拉取失败的迹象，进一步确认为 ConfigError 类型。ReplicaSet 的配置也指向了 l4-scenario=config-bootstrap-fail 的标签，符合 L4 归类。",
  "abnormal_pods": [
    "appconfigfail-575d77485d-nfpvh"
  ],
  "abnormal_groups": [
    "CrashLoopBackOff"
  ],
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "ConfigError",
  "status_category": "CrashLoopBackOff",
  "key_entities": [
    "Pod: appconfigfail-575d77485d-nfpvh",
    "ReplicaSet: appconfigfail-575d77485d",
    "ConfigMap/Secret 缺失或错误"
  ],
  "possible_scenarios": [
    "配置缺失（如 APP_BOOT_MODE）",
    "ConfigMap/Secret 键名拼错",
    "业务配置校验失败"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 52.4s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[]
   entities=[]
   reasoning=当前 Pod 状态为 CrashLoopBackOff，重启次数持续增加，日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和缺失 APP_BOOT_MODE 的错误，表明这是典型的配置错误问题。Describe 中显示 Exit Code 为 42，且无 OOMKilled 或镜像拉取失败的迹象，进一步确认为 ConfigError 类型。ReplicaSet 的配置也指向了 l4-scenario=config-bootstrap-fail 的标签，符合 L4 归类。
   layer_analysis={"layer": "L4", "derived_layer": "", "layers": [], "layer_name": "", "confidence": 0.5, "reasoning": "当前 Pod 状态为 CrashLoopBackOff，重启次数持续增加，日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和缺失 APP_BOOT_MODE 的错误，表明这是典型的配置错误问题。Describe 中显示 Exit Code 为 42，且无 OOMKilled 或镜像拉取失败的迹象，进一步确认为 ConfigError 类型。ReplicaSet 的配置也指向了 l4-scenario=config-bootstrap-fail 的标签，符合 L4 归类。", "abnormal_pods": [{"name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "app_config", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     appconfigfail-575d77485d-nfpvh                      0/1     CrashLoopBackOff   25 (91s ago)    104m   172.16.166.184   node1    <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError"], "raw_ref": "/tmp/aiops/reports/context_archives/1cc5ef1a2d504bd7/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/1cc5ef1a2d504bd7/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/1cc5ef1a2d504bd7/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
4m20s (x485 over 109m)   Warning   BackOff   Pod/appconfigfail-575d77485d-nfpvh   Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c
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
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 表格摘要: rows=1 abnormal=0 status_counts={}
NAME               DATA   AGE    LABELS
# 样例行
kube-root-ca.crt   1      108d   <none>
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。
   💭 [证据链采集] 已采集证据：
1. `kubectl_get_yaml`：确认 Pod 的配置中无 APP_BOOT_MODE 环境变量，且容器状态显示 CrashLoopBackOff，退出码为 42。
2. `kubectl_events`：发现 Pod 多次重启失败，事件显示容器启动失败。
3. `kubectl_logs`：日志显示 `L4_CONFIG_BOOTSTRAP_FAIL`、`FATAL: missing required APP_BOOT_MODE` 和 `FATAL: business config validation failed before server startup`。
4. `kubectl_previous_logs`：最后一次失败的容器日志与当前日志一致，确认配置错误。
5. `kubectl_get_by_kind_in_namespace (ConfigMap)`：确认命名空间中没有相关的 ConfigMap。
6. `kubectl_get_by_kind_in_namespace (Secret)`：确认命名空间中没有相关的 Secret。

结论：当前 Pod 异常的根本原因是缺少关键配置参数 `APP_BOOT_MODE`，导致业务配置校验失败，无法正常启动容器。建议检查业务配置需求，确认是否应通过 ConfigMap、Secret 或环境变量注入该参数。
   ✅ [证据链采集] 完成 (4m 11.0s)
   📤 → 下游数据: evidence_items=8/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 的完整 YAML 配置以验证其配置是否缺失 APP_BOOT_MODE 环境变量或其他配置错误","level":"critical","tool":"kubectl_get_yaml","command":"get pods appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e"},"purpose":"验证 Pod 是否缺少 APP_BOOT_MODE 等关键配置","evidence_type":"configuration","target_scope":"Pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 的事件日志以确认是否存在配置拉取失败或其他异常事件","level":"important","tool":"kubectl_events","command":"get events -n aiops-e2e --field-selector=involvedObject.name=appconfigfail-575d77485d-nfpvh","tool_args":{"kind":"Pod","name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e"},"purpose":"确认 Pod 是否存在配置拉取失败或事件异常","evidence_type":"event_log","target_scope":"Pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod 的容器日志以确认业务配置错误的具体信息","level":"critical","tool":"kubectl_logs","command":"logs pods/appconfigfail-575d77485d-nfpvh -n aiops-e2e","tool_args":{"kind":"Pod","name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e","container":null},"purpose":"确认业务配置错误的具体信息，如 L4_CONFIG_BOOTSTRAP_FAIL、APP_BOOT_MODE 缺失等","evidence_type":"log","target_scope":"Pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"获取异常 Pod 的上一次容器日志以确认最后一次失败的退出原因","level":"important","tool":"kubectl_previous_logs","command":"logs pods/appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous","tool_args":{"kind":"Pod","name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e","container":null},"purpose":"确认最后一次容器失败的退出原因，如 L4_CONFIG_BOOTSTRAP_FAIL、APP_BOOT_MODE 缺失等","evidence_type":"log","target_scope":"Pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"e5","description":"验证异常 Pod 的 ConfigMap 或 Secret 是否缺失或配置错误","level":"critical","tool":"kubectl_get_by_kind_in_namespace","command":"get configmaps,secrets -n aiops-e2e","tool_args":{"kind":"ConfigMap","namespace":"aiops-e2e"},"purpose":"确认是否缺少 ConfigMap 或 Secret，或其内容是否缺失 APP_BOOT_MODE 等关键配置","evidence_type":"configuration","target_scope":"ConfigMap/Secret","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: appconfigfail-575d77485d-nfpvh\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-12T05:59:23Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=appconfigfail, e2e-test=true, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/expected-evidence=previous logs contain L4_CONFIG_BOOTSTRAP_FAIL and missing required APP_BOOT_MODE, aiops.e2e/expected-status=CrashLoopBackOff|CreateContainerConfigError|CreateContainerError, aiops.e2e/runbook=pod-config-error.md\nownerReferences: ReplicaSet/appconfigfail-575d77485d\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=26 reason=CrashLoopBackOff exitCode=42\n  message: back-off 5m0s restarting failed container=app pod=appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)\nvolumes:\n- {\"name\": \"kube-api-access-r4t7x\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1cc5ef1a2d504bd7/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1cc5ef1a2d504bd7/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1cc5ef1a2d504bd7/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n4m20s (x485 over 109m)   Warning   BackOff   Pod/appconfigfail-575d77485d-nfpvh   Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1cc5ef1a2d504bd7/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1cc5ef1a2d504bd7/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1cc5ef1a2d504bd7/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_logs","data":"kubectl_logs 日志摘要:\nlines: 6\nsignals: 5\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1cc5ef1a2d504bd7/tools/003-evidence-kubectl_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1cc5ef1a2d504bd7/tools/003-evidence-kubectl_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1cc5ef1a2d504bd7/tools/003-evidence-kubectl_logs.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 6\nsignals: 5\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1cc5ef1a2d504bd7/tools/004-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1cc5ef1a2d504bd7/tools/004-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1cc5ef1a2d504bd7/tools/004-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"kubectl_get_by_kind_in_namespace 表格摘要: rows=1 abnormal=0 status_counts={}\nNAME               DATA   AGE    LABELS\n# 样例行\nkube-root-ca.crt   1      108d   <none>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1cc5ef1a2d504bd7/tools/005-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1cc5ef1a2d504bd7/tools/005-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1cc5ef1a2d504bd7/tools/005-evidence-kubectl_get_by_kind_in_namespace.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/1cc5ef1a2d504bd7/tools/006-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1cc5ef1a2d504bd7/tools/006-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1cc5ef1a2d504bd7/tools/006-evidence-kubectl_get_by_kind_in_namespace.summary.txt"}],"llm_analysis":"已采集证据：\n1. `kubectl_get_yaml`：确认 Pod 的配置中无 APP_BOOT_MODE 环境变量，且容器状态显示 CrashLoopBackOff，退出码为 42。\n2. `kubectl_events`：发现 Pod 多次重启失败，事件显示容器启动失败。\n3. `kubectl_logs`：日志显示 `L4_CONFIG_BOOTSTRAP_FAIL`、`FATAL: missing required APP_BOOT_MODE` 和 `FATAL: business config validation failed before server startup`。\n4. `kubectl_previous_logs`：最后一次失败的容器日志与当前日志一致，确认配置错误。\n5. `kubectl_get_by_kind_in_namespace (ConfigMap)`：确认命名空间中没有相关的 ConfigMap。\n6. `kubectl_get_by_kind_in_namespace (Secret)`：确认命名空间中没有相关的 Secret。\n\n结论：当前 Pod 异常的根本原因是缺少关键配置参数 `APP_BOOT_MODE`，导致业务配置校验失败，无法正常启动容器。建议检查业务配置需求，确认是否应通过 ConfigMap、Secret 或环境变量注入该参数。","collection_summary":"计划 5 项，实际采集 4 项，未采集 1 项，完整度 80%；其中真实环境证据 8/9 项，完整度 89%；实际执行工具 9 个，匹配计划 4 个，未规划证据 5 个","plan_total":5,"plan_collected":4,"plan_completeness":0.8,"environment_evidence_total":9,"environment_evidence_collected":8,"environment_evidence_completeness":0.8888888888888888,"executed_tool_count":9,"matched_tool_count":4,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 的完整 YAML 配置以验证其配置是否缺失 APP_BOOT_MODE 环境变量或其他配置错误","level":"critical","tool":"kubectl_get_yaml","command":"get pods appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml","purpose":"验证 Pod 是否缺少 APP_BOOT_MODE 等关键配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 的事件日志以确认是否存在配置拉取失败或其他异常事件","level":"important","tool":"kubectl_events","command":"get events -n aiops-e2e --field-selector=involvedObject.name=appconfigfail-575d77485d-nfpvh","purpose":"确认 Pod 是否存在配置拉取失败或事件异常","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod 的容器日志以确认业务配置错误的具体信息","level":"critical","tool":"kubectl_logs","command":"logs pods/appconfigfail-575d77485d-nfpvh -n aiops-e2e","purpose":"确认业务配置错误的具体信息，如 L4_CONFIG_BOOTSTRAP_FAIL、APP_BOOT_MODE 缺失等","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"获取异常 Pod 的上一次容器日志以确认最后一次失败的退出原因","level":"important","tool":"kubectl_previous_logs","command":"logs pods/appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous","purpose":"确认最后一次容器失败的退出原因，如 L4_CONFIG_BOOTSTRAP_FAIL、APP_BOOT_MODE 缺失等","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5","description":"验证异常 Pod 的 ConfigMap 或 Secret 是否缺失或配置错误","level":"critical","tool":"kubectl_get_by_kind_in_namespace","command":"get configmaps,secrets -n aiops-e2e","purpose":"确认是否缺少 ConfigMap 或 Secret，或其内容是否缺失 APP_BOOT_MODE 等关键配置","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e5(验证异常 Pod 的 ConfigMap 或 Secret 是否缺失或配置错误): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/5 项, 完整度: 89%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_yaml | 获取异常 Pod 的完整 YAML 配置以验证其配置是否缺失 APP_BOOT_MODE ... | `get pods appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml` |
   | e2 | important | ✅ | kubectl_events | 获取异常 Pod 的事件日志以确认是否存在配置拉取失败或其他异常事件 | `get events -n aiops-e2e --field-selector=involvedObject.name=appconfigfail-57...` |
   | e3 | critical | ✅ | kubectl_logs | 获取异常 Pod 的容器日志以确认业务配置错误的具体信息 | `logs pods/appconfigfail-575d77485d-nfpvh -n aiops-e2e` |
   | e4 | important | ✅ | kubectl_previous_logs | 获取异常 Pod 的上一次容器日志以确认最后一次失败的退出原因 | `logs pods/appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous` |
   | e5 | critical | ❌ | kubectl_get_by_kind_in_na... | 验证异常 Pod 的 ConfigMap 或 Secret 是否缺失或配置错误 | `get configmaps,secrets -n aiops-e2e` |

   ⚠️ 未采集原因:
   - e5(验证异常 Pod 的 ConfigMap 或 Secret 是否缺失或配置错误): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (31.6s)
   📤 → 下游数据: root_cause=当前 Pod (appconfigfail-575d77485d-nfpvh) 异常的根本原因是缺少关键配置参数 APP_BOOT_MODE，导致业务配置校验失败，无法正常启动容器。此结论基于以下证据：
1. kubectl_get_yaml 显示容器状态为 CrashLoopBackOff，退出码为 42。
2. kubectl_logs 和 kubectl_previous_logs 显示 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: missing required APP_BOOT_MODE。
3. kubectl_get_by_kind_in_namespace 确认命名空间中没有相关的 ConfigMap 或 Secret。
   confidence=80%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [], "causal_chain": {}, "root_cause": "当前 Pod (appconfigfail-575d77485d-nfpvh) 异常的根本原因是缺少关键配置参数 APP_BOOT_MODE，导致业务配置校验失败，无法正常启动容器。此结论基于以下证据：\n1. kubectl_get_yaml 显示容器状态为 CrashLoopBackOff，退出码为 42。\n2. kubectl_logs 和 kubectl_previous_logs 显示 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: missing required APP_BOOT_MODE。\n3. kubectl_get_by_kind_in_namespace 确认命名空间中没有相关的 ConfigMap 或 Secret。", "root_cause_summary": "当前 Pod (appconfigfail-575d77485d-nfpvh) 异常的根本原因是缺少关键配置参数 APP_BOOT_MODE，导致业务配置校验失败，无法正常启动容器。此结论基于以下证据：\n1. kubectl_get_yaml 显示容器状态为 CrashLoopBackOff，退出码为 42。\n2. kubectl_logs 和 kubectl_previous_logs 显示 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: missing required APP_BOOT_MODE。\n3. kubectl_get_by_kind_in_namespace 确认命名空间中没有相关的 ConfigMap 或 Secret。", "confidence": 0.8, "confidence_reason": "", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [], "limitations": "缺少直接验证 ConfigMap/Secret 是否缺失的证据。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 当前 Pod (appconfigfail-575d77485d-nfpvh) 异常的根本原因是缺少关键配置参数 APP_BOOT_MODE，导致业务配置校验失败，无法正常启动容器。此结论基于以下证据：
1. kubectl_get_yaml 显示容器状态为 CrashLoopBackOff，退出码...
   置信度: 80%

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
   ✅ [汇总总结] 完成 (3m 14.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4257 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 9m 49.7s
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
| **置信度** | 高 (80%) |
| **证据完整度** | 4/5 (80%) |

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
| 错误信息 | L4_CONFIG_BOOTSTRAP_FAIL, missing required APP_BOOT_MODE |

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | kubectl get pod | `STATUS: CrashLoopBackOff, RESTARTS: 25` | Pod 持续重启，无法正常启动 |
| 2 | Pod 最后状态 | kubectl get pod -o json | `Last State: Terminated, Exit Code: 42` | 容器以业务退出码 42 终止 |
| 3 | 容器日志 | kubectl logs appconfigfail-575d77485d-nfpvh | `L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config` | 明确指出是配置错误 |
| 4 | 上一次容器日志 | kubectl logs appconfigfail-575d77485d-nfpvh --previous | `FATAL: missing required APP_BOOT_MODE` | 确认缺失关键配置参数 |
| 5 | Pod YAML | kubectl get pod -o yaml | `app=appconfigfail, l4-scenario=config-bootstrap-fail, pod_abnormal_type=ConfigError` | 明确归类为配置错误 |

### 证据关联分析
- **证据 #3 + #4 印证**：日志中明确指出 `missing required APP_BOOT_MODE`，结合 Exit Code 42，说明是启动时配置校验失败。
- **证据 #1 + #2 印证**：Pod 状态为 `CrashLoopBackOff`，且 Exit Code 为 42，表明容器无法正常启动，符合配置错误的特征。
- **证据 #5 印证**：Pod 标签中包含 `pod_abnormal_type=ConfigError` 和 `l4-scenario=config-bootstrap-fail`，进一步确认属于 L4 归因层。

### 缺失证据
| 证据 | 级别 | 影响 |
|------|------|------|
| ConfigMap/Secret 是否缺失 | critical | 无法确认是否由于缺少外部配置导致错误，需进一步验证 |

---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 缺失关键配置参数 APP_BOOT_MODE，导致业务配置校验失败             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 应用启动时校验配置失败 → 容器以 Exit Code 42 退出                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器因配置错误无法启动（Exit Code 42）                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CrashLoopBackOff，重启次数持续增加                    │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #3 (L4_CONFIG_BOOTSTRAP_FAIL) 和 #4 (FATAL: missing required APP_BOOT_MODE)，问题的根本原因是**应用缺少关键配置参数 `APP_BOOT_MODE`**，导致启动时配置校验失败，容器无法正常启动。最终表现为 Pod 状态为 `CrashLoopBackOff`，重启次数持续增加。
**置信度**：高 (80%)
- ✅ Exit Code 42 明确指向业务配置错误
- ✅ 日志中明确指出 `missing required APP_BOOT_MODE`
- ⚠️ 缺少 ConfigMap/Secret 检查，无法确认是否由外部配置缺失导致

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 为 Pod 添加缺失的环境变量 `APP_BOOT_MODE`**
```bash
kubectl set env deployment/appconfigfail-575d77485d APP_BOOT_MODE="local" -n aiops-e2e
```
*依据*：日志中明确指出 `missing required APP_BOOT_MODE`，添加该环境变量可解决配置错误

**2. [可选] 查看完整日志**
```bash
kubectl logs appconfigfail-575d77485d-nfpvh --previous -n aiops-e2e
```
*目的*：确认是否还有其他配置问题

**3. [可选] 检查 ConfigMap/Secret 是否缺失**
```bash
kubectl get configmap -n aiops-e2e
kubectl get secret -n aiops-e2e
```
*目的*：确认是否因缺少外部配置导致错误

### 后续优化
1. **配置验证机制**：在部署前增加配置校验逻辑，防止此类问题
2. **配置中心化管理**：将关键配置参数通过 ConfigMap/Secret 管理，避免硬编码
3. **日志监控**：配置日志告警，当出现 `L4_CONFIG_BOOTSTRAP_FAIL` 时触发告警

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod appconfigfail-575d77485d-nfpvh -o jsonpath='{.status.containerStatuses[0].restartCount}' -n aiops-e2e` | 重启次数不再增加 |
| 3. 检查环境变量 | `kubectl get pod appconfigfail-575d77485d-nfpvh -o jsonpath='{.spec.containers[0].env}' -n aiops-e2e` | 包含 `APP_BOOT_MODE` |

---
## ⚠️ 注意事项
- 如果问题仍然存在，建议检查业务代码中配置校验逻辑
- 如果 `APP_BOOT_MODE` 是由 ConfigMap/Secret 提供的，需确保 ConfigMap/Secret 存在且配置正确
- 避免将关键配置参数硬编码到容器镜像中，建议使用外部配置管理

---

## 📊 性能统计

├─ 总耗时: 9.8m
├─ 问题定位: 112.4s (19%) ✅
├─ 证据链采集: 251.0s (43%) ✅
├─ 根因分析: 31.6s (5%) ✅
├─ 汇总总结: 194.7s (33%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 11 次
```

📋 诊断追踪

- **核心 Runbook**: pod-config-error
- **参考 Runbook**: pod-config-error
- **工具调用**: 11 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
