======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: b0414ff383564c47]

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
  "layers": [
    "L4"
  ],
  "layer_name": "ConfigError",
  "confidence": "high",
  "reasoning": "Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，并且日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，表明这是一个配置错误问题。此问题归类为 L4 层，与应用配置或启动相关的错误有关。",
  "abnormal_pods": [
    {
      "name": "rc-config-env-missing-5d9b8b766c-cstkh",
      "namespace": "aiops-e2e",
      "status": "CrashLoopBackOff",
      "restarts": "9 (4m43s ago)",
      "age": "25m",
      "ip": "172.16.166.152",
      "node": "node1"
    }
  ],
  "abnormal_groups": [
    {
      "type": "ConfigError",
      "pods": [
        "rc-config-env-missing-5d9b8b766c-cstkh"
      ]
    }
  ],
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "ConfigError",
  "status_category": "CrashLoopBackOff",
  "key_entities": [
    "rc-config-env-missing-5d9b8b766c-cstkh",
    "APP_BOOT_MODE",
    "ConfigError",
    "CrashLoopBackOff"
  ],
  "possible_scenarios": [
    "Pod 配置错误导致容器启动失败。",
    "缺失的环境变量 APP_BOOT_MODE 导致配置校验失败。",
    "应用在启动前无法完成配置解析，导致容器崩溃。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (2m 20.3s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'Pod 配置错误导致容器启动失败。', 'probability': 'high', 'reason': '日志中显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，表明配置错误导致启动失败。'}, {'scenario': '缺失的环境变量 APP_BOOT_MODE 导致配置校验失败。', 'probability': 'high', 'reason': '日志中明确指出缺失的环境变量 APP_BOOT_MODE 是导致问题的原因。'}, {'scenario': '应用在启动前无法完成配置解析，导致容器崩溃。', 'probability': 'high', 'reason': 'Pod 状态为 CrashLoopBackOff，且日志中显示配置解析失败，表明容器崩溃。'}]
   entities=[{"type": "Pod", "name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e"}, {"type": "ConfigError", "name": "ConfigError", "namespace": ""}, {"type": "PodStatus", "name": "CrashLoopBackOff", "namespace": ""}]
   reasoning=Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，并且日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，表明这是一个配置错误问题。此问题归类为 L4 层，与应用配置或启动相关的错误有关。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.5, "reasoning": "Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，并且日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，表明这是一个配置错误问题。此问题归类为 L4 层，与应用配置或启动相关的错误有关。", "abnormal_pods": [{"name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "CrashLoopBackOff", "key_entities": [{"type": "Pod", "name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e"}, {"type": "ConfigError", "name": "ConfigError", "namespace": ""}, {"type": "PodStatus", "name": "CrashLoopBackOff", "namespace": ""}], "possible_scenarios": [{"scenario": "Pod 配置错误导致容器启动失败。", "probability": "high", "reason": "日志中显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，表明配置错误导致启动失败。"}, {"scenario": "缺失的环境变量 APP_BOOT_MODE 导致配置校验失败。", "probability": "high", "reason": "日志中明确指出缺失的环境变量 APP_BOOT_MODE 是导致问题的原因。"}, {"scenario": "应用在启动前无法完成配置解析，导致容器崩溃。", "probability": "high", "reason": "Pod 状态为 CrashLoopBackOff，且日志中显示配置解析失败，表明容器崩溃。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-cstkh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-cstkh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-env-missing-5d9b8b766c-cstkh              0/1     CrashLoopBackOff   9 (4m17s ago)   25m     172.16.166.152   node1    <none>           <none>            app=rc-config-env-missing,pod-template-hash=5d9b8b766c,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/b0414ff383564c47/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/b0414ff383564c47/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/b0414ff383564c47/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-env-missing-5d9b8b766c-cstkh
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Reason:       CrashLoopBackOff
  Warning  BackOff         4m15
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
4m18s (x118 over 29m)   Warning   BackOff          Pod/rc-config-env-missing-5d9b8b766c-cstkh   Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b76
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
   💭 [证据链采集] 已采集证据：
1. **kubectl_describe**: 证实 Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，最近的事件显示容器因错误（Exit Code 42）而重启。
2. **kubectl_events**: 显示 Pod 由于容器启动失败多次重启（Back-off restarting failed container）。
3. **kubectl_previous_logs**: 显示容器崩溃前的日志信息为 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`，表明配置错误导致容器启动失败。
4. **kubectl_get_yaml**: 显示 Pod 的配置信息，包括容器的镜像为 `busybox:1.36`，重启策略为 Always，且容器状态为未就绪（Ready=False）。

未采集证据：
- 无。

冲突证据：
- 无。
   ✅ [证据链采集] 完成 (2m 5.1s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证异常 Pod 的详细描述信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-config-env-missing-5d9b8b766c-cstkh","namespace":"aiops-e2e"},"purpose":"获取 Pod 的详细描述信息，包括事件、状态和配置信息，用于诊断配置错误原因","evidence_type":"Pod 事件/状态/配置信息","target_scope":"aiops-e2e/rc-config-env-missing-5d9b8b766c-cstkh","acceptable_tools":["kubectl_describe","kubectl_get_by_name","kubectl_events","kubectl_previous_logs"],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 的事件信息","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-env-missing-5d9b8b766c-cstkh","tool_args":{"kind":"Event","namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-config-env-missing-5d9b8b766c-cstkh"},"purpose":"获取与异常 Pod 相关的事件信息，分析配置错误的具体原因","evidence_type":"Pod 事件信息","target_scope":"aiops-e2e/rc-config-env-missing-5d9b8b766c-cstkh","acceptable_tools":["kubectl_events","kubectl_get_by_name","kubectl_describe"],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod 的前一次容器日志","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e --previous","tool_args":{"kind":"Pod","name":"rc-config-env-missing-5d9b8b766c-cstkh","namespace":"aiops-e2e","container":""},"purpose":"获取异常 Pod 的前一次容器日志，验证配置错误的具体原因","evidence_type":"Pod 日志信息","target_scope":"aiops-e2e/rc-config-env-missing-5d9b8b766c-cstkh","acceptable_tools":["kubectl_previous_logs","kubectl_logs","kubectl_logs_grep"],"counts_for_completeness":true},{"id":"e4","description":"获取异常 Pod 的配置信息","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-config-env-missing-5d9b8b766c-cstkh","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"获取异常 Pod 的配置信息，验证配置错误的具体原因","evidence_type":"Pod 配置信息","target_scope":"aiops-e2e/rc-config-env-missing-5d9b8b766c-cstkh","acceptable_tools":["kubectl_get_yaml","kubectl_get_by_name"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-env-missing-5d9b8b766c-cstkh\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         4m15s (x118 over 29m)  kubelet            Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-cstkh_aiops-e2e(5ed47e61-9e99-459d-88de-ee30d25b1def)\n                  cni.projectcalico.org/containerID: b609d3199474fd0c991fb51944c653ad8de49c03971407f25be4cb50f1498fc2\n                  cni.projectcalico.org/podIP: 172.16.166.152/32\n                  cni.projectcalico.org/podIPs: 172.16.166.152/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b0414ff383564c47/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b0414ff383564c47/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b0414ff383564c47/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n4m18s (x118 over 29m)   Warning   BackOff          Pod/rc-config-env-missing-5d9b8b766c-cstkh   Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-cstkh_aiops-e2e(5ed47e61-9e99-459d-88de-ee30d25b1def)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b0414ff383564c47/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b0414ff383564c47/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b0414ff383564c47/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 1\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b0414ff383564c47/tools/003-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b0414ff383564c47/tools/003-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b0414ff383564c47/tools/003-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-config-env-missing-5d9b8b766c-cstkh\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-14T22:19:01Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-config-env-missing, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/runbook=pod-config-error.md\nownerReferences: ReplicaSet/rc-config-env-missing-5d9b8b766c\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=10 reason=CrashLoopBackOff exitCode=42\n  message: back-off 5m0s restarting failed container=app pod=rc-config-env-missing-5d9b8b766c-cstkh_aiops-e2e(5ed47e61-9e99-459d-88de-ee30d25b1def)\nvolumes:\n- {\"name\": \"kube-api-access-z9rrw\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b0414ff383564c47/tools/004-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b0414ff383564c47/tools/004-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b0414ff383564c47/tools/004-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"已采集证据：\n1. **kubectl_describe**: 证实 Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，最近的事件显示容器因错误（Exit Code 42）而重启。\n2. **kubectl_events**: 显示 Pod 由于容器启动失败多次重启（Back-off restarting failed container）。\n3. **kubectl_previous_logs**: 显示容器崩溃前的日志信息为 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`，表明配置错误导致容器启动失败。\n4. **kubectl_get_yaml**: 显示 Pod 的配置信息，包括容器的镜像为 `busybox:1.36`，重启策略为 Always，且容器状态为未就绪（Ready=False）。\n\n未采集证据：\n- 无。\n\n冲突证据：\n- 无。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 7 个，匹配计划 4 个，未规划证据 3 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":7,"matched_tool_count":4,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1","description":"验证异常 Pod 的详细描述信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e","purpose":"获取 Pod 的详细描述信息，包括事件、状态和配置信息，用于诊断配置错误原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 的事件信息","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-env-missing-5d9b8b766c-cstkh","purpose":"获取与异常 Pod 相关的事件信息，分析配置错误的具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod 的前一次容器日志","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e --previous","purpose":"获取异常 Pod 的前一次容器日志，验证配置错误的具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"获取异常 Pod 的配置信息","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o yaml","purpose":"获取异常 Pod 的配置信息，验证配置错误的具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证异常 Pod 的详细描述信息 | `kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_events | 获取异常 Pod 的事件信息 | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-confi...` |
   | e3 | important | ✅ | kubectl_previous_logs | 获取异常 Pod 的前一次容器日志 | `kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e --previous` |
   | e4 | important | ✅ | kubectl_get_yaml | 获取异常 Pod 的配置信息 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o yaml` |

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (11.7s)
   📤 → 下游数据: root_cause=Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，表明这是一个配置错误问题。容器因缺少 APP_BOOT_MODE 环境变量而崩溃，导致 Kubernetes 不断重启容器。
   confidence=90%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [], "causal_chain": {}, "root_cause": "Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，表明这是一个配置错误问题。容器因缺少 APP_BOOT_MODE 环境变量而崩溃，导致 Kubernetes 不断重启容器。", "root_cause_summary": "Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，表明这是一个配置错误问题。容器因缺少 APP_BOOT_MODE 环境变量而崩溃，导致 Kubernetes 不断重启容器。", "confidence": 0.9, "confidence_reason": "", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [], "limitations": "", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，表明这是一个配置错误问题。容器因缺少 AP...
   置信度: 90%

📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 33.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4234 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 6m 10.8s
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
| **兼容归因层** | L4 - 应用配置或启动错误 |
| **问题分类** | ConfigError（配置缺失） |
| **置信度** | 高 (90%) |
| **证据完整度** | 4/4 (100%) |

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
| 1 | Pod 状态 | `kubectl get pod -n aiops-e2e` | `STATUS: CrashLoopBackOff, RESTARTS: 9` | Pod 持续重启，表明容器启动失败 |
| 2 | 日志 | `kubectl logs <pod> -n aiops-e2e --previous` | `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE` | 明确指出配置缺失 |
| 3 | 事件 | `kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` | `Reason: CrashLoopBackOff` | Kubernetes 检测到容器启动失败，进入重启循环 |
| 4 | Pod 配置 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o yaml` | `deletionTimestamp: <absent>` | Pod 未被标记为删除，但状态异常 |
| 5 | 事件重复 | `kubectl describe pod` 事件 | `Warning BackOff Pod/rc-config-env-missing-5d9b8b766c-cstkh Back-off restarting failed container app in pod` | 容器持续失败，Kubernetes 限制重启频率 |
| 6 | Runbook 匹配 | `fetch_runbook` | 匹配 `pod-config-error.md` | 表明这是一个典型的配置错误场景 |
| 7 | Pod 详细信息 | `kubectl describe pod` | `node: node1/10.2.0.49, status: Running` | Pod 已被调度，但容器无法正常运行 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 `CrashLoopBackOff`，日志显示 `missing required APP_BOOT_MODE` → 容器因缺少环境变量崩溃
- **证据链**：容器缺少 `APP_BOOT_MODE` → 应用启动失败 → Kubernetes 重启容器 → 持续失败 → Pod 处于 `CrashLoopBackOff` 状态

### 缺失证据（无）

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 应用启动时缺少必须的环境变量 APP_BOOT_MODE                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 应用启动脚本依赖 APP_BOOT_MODE，但该变量未注入                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器因启动失败退出（日志中 L4_CONFIG_BOOTSTRAP_FAIL）          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CrashLoopBackOff，不断重启                          │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2 (日志 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`) 和证据 #1 (Pod 状态 `CrashLoopBackOff`)，问题的根本原因是**容器缺少必须的环境变量 `APP_BOOT_MODE`**，导致应用启动失败，Kubernetes 无法成功启动容器。

**置信度**：高 (90%)
- ✅ 日志直接指出 `APP_BOOT_MODE` 缺失
- ✅ Pod 状态为 `CrashLoopBackOff`，表明容器不断失败重启
- ✅ 事件记录显示 `Back-off restarting failed container`

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 为 Pod 注入缺失的环境变量 `APP_BOOT_MODE`**

```bash
kubectl set env deployment/<deployment_name> -n aiops-e2e APP_BOOT_MODE=dev
```

*依据*：日志中明确指出缺少 `APP_BOOT_MODE`，注入默认值 `dev` 可尝试恢复启动

**2. [可选] 验证 Pod 是否成功启动**

```bash
kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e
```

*目的*：确认 Pod 是否已恢复正常状态

**3. [可选] 检查 Deployment 的环境变量配置**

```bash
kubectl get deployment <deployment_name> -n aiops-e2e -o yaml
```

*目的*：确认 `APP_BOOT_MODE` 是否已正确配置

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` | STATUS: Running |
| 2. 确认重启次数 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 0 或不再增加 |
| 3. 查看容器日志 | `kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` | 应用启动成功，无错误日志 |

---

## ⚠️ 注意事项

- 如果 `APP_BOOT_MODE` 需要动态注入（如来自 ConfigMap 或 Secret），请检查相关对象是否已正确创建并绑定到 Pod
- 如果问题仍然存在，考虑检查应用的启动脚本是否对 `APP_BOOT_MODE` 有额外校验逻辑
- 建议对所有依赖环境变量的应用进行统一的环境变量注入校验，避免类似问题再次发生

---

## 📊 性能统计

├─ 总耗时: 6.2m
├─ 问题定位: 140.3s (38%) ✅
├─ 证据链采集: 125.1s (34%) ✅
├─ 根因分析: 11.7s (3%) ✅
├─ 汇总总结: 93.7s (25%) ✅
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
