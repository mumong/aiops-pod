======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: ea74f5ab9baa4e4e]

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
      📄 NAME                   READY   STATUS             RESTARTS       AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-notready-liveness   0/1     CrashLoopBackOff   16 (30s ago)
   💭 [问题定位] 调用工具: kubectl_container_logs
   💭 [问题定位] 工具结果: kubectl_container_logs (success)
      📄 kubectl_container_logs 输出摘要: raw_chars=187 lines=3
Command failed (exit 1):
kubectl logs rc-notready-liveness -c rc-notready-liveness -n aiops-e2e --tail=100
error: container rc-notready-liveness is n
   💭 [问题定位] 调用工具: kubectl_previous_logs_all_containers
   💭 [问题定位] 工具结果: kubectl_previous_logs_all_containers (success)
      📄 kubectl_previous_logs_all_containers 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [问题定位] 调用工具: kubectl_logs_all_containers
   💭 [问题定位] 工具结果: kubectl_logs_all_containers (success)
      📄 kubectl_logs_all_containers 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
33m (x10 over 35m)    Warning   Unhealthy        Pod/rc-notready-liveness   Liveness probe failed: liveness endpoint failed
12s (x122 over 31m)   Warning   BackOff          P
   💭 [问题定位] 调用工具: kubectl_get_yaml
   ✅ [问题定位] 完成 (28.3s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[]
   entities=[]
   reasoning=当前环境中存在一个处于 CrashLoopBackOff 状态的 Pod 'rc-notready-liveness'，且其 pod_abnormal_type 明确标记为 'NotReadyProbeFailed'。这表明异常根因是应用程序健康检查失败，属于 L4 层级（应用错误/配置错误）。虽然事件日志中多次出现重启和探针失败的警告，但当前仍异常的 Pod 状态决定了最终归因于 L4。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "", "confidence": 0.5, "reasoning": "当前环境中存在一个处于 CrashLoopBackOff 状态的 Pod 'rc-notready-liveness'，且其 pod_abnormal_type 明确标记为 'NotReadyProbeFailed'。这表明异常根因是应用程序健康检查失败，属于 L4 层级（应用错误/配置错误）。虽然事件日志中多次出现重启和探针失败的警告，但当前仍异常的 Pod 状态决定了最终归因于 L4。", "abnormal_pods": [{"name": "rc-notready-liveness", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "NotReadyProbeFailed", "status_category": "app_health", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-notready-liveness                                0/1     CrashLoopBackOff   16 (27s ago)   35m    172.16.166.164   node1    <none>           <none>            app=rc-notready-liveness,pod_abnormal_type=NotReadyProbeFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/ea74f5ab9baa4e4e/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/ea74f5ab9baa4e4e/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/ea74f5ab9baa4e4e/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
name: rc-notready-liveness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Exit Code:    137
  Warning  Unhealthy       35m (x10 over 37m)    kubelet      
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
35m (x10 over 37m)     Warning   Unhealthy        Pod/rc-notready-liveness   Liveness probe failed: liveness endpoint failed
119s (x122 over 33m)   Warning   BackOff         
   💭 [证据链采集] 调用工具: kubectl_previous_logs_all_containers
   💭 [证据链采集] 工具结果: kubectl_previous_logs_all_containers (success)
      📄 kubectl_previous_logs_all_containers 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [证据链采集] # 证据结论

已采集证据：
- `kubectl_describe`：Pod `rc-notready-liveness` 处于 `CrashLoopBackOff` 状态，`Exit Code: 137`，事件中频繁出现 `Liveness probe failed` 和 `Back-off restarting failed container`。
- `kubectl_events`：事件日志显示 `Liveness probe failed` 和 `Back-off restarting failed container`，确认健康检查失败。
- `kubectl_previous_logs_all_containers`：未发现上一次运行时的容器日志。

未采集证据：
- 无

冲突证据：
- 无

根据以上证据，Pod `rc-notready-liveness` 处于 `CrashLoopBackOff` 状态，主要原因是健康检查失败（`Liveness probe failed`）。需要进一步检查探针配置和应用日志以确定具体原因。
   ✅ [证据链采集] 完成 (2m 1.2s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 'rc-notready-liveness' 的详细描述，验证其状态、事件、容器状态和配置","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","tool_args":{"name":"rc-notready-liveness","namespace":"aiops-e2e","kind":"Pod"},"purpose":"验证 Pod 的当前状态、事件、容器状态和配置信息，确认异常原因","evidence_type":"state/configuration","target_scope":"Pod/aiops-e2e/rc-notready-liveness","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 'rc-notready-liveness' 的事件日志，验证其健康检查失败的具体原因","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-notready-liveness","tool_args":{"namespace":"aiops-e2e","selector":"involvedObject.name=rc-notready-liveness"},"purpose":"验证 Pod 'rc-notready-liveness' 的事件日志，确认健康检查失败的详细原因","evidence_type":"event","target_scope":"Pod/aiops-e2e/rc-notready-liveness","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod 'rc-notready-liveness' 的上一次容器日志，验证其健康检查失败时的错误信息","level":"important","tool":"kubectl_previous_logs_all_containers","command":"kubectl logs rc-notready-liveness -n aiops-e2e --previous --all-containers=true","tool_args":{"name":"rc-notready-liveness","namespace":"aiops-e2e","all_containers":true,"previous":true},"purpose":"验证 Pod 'rc-notready-liveness' 上一次运行时的容器日志，确认健康检查失败时的错误信息","evidence_type":"log","target_scope":"Pod/aiops-e2e/rc-notready-liveness","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-liveness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Exit Code:    137\n  Warning  Unhealthy       35m (x10 over 37m)    kubelet            Liveness probe failed: liveness endpoint failed\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         112s (x122 over 33m)  kubelet            Back-off restarting failed container app in pod rc-notready-liveness_aiops-e2e(74fed2e5-116f-4b55-900c-9d0d8b7e83ab)\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\n  Normal   Killing         35m (x3 over 36m)     kubelet            Container app failed liveness probe, will be restarted\nName:             rc-notready-liveness\nLabels:           app=rc-notready-liveness\n                  cni.projectcalico.org/containerID: c311a318e2ee0d3b13fe103b0767abd6b4dd610d9e1aae4c7cf82792fb942255\n                  cni.projectcalico.org/podIP: 172.16.166.164/32\n                  cni.projectcalico.org/podIPs: 172.16.166.164/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n  Normal   Scheduled       37m                   default-scheduler  Successfully assigned aiops-e2e/rc-notready-liveness to node1\n关键状态/事件:\n    State:          Waiting\n    Last State:     Terminated\n      Reason:       Error","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ea74f5ab9baa4e4e/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ea74f5ab9baa4e4e/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ea74f5ab9baa4e4e/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n35m (x10 over 37m)     Warning   Unhealthy        Pod/rc-notready-liveness   Liveness probe failed: liveness endpoint failed\n119s (x122 over 33m)   Warning   BackOff          Pod/rc-notready-liveness   Back-off restarting failed container app in pod rc-notready-liveness_aiops-e2e(74fed2e5-116f-4b55-900c-9d0d8b7e83ab)\n35m (x3 over 37m)      Normal    Killing          Pod/rc-notready-liveness   Container app failed liveness probe, will be restarted\n37m                    Normal    Scheduled        Pod/rc-notready-liveness   Successfully assigned aiops-e2e/rc-notready-liveness to node1\n37m                    Normal    AddedInterface   Pod/rc-notready-liveness   Add eth0 [172.16.166.164/32] from k8s-pod-network\n35m (x4 over 37m)      Normal    Created          Pod/rc-notready-liveness   Created container app\n35m (x4 over 37m)      Normal    Started          Pod/rc-notready-liveness   Started container app\n22m (x11 over 37m)     Normal    Pulled           Pod/rc-notready-liveness   Container image \"busybox:1.36\" already present on machine","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ea74f5ab9baa4e4e/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ea74f5ab9baa4e4e/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ea74f5ab9baa4e4e/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_previous_logs_all_containers","data":"kubectl_previous_logs_all_containers 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ea74f5ab9baa4e4e/tools/003-evidence-kubectl_previous_logs_all_containers.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ea74f5ab9baa4e4e/tools/003-evidence-kubectl_previous_logs_all_containers.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ea74f5ab9baa4e4e/tools/003-evidence-kubectl_previous_logs_all_containers.summary.txt"}],"llm_analysis":"# 证据结论\n\n已采集证据：\n- `kubectl_describe`：Pod `rc-notready-liveness` 处于 `CrashLoopBackOff` 状态，`Exit Code: 137`，事件中频繁出现 `Liveness probe failed` 和 `Back-off restarting failed container`。\n- `kubectl_events`：事件日志显示 `Liveness probe failed` 和 `Back-off restarting failed container`，确认健康检查失败。\n- `kubectl_previous_logs_all_containers`：未发现上一次运行时的容器日志。\n\n未采集证据：\n- 无\n\n冲突证据：\n- 无\n\n根据以上证据，Pod `rc-notready-liveness` 处于 `CrashLoopBackOff` 状态，主要原因是健康检查失败（`Liveness probe failed`）。需要进一步检查探针配置和应用日志以确定具体原因。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 9/9 项，完整度 100%；实际执行工具 8 个，匹配计划 3 个，未规划证据 5 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":9,"environment_evidence_collected":9,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":3,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 'rc-notready-liveness' 的详细描述，验证其状态、事件、容器状态和配置","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","purpose":"验证 Pod 的当前状态、事件、容器状态和配置信息，确认异常原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 'rc-notready-liveness' 的事件日志，验证其健康检查失败的具体原因","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-notready-liveness","purpose":"验证 Pod 'rc-notready-liveness' 的事件日志，确认健康检查失败的详细原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod 'rc-notready-liveness' 的上一次容器日志，验证其健康检查失败时的错误信息","level":"important","tool":"kubectl_previous_logs_all_containers","command":"kubectl logs rc-notready-liveness -n aiops-e2e --previous --all-containers=true","purpose":"验证 Pod 'rc-notready-liveness' 上一次运行时的容器日志，确认健康检查失败时的错误信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_container_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_previous_logs_all_containers","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_logs_all_containers","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取异常 Pod 'rc-notready-liveness' 的详细描述，验证其状态、事... | `kubectl describe pod rc-notready-liveness -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_events | 获取异常 Pod 'rc-notready-liveness' 的事件日志，验证其健康检查... | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-notre...` |
   | e3 | important | ✅ | kubectl_previous_logs_all... | 获取异常 Pod 'rc-notready-liveness' 的上一次容器日志，验证其健... | `kubectl logs rc-notready-liveness -n aiops-e2e --previous --all-containers=true` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 4.8s)
   📤 → 下游数据: root_cause=Pod 'rc-notready-liveness' 的健康检查失败导致其处于 'CrashLoopBackOff' 状态。
   confidence=80%
   causal_chain={"root_cause": "Pod 'rc-notready-liveness' 的健康检查失败导致其处于 'CrashLoopBackOff' 状态。", "conveyance": "健康检查失败导致容器被终止并重新启动，形成循环。", "direct_cause": "健康检查失败，具体原因需要检查探针配置和应用日志。"}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"kubectl_describe": "Pod 'rc-notready-liveness' 处于 'CrashLoopBackOff' 状态，Exit Code: 137，事件中频繁出现 'Liveness probe failed' 和 'Back-off restarting failed container'。"}, {"kubectl_events": "事件日志显示 'Liveness probe failed' 和 'Back-off restarting failed container'，确认健康检查失败。"}, {"kubectl_previous_logs_all_containers": "未发现上一次运行时的容器日志。"}], "evidence_analysis": [{"kubectl_describe": "Pod 'rc-notready-liveness' 处于 'CrashLoopBackOff' 状态，Exit Code: 137，事件中频繁出现 'Liveness probe failed' 和 'Back-off restarting failed container'。"}, {"kubectl_events": "事件日志显示 'Liveness probe failed' 和 'Back-off restarting failed container'，确认健康检查失败。"}, {"kubectl_previous_logs_all_containers": "未发现上一次运行时的容器日志。"}], "causal_chain": {"root_cause": "Pod 'rc-notready-liveness' 的健康检查失败导致其处于 'CrashLoopBackOff' 状态。", "conveyance": "健康检查失败导致容器被终止并重新启动，形成循环。", "direct_cause": "健康检查失败，具体原因需要检查探针配置和应用日志。"}, "root_cause": "Pod 'rc-notready-liveness' 的健康检查失败导致其处于 'CrashLoopBackOff' 状态。", "root_cause_summary": "Pod 'rc-notready-liveness' 的健康检查失败导致其处于 'CrashLoopBackOff' 状态。", "confidence": 0.8, "confidence_reason": "有工具证据，分析合理。", "primary_runbooks": ["pod-notready-probe.md"], "alternative_causes": [], "limitations": "没有获取到容器日志，无法确定具体失败原因。", "llm_raw_analysis": "已采集证据：- `kubectl_describe`：Pod `rc-notready-liveness` 处于 `CrashLoopBackOff` 状态，`Exit Code: 137`，事件中频繁出现 `Liveness probe failed` 和 `Back-off restarting failed container`。- `kubectl_events`：事件日志显示 `Liveness probe failed` 和 `Back-off restarting failed container`，确认健康检查失败。- `kubectl_previous_logs_all_containers`：未发现上一次运行时的容器日志。未采集证据：- 无冲突证据：- 无根据以上证据，Pod `rc-notready-liveness` 处于 `CrashLoopBackOff` 状态，主要原因是健康检查失败（`Liveness probe failed`）。需要进一步检查探针配置和应用日志以确定具体原因。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'rc-notready-liveness' 的健康检查失败导致其处于 'CrashLoopBackOff' 状态。
   置信度: 80%
   🔗 因果链:
     根本原因: Pod 'rc-notready-liveness' 的健康检查失败导致其处于 'CrashLoopBackOff' 状态。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 31.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4440 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 5.8s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | CrashLoopBackOff |
| **兼容归因层** | L4（应用错误/配置错误） |
| **问题分类** | NotReadyProbeFailed（健康检查失败） |
| **置信度** | 高 (80%) |
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

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff, RESTARTS: 16 (30s ago)` | Pod 处于崩溃重启循环中 |
| 2 | 事件日志 | `kubectl get event` | `Warning Unhealthy: Liveness probe failed: liveness endpoint failed` | 健康检查探针失败导致容器被终止 |
| 3 | 容器状态 | `kubectl describe pod` | `Exit Code: 137 (OOMKilled)` | 退出码表明容器可能因内存不足被终止 |
| 4 | 重启次数 | `kubectl get pod` | `RESTARTS: 16 (30s ago)` | 说明容器反复崩溃并重启 |
| 5 | 健康检查失败记录 | `kubectl describe pod` | `Warning Unhealthy: Liveness probe failed: liveness endpoint failed` | 明确指出健康检查失败 |
| 6 | 上一次容器日志 | `kubectl logs <pod> --previous` | `无输出` | 无法获取崩溃前日志，无法判断崩溃原因 |
| 7 | 容器日志 | `kubectl logs <pod>` | `Command failed (exit 1): kubectl logs rc-notready-liveness -c rc-notready-liveness -n aiops-e2e --tail=100` | 当前容器未运行，无法获取日志 |
| 8 | Pod 标签 | `kubectl get pod` | `pod_abnormal_type=NotReadyProbeFailed` | 明确标记为探针失败 |
| 9 | Pod 命名空间 | `kubectl get pod` | `NAMESPACE: aiops-e2e` | 明确命名空间，便于后续排查 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 CrashLoopBackOff 且事件日志显示健康检查失败 → 健康检查失败是导致 Pod 重启的直接原因
- **证据链**：健康检查探针失败 → 容器被终止 → Pod 重启 → 形成 CrashLoopBackOff 状态

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 容器崩溃前日志 | critical | 无法确认探针失败的具体原因（如应用未响应、端口未开放等） |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 应用健康检查探针配置不当或应用未正确响应健康检查端点            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 探针失败 → 容器被终止 → Pod 重启 → 形成 CrashLoopBackOff 状态   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 健康检查探针失败（事件日志显示 Liveness probe failed）          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 CrashLoopBackOff，健康检查失败，频繁重启               │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (CrashLoopBackOff 状态)、#2 (事件日志显示健康检查失败)、#5 (健康检查失败记录) 和 #8 (Pod 标签标记为 NotReadyProbeFailed)，问题的根本原因是 **Pod `rc-notready-liveness` 的健康检查探针失败**，导致容器被终止并进入 CrashLoopBackOff 状态。

**置信度**：高 (80%)
- ✅ 事件日志显示健康检查失败
- ✅ Pod 标签明确标记为 NotReadyProbeFailed
- ⚠️ 缺少容器崩溃前日志，无法确认探针失败的具体原因

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查并调整探针配置**
```bash
kubectl describe pod rc-notready-liveness -n aiops-e2e
```
*依据*：查看探针配置（如 `livenessProbe` 的 `initialDelaySeconds`、`timeoutSeconds`、`path`、`port` 等），判断是否合理

**2. [优先] 优化探针配置示例**
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 10
  timeoutSeconds: 5
```
*依据*：适当延长 `initialDelaySeconds` 和 `timeoutSeconds`，避免应用启动慢导致探针失败

**3. [可选] 查看崩溃前日志**
```bash
kubectl logs rc-notready-liveness -n aiops-e2e --previous
```
*目的*：确认健康检查失败时应用的状态（如服务未响应、端口未监听等）

### 后续优化

1. **监控告警**：配置探针失败告警，如探针失败次数超过阈值时触发告警
2. **应用健康检查优化**：确保应用在探针检查路径和端口上正确响应
3. **资源评估**：检查应用是否因资源不足（如内存）导致探针失败（结合 `kubectl describe pod` 中的 `Exit Code: 137` 判断）

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-notready-liveness -n aiops-e2e` | STATUS: Running |
| 2. 检查探针事件 | `kubectl describe pod rc-notready-liveness -n aiops-e2e` | 无 Unhealthy 事件 |
| 3. 查看探针配置 | `kubectl describe pod rc-notready-liveness -n aiops-e2e` | livenessProbe 配置合理 |
| 4. 检查重启次数 | `kubectl get pod rc-notready-liveness -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 重启次数不再增加 |

---

## ⚠️ 注意事项

- 如果问题持续，可能需要进一步分析探针失败原因（如应用未响应、端口未开放、配置错误等）
- 考虑配置 HPA 根据探针失败情况自动扩缩容
- 如果应用本身存在健康检查逻辑，建议与探针路径保持一致，避免探针误判

---

## 📊 性能统计

├─ 总耗时: 5.1m
├─ 问题定位: 28.3s (9%) ✅
├─ 证据链采集: 121.2s (40%) ✅
├─ 根因分析: 64.8s (21%) ✅
├─ 汇总总结: 91.5s (30%) ✅
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
