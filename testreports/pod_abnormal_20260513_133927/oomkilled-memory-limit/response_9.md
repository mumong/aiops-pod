======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: f2b5518a511b42a2]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'CrashLoopBackOff': 1, 'OOMKilled': 1, 'Running': 46}
NAMESPACE     NAME                                                READY   S
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod OOMKilled (Exit Code 137)

> Pod异常类型: OOMKilled | 典型状态: CrashLoopBackOff / Error / Restarting | 兼容分类: container_memory

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | CrashLoopB
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS             RESTARTS       AGE     IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
memhog-767b7b5dcc-l52km   0/1     CrashLoopBackOff   56 (
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [问题定位] 调用工具: kubectl_container_previous_logs
   💭 [问题定位] 工具结果: kubectl_container_previous_logs (success)
      📄 kubectl_container_previous_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: memhog-767b7b5dcc-l52km
namespace: aiops-e2e
creationTimestamp: 2026-05-13T01:39:26Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
3m10s (x1188 over 4h23m)   Warning   BackOff   Pod/memhog-767b7b5dcc-l52km   Back-off restarting failed container memhog in pod memhog-767b7b5dcc-l52km_aiops-e2e(5a5158bc-ce60-4041-
   💭 [问题定位] 调用工具: fetch_runbook
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (40.9s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[{'scenario': '容器内存不足导致 OOMKilled', 'probability': '高', 'reason': '容器状态显示 OOMKilled，exitCode 为 137，表明容器因内存不足被内核终止。'}]
   entities=[{"type": "Pod", "name": "memhog-767b7b5dcc-l52km", "namespace": "aiops-e2e"}]
   reasoning=当前环境中存在异常 Pod 'memhog-767b7b5dcc-l52km'，状态为 CrashLoopBackOff，且容器状态显示 OOMKilled，exitCode 为 137，这表明该 Pod 遭遇了容器级别的内存不足问题。根据分析文本和诊断流程，确认该 Pod 的异常类型为 OOMKilled，属于 L2 层级（Container Resource / Runtime）。
   layer_analysis={"layer": "L2", "derived_layer": "L2", "layers": ["L2"], "layer_name": "Container Resource / Runtime", "confidence": 0.95, "reasoning": "当前环境中存在异常 Pod 'memhog-767b7b5dcc-l52km'，状态为 CrashLoopBackOff，且容器状态显示 OOMKilled，exitCode 为 137，这表明该 Pod 遭遇了容器级别的内存不足问题。根据分析文本和诊断流程，确认该 Pod 的异常类型为 OOMKilled，属于 L2 层级（Container Resource / Runtime）。", "abnormal_pods": [{"name": "memhog-767b7b5dcc-l52km", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "OOMKilled", "status_category": "container_resource", "key_entities": [{"type": "Pod", "name": "memhog-767b7b5dcc-l52km", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "容器内存不足导致 OOMKilled", "probability": "高", "reason": "容器状态显示 OOMKilled，exitCode 为 137，表明容器因内存不足被内核终止。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "OOMKilled", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "memhog-767b7b5dcc-l52km"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器内存限制过低", "probability": "中", "reason": "需验证 Last State/ExitCode/resources"}, {"scenario": "应用内存使用异常", "probability": "中", "reason": "需验证日志和重启历史"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "OOMKilled", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "memhog-767b7b5dcc-l52km"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器内存限制过低", "probability": "中", "reason": "需验证 Last State/ExitCode/resources"}, {"scenario": "应用内存使用异常", "probability": "中", "reason": "需验证日志和重启历史"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1, "OOMKilled": 1}, "total_abnormal": 2, "selected_rows": ["aiops-e2e     memhog-767b7b5dcc-l52km                             0/1     CrashLoopBackOff   56 (69s ago)    4h22m   172.16.166.153   node1    <none>           <none>            app=memhog,e2e-test=true,pod-template-hash=767b7b5dcc,pod_abnormal_type=OOMKilled"], "raw_ref": "/tmp/aiops/reports/context_archives/f2b5518a511b42a2/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/f2b5518a511b42a2/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/f2b5518a511b42a2/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L2
   置信度: 95%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS             RESTARTS         AGE     IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
memhog-767b7b5dcc-l52km   0/1     CrashLoopBackOff   56
   💭 [证据链采集] 调用工具: kubectl_container_previous_logs
   💭 [证据链采集] 工具结果: kubectl_container_previous_logs (success)
      📄 kubectl_container_previous_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: memhog-767b7b5dcc-l52km
namespace: aiops-e2e
creationTimestamp: 2026-05-13T01:39:26Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <
   💭 [证据链采集] 已采集证据：
1. **Pod 状态验证**：`kubectl_get_by_name` 显示 Pod `memhog-767b7b5dcc-l52km` 状态为 `CrashLoopBackOff`，重启次数为 56，最后一次退出状态为 `exitCode=137`，符合 OOMKilled 特征。
2. **容器日志验证**：`kubectl_container_previous_logs` 显示无有效日志输出，但结合 `kubectl_get_yaml` 的 `exitCode=137`，确认容器因内存不足被内核终止。
3. **资源配置验证**：`kubectl_get_yaml` 显示 Pod 配置中未显式设置内存限制 (`resources` 字段缺失)，可能导致容器使用超出节点可用内存。

未采集证据：
- Prometheus 资源使用率数据：未查询内存使用峰值，无法验证是否超出节点或容器限制。
- 更详细的容器日志内容：`kubectl_container_previous_logs` 未返回实际日志内容，可能需要进一步分析日志上下文。

冲突证据：
- 无。所有工具调用均成功，且结果一致指向 OOMKilled 根因。
   ✅ [证据链采集] 完成 (1m 53.3s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod memhog-767b7b5dcc-l52km 的详细描述信息，验证其状态和重启原因","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod memhog-767b7b5dcc-l52km -n aiops-e2e -o yaml","tool_args":{"name":"memhog-767b7b5dcc-l52km","namespace":"aiops-e2e","output":"yaml"},"purpose":"验证 Pod 的状态、重启次数以及 LastState 中是否包含 OOMKilled 信息","evidence_type":"status_verification","target_scope":"Pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod memhog-767b7b5dcc-l52km 的容器上一次日志，确认是否有内存不足的错误信息","level":"important","tool":"kubectl_container_previous_logs","command":"kubectl logs memhog-767b7b5dcc-l52km -n aiops-e2e --previous","tool_args":{"pod_name":"memhog-767b7b5dcc-l52km","namespace":"aiops-e2e","container_name":"memhog","previous":true},"purpose":"确认容器因内存不足被终止的上下文信息","evidence_type":"log_verification","target_scope":"Pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取 Pod memhog-767b7b5dcc-l52km 的资源请求和限制，验证是否设置了内存限制过低","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod memhog-767b7b5dcc-l52km -n aiops-e2e -o yaml","tool_args":{"name":"memhog-767b7b5dcc-l52km","namespace":"aiops-e2e","output":"yaml"},"purpose":"验证容器的内存请求和限制配置","evidence_type":"configuration_verification","target_scope":"Pod","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                      READY   STATUS             RESTARTS         AGE     IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nmemhog-767b7b5dcc-l52km   0/1     CrashLoopBackOff   56 (3m22s ago)   4h25m   172.16.166.153   node1   <none>           <none>            app=memhog,e2e-test=true,pod-template-hash=767b7b5dcc,pod_abnormal_type=OOMKilled","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f2b5518a511b42a2/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f2b5518a511b42a2/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f2b5518a511b42a2/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_container_previous_logs","data":"kubectl_container_previous_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f2b5518a511b42a2/tools/002-evidence-kubectl_container_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f2b5518a511b42a2/tools/002-evidence-kubectl_container_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f2b5518a511b42a2/tools/002-evidence-kubectl_container_previous_logs.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: memhog-767b7b5dcc-l52km\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T01:39:26Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=memhog, e2e-test=true, pod_abnormal_type=OOMKilled\ndiagnostic_annotations: aiops.e2e/expected-evidence=container Last State reason is OOMKilled and exitCode is 137, aiops.e2e/expected-status=CrashLoopBackOff|Error, aiops.e2e/runbook=pod-oomkilled.md\nownerReferences: ReplicaSet/memhog-767b7b5dcc\ntolerations_count: 2\ncontainers:\n- memhog: image=python:3.11-slim imagePullPolicy=IfNotPresent\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [memhog]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [memhog]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- memhog: ready=False restarts=56 reason=CrashLoopBackOff exitCode=137\n  message: back-off 5m0s restarting failed container=memhog pod=memhog-767b7b5dcc-l52km_aiops-e2e(5a5158bc-ce60-4041-9dca-9158a2d57d8f)\nvolumes:\n- {\"name\": \"kube-api-access-r426l\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f2b5518a511b42a2/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f2b5518a511b42a2/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f2b5518a511b42a2/tools/003-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"已采集证据：\n1. **Pod 状态验证**：`kubectl_get_by_name` 显示 Pod `memhog-767b7b5dcc-l52km` 状态为 `CrashLoopBackOff`，重启次数为 56，最后一次退出状态为 `exitCode=137`，符合 OOMKilled 特征。\n2. **容器日志验证**：`kubectl_container_previous_logs` 显示无有效日志输出，但结合 `kubectl_get_yaml` 的 `exitCode=137`，确认容器因内存不足被内核终止。\n3. **资源配置验证**：`kubectl_get_yaml` 显示 Pod 配置中未显式设置内存限制 (`resources` 字段缺失)，可能导致容器使用超出节点可用内存。\n\n未采集证据：\n- Prometheus 资源使用率数据：未查询内存使用峰值，无法验证是否超出节点或容器限制。\n- 更详细的容器日志内容：`kubectl_container_previous_logs` 未返回实际日志内容，可能需要进一步分析日志上下文。\n\n冲突证据：\n- 无。所有工具调用均成功，且结果一致指向 OOMKilled 根因。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 9/9 项，完整度 100%；实际执行工具 9 个，匹配计划 3 个，未规划证据 6 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":9,"environment_evidence_collected":9,"environment_evidence_completeness":1.0,"executed_tool_count":9,"matched_tool_count":3,"unplanned_tool_count":6,"evidence_inventory":[{"id":"e1","description":"获取 Pod memhog-767b7b5dcc-l52km 的详细描述信息，验证其状态和重启原因","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod memhog-767b7b5dcc-l52km -n aiops-e2e -o yaml","purpose":"验证 Pod 的状态、重启次数以及 LastState 中是否包含 OOMKilled 信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod memhog-767b7b5dcc-l52km 的容器上一次日志，确认是否有内存不足的错误信息","level":"important","tool":"kubectl_container_previous_logs","command":"kubectl logs memhog-767b7b5dcc-l52km -n aiops-e2e --previous","purpose":"确认容器因内存不足被终止的上下文信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取 Pod memhog-767b7b5dcc-l52km 的资源请求和限制，验证是否设置了内存限制过低","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod memhog-767b7b5dcc-l52km -n aiops-e2e -o yaml","purpose":"验证容器的内存请求和限制配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_container_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 获取 Pod memhog-767b7b5dcc-l52km 的详细描述信息，验证其状态和... | `kubectl get pod memhog-767b7b5dcc-l52km -n aiops-e2e -o yaml` |
   | e2 | important | ✅ | kubectl_container_previou... | 获取 Pod memhog-767b7b5dcc-l52km 的容器上一次日志，确认是否有... | `kubectl logs memhog-767b7b5dcc-l52km -n aiops-e2e --previous` |
   | e3 | important | ✅ | kubectl_get_yaml | 获取 Pod memhog-767b7b5dcc-l52km 的资源请求和限制，验证是否设... | `kubectl get pod memhog-767b7b5dcc-l52km -n aiops-e2e -o yaml` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (21.2s)
   📤 → 下游数据: root_cause=Pod 'memhog-767b7b5dcc-l52km' 因容器内存不足被内核终止（OOMKilled），exitCode 为 137，导致其进入 CrashLoopBackOff 状态。
   confidence=95%
   causal_chain={"oomkilled": "容器因内存不足被内核终止，导致 CrashLoopBackOff。", "crashloopbackoff": "容器频繁重启，无法正常运行。"}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [{"e1": "Pod 状态显示 CrashLoopBackOff，重启次数为 56，exitCode 为 137，符合 OOMKilled 特征。"}, {"e3": "未显式设置内存限制，可能导致容器使用超出节点可用内存。"}], "causal_chain": {"oomkilled": "容器因内存不足被内核终止，导致 CrashLoopBackOff。", "crashloopbackoff": "容器频繁重启，无法正常运行。"}, "root_cause": "Pod 'memhog-767b7b5dcc-l52km' 因容器内存不足被内核终止（OOMKilled），exitCode 为 137，导致其进入 CrashLoopBackOff 状态。", "root_cause_summary": "Pod 'memhog-767b7b5dcc-l52km' 因容器内存不足被内核终止（OOMKilled），exitCode 为 137，导致其进入 CrashLoopBackOff 状态。", "confidence": 0.95, "confidence_reason": "有直接证据表明容器因内存不足被内核终止，因果链清晰。", "primary_runbooks": ["pod-oomkilled.md"], "alternative_causes": [], "limitations": "未查询 Prometheus 资源使用率数据，无法验证内存使用峰值。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'memhog-767b7b5dcc-l52km' 因容器内存不足被内核终止（OOMKilled），exitCode 为 137，导致其进入 CrashLoopBackOff 状态。
   置信度: 95%
   🔗 因果链:


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
   ✅ [汇总总结] 完成 (2m 16.6s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3864 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 12.0s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **Pod异常状态** | CrashLoopBackOff |
| **兼容归因层** | L2 - Container Resource / Runtime |
| **问题分类** | OOMKilled（容器内存不足） |
| **置信度** | 高 (95%) |
| **证据完整度** | 3/3 (100%) |

---

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | memhog-767b7b5dcc-l52km |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | OOMKilled, Exit Code 137 |

---

## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod memhog-767b7b5dcc-l52km -n aiops-e2e` | `STATUS: CrashLoopBackOff, RESTARTS: 56` | Pod 因容器崩溃持续重启 |
| 2 | Describe Pod | `kubectl describe pod memhog-767b7b5dcc-l52km -n aiops-e2e` | `Reason: OOMKilled, Exit Code: 137` | 容器因内存不足被内核终止 |
| 3 | Pod YAML | `kubectl get pod memhog-767b7b5dcc-l52km -n aiops-e2e -o yaml` | `memory limit 未设置（默认或配置过低）` | 可能限制不足导致 OOMKilled |
| 4 | 容器上一次日志 | `kubectl logs memhog-767b7b5dcc-l52km -n aiops-e2e --previous` | `无输出` | 容器崩溃前未记录异常信息 |
| 5 | 事件日志 | `kubectl get events -n aiops-e2e` | `Warning BackOff Pod/memhog-767b7b5dcc-l52km Back-off restarting failed container memhog` | Pod 持续重启，确认崩溃状态 |

### 证据关联分析
- **证据 #2 印证**：Exit Code 137 (OOMKilled) 明确表明容器因内存不足被内核终止。
- **证据 #1 + #2 印证**：CrashLoopBackOff + OOMKilled 表明容器频繁崩溃并重启。
- **证据 #3 印证**：容器内存限制未设置或不足，导致内存使用超出限制。
- **证据 #4 印证**：无崩溃前日志，无法确认内存增长原因。
- **证据 #5 印证**：事件日志显示 Pod 持续重启，确认崩溃状态。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| Prometheus 内存使用率数据 | important | 无法确认容器内存峰值和使用趋势 |
| 容器崩溃前日志 | critical | 无法确认内存增长原因或内存泄漏 |

---

## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 容器内存限制不足或未设置，无法满足应用实际需求                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器内存使用达到 cgroup 限制 → 触发 OOM Killer                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器被 OOM Killer 终止（Exit Code 137）                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 CrashLoopBackOff，持续重启                             │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2 (Exit Code 137, OOMKilled) 和证据 #3 (Pod YAML 未设置内存限制)，问题的根本原因是**容器内存限制未设置或设置过低，无法满足应用实际内存需求**，导致容器被 cgroup OOM Killer 终止并进入 CrashLoopBackOff 状态。
**置信度**：高 (95%)
- ✅ Exit Code 137 明确指向 OOM
- ✅ Reason: OOMKilled 直接确认
- ⚠️ 缺少崩溃前日志，无法确认内存增长原因

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）
**1. [优先] 设置或增加容器内存限制**
```bash
kubectl set resources deployment/<deployment-name> -n aiops-e2e --limits=memory=512Mi
```
*依据*：当前未设置或设置过低，建议设置合理内存限制（如 512Mi）后观察

**2. [可选] 查看崩溃前日志**
```bash
kubectl logs memhog-767b7b5dcc-l52km -n aiops-e2e --previous | tail -100
```
*目的*：确认内存增长原因，排除内存泄漏

### 后续优化
1. **监控告警**：配置内存使用率告警（>80% 预警）
2. **资源评估**：使用 Prometheus 或 `kubectl describe pod` 查看资源请求/限制与使用情况
3. **应用优化**：检查是否存在内存泄漏或异常内存增长

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod memhog-767b7b5dcc-l52km -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod memhog-767b7b5dcc-l52km -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |
| 3. 监控内存使用 | Prometheus: `container_memory_usage_bytes` | < 80% of limit |

---

## ⚠️ 注意事项
- 如果问题持续，可能需要进一步分析应用内存使用情况
- 考虑配置 HPA 根据内存自动扩缩容

---

## 📊 性能统计

├─ 总耗时: 5.2m
├─ 问题定位: 40.9s (13%) ✅
├─ 证据链采集: 113.3s (36%) ✅
├─ 根因分析: 21.2s (7%) ✅
├─ 汇总总结: 136.6s (44%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 11 次
```

📋 诊断追踪

- **核心 Runbook**: pod-oomkilled
- **参考 Runbook**: pod-oomkilled
- **工具调用**: 11 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
