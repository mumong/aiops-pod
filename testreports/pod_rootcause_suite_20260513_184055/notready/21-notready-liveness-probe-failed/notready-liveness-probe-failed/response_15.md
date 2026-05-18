======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 1bfeefaa08034060]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'CrashLoopBackOff': 1, 'Running': 46}
NAMESPACE     NAME                                                READY   STATUS           
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 Error: Runbook 'pod-notready-probe.md' is disabled by the current runtime profile
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 Error: Runbook 'pod-crashloop-backoff.md' is disabled by the current runtime profile
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod CrashLoopBackOffRuntime / 容器反复退出

> Pod异常类型: CrashLoopBackOffRuntime | 典型状态: CrashLoopBackOff | 兼容分类: container_runtime

## 状态识别
- Pod 状态: `CrashLoopBackOff`
- Last State: Terminated
-
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                   READY   STATUS             RESTARTS       AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-notready-liveness   0/1     CrashLoopBackOff   16 (58s ago)
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-liveness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Exit Code:    137
  Warning  Unhealthy       34m (x10 over 35m)   kubelet       
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "NotReadyProbeFailed",
  "confidence": "high",
  "reasoning": "Pod rc-notready-liveness 处于 CrashLoopBackOff 状态，Exit Code 为 137，且 Events 显示 Liveness probe failed。根据 runbook 判定规则，这表明 Pod 的 readiness/liveness 探针配置错误或应用健康接口存在问题，归因于 L4 层的 NotReadyProbeFailed 类型。",
  "abnormal_pods": [
    "rc-notready-liveness"
  ],
  "abnormal_groups": {
    "CrashLoopBackOff": [
      "rc-notready-liveness"
    ]
  },
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "NotReadyProbeFailed",
  "status_category": "CrashLoopBackOff",
  "key_entities": {
    "pod": "rc-notready-liveness",
    "namespace": "aiops-e2e",
    "node": "node1"
  },
  "possible_scenarios": [
    "Liveness probe 配置错误导致容器被反复重启",
    "应用健康接口返回 500 或超时，导致探针失败",
    "容器启动后短时间内退出，导致探针无法通过"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 29.6s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[]
   entities=[]
   reasoning=Pod rc-notready-liveness 处于 CrashLoopBackOff 状态，Exit Code 为 137，且 Events 显示 Liveness probe failed。根据 runbook 判定规则，这表明 Pod 的 readiness/liveness 探针配置错误或应用健康接口存在问题，归因于 L4 层的 NotReadyProbeFailed 类型。
   layer_analysis={"layer": "L4", "derived_layer": "", "layers": [], "layer_name": "", "confidence": 0.5, "reasoning": "Pod rc-notready-liveness 处于 CrashLoopBackOff 状态，Exit Code 为 137，且 Events 显示 Liveness probe failed。根据 runbook 判定规则，这表明 Pod 的 readiness/liveness 探针配置错误或应用健康接口存在问题，归因于 L4 层的 NotReadyProbeFailed 类型。", "abnormal_pods": [{"name": "rc-notready-liveness", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "NotReadyProbeFailed", "status_category": "app_health", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-notready-liveness                                0/1     CrashLoopBackOff   16 (47s ago)   35m    172.16.166.164   node1    <none>           <none>            app=rc-notready-liveness,pod_abnormal_type=NotReadyProbeFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/1bfeefaa08034060/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/1bfeefaa08034060/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/1bfeefaa08034060/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-liveness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Exit Code:    137
  Warning  Unhealthy       36m (x10 over 38m)     kubelet     
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-notready-liveness
namespace: aiops-e2e
creationTimestamp: 2026-05-15T11:40:37Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <non
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (1m 50.0s)
   📤 → 下游数据: evidence_items=7/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod 的详细状态信息以验证 CrashLoopBackOff 原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","tool_args":{"pod":"rc-notready-liveness","namespace":"aiops-e2e"},"purpose":"验证 Pod 的 Last State、Exit Code、Events 和重启次数，以判断 CrashLoopBackOff 的具体原因。","evidence_type":"state_validation","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"获取崩溃前的日志以验证容器崩溃原因","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-notready-liveness -n aiops-e2e --previous","tool_args":{"pod":"rc-notready-liveness","namespace":"aiops-e2e","previous":true},"purpose":"获取崩溃前的容器日志，以判断应用是否主动退出、是否有业务异常或资源问题。","evidence_type":"log_validation","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":["kubectl_previous_logs"],"counts_for_completeness":true},{"id":"e3","description":"获取 Pod 的 YAML 配置以验证 command/image 等关键配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-liveness -n aiops-e2e -o yaml","tool_args":{"pod":"rc-notready-liveness","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"验证容器的 command/args/image/resources 等配置，以判断是否存在启动命令错误或镜像问题。","evidence_type":"config_validation","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e4","description":"获取与 Pod 相关的 Events 以验证 probe 失败和重启原因","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-notready-liveness --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-notready-liveness","sort_by":".lastTimestamp"},"purpose":"验证 Events 中的 probe 失败信息、Killing 事件和 BackOff 事件，以判断是否为探针配置错误或健康检查问题。","evidence_type":"event_validation","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-liveness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Exit Code:    137\n  Warning  Unhealthy       36m (x10 over 38m)     kubelet            Liveness probe failed: liveness endpoint failed\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         3m24s (x122 over 34m)  kubelet            Back-off restarting failed container app in pod rc-notready-liveness_aiops-e2e(74fed2e5-116f-4b55-900c-9d0d8b7e83ab)\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\n  Normal   Killing         37m (x3 over 38m)      kubelet            Container app failed liveness probe, will be restarted\nName:             rc-notready-liveness\nLabels:           app=rc-notready-liveness\n                  cni.projectcalico.org/containerID: c311a318e2ee0d3b13fe103b0767abd6b4dd610d9e1aae4c7cf82792fb942255\n                  cni.projectcalico.org/podIP: 172.16.166.164/32\n                  cni.projectcalico.org/podIPs: 172.16.166.164/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n  Normal   Scheduled       38m                    default-scheduler  Successfully assigned aiops-e2e/rc-notready-liveness to node1\n关键状态/事件:\n    State:          Waiting\n    Last State:     Terminated\n      Reason:       Error","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1bfeefaa08034060/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1bfeefaa08034060/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1bfeefaa08034060/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1bfeefaa08034060/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1bfeefaa08034060/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1bfeefaa08034060/tools/002-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-liveness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T11:40:37Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-liveness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=16 reason=CrashLoopBackOff exitCode=137\n  message: back-off 5m0s restarting failed container=app pod=rc-notready-liveness_aiops-e2e(74fed2e5-116f-4b55-900c-9d0d8b7e83ab)\nvolumes:\n- {\"name\": \"kube-api-access-lz5gb\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1bfeefaa08034060/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1bfeefaa08034060/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1bfeefaa08034060/tools/003-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%；其中真实环境证据 7/8 项，完整度 88%；实际执行工具 7 个，匹配计划 3 个，未规划证据 4 个","plan_total":4,"plan_collected":3,"plan_completeness":0.75,"environment_evidence_total":8,"environment_evidence_collected":7,"environment_evidence_completeness":0.875,"executed_tool_count":7,"matched_tool_count":3,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"获取 Pod 的详细状态信息以验证 CrashLoopBackOff 原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","purpose":"验证 Pod 的 Last State、Exit Code、Events 和重启次数，以判断 CrashLoopBackOff 的具体原因。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取崩溃前的日志以验证容器崩溃原因","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-notready-liveness -n aiops-e2e --previous","purpose":"获取崩溃前的容器日志，以判断应用是否主动退出、是否有业务异常或资源问题。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取 Pod 的 YAML 配置以验证 command/image 等关键配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-liveness -n aiops-e2e -o yaml","purpose":"验证容器的 command/args/image/resources 等配置，以判断是否存在启动命令错误或镜像问题。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"获取与 Pod 相关的 Events 以验证 probe 失败和重启原因","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-notready-liveness --sort-by='.lastTimestamp'","purpose":"验证 Events 中的 probe 失败信息、Killing 事件和 BackOff 事件，以判断是否为探针配置错误或健康检查问题。","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":["e4(获取与 Pod 相关的 Events 以验证 probe 失败和重启原因): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 88%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取 Pod 的详细状态信息以验证 CrashLoopBackOff 原因 | `kubectl describe pod rc-notready-liveness -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_previous_logs | 获取崩溃前的日志以验证容器崩溃原因 | `kubectl logs rc-notready-liveness -n aiops-e2e --previous` |
   | e3 | important | ✅ | kubectl_get_yaml | 获取 Pod 的 YAML 配置以验证 command/image 等关键配置 | `kubectl get pod rc-notready-liveness -n aiops-e2e -o yaml` |
   | e4 | important | ❌ | kubectl_events | 获取与 Pod 相关的 Events 以验证 probe 失败和重启原因 | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-notre...` |

   ⚠️ 未采集原因:
   - e4(获取与 Pod 相关的 Events 以验证 probe 失败和重启原因): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (39.9s)
   📤 → 下游数据: root_cause=Pod rc-notready-liveness 的 liveness 探针配置错误或应用健康接口存在问题，导致健康检查失败，容器被强制终止并进入 CrashLoopBackOff 状态。
   confidence=80%
   causal_chain={"root_cause": "Pod 的 liveness 探针配置错误或应用健康接口存在问题，导致健康检查失败，容器被强制终止并进入 CrashLoopBackOff 状态。", "intermediate_causes": ["健康检查失败", "容器被强制终止"], "direct_causes": ["Exit Code 为 137", "Liveness probe failed"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"phenomenon": "Pod rc-notready-liveness 处于 CrashLoopBackOff 状态，Exit Code 为 137，且 Events 显示 Liveness probe failed。", "evidence": "kubectl_describe 摘要:\nname: rc-notready-liveness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Exit Code:    137\n  Warning  Unhealthy       36m (x10 over 38m)     kubelet            Liveness probe failed: liveness endpoint failed\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         3m24s (x122 over 34m)  kubelet            Back-off restarting failed container app in pod rc-notready-liveness_aiops-e2e(74fed2e5-116f-4b55-900c-9d0d8b7e83ab)\n                  pod_\n... 截断，原始 599 字符"}], "evidence_analysis": [{"phenomenon": "Pod rc-notready-liveness 处于 CrashLoopBackOff 状态，Exit Code 为 137，且 Events 显示 Liveness probe failed。", "analysis": "kubectl_describe 摘要显示 Pod rc-notready-liveness 的 Exit Code 为 137，表明容器在运行时被强制终止。Events 显示 Liveness probe failed，表明健康检查失败，导致容器重启。"}], "causal_chain": {"root_cause": "Pod 的 liveness 探针配置错误或应用健康接口存在问题，导致健康检查失败，容器被强制终止并进入 CrashLoopBackOff 状态。", "intermediate_causes": ["健康检查失败", "容器被强制终止"], "direct_causes": ["Exit Code 为 137", "Liveness probe failed"]}, "root_cause": "Pod rc-notready-liveness 的 liveness 探针配置错误或应用健康接口存在问题，导致健康检查失败，容器被强制终止并进入 CrashLoopBackOff 状态。", "root_cause_summary": "Pod rc-notready-liveness 的 liveness 探针配置错误或应用健康接口存在问题，导致健康检查失败，容器被强制终止并进入 CrashLoopBackOff 状态。", "confidence": 0.8, "confidence_reason": "有直接证据表明健康检查失败和容器强制终止，但缺少应用日志以进一步确认具体原因。", "primary_runbooks": ["pod-notready-probe-failed.md"], "alternative_causes": [{"cause": "容器启动失败", "probability": "低", "reason": "Exit Code 为 137 表示强制终止，而非启动失败。"}, {"cause": "资源不足", "probability": "低", "reason": "没有证据表明资源不足导致容器终止。"}], "limitations": "缺少应用日志，无法进一步确认健康检查失败的具体原因。", "llm_raw_analysis": "Pod rc-notready-liveness 处于 CrashLoopBackOff 状态，Exit Code 为 137，且 Events 显示 Liveness probe failed。这表明健康检查失败，导致容器被强制终止并进入 CrashLoopBackOff 状态。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-notready-liveness 的 liveness 探针配置错误或应用健康接口存在问题，导致健康检查失败，容器被强制终止并进入 CrashLoopBackOff 状态。
   置信度: 80%
   🔗 因果链:
     根本原因: Pod 的 liveness 探针配置错误或应用健康接口存在问题，导致健康检查失败，容器被强制终止并进入 CrashLoopBackOff 状态。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 23.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4313 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 22.8s
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
| **Pod异常状态** | CrashLoopBackOff |
| **兼容归因层** | L4 |
| **问题分类** | NotReadyProbeFailed |
| **置信度** | 高 (80%) |
| **证据完整度** | 3/4 (75%) |

---

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-notready-liveness |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | Liveness probe failed, Exit Code: 137 |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff, RESTARTS: 16 (58s ago)` | Pod 处于 CrashLoopBackOff 状态，已重启 16 次 |
| 2 | 描述信息 | `kubectl describe pod rc-notready-liveness` | `Exit Code: 137`, `Warning: Unhealthy (Liveness probe failed)` | 容器因健康检查失败被强制终止 |
| 3 | Pod YAML 配置 | `kubectl get pod -o yaml` | 未发现明显配置错误（如 command、image、探针路径等） | 无法从配置直接确认探针错误 |
| 4 | 崩溃前日志 | `kubectl logs rc-notready-liveness --previous` | `关键日志: (no output)` | 无日志输出，无法确认健康检查失败原因 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 CrashLoopBackOff，Exit Code 137 与 Liveness probe 失败事件一致，表明容器被强制终止。
- **证据链**：健康检查失败 → kubelet 强制终止容器 → Pod 重启 → 重复失败 → 进入 CrashLoopBackOff 状态。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 与 Pod 相关的 Events | important | 无法进一步分析探针失败的上下文和具体原因 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod 的 liveness 探针配置错误或应用健康接口存在问题，导致健康检查失败，容器被强制终止并进入 CrashLoopBackOff 状态。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ liveness 探针配置错误 → 探针失败 → kubelet 强制终止容器 → 容器重启 → 重复失败 → 进入 CrashLoopBackOff 状态。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器被强制终止（Exit Code 137），Pod 进入 CrashLoopBackOff 状态。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod rc-notready-liveness 状态为 CrashLoopBackOff，重启次数不断增加。 │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (CrashLoopBackOff 状态) 和证据 #2 (Exit Code 137, Liveness probe failed)，问题的根本原因是**Pod 的 liveness 探针配置错误或应用健康接口存在问题**，导致健康检查失败，容器被 kubelet 强制终止并进入 CrashLoopBackOff 状态。

**置信度**：高 (80%)
- ✅ Pod 状态为 CrashLoopBackOff
- ✅ Exit Code 137 明确指向强制终止
- ✅ Liveness probe failed 明确指出健康检查失败
- ⚠️ 缺少应用日志和 Events，无法进一步确认探针失败的具体原因

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查 liveness 探针配置**
```bash
kubectl get pod rc-notready-liveness -n aiops-e2e -o jsonpath='{.spec.containers[*].livenessProbe}' | jq .
```
*目的*：查看探针的路径、端口、超时时间等配置，确认是否与应用实际接口一致。

**2. [优先] 检查应用健康接口**
```bash
curl -v http://172.16.166.164:8080/health
```
*目的*：确认健康接口是否正常响应（HTTP 200）。

**3. [可选] 查看崩溃前日志**
```bash
kubectl logs rc-notready-liveness -n aiops-e2e --previous | tail -100
```
*目的*：确认健康检查失败前的应用状态（虽然当前无日志输出，但可尝试查看）。

### 后续优化

1. **调整 liveness 探针配置**：
   - 增加 `failureThreshold`，避免因短时失败导致频繁重启。
   - 调整 `initialDelaySeconds`，避免应用启动前探针误判。
   - 示例调整：
     ```yaml
     livenessProbe:
       httpGet:
         path: /health
         port: 8080
       initialDelaySeconds: 10
       failureThreshold: 3
       timeoutSeconds: 1
     ```

2. **配置 readiness 探针**：确保健康检查失败前不将流量路由到 Pod。

3. **监控健康检查失败事件**：使用 Prometheus 或 Kubernetes Events 界面监控探针失败频率。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-notready-liveness -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-notready-liveness -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 重启次数不再增加 |
| 3. 检查探针事件 | `kubectl describe pod rc-notready-liveness -n aiops-e2e` | 无 Unhealthy 警告 |
| 4. 检查健康接口 | `curl -v http://172.16.166.164:8080/health` | HTTP 200 OK |

---

## ⚠️ 注意事项

- 如果健康检查接口本身存在问题（如路径错误、端口错误），需同步调整 readiness 探针配置。
- 如果探针配置无误，可能需要进一步分析应用日志，确认健康接口返回失败的具体原因。
- 注意调整探针参数时，避免设置过高的 `failureThreshold`，以免掩盖真正的健康问题。

---

---

## 📊 性能统计

├─ 总耗时: 5.4m
├─ 问题定位: 89.6s (28%) ✅
├─ 证据链采集: 110.0s (34%) ✅
├─ 根因分析: 39.9s (12%) ✅
├─ 汇总总结: 83.3s (26%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 11 次
```

📋 诊断追踪

- **核心 Runbook**: pod-notready-probe-failed
- **参考 Runbook**: pod-notready-probe-failed, pod-crashloop-backoff, pod-crashloop-runtime
- **工具调用**: 11 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
