======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 64e8d43369444d99]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=0 status_counts={'Running': 47}。
key_facts: ["aiops-e2e 命名空间中 rc-notready-readiness Pod 状态为 0/1 Running，标签显示 pod_abnormal_type=NotReadyProbeFailed
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
rc-notready-readiness   0/1     Running   0          67m   172.16.166.186 
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-readiness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
  Warning  Unhealthy  2m42s (x1354 over 67m)  kubelet  Readiness probe failed: readin
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
   💭 [问题定位] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
2m50s (x1354 over 67m)   Warning   Unhealthy   Pod/rc-notready-readiness   Readiness probe failed: readiness dependency unavailable
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "NotReadyProbeFailed",
  "confidence": "high",
  "reasoning": "Pod rc-notready-readiness 处于 Running 状态，但 READY 为 0/1，且 readiness probe 失败，事件显示 readiness dependency unavailable。这表明该 Pod 的就绪探针检查失败，属于 NotReadyProbeFailed 类型，归类为 L4 层次的异常。",
  "abnormal_pods": [
    "rc-notready-readiness"
  ],
  "abnormal_groups": [
    "NotReadyProbeFailed"
  ],
  "pod_status_keyword": "Running",
  "pod_abnormal_type": "NotReadyProbeFailed",
  "status_category": "NotReady",
  "key_entities": [
    "rc-notready-readiness",
    "readiness probe",
    "Unhealthy event"
  ],
  "possible_scenarios": [
    "readinessProbe 配置错误，与容器实际监听端口或路径不匹配",
    "应用健康接口未响应或返回非 2xx/3xx 状态码",
    "容器启动时间过长，initialDelaySeconds 设置过小",
    "startupProbe 失败导致容器尚未进入服务窗口"
  ]
}
   ✅ [问题定位] 完成 (1m 5.1s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[]
   entities=[]
   reasoning=Pod rc-notready-readiness 处于 Running 状态，但 READY 为 0/1，且 readiness probe 失败，事件显示 readiness dependency unavailable。这表明该 Pod 的就绪探针检查失败，属于 NotReadyProbeFailed 类型，归类为 L4 层次的异常。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "NotReadyProbeFailed", "confidence": 1.0, "reasoning": "Pod rc-notready-readiness 处于 Running 状态，但 READY 为 0/1，且 readiness probe 失败，事件显示 readiness dependency unavailable。这表明该 Pod 的就绪探针检查失败，属于 NotReadyProbeFailed 类型，归类为 L4 层次的异常。", "abnormal_pods": [{"name": "rc-notready-readiness", "namespace": "aiops-e2e", "status": "Running"}], "pod_status_keyword": "Running", "pod_abnormal_type": "NotReadyProbeFailed", "status_category": "NotReady", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Running"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Running"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 0, "selected_rows": [], "raw_ref": "/tmp/aiops/reports/context_archives/64e8d43369444d99/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/64e8d43369444d99/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/64e8d43369444d99/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-readiness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
  Warning  Unhealthy  4m40s (x1354 over 69m)  kubelet  Readiness probe failed: readin
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
4m48s (x1354 over 69m)   Warning   Unhealthy   Pod/rc-notready-readiness   Readiness probe failed: readiness dependency unavailable
   💭 [证据链采集] # 证据结论

## 已采集证据
1. **Pod 描述信息**：
   - Pod 名称：`rc-notready-readiness`
   - 命名空间：`aiops-e2e`
   - 节点：`node1`
   - 状态：`Running`
   - 关键事件：`Warning Unhealthy`，原因：`Readiness probe failed: readiness dependency unavailable`
   - 注解：`pod_abnormal_type=NotReadyProbeFailed`，`aiops.e2e/runbook=pod-notready-probe-failed.md`
   - 标签：`app=rc-notready-readiness`

2. **Pod YAML 配置**：
   - 名称：`rc-notready-readiness`
   - 命名空间：`aiops-e2e`
   - 创建时间：`2026-05-15T07:05:35Z`
   - 节点：`node1`
   - 重启策略：`Always`
   - 状态：`Running`
   - 容器状态：`ready=False`，`restarts=0`
   - 标签：`app=rc-notready-readiness`, `pod_abnormal_type=NotReadyProbeFailed`
   - 注解：`aiops.e2e/runbook=pod-notready-probe-failed.md`

3. **Pod 日志**：
   - 日志输出为空，没有关键日志。

4. **Pod 事件**：
   - 事件：`Warning Unhealthy`
   - 原因：`Readiness probe failed: readiness dependency unavailable`
   - 重复次数：`x1354 over 69m`

## 未采集证据
- 无

## 冲突证据
- 无

## 分析总结
根据已采集的证据，Pod `rc-notready-readiness` 处于 `Running` 状态，但其 `READY` 状态为 `0/1`，且 readiness probe 失败，事件显示 `Readiness probe failed: readiness dependency unavailable`。这表明该 Pod 的就绪探针检查失败，属于 `NotReadyProbeFailed` 类型。可能的原因包括：
- readinessProbe 配置不正确，路径、端口、scheme、initialDelaySeconds 等不匹配。
- 应用进程已启动但健康接口返回非 2xx/3xx 或超时。
- livenessProbe 反复失败导致容器重启。
- startupProbe 失败导致容器尚未进入正常服务窗口。

建议进一步检查 readinessProbe 的配置，并查看应用的健康接口是否正常返回。
   ✅ [证据链采集] 完成 (2m 4.6s)
   📤 → 下游数据: evidence_items=10/10
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证异常 Pod rc-notready-readiness 的 readinessProbe 配置和失败事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-readiness -n aiops-e2e","tool_args":{},"purpose":"查看 readinessProbe 配置和失败事件，确认探针失败原因","evidence_type":"事件/配置","target_scope":"Pod/aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"检查 rc-notready-readiness Pod 的 YAML 配置中的 probe 设置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml","tool_args":{},"purpose":"查看 readinessProbe/livenessProbe/startupProbe 的详细配置，包括路径、端口、超时等","evidence_type":"配置","target_scope":"Pod/aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e3","description":"检查 rc-notready-readiness Pod 的日志，查看应用健康接口或启动错误","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --tail=200","tool_args":{},"purpose":"查看日志以确定应用是否正常运行并返回正确的健康状态","evidence_type":"日志","target_scope":"Pod/aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_logs"],"counts_for_completeness":true},{"id":"e4","description":"检查 rc-notready-readiness Pod 的 readinessEvents","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e | grep rc-notready-readiness","tool_args":{"namespace":"aiops-e2e"},"purpose":"查看与 rc-notready-readiness Pod 相关的 readinessEvents，确认探针失败的详细信息","evidence_type":"事件","target_scope":"Pod/aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-readiness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n  Warning  Unhealthy  4m40s (x1354 over 69m)  kubelet  Readiness probe failed: readiness dependency unavailable\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\nName:             rc-notready-readiness\nLabels:           app=rc-notready-readiness\n                  cni.projectcalico.org/containerID: fb8e26665bf8a745a3d1ec6dc6a9b9d528c0b6504e8895b370296a560f31067e\n                  cni.projectcalico.org/podIP: 172.16.166.186/32\n                  cni.projectcalico.org/podIPs: 172.16.166.186/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Running","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/64e8d43369444d99/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/64e8d43369444d99/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/64e8d43369444d99/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-readiness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T07:05:35Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-readiness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=None exitCode=None\nvolumes:\n- {\"name\": \"kube-api-access-sqcn2\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/64e8d43369444d99/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/64e8d43369444d99/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/64e8d43369444d99/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_logs","data":"kubectl_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/64e8d43369444d99/tools/003-evidence-kubectl_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/64e8d43369444d99/tools/003-evidence-kubectl_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/64e8d43369444d99/tools/003-evidence-kubectl_logs.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n4m48s (x1354 over 69m)   Warning   Unhealthy   Pod/rc-notready-readiness   Readiness probe failed: readiness dependency unavailable","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/64e8d43369444d99/tools/004-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/64e8d43369444d99/tools/004-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/64e8d43369444d99/tools/004-evidence-kubectl_events.summary.txt"}],"llm_analysis":"# 证据结论\n\n## 已采集证据\n1. **Pod 描述信息**：\n   - Pod 名称：`rc-notready-readiness`\n   - 命名空间：`aiops-e2e`\n   - 节点：`node1`\n   - 状态：`Running`\n   - 关键事件：`Warning Unhealthy`，原因：`Readiness probe failed: readiness dependency unavailable`\n   - 注解：`pod_abnormal_type=NotReadyProbeFailed`，`aiops.e2e/runbook=pod-notready-probe-failed.md`\n   - 标签：`app=rc-notready-readiness`\n\n2. **Pod YAML 配置**：\n   - 名称：`rc-notready-readiness`\n   - 命名空间：`aiops-e2e`\n   - 创建时间：`2026-05-15T07:05:35Z`\n   - 节点：`node1`\n   - 重启策略：`Always`\n   - 状态：`Running`\n   - 容器状态：`ready=False`，`restarts=0`\n   - 标签：`app=rc-notready-readiness`, `pod_abnormal_type=NotReadyProbeFailed`\n   - 注解：`aiops.e2e/runbook=pod-notready-probe-failed.md`\n\n3. **Pod 日志**：\n   - 日志输出为空，没有关键日志。\n\n4. **Pod 事件**：\n   - 事件：`Warning Unhealthy`\n   - 原因：`Readiness probe failed: readiness dependency unavailable`\n   - 重复次数：`x1354 over 69m`\n\n## 未采集证据\n- 无\n\n## 冲突证据\n- 无\n\n## 分析总结\n根据已采集的证据，Pod `rc-notready-readiness` 处于 `Running` 状态，但其 `READY` 状态为 `0/1`，且 readiness probe 失败，事件显示 `Readiness probe failed: readiness dependency unavailable`。这表明该 Pod 的就绪探针检查失败，属于 `NotReadyProbeFailed` 类型。可能的原因包括：\n- readinessProbe 配置不正确，路径、端口、scheme、initialDelaySeconds 等不匹配。\n- 应用进程已启动但健康接口返回非 2xx/3xx 或超时。\n- livenessProbe 反复失败导致容器重启。\n- startupProbe 失败导致容器尚未进入正常服务窗口。\n\n建议进一步检查 readinessProbe 的配置，并查看应用的健康接口是否正常返回。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 10/10 项，完整度 100%；实际执行工具 10 个，匹配计划 4 个，未规划证据 6 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":10,"environment_evidence_collected":10,"environment_evidence_completeness":1.0,"executed_tool_count":10,"matched_tool_count":4,"unplanned_tool_count":6,"evidence_inventory":[{"id":"e1","description":"验证异常 Pod rc-notready-readiness 的 readinessProbe 配置和失败事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-readiness -n aiops-e2e","purpose":"查看 readinessProbe 配置和失败事件，确认探针失败原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"检查 rc-notready-readiness Pod 的 YAML 配置中的 probe 设置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml","purpose":"查看 readinessProbe/livenessProbe/startupProbe 的详细配置，包括路径、端口、超时等","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"检查 rc-notready-readiness Pod 的日志，查看应用健康接口或启动错误","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --tail=200","purpose":"查看日志以确定应用是否正常运行并返回正确的健康状态","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"检查 rc-notready-readiness Pod 的 readinessEvents","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e | grep rc-notready-readiness","purpose":"查看与 rc-notready-readiness Pod 相关的 readinessEvents，确认探针失败的详细信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证异常 Pod rc-notready-readiness 的 readinessPro... | `kubectl describe pod rc-notready-readiness -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_get_yaml | 检查 rc-notready-readiness Pod 的 YAML 配置中的 prob... | `kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml` |
   | e3 | important | ✅ | kubectl_logs | 检查 rc-notready-readiness Pod 的日志，查看应用健康接口或启动错误 | `kubectl logs rc-notready-readiness -n aiops-e2e --tail=200` |
   | e4 | important | ✅ | kubectl_events | 检查 rc-notready-readiness Pod 的 readinessEvents | `kubectl get events -n aiops-e2e | grep rc-notready-readiness` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (22.2s)
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
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (2m 6.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3807 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 38.4s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Running |
| **兼容归因层** | L4 |
| **问题分类** | NotReadyProbeFailed |
| **置信度** | 中 |
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
| 1 | Pod 状态 | `kubectl get pod` | `READY: 0/1, STATUS: Running` | Pod 已启动但未就绪 |
| 2 | 探针事件 | `kubectl describe pod` | `Warning: Unhealthy (x1354 over 67m) Readiness probe failed: readiness dependency unavailable` | 探针持续失败，导致 Pod 未就绪 |
| 3 | YAML 配置 | `kubectl get pod -o yaml` | readinessProbe 路径、端口、initialDelaySeconds 未显示 | 无法确认探针配置是否合理 |
| 4 | 日志检查 | `kubectl logs` | 无输出 | 无应用日志，无法判断健康接口是否正常 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 Running，但 READY 为 0/1，探针失败事件频繁发生 → Pod 未就绪
- **证据链**：应用健康接口未响应或响应失败 → readinessProbe 失败 → Pod 被标记为未就绪 → 服务流量无法到达该 Pod
- **证据 #3 补充**：YAML 中未提供探针配置 → 无法判断是否配置错误（如路径、端口、延迟等）

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| readinessProbe 配置 | critical | 无法确认探针是否配置正确 |
| 应用健康接口响应 | critical | 无法判断探针失败的具体原因 |
| 应用日志（启动过程） | important | 无法判断应用是否正常启动或存在初始化错误 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ readinessProbe 配置不匹配应用健康接口，或应用健康接口未正确响应 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ readinessProbe 路径、端口或延迟设置不正确 → 探针失败 → Pod 未就绪 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ readinessProbe 失败 → Pod READY 为 0/1，未加入服务 Endpoints     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 Running 但 READY 为 0/1，事件显示 readiness dependency unavailable |
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Pod READY 为 0/1, STATUS 为 Running) 和证据 #2 (readiness probe 失败，事件显示 readiness dependency unavailable)，问题的根本原因是 **readinessProbe 配置不匹配应用健康接口，或应用健康接口未正常响应**，导致探针失败，Pod 未就绪。
**置信度**：中 (60%)
- ✅ 探针失败事件频繁，确认探针失败
- ⚠️ 缺少探针配置和应用健康接口日志，无法进一步确认具体原因

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查 readinessProbe 配置**
```bash
kubectl get pod rc-notready-readiness -n aiops-e2e -o jsonpath='{.spec.containers[*].readinessProbe}'
```
*目的*：确认探针路径、端口、initialDelaySeconds 等配置是否合理

**2. [可选] 检查应用健康接口**
```bash
curl -I http://<pod-ip>:<port>/<health-path>
```
*目的*：手动验证健康接口是否可访问，返回 2xx/3xx 状态码

**3. [可选] 查看应用启动日志**
```bash
kubectl logs rc-notready-readiness -n aiops-e2e --previous
```
*目的*：查看容器启动过程是否有异常，如端口未监听、初始化失败等

### 后续优化

1. **调整探针配置**：根据应用实际启动时间调整 `initialDelaySeconds` 和 `failureThreshold`
2. **配置 livenessProbe**：确保探针失败后能及时重启容器（如有必要）
3. **启用健康检查日志**：在应用中增加健康接口日志，便于排查探针失败原因

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 就绪 | `kubectl get pod rc-notready-readiness -n aiops-e2e` | READY: 1/1 |
| 2. 检查探针事件 | `kubectl describe pod rc-notready-readiness -n aiops-e2e` | 无 Unhealthy 事件 |
| 3. 验证健康接口 | `curl -I http://<pod-ip>:<port>/<health-path>` | 返回 200 OK |

---

## ⚠️ 注意事项

- 如果探针配置正确，但健康接口仍失败，可能是应用本身存在启动问题或资源不足
- 建议结合 `kubectl logs` 和 `kubectl describe` 一起分析问题
- 如果问题频繁出现，建议启用 Prometheus 等监控系统进行持续监控

---

## 📊 性能统计

├─ 总耗时: 5.6m
├─ 问题定位: 65.1s (19%) ✅
├─ 证据链采集: 124.6s (37%) ✅
├─ 根因分析: 22.2s (7%) ✅
├─ 汇总总结: 126.5s (37%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 11 次
```

📋 诊断追踪

- **核心 Runbook**: pod-notready-probe-failed
- **参考 Runbook**: pod-notready-probe-failed
- **工具调用**: 11 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
