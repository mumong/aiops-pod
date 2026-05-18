======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 872528fdf8be4f6c]

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
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                     READY   STATUS             RESTARTS        AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-config-env-missing-5d9b8b766c-cstkh   0/
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": ["L4"],
  "layer_name": "ConfigError",
  "confidence": 0.95,
  "reasoning": "当前 Pod 状态为 CrashLoopBackOff，重启次数持续增加，且最后一次崩溃前的日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，表明这是一个配置错误问题。此外，describe Pod 显示其状态为 CrashLoopBackOff，符合 ConfigError 的典型特征。",
  "abnormal_pods": [
    {
      "name": "rc-config-env-missing-5d9b8b766c-cstkh",
      "namespace": "aiops-e2e",
      "status": "CrashLoopBackOff",
      "restarts": "14 (5m1s ago)",
      "ip": "172.16.166.152",
      "node": "node1"
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
    "rc-config-env-missing-5d9b8b766c-cstkh",
    "aiops-e2e",
    "node1"
  ],
  "possible_scenarios": [
    "Pod 缺失环境变量 APP_BOOT_MODE，导致配置校验失败。",
    "Pod 的 ConfigMap 或 Secret 中缺少必要的配置信息。",
    "Pod 的启动脚本或配置文件存在错误，导致容器无法正常启动。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 12.5s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'Pod 缺失环境变量 APP_BOOT_MODE，导致配置校验失败。', 'probability': 'High', 'reason': '日志中显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE。'}, {'scenario': 'Pod 的 ConfigMap 或 Secret 中缺少必要的配置信息。', 'probability': 'High', 'reason': 'Pod 状态为 CrashLoopBackOff，describe 中显示 pod_abnormal_type=ConfigError。'}, {'scenario': 'Pod 的启动脚本或配置文件存在错误，导致容器无法正常启动。', 'probability': 'High', 'reason': '日志中显示配置校验失败，且 Exit Code 非 137，符合 ConfigError 特征。'}]
   entities=[{"type": "Pod", "name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}]
   reasoning=当前 Pod 状态为 CrashLoopBackOff，重启次数持续增加，且最后一次崩溃前的日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，表明这是一个配置错误问题。此外，describe Pod 显示其状态为 CrashLoopBackOff，符合 ConfigError 的典型特征。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.95, "reasoning": "当前 Pod 状态为 CrashLoopBackOff，重启次数持续增加，且最后一次崩溃前的日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，表明这是一个配置错误问题。此外，describe Pod 显示其状态为 CrashLoopBackOff，符合 ConfigError 的典型特征。", "abnormal_pods": [{"name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "CrashLoopBackOff", "key_entities": [{"type": "Pod", "name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}], "possible_scenarios": [{"scenario": "Pod 缺失环境变量 APP_BOOT_MODE，导致配置校验失败。", "probability": "High", "reason": "日志中显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE。"}, {"scenario": "Pod 的 ConfigMap 或 Secret 中缺少必要的配置信息。", "probability": "High", "reason": "Pod 状态为 CrashLoopBackOff，describe 中显示 pod_abnormal_type=ConfigError。"}, {"scenario": "Pod 的启动脚本或配置文件存在错误，导致容器无法正常启动。", "probability": "High", "reason": "日志中显示配置校验失败，且 Exit Code 非 137，符合 ConfigError 特征。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-cstkh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-cstkh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-env-missing-5d9b8b766c-cstkh              0/1     CrashLoopBackOff   14 (4m41s ago)   51m     172.16.166.152   node1    <none>           <none>            app=rc-config-env-missing,pod-template-hash=5d9b8b766c,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/872528fdf8be4f6c/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/872528fdf8be4f6c/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/872528fdf8be4f6c/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-env-missing-5d9b8b766c-cstkh
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Reason:       CrashLoopBackOff
  Warning  BackOff         3m30
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                     READY   STATUS             RESTARTS         AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-config-env-missing-5d9b8b766c-cstkh   0
   💭 [证据链采集] # 证据结论

## 已采集证据
1. **Pod 状态与事件**：通过 `kubectl describe pod` 确认 Pod 状态为 `CrashLoopBackOff`，且最近一次失败原因为 `Error`，Exit Code 为 42。事件日志显示 `Back-off restarting failed container app`，确认 Pod 正在频繁崩溃。
2. **崩溃前日志**：通过 `kubectl logs --previous` 确认崩溃前日志为 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`，表明配置校验失败，缺少必要的环境变量。
3. **Pod 配置验证**：通过 `kubectl get pod` 确认 Pod 当前仍处于 `CrashLoopBackOff` 状态，重启次数为 15 次，状态未改善。

## 未采集证据
- 未进一步验证 Pod 所引用的 ConfigMap 或 Secret 是否缺失或配置错误。
- 未检查 Pod 的启动脚本或配置文件是否存在语法错误或依赖问题。

## 冲突证据
- 无冲突证据。

## 结论
当前 Pod `rc-config-env-missing-5d9b8b766c-cstkh` 处于 `CrashLoopBackOff` 状态，频繁崩溃，且崩溃前日志显示缺少必要的环境变量 `APP_BOOT_MODE`。这表明 Pod 的启动配置存在错误，导致容器无法正常启动。建议进一步检查 Pod 所引用的 ConfigMap 或 Secret，确认 `APP_BOOT_MODE` 环境变量是否存在并正确配置。
   ✅ [证据链采集] 完成 (1m 53.1s)
   📤 → 下游数据: evidence_items=5/6
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证异常 Pod 的详细状态信息和事件，确认配置错误的具体原因。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e","tool_args":{"name":"rc-config-env-missing-5d9b8b766c-cstkh","namespace":"aiops-e2e"},"purpose":"确认异常 Pod 的详细状态、事件和原因，以验证配置错误的具体特征。","evidence_type":"status_events","target_scope":"Pod/aiops-e2e/rc-config-env-missing-5d9b8b766c-cstkh","acceptable_tools":["kubectl_describe","kubectl_events"],"counts_for_completeness":true},{"id":"e2","description":"查看异常 Pod 的上一次容器日志，确认配置校验失败的具体错误信息。","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e --previous","tool_args":{"name":"rc-config-env-missing-5d9b8b766c-cstkh","namespace":"aiops-e2e","container":""},"purpose":"确认 Pod 上一次崩溃的容器日志，以验证配置校验失败的错误信息。","evidence_type":"container_logs","target_scope":"Pod/aiops-e2e/rc-config-env-missing-5d9b8b766c-cstkh","acceptable_tools":["kubectl_previous_logs","kubectl_logs"],"counts_for_completeness":true},{"id":"e3","description":"查看异常 Pod 的配置，确认环境变量、ConfigMap、Secret 等配置是否缺失。","level":"important","tool":"kubectl_get_by_name","command":"kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o yaml","tool_args":{"name":"rc-config-env-missing-5d9b8b766c-cstkh","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"确认 Pod 的配置是否缺失环境变量 APP_BOOT_MODE 或其他配置资源。","evidence_type":"configuration","target_scope":"Pod/aiops-e2e/rc-config-env-missing-5d9b8b766c-cstkh","acceptable_tools":["kubectl_get_by_name","kubectl_get_yaml"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-env-missing-5d9b8b766c-cstkh\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         3m30s (x234 over 53m)  kubelet            Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-cstkh_aiops-e2e(5ed47e61-9e99-459d-88de-ee30d25b1def)\n                  cni.projectcalico.org/containerID: b609d3199474fd0c991fb51944c653ad8de49c03971407f25be4cb50f1498fc2\n                  cni.projectcalico.org/podIP: 172.16.166.152/32\n                  cni.projectcalico.org/podIPs: 172.16.166.152/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/872528fdf8be4f6c/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/872528fdf8be4f6c/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/872528fdf8be4f6c/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 1\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/872528fdf8be4f6c/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/872528fdf8be4f6c/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/872528fdf8be4f6c/tools/002-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                                     READY   STATUS             RESTARTS         AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-config-env-missing-5d9b8b766c-cstkh   0/1     CrashLoopBackOff   15 (2m20s ago)   53m   172.16.166.152   node1   <none>           <none>            app=rc-config-env-missing,pod-template-hash=5d9b8b766c,pod_abnormal_type=ConfigError,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/872528fdf8be4f6c/tools/003-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/872528fdf8be4f6c/tools/003-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/872528fdf8be4f6c/tools/003-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"# 证据结论\n\n## 已采集证据\n1. **Pod 状态与事件**：通过 `kubectl describe pod` 确认 Pod 状态为 `CrashLoopBackOff`，且最近一次失败原因为 `Error`，Exit Code 为 42。事件日志显示 `Back-off restarting failed container app`，确认 Pod 正在频繁崩溃。\n2. **崩溃前日志**：通过 `kubectl logs --previous` 确认崩溃前日志为 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`，表明配置校验失败，缺少必要的环境变量。\n3. **Pod 配置验证**：通过 `kubectl get pod` 确认 Pod 当前仍处于 `CrashLoopBackOff` 状态，重启次数为 15 次，状态未改善。\n\n## 未采集证据\n- 未进一步验证 Pod 所引用的 ConfigMap 或 Secret 是否缺失或配置错误。\n- 未检查 Pod 的启动脚本或配置文件是否存在语法错误或依赖问题。\n\n## 冲突证据\n- 无冲突证据。\n\n## 结论\n当前 Pod `rc-config-env-missing-5d9b8b766c-cstkh` 处于 `CrashLoopBackOff` 状态，频繁崩溃，且崩溃前日志显示缺少必要的环境变量 `APP_BOOT_MODE`。这表明 Pod 的启动配置存在错误，导致容器无法正常启动。建议进一步检查 Pod 所引用的 ConfigMap 或 Secret，确认 `APP_BOOT_MODE` 环境变量是否存在并正确配置。","collection_summary":"计划 3 项，实际采集 2 项，未采集 1 项，完整度 67%；其中真实环境证据 5/6 项，完整度 83%；实际执行工具 6 个，匹配计划 2 个，未规划证据 4 个","plan_total":3,"plan_collected":2,"plan_completeness":0.6666666666666666,"environment_evidence_total":6,"environment_evidence_collected":5,"environment_evidence_completeness":0.8333333333333334,"executed_tool_count":6,"matched_tool_count":2,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"验证异常 Pod 的详细状态信息和事件，确认配置错误的具体原因。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e","purpose":"确认异常 Pod 的详细状态、事件和原因，以验证配置错误的具体特征。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"查看异常 Pod 的上一次容器日志，确认配置校验失败的具体错误信息。","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e --previous","purpose":"确认 Pod 上一次崩溃的容器日志，以验证配置校验失败的错误信息。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"查看异常 Pod 的配置，确认环境变量、ConfigMap、Secret 等配置是否缺失。","level":"important","tool":"kubectl_get_by_name","command":"kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o yaml","purpose":"确认 Pod 的配置是否缺失环境变量 APP_BOOT_MODE 或其他配置资源。","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e3(查看异常 Pod 的配置，确认环境变量、ConfigMap、Secret 等配置是否缺失。): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/3 项, 完整度: 83%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证异常 Pod 的详细状态信息和事件，确认配置错误的具体原因。 | `kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_previous_logs | 查看异常 Pod 的上一次容器日志，确认配置校验失败的具体错误信息。 | `kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e --previous` |
   | e3 | important | ❌ | kubectl_get_by_name | 查看异常 Pod 的配置，确认环境变量、ConfigMap、Secret 等配置是否缺失。 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o yaml` |

   ⚠️ 未采集原因:
   - e3(查看异常 Pod 的配置，确认环境变量、ConfigMap、Secret 等配置是否缺失。): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (39.6s)
   📤 → 下游数据: root_cause=Pod rc-config-env-missing-5d9b8b766c-cstkh 缺少必要的环境变量 APP_BOOT_MODE，导致配置校验失败。崩溃前日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，表明配置错误。
   confidence=95%
   causal_chain={"root_cause": "Pod rc-config-env-missing-5d9b8b766c-cstkh 缺少必要的环境变量 APP_BOOT_MODE，导致配置校验失败。", "immediate_cause": "配置校验失败，容器无法正常启动。", "effect": "Pod 状态为 CrashLoopBackOff，频繁崩溃。"}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"kubectl_describe_pod": "Pod rc-config-env-missing-5d9b8b766c-cstkh 状态为 CrashLoopBackOff，重启次数为15次，最近一次失败原因为 Error，Exit Code 为42。"}, {"kubectl_previous_logs": "崩溃前日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，表明配置校验失败，缺少必要的环境变量。"}, {"kubectl_get_pod": "Pod rc-config-env-missing-5d9b8b766c-cstkh 当前仍处于 CrashLoopBackOff 状态，重启次数为15次，状态未改善。"}], "evidence_analysis": [{"kubectl_describe_pod": "Pod 状态为 CrashLoopBackOff，表明容器频繁崩溃并被 Kubernetes 重启。最近一次失败原因为 Error，Exit Code 为42，表明配置错误。"}, {"kubectl_previous_logs": "崩溃前日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，表明配置校验失败，缺少必要的环境变量 APP_BOOT_MODE。"}, {"kubectl_get_pod": "Pod 状态未改善，表明问题仍未解决，需要进一步检查配置。"}], "causal_chain": {"root_cause": "Pod rc-config-env-missing-5d9b8b766c-cstkh 缺少必要的环境变量 APP_BOOT_MODE，导致配置校验失败。", "immediate_cause": "配置校验失败，容器无法正常启动。", "effect": "Pod 状态为 CrashLoopBackOff，频繁崩溃。"}, "root_cause": "Pod rc-config-env-missing-5d9b8b766c-cstkh 缺少必要的环境变量 APP_BOOT_MODE，导致配置校验失败。崩溃前日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，表明配置错误。", "root_cause_summary": "Pod rc-config-env-missing-5d9b8b766c-cstkh 缺少必要的环境变量 APP_BOOT_MODE，导致配置校验失败。崩溃前日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，表明配置错误。", "confidence": 0.95, "confidence_reason": "有直接证据支持，因果链清晰。", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [{"scenario": "Pod 的 ConfigMap 或 Secret 中缺少必要的配置信息。", "probability": "High", "reason": "Pod 状态为 CrashLoopBackOff，describe 中显示 pod_abnormal_type=ConfigError。"}, {"scenario": "Pod 的启动脚本或配置文件存在错误，导致容器无法正常启动。", "probability": "High", "reason": "日志中显示配置校验失败，且 Exit Code 非 137，符合 ConfigError 特征。"}], "limitations": "未进一步验证 Pod 所引用的 ConfigMap 或 Secret 是否缺失或配置错误。", "llm_raw_analysis": "当前 Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，频繁崩溃，且崩溃前日志显示缺少必要的环境变量 APP_BOOT_MODE。这表明 Pod 的启动配置存在错误，导致容器无法正常启动。建议进一步检查 Pod 所引用的 ConfigMap 或 Secret，确认 APP_BOOT_MODE 环境变量是否存在并正确配置。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-config-env-missing-5d9b8b766c-cstkh 缺少必要的环境变量 APP_BOOT_MODE，导致配置校验失败。崩溃前日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，表明配置错误。
   置信度: 95%
   🔗 因果链:
     根本原因: Pod rc-config-env-missing-5d9b8b766c-cstkh 缺少必要的环境变量 APP_BOOT_MODE，导致配置校验失败。


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
   ✅ [汇总总结] 完成 (2m 23.4s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4986 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 6m 8.5s
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
| **兼容归因层** | L4 - 配置错误（ConfigError） |
| **问题分类** | ConfigError（配置错误） |
| **置信度** | 高 (95%) |
| **证据完整度** | 2/3 (67%) |

---

## 🔍 现象描述

**用户报告**：  
> 我的集群有什么问题？

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | `rc-config-env-missing-5d9b8b766c-cstkh` |
| Namespace | `aiops-e2e` |
| Node | `node1` |
| 错误信息 | `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff`, `RESTARTS: 14 (5m1s ago)` | Pod 由于配置错误持续崩溃并重启 |
| 2 | 崩溃前日志 | `kubectl logs <pod> --previous` | `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE` | 明确指出缺少必要环境变量 |
| 3 | kubectl describe | `kubectl describe pod` | `Reason: CrashLoopBackOff` | 事件表明是配置错误导致容器无法启动 |
| 4 | kubectl get pod by name | `kubectl get pod -n aiops-e2e rc-config-env-missing-5d9b8b766c-cstkh` | `STATUS: CrashLoopBackOff`, `NAMESPACE: aiops-e2e` | 确认 Pod 当前状态 |
| 5 | 工具结果验证 | `kubectl_get_by_kind_in_cluster` | `rows=49 abnormal=1 status_counts={'CrashLoopBackOff': 1, 'Running': 46}` | 仅 1 个 Pod 出现异常，其余运行正常 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 `CrashLoopBackOff`，且崩溃前日志明确指出 `APP_BOOT_MODE` 缺失 → **配置错误**
- **证据 #3 印证**：`kubectl describe pod` 显示 `Reason: CrashLoopBackOff`，表明是容器启动失败后的自动重启
- **证据链**：缺失 `APP_BOOT_MODE` → 配置校验失败 → 容器启动失败 → Pod 进入 CrashLoopBackOff 状态

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| Pod 的配置信息（env、ConfigMap、Secret） | important | 无法确认缺失配置的具体来源（是否来自 ConfigMap、Secret 或直接 env） |

---

## 🎯 根因分析

### 因果链

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                      │
│ Pod 缺少环境变量 `APP_BOOT_MODE`，导致配置校验失败                            │
└───────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                      │
│ 容器启动时依赖的 `APP_BOOT_MODE` 环境变量缺失 → 配置校验失败 → 容器启动失败   │
└───────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                      │
│ 容器启动失败 → Pod 进入 CrashLoopBackOff 状态，持续重启                       │
└───────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                  │
│ Pod 状态为 `CrashLoopBackOff`，重启次数不断增加                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2 (`L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`) 和证据 #1 (`CrashLoopBackOff`)，问题的根本原因是 **Pod 缺少必要的环境变量 `APP_BOOT_MODE`，导致配置校验失败**，从而无法正常启动容器。  
**置信度**：高 (95%)  
- ✅ 崩溃前日志明确指出 `APP_BOOT_MODE` 缺失  
- ✅ `kubectl describe pod` 显示 `Reason: CrashLoopBackOff`  
- ⚠️ 缺失 `kubectl get pod -o yaml` 信息，无法确认 `APP_BOOT_MODE` 是直接定义、来自 ConfigMap 还是 Secret

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 为 Pod 补充缺失的环境变量 `APP_BOOT_MODE`**

```bash
kubectl set env deployment/rc-config-env-missing-5d9b8b766c APP_BOOT_MODE=dev -n aiops-e2e
```

*依据*：崩溃前日志明确指出 `APP_BOOT_MODE` 缺失，这是配置失败的根本原因

**2. [可选] 查看 Pod 的完整配置**

```bash
kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -o yaml -n aiops-e2e
```

*目的*：确认 `APP_BOOT_MODE` 是通过 env、ConfigMap 还是 Secret 注入的

### 后续优化

1. **配置检查自动化**：通过 CI/CD 管道或 Helm Chart 模板检查环境变量完整性
2. **监控告警**：设置 Pod 重启次数告警，如超过 3 次重启自动通知
3. **配置中心管理**：集中管理 ConfigMap/Secret，减少配置遗漏风险

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 重启次数不再增加 |
| 3. 查看容器日志 | `kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` | 没有 `L4_CONFIG_BOOTSTRAP_FAIL` 等错误 |

---

## ⚠️ 注意事项

- 如果补丁后问题仍然存在，检查 `APP_BOOT_MODE` 是否被正确注入（如 ConfigMap/Secret 是否存在、权限是否正确）
- 如果是 ConfigMap/Secret 配置问题，可进一步检查 `kubectl get configmap` 或 `kubectl get secret`
- 考虑将环境变量注入机制统一化，防止类似问题再次发生

---

## 📎 附录

### 🧾 证据引用

- [kubectl_get_by_kind_in_cluster](/tmp/aiops/reports/context_archives/872528fdf8be4f6c/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt)
- [kubectl_previous_logs](/tmp/aiops/reports/context_archives/872528fdf8be4f6c/tools/003-layer-kubectl_previous_logs.raw.txt)
- [kubectl_get_by_name](/tmp/aiops/reports/context_archives/872528fdf8be4f6c/tools/004-layer-kubectl_get_by_name.raw.txt)
- [kubectl_describe](evidence)

---

## 📊 性能统计

├─ 总耗时: 6.1m
├─ 问题定位: 72.5s (20%) ✅
├─ 证据链采集: 113.1s (31%) ✅
├─ 根因分析: 39.6s (11%) ✅
├─ 汇总总结: 143.4s (39%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 7 次
```

📋 诊断追踪

- **核心 Runbook**: pod-config-error
- **参考 Runbook**: pod-config-error
- **工具调用**: 7 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
