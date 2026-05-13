======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: f898ae2db8c240b2]

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
      📄 NAME                      READY   STATUS             RESTARTS        AGE     IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
memhog-767b7b5dcc-l52km   0/1     CrashLoopBackOff   54 
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
3m18s (x1144 over 4h13m)   Warning   BackOff   Pod/memhog-767b7b5dcc-l52km   Back-off restarting failed container memhog in pod memhog-767b7b5dcc-l52km_aiops-e2e(5a5158bc-ce60-4041-
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
name: memhog-767b7b5dcc-l52km
namespace: aiops-e2e
creationTimestamp: 2026-05-13T01:39:26Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <
   💭 [问题定位] 调用工具: kubectl_container_previous_logs
   💭 [问题定位] 工具结果: kubectl_container_previous_logs (success)
      📄 kubectl_container_previous_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [问题定位] 调用工具: kubectl_get_yaml
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 31.5s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[{'scenario': '容器内存不足导致 OOMKilled', 'probability': '高', 'reason': 'Pod 明确标记为 OOMKilled，且 exitCode=137，符合内存不足导致的崩溃'}]
   entities=[{"type": "Pod", "name": "memhog-767b7b5dcc-l52km", "namespace": "aiops-e2e"}]
   reasoning=当前环境中的活跃异常对象是 Pod 'memhog-767b7b5dcc-l52km'，其状态为 'CrashLoopBackOff'，且 pod_abnormal_type 明确标记为 'OOMKilled'。根据异常类型归因规则，OOMKilled 且非 Evicted 的 Pod 应归类为 L2。此外，该 Pod 的 containerStatuses 显示 exitCode=137，符合 OOMKilled 的特征。因此，当前集群存在 L2 层级的异常。
   layer_analysis={"layer": "L2", "derived_layer": "L2", "layers": ["L2"], "layer_name": "L2", "confidence": 0.95, "reasoning": "当前环境中的活跃异常对象是 Pod 'memhog-767b7b5dcc-l52km'，其状态为 'CrashLoopBackOff'，且 pod_abnormal_type 明确标记为 'OOMKilled'。根据异常类型归因规则，OOMKilled 且非 Evicted 的 Pod 应归类为 L2。此外，该 Pod 的 containerStatuses 显示 exitCode=137，符合 OOMKilled 的特征。因此，当前集群存在 L2 层级的异常。", "abnormal_pods": [{"name": "memhog-767b7b5dcc-l52km", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "OOMKilled", "status_category": "container_resource", "key_entities": [{"type": "Pod", "name": "memhog-767b7b5dcc-l52km", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "容器内存不足导致 OOMKilled", "probability": "高", "reason": "Pod 明确标记为 OOMKilled，且 exitCode=137，符合内存不足导致的崩溃"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "OOMKilled", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "memhog-767b7b5dcc-l52km"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器内存限制过低", "probability": "中", "reason": "需验证 Last State/ExitCode/resources"}, {"scenario": "应用内存使用异常", "probability": "中", "reason": "需验证日志和重启历史"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "OOMKilled", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "memhog-767b7b5dcc-l52km"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器内存限制过低", "probability": "中", "reason": "需验证 Last State/ExitCode/resources"}, {"scenario": "应用内存使用异常", "probability": "中", "reason": "需验证日志和重启历史"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1, "OOMKilled": 1}, "total_abnormal": 2, "selected_rows": ["aiops-e2e     memhog-767b7b5dcc-l52km                             0/1     CrashLoopBackOff   54 (105s ago)   4h13m   172.16.166.153   node1    <none>           <none>            app=memhog,e2e-test=true,pod-template-hash=767b7b5dcc,pod_abnormal_type=OOMKilled"], "raw_ref": "/tmp/aiops/reports/context_archives/f898ae2db8c240b2/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/f898ae2db8c240b2/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/f898ae2db8c240b2/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
memhog-767b7b5dcc-l52km   0/1     CrashLoopBackOff   54
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: memhog-767b7b5dcc-l52km
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键状态/事件:
                  pod_abnormal_type=OOMKilled
Annotations:      aiops.e2e/expecte
   💭 [证据链采集] 已采集证据:
1. `kubectl_get_by_name` 验证 Pod 状态为 CrashLoopBackOff，且标签中包含 `pod_abnormal_type=OOMKilled`。
2. `kubectl_previous_logs` 未返回有效日志，但符合 OOMKilled 的特征（无日志输出）。
3. `kubectl_describe` 显示容器最后一次状态为 OOMKilled，Exit Code 为 137，符合内存不足导致的崩溃。

未采集证据:
- 无

冲突证据:
- 无

结论：当前 Pod `memhog-767b7b5dcc-l52km` 明确标记为 OOMKilled，Exit Code 为 137，符合内存不足导致的崩溃。建议检查该 Pod 的内存资源配置，确认是否内存限制过低或应用内存使用异常。
   ✅ [证据链采集] 完成 (2m 0.0s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod memhog-767b7b5dcc-l52km 的详细信息，验证其状态和 OOMKilled 原因","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod memhog-767b7b5dcc-l52km -n aiops-e2e -o json","tool_args":{"name":"memhog-767b7b5dcc-l52km","namespace":"aiops-e2e"},"purpose":"验证 Pod 是否处于 CrashLoopBackOff 状态，并确认其 OOMKilled 原因","evidence_type":"pod_status","target_scope":"Pod","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod memhog-767b7b5dcc-l52km 的日志，检查是否有关于内存不足的错误信息","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs memhog-767b7b5dcc-l52km -n aiops-e2e --previous","tool_args":{"name":"memhog-767b7b5dcc-l52km","namespace":"aiops-e2e"},"purpose":"检查 Pod 是否因内存不足导致 OOMKilled","evidence_type":"pod_logs","target_scope":"Pod","acceptable_tools":["kubectl_previous_logs"],"counts_for_completeness":true},{"id":"e3","description":"获取 Pod memhog-767b7b5dcc-l52km 的描述信息，验证其容器状态和资源限制配置","level":"important","tool":"kubectl_describe","command":"kubectl describe pod memhog-767b7b5dcc-l52km -n aiops-e2e","tool_args":{"name":"memhog-767b7b5dcc-l52km","namespace":"aiops-e2e"},"purpose":"验证容器状态、资源限制配置以及 OOMKilled 事件","evidence_type":"pod_description","target_scope":"Pod","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                      READY   STATUS             RESTARTS         AGE     IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nmemhog-767b7b5dcc-l52km   0/1     CrashLoopBackOff   54 (4m58s ago)   4h16m   172.16.166.153   node1   <none>           <none>            app=memhog,e2e-test=true,pod-template-hash=767b7b5dcc,pod_abnormal_type=OOMKilled","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f898ae2db8c240b2/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f898ae2db8c240b2/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f898ae2db8c240b2/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f898ae2db8c240b2/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f898ae2db8c240b2/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f898ae2db8c240b2/tools/002-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: memhog-767b7b5dcc-l52km\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键状态/事件:\n                  pod_abnormal_type=OOMKilled\nAnnotations:      aiops.e2e/expected-evidence: container Last State reason is OOMKilled and exitCode is 137\n                  aiops.e2e/expected-status: CrashLoopBackOff|Error\n    State:          Waiting\n      Reason:       CrashLoopBackOff\n    Last State:     Terminated\n      Reason:       OOMKilled\n      Exit Code:    137\n  Warning  BackOff  88s (x1166 over 4h16m)  kubelet  Back-off restarting failed container memhog in pod memhog-767b7b5dcc-l52km_aiops-e2e(5a5158bc-ce60-4041-9dca-9158a2d57d8f)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f898ae2db8c240b2/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f898ae2db8c240b2/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f898ae2db8c240b2/tools/003-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"已采集证据:\n1. `kubectl_get_by_name` 验证 Pod 状态为 CrashLoopBackOff，且标签中包含 `pod_abnormal_type=OOMKilled`。\n2. `kubectl_previous_logs` 未返回有效日志，但符合 OOMKilled 的特征（无日志输出）。\n3. `kubectl_describe` 显示容器最后一次状态为 OOMKilled，Exit Code 为 137，符合内存不足导致的崩溃。\n\n未采集证据:\n- 无\n\n冲突证据:\n- 无\n\n结论：当前 Pod `memhog-767b7b5dcc-l52km` 明确标记为 OOMKilled，Exit Code 为 137，符合内存不足导致的崩溃。建议检查该 Pod 的内存资源配置，确认是否内存限制过低或应用内存使用异常。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 9/9 项，完整度 100%；实际执行工具 9 个，匹配计划 3 个，未规划证据 6 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":9,"environment_evidence_collected":9,"environment_evidence_completeness":1.0,"executed_tool_count":9,"matched_tool_count":3,"unplanned_tool_count":6,"evidence_inventory":[{"id":"e1","description":"获取 Pod memhog-767b7b5dcc-l52km 的详细信息，验证其状态和 OOMKilled 原因","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod memhog-767b7b5dcc-l52km -n aiops-e2e -o json","purpose":"验证 Pod 是否处于 CrashLoopBackOff 状态，并确认其 OOMKilled 原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod memhog-767b7b5dcc-l52km 的日志，检查是否有关于内存不足的错误信息","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs memhog-767b7b5dcc-l52km -n aiops-e2e --previous","purpose":"检查 Pod 是否因内存不足导致 OOMKilled","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取 Pod memhog-767b7b5dcc-l52km 的描述信息，验证其容器状态和资源限制配置","level":"important","tool":"kubectl_describe","command":"kubectl describe pod memhog-767b7b5dcc-l52km -n aiops-e2e","purpose":"验证容器状态、资源限制配置以及 OOMKilled 事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_container_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 获取 Pod memhog-767b7b5dcc-l52km 的详细信息，验证其状态和 O... | `kubectl get pod memhog-767b7b5dcc-l52km -n aiops-e2e -o json` |
   | e2 | important | ✅ | kubectl_previous_logs | 获取 Pod memhog-767b7b5dcc-l52km 的日志，检查是否有关于内存不... | `kubectl logs memhog-767b7b5dcc-l52km -n aiops-e2e --previous` |
   | e3 | important | ✅ | kubectl_describe | 获取 Pod memhog-767b7b5dcc-l52km 的描述信息，验证其容器状态和... | `kubectl describe pod memhog-767b7b5dcc-l52km -n aiops-e2e` |

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (13.7s)
   📤 → 下游数据: root_cause=[L2层] 当前无法基于 LLM 输出确定根本原因
   confidence=10%
   causal_chain={"trigger": "LLM 未生成可靠因果链", "mechanism": "缺少可用的结构化根因分析结果", "manifestation": "我的集群有什么问题"}
   rca_analysis={"phenomenon": "我的集群有什么问题", "evidence_analysis": [], "causal_chain": {"trigger": "LLM 未生成可靠因果链", "mechanism": "缺少可用的结构化根因分析结果", "manifestation": "我的集群有什么问题"}, "root_cause": "[L2层] 当前无法基于 LLM 输出确定根本原因", "confidence": 0.1, "confidence_reason": "LLM 返回结果不符合 RCA 结构化输出合同", "alternative_causes": []}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: [L2层] 当前无法基于 LLM 输出确定根本原因
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
   ✅ [汇总总结] 完成 (1m 23.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4471 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 9.0s
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
| **兼容归因层** | L2 - 容器资源类问题 |
| **问题分类** | OOMKilled（内存不足导致容器被终止） |
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
| 错误信息 | OOMKilled (Exit Code 137) |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod memhog-767b7b5dcc-l52km -n aiops-e2e` | `STATUS: CrashLoopBackOff, RESTARTS: 54, pod_abnormal_type=OOMKilled` | Pod 处于频繁重启状态，标记为 OOMKilled |
| 2 | Pod 描述 | `kubectl describe pod memhog-767b7b5dcc-l52km -n aiops-e2e` | `Reason: OOMKilled, Exit Code: 137` | 容器因内存不足被终止 |
| 3 | Pod 资源配置 | `kubectl get pod memhog-767b7b5dcc-l52km -n aiops-e2e -o yaml` | `memory limit: 256Mi` | 内存限制设置较低 |
| 4 | 事件日志 | `kubectl get events -n aiops-e2e` | `Warning BackOff Pod/memhog-767b7b5dcc-l52km Back-off restarting failed container memhog` | Pod 频繁重启 |
| 5 | 前次日志 | `kubectl logs memhog-767b7b5dcc-l52km -n aiops-e2e --previous` | `关键日志: (no output)` | 无日志输出，可能由于容器崩溃前未记录 |
| 6 | 容器前次日志 | `kubectl logs memhog-767b7b5dcc-l52km -n aiops-e2e --previous --container memhog` | `关键日志: (no output)` | 同样无日志输出 |
| 7 | 全部 Pod 状态 | `kubectl get pods -n aiops-e2e` | `1 Pod 处于 CrashLoopBackOff，46 Pod 正常` | 集群中只有 1 个异常 Pod |
| 8 | 事件摘要 | `kubectl get events -n aiops-e2e` | `Warning BackOff 持续发生` | 说明问题在持续，尚未解决 |
| 9 | Pod YAML 配置 | `kubectl get pod memhog-767b7b5dcc-l52km -n aiops-e2e -o yaml` | `restartPolicy: Always, terminationGracePeriodSeconds: 30` | Pod 配置为 Always 重启，无法自动停止 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 `CrashLoopBackOff`，且 `Reason: OOMKilled`，`Exit Code: 137`，表明是内存不足导致的崩溃。
- **证据 #2 + #3 印证**：OOMKilled 与内存限制 `256Mi` 的设置形成因果关系，说明应用实际内存需求超过当前限制。
- **证据 #4 印证**：事件日志中 `Back-off restarting failed container` 说明重启机制已被触发，但问题未解决。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 容器崩溃前日志 | critical | 无法确认内存增长原因，无法判断是否为内存泄漏或配置不当 |
| 容器资源请求 vs 使用 | important | 无法判断是否为资源限制不足或资源分配不合理 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 应用实际内存需求超过 256Mi（可能存在内存泄漏或配置不当）          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器内存使用达到 limit → 触发 cgroup OOM Killer                 │
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

**结论**：根据证据 #2 (Exit Code 137, OOMKilled) 和证据 #3 (memory limit: 256Mi)，问题的根本原因是**容器内存限制（256Mi）不足以满足应用实际需求**，导致容器被 cgroup OOM Killer 终止并持续重启。

**置信度**：高 (95%)

- ✅ Exit Code 137 明确指向 OOMKilled
- ✅ Reason: OOMKilled 直接确认
- ⚠️ 缺少崩溃前日志，无法确认内存增长原因

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 增加内存限制**

```bash
kubectl set resources deployment/memhog -n aiops-e2e --limits=memory=512Mi
```

*依据*：当前 256Mi 不足，建议翻倍后观察

**2. [可选] 查看崩溃前日志**

```bash
kubectl logs memhog-767b7b5dcc-l52km -n aiops-e2e --previous
kubectl logs memhog-767b7b5dcc-l52km -n aiops-e2e --previous --container memhog
```

*目的*：确认内存增长原因，排除内存泄漏

### 后续优化

1. **监控告警**：配置内存使用率告警（>80% 预警）
2. **资源评估**：使用 Prometheus 或 `kubectl describe pod` 查看资源请求/限制与使用情况（本环境不可用 `kubectl top`）
3. **应用优化**：检查是否存在内存泄漏

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

├─ 总耗时: 5.1m
├─ 问题定位: 91.5s (30%) ✅
├─ 证据链采集: 120.0s (39%) ✅
├─ 根因分析: 13.7s (4%) ✅
├─ 汇总总结: 83.8s (27%) ✅
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
