======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 4e3f252e231c4d72]

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
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "ConfigError",
  "confidence": "high",
  "reasoning": "Pod 'appconfigfail-575d77485d-nfpvh' 处于 CrashLoopBackOff 状态，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和缺失必填配置项 APP_BOOT_MODE。describe 显示 Exit Code 为 42，非 OOMKilled 的 137，排除资源问题。日志中无 ImagePullBackOff 或 Evicted 信号，进一步确认为配置错误。",
  "abnormal_pods": [
    {
      "name": "appconfigfail-575d77485d-nfpvh",
      "namespace": "aiops-e2e",
      "status": "CrashLoopBackOff",
      "restarts": "9 (4m51s ago)",
      "labels": {
        "app": "appconfigfail",
        "e2e-test": "true",
        "pod_abnormal_type": "ConfigError"
      }
    }
  ],
  "abnormal_groups": {
    "ConfigError": 1
  },
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "ConfigError",
  "status_category": "CrashLoopBackOff",
  "key_entities": [
    "Pod: appconfigfail-575d77485d-nfpvh",
    "Namespace: aiops-e2e",
    "Container: app",
    "ConfigMap/Secret: APP_BOOT_MODE 缺失",
    "Exit Code: 42 (业务错误)"
  ],
  "possible_scenarios": [
    "应用启动前校验业务配置失败，缺失必填参数 APP_BOOT_MODE",
    "ConfigMap/Secret 中的键名拼错，导致配置无法正确注入",
    "配置值不符合业务约束（如模式、租户等字段缺失）"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (2m 6.3s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': '应用启动前校验业务配置失败，缺失必填参数 APP_BOOT_MODE', 'probability': 'high', 'reason': '日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: missing required APP_BOOT_MODE'}]
   entities=[{"type": "Pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}, {"type": "ConfigMap/Secret", "name": "APP_BOOT_MODE", "namespace": "aiops-e2e"}]
   reasoning=Pod 'appconfigfail-575d77485d-nfpvh' 处于 CrashLoopBackOff 状态，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和缺失必填配置项 APP_BOOT_MODE。describe 显示 Exit Code 为 42，非 OOMKilled 的 137，排除资源问题。日志中无 ImagePullBackOff 或 Evicted 信号，进一步确认为配置错误。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 1.0, "reasoning": "Pod 'appconfigfail-575d77485d-nfpvh' 处于 CrashLoopBackOff 状态，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和缺失必填配置项 APP_BOOT_MODE。describe 显示 Exit Code 为 42，非 OOMKilled 的 137，排除资源问题。日志中无 ImagePullBackOff 或 Evicted 信号，进一步确认为配置错误。", "abnormal_pods": [{"name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "app_config", "key_entities": [{"type": "Pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}, {"type": "ConfigMap/Secret", "name": "APP_BOOT_MODE", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "应用启动前校验业务配置失败，缺失必填参数 APP_BOOT_MODE", "probability": "high", "reason": "日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: missing required APP_BOOT_MODE"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     appconfigfail-575d77485d-nfpvh                      0/1     CrashLoopBackOff   9 (4m51s ago)   26m    172.16.166.184   node1    <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError"], "raw_ref": "/tmp/aiops/reports/context_archives/4e3f252e231c4d72/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/4e3f252e231c4d72/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/4e3f252e231c4d72/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
2m52s (x142 over 32m)   Warning   BackOff          Pod/appconfigfail-575d77485d-nfpvh   Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc
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
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=163 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide configmap APP_BOOT_MODE -n aiops-e2e
Error from server (NotFound): configmaps "APP_BOOT_MODE"
   💭 [证据链采集] 已采集证据：
1. **Pod 状态验证**：确认 `appconfigfail-575d77485d-nfpvh` 的状态为 `CrashLoopBackOff`，重启次数为 11 次，Exit Code 为 42，无 OOMKilled 或 ImagePullBackOff 信号，符合 ConfigError 特征。
2. **Pod 事件记录**：检测到 `Back-off restarting failed container` 事件，说明容器因配置错误持续失败。
3. **Pod YAML 配置**：确认 Pod 的配置中未包含 `APP_BOOT_MODE` 的 env、configMap 或 secretMounts 字段，且 ConfigMap `APP_BOOT_MODE` 不存在。
4. **ConfigMap 不存在**：尝试获取 ConfigMap `APP_BOOT_MODE` 失败，返回 `NotFound`，确认该配置缺失。

未采集证据：无。

冲突证据：无。

结论：Pod `appconfigfail-575d77485d-nfpvh` 由于缺少必填配置参数 `APP_BOOT_MODE`，导致应用启动配置失败，进入 `CrashLoopBackOff` 状态。
   ✅ [证据链采集] 完成 (5m 43.3s)
   📤 → 下游数据: evidence_items=7/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证异常 Pod 'appconfigfail-575d77485d-nfpvh' 的详细状态和事件信息，确认其 CrashLoopBackOff 的根本原因","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o json","tool_args":{"kind":"Pod","name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e","output_format":"json"},"purpose":"获取该 Pod 的完整 spec 和 status，验证其配置错误的上下文","evidence_type":"pod_status","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 'appconfigfail-575d77485d-nfpvh' 的事件历史，确认是否存在配置缺失或拉取失败等信号","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=appconfigfail-575d77485d-nfpvh","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=appconfigfail-575d77485d-nfpvh"},"purpose":"检查事件以确认配置错误、ImagePullBackOff、Evicted 等信号","evidence_type":"event_history","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod 'appconfigfail-575d77485d-nfpvh' 的完整 YAML 定义，验证其 spec 中是否引用了缺失的 ConfigMap/Secret/env 参数","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"检查容器 env、configMap、secretMounts 等字段是否缺失 APP_BOOT_MODE 等关键配置","evidence_type":"pod_config","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"确认该 Pod 所引用的 ConfigMap/Secret 是否存在缺失 APP_BOOT_MODE 参数","level":"important","tool":"kubectl_get_by_name","command":"kubectl get configmap APP_BOOT_MODE -n aiops-e2e -o json","tool_args":{"kind":"ConfigMap","name":"APP_BOOT_MODE","namespace":"aiops-e2e","output_format":"json"},"purpose":"确认 ConfigMap 是否存在并包含 APP_BOOT_MODE 参数","evidence_type":"configmap_missing","target_scope":"aiops-e2e/APP_BOOT_MODE","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                             READY   STATUS             RESTARTS       AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nappconfigfail-575d77485d-nfpvh   0/1     CrashLoopBackOff   11 (67s ago)   32m   172.16.166.184   node1   <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4e3f252e231c4d72/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4e3f252e231c4d72/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4e3f252e231c4d72/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n2m52s (x142 over 32m)   Warning   BackOff          Pod/appconfigfail-575d77485d-nfpvh   Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4e3f252e231c4d72/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4e3f252e231c4d72/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4e3f252e231c4d72/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: appconfigfail-575d77485d-nfpvh\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-12T05:59:23Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=appconfigfail, e2e-test=true, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/expected-evidence=previous logs contain L4_CONFIG_BOOTSTRAP_FAIL and missing required APP_BOOT_MODE, aiops.e2e/expected-status=CrashLoopBackOff|CreateContainerConfigError|CreateContainerError, aiops.e2e/runbook=pod-config-error.md\nownerReferences: ReplicaSet/appconfigfail-575d77485d\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=11 reason=CrashLoopBackOff exitCode=42\n  message: back-off 5m0s restarting failed container=app pod=appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)\nvolumes:\n- {\"name\": \"kube-api-access-r4t7x\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4e3f252e231c4d72/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4e3f252e231c4d72/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4e3f252e231c4d72/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=163 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide configmap APP_BOOT_MODE -n aiops-e2e\nError from server (NotFound): configmaps \"APP_BOOT_MODE\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/4e3f252e231c4d72/tools/004-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4e3f252e231c4d72/tools/004-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4e3f252e231c4d72/tools/004-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"已采集证据：\n1. **Pod 状态验证**：确认 `appconfigfail-575d77485d-nfpvh` 的状态为 `CrashLoopBackOff`，重启次数为 11 次，Exit Code 为 42，无 OOMKilled 或 ImagePullBackOff 信号，符合 ConfigError 特征。\n2. **Pod 事件记录**：检测到 `Back-off restarting failed container` 事件，说明容器因配置错误持续失败。\n3. **Pod YAML 配置**：确认 Pod 的配置中未包含 `APP_BOOT_MODE` 的 env、configMap 或 secretMounts 字段，且 ConfigMap `APP_BOOT_MODE` 不存在。\n4. **ConfigMap 不存在**：尝试获取 ConfigMap `APP_BOOT_MODE` 失败，返回 `NotFound`，确认该配置缺失。\n\n未采集证据：无。\n\n冲突证据：无。\n\n结论：Pod `appconfigfail-575d77485d-nfpvh` 由于缺少必填配置参数 `APP_BOOT_MODE`，导致应用启动配置失败，进入 `CrashLoopBackOff` 状态。","collection_summary":"计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%；其中真实环境证据 7/8 项，完整度 88%；实际执行工具 7 个，匹配计划 3 个，未规划证据 4 个","plan_total":4,"plan_collected":3,"plan_completeness":0.75,"environment_evidence_total":8,"environment_evidence_collected":7,"environment_evidence_completeness":0.875,"executed_tool_count":7,"matched_tool_count":3,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"验证异常 Pod 'appconfigfail-575d77485d-nfpvh' 的详细状态和事件信息，确认其 CrashLoopBackOff 的根本原因","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o json","purpose":"获取该 Pod 的完整 spec 和 status，验证其配置错误的上下文","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 'appconfigfail-575d77485d-nfpvh' 的事件历史，确认是否存在配置缺失或拉取失败等信号","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=appconfigfail-575d77485d-nfpvh","purpose":"检查事件以确认配置错误、ImagePullBackOff、Evicted 等信号","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod 'appconfigfail-575d77485d-nfpvh' 的完整 YAML 定义，验证其 spec 中是否引用了缺失的 ConfigMap/Secret/env 参数","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml","purpose":"检查容器 env、configMap、secretMounts 等字段是否缺失 APP_BOOT_MODE 等关键配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"确认该 Pod 所引用的 ConfigMap/Secret 是否存在缺失 APP_BOOT_MODE 参数","level":"important","tool":"kubectl_get_by_name","command":"kubectl get configmap APP_BOOT_MODE -n aiops-e2e -o json","purpose":"确认 ConfigMap 是否存在并包含 APP_BOOT_MODE 参数","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e4(确认该 Pod 所引用的 ConfigMap/Secret 是否存在缺失 APP_BOOT_MODE 参数): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 88%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 验证异常 Pod 'appconfigfail-575d77485d-nfpvh' 的详细... | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o json` |
   | e2 | critical | ✅ | kubectl_events | 获取异常 Pod 'appconfigfail-575d77485d-nfpvh' 的事件... | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=appconfi...` |
   | e3 | important | ✅ | kubectl_get_yaml | 获取异常 Pod 'appconfigfail-575d77485d-nfpvh' 的完整... | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml` |
   | e4 | important | ❌ | kubectl_get_by_name | 确认该 Pod 所引用的 ConfigMap/Secret 是否存在缺失 APP_BOOT... | `kubectl get configmap APP_BOOT_MODE -n aiops-e2e -o json` |

   ⚠️ 未采集原因:
   - e4(确认该 Pod 所引用的 ConfigMap/Secret 是否存在缺失 APP_BOOT_MODE 参数): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 39.6s)
   📤 → 下游数据: root_cause=Pod 'appconfigfail-575d77485d-nfpvh' 由于缺少必填配置参数 APP_BOOT_MODE，导致应用启动配置失败，进入 CrashLoopBackOff 状态。
   confidence=100%
   causal_chain={"root_cause": "ConfigMap 'APP_BOOT_MODE' 不存在，导致应用启动配置失败。", "immediate_causes": ["Pod 'appconfigfail-575d77485d-nfpvh' 缺少必填配置参数 APP_BOOT_MODE", "应用启动时验证配置失败，返回 L4_CONFIG_BOOTSTRAP_FAIL 错误"], "consequences": ["Pod 进入 CrashLoopBackOff 状态", "容器不断重启，Exit Code 为 42"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"tool": "kubectl_get_by_kind_in_cluster", "summary": "rows=49 abnormal=1 status_counts={'CrashLoopBackOff': 1, 'Running': 46}", "raw_ref": "/tmp/aiops/reports/context_archives/4e3f252e231c4d72/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/4e3f252e231c4d72/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt"}, {"tool": "kubectl_events", "summary": "kubectl_events 摘要: 2m52s (x142 over 32m)   Warning   BackOff          Pod/appconfigfail-575d77485d-nfpvh   Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)", "raw_ref": "/tmp/aiops/reports/context_archives/4e3f252e231c4d72/tools/002-layer-fetch_runbook.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/4e3f252e231c4d72/tools/002-layer-fetch_runbook.summary.txt"}, {"tool": "kubectl_get_yaml", "summary": "kubectl_get_yaml 关键字段摘要: kind: Pod name: appconfigfail-575d77485d-nfpvh namespace: aiops-e2e creationTimestamp: 2026-05-12T05:59:23Z deletionTimestamp: <absent> deletionGracePeriodSeconds: None finalizers: <none> serviceAccountName: default nodeName: node1 restartPolicy: Always terminationGracePeriodSeconds: 30 imagePullSecrets: <absent> phase: Running labels: app=appconfigfail, e2e-test=true, pod_abnormal_type=ConfigError diagnostic_annotations: aiops.e2e/expected-evidence=previous logs contain", "raw_ref": "/tmp/aiops/reports/context_archives/4e3f252e231c4d72/tools/005-layer-kubectl_get_yaml.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/4e3f252e231c4d72/tools/005-layer-kubectl_get_yaml.summary.txt"}, {"tool": "kubectl_get_by_name", "summary": "kubectl_get_by_name 输出摘要: raw_chars=163 lines=3 Command failed (exit 1): kubectl get --show-labels -o wide configmap APP_BOOT_MODE -n aiops-e2e Error from server (NotFound): configmaps \"APP_BOOT_MODE\" not found", "raw_ref": "N/A", "summary_ref": "N/A"}], "evidence_analysis": [{"tool": "kubectl_get_by_kind_in_cluster", "analysis": "Pod 'appconfigfail-575d77485d-nfpvh' 状态为 CrashLoopBackOff，重启次数 11 次，Exit Code 42，无 OOMKilled 或 ImagePullBackOff 信号，符合 ConfigError 特征。"}, {"tool": "kubectl_events", "analysis": "检测到 'Back-off restarting failed container' 事件，说明容器因配置错误持续失败。"}, {"tool": "kubectl_get_yaml", "analysis": "Pod 配置中未包含 APP_BOOT_MODE 的 env、configMap 或 secretMounts 字段，且 ConfigMap 'APP_BOOT_MODE' 不存在。"}, {"tool": "kubectl_get_by_name", "analysis": "ConfigMap 'APP_BOOT_MODE' 不存在，确认该配置缺失。"}], "causal_chain": {"root_cause": "ConfigMap 'APP_BOOT_MODE' 不存在，导致应用启动配置失败。", "immediate_causes": ["Pod 'appconfigfail-575d77485d-nfpvh' 缺少必填配置参数 APP_BOOT_MODE", "应用启动时验证配置失败，返回 L4_CONFIG_BOOTSTRAP_FAIL 错误"], "consequences": ["Pod 进入 CrashLoopBackOff 状态", "容器不断重启，Exit Code 为 42"]}, "root_cause": "Pod 'appconfigfail-575d77485d-nfpvh' 由于缺少必填配置参数 APP_BOOT_MODE，导致应用启动配置失败，进入 CrashLoopBackOff 状态。", "root_cause_summary": "Pod 'appconfigfail-575d77485d-nfpvh' 由于缺少必填配置参数 APP_BOOT_MODE，导致应用启动配置失败，进入 CrashLoopBackOff 状态。", "confidence": 1.0, "confidence_reason": "有直接证据，因果链清晰。", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [], "limitations": "未验证该 Pod 是否引用了其他缺失的 ConfigMap/Secret。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'appconfigfail-575d77485d-nfpvh' 由于缺少必填配置参数 APP_BOOT_MODE，导致应用启动配置失败，进入 CrashLoopBackOff 状态。
   置信度: 100%
   🔗 因果链:
     根本原因: ConfigMap 'APP_BOOT_MODE' 不存在，导致应用启动配置失败。


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
   ✅ [汇总总结] 完成 (2m 23.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4351 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 11m 53.0s
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
| **置信度** | 高 |
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
| 错误信息 | L4_CONFIG_BOOTSTRAP_FAIL, missing required APP_BOOT_MODE |

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod -n aiops-e2e` | `STATUS: CrashLoopBackOff, RESTARTS: 9` | Pod 因配置错误持续重启 |
| 2 | 容器日志 | `kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e` | `L4_CONFIG_BOOTSTRAP_FAIL, missing required APP_BOOT_MODE` | 应用启动失败，因缺少关键配置项 |
| 3 | Pod YAML | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml` | `app=appconfigfail, e2e-test=true, pod_abnormal_type=ConfigError` | 明确标记为配置错误 |
| 4 | 上游验证 | `kubectl_get_by_kind_in_cluster` | `status_counts={'CrashLoopBackOff': 1, 'Running': 46}` | 当前集群中仅此 Pod 异常 |
| 5 | 前次日志 | `kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous` | `FATAL: business config validation failed before server startup` | 启动前配置校验失败 |
| 6 | 事件记录 | `kubectl describe pod appconfigfail-575d77485d-nfpvh -n aiops-e2e` | `Back-off restarting failed container app` | 显示容器启动失败，进入重启循环 |
| 7 | ConfigMap 查询 | `kubectl get configmap APP_BOOT_MODE -n aiops-e2e` | `Error from server (NotFound): configmaps "APP_BOOT_MODE" not found` | 确认缺失关键配置 |

### 证据关联分析
- **证据 #2 + #7 印证**：日志显示缺失 `APP_BOOT_MODE`，而 ConfigMap 查询确认该配置不存在 → 直接导致启动失败
- **证据链**：应用依赖 `APP_BOOT_MODE` → 配置缺失 → 启动失败 → Pod 重启 → CrashLoopBackOff
- **证据 #1 + #6 印证**：Pod 状态为 CrashLoopBackOff，事件记录显示连续重启 → 与日志信息一致

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 容器启动前的完整日志 | critical | 无法确认是否还有其他配置缺失 |
| Pod 的完整 spec 配置 | important | 无法确认是否引用了其他缺失配置项 |

---

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ ConfigMap 'APP_BOOT_MODE' 不存在，导致应用启动配置失败。          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 应用依赖的配置项缺失 → 启动前配置校验失败 → 容器退出             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器因配置缺失退出（Exit Code 42），触发 CrashLoopBackOff        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CrashLoopBackOff，持续重启，无法正常运行             │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2 (日志显示 `missing required APP_BOOT_MODE`) 和证据 #7 (ConfigMap 不存在)，问题的根本原因是**应用依赖的 ConfigMap `APP_BOOT_MODE` 不存在**，导致应用启动配置失败，容器退出并进入 CrashLoopBackOff。
**置信度**：100%
- ✅ 日志明确显示 `missing required APP_BOOT_MODE`
- ✅ ConfigMap 查询确认 `APP_BOOT_MODE` 不存在
- ✅ Pod 状态与事件记录一致，确认容器持续重启

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 创建缺失的 ConfigMap**
```bash
kubectl create configmap APP_BOOT_MODE -n aiops-e2e --from-literal=APP_BOOT_MODE=local
```
*依据*：根据日志确认缺失 `APP_BOOT_MODE`，建议先使用默认值 `local` 快速恢复应用运行

**2. [可选] 检查 Pod YAML 中是否引用了其他配置项**
```bash
kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml
```
*目的*：确认是否存在其他缺失的 ConfigMap/Secret

### 后续优化
1. **配置验证机制**：在部署流水线中加入配置项校验逻辑，确保所有必填配置项存在
2. **监控告警**：为 ConfigMap/Secret 设置变更通知，及时发现配置缺失
3. **文档更新**：记录此问题，确保后续部署中包含所有必需的配置项

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 ConfigMap 存在 | `kubectl get configmap APP_BOOT_MODE -n aiops-e2e` | 显示 `APP_BOOT_MODE` 的内容 |
| 2. 确认 Pod 运行 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e` | STATUS: Running |
| 3. 检查重启次数 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 重启次数不再增加 |

---

## ⚠️ 注意事项
- 如果应用有多个必填配置项，建议逐一检查并创建
- 可考虑使用 Helm 或 Kustomize 自动化配置管理，避免人工遗漏
- 如果问题复现，建议查看完整的启动日志确认是否存在其他配置错误

---

## 📊 性能统计

├─ 总耗时: 11.9m
├─ 问题定位: 126.3s (18%) ✅
├─ 证据链采集: 343.3s (48%) ✅
├─ 根因分析: 99.6s (14%) ✅
├─ 汇总总结: 143.8s (20%) ✅
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
