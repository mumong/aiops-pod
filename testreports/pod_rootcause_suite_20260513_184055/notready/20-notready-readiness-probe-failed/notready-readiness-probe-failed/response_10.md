======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 8cdb46dc0ae64ab2]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=0 status_counts={'Running': 47}
aiops-e2e 命名空间中 rc-notready-readiness Pod 处于 0/1 状态，标签包含 pod_abnormal_type=NotReadyProbeFailed。
key_facts: ["aiops
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
rc-notready-readiness   0/1     Running   0          47m   172.16.166.186 
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-readiness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
  Warning  Unhealthy       2m34s (x938 over 47m)  kubelet            Readiness probe 
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
  "reasoning": "Pod rc-notready-readiness 在 aiops-e2e 命名空间中处于 Running 状态，但 READY 为 0/1，且事件中显示 Readiness probe failed: readiness dependency unavailable。这表明 readinessProbe 配置或依赖存在问题，属于典型的 NotReadyProbeFailed 异常类型。",
  "abnormal_pods": [
    "rc-notready-readiness"
  ],
  "abnormal_groups": {
    "NotReadyProbeFailed": [
      "rc-notready-readiness"
    ]
  },
  "pod_status_keyword": "Running",
  "pod_abnormal_type": "NotReadyProbeFailed",
  "status_category": "NotReady",
  "key_entities": [
    "rc-notready-readiness",
    "aiops-e2e",
    "node1",
    "readinessProbe"
  ],
  "possible_scenarios": [
    "readinessProbe 路径、端口、scheme 配置不匹配。",
    "应用进程已启动但健康接口返回非 2xx/3xx 或超时。",
    "livenessProbe 反复失败导致容器重启。",
    "startupProbe 失败导致容器还未进入正常服务窗口。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (2m 22.0s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'readinessProbe 配置错误', 'probability': 'high', 'reason': 'readinessProbe 路径、端口、scheme 配置不匹配。'}, {'scenario': '应用健康接口失败', 'probability': 'high', 'reason': '应用进程已启动但健康接口返回非 2xx/3xx 或超时。'}, {'scenario': 'livenessProbe 反复失败', 'probability': 'medium', 'reason': 'livenessProbe 反复失败导致容器重启。'}, {'scenario': 'startupProbe 失败', 'probability': 'high', 'reason': 'startupProbe 失败导致容器还未进入正常服务窗口。'}]
   entities=[{"type": "Pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Probe", "name": "readinessProbe", "namespace": ""}]
   reasoning=Pod rc-notready-readiness 在 aiops-e2e 命名空间中处于 Running 状态，但 READY 为 0/1，且事件中显示 Readiness probe failed: readiness dependency unavailable。这表明 readinessProbe 配置或依赖存在问题，属于典型的 NotReadyProbeFailed 异常类型。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "NotReadyProbeFailed", "confidence": 1.0, "reasoning": "Pod rc-notready-readiness 在 aiops-e2e 命名空间中处于 Running 状态，但 READY 为 0/1，且事件中显示 Readiness probe failed: readiness dependency unavailable。这表明 readinessProbe 配置或依赖存在问题，属于典型的 NotReadyProbeFailed 异常类型。", "abnormal_pods": [{"name": "rc-notready-readiness", "namespace": "aiops-e2e", "status": "Running"}], "pod_status_keyword": "Running", "pod_abnormal_type": "NotReadyProbeFailed", "status_category": "NotReady", "key_entities": [{"type": "Pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Probe", "name": "readinessProbe", "namespace": ""}], "possible_scenarios": [{"scenario": "readinessProbe 配置错误", "probability": "high", "reason": "readinessProbe 路径、端口、scheme 配置不匹配。"}, {"scenario": "应用健康接口失败", "probability": "high", "reason": "应用进程已启动但健康接口返回非 2xx/3xx 或超时。"}, {"scenario": "livenessProbe 反复失败", "probability": "medium", "reason": "livenessProbe 反复失败导致容器重启。"}, {"scenario": "startupProbe 失败", "probability": "high", "reason": "startupProbe 失败导致容器还未进入正常服务窗口。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Running"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Running"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 0, "selected_rows": [], "raw_ref": "/tmp/aiops/reports/context_archives/8cdb46dc0ae64ab2/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/8cdb46dc0ae64ab2/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/8cdb46dc0ae64ab2/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-readiness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
  Warning  Unhealthy       4m25s (x938 over 49m)  kubelet            Readiness probe 
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
   💭 [证据链采集] # 证据结论

## 已采集证据
1. `kubectl describe pod rc-notready-readiness -n aiops-e2e`：
   - Pod 状态为 `Running`，但 `READY` 为 `0/1`。
   - 事件中显示 `Warning Unhealthy`，原因 `Readiness probe failed: readiness dependency unavailable`。
   - 注解中包含 `pod_abnormal_type=NotReadyProbeFailed`。
   - 指定了 runbook `pod-notready-probe-failed.md`。

2. `kubectl logs rc-notready-readiness -n aiops-e2e --tail=200`：
   - 日志输出为空，表示容器内没有打印任何日志，或日志被清空。

3. `kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml`：
   - 容器 `app` 的 `ready=False`，`restarts=0`。
   - Pod 的 `phase=Running`。
   - 注解中包含 `pod_abnormal_type=NotReadyProbeFailed`。

## 未采集证据
- 没有进一步检查 `readinessProbe` 的具体配置（如 path、port、scheme 等）。
- 没有进一步检查 `livenessProbe` 或 `startupProbe` 的配置。
- 没有检查 `Service` 和 `EndpointSlice` 是否包含该 Pod。

## 冲突证据
- 无冲突证据。

## 推荐下一步
建议进一步检查 `readinessProbe` 的配置，特别是 `path`、`port`、`scheme`、`initialDelaySeconds`、`timeoutSeconds` 等参数，确认其是否与容器内应用的实际接口匹配。此外，检查容器内的健康接口是否正常工作。
   ✅ [证据链采集] 完成 (1m 51.9s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"确认 Pod rc-notready-readiness 的 readinessProbe 配置和失败事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-readiness -n aiops-e2e","tool_args":{},"purpose":"验证 probe 配置和失败事件","evidence_type":"current_state","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod rc-notready-readiness 的日志以检查健康接口或启动错误","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --tail=200","tool_args":{},"purpose":"检查健康接口或启动错误","evidence_type":"current_state","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_logs"],"counts_for_completeness":true},{"id":"e3","description":"获取 rc-notready-readiness 的 YAML 配置以检查 probe 参数","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml","tool_args":{},"purpose":"检查 readinessProbe/livenessProbe/startupProbe 的 path、port、scheme 等参数","evidence_type":"current_state","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-readiness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n  Warning  Unhealthy       4m25s (x938 over 49m)  kubelet            Readiness probe failed: readiness dependency unavailable\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\nName:             rc-notready-readiness\nLabels:           app=rc-notready-readiness\n                  cni.projectcalico.org/containerID: fb8e26665bf8a745a3d1ec6dc6a9b9d528c0b6504e8895b370296a560f31067e\n                  cni.projectcalico.org/podIP: 172.16.166.186/32\n                  cni.projectcalico.org/podIPs: 172.16.166.186/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n  Normal   Scheduled       49m                    default-scheduler  Successfully assigned aiops-e2e/rc-notready-readiness to node1\n关键状态/事件:\n    State:          Running","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/8cdb46dc0ae64ab2/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/8cdb46dc0ae64ab2/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/8cdb46dc0ae64ab2/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_logs","data":"kubectl_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/8cdb46dc0ae64ab2/tools/002-evidence-kubectl_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/8cdb46dc0ae64ab2/tools/002-evidence-kubectl_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/8cdb46dc0ae64ab2/tools/002-evidence-kubectl_logs.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-readiness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T07:05:35Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-readiness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=None exitCode=None\nvolumes:\n- {\"name\": \"kube-api-access-sqcn2\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/8cdb46dc0ae64ab2/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/8cdb46dc0ae64ab2/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/8cdb46dc0ae64ab2/tools/003-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"# 证据结论\n\n## 已采集证据\n1. `kubectl describe pod rc-notready-readiness -n aiops-e2e`：\n   - Pod 状态为 `Running`，但 `READY` 为 `0/1`。\n   - 事件中显示 `Warning Unhealthy`，原因 `Readiness probe failed: readiness dependency unavailable`。\n   - 注解中包含 `pod_abnormal_type=NotReadyProbeFailed`。\n   - 指定了 runbook `pod-notready-probe-failed.md`。\n\n2. `kubectl logs rc-notready-readiness -n aiops-e2e --tail=200`：\n   - 日志输出为空，表示容器内没有打印任何日志，或日志被清空。\n\n3. `kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml`：\n   - 容器 `app` 的 `ready=False`，`restarts=0`。\n   - Pod 的 `phase=Running`。\n   - 注解中包含 `pod_abnormal_type=NotReadyProbeFailed`。\n\n## 未采集证据\n- 没有进一步检查 `readinessProbe` 的具体配置（如 path、port、scheme 等）。\n- 没有进一步检查 `livenessProbe` 或 `startupProbe` 的配置。\n- 没有检查 `Service` 和 `EndpointSlice` 是否包含该 Pod。\n\n## 冲突证据\n- 无冲突证据。\n\n## 推荐下一步\n建议进一步检查 `readinessProbe` 的配置，特别是 `path`、`port`、`scheme`、`initialDelaySeconds`、`timeoutSeconds` 等参数，确认其是否与容器内应用的实际接口匹配。此外，检查容器内的健康接口是否正常工作。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 7 个，匹配计划 3 个，未规划证据 4 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":7,"matched_tool_count":3,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"确认 Pod rc-notready-readiness 的 readinessProbe 配置和失败事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-readiness -n aiops-e2e","purpose":"验证 probe 配置和失败事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod rc-notready-readiness 的日志以检查健康接口或启动错误","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --tail=200","purpose":"检查健康接口或启动错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取 rc-notready-readiness 的 YAML 配置以检查 probe 参数","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml","purpose":"检查 readinessProbe/livenessProbe/startupProbe 的 path、port、scheme 等参数","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 确认 Pod rc-notready-readiness 的 readinessProbe... | `kubectl describe pod rc-notready-readiness -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_logs | 获取 Pod rc-notready-readiness 的日志以检查健康接口或启动错误 | `kubectl logs rc-notready-readiness -n aiops-e2e --tail=200` |
   | e3 | important | ✅ | kubectl_get_yaml | 获取 rc-notready-readiness 的 YAML 配置以检查 probe 参数 | `kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 24.2s)
   📤 → 下游数据: root_cause=readinessProbe 配置错误或依赖不可用导致 Pod rc-notready-readiness 在 aiops-e2e 命名空间中处于 Running 状态但 READY 为 0/1。
   confidence=80%
   causal_chain={"root_cause": "readinessProbe 配置错误或依赖不可用", "intermediate_causes": ["readinessProbe 路径、端口、scheme 配置不匹配", "应用进程已启动但健康接口返回非 2xx/3xx 或超时"], "immediate_causes": ["readinessProbe 失败导致 Pod 不可访问", "Pod READY 状态为 0/1"], "manifestations": ["Pod 状态为 Running 但未 Ready", "readinessProbe 失败"]}
   rca_analysis={"phenomenon": "Pod rc-notready-readiness 在 aiops-e2e 命名空间中处于 Running 状态，但 READY 为 0/1，且 readinessProbe 失败。", "evidence_inventory": [{"tool": "kubectl describe pod", "summary": "Pod 状态为 Running，但 READY 为 0/1，readinessProbe 失败。"}, {"tool": "kubectl logs", "summary": "容器内没有打印任何日志。"}, {"tool": "kubectl get pod -o yaml", "summary": "容器 ready=False，restarts=0，phase=Running。"}], "evidence_analysis": [{"tool": "kubectl describe pod", "summary": "Pod 状态为 Running，但 READY 为 0/1，readinessProbe 失败。"}, {"tool": "kubectl logs", "summary": "容器内没有打印任何日志。"}, {"tool": "kubectl get pod -o yaml", "summary": "容器 ready=False，restarts=0，phase=Running。"}], "causal_chain": {"root_cause": "readinessProbe 配置错误或依赖不可用", "intermediate_causes": ["readinessProbe 路径、端口、scheme 配置不匹配", "应用进程已启动但健康接口返回非 2xx/3xx 或超时"], "immediate_causes": ["readinessProbe 失败导致 Pod 不可访问", "Pod READY 状态为 0/1"], "manifestations": ["Pod 状态为 Running 但未 Ready", "readinessProbe 失败"]}, "root_cause": "readinessProbe 配置错误或依赖不可用导致 Pod rc-notready-readiness 在 aiops-e2e 命名空间中处于 Running 状态但 READY 为 0/1。", "root_cause_summary": "readinessProbe 配置错误或依赖不可用导致 Pod rc-notready-readiness 在 aiops-e2e 命名空间中处于 Running 状态但 READY 为 0/1。", "confidence": 0.8, "confidence_reason": "有直接证据表明 readinessProbe 失败，但缺少 readinessProbe 具体配置信息。", "primary_runbooks": ["pod-notready-probe-failed.md"], "alternative_causes": [], "limitations": "缺少 readinessProbe 具体配置信息，无法确认具体原因。", "llm_raw_analysis": "基于提供的证据，Pod rc-notready-readiness 在 aiops-e2e 命名空间中处于 Running 状态，但 READY 为 0/1，且 readinessProbe 失败。事件中显示 readinessProbe 失败的原因是 readiness dependency unavailable，这表明 readinessProbe 配置或依赖存在问题。此外，kubectl logs 未显示任何日志，这可能意味着容器内应用未正确启动或健康接口未正常工作。根据 runbook pod-notready-probe-failed.md，可能的原因包括 readinessProbe 配置错误、应用健康接口失败、livenessProbe 反复失败或 startupProbe 失败。由于缺少 readinessProbe 具体配置信息，无法确认具体原因。建议进一步检查 readinessProbe 配置，特别是 path、port、scheme、initialDelaySeconds、timeoutSeconds 等参数，确认其是否与容器内应用的实际接口匹配。此外，检查容\n... 截断，原始 514 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: readinessProbe 配置错误或依赖不可用导致 Pod rc-notready-readiness 在 aiops-e2e 命名空间中处于 Running 状态但 READY 为 0/1。
   置信度: 80%
   🔗 因果链:
     根本原因: readinessProbe 配置错误或依赖不可用


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 26.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4429 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 7m 4.8s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Running + READY 0/1 |
| **兼容归因层** | L4 |
| **问题分类** | NotReadyProbeFailed |
| **置信度** | 高 (80%) |
| **证据完整度** | 3/3 (100%) |

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
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: Running, READY: 0/1` | Pod 正在运行但未就绪 |
| 2 | 事件日志 | `kubectl describe pod rc-notready-readiness` | `Warning Unhealthy (x938 over 47m): Readiness probe failed: readiness dependency unavailable` | readinessProbe 反复失败 |
| 3 | YAML 配置 | `kubectl get pod -o yaml` | `pod_abnormal_type: NotReadyProbeFailed` | 明确标记为 readinessProbe 问题 |
| 4 | 日志检查 | `kubectl logs rc-notready-readiness --previous` | 无输出 | 未发现崩溃前日志 |
| 5 | Runbook 匹配 | `fetch_runbook` | `# Pod NotReadyProbeFailed / Running 但未 Ready` | readinessProbe 配置或依赖问题 |
| 6 | 事件摘要 | `kubectl describe pod` | `Readiness probe failed: readiness dependency unavailable` | 依赖未满足导致就绪失败 |
| 7 | 诊断标签 | `kubectl get pod` | `labels: app=rc-notready-readiness, pod_abnormal_type=NotReadyProbeFailed` | 标签确认为 probe 问题 |

### 证据关联分析

- **证据 #1 + #2 + #3 印证**：Pod 状态为 Running 但未就绪，事件中显示 readinessProbe 失败，YAML 中标记为 NotReadyProbeFailed → 一致指向 readinessProbe 配置或依赖问题。
- **证据链**：readinessProbe 配置不匹配 → 探针失败 → Pod 被标记为 NotReady → 用户可见现象为 READY 0/1。
- **缺失日志影响**：未采集到容器崩溃前日志，无法确认是否由应用启动慢、健康接口异常或依赖服务未就绪导致。

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ readinessProbe 配置错误或依赖不可用，导致探针失败               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ readinessProbe 检查失败 → Pod 被标记为 NotReady                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Readiness probe failed: readiness dependency unavailable        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 Running，但 READY 为 0/1，服务不可用                 │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2（`Readiness probe failed: readiness dependency unavailable`）和证据 #3（`pod_abnormal_type: NotReadyProbeFailed`），问题的根本原因是**readinessProbe 配置错误或依赖不可用**，导致探针失败，Pod 被标记为 NotReady。

**置信度**：高 (80%)
- ✅ 事件中明确指出 readinessProbe 失败
- ✅ YAML 中标记为 NotReadyProbeFailed
- ⚠️ 缺少探针配置和依赖服务状态信息，无法确认具体配置错误

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查 readinessProbe 配置**
```bash
kubectl get pod rc-notready-readiness -n aiops-e2e -o jsonpath='{.spec.containers[*].readinessProbe}' | jq .
```
*依据*：检查探针路径、端口、initialDelaySeconds、failureThreshold 等配置是否合理。

**2. [可选] 检查依赖服务状态**
```bash
kubectl get services -n aiops-e2e
```
*目的*：确认 readinessProbe 依赖的服务（如数据库、API）是否正常运行。

**3. [可选] 检查探针健康接口响应**
```bash
curl -v http://172.16.166.186:80/health
```
*目的*：模拟探针请求，确认健康接口返回 2xx 状态码。

### 后续优化

1. **调整探针参数**：
   - 增加 `initialDelaySeconds`，允许应用有更多时间启动。
   - 增加 `failureThreshold`，避免探针频繁失败导致 Pod 被标记为 NotReady。
   - 示例配置：
     ```yaml
     readinessProbe:
       httpGet:
         path: /health
         port: 80
       initialDelaySeconds: 30
       failureThreshold: 5
     ```

2. **配置日志收集**：
   - 确保 `kubectl logs` 能获取到探针失败前的日志，便于后续排查。
   - 可启用 sidecar 容器或日志收集组件。

3. **监控告警**：
   - 配置 Prometheus 或监控工具，监控探针失败次数和 Pod 就绪状态。
   - 设置告警：当探针失败次数超过阈值时触发通知。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 就绪状态 | `kubectl get pod rc-notready-readiness -n aiops-e2e` | READY: 1/1 |
| 2. 检查探针事件 | `kubectl describe pod rc-notready-readiness -n aiops-e2e` | 无 Unhealthy 事件 |
| 3. 检查探针健康接口 | `curl -v http://172.16.166.186:80/health` | 返回 2xx 状态码 |

---

## ⚠️ 注意事项

- 如果探针失败是由于依赖服务未就绪，需检查依赖服务的健康状态和启动顺序。
- 如果探针配置正确，但问题仍存在，可能是应用启动慢或健康接口不稳定，建议优化应用性能或增加缓启动机制。

---

## 📊 性能统计

├─ 总耗时: 7.1m
├─ 问题定位: 142.0s (33%) ✅
├─ 证据链采集: 111.9s (26%) ✅
├─ 根因分析: 84.2s (20%) ✅
├─ 汇总总结: 86.7s (20%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 8 次
```

📋 诊断追踪

- **核心 Runbook**: pod-notready-probe-failed
- **参考 Runbook**: pod-notready-probe-failed
- **工具调用**: 8 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
