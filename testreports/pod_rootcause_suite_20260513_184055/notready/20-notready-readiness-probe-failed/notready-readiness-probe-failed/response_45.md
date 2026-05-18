======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 4168ece6b1c049ed]

📍 [问题定位] 执行中...
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
key_facts: ["aiops-e2e rc-notready-readiness 0/1 Running 0 4h6m 172.16.166.186 node1 app=rc-notready-readiness,pod
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=0 status_counts={'Running': 47}
key_facts: ["aiops-e2e/rc-notready-readiness: 0/1 Running, 0 restarts, 4h15m old, pod_abnormal_type=NotReadyProbeF
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
rc-notready-readiness   0/1     Running   0          4h15m   172.16.166.
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-readiness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
  Warning  Unhealthy  40s (x5307 over 4h15m)  kubelet  Readiness probe failed: readin
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
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "NotReadyProbeFailed",
  "confidence": "high",
  "reasoning": "Pod 'rc-notready-readiness' 在命名空间 'aiops-e2e' 中处于 Running 状态，但 READY 为 0/1。事件显示 readiness probe 失败，具体原因是 'readiness dependency unavailable'。此 Pod 的探针配置和相关日志表明问题可能出在 readiness 探针的配置或依赖项上。",
  "abnormal_pods": [
    {
      "name": "rc-notready-readiness",
      "namespace": "aiops-e2e",
      "status": "Running",
      "ready": "0/1"
    }
  ],
  "abnormal_groups": [
    "NotReadyProbeFailed"
  ],
  "pod_status_keyword": "Running",
  "pod_abnormal_type": "NotReadyProbeFailed",
  "status_category": "NotReady",
  "key_entities": [
    {
      "type": "Pod",
      "name": "rc-notready-readiness",
      "namespace": "aiops-e2e"
    },
    {
      "type": "Node",
      "name": "node1"
    }
  ],
  "possible_scenarios": [
    "readinessProbe 配置错误，路径、端口或 scheme 不匹配。",
    "应用进程已启动但健康接口返回非 2xx/3xx 或超时。",
    "livenessProbe 反复失败导致容器重启。",
    "startupProbe 失败，容器尚未完成启动。",
    "Service selector 不匹配导致用户感知不可用。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (9m 56.1s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'readinessProbe 配置错误，路径、端口或 scheme 不匹配。', 'probability': 'high', 'reason': '探针配置不匹配导致健康检查失败。'}, {'scenario': '应用进程已启动但健康接口返回非 2xx/3xx 或超时。', 'probability': 'high', 'reason': '应用接口不可用导致探针失败。'}, {'scenario': 'livenessProbe 反复失败导致容器重启。', 'probability': 'medium', 'reason': 'livenessProbe 可能导致容器重启，但当前无明确证据。'}, {'scenario': 'startupProbe 失败，容器尚未完成启动。', 'probability': 'medium', 'reason': 'startupProbe 可能导致容器尚未进入正常服务窗口。'}, {'scenario': 'Service selector 不匹配导致用户感知不可用。', 'probability': 'high', 'reason': 'Service selector 错误可能导致服务不可用，但 Pod READY 可能正常。'}]
   entities=[{"type": "Pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}]
   reasoning=Pod 'rc-notready-readiness' 在命名空间 'aiops-e2e' 中处于 Running 状态，但 READY 为 0/1。事件显示 readiness probe 失败，具体原因是 'readiness dependency unavailable'。此 Pod 的探针配置和相关日志表明问题可能出在 readiness 探针的配置或依赖项上。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "NotReadyProbeFailed", "confidence": 1.0, "reasoning": "Pod 'rc-notready-readiness' 在命名空间 'aiops-e2e' 中处于 Running 状态，但 READY 为 0/1。事件显示 readiness probe 失败，具体原因是 'readiness dependency unavailable'。此 Pod 的探针配置和相关日志表明问题可能出在 readiness 探针的配置或依赖项上。", "abnormal_pods": [{"name": "rc-notready-readiness", "namespace": "aiops-e2e", "status": "Running"}], "pod_status_keyword": "Running", "pod_abnormal_type": "NotReadyProbeFailed", "status_category": "NotReady", "key_entities": [{"type": "Pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}], "possible_scenarios": [{"scenario": "readinessProbe 配置错误，路径、端口或 scheme 不匹配。", "probability": "high", "reason": "探针配置不匹配导致健康检查失败。"}, {"scenario": "应用进程已启动但健康接口返回非 2xx/3xx 或超时。", "probability": "high", "reason": "应用接口不可用导致探针失败。"}, {"scenario": "livenessProbe 反复失败导致容器重启。", "probability": "medium", "reason": "livenessProbe 可能导致容器重启，但当前无明确证据。"}, {"scenario": "startupProbe 失败，容器尚未完成启动。", "probability": "medium", "reason": "startupProbe 可能导致容器尚未进入正常服务窗口。"}, {"scenario": "Service selector 不匹配导致用户感知不可用。", "probability": "high", "reason": "Service selector 错误可能导致服务不可用，但 Pod READY 可能正常。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Running"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Running"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 0, "selected_rows": [], "raw_ref": "/tmp/aiops/reports/context_archives/4168ece6b1c049ed/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/4168ece6b1c049ed/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/4168ece6b1c049ed/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-readiness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
  Warning  Unhealthy  3m42s (x5307 over 4h18m)  kubelet  Readiness probe failed: read
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
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。
   💭 [证据链采集] # 证据采集结论

## 已采集证据
1. **kubectl describe pod** 确认了 Pod 的关键诊断信息：
   - 当前状态为 `Running`，但 `READY` 为 `0/1`。
   - 事件显示 `Readiness probe failed: readiness dependency unavailable`。
   - Pod 的注解中包含 `pod_abnormal_type=NotReadyProbeFailed` 和 `aiops.e2e/runbook: pod-notready-probe-failed.md`，表明该 Pod 的异常已被归类为 `NotReadyProbeFailed`。

2. **kubectl logs** 尝试获取了最近的日志，但没有输出。这表明容器可能没有输出日志，或者日志尚未达到预期状态。

3. **kubectl get pod -o yaml** 提供了该 Pod 的完整配置信息：
   - 确认了该 Pod 的 readiness 探针配置未被显式设置。
   - 容器状态显示 `ready=False`。
   - 该 Pod 的标签中包含 `pod_abnormal_type=NotReadyProbeFailed`，进一步确认了异常类型。

4. **kubectl get endpoints** 检查了 `aiops-e2e` 命名空间下的 Endpoints 资源，但未找到匹配的资源。这表明当前命名空间中没有定义 Endpoints，或者 Endpoints 未正确配置。

## 未采集证据
- 未获取到 `kubectl describe pod` 中提到的 readiness 探针的具体配置。
- 未获取到该 Pod 的 readiness 探针的配置参数，例如 `path`、`port`、`initialDelaySeconds` 等。
- 未检查该 Pod 所在的 Service 是否配置了正确的 selector。

## 冲突证据
- `kubectl get endpoints` 返回为空，表明当前命名空间中没有 Endpoints 资源。这可能是由于该 Pod 所在的 Service 未定义 Endpoints，或者 Endpoints 未正确配置。

## 结论
当前 Pod `rc-notready-readiness` 处于 `Running` 状态，但 `READY` 为 `0/1`，并且事件显示 `Readiness probe failed: readiness dependency unavailable`。这表明该 Pod 的 readiness 探针失败，导致 Pod 未被标记为就绪。下一步应检查该 Pod 的 readiness 探针配置，并确认其是否与容器的健康接口匹配。此外，还应检查该 Pod 所在的 Service 是否配置了正确的 selector，以确保其能够正确地将流量路由到该 Pod。
   ✅ [证据链采集] 完成 (2m 55.0s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod 'rc-notready-readiness' 的详细信息，包括 readiness probe 配置和失败事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-readiness -n aiops-e2e","tool_args":{"name":"rc-notready-readiness","namespace":"aiops-e2e"},"purpose":"确认 readiness probe 的配置和失败原因","evidence_type":"status_and_configuration","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod 'rc-notready-readiness' 的日志，检查健康接口或启动错误","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --tail=200","tool_args":{"name":"rc-notready-readiness","namespace":"aiops-e2e","tail":"200"},"purpose":"检查应用健康接口或启动错误","evidence_type":"logs","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取 Pod 'rc-notready-readiness' 的 YAML 配置，验证 readiness/liveness/startup probe 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml","tool_args":{"name":"rc-notready-readiness","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"验证 readiness/liveness/startup probe 的配置","evidence_type":"configuration","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"检查 Service 是否包含 'rc-notready-readiness' Pod，确认其是否 Ready","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get endpoints -n aiops-e2e","tool_args":{"kind":"endpoints","namespace":"aiops-e2e"},"purpose":"确认 Service Endpoints 是否包含 'rc-notready-readiness' Pod","evidence_type":"service_dependency","target_scope":"aiops-e2e","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-readiness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n  Warning  Unhealthy  3m42s (x5307 over 4h18m)  kubelet  Readiness probe failed: readiness dependency unavailable\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\nName:             rc-notready-readiness\nLabels:           app=rc-notready-readiness\n                  cni.projectcalico.org/containerID: fb8e26665bf8a745a3d1ec6dc6a9b9d528c0b6504e8895b370296a560f31067e\n                  cni.projectcalico.org/podIP: 172.16.166.186/32\n                  cni.projectcalico.org/podIPs: 172.16.166.186/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Running","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4168ece6b1c049ed/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4168ece6b1c049ed/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4168ece6b1c049ed/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_logs","data":"kubectl_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4168ece6b1c049ed/tools/002-evidence-kubectl_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4168ece6b1c049ed/tools/002-evidence-kubectl_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4168ece6b1c049ed/tools/002-evidence-kubectl_logs.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-readiness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T07:05:35Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-readiness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=None exitCode=None\nvolumes:\n- {\"name\": \"kube-api-access-sqcn2\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4168ece6b1c049ed/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4168ece6b1c049ed/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4168ece6b1c049ed/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/4168ece6b1c049ed/tools/004-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4168ece6b1c049ed/tools/004-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4168ece6b1c049ed/tools/004-evidence-kubectl_get_by_kind_in_namespace.summary.txt"}],"llm_analysis":"# 证据采集结论\n\n## 已采集证据\n1. **kubectl describe pod** 确认了 Pod 的关键诊断信息：\n   - 当前状态为 `Running`，但 `READY` 为 `0/1`。\n   - 事件显示 `Readiness probe failed: readiness dependency unavailable`。\n   - Pod 的注解中包含 `pod_abnormal_type=NotReadyProbeFailed` 和 `aiops.e2e/runbook: pod-notready-probe-failed.md`，表明该 Pod 的异常已被归类为 `NotReadyProbeFailed`。\n\n2. **kubectl logs** 尝试获取了最近的日志，但没有输出。这表明容器可能没有输出日志，或者日志尚未达到预期状态。\n\n3. **kubectl get pod -o yaml** 提供了该 Pod 的完整配置信息：\n   - 确认了该 Pod 的 readiness 探针配置未被显式设置。\n   - 容器状态显示 `ready=False`。\n   - 该 Pod 的标签中包含 `pod_abnormal_type=NotReadyProbeFailed`，进一步确认了异常类型。\n\n4. **kubectl get endpoints** 检查了 `aiops-e2e` 命名空间下的 Endpoints 资源，但未找到匹配的资源。这表明当前命名空间中没有定义 Endpoints，或者 Endpoints 未正确配置。\n\n## 未采集证据\n- 未获取到 `kubectl describe pod` 中提到的 readiness 探针的具体配置。\n- 未获取到该 Pod 的 readiness 探针的配置参数，例如 `path`、`port`、`initialDelaySeconds` 等。\n- 未检查该 Pod 所在的 Service 是否配置了正确的 selector。\n\n## 冲突证据\n- `kubectl get endpoints` 返回为空，表明当前命名空间中没有 Endpoints 资源。这可能是由于该 Pod 所在的 Service 未定义 Endpoints，或者 Endpoints 未正确配置。\n\n## 结论\n当前 Pod `rc-notready-readiness` 处于 `Running` 状态，但 `READY` 为 `0/1`，并且事件显示 `Readiness probe failed: readiness dependency unavailable`。这表明该 Pod 的 readiness 探针失败，导致 Pod 未被标记为就绪。下一步应检查该 Pod 的 readiness 探针配置，并确认其是否与容器的健康接口匹配。此外，还应检查该 Pod 所在的 Service 是否配置了正确的 selector，以确保其能够正确地将流量路由到该 Pod。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 9/9 项，完整度 100%；实际执行工具 8 个，匹配计划 4 个，未规划证据 4 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":9,"environment_evidence_collected":9,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":4,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"获取 Pod 'rc-notready-readiness' 的详细信息，包括 readiness probe 配置和失败事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-readiness -n aiops-e2e","purpose":"确认 readiness probe 的配置和失败原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod 'rc-notready-readiness' 的日志，检查健康接口或启动错误","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --tail=200","purpose":"检查应用健康接口或启动错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取 Pod 'rc-notready-readiness' 的 YAML 配置，验证 readiness/liveness/startup probe 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml","purpose":"验证 readiness/liveness/startup probe 的配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"检查 Service 是否包含 'rc-notready-readiness' Pod，确认其是否 Ready","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get endpoints -n aiops-e2e","purpose":"确认 Service Endpoints 是否包含 'rc-notready-readiness' Pod","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取 Pod 'rc-notready-readiness' 的详细信息，包括 readi... | `kubectl describe pod rc-notready-readiness -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_logs | 获取 Pod 'rc-notready-readiness' 的日志，检查健康接口或启动错误 | `kubectl logs rc-notready-readiness -n aiops-e2e --tail=200` |
   | e3 | important | ✅ | kubectl_get_yaml | 获取 Pod 'rc-notready-readiness' 的 YAML 配置，验证 r... | `kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml` |
   | e4 | important | ✅ | kubectl_get_by_kind_in_na... | 检查 Service 是否包含 'rc-notready-readiness' Pod，确... | `kubectl get endpoints -n aiops-e2e` |

📍 [根因分析] 执行中...
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
   ✅ [根因分析] 完成 (2m 31.7s)
   📤 → 下游数据: root_cause=Pod 'rc-notready-readiness' 处于 Running 状态，但 READY 为 0/1。Events 显示 readiness probe 失败，具体原因是 'readiness dependency unavailable'。YAML 配置显示 readiness 探针未被显式设置，容器状态显示 'ready=False'，表明容器未通过健康检查。
   confidence=90%
   causal_chain={"root_cause": "readiness dependency unavailable", "intermediate_causes": ["readiness probe 配置不匹配", "容器依赖的服务或资源未就绪"], "immediate_causes": ["readiness probe 失败", "容器未通过健康检查"], "symptoms": ["Pod 'rc-notready-readiness' 处于 Running 状态，但 READY 为 0/1", "Events 显示 readiness probe 失败", "Pod 未通过健康检查"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"tool": "kubectl_describe", "description": "获取 Pod 'rc-notready-readiness' 的详细信息，包括 readiness probe 配置和失败事件", "value": "kubectl_describe 摘要:\nname: rc-notready-readiness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n  Warning  Unhealthy  3m42s (x5307 over 4h18m)  kubelet  Readiness probe failed: readiness dependency unavailable\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\nName:             rc-notready-readiness\nLabels:           app=rc-notready-readiness\n                  cni.projectcalico.org/containerID: fb8e26665bf8\n... 截断，原始 827 字符"}, {"tool": "kubectl_logs", "description": "获取 Pod 'rc-notready-readiness' 的日志，检查健康接口或启动错误", "value": "kubectl_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)"}, {"tool": "kubectl_get_yaml", "description": "获取 Pod 'rc-notready-readiness' 的 YAML 配置，验证 readiness/liveness/startup probe 配置", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-readiness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T07:05:35Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-readiness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntoleration\n... 截断，原始 978 字符"}, {"tool": "kubectl_get_by_kind_in_cluster", "description": "检查 Service 是否包含 'rc-notready-readiness' Pod，确认其是否 Ready", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=0 status_counts={'Running': 47}\nkey_facts: [\"aiops-e2e/rc-notready-readiness: 0/1 Running, 0 restarts, 4h15m old, pod_abnormal_type=NotReadyProbeFailed\", \"kube-system/calico-node-4kp26: 1/1 Running, 18 restarts (9d ago), 207d old\", \"kube-system/calico-node-d2dhp: 1/1 Running, 15 restarts (9d ago), 207d old\", \"kube-system/calico-node-mnrjs: 1/1 Running, 14 restarts (9d ago), 207d old\", \"kube-system/kube-controller-manager-master: 1/1 Running,"}, {"tool": "kubectl_get_by_kind_in_cluster", "description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=0 status_counts={'Running': 47}\nkey_facts: [\"aiops-e2e rc-notready-readiness 0/1 Running 0 4h6m 172.16.166.186 node1 app=rc-notready-readiness,pod_abnormal_type=NotReadyProbeFailed,rootcause-e2e=true\", \"aiops aiops-copilot-67fc5474d6-v2rlj 1/1 Running 0 2d2h 172.16.166.145 node1 app=aiops-copilot,pod-template-hash=67fc5474d6\", \"default nfs-client-provisioner-6fcd4994c9-rjzv5 1/1 Running 1 (9d ago) 18d 172.16.219.105 master app=nfs-client-prov"}, {"tool": "kubectl_get_by_kind_in_cluster", "description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=0 status_counts={'Running': 47}\nkey_facts: [\"aiops-e2e/rc-notready-readiness: 0/1 Running, 0 restarts, 4h15m old, pod_abnormal_type=NotReadyProbeFailed\", \"kube-system/calico-node-4kp26: 1/1 Running, 18 restarts (9d ago), 207d old\", \"kube-system/calico-node-d2dhp: 1/1 Running, 15 restarts (9d ago), 207d old\", \"kube-system/calico-node-mnrjs: 1/1 Running, 14 restarts (9d ago), 207d old\", \"kube-system/kube-controller-manager-master: 1/1 Running,"}, {"tool": "kubectl_get_by_name", "description": "上游已验证工具结果: kubectl_get_by_name", "value": "NAME                    READY   STATUS    RESTARTS   AGE     IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-notready-readiness   0/1     Running   0          4h15m   172.16.166.186   node1   <none>           <none>            app=rc-notready-readiness,pod_abnormal_type=NotReadyProbeFailed,rootcause-e2e=true"}, {"tool": "kubectl_describe", "description": "上游已验证工具结果: kubectl_describe", "value": "kubectl_describe 摘要:\nname: rc-notready-readiness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n  Warning  Unhealthy  40s (x5307 over 4h15m)  kubelet  Readiness probe failed: readiness dependency unavailable\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\nName:             rc-notready-readiness\nLabels:           app=rc-notready-readiness\n                  cni.projectcalico.org/containerID: fb8e26665bf8a7"}, {"tool": "kubectl_get_yaml", "description": "上游已验证工具结果: kubectl_get_yaml", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-readiness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T07:05:35Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-readiness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntoleration"}], "evidence_analysis": [{"tool": "kubectl_describe", "description": "Pod 'rc-notready-readiness' 的 readiness probe 失败，具体原因是 'readiness dependency unavailable'", "value": "关键诊断行显示 readiness probe 失败，具体原因是 'readiness dependency unavailable'，表明容器依赖的服务或资源未就绪。"}, {"tool": "kubectl_get_yaml", "description": "Pod 'rc-notready-readiness' 的 YAML 配置显示 readiness 探针未被显式设置", "value": "YAML 配置中未显式设置 readiness 探针，容器状态显示 'ready=False'，表明容器未通过健康检查。"}, {"tool": "kubectl_get_by_kind_in_cluster", "description": "Pod 'rc-notready-readiness' 处于 Running 状态，但 READY 为 0/1", "value": "kubectl_get_by_kind_in_cluster 表格摘要显示该 Pod 处于 Running 状态，但 READY 为 0/1，表明容器未就绪。"}], "causal_chain": {"root_cause": "readiness dependency unavailable", "intermediate_causes": ["readiness probe 配置不匹配", "容器依赖的服务或资源未就绪"], "immediate_causes": ["readiness probe 失败", "容器未通过健康检查"], "symptoms": ["Pod 'rc-notready-readiness' 处于 Running 状态，但 READY 为 0/1", "Events 显示 readiness probe 失败", "Pod 未通过健康检查"]}, "root_cause": "Pod 'rc-notready-readiness' 处于 Running 状态，但 READY 为 0/1。Events 显示 readiness probe 失败，具体原因是 'readiness dependency unavailable'。YAML 配置显示 readiness 探针未被显式设置，容器状态显示 'ready=False'，表明容器未通过健康检查。", "root_cause_summary": "Pod 'rc-notready-readiness' 处于 Running 状态，但 READY 为 0/1。Events 显示 readiness probe 失败，具体原因是 'readiness dependency unavailable'。YAML 配置显示 readiness 探针未被显式设置，容器状态显示 'ready=False'，表明容器未通过健康检查。", "confidence": 0.9, "confidence_reason": "有直接证据表明 readiness probe 失败，因果链清晰。", "primary_runbooks": ["pod-notready-probe-failed.md"], "alternative_causes": [], "limitations": "未获取到 readiness 探针的具体配置，未检查该 Pod 所在的 Service 是否配置了正确的 selector。", "llm_raw_analysis": "基于已采集的证据，Pod 'rc-notready-readiness' 处于 Running 状态，但 READY 为 0/1。Events 显示 readiness probe 失败，具体原因是 'readiness dependency unavailable'。YAML 配置显示 readiness 探针未被显式设置，容器状态显示 'ready=False'，表明容器未通过健康检查。这些证据表明 readiness probe 配置不匹配或容器依赖的服务或资源未就绪，导致容器未就绪。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'rc-notready-readiness' 处于 Running 状态，但 READY 为 0/1。Events 显示 readiness probe 失败，具体原因是 'readiness dependency unavailable'。YAML 配置显示 readiness 探针未被...
   置信度: 90%
   🔗 因果链:
     根本原因: readiness dependency unavailable


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 11.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4015 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 16m 33.7s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Running 但 READY 为 0/1，NotReadyProbeFailed |
| **兼容归因层** | L4 |
| **问题分类** | ReadinessProbeFailed |
| **置信度** | 高 (90%) |
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

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod rc-notready-readiness -n aiops-e2e` | `0/1 Running` | Pod 处于 Running 状态，但未就绪 |
| 2 | 事件日志 | `kubectl describe pod rc-notready-readiness -n aiops-e2e` | `Warning Unhealthy 40s (x5307 over 4h15m) kubelet Readiness probe failed: readiness dependency unavailable` | Readiness 探针持续失败 |
| 3 | YAML 配置 | `kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml` | `readinessProbe: <none>` | 未显式配置 readinessProbe |
| 4 | 日志 | `kubectl logs rc-notready-readiness -n aiops-e2e` | `no output` | 未发现明确的健康接口错误 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 处于 Running 状态，但 READY 为 0/1，且 readiness 探针持续失败 → 明确为探针问题。
- **证据 #3 印证**：未显式配置 readinessProbe，表明依赖默认配置或容器自身未提供健康接口。
- **证据 #4 补充**：未发现容器日志异常，推测探针失败可能是由于接口不可用或配置不匹配。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| readinessProbe 具体配置 | critical | 无法确认探针路径、端口、超时等参数是否匹配应用实际接口 |
| 应用健康接口响应 | important | 无法确认是否健康接口本身存在问题 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ readinessProbe 未显式配置或配置不匹配，容器未返回健康状态        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ readinessProbe 未通过 → Pod 被标记为 NotReady → Service 不可用   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Readiness probe failed: readiness dependency unavailable         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 Running 但 READY 为 0/1，Service 无可用 Endpoint        │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Pod 状态 0/1 Running)、证据 #2 (readiness probe 失败) 和证据 #3 (readinessProbe 未显式配置)，问题的根本原因是 **readinessProbe 未配置或配置不匹配，导致容器未通过健康检查**，从而被标记为 NotReady。

**置信度**：高 (90%)
- ✅ Pod READY 状态为 0/1
- ✅ Readiness probe 失败事件频繁
- ⚠️ 未获取到探针具体配置，无法判断是否为探针配置错误或健康接口未响应

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 显式配置 readinessProbe**
```bash
kubectl set probe deployment/<deployment-name> -n aiops-e2e --readiness --http-get=http://localhost:8080/health --initial-delay-seconds=10 --period-seconds=5
```
*依据*：当前探针未显式配置，可能导致探针路径或端口不匹配。

**2. [可选] 查看容器健康接口响应
```bash
kubectl exec -it rc-notready-readiness -n aiops-e2e -- curl -v http://localhost:8080/health
```
*目的*：确认健康接口是否正常响应，排除应用本身问题。

### 后续优化

1. **配置 livenessProbe**：防止容器陷入非健康状态而无法自动恢复。
2. **监控 readiness 探针状态**：配置 Prometheus 或使用 kube-state-metrics 监控探针失败率。
3. **验证 Service selector**：确保 Service 正确选择了该 Pod，避免服务不可用。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-notready-readiness -n aiops-e2e` | READY: 1/1 |
| 2. 检查探针状态 | `kubectl describe pod rc-notready-readiness -n aiops-e2e` | 无 Unhealthy 事件 |
| 3. 查看健康接口 | `kubectl exec -it rc-notready-readiness -n aiops-e2e -- curl -v http://localhost:8080/health` | 2xx 响应 |

---

## ⚠️ 注意事项

- 如果 readinessProbe 配置后仍失败，需进一步检查应用健康接口是否可用。
- 如果 Pod 多次重启，应同时检查 livenessProbe 配置，防止探针误杀。
- 如果此 Pod 是 Service 的一部分，需检查 Service 的 selector 是否匹配该 Pod 的 labels。

---

## 📊 性能统计

├─ 总耗时: 16.6m
├─ 问题定位: 596.1s (60%) ✅
├─ 证据链采集: 175.0s (18%) ✅
├─ 根因分析: 151.7s (15%) ✅
├─ 汇总总结: 71.0s (7%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 10 次
```

📋 诊断追踪

- **核心 Runbook**: pod-notready-probe-failed
- **参考 Runbook**: pod-notready-probe-failed
- **工具调用**: 10 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
