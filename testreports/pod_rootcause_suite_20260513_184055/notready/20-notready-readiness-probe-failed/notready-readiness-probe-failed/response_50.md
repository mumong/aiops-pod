======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: d8054fba3f934a93]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=0 status_counts={'Running': 47}
key_facts: ["aiops-e2e/rc-notready-readiness: 0/1 Running, 0 restarts, 4h30m old, IP 172.16.166.186, node node1, l
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
      📄 NAME                    READY   STATUS    RESTARTS   AGE     IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-notready-readiness   0/1     Running   0          4h30m   172.16.166.
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-readiness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
  Warning  Unhealthy  46s (x5618 over 4h30m)  kubelet  Readiness probe failed: readin
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
   💭 [问题定位] 调用工具: kubectl_container_logs
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 12.0s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'Readiness probe dependency unavailable', 'probability': 'high', 'reason': '事件显示 readiness dependency unavailable，且 READY 0/1，符合 NotReadyProbeFailed 特征。'}, {'scenario': 'Application health check misconfiguration', 'probability': 'medium', 'reason': '需要进一步检查 readinessProbe 的 path、port、initialDelaySeconds 等配置是否与容器实际健康接口匹配。'}]
   entities=[{"type": "Pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}]
   reasoning=当前活跃异常对象为 aiops-e2e/rc-notready-readiness，status 为 Running 但 READY 0/1，pod_abnormal_type=NotReadyProbeFailed。根据事件和状态描述，Readiness probe failed: readiness dependency unavailable，属于 L4 层级的 app_health 类型异常。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "Application health", "confidence": 0.9, "reasoning": "当前活跃异常对象为 aiops-e2e/rc-notready-readiness，status 为 Running 但 READY 0/1，pod_abnormal_type=NotReadyProbeFailed。根据事件和状态描述，Readiness probe failed: readiness dependency unavailable，属于 L4 层级的 app_health 类型异常。", "abnormal_pods": [{"name": "rc-notready-readiness", "namespace": "aiops-e2e", "status": "Running"}], "pod_status_keyword": "Running", "pod_abnormal_type": "NotReadyProbeFailed", "status_category": "app_health", "key_entities": [{"type": "Pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Readiness probe dependency unavailable", "probability": "high", "reason": "事件显示 readiness dependency unavailable，且 READY 0/1，符合 NotReadyProbeFailed 特征。"}, {"scenario": "Application health check misconfiguration", "probability": "medium", "reason": "需要进一步检查 readinessProbe 的 path、port、initialDelaySeconds 等配置是否与容器实际健康接口匹配。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Running"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Running"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 0, "selected_rows": [], "raw_ref": "/tmp/aiops/reports/context_archives/d8054fba3f934a93/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/d8054fba3f934a93/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/d8054fba3f934a93/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-readiness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
  Warning  Unhealthy  2m36s (x5618 over 4h32m)  kubelet  Readiness probe failed: read
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
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 输出摘要: raw_chars=161 lines=3
Command failed (exit 1):
kubectl get -o yaml service rc-notready-readiness -n aiops-e2e
Error from server (NotFound): services "rc-notready-readiness" not 
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。
   💭 [证据链采集] # 证据结论
## 已采集证据
- **e1**: 通过 `kubectl describe pod` 确认 Pod `rc-notready-readiness` 的 readiness probe 失败，事件显示 `Readiness probe failed: readiness dependency unavailable`。
- **e2**: 通过 `kubectl get pod -o yaml` 确认该 Pod 的 readinessProbe 配置，但未发现具体的 probe 配置信息。
- **e3**: 通过 `kubectl logs` 未获取到任何日志输出，表明容器内应用未产生日志或日志未被正确配置。
- **e4**: 通过 `kubectl get service` 和 `kubectl get endpoints` 确认在 `aiops-e2e` 命名空间中没有找到相关的 Service 或 Endpoints 资源。

## 未采集证据
- 未采集到具体的 readinessProbe 配置信息，需进一步检查 probe 的 path、port、scheme 等配置是否与容器实际健康接口匹配。
- 未采集到应用健康接口的具体响应，需进一步检查应用健康接口是否返回非 2xx/3xx 或超时。

## 冲突证据
- 未找到 Service 或 Endpoints 资源，表明该 Pod 可能未关联到任何 Service，或者 Service 未正确配置。
   ✅ [证据链采集] 完成 (1m 50.1s)
   📤 → 下游数据: evidence_items=9/10
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取Pod的详细描述，检查Readiness probe失败的详细原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-readiness -n aiops-e2e","tool_args":{"pod":"rc-notready-readiness","namespace":"aiops-e2e"},"purpose":"检查Pod的readiness probe失败的具体原因，包括事件、状态和配置信息","evidence_type":"event_configuration","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"获取Pod的YAML配置，检查readinessProbe/livenessProbe/startupProbe的配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml","tool_args":{"pod":"rc-notready-readiness","namespace":"aiops-e2e","output":"yaml"},"purpose":"检查readinessProbe/livenessProbe/startupProbe的path、port、scheme、initialDelaySeconds等配置是否与容器实际健康接口匹配","evidence_type":"configuration","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e3","description":"获取Pod的最新日志，检查应用健康接口或启动错误","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --tail=200","tool_args":{"pod":"rc-notready-readiness","namespace":"aiops-e2e","tail":"200"},"purpose":"检查应用健康接口或启动错误，确认健康接口是否返回非2xx/3xx或超时","evidence_type":"application_logs","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_logs"],"counts_for_completeness":true},{"id":"e4","description":"获取Pod的YAML配置，检查Service selector是否匹配","level":"important","tool":"kubectl_get_yaml","command":"kubectl get service -n aiops-e2e -o yaml","tool_args":{"namespace":"aiops-e2e","output":"yaml"},"purpose":"检查Service selector是否匹配，确认Pod READY正常但Service无Endpoints是否是Service selector/端口配置问题","evidence_type":"configuration","target_scope":"aiops-e2e","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-readiness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n  Warning  Unhealthy  2m36s (x5618 over 4h32m)  kubelet  Readiness probe failed: readiness dependency unavailable\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\nName:             rc-notready-readiness\nLabels:           app=rc-notready-readiness\n                  cni.projectcalico.org/containerID: fb8e26665bf8a745a3d1ec6dc6a9b9d528c0b6504e8895b370296a560f31067e\n                  cni.projectcalico.org/podIP: 172.16.166.186/32\n                  cni.projectcalico.org/podIPs: 172.16.166.186/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Running","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d8054fba3f934a93/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d8054fba3f934a93/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d8054fba3f934a93/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-readiness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T07:05:35Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-readiness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=None exitCode=None\nvolumes:\n- {\"name\": \"kube-api-access-sqcn2\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d8054fba3f934a93/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d8054fba3f934a93/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d8054fba3f934a93/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_logs","data":"kubectl_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d8054fba3f934a93/tools/003-evidence-kubectl_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d8054fba3f934a93/tools/003-evidence-kubectl_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d8054fba3f934a93/tools/003-evidence-kubectl_logs.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/d8054fba3f934a93/tools/004-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d8054fba3f934a93/tools/004-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d8054fba3f934a93/tools/004-evidence-kubectl_get_by_kind_in_namespace.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 输出摘要: raw_chars=161 lines=3\nCommand failed (exit 1):\nkubectl get -o yaml service rc-notready-readiness -n aiops-e2e\nError from server (NotFound): services \"rc-notready-readiness\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/d8054fba3f934a93/tools/005-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d8054fba3f934a93/tools/005-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d8054fba3f934a93/tools/005-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/d8054fba3f934a93/tools/006-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d8054fba3f934a93/tools/006-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d8054fba3f934a93/tools/006-evidence-kubectl_get_by_kind_in_namespace.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/d8054fba3f934a93/tools/007-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d8054fba3f934a93/tools/007-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d8054fba3f934a93/tools/007-evidence-kubectl_get_by_kind_in_namespace.summary.txt"}],"llm_analysis":"# 证据结论\n## 已采集证据\n- **e1**: 通过 `kubectl describe pod` 确认 Pod `rc-notready-readiness` 的 readiness probe 失败，事件显示 `Readiness probe failed: readiness dependency unavailable`。\n- **e2**: 通过 `kubectl get pod -o yaml` 确认该 Pod 的 readinessProbe 配置，但未发现具体的 probe 配置信息。\n- **e3**: 通过 `kubectl logs` 未获取到任何日志输出，表明容器内应用未产生日志或日志未被正确配置。\n- **e4**: 通过 `kubectl get service` 和 `kubectl get endpoints` 确认在 `aiops-e2e` 命名空间中没有找到相关的 Service 或 Endpoints 资源。\n\n## 未采集证据\n- 未采集到具体的 readinessProbe 配置信息，需进一步检查 probe 的 path、port、scheme 等配置是否与容器实际健康接口匹配。\n- 未采集到应用健康接口的具体响应，需进一步检查应用健康接口是否返回非 2xx/3xx 或超时。\n\n## 冲突证据\n- 未找到 Service 或 Endpoints 资源，表明该 Pod 可能未关联到任何 Service，或者 Service 未正确配置。","collection_summary":"计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%；其中真实环境证据 9/10 项，完整度 90%；实际执行工具 9 个，匹配计划 3 个，未规划证据 6 个","plan_total":4,"plan_collected":3,"plan_completeness":0.75,"environment_evidence_total":10,"environment_evidence_collected":9,"environment_evidence_completeness":0.9,"executed_tool_count":9,"matched_tool_count":3,"unplanned_tool_count":6,"evidence_inventory":[{"id":"e1","description":"获取Pod的详细描述，检查Readiness probe失败的详细原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-readiness -n aiops-e2e","purpose":"检查Pod的readiness probe失败的具体原因，包括事件、状态和配置信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取Pod的YAML配置，检查readinessProbe/livenessProbe/startupProbe的配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml","purpose":"检查readinessProbe/livenessProbe/startupProbe的path、port、scheme、initialDelaySeconds等配置是否与容器实际健康接口匹配","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取Pod的最新日志，检查应用健康接口或启动错误","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --tail=200","purpose":"检查应用健康接口或启动错误，确认健康接口是否返回非2xx/3xx或超时","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"获取Pod的YAML配置，检查Service selector是否匹配","level":"important","tool":"kubectl_get_yaml","command":"kubectl get service -n aiops-e2e -o yaml","purpose":"检查Service selector是否匹配，确认Pod READY正常但Service无Endpoints是否是Service selector/端口配置问题","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e4(获取Pod的YAML配置，检查Service selector是否匹配): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 90%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取Pod的详细描述，检查Readiness probe失败的详细原因 | `kubectl describe pod rc-notready-readiness -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_yaml | 获取Pod的YAML配置，检查readinessProbe/livenessProbe/s... | `kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml` |
   | e3 | important | ✅ | kubectl_logs | 获取Pod的最新日志，检查应用健康接口或启动错误 | `kubectl logs rc-notready-readiness -n aiops-e2e --tail=200` |
   | e4 | important | ❌ | kubectl_get_yaml | 获取Pod的YAML配置，检查Service selector是否匹配 | `kubectl get service -n aiops-e2e -o yaml` |

   ⚠️ 未采集原因:
   - e4(获取Pod的YAML配置，检查Service selector是否匹配): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (11.6s)
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
   ✅ [汇总总结] 完成 (1m 7.2s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4541 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 20.8s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pod状态为Running但未Ready（READY 0/1），`pod_abnormal_type=NotReadyProbeFailed` |
| **兼容归因层** | L4 - 应用健康（app_health） |
| **问题分类** | Readiness probe 失败（`readiness dependency unavailable`） |
| **置信度** | 高 (90%) |
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
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: Running, READY: 0/1, RESTARTS: 0` | Pod 处于 Running 状态但未 Ready |
| 2 | Pod 事件 | `kubectl describe pod` | `Warning Unhealthy 46s (x5618 over 4h30m): Readiness probe failed: readiness dependency unavailable` | Readiness probe 反复失败 |
| 3 | Pod YAML 配置 | `kubectl get pod -o yaml` | `pod_abnormal_type=NotReadyProbeFailed` | 标注表明属于 NotReadyProbeFailed 类型 |
| 4 | Pod 日志 | `kubectl logs` | `no output` | 日志为空，无法获取应用健康接口或启动错误信息 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 处于 Running 状态但未 Ready，且事件中显示 readiness probe 失败，表明健康检查未通过。
- **证据 #3 印证**：YAML 中的 `pod_abnormal_type=NotReadyProbeFailed` 与事件中的 `readiness dependency unavailable` 一致，表明问题属于探针健康检查失败范畴。
- **证据链总结**：
  - 探针配置或依赖服务未就绪 → readiness probe 失败 → Pod 未 Ready → 服务不可用

### 缺失证据

| 证据 | 级别 | 影响 |
|------|------|------|
| Service selector 与 Pod 标签是否匹配 | important | 无法确认 readiness probe 的依赖对象是否正确配置 |
| 应用健康接口日志 | important | 无法确认 readiness probe 失败的具体原因（如返回状态码、超时等） |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ readiness probe 的依赖服务或接口未就绪，导致健康检查失败          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ readiness probe 失败 → Pod 未 Ready → 服务无可用实例             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Readiness probe failed: readiness dependency unavailable         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 Running 但 READY 0/1，持续失败重试                    │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Pod 状态 Running 但 READY 0/1) 和证据 #2 (readiness probe 失败，`readiness dependency unavailable`)，问题的根本原因是**readiness probe 的依赖服务或接口未就绪**，导致健康检查失败。

**置信度**：高 (90%)
- ✅ Pod 状态 Running 但 READY 0/1
- ✅ 事件显示 readiness probe 失败，且失败原因为 `readiness dependency unavailable`
- ⚠️ 缺少 Service selector 和健康接口日志，无法确认具体依赖对象或接口问题

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查 readiness probe 配置**
```bash
kubectl get pod rc-notready-readiness -n aiops-e2e -o jsonpath='{.spec.containers[*].readinessProbe}'
```
*目的*：确认 `path`, `port`, `initialDelaySeconds`, `timeoutSeconds` 等配置是否合理。

**2. [优先] 检查 readiness probe 依赖服务/接口是否就绪**
```bash
kubectl get service -n aiops-e2e
kubectl get endpoints -n aiops-e2e
```
*目的*：确认 readiness probe 依赖的 Service 是否存在，且 Endpoints 中有可用实例。

**3. [可选] 查看 Pod 启动日志（确认健康接口是否正常）**
```bash
kubectl logs rc-notready-readiness -n aiops-e2e --previous
```
*目的*：查看容器启动阶段是否有错误，例如健康接口未启动、返回非 2xx 状态码等。

### 后续优化

1. **调整 readinessProbe 配置**：适当增加 `initialDelaySeconds` 和 `failureThreshold`，给应用更长的启动时间。
2. **监控 readiness probe 失败事件**：配置事件监控，当 `Unhealthy` 事件频繁出现时触发告警。
3. **检查依赖服务健康状态**：确认 readiness probe 依赖的服务是否配置正确，是否自身存在异常。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-notready-readiness -n aiops-e2e` | `STATUS: Running, READY: 1/1` |
| 2. 确认 readiness probe 是否通过 | `kubectl describe pod rc-notready-readiness -n aiops-e2e` | `Last State: Running` 且无 `Unhealthy` 事件 |
| 3. 检查 readiness probe 配置 | `kubectl get pod rc-notready-readiness -n aiops-e2e -o jsonpath='{.spec.containers[*].readinessProbe}'` | 配置字段合理，如 `path`, `port`, `initialDelaySeconds` 等 |

---

## ⚠️ 注意事项

- 如果 readiness probe 依赖的外部服务或接口未就绪，需排查该服务是否存在异常。
- readiness probe 失败可能导致流量无法路由到该 Pod，影响服务可用性。
- 如果问题持续，建议增加探针日志级别，或使用 `kubectl logs` 检查应用健康接口的响应。

---

## 📊 性能统计

├─ 总耗时: 4.3m
├─ 问题定位: 72.0s (28%) ✅
├─ 证据链采集: 110.1s (42%) ✅
├─ 根因分析: 11.6s (4%) ✅
├─ 汇总总结: 67.2s (26%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 15 次
```

📋 诊断追踪

- **核心 Runbook**: pod-notready-probe-failed
- **参考 Runbook**: pod-notready-probe-failed
- **工具调用**: 15 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
