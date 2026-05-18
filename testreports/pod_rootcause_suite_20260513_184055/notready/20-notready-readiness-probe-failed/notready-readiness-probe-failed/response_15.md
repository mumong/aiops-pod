======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: b74cd5b3a3064007]

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
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=0 status_counts={'Running': 47}
aiops-e2e 中 rc-notready-readiness 为 0/1 Running，标签包含 pod_abnormal_type=NotReadyProbeFailed。
key_facts: ["aiops-e2e
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
  "reasoning": "识别到异常 Pod aiops-e2e 中的 rc-notready-readiness 状态为 0/1 Running，且 pod_abnormal_type=NotReadyProbeFailed。根据 runbook，此状态归类为 L4 层级，需检查 readinessProbe 配置、应用健康接口、livenessProbe 及 Service Endpoints。",
  "abnormal_pods": [
    {
      "name": "rc-notready-readiness",
      "namespace": "aiops-e2e",
      "status": "0/1 Running",
      "abnormal_type": "NotReadyProbeFailed"
    }
  ],
  "abnormal_groups": [
    {
      "type": "NotReadyProbeFailed",
      "count": 1
    }
  ],
  "pod_status_keyword": "0/1 Running",
  "pod_abnormal_type": "NotReadyProbeFailed",
  "status_category": "Running",
  "key_entities": [
    "rc-notready-readiness",
    "readinessProbe",
    "livenessProbe",
    "Service Endpoints"
  ],
  "possible_scenarios": [
    "readinessProbe 配置错误（如路径、端口、超时时间）",
    "应用健康接口返回异常（如 500 错误或超时）",
    "livenessProbe 失败导致容器重启",
    "Service selector 与 Pod 标签不匹配"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (7m 38.6s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'readinessProbe 配置错误（如路径、端口、超时时间）', 'probability': 'high', 'reason': 'Pod 状态显示 0/1 Running，表明 readinessProbe 可能配置不当。'}, {'scenario': '应用健康接口返回异常（如 500 错误或超时）', 'probability': 'high', 'reason': 'Pod 处于 Running 状态但未 Ready，表明应用健康接口可能返回非 2xx/3xx 状态码或超时。'}, {'scenario': 'livenessProbe 失败导致容器重启', 'probability': 'medium', 'reason': 'livenessProbe 失败可能导致容器重启，但当前状态未显示 CrashLoopBackOffRuntime。'}, {'scenario': 'Service selector 与 Pod 标签不匹配', 'probability': 'high', 'reason': 'Service selector 与 Pod 标签不匹配可能导致服务不可用，但 Pod READY 可能正常。'}]
   entities=[{"type": "Pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}, {"type": "Probe", "name": "readinessProbe", "namespace": "aiops-e2e"}, {"type": "Probe", "name": "livenessProbe", "namespace": "aiops-e2e"}, {"type": "Service", "name": "Service Endpoints", "namespace": "aiops-e2e"}]
   reasoning=识别到异常 Pod aiops-e2e 中的 rc-notready-readiness 状态为 0/1 Running，且 pod_abnormal_type=NotReadyProbeFailed。根据 runbook，此状态归类为 L4 层级，需检查 readinessProbe 配置、应用健康接口、livenessProbe 及 Service Endpoints。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "NotReadyProbeFailed", "confidence": 0.5, "reasoning": "识别到异常 Pod aiops-e2e 中的 rc-notready-readiness 状态为 0/1 Running，且 pod_abnormal_type=NotReadyProbeFailed。根据 runbook，此状态归类为 L4 层级，需检查 readinessProbe 配置、应用健康接口、livenessProbe 及 Service Endpoints。", "abnormal_pods": [{"name": "rc-notready-readiness", "namespace": "aiops-e2e", "status": "0/1 Running"}], "pod_status_keyword": "0/1 Running", "pod_abnormal_type": "NotReadyProbeFailed", "status_category": "Running", "key_entities": [{"type": "Pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}, {"type": "Probe", "name": "readinessProbe", "namespace": "aiops-e2e"}, {"type": "Probe", "name": "livenessProbe", "namespace": "aiops-e2e"}, {"type": "Service", "name": "Service Endpoints", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "readinessProbe 配置错误（如路径、端口、超时时间）", "probability": "high", "reason": "Pod 状态显示 0/1 Running，表明 readinessProbe 可能配置不当。"}, {"scenario": "应用健康接口返回异常（如 500 错误或超时）", "probability": "high", "reason": "Pod 处于 Running 状态但未 Ready，表明应用健康接口可能返回非 2xx/3xx 状态码或超时。"}, {"scenario": "livenessProbe 失败导致容器重启", "probability": "medium", "reason": "livenessProbe 失败可能导致容器重启，但当前状态未显示 CrashLoopBackOffRuntime。"}, {"scenario": "Service selector 与 Pod 标签不匹配", "probability": "high", "reason": "Service selector 与 Pod 标签不匹配可能导致服务不可用，但 Pod READY 可能正常。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["0/1 Running"], "pod_abnormal_type": "0/1 Running", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "0/1 Running 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["0/1 Running"], "pod_abnormal_type": "0/1 Running", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "0/1 Running 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 0, "selected_rows": [], "raw_ref": "/tmp/aiops/reports/context_archives/b74cd5b3a3064007/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/b74cd5b3a3064007/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/b74cd5b3a3064007/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
  Warning  Unhealthy  2m8s (x1458 over 72m)  kubelet  Readiness probe failed: readine
   💭 [证据链采集] 调用工具: kubectl_logs
   💭 [证据链采集] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=218 lines=4
Command failed (exit 1):
kubectl get --show-labels -o wide service Service Endpoints -n aiops-e2e
Error from server (NotFound): services "Service" not f
   💭 [证据链采集] 已采集证据：
- e1: kubectl describe pod 显示 readinessProbe 失败，原因 `readiness dependency unavailable`，状态为 Running 但未 Ready。
- e2: kubectl logs 无输出，表示容器未产生日志。
- e3: kubectl get service 报错 `services "Service" not found`，表示 Service Endpoints 不存在。

冲突证据：
- Service Endpoints 不存在，表明 Service 可能未正确配置或命名错误。

结论：
1. Pod `rc-notready-readiness` 处于 Running 但未 Ready 状态，readinessProbe 失败，需检查探针配置是否与应用实际监听端口/路径一致。
2. 应用健康接口未返回日志，可能是探针配置错误或应用未正确响应。
3. Service Endpoints 不存在，可能是 Service 配置错误或命名错误，需验证 Service 定义是否匹配 Pod 标签。
   ✅ [证据链采集] 完成 (1m 31.7s)
   📤 → 下游数据: evidence_items=3/4
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod 'rc-notready-readiness' 的详细描述，以确认 readinessProbe/livenessProbe 配置和失败事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-readiness -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-notready-readiness","namespace":"aiops-e2e"},"purpose":"确认 readinessProbe/livenessProbe 配置和失败事件","evidence_type":"pod_events","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod 'rc-notready-readiness' 的最后 200 行日志，以检查健康接口或启动错误","level":"critical","tool":"kubectl_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --tail=200","tool_args":{"kind":"pod","name":"rc-notready-readiness","namespace":"aiops-e2e","tail":"200"},"purpose":"检查健康接口或启动错误","evidence_type":"pod_logs","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_logs"],"counts_for_completeness":true},{"id":"e3","description":"获取 Service 'Service Endpoints' 的详细描述，以确认是否包含 Pod 'rc-notready-readiness' 并 ready","level":"important","tool":"kubectl_get_by_name","command":"kubectl get service Service Endpoints -n aiops-e2e -o yaml","tool_args":{"kind":"service","name":"Service Endpoints","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"确认 Service Endpoints 是否包含该 Pod 并 ready","evidence_type":"service_endpoints","target_scope":"aiops-e2e/Service Endpoints","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-readiness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n  Warning  Unhealthy  2m8s (x1458 over 72m)  kubelet  Readiness probe failed: readiness dependency unavailable\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\nName:             rc-notready-readiness\nLabels:           app=rc-notready-readiness\n                  cni.projectcalico.org/containerID: fb8e26665bf8a745a3d1ec6dc6a9b9d528c0b6504e8895b370296a560f31067e\n                  cni.projectcalico.org/podIP: 172.16.166.186/32\n                  cni.projectcalico.org/podIPs: 172.16.166.186/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Running","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b74cd5b3a3064007/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b74cd5b3a3064007/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b74cd5b3a3064007/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_logs","data":"kubectl_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b74cd5b3a3064007/tools/002-evidence-kubectl_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b74cd5b3a3064007/tools/002-evidence-kubectl_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b74cd5b3a3064007/tools/002-evidence-kubectl_logs.summary.txt"},{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=218 lines=4\nCommand failed (exit 1):\nkubectl get --show-labels -o wide service Service Endpoints -n aiops-e2e\nError from server (NotFound): services \"Service\" not found\nError from server (NotFound): services \"Endpoints\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/b74cd5b3a3064007/tools/003-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b74cd5b3a3064007/tools/003-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b74cd5b3a3064007/tools/003-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"已采集证据：\n- e1: kubectl describe pod 显示 readinessProbe 失败，原因 `readiness dependency unavailable`，状态为 Running 但未 Ready。\n- e2: kubectl logs 无输出，表示容器未产生日志。\n- e3: kubectl get service 报错 `services \"Service\" not found`，表示 Service Endpoints 不存在。\n\n冲突证据：\n- Service Endpoints 不存在，表明 Service 可能未正确配置或命名错误。\n\n结论：\n1. Pod `rc-notready-readiness` 处于 Running 但未 Ready 状态，readinessProbe 失败，需检查探针配置是否与应用实际监听端口/路径一致。\n2. 应用健康接口未返回日志，可能是探针配置错误或应用未正确响应。\n3. Service Endpoints 不存在，可能是 Service 配置错误或命名错误，需验证 Service 定义是否匹配 Pod 标签。","collection_summary":"计划 3 项，实际采集 2 项，未采集 1 项，完整度 67%；其中真实环境证据 3/4 项，完整度 75%；实际执行工具 4 个，匹配计划 2 个，未规划证据 2 个","plan_total":3,"plan_collected":2,"plan_completeness":0.6666666666666666,"environment_evidence_total":4,"environment_evidence_collected":3,"environment_evidence_completeness":0.75,"executed_tool_count":4,"matched_tool_count":2,"unplanned_tool_count":2,"evidence_inventory":[{"id":"e1","description":"获取 Pod 'rc-notready-readiness' 的详细描述，以确认 readinessProbe/livenessProbe 配置和失败事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-readiness -n aiops-e2e","purpose":"确认 readinessProbe/livenessProbe 配置和失败事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod 'rc-notready-readiness' 的最后 200 行日志，以检查健康接口或启动错误","level":"critical","tool":"kubectl_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --tail=200","purpose":"检查健康接口或启动错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取 Service 'Service Endpoints' 的详细描述，以确认是否包含 Pod 'rc-notready-readiness' 并 ready","level":"important","tool":"kubectl_get_by_name","command":"kubectl get service Service Endpoints -n aiops-e2e -o yaml","purpose":"确认 Service Endpoints 是否包含该 Pod 并 ready","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e3(获取 Service 'Service Endpoints' 的详细描述，以确认是否包含 Pod 'rc-notready-readiness' 并 ready): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/3 项, 完整度: 75%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取 Pod 'rc-notready-readiness' 的详细描述，以确认 read... | `kubectl describe pod rc-notready-readiness -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_logs | 获取 Pod 'rc-notready-readiness' 的最后 200 行日志，以检... | `kubectl logs rc-notready-readiness -n aiops-e2e --tail=200` |
   | e3 | important | ❌ | kubectl_get_by_name | 获取 Service 'Service Endpoints' 的详细描述，以确认是否包含 ... | `kubectl get service Service Endpoints -n aiops-e2e -o yaml` |

   ⚠️ 未采集原因:
   - e3(获取 Service 'Service Endpoints' 的详细描述，以确认是否包含 Pod 'rc-notready-readiness' 并 ready): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (15.3s)
   📤 → 下游数据: root_cause=Pod rc-notready-readiness 的 readinessProbe 失败，原因为 readiness dependency unavailable。这表明探针依赖的服务或资源未就绪，导致 Pod 无法变为 Ready 状态。
   confidence=80%
   causal_chain={"root_cause": "readiness dependency unavailable", "immediate_cause": "readinessProbe 失败", "symptom": "Pod rc-notready-readiness 为 0/1 Running 状态"}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [{"e1": "readinessProbe 失败，原因: readiness dependency unavailable。这表明探针依赖的服务或资源未就绪。"}, {"e2": "kubectl logs 无输出，表明容器未产生日志或健康接口未被调用。"}, {"layer_1": "Pod rc-notready-readiness 处于 0/1 Running 状态，且被标记为 NotReadyProbeFailed。"}], "causal_chain": {"root_cause": "readiness dependency unavailable", "immediate_cause": "readinessProbe 失败", "symptom": "Pod rc-notready-readiness 为 0/1 Running 状态"}, "root_cause": "Pod rc-notready-readiness 的 readinessProbe 失败，原因为 readiness dependency unavailable。这表明探针依赖的服务或资源未就绪，导致 Pod 无法变为 Ready 状态。", "root_cause_summary": "Pod rc-notready-readiness 的 readinessProbe 失败，原因为 readiness dependency unavailable。这表明探针依赖的服务或资源未就绪，导致 Pod 无法变为 Ready 状态。", "confidence": 0.8, "confidence_reason": "", "primary_runbooks": [], "alternative_causes": [], "limitations": "缺少 Service 'Service Endpoints' 的详细描述，无法确认是否包含 Pod 'rc-notready-readiness' 并 ready。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-notready-readiness 的 readinessProbe 失败，原因为 readiness dependency unavailable。这表明探针依赖的服务或资源未就绪，导致 Pod 无法变为 Ready 状态。
   置信度: 80%
   🔗 因果链:
     根本原因: readiness dependency unavailable


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 17.1s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4113 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 10m 42.7s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | `0/1 Running`, `pod_abnormal_type=NotReadyProbeFailed` |
| **兼容归因层** | `L4` |
| **问题分类** | `readinessProbe 失败` |
| **置信度** | 高 (80%) |
| **证据完整度** | 2/3 (67%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题？

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `rc-notready-readiness` |
| Namespace | `aiops-e2e` |
| Node | `node1/10.2.0.49` |
| 错误信息 | `Readiness probe failed: readinessProbe` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl describe pod rc-notready-readiness -n aiops-e2e` | `Warning  Unhealthy  2m8s (x1458 over 72m)  kubelet  Readiness probe failed: readinessProbe` | readinessProbe 失败，Pod 无法变为 Ready 状态 |
| 2 | Pod 日志 | `kubectl logs rc-notready-readiness -n aiops-e2e` | `no output` | 未发现明确错误，需进一步检查探针配置或依赖服务 |
| 3 | 集群 Pod 状态 | `kubectl get pod -A` | `aiops-e2e 中 rc-notready-readiness 为 0/1 Running，标签包含 pod_abnormal_type=NotReadyProbeFailed` | 仅 1 个 Pod 异常，其余 Pod 状态正常 |

### 证据关联分析

- **证据 #1 印证**：`Warning  Unhealthy` + `Readiness probe failed` → readinessProbe 配置或依赖资源异常。
- **证据 #2 印证**：日志无输出，说明探针失败并非由应用错误直接导致，更可能是探针配置或外部依赖问题。
- **证据 #3 印证**：Pod 处于 `Running` 状态但 `Ready: 0/1`，说明容器已启动，但健康检查失败。

### 缺失证据

| 证据 | 级别 | 影响 |
|------|------|------|
| Service 'Service Endpoints' 配置 | critical | 无法确认 Service 是否指向该 Pod，或是否包含其 Endpoints |
| readinessProbe 具体配置 | important | 无法判断探针路径、端口、超时时间是否合理 |
| 应用健康接口响应 | important | 无法确认健康接口是否正常返回 2xx/3xx 状态码 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ readinessProbe 依赖的外部服务或资源未就绪                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ readinessProbe 无法连接到健康接口或健康接口返回异常             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ readinessProbe 失败，导致 Pod 无法变为 Ready 状态               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 0/1 Running，Service 无法发现该 Pod 为 Ready         │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1（`Readiness probe failed`）和证据 #3（`0/1 Running`），问题的根本原因是 **readinessProbe 依赖的服务或资源未就绪**，导致探针失败，Pod 无法变为 Ready 状态。  
**置信度**：高 (80%)  
- ✅ 探针失败事件频繁（`x1458 over 72m`）  
- ✅ Pod 已 Running，说明容器本身无问题  
- ⚠️ 缺少 Service Endpoints 信息，无法确认是否服务未正确指向该 Pod  

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查 readinessProbe 配置**
```bash
kubectl describe pod rc-notready-readiness -n aiops-e2e | grep -A 5 'Readiness:'
```
*目的*：确认探针路径、端口、超时时间、initialDelaySeconds 是否合理

**2. [优先] 检查 Service Endpoints**
```bash
kubectl get endpoints -n aiops-e2e
```
*目的*：确认 Service 是否包含 `rc-notready-readiness` Pod，并标记为 Ready

**3. [可选] 检查 readiness 接口响应**
```bash
curl -I http://<pod-ip>:<port>/<health-path>
```
*目的*：手动测试健康接口是否返回 2xx/3xx 状态码

**4. [可选] 增加探针容忍时间**
```bash
kubectl set probe deployment/<deployment-name> -n aiops-e2e --readiness --initial-delay-seconds=30 --period-seconds=10
```
*目的*：给应用更多启动时间，适用于冷启动或依赖初始化时间较长的场景

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 是否变为 Ready | `kubectl get pod rc-notready-readiness -n aiops-e2e` | READY: 1/1 |
| 2. 检查 readiness 探针事件 | `kubectl describe pod rc-notready-readiness -n aiops-e2e` | 无 `Unhealthy` 或 `Failed` 事件 |
| 3. 检查 Service Endpoints | `kubectl get endpoints -n aiops-e2e` | 包含 `rc-notready-readiness` 并标记为 Ready |

---

## ⚠️ 注意事项

- 如果 readinessProbe 依赖其他服务，请检查这些服务是否已 Ready。
- 如果探针配置无误，考虑临时放宽探针参数（如 `initialDelaySeconds`）以适应启动延迟。
- 检查应用日志，确认健康接口是否被正确调用，避免应用逻辑导致健康接口返回异常。

---

## 📊 性能统计

├─ 总耗时: 10.7m
├─ 问题定位: 458.6s (71%) ✅
├─ 证据链采集: 91.7s (14%) ✅
├─ 根因分析: 15.3s (2%) ✅
├─ 汇总总结: 77.1s (12%) ✅
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
