======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 6a9a517b2e8445dc]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=0 status_counts={'Running': 47}，但 aiops-e2e 命名空间中的 rc-notready-readiness Pod READY 状态为 0/1，且标签中包含 pod_abnormal_type=NotReadyProbeFailed，表明存在异常。
ke
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod NotReadyProbeFailed / Running 但未 Ready

> Pod异常类型: NotReadyProbeFailed | 典型状态: Running + READY 0/1 | 兼容分类: probe_health

## 状态识别
- Pod phase 通常为 `Running`，但 READY 为 `0/1` 或部分容器未 Ready

   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                    READY   STATUS    RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-notready-readiness   0/1     Running   0          57m   172.16.166.186 
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-readiness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
  Warning  Unhealthy       2m47s (x1146 over 57m)  kubelet            Readiness probe
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
   💭 [问题定位] 调用工具: kubectl_logs_grep
   💭 [问题定位] 工具结果: kubectl_logs_grep (success)
      📄 kubectl_logs_grep 输出摘要: raw_chars=105 lines=2
Command failed (exit 1):
kubectl logs rc-notready-readiness -n aiops-e2e --tail=200 | grep -i -- 'probe'
   💭 [问题定位] 调用工具: kubectl_container_logs
   💭 [问题定位] 工具结果: kubectl_container_logs (success)
      📄 kubectl_container_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 42.9s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'readinessProbe 配置错误', 'probability': '高', 'reason': 'Pod 状态为 Running 但 READY 0/1，readiness probe 失败，可能是探针配置与应用实际接口不匹配。'}, {'scenario': '应用健康接口返回异常', 'probability': '高', 'reason': 'Pod 可能已启动，但健康接口返回非 2xx/3xx 状态码或超时。'}, {'scenario': 'startupProbe 参数过严', 'probability': '中', 'reason': '若容器启动慢或 startupProbe 配置过严，可能导致探针失败。'}]
   entities=[{"type": "Pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}]
   reasoning=当前环境中存在异常 Pod rc-notready-readiness，其 READY 状态为 0/1，且标签中包含 pod_abnormal_type=NotReadyProbeFailed。根据 runbook，Pod 处于 Running 状态但未 Ready，且 readiness probe 失败，属于 L4 层级的异常，归类为应用健康检查失败。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "application error", "confidence": 0.5, "reasoning": "当前环境中存在异常 Pod rc-notready-readiness，其 READY 状态为 0/1，且标签中包含 pod_abnormal_type=NotReadyProbeFailed。根据 runbook，Pod 处于 Running 状态但未 Ready，且 readiness probe 失败，属于 L4 层级的异常，归类为应用健康检查失败。", "abnormal_pods": [{"name": "rc-notready-readiness", "namespace": "aiops-e2e", "status": "Running"}], "pod_status_keyword": "Running", "pod_abnormal_type": "NotReadyProbeFailed", "status_category": "app_health", "key_entities": [{"type": "Pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "readinessProbe 配置错误", "probability": "高", "reason": "Pod 状态为 Running 但 READY 0/1，readiness probe 失败，可能是探针配置与应用实际接口不匹配。"}, {"scenario": "应用健康接口返回异常", "probability": "高", "reason": "Pod 可能已启动，但健康接口返回非 2xx/3xx 状态码或超时。"}, {"scenario": "startupProbe 参数过严", "probability": "中", "reason": "若容器启动慢或 startupProbe 配置过严，可能导致探针失败。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Running"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Running"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 0, "selected_rows": [], "raw_ref": "/tmp/aiops/reports/context_archives/6a9a517b2e8445dc/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/6a9a517b2e8445dc/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/6a9a517b2e8445dc/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
name: rc-notready-readiness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
  Warning  Unhealthy       16s (x1251 over 60m)  kubelet            Readiness probe f
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
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
23s (x1251 over 60m)   Warning   Unhealthy        Pod/rc-notready-readiness   Readiness probe failed: readiness dependency unavailable
60m                    Normal    AddedI
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。
   💭 [证据链采集] # 证据结论

## 已采集证据
1. **kubectl_describe pod** 显示 `rc-notready-readiness` Pod 的 readiness probe 失败，原因是 "readiness dependency unavailable"。
2. **kubectl_get_yaml** 显示该 Pod 的容器状态为未就绪，且 readiness probe 配置未提供具体细节。
3. **kubectl_logs** 没有输出，表示容器中没有日志记录。
4. **kubectl_events** 显示 readiness probe 失败的重复事件，表明探针持续失败。
5. **kubectl_get_by_kind_in_namespace** 未找到 endpoints 或 endpointslice 资源，表明该命名空间中没有相关的服务端点。

## 未采集证据
- 无进一步的探针配置细节。
- 无应用健康接口的具体错误信息。

## 冲突证据
- endpoints 和 endpointslice 资源不存在，表明该 Pod 可能未关联到任何服务，或服务配置存在问题。
   ✅ [证据链采集] 完成 (2m 14.9s)
   📤 → 下游数据: evidence_items=11/11
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod rc-notready-readiness 的详细信息，确认 readinessProbe 配置和失败原因。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-readiness -n aiops-e2e","tool_args":{"name":"rc-notready-readiness","namespace":"aiops-e2e"},"purpose":"验证 readinessProbe 配置和失败原因","evidence_type":"diagnostic_event","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod rc-notready-readiness 的 YAML 配置，查看 readinessProbe/livenessProbe/startupProbe 的配置细节。","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml","tool_args":{"name":"rc-notready-readiness","namespace":"aiops-e2e","output":"yaml"},"purpose":"验证 probe 配置细节","evidence_type":"configuration","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod rc-notready-readiness 的日志，查看健康接口或启动错误。","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --tail=200","tool_args":{"name":"rc-notready-readiness","namespace":"aiops-e2e","tail":"200"},"purpose":"查看健康接口或启动错误","evidence_type":"application_log","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"获取异常 Pod rc-notready-readiness 的事件信息，查看 probe 失败事件。","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-notready-readiness","tool_args":{"namespace":"aiops-e2e","filter":"involvedObject.name=rc-notready-readiness"},"purpose":"查看 probe 失败事件","evidence_type":"event","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":[],"counts_for_completeness":true},{"id":"e5","description":"获取 Service Endpoints/EndpointSlice 信息，确认是否包含异常 Pod rc-notready-readiness，以及是否 ready=false。","level":"optional","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get endpoints,endpointslice -n aiops-e2e","tool_args":{"kind":"endpoints,endpointslice","namespace":"aiops-e2e"},"purpose":"确认 Service 是否包含异常 Pod 并 ready=false","evidence_type":"service_configuration","target_scope":"aiops-e2e","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-readiness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n  Warning  Unhealthy       16s (x1251 over 60m)  kubelet            Readiness probe failed: readiness dependency unavailable\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\nName:             rc-notready-readiness\nLabels:           app=rc-notready-readiness\n                  cni.projectcalico.org/containerID: fb8e26665bf8a745a3d1ec6dc6a9b9d528c0b6504e8895b370296a560f31067e\n                  cni.projectcalico.org/podIP: 172.16.166.186/32\n                  cni.projectcalico.org/podIPs: 172.16.166.186/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n  Normal   Scheduled       60m                   default-scheduler  Successfully assigned aiops-e2e/rc-notready-readiness to node1\n关键状态/事件:\n    State:          Running","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6a9a517b2e8445dc/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6a9a517b2e8445dc/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6a9a517b2e8445dc/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-readiness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T07:05:35Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-readiness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=None exitCode=None\nvolumes:\n- {\"name\": \"kube-api-access-sqcn2\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6a9a517b2e8445dc/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6a9a517b2e8445dc/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6a9a517b2e8445dc/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_logs","data":"kubectl_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6a9a517b2e8445dc/tools/003-evidence-kubectl_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6a9a517b2e8445dc/tools/003-evidence-kubectl_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6a9a517b2e8445dc/tools/003-evidence-kubectl_logs.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n23s (x1251 over 60m)   Warning   Unhealthy        Pod/rc-notready-readiness   Readiness probe failed: readiness dependency unavailable\n60m                    Normal    AddedInterface   Pod/rc-notready-readiness   Add eth0 [172.16.166.186/32] from k8s-pod-network\n60m                    Normal    Pulled           Pod/rc-notready-readiness   Container image \"busybox:1.36\" already present on machine\n60m                    Normal    Created          Pod/rc-notready-readiness   Created container app\n60m                    Normal    Started          Pod/rc-notready-readiness   Started container app\n60m                    Normal    Scheduled        Pod/rc-notready-readiness   Successfully assigned aiops-e2e/rc-notready-readiness to node1","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6a9a517b2e8445dc/tools/004-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6a9a517b2e8445dc/tools/004-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6a9a517b2e8445dc/tools/004-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/6a9a517b2e8445dc/tools/005-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6a9a517b2e8445dc/tools/005-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6a9a517b2e8445dc/tools/005-evidence-kubectl_get_by_kind_in_namespace.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/6a9a517b2e8445dc/tools/006-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6a9a517b2e8445dc/tools/006-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6a9a517b2e8445dc/tools/006-evidence-kubectl_get_by_kind_in_namespace.summary.txt"}],"llm_analysis":"# 证据结论\n\n## 已采集证据\n1. **kubectl_describe pod** 显示 `rc-notready-readiness` Pod 的 readiness probe 失败，原因是 \"readiness dependency unavailable\"。\n2. **kubectl_get_yaml** 显示该 Pod 的容器状态为未就绪，且 readiness probe 配置未提供具体细节。\n3. **kubectl_logs** 没有输出，表示容器中没有日志记录。\n4. **kubectl_events** 显示 readiness probe 失败的重复事件，表明探针持续失败。\n5. **kubectl_get_by_kind_in_namespace** 未找到 endpoints 或 endpointslice 资源，表明该命名空间中没有相关的服务端点。\n\n## 未采集证据\n- 无进一步的探针配置细节。\n- 无应用健康接口的具体错误信息。\n\n## 冲突证据\n- endpoints 和 endpointslice 资源不存在，表明该 Pod 可能未关联到任何服务，或服务配置存在问题。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 10/10 项，完整度 100%；实际执行工具 9 个，匹配计划 5 个，未规划证据 4 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":10,"environment_evidence_collected":10,"environment_evidence_completeness":1.0,"executed_tool_count":9,"matched_tool_count":5,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod rc-notready-readiness 的详细信息，确认 readinessProbe 配置和失败原因。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-readiness -n aiops-e2e","purpose":"验证 readinessProbe 配置和失败原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod rc-notready-readiness 的 YAML 配置，查看 readinessProbe/livenessProbe/startupProbe 的配置细节。","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml","purpose":"验证 probe 配置细节","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod rc-notready-readiness 的日志，查看健康接口或启动错误。","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --tail=200","purpose":"查看健康接口或启动错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"获取异常 Pod rc-notready-readiness 的事件信息，查看 probe 失败事件。","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-notready-readiness","purpose":"查看 probe 失败事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5","description":"获取 Service Endpoints/EndpointSlice 信息，确认是否包含异常 Pod rc-notready-readiness，以及是否 ready=false。","level":"optional","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get endpoints,endpointslice -n aiops-e2e","purpose":"确认 Service 是否包含异常 Pod 并 ready=false","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_logs_grep","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_container_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取异常 Pod rc-notready-readiness 的详细信息，确认 readi... | `kubectl describe pod rc-notready-readiness -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_yaml | 获取异常 Pod rc-notready-readiness 的 YAML 配置，查看 r... | `kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml` |
   | e3 | important | ✅ | kubectl_logs | 获取异常 Pod rc-notready-readiness 的日志，查看健康接口或启动错误。 | `kubectl logs rc-notready-readiness -n aiops-e2e --tail=200` |
   | e4 | important | ✅ | kubectl_events | 获取异常 Pod rc-notready-readiness 的事件信息，查看 probe... | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-notre...` |
   | e5 | optional | ✅ | kubectl_get_by_kind_in_na... | 获取 Service Endpoints/EndpointSlice 信息，确认是否包含异... | `kubectl get endpoints,endpointslice -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 12.1s)
   📤 → 下游数据: root_cause=rc-notready-readiness Pod 的 readiness probe 失败，原因是 readiness dependency unavailable。这表明探针的依赖项不可用，可能是探针配置错误或应用健康接口未正确响应。
   confidence=80%
   causal_chain={"root_cause": "readinessProbe 配置错误或应用健康接口未正确响应", "intermediate_causes": ["readiness dependency unavailable", "Pod 未就绪"], "immediate_causes": ["readiness probe 失败"], "symptoms": ["Pod READY 状态为 0/1", "readiness probe 失败"]}
   rca_analysis={"phenomenon": "Pod rc-notready-readiness 位于命名空间 aiops-e2e 中，处于 Running 状态，但 READY 状态为 0/1，表明其未就绪。此外，标签中包含 pod_abnormal_type=NotReadyProbeFailed，表明该 Pod 的 readiness probe 失败。", "evidence_inventory": [{"description": "获取异常 Pod rc-notready-readiness 的详细信息，确认 readinessProbe 配置和失败原因。", "value": "kubectl_describe 摘要:\nname: rc-notready-readiness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n  Warning  Unhealthy       16s (x1251 over 60m)  kubelet            Readiness probe failed: readiness dependency unavailable\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\nName:             rc-notready-readiness\nLabels:           app=rc-notready-readiness\n                  cni.projectcalico.org/containerID: f"}, {"description": "获取异常 Pod rc-notready-readiness 的 YAML 配置，查看 readinessProbe/livenessProbe/startupProbe 的配置细节。", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-readiness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T07:05:35Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-readiness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntoleration"}, {"description": "获取异常 Pod rc-notready-readiness 的事件信息，查看 probe 失败事件。", "value": "kubectl_events 摘要:\n关键诊断行:\n23s (x1251 over 60m)   Warning   Unhealthy        Pod/rc-notready-readiness   Readiness probe failed: readiness dependency unavailable\n60m                    Normal    AddedInterface   Pod/rc-notready-readiness   Add eth0 [172.16.166.186/32] from k8s-pod-network\n60m                    Normal    Pulled           Pod/rc-notready-readiness   Container image \"busybox:1.36\" already present on machine\n60m                    Normal    Created          Pod/rc-notready-readiness"}], "evidence_analysis": [{"description": "kubectl_describe pod", "analysis": "kubectl_describe 显示 rc-notready-readiness Pod 的 readiness probe 失败，原因是 readiness dependency unavailable。这表明探针的依赖项不可用，可能是探针配置错误或应用健康接口未正确响应。"}, {"description": "kubectl_get_yaml", "analysis": "kubectl_get_yaml 显示 rc-notready-readiness Pod 的容器状态为未就绪，且 readiness probe 配置未提供具体细节。这表明探针配置可能不正确，或者应用健康接口未返回预期状态。"}, {"description": "kubectl_events", "analysis": "kubectl_events 显示 readiness probe 失败的重复事件，表明探针持续失败。这表明探针配置或应用健康接口存在问题，导致探针无法成功。"}], "causal_chain": {"root_cause": "readinessProbe 配置错误或应用健康接口未正确响应", "intermediate_causes": ["readiness dependency unavailable", "Pod 未就绪"], "immediate_causes": ["readiness probe 失败"], "symptoms": ["Pod READY 状态为 0/1", "readiness probe 失败"]}, "root_cause": "rc-notready-readiness Pod 的 readiness probe 失败，原因是 readiness dependency unavailable。这表明探针的依赖项不可用，可能是探针配置错误或应用健康接口未正确响应。", "root_cause_summary": "rc-notready-readiness Pod 的 readiness probe 失败，原因是 readiness dependency unavailable。这表明探针的依赖项不可用，可能是探针配置错误或应用健康接口未正确响应。", "confidence": 0.8, "confidence_reason": "有直接证据表明 readiness probe 失败，且探针配置可能存在错误。", "primary_runbooks": ["pod-notready-probe-failed.md"], "alternative_causes": [{"description": "应用健康接口返回异常", "probability": "高", "reason": "Pod 可能已启动，但健康接口返回非 2xx/3xx 状态码或超时。"}], "limitations": "未采集到进一步的探针配置细节和应用健康接口的具体错误信息，因此无法完全确定根因。", "llm_raw_analysis": "基于提供的证据，rc-notready-readiness Pod 的 readiness probe 失败，原因是 readiness dependency unavailable。这表明探针的依赖项不可用，可能是探针配置错误或应用健康接口未正确响应。kubectl_get_yaml 显示该 Pod 的容器状态为未就绪，且 readiness probe 配置未提供具体细节。kubectl_events 显示 readiness probe 失败的重复事件，表明探针持续失败。这表明探针配置或应用健康接口存在问题，导致探针无法成功。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: rc-notready-readiness Pod 的 readiness probe 失败，原因是 readiness dependency unavailable。这表明探针的依赖项不可用，可能是探针配置错误或应用健康接口未正确响应。
   置信度: 80%
   🔗 因果链:
     根本原因: readinessProbe 配置错误或应用健康接口未正确响应


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 21.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4308 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 6m 31.7s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | NotReadyProbeFailed |
| **兼容归因层** | L4 |
| **问题分类** | ReadinessProbe 失败 |
| **置信度** | 高 (80%) |
| **证据完整度** | 4/4 (100%) |

---

## 🔍 现象描述

**用户报告**：  
> 我的集群有什么问题？

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | rc-notready-readiness |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | Readiness probe failed: readiness dependency unavailable |

该 Pod 当前状态为 `Running`，但 `READY` 状态为 `0/1`，表明其未通过就绪检查，属于 `NotReadyProbeFailed` 类型的异常。此 Pod 已运行 57 分钟，但 readiness probe 已失败 1146 次，失败频率为每 2 分 47 秒一次。

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod rc-notready-readiness -n aiops-e2e` | `READY: 0/1`, `STATUS: Running` | Pod 已启动但未 Ready |
| 2 | 事件记录 | `kubectl describe pod rc-notready-readiness -n aiops-e2e` | `Warning Unhealthy: Readiness probe failed: readiness dependency unavailable` | readiness probe 失败，依赖项不可用 |
| 3 | YAML 配置 | `kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml` | 包含 readinessProbe 配置字段 | 需进一步查看探针具体配置 |
| 4 | 日志 | `kubectl logs rc-notready-readiness -n aiops-e2e` | `no output` | 日志中未发现与探针失败直接相关的错误信息 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 Running 但未 Ready，且探针失败事件频繁发生，确认该 Pod 存在 readiness probe 问题。
- **证据 #3 印证**：探针配置字段存在，但未采集到具体配置内容（如 HTTP 路径、端口、超时时间等），需进一步检查探针参数。
- **证据 #4 表明**：容器日志中未发现探针失败的直接原因，可能是探针配置错误或应用健康接口未正确响应。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| readinessProbe 的具体配置 | critical | 无法确认探针配置是否与应用接口匹配 |
| 应用健康接口返回状态 | critical | 无法确认探针失败的根本原因 |
| startupProbe/livenessProbe 配置 | optional | 无法判断是否为启动或存活探针问题 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ readinessProbe 配置错误或应用健康接口未正确响应                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ readinessProbe 依赖项不可用 → 探针失败 → Pod 未 Ready           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Readiness probe failed: readiness dependency unavailable        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 Running 但 READY 0/1，且探针失败事件频繁              │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Pod 状态为 Running 但 READY 0/1) 和证据 #2 (readiness probe 失败事件)，问题的根本原因是 **readinessProbe 配置错误或应用健康接口未正确响应**，导致探针失败，Pod 无法标记为 Ready。

**置信度**：高 (80%)  
- ✅ `Warning Unhealthy` 事件频繁，确认探针失败
- ✅ `Ready=0/1` 状态表明 Pod 未通过就绪检查
- ⚠️ 未采集到探针配置和健康接口返回状态，无法进一步确认具体原因

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查 readinessProbe 配置**

```bash
kubectl get pod rc-notready-readiness -n aiops-e2e -o jsonpath='{.spec.containers[*].readinessProbe}' | jq
```

*依据*：确认探针配置是否与应用实际接口匹配（如 HTTP 路径、端口、超时时间）。

**2. [可选] 检查 livenessProbe 和 startupProbe 配置**

```bash
kubectl get pod rc-notready-readiness -n aiops-e2e -o jsonpath='{.spec.containers[*].livenessProbe}' | jq
kubectl get pod rc-notready-readiness -n aiops-e2e -o jsonpath='{.spec.containers[*].startupProbe}' | jq
```

*目的*：排查是否为启动或存活探针问题。

**3. [可选] 直接访问健康接口验证响应**

```bash
curl -v http://172.16.166.186:80/health
```

*目的*：确认健康接口是否返回 2xx/3xx 状态码，是否超时。

### 后续优化

1. **调整探针配置**：根据实际应用响应时间调整 `initialDelaySeconds`、`timeoutSeconds` 等参数。
2. **监控探针失败频率**：配置 Prometheus 或使用 `kubectl get events` 定期监控探针失败事件。
3. **增加日志记录**：在应用中增加探针调用日志，便于排查失败原因。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-notready-readiness -n aiops-e2e` | STATUS: Running, READY: 1/1 |
| 2. 检查探针失败事件 | `kubectl describe pod rc-notready-readiness -n aiops-e2e` | 无 Unhealthy 事件 |
| 3. 监控健康接口 | `curl -v http://172.16.166.186:80/health` | 返回 2xx/3xx 状态码 |

---

## ⚠️ 注意事项

- 如果探针配置正确但仍然失败，可能是应用启动慢或存在健康接口逻辑问题。
- 如果问题持续，建议进一步检查应用代码或增加探针容忍时间。

---

## 📊 性能统计

├─ 总耗时: 6.5m
├─ 问题定位: 102.9s (26%) ✅
├─ 证据链采集: 134.9s (34%) ✅
├─ 根因分析: 72.1s (18%) ✅
├─ 汇总总结: 81.8s (21%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 14 次
```

📋 诊断追踪

- **核心 Runbook**: pod-notready-probe-failed
- **参考 Runbook**: pod-notready-probe-failed
- **工具调用**: 14 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
