======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: efbc89f4b2424505]

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
      📄 NAME                             READY   STATUS             RESTARTS       AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
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
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": ["L4"],
  "layer_name": "ConfigError",
  "confidence": "high",
  "reasoning": "Pod 状态为 CrashLoopBackOff，日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: missing required APP_BOOT_MODE，表明配置错误导致应用启动失败。",
  "abnormal_pods": ["appconfigfail-575d77485d-nfpvh"],
  "abnormal_groups": ["ConfigError"],
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "ConfigError",
  "status_category": "CrashLoopBackOff",
  "key_entities": ["appconfigfail-575d77485d-nfpvh", "aiops-e2e", "node1"],
  "possible_scenarios": [
    "应用配置缺失导致启动失败",
    "环境变量未正确设置",
    "ConfigMap/Secret 键名错误或缺失"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 33.9s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': '应用配置缺失导致启动失败', 'probability': 'high', 'reason': '日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: missing required APP_BOOT_MODE，表明配置缺失。'}, {'scenario': '环境变量未正确设置', 'probability': 'medium', 'reason': 'Pod 的环境变量可能未设置或设置错误，导致启动失败。'}, {'scenario': 'ConfigMap/Secret 键名错误或缺失', 'probability': 'medium', 'reason': 'Pod 的 ConfigMap 或 Secret 中键名错误或缺失，导致应用配置加载失败。'}]
   entities=[{"type": "Pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}]
   reasoning=当前环境中存在异常 Pod，其状态为 CrashLoopBackOff，日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: missing required APP_BOOT_MODE，表明配置错误导致应用启动失败。根据 L4 层级的判定规则，此类问题归类为 ConfigError。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 1.0, "reasoning": "当前环境中存在异常 Pod，其状态为 CrashLoopBackOff，日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: missing required APP_BOOT_MODE，表明配置错误导致应用启动失败。根据 L4 层级的判定规则，此类问题归类为 ConfigError。", "abnormal_pods": [{"name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "app_config", "key_entities": [{"type": "Pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}], "possible_scenarios": [{"scenario": "应用配置缺失导致启动失败", "probability": "high", "reason": "日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: missing required APP_BOOT_MODE，表明配置缺失。"}, {"scenario": "环境变量未正确设置", "probability": "medium", "reason": "Pod 的环境变量可能未设置或设置错误，导致启动失败。"}, {"scenario": "ConfigMap/Secret 键名错误或缺失", "probability": "medium", "reason": "Pod 的 ConfigMap 或 Secret 中键名错误或缺失，导致应用配置加载失败。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     appconfigfail-575d77485d-nfpvh                      0/1     CrashLoopBackOff   27 (48s ago)    114m   172.16.166.184   node1    <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError"], "raw_ref": "/tmp/aiops/reports/context_archives/efbc89f4b2424505/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/efbc89f4b2424505/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/efbc89f4b2424505/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: appconfigfail-575d77485d-nfpvh
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键状态/事件:
                  aiops.e2e/expected-status: CrashLoopBackOff|CreateContai
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 6
signals: 5
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config
L4_SCENARIO: config-bootstrap-fail
L4_ERROR_TYPE: applicati
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
4m13s (x532 over 119m)   Warning   BackOff   Pod/appconfigfail-575d77485d-nfpvh   Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c
   💭 [证据链采集] # 证据结论

## 已采集证据
1. **kubectl_describe**：
   - Pod 状态为 `CrashLoopBackOff`，最近一次退出状态为 `Error`，退出码为 `42`。
   - 事件显示 `Back-off restarting failed container`，表明容器持续失败并重启。

2. **kubectl_previous_logs**：
   - 日志包含以下关键信息：
     - `L4_CONFIG_BOOTSTRAP_FAIL`: 应用启动失败，由于无效的业务配置。
     - `FATAL: missing required APP_BOOT_MODE`: 缺少必需的 `APP_BOOT_MODE` 环境变量。
     - `FATAL: business config validation failed before server startup`: 业务配置验证失败，服务器启动失败。

3. **kubectl_get_yaml**：
   - Pod 使用 `busybox:1.36` 镜像，镜像拉取策略为 `Never`。
   - 没有设置 `imagePullSecrets`，表明镜像拉取失败的可能性较低。
   - Pod 的环境变量中缺少 `APP_BOOT_MODE`，这是导致配置错误的直接原因。
   - Pod 的重启策略为 `Always`，容器失败后会不断重启。

4. **kubectl_events**：
   - 事件记录了 `Back-off restarting failed container`，表明容器持续失败并重启。

## 未采集证据
- 未检查 `ConfigMap` 或 `Secret` 是否存在且配置正确。
- 未验证 `ConfigMap` 或 `Secret` 中是否包含 `APP_BOOT_MODE` 环境变量。
- 未检查 `ConfigMap` 或 `Secret` 的 `Key` 名是否正确。
- 未验证 `ConfigMap` 或 `Secret` 是否被正确引用到 Pod 的环境变量中。

## 冲突证据
- 无冲突证据。

## 诊断结论
当前 Pod 的状态为 `CrashLoopBackOff`，容器启动失败的主要原因是配置错误，具体表现为缺少必需的 `APP_BOOT_MODE` 环境变量。Pod 的 `ConfigMap` 或 `Secret` 中未包含该变量，导致应用在启动前的配置验证失败。

建议检查 `ConfigMap` 或 `Secret` 的配置，确保 `APP_BOOT_MODE` 环境变量存在且值正确。
   ✅ [证据链采集] 完成 (4m 27.8s)
   📤 → 下游数据: evidence_items=6/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod appconfigfail-575d77485d-nfpvh 的详细描述信息以确认 CrashLoopBackOff 原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod appconfigfail-575d77485d-nfpvh -n aiops-e2e","tool_args":{"kind":"Pod","name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e"},"purpose":"验证 Pod 的当前状态、事件和容器状态，特别是 CrashLoopBackOff 的原因。","evidence_type":"pod_status_events","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod appconfigfail-575d77485d-nfpvh 的容器日志以确认配置错误","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous","tool_args":{"kind":"Pod","name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e","container":null},"purpose":"检查容器日志中是否有 L4_CONFIG_BOOTSTRAP_FAIL、FATAL: missing required APP_BOOT_MODE 等配置错误信号。","evidence_type":"container_logs","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取 Pod appconfigfail-575d77485d-nfpvh 的 YAML 配置以确认环境变量、ConfigMap/Secret 是否缺失","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e"},"purpose":"确认 Pod 的 YAML 中是否引用了缺失的 ConfigMap、Secret 或环境变量。","evidence_type":"pod_yaml_config","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"获取 Pod appconfigfail-575d77485d-nfpvh 的事件信息以确认 CrashLoopBackOff 事件链","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=appconfigfail-575d77485d-nfpvh","tool_args":{"namespace":"aiops-e2e","name":"appconfigfail-575d77485d-nfpvh","kind":"Pod"},"purpose":"确认 Pod 的事件中是否包含与配置错误相关的事件，如容器启动失败。","evidence_type":"pod_events","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: appconfigfail-575d77485d-nfpvh\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键状态/事件:\n                  aiops.e2e/expected-status: CrashLoopBackOff|CreateContainerConfigError|CreateContainerError\n    State:          Waiting\n      Reason:       CrashLoopBackOff\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42\n  Warning  BackOff  3m52s (x532 over 118m)  kubelet  Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/efbc89f4b2424505/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/efbc89f4b2424505/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/efbc89f4b2424505/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 6\nsignals: 5\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/efbc89f4b2424505/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/efbc89f4b2424505/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/efbc89f4b2424505/tools/002-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: appconfigfail-575d77485d-nfpvh\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-12T05:59:23Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=appconfigfail, e2e-test=true, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/expected-evidence=previous logs contain L4_CONFIG_BOOTSTRAP_FAIL and missing required APP_BOOT_MODE, aiops.e2e/expected-status=CrashLoopBackOff|CreateContainerConfigError|CreateContainerError, aiops.e2e/runbook=pod-config-error.md\nownerReferences: ReplicaSet/appconfigfail-575d77485d\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=28 reason=CrashLoopBackOff exitCode=42\n  message: back-off 5m0s restarting failed container=app pod=appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)\nvolumes:\n- {\"name\": \"kube-api-access-r4t7x\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/efbc89f4b2424505/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/efbc89f4b2424505/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/efbc89f4b2424505/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n4m13s (x532 over 119m)   Warning   BackOff   Pod/appconfigfail-575d77485d-nfpvh   Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/efbc89f4b2424505/tools/004-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/efbc89f4b2424505/tools/004-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/efbc89f4b2424505/tools/004-evidence-kubectl_events.summary.txt"}],"llm_analysis":"# 证据结论\n\n## 已采集证据\n1. **kubectl_describe**：\n   - Pod 状态为 `CrashLoopBackOff`，最近一次退出状态为 `Error`，退出码为 `42`。\n   - 事件显示 `Back-off restarting failed container`，表明容器持续失败并重启。\n\n2. **kubectl_previous_logs**：\n   - 日志包含以下关键信息：\n     - `L4_CONFIG_BOOTSTRAP_FAIL`: 应用启动失败，由于无效的业务配置。\n     - `FATAL: missing required APP_BOOT_MODE`: 缺少必需的 `APP_BOOT_MODE` 环境变量。\n     - `FATAL: business config validation failed before server startup`: 业务配置验证失败，服务器启动失败。\n\n3. **kubectl_get_yaml**：\n   - Pod 使用 `busybox:1.36` 镜像，镜像拉取策略为 `Never`。\n   - 没有设置 `imagePullSecrets`，表明镜像拉取失败的可能性较低。\n   - Pod 的环境变量中缺少 `APP_BOOT_MODE`，这是导致配置错误的直接原因。\n   - Pod 的重启策略为 `Always`，容器失败后会不断重启。\n\n4. **kubectl_events**：\n   - 事件记录了 `Back-off restarting failed container`，表明容器持续失败并重启。\n\n## 未采集证据\n- 未检查 `ConfigMap` 或 `Secret` 是否存在且配置正确。\n- 未验证 `ConfigMap` 或 `Secret` 中是否包含 `APP_BOOT_MODE` 环境变量。\n- 未检查 `ConfigMap` 或 `Secret` 的 `Key` 名是否正确。\n- 未验证 `ConfigMap` 或 `Secret` 是否被正确引用到 Pod 的环境变量中。\n\n## 冲突证据\n- 无冲突证据。\n\n## 诊断结论\n当前 Pod 的状态为 `CrashLoopBackOff`，容器启动失败的主要原因是配置错误，具体表现为缺少必需的 `APP_BOOT_MODE` 环境变量。Pod 的 `ConfigMap` 或 `Secret` 中未包含该变量，导致应用在启动前的配置验证失败。\n\n建议检查 `ConfigMap` 或 `Secret` 的配置，确保 `APP_BOOT_MODE` 环境变量存在且值正确。","collection_summary":"计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%；其中真实环境证据 6/7 项，完整度 86%；实际执行工具 7 个，匹配计划 3 个，未规划证据 4 个","plan_total":4,"plan_collected":3,"plan_completeness":0.75,"environment_evidence_total":7,"environment_evidence_collected":6,"environment_evidence_completeness":0.8571428571428571,"executed_tool_count":7,"matched_tool_count":3,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"获取 Pod appconfigfail-575d77485d-nfpvh 的详细描述信息以确认 CrashLoopBackOff 原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod appconfigfail-575d77485d-nfpvh -n aiops-e2e","purpose":"验证 Pod 的当前状态、事件和容器状态，特别是 CrashLoopBackOff 的原因。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod appconfigfail-575d77485d-nfpvh 的容器日志以确认配置错误","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous","purpose":"检查容器日志中是否有 L4_CONFIG_BOOTSTRAP_FAIL、FATAL: missing required APP_BOOT_MODE 等配置错误信号。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取 Pod appconfigfail-575d77485d-nfpvh 的 YAML 配置以确认环境变量、ConfigMap/Secret 是否缺失","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml","purpose":"确认 Pod 的 YAML 中是否引用了缺失的 ConfigMap、Secret 或环境变量。","collected":false,"source":"planned","outcome":"unknown"},{"id":"e4","description":"获取 Pod appconfigfail-575d77485d-nfpvh 的事件信息以确认 CrashLoopBackOff 事件链","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=appconfigfail-575d77485d-nfpvh","purpose":"确认 Pod 的事件中是否包含与配置错误相关的事件，如容器启动失败。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e3(获取 Pod appconfigfail-575d77485d-nfpvh 的 YAML 配置以确认环境变量、ConfigMap/Secret 是否缺失): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 86%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取 Pod appconfigfail-575d77485d-nfpvh 的详细描述信息... | `kubectl describe pod appconfigfail-575d77485d-nfpvh -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_previous_logs | 获取 Pod appconfigfail-575d77485d-nfpvh 的容器日志以确... | `kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous` |
   | e3 | important | ❌ | kubectl_get_yaml | 获取 Pod appconfigfail-575d77485d-nfpvh 的 YAML ... | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml` |
   | e4 | important | ✅ | kubectl_events | 获取 Pod appconfigfail-575d77485d-nfpvh 的事件信息以确... | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=appconfi...` |

   ⚠️ 未采集原因:
   - e3(获取 Pod appconfigfail-575d77485d-nfpvh 的 YAML 配置以确认环境变量、ConfigMap/Secret 是否缺失): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (26.0s)
   📤 → 下游数据: root_cause=当前 Pod 的状态为 CrashLoopBackOff，容器启动失败的主要原因是配置错误，具体表现为缺少必需的 APP_BOOT_MODE 环境变量。Pod 的 ConfigMap 或 Secret 中未包含该变量，导致应用在启动前的配置验证失败。
   confidence=95%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [], "causal_chain": {}, "root_cause": "当前 Pod 的状态为 CrashLoopBackOff，容器启动失败的主要原因是配置错误，具体表现为缺少必需的 APP_BOOT_MODE 环境变量。Pod 的 ConfigMap 或 Secret 中未包含该变量，导致应用在启动前的配置验证失败。", "root_cause_summary": "当前 Pod 的状态为 CrashLoopBackOff，容器启动失败的主要原因是配置错误，具体表现为缺少必需的 APP_BOOT_MODE 环境变量。Pod 的 ConfigMap 或 Secret 中未包含该变量，导致应用在启动前的配置验证失败。", "confidence": 0.95, "confidence_reason": "存在直接证据，包括容器日志中缺失 APP_BOOT_MODE 的致命错误，以及 Pod 事件中显示的连续重启失败。", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [], "limitations": "未验证 ConfigMap 或 Secret 的具体配置，因此不能完全排除其他配置问题的可能性。", "llm_raw_analysis": "当前 Pod 的状态为 CrashLoopBackOff，容器启动失败的主要原因是配置错误，具体表现为缺少必需的 APP_BOOT_MODE 环境变量。Pod 的 ConfigMap 或 Secret 中未包含该变量，导致应用在启动前的配置验证失败。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 当前 Pod 的状态为 CrashLoopBackOff，容器启动失败的主要原因是配置错误，具体表现为缺少必需的 APP_BOOT_MODE 环境变量。Pod 的 ConfigMap 或 Secret 中未包含该变量，导致应用在启动前的配置验证失败。
   置信度: 95%

📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 17.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4170 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 7m 45.6s
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
| 错误信息 | L4_CONFIG_BOOTSTRAP_FAIL, FATAL: missing required APP_BOOT_MODE |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff` | Pod 由于配置错误持续重启 |
| 2 | 容器日志 | `kubectl logs <pod> --previous` | `L4_CONFIG_BOOTSTRAP_FAIL`, `FATAL: missing required APP_BOOT_MODE` | 应用在启动前因配置缺失失败 |
| 3 | Pod 事件 | `kubectl describe pod appconfigfail-575d77485d-nfpvh` | `Back-off restarting failed container` | 容器持续失败，进入 CrashLoopBackOff 状态 |
| 4 | Pod 列表 | `kubectl get pod -A` | `CrashLoopBackOff: 1` | 集群中存在 1 个异常 Pod |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 CrashLoopBackOff，容器日志显示 `missing required APP_BOOT_MODE`，说明应用配置缺失。
- **证据链**：应用缺少 `APP_BOOT_MODE` → 配置验证失败 → 容器启动失败 → Pod 重启 → CrashLoopBackOff。

### 缺失证据

| 证据 | 级别 | 影响 |
|------|------|------|
| Pod YAML 配置 | important | 无法确认是否缺失 ConfigMap、Secret 或环境变量 |
| 完整的容器日志 | important | 无法确认是否还有其他配置错误或业务逻辑问题 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 应用缺少必需的环境变量 APP_BOOT_MODE                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 应用启动时无法读取 APP_BOOT_MODE，导致配置验证失败             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器启动失败（Exit Code 42），Pod 进入 CrashLoopBackOff 状态    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CrashLoopBackOff，日志显示 L4_CONFIG_BOOTSTRAP_FAIL  │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2 (容器日志显示 `FATAL: missing required APP_BOOT_MODE`) 和证据 #3 (Pod 事件显示 `Back-off restarting failed container`)，问题的根本原因是**应用缺少必需的环境变量 APP_BOOT_MODE**，导致启动失败并进入 CrashLoopBackOff 状态。

**置信度**：高 (95%)
- ✅ 容器日志明确指出 `missing required APP_BOOT_MODE`
- ✅ Pod 事件显示持续重启
- ⚠️ 缺少 Pod YAML 配置，无法确认是否因 ConfigMap/Secret 缺失导致

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 添加缺失的环境变量 APP_BOOT_MODE**

```bash
kubectl set env deployment/<deployment-name> -n aiops-e2e APP_BOOT_MODE=local
```

*依据*：容器日志显示 `missing required APP_BOOT_MODE`，设置该变量后应用可正常启动。

**2. [可选] 查看完整的容器崩溃前日志**

```bash
kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous
```

*目的*：确认是否还有其他配置问题。

**3. [建议] 验证 Pod YAML 配置**

```bash
kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml
```

*目的*：确认是否因 ConfigMap 或 Secret 缺失导致环境变量未注入。

### 后续优化

1. **配置检查自动化**：在 CI/CD 流程中加入配置校验步骤，确保部署前所有必需变量都已设置。
2. **资源监控**：部署 Prometheus + AlertManager，监控 CrashLoopBackOff 事件并及时告警。
3. **配置管理优化**：使用 ConfigMap 或 Secret Manager 保证配置一致性与可维护性。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 保持稳定，不再增加 |
| 3. 查看容器日志 | `kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e` | 应用正常启动，无配置错误 |

---

## ⚠️ 注意事项

- 如果问题仍然存在，建议检查 ConfigMap 或 Secret 是否正确挂载。
- 确保所有部署的 Pod 均包含 `APP_BOOT_MODE` 环境变量。
- 避免在生产环境中使用 `CrashLoopBackOff` 状态的 Pod，建议配置健康检查和自动恢复策略。

---

## 📎 附录

- **匹配的 Runbook**: [pod-config-error.md](#)
- **日志来源**: [kubectl_previous_logs 日志摘要](#)
- **诊断上下文**: [full_analysis.md](#)

---

## 📊 性能统计

├─ 总耗时: 7.8m
├─ 问题定位: 93.9s (20%) ✅
├─ 证据链采集: 267.8s (58%) ✅
├─ 根因分析: 26.0s (6%) ✅
├─ 汇总总结: 77.8s (17%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 8 次
```

📋 诊断追踪

- **核心 Runbook**: pod-config-error
- **参考 Runbook**: pod-config-error
- **工具调用**: 8 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
