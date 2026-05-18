======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: a16de0599e9448e4]

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
      📄 NAME                                              READY   STATUS             RESTARTS        AGE     IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-crashloop-command-not-found-5
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 2
signals: 2
关键日志:
RUNTIME_STARTUP_ERROR: command not found
sh: definitely-missing-command-for-rootcause: not found
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 输出摘要: raw_chars=4397 lines=150
apiVersion: v1
kind: Pod
metadata:
  annotations:
    aiops.e2e/runbook: pod-crashloop-runtime.md
    cni.projectcalico.org/containerID: 22d144a806376f4
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
2m35s (x25 over 7m44s)   Warning   BackOff          Pod/rc-crashloop-command-not-found-55b7bcd797-rhdvk   Back-off restarting failed container app in pod rc-crashloop-command
   💭 [问题定位] {
  "layer": "L2",
  "derived_layer": "L2",
  "layers": [
    "L2"
  ],
  "layer_name": "CrashLoopBackOffRuntime",
  "confidence": "high",
  "reasoning": "Pod 处于 CrashLoopBackOff 状态，且日志显示 'command not found'，表明容器启动命令错误或缺失。Exit Code 非 137，且没有配置缺失信号，符合 CrashLoopBackOffRuntime 的典型原因。",
  "abnormal_pods": [
    "rc-crashloop-command-not-found-55b7bcd797-rhdvk"
  ],
  "abnormal_groups": {
    "CrashLoopBackOffRuntime": 1
  },
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "CrashLoopBackOffRuntime",
  "status_category": "CrashLoopBackOff",
  "key_entities": [
    "Pod rc-crashloop-command-not-found-55b7bcd797-rhdvk",
    "Command not found",
    "Exit code non-137"
  ],
  "possible_scenarios": [
    "容器启动命令错误或缺失",
    "容器主进程启动失败",
    "容器主进程 exit(0) 后被控制器反复拉起"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 51.7s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[{'scenario': '容器启动命令错误或缺失', 'probability': 'high', 'reason': "日志显示 'command not found'"}, {'scenario': '容器主进程启动失败', 'probability': 'high', 'reason': 'Pod 处于 CrashLoopBackOff 状态'}, {'scenario': '容器主进程 exit(0) 后被控制器反复拉起', 'probability': 'high', 'reason': 'Exit Code 非 137，且没有配置缺失信号'}]
   entities=[{"type": "Pod", "name": "rc-crashloop-command-not-found-55b7bcd797-rhdvk", "namespace": "aiops-e2e"}]
   reasoning=Pod 处于 CrashLoopBackOff 状态，且日志显示 'command not found'，表明容器启动命令错误或缺失。Exit Code 非 137，且没有配置缺失信号，符合 CrashLoopBackOffRuntime 的典型原因。
   layer_analysis={"layer": "L2", "derived_layer": "", "layers": [], "layer_name": "", "confidence": 0.5, "reasoning": "Pod 处于 CrashLoopBackOff 状态，且日志显示 'command not found'，表明容器启动命令错误或缺失。Exit Code 非 137，且没有配置缺失信号，符合 CrashLoopBackOffRuntime 的典型原因。", "abnormal_pods": [{"name": "rc-crashloop-command-not-found-55b7bcd797-rhdvk", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "CrashLoopBackOffRuntime", "status_category": "container_runtime", "key_entities": [{"type": "Pod", "name": "rc-crashloop-command-not-found-55b7bcd797-rhdvk", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "容器启动命令错误或缺失", "probability": "high", "reason": "日志显示 'command not found'"}, {"scenario": "容器主进程启动失败", "probability": "high", "reason": "Pod 处于 CrashLoopBackOff 状态"}, {"scenario": "容器主进程 exit(0) 后被控制器反复拉起", "probability": "high", "reason": "Exit Code 非 137，且没有配置缺失信号"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-command-not-found-55b7bcd797-rhdvk"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-command-not-found-55b7bcd797-rhdvk"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-crashloop-command-not-found-55b7bcd797-rhdvk     0/1     CrashLoopBackOff   6 (2m6s ago)   7m32s   172.16.166.150   node1    <none>           <none>            app=rc-crashloop-command-not-found,pod-template-hash=55b7bcd797,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/a16de0599e9448e4/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/a16de0599e9448e4/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/a16de0599e9448e4/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                              READY   STATUS             RESTARTS      AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-crashloop-command-not-found-55b7b
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 2
signals: 2
关键日志:
RUNTIME_STARTUP_ERROR: command not found
sh: definitely-missing-command-for-rootcause: not found
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (2m 28.6s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 的详细信息，包括 Last State、Exit Code、Reason 和重启次数","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e -o yaml","tool_args":{"name":"rc-crashloop-command-not-found-55b7bcd797-rhdvk","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"验证 Pod 的 Last State、Exit Code、Reason 和重启次数","evidence_type":"Pod Status","target_scope":"aiops-e2e/rc-crashloop-command-not-found-55b7bcd797-rhdvk","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 的崩溃前日志，以查看崩溃原因","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e --previous --tail=200","tool_args":{"name":"rc-crashloop-command-not-found-55b7bcd797-rhdvk","namespace":"aiops-e2e","tail":"200","container":"app"},"purpose":"验证崩溃前日志中的错误信息","evidence_type":"Container Logs","target_scope":"aiops-e2e/rc-crashloop-command-not-found-55b7bcd797-rhdvk/app","acceptable_tools":["kubectl_previous_logs"],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod 的 Events，以查看是否有 BackOff、probe failed、Killing 等事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crashloop-command-not-found-55b7bcd797-rhdvk --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-crashloop-command-not-found-55b7bcd797-rhdvk","sort_by":".lastTimestamp"},"purpose":"验证 Events 中的 BackOff、probe failed、Killing 等事件","evidence_type":"Events","target_scope":"aiops-e2e/rc-crashloop-command-not-found-55b7bcd797-rhdvk","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                                              READY   STATUS             RESTARTS      AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-crashloop-command-not-found-55b7bcd797-rhdvk   0/1     CrashLoopBackOff   7 (64s ago)   11m   172.16.166.150   node1   <none>           <none>            app=rc-crashloop-command-not-found,pod-template-hash=55b7bcd797,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a16de0599e9448e4/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a16de0599e9448e4/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a16de0599e9448e4/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 2\nsignals: 2\n关键日志:\nRUNTIME_STARTUP_ERROR: command not found\nsh: definitely-missing-command-for-rootcause: not found","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a16de0599e9448e4/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a16de0599e9448e4/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a16de0599e9448e4/tools/002-evidence-kubectl_previous_logs.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 6 个，匹配计划 3 个，未规划证据 3 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":3,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 的详细信息，包括 Last State、Exit Code、Reason 和重启次数","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e -o yaml","purpose":"验证 Pod 的 Last State、Exit Code、Reason 和重启次数","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 的崩溃前日志，以查看崩溃原因","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e --previous --tail=200","purpose":"验证崩溃前日志中的错误信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod 的 Events，以查看是否有 BackOff、probe failed、Killing 等事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crashloop-command-not-found-55b7bcd797-rhdvk --sort-by='.lastTimestamp'","purpose":"验证 Events 中的 BackOff、probe failed、Killing 等事件","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 获取异常 Pod 的详细信息，包括 Last State、Exit Code、Reason... | `kubectl get pod rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e ...` |
   | e2 | critical | ✅ | kubectl_previous_logs | 获取异常 Pod 的崩溃前日志，以查看崩溃原因 | `kubectl logs rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e --p...` |
   | e3 | important | ✅ | kubectl_events | 获取异常 Pod 的 Events，以查看是否有 BackOff、probe failed... | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crash...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (35.5s)
   📤 → 下游数据: root_cause=容器启动命令错误或缺失，导致容器启动失败并触发了重启机制，最终导致 Pod 处于 CrashLoopBackOff 状态。
   confidence=90%
   causal_chain={"直接原因": "容器启动命令错误或缺失", "传导原因": "容器启动失败并触发了重启机制", "根因": "容器启动命令错误或缺失"}
   rca_analysis={"phenomenon": "Pod 处于 CrashLoopBackOff 状态，且日志显示 'command not found'，表明容器启动命令错误或缺失。Exit Code 非 137，且没有配置缺失信号，符合 CrashLoopBackOffRuntime 的典型原因。", "evidence_inventory": [{"tool": "kubectl_get_by_name", "data": "Pod rc-crashloop-command-not-found-55b7bcd797-rhdvk 处于 CrashLoopBackOff 状态，重启次数为 7，最后一次重启时间为 64s ago。"}, {"tool": "kubectl_previous_logs", "data": "Pod 日志显示 'RUNTIME_STARTUP_ERROR: command not found' 和 'sh: definitely-missing-command-for-rootcause: not found'，表明容器启动命令错误或缺失。"}, {"tool": "kubectl_events", "data": "Pod 事件显示 'Back-off restarting failed container app'，表明容器启动失败并触发了重启机制。"}], "evidence_analysis": [{"tool": "kubectl_get_by_name", "summary": "Pod rc-crashloop-command-not-found-55b7bcd797-rhdvk 处于 CrashLoopBackOff 状态，表明容器启动失败并触发了重启机制。"}, {"tool": "kubectl_previous_logs", "summary": "Pod 日志显示 'RUNTIME_STARTUP_ERROR: command not found' 和 'sh: definitely-missing-command-for-rootcause: not found'，表明容器启动命令错误或缺失。"}, {"tool": "kubectl_events", "summary": "Pod 事件显示 'Back-off restarting failed container app'，表明容器启动失败并触发了重启机制。"}], "causal_chain": {"直接原因": "容器启动命令错误或缺失", "传导原因": "容器启动失败并触发了重启机制", "根因": "容器启动命令错误或缺失"}, "root_cause": "容器启动命令错误或缺失，导致容器启动失败并触发了重启机制，最终导致 Pod 处于 CrashLoopBackOff 状态。", "root_cause_summary": "容器启动命令错误或缺失，导致容器启动失败并触发了重启机制，最终导致 Pod 处于 CrashLoopBackOff 状态。", "confidence": 0.9, "confidence_reason": "有直接证据表明容器启动命令错误或缺失，且因果链清晰。", "primary_runbooks": ["pod-crashloop-runtime.md"], "alternative_causes": [], "limitations": "无", "llm_raw_analysis": "无"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 容器启动命令错误或缺失，导致容器启动失败并触发了重启机制，最终导致 Pod 处于 CrashLoopBackOff 状态。
   置信度: 90%
   🔗 因果链:


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 14.4s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4631 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 6m 10.2s
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
| **兼容归因层** | L2 - container_runtime |
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
| Pod | rc-crashloop-command-not-found-55b7bcd797-rhdvk |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | command not found |

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | kubectl get pod | `STATUS: CrashLoopBackOff, RESTARTS: 6 (2m6s ago)` | Pod 正在持续重启，处于 CrashLoopBackOff 状态 |
| 2 | 崩溃前日志 | kubectl logs --previous | `RUNTIME_STARTUP_ERROR: command not found`<br>`sh: definitely-missing-command-for-rootcause: not found` | 容器启动命令缺失或错误，导致无法启动 |
| 3 | Pod Events | kubectl describe pod | `Back-off restarting failed container app` | Kubernetes 检测到容器启动失败，正在进行重启回退 |

### 证据关联分析
- **证据 #1 + #2 印证**：Pod 状态为 CrashLoopBackOff，且崩溃前日志显示 `command not found`，说明容器启动命令错误或缺失。
- **证据 #1 + #3 印证**：Pod 正在被控制器反复重启，且事件中明确提示 `Back-off restarting failed container app`，表明容器主进程未能成功启动。
- **证据链总结**：容器启动命令缺失或错误 → 容器启动失败 → Kubernetes 重启容器 → Pod 状态为 CrashLoopBackOff。

### 缺失证据（无）
无缺失关键证据，证据采集完整度为 100%。

---
## 🎯 根因分析
### 因果链
```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                              │
│ 容器启动命令缺失或错误，导致容器无法启动。例如，应用镜像中缺少指定的命令或脚本。         │
└──────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                              │
│ 容器主进程无法启动 → 容器退出 → Kubernetes 检测到容器失败 → 自动重启容器。             │
└──────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                              │
│ 容器启动命令错误，日志显示 `command not found`，容器无法正常运行。                     │
└──────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                          │
│ Pod 状态为 CrashLoopBackOff，持续重启，Events 显示 `Back-off restarting failed container`。 │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (Pod 状态为 CrashLoopBackOff, 重启次数为 6)、证据 #2 (崩溃前日志显示 `command not found`) 和证据 #3 (Events 显示 `Back-off restarting failed container app`)，问题的根本原因是**容器启动命令缺失或错误**，导致容器无法启动，Kubernetes 自动重启容器，最终导致 Pod 处于 CrashLoopBackOff 状态。

**置信度**：高 (90%)
- ✅ Pod 状态为 CrashLoopBackOff
- ✅ 崩溃前日志显示 `command not found`
- ✅ Events 明确提示 `Back-off restarting failed container`

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 修正容器启动命令**
```bash
kubectl edit deployment <deployment-name> -n aiops-e2e
```
*修改内容示例*：
```yaml
spec:
  containers:
  - name: app
    image: <your-image>
    command: ["/bin/sh", "-c", "your-correct-command-here"]
```
*依据*：当前容器启动命令缺失或错误，需要明确指定正确的启动命令。

**2. [可选] 查看容器启动命令配置**
```bash
kubectl get deployment <deployment-name> -n aiops-e2e -o yaml
```
*目的*：确认容器的 `command` 或 `args` 是否缺失或错误。

**3. [可选] 查看容器镜像内容**
```bash
docker run --rm <your-image> sh -c "which definitely-missing-command-for-rootcause"
```
*目的*：确认镜像中是否确实缺少指定命令。

### 后续优化
1. **验证修复**：确保修复后 Pod 能够正常运行，不再重启。
2. **配置健康检查**：添加 `livenessProbe` 和 `readinessProbe`，确保容器健康状态可检测。
3. **文档记录**：记录命令修改原因和步骤，防止再次遗漏。
4. **镜像管理**：确保镜像中包含所有必要的启动依赖和命令。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 重启次数不再增加 |
| 3. 检查日志 | `kubectl logs rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e` | 没有 `command not found` 等错误信息 |
| 4. 检查 Events | `kubectl describe pod rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e` | 没有 `Back-off restarting failed container` 等错误事件 |

---
## ⚠️ 注意事项
- 如果修复后 Pod 仍处于 CrashLoopBackOff 状态，建议进一步检查容器镜像内容和启动脚本。
- 避免在容器中使用一次性任务作为主进程，应确保主进程是长期运行的服务（如 Web 服务器、守护进程等）。
- 可使用 `kubectl logs` 和 `kubectl describe pod` 定期检查容器日志和状态，防止类似问题再次发生。

---

---

## 📊 性能统计

├─ 总耗时: 6.2m
├─ 问题定位: 111.7s (30%) ✅
├─ 证据链采集: 148.6s (40%) ✅
├─ 根因分析: 35.5s (10%) ✅
├─ 汇总总结: 74.4s (20%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 9 次
```

📋 诊断追踪

- **核心 Runbook**: pod-crashloop-runtime
- **参考 Runbook**: pod-crashloop-runtime
- **工具调用**: 9 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
