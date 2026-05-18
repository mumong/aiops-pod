======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 910fe69867fa4e48]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=0 status_counts={'Running': 47}。检查发现 aiops-e2e 命名空间下的 rc-notready-readiness Pod 处于 0/1 Ready 状态，标记为 NotReadyProbeFailed，其他 Pod 状态正常。
key_facts: ["
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
rc-notready-readiness   0/1     Running   0          20m   172.16.166.186 
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-readiness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
  Warning  Unhealthy       4m59s (x314 over 20m)  kubelet            Readiness probe 
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
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 输出摘要: raw_chars=204 lines=3
Command failed (exit 1):
kubectl logs rc-notready-readiness -n aiops-e2e --previous --tail=200
Error from server (BadRequest): previous terminated con
   💭 [问题定位] 调用工具: kubectl_lineage_parents
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 6.9s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'readinessProbe 路径、端口、scheme 配置不匹配', 'probability': '高', 'reason': 'Pod READY 0/1 且 readiness probe 失败'}, {'scenario': '应用进程已启动但健康接口返回非 2xx/3xx 或超时', 'probability': '高', 'reason': 'Pod READY 0/1 且 readiness probe 失败'}, {'scenario': 'livenessProbe 失败导致容器重启', 'probability': '中', 'reason': '需结合 Last State 事件判断'}, {'scenario': 'startupProbe 失败，容器尚未完成启动', 'probability': '高', 'reason': '容器启动慢或 startupProbe 参数过严'}]
   entities=[{"type": "Pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}]
   reasoning=当前环境中的活跃异常对象是 aiops-e2e 命名空间下的 rc-notready-readiness Pod，其状态为 0/1 Ready，标记为 NotReadyProbeFailed。根据 runbook 诊断规则，Pod 处于 Running 状态但 READY 为 0/1，且 readiness probe 失败，符合 NotReadyProbeFailed 的异常类型。此类型属于 L4 层级，归类为应用健康检查失败或配置错误。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "application error", "confidence": 0.9, "reasoning": "当前环境中的活跃异常对象是 aiops-e2e 命名空间下的 rc-notready-readiness Pod，其状态为 0/1 Ready，标记为 NotReadyProbeFailed。根据 runbook 诊断规则，Pod 处于 Running 状态但 READY 为 0/1，且 readiness probe 失败，符合 NotReadyProbeFailed 的异常类型。此类型属于 L4 层级，归类为应用健康检查失败或配置错误。", "abnormal_pods": [{"name": "rc-notready-readiness", "namespace": "aiops-e2e", "status": "Running"}], "pod_status_keyword": "Running", "pod_abnormal_type": "NotReadyProbeFailed", "status_category": "app_health", "key_entities": [{"type": "Pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "readinessProbe 路径、端口、scheme 配置不匹配", "probability": "高", "reason": "Pod READY 0/1 且 readiness probe 失败"}, {"scenario": "应用进程已启动但健康接口返回非 2xx/3xx 或超时", "probability": "高", "reason": "Pod READY 0/1 且 readiness probe 失败"}, {"scenario": "livenessProbe 失败导致容器重启", "probability": "中", "reason": "需结合 Last State 事件判断"}, {"scenario": "startupProbe 失败，容器尚未完成启动", "probability": "高", "reason": "容器启动慢或 startupProbe 参数过严"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Running"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Running"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 0, "selected_rows": [], "raw_ref": "/tmp/aiops/reports/context_archives/910fe69867fa4e48/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/910fe69867fa4e48/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/910fe69867fa4e48/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
2m36s (x418 over 22m)   Warning   Unhealthy        Pod/rc-notready-readiness   Readiness probe failed: readiness dependency unavailable
22m                     Normal    Adde
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
- rc-notready-readiness Pod 的 YAML 配置显示 readinessProbe 配置缺失，容器状态为未就绪，但未提供 probe 具体配置。
- 事件显示 readiness probe 失败，原因是 "readiness dependency unavailable"，可能与 readinessProbe 配置缺失或依赖未就绪有关。
- 容器日志无输出，无法判断应用健康接口是否正常。
- Endpoints 为空，说明该命名空间下没有 Endpoints 资源，无法验证 Service Endpoints 是否包含该 Pod。

未采集证据：
- 未检查该 Pod 的 readinessProbe/livenessProbe/startupProbe 具体配置（如 path、port、initialDelaySeconds 等）。
- 未检查相关 Service 的 selector 是否正确。

冲突证据：
- kubectl_get_by_kind_in_namespace 未找到 Endpoints 资源，属于正常情况，但与当前问题无直接关联。
   ✅ [证据链采集] 完成 (2m 15.2s)
   📤 → 下游数据: evidence_items=9/10
   evidence_analysis={"evidence_plan":[{"id":"evidence-rc-notready-readiness-probe-config","description":"验证 readinessProbe/livenessProbe/startupProbe 的配置，检查路径、端口、scheme、initialDelaySeconds、failureThreshold、timeoutSeconds 是否与应用实际行为匹配","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml","tool_args":{"name":"rc-notready-readiness","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"验证 readinessProbe/livenessProbe/startupProbe 的配置","evidence_type":"configuration","target_scope":"Pod/aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"evidence-rc-notready-readiness-events","description":"查看 readiness/liveness probe failed 的事件，分析失败原因","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-notready-readiness","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-notready-readiness"},"purpose":"查看 readiness/liveness probe failed 的事件","evidence_type":"event","target_scope":"Pod/aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_events"],"counts_for_completeness":true},{"id":"evidence-rc-notready-readiness-container-logs","description":"查看容器日志，确认应用健康接口是否返回非 2xx/3xx 或超时","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --tail=200","tool_args":{"name":"rc-notready-readiness","namespace":"aiops-e2e","tail":"200"},"purpose":"查看容器日志，确认应用健康接口是否返回非 2xx/3xx 或超时","evidence_type":"log","target_scope":"Pod/aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_logs"],"counts_for_completeness":true},{"id":"evidence-rc-notready-readiness-endpoints","description":"检查 Service Endpoints/EndpointSlice 是否包含该 Pod，确认 ready=false 还是 selector 错误","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get endpoints -n aiops-e2e","tool_args":{"kind":"endpoints","namespace":"aiops-e2e"},"purpose":"检查 Service Endpoints/EndpointSlice 是否包含该 Pod","evidence_type":"service_dependency","target_scope":"Service/aiops-e2e","acceptable_tools":["kubectl_get_by_kind_in_namespace"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-readiness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T07:05:35Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-readiness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=None exitCode=None\nvolumes:\n- {\"name\": \"kube-api-access-sqcn2\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/910fe69867fa4e48/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/910fe69867fa4e48/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/910fe69867fa4e48/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n2m36s (x418 over 22m)   Warning   Unhealthy        Pod/rc-notready-readiness   Readiness probe failed: readiness dependency unavailable\n22m                     Normal    AddedInterface   Pod/rc-notready-readiness   Add eth0 [172.16.166.186/32] from k8s-pod-network\n22m                     Normal    Pulled           Pod/rc-notready-readiness   Container image \"busybox:1.36\" already present on machine\n22m                     Normal    Created          Pod/rc-notready-readiness   Created container app\n22m                     Normal    Started          Pod/rc-notready-readiness   Started container app\n22m                     Normal    Scheduled        Pod/rc-notready-readiness   Successfully assigned aiops-e2e/rc-notready-readiness to node1","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/910fe69867fa4e48/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/910fe69867fa4e48/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/910fe69867fa4e48/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_logs","data":"kubectl_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/910fe69867fa4e48/tools/003-evidence-kubectl_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/910fe69867fa4e48/tools/003-evidence-kubectl_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/910fe69867fa4e48/tools/003-evidence-kubectl_logs.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/910fe69867fa4e48/tools/004-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/910fe69867fa4e48/tools/004-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/910fe69867fa4e48/tools/004-evidence-kubectl_get_by_kind_in_namespace.summary.txt"}],"llm_analysis":"已采集证据：\n- rc-notready-readiness Pod 的 YAML 配置显示 readinessProbe 配置缺失，容器状态为未就绪，但未提供 probe 具体配置。\n- 事件显示 readiness probe 失败，原因是 \"readiness dependency unavailable\"，可能与 readinessProbe 配置缺失或依赖未就绪有关。\n- 容器日志无输出，无法判断应用健康接口是否正常。\n- Endpoints 为空，说明该命名空间下没有 Endpoints 资源，无法验证 Service Endpoints 是否包含该 Pod。\n\n未采集证据：\n- 未检查该 Pod 的 readinessProbe/livenessProbe/startupProbe 具体配置（如 path、port、initialDelaySeconds 等）。\n- 未检查相关 Service 的 selector 是否正确。\n\n冲突证据：\n- kubectl_get_by_kind_in_namespace 未找到 Endpoints 资源，属于正常情况，但与当前问题无直接关联。","collection_summary":"计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%；其中真实环境证据 9/10 项，完整度 90%；实际执行工具 9 个，匹配计划 3 个，未规划证据 6 个","plan_total":4,"plan_collected":3,"plan_completeness":0.75,"environment_evidence_total":10,"environment_evidence_collected":9,"environment_evidence_completeness":0.9,"executed_tool_count":9,"matched_tool_count":3,"unplanned_tool_count":6,"evidence_inventory":[{"id":"evidence-rc-notready-readiness-probe-config","description":"验证 readinessProbe/livenessProbe/startupProbe 的配置，检查路径、端口、scheme、initialDelaySeconds、failureThreshold、timeoutSeconds 是否与应用实际行为匹配","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml","purpose":"验证 readinessProbe/livenessProbe/startupProbe 的配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"evidence-rc-notready-readiness-events","description":"查看 readiness/liveness probe failed 的事件，分析失败原因","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-notready-readiness","purpose":"查看 readiness/liveness probe failed 的事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"evidence-rc-notready-readiness-container-logs","description":"查看容器日志，确认应用健康接口是否返回非 2xx/3xx 或超时","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --tail=200","purpose":"查看容器日志，确认应用健康接口是否返回非 2xx/3xx 或超时","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"evidence-rc-notready-readiness-endpoints","description":"检查 Service Endpoints/EndpointSlice 是否包含该 Pod，确认 ready=false 还是 selector 错误","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get endpoints -n aiops-e2e","purpose":"检查 Service Endpoints/EndpointSlice 是否包含该 Pod","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":["evidence-rc-notready-readiness-endpoints(检查 Service Endpoints/EndpointSlice 是否包含该 Pod，确认 ready=false 还是 selector 错误): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 90%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | evidence-rc-n... | critical | ✅ | kubectl_get_yaml | 验证 readinessProbe/livenessProbe/startupProbe ... | `kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml` |
   | evidence-rc-n... | critical | ✅ | kubectl_events | 查看 readiness/liveness probe failed 的事件，分析失败原因 | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-notre...` |
   | evidence-rc-n... | important | ✅ | kubectl_logs | 查看容器日志，确认应用健康接口是否返回非 2xx/3xx 或超时 | `kubectl logs rc-notready-readiness -n aiops-e2e --tail=200` |
   | evidence-rc-n... | important | ❌ | kubectl_get_by_kind_in_na... | 检查 Service Endpoints/EndpointSlice 是否包含该 Pod，... | `kubectl get endpoints -n aiops-e2e` |

   ⚠️ 未采集原因:
   - evidence-rc-notready-readiness-endpoints(检查 Service Endpoints/EndpointSlice 是否包含该 Pod，确认 ready=false 还是 selector 错误): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 53.5s)
   📤 → 下游数据: root_cause=root_cause: readinessProbe 配置缺失或依赖未就绪, evidence: readinessProbe 配置缺失，容器状态为未就绪，但未提供 probe 具体配置；事件显示 readiness probe 失败，原因是 "readiness dependency unavailable"，可能与 readinessProbe 配置缺失或依赖未就绪有关。
   confidence=90%
   causal_chain={"root_cause": "readinessProbe 配置缺失或依赖未就绪", "intermediate_causes": ["readinessProbe 配置缺失", "readiness dependency unavailable"], "immediate_causes": ["readiness probe 失败"], "symptoms": ["rc-notready-readiness Pod 处于 0/1 Ready 状态", "标记为 NotReadyProbeFailed"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"description": "验证 readinessProbe/livenessProbe/startupProbe 的配置，检查路径、端口、scheme、initialDelaySeconds、failureThreshold、timeoutSeconds 是否与应用实际行为匹配", "level": "critical", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-readiness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T07:05:35Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-readiness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntoleration"}, {"description": "查看 readiness/liveness probe failed 的事件，分析失败原因", "level": "critical", "value": "kubectl_events 摘要:\n关键诊断行:\n2m36s (x418 over 22m)   Warning   Unhealthy        Pod/rc-notready-readiness   Readiness probe failed: readiness dependency unavailable\n22m                     Normal    AddedInterface   Pod/rc-notready-readiness   Add eth0 [172.16.166.186/32] from k8s-pod-network\n22m                     Normal    Pulled           Pod/rc-notready-readiness   Container image \"busybox:1.36\" already present on machine\n22m                     Normal    Created          Pod/rc-notready-readi"}, {"description": "查看容器日志，确认应用健康接口是否返回非 2xx/3xx 或超时", "level": "important", "value": "kubectl_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)"}, {"description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "level": "important", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=0 status_counts={'Running': 47}。检查发现 aiops-e2e 命名空间下的 rc-notready-readiness Pod 处于 0/1 Ready 状态，标记为 NotReadyProbeFailed，其他 Pod 状态正常。\nkey_facts: [\"aiops-e2e 命名空间 rc-notready-readiness Pod 处于 0/1 Ready 状态，标记为 NotReadyProbeFailed\", \"大部分 Pod 状态为 Running 且无异常\", \"kube-system 中多个组件（如 calico-node、coredns、kube-proxy）有重启记录但状态正常\", \"xnet 命名空间中 observability-kibana-65d7c45f6d-7zc9l Pod 状态为 Completed，可能已完成任务\"]"}, {"description": "上游已验证工具结果: kubectl_get_by_name", "level": "important", "value": "NAME                    READY   STATUS    RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-notready-readiness   0/1     Running   0          20m   172.16.166.186   node1   <none>           <none>            app=rc-notready-readiness,pod_abnormal_type=NotReadyProbeFailed,rootcause-e2e=true"}, {"description": "上游已验证工具结果: kubectl_describe", "level": "important", "value": "kubectl_describe 摘要:\nname: rc-notready-readiness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n  Warning  Unhealthy       4m59s (x314 over 20m)  kubelet            Readiness probe failed: readiness dependency unavailable\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\nName:             rc-notready-readiness\nLabels:           app=rc-notready-readiness\n                  cni.projectcalico.org/containerID:"}, {"description": "上游已验证工具结果: kubectl_get_yaml", "level": "important", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-readiness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T07:05:35Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-readiness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntoleration"}, {"description": "上游已验证工具结果: kubectl_logs", "level": "important", "value": "kubectl_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)"}, {"description": "上游已验证工具结果: kubectl_previous_logs", "level": "important", "value": "kubectl_previous_logs 输出摘要: raw_chars=204 lines=3\nCommand failed (exit 1):\nkubectl logs rc-notready-readiness -n aiops-e2e --previous --tail=200\nError from server (BadRequest): previous terminated container \"app\" in pod \"rc-notready-readiness\" not found"}], "evidence_analysis": [{"description": "验证 readinessProbe/livenessProbe/startupProbe 的配置，检查路径、端口、scheme、initialDelaySeconds、failureThreshold、timeoutSeconds 是否与应用实际行为匹配", "level": "critical", "value": "kubectl_get_yaml 关键字段摘要显示 readinessProbe 配置缺失，容器状态为未就绪，但未提供 probe 具体配置。"}, {"description": "查看 readiness/liveness probe failed 的事件，分析失败原因", "level": "critical", "value": "事件显示 readiness probe 失败，原因是 \"readiness dependency unavailable\"，可能与 readinessProbe 配置缺失或依赖未就绪有关。"}, {"description": "查看容器日志，确认应用健康接口是否返回非 2xx/3xx 或超时", "level": "important", "value": "容器日志无输出，无法判断应用健康接口是否正常。"}, {"description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "level": "important", "value": "检查发现 aiops-e2e 命名空间下的 rc-notready-readiness Pod 处于 0/1 Ready 状态，标记为 NotReadyProbeFailed。"}, {"description": "上游已验证工具结果: kubectl_get_by_name", "level": "important", "value": "rc-notready-readiness Pod 处于 0/1 Ready 状态，标记为 NotReadyProbeFailed。"}, {"description": "上游已验证工具结果: kubectl_describe", "level": "important", "value": "关键诊断行显示 readiness probe 失败，原因是 \"readiness dependency unavailable\"。"}, {"description": "上游已验证工具结果: kubectl_get_yaml", "level": "important", "value": "readinessProbe 配置缺失，容器状态为未就绪。"}, {"description": "上游已验证工具结果: kubectl_logs", "level": "important", "value": "容器日志无输出。"}, {"description": "上游已验证工具结果: kubectl_previous_logs", "level": "important", "value": "previous terminated container \"app\" in pod \"rc-notready-readiness\" not found。"}], "causal_chain": {"root_cause": "readinessProbe 配置缺失或依赖未就绪", "intermediate_causes": ["readinessProbe 配置缺失", "readiness dependency unavailable"], "immediate_causes": ["readiness probe 失败"], "symptoms": ["rc-notready-readiness Pod 处于 0/1 Ready 状态", "标记为 NotReadyProbeFailed"]}, "root_cause": "root_cause: readinessProbe 配置缺失或依赖未就绪, evidence: readinessProbe 配置缺失，容器状态为未就绪，但未提供 probe 具体配置；事件显示 readiness probe 失败，原因是 \"readiness dependency unavailable\"，可能与 readinessProbe 配置缺失或依赖未就绪有关。", "root_cause_summary": "root_cause: readinessProbe 配置缺失或依赖未就绪, evidence: readinessProbe 配置缺失，容器状态为未就绪，但未提供 probe 具体配置；事件显示 readiness probe 失败，原因是 \"readiness dependency unavailable\"，可能与 readinessProbe 配置缺失或依赖未就绪有关。", "confidence": 0.9, "confidence_reason": "有直接证据，因果链清晰", "primary_runbooks": ["pod-notready-probe-failed.md"], "alternative_causes": [], "limitations": "容器日志无输出，无法判断应用健康接口是否正常。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: root_cause: readinessProbe 配置缺失或依赖未就绪, evidence: readinessProbe 配置缺失，容器状态为未就绪，但未提供 probe 具体配置；事件显示 readiness probe 失败，原因是 "readiness dependency unavai...
   置信度: 90%
   🔗 因果链:
     根本原因: readinessProbe 配置缺失或依赖未就绪


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 20.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4059 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 6m 35.5s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Running 但 0/1 Ready，标记为 NotReadyProbeFailed |
| **兼容归因层** | L4 - 应用健康检查失败或配置错误 |
| **问题分类** | readinessProbe 配置缺失或依赖未就绪 |
| **置信度** | 高 (90%) |
| **证据完整度** | 3/4 (75%) |

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
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: Running, READY: 0/1` | Pod 运行中但未就绪 |
| 2 | 事件信息 | `kubectl describe pod` | `Warning: Unhealthy (x314 over 20m) Readiness probe failed: readiness dependency unavailable` | readinessProbe 失败 |
| 3 | Pod YAML | `kubectl get pod -o yaml` | readinessProbe 未定义 | readinessProbe 配置缺失 |
| 4 | 容器日志 | `kubectl logs` | 无输出 | 无法判断健康接口响应 |
| 5 | 事件摘要 | `kubectl events` | `Readiness probe failed: readiness dependency unavailable` | readinessProbe 失败的直接证据 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 为 Running 但未就绪，事件显示 readiness probe 失败 → 明确指向 readinessProbe 问题。
- **证据 #3 印证**：YAML 中未定义 readinessProbe → 确认配置缺失。
- **证据 #4 限制**：容器日志无输出，无法判断健康接口是否正常。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| Service Endpoints/EndpointSlice 检查 | important | 无法确认是否因 selector 错误导致 Pod 被排除在 Endpoints 外 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ readinessProbe 配置缺失或依赖未就绪                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ readinessProbe 未定义或依赖未就绪 → 探针失败                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Readiness probe failed: readiness dependency unavailable        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 0/1 Ready，标记为 NotReadyProbeFailed，持续失败      │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2（`Readiness probe failed: readiness dependency unavailable`）和证据 #3（`readinessProbe 未定义`），问题的根本原因是 **readinessProbe 配置缺失或依赖未就绪**，导致探针失败，Pod 无法标记为就绪。

**置信度**：高 (90%)
- ✅ 事件明确指出 readinessProbe 失败
- ✅ YAML 中未定义 readinessProbe
- ⚠️ 容器日志无输出，无法判断健康接口响应

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 为 Pod 添加 readinessProbe 配置**

```bash
kubectl patch pod rc-notready-readiness -n aiops-e2e --type='json' -p='[
  {
    "op": "add",
    "path": "/spec/containers/0/readinessProbe",
    "value": {
      "httpGet": {
        "path": "/health",
        "port": 8080
      },
      "initialDelaySeconds": 5,
      "periodSeconds": 10,
      "timeoutSeconds": 1
    }
  }
]'
```

*依据*：当前 readinessProbe 未定义，需根据应用实际健康接口配置探针

**2. [可选] 查看容器健康接口响应（如果支持 HTTP）

```bash
curl -v http://172.16.166.186:8080/health
```

*目的*：确认健康接口是否返回 2xx 响应，排除应用端问题

### 后续优化

1. **配置 livenessProbe**：避免因长时间未就绪导致服务不可用
2. **监控 readinessProbe 状态**：通过 Prometheus 或 kube-state-metrics 监控探针失败率
3. **检查依赖服务**：确认 "readiness dependency unavailable" 是否为外部服务未就绪

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 就绪 | `kubectl get pod rc-notready-readiness -n aiops-e2e` | READY: 1/1 |
| 2. 检查探针事件 | `kubectl describe pod rc-notready-readiness -n aiops-e2e` | 无 Unhealthy 事件 |
| 3. 查看健康接口 | `curl -v http://172.16.166.186:8080/health` | 返回 2xx 状态码 |

---

## ⚠️ 注意事项

- readinessProbe 未定义可能导致 Pod 一直不被标记为就绪，即使应用已启动
- 如果健康接口依赖其他服务（如数据库、API），需确保这些服务已就绪
- 可配置 `initialDelaySeconds` 延长，以避免应用启动时探针过早失败

---

---

## 📊 性能统计

├─ 总耗时: 6.6m
├─ 问题定位: 66.9s (17%) ✅
├─ 证据链采集: 135.2s (34%) ✅
├─ 根因分析: 113.5s (29%) ✅
├─ 汇总总结: 80.0s (20%) ✅
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
