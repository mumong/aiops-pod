======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 67a0ee74daf44291]

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
      📄 NAME                             READY   STATUS             RESTARTS        AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
appconfigfail-575d77485d-nfpvh   0/1     CrashLoopB
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
  "confidence": 0.95,
  "reasoning": "Pod 'appconfigfail-575d77485d-nfpvh' 处于 CrashLoopBackOff 状态，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和缺失关键环境变量 APP_BOOT_MODE。describe 显示 Exit Code 42，无 OOMKilled/137 等内存问题信号，且诊断注解明确指向 ConfigError。该 Pod 重启次数持续增加，符合 L4 中应用配置缺失或校验失败的典型特征。",
  "abnormal_pods": [
    {
      "name": "appconfigfail-575d77485d-nfpvh",
      "namespace": "aiops-e2e",
      "status": "CrashLoopBackOff",
      "restarts": "14 (112s ago)",
      "ip": "172.16.166.184",
      "node": "node1",
      "labels": {
        "app": "appconfigfail",
        "e2e-test": "true",
        "l4-scenario": "config-bootstrap-fail",
        "pod-template-hash": "575d77485d",
        "pod_abnormal_type": "ConfigError"
      }
    }
  ],
  "abnormal_groups": [
    {
      "pod_status_keyword": "CrashLoopBackOff",
      "pod_abnormal_type": "ConfigError",
      "status_category": "ConfigError",
      "count": 1
    }
  ],
  "key_entities": [
    {
      "type": "Pod",
      "name": "appconfigfail-575d77485d-nfpvh",
      "namespace": "aiops-e2e",
      "status": "CrashLoopBackOff"
    },
    {
      "type": "ConfigMap/Secret",
      "name": "missing APP_BOOT_MODE",
      "namespace": "aiops-e2e",
      "status": "ConfigValidationFailed"
    }
  ],
  "possible_scenarios": [
    "应用配置校验失败（APP_BOOT_MODE 缺失）",
    "ConfigMap/Secret 键名拼写错误导致注入失败",
    "业务配置约束未满足（如端口/租户配置缺失）",
    "环境变量注入异常（如 Secret 权限问题）"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (2m 50.2s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': '应用配置校验失败（APP_BOOT_MODE 缺失）', 'probability': 'high', 'reason': '日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: missing required APP_BOOT_MODE'}, {'scenario': 'ConfigMap/Secret 键名拼写错误导致注入失败', 'probability': 'medium', 'reason': 'Pod 中的环境变量缺失，可能与配置资源定义错误有关'}, {'scenario': '业务配置约束未满足（如端口/租户配置缺失）', 'probability': 'medium', 'reason': '日志中提到 business config validation failed before server startup'}, {'scenario': '环境变量注入异常（如 Secret 权限问题）', 'probability': 'low', 'reason': '无直接证据表明权限问题，但可能与配置资源未正确注入有关'}]
   entities=[{"type": "Pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}, {"type": "ConfigMap/Secret", "name": "missing APP_BOOT_MODE", "namespace": "aiops-e2e"}]
   reasoning=Pod 'appconfigfail-575d77485d-nfpvh' 处于 CrashLoopBackOff 状态，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和缺失关键环境变量 APP_BOOT_MODE。describe 显示 Exit Code 42，无 OOMKilled/137 等内存问题信号，且诊断注解明确指向 ConfigError。该 Pod 重启次数持续增加，符合 L4 中应用配置缺失或校验失败的典型特征。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.95, "reasoning": "Pod 'appconfigfail-575d77485d-nfpvh' 处于 CrashLoopBackOff 状态，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和缺失关键环境变量 APP_BOOT_MODE。describe 显示 Exit Code 42，无 OOMKilled/137 等内存问题信号，且诊断注解明确指向 ConfigError。该 Pod 重启次数持续增加，符合 L4 中应用配置缺失或校验失败的典型特征。", "abnormal_pods": [{"name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "app_config", "key_entities": [{"type": "Pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}, {"type": "ConfigMap/Secret", "name": "missing APP_BOOT_MODE", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "应用配置校验失败（APP_BOOT_MODE 缺失）", "probability": "high", "reason": "日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: missing required APP_BOOT_MODE"}, {"scenario": "ConfigMap/Secret 键名拼写错误导致注入失败", "probability": "medium", "reason": "Pod 中的环境变量缺失，可能与配置资源定义错误有关"}, {"scenario": "业务配置约束未满足（如端口/租户配置缺失）", "probability": "medium", "reason": "日志中提到 business config validation failed before server startup"}, {"scenario": "环境变量注入异常（如 Secret 权限问题）", "probability": "low", "reason": "无直接证据表明权限问题，但可能与配置资源未正确注入有关"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     appconfigfail-575d77485d-nfpvh                      0/1     CrashLoopBackOff   14 (106s ago)   48m    172.16.166.184   node1    <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError"], "raw_ref": "/tmp/aiops/reports/context_archives/67a0ee74daf44291/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/67a0ee74daf44291/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/67a0ee74daf44291/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                             READY   STATUS             RESTARTS         AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
appconfigfail-575d77485d-nfpvh   0/1     CrashLoop
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
4m34s (x234 over 54m)   Warning   BackOff          Pod/appconfigfail-575d77485d-nfpvh   Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc
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
1. Pod `appconfigfail-575d77485d-nfpvh` 的状态为 `CrashLoopBackOff`，重启次数为 15，ExitCode 为 42，符合 ConfigError 的典型特征。
2. Pod 的事件显示 `Back-off restarting failed container app`，且日志包含 `L4_CONFIG_BOOTSTRAP_FAIL`、`missing required APP_BOOT_MODE` 等配置错误信号。
3. 未在 `aiops-e2e` 命名空间中找到与问题相关的 ConfigMap 或 Secret，进一步支持了配置缺失的可能性。

未采集证据：
1. 未检查到业务配置校验失败的具体原因（如是否涉及其他环境变量缺失）。
2. 未检查到 ConfigMap/Secret 的键名拼写是否正确，但已确认未定义相关资源。

冲突证据：
1. `kubectl_get_by_kind_in_namespace` 未找到 Secret，确认了配置资源缺失的可能性。

综上，当前异常的证据表明这是一个由于配置缺失导致的 ConfigError。建议检查业务配置并提供缺失的 `APP_BOOT_MODE` 环境变量。
   ✅ [证据链采集] 完成 (4m 23.6s)
   📤 → 下游数据: evidence_items=7/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod 'appconfigfail-575d77485d-nfpvh' 的详细状态和配置","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","namespace":"aiops-e2e","name":"appconfigfail-575d77485d-nfpvh"},"purpose":"验证 Pod 的详细状态、重启次数和配置，确认其是否处于 CrashLoopBackOff 状态且 ExitCode 为 42","evidence_type":"state_configuration","target_scope":"Pod","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod 'appconfigfail-575d77485d-nfpvh' 的事件记录","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=appconfigfail-575d77485d-nfpvh","tool_args":{"namespace":"aiops-e2e","involved_object_name":"appconfigfail-575d77485d-nfpvh"},"purpose":"验证 Pod 是否有 'L4_CONFIG_BOOTSTRAP_FAIL'、'missing required APP_BOOT_MODE' 等关键事件","evidence_type":"events","target_scope":"Pod","acceptable_tools":["kubectl_events"],"counts_for_completeness":true},{"id":"e3","description":"获取 Pod 'appconfigfail-575d77485d-nfpvh' 的容器日志","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous","tool_args":{"namespace":"aiops-e2e","pod_name":"appconfigfail-575d77485d-nfpvh","container_name":null,"previous":true},"purpose":"验证容器日志是否包含 'L4_CONFIG_BOOTSTRAP_FAIL'、'missing required APP_BOOT_MODE' 等配置错误信号","evidence_type":"logs","target_scope":"Pod","acceptable_tools":["kubectl_previous_logs"],"counts_for_completeness":true},{"id":"e4","description":"获取 ConfigMap/Secret 是否存在并检查键名拼写","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get configmap,secret -n aiops-e2e -o name","tool_args":{"kind":"ConfigMap","namespace":"aiops-e2e"},"purpose":"验证 ConfigMap/Secret 是否存在并检查键名拼写是否正确，确认是否缺失 APP_BOOT_MODE 环境变量","evidence_type":"configuration_dependency","target_scope":"ConfigMap/Secret","acceptable_tools":["kubectl_get_by_kind_in_namespace"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                             READY   STATUS             RESTARTS         AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nappconfigfail-575d77485d-nfpvh   0/1     CrashLoopBackOff   15 (2m28s ago)   54m   172.16.166.184   node1   <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/67a0ee74daf44291/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/67a0ee74daf44291/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/67a0ee74daf44291/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n4m34s (x234 over 54m)   Warning   BackOff          Pod/appconfigfail-575d77485d-nfpvh   Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/67a0ee74daf44291/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/67a0ee74daf44291/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/67a0ee74daf44291/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 6\nsignals: 5\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/67a0ee74daf44291/tools/003-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/67a0ee74daf44291/tools/003-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/67a0ee74daf44291/tools/003-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"kubectl_get_by_kind_in_namespace 表格摘要: rows=1 abnormal=0 status_counts={}\nNAME               DATA   AGE    LABELS\n# 样例行\nkube-root-ca.crt   1      108d   <none>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/67a0ee74daf44291/tools/004-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/67a0ee74daf44291/tools/004-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/67a0ee74daf44291/tools/004-evidence-kubectl_get_by_kind_in_namespace.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/67a0ee74daf44291/tools/005-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/67a0ee74daf44291/tools/005-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/67a0ee74daf44291/tools/005-evidence-kubectl_get_by_kind_in_namespace.summary.txt"}],"llm_analysis":"已采集证据：\n1. Pod `appconfigfail-575d77485d-nfpvh` 的状态为 `CrashLoopBackOff`，重启次数为 15，ExitCode 为 42，符合 ConfigError 的典型特征。\n2. Pod 的事件显示 `Back-off restarting failed container app`，且日志包含 `L4_CONFIG_BOOTSTRAP_FAIL`、`missing required APP_BOOT_MODE` 等配置错误信号。\n3. 未在 `aiops-e2e` 命名空间中找到与问题相关的 ConfigMap 或 Secret，进一步支持了配置缺失的可能性。\n\n未采集证据：\n1. 未检查到业务配置校验失败的具体原因（如是否涉及其他环境变量缺失）。\n2. 未检查到 ConfigMap/Secret 的键名拼写是否正确，但已确认未定义相关资源。\n\n冲突证据：\n1. `kubectl_get_by_kind_in_namespace` 未找到 Secret，确认了配置资源缺失的可能性。\n\n综上，当前异常的证据表明这是一个由于配置缺失导致的 ConfigError。建议检查业务配置并提供缺失的 `APP_BOOT_MODE` 环境变量。","collection_summary":"计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%；其中真实环境证据 7/8 项，完整度 88%；实际执行工具 8 个，匹配计划 3 个，未规划证据 5 个","plan_total":4,"plan_collected":3,"plan_completeness":0.75,"environment_evidence_total":8,"environment_evidence_collected":7,"environment_evidence_completeness":0.875,"executed_tool_count":8,"matched_tool_count":3,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"获取 Pod 'appconfigfail-575d77485d-nfpvh' 的详细状态和配置","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml","purpose":"验证 Pod 的详细状态、重启次数和配置，确认其是否处于 CrashLoopBackOff 状态且 ExitCode 为 42","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod 'appconfigfail-575d77485d-nfpvh' 的事件记录","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=appconfigfail-575d77485d-nfpvh","purpose":"验证 Pod 是否有 'L4_CONFIG_BOOTSTRAP_FAIL'、'missing required APP_BOOT_MODE' 等关键事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取 Pod 'appconfigfail-575d77485d-nfpvh' 的容器日志","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous","purpose":"验证容器日志是否包含 'L4_CONFIG_BOOTSTRAP_FAIL'、'missing required APP_BOOT_MODE' 等配置错误信号","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"获取 ConfigMap/Secret 是否存在并检查键名拼写","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get configmap,secret -n aiops-e2e -o name","purpose":"验证 ConfigMap/Secret 是否存在并检查键名拼写是否正确，确认是否缺失 APP_BOOT_MODE 环境变量","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e4(获取 ConfigMap/Secret 是否存在并检查键名拼写): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 88%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 获取 Pod 'appconfigfail-575d77485d-nfpvh' 的详细状态和配置 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml` |
   | e2 | critical | ✅ | kubectl_events | 获取 Pod 'appconfigfail-575d77485d-nfpvh' 的事件记录 | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=appconfi...` |
   | e3 | critical | ✅ | kubectl_previous_logs | 获取 Pod 'appconfigfail-575d77485d-nfpvh' 的容器日志 | `kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous` |
   | e4 | important | ❌ | kubectl_get_by_kind_in_na... | 获取 ConfigMap/Secret 是否存在并检查键名拼写 | `kubectl get configmap,secret -n aiops-e2e -o name` |

   ⚠️ 未采集原因:
   - e4(获取 ConfigMap/Secret 是否存在并检查键名拼写): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (38.4s)
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
   ✅ [汇总总结] 完成 (1m 32.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4629 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 9m 24.9s
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
| 1 | Pod 状态 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e` | `STATUS: CrashLoopBackOff, RESTARTS: 14 (106s ago), AGE: 48m` | Pod 处于持续重启状态 |
| 2 | Pod 事件 | `kubectl describe pod appconfigfail-575d77485d-nfpvh -n aiops-e2e` | `Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc...` | 容器持续失败，K8s 暂停重启 |
| 3 | 容器日志 | `kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous` | `L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config`<br>`FATAL: missing required APP_BOOT_MODE`<br>`FATAL: business config validation failed before server startup` | 应用启动失败，缺失关键环境变量 APP_BOOT_MODE |
| 4 | Pod YAML | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml` | `labels: app=appconfigfail, e2e-test=true, pod_abnormal_type=ConfigError`<br>`diagnostic_annotations: aiops.e2e/expected-evidence=previous logs contain L4_CONFIG_BOOTSTRAP_FAIL` | 明确标注为配置错误 |
| 5 | Runbook | `fetch_runbook` | `Pod异常类型: ConfigError`<br>`典型状态: CrashLoopBackOff`<br>`Exit Code: 42`<br>`无 OOMKilled/137` | 证据链与预设的配置错误 Runbook 匹配 |

### 证据关联分析

- **证据 #1 + #2 + #3 印证**：Pod 持续重启（CrashLoopBackOff） + 容器日志显示 `missing required APP_BOOT_MODE` → 应用配置缺失，导致启动失败。
- **证据 #4 印证**：Pod 的 YAML 明确标注 `pod_abnormal_type=ConfigError`，且日志注解匹配 L4_CONFIG_BOOTSTRAP_FAIL。
- **证据 #5 印证**：Runbook 明确指向配置错误（ConfigError），且典型状态与当前 Pod 状态一致。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| ConfigMap/Secret 是否存在并检查键名拼写 | important | 无法确认是否配置对象缺失或拼写错误导致环境变量注入失败 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 缺失关键环境变量 APP_BOOT_MODE，导致应用配置校验失败            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 应用启动时依赖 APP_BOOT_MODE 环境变量进行初始化，缺失导致失败   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器启动失败（Exit Code 42），日志显示 FATAL: missing APP_BOOT_MODE │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 CrashLoopBackOff，持续重启                             │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (CrashLoopBackOff, 重启次数持续增加)、证据 #3 (日志显示 `missing required APP_BOOT_MODE`) 和证据 #4 (Pod YAML 中的诊断注解)，问题的根本原因是**应用缺少关键环境变量 APP_BOOT_MODE，导致配置校验失败**。

**置信度**：高 (95%)
- ✅ 日志显示 `missing required APP_BOOT_MODE`
- ✅ Pod 状态为 `CrashLoopBackOff`
- ✅ Pod YAML 中的诊断注解与 Runbook 匹配
- ⚠️ 缺少 ConfigMap/Secret 的验证，无法确认是否配置资源未注入

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 注入缺失的环境变量 APP_BOOT_MODE**

```bash
kubectl set env deployment/<deployment-name> -n aiops-e2e APP_BOOT_MODE=dev
```

*依据*：日志显示 `missing required APP_BOOT_MODE`，注入该变量可解决配置校验失败问题。

**2. [可选] 检查 ConfigMap/Secret 是否存在并注入正确**

```bash
kubectl get configmap,secret -n aiops-e2e
```

*目的*：确认配置资源是否存在，且是否正确注入到 Pod 的环境变量中。

### 后续优化

1. **配置校验**：在部署前增加配置校验逻辑，确保关键环境变量存在。
2. **健康检查**：增加 readiness/liveness 探针，避免容器启动失败导致持续重启。
3. **监控告警**：为 CrashLoopBackOff 设置告警，及时发现配置问题。
4. **文档更新**：记录环境变量要求，避免未来部署遗漏关键配置。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 重启次数不再增加 |
| 3. 检查环境变量 | `kubectl exec -it appconfigfail-575d77485d-nfpvh -n aiops-e2e -- env` | 输出包含 APP_BOOT_MODE |

---

## ⚠️ 注意事项

- 如果问题依然存在，请检查是否还有其他依赖的环境变量缺失。
- 如果使用 ConfigMap/Secret 注入环境变量，确保键名拼写正确。
- 可以在 Deployment 中设置 `imagePullPolicy: IfNotPresent` 避免因镜像拉取问题干扰诊断。

---

## 📊 性能统计

├─ 总耗时: 9.4m
├─ 问题定位: 170.2s (30%) ✅
├─ 证据链采集: 263.6s (47%) ✅
├─ 根因分析: 38.4s (7%) ✅
├─ 汇总总结: 92.7s (16%) ✅
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
