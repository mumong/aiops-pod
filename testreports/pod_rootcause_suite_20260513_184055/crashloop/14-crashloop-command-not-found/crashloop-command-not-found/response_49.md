======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 2acf929dc6ed4e5a]

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
      📄 NAME                                              READY   STATUS             RESTARTS         AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
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
      📄 kubectl_get_yaml 输出摘要: raw_chars=4398 lines=150
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
2m53s (x788 over 173m)   Warning   BackOff   Pod/rc-crashloop-command-not-found-55b7bcd797-rhdvk   Back-off restarting failed container app in pod rc-crashloop-command-not-fo
   💭 [问题定位] {
  "layer": "L2",
  "derived_layer": "L2",
  "layers": [
    "L2"
  ],
  "layer_name": "容器运行时异常",
  "confidence": "高",
  "reasoning": "Pod rc-crashloop-command-not-found-55b7bcd797-rhdvk 处于 CrashLoopBackOff 状态，且日志显示 command not found，表明容器内启动命令错误或缺失。此问题属于容器运行时异常，归类为 L2。",
  "abnormal_pods": [
    "rc-crashloop-command-not-found-55b7bcd797-rhdvk"
  ],
  "abnormal_groups": [
    "CrashLoopBackOffRuntime"
  ],
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "CrashLoopBackOffRuntime",
  "status_category": "L2",
  "key_entities": [
    "rc-crashloop-command-not-found-55b7bcd797-rhdvk",
    "CrashLoopBackOff",
    "command not found",
    "aiops-e2e"
  ],
  "possible_scenarios": [
    "容器启动命令错误或缺失",
    "容器内进程启动失败",
    "容器内文件系统或权限问题"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (54.8s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[{'scenario': '容器启动命令错误或缺失', 'probability': '高', 'reason': "日志显示'command not found'，表明容器启动命令不存在或配置错误。"}, {'scenario': '容器内进程启动失败', 'probability': '中', 'reason': 'Pod处于CrashLoopBackOff状态，表明容器内进程启动失败。'}, {'scenario': '容器内文件系统或权限问题', 'probability': '低', 'reason': '可能由于文件系统或权限问题导致启动失败，但日志未明确显示。'}]
   entities=[{"type": "Pod", "name": "rc-crashloop-command-not-found-55b7bcd797-rhdvk", "namespace": "aiops-e2e"}, {"type": "Status", "name": "CrashLoopBackOff", "namespace": ""}, {"type": "Error", "name": "command not found", "namespace": ""}, {"type": "Namespace", "name": "aiops-e2e", "namespace": ""}]
   reasoning=当前集群中存在1个处于CrashLoopBackOff状态的Pod（rc-crashloop-command-not-found-55b7bcd797-rhdvk），其异常类型被归类为CrashLoopBackOffRuntime。日志显示容器启动失败，原因包括'command not found'。此问题属于容器运行时异常，符合L2层级的诊断标准。
   layer_analysis={"layer": "L2", "derived_layer": "L2", "layers": ["L2"], "layer_name": "容器运行时异常", "confidence": 0.95, "reasoning": "当前集群中存在1个处于CrashLoopBackOff状态的Pod（rc-crashloop-command-not-found-55b7bcd797-rhdvk），其异常类型被归类为CrashLoopBackOffRuntime。日志显示容器启动失败，原因包括'command not found'。此问题属于容器运行时异常，符合L2层级的诊断标准。", "abnormal_pods": [{"name": "rc-crashloop-command-not-found-55b7bcd797-rhdvk", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "CrashLoopBackOffRuntime", "status_category": "container_runtime", "key_entities": [{"type": "Pod", "name": "rc-crashloop-command-not-found-55b7bcd797-rhdvk", "namespace": "aiops-e2e"}, {"type": "Status", "name": "CrashLoopBackOff", "namespace": ""}, {"type": "Error", "name": "command not found", "namespace": ""}, {"type": "Namespace", "name": "aiops-e2e", "namespace": ""}], "possible_scenarios": [{"scenario": "容器启动命令错误或缺失", "probability": "高", "reason": "日志显示'command not found'，表明容器启动命令不存在或配置错误。"}, {"scenario": "容器内进程启动失败", "probability": "中", "reason": "Pod处于CrashLoopBackOff状态，表明容器内进程启动失败。"}, {"scenario": "容器内文件系统或权限问题", "probability": "低", "reason": "可能由于文件系统或权限问题导致启动失败，但日志未明确显示。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-command-not-found-55b7bcd797-rhdvk"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-command-not-found-55b7bcd797-rhdvk"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-crashloop-command-not-found-55b7bcd797-rhdvk     0/1     CrashLoopBackOff   38 (3m37s ago)   172m    172.16.166.150   node1    <none>           <none>            app=rc-crashloop-command-not-found,pod-template-hash=55b7bcd797,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/2acf929dc6ed4e5a/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/2acf929dc6ed4e5a/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/2acf929dc6ed4e5a/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
      📄 NAME                                              READY   STATUS             RESTARTS       AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-crashloop-command-not-found-55b
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 2
signals: 2
关键日志:
RUNTIME_STARTUP_ERROR: command not found
sh: definitely-missing-command-for-rootcause: not found
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (1m 48.1s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常Pod的详细信息，包括Last State、Exit Code、Reason等关键字段","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e -o yaml","tool_args":{"name":"rc-crashloop-command-not-found-55b7bcd797-rhdvk","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"验证Pod的Last State、Exit Code、Reason等字段，判断是否符合CrashLoopBackOffRuntime的典型特征","evidence_type":"pod_status","target_scope":"aiops-e2e/rc-crashloop-command-not-found-55b7bcd797-rhdvk","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取异常Pod的崩溃前日志，用于分析启动失败原因","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e --previous --tail=200","tool_args":{"name":"rc-crashloop-command-not-found-55b7bcd797-rhdvk","namespace":"aiops-e2e","tail":"200"},"purpose":"验证崩溃前日志是否显示启动命令错误、权限问题、依赖缺失等关键信号","evidence_type":"pod_logs","target_scope":"aiops-e2e/rc-crashloop-command-not-found-55b7bcd797-rhdvk","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取异常Pod的事件，用于分析容器启动失败的上下文","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crashloop-command-not-found-55b7bcd797-rhdvk --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-crashloop-command-not-found-55b7bcd797-rhdvk","sort_by":".lastTimestamp"},"purpose":"验证是否有BackOff、Killing、Liveness probe failed等事件，分析容器反复重启的原因","evidence_type":"pod_events","target_scope":"aiops-e2e/rc-crashloop-command-not-found-55b7bcd797-rhdvk","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                                              READY   STATUS             RESTARTS       AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-crashloop-command-not-found-55b7bcd797-rhdvk   0/1     CrashLoopBackOff   39 (62s ago)   175m   172.16.166.150   node1   <none>           <none>            app=rc-crashloop-command-not-found,pod-template-hash=55b7bcd797,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2acf929dc6ed4e5a/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2acf929dc6ed4e5a/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2acf929dc6ed4e5a/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 2\nsignals: 2\n关键日志:\nRUNTIME_STARTUP_ERROR: command not found\nsh: definitely-missing-command-for-rootcause: not found","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2acf929dc6ed4e5a/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2acf929dc6ed4e5a/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2acf929dc6ed4e5a/tools/002-evidence-kubectl_previous_logs.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 6 个，匹配计划 3 个，未规划证据 3 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":3,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1","description":"获取异常Pod的详细信息，包括Last State、Exit Code、Reason等关键字段","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e -o yaml","purpose":"验证Pod的Last State、Exit Code、Reason等字段，判断是否符合CrashLoopBackOffRuntime的典型特征","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常Pod的崩溃前日志，用于分析启动失败原因","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e --previous --tail=200","purpose":"验证崩溃前日志是否显示启动命令错误、权限问题、依赖缺失等关键信号","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常Pod的事件，用于分析容器启动失败的上下文","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crashloop-command-not-found-55b7bcd797-rhdvk --sort-by='.lastTimestamp'","purpose":"验证是否有BackOff、Killing、Liveness probe failed等事件，分析容器反复重启的原因","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 获取异常Pod的详细信息，包括Last State、Exit Code、Reason等关键字段 | `kubectl get pod rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e ...` |
   | e2 | critical | ✅ | kubectl_previous_logs | 获取异常Pod的崩溃前日志，用于分析启动失败原因 | `kubectl logs rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e --p...` |
   | e3 | important | ✅ | kubectl_events | 获取异常Pod的事件，用于分析容器启动失败的上下文 | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crash...` |

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (14.5s)
   📤 → 下游数据: root_cause=根因分析表明，Pod 'rc-crashloop-command-not-found-55b7bcd797-rhdvk' 处于 CrashLoopBackOff 状态，其直接原因是容器启动命令缺失。日志显示 'command not found'，表明容器启动命令不存在或配置错误。此外，kubectl_events 显示 'Back-off restarting failed container app'，进一步确认了容器启动失败的问题。
   confidence=95%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [], "causal_chain": {}, "root_cause": "根因分析表明，Pod 'rc-crashloop-command-not-found-55b7bcd797-rhdvk' 处于 CrashLoopBackOff 状态，其直接原因是容器启动命令缺失。日志显示 'command not found'，表明容器启动命令不存在或配置错误。此外，kubectl_events 显示 'Back-off restarting failed container app'，进一步确认了容器启动失败的问题。", "root_cause_summary": "根因分析表明，Pod 'rc-crashloop-command-not-found-55b7bcd797-rhdvk' 处于 CrashLoopBackOff 状态，其直接原因是容器启动命令缺失。日志显示 'command not found'，表明容器启动命令不存在或配置错误。此外，kubectl_events 显示 'Back-off restarting failed container app'，进一步确认了容器启动失败的问题。", "confidence": 0.95, "confidence_reason": "", "primary_runbooks": ["pod-crashloop-runtime.md"], "alternative_causes": [], "limitations": "当前分析基于已采集的证据，未进一步验证容器配置文件或镜像内容，可能需要更多上下文信息。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 根因分析表明，Pod 'rc-crashloop-command-not-found-55b7bcd797-rhdvk' 处于 CrashLoopBackOff 状态，其直接原因是容器启动命令缺失。日志显示 'command not found'，表明容器启动命令不存在或配置错误。此外，kubect...
   置信度: 95%

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
   ✅ [汇总总结] 完成 (2m 25.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4000 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 22.6s
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
| **兼容归因层** | L2 - 容器运行时 |
| **问题分类** | CrashLoopBackOffRuntime |
| **置信度** | 高 (95%) |
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
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff, RESTARTS: 38` | Pod 正在不断重启 |
| 2 | 容器崩溃前日志 | `kubectl logs <pod> --previous` | `RUNTIME_STARTUP_ERROR: command not found` | 容器启动命令缺失或配置错误 |
| 3 | Pod 事件 | `kubectl describe pod <pod>` | `Warning BackOff: Back-off restarting failed container` | Kubernetes 检测到容器启动失败并尝试重启 |
| 4 | Pod YAML 定义 | `kubectl get pod -o yaml` | `app=rc-crashloop-command-not-found` | Pod 标签表明其用于测试 CrashLoopBackOff 案例 |
| 5 | 容器退出代码 | `kubectl describe pod <pod>` | `Last State: Terminated, Exit Code: 127` | Exit Code 127 表明命令未找到（command not found） |

### 证据关联分析
- **证据 #2 印证**：`command not found` 直接说明容器启动命令缺失或路径错误。
- **证据 #3 印证**：`Back-off restarting failed container` 说明 Kubernetes 无法成功启动容器。
- **证据 #4 印证**：Pod 的标签表明这是一个用于测试的 Pod，用于模拟 CrashLoopBackOff 场景。
- **证据链**：`command not found` → 容器启动失败 → Kubernetes 重启 → `CrashLoopBackOff` 状态。

### 缺失证据（无）
无缺失证据，所有关键证据均已采集。

---

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 容器启动命令缺失或配置错误（command not found）                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器启动失败 → Kubernetes 重启 → CrashLoopBackOff 状态          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器无法启动，Exit Code 127（command not found）                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 CrashLoopBackOff，持续重启                             │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2（`command not found`）和证据 #5（`Exit Code 127`），问题的根本原因是**容器启动命令缺失或配置错误**，导致容器无法正常启动，Kubernetes 无法成功运行容器，从而进入 `CrashLoopBackOff` 状态。

**置信度**：高 (95%)
- ✅ `command not found` 明确指出命令不存在
- ✅ `Exit Code 127` 确认命令未找到
- ✅ `kubectl_events` 显示 Kubernetes 无法启动容器并不断尝试重启

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 检查容器启动命令配置**
```bash
kubectl get deployment rc-crashloop-command-not-found -n aiops-e2e -o jsonpath='{.spec.template.spec.containers[*].command}'
```
*目的*：确认容器的启动命令是否正确配置，例如是否缺少可执行文件路径或命令拼写错误。

**2. [可选] 修改容器启动命令**
```bash
kubectl set image deployment/rc-crashloop-command-not-found -n aiops-e2e app=your-correct-image:tag
```
*目的*：如果命令配置错误，可以通过修改镜像或命令字段修复。

### 后续优化
1. **验证镜像内容**：确保容器镜像中存在启动命令所需的可执行文件。
2. **配置健康检查**：为容器添加 `livenessProbe` 和 `readinessProbe`，以便 Kubernetes 更早检测异常。
3. **监控日志**：配置日志收集和告警，便于快速发现类似问题。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e` | STATUS: Running |
| 2. 检查容器命令 | `kubectl get pod rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e -o jsonpath='{.spec.containers[*].command}'` | 显示正确的启动命令 |
| 3. 查看容器日志 | `kubectl logs rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e` | 无 `command not found` 错误 |

---

## ⚠️ 注意事项
- 如果此 Pod 是测试用例的一部分，可考虑删除或忽略。
- 如果此 Pod 是实际业务应用，请尽快修复启动命令或镜像配置。
- 建议为容器配置 `livenessProbe`，以便 Kubernetes 更早检测并重启异常容器。

---

---

## 📊 性能统计

├─ 总耗时: 5.4m
├─ 问题定位: 54.8s (17%) ✅
├─ 证据链采集: 108.1s (33%) ✅
├─ 根因分析: 14.5s (4%) ✅
├─ 汇总总结: 145.3s (45%) ✅
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
