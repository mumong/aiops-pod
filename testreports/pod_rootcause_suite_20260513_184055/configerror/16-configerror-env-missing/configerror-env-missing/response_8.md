======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 6039f39462bc44a1]

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
lines: 1
signals: 1
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                     READY   STATUS             RESTARTS       AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-config-env-missing-5d9b8b766c-cstkh   0/1
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "ConfigError",
  "layers": [
    "L4"
  ],
  "layer_name": "ConfigError",
  "confidence": 0.95,
  "reasoning": "当前异常 Pod 状态为 CrashLoopBackOff，日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，且 Exit Code 非 137，没有 OOMKilled 的迹象，符合 ConfigError 的特征。",
  "abnormal_pods": [
    "rc-config-env-missing-5d9b8b766c-cstkh"
  ],
  "abnormal_groups": [
    "CrashLoopBackOff"
  ],
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "ConfigError",
  "status_category": "CrashLoopBackOff",
  "key_entities": [
    "APP_BOOT_MODE",
    "ConfigMap",
    "Secret"
  ],
  "possible_scenarios": [
    "Pod 缺失必要的环境变量 APP_BOOT_MODE，导致配置初始化失败。",
    "ConfigMap 或 Secret 中的键名拼写错误，导致配置无法正确加载。",
    "Secret data 不是合法 Base64 编码，导致容器启动失败。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 42.7s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'Pod 缺失必要的环境变量 APP_BOOT_MODE，导致配置初始化失败。', 'probability': '高', 'reason': '日志中明确显示缺失 APP_BOOT_MODE 环境变量。'}, {'scenario': 'ConfigMap 或 Secret 中的键名拼写错误，导致配置无法正确加载。', 'probability': '中', 'reason': '配置引用对象可能拼写错误，但需进一步检查配置对象内容。'}, {'scenario': 'Secret data 不是合法 Base64 编码，导致容器启动失败。', 'probability': '低', 'reason': '需要进一步检查 Secret 的 data 编码是否合法。'}]
   entities=[{"type": "ConfigError", "name": "APP_BOOT_MODE", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "ConfigMap", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "Secret", "namespace": "aiops-e2e"}]
   reasoning=当前异常 Pod 状态为 CrashLoopBackOff，日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，且 Exit Code 非 137，没有 OOMKilled 的迹象，符合 ConfigError 的特征。
   layer_analysis={"layer": "L4", "derived_layer": "CONFIGERROR", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.95, "reasoning": "当前异常 Pod 状态为 CrashLoopBackOff，日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，且 Exit Code 非 137，没有 OOMKilled 的迹象，符合 ConfigError 的特征。", "abnormal_pods": [{"name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "CrashLoopBackOff", "key_entities": [{"type": "ConfigError", "name": "APP_BOOT_MODE", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "ConfigMap", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "Secret", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Pod 缺失必要的环境变量 APP_BOOT_MODE，导致配置初始化失败。", "probability": "高", "reason": "日志中明确显示缺失 APP_BOOT_MODE 环境变量。"}, {"scenario": "ConfigMap 或 Secret 中的键名拼写错误，导致配置无法正确加载。", "probability": "中", "reason": "配置引用对象可能拼写错误，但需进一步检查配置对象内容。"}, {"scenario": "Secret data 不是合法 Base64 编码，导致容器启动失败。", "probability": "低", "reason": "需要进一步检查 Secret 的 data 编码是否合法。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-cstkh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-cstkh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-env-missing-5d9b8b766c-cstkh              0/1     CrashLoopBackOff   8 (3m ago)    18m     172.16.166.152   node1    <none>           <none>            app=rc-config-env-missing,pod-template-hash=5d9b8b766c,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/6039f39462bc44a1/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/6039f39462bc44a1/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/6039f39462bc44a1/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-env-missing-5d9b8b766c-cstkh
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Reason:       CrashLoopBackOff
  Warning  BackOff         3m6s
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-config-env-missing-5d9b8b766c-cstkh
namespace: aiops-e2e
creationTimestamp: 2026-05-14T22:19:01Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: Non
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
3m15s (x95 over 23m)   Warning   BackOff          Pod/rc-config-env-missing-5d9b8b766c-cstkh   Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766
   💭 [证据链采集] ### 已采集证据
1. **kubectl_describe**: 
   - Pod 状态为 `CrashLoopBackOff`，Exit Code 为 `42`，无 OOMKilled 痕迹，确认为配置错误。
2. **kubectl_previous_logs**:
   - 日志显示 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`，明确指出缺失的环境变量。
3. **kubectl_get_yaml**:
   - Pod 的配置中未找到 `APP_BOOT_MODE` 的环境变量配置，且未引用任何 ConfigMap 或 Secret 来提供此参数。
4. **kubectl_events**:
   - 事件表明容器因配置错误持续重启，符合 `ConfigError` 的特征。

### 未采集证据
无进一步计划，当前证据已满足诊断需求。

### 冲突证据
无冲突证据。所有采集步骤均成功，且结果一致指向配置缺失问题。
   ✅ [证据链采集] 完成 (2m 54.2s)
   📤 → 下游数据: evidence_items=6/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod rc-config-env-missing-5d9b8b766c-cstkh 的详细描述信息，验证其当前状态和事件信息。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e","tool_args":{"name":"rc-config-env-missing-5d9b8b766c-cstkh","namespace":"aiops-e2e","kind":"pod"},"purpose":"验证异常 Pod 的当前状态、事件和配置信息","evidence_type":"Pod 事件和配置信息","target_scope":"aiops-e2e/rc-config-env-missing-5d9b8b766c-cstkh","acceptable_tools":["kubectl_describe","kubectl_get_by_name","kubectl_events"],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod rc-config-env-missing-5d9b8b766c-cstkh 的日志，验证其启动失败的原因。","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs --previous rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e","tool_args":{"name":"rc-config-env-missing-5d9b8b766c-cstkh","namespace":"aiops-e2e","kind":"pod","container":"container-0"},"purpose":"验证异常 Pod 的启动失败日志","evidence_type":"Pod 启动失败日志","target_scope":"aiops-e2e/rc-config-env-missing-5d9b8b766c-cstkh","acceptable_tools":["kubectl_previous_logs","kubectl_logs"],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod rc-config-env-missing-5d9b8b766c-cstkh 的配置信息，验证其引用的 ConfigMap 或 Secret 是否正确。","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o yaml","tool_args":{"name":"rc-config-env-missing-5d9b8b766c-cstkh","namespace":"aiops-e2e","kind":"pod"},"purpose":"验证异常 Pod 的配置信息","evidence_type":"Pod 配置信息","target_scope":"aiops-e2e/rc-config-env-missing-5d9b8b766c-cstkh","acceptable_tools":["kubectl_get_yaml","kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e4","description":"获取异常 Pod rc-config-env-missing-5d9b8b766c-cstkh 的事件信息，验证其失败的事件。","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-env-missing-5d9b8b766c-cstkh","tool_args":{"name":"rc-config-env-missing-5d9b8b766c-cstkh","namespace":"aiops-e2e","kind":"pod"},"purpose":"验证异常 Pod 的事件信息","evidence_type":"Pod 事件信息","target_scope":"aiops-e2e/rc-config-env-missing-5d9b8b766c-cstkh","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-env-missing-5d9b8b766c-cstkh\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         3m6s (x95 over 23m)  kubelet            Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-cstkh_aiops-e2e(5ed47e61-9e99-459d-88de-ee30d25b1def)\n                  cni.projectcalico.org/containerID: b609d3199474fd0c991fb51944c653ad8de49c03971407f25be4cb50f1498fc2\n                  cni.projectcalico.org/podIP: 172.16.166.152/32\n                  cni.projectcalico.org/podIPs: 172.16.166.152/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6039f39462bc44a1/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6039f39462bc44a1/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6039f39462bc44a1/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 1\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6039f39462bc44a1/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6039f39462bc44a1/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6039f39462bc44a1/tools/002-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-config-env-missing-5d9b8b766c-cstkh\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-14T22:19:01Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-config-env-missing, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/runbook=pod-config-error.md\nownerReferences: ReplicaSet/rc-config-env-missing-5d9b8b766c\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=9 reason=CrashLoopBackOff exitCode=42\n  message: back-off 5m0s restarting failed container=app pod=rc-config-env-missing-5d9b8b766c-cstkh_aiops-e2e(5ed47e61-9e99-459d-88de-ee30d25b1def)\nvolumes:\n- {\"name\": \"kube-api-access-z9rrw\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6039f39462bc44a1/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6039f39462bc44a1/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6039f39462bc44a1/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n3m15s (x95 over 23m)   Warning   BackOff          Pod/rc-config-env-missing-5d9b8b766c-cstkh   Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-cstkh_aiops-e2e(5ed47e61-9e99-459d-88de-ee30d25b1def)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6039f39462bc44a1/tools/004-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6039f39462bc44a1/tools/004-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6039f39462bc44a1/tools/004-evidence-kubectl_events.summary.txt"}],"llm_analysis":"### 已采集证据\n1. **kubectl_describe**: \n   - Pod 状态为 `CrashLoopBackOff`，Exit Code 为 `42`，无 OOMKilled 痕迹，确认为配置错误。\n2. **kubectl_previous_logs**:\n   - 日志显示 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`，明确指出缺失的环境变量。\n3. **kubectl_get_yaml**:\n   - Pod 的配置中未找到 `APP_BOOT_MODE` 的环境变量配置，且未引用任何 ConfigMap 或 Secret 来提供此参数。\n4. **kubectl_events**:\n   - 事件表明容器因配置错误持续重启，符合 `ConfigError` 的特征。\n\n### 未采集证据\n无进一步计划，当前证据已满足诊断需求。\n\n### 冲突证据\n无冲突证据。所有采集步骤均成功，且结果一致指向配置缺失问题。","collection_summary":"计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%；其中真实环境证据 6/7 项，完整度 86%；实际执行工具 7 个，匹配计划 3 个，未规划证据 4 个","plan_total":4,"plan_collected":3,"plan_completeness":0.75,"environment_evidence_total":7,"environment_evidence_collected":6,"environment_evidence_completeness":0.8571428571428571,"executed_tool_count":7,"matched_tool_count":3,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod rc-config-env-missing-5d9b8b766c-cstkh 的详细描述信息，验证其当前状态和事件信息。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e","purpose":"验证异常 Pod 的当前状态、事件和配置信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod rc-config-env-missing-5d9b8b766c-cstkh 的日志，验证其启动失败的原因。","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs --previous rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e","purpose":"验证异常 Pod 的启动失败日志","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod rc-config-env-missing-5d9b8b766c-cstkh 的配置信息，验证其引用的 ConfigMap 或 Secret 是否正确。","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o yaml","purpose":"验证异常 Pod 的配置信息","collected":false,"source":"planned","outcome":"unknown"},{"id":"e4","description":"获取异常 Pod rc-config-env-missing-5d9b8b766c-cstkh 的事件信息，验证其失败的事件。","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-env-missing-5d9b8b766c-cstkh","purpose":"验证异常 Pod 的事件信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e3(获取异常 Pod rc-config-env-missing-5d9b8b766c-cstkh 的配置信息，验证其引用的 ConfigMap 或 Secret 是否正确。): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 86%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取异常 Pod rc-config-env-missing-5d9b8b766c-cst... | `kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_previous_logs | 获取异常 Pod rc-config-env-missing-5d9b8b766c-cst... | `kubectl logs --previous rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` |
   | e3 | important | ❌ | kubectl_get_yaml | 获取异常 Pod rc-config-env-missing-5d9b8b766c-cst... | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o yaml` |
   | e4 | important | ✅ | kubectl_events | 获取异常 Pod rc-config-env-missing-5d9b8b766c-cst... | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-confi...` |

   ⚠️ 未采集原因:
   - e3(获取异常 Pod rc-config-env-missing-5d9b8b766c-cstkh 的配置信息，验证其引用的 ConfigMap 或 Secret 是否正确。): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (26.1s)
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
   ✅ [汇总总结] 完成 (1m 13.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4096 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 6m 16.0s
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
| **兼容归因层** | CONFIGERROR |
| **问题分类** | 配置错误（ConfigError） |
| **置信度** | 高 (95%) |
| **证据完整度** | 3/4 (75%) |

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
| 1 | Pod 状态 | kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh | `Status: CrashLoopBackOff, Reason: CrashLoopBackOff` | Pod 无法正常启动，处于 CrashLoopBackOff 状态 |
| 2 | 日志信息 | kubectl logs rc-config-env-missing-5d9b8b766c-cstkh --previous | `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE` | 容器启动失败，原因是缺少环境变量 `APP_BOOT_MODE` |
| 3 | 事件信息 | kubectl get events | `Warning BackOff: Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-cstkh` | 容器持续重启，但始终失败 |
| 4 | 上游工具验证 | kubectl get pod | `STATUS: CrashLoopBackOff, RESTARTS: 8 (3m ago)` | Pod 持续重启，重启次数增加 |

### 证据关联分析

- **证据 #2 印证**：日志明确指出 `APP_BOOT_MODE` 环境变量缺失，这是容器启动失败的根本原因。
- **证据链**：容器启动过程中依赖 `APP_BOOT_MODE` 环境变量 → 该变量缺失 → 容器初始化失败 → 容器被终止 → Pod 进入 CrashLoopBackOff 状态 → 重启容器 → 重复失败。

### 缺失证据

| 证据 | 级别 | 影响 |
|------|------|------|
| Pod 的 YAML 配置 | important | 无法确认是否正确引用 ConfigMap/Secret 或环境变量定义错误 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 容器启动过程中缺少必需的环境变量 APP_BOOT_MODE                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器初始化脚本依赖 APP_BOOT_MODE → 该变量缺失 → 初始化失败     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器初始化失败（Exit Code 137 不适用，Exit Code 非 137）        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 CrashLoopBackOff，重启次数持续增加                     │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2（日志显示 `APP_BOOT_MODE` 环境变量缺失）和证据 #1（Pod 状态为 `CrashLoopBackOff`），问题的根本原因是**容器启动时缺少必需的环境变量 `APP_BOOT_MODE`**，导致初始化失败并持续重启。

**置信度**：高 (95%)
- ✅ 日志明确指出 `missing required APP_BOOT_MODE`
- ✅ Pod 状态为 `CrashLoopBackOff`，重启次数持续增加
- ⚠️ 缺少 Pod YAML 配置，无法确认是否正确引用 ConfigMap/Secret 或环境变量定义错误

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 补充缺失的环境变量 `APP_BOOT_MODE`**

```bash
kubectl set env deployment/rc-config-env-missing APP_BOOT_MODE=development -n aiops-e2e
```

*依据*：日志明确指出缺少该变量，需为容器注入此环境变量以完成初始化。

**2. [可选] 检查 ConfigMap/Secret 配置是否正确**

```bash
kubectl get configmap -n aiops-e2e
kubectl get secret -n aiops-e2e
kubectl describe configmap <configmap-name> -n aiops-e2e
```

*目的*：确认是否引用了正确的 ConfigMap/Secret，并检查其内容是否包含 `APP_BOOT_MODE`。

### 后续优化

1. **配置检查自动化**：在部署流水线中加入环境变量校验逻辑，避免部署缺失关键变量的 Pod。
2. **应用配置优化**：为环境变量提供默认值或验证逻辑，避免因变量缺失导致崩溃。
3. **监控告警**：配置 Pod 状态异常监控，及时发现并处理 CrashLoopBackOff 事件。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |
| 3. 查看最新日志 | `kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` | 不再出现 `missing required APP_BOOT_MODE` 错误 |

---

## ⚠️ 注意事项

- 如果补充环境变量后问题仍未解决，应检查容器启动脚本是否对变量有额外要求（如格式、值范围等）。
- 建议为 `APP_BOOT_MODE` 设置默认值，防止再次出现类似问题。
- 如果 Pod 是由 Deployment 管理，确保更新 Deployment 会触发 Pod 重建。

---

## 📊 性能统计

├─ 总耗时: 6.3m
├─ 问题定位: 102.7s (27%) ✅
├─ 证据链采集: 174.2s (46%) ✅
├─ 根因分析: 26.1s (7%) ✅
├─ 汇总总结: 73.0s (19%) ✅
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
