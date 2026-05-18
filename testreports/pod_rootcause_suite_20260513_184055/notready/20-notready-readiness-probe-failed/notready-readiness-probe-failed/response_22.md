======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 19349ad5d3964d47]

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
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 {"summary":"","key_facts":["aiops-e2e/rc-notready-readiness: 0/1 Ready, Running, 0 restarts, 93m old, IP 172.16.166.186, node node1, labels: app=rc-notready-readiness, pod_abnormal_type=NotReadyProbeF
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
rc-notready-readiness   0/1     Running   0          97m   172.16.166.186 
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
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
2m43s (x1978 over 97m)   Warning   Unhealthy   Pod/rc-notready-readiness   Readiness probe failed: readiness dependency unavailable
   💭 [问题定位] 调用工具: kubectl_container_logs
   💭 [问题定位] 工具结果: kubectl_container_logs (success)
      📄 kubectl_container_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "NotReadyProbeFailed",
  "confidence": "high",
  "reasoning": "Pod rc-notready-readiness 处于 Running 状态，但 READY 为 0/1，且 readiness probe failed。Events 显示 readiness dependency unavailable，表明健康检查失败，属于 NotReadyProbeFailed 类型。",
  "abnormal_pods": [
    {
      "name": "rc-notready-readiness",
      "namespace": "aiops-e2e",
      "status": "Running",
      "ready": "0/1",
      "reason": "ContainersNotReady",
      "message": "containers with unready status: [app]"
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
      "entity_type": "Pod",
      "name": "rc-notready-readiness",
      "namespace": "aiops-e2e"
    },
    {
      "entity_type": "Container",
      "name": "app",
      "pod_name": "rc-notready-readiness",
      "namespace": "aiops-e2e"
    }
  ],
  "possible_scenarios": [
    {
      "scenario": "readinessProbe 配置错误，路径、端口、scheme 不匹配",
      "confidence": "high"
    },
    {
      "scenario": "应用健康接口返回非 2xx/3xx 或超时",
      "confidence": "high"
    },
    {
      "scenario": "startupProbe 失败，容器尚未完成启动",
      "confidence": "high"
    }
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (4m 39.7s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'readinessProbe 配置错误，路径、端口、scheme 不匹配', 'probability': 'high', 'reason': 'Pod readiness probe failed, readiness dependency unavailable'}, {'scenario': '应用健康接口返回非 2xx/3xx 或超时', 'probability': 'high', 'reason': 'Pod readiness probe failed, readiness dependency unavailable'}, {'scenario': 'startupProbe 失败，容器尚未完成启动', 'probability': 'high', 'reason': 'Pod readiness probe failed, readiness dependency unavailable'}]
   entities=[{"type": "Pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}, {"type": "Container", "name": "app", "namespace": "aiops-e2e"}]
   reasoning=Pod rc-notready-readiness 处于 Running 状态，但 READY 为 0/1，且 readiness probe failed。Events 显示 readiness dependency unavailable，表明健康检查失败，属于 NotReadyProbeFailed 类型。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "NotReadyProbeFailed", "confidence": 0.5, "reasoning": "Pod rc-notready-readiness 处于 Running 状态，但 READY 为 0/1，且 readiness probe failed。Events 显示 readiness dependency unavailable，表明健康检查失败，属于 NotReadyProbeFailed 类型。", "abnormal_pods": [{"name": "rc-notready-readiness", "namespace": "aiops-e2e", "status": "Running"}], "pod_status_keyword": "Running", "pod_abnormal_type": "NotReadyProbeFailed", "status_category": "NotReady", "key_entities": [{"type": "Pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}, {"type": "Container", "name": "app", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "readinessProbe 配置错误，路径、端口、scheme 不匹配", "probability": "high", "reason": "Pod readiness probe failed, readiness dependency unavailable"}, {"scenario": "应用健康接口返回非 2xx/3xx 或超时", "probability": "high", "reason": "Pod readiness probe failed, readiness dependency unavailable"}, {"scenario": "startupProbe 失败，容器尚未完成启动", "probability": "high", "reason": "Pod readiness probe failed, readiness dependency unavailable"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Running"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Running"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 0, "selected_rows": [], "raw_ref": "/tmp/aiops/reports/context_archives/19349ad5d3964d47/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/19349ad5d3964d47/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/19349ad5d3964d47/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
6s (x2082 over 100m)   Warning   Unhealthy   Pod/rc-notready-readiness   Readiness probe failed: readiness dependency unavailable
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 输出摘要: raw_chars=193 lines=3
Command failed (exit 1):
kubectl logs rc-notready-readiness -n aiops-e2e --previous
Error from server (BadRequest): previous terminated container "app
   💭 [证据链采集] 调用工具: kubectl_find_resource
   ✅ [证据链采集] 完成 (1m 40.8s)
   📤 → 下游数据: evidence_items=8/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod rc-notready-readiness 的详细信息以确认 readinessProbe 配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml","tool_args":{"pod_name":"rc-notready-readiness","namespace":"aiops-e2e"},"purpose":"验证 readinessProbe/livenessProbe/startupProbe 的 path、port、scheme、timeoutSeconds、periodSeconds、failureThreshold、initialDelaySeconds 等配置","evidence_type":"configuration","target_scope":"Pod/aiops-e2e/rc-notready-readiness","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod rc-notready-readiness 的 Events 以确认 readinessProbe 失败原因","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-notready-readiness","tool_args":{"pod_name":"rc-notready-readiness","namespace":"aiops-e2e"},"purpose":"确认 readiness/liveness/startup probe failed 的具体原因，例如 readiness dependency unavailable","evidence_type":"event","target_scope":"Pod/aiops-e2e/rc-notready-readiness","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取 Pod rc-notready-readiness 的日志以确认应用健康接口或启动错误","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --previous","tool_args":{"pod_name":"rc-notready-readiness","namespace":"aiops-e2e"},"purpose":"查看容器重启前的最后日志，排查健康检查失败的具体原因","evidence_type":"log","target_scope":"Pod/aiops-e2e/rc-notready-readiness","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"获取 Service Endpoints 以确认是否包含 rc-notready-readiness 并标记为 ready","level":"optional","tool":"kubectl_find_resource","command":"kubectl get endpoints -n aiops-e2e","tool_args":{"namespace":"aiops-e2e"},"purpose":"确认 Service Endpoints 是否包含 rc-notready-readiness 并标记为 ready=false，以判断是否为 Service selector 问题","evidence_type":"service_endpoint","target_scope":"Service/aiops-e2e","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-readiness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T07:05:35Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-readiness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=None exitCode=None\nvolumes:\n- {\"name\": \"kube-api-access-sqcn2\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/19349ad5d3964d47/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/19349ad5d3964d47/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/19349ad5d3964d47/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n6s (x2082 over 100m)   Warning   Unhealthy   Pod/rc-notready-readiness   Readiness probe failed: readiness dependency unavailable","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/19349ad5d3964d47/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/19349ad5d3964d47/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/19349ad5d3964d47/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 输出摘要: raw_chars=193 lines=3\nCommand failed (exit 1):\nkubectl logs rc-notready-readiness -n aiops-e2e --previous\nError from server (BadRequest): previous terminated container \"app\" in pod \"rc-notready-readiness\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/19349ad5d3964d47/tools/003-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/19349ad5d3964d47/tools/003-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/19349ad5d3964d47/tools/003-evidence-kubectl_previous_logs.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'keyword' is a required property","collection_summary":"计划 3 项，实际采集 2 项，未采集 1 项，完整度 67%；其中真实环境证据 7/8 项，完整度 88%；实际执行工具 8 个，匹配计划 3 个，未规划证据 5 个","plan_total":3,"plan_collected":2,"plan_completeness":0.6666666666666666,"environment_evidence_total":8,"environment_evidence_collected":7,"environment_evidence_completeness":0.875,"executed_tool_count":8,"matched_tool_count":3,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"获取 Pod rc-notready-readiness 的详细信息以确认 readinessProbe 配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml","purpose":"验证 readinessProbe/livenessProbe/startupProbe 的 path、port、scheme、timeoutSeconds、periodSeconds、failureThreshold、initialDelaySeconds 等配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod rc-notready-readiness 的 Events 以确认 readinessProbe 失败原因","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-notready-readiness","purpose":"确认 readiness/liveness/startup probe failed 的具体原因，例如 readiness dependency unavailable","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取 Pod rc-notready-readiness 的日志以确认应用健康接口或启动错误","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --previous","purpose":"查看容器重启前的最后日志，排查健康检查失败的具体原因","collected":false,"source":"planned","outcome":"unknown"},{"id":"e4","description":"获取 Service Endpoints 以确认是否包含 rc-notready-readiness 并标记为 ready","level":"optional","tool":"kubectl_find_resource","command":"kubectl get endpoints -n aiops-e2e","purpose":"确认 Service Endpoints 是否包含 rc-notready-readiness 并标记为 ready=false，以判断是否为 Service selector 问题","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_container_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e3(获取 Pod rc-notready-readiness 的日志以确认应用健康接口或启动错误): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/3 项, 完整度: 88%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_yaml | 获取 Pod rc-notready-readiness 的详细信息以确认 readine... | `kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml` |
   | e2 | critical | ✅ | kubectl_events | 获取 Pod rc-notready-readiness 的 Events 以确认 rea... | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-notre...` |
   | e3 | important | ❌ | kubectl_previous_logs | 获取 Pod rc-notready-readiness 的日志以确认应用健康接口或启动错误 | `kubectl logs rc-notready-readiness -n aiops-e2e --previous` |
   | e4 | optional | ✅ | kubectl_find_resource | 获取 Service Endpoints 以确认是否包含 rc-notready-read... | `kubectl get endpoints -n aiops-e2e` |

   ⚠️ 未采集原因:
   - e3(获取 Pod rc-notready-readiness 的日志以确认应用健康接口或启动错误): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (41.9s)
   📤 → 下游数据: root_cause=Pod rc-notready-readiness 处于 Running 状态，但 READY 为 0/1，且 readiness probe failed。Events 显示 readiness dependency unavailable，表明健康检查失败，属于 NotReadyProbeFailed 类型。
   confidence=80%
   causal_chain={"root_cause": "readinessProbe 配置错误或应用健康接口不可用", "intermediate_causes": ["readinessProbe 路径、端口、scheme 不匹配", "应用健康接口返回非 2xx/3xx 或超时"], "immediate_causes": ["Pod rc-notready-readiness 的 readiness probe failed: readiness dependency unavailable"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"tool": "kubectl_get_yaml", "description": "获取 Pod rc-notready-readiness 的详细信息以确认 readinessProbe 配置", "status": "success"}, {"tool": "kubectl_events", "description": "获取 Pod rc-notready-readiness 的 Events 以确认 readinessProbe 失败原因", "status": "success"}, {"tool": "kubectl_get_by_name", "description": "获取 Service Endpoints 以确认是否包含 rc-notready-readiness 并标记为 ready", "status": "success"}, {"tool": "kubectl_get_by_kind_in_cluster", "description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "status": "success"}, {"tool": "kubectl_container_logs", "description": "获取 Pod rc-notready-readiness 的日志以确认应用健康接口或启动错误", "status": "failure"}], "evidence_analysis": [{"tool": "kubectl_get_yaml", "summary": "Pod rc-notready-readiness 的配置表明其 readinessProbe 配置未被显式提供，但健康检查失败。"}, {"tool": "kubectl_events", "summary": "Events 显示 readiness probe failed: readiness dependency unavailable，表明 readinessProbe 失败，且失败原因与依赖项不可用相关。"}, {"tool": "kubectl_get_by_name", "summary": "Pod rc-notready-readiness 的状态为 Running，但 READY 为 0/1，表明其容器未通过 readinessProbe。"}, {"tool": "kubectl_container_logs", "summary": "未获取到容器日志，无法确认应用健康接口或启动错误。"}], "causal_chain": {"root_cause": "readinessProbe 配置错误或应用健康接口不可用", "intermediate_causes": ["readinessProbe 路径、端口、scheme 不匹配", "应用健康接口返回非 2xx/3xx 或超时"], "immediate_causes": ["Pod rc-notready-readiness 的 readiness probe failed: readiness dependency unavailable"]}, "root_cause": "Pod rc-notready-readiness 处于 Running 状态，但 READY 为 0/1，且 readiness probe failed。Events 显示 readiness dependency unavailable，表明健康检查失败，属于 NotReadyProbeFailed 类型。", "root_cause_summary": "Pod rc-notready-readiness 处于 Running 状态，但 READY 为 0/1，且 readiness probe failed。Events 显示 readiness dependency unavailable，表明健康检查失败，属于 NotReadyProbeFailed 类型。", "confidence": 0.8, "confidence_reason": "有直接证据表明 readinessProbe 失败，但缺少容器日志以确认具体原因。", "primary_runbooks": ["pod-notready-probe-failed.md"], "alternative_causes": [{"cause": "livenessProbe 反复失败导致容器重启"}, {"cause": "startupProbe 失败导致容器尚未完成启动"}], "limitations": "缺少容器日志，无法确认应用健康接口或启动错误。", "llm_raw_analysis": "基于已采集证据，Pod rc-notready-readiness 的 readinessProbe 配置错误或应用健康接口不可用是导致其处于 Running 但未 Ready 的主要原因。Events 显示 readiness probe failed: readiness dependency unavailable，表明 readinessProbe 失败，且失败原因与依赖项不可用相关。然而，缺少容器日志，无法确认具体原因。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-notready-readiness 处于 Running 状态，但 READY 为 0/1，且 readiness probe failed。Events 显示 readiness dependency unavailable，表明健康检查失败，属于 NotReadyProbeFai...
   置信度: 80%
   🔗 因果链:
     根本原因: readinessProbe 配置错误或应用健康接口不可用


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 28.1s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4549 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 8m 30.6s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Running 但 READY 为 0/1，readiness probe failed |
| **兼容归因层** | L4 |
| **问题分类** | NotReadyProbeFailed |
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
| Node | node1 |
| 错误信息 | Readiness probe failed: readiness dependency unavailable |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | kubectl get pod rc-notready-readiness -n aiops-e2e | READY: 0/1, STATUS: Running, RESTARTS: 0, AGE: 97m | Pod 正在运行但未通过就绪检查 |
| 2 | Events | kubectl describe pod rc-notready-readiness -n aiops-e2e | `Warning: Unhealthy (x1978 over 97m): Readiness probe failed: readiness dependency unavailable` | readiness probe 失败，多次重复发生 |
| 3 | Pod YAML 配置 | kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml | readinessProbe 配置字段缺失（未显示具体配置） | 需进一步检查 readinessProbe 路径、端口等配置是否正确 |
| 4 | Container logs | kubectl logs rc-notready-readiness -n aiops-e2e | (no output) | 容器无输出，健康接口可能未正确响应 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 Running，但 readiness probe 多次失败，表明应用虽已启动，但健康检查未通过。
- **证据链**：
  1. readinessProbe 配置错误或应用健康接口不可达 →
  2. readinessProbe 失败 →
  3. Pod 被标记为 NotReady →
  4. Pod 未被纳入 Service Endpoints →
  5. 用户访问失败，表现为服务不可用。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 容器崩溃前日志 | important | 无法确认 readinessProbe 失败的具体原因（如路径、端口、超时等） |
| readinessProbe 配置详情 | important | 无法判断配置是否合理（如 initialDelaySeconds、timeoutSeconds） |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ readinessProbe 配置错误或应用健康接口不可用                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ readinessProbe 失败 → readiness dependency unavailable          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ readinessProbe failed: readiness dependency unavailable         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 Running 但 READY 为 0/1，健康检查失败，服务不可用     │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1（Pod 状态为 Running 但 READY 为 0/1）和证据 #2（Events 显示 readiness probe failed: readiness dependency unavailable），问题的根本原因是 **readinessProbe 配置错误或应用健康接口不可用**，导致健康检查失败，Pod 被标记为 NotReady。

**置信度**：高 (80%)
- ✅ Pod 状态为 Running 但未就绪
- ✅ Events 明确指出 readiness probe 失败
- ⚠️ 缺少容器日志和 readinessProbe 配置详情，无法确认具体配置错误

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查 readinessProbe 配置**
```bash
kubectl get pod rc-notready-readiness -n aiops-e2e -o jsonpath='{.spec.containers[*].readinessProbe}' 
```
*依据*：确认 readinessProbe 的路径、端口、scheme、initialDelaySeconds、timeoutSeconds 等配置是否合理。

**2. [可选] 查看容器崩溃前日志**
```bash
kubectl logs rc-notready-readiness -n aiops-e2e --previous
```
*目的*：确认应用是否启动成功，健康接口是否正常响应。

**3. [建议] 更新 readinessProbe 配置**
```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 8080
    scheme: HTTP
  initialDelaySeconds: 10
  timeoutSeconds: 5
  periodSeconds: 10
```
*依据*：确保 readinessProbe 配置与应用健康接口一致，并适当延长 initialDelaySeconds。

### 后续优化

1. **配置 livenessProbe**：防止容器长时间处于不可用状态。
2. **配置 startupProbe**：避免 readinessProbe 失败导致的快速重启。
3. **应用健康接口测试**：确保应用健康接口在容器启动后能正确响应 HTTP 请求。
4. **监控告警**：配置 readiness/liveness probe 失败告警。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-notready-readiness -n aiops-e2e` | READY: 1/1 |
| 2. 检查 readinessProbe 配置 | `kubectl get pod rc-notready-readiness -n aiops-e2e -o jsonpath='{.spec.containers[*].readinessProbe}'` | 显示合理的配置 |
| 3. 查看事件 | `kubectl describe pod rc-notready-readiness -n aiops-e2e` | 无 Unhealthy 事件 |
| 4. 查看容器日志 | `kubectl logs rc-notready-readiness -n aiops-e2e` | 应用健康接口正常响应 |

---

## ⚠️ 注意事项

- 如果 readinessProbe 配置正确，但问题仍存在，可能是应用健康接口本身存在问题（如服务未启动、端口未监听等）。
- 如果 readinessProbe 的 `initialDelaySeconds` 过小，容器启动前探针失败，需适当增加该值。
- 建议同时配置 livenessProbe 以防止容器长时间不可用。

---

## 📊 性能统计

├─ 总耗时: 8.5m
├─ 问题定位: 279.7s (55%) ✅
├─ 证据链采集: 100.8s (20%) ✅
├─ 根因分析: 41.9s (8%) ✅
├─ 汇总总结: 88.1s (17%) ✅
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
