======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: d552341c575644d3]

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
      📄 NAME                                      READY   STATUS             RESTARTS        AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-oomkilled-memory-limit-b6d999d-m8sl8   
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-oomkilled-memory-limit-b6d999d-m8sl8
namespace: aiops-e2e
creationTimestamp: 2026-05-15T04:24:12Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: No
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
4m19s (x347 over 79m)   Warning   BackOff   Pod/rc-oomkilled-memory-limit-b6d999d-m8sl8   Back-off restarting failed container app in pod rc-oomkilled-memory-limit-b6d999d-m8
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
node1   Ready    <none>   232d   v1.26.8   10.2.0.49     <
   💭 [问题定位] 调用工具: kubectl_describe
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 0.4s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[{'scenario': 'OOMKilled', 'probability': '高', 'reason': 'Pod 状态显示 CrashLoopBackOff，最近一次退出码为 137，表明容器因 OOMKilled 被终止。'}, {'scenario': '容器内存 limit 过低', 'probability': '高', 'reason': 'OOMKilled 通常是因为容器的内存 limit 设置过低，低于应用实际需求或历史峰值。'}, {'scenario': '应用内存泄漏', 'probability': '中', 'reason': '需进一步检查容器日志，查看是否有内存泄漏、GC overhead 或 heap space 等问题。'}]
   entities=[{"type": "Pod", "name": "rc-oomkilled-memory-limit-b6d999d-m8sl8", "namespace": "aiops-e2e"}]
   reasoning=当前环境中存在异常 Pod，其状态为 CrashLoopBackOff，重启次数为 20 次，最近一次退出码为 137，表明容器因 OOMKilled 被终止。根据分析文本及 runbook 的诊断规则，OOMKilled 且非 Evicted 的情况应归类为 L2 层级。
   layer_analysis={"layer": "L2", "derived_layer": "", "layers": [], "layer_name": "", "confidence": 0.5, "reasoning": "当前环境中存在异常 Pod，其状态为 CrashLoopBackOff，重启次数为 20 次，最近一次退出码为 137，表明容器因 OOMKilled 被终止。根据分析文本及 runbook 的诊断规则，OOMKilled 且非 Evicted 的情况应归类为 L2 层级。", "abnormal_pods": [{"name": "rc-oomkilled-memory-limit-b6d999d-m8sl8", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "OOMKilled", "status_category": "container_resource", "key_entities": [{"type": "Pod", "name": "rc-oomkilled-memory-limit-b6d999d-m8sl8", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "OOMKilled", "probability": "高", "reason": "Pod 状态显示 CrashLoopBackOff，最近一次退出码为 137，表明容器因 OOMKilled 被终止。"}, {"scenario": "容器内存 limit 过低", "probability": "高", "reason": "OOMKilled 通常是因为容器的内存 limit 设置过低，低于应用实际需求或历史峰值。"}, {"scenario": "应用内存泄漏", "probability": "中", "reason": "需进一步检查容器日志，查看是否有内存泄漏、GC overhead 或 heap space 等问题。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "OOMKilled", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-oomkilled-memory-limit-b6d999d-m8sl8"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器内存限制过低", "probability": "中", "reason": "需验证 Last State/ExitCode/resources"}, {"scenario": "应用内存使用异常", "probability": "中", "reason": "需验证日志和重启历史"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "OOMKilled", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-oomkilled-memory-limit-b6d999d-m8sl8"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器内存限制过低", "probability": "中", "reason": "需验证 Last State/ExitCode/resources"}, {"scenario": "应用内存使用异常", "probability": "中", "reason": "需验证日志和重启历史"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1, "OOMKilled": 1}, "total_abnormal": 2, "selected_rows": ["aiops-e2e     rc-oomkilled-memory-limit-b6d999d-m8sl8             0/1     CrashLoopBackOff   20 (90s ago)   78m     172.16.166.163   node1    <none>           <none>            app=rc-oomkilled-memory-limit,pod-template-hash=b6d999d,pod_abnormal_type=OOMKilled,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/d552341c575644d3/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/d552341c575644d3/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/d552341c575644d3/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L2
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
name: rc-oomkilled-memory-limit-b6d999d-m8sl8
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
Name:             rc-oomkilled-memory-limit-b6d999d-m8sl8
Labels:  
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
83s (x370 over 81m)   Warning   BackOff   Pod/rc-oomkilled-memory-limit-b6d999d-m8sl8   Back-off restarting failed container app in pod rc-oomkilled-memory-limit-b6d999d-m8sl
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [证据链采集] 已采集证据：
- `kubectl_describe`：确认 Pod 最近一次退出码为 137，且最后一次状态为 OOMKilled。
- `kubectl_events`：确认 Pod 因容器失败而持续重启（Back-off restarting failed container）。
- `kubectl_previous_logs`：未发现与 OOMKilled 相关的日志。

未采集证据：
- 无。

冲突证据：
- 无。
   ✅ [证据链采集] 完成 (1m 47.0s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan":[{"id":"evidence_pod_describe","description":"获取异常 Pod 的详细信息，验证其状态、重启原因和资源限制。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-oomkilled-memory-limit-b6d999d-m8sl8","namespace":"aiops-e2e"},"purpose":"验证 OOMKilled 的原因及容器资源限制配置","evidence_type":"pod_status","target_scope":"aiops-e2e/rc-oomkilled-memory-limit-b6d999d-m8sl8","acceptable_tools":[],"counts_for_completeness":true},{"id":"evidence_pod_events","description":"获取异常 Pod 的事件日志，验证是否包含 OOMKilled 或 BackOff 重启等信息。","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-oomkilled-memory-limit-b6d999d-m8sl8","tool_args":{"kind":"Pod","name":"rc-oomkilled-memory-limit-b6d999d-m8sl8","namespace":"aiops-e2e"},"purpose":"验证 Pod 是否因 OOMKilled 被终止","evidence_type":"pod_events","target_scope":"aiops-e2e/rc-oomkilled-memory-limit-b6d999d-m8sl8","acceptable_tools":[],"counts_for_completeness":true},{"id":"evidence_pod_previous_logs","description":"获取 Pod 的上一次容器日志，验证是否存在内存不足或 OOMKilled 相关的错误信息。","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e --previous","tool_args":{"kind":"Pod","name":"rc-oomkilled-memory-limit-b6d999d-m8sl8","namespace":"aiops-e2e"},"purpose":"验证容器是否存在内存不足或 OOMKilled 的日志记录","evidence_type":"pod_logs","target_scope":"aiops-e2e/rc-oomkilled-memory-limit-b6d999d-m8sl8","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-oomkilled-memory-limit-b6d999d-m8sl8\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\nName:             rc-oomkilled-memory-limit-b6d999d-m8sl8\nLabels:           app=rc-oomkilled-memory-limit\n                  pod_abnormal_type=OOMKilled\nAnnotations:      aiops.e2e/runbook: pod-oomkilled.md\nControlled By:  ReplicaSet/rc-oomkilled-memory-limit-b6d999d\n      Reason:       OOMKilled\n      Exit Code:    137\n  Warning  BackOff  80s (x370 over 81m)  kubelet  Back-off restarting failed container app in pod rc-oomkilled-memory-limit-b6d999d-m8sl8_aiops-e2e(837f1b14-9cec-4f6f-8f5b-c89f5b397ca5)\n      Reason:       CrashLoopBackOff\n                  cni.projectcalico.org/containerID: e6061e9e2466775a2aa864ee0168e2c2d1b8f1fb2a8e6d5ea5f738ef2425c284\n                  cni.projectcalico.org/podIP: 172.16.166.163/32\n                  cni.projectcalico.org/podIPs: 172.16.166.163/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n    Last State:     Terminated","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d552341c575644d3/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d552341c575644d3/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d552341c575644d3/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n83s (x370 over 81m)   Warning   BackOff   Pod/rc-oomkilled-memory-limit-b6d999d-m8sl8   Back-off restarting failed container app in pod rc-oomkilled-memory-limit-b6d999d-m8sl8_aiops-e2e(837f1b14-9cec-4f6f-8f5b-c89f5b397ca5)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d552341c575644d3/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d552341c575644d3/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d552341c575644d3/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d552341c575644d3/tools/003-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d552341c575644d3/tools/003-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d552341c575644d3/tools/003-evidence-kubectl_previous_logs.summary.txt"}],"llm_analysis":"已采集证据：\n- `kubectl_describe`：确认 Pod 最近一次退出码为 137，且最后一次状态为 OOMKilled。\n- `kubectl_events`：确认 Pod 因容器失败而持续重启（Back-off restarting failed container）。\n- `kubectl_previous_logs`：未发现与 OOMKilled 相关的日志。\n\n未采集证据：\n- 无。\n\n冲突证据：\n- 无。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 9/9 项，完整度 100%；实际执行工具 9 个，匹配计划 3 个，未规划证据 6 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":9,"environment_evidence_collected":9,"environment_evidence_completeness":1.0,"executed_tool_count":9,"matched_tool_count":3,"unplanned_tool_count":6,"evidence_inventory":[{"id":"evidence_pod_describe","description":"获取异常 Pod 的详细信息，验证其状态、重启原因和资源限制。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e","purpose":"验证 OOMKilled 的原因及容器资源限制配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"evidence_pod_events","description":"获取异常 Pod 的事件日志，验证是否包含 OOMKilled 或 BackOff 重启等信息。","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-oomkilled-memory-limit-b6d999d-m8sl8","purpose":"验证 Pod 是否因 OOMKilled 被终止","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"evidence_pod_previous_logs","description":"获取 Pod 的上一次容器日志，验证是否存在内存不足或 OOMKilled 相关的错误信息。","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e --previous","purpose":"验证容器是否存在内存不足或 OOMKilled 的日志记录","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | evidence_pod_... | critical | ✅ | kubectl_describe | 获取异常 Pod 的详细信息，验证其状态、重启原因和资源限制。 | `kubectl describe pod rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e` |
   | evidence_pod_... | important | ✅ | kubectl_events | 获取异常 Pod 的事件日志，验证是否包含 OOMKilled 或 BackOff 重启等信息。 | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-oomki...` |
   | evidence_pod_... | important | ✅ | kubectl_previous_logs | 获取 Pod 的上一次容器日志，验证是否存在内存不足或 OOMKilled 相关的错误信息。 | `kubectl logs rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e --previous` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (27.0s)
   📤 → 下游数据: root_cause=Pod rc-oomkilled-memory-limit-b6d999d-m8sl8 在命名空间 aiops-e2e 中因内存不足被 OOMKilled，导致其进入 CrashLoopBackOff 状态，并且已重启 20 次。
   confidence=80%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [{"tool": "kubectl_describe", "analysis": "kubectl_describe 显示 Pod 最近一次退出码为 137，最后一次状态为 OOMKilled，表明容器因内存不足被终止。"}, {"tool": "kubectl_events", "analysis": "kubectl_events 显示 Pod 因容器失败而持续重启，事件为 Back-off restarting failed container。"}, {"tool": "kubectl_previous_logs", "analysis": "kubectl_previous_logs 未发现与 OOMKilled 相关的日志。"}], "causal_chain": {}, "root_cause": "Pod rc-oomkilled-memory-limit-b6d999d-m8sl8 在命名空间 aiops-e2e 中因内存不足被 OOMKilled，导致其进入 CrashLoopBackOff 状态，并且已重启 20 次。", "root_cause_summary": "Pod rc-oomkilled-memory-limit-b6d999d-m8sl8 在命名空间 aiops-e2e 中因内存不足被 OOMKilled，导致其进入 CrashLoopBackOff 状态，并且已重启 20 次。", "confidence": 0.8, "confidence_reason": "有直接证据表明容器因 OOMKilled 被终止，但缺少容器日志以进一步确认内存使用情况。", "primary_runbooks": ["pod-oomkilled.md"], "alternative_causes": [], "limitations": "缺少容器日志以进一步确认内存使用情况。", "llm_raw_analysis": "kubectl_describe 显示 Pod 最近一次退出码为 137，最后一次状态为 OOMKilled，表明容器因内存不足被终止。kubectl_events 显示 Pod 因容器失败而持续重启，事件为 Back-off restarting failed container。kubectl_previous_logs 未发现与 OOMKilled 相关的日志。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-oomkilled-memory-limit-b6d999d-m8sl8 在命名空间 aiops-e2e 中因内存不足被 OOMKilled，导致其进入 CrashLoopBackOff 状态，并且已重启 20 次。
   置信度: 80%

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
   ✅ [汇总总结] 完成 (2m 35.4s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4350 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 49.9s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | CrashLoopBackOff，最近一次退出码为 137（OOMKilled） |
| **兼容归因层** | L2 - 容器资源类问题 |
| **问题分类** | OOMKilled（容器内存不足被终止） |
| **置信度** | 高 (80%) |
| **证据完整度** | 3/3 (100%) |

---

## 🔍 现象描述

**用户报告**：  
> 我的集群有什么问题？

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | rc-oomkilled-memory-limit-b6d999d-m8sl8 |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | OOMKilled, Exit Code: 137, 重启次数: 20 次 |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff, RESTARTS: 20, EXIT CODE: 137` | Pod 频繁重启，最后一次退出码为 137，表明容器被 OOMKilled |
| 2 | Pod 事件 | `kubectl describe pod` | `Reason: OOMKilled` | 容器因内存不足被终止 |
| 3 | Pod 事件日志 | `kubectl get events` | `Warning BackOff Pod/rc-oomkilled-memory-limit-b6d999d-m8sl8 Back-off restarting failed container app` | Pod 重启失败，事件中多次记录重启失败 |
| 4 | 容器资源配置 | `kubectl get pod -o yaml` | `memory limit: 未显式设置` | 缺乏明确的资源限制配置 |
| 5 | 上一次容器日志 | `kubectl logs <pod> --previous` | `无输出` | 无日志内容，无法进一步确认内存增长原因 |

### 证据关联分析

- **证据 #1 + #2 印证**：Exit Code 137 + OOMKilled → 容器因内存不足被终止。
- **证据链**：
  - Pod 状态为 CrashLoopBackOff，重启次数为 20 次。
  - 最近一次容器退出码为 137，表明容器被 OOMKilled。
  - 无容器日志输出，无法确认是否为内存泄漏或突发峰值。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 容器崩溃前日志 | critical | 无法确认内存增长原因，无法判断是否为内存泄漏或配置不足 |
| Prometheus 内存使用监控数据 | important | 无法确认容器内存使用历史趋势和峰值 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 应用实际内存需求超过当前容器资源限制，导致容器被 OOMKilled        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器内存使用达到 cgroup 限制 → 被 OOM Killer 终止               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器被 OOM Killer 终止（Exit Code 137）                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CrashLoopBackOff，持续重启                           │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Exit Code 137, OOMKilled) 和证据 #2 (Pod 事件记录 OOMKilled)，问题的根本原因是 **容器内存不足导致被 OOM Killer 终止**，Pod 因此进入 CrashLoopBackOff 状态并频繁重启。

**置信度**：高 (80%)

- ✅ Exit Code 137 明确指向 OOMKilled
- ✅ Pod 事件记录中多次出现 "Back-off restarting failed container"
- ⚠️ 缺少崩溃前日志，无法确认内存增长原因

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 增加容器内存限制**
```bash
kubectl set resources deployment/<name> -n aiops-e2e --limits=memory=512Mi
```
*依据*：当前容器内存限制未显式设置或过低，建议设置为 512Mi 并观察是否仍被 OOMKilled。

**2. [可选] 查看崩溃前日志**
```bash
kubectl logs rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e --previous | tail -100
```
*目的*：确认容器崩溃前是否有内存泄漏、GC overhead 等异常。

**3. [可选] 配置资源请求和限制**
```yaml
resources:
  limits:
    memory: 1Gi
  requests:
    memory: 512Mi
```
*目的*：确保容器在内存受限时优先被调度，避免资源争抢。

### 后续优化

1. **监控告警**：
   - 配置 Prometheus 告警，监控 `container_memory_usage_bytes`，当超过 80% 时预警。
   - 配置 HPA（Horizontal Pod Autoscaler）根据内存使用自动扩缩容。

2. **资源评估**：
   - 使用 `kubectl describe pod` 或 Prometheus 检查历史资源使用情况。
   - 考虑使用 `kubectl top pod`（若启用 Metrics Server）监控当前内存使用。

3. **应用优化**：
   - 如果是 Java 应用，检查 JVM 参数是否合理，是否存在内存泄漏。
   - 优化代码逻辑，减少内存占用。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 重启次数不再增加 |
| 3. 监控内存使用 | Prometheus: `container_memory_usage_bytes{pod="rc-oomkilled-memory-limit-b6d999d-m8sl8", namespace="aiops-e2e"}` | 内存使用 < 80% of limit |

---

## ⚠️ 注意事项

- 如果问题持续，建议进一步分析应用内存使用情况，确认是否存在内存泄漏。
- 考虑配置 HPA（Horizontal Pod Autoscaler）根据内存自动扩缩容，避免单个 Pod 过载。
- 如果使用的是 Java 应用，建议检查 JVM 参数配置是否合理，例如堆内存大小、GC 策略等。

---

## 📊 性能统计

├─ 总耗时: 5.8m
├─ 问题定位: 60.4s (17%) ✅
├─ 证据链采集: 107.0s (31%) ✅
├─ 根因分析: 27.0s (8%) ✅
├─ 汇总总结: 155.4s (44%) ✅
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
