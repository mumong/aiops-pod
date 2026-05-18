======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 3c4dd256f1be445d]

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
      📄 NAME                                      READY   STATUS             RESTARTS         AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-crashloop-exit-code-5db5947859-gk6cf  
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-crashloop-exit-code-5db5947859-gk6cf
namespace: aiops-e2e
creationTimestamp: 2026-05-14T13:49:22Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: No
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
4m8s (x184 over 44m)   Warning   BackOff          Pod/rc-crashloop-exit-code-5db5947859-gk6cf   Back-off restarting failed container app in pod rc-crashloop-exit-code-5db5947
   💭 [问题定位] {
  "layer": "L2",
  "derived_layer": "L2",
  "layers": ["L2"],
  "layer_name": "容器运行时异常",
  "confidence": "high",
  "reasoning": "当前异常 Pod rc-crashloop-exit-code-5db5947859-gk6cf 处于 CrashLoopBackOff 状态，Exit Code 为 2，表明容器进程启动失败或运行时退出。通过日志发现关键错误信息 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'，且 Events 中反复出现 'Back-off restarting failed container app'。根据判定规则，CrashLoopBackOff + Exit Code 非 137 + 命令/进程错误，归类为 CrashLoopBackOffRuntime，兼容归因 L2。",
  "abnormal_pods": [
    {
      "name": "rc-crashloop-exit-code-5db5947859-gk6cf",
      "namespace": "aiops-e2e",
      "status": "CrashLoopBackOff",
      "restarts": "13 (2m26s ago)",
      "ip": "172.16.166.139",
      "node": "node1"
    }
  ],
  "abnormal_groups": [
    {
      "type": "CrashLoopBackOffRuntime",
      "count": 1,
      "pods": [
        "rc-crashloop-exit-code-5db5947859-gk6cf"
      ]
    }
  ],
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "CrashLoopBackOffRuntime",
  "status_category": "CrashLoopBackOff",
  "key_entities": [
    {
      "entity": "rc-crashloop-exit-code-5db5947859-gk6cf",
      "type": "Pod",
      "namespace": "aiops-e2e",
      "status": "CrashLoopBackOff"
    },
    {
      "entity": "app",
      "type": "Container",
      "pod": "rc-crashloop-exit-code-5db5947859-gk6cf",
      "exit_code": 2
    }
  ],
  "possible_scenarios": [
    {
      "scenario": "容器主进程启动失败，Exit Code 为 2，日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'。可能是命令/args 错误、入口脚本错误、应用配置异常或依赖缺失。",
      "confidence": "high"
    },
    {
      "scenario": "容器内进程启动后立即退出，可能是容器内的应用程序逻辑错误，例如初始化失败或配置校验失败，但未涉及配置缺失或 OOM。",
      "confidence": "medium"
    }
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 10.9s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[{'scenario': "容器主进程启动失败，Exit Code 为 2，日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'。可能是命令/args 错误、入口脚本错误、应用配置异常或依赖缺失。", 'probability': 'high', 'reason': 'CrashLoopBackOff + Exit Code 非 137 + 命令/进程错误'}]
   entities=[{"type": "Pod", "name": "rc-crashloop-exit-code-5db5947859-gk6cf", "namespace": "aiops-e2e"}, {"type": "Container", "name": "app", "namespace": "aiops-e2e"}]
   reasoning=当前异常 Pod rc-crashloop-exit-code-5db5947859-gk6cf 处于 CrashLoopBackOff 状态，Exit Code 为 2，表明容器进程启动失败或运行时退出。通过日志发现关键错误信息 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'，且 Events 中反复出现 'Back-off restarting failed container app'。根据判定规则，CrashLoopBackOff + Exit Code 非 137 + 命令/进程错误，归类为 CrashLoopBackOffRuntime，兼容归因 L2。
   layer_analysis={"layer": "L2", "derived_layer": "L2", "layers": ["L2"], "layer_name": "容器运行时异常", "confidence": 1.0, "reasoning": "当前异常 Pod rc-crashloop-exit-code-5db5947859-gk6cf 处于 CrashLoopBackOff 状态，Exit Code 为 2，表明容器进程启动失败或运行时退出。通过日志发现关键错误信息 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'，且 Events 中反复出现 'Back-off restarting failed container app'。根据判定规则，CrashLoopBackOff + Exit Code 非 137 + 命令/进程错误，归类为 CrashLoopBackOffRuntime，兼容归因 L2。", "abnormal_pods": [{"name": "rc-crashloop-exit-code-5db5947859-gk6cf", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "CrashLoopBackOffRuntime", "status_category": "CrashLoopBackOff", "key_entities": [{"type": "Pod", "name": "rc-crashloop-exit-code-5db5947859-gk6cf", "namespace": "aiops-e2e"}, {"type": "Container", "name": "app", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "容器主进程启动失败，Exit Code 为 2，日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'。可能是命令/args 错误、入口脚本错误、应用配置异常或依赖缺失。", "probability": "high", "reason": "CrashLoopBackOff + Exit Code 非 137 + 命令/进程错误"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-exit-code-5db5947859-gk6cf"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-exit-code-5db5947859-gk6cf"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-crashloop-exit-code-5db5947859-gk6cf             0/1     CrashLoopBackOff   13 (2m21s ago)   43m    172.16.166.139   node1    <none>           <none>            app=rc-crashloop-exit-code,pod-template-hash=5db5947859,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/3c4dd256f1be445d/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/3c4dd256f1be445d/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/3c4dd256f1be445d/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                      READY   STATUS             RESTARTS       AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-crashloop-exit-code-5db5947859-gk6cf   0
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (3m 1.7s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod rc-crashloop-exit-code-5db5947859-gk6cf 的详细信息，包括 Last State、Exit Code 和重启次数","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o yaml","tool_args":{"name":"rc-crashloop-exit-code-5db5947859-gk6cf","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"验证 Pod 的 Last State、Exit Code、重启次数等关键状态信息","evidence_type":"Pod Status","target_scope":"aiops-e2e/rc-crashloop-exit-code-5db5947859-gk6cf","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod rc-crashloop-exit-code-5db5947859-gk6cf 的崩溃前日志","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous --tail=200","tool_args":{"name":"rc-crashloop-exit-code-5db5947859-gk6cf","namespace":"aiops-e2e","tail":"200"},"purpose":"验证崩溃前的日志，查找 'RUNTIME_STARTUP_ERROR' 或其他异常信息","evidence_type":"Pod Logs","target_scope":"aiops-e2e/rc-crashloop-exit-code-5db5947859-gk6cf","acceptable_tools":["kubectl_previous_logs"],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod rc-crashloop-exit-code-5db5947859-gk6cf 的 Events 信息","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crashloop-exit-code-5db5947859-gk6cf --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-crashloop-exit-code-5db5947859-gk6cf","sort_by":".lastTimestamp"},"purpose":"验证与该 Pod 相关的 Events，如 BackOff、Killing 等","evidence_type":"Pod Events","target_scope":"aiops-e2e/rc-crashloop-exit-code-5db5947859-gk6cf","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                                      READY   STATUS             RESTARTS       AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-crashloop-exit-code-5db5947859-gk6cf   0/1     CrashLoopBackOff   14 (64s ago)   47m   172.16.166.139   node1   <none>           <none>            app=rc-crashloop-exit-code,pod-template-hash=5db5947859,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/3c4dd256f1be445d/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/3c4dd256f1be445d/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/3c4dd256f1be445d/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 1\n关键日志:\nRUNTIME_STARTUP_ERROR: rc crashloop exits with code 2","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/3c4dd256f1be445d/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/3c4dd256f1be445d/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/3c4dd256f1be445d/tools/002-evidence-kubectl_previous_logs.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 7 个，匹配计划 3 个，未规划证据 4 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":7,"matched_tool_count":3,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod rc-crashloop-exit-code-5db5947859-gk6cf 的详细信息，包括 Last State、Exit Code 和重启次数","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o yaml","purpose":"验证 Pod 的 Last State、Exit Code、重启次数等关键状态信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod rc-crashloop-exit-code-5db5947859-gk6cf 的崩溃前日志","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous --tail=200","purpose":"验证崩溃前的日志，查找 'RUNTIME_STARTUP_ERROR' 或其他异常信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod rc-crashloop-exit-code-5db5947859-gk6cf 的 Events 信息","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crashloop-exit-code-5db5947859-gk6cf --sort-by='.lastTimestamp'","purpose":"验证与该 Pod 相关的 Events，如 BackOff、Killing 等","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 获取异常 Pod rc-crashloop-exit-code-5db5947859-gk... | `kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o yaml` |
   | e2 | critical | ✅ | kubectl_previous_logs | 获取异常 Pod rc-crashloop-exit-code-5db5947859-gk... | `kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous ...` |
   | e3 | important | ✅ | kubectl_events | 获取异常 Pod rc-crashloop-exit-code-5db5947859-gk... | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crash...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (31.6s)
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
   ✅ [汇总总结] 完成 (1m 30.9s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4022 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 6m 15.2s
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
| **兼容归因层** | L2 |
| **问题分类** | CrashLoopBackOffRuntime（容器启动失败或运行时退出） |
| **置信度** | 高 |
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
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff, RESTARTS: 13` | Pod 处于持续重启状态 |
| 2 | 崩溃前日志 | `kubectl logs <pod> --previous` | `RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2` | 容器主进程启动失败，Exit Code 为 2 |
| 3 | Events | `kubectl describe pod` | `Back-off restarting failed container app` | 容器反复启动失败，Kubernetes 进行重启回退 |
| 4 | Pod YAML | `kubectl get pod -o yaml` | `restartPolicy: Always` | Pod 设置为 Always 重启策略，导致循环重启 |

### 证据关联分析

- **证据 #1 + #2 印证**：CrashLoopBackOff + Exit Code 2（非 137）+ 日志显示启动错误 → 容器主进程启动失败。
- **证据 #3 印证**：Events 显示 Kubernetes 正在进行 Back-off 重启，进一步确认容器失败。
- **证据 #4 印证**：Pod 设置为 Always 重启策略，导致容器在失败后自动重启，进入 CrashLoopBackOff 状态。

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 容器主进程启动失败，Exit Code 为 2，日志显示 'RUNTIME_STARTUP_ERROR'，表明命令、脚本、配置或依赖异常。│
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器进程启动失败 → Kubernetes 重启容器 → 重启失败 → CrashLoopBackOff 状态。│
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器启动失败，Exit Code 为 2，日志显示 'RUNTIME_STARTUP_ERROR'。│
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CrashLoopBackOff，持续重启。                        │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (CrashLoopBackOff, 重启 13 次)、证据 #2 (Exit Code 2, 日志显示 `RUNTIME_STARTUP_ERROR`) 和证据 #3 (Events 显示 Back-off 重启)，问题的根本原因是**容器主进程启动失败**，可能是由于命令/args 错误、入口脚本错误、应用配置异常或依赖缺失导致。

**置信度**：高 (85%)

- ✅ Exit Code 2 表示启动失败
- ✅ 日志显示 `RUNTIME_STARTUP_ERROR`
- ✅ Events 显示 Kubernetes 正在进行 Back-off 重启

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 查看崩溃前日志，定位启动失败原因**
```bash
kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous
```
*目的*：查看详细的启动错误信息，确定 Exit Code 2 的具体原因（例如命令不存在、脚本错误、配置缺失等）。

**2. [可选] 检查容器启动命令和入口点**
```bash
kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o jsonpath='{.spec.containers[0].command}'
```
*目的*：确认容器启动命令是否正确，是否存在拼写错误或路径错误。

**3. [可选] 检查容器启动脚本或入口文件是否存在**
```bash
kubectl exec -it rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -- ls /path/to/entrypoint
```
*目的*：确认容器启动脚本或入口文件是否存在于指定路径，权限是否正确。

### 后续优化

1. **调整启动命令或配置**：根据日志信息，修复命令、脚本或配置错误。
2. **配置健康检查探针**：设置 `livenessProbe` 和 `readinessProbe`，提高容器的自我恢复能力。
3. **监控和告警**：配置 Prometheus 或 Kubernetes 内置监控，对 Pod 状态和重启次数进行告警。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |
| 3. 查看日志 | `kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e` | 应无错误信息，或显示正常启动日志 |

---

## ⚠️ 注意事项

- 如果容器仍然失败，请进一步检查镜像是否完整、依赖是否正确安装。
- 如果 Exit Code 为 2 且日志未明确指出问题，可尝试在容器中手动执行启动命令，验证其行为。
- 如果是脚本问题，建议使用 `sh -x` 或 `bash -x` 执行脚本以获取更详细的调试信息。

---

## 📊 性能统计

├─ 总耗时: 6.3m
├─ 问题定位: 70.9s (19%) ✅
├─ 证据链采集: 181.7s (48%) ✅
├─ 根因分析: 31.6s (8%) ✅
├─ 汇总总结: 90.9s (24%) ✅
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
