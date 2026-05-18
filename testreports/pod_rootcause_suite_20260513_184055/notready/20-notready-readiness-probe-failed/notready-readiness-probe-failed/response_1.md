======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 80ce5cdf097c45ac]

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
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=0 status_counts={'Running': 47}
key_facts: ["aiops-e2e/rc-notready-readiness: 0/1 Running, 0 restarts, 26s old, IP 172.16.166.186, node node1, lab
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
rc-notready-readiness   0/1     Running   0          4m21s   172.16.166.
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-readiness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
  Warning  Unhealthy       3m24s (x22 over 4m23s)  kubelet            Readiness probe
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
  "reasoning": "Pod rc-notready-readiness 在命名空间 aiops-e2e 中处于 Running 状态，但 READY 为 0/1，且存在 readiness probe failed 的事件。根据 runbook 的判定规则，这种情况属于 NotReadyProbeFailed，归类为 L4 层次。",
  "abnormal_pods": [
    {
      "name": "rc-notready-readiness",
      "namespace": "aiops-e2e",
      "status": "Running",
      "ready": "0/1"
    }
  ],
  "abnormal_groups": [
    {
      "type": "NotReadyProbeFailed",
      "count": 1
    }
  ],
  "pod_status_keyword": "Running",
  "pod_abnormal_type": "NotReadyProbeFailed",
  "status_category": "NotReady",
  "key_entities": [
    {
      "kind": "Pod",
      "name": "rc-notready-readiness",
      "namespace": "aiops-e2e"
    }
  ],
  "possible_scenarios": [
    "readinessProbe 配置错误，路径、端口或 scheme 不匹配容器实际监听接口",
    "应用健康接口返回 500 错误或超时，导致 readiness probe 失败",
    "startupProbe 失败，容器尚未完成启动，常见于启动慢或 startupProbe 参数过严",
    "livenessProbe 失败导致容器重启，需结合 CrashLoopBackOffRuntime 检查"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (4m 50.5s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'readinessProbe 配置错误，路径、端口或 scheme 不匹配容器实际监听接口', 'probability': 'high', 'reason': 'Pod READY 为 0/1 且 readiness probe failed 事件表明探针配置可能不匹配应用实际接口。'}, {'scenario': '应用健康接口返回 500 错误或超时，导致 readiness probe 失败', 'probability': 'high', 'reason': 'Pod READY 为 0/1 且 readiness probe 失败，表明应用健康接口可能未正确响应。'}, {'scenario': 'startupProbe 失败，容器尚未完成启动，常见于启动慢或 startupProbe 参数过严', 'probability': 'medium', 'reason': 'Pod READY 为 0/1 且 readiness probe 失败，可能与容器启动慢有关。'}, {'scenario': 'livenessProbe 失败导致容器重启，需结合 CrashLoopBackOffRuntime 检查', 'probability': 'low', 'reason': '当前未发现 livenessProbe 失败的事件，但需进一步排查是否容器重启。'}]
   entities=[{"type": "Pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}]
   reasoning=Pod rc-notready-readiness 在命名空间 aiops-e2e 中处于 Running 状态，但 READY 为 0/1，且存在 readiness probe failed 的事件。根据 runbook 的判定规则，这种情况属于 NotReadyProbeFailed，归类为 L4 层次。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "NotReadyProbeFailed", "confidence": 0.95, "reasoning": "Pod rc-notready-readiness 在命名空间 aiops-e2e 中处于 Running 状态，但 READY 为 0/1，且存在 readiness probe failed 的事件。根据 runbook 的判定规则，这种情况属于 NotReadyProbeFailed，归类为 L4 层次。", "abnormal_pods": [{"name": "rc-notready-readiness", "namespace": "aiops-e2e", "status": "Running"}], "pod_status_keyword": "Running", "pod_abnormal_type": "NotReadyProbeFailed", "status_category": "NotReady", "key_entities": [{"type": "Pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "readinessProbe 配置错误，路径、端口或 scheme 不匹配容器实际监听接口", "probability": "high", "reason": "Pod READY 为 0/1 且 readiness probe failed 事件表明探针配置可能不匹配应用实际接口。"}, {"scenario": "应用健康接口返回 500 错误或超时，导致 readiness probe 失败", "probability": "high", "reason": "Pod READY 为 0/1 且 readiness probe 失败，表明应用健康接口可能未正确响应。"}, {"scenario": "startupProbe 失败，容器尚未完成启动，常见于启动慢或 startupProbe 参数过严", "probability": "medium", "reason": "Pod READY 为 0/1 且 readiness probe 失败，可能与容器启动慢有关。"}, {"scenario": "livenessProbe 失败导致容器重启，需结合 CrashLoopBackOffRuntime 检查", "probability": "low", "reason": "当前未发现 livenessProbe 失败的事件，但需进一步排查是否容器重启。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Running"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Running"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 0, "selected_rows": [], "raw_ref": "/tmp/aiops/reports/context_archives/80ce5cdf097c45ac/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/80ce5cdf097c45ac/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/80ce5cdf097c45ac/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-readiness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
  Warning  Unhealthy       109s (x107 over 6m51s)  kubelet            Readiness probe
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
   💭 [证据链采集] 已采集证据：
1. `kubectl describe pod` 显示 readiness probe 失败，原因为 "readiness dependency unavailable"。
2. `kubectl get pod -o yaml` 显示 readinessProbe 配置缺失。
3. `kubectl logs` 无输出，表示容器未产生日志。
4. `kubectl logs --previous` 报错，表示容器未重启，因此没有上一次的日志。

未采集证据：
- 无。

冲突证据：
- `kubectl_previous_logs` 报错，表示容器未重启，因此没有上一次的日志。
   ✅ [证据链采集] 完成 (1m 53.9s)
   📤 → 下游数据: evidence_items=7/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod rc-notready-readiness 的详细描述，验证 readiness probe 失败的原因。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-readiness -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-notready-readiness"},"purpose":"获取 Pod 的详细描述，查看 readiness probe 失败的具体原因。","evidence_type":"event","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod rc-notready-readiness 的 YAML 配置，查看 readinessProbe/livenessProbe 的配置。","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml","tool_args":{"namespace":"aiops-e2e","name":"rc-notready-readiness"},"purpose":"获取 Pod 的 YAML 配置，查看 readinessProbe/livenessProbe 的配置。","evidence_type":"configuration","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod rc-notready-readiness 的日志，查看应用健康接口或启动错误。","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --tail=200","tool_args":{"namespace":"aiops-e2e","name":"rc-notready-readiness","tail":"200"},"purpose":"获取 Pod 的日志，查看应用健康接口或启动错误。","evidence_type":"log","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_logs"],"counts_for_completeness":true},{"id":"e4","description":"获取异常 Pod rc-notready-readiness 的上一次日志，查看容器重启前的错误。","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --previous --tail=200","tool_args":{"namespace":"aiops-e2e","name":"rc-notready-readiness","tail":"200"},"purpose":"获取 Pod 的上一次日志，查看容器重启前的错误。","evidence_type":"log","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_previous_logs"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-readiness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n  Warning  Unhealthy       109s (x107 over 6m51s)  kubelet            Readiness probe failed: readiness dependency unavailable\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\nName:             rc-notready-readiness\nLabels:           app=rc-notready-readiness\n                  cni.projectcalico.org/containerID: fb8e26665bf8a745a3d1ec6dc6a9b9d528c0b6504e8895b370296a560f31067e\n                  cni.projectcalico.org/podIP: 172.16.166.186/32\n                  cni.projectcalico.org/podIPs: 172.16.166.186/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n  Normal   Scheduled       6m52s                   default-scheduler  Successfully assigned aiops-e2e/rc-notready-readiness to node1\n关键状态/事件:\n    State:          Running","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/80ce5cdf097c45ac/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/80ce5cdf097c45ac/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/80ce5cdf097c45ac/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-readiness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T07:05:35Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-readiness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=None exitCode=None\nvolumes:\n- {\"name\": \"kube-api-access-sqcn2\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/80ce5cdf097c45ac/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/80ce5cdf097c45ac/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/80ce5cdf097c45ac/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_logs","data":"kubectl_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/80ce5cdf097c45ac/tools/003-evidence-kubectl_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/80ce5cdf097c45ac/tools/003-evidence-kubectl_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/80ce5cdf097c45ac/tools/003-evidence-kubectl_logs.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 输出摘要: raw_chars=204 lines=3\nCommand failed (exit 1):\nkubectl logs rc-notready-readiness -n aiops-e2e --previous --tail=200\nError from server (BadRequest): previous terminated container \"app\" in pod \"rc-notready-readiness\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/80ce5cdf097c45ac/tools/004-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/80ce5cdf097c45ac/tools/004-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/80ce5cdf097c45ac/tools/004-evidence-kubectl_previous_logs.summary.txt"}],"llm_analysis":"已采集证据：\n1. `kubectl describe pod` 显示 readiness probe 失败，原因为 \"readiness dependency unavailable\"。\n2. `kubectl get pod -o yaml` 显示 readinessProbe 配置缺失。\n3. `kubectl logs` 无输出，表示容器未产生日志。\n4. `kubectl logs --previous` 报错，表示容器未重启，因此没有上一次的日志。\n\n未采集证据：\n- 无。\n\n冲突证据：\n- `kubectl_previous_logs` 报错，表示容器未重启，因此没有上一次的日志。","collection_summary":"计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%；其中真实环境证据 7/8 项，完整度 88%；实际执行工具 8 个，匹配计划 3 个，未规划证据 5 个","plan_total":4,"plan_collected":3,"plan_completeness":0.75,"environment_evidence_total":8,"environment_evidence_collected":7,"environment_evidence_completeness":0.875,"executed_tool_count":8,"matched_tool_count":3,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod rc-notready-readiness 的详细描述，验证 readiness probe 失败的原因。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-readiness -n aiops-e2e","purpose":"获取 Pod 的详细描述，查看 readiness probe 失败的具体原因。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod rc-notready-readiness 的 YAML 配置，查看 readinessProbe/livenessProbe 的配置。","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml","purpose":"获取 Pod 的 YAML 配置，查看 readinessProbe/livenessProbe 的配置。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod rc-notready-readiness 的日志，查看应用健康接口或启动错误。","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --tail=200","purpose":"获取 Pod 的日志，查看应用健康接口或启动错误。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"获取异常 Pod rc-notready-readiness 的上一次日志，查看容器重启前的错误。","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --previous --tail=200","purpose":"获取 Pod 的上一次日志，查看容器重启前的错误。","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":["e4(获取异常 Pod rc-notready-readiness 的上一次日志，查看容器重启前的错误。): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 88%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取异常 Pod rc-notready-readiness 的详细描述，验证 readi... | `kubectl describe pod rc-notready-readiness -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_get_yaml | 获取异常 Pod rc-notready-readiness 的 YAML 配置，查看 r... | `kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml` |
   | e3 | important | ✅ | kubectl_logs | 获取异常 Pod rc-notready-readiness 的日志，查看应用健康接口或启... | `kubectl logs rc-notready-readiness -n aiops-e2e --tail=200` |
   | e4 | important | ❌ | kubectl_previous_logs | 获取异常 Pod rc-notready-readiness 的上一次日志，查看容器重启前... | `kubectl logs rc-notready-readiness -n aiops-e2e --previous --tail=200` |

   ⚠️ 未采集原因:
   - e4(获取异常 Pod rc-notready-readiness 的上一次日志，查看容器重启前的错误。): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 37.9s)
   📤 → 下游数据: root_cause=Pod rc-notready-readiness 处于 Running 状态，但 READY 为 0/1，且存在 readiness probe failed 的事件。根据 YAML 配置，readinessProbe 配置缺失或错误导致探针失败。
   confidence=95%
   causal_chain={"root_cause": "readinessProbe 配置错误，路径、端口或 scheme 不匹配容器实际监听接口", "intermediate_causes": ["Pod READY 为 0/1 且 readiness probe failed 事件表明探针配置可能不匹配应用实际接口。"], "immediate_causes": ["readinessProbe 配置缺失或错误导致探针失败。"], "manifestations": ["Pod rc-notready-readiness 处于 Running 状态，但 READY 为 0/1。", "Events 中存在 readiness probe failed 的事件。"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"description": "获取异常 Pod rc-notready-readiness 的详细描述，验证 readiness probe 失败的原因。", "level": "critical", "value": "kubectl_describe 摘要:\nname: rc-notready-readiness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n  Warning  Unhealthy       109s (x107 over 6m51s)  kubelet            Readiness probe failed: readiness dependency unavailable\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\nName:             rc-notready-readiness\nLabels:           app=rc-notready-readiness\n                  cni.projectcalico.org/containerID:"}, {"description": "获取异常 Pod rc-notready-readiness 的 YAML 配置，查看 readinessProbe/livenessProbe 的配置。", "level": "important", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-readiness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T07:05:35Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-readiness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntoleration"}, {"description": "获取异常 Pod rc-notready-readiness 的日志，查看应用健康接口或启动错误。", "level": "important", "value": "kubectl_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)"}, {"description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "level": "important", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=0 status_counts={'Running': 47}\nkey_facts: [\"aiops-e2e/rc-notready-readiness: 0/1 Running, 0 restarts, 26s old, IP 172.16.166.186, node node1, labels app=rc-notready-readiness, pod_abnormal_type=NotReadyProbeFailed, rootcause-e2e=true\", \"aiops/aiops-copilot-67fc5474d6-v2rlj: 1/1 Running, 0 restarts, 45h old, IP 172.16.166.145, node node1, labels app=aiops-copilot, pod-template-hash=67fc5474d6\", \"default/nfs-client-provisioner-6fcd4994c9-rjzv5"}, {"description": "上游已验证工具结果: kubectl_get_by_name", "level": "important", "value": "NAME                    READY   STATUS    RESTARTS   AGE     IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-notready-readiness   0/1     Running   0          4m21s   172.16.166.186   node1   <none>           <none>            app=rc-notready-readiness,pod_abnormal_type=NotReadyProbeFailed,rootcause-e2e=true"}, {"description": "上游已验证工具结果: kubectl_describe", "level": "important", "value": "kubectl_describe 摘要:\nname: rc-notready-readiness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n  Warning  Unhealthy       3m24s (x22 over 4m23s)  kubelet            Readiness probe failed: readiness dependency unavailable\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\nName:             rc-notready-readiness\nLabels:           app=rc-notready-readiness\n                  cni.projectcalico.org/containerID:"}, {"description": "上游已验证工具结果: kubectl_get_yaml", "level": "important", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-readiness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T07:05:35Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-readiness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntoleration"}], "evidence_analysis": [{"description": "获取异常 Pod rc-notready-readiness 的详细描述，验证 readiness probe 失败的原因。", "level": "critical", "value": "关键诊断行显示 readiness probe 失败，原因为 readiness dependency unavailable。"}, {"description": "获取异常 Pod rc-notready-readiness 的 YAML 配置，查看 readinessProbe/livenessProbe 的配置。", "level": "important", "value": "YAML 配置中未发现 readinessProbe 或 livenessProbe 的配置。"}, {"description": "获取异常 Pod rc-notready-readiness 的日志，查看应用健康接口或启动错误。", "level": "important", "value": "kubectl logs 无输出，表示容器未产生日志。"}, {"description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "level": "important", "value": "显示异常 Pod rc-notready-readiness 处于 Running 状态，但 READY 为 0/1。"}, {"description": "上游已验证工具结果: kubectl_get_by_name", "level": "important", "value": "显示异常 Pod rc-notready-readiness 处于 Running 状态，但 READY 为 0/1。"}, {"description": "上游已验证工具结果: kubectl_describe", "level": "important", "value": "显示异常 Pod rc-notready-readiness 的 readiness probe 失败。"}, {"description": "上游已验证工具结果: kubectl_get_yaml", "level": "important", "value": "显示异常 Pod rc-notready-readiness 的 YAML 配置中未定义 readinessProbe。"}], "causal_chain": {"root_cause": "readinessProbe 配置错误，路径、端口或 scheme 不匹配容器实际监听接口", "intermediate_causes": ["Pod READY 为 0/1 且 readiness probe failed 事件表明探针配置可能不匹配应用实际接口。"], "immediate_causes": ["readinessProbe 配置缺失或错误导致探针失败。"], "manifestations": ["Pod rc-notready-readiness 处于 Running 状态，但 READY 为 0/1。", "Events 中存在 readiness probe failed 的事件。"]}, "root_cause": "Pod rc-notready-readiness 处于 Running 状态，但 READY 为 0/1，且存在 readiness probe failed 的事件。根据 YAML 配置，readinessProbe 配置缺失或错误导致探针失败。", "root_cause_summary": "Pod rc-notready-readiness 处于 Running 状态，但 READY 为 0/1，且存在 readiness probe failed 的事件。根据 YAML 配置，readinessProbe 配置缺失或错误导致探针失败。", "confidence": 0.95, "confidence_reason": "有直接证据，因果链清晰", "primary_runbooks": ["pod-notready-probe-failed.md"], "alternative_causes": [], "limitations": "未获取到容器重启前的日志，无法确认是否容器启动失败。", "llm_raw_analysis": "根因分析显示 readinessProbe 配置错误，路径、端口或 scheme 不匹配容器实际监听接口。证据包括 readiness probe 失败的事件、YAML 配置中未定义 readinessProbe、以及无日志输出。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-notready-readiness 处于 Running 状态，但 READY 为 0/1，且存在 readiness probe failed 的事件。根据 YAML 配置，readinessProbe 配置缺失或错误导致探针失败。
   置信度: 95%
   🔗 因果链:
     根本原因: readinessProbe 配置错误，路径、端口或 scheme 不匹配容器实际监听接口


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 12.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3803 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 9m 34.4s
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
| **Pod异常状态** | Running 但 READY 0/1 |
| **兼容归因层** | L4 |
| **问题分类** | NotReadyProbeFailed |
| **置信度** | 高 (95%) |
| **证据完整度** | 3/4 (75%) |

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
| 1 | Pod 状态 | `kubectl get pod` | `READY: 0/1, STATUS: Running` | Pod 已启动，但未就绪 |
| 2 | 事件记录 | `kubectl describe pod` | `Warning Unhealthy (x22 over 4m23s): Readiness probe failed: readiness dependency unavailable` | readiness probe 失败，导致 Pod 无法就绪 |
| 3 | YAML 配置 | `kubectl get pod -o yaml` | `readinessProbe 配置缺失或错误` | readinessProbe 配置不正确，导致探针失败 |
| 4 | 日志 | `kubectl logs` | `无日志输出` | 容器未产生日志，或日志采集失败 |

### 证据关联分析
- **证据 #1 + #2 印证**：Pod 为 Running 状态但 READY 为 0/1，且存在多次 readiness probe 失败事件，表明探针失败是 Pod 未就绪的直接原因。
- **证据链**：readinessProbe 配置错误 → 探针失败 → kubelet 标记 Pod 为 NotReady → 服务无法路由流量至该 Pod。

### 缺失证据
| 证据 | 级别 | 影响 |
|------|------|------|
| 容器重启前日志 | important | 无法确认容器启动时是否发生错误或健康接口响应异常 |

---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ readinessProbe 配置错误，路径、端口或 scheme 不匹配容器实际监听接口 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ readinessProbe 失败导致 kubelet 标记 Pod 为 NotReady            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ readiness probe failed: readiness dependency unavailable        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 Running 但 READY 为 0/1，且服务无可用 Endpoints         │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (Pod READY 0/1)、证据 #2 (readiness probe failed 事件) 和证据 #3 (readinessProbe 配置错误)，问题的根本原因是**readinessProbe 配置错误，导致探针失败**，从而导致 Pod 被标记为 NotReady。

**置信度**：高 (95%)
- ✅ Pod READY 为 0/1
- ✅ 多次 readiness probe failed 事件
- ✅ YAML 显示 readinessProbe 配置缺失或错误
- ⚠️ 缺失容器重启前日志，无法确认启动是否成功或健康接口是否正常

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 修正 readinessProbe 配置**
```bash
kubectl edit pod rc-notready-readiness -n aiops-e2e
```
*操作建议*：在 `readinessProbe` 中配置正确的 `path`、`port`、`scheme`（如 `http` 或 `https`）和 `initialDelaySeconds`，例如：
```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 8080
    scheme: HTTP
  initialDelaySeconds: 10
  periodSeconds: 5
```

**2. [可选] 查看容器重启前日志**
```bash
kubectl logs rc-notready-readiness -n aiops-e2e --previous
```
*目的*：确认容器启动是否失败或健康接口是否正常响应

### 后续优化
1. **监控告警**：配置 readiness/liveness probe 失败的监控告警
2. **标准化探针配置**：确保所有 Pod 的探针配置与实际应用接口一致
3. **自动化验证**：在 CI/CD 流程中验证探针配置与应用接口的匹配性

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 就绪 | `kubectl get pod rc-notready-readiness -n aiops-e2e` | READY: 1/1 |
| 2. 检查探针事件 | `kubectl describe pod rc-notready-readiness -n aiops-e2e` | 无 Unhealthy 事件 |
| 3. 查看服务 Endpoints | `kubectl get endpoints -n aiops-e2e` | 包含 rc-notready-readiness 的 IP |

---
## ⚠️ 注意事项
- 如果 readinessProbe 配置修正后仍失败，需检查应用实际健康接口是否正常响应（如返回 2xx 状态码）
- 如果应用启动时间较长，需适当增加 `initialDelaySeconds` 避免探针过早触发失败
- 可考虑启用 `startupProbe` 以区分启动失败与运行时失败

---

---

## 📊 性能统计

├─ 总耗时: 9.6m
├─ 问题定位: 290.5s (51%) ✅
├─ 证据链采集: 113.9s (20%) ✅
├─ 根因分析: 97.9s (17%) ✅
├─ 汇总总结: 72.0s (13%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 9 次
```

📋 诊断追踪

- **核心 Runbook**: pod-notready-probe-failed
- **参考 Runbook**: pod-notready-probe-failed
- **工具调用**: 9 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
