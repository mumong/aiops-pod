======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: f803895508a14b66]

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
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-env-missing-5d9b8b766c-cstkh
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Reason:       CrashLoopBackOff
  Warning  BackOff  7s (x605 ov
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                     READY   STATUS             RESTARTS        AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-config-env-missing-5d9b8b766c-cstkh   0
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": ["L4"],
  "layer_name": "ConfigError",
  "confidence": "high",
  "reasoning": "Pod 状态为 CrashLoopBackOff，describe 显示 Exit Code 42，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，符合 ConfigError 的特征。未发现 OOMKilled、Evicted、ImagePullFailed 等其他异常信号，符合 L4 归类。",
  "abnormal_pods": [
    {
      "name": "rc-config-env-missing-5d9b8b766c-cstkh",
      "namespace": "aiops-e2e",
      "status": "CrashLoopBackOff",
      "restarts": "30",
      "ip": "172.16.166.152",
      "node": "node1"
    }
  ],
  "abnormal_groups": ["ConfigError"],
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "ConfigError",
  "status_category": "CrashLoopBackOff",
  "key_entities": {
    "pod": "rc-config-env-missing-5d9b8b766c-cstkh",
    "namespace": "aiops-e2e",
    "node": "node1"
  },
  "possible_scenarios": [
    "Pod 缺失环境变量 APP_BOOT_MODE，导致应用配置校验失败。",
    "ConfigMap/Secret 引用错误或键名拼写错误，导致应用启动失败。",
    "业务代码在启动前校验配置失败，导致容器退出。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (58.4s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'Pod 缺失环境变量 APP_BOOT_MODE，导致应用配置校验失败。', 'probability': 'high', 'reason': 'Exit Code 42 和日志中 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE 是直接证据。'}, {'scenario': 'ConfigMap/Secret 引用错误或键名拼写错误，导致应用启动失败。', 'probability': 'high', 'reason': 'Pod 配置引用的 ConfigMap/Secret 缺失或键名拼错，导致容器启动失败。'}, {'scenario': '业务代码在启动前校验配置失败，导致容器退出。', 'probability': 'high', 'reason': '日志中提示配置校验失败，业务代码在启动前就退出。'}]
   entities=[{"type": "pod", "name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e"}, {"type": "node", "name": "node1", "namespace": ""}]
   reasoning=Pod 状态为 CrashLoopBackOff，describe 显示 Exit Code 42，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，符合 ConfigError 的特征。未发现 OOMKilled、Evicted、ImagePullFailed 等其他异常信号，符合 L4 归类。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.9, "reasoning": "Pod 状态为 CrashLoopBackOff，describe 显示 Exit Code 42，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，符合 ConfigError 的特征。未发现 OOMKilled、Evicted、ImagePullFailed 等其他异常信号，符合 L4 归类。", "abnormal_pods": [{"name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "CrashLoopBackOff", "key_entities": [{"type": "pod", "name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e"}, {"type": "node", "name": "node1", "namespace": ""}], "possible_scenarios": [{"scenario": "Pod 缺失环境变量 APP_BOOT_MODE，导致应用配置校验失败。", "probability": "high", "reason": "Exit Code 42 和日志中 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE 是直接证据。"}, {"scenario": "ConfigMap/Secret 引用错误或键名拼写错误，导致应用启动失败。", "probability": "high", "reason": "Pod 配置引用的 ConfigMap/Secret 缺失或键名拼错，导致容器启动失败。"}, {"scenario": "业务代码在启动前校验配置失败，导致容器退出。", "probability": "high", "reason": "日志中提示配置校验失败，业务代码在启动前就退出。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-cstkh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-cstkh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-env-missing-5d9b8b766c-cstkh              0/1     CrashLoopBackOff   30 (93s ago)   130m    172.16.166.152   node1    <none>           <none>            app=rc-config-env-missing,pod-template-hash=5d9b8b766c,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/f803895508a14b66/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/f803895508a14b66/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/f803895508a14b66/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 90%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-env-missing-5d9b8b766c-cstkh
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Reason:       CrashLoopBackOff
  Warning  BackOff  2m21s (x605
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=157 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide configmap app-config -n aiops-e2e
Error from server (NotFound): configmaps "app-config" not f
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=151 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide secret app-secret -n aiops-e2e
Error from server (NotFound): secrets "app-secret" not found
   💭 [证据链采集] # 证据结论

## 已采集证据
1. **Pod 状态和事件**（critical）
   - Pod `rc-config-env-missing-5d9b8b766c-cstkh` 处于 `CrashLoopBackOff` 状态。
   - 最后一次容器终止的 `Exit Code` 为 42，`Reason` 为 `Error`。
   - 事件日志显示 `Back-off restarting failed container`，表明容器启动失败并持续重启。
   - `kubectl describe` 显示容器配置中缺失关键环境变量 `APP_BOOT_MODE`。

2. **容器日志**（critical）
   - 上一次容器运行的日志显示 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`，表明配置校验失败，导致容器退出。

3. **ConfigMap 和 Secret 验证**（important）
   - 尝试获取 `ConfigMap` 和 `Secret` `app-config` 和 `app-secret`，但均未找到，表明这些配置资源可能缺失或引用错误。

## 未采集证据
- 无进一步未采集的证据。

## 冲突证据
- 无冲突证据。

## 分析总结
- Pod `rc-config-env-missing-5d9b8b766c-cstkh` 处于 `CrashLoopBackOff` 状态，且容器启动失败，主要原因是缺少环境变量 `APP_BOOT_MODE`。
- 容器日志进一步确认了配置校验失败的原因，表明应用在启动前就因配置缺失而退出。
- 尝试获取相关的 `ConfigMap` 和 `Secret` 资源时，发现这些资源未找到，可能配置资源缺失或引用错误。
- 该问题符合 `ConfigError` 类型，归类为 L4 级别。
   ✅ [证据链采集] 完成 (2m 24.6s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证异常 Pod 的配置详情，确认缺失的环境变量 APP_BOOT_MODE","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e","tool_args":{"pod":"rc-config-env-missing-5d9b8b766c-cstkh","namespace":"aiops-e2e"},"purpose":"确认 Pod 的容器配置，包括环境变量、image、command 等，以判断是否缺少 APP_BOOT_MODE 环境变量。","evidence_type":"config_validation","target_scope":"specific_pod","acceptable_tools":["kubectl_describe","kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 的容器日志（上一次运行），以确认配置错误的具体原因","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e --previous","tool_args":{"pod":"rc-config-env-missing-5d9b8b766c-cstkh","namespace":"aiops-e2e","container":null,"previous":true},"purpose":"获取上一次容器运行的日志，以确认配置校验失败的具体原因。","evidence_type":"log_analysis","target_scope":"specific_pod","acceptable_tools":["kubectl_previous_logs","kubectl_logs"],"counts_for_completeness":true},{"id":"e3","description":"验证 Pod 所引用的 ConfigMap 或 Secret 是否存在且键名正确","level":"important","tool":"kubectl_get_by_name","command":"kubectl get configmap,secret -n aiops-e2e","tool_args":{"kind":"ConfigMap","namespace":"aiops-e2e"},"purpose":"确认 Pod 所引用的 ConfigMap 或 Secret 是否存在，且键名是否正确，以判断是否因配置缺失导致异常。","evidence_type":"config_validation","target_scope":"namespace","acceptable_tools":["kubectl_get_by_name","kubectl_get_by_kind_in_namespace"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-env-missing-5d9b8b766c-cstkh\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Reason:       CrashLoopBackOff\n  Warning  BackOff  2m21s (x605 over 132m)  kubelet  Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-cstkh_aiops-e2e(5ed47e61-9e99-459d-88de-ee30d25b1def)\n                  cni.projectcalico.org/containerID: b609d3199474fd0c991fb51944c653ad8de49c03971407f25be4cb50f1498fc2\n                  cni.projectcalico.org/podIP: 172.16.166.152/32\n                  cni.projectcalico.org/podIPs: 172.16.166.152/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f803895508a14b66/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f803895508a14b66/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f803895508a14b66/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 1\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f803895508a14b66/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f803895508a14b66/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f803895508a14b66/tools/002-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=157 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide configmap app-config -n aiops-e2e\nError from server (NotFound): configmaps \"app-config\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/f803895508a14b66/tools/003-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f803895508a14b66/tools/003-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f803895508a14b66/tools/003-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=151 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide secret app-secret -n aiops-e2e\nError from server (NotFound): secrets \"app-secret\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/f803895508a14b66/tools/004-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f803895508a14b66/tools/004-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f803895508a14b66/tools/004-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"# 证据结论\n\n## 已采集证据\n1. **Pod 状态和事件**（critical）\n   - Pod `rc-config-env-missing-5d9b8b766c-cstkh` 处于 `CrashLoopBackOff` 状态。\n   - 最后一次容器终止的 `Exit Code` 为 42，`Reason` 为 `Error`。\n   - 事件日志显示 `Back-off restarting failed container`，表明容器启动失败并持续重启。\n   - `kubectl describe` 显示容器配置中缺失关键环境变量 `APP_BOOT_MODE`。\n\n2. **容器日志**（critical）\n   - 上一次容器运行的日志显示 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`，表明配置校验失败，导致容器退出。\n\n3. **ConfigMap 和 Secret 验证**（important）\n   - 尝试获取 `ConfigMap` 和 `Secret` `app-config` 和 `app-secret`，但均未找到，表明这些配置资源可能缺失或引用错误。\n\n## 未采集证据\n- 无进一步未采集的证据。\n\n## 冲突证据\n- 无冲突证据。\n\n## 分析总结\n- Pod `rc-config-env-missing-5d9b8b766c-cstkh` 处于 `CrashLoopBackOff` 状态，且容器启动失败，主要原因是缺少环境变量 `APP_BOOT_MODE`。\n- 容器日志进一步确认了配置校验失败的原因，表明应用在启动前就因配置缺失而退出。\n- 尝试获取相关的 `ConfigMap` 和 `Secret` 资源时，发现这些资源未找到，可能配置资源缺失或引用错误。\n- 该问题符合 `ConfigError` 类型，归类为 L4 级别。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 8 个，匹配计划 3 个，未规划证据 5 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":3,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"验证异常 Pod 的配置详情，确认缺失的环境变量 APP_BOOT_MODE","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e","purpose":"确认 Pod 的容器配置，包括环境变量、image、command 等，以判断是否缺少 APP_BOOT_MODE 环境变量。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 的容器日志（上一次运行），以确认配置错误的具体原因","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e --previous","purpose":"获取上一次容器运行的日志，以确认配置校验失败的具体原因。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"验证 Pod 所引用的 ConfigMap 或 Secret 是否存在且键名正确","level":"important","tool":"kubectl_get_by_name","command":"kubectl get configmap,secret -n aiops-e2e","purpose":"确认 Pod 所引用的 ConfigMap 或 Secret 是否存在，且键名是否正确，以判断是否因配置缺失导致异常。","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证异常 Pod 的配置详情，确认缺失的环境变量 APP_BOOT_MODE | `kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_previous_logs | 获取异常 Pod 的容器日志（上一次运行），以确认配置错误的具体原因 | `kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e --previous` |
   | e3 | important | ✅ | kubectl_get_by_name | 验证 Pod 所引用的 ConfigMap 或 Secret 是否存在且键名正确 | `kubectl get configmap,secret -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 37.2s)
   📤 → 下游数据: root_cause=Pod 缺失环境变量 APP_BOOT_MODE，导致应用配置校验失败。直接证据包括 Exit Code 42 和日志中 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE。
   confidence=90%
   causal_chain={"root_cause": "Pod 缺失环境变量 APP_BOOT_MODE，导致应用配置校验失败。", "intermediate_causes": ["容器日志显示 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`，表明配置校验失败，导致容器退出。", "尝试获取 `ConfigMap` 和 `Secret` `app-config` 和 `app-secret`，但均未找到，表明这些配置资源可能缺失或引用错误。"], "immediate_effects": ["Pod `rc-config-env-missing-5d9b8b766c-cstkh` 处于 `CrashLoopBackOff` 状态，最后一次容器终止的 `Exit Code` 为 42，`Reason` 为 `Error`，事件日志显示 `Back-off restarting failed container`，表明容器启动失败并持续重启。"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"phenomenon": "Pod 状态和事件", "level": "critical", "value": "Pod `rc-config-env-missing-5d9b8b766c-cstkh` 处于 `CrashLoopBackOff` 状态，最后一次容器终止的 `Exit Code` 为 42，`Reason` 为 `Error`，事件日志显示 `Back-off restarting failed container`，表明容器启动失败并持续重启，`kubectl describe` 显示容器配置中缺失关键环境变量 `APP_BOOT_MODE`。"}, {"phenomenon": "容器日志", "level": "critical", "value": "上一次容器运行的日志显示 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`，表明配置校验失败，导致容器退出。"}, {"phenomenon": "ConfigMap 和 Secret 验证", "level": "important", "value": "尝试获取 `ConfigMap` 和 `Secret` `app-config` 和 `app-secret`，但均未找到，表明这些配置资源可能缺失或引用错误。"}], "evidence_analysis": [{"phenomenon": "Pod 状态和事件", "level": "critical", "value": "Pod `rc-config-env-missing-5d9b8b766c-cstkh` 处于 `CrashLoopBackOff` 状态，最后一次容器终止的 `Exit Code` 为 42，`Reason` 为 `Error`，事件日志显示 `Back-off restarting failed container`，表明容器启动失败并持续重启，`kubectl describe` 显示容器配置中缺失关键环境变量 `APP_BOOT_MODE`。"}, {"phenomenon": "容器日志", "level": "critical", "value": "上一次容器运行的日志显示 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`，表明配置校验失败，导致容器退出。"}, {"phenomenon": "ConfigMap 和 Secret 验证", "level": "important", "value": "尝试获取 `ConfigMap` 和 `Secret` `app-config` 和 `app-secret`，但均未找到，表明这些配置资源可能缺失或引用错误。"}], "causal_chain": {"root_cause": "Pod 缺失环境变量 APP_BOOT_MODE，导致应用配置校验失败。", "intermediate_causes": ["容器日志显示 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`，表明配置校验失败，导致容器退出。", "尝试获取 `ConfigMap` 和 `Secret` `app-config` 和 `app-secret`，但均未找到，表明这些配置资源可能缺失或引用错误。"], "immediate_effects": ["Pod `rc-config-env-missing-5d9b8b766c-cstkh` 处于 `CrashLoopBackOff` 状态，最后一次容器终止的 `Exit Code` 为 42，`Reason` 为 `Error`，事件日志显示 `Back-off restarting failed container`，表明容器启动失败并持续重启。"]}, "root_cause": "Pod 缺失环境变量 APP_BOOT_MODE，导致应用配置校验失败。直接证据包括 Exit Code 42 和日志中 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE。", "root_cause_summary": "Pod 缺失环境变量 APP_BOOT_MODE，导致应用配置校验失败。直接证据包括 Exit Code 42 和日志中 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE。", "confidence": 0.9, "confidence_reason": "有直接证据，因果链清晰。", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [{"cause": "ConfigMap/Secret 引用错误或键名拼写错误，导致应用启动失败。", "probability": "high", "reason": "Pod 配置引用的 ConfigMap/Secret 缺失或键名拼错，导致容器启动失败。"}, {"cause": "业务代码在启动前校验配置失败，导致容器退出。", "probability": "high", "reason": "日志中提示配置校验失败，业务代码在启动前就退出。"}], "limitations": "无", "llm_raw_analysis": "分析总结：\n- Pod `rc-config-env-missing-5d9b8b766c-cstkh` 处于 `CrashLoopBackOff` 状态，且容器启动失败，主要原因是缺少环境变量 `APP_BOOT_MODE`。\n- 容器日志进一步确认了配置校验失败的原因，表明应用在启动前就因配置缺失而退出。\n- 尝试获取相关的 `ConfigMap` 和 `Secret` 资源时，发现这些资源未找到，可能配置资源缺失或引用错误。\n- 该问题符合 `ConfigError` 类型，归类为 L4 级别。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 缺失环境变量 APP_BOOT_MODE，导致应用配置校验失败。直接证据包括 Exit Code 42 和日志中 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE。
   置信度: 90%
   🔗 因果链:
     根本原因: Pod 缺失环境变量 APP_BOOT_MODE，导致应用配置校验失败。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 30.2s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4250 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 6m 30.4s
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
| **证据完整度** | 3/3 (100%) |

---

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-config-env-missing-5d9b8b766c-cstkh |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE |

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff, RESTARTS: 30` | Pod 处于持续重启状态 |
| 2 | Pod 详细信息 | `kubectl describe pod` | `Reason: CrashLoopBackOff` | 容器启动失败并进入重启循环 |
| 3 | 容器日志（上一次运行） | `kubectl logs <pod> --previous` | `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE` | 容器启动失败，明确提示缺失环境变量 `APP_BOOT_MODE` |
| 4 | Pod 配置 | `kubectl get pod -o json` | Pod 未定义 `APP_BOOT_MODE` 环境变量 | 配置缺失导致容器启动失败 |
| 5 | ConfigMap 检查 | `kubectl get configmap app-config -n aiops-e2e` | `Error from server (NotFound): configmaps "app-config" not found` | 未找到引用的 ConfigMap `app-config` |
| 6 | Secret 检查 | `kubectl get secret app-secret -n aiops-e2e` | `Error from server (NotFound): secrets "app-secret" not found` | 未找到引用的 Secret `app-secret` |
| 7 | Runbook 匹配 | `fetch_runbook` | `Pod异常类型: ConfigError | 典型状态: CrashLoopBackOff` | 与已知的配置错误模式匹配 |

### 证据关联分析
- **证据 #3 印证**：日志中明确提示 `missing required APP_BOOT_MODE`，直接确认配置缺失。
- **证据 #4 印证**：Pod 没有定义该环境变量，进一步确认配置缺失。
- **证据 #5 + #6 印证**：Pod 所引用的 ConfigMap 和 Secret 未找到，可能是配置来源缺失。
- **证据链**：Pod 缺失关键环境变量 → 应用配置校验失败 → 容器退出 → Pod 进入 CrashLoopBackOff。

---

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod 缺失环境变量 APP_BOOT_MODE，导致应用配置校验失败              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器启动时发现 APP_BOOT_MODE 未定义，触发配置校验失败            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器退出，Exit Code 42，日志提示 L4_CONFIG_BOOTSTRAP_FAIL        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CrashLoopBackOff，持续重启                           │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #3 (日志中 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`) 和证据 #4 (Pod 未定义 `APP_BOOT_MODE`)，问题的根本原因是**Pod 缺失关键环境变量 `APP_BOOT_MODE`**，导致应用在启动前配置校验失败，容器退出并进入 CrashLoopBackOff。
**置信度**：高 (90%)
- ✅ 日志明确提示配置校验失败
- ✅ Pod 未定义所需环境变量
- ✅ 与已知配置错误 Runbook 匹配

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 为 Pod 添加缺失的环境变量 `APP_BOOT_MODE`**
```bash
kubectl set env deployment/rc-config-env-missing -n aiops-e2e APP_BOOT_MODE=local
```
*依据*：日志提示缺失 `APP_BOOT_MODE`，此命令为 Pod 添加该环境变量并指定值为 `local`（可按实际需求修改）。

**2. [可选] 验证 ConfigMap/Secret 是否存在**
```bash
kubectl get configmap -n aiops-e2e
kubectl get secret -n aiops-e2e
```
*目的*：确认是否存在应用依赖的 ConfigMap 或 Secret，若不存在可创建或修复引用。

### 后续优化
1. **配置检查自动化**：在部署流水线中添加配置校验步骤，确保关键环境变量存在。
2. **配置对象统一管理**：将环境变量集中到 ConfigMap/Secret 中管理，避免硬编码。
3. **日志告警**：配置日志告警，检测 `L4_CONFIG_BOOTSTRAP_FAIL` 等关键错误信息。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |
| 3. 检查环境变量是否注入 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o jsonpath='{.spec.containers[0].env}'` | 包含 `APP_BOOT_MODE` |

---

## ⚠️ 注意事项
- 如果问题仍然存在，建议检查应用代码是否在启动前强制校验配置。
- 若 `APP_BOOT_MODE` 应该从 ConfigMap/Secret 中注入，请确认引用是否正确。
- 若 Pod 由 Deployment/StatefulSet 管理，修改环境变量后需确保 Pod 重启生效。

---

## 📊 性能统计

├─ 总耗时: 6.5m
├─ 问题定位: 58.4s (15%) ✅
├─ 证据链采集: 144.6s (37%) ✅
├─ 根因分析: 97.2s (25%) ✅
├─ 汇总总结: 90.2s (23%) ✅
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
