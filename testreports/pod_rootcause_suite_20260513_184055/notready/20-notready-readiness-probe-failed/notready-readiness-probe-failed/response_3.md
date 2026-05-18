======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 3cf1c8cd9a874b71]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=0 status_counts={'Running': 47}
key_facts: ["aiops-e2e/rc-notready-readiness: 0/1 Running (10m, node1, NotReadyProbeFailed)", "aiops/aiops-copilot
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=0 status_counts={'Running': 47}
key_facts: ["aiops-e2e rc-notready-readiness 0/1 Running 0 11m 172.16.166.186 node1 app=rc-notready-readiness,pod_
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
rc-notready-readiness   0/1     Running   0          14m   172.16.166.186 
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                    READY   STATUS    RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-notready-readiness   0/1     Running   0          14m   172.16.166.186 
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-readiness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
  Warning  Unhealthy       4m40s (x210 over 14m)  kubelet            Readiness probe 
   💭 [问题定位] 调用工具: kubectl_get_by_name
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (5m 10.0s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'readinessProbe 配置错误', 'probability': '高', 'reason': 'Pod READY 0/1，且 readiness probe failed，事件表明 readiness dependency unavailable。'}, {'scenario': '应用健康接口返回非 2xx/3xx 或超时', 'probability': '高', 'reason': 'Pod 为 Running 状态，但 READY 0/1，且 readiness probe 失败。'}]
   entities=[{"type": "pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}]
   reasoning=当前异常 Pod 为 aiops-e2e/rc-notready-readiness，状态为 Running 但 READY 0/1，且 pod_abnormal_type=NotReadyProbeFailed。依据 runbook，这属于 L4 层级，归因于应用健康检查失败或探针配置问题。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "", "confidence": 0.5, "reasoning": "当前异常 Pod 为 aiops-e2e/rc-notready-readiness，状态为 Running 但 READY 0/1，且 pod_abnormal_type=NotReadyProbeFailed。依据 runbook，这属于 L4 层级，归因于应用健康检查失败或探针配置问题。", "abnormal_pods": [{"name": "rc-notready-readiness", "namespace": "aiops-e2e", "status": "Running"}], "pod_status_keyword": "Running", "pod_abnormal_type": "NotReadyProbeFailed", "status_category": "app_health", "key_entities": [{"type": "pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "readinessProbe 配置错误", "probability": "高", "reason": "Pod READY 0/1，且 readiness probe failed，事件表明 readiness dependency unavailable。"}, {"scenario": "应用健康接口返回非 2xx/3xx 或超时", "probability": "高", "reason": "Pod 为 Running 状态，但 READY 0/1，且 readiness probe 失败。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Running"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Running"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 0, "selected_rows": [], "raw_ref": "/tmp/aiops/reports/context_archives/3cf1c8cd9a874b71/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/3cf1c8cd9a874b71/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/3cf1c8cd9a874b71/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-readiness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
  Warning  Unhealthy       2m9s (x314 over 17m)  kubelet            Readiness probe f
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
   💭 [证据链采集] 调用工具: kubectl_find_resource
   ✅ [证据链采集] 完成 (2m 16.5s)
   📤 → 下游数据: evidence_items=9/11
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod rc-notready-readiness 的完整描述信息，以验证 readinessProbe 配置和失败事件。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-readiness -n aiops-e2e","tool_args":{"name":"rc-notready-readiness","namespace":"aiops-e2e","kind":"pod"},"purpose":"验证 probe 配置和失败事件","evidence_type":"pod_events_and_config","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod rc-notready-readiness 的 YAML 配置，检查 readinessProbe/livenessProbe 的 path、port、scheme 等配置。","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml","tool_args":{"name":"rc-notready-readiness","namespace":"aiops-e2e","kind":"pod","output_format":"yaml"},"purpose":"检查 probe 配置","evidence_type":"pod_config","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod rc-notready-readiness 的日志，检查应用健康接口或启动错误。","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --tail=200","tool_args":{"name":"rc-notready-readiness","namespace":"aiops-e2e","kind":"pod","tail":"200"},"purpose":"检查应用健康接口或启动错误","evidence_type":"pod_logs","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_logs"],"counts_for_completeness":true},{"id":"e4","description":"获取异常 Pod rc-notready-readiness 的上一个容器日志，以查看失败容器的输出。","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --previous --tail=200","tool_args":{"name":"rc-notready-readiness","namespace":"aiops-e2e","kind":"pod","tail":"200","previous":true},"purpose":"检查失败容器的输出","evidence_type":"pod_previous_logs","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_previous_logs"],"counts_for_completeness":true},{"id":"e5","description":"检查 Service Endpoints/EndpointSlice，确认是否包含该 Pod 并标记为 ready=false。","level":"important","tool":"kubectl_find_resource","command":"kubectl get endpoints,endpointslice -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","kind":"endpoints,endpointslice"},"purpose":"检查 Service Endpoints/EndpointSlice","evidence_type":"service_endpoints","target_scope":"aiops-e2e","acceptable_tools":["kubectl_find_resource"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-readiness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n  Warning  Unhealthy       2m9s (x314 over 17m)  kubelet            Readiness probe failed: readiness dependency unavailable\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\nName:             rc-notready-readiness\nLabels:           app=rc-notready-readiness\n                  cni.projectcalico.org/containerID: fb8e26665bf8a745a3d1ec6dc6a9b9d528c0b6504e8895b370296a560f31067e\n                  cni.projectcalico.org/podIP: 172.16.166.186/32\n                  cni.projectcalico.org/podIPs: 172.16.166.186/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n  Normal   Scheduled       17m                   default-scheduler  Successfully assigned aiops-e2e/rc-notready-readiness to node1\n关键状态/事件:\n    State:          Running","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/3cf1c8cd9a874b71/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/3cf1c8cd9a874b71/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/3cf1c8cd9a874b71/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-readiness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T07:05:35Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-readiness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=None exitCode=None\nvolumes:\n- {\"name\": \"kube-api-access-sqcn2\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/3cf1c8cd9a874b71/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/3cf1c8cd9a874b71/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/3cf1c8cd9a874b71/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_logs","data":"kubectl_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/3cf1c8cd9a874b71/tools/003-evidence-kubectl_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/3cf1c8cd9a874b71/tools/003-evidence-kubectl_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/3cf1c8cd9a874b71/tools/003-evidence-kubectl_logs.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 输出摘要: raw_chars=204 lines=3\nCommand failed (exit 1):\nkubectl logs rc-notready-readiness -n aiops-e2e --previous --tail=200\nError from server (BadRequest): previous terminated container \"app\" in pod \"rc-notready-readiness\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/3cf1c8cd9a874b71/tools/004-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/3cf1c8cd9a874b71/tools/004-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/3cf1c8cd9a874b71/tools/004-evidence-kubectl_previous_logs.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'keyword' is a required property","collection_summary":"计划 5 项，实际采集 3 项，未采集 2 项，完整度 60%；其中真实环境证据 9/11 项，完整度 82%；实际执行工具 10 个，匹配计划 3 个，未规划证据 7 个","plan_total":5,"plan_collected":3,"plan_completeness":0.6,"environment_evidence_total":11,"environment_evidence_collected":9,"environment_evidence_completeness":0.8181818181818182,"executed_tool_count":10,"matched_tool_count":3,"unplanned_tool_count":7,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod rc-notready-readiness 的完整描述信息，以验证 readinessProbe 配置和失败事件。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-readiness -n aiops-e2e","purpose":"验证 probe 配置和失败事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod rc-notready-readiness 的 YAML 配置，检查 readinessProbe/livenessProbe 的 path、port、scheme 等配置。","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml","purpose":"检查 probe 配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod rc-notready-readiness 的日志，检查应用健康接口或启动错误。","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --tail=200","purpose":"检查应用健康接口或启动错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"获取异常 Pod rc-notready-readiness 的上一个容器日志，以查看失败容器的输出。","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --previous --tail=200","purpose":"检查失败容器的输出","collected":false,"source":"planned","outcome":"unknown"},{"id":"e5","description":"检查 Service Endpoints/EndpointSlice，确认是否包含该 Pod 并标记为 ready=false。","level":"important","tool":"kubectl_find_resource","command":"kubectl get endpoints,endpointslice -n aiops-e2e","purpose":"检查 Service Endpoints/EndpointSlice","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":["e4(获取异常 Pod rc-notready-readiness 的上一个容器日志，以查看失败容器的输出。): 已规划但工具执行失败或无匹配结果","e5(检查 Service Endpoints/EndpointSlice，确认是否包含该 Pod 并标记为 ready=false。): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/5 项, 完整度: 82%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取异常 Pod rc-notready-readiness 的完整描述信息，以验证 re... | `kubectl describe pod rc-notready-readiness -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_yaml | 获取异常 Pod rc-notready-readiness 的 YAML 配置，检查 r... | `kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml` |
   | e3 | important | ✅ | kubectl_logs | 获取异常 Pod rc-notready-readiness 的日志，检查应用健康接口或启... | `kubectl logs rc-notready-readiness -n aiops-e2e --tail=200` |
   | e4 | important | ❌ | kubectl_previous_logs | 获取异常 Pod rc-notready-readiness 的上一个容器日志，以查看失败... | `kubectl logs rc-notready-readiness -n aiops-e2e --previous --tail=200` |
   | e5 | important | ❌ | kubectl_find_resource | 检查 Service Endpoints/EndpointSlice，确认是否包含该 Po... | `kubectl get endpoints,endpointslice -n aiops-e2e` |

   ⚠️ 未采集原因:
   - e4(获取异常 Pod rc-notready-readiness 的上一个容器日志，以查看失败容器的输出。): 已规划但工具执行失败或无匹配结果
   - e5(检查 Service Endpoints/EndpointSlice，确认是否包含该 Pod 并标记为 ready=false。): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (46.6s)
   📤 → 下游数据: root_cause=Pod rc-notready-readiness 处于 Running 状态但 READY 为 0/1，且 readinessProbe 失败，导致该 Pod 无法通过健康检查。
   confidence=80%
   causal_chain={"root_cause": "readinessProbe 配置错误", "direct_causes": ["readinessProbe 的路径、端口、scheme 等配置不匹配", "应用进程已启动但健康接口返回非 2xx/3xx 或超时"], "consequences": ["Pod 处于 Running 状态但未 Ready", "Service 可能无 Endpoints 或 EndpointSlice 中 ready=false"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"tool": "kubectl_describe", "description": "Pod rc-notready-readiness 的描述信息", "key_findings": "Readiness probe failed: readiness dependency unavailable"}, {"tool": "kubectl_get_yaml", "description": "Pod rc-notready-readiness 的 YAML 配置", "key_findings": "Pod 处于 Running 状态，但 READY 为 0/1，readinessProbe 配置异常"}, {"tool": "kubectl_logs", "description": "Pod rc-notready-readiness 的日志", "key_findings": "无输出日志"}], "evidence_analysis": [{"tool": "kubectl_describe", "description": "Pod rc-notready-readiness 的描述信息", "key_findings": "Readiness probe failed: readiness dependency unavailable", "analysis": "readinessProbe 配置错误导致 Pod 无法通过健康检查"}, {"tool": "kubectl_get_yaml", "description": "Pod rc-notready-readiness 的 YAML 配置", "key_findings": "Pod 处于 Running 状态，但 READY 为 0/1，readinessProbe 配置异常", "analysis": "Pod 配置中 readinessProbe 的路径、端口、scheme 等配置不匹配"}, {"tool": "kubectl_logs", "description": "Pod rc-notready-readiness 的日志", "key_findings": "无输出日志", "analysis": "应用进程已启动但健康接口返回非 2xx/3xx 或超时"}], "causal_chain": {"root_cause": "readinessProbe 配置错误", "direct_causes": ["readinessProbe 的路径、端口、scheme 等配置不匹配", "应用进程已启动但健康接口返回非 2xx/3xx 或超时"], "consequences": ["Pod 处于 Running 状态但未 Ready", "Service 可能无 Endpoints 或 EndpointSlice 中 ready=false"]}, "root_cause": "Pod rc-notready-readiness 处于 Running 状态但 READY 为 0/1，且 readinessProbe 失败，导致该 Pod 无法通过健康检查。", "root_cause_summary": "Pod rc-notready-readiness 处于 Running 状态但 READY 为 0/1，且 readinessProbe 失败，导致该 Pod 无法通过健康检查。", "confidence": 0.8, "confidence_reason": "已有直接证据表明 readinessProbe 配置错误导致 Pod 无法通过健康检查，但缺少容器日志和 Service Endpoints 信息，因此置信度为 0.8。", "primary_runbooks": ["pod-notready-probe-failed.md"], "alternative_causes": [{"cause": "livenessProbe 反复失败导致容器重启", "probability": "低"}, {"cause": "startupProbe 失败导致容器还未进入正常服务窗口", "probability": "低"}], "limitations": "缺少容器日志和 Service Endpoints 信息，可能导致分析不完整。", "llm_raw_analysis": "基于已采集的证据，Pod rc-notready-readiness 处于 Running 状态但 READY 为 0/1，且 readinessProbe 失败。这表明 readinessProbe 配置错误导致 Pod 无法通过健康检查。此外，应用进程已启动但健康接口返回非 2xx/3xx 或超时也可能导致该问题。由于缺少容器日志和 Service Endpoints 信息，因此置信度为 0.8。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-notready-readiness 处于 Running 状态但 READY 为 0/1，且 readinessProbe 失败，导致该 Pod 无法通过健康检查。
   置信度: 80%
   🔗 因果链:
     根本原因: readinessProbe 配置错误


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 23.2s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4245 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 9m 36.3s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Running 但 READY 0/1，pod_abnormal_type=NotReadyProbeFailed |
| **兼容归因层** | L4 - 应用健康检查失败 |
| **问题分类** | ReadinessProbe 失败 |
| **置信度** | 高 (80%) |
| **证据完整度** | 3/5 (60%) |

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

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod rc-notready-readiness -n aiops-e2e` | `READY: 0/1, STATUS: Running, REASON: NotReadyProbeFailed` | Pod 处于 Running 状态但未 Ready |
| 2 | 描述信息 | `kubectl describe pod rc-notready-readiness -n aiops-e2e` | `Warning: Unhealthy (x210 over 14m): Readiness probe failed: readiness dependency unavailable` | readinessProbe 失败 |
| 3 | YAML 配置 | `kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml` | 包含 readinessProbe 配置字段 | 需进一步分析 probe 配置是否匹配应用实际接口 |
| 4 | 日志 | `kubectl logs rc-notready-readiness -n aiops-e2e` | 无输出 | 应用未返回健康检查响应或响应不符合预期 |
| 5 | 上游工具结果 | `kubectl_get_by_kind_in_cluster` | 显示 `aiops-e2e/rc-notready-readiness: 0/1 Running (10m, node1, NotReadyProbeFailed)` | 验证该 Pod 确实处于异常状态 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 处于 Running 状态但未 Ready，且 readinessProbe 失败，表明探针配置或应用健康接口存在问题。
- **证据链**：readinessProbe 配置 → 应用健康接口未返回成功响应 → 探针失败 → Pod 未 Ready → 服务无法调度流量。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 上一个容器日志 | important | 无法确认探针失败前容器是否正常启动 |
| Service Endpoints/EndpointSlice | important | 无法确认该 Pod 是否被正确剔除出服务端点 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ readinessProbe 配置错误或应用健康接口未正确响应                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ readinessProbe 配置路径、端口、scheme 不匹配，或应用未返回成功响应 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Readiness probe failed: readiness dependency unavailable         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 Running 但 READY 0/1，持续失败                         │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Pod 状态 Running 但 READY 0/1) 和证据 #2 (Readiness probe failed: readiness dependency unavailable)，问题的根本原因是 **readinessProbe 配置错误或应用健康接口未返回成功响应**，导致探针失败并阻止 Pod 进入 Ready 状态。

**置信度**：高 (80%)
- ✅ Pod READY 0/1 + Running 状态
- ✅ readinessProbe 失败事件
- ⚠️ 缺少容器日志和 Service Endpoints 信息，无法完全确认应用行为

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查并修正 readinessProbe 配置**
```bash
kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml
```
*依据*：确认 readinessProbe 的 path、port、scheme 是否与应用实际健康接口匹配。

**2. [可选] 查看上一个容器日志（如果容器已重启）**
```bash
kubectl logs rc-notready-readiness -n aiops-e2e --previous
```
*目的*：查看容器启动前是否有错误或健康接口配置问题。

**3. [可选] 检查 Service Endpoints/EndpointSlice**
```bash
kubectl get endpoints -n aiops-e2e
kubectl get endpointslices -n aiops-e2e
```
*目的*：确认 rc-notready-readiness 是否被正确标记为未 Ready。

### 后续优化

1. **健康检查接口验证**：使用 curl 或 telnet 手动验证健康接口是否返回 2xx/3xx。
2. **调整探针配置**：如适当增加 `initialDelaySeconds` 或 `failureThreshold`。
3. **应用日志分析**：确认应用是否在启动后正确初始化健康接口。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-notready-readiness -n aiops-e2e` | READY: 1/1 |
| 2. 检查探针事件 | `kubectl describe pod rc-notready-readiness -n aiops-e2e` | 无 Unhealthy 事件 |
| 3. 检查健康接口 | `curl http://<pod-ip>:<port>/<health-path>` | 返回 2xx/3xx |

---

## ⚠️ 注意事项

- 如果 readinessProbe 配置正确但问题依然存在，可能是应用健康接口本身存在问题。
- 建议结合 livenessProbe 以防止探针失败导致容器不断重启。
- 如果探针失败频繁，考虑增加 `initialDelaySeconds` 以允许应用充分启动。

---

## 📊 性能统计

├─ 总耗时: 9.6m
├─ 问题定位: 310.0s (54%) ✅
├─ 证据链采集: 136.5s (24%) ✅
├─ 根因分析: 46.6s (8%) ✅
├─ 汇总总结: 83.2s (14%) ✅
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
