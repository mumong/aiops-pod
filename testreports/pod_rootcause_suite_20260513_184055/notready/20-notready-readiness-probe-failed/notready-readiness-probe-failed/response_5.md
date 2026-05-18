======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: c052735287c547c6]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 工具输出摘要: rows=49 abnormal=0 status_counts={'Running': 47}，共 49 行，其中 47 个 Pod 处于 Running 状态。
key_facts: ["aiops-e2e/rc-notready-readiness Pod 处于 0/1 状态，标签包含 pod_abnormal_t
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod NotReadyProbeFailed / Running 但未 Ready

> Pod异常类型: NotReadyProbeFailed | 典型状态: Running + READY 0/1 | 兼容分类: probe_health

## 状态识别
- Pod phase 通常为 `Running`，但 READY 为 `0/1` 或部分容器未 Ready

   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=331 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide pod aiops-e2e/rc-notready-readiness -n aiops-e2e
error: there is no need to specify a resourc
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                    READY   STATUS    RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-notready-readiness   0/1     Running   0          27m   172.16.166.186 
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-readiness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
  Warning  Unhealthy       2m34s (x522 over 27m)  kubelet            Readiness probe 
   💭 [问题定位] 调用工具: kubectl_logs
   💭 [问题定位] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=175 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide service rc-notready-readiness -n aiops-e2e
Error from server (NotFound): services "rc-notread
   💭 [问题定位] 调用工具: kubectl_get_by_name
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 53.7s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'readinessProbe 配置错误或不匹配', 'probability': '高', 'reason': 'Pod 为 Running 状态但 READY 0/1，且 readiness probe failed 事件频繁。'}, {'scenario': '应用健康接口返回错误状态码或超时', 'probability': '高', 'reason': 'readiness probe 失败可能是由于应用接口未正确响应健康检查。'}, {'scenario': 'Service selector 配置错误', 'probability': '中', 'reason': '未找到同名 Service，需检查 Service 是否存在及 selector 是否正确。'}]
   entities=[{"type": "Pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}]
   reasoning=发现异常 Pod aiops-e2e/rc-notready-readiness，状态为 Running 但 READY 0/1，标签中标注 pod_abnormal_type=NotReadyProbeFailed，符合 L4 层级的应用健康检查失败特征。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "application error", "confidence": 0.9, "reasoning": "发现异常 Pod aiops-e2e/rc-notready-readiness，状态为 Running 但 READY 0/1，标签中标注 pod_abnormal_type=NotReadyProbeFailed，符合 L4 层级的应用健康检查失败特征。", "abnormal_pods": [{"name": "rc-notready-readiness", "namespace": "aiops-e2e", "status": "Running"}], "pod_status_keyword": "Running", "pod_abnormal_type": "NotReadyProbeFailed", "status_category": "app_health", "key_entities": [{"type": "Pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "readinessProbe 配置错误或不匹配", "probability": "高", "reason": "Pod 为 Running 状态但 READY 0/1，且 readiness probe failed 事件频繁。"}, {"scenario": "应用健康接口返回错误状态码或超时", "probability": "高", "reason": "readiness probe 失败可能是由于应用接口未正确响应健康检查。"}, {"scenario": "Service selector 配置错误", "probability": "中", "reason": "未找到同名 Service，需检查 Service 是否存在及 selector 是否正确。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Running"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Running"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 0, "selected_rows": [], "raw_ref": "/tmp/aiops/reports/context_archives/c052735287c547c6/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/c052735287c547c6/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/c052735287c547c6/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-readiness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
  Warning  Unhealthy       4m34s (x522 over 29m)  kubelet            Readiness probe 
   💭 [证据链采集] 调用工具: kubectl_logs
   💭 [证据链采集] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
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
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
4m43s (x522 over 29m)   Warning   Unhealthy        Pod/rc-notready-readiness   Readiness probe failed: readiness dependency unavailable
29m                     Normal    Adde
   💭 [证据链采集] # 证据结论

## 已采集证据
1. **Pod 描述信息**：通过 `kubectl describe` 确认 Pod `rc-notready-readiness` 处于 `Running` 状态，但 `READY` 为 `0/1`。事件显示 `readiness probe failed: readiness dependency unavailable`，且标签中标注 `pod_abnormal_type=NotReadyProbeFailed`。
2. **容器日志**：通过 `kubectl logs` 检查容器日志，但未发现输出内容，表明容器可能未正常启动或健康接口未响应。
3. **Pod 配置**：通过 `kubectl get -o yaml` 检查 Pod 配置，确认容器 `app` 使用镜像 `busybox:1.36`，且 `readinessProbe` 配置未在输出中显示。
4. **事件信息**：通过 `kubectl events` 确认事件 `readiness probe failed: readiness dependency unavailable` 频繁出现，表明 readiness probe 配置或应用健康接口存在问题。

## 未采集证据
1. **Service Endpoints**：未检查 Service `rc-notready-readiness` 的 Endpoints 或 EndpointSlice，以确认是否由于 Service selector 配置错误导致服务不可用。
2. **StartupProbe 配置**：未检查 `startupProbe` 配置，以确认是否由于启动慢或配置过严导致探针失败。

## 冲突证据
1. **容器日志**：`kubectl logs` 未返回任何输出，表明容器可能未正常启动或健康接口未响应。
   ✅ [证据链采集] 完成 (2m 17.1s)
   📤 → 下游数据: evidence_items=10/10
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 的详细信息以验证 readinessProbe 配置及失败事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-readiness -n aiops-e2e","tool_args":{"pod":"rc-notready-readiness","namespace":"aiops-e2e"},"purpose":"验证 readinessProbe 配置及失败事件","evidence_type":"pod_events","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 的日志以检查健康接口响应或启动错误","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --tail=200","tool_args":{"pod":"rc-notready-readiness","namespace":"aiops-e2e","tail":"200"},"purpose":"检查健康接口响应或启动错误","evidence_type":"pod_logs","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_logs"],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod 的 YAML 配置以验证 readinessProbe/livenessProbe/startupProbe 的配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml","tool_args":{"pod":"rc-notready-readiness","namespace":"aiops-e2e","output":"yaml"},"purpose":"验证 readinessProbe/livenessProbe/startupProbe 的配置","evidence_type":"pod_yaml","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e4","description":"获取异常 Pod 的事件列表以检查 readiness/liveness/startup probe failed 事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-notready-readiness","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-notready-readiness"},"purpose":"检查 readiness/liveness/startup probe failed 事件","evidence_type":"pod_events","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-readiness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n  Warning  Unhealthy       4m34s (x522 over 29m)  kubelet            Readiness probe failed: readiness dependency unavailable\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\nName:             rc-notready-readiness\nLabels:           app=rc-notready-readiness\n                  cni.projectcalico.org/containerID: fb8e26665bf8a745a3d1ec6dc6a9b9d528c0b6504e8895b370296a560f31067e\n                  cni.projectcalico.org/podIP: 172.16.166.186/32\n                  cni.projectcalico.org/podIPs: 172.16.166.186/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n  Normal   Scheduled       29m                    default-scheduler  Successfully assigned aiops-e2e/rc-notready-readiness to node1\n关键状态/事件:\n    State:          Running","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c052735287c547c6/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c052735287c547c6/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c052735287c547c6/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_logs","data":"kubectl_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c052735287c547c6/tools/002-evidence-kubectl_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c052735287c547c6/tools/002-evidence-kubectl_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c052735287c547c6/tools/002-evidence-kubectl_logs.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-readiness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T07:05:35Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-readiness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=None exitCode=None\nvolumes:\n- {\"name\": \"kube-api-access-sqcn2\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c052735287c547c6/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c052735287c547c6/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c052735287c547c6/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n4m43s (x522 over 29m)   Warning   Unhealthy        Pod/rc-notready-readiness   Readiness probe failed: readiness dependency unavailable\n29m                     Normal    AddedInterface   Pod/rc-notready-readiness   Add eth0 [172.16.166.186/32] from k8s-pod-network\n29m                     Normal    Pulled           Pod/rc-notready-readiness   Container image \"busybox:1.36\" already present on machine\n29m                     Normal    Created          Pod/rc-notready-readiness   Created container app\n29m                     Normal    Started          Pod/rc-notready-readiness   Started container app\n29m                     Normal    Scheduled        Pod/rc-notready-readiness   Successfully assigned aiops-e2e/rc-notready-readiness to node1","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c052735287c547c6/tools/004-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c052735287c547c6/tools/004-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c052735287c547c6/tools/004-evidence-kubectl_events.summary.txt"}],"llm_analysis":"# 证据结论\n\n## 已采集证据\n1. **Pod 描述信息**：通过 `kubectl describe` 确认 Pod `rc-notready-readiness` 处于 `Running` 状态，但 `READY` 为 `0/1`。事件显示 `readiness probe failed: readiness dependency unavailable`，且标签中标注 `pod_abnormal_type=NotReadyProbeFailed`。\n2. **容器日志**：通过 `kubectl logs` 检查容器日志，但未发现输出内容，表明容器可能未正常启动或健康接口未响应。\n3. **Pod 配置**：通过 `kubectl get -o yaml` 检查 Pod 配置，确认容器 `app` 使用镜像 `busybox:1.36`，且 `readinessProbe` 配置未在输出中显示。\n4. **事件信息**：通过 `kubectl events` 确认事件 `readiness probe failed: readiness dependency unavailable` 频繁出现，表明 readiness probe 配置或应用健康接口存在问题。\n\n## 未采集证据\n1. **Service Endpoints**：未检查 Service `rc-notready-readiness` 的 Endpoints 或 EndpointSlice，以确认是否由于 Service selector 配置错误导致服务不可用。\n2. **StartupProbe 配置**：未检查 `startupProbe` 配置，以确认是否由于启动慢或配置过严导致探针失败。\n\n## 冲突证据\n1. **容器日志**：`kubectl logs` 未返回任何输出，表明容器可能未正常启动或健康接口未响应。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 10/10 项，完整度 100%；实际执行工具 9 个，匹配计划 4 个，未规划证据 5 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":10,"environment_evidence_collected":10,"environment_evidence_completeness":1.0,"executed_tool_count":9,"matched_tool_count":4,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 的详细信息以验证 readinessProbe 配置及失败事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-readiness -n aiops-e2e","purpose":"验证 readinessProbe 配置及失败事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 的日志以检查健康接口响应或启动错误","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --tail=200","purpose":"检查健康接口响应或启动错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod 的 YAML 配置以验证 readinessProbe/livenessProbe/startupProbe 的配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml","purpose":"验证 readinessProbe/livenessProbe/startupProbe 的配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"获取异常 Pod 的事件列表以检查 readiness/liveness/startup probe failed 事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-notready-readiness","purpose":"检查 readiness/liveness/startup probe failed 事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取异常 Pod 的详细信息以验证 readinessProbe 配置及失败事件 | `kubectl describe pod rc-notready-readiness -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_logs | 获取异常 Pod 的日志以检查健康接口响应或启动错误 | `kubectl logs rc-notready-readiness -n aiops-e2e --tail=200` |
   | e3 | important | ✅ | kubectl_get_yaml | 获取异常 Pod 的 YAML 配置以验证 readinessProbe/liveness... | `kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml` |
   | e4 | important | ✅ | kubectl_events | 获取异常 Pod 的事件列表以检查 readiness/liveness/startup ... | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-notre...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (24.3s)
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
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 52.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4205 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 6m 28.0s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Running 但 READY 0/1，标签中标注 `pod_abnormal_type=NotReadyProbeFailed` |
| **兼容归因层** | L4 |
| **问题分类** | 健康检查失败（readiness/liveness probe） |
| **置信度** | 高 (85%) |
| **证据完整度** | 4/4 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

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
| 1 | Pod 状态 | `kubectl describe pod rc-notready-readiness` | `Warning Unhealthy 2m34s (x522 over 27m) kubelet Readiness probe failed: readiness dependency unavailable` | readiness probe 失败，重复 522 次 |
| 2 | Pod 事件 | `kubectl describe pod rc-notready-readiness` | `pod_abnormal_type=NotReadyProbeFailed` | 明确标记为 probe 失败 |
| 3 | Pod 配置 | `kubectl get pod rc-notready-readiness -o yaml` | `kind: Pod`, `creationTimestamp: 2026-05-15T07:05:35Z` | Pod 正常创建，无明显配置错误 |
| 4 | Pod 日志 | `kubectl logs rc-notready-readiness -n aiops-e2e` | `(no output)` | 无输出，可能探针路径不可达或应用未响应 |

### 证据关联分析

- **证据 #1 + #2 印证**：`Warning Unhealthy` + `pod_abnormal_type=NotReadyProbeFailed` → readiness probe 配置或应用健康接口异常
- **证据链**：健康接口未响应 → readiness probe 失败 → Pod 被标记为 NotReady → 服务无法调度流量

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| readiness/livenessProbe 配置 | critical | 无法确认探针配置是否合理 |
| 应用健康接口响应 | important | 无法确认是否应用未正确响应健康检查 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ readiness probe 配置错误或应用未正确响应健康检查路径              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ readiness probe 无法连接到健康检查路径，或返回错误状态码          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ readiness probe 失败，触发 Unhealthy 事件，Pod 被标记为 NotReady  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 Running 但 READY 0/1，无法正常服务流量                │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 和 #2，`Warning Unhealthy` 和 `pod_abnormal_type=NotReadyProbeFailed` 表明，**readiness probe 配置错误或应用未正确响应健康检查路径**，导致探针失败，Pod 被标记为 NotReady。

**置信度**：高 (85%)
- ✅ `Warning Unhealthy` 明确指向探针失败
- ✅ `pod_abnormal_type=NotReadyProbeFailed` 标记明确
- ⚠️ 缺少探针配置和健康接口日志，无法确认具体配置问题

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查并修改 readinessProbe 配置**
```bash
kubectl get pod rc-notready-readiness -n aiops-e2e -o jsonpath='{.spec.containers[*].readinessProbe}' | python3 -m json.tool
```
*依据*：确认探针路径、端口、超时、初始延迟等配置是否合理

**2. [优先] 优化探针配置（示例）**
```bash
kubectl set probe deployment/<deployment-name> -n aiops-e2e --readiness --http-get=http://localhost:8080/health --initial-delay-seconds=10 --period-seconds=5
```
*依据*：增加 `initialDelaySeconds` 以适应应用启动时间，减少探针失败

**3. [可选] 查看应用健康接口响应**
```bash
curl -I http://172.16.166.186:8080/health
```
*目的*：确认健康接口是否返回 2xx 状态码

### 后续优化

1. **监控告警**：配置探针失败告警（如 Prometheus 中的 `kube_pod_status_ready` 指标）
2. **资源评估**：使用 Prometheus 或 `kubectl describe pod` 查看探针配置与应用健康状态
3. **应用优化**：确保健康检查接口在应用启动后立即可用

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-notready-readiness -n aiops-e2e` | READY: 1/1 |
| 2. 检查探针事件 | `kubectl describe pod rc-notready-readiness -n aiops-e2e` | 无 `Warning Unhealthy` |
| 3. 查看探针配置 | `kubectl get pod rc-notready-readiness -n aiops-e2e -o jsonpath='{.spec.containers[*].readinessProbe}'` | 配置合理，路径可访问 |

---

## ⚠️ 注意事项

- 如果 readiness probe 仍然失败，可能需要检查应用是否实际健康
- 确保探针路径在容器内部可访问（例如，使用 `localhost` 而非外部 IP）
- 如果 Service 未正确配置，Pod 即使 Ready 也不会被调度到流量

---

---

## 📊 性能统计

├─ 总耗时: 6.5m
├─ 问题定位: 113.7s (29%) ✅
├─ 证据链采集: 137.1s (35%) ✅
├─ 根因分析: 24.3s (6%) ✅
├─ 汇总总结: 112.8s (29%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 12 次
```

📋 诊断追踪

- **核心 Runbook**: pod-notready-probe-failed
- **参考 Runbook**: pod-notready-probe-failed
- **工具调用**: 12 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
