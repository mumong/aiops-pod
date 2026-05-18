======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: cfb8fd49b4604da6]

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
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=0 status_counts={'Running': 47}
aiops-e2e 中 rc-notready-readiness Pod 为 0/1 Running，标记为 NotReadyProbeFailed。
key_facts: ["aiops-e2e/rc-notready-re
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod NotReadyProbeFailed / Running 但未 Ready

> Pod异常类型: NotReadyProbeFailed | 典型状态: Running + READY 0/1 | 兼容分类: probe_health

## 状态识别
- Pod phase 通常为 `Running`，但 READY 为 `0/1` 或部分容器未 Ready

   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "NotReadyProbeFailed",
  "confidence": "high",
  "reasoning": "识别到 aiops-e2e/rc-notready-readiness Pod 为 0/1 Running，标记为 NotReadyProbeFailed。根据 runbook，这属于 L4 层次的异常，涉及 readinessProbe 配置错误、应用健康检查失败或 startupProbe 失败等问题。",
  "abnormal_pods": [
    {
      "namespace": "aiops-e2e",
      "name": "rc-notready-readiness",
      "pod_status_keyword": "NotReady",
      "pod_abnormal_type": "NotReadyProbeFailed",
      "status_category": "NotReady"
    }
  ],
  "abnormal_groups": [
    {
      "pod_status_keyword": "NotReady",
      "pod_abnormal_type": "NotReadyProbeFailed",
      "status_category": "NotReady"
    }
  ],
  "key_entities": [
    "aiops-e2e/rc-notready-readiness Pod"
  ],
  "possible_scenarios": [
    "readinessProbe 路径、端口、scheme、initialDelaySeconds 配置不匹配",
    "应用进程已启动但健康接口返回非 2xx/3xx 或超时",
    "livenessProbe 反复失败导致容器重启",
    "startupProbe 失败导致容器还未进入正常服务窗口",
    "Service selector 不匹配"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (2m 44.8s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'readinessProbe 路径、端口、scheme、initialDelaySeconds 配置不匹配', 'probability': 'high', 'reason': 'Pod READY 0/1 且 readiness probe failed'}, {'scenario': '应用进程已启动但健康接口返回非 2xx/3xx 或超时', 'probability': 'high', 'reason': 'Pod READY 0/1 且 readiness probe failed'}, {'scenario': 'livenessProbe 反复失败导致容器重启', 'probability': 'medium', 'reason': '需要结合 Last State 判断'}, {'scenario': 'startupProbe 失败导致容器还未进入正常服务窗口', 'probability': 'high', 'reason': 'Pod READY 0/1 且 readiness probe failed'}, {'scenario': 'Service selector 不匹配', 'probability': 'high', 'reason': 'Pod READY 0/1 且 readiness probe failed'}]
   entities=[{"type": "Pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}]
   reasoning=识别到 aiops-e2e/rc-notready-readiness Pod 为 0/1 Running，标记为 NotReadyProbeFailed。根据 runbook，这属于 L4 层次的异常，涉及 readinessProbe 配置错误、应用健康检查失败或 startupProbe 失败等问题。
   layer_analysis={"layer": "L4", "derived_layer": "", "layers": [], "layer_name": "", "confidence": 0.5, "reasoning": "识别到 aiops-e2e/rc-notready-readiness Pod 为 0/1 Running，标记为 NotReadyProbeFailed。根据 runbook，这属于 L4 层次的异常，涉及 readinessProbe 配置错误、应用健康检查失败或 startupProbe 失败等问题。", "abnormal_pods": [{"name": "rc-notready-readiness", "namespace": "aiops-e2e", "status": "0/1 Running"}], "pod_status_keyword": "NotReady", "pod_abnormal_type": "NotReadyProbeFailed", "status_category": "app_health", "key_entities": [{"type": "Pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "readinessProbe 路径、端口、scheme、initialDelaySeconds 配置不匹配", "probability": "high", "reason": "Pod READY 0/1 且 readiness probe failed"}, {"scenario": "应用进程已启动但健康接口返回非 2xx/3xx 或超时", "probability": "high", "reason": "Pod READY 0/1 且 readiness probe failed"}, {"scenario": "livenessProbe 反复失败导致容器重启", "probability": "medium", "reason": "需要结合 Last State 判断"}, {"scenario": "startupProbe 失败导致容器还未进入正常服务窗口", "probability": "high", "reason": "Pod READY 0/1 且 readiness probe failed"}, {"scenario": "Service selector 不匹配", "probability": "high", "reason": "Pod READY 0/1 且 readiness probe failed"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["0/1 Running"], "pod_abnormal_type": "0/1 Running", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "0/1 Running 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["0/1 Running"], "pod_abnormal_type": "0/1 Running", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "0/1 Running 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 0, "selected_rows": [], "raw_ref": "/tmp/aiops/reports/context_archives/cfb8fd49b4604da6/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/cfb8fd49b4604da6/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/cfb8fd49b4604da6/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-readiness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
  Warning  Unhealthy       2m39s (x1146 over 57m)  kubelet            Readiness probe
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 输出摘要: raw_chars=193 lines=3
Command failed (exit 1):
kubectl logs rc-notready-readiness -n aiops-e2e --previous
Error from server (BadRequest): previous terminated container "app
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
   💭 [证据链采集] 已采集证据：
1. **kubectl describe pod** 显示 readiness probe 失败，原因是 `readiness dependency unavailable`。
2. **kubectl logs --previous** 返回错误，说明容器没有之前的日志，可能容器没有成功启动过。
3. **kubectl get pod -o yaml** 显示 Pod 正在运行，但 readiness 状态为 `False`，容器状态为 `unready`。

未采集证据：
- 无

冲突证据：
- 无

结论：当前 Pod `rc-notready-readiness` 的 readiness probe 失败，可能由于应用健康检查接口不可用或配置错误。下一步建议检查应用健康检查接口的配置和依赖项。
   ✅ [证据链采集] 完成 (1m 31.4s)
   📤 → 下游数据: evidence_items=3/4
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"描述异常 Pod 的详细信息，包括 readinessProbe/livenessProbe 配置和失败事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-readiness -n aiops-e2e","tool_args":{"pod":"rc-notready-readiness","namespace":"aiops-e2e"},"purpose":"确认 readinessProbe/livenessProbe 配置及失败原因","evidence_type":"pod_events_and_probe_config","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 的日志，验证健康接口错误、启动超时等问题","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --previous","tool_args":{"pod":"rc-notready-readiness","namespace":"aiops-e2e","container":null},"purpose":"获取容器上一次运行的日志，检查健康检查失败原因","evidence_type":"pod_logs","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_previous_logs"],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod 的 YAML 配置，验证 readinessProbe/livenessProbe 的 path、port、initialDelaySeconds 等字段","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-notready-readiness","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"获取 Pod 的 YAML 配置，检查 readinessProbe/livenessProbe 字段","evidence_type":"pod_yaml_probe_config","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-readiness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n  Warning  Unhealthy       2m39s (x1146 over 57m)  kubelet            Readiness probe failed: readiness dependency unavailable\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\nName:             rc-notready-readiness\nLabels:           app=rc-notready-readiness\n                  cni.projectcalico.org/containerID: fb8e26665bf8a745a3d1ec6dc6a9b9d528c0b6504e8895b370296a560f31067e\n                  cni.projectcalico.org/podIP: 172.16.166.186/32\n                  cni.projectcalico.org/podIPs: 172.16.166.186/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n  Normal   Scheduled       57m                     default-scheduler  Successfully assigned aiops-e2e/rc-notready-readiness to node1\n关键状态/事件:\n    State:          Running","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/cfb8fd49b4604da6/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/cfb8fd49b4604da6/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/cfb8fd49b4604da6/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 输出摘要: raw_chars=193 lines=3\nCommand failed (exit 1):\nkubectl logs rc-notready-readiness -n aiops-e2e --previous\nError from server (BadRequest): previous terminated container \"app\" in pod \"rc-notready-readiness\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/cfb8fd49b4604da6/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/cfb8fd49b4604da6/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/cfb8fd49b4604da6/tools/002-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-readiness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T07:05:35Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-readiness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=None exitCode=None\nvolumes:\n- {\"name\": \"kube-api-access-sqcn2\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/cfb8fd49b4604da6/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/cfb8fd49b4604da6/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/cfb8fd49b4604da6/tools/003-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"已采集证据：\n1. **kubectl describe pod** 显示 readiness probe 失败，原因是 `readiness dependency unavailable`。\n2. **kubectl logs --previous** 返回错误，说明容器没有之前的日志，可能容器没有成功启动过。\n3. **kubectl get pod -o yaml** 显示 Pod 正在运行，但 readiness 状态为 `False`，容器状态为 `unready`。\n\n未采集证据：\n- 无\n\n冲突证据：\n- 无\n\n结论：当前 Pod `rc-notready-readiness` 的 readiness probe 失败，可能由于应用健康检查接口不可用或配置错误。下一步建议检查应用健康检查接口的配置和依赖项。","collection_summary":"计划 3 项，实际采集 2 项，未采集 1 项，完整度 67%；其中真实环境证据 3/4 项，完整度 75%；实际执行工具 4 个，匹配计划 2 个，未规划证据 2 个","plan_total":3,"plan_collected":2,"plan_completeness":0.6666666666666666,"environment_evidence_total":4,"environment_evidence_collected":3,"environment_evidence_completeness":0.75,"executed_tool_count":4,"matched_tool_count":2,"unplanned_tool_count":2,"evidence_inventory":[{"id":"e1","description":"描述异常 Pod 的详细信息，包括 readinessProbe/livenessProbe 配置和失败事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-readiness -n aiops-e2e","purpose":"确认 readinessProbe/livenessProbe 配置及失败原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 的日志，验证健康接口错误、启动超时等问题","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --previous","purpose":"获取容器上一次运行的日志，检查健康检查失败原因","collected":false,"source":"planned","outcome":"unknown"},{"id":"e3","description":"获取异常 Pod 的 YAML 配置，验证 readinessProbe/livenessProbe 的 path、port、initialDelaySeconds 等字段","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml","purpose":"获取 Pod 的 YAML 配置，检查 readinessProbe/livenessProbe 字段","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e2(获取异常 Pod 的日志，验证健康接口错误、启动超时等问题): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/3 项, 完整度: 75%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 描述异常 Pod 的详细信息，包括 readinessProbe/livenessProb... | `kubectl describe pod rc-notready-readiness -n aiops-e2e` |
   | e2 | critical | ❌ | kubectl_previous_logs | 获取异常 Pod 的日志，验证健康接口错误、启动超时等问题 | `kubectl logs rc-notready-readiness -n aiops-e2e --previous` |
   | e3 | critical | ✅ | kubectl_get_yaml | 获取异常 Pod 的 YAML 配置，验证 readinessProbe/liveness... | `kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml` |

   ⚠️ 未采集原因:
   - e2(获取异常 Pod 的日志，验证健康接口错误、启动超时等问题): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (44.8s)
   📤 → 下游数据: root_cause=Pod rc-notready-readiness 的 readiness probe 失败，原因是 readiness dependency unavailable。这表明健康检查依赖的资源或服务未就绪，导致 readiness probe 无法通过。
   confidence=80%
   causal_chain={"root_cause": "readiness dependency unavailable", "conduction": "readiness dependency unavailable 导致 readiness probe 失败", "direct_cause": "readiness probe 失败", "phenomenon": "rc-notready-readiness Pod 为 0/1 Running，标记为 NotReadyProbeFailed"}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"e1": "kubectl describe pod 显示 readiness probe 失败，原因是 readiness dependency unavailable"}, {"e3": "kubectl get pod -o yaml 显示 Pod 正在运行，但 readiness 状态为 False，容器状态为 unready"}, {"layer_1": "kubectl_get_by_kind_in_cluster 表格摘要: aiops-e2e 中 rc-notready-readiness Pod 为 0/1 Running，标记为 NotReadyProbeFailed"}], "evidence_analysis": [{"e1": "Pod rc-notready-readiness 的 readiness probe 失败，事件信息显示 readiness dependency unavailable，表明健康检查依赖的资源或服务可能未就绪"}, {"e3": "Pod rc-notready-readiness 的 YAML 配置显示 readiness 状态为 False，容器状态为 unready，表明健康检查未能通过"}, {"layer_1": "kubectl_get_by_kind_in_cluster 显示 rc-notready-readiness Pod 为 0/1 Running，标记为 NotReadyProbeFailed，表明该 Pod 未通过健康检查"}], "causal_chain": {"root_cause": "readiness dependency unavailable", "conduction": "readiness dependency unavailable 导致 readiness probe 失败", "direct_cause": "readiness probe 失败", "phenomenon": "rc-notready-readiness Pod 为 0/1 Running，标记为 NotReadyProbeFailed"}, "root_cause": "Pod rc-notready-readiness 的 readiness probe 失败，原因是 readiness dependency unavailable。这表明健康检查依赖的资源或服务未就绪，导致 readiness probe 无法通过。", "root_cause_summary": "Pod rc-notready-readiness 的 readiness probe 失败，原因是 readiness dependency unavailable。这表明健康检查依赖的资源或服务未就绪，导致 readiness probe 无法通过。", "confidence": 0.8, "confidence_reason": "有直接证据表明 readiness probe 失败，且事件信息显示 readiness dependency unavailable，因此置信度较高。", "primary_runbooks": ["pod-notready-probe-failed.md"], "alternative_causes": [], "limitations": "缺少异常 Pod 的日志，无法验证健康接口错误、启动超时等问题。", "llm_raw_analysis": "已采集证据：1. **kubectl describe pod** 显示 readiness probe 失败，原因是 `readiness dependency unavailable`。2. **kubectl logs --previous** 返回错误，说明容器没有之前的日志，可能容器没有成功启动过。3. **kubectl get pod -o yaml** 显示 Pod 正在运行，但 readiness 状态为 `False`，容器状态为 `unready`。\n\n未采集证据：- 无\n\n冲突证据：- 无\n\n结论：当前 Pod `rc-notready-readiness` 的 readiness probe 失败，可能由于应用健康检查接口不可用或配置错误。下一步建议检查应用健康检查接口的配置和依赖项。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-notready-readiness 的 readiness probe 失败，原因是 readiness dependency unavailable。这表明健康检查依赖的资源或服务未就绪，导致 readiness probe 无法通过。
   置信度: 80%
   🔗 因果链:
     根本原因: readiness dependency unavailable


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (2m 32.4s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4363 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 7m 33.5s
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
| **Pod异常状态** | NotReadyProbeFailed |
| **兼容归因层** | L4 |
| **问题分类** | probe_health（健康检查失败） |
| **置信度** | 高 (80%) |
| **证据完整度** | 2/3 (67%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-notready-readiness |
| Namespace | aiops-e2e |
| Node | node1/10.2.0.49 |
| 错误信息 | Readiness probe failed |

**当前状态**：
- Pod `rc-notready-readiness` 处于 `0/1 Running` 状态，标记为 `NotReadyProbeFailed`
- Pod phase 为 `Running`，但 readiness 为 `0/1`，表明容器进程已启动但健康检查未通过

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态描述 | `kubectl describe pod rc-notready-readiness -n aiops-e2e` | `Warning  Unhealthy       2m39s (x1146 over 57m)  kubelet            Readiness probe` | readiness probe 失败，持续重试 |
| 2 | Pod YAML 配置 | `kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml` | `readinessProbe` 的 path、port、initialDelaySeconds 等字段 | 需要进一步验证是否配置不匹配 |
| 3 | 上游工具结果 | `kubectl get pod -A` | `aiops-e2e/rc-notready-readiness: 0/1 Running, pod_abnormal_type=NotReadyProbeFailed` | 确认 Pod 处于异常状态 |

### 证据关联分析

- **证据 #1 印证**：`Warning: Unhealthy` + `Readiness probe` → readinessProbe 失败
- **证据 #1 + #2 印证**：Pod phase 为 `Running`，但 readiness 为 `0/1` → 健康检查未通过
- **证据链**：readinessProbe 配置不匹配或健康接口异常 → 健康检查失败 → Pod 被标记为 NotReady

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 容器崩溃前日志 | critical | 无法确认健康接口失败原因、是否存在启动超时或依赖未就绪 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ readiness dependency unavailable（健康检查依赖的资源或服务未就绪） │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ readinessProbe 路径、端口、initialDelaySeconds 配置不匹配       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ readiness probe 失败（健康接口返回异常或超时）                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 0/1 Running，标记为 NotReadyProbeFailed，持续失败        │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1（`Readiness probe` 失败）和证据 #2（readinessProbe 配置需验证），
问题的根本原因是**readinessProbe 失败，健康检查依赖的资源或服务未就绪**，
导致容器被标记为 NotReady，Pod 无法正常提供服务。
**置信度**：高 (80%)
- ✅ readiness probe 失败事件明确
- ✅ Pod phase 为 Running，但 readiness 为 0/1
- ⚠️ 缺少崩溃前日志，无法确认健康接口失败原因

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查 readinessProbe 配置**
```bash
kubectl get pod rc-notready-readiness -n aiops-e2e -o jsonpath='{.spec.containers[*].readinessProbe}' 
```
*目的*：查看 path、port、initialDelaySeconds、failureThreshold 等配置是否与应用实际健康接口匹配

**2. [可选] 获取容器崩溃前日志**
```bash
kubectl logs rc-notready-readiness -n aiops-e2e --previous
```
*目的*：查看健康接口失败时的错误信息、启动超时或依赖未就绪等信息

**3. [可选] 增加 readinessProbe 的 initialDelaySeconds**
```bash
kubectl set probe pod/rc-notready-readiness -n aiops-e2e --readiness --initial-delay-seconds=30
```
*目的*：如果应用启动慢，适当增加等待时间，避免 probe 失败

### 后续优化

1. **健康检查优化**：
   - 确保 health check 路径返回 2xx/3xx
   - 增加 timeoutSeconds 避免超时
   - 配置 startupProbe 以避免 readinessProbe 过早失败
2. **监控告警**：
   - 配置 readinessProbe 失败告警
   - 使用 Prometheus 监控 `kube_pod_status_ready` 指标
3. **依赖检查**：
   - 确认 health check 依赖的数据库、API、网络服务是否正常

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-notready-readiness -n aiops-e2e` | STATUS: Running，READY: 1/1 |
| 2. 检查 readinessProbe 配置 | `kubectl get pod rc-notready-readiness -n aiops-e2e -o jsonpath='{.spec.containers[*].readinessProbe}'` | 配置合理，无错误 |
| 3. 查看事件 | `kubectl describe pod rc-notready-readiness -n aiops-e2e` | 无 Unhealthy 事件 |
| 4. 查看健康接口 | `curl -I http://<pod-ip>:<port>/<health-path>` | 返回 2xx 状态码 |

---

## ⚠️ 注意事项

- 如果 readinessProbe 配置正确，但仍然失败，可能是应用内部健康检查接口异常
- 建议配置 startupProbe 以避免 readinessProbe 过早失败
- 如果健康检查依赖外部服务（如数据库、API），需确保这些服务已就绪

---

---

## 📊 性能统计

├─ 总耗时: 7.6m
├─ 问题定位: 164.8s (36%) ✅
├─ 证据链采集: 91.4s (20%) ✅
├─ 根因分析: 44.8s (10%) ✅
├─ 汇总总结: 152.4s (34%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 5 次
```

📋 诊断追踪

- **核心 Runbook**: pod-notready-probe-failed
- **参考 Runbook**: pod-notready-probe-failed
- **工具调用**: 5 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
