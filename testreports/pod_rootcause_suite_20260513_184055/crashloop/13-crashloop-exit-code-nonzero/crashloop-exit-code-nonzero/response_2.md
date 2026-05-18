======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: fe89fde6499b4f86]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Error': 1, 'Running': 46}
NAMESPACE     NAME                                                READY   STATUS      RESTARTS      AG
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
      📄 NAME                                      READY   STATUS             RESTARTS      AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-crashloop-exit-code-5db5947859-gk6cf   0/
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
8s (x4 over 35s)    Warning   BackOff          Pod/rc-crashloop-exit-code-5db5947859-gk6cf   Back-off restarting failed container app in pod rc-crashloop-exit-code-5db5947859
   💭 [问题定位] {
  "layer": "L2",
  "derived_layer": "L2",
  "layers": [
    "L2"
  ],
  "layer_name": "CrashLoopBackOffRuntime",
  "confidence": 0.95,
  "reasoning": "当前 Pod rc-crashloop-exit-code-5db5947859-gk6cf 处于 CrashLoopBackOff 状态，最后一次容器退出代码为 2，日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'，同时事件显示 'Back-off restarting failed container'。这表明容器在启动后由于运行时错误退出，符合 CrashLoopBackOffRuntime 的诊断条件。需要进一步检查容器的启动命令、应用配置和日志以确定具体原因。",
  "abnormal_pods": [
    "rc-crashloop-exit-code-5db5947859-gk6cf"
  ],
  "abnormal_groups": {
    "CrashLoopBackOffRuntime": 1
  },
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "CrashLoopBackOffRuntime",
  "status_category": "CrashLoopBackOff",
  "key_entities": [
    "Pod/rc-crashloop-exit-code-5db5947859-gk6cf",
    "Container/app",
    "Exit Code/2"
  ],
  "possible_scenarios": [
    "容器启动命令错误或配置缺失导致退出代码 2",
    "应用启动后立即退出，可能是业务逻辑错误或资源不足",
    "容器内进程异常终止，需要检查应用日志和配置"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 1.1s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[{'scenario': '容器启动命令错误或配置缺失导致退出代码 2', 'probability': '高', 'reason': "日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'"}, {'scenario': '应用启动后立即退出，可能是业务逻辑错误或资源不足', 'probability': '中', 'reason': '容器在启动后立即退出，没有明确的资源不足或配置缺失信号'}, {'scenario': '容器内进程异常终止，需要检查应用日志和配置', 'probability': '高', 'reason': '日志中显示了运行时错误，需要进一步检查日志和配置'}]
   entities=[{"type": "Pod", "name": "rc-crashloop-exit-code-5db5947859-gk6cf", "namespace": "aiops-e2e"}, {"type": "Container", "name": "app", "namespace": "aiops-e2e"}, {"type": "Exit Code", "name": "2", "namespace": "aiops-e2e"}]
   reasoning=当前 Pod rc-crashloop-exit-code-5db5947859-gk6cf 处于 CrashLoopBackOff 状态，最后一次容器退出代码为 2，日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'，同时事件显示 'Back-off restarting failed container'。这表明容器在启动后由于运行时错误退出，符合 CrashLoopBackOffRuntime 的诊断条件。需要进一步检查容器的启动命令、应用配置和日志以确定具体原因。
   layer_analysis={"layer": "L2", "derived_layer": "L2", "layers": ["L2"], "layer_name": "CrashLoopBackOffRuntime", "confidence": 0.5, "reasoning": "当前 Pod rc-crashloop-exit-code-5db5947859-gk6cf 处于 CrashLoopBackOff 状态，最后一次容器退出代码为 2，日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'，同时事件显示 'Back-off restarting failed container'。这表明容器在启动后由于运行时错误退出，符合 CrashLoopBackOffRuntime 的诊断条件。需要进一步检查容器的启动命令、应用配置和日志以确定具体原因。", "abnormal_pods": [{"name": "rc-crashloop-exit-code-5db5947859-gk6cf", "namespace": "aiops-e2e", "status": "Error"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "CrashLoopBackOffRuntime", "status_category": "container_runtime", "key_entities": [{"type": "Pod", "name": "rc-crashloop-exit-code-5db5947859-gk6cf", "namespace": "aiops-e2e"}, {"type": "Container", "name": "app", "namespace": "aiops-e2e"}, {"type": "Exit Code", "name": "2", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "容器启动命令错误或配置缺失导致退出代码 2", "probability": "高", "reason": "日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'"}, {"scenario": "应用启动后立即退出，可能是业务逻辑错误或资源不足", "probability": "中", "reason": "容器在启动后立即退出，没有明确的资源不足或配置缺失信号"}, {"scenario": "容器内进程异常终止，需要检查应用日志和配置", "probability": "高", "reason": "日志中显示了运行时错误，需要进一步检查日志和配置"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Error"], "pod_abnormal_type": "Error", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-exit-code-5db5947859-gk6cf"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "Error 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Error"], "pod_abnormal_type": "Error", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-exit-code-5db5947859-gk6cf"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "Error 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Error": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-crashloop-exit-code-5db5947859-gk6cf             0/1     Error       2 (25s ago)   27s    172.16.166.139   node1    <none>           <none>            app=rc-crashloop-exit-code,pod-template-hash=5db5947859,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/fe89fde6499b4f86/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/fe89fde6499b4f86/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/fe89fde6499b4f86/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                      READY   STATUS             RESTARTS      AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-crashloop-exit-code-5db5947859-gk6cf   0
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (2m 59.9s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常Pod的详细信息，包括状态、重启次数、最后状态、退出代码等","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o yaml","tool_args":{"name":"rc-crashloop-exit-code-5db5947859-gk6cf","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"获取Pod的完整配置和状态，特别是Last State和Exit Code","evidence_type":"pod_status","target_scope":"aiops-e2e/rc-crashloop-exit-code-5db5947859-gk6cf","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e2","description":"获取异常Pod崩溃前的日志，检查是否有运行时错误或配置缺失","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous --tail=200","tool_args":{"pod_name":"rc-crashloop-exit-code-5db5947859-gk6cf","namespace":"aiops-e2e","tail_lines":200},"purpose":"获取Pod崩溃前的容器日志，检查是否有业务异常或配置缺失","evidence_type":"container_logs","target_scope":"aiops-e2e/rc-crashloop-exit-code-5db5947859-gk6cf","acceptable_tools":["kubectl_previous_logs"],"counts_for_completeness":true},{"id":"e3","description":"获取Pod相关的事件，确认是否有BackOff、probe失败、Killing等关键事件","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crashloop-exit-code-5db5947859-gk6cf --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-crashloop-exit-code-5db5947859-gk6cf","sort_by":".lastTimestamp"},"purpose":"获取Pod相关的事件，确认是否有BackOff、probe失败、Killing等关键事件","evidence_type":"event_logs","target_scope":"aiops-e2e/rc-crashloop-exit-code-5db5947859-gk6cf","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                                      READY   STATUS             RESTARTS      AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-crashloop-exit-code-5db5947859-gk6cf   0/1     CrashLoopBackOff   5 (70s ago)   4m6s   172.16.166.139   node1   <none>           <none>            app=rc-crashloop-exit-code,pod-template-hash=5db5947859,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fe89fde6499b4f86/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fe89fde6499b4f86/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fe89fde6499b4f86/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 1\n关键日志:\nRUNTIME_STARTUP_ERROR: rc crashloop exits with code 2","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fe89fde6499b4f86/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fe89fde6499b4f86/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fe89fde6499b4f86/tools/002-evidence-kubectl_previous_logs.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 6 个，匹配计划 3 个，未规划证据 3 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":3,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1","description":"获取异常Pod的详细信息，包括状态、重启次数、最后状态、退出代码等","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o yaml","purpose":"获取Pod的完整配置和状态，特别是Last State和Exit Code","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常Pod崩溃前的日志，检查是否有运行时错误或配置缺失","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous --tail=200","purpose":"获取Pod崩溃前的容器日志，检查是否有业务异常或配置缺失","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取Pod相关的事件，确认是否有BackOff、probe失败、Killing等关键事件","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crashloop-exit-code-5db5947859-gk6cf --sort-by='.lastTimestamp'","purpose":"获取Pod相关的事件，确认是否有BackOff、probe失败、Killing等关键事件","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 获取异常Pod的详细信息，包括状态、重启次数、最后状态、退出代码等 | `kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o yaml` |
   | e2 | critical | ✅ | kubectl_previous_logs | 获取异常Pod崩溃前的日志，检查是否有运行时错误或配置缺失 | `kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous ...` |
   | e3 | critical | ✅ | kubectl_events | 获取Pod相关的事件，确认是否有BackOff、probe失败、Killing等关键事件 | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crash...` |

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (14.6s)
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
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 44.6s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4870 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 6m 0.2s
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
| **兼容归因层** | L2 - container_runtime |
| **问题分类** | CrashLoopBackOffRuntime |
| **置信度** | 高 (85%) |
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
| 错误信息 | RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2 |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e` | `STATUS: Error, RESTARTS: 2 (25s ago)` | Pod 处于 Error 状态，持续重启 |
| 2 | 容器退出代码 | `kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e` | `Last State: Terminated, Exit Code: 2` | 容器因运行时错误退出 |
| 3 | 崩溃前日志 | `kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous` | `RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2` | 容器启动时运行时错误 |
| 4 | 事件记录 | `kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e` | `Warning BackOff: Back-off restarting failed container app` | Kubernetes 正在 BackOff 重启失败容器 |
| 5 | kubectl_get_by_kind_in_cluster | `kubectl get pods -n aiops-e2e` | `aiops-e2e rc-crashloop-exit-code-5db5947859-gk6cf 0/1 Error 2 (25s ago) 27s 172.16.166.139 node1` | Pod 状态为 Error，重启中 |
| 6 | 上游 runbook | `fetch_runbook` | `CrashLoopBackOffRuntime 通常由 command/args 错误、入口进程启动失败、业务逻辑错误、文件系统权限问题等导致` | 指示该问题属于容器启动失败范畴 |
| 7 | kubectl_events | `kubectl events -n aiops-e2e` | `8s (x4 over 35s) Warning BackOff Pod/rc-crashloop-exit-code-5db5947859-gk6cf Back-off restarting failed container app` | Kubernetes 正在 BackOff 重启失败容器 |

### 证据关联分析

- **证据 #2 + #3 印证**：Exit Code 2 + 日志中 `RUNTIME_STARTUP_ERROR` → 容器启动时运行时错误
- **证据链**：容器启动时运行时错误 → 容器退出 → Kubernetes 重启容器 → 重复失败 → Pod 状态为 `CrashLoopBackOff`
- **证据 #4 + #7 印证**：BackOff 事件 → 表明 Kubernetes 识别到容器失败并采取 BackOff 策略

### 缺失证据（无）

| 证据 | 级别 | 影响 |
|------|------|------|
| 无 | 无 | 无 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 容器启动时发生运行时错误，导致容器退出，退出代码为 2            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器启动失败 → Kubernetes 重启容器 → 重启失败 → BackOff 策略    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器因运行时错误退出（Exit Code 2）                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CrashLoopBackOff，持续重启                           │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2 (Exit Code 2) 和证据 #3 (日志中 `RUNTIME_STARTUP_ERROR`)，
问题的根本原因是**容器启动时发生运行时错误，导致容器退出，退出代码为 2**，
这可能是由于容器启动命令错误、配置缺失、应用逻辑异常等原因导致。
**置信度**：高 (85%)
- ✅ Exit Code 2 明确指向启动失败
- ✅ 日志中 RUNTIME_STARTUP_ERROR 确认运行时错误
- ⚠️ 未提供容器启动命令和应用配置，无法确认具体错误原因

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 查看容器启动命令和配置**
```bash
kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o jsonpath='{.spec.containers[*].command}' 
kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o jsonpath='{.spec.containers[*].args}'
```
*目的*：确认容器启动命令和参数是否正确，是否存在语法错误或路径错误

**2. [优先] 检查容器日志和应用配置**
```bash
kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous
kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e
```
*目的*：确认应用启动时是否有明确的错误信息，如文件缺失、权限不足、端口冲突等

**3. [可选] 调整容器 restartPolicy（仅用于调试）**
```bash
kubectl set env deployment/<deployment-name> -n aiops-e2e RESTART_POLICY=Always
```
*目的*：避免容器持续重启，便于查看日志

### 后续优化

1. **容器健康检查**：为容器配置 `livenessProbe` 和 `readinessProbe`，避免无意义重启
2. **日志采集与告警**：配置日志采集并设置运行时错误告警，及时发现类似问题
3. **容器镜像验证**：确保容器镜像构建正确，启动脚本和依赖项完整

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |
| 3. 检查容器退出状态 | `kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e` | `Last State: Running` |

---

## ⚠️ 注意事项

- 如果确认容器启动命令和参数正确，但问题仍然存在，可能需要检查应用本身的逻辑或依赖项
- 如果容器启动命令中使用了环境变量，请确认环境变量是否正确配置
- 如果容器中应用需要访问文件或目录，请确认权限是否正确，路径是否存在

---

## 📊 性能统计

├─ 总耗时: 6.0m
├─ 问题定位: 61.1s (17%) ✅
├─ 证据链采集: 179.9s (50%) ✅
├─ 根因分析: 14.6s (4%) ✅
├─ 汇总总结: 104.6s (29%) ✅
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
