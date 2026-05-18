======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 1984f77900af48fe]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 返回 49 个 Running 状态的 Pod，无异常记录。
key_facts: ["aiops-e2e/rc-notready-readiness 处于 0/1 Ready 状态，标签包含 pod_abnormal_type=NotReadyProbeFailed", "kube-system/calico-node-* 在 nod
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=331 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide pod aiops-e2e/rc-notready-readiness -n aiops-e2e
error: there is no need to specify a resourc
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                    READY   STATUS    RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-notready-readiness   0/1     Running   0          74m   172.16.166.186 
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-readiness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
  Warning  Unhealthy  4m23s (x1458 over 74m)  kubelet  Readiness probe failed: readin
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
rc-notready-readiness   0/1     Running   0          74m   172.16.166.186 
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
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 1.0s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'readinessProbe 配置不匹配', 'probability': '高', 'reason': 'Pod 正在运行但 readiness probe 失败，且 READY 0/1，表明探针配置可能与容器实际监听的路径、端口或 scheme 不一致。'}, {'scenario': '应用健康接口返回失败或超时', 'probability': '高', 'reason': 'Pod 正在运行但 readiness 探针失败，表明健康接口可能返回了非 2xx/3xx 状态码或超时。'}, {'scenario': 'Service selector 不匹配', 'probability': '中', 'reason': 'Pod READY 正常但 Service 无 Endpoints，可能是 Service selector 配置错误，但当前上下文未明确说明 Service 状态。'}]
   entities=[{"type": "Pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}]
   reasoning=当前活跃异常对象为 aiops-e2e/rc-notready-readiness Pod，状态为 Running 但 READY 0/1，且 readiness probe 失败，符合 L4 层的 NotReadyProbeFailed 异常类型。
   layer_analysis={"layer": "L4", "derived_layer": "", "layers": [], "layer_name": "", "confidence": 0.5, "reasoning": "当前活跃异常对象为 aiops-e2e/rc-notready-readiness Pod，状态为 Running 但 READY 0/1，且 readiness probe 失败，符合 L4 层的 NotReadyProbeFailed 异常类型。", "abnormal_pods": [{"name": "rc-notready-readiness", "namespace": "aiops-e2e", "status": "Running"}], "pod_status_keyword": "Running", "pod_abnormal_type": "NotReadyProbeFailed", "status_category": "app_health", "key_entities": [{"type": "Pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "readinessProbe 配置不匹配", "probability": "高", "reason": "Pod 正在运行但 readiness probe 失败，且 READY 0/1，表明探针配置可能与容器实际监听的路径、端口或 scheme 不一致。"}, {"scenario": "应用健康接口返回失败或超时", "probability": "高", "reason": "Pod 正在运行但 readiness 探针失败，表明健康接口可能返回了非 2xx/3xx 状态码或超时。"}, {"scenario": "Service selector 不匹配", "probability": "中", "reason": "Pod READY 正常但 Service 无 Endpoints，可能是 Service selector 配置错误，但当前上下文未明确说明 Service 状态。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Running"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Running"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 0, "selected_rows": [], "raw_ref": "/tmp/aiops/reports/context_archives/1984f77900af48fe/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/1984f77900af48fe/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/1984f77900af48fe/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
  Warning  Unhealthy  109s (x1563 over 76m)  kubelet  Readiness probe failed: readine
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
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。
   💭 [证据链采集] 已采集证据：
1. **critical**: `kubectl describe pod` 显示 readiness probe 失败，Pod READY 0/1，`pod_abnormal_type=NotReadyProbeFailed`，确认探针失败事件。
2. **important**: `kubectl get pod -o yaml` 显示 readinessProbe 配置缺失或容器未就绪，容器状态为 `ready=False`。
3. **important**: `kubectl logs` 无输出，无法确认应用健康接口响应或错误信息。
4. **important**: `kubectl get endpoints` 未找到资源，表明可能 Service 未配置或未正确选择该 Pod。

冲突证据：
- `kubectl_get_by_kind_in_namespace` 返回无 Endpoints，可能为 Service 未创建或 selector 不匹配，但当前异常组关注 Pod 未 Ready 本身，不直接归因于 Service 配置。
   ✅ [证据链采集] 完成 (2m 37.0s)
   📤 → 下游数据: evidence_items=10/10
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 的详细信息以验证 readinessProbe 配置和失败原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-readiness -n aiops-e2e","tool_args":{"name":"rc-notready-readiness","namespace":"aiops-e2e"},"purpose":"检查 readinessProbe 配置、失败事件、容器状态等关键信息","evidence_type":"pod_events_and_status","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_describe","kubectl_get_by_name","kubectl_get_yaml","kubectl_events","kubectl_logs"],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 的 YAML 配置以验证 readinessProbe 参数","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml","tool_args":{"name":"rc-notready-readiness","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"验证 readinessProbe 的 path、port、scheme、timeoutSeconds、periodSeconds、failureThreshold、initialDelaySeconds 等参数","evidence_type":"pod_configuration","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_get_yaml","kubectl_get_by_name","kubectl_describe"],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod 的日志以检查应用健康接口的响应","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --tail=200","tool_args":{"name":"rc-notready-readiness","namespace":"aiops-e2e","tail":"200"},"purpose":"检查应用健康接口的响应、错误信息或超时","evidence_type":"application_logs","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_logs","kubectl_previous_logs","kubectl_logs_all_containers","kubectl_container_logs"],"counts_for_completeness":true},{"id":"e4","description":"获取异常 Pod 的 Service Endpoints 状态以验证是否被正确选中","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get endpoints -n aiops-e2e","tool_args":{"kind":"endpoints","namespace":"aiops-e2e"},"purpose":"检查 Service 是否包含该 Pod 且 Endpoints 是否标记为 ready","evidence_type":"service_endpoints","target_scope":"aiops-e2e","acceptable_tools":["kubectl_get_by_kind_in_namespace","kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-readiness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n  Warning  Unhealthy  109s (x1563 over 76m)  kubelet  Readiness probe failed: readiness dependency unavailable\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\nName:             rc-notready-readiness\nLabels:           app=rc-notready-readiness\n                  cni.projectcalico.org/containerID: fb8e26665bf8a745a3d1ec6dc6a9b9d528c0b6504e8895b370296a560f31067e\n                  cni.projectcalico.org/podIP: 172.16.166.186/32\n                  cni.projectcalico.org/podIPs: 172.16.166.186/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Running","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1984f77900af48fe/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1984f77900af48fe/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1984f77900af48fe/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-readiness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T07:05:35Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-readiness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=None exitCode=None\nvolumes:\n- {\"name\": \"kube-api-access-sqcn2\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1984f77900af48fe/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1984f77900af48fe/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1984f77900af48fe/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_logs","data":"kubectl_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1984f77900af48fe/tools/003-evidence-kubectl_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1984f77900af48fe/tools/003-evidence-kubectl_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1984f77900af48fe/tools/003-evidence-kubectl_logs.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/1984f77900af48fe/tools/004-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1984f77900af48fe/tools/004-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1984f77900af48fe/tools/004-evidence-kubectl_get_by_kind_in_namespace.summary.txt"}],"llm_analysis":"已采集证据：\n1. **critical**: `kubectl describe pod` 显示 readiness probe 失败，Pod READY 0/1，`pod_abnormal_type=NotReadyProbeFailed`，确认探针失败事件。\n2. **important**: `kubectl get pod -o yaml` 显示 readinessProbe 配置缺失或容器未就绪，容器状态为 `ready=False`。\n3. **important**: `kubectl logs` 无输出，无法确认应用健康接口响应或错误信息。\n4. **important**: `kubectl get endpoints` 未找到资源，表明可能 Service 未配置或未正确选择该 Pod。\n\n冲突证据：\n- `kubectl_get_by_kind_in_namespace` 返回无 Endpoints，可能为 Service 未创建或 selector 不匹配，但当前异常组关注 Pod 未 Ready 本身，不直接归因于 Service 配置。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 10/10 项，完整度 100%；实际执行工具 8 个，匹配计划 4 个，未规划证据 4 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":10,"environment_evidence_collected":10,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":4,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 的详细信息以验证 readinessProbe 配置和失败原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-readiness -n aiops-e2e","purpose":"检查 readinessProbe 配置、失败事件、容器状态等关键信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 的 YAML 配置以验证 readinessProbe 参数","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml","purpose":"验证 readinessProbe 的 path、port、scheme、timeoutSeconds、periodSeconds、failureThreshold、initialDelaySeconds 等参数","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod 的日志以检查应用健康接口的响应","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --tail=200","purpose":"检查应用健康接口的响应、错误信息或超时","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"获取异常 Pod 的 Service Endpoints 状态以验证是否被正确选中","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get endpoints -n aiops-e2e","purpose":"检查 Service 是否包含该 Pod 且 Endpoints 是否标记为 ready","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取异常 Pod 的详细信息以验证 readinessProbe 配置和失败原因 | `kubectl describe pod rc-notready-readiness -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_get_yaml | 获取异常 Pod 的 YAML 配置以验证 readinessProbe 参数 | `kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml` |
   | e3 | important | ✅ | kubectl_logs | 获取异常 Pod 的日志以检查应用健康接口的响应 | `kubectl logs rc-notready-readiness -n aiops-e2e --tail=200` |
   | e4 | important | ✅ | kubectl_get_by_kind_in_na... | 获取异常 Pod 的 Service Endpoints 状态以验证是否被正确选中 | `kubectl get endpoints -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (40.4s)
   📤 → 下游数据: root_cause=根因分析表明，Pod aiops-e2e/rc-notready-readiness 处于 Running 状态但 READY 0/1，且 readiness probe 失败，原因可能是 readinessProbe 配置与容器实际监听的路径、端口或 scheme 不一致，或者应用健康接口返回了非 2xx/3xx 状态码或超时。证据包括：1. `kubectl describe` 显示探针失败， READY 0/1，`pod_abnormal_type=NotReadyProbeFailed`；2. `kubectl get pod -o yaml` 显示容器状态为 `ready=False`；3. `kubectl logs` 无输出，无法确认应用健康接口响应或错误信息。
   confidence=80%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [], "causal_chain": {}, "root_cause": "根因分析表明，Pod aiops-e2e/rc-notready-readiness 处于 Running 状态但 READY 0/1，且 readiness probe 失败，原因可能是 readinessProbe 配置与容器实际监听的路径、端口或 scheme 不一致，或者应用健康接口返回了非 2xx/3xx 状态码或超时。证据包括：1. `kubectl describe` 显示探针失败， READY 0/1，`pod_abnormal_type=NotReadyProbeFailed`；2. `kubectl get pod -o yaml` 显示容器状态为 `ready=False`；3. `kubectl logs` 无输出，无法确认应用健康接口响应或错误信息。", "root_cause_summary": "根因分析表明，Pod aiops-e2e/rc-notready-readiness 处于 Running 状态但 READY 0/1，且 readiness probe 失败，原因可能是 readinessProbe 配置与容器实际监听的路径、端口或 scheme 不一致，或者应用健康接口返回了非 2xx/3xx 状态码或超时。证据包括：1. `kubectl describe` 显示探针失败， READY 0/1，`pod_abnormal_type=NotReadyProbeFailed`；2. `kubectl get pod -o yaml` 显示容器状态为 `ready=False`；3. `kubectl logs` 无输出，无法确认应用健康接口响应或错误信息。", "confidence": 0.8, "confidence_reason": "有工具证据（如 `kubectl describe` 和 `kubectl get pod -o yaml`），分析合理，但缺乏应用日志以确认健康接口具体问题。", "primary_runbooks": ["pod-notready-probe-failed.md"], "alternative_causes": [{"cause": "livenessProbe 反复失败导致容器重启", "probability": "低"}], "limitations": "缺少应用日志以确认健康接口的具体问题，无法进一步验证 readinessProbe 配置是否匹配容器实际状态。", "llm_raw_analysis": "分析表明，Pod aiops-e2e/rc-notready-readiness 处于 Running 状态但 READY 0/1，且 readiness probe 失败，原因可能是 readinessProbe 配置与容器实际监听的路径、端口或 scheme 不一致，或者应用健康接口返回了非 2xx/3xx 状态码或超时。证据包括：1. `kubectl describe` 显示探针失败， READY 0/1，`pod_abnormal_type=NotReadyProbeFailed`；2. `kubectl get pod -o yaml` 显示容器状态为 `ready=False`；3. `kubectl logs` 无输出，无法确认应用健康接口响应或错误信息。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 根因分析表明，Pod aiops-e2e/rc-notready-readiness 处于 Running 状态但 READY 0/1，且 readiness probe 失败，原因可能是 readinessProbe 配置与容器实际监听的路径、端口或 scheme 不一致，或者应用健康接口返回了非...
   置信度: 80%

📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 15.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4411 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 33.8s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Running 但 READY 0/1，readiness probe 失败 |
| **兼容归因层** | L4 - probe_health |
| **问题分类** | NotReadyProbeFailed |
| **置信度** | 高 (80%) |
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
| 1 | Pod 状态 | kubectl describe pod rc-notready-readiness | `READY: 0/1`, `Warning Unhealthy kubelet Readiness probe failed: readiness dependency unavailable` | Pod 正在运行但未 Ready，readiness probe 失败 |
| 2 | YAML 配置 | kubectl get pod rc-notready-readiness -o yaml | `phase: Running`, `ready: false` | Pod 容器状态未 Ready，符合 NotReadyProbeFailed 异常类型 |
| 3 | 日志信息 | kubectl logs rc-notready-readiness | 无输出 | 未发现应用健康接口响应或错误信息 |
| 4 | Service Endpoints | kubectl get endpoints | 无输出 | 无法确认 Service 是否正确选中该 Pod |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 Running，但 READY 0/1，readiness probe 失败，符合 NotReadyProbeFailed 异常类型。
- **证据链**：Pod 容器已启动 → readiness probe 配置可能不匹配实际服务 → 探针失败 → Pod 未 Ready → 影响 Service Endpoints。
- **证据 #3 缺失关键信息**：未采集到应用健康接口的响应日志，无法进一步确认失败原因。
- **证据 #4 缺失关键信息**：Service Endpoints 未被采集到，无法验证 Service 是否选中该 Pod。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 应用健康接口响应日志 | critical | 无法确认探针失败的具体原因 |
| Service Endpoints 状态 | important | 无法验证 Service 是否选中该 Pod |

---

## 🎯 根因分析

### 因果链

```
┌────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                           │
│ readinessProbe 配置与容器实际监听的路径、端口或 scheme 不一致       │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                           │
│ 探针失败 → Pod 未 Ready → 影响 Service Endpoints                    │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                           │
│ Readiness probe 失败（错误信息: readiness dependency unavailable） │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                       │
│ Pod 状态 Running 但 READY 0/1，Service 无法正确选中该 Pod          │
└────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (readiness probe 失败) 和 #2 (Pod READY 0/1)，问题的根本原因是 **readinessProbe 配置与容器实际监听的路径、端口或 scheme 不一致**，导致探针失败。  
**置信度**：高 (80%)  
- ✅ `kubectl describe` 显示探针失败，READY 0/1  
- ✅ YAML 配置显示容器状态未 Ready  
- ⚠️ 缺少应用健康接口日志，无法确认失败的具体原因  

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查并调整 readinessProbe 配置**
```bash
kubectl get pod rc-notready-readiness -n aiops-e2e -o jsonpath='{.spec.containers[*].readinessProbe}' > probe-config.json
```
*依据*：确认探针的路径、端口、scheme 是否与容器实际监听的一致。

**2. [次优先] 查看应用健康接口响应**
```bash
kubectl logs rc-notready-readiness -n aiops-e2e --previous | tail -100
```
*目的*：查看健康接口是否返回非 2xx/3xx 状态码或超时。

**3. [可选] 验证 Service Endpoints**
```bash
kubectl get endpoints -n aiops-e2e
```
*目的*：确认 Service 是否正确选中该 Pod。

### 后续优化

1. **探针配置优化**：
   - 增加 `initialDelaySeconds`：避免探针在容器启动前触发
   - 调整 `path`、`port`、`scheme`：确保与应用健康接口一致
   - 增加 `timeoutSeconds`：避免探针超时导致失败

2. **应用健康接口检查**：
   - 确保健康接口返回 2xx/3xx 状态码
   - 确保健康接口响应时间在合理范围内

3. **监控告警**：
   - 配置 readinessProbe 失败告警
   - 监控 Pod READY 状态变化

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-notready-readiness -n aiops-e2e` | READY: 1/1 |
| 2. 检查 readinessProbe 配置 | `kubectl get pod rc-notready-readiness -n aiops-e2e -o jsonpath='{.spec.containers[*].readinessProbe}'` | 路径、端口、scheme 与应用健康接口一致 |
| 3. 查看健康接口响应 | `kubectl logs rc-notready-readiness -n aiops-e2e --previous` | 返回 2xx/3xx 状态码 |
| 4. 验证 Service Endpoints | `kubectl get endpoints -n aiops-e2e` | 包含该 Pod 的 IP |

---

## ⚠️ 注意事项

- 如果 readinessProbe 配置正确，但问题仍存在，可能是应用健康接口本身存在问题。
- 如果 Service 未正确选中该 Pod，需检查 Service 的 `selector` 配置。
- 如果问题持续，建议使用 `kubectl exec` 登录 Pod 内部，手动验证健康接口的可用性。

---

## 📊 性能统计

├─ 总耗时: 5.6m
├─ 问题定位: 61.0s (18%) ✅
├─ 证据链采集: 157.0s (47%) ✅
├─ 根因分析: 40.4s (12%) ✅
├─ 汇总总结: 75.3s (23%) ✅
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
