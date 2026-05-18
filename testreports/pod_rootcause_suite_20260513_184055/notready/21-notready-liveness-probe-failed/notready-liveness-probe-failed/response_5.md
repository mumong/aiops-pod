======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 2d28dc77a1b746af]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'CrashLoopBackOff': 1, 'Running': 46}
NAMESPACE     NAME                                                READY   STATUS           
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 Error: Runbook 'pod-notready-probe.md' is disabled by the current runtime profile
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                   READY   STATUS             RESTARTS      AGE     IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-notready-liveness   0/1     CrashLoopBackOff   7 (75s ago)
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-liveness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Exit Code:    137
  Warning  Unhealthy       5m17s (x10 over 7m14s)  kubelet    
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": ["L4"],
  "layer_name": "NotReadyProbeFailed",
  "confidence": 0.95,
  "reasoning": "当前存在1个Pod异常，状态为CrashLoopBackOff，归类为NotReadyProbeFailed。异常Pod的Exit Code为137，表明可能是由于liveness probe失败导致容器被重启。诊断事件显示Liveness probe失败，Pod状态为Unhealthy，并且正在被Killing，最终进入CrashLoopBackOff状态。建议检查liveness probe配置、应用健康检查接口是否正常。",
  "abnormal_pods": [
    {
      "namespace": "aiops-e2e",
      "name": "rc-notready-liveness",
      "status": "CrashLoopBackOff",
      "ready": "0/1",
      "restarts": "7 (75s ago)",
      "age": "7m16s",
      "ip": "172.16.166.164",
      "node": "node1"
    }
  ],
  "abnormal_groups": [
    {
      "pod_abnormal_type": "NotReadyProbeFailed",
      "pod_status_keyword": "CrashLoopBackOff",
      "status_category": "CrashLoopBackOff",
      "count": 1
    }
  ],
  "key_entities": [
    "rc-notready-liveness",
    "aiops-e2e",
    "node1",
    "liveness probe"
  ],
  "possible_scenarios": [
    "Pod健康检查(liveness probe)配置错误或接口返回异常",
    "应用启动慢导致健康检查超时",
    "应用健康接口本身异常或返回500错误",
    "容器内存不足或OOMKilled导致Pod被重启"
  ]
}
   ✅ [问题定位] 完成 (40.8s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[]
   entities=[]
   reasoning=当前存在1个Pod异常，状态为CrashLoopBackOff，归类为NotReadyProbeFailed。异常Pod的Exit Code为137，表明可能是由于liveness probe失败导致容器被重启。诊断事件显示Liveness probe失败，Pod状态为Unhealthy，并且正在被Killing，最终进入CrashLoopBackOff状态。建议检查liveness probe配置、应用健康检查接口是否正常。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "NotReadyProbeFailed", "confidence": 0.95, "reasoning": "当前存在1个Pod异常，状态为CrashLoopBackOff，归类为NotReadyProbeFailed。异常Pod的Exit Code为137，表明可能是由于liveness probe失败导致容器被重启。诊断事件显示Liveness probe失败，Pod状态为Unhealthy，并且正在被Killing，最终进入CrashLoopBackOff状态。建议检查liveness probe配置、应用健康检查接口是否正常。", "abnormal_pods": [{"name": "rc-notready-liveness", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "NotReadyProbeFailed", "status_category": "CrashLoopBackOff", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-notready-liveness                                0/1     CrashLoopBackOff   7 (70s ago)   7m11s   172.16.166.164   node1    <none>           <none>            app=rc-notready-liveness,pod_abnormal_type=NotReadyProbeFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/2d28dc77a1b746af/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/2d28dc77a1b746af/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/2d28dc77a1b746af/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-liveness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Exit Code:    137
  Warning  Unhealthy       7m18s (x10 over 9m15s)  kubelet    
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
7m27s (x10 over 9m24s)   Warning   Unhealthy        Pod/rc-notready-liveness   Liveness probe failed: liveness endpoint failed
8m (x3 over 9m18s)       Normal    Killing     
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [证据链采集] 已采集证据：
1. **kubectl_describe** 显示 Pod rc-notready-liveness 处于 CrashLoopBackOff 状态，Exit Code 为 137，表明可能是 OOMKilled 或 liveness probe 失败。
2. **kubectl_events** 显示 liveness probe 失败，Pod 被标记为 Unhealthy 并触发 Killing。
3. **kubectl_previous_logs** 未返回日志，表明容器崩溃前没有输出信息。

未采集证据：
1. 应用健康检查接口的配置和响应状态。
2. liveness probe 的具体配置（如 path、initialDelaySeconds、failureThreshold 等）。

冲突证据：
1. kubectl_previous_logs 未返回任何日志，可能表明容器崩溃前没有输出或容器未正确记录日志。

建议检查 liveness probe 配置和应用健康检查接口是否正常。
   ✅ [证据链采集] 完成 (2m 6.5s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod 'rc-notready-liveness' 的详细描述信息，以验证其异常原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","tool_args":{"name":"rc-notready-liveness","namespace":"aiops-e2e"},"purpose":"获取 Pod 的详细状态、事件和配置信息，确认导致 CrashLoopBackOff 的原因","evidence_type":"current_status","target_scope":"Pod/aiops-e2e/rc-notready-liveness","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod 'rc-notready-liveness' 的事件信息，以确认异常事件的详细信息","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-notready-liveness","tool_args":{"name":"rc-notready-liveness","namespace":"aiops-e2e"},"purpose":"确认异常 Pod 的事件记录，如 Unhealthy、Killing 等，以判断其状态变化原因","evidence_type":"events","target_scope":"Pod/aiops-e2e/rc-notready-liveness","acceptable_tools":["kubectl_events"],"counts_for_completeness":true},{"id":"e3","description":"获取 Pod 'rc-notready-liveness' 的日志，以检查容器崩溃前的最后状态","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-notready-liveness -n aiops-e2e --previous","tool_args":{"name":"rc-notready-liveness","namespace":"aiops-e2e","container":null},"purpose":"获取容器在崩溃前的最后日志，确认是否与 liveness probe 失败有关","evidence_type":"logs","target_scope":"Pod/aiops-e2e/rc-notready-liveness","acceptable_tools":["kubectl_previous_logs"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-liveness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Exit Code:    137\n  Warning  Unhealthy       7m18s (x10 over 9m15s)  kubelet            Liveness probe failed: liveness endpoint failed\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\n  Normal   Killing         7m51s (x3 over 9m9s)    kubelet            Container app failed liveness probe, will be restarted\nName:             rc-notready-liveness\nLabels:           app=rc-notready-liveness\n                  cni.projectcalico.org/containerID: c311a318e2ee0d3b13fe103b0767abd6b4dd610d9e1aae4c7cf82792fb942255\n                  cni.projectcalico.org/podIP: 172.16.166.164/32\n                  cni.projectcalico.org/podIPs: 172.16.166.164/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n  Normal   Scheduled       9m18s                   default-scheduler  Successfully assigned aiops-e2e/rc-notready-liveness to node1\n关键状态/事件:\n    State:          Running\n    Last State:     Terminated\n      Reason:       Error","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2d28dc77a1b746af/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2d28dc77a1b746af/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2d28dc77a1b746af/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n7m27s (x10 over 9m24s)   Warning   Unhealthy        Pod/rc-notready-liveness   Liveness probe failed: liveness endpoint failed\n8m (x3 over 9m18s)       Normal    Killing          Pod/rc-notready-liveness   Container app failed liveness probe, will be restarted\n9m28s                    Normal    Scheduled        Pod/rc-notready-liveness   Successfully assigned aiops-e2e/rc-notready-liveness to node1\n9m27s                    Normal    AddedInterface   Pod/rc-notready-liveness   Add eth0 [172.16.166.164/32] from k8s-pod-network\n7m30s (x4 over 9m27s)    Normal    Created          Pod/rc-notready-liveness   Created container app\n7m30s (x4 over 9m27s)    Normal    Started          Pod/rc-notready-liveness   Started container app\n4m6s (x8 over 9m27s)     Normal    Pulled           Pod/rc-notready-liveness   Container image \"busybox:1.36\" already present on machine","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2d28dc77a1b746af/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2d28dc77a1b746af/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2d28dc77a1b746af/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2d28dc77a1b746af/tools/003-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2d28dc77a1b746af/tools/003-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2d28dc77a1b746af/tools/003-evidence-kubectl_previous_logs.summary.txt"}],"llm_analysis":"已采集证据：\n1. **kubectl_describe** 显示 Pod rc-notready-liveness 处于 CrashLoopBackOff 状态，Exit Code 为 137，表明可能是 OOMKilled 或 liveness probe 失败。\n2. **kubectl_events** 显示 liveness probe 失败，Pod 被标记为 Unhealthy 并触发 Killing。\n3. **kubectl_previous_logs** 未返回日志，表明容器崩溃前没有输出信息。\n\n未采集证据：\n1. 应用健康检查接口的配置和响应状态。\n2. liveness probe 的具体配置（如 path、initialDelaySeconds、failureThreshold 等）。\n\n冲突证据：\n1. kubectl_previous_logs 未返回任何日志，可能表明容器崩溃前没有输出或容器未正确记录日志。\n\n建议检查 liveness probe 配置和应用健康检查接口是否正常。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 6/6 项，完整度 100%；实际执行工具 6 个，匹配计划 3 个，未规划证据 3 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":6,"environment_evidence_collected":6,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":3,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1","description":"获取 Pod 'rc-notready-liveness' 的详细描述信息，以验证其异常原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","purpose":"获取 Pod 的详细状态、事件和配置信息，确认导致 CrashLoopBackOff 的原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod 'rc-notready-liveness' 的事件信息，以确认异常事件的详细信息","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-notready-liveness","purpose":"确认异常 Pod 的事件记录，如 Unhealthy、Killing 等，以判断其状态变化原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取 Pod 'rc-notready-liveness' 的日志，以检查容器崩溃前的最后状态","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-notready-liveness -n aiops-e2e --previous","purpose":"获取容器在崩溃前的最后日志，确认是否与 liveness probe 失败有关","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取 Pod 'rc-notready-liveness' 的详细描述信息，以验证其异常原因 | `kubectl describe pod rc-notready-liveness -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_events | 获取 Pod 'rc-notready-liveness' 的事件信息，以确认异常事件的详细信息 | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-notre...` |
   | e3 | important | ✅ | kubectl_previous_logs | 获取 Pod 'rc-notready-liveness' 的日志，以检查容器崩溃前的最后状态 | `kubectl logs rc-notready-liveness -n aiops-e2e --previous` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 13.8s)
   📤 → 下游数据: root_cause=Pod rc-notready-liveness 进入 CrashLoopBackOff 状态，Exit Code 为 137，表明可能是由于 liveness probe 配置不正确或应用健康检查接口异常导致容器被重启。kubectl_events 显示 liveness probe 失败，Pod 被标记为 Unhealthy 并触发 Killing。
   confidence=85%
   causal_chain={"root_cause": "liveness probe 配置不正确或应用健康检查接口异常", "intermediate_causes": ["liveness probe 失败", "Pod 被标记为 Unhealthy 并触发 Killing"], "immediate_effects": ["Pod 进入 CrashLoopBackOff 状态", "Exit Code 为 137"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"kubectl_describe": "显示 Pod rc-notready-liveness 处于 CrashLoopBackOff 状态，Exit Code 为 137，表明可能是 OOMKilled 或 liveness probe 失败。"}, {"kubectl_events": "显示 liveness probe 失败，Pod 被标记为 Unhealthy 并触发 Killing。"}, {"kubectl_previous_logs": "未返回日志，表明容器崩溃前没有输出信息。"}], "evidence_analysis": [{"kubectl_describe": "Exit Code 137 通常表示 OOMKilled 或 liveness probe 失败。"}, {"kubectl_events": "liveness probe 失败导致 Pod 被标记为 Unhealthy 并触发 Killing。"}, {"kubectl_previous_logs": "无日志输出表明容器崩溃前没有记录任何信息。"}], "causal_chain": {"root_cause": "liveness probe 配置不正确或应用健康检查接口异常", "intermediate_causes": ["liveness probe 失败", "Pod 被标记为 Unhealthy 并触发 Killing"], "immediate_effects": ["Pod 进入 CrashLoopBackOff 状态", "Exit Code 为 137"]}, "root_cause": "Pod rc-notready-liveness 进入 CrashLoopBackOff 状态，Exit Code 为 137，表明可能是由于 liveness probe 配置不正确或应用健康检查接口异常导致容器被重启。kubectl_events 显示 liveness probe 失败，Pod 被标记为 Unhealthy 并触发 Killing。", "root_cause_summary": "Pod rc-notready-liveness 进入 CrashLoopBackOff 状态，Exit Code 为 137，表明可能是由于 liveness probe 配置不正确或应用健康检查接口异常导致容器被重启。kubectl_events 显示 liveness probe 失败，Pod 被标记为 Unhealthy 并触发 Killing。", "confidence": 0.85, "confidence_reason": "有直接证据表明 liveness probe 失败，因果链清晰。", "primary_runbooks": ["pod-notready-probe-failed.md"], "alternative_causes": [{"cause": "容器内存不足导致 OOMKilled", "probability": "低", "reason": "Exit Code 137 也可能是 OOMKilled，但无日志支持此假设。"}], "limitations": "kubectl_previous_logs 未返回任何日志，无法确认容器崩溃前的具体状态。", "llm_raw_analysis": "已采集证据：1. kubectl_describe 显示 Pod rc-notready-liveness 处于 CrashLoopBackOff 状态，Exit Code 为 137，表明可能是 OOMKilled 或 liveness probe 失败。2. kubectl_events 显示 liveness probe 失败，Pod 被标记为 Unhealthy 并触发 Killing。3. kubectl_previous_logs 未返回日志，表明容器崩溃前没有输出信息。未采集证据：1. 应用健康检查接口的配置和响应状态。2. liveness probe 的具体配置（如 path、initialDelaySeconds、failureThreshold 等）。冲突证据：1. kubectl_previous_logs 未返回任何日志，可能表明容器崩溃前没有输出或容器未正确记录日志。建议检查 liveness probe 配置和应用健康检查接口是否正常。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-notready-liveness 进入 CrashLoopBackOff 状态，Exit Code 为 137，表明可能是由于 liveness probe 配置不正确或应用健康检查接口异常导致容器被重启。kubectl_events 显示 liveness probe 失败，Pod...
   置信度: 85%
   🔗 因果链:
     根本原因: liveness probe 配置不正确或应用健康检查接口异常


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 9.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4024 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 10.8s
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
| **问题分类** | NotReadyProbeFailed（Liveness probe 失败） |
| **置信度** | 高 (85%) |
| **证据完整度** | 3/3 (100%) |

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
| 错误信息 | Liveness probe failed: liveness endpoint failed |

**当前集群状态**：
- 存在 1 个异常 Pod，状态为 `CrashLoopBackOff`，重启次数为 7 次
- Pod 被标记为 `Unhealthy`，并被 `Killing`
- Pod 的 Exit Code 为 137，表明可能是内存不足（OOMKilled）或探针失败
- 无崩溃前容器日志输出

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff, RESTARTS: 7` | Pod 持续崩溃并重启 |
| 2 | Liveness probe 失败 | `kubectl describe pod` | `Warning: Unhealthy (x10 over 7m14s): Liveness probe failed` | 探针失败导致容器被终止 |
| 3 | 容器退出码 | `kubectl describe pod` | `Exit Code: 137` | 可能是 OOMKilled 或探针失败 |
| 4 | 事件记录 | `kubectl get events` | `7m27s (x10 over 9m24s): Warning Unhealthy, Liveness probe failed` | 探针失败事件重复发生 |
| 5 | Pod 描述摘要 | `kubectl describe pod` | `Reason: CrashLoopBackOff` | Pod 被标记为不健康并进入 CrashLoopBackOff |
| 6 | 日志缺失 | `kubectl logs --previous` | `no output` | 无法确认容器崩溃前状态 |

### 证据关联分析
- **证据 #1 + #2 + #5 印证**：Pod 被标记为 Unhealthy，探针失败，触发 Killing，进入 CrashLoopBackOff 状态
- **证据链**：
  - Liveness probe 配置或应用健康检查接口异常 → 探针失败 → 容器被终止 → Pod 重启 → 持续失败 → CrashLoopBackOff

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 容器崩溃前日志 | critical | 无法确认健康检查接口是否正常，或探针配置是否合理 |

---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Liveness probe 配置不正确或应用健康检查接口异常                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 探针失败 → 容器被终止 → Pod 重启                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Liveness probe 失败（Exit Code 137）                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 CrashLoopBackOff，持续重启                             │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2（探针失败事件）、证据 #3（Exit Code 137）和证据 #5（CrashLoopBackOff），问题的根本原因是**liveness probe 配置不正确或应用健康检查接口异常**，导致探针失败，容器被终止并持续重启。
**置信度**：高 (85%)
- ✅ 多次探针失败事件记录
- ✅ 明确的 Exit Code 137
- ⚠️ 缺少崩溃前日志，无法确认探针失败的具体原因

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 检查 liveness probe 配置**
```bash
kubectl describe pod rc-notready-liveness -n aiops-e2e | grep -i liveness
```
*依据*：确认 probe 路径、超时时间和失败阈值是否合理

**2. [可选] 检查应用健康检查接口**
```bash
curl -v http://<pod-ip>:<health-check-port>/<health-check-path>
```
*目的*：确认接口是否正常响应

**3. [可选] 查看崩溃前日志**
```bash
kubectl logs rc-notready-liveness -n aiops-e2e --previous
```
*目的*：确认探针失败前应用状态（当前无日志输出）

### 后续优化
1. **调整 liveness probe 配置**：适当增加 `initialDelaySeconds`、`failureThreshold` 和 `timeoutSeconds`
2. **配置 readiness probe**：确保探针失败时不会影响流量
3. **启用日志采集**：确保容器崩溃前日志可访问

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-notready-liveness -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-notready-liveness -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |
| 3. 检查探针状态 | `kubectl describe pod rc-notready-liveness -n aiops-e2e` | No Unhealthy events |

---
## ⚠️ 注意事项
- 如果探针失败仍持续，需检查应用是否正常响应健康检查接口
- 调整 probe 配置时，建议逐步测试，避免影响服务可用性
- 如果问题与资源限制（如内存不足）相关，可能需结合 OOMKilled 原因进一步排查

---

## 📊 性能统计

├─ 总耗时: 5.2m
├─ 问题定位: 40.8s (13%) ✅
├─ 证据链采集: 126.5s (41%) ✅
├─ 根因分析: 73.8s (24%) ✅
├─ 汇总总结: 69.8s (22%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 7 次
```

📋 诊断追踪

- **核心 Runbook**: pod-notready-probe-failed
- **参考 Runbook**: pod-notready-probe-failed
- **工具调用**: 7 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
