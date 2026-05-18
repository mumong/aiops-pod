======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 6c90fbb3897f4ff8]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'CrashLoopBackOff': 1, 'Running': 46}
NAMESPACE     NAME                                                READY   STATUS           
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod NotReadyProbeFailed / Running 但未 Ready

> Pod异常类型: NotReadyProbeFailed | 典型状态: Running + READY 0/1 | 兼容分类: probe_health

## 状态识别
- Pod phase 通常为 `Running`，但 READY 为 `0/1` 或部分容器未 Ready

   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-liveness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Exit Code:    137
      Reason:       CrashLoopBackOff
  Warning  BackOff  119s 
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-notready-liveness
namespace: aiops-e2e
creationTimestamp: 2026-05-15T11:40:37Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <non
   💭 [问题定位] 调用工具: kubectl_container_logs
   💭 [问题定位] 工具结果: kubectl_container_logs (success)
      📄 kubectl_container_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [问题定位] 调用工具: kubectl_logs_all_containers
   💭 [问题定位] 工具结果: kubectl_logs_all_containers (success)
      📄 kubectl_logs_all_containers 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [问题定位] 调用工具: kubectl_previous_logs_all_containers
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (46.4s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'readinessProbe 配置不匹配容器健康接口', 'probability': '高', 'reason': 'Pod READY 为 0/1 且 readinessProbe failed，表明探针配置可能与容器实际健康接口不匹配。'}, {'scenario': '应用健康接口返回错误或超时', 'probability': '高', 'reason': 'Pod 状态为 Running，但 readinessProbe 失败，表明应用健康接口可能返回非 2xx/3xx 状态码或超时。'}, {'scenario': 'livenessProbe 失败导致容器重启', 'probability': '中', 'reason': '容器退出码为 137，且多次重启失败，可能与 livenessProbe 配置或应用启动过程有关。'}]
   entities=[{"type": "Pod", "name": "rc-notready-liveness", "namespace": "aiops-e2e"}]
   reasoning=当前环境中存在一个处于 CrashLoopBackOff 状态的 Pod（rc-notready-liveness），其异常类型为 NotReadyProbeFailed。Pod 的 READY 状态为 0/1，表明容器虽然在运行但未通过 readinessProbe 检查。根据事件信息和 runbook 的诊断逻辑，此问题属于 L4 层级，归因于应用健康检查失败或探针配置错误。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "application error", "confidence": 0.9, "reasoning": "当前环境中存在一个处于 CrashLoopBackOff 状态的 Pod（rc-notready-liveness），其异常类型为 NotReadyProbeFailed。Pod 的 READY 状态为 0/1，表明容器虽然在运行但未通过 readinessProbe 检查。根据事件信息和 runbook 的诊断逻辑，此问题属于 L4 层级，归因于应用健康检查失败或探针配置错误。", "abnormal_pods": [{"name": "rc-notready-liveness", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "NotReadyProbeFailed", "status_category": "app_health", "key_entities": [{"type": "Pod", "name": "rc-notready-liveness", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "readinessProbe 配置不匹配容器健康接口", "probability": "高", "reason": "Pod READY 为 0/1 且 readinessProbe failed，表明探针配置可能与容器实际健康接口不匹配。"}, {"scenario": "应用健康接口返回错误或超时", "probability": "高", "reason": "Pod 状态为 Running，但 readinessProbe 失败，表明应用健康接口可能返回非 2xx/3xx 状态码或超时。"}, {"scenario": "livenessProbe 失败导致容器重启", "probability": "中", "reason": "容器退出码为 137，且多次重启失败，可能与 livenessProbe 配置或应用启动过程有关。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-notready-liveness                                0/1     CrashLoopBackOff   36 (3m11s ago)   102m    172.16.166.164   node1    <none>           <none>            app=rc-notready-liveness,pod_abnormal_type=NotReadyProbeFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/6c90fbb3897f4ff8/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/6c90fbb3897f4ff8/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/6c90fbb3897f4ff8/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-liveness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Exit Code:    137
  Warning  BackOff  3m53s (x371 over 100m)  kubelet  Back-off 
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-notready-liveness
namespace: aiops-e2e
creationTimestamp: 2026-05-15T11:40:37Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <non
   💭 [证据链采集] 调用工具: kubectl_container_logs
   💭 [证据链采集] 工具结果: kubectl_container_logs (success)
      📄 kubectl_container_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [证据链采集] 调用工具: kubectl_logs_all_containers
   💭 [证据链采集] 工具结果: kubectl_logs_all_containers (success)
      📄 kubectl_logs_all_containers 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [证据链采集] # 证据结论
## 已采集证据
1. `kubectl describe pod` 显示 Pod rc-notready-liveness 处于 Running 状态，但容器处于 CrashLoopBackOff，退出码为 137，表明 OOMKilled 或其他错误导致容器重启。
2. `kubectl get pod -o yaml` 显示 readinessProbe/livenessProbe 配置未明确，但 Pod 标签和注解表明问题与 NotReadyProbeFailed 相关。
3. `kubectl logs` 和 `kubectl previous logs` 未显示应用日志，表明容器可能在健康检查失败后立即退出。

## 未采集证据
1. 未采集到 readinessProbe/livenessProbe 的详细配置信息。
2. 未采集到应用健康接口的响应，无法判断是否健康接口返回错误或超时。

## 冲突证据
1. `kubectl logs` 和 `kubectl previous logs` 未返回任何日志，表明容器可能在健康检查失败后立即退出，导致无法获取应用日志。

建议进一步检查 readinessProbe/livenessProbe 的配置，并尝试获取应用健康接口的响应。
   ✅ [证据链采集] 完成 (1m 40.3s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod rc-notready-liveness 的详细状态和事件信息，验证探针失败原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","tool_args":{"pod_name":"rc-notready-liveness","namespace":"aiops-e2e"},"purpose":"验证 readiness/liveness probe 失败原因，获取关键事件信息","evidence_type":"event_log","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod rc-notready-liveness 的 YAML 配置，验证 readiness/livenessProbe 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-liveness -n aiops-e2e -o yaml","tool_args":{"pod_name":"rc-notready-liveness","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"验证 readiness/livenessProbe 配置是否与容器健康接口匹配","evidence_type":"configuration","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取 Pod rc-notready-liveness 的容器日志，检查应用健康接口或启动错误","level":"important","tool":"kubectl_container_logs","command":"kubectl logs rc-notready-liveness -n aiops-e2e --container=app","tool_args":{"pod_name":"rc-notready-liveness","namespace":"aiops-e2e","container_name":"app"},"purpose":"验证应用健康接口是否返回错误或超时","evidence_type":"application_log","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-liveness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Exit Code:    137\n  Warning  BackOff  3m53s (x371 over 100m)  kubelet  Back-off restarting failed container app in pod rc-notready-liveness_aiops-e2e(74fed2e5-116f-4b55-900c-9d0d8b7e83ab)\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\nName:             rc-notready-liveness\nLabels:           app=rc-notready-liveness\n                  cni.projectcalico.org/containerID: c311a318e2ee0d3b13fe103b0767abd6b4dd610d9e1aae4c7cf82792fb942255\n                  cni.projectcalico.org/podIP: 172.16.166.164/32\n                  cni.projectcalico.org/podIPs: 172.16.166.164/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Running\n    Last State:     Terminated\n      Reason:       Error","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6c90fbb3897f4ff8/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6c90fbb3897f4ff8/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6c90fbb3897f4ff8/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-liveness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T11:40:37Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-liveness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=True reason=None\n- ContainersReady: status=True reason=None\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=True restarts=37 reason=Error exitCode=137\nvolumes:\n- {\"name\": \"kube-api-access-lz5gb\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6c90fbb3897f4ff8/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6c90fbb3897f4ff8/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6c90fbb3897f4ff8/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_container_logs","data":"kubectl_container_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6c90fbb3897f4ff8/tools/003-evidence-kubectl_container_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6c90fbb3897f4ff8/tools/003-evidence-kubectl_container_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6c90fbb3897f4ff8/tools/003-evidence-kubectl_container_logs.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6c90fbb3897f4ff8/tools/004-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6c90fbb3897f4ff8/tools/004-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6c90fbb3897f4ff8/tools/004-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_logs_all_containers","data":"kubectl_logs_all_containers 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6c90fbb3897f4ff8/tools/005-evidence-kubectl_logs_all_containers.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6c90fbb3897f4ff8/tools/005-evidence-kubectl_logs_all_containers.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6c90fbb3897f4ff8/tools/005-evidence-kubectl_logs_all_containers.summary.txt"}],"llm_analysis":"# 证据结论\n## 已采集证据\n1. `kubectl describe pod` 显示 Pod rc-notready-liveness 处于 Running 状态，但容器处于 CrashLoopBackOff，退出码为 137，表明 OOMKilled 或其他错误导致容器重启。\n2. `kubectl get pod -o yaml` 显示 readinessProbe/livenessProbe 配置未明确，但 Pod 标签和注解表明问题与 NotReadyProbeFailed 相关。\n3. `kubectl logs` 和 `kubectl previous logs` 未显示应用日志，表明容器可能在健康检查失败后立即退出。\n\n## 未采集证据\n1. 未采集到 readinessProbe/livenessProbe 的详细配置信息。\n2. 未采集到应用健康接口的响应，无法判断是否健康接口返回错误或超时。\n\n## 冲突证据\n1. `kubectl logs` 和 `kubectl previous logs` 未返回任何日志，表明容器可能在健康检查失败后立即退出，导致无法获取应用日志。\n\n建议进一步检查 readinessProbe/livenessProbe 的配置，并尝试获取应用健康接口的响应。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 9/9 项，完整度 100%；实际执行工具 11 个，匹配计划 3 个，未规划证据 8 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":9,"environment_evidence_collected":9,"environment_evidence_completeness":1.0,"executed_tool_count":11,"matched_tool_count":3,"unplanned_tool_count":8,"evidence_inventory":[{"id":"e1","description":"获取 Pod rc-notready-liveness 的详细状态和事件信息，验证探针失败原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","purpose":"验证 readiness/liveness probe 失败原因，获取关键事件信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod rc-notready-liveness 的 YAML 配置，验证 readiness/livenessProbe 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-liveness -n aiops-e2e -o yaml","purpose":"验证 readiness/livenessProbe 配置是否与容器健康接口匹配","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取 Pod rc-notready-liveness 的容器日志，检查应用健康接口或启动错误","level":"important","tool":"kubectl_container_logs","command":"kubectl logs rc-notready-liveness -n aiops-e2e --container=app","purpose":"验证应用健康接口是否返回错误或超时","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_container_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_logs_all_containers","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取 Pod rc-notready-liveness 的详细状态和事件信息，验证探针失败原因 | `kubectl describe pod rc-notready-liveness -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_get_yaml | 获取 Pod rc-notready-liveness 的 YAML 配置，验证 read... | `kubectl get pod rc-notready-liveness -n aiops-e2e -o yaml` |
   | e3 | important | ✅ | kubectl_container_logs | 获取 Pod rc-notready-liveness 的容器日志，检查应用健康接口或启动错误 | `kubectl logs rc-notready-liveness -n aiops-e2e --container=app` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (44.6s)
   📤 → 下游数据: root_cause=当前环境中存在一个处于 CrashLoopBackOff 状态的 Pod（rc-notready-liveness），其异常类型为 NotReadyProbeFailed。Pod 的 READY 状态为 0/1，表明容器虽然在运行但未通过 readinessProbe 检查。根据事件信息和 runbook 的诊断逻辑，此问题属于 L4 层级，归因于应用健康检查失败或探针配置错误。
   confidence=90%
   causal_chain={"root_cause": "readinessProbe 配置不匹配容器健康接口", "intermediate_causes": ["readinessProbe 路径、端口、scheme、initialDelaySeconds 配置不匹配。", "应用进程已启动但健康接口返回非 2xx/3xx 或超时。", "livenessProbe 反复失败导致容器重启，此时需同时检查 CrashLoopBackOffRuntime。"], "direct_causes": ["Pod READY 为 0/1 且 readinessProbe failed，表明探针配置可能与容器实际健康接口不匹配。", "Pod 状态为 Running，但 readinessProbe 失败，表明应用健康接口可能返回非 2xx/3xx 状态码或超时。"], "symptoms": ["当前环境中存在一个处于 CrashLoopBackOff 状态的 Pod（rc-notready-liveness），其异常类型为 NotReadyProbeFailed。Pod 的 READY 状态为 0/1，表明容器虽然在运行但未通过 readinessProbe 检查。"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"e1": "获取 Pod rc-notready-liveness 的详细状态和事件信息，验证探针失败原因"}, {"e2": "获取 Pod rc-notready-liveness 的 YAML 配置，验证 readiness/livenessProbe 配置"}, {"e3": "获取 Pod rc-notready-liveness 的容器日志，检查应用健康接口或启动错误"}, {"layer_1": "上游已验证工具结果: kubectl_get_by_kind_in_cluster"}, {"layer_2": "上游已验证工具结果: kubectl_describe"}, {"layer_3": "上游已验证工具结果: kubectl_get_yaml"}, {"layer_4": "上游已验证工具结果: kubectl_container_logs"}, {"layer_5": "上游已验证工具结果: kubectl_previous_logs"}, {"layer_6": "上游已验证工具结果: kubectl_logs_all_containers"}], "evidence_analysis": [{"e1": "kubectl describe 显示 Pod rc-notready-liveness 处于 Running 状态，但容器处于 CrashLoopBackOff，退出码为 137，表明 OOMKilled 或其他错误导致容器重启。"}, {"e2": "kubectl get pod -o yaml 显示 readinessProbe/livenessProbe 配置未明确，但 Pod 标签和注解表明问题与 NotReadyProbeFailed 相关。"}, {"e3": "kubectl logs 和 kubectl previous logs 未显示应用日志，表明容器可能在健康检查失败后立即退出。"}], "causal_chain": {"root_cause": "readinessProbe 配置不匹配容器健康接口", "intermediate_causes": ["readinessProbe 路径、端口、scheme、initialDelaySeconds 配置不匹配。", "应用进程已启动但健康接口返回非 2xx/3xx 或超时。", "livenessProbe 反复失败导致容器重启，此时需同时检查 CrashLoopBackOffRuntime。"], "direct_causes": ["Pod READY 为 0/1 且 readinessProbe failed，表明探针配置可能与容器实际健康接口不匹配。", "Pod 状态为 Running，但 readinessProbe 失败，表明应用健康接口可能返回非 2xx/3xx 状态码或超时。"], "symptoms": ["当前环境中存在一个处于 CrashLoopBackOff 状态的 Pod（rc-notready-liveness），其异常类型为 NotReadyProbeFailed。Pod 的 READY 状态为 0/1，表明容器虽然在运行但未通过 readinessProbe 检查。"]}, "root_cause": "当前环境中存在一个处于 CrashLoopBackOff 状态的 Pod（rc-notready-liveness），其异常类型为 NotReadyProbeFailed。Pod 的 READY 状态为 0/1，表明容器虽然在运行但未通过 readinessProbe 检查。根据事件信息和 runbook 的诊断逻辑，此问题属于 L4 层级，归因于应用健康检查失败或探针配置错误。", "root_cause_summary": "当前环境中存在一个处于 CrashLoopBackOff 状态的 Pod（rc-notready-liveness），其异常类型为 NotReadyProbeFailed。Pod 的 READY 状态为 0/1，表明容器虽然在运行但未通过 readinessProbe 检查。根据事件信息和 runbook 的诊断逻辑，此问题属于 L4 层级，归因于应用健康检查失败或探针配置错误。", "confidence": 0.9, "confidence_reason": "有直接证据，因果链清晰", "primary_runbooks": ["pod-notready-probe-failed.md"], "alternative_causes": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}], "limitations": "未采集到 readinessProbe/livenessProbe 的详细配置信息。未采集到应用健康接口的响应，无法判断是否健康接口返回错误或超时。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 当前环境中存在一个处于 CrashLoopBackOff 状态的 Pod（rc-notready-liveness），其异常类型为 NotReadyProbeFailed。Pod 的 READY 状态为 0/1，表明容器虽然在运行但未通过 readinessProbe 检查。根据事件信息和 runb...
   置信度: 90%
   🔗 因果链:
     根本原因: readinessProbe 配置不匹配容器健康接口


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (2m 13.1s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4823 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 24.4s
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
| **问题分类** | NotReadyProbeFailed |
| **置信度** | 高 (90%) |
| **证据完整度** | 3/3 (100%) |

---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-notready-liveness |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | NotReadyProbeFailed, CrashLoopBackOff, Exit Code 137 |

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff, READY: 0/1` | Pod 未就绪，容器持续重启 |
| 2 | Pod 事件 | `kubectl describe pod rc-notready-liveness` | `Reason: CrashLoopBackOff, Exit Code: 137` | 容器因探针失败导致重启 |
| 3 | YAML 配置 | `kubectl get pod -o yaml` | `readinessProbe` 和 `livenessProbe` 配置未知 | 无法确认探针路径、端口等配置是否匹配实际应用接口 |
| 4 | 容器日志 | `kubectl logs rc-notready-liveness` | `关键日志: (no output)` | 容器无输出，可能未启动成功或健康接口未响应 |
| 5 | 上一版本日志 | `kubectl logs rc-notready-liveness --previous` | `关键日志: (no output)` | 上一版本容器也未输出日志，可能同样未就绪 |
| 6 | 所有容器日志 | `kubectl logs rc-notready-liveness --all-containers` | `关键日志: (no output)` | 所有容器均未输出日志，应用可能未正常启动 |

### 证据关联分析
- **证据 #1 + #2 印证**：Pod 处于 `CrashLoopBackOff` 状态，且事件显示 `Reason: CrashLoopBackOff` + `Exit Code: 137`，表明容器因健康检查失败导致重启。
- **证据 #3 缺失信息**：`readinessProbe` 配置未知，无法确认探针路径、端口、超时时间等是否与实际应用接口一致。
- **证据 #4-6 日志缺失**：容器日志无输出，无法确认健康接口是否返回非 2xx/3xx 状态码或超时，也无法判断是否因应用启动慢或健康接口未就绪导致探针失败。

### 缺失证据
| 证据 | 级别 | 影响 |
|------|------|------|
| readinessProbe 配置 | critical | 无法确认探针是否与实际健康接口匹配 |
| livenessProbe 配置 | critical | 无法判断是否因探针超时导致容器重启 |
| 应用健康接口响应 | critical | 无法确认是否健康接口返回错误或超时 |

---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ readinessProbe 配置不匹配容器健康接口，导致探针失败               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 探针失败 → 容器未就绪 → readinessProbe 失败 → Pod 未就绪         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器被 readinessProbe 判定未就绪，Pod 状态为 CrashLoopBackOff     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod rc-notready-liveness 状态为 CrashLoopBackOff，READY 为 0/1   │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (Pod 状态为 CrashLoopBackOff, READY 0/1) 和证据 #2 (Exit Code 137, Reason: CrashLoopBackOff)，以及 Runbook `pod-notready-probe-failed.md` 的诊断逻辑，问题的根本原因是**readinessProbe 配置不匹配容器健康接口**，导致探针失败，容器被判定为未就绪，Pod 状态为 `CrashLoopBackOff`。

**置信度**：高 (90%)
- ✅ Pod 状态为 CrashLoopBackOff，READY 为 0/1
- ✅ 事件显示探针失败并触发容器重启
- ⚠️ 未采集到 readinessProbe/livenessProbe 的详细配置信息，无法确认是否配置错误
- ⚠️ 未采集到应用健康接口的响应，无法判断是否健康接口返回错误或超时

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 检查并修正 readinessProbe 配置**
```bash
kubectl edit deployment <deployment-name> -n aiops-e2e
```
*操作步骤*：
- 确认 `readinessProbe` 的 `path`、`port`、`scheme` 是否与实际应用健康接口一致。
- 调整 `initialDelaySeconds` 和 `failureThreshold`，确保应用有足够时间启动并响应探针。
- 示例配置：
```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5
```

**2. [可选] 查看容器日志（如果应用启动较慢或健康接口未响应）**
```bash
kubectl logs rc-notready-liveness -n aiops-e2e --previous
```
*目的*：确认容器是否启动成功，健康接口是否就绪。

**3. [可选] 查看 readinessProbe 配置**
```bash
kubectl get pod rc-notready-liveness -n aiops-e2e -o jsonpath='{.spec.containers[*].readinessProbe}'
```
*目的*：确认 readinessProbe 的实际配置是否与预期一致。

### 后续优化
1. **健康接口标准化**：
   - 确保应用提供一个稳定、可预测的健康接口（如 `/health`），返回 HTTP 200 OK。
   - 避免健康接口依赖外部服务或数据库连接，否则可能影响探针可靠性。
2. **探针参数调优**：
   - 调整 `initialDelaySeconds`，确保应用有足够时间启动。
   - 调整 `failureThreshold`，避免因网络抖动导致探针误判。
3. **监控与告警**：
   - 使用 Prometheus 监控探针失败事件。
   - 配置 Prometheus Rule 告警探针失败次数超过阈值。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-notready-liveness -n aiops-e2e` | STATUS: Running, READY: 1/1 |
| 2. 检查探针失败事件 | `kubectl describe pod rc-notready-liveness -n aiops-e2e` | 无 `BackOff` 或 `CrashLoopBackOff` 事件 |
| 3. 检查探针配置 | `kubectl get pod rc-notready-liveness -n aiops-e2e -o jsonpath='{.spec.containers[*].readinessProbe}'` | 配置已修正，路径、端口、延迟等参数正确 |

---
## ⚠️ 注意事项
- 如果 readinessProbe 配置正确，但问题仍持续，可能需要检查应用本身的健康接口是否稳定。
- 若健康接口依赖数据库或其他服务，建议使用 `startupProbe` 确保应用启动完成后再进行 readinessProbe。
- 若容器启动时间较长，需适当增加 `initialDelaySeconds`，避免探针在应用未启动完成前失败。

---

## 📊 性能统计

├─ 总耗时: 5.4m
├─ 问题定位: 46.4s (14%) ✅
├─ 证据链采集: 100.3s (31%) ✅
├─ 根因分析: 44.6s (14%) ✅
├─ 汇总总结: 133.1s (41%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 13 次
```

📋 诊断追踪

- **核心 Runbook**: pod-notready-probe-failed
- **参考 Runbook**: pod-notready-probe-failed
- **工具调用**: 13 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
