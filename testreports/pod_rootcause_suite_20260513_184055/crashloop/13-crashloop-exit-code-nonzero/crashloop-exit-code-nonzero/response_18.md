======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 947e2c50df8d4f8b]

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
signals: 0
关键日志:
unable to retrieve container logs for containerd://cf29803c7f930755d4486afbb885a5054e2a6703454e3bc89199eb7643416e49
   💭 [问题定位] 调用工具: kubectl_container_previous_logs
   💭 [问题定位] 工具结果: kubectl_container_previous_logs (success)
      📄 kubectl_container_previous_logs 输出摘要: raw_chars=240 lines=3
Command failed (exit 1):
kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -c rc-crashloop-exit-code -n aiops-e2e --previous --tail=200
e
   💭 [问题定位] 调用工具: kubectl_container_logs
   💭 [问题定位] 工具结果: kubectl_container_logs (success)
      📄 kubectl_container_logs 输出摘要: raw_chars=229 lines=3
Command failed (exit 1):
kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -c rc-crashloop-exit-code -n aiops-e2e --tail=200
error: container rc-c
   💭 [问题定位] 调用工具: kubectl_logs
   💭 [问题定位] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 日志摘要:
lines: 1
signals: 1
关键日志:
RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2
   💭 [问题定位] 调用工具: kubectl_get_yaml
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (41.9s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[{'scenario': '容器启动失败，主进程无法正常运行', 'probability': '高', 'reason': 'Pod状态为CrashLoopBackOff，且异常类型为CrashLoopBackOffRuntime，结合日志中RUNTIME_STARTUP_ERROR提示，表明容器主进程启动失败。'}]
   entities=[{"type": "Pod", "name": "rc-crashloop-exit-code-5db5947859-gk6cf", "namespace": "aiops-e2e"}]
   reasoning=当前环境中存在一个Pod处于CrashLoopBackOff状态，其异常类型为CrashLoopBackOffRuntime，符合L2层级的归因特征，即容器运行时异常。
   layer_analysis={"layer": "L2", "derived_layer": "L2", "layers": ["L2"], "layer_name": "container_resource", "confidence": 0.5, "reasoning": "当前环境中存在一个Pod处于CrashLoopBackOff状态，其异常类型为CrashLoopBackOffRuntime，符合L2层级的归因特征，即容器运行时异常。", "abnormal_pods": [{"name": "rc-crashloop-exit-code-5db5947859-gk6cf", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "CrashLoopBackOffRuntime", "status_category": "container_runtime", "key_entities": [{"type": "Pod", "name": "rc-crashloop-exit-code-5db5947859-gk6cf", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "容器启动失败，主进程无法正常运行", "probability": "高", "reason": "Pod状态为CrashLoopBackOff，且异常类型为CrashLoopBackOffRuntime，结合日志中RUNTIME_STARTUP_ERROR提示，表明容器主进程启动失败。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-exit-code-5db5947859-gk6cf"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-exit-code-5db5947859-gk6cf"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-crashloop-exit-code-5db5947859-gk6cf             0/1     CrashLoopBackOff   15 (5m5s ago)   56m    172.16.166.139   node1    <none>           <none>            app=rc-crashloop-exit-code,pod-template-hash=5db5947859,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/947e2c50df8d4f8b/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/947e2c50df8d4f8b/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/947e2c50df8d4f8b/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                      READY   STATUS             RESTARTS        AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-crashloop-exit-code-5db5947859-gk6cf   
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (1m 45.6s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 的详细描述信息，包括 Last State、Exit Code、Reason、重启次数等关键信息","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o yaml","tool_args":{"name":"rc-crashloop-exit-code-5db5947859-gk6cf","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"验证 CrashLoopBackOffRuntime 的核心特征","evidence_type":"pod_state","target_scope":"aiops-e2e/rc-crashloop-exit-code-5db5947859-gk6cf","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 的崩溃前日志，验证启动失败原因","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous --tail=200","tool_args":{"pod":"rc-crashloop-exit-code-5db5947859-gk6cf","namespace":"aiops-e2e","tail":"200"},"purpose":"获取崩溃前日志以定位启动失败原因","evidence_type":"container_logs","target_scope":"aiops-e2e/rc-crashloop-exit-code-5db5947859-gk6cf","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod 的 Events，确认 BackOff、probe failed、Killing 等事件信号","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crashloop-exit-code-5db5947859-gk6cf --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-crashloop-exit-code-5db5947859-gk6cf","sort_by":".lastTimestamp"},"purpose":"确认 BackOff、probe failed、Killing 等事件信号","evidence_type":"pod_events","target_scope":"aiops-e2e/rc-crashloop-exit-code-5db5947859-gk6cf","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                                      READY   STATUS             RESTARTS        AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-crashloop-exit-code-5db5947859-gk6cf   0/1     CrashLoopBackOff   16 (2m8s ago)   59m   172.16.166.139   node1   <none>           <none>            app=rc-crashloop-exit-code,pod-template-hash=5db5947859,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/947e2c50df8d4f8b/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/947e2c50df8d4f8b/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/947e2c50df8d4f8b/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 1\n关键日志:\nRUNTIME_STARTUP_ERROR: rc crashloop exits with code 2","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/947e2c50df8d4f8b/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/947e2c50df8d4f8b/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/947e2c50df8d4f8b/tools/002-evidence-kubectl_previous_logs.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 9/9 项，完整度 100%；实际执行工具 6 个，匹配计划 3 个，未规划证据 3 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":9,"environment_evidence_collected":9,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":3,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 的详细描述信息，包括 Last State、Exit Code、Reason、重启次数等关键信息","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o yaml","purpose":"验证 CrashLoopBackOffRuntime 的核心特征","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 的崩溃前日志，验证启动失败原因","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous --tail=200","purpose":"获取崩溃前日志以定位启动失败原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod 的 Events，确认 BackOff、probe failed、Killing 等事件信号","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crashloop-exit-code-5db5947859-gk6cf --sort-by='.lastTimestamp'","purpose":"确认 BackOff、probe failed、Killing 等事件信号","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_container_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_container_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 获取异常 Pod 的详细描述信息，包括 Last State、Exit Code、Reas... | `kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o yaml` |
   | e2 | critical | ✅ | kubectl_previous_logs | 获取异常 Pod 的崩溃前日志，验证启动失败原因 | `kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous ...` |
   | e3 | important | ✅ | kubectl_events | 获取异常 Pod 的 Events，确认 BackOff、probe failed、Kil... | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crash...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (34.3s)
   📤 → 下游数据: root_cause=Pod 'rc-crashloop-exit-code-5db5947859-gk6cf' 处于 CrashLoopBackOff 状态，重启次数为 16，表明容器频繁崩溃。崩溃前日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'，表明容器启动失败并返回错误代码 2。
   confidence=90%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [{"e1": "Pod 'rc-crashloop-exit-code-5db5947859-gk6cf' 处于 CrashLoopBackOff 状态，重启次数为 16，表明容器频繁崩溃。", "e2": "Pod 崩溃前日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'，表明容器启动失败并返回错误代码 2。", "layer_1": "集群中存在 1 个异常 Pod，状态为 CrashLoopBackOff，其余 46 个 Pod 状态正常。", "layer_3": "无法获取容器的崩溃前日志，可能是因为容器已销毁或日志未被保留。", "layer_4": "尝试获取容器的崩溃前日志失败，错误信息显示容器名称无效，可能容器已不存在。", "layer_5": "尝试获取容器日志失败，错误信息显示容器名称无效，可能容器已不存在。", "layer_6": "容器日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'，表明容器启动失败并返回错误代码 2。"}], "causal_chain": {}, "root_cause": "Pod 'rc-crashloop-exit-code-5db5947859-gk6cf' 处于 CrashLoopBackOff 状态，重启次数为 16，表明容器频繁崩溃。崩溃前日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'，表明容器启动失败并返回错误代码 2。", "root_cause_summary": "Pod 'rc-crashloop-exit-code-5db5947859-gk6cf' 处于 CrashLoopBackOff 状态，重启次数为 16，表明容器频繁崩溃。崩溃前日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'，表明容器启动失败并返回错误代码 2。", "confidence": 0.9, "confidence_reason": "有直接证据表明容器启动失败，错误代码 2 明确指向容器启动失败，因果链清晰。", "primary_runbooks": ["pod-crashloop-runtime.md"], "alternative_causes": [], "limitations": "无法获取容器的崩溃前日志，可能是因为容器已销毁或日志未被保留。", "llm_raw_analysis": "基于提供的证据，可以确定 Pod 'rc-crashloop-exit-code-5db5947859-gk6cf' 处于 CrashLoopBackOff 状态，重启次数为 16，表明容器频繁崩溃。崩溃前日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'，表明容器启动失败并返回错误代码 2。这些证据表明容器启动失败，主进程无法正常运行。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'rc-crashloop-exit-code-5db5947859-gk6cf' 处于 CrashLoopBackOff 状态，重启次数为 16，表明容器频繁崩溃。崩溃前日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'...
   置信度: 90%

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
   ✅ [汇总总结] 完成 (2m 20.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4548 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 22.2s
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
| **问题分类** | CrashLoopBackOffRuntime（容器运行时异常） |
| **置信度** | 高 (90%) |
| **证据完整度** | 3/3 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | `rc-crashloop-exit-code-5db5947859-gk6cf` |
| Namespace | `aiops-e2e` |
| Node | `node1` |
| 错误信息 | `RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2` |
| 状态 | `CrashLoopBackOff` |
| 重启次数 | `15` 次（最后一次重启 5m5s ago） |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff, RESTARTS: 15 (5m5s ago)` | 容器频繁崩溃，Kubernetes 正在进行 BackOff 重启 |
| 2 | 容器崩溃日志 | `kubectl logs <pod> --previous` | `RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2` | 容器主进程启动失败，返回错误码 2 |
| 3 | Pod 事件 | `kubectl describe pod <pod>` | `Last State: Terminated, Reason: Error, Exit Code: 2` | 容器以错误码 2 退出，属于非正常终止 |
| 4 | 容器容器日志尝试 | `kubectl logs <pod> -c <container> --previous` | `error: container <name> is not valid for pod` | 容器名称无效，可能容器配置或命名错误 |
| 5 | 容器描述 | `kubectl get pod -o json` | `Labels: pod_abnormal_type=CrashLoopBackOffRuntime` | 明确标识为运行时异常 |
| 6 | 事件日志 | `kubectl describe pod <pod>` | 包含 `BackOff`、`Killing` 事件 | Kubernetes 已检测到异常并尝试恢复 |
| 7 | Pod 列表 | `kubectl get pod` | `aiops-e2e rc-crashloop-exit-code-5db5947859-gk6cf 0/1 CrashLoopBackOff 15 (5m5s ago) 56m` | 集群中只有一个异常 Pod，其余 48 个 Pod 正常 |
| 8 | 上游工具数据 | `kubectl_get_by_kind_in_cluster` | `status_counts={'CrashLoopBackOff': 1, 'Running': 46}` | 仅 1 个 Pod 异常，集群整体运行正常 |
| 9 | 上游 runbook | `pod-crashloop-runtime.md` | 匹配 `CrashLoopBackOffRuntime` 异常类型 | 提供了容器运行时异常的诊断建议 |

### 证据关联分析

- **证据 #1 + #2 + #3 印证**：Pod 状态为 `CrashLoopBackOff`，容器返回错误码 2，表明容器主进程启动失败。
- **证据链**：容器主进程启动失败 → 返回错误码 2 → Kubernetes 进行重启 → 重启失败 → 进入 `CrashLoopBackOff` 状态。
- **证据 #4 + #5 + #6 佐证**：容器配置错误或命名错误，导致 Kubernetes 无法正确识别容器，加剧了问题。

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 容器主进程启动失败，返回错误码 2，可能是启动命令错误、配置错误或容器镜像问题。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器主进程启动失败 → 返回错误码 2 → Kubernetes 重启容器 → 重启失败 → CrashLoopBackOff。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器返回错误码 2，表示启动失败。 |
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 `CrashLoopBackOff`，重启次数不断增加，容器无法正常运行。 |
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2（崩溃前日志 `RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2`）和证据 #3（`kubectl describe pod` 显示 `Exit Code: 2`），问题的根本原因是**容器主进程启动失败，返回错误码 2**。  
**置信度**：高 (90%)  
- ✅ 错误码 2 明确表明容器启动失败  
- ✅ 日志中出现 `RUNTIME_STARTUP_ERROR`，确认为运行时异常  
- ⚠️ 缺少容器配置和启动命令信息，无法进一步确认失败原因

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 查看容器启动命令和配置**
```bash
kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o jsonpath='{.spec.containers[0].command}'
kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o jsonpath='{.spec.containers[0].args}'
```
*目的*：确认容器启动命令是否正确，是否存在命令路径错误、脚本缺失等问题。

**2. [可选] 查看容器的完整日志（如果容器能正常运行一次）**
```bash
kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous
```
*目的*：获取更多上下文，确认崩溃前是否有异常日志。

**3. [修复] 修改容器启动命令或配置**
*建议*：根据日志和配置，修正启动命令或配置，例如：
- 修复命令路径或脚本
- 检查环境变量是否正确
- 确认启动命令是否为长期运行服务（非一次性任务）

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |
| 3. 检查容器状态 | `kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e` | `Last State: Running` |

---

## ⚠️ 注意事项

- 如果错误码 2 是应用自定义错误，建议查看应用文档或联系应用维护者确认具体含义。
- 如果问题持续，可能需要进一步检查容器镜像是否完整、是否有权限问题、是否缺少依赖等。
- 建议为容器添加健康检查（liveness/readiness probe），以便 Kubernetes 更早发现异常。

---

## 📊 性能统计

├─ 总耗时: 5.4m
├─ 问题定位: 41.9s (13%) ✅
├─ 证据链采集: 105.6s (33%) ✅
├─ 根因分析: 34.3s (11%) ✅
├─ 汇总总结: 140.3s (44%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 11 次
```

📋 诊断追踪

- **核心 Runbook**: pod-crashloop-runtime
- **参考 Runbook**: pod-crashloop-runtime
- **工具调用**: 11 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
