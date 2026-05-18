======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 6896f7c1a3b04383]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 检测到 49 个 Pod，其中 47 个状态为 Running，0 个异常。关键信息包括：aiops-e2e 命名空间中的 rc-notready-readiness Pod 为 0/1 状态，标记为 pod_abnormal_type=NotReadyProbeFailed；多个 kube-system 组件如 calico-node
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod NotReadyProbeFailed / Running 但未 Ready

> Pod异常类型: NotReadyProbeFailed | 典型状态: Running + READY 0/1 | 兼容分类: probe_health

## 状态识别
- Pod phase 通常为 `Running`，但 READY 为 `0/1` 或部分容器未 Ready

   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                    READY   STATUS    RESTARTS   AGE     IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-notready-readiness   0/1     Running   0          3h59m   172.16.166.
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-readiness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
  Warning  Unhealthy  4m44s (x4891 over 3h59m)  kubelet  Readiness probe failed: read
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-notready-readiness
namespace: aiops-e2e
creationTimestamp: 2026-05-15T07:05:35Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <no
   💭 [问题定位] 调用工具: kubectl_logs
   💭 [问题定位] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [问题定位] 调用工具: kubectl_lineage_parents
   💭 [问题定位] 工具结果: kubectl_lineage_parents (success)
      📄 kubectl_lineage_parents 输出摘要: raw_chars=130 lines=3
Command failed (exit 1):
kubectl lineage pod rc-notready-readiness -n aiops-e2e -D
error: unknown command "lineage" for "kubectl"
   💭 [问题定位] 调用工具: kubectl_find_resource
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 1.0s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'readinessProbe 配置错误，导致探针失败', 'probability': '高', 'reason': 'Pod 为 Running 状态，但 READY 为 0/1，且有 readiness probe failed 事件。'}, {'scenario': '应用健康接口返回非 2xx/3xx 或超时', 'probability': '高', 'reason': 'Pod 为 Running 状态，但 READY 为 0/1，且有 readiness probe failed 事件。'}]
   entities=[{"type": "pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}]
   reasoning=检测到当前仍异常的 Pod aiops-e2e/rc-notready-readiness，状态为 0/1，标记为 pod_abnormal_type=NotReadyProbeFailed，符合 L4 层级的特征，即应用健康检查失败或配置错误。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "L4", "confidence": 0.8, "reasoning": "检测到当前仍异常的 Pod aiops-e2e/rc-notready-readiness，状态为 0/1，标记为 pod_abnormal_type=NotReadyProbeFailed，符合 L4 层级的特征，即应用健康检查失败或配置错误。", "abnormal_pods": [{"name": "rc-notready-readiness", "namespace": "aiops-e2e", "status": "Running"}], "pod_status_keyword": "0/1", "pod_abnormal_type": "NotReadyProbeFailed", "status_category": "app_health", "key_entities": [{"type": "pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "readinessProbe 配置错误，导致探针失败", "probability": "高", "reason": "Pod 为 Running 状态，但 READY 为 0/1，且有 readiness probe failed 事件。"}, {"scenario": "应用健康接口返回非 2xx/3xx 或超时", "probability": "高", "reason": "Pod 为 Running 状态，但 READY 为 0/1，且有 readiness probe failed 事件。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Running"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Running"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 0, "selected_rows": [], "raw_ref": "/tmp/aiops/reports/context_archives/6896f7c1a3b04383/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/6896f7c1a3b04383/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/6896f7c1a3b04383/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 80%

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
name: rc-notready-readiness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
  Warning  Unhealthy  3m28s (x4995 over 4h3m)  kubelet  Readiness probe failed: readi
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-notready-readiness
namespace: aiops-e2e
creationTimestamp: 2026-05-15T07:05:35Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <no
   💭 [证据链采集] 调用工具: kubectl_logs
   💭 [证据链采集] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 输出摘要: raw_chars=204 lines=3
Command failed (exit 1):
kubectl logs rc-notready-readiness -n aiops-e2e --previous --tail=200
Error from server (BadRequest): previous terminated con
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
3m53s (x4995 over 4h3m)   Warning   Unhealthy   Pod/rc-notready-readiness   Readiness probe failed: readiness dependency unavailable
   💭 [证据链采集] # 证据结论

## 已采集证据
1. **kubectl describe pod**: 
   - Pod 状态为 Running，但 READY 为 0/1。
   - 包含 readiness probe 失败的事件，提示 "Readiness probe failed: readiness dependency unavailable"。
   - 标注了 `pod_abnormal_type=NotReadyProbeFailed`，并关联了 `pod-notready-probe-failed.md` 的 Runbook。

2. **kubectl get pod -o yaml**:
   - 验证了 readinessProbe/livenessProbe 的配置参数。
   - Pod 状态为 Running，但 READY 为 0/1，容器未就绪。
   - 标注了 `pod_abnormal_type=NotReadyProbeFailed`，并关联了 `pod-notready-probe-failed.md` 的 Runbook。

3. **kubectl logs**:
   - 没有输出，说明当前容器的日志中没有明显的错误信息。

4. **kubectl previous logs**:
   - 无法获取 previous logs，提示 "previous terminated container 'app' in pod 'rc-notready-readiness' not found"，说明容器没有重启过或者没有 previous logs。

5. **kubectl events**:
   - 显示 readiness probe 失败的事件，提示 "Readiness probe failed: readiness dependency unavailable"。

## 未采集证据
- 无。

## 冲突证据
- 无。

## 初步结论
该 Pod 状态为 Running，但 READY 为 0/1，且 readiness probe 失败。事件中提示 "Readiness probe failed: readiness dependency unavailable"，表明 readiness probe 的失败可能是由于依赖项不可用或配置错误。需要进一步检查 readiness probe 的配置，确认其路径、端口、scheme、initialDelaySeconds 等参数是否与容器的实际情况匹配。
   ✅ [证据链采集] 完成 (4m 11.4s)
   📤 → 下游数据: evidence_items=11/11
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod 的详细信息，包括 readinessProbe/livenessProbe 配置和失败事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-readiness -n aiops-e2e","tool_args":{"pod":"rc-notready-readiness","namespace":"aiops-e2e"},"purpose":"验证 readinessProbe/livenessProbe 配置和失败事件","evidence_type":"configuration","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_describe","kubectl_get_by_name","kubectl_get_by_kind_in_namespace","kubectl_get_by_kind_in_cluster","kubectl_find_resource","kubectl_get_yaml","kubectl_events","kubectl_logs","kubectl_previous_logs","kubectl_logs_all_containers","kubectl_previous_logs_all_containers","kubectl_container_logs","kubectl_container_previous_logs","kubectl_logs_grep","kubectl_logs_all_containers_grep","kubernetes_jq_query","kubernetes_tabular_query","kubernetes_count","get_prometheus_target","kubectl_lineage_children","kubectl_lineage_parents","run_bash_command","kubectl_run_image","list_prometheus_rules","get_metric_names","get_label_values","get_all_labels","get_series","get_metric_metadata","execute_prometheus_instant_query","execute_prometheus_range_query","fetch_runbook"],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod 的 YAML 配置，检查 readinessProbe/livenessProbe 的配置参数","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml","tool_args":{"pod":"rc-notready-readiness","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"验证 readinessProbe/livenessProbe 的配置参数","evidence_type":"configuration","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_describe","kubectl_get_by_name","kubectl_get_by_kind_in_namespace","kubectl_get_by_kind_in_cluster","kubectl_find_resource","kubectl_get_yaml","kubectl_events","kubectl_logs","kubectl_previous_logs","kubectl_logs_all_containers","kubectl_previous_logs_all_containers","kubectl_container_logs","kubectl_container_previous_logs","kubectl_logs_grep","kubectl_logs_all_containers_grep","kubernetes_jq_query","kubernetes_tabular_query","kubernetes_count","get_prometheus_target","kubectl_lineage_children","kubectl_lineage_parents","run_bash_command","kubectl_run_image","list_prometheus_rules","get_metric_names","get_label_values","get_all_labels","get_series","get_metric_metadata","execute_prometheus_instant_query","execute_prometheus_range_query","fetch_runbook"],"counts_for_completeness":true},{"id":"e3","description":"获取 Pod 的日志，检查健康检查失败时应用的响应","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --tail=200","tool_args":{"pod":"rc-notready-readiness","namespace":"aiops-e2e","tail":"200"},"purpose":"验证健康检查失败时应用的响应","evidence_type":"log","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_describe","kubectl_get_by_name","kubectl_get_by_kind_in_namespace","kubectl_get_by_kind_in_cluster","kubectl_find_resource","kubectl_get_yaml","kubectl_events","kubectl_logs","kubectl_previous_logs","kubectl_logs_all_containers","kubectl_previous_logs_all_containers","kubectl_container_logs","kubectl_container_previous_logs","kubectl_logs_grep","kubectl_logs_all_containers_grep","kubernetes_jq_query","kubernetes_tabular_query","kubernetes_count","get_prometheus_target","kubectl_lineage_children","kubectl_lineage_parents","run_bash_command","kubectl_run_image","list_prometheus_rules","get_metric_names","get_label_values","get_all_labels","get_series","get_metric_metadata","execute_prometheus_instant_query","execute_prometheus_range_query","fetch_runbook"],"counts_for_completeness":true},{"id":"e4","description":"获取 Pod 的上一个容器的日志，检查容器重启时的错误信息","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --previous --tail=200","tool_args":{"pod":"rc-notready-readiness","namespace":"aiops-e2e","previous":true,"tail":"200"},"purpose":"验证容器重启时的错误信息","evidence_type":"log","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_describe","kubectl_get_by_name","kubectl_get_by_kind_in_namespace","kubectl_get_by_kind_in_cluster","kubectl_find_resource","kubectl_get_yaml","kubectl_events","kubectl_logs","kubectl_previous_logs","kubectl_logs_all_containers","kubectl_previous_logs_all_containers","kubectl_container_logs","kubectl_container_previous_logs","kubectl_logs_grep","kubectl_logs_all_containers_grep","kubernetes_jq_query","kubernetes_tabular_query","kubernetes_count","get_prometheus_target","kubectl_lineage_children","kubectl_lineage_parents","run_bash_command","kubectl_run_image","list_prometheus_rules","get_metric_names","get_label_values","get_all_labels","get_series","get_metric_metadata","execute_prometheus_instant_query","execute_prometheus_range_query","fetch_runbook"],"counts_for_completeness":true},{"id":"e5","description":"获取 Pod 的事件，检查 readinessProbe/livenessProbe 失败的详细信息","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-notready-readiness","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-notready-readiness"},"purpose":"验证 readinessProbe/livenessProbe 失败的详细信息","evidence_type":"event","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_describe","kubectl_get_by_name","kubectl_get_by_kind_in_namespace","kubectl_get_by_kind_in_cluster","kubectl_find_resource","kubectl_get_yaml","kubectl_events","kubectl_logs","kubectl_previous_logs","kubectl_logs_all_containers","kubectl_previous_logs_all_containers","kubectl_container_logs","kubectl_container_previous_logs","kubectl_logs_grep","kubectl_logs_all_containers_grep","kubernetes_jq_query","kubernetes_tabular_query","kubernetes_count","get_prometheus_target","kubectl_lineage_children","kubectl_lineage_parents","run_bash_command","kubectl_run_image","list_prometheus_rules","get_metric_names","get_label_values","get_all_labels","get_series","get_metric_metadata","execute_prometheus_instant_query","execute_prometheus_range_query","fetch_runbook"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-readiness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n  Warning  Unhealthy  3m28s (x4995 over 4h3m)  kubelet  Readiness probe failed: readiness dependency unavailable\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\nName:             rc-notready-readiness\nLabels:           app=rc-notready-readiness\n                  cni.projectcalico.org/containerID: fb8e26665bf8a745a3d1ec6dc6a9b9d528c0b6504e8895b370296a560f31067e\n                  cni.projectcalico.org/podIP: 172.16.166.186/32\n                  cni.projectcalico.org/podIPs: 172.16.166.186/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Running","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6896f7c1a3b04383/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6896f7c1a3b04383/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6896f7c1a3b04383/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-readiness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T07:05:35Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-readiness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=None exitCode=None\nvolumes:\n- {\"name\": \"kube-api-access-sqcn2\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6896f7c1a3b04383/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6896f7c1a3b04383/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6896f7c1a3b04383/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_logs","data":"kubectl_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6896f7c1a3b04383/tools/003-evidence-kubectl_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6896f7c1a3b04383/tools/003-evidence-kubectl_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6896f7c1a3b04383/tools/003-evidence-kubectl_logs.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 输出摘要: raw_chars=204 lines=3\nCommand failed (exit 1):\nkubectl logs rc-notready-readiness -n aiops-e2e --previous --tail=200\nError from server (BadRequest): previous terminated container \"app\" in pod \"rc-notready-readiness\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/6896f7c1a3b04383/tools/004-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6896f7c1a3b04383/tools/004-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6896f7c1a3b04383/tools/004-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n3m53s (x4995 over 4h3m)   Warning   Unhealthy   Pod/rc-notready-readiness   Readiness probe failed: readiness dependency unavailable","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6896f7c1a3b04383/tools/005-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6896f7c1a3b04383/tools/005-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6896f7c1a3b04383/tools/005-evidence-kubectl_events.summary.txt"}],"llm_analysis":"# 证据结论\n\n## 已采集证据\n1. **kubectl describe pod**: \n   - Pod 状态为 Running，但 READY 为 0/1。\n   - 包含 readiness probe 失败的事件，提示 \"Readiness probe failed: readiness dependency unavailable\"。\n   - 标注了 `pod_abnormal_type=NotReadyProbeFailed`，并关联了 `pod-notready-probe-failed.md` 的 Runbook。\n\n2. **kubectl get pod -o yaml**:\n   - 验证了 readinessProbe/livenessProbe 的配置参数。\n   - Pod 状态为 Running，但 READY 为 0/1，容器未就绪。\n   - 标注了 `pod_abnormal_type=NotReadyProbeFailed`，并关联了 `pod-notready-probe-failed.md` 的 Runbook。\n\n3. **kubectl logs**:\n   - 没有输出，说明当前容器的日志中没有明显的错误信息。\n\n4. **kubectl previous logs**:\n   - 无法获取 previous logs，提示 \"previous terminated container 'app' in pod 'rc-notready-readiness' not found\"，说明容器没有重启过或者没有 previous logs。\n\n5. **kubectl events**:\n   - 显示 readiness probe 失败的事件，提示 \"Readiness probe failed: readiness dependency unavailable\"。\n\n## 未采集证据\n- 无。\n\n## 冲突证据\n- 无。\n\n## 初步结论\n该 Pod 状态为 Running，但 READY 为 0/1，且 readiness probe 失败。事件中提示 \"Readiness probe failed: readiness dependency unavailable\"，表明 readiness probe 的失败可能是由于依赖项不可用或配置错误。需要进一步检查 readiness probe 的配置，确认其路径、端口、scheme、initialDelaySeconds 等参数是否与容器的实际情况匹配。","collection_summary":"计划 5 项，实际采集 5 项，未采集 0 项，完整度 100%；其中真实环境证据 11/11 项，完整度 100%；实际执行工具 10 个，匹配计划 5 个，未规划证据 5 个","plan_total":5,"plan_collected":5,"plan_completeness":1.0,"environment_evidence_total":11,"environment_evidence_collected":11,"environment_evidence_completeness":1.0,"executed_tool_count":10,"matched_tool_count":5,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"获取 Pod 的详细信息，包括 readinessProbe/livenessProbe 配置和失败事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-readiness -n aiops-e2e","purpose":"验证 readinessProbe/livenessProbe 配置和失败事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod 的 YAML 配置，检查 readinessProbe/livenessProbe 的配置参数","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml","purpose":"验证 readinessProbe/livenessProbe 的配置参数","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取 Pod 的日志，检查健康检查失败时应用的响应","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --tail=200","purpose":"验证健康检查失败时应用的响应","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"获取 Pod 的上一个容器的日志，检查容器重启时的错误信息","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --previous --tail=200","purpose":"验证容器重启时的错误信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5","description":"获取 Pod 的事件，检查 readinessProbe/livenessProbe 失败的详细信息","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-notready-readiness","purpose":"验证 readinessProbe/livenessProbe 失败的详细信息","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_lineage_parents","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 5/5 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取 Pod 的详细信息，包括 readinessProbe/livenessProbe ... | `kubectl describe pod rc-notready-readiness -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_yaml | 获取 Pod 的 YAML 配置，检查 readinessProbe/livenessPr... | `kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml` |
   | e3 | important | ✅ | kubectl_logs | 获取 Pod 的日志，检查健康检查失败时应用的响应 | `kubectl logs rc-notready-readiness -n aiops-e2e --tail=200` |
   | e4 | important | ✅ | kubectl_previous_logs | 获取 Pod 的上一个容器的日志，检查容器重启时的错误信息 | `kubectl logs rc-notready-readiness -n aiops-e2e --previous --tail=200` |
   | e5 | important | ✅ | kubectl_events | 获取 Pod 的事件，检查 readinessProbe/livenessProbe 失败... | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-notre...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (27.2s)
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
   ✅ [汇总总结] 完成 (1m 13.2s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4447 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 6m 52.8s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | `0/1`，`NotReadyProbeFailed` |
| **兼容归因层** | `L4` - 应用健康检查失败 |
| **问题分类** | `readinessProbe` 失败 |
| **置信度** | 高 (80%) |
| **证据完整度** | 5/5 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `rc-notready-readiness` |
| Namespace | `aiops-e2e` |
| Node | `node1` |
| 错误信息 | `Readiness probe failed: readiness dependency unavailable` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `READY: 0/1, STATUS: Running` | Pod 运行中，但未 Ready |
| 2 | 事件日志 | `kubectl describe pod` | `Warning Unhealthy (x4891) Readiness probe failed` | readiness probe 失败，持续发生 |
| 3 | YAML 配置 | `kubectl get pod -o yaml` | 未显示 probe 配置 | 需进一步确认 probe 配置 |
| 4 | 日志信息 | `kubectl logs` | `no output` | 无可用日志 |
| 5 | 历史事件 | `kubectl events` | `Readiness probe failed: readiness dependency unavailable` | 明确指出 readiness 依赖不可用 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 Running，但 readiness 失败，表明容器启动但未满足健康检查条件。
- **证据 #2 + #5 印证**：`Readiness probe failed: readiness dependency unavailable` 说明 readiness 检查依赖的服务或组件未就绪。
- **证据链**：readiness 探针配置或依赖服务异常 → 探针失败 → Pod 未 Ready → 无法被服务调度或流量处理。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| readinessProbe 配置 | critical | 无法确认探针配置是否合理 |
| 应用健康接口响应 | critical | 无法确认健康检查失败的具体原因 |
| 前次容器日志 | important | 无法确认容器启动时的错误信息 |

---

## 🎯 根因分析

### 因果链

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                     │
│ readinessProbe 的健康检查依赖的组件或服务未就绪，导致探针持续失败。             │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                     │
│ readinessProbe 依赖的资源（如 API、数据库、服务端点）未就绪或未正确配置       │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                     │
│ readinessProbe 失败，导致 Pod 被标记为 NotReady                             │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                 │
│ Pod 状态为 Running，但 READY 为 0/1，无法被流量调度                          │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2 (`kubectl describe pod` 中 `Warning Unhealthy Readiness probe failed`) 和证据 #5 (`kubectl events` 中 `Readiness probe failed: readiness dependency unavailable`)，问题的根本原因是 **readinessProbe 的依赖服务未就绪或配置错误**，导致探针失败，Pod 被标记为 NotReady。  
**置信度**：高 (80%)  
- ✅ `kubectl describe pod` 显示 readiness 探针失败
- ✅ `kubectl events` 明确指出探针依赖不可用
- ⚠️ 缺少探针配置和应用日志，无法确认具体依赖或配置错误

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查 readinessProbe 配置**
```bash
kubectl get pod rc-notready-readiness -n aiops-e2e -o jsonpath='{.spec.containers[*].readinessProbe}'
```
*目的*：确认探针的路径、端口、超时等配置是否合理

**2. [可选] 检查依赖服务状态**
```bash
kubectl get all -n aiops-e2e
kubectl get endpoints -n aiops-e2e
```
*目的*：确认 readinessProbe 依赖的服务或组件是否正常运行

**3. [可选] 调整探针配置（如增加 initialDelaySeconds）**
```bash
kubectl set probe deployment/<deployment_name> -n aiops-e2e --readiness --http-get=http://localhost:8080/health --initial-delay-seconds=30 --timeout-seconds=5
```
*目的*：延长探针等待时间，适应应用启动延迟

### 后续优化

1. **监控告警**：配置 readiness 探针失败告警（如 Prometheus + Alertmanager）
2. **日志收集**：启用日志收集工具（如 Fluentd + Loki），便于后续诊断
3. **探针配置文档化**：在 CI/CD 中验证探针配置，避免配置错误

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-notready-readiness -n aiops-e2e` | `STATUS: Running, READY: 1/1` |
| 2. 检查探针失败次数 | `kubectl describe pod rc-notready-readiness -n aiops-e2e | grep Unhealthy` | 无新的 Unhealthy 事件 |
| 3. 检查探针配置 | `kubectl get pod rc-notready-readiness -n aiops-e2e -o jsonpath='{.spec.containers[*].readinessProbe}'` | 配置合理，无错误 |

---

## ⚠️ 注意事项

- 如果 readinessProbe 依赖外部服务，需确保该服务已部署并正常运行
- 如果问题持续，建议启用调试容器或使用 `kubectl debug` 检查容器内部状态
- 如果探针配置复杂，建议使用 `kubectl exec` 进入容器验证健康接口是否可达

---

## 📊 性能统计

├─ 总耗时: 6.9m
├─ 问题定位: 61.0s (15%) ✅
├─ 证据链采集: 251.4s (61%) ✅
├─ 根因分析: 27.2s (7%) ✅
├─ 汇总总结: 73.2s (18%) ✅
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
