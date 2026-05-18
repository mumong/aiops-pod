======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 58b6e326546b4ede]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'CrashLoopBackOff': 1, 'Running': 46}
NAMESPACE     NAME                                                READY   STATUS           
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
      📄 NAME                                      READY   STATUS             RESTARTS         AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-crashloop-exit-code-5db5947859-gk6cf 
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
4m1s (x743 over 164m)   Warning   BackOff   Pod/rc-crashloop-exit-code-5db5947859-gk6cf   Back-off restarting failed container app in pod rc-crashloop-exit-code-5db5947859-gk
   💭 [问题定位] {
  "layer": "L2",
  "derived_layer": "L2",
  "layers": [
    "L2"
  ],
  "layer_name": "容器运行时异常",
  "confidence": "high",
  "reasoning": "识别到 Pod rc-crashloop-exit-code-5db5947859-gk6cf 处于 CrashLoopBackOff 状态，Exit Code 为 2，且日志显示 rc crashloop exits with code 2。Events 显示 Back-off restarting failed container。此类型异常属于容器运行时问题，归类为 L2。",
  "abnormal_pods": [
    {
      "name": "rc-crashloop-exit-code-5db5947859-gk6cf",
      "namespace": "aiops-e2e",
      "status": "CrashLoopBackOff",
      "restarts": "36 (4m42s ago)",
      "age": "163m",
      "ip": "172.16.166.139",
      "node": "node1",
      "labels": {
        "app": "rc-crashloop-exit-code",
        "pod-template-hash": "5db5947859",
        "pod_abnormal_type": "CrashLoopBackOffRuntime",
        "rootcause-e2e": "true"
      }
    }
  ],
  "abnormal_groups": [
    "CrashLoopBackOffRuntime"
  ],
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "CrashLoopBackOffRuntime",
  "status_category": "L2",
  "key_entities": [
    "rc-crashloop-exit-code-5db5947859-gk6cf (Pod)"
  ],
  "possible_scenarios": [
    "容器主进程启动失败，Exit Code 为 2。",
    "容器内部命令或脚本执行失败，导致容器退出。",
    "容器配置错误，导致容器无法正常运行。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (2m 20.6s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[{'scenario': '容器主进程启动失败，Exit Code 为 2。', 'probability': 'high', 'reason': 'CrashLoopBackOff + Exit Code 2'}, {'scenario': '容器内部命令或脚本执行失败，导致容器退出。', 'probability': 'high', 'reason': 'CrashLoopBackOff + Exit Code 2'}, {'scenario': '容器配置错误，导致容器无法正常运行。', 'probability': 'medium', 'reason': 'CrashLoopBackOff + Exit Code 2'}]
   entities=[{"type": "Pod", "name": "rc-crashloop-exit-code-5db5947859-gk6cf", "namespace": "aiops-e2e"}]
   reasoning=识别到 Pod rc-crashloop-exit-code-5db5947859-gk6cf 处于 CrashLoopBackOff 状态，Exit Code 为 2，且日志显示 rc crashloop exits with code 2。Events 显示 Back-off restarting failed container。此类型异常属于容器运行时问题，归类为 L2。
   layer_analysis={"layer": "L2", "derived_layer": "L2", "layers": ["L2"], "layer_name": "容器运行时异常", "confidence": 1.0, "reasoning": "识别到 Pod rc-crashloop-exit-code-5db5947859-gk6cf 处于 CrashLoopBackOff 状态，Exit Code 为 2，且日志显示 rc crashloop exits with code 2。Events 显示 Back-off restarting failed container。此类型异常属于容器运行时问题，归类为 L2。", "abnormal_pods": [{"name": "rc-crashloop-exit-code-5db5947859-gk6cf", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "CrashLoopBackOffRuntime", "status_category": "container_runtime", "key_entities": [{"type": "Pod", "name": "rc-crashloop-exit-code-5db5947859-gk6cf", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "容器主进程启动失败，Exit Code 为 2。", "probability": "high", "reason": "CrashLoopBackOff + Exit Code 2"}, {"scenario": "容器内部命令或脚本执行失败，导致容器退出。", "probability": "high", "reason": "CrashLoopBackOff + Exit Code 2"}, {"scenario": "容器配置错误，导致容器无法正常运行。", "probability": "medium", "reason": "CrashLoopBackOff + Exit Code 2"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-exit-code-5db5947859-gk6cf"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-exit-code-5db5947859-gk6cf"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-crashloop-exit-code-5db5947859-gk6cf             0/1     CrashLoopBackOff   36 (4m25s ago)   163m    172.16.166.139   node1    <none>           <none>            app=rc-crashloop-exit-code,pod-template-hash=5db5947859,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/58b6e326546b4ede/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/58b6e326546b4ede/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/58b6e326546b4ede/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L2
   置信度: 100%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                      READY   STATUS             RESTARTS        AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-crashloop-exit-code-5db5947859-gk6cf  
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (1m 40.5s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 的详细信息，包括 Last State、Exit Code、Reason、重启次数等","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o yaml","tool_args":{"name":"rc-crashloop-exit-code-5db5947859-gk6cf","namespace":"aiops-e2e","output":"yaml"},"purpose":"验证 Pod 的 Last State、Exit Code、Reason、重启次数","evidence_type":"pod_status","target_scope":"aiops-e2e","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 的崩溃前日志","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous --tail=200","tool_args":{"pod":"rc-crashloop-exit-code-5db5947859-gk6cf","namespace":"aiops-e2e","tail":"200","previous":true},"purpose":"验证崩溃前的日志，查找业务异常、命令错误、文件系统问题等","evidence_type":"pod_logs","target_scope":"aiops-e2e","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取与异常 Pod 相关的 Events","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crashloop-exit-code-5db5947859-gk6cf --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-crashloop-exit-code-5db5947859-gk6cf","sort_by":".lastTimestamp"},"purpose":"验证 BackOff、Killing、probe failed 等关键事件","evidence_type":"event","target_scope":"aiops-e2e","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                                      READY   STATUS             RESTARTS        AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-crashloop-exit-code-5db5947859-gk6cf   0/1     CrashLoopBackOff   37 (3m5s ago)   167m   172.16.166.139   node1   <none>           <none>            app=rc-crashloop-exit-code,pod-template-hash=5db5947859,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/58b6e326546b4ede/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/58b6e326546b4ede/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/58b6e326546b4ede/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 1\n关键日志:\nRUNTIME_STARTUP_ERROR: rc crashloop exits with code 2","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/58b6e326546b4ede/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/58b6e326546b4ede/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/58b6e326546b4ede/tools/002-evidence-kubectl_previous_logs.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 6 个，匹配计划 3 个，未规划证据 3 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":3,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 的详细信息，包括 Last State、Exit Code、Reason、重启次数等","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o yaml","purpose":"验证 Pod 的 Last State、Exit Code、Reason、重启次数","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 的崩溃前日志","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous --tail=200","purpose":"验证崩溃前的日志，查找业务异常、命令错误、文件系统问题等","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取与异常 Pod 相关的 Events","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crashloop-exit-code-5db5947859-gk6cf --sort-by='.lastTimestamp'","purpose":"验证 BackOff、Killing、probe failed 等关键事件","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 获取异常 Pod 的详细信息，包括 Last State、Exit Code、Reason... | `kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o yaml` |
   | e2 | critical | ✅ | kubectl_previous_logs | 获取异常 Pod 的崩溃前日志 | `kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous ...` |
   | e3 | critical | ✅ | kubectl_events | 获取与异常 Pod 相关的 Events | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crash...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (37.1s)
   📤 → 下游数据: root_cause=容器主进程启动失败，Exit Code 为 2。证据包括 Pod rc-crashloop-exit-code-5db5947859-gk6cf 处于 CrashLoopBackOff 状态，重启次数为 37 次，Exit Code 为 2；Pod 崩溃前日志显示 rc crashloop exits with code 2；Events 显示 Back-off restarting failed container app。
   confidence=90%
   causal_chain={"root_cause": "容器主进程启动失败，Exit Code 为 2", "intermediate_causes": ["容器内部命令或脚本执行失败，导致容器退出", "容器配置错误，导致容器无法正常运行"], "immediate_causes": ["容器主进程启动失败，Exit Code 为 2"], "phenomena": ["Pod rc-crashloop-exit-code-5db5947859-gk6cf 处于 CrashLoopBackOff 状态", "Pod 崩溃前日志显示 rc crashloop exits with code 2", "Events 显示 Back-off restarting failed container app"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"e1": "获取异常 Pod 的详细信息，包括 Last State、Exit Code、Reason、重启次数等"}, {"e2": "获取异常 Pod 的崩溃前日志"}, {"e3": "获取与异常 Pod 相关的 Events"}, {"layer_1": "上游已验证工具结果: kubectl_get_by_kind_in_cluster"}, {"layer_2": "上游已验证工具结果: kubectl_get_by_name"}, {"layer_3": "上游已验证工具结果: kubectl_previous_logs"}, {"layer_4": "上游已验证工具结果: kubectl_events"}], "evidence_analysis": [{"e1": "Pod rc-crashloop-exit-code-5db5947859-gk6cf 处于 CrashLoopBackOff 状态，重启次数为 37 次，Exit Code 为 2"}, {"e2": "Pod 崩溃前日志显示 rc crashloop exits with code 2"}, {"e3": "Events 显示 Back-off restarting failed container app"}, {"layer_1": "kubectl_get_by_kind_in_cluster 显示有 1 个 Pod 处于 CrashLoopBackOff 状态"}, {"layer_2": "kubectl_get_by_name 显示 rc-crashloop-exit-code-5db5947859-gk6cf 处于 CrashLoopBackOff 状态，重启次数为 36 次"}, {"layer_3": "kubectl_previous_logs 显示 rc crashloop exits with code 2"}, {"layer_4": "kubectl_events 显示 Back-off restarting failed container app"}], "causal_chain": {"root_cause": "容器主进程启动失败，Exit Code 为 2", "intermediate_causes": ["容器内部命令或脚本执行失败，导致容器退出", "容器配置错误，导致容器无法正常运行"], "immediate_causes": ["容器主进程启动失败，Exit Code 为 2"], "phenomena": ["Pod rc-crashloop-exit-code-5db5947859-gk6cf 处于 CrashLoopBackOff 状态", "Pod 崩溃前日志显示 rc crashloop exits with code 2", "Events 显示 Back-off restarting failed container app"]}, "root_cause": "容器主进程启动失败，Exit Code 为 2。证据包括 Pod rc-crashloop-exit-code-5db5947859-gk6cf 处于 CrashLoopBackOff 状态，重启次数为 37 次，Exit Code 为 2；Pod 崩溃前日志显示 rc crashloop exits with code 2；Events 显示 Back-off restarting failed container app。", "root_cause_summary": "容器主进程启动失败，Exit Code 为 2。证据包括 Pod rc-crashloop-exit-code-5db5947859-gk6cf 处于 CrashLoopBackOff 状态，重启次数为 37 次，Exit Code 为 2；Pod 崩溃前日志显示 rc crashloop exits with code 2；Events 显示 Back-off restarting failed container app。", "confidence": 0.9, "confidence_reason": "有直接证据，因果链清晰", "primary_runbooks": ["pod-crashloop-runtime.md"], "alternative_causes": [], "limitations": "无", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 容器主进程启动失败，Exit Code 为 2。证据包括 Pod rc-crashloop-exit-code-5db5947859-gk6cf 处于 CrashLoopBackOff 状态，重启次数为 37 次，Exit Code 为 2；Pod 崩溃前日志显示 rc crashloop exit...
   置信度: 90%
   🔗 因果链:
     根本原因: 容器主进程启动失败，Exit Code 为 2


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 25.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4604 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 6m 3.9s
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
| **兼容归因层** | L2 - 容器运行时 |
| **问题分类** | CrashLoopBackOffRuntime |
| **置信度** | 高 (90%) |
| **证据完整度** | 3/3 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-crashloop-exit-code-5db5947859-gk6cf |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | rc crashloop exits with code 2 |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e` | `STATUS: CrashLoopBackOff, RESTARTS: 36 (4m25s ago)` | Pod 由于容器退出码 2 持续重启 |
| 2 | 崩溃前日志 | `kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous` | `RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2` | 容器主进程启动失败，退出码为 2 |
| 3 | Events | `kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e` | `Warning BackOff Pod/rc-crashloop-exit-code-5db5947859-gk6cf Back-off restarting failed container app` | Kubernetes 正在进行重启回退，容器持续失败 |
| 4 | 容器状态 | `kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e` | `Last State: Terminated, Reason: Error, Exit Code: 2` | 容器退出码 2 表示启动失败 |
| 5 | 集群状态 | `kubectl get pods -A` | `CrashLoopBackOff: 1` | 集群中存在 1 个 CrashLoopBackOff 状态的 Pod |
| 6 | Runbook | `fetch_runbook` | `Pod异常类型: CrashLoopBackOffRuntime | 典型状态: CrashLoopBackOff | 兼容分类: container_runtime` | 该类型问题归类为容器运行时问题 |
| 7 | 重启次数 | `kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e` | `RESTARTS: 36` | Pod 已重启 36 次 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 `CrashLoopBackOff` + 崩溃前日志显示 `Exit Code 2` → 容器主进程启动失败。
- **证据链**：容器主进程启动失败 → 容器退出码 2 → Pod 被 Kubernetes 重启 → 事件中记录 `Back-off restarting failed container`。
- **证据 #3 + #4 印证**：Events 显示 `Back-off restarting failed container` + 容器状态显示 `Exit Code 2` → 容器运行时异常。

### 缺失证据（无）

无缺失关键证据。

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 容器主进程启动失败，退出码为 2，可能是命令、脚本或配置错误        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器进程启动失败，退出码 2，导致容器无法正常运行                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器被 Kubernetes 重启，退出码 2 导致持续 CrashLoopBackOff      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CrashLoopBackOff，重启次数为 36                      │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Pod 状态 CrashLoopBackOff, 重启 36 次)、证据 #2 (崩溃前日志显示 rc crashloop exits with code 2) 和证据 #3 (Events 显示 Back-off restarting failed container app)，问题的根本原因是 **容器主进程启动失败，退出码为 2**，这通常由命令错误、脚本错误、配置错误或依赖缺失引起。

**置信度**：高 (90%)
- ✅ Exit Code 2 明确指向启动失败
- ✅ 崩溃前日志直接确认了错误信息
- ✅ Events 显示容器持续失败和重启

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查容器启动命令或入口脚本**
```bash
kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e
```
*依据*：查看 `command` 和 `args` 是否正确，确认入口脚本是否存在或权限是否正确。

**2. [优先] 检查容器日志以定位启动失败原因**
```bash
kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous
```
*目的*：查看崩溃前的日志，确认是脚本错误、依赖缺失、配置错误还是其他原因。

**3. [可选] 修改容器启动命令或修复脚本**
```bash
kubectl set image deployment/<deployment-name> app=image:tag
```
*依据*：如果确认是容器镜像中的脚本或配置错误，建议修复后重新部署。

### 后续优化

1. **增加容器健康检查**：
   - 配置 `livenessProbe` 和 `readinessProbe`，及时发现启动失败。
2. **监控告警**：
   - 配置 `CrashLoopBackOff` 状态的监控告警，及时发现类似问题。
3. **容器日志收集**：
   - 使用集中式日志系统（如 Fluentd + Loki）收集崩溃前日志，便于排查。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e` | STATUS: Running |
| 2. 确认重启次数停止增加 | `kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e` | RESTARTS 不再增加 |
| 3. 检查容器日志 | `kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e` | 应无错误日志，容器正常运行 |

---

## ⚠️ 注意事项

- 如果修复后 Pod 仍持续重启，应进一步检查容器内部依赖（如文件路径、环境变量、端口占用等）。
- 如果是 Deployment 管理的 Pod，修复后需等待 Deployment 更新完成。
- 如果是 Job 或一次性任务，应考虑使用 `Job` 而非 `Deployment` 来避免循环重启。

---

## 📊 性能统计

├─ 总耗时: 6.1m
├─ 问题定位: 140.6s (39%) ✅
├─ 证据链采集: 100.5s (28%) ✅
├─ 根因分析: 37.1s (10%) ✅
├─ 汇总总结: 85.7s (24%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 8 次
```

📋 诊断追踪

- **核心 Runbook**: pod-crashloop-runtime
- **参考 Runbook**: pod-crashloop-runtime
- **工具调用**: 8 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
