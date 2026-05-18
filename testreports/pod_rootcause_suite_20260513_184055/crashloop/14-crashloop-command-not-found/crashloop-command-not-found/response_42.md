======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 5fe2bd9e27724d2c]

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
      📄 NAME                                              READY   STATUS   RESTARTS        AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-crashloop-command-not-found-55b7bcd797-r
   💭 [问题定位] 调用工具: kubectl_logs
   💭 [问题定位] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 日志摘要:
lines: 2
signals: 2
关键日志:
RUNTIME_STARTUP_ERROR: command not found
sh: definitely-missing-command-for-rootcause: not found
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 0
关键日志:
unable to retrieve container logs for containerd://d85bdf341992a9cc088e2c3de5a66b33aa8d941e263214c5c585d997ac25a0c3
   💭 [问题定位] 调用工具: kubectl_container_logs
   💭 [问题定位] 工具结果: kubectl_container_logs (success)
      📄 kubectl_container_logs 输出摘要: raw_chars=261 lines=3
Command failed (exit 1):
kubectl logs rc-crashloop-command-not-found-55b7bcd797-rhdvk -c rc-crashloop-command-not-found -n aiops-e2e --tail=200
error
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
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (46.9s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[{'scenario': '容器启动命令错误或缺失', 'probability': '高', 'reason': "日志显示'command not found'，表明容器启动命令错误或缺失。"}]
   entities=[{"type": "Pod", "name": "rc-crashloop-command-not-found-55b7bcd797-rhdvk", "namespace": "aiops-e2e"}]
   reasoning=当前环境中存在1个异常Pod：rc-crashloop-command-not-found-55b7bcd797-rhdvk，状态为CrashLoopBackOff。结合日志信息，关键异常表现为'command not found'，表明容器启动命令错误或缺失。根据五层模型，CrashLoopBackOff + command错误属于L2层级，归因于container_resource。
   layer_analysis={"layer": "L2", "derived_layer": "L2", "layers": ["L2"], "layer_name": "container_resource", "confidence": 0.85, "reasoning": "当前环境中存在1个异常Pod：rc-crashloop-command-not-found-55b7bcd797-rhdvk，状态为CrashLoopBackOff。结合日志信息，关键异常表现为'command not found'，表明容器启动命令错误或缺失。根据五层模型，CrashLoopBackOff + command错误属于L2层级，归因于container_resource。", "abnormal_pods": [{"name": "rc-crashloop-command-not-found-55b7bcd797-rhdvk", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "CrashLoopBackOffRuntime", "status_category": "container_resource", "key_entities": [{"type": "Pod", "name": "rc-crashloop-command-not-found-55b7bcd797-rhdvk", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "容器启动命令错误或缺失", "probability": "高", "reason": "日志显示'command not found'，表明容器启动命令错误或缺失。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-command-not-found-55b7bcd797-rhdvk"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-command-not-found-55b7bcd797-rhdvk"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-crashloop-command-not-found-55b7bcd797-rhdvk     0/1     CrashLoopBackOff   33 (5m3s ago)   148m    172.16.166.150   node1    <none>           <none>            app=rc-crashloop-command-not-found,pod-template-hash=55b7bcd797,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/5fe2bd9e27724d2c/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/5fe2bd9e27724d2c/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/5fe2bd9e27724d2c/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L2
   置信度: 85%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                              READY   STATUS             RESTARTS         AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-crashloop-command-not-found-5
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 2
signals: 2
关键日志:
RUNTIME_STARTUP_ERROR: command not found
sh: definitely-missing-command-for-rootcause: not found
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (1m 46.6s)
   📤 → 下游数据: evidence_items=8/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 的详细信息，包括 Last State、Exit Code、Reason 和重启次数等关键字段。","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e -o yaml","tool_args":{"name":"rc-crashloop-command-not-found-55b7bcd797-rhdvk","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"验证异常 Pod 的详细状态信息，包括 Last State、Exit Code、Reason 和重启次数等。","evidence_type":"state_verification","target_scope":"Pod/aiops-e2e/rc-crashloop-command-not-found-55b7bcd797-rhdvk","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 的崩溃前日志，用于分析容器启动失败的具体原因。","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e --previous --tail=200","tool_args":{"name":"rc-crashloop-command-not-found-55b7bcd797-rhdvk","namespace":"aiops-e2e","tail":"200","previous":true},"purpose":"获取崩溃前日志，分析容器启动失败的具体原因。","evidence_type":"log_verification","target_scope":"Pod/aiops-e2e/rc-crashloop-command-not-found-55b7bcd797-rhdvk","acceptable_tools":["kubectl_previous_logs"],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod 的事件列表，用于检查 BackOff、probe failed、Killing 等关键事件。","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crashloop-command-not-found-5m3s-ago --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-crashloop-command-not-found-5m3s-ago","sort_by":".lastTimestamp"},"purpose":"获取异常 Pod 的事件列表，用于检查 BackOff、probe failed、Killing 等关键事件。","evidence_type":"event_verification","target_scope":"Pod/aiops-e2e/rc-crashloop-command-not-found-55b7bcd797-rhdvk","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                                              READY   STATUS             RESTARTS         AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-crashloop-command-not-found-55b7bcd797-rhdvk   0/1     CrashLoopBackOff   34 (2m22s ago)   151m   172.16.166.150   node1   <none>           <none>            app=rc-crashloop-command-not-found,pod-template-hash=55b7bcd797,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/5fe2bd9e27724d2c/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/5fe2bd9e27724d2c/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/5fe2bd9e27724d2c/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 2\nsignals: 2\n关键日志:\nRUNTIME_STARTUP_ERROR: command not found\nsh: definitely-missing-command-for-rootcause: not found","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/5fe2bd9e27724d2c/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/5fe2bd9e27724d2c/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/5fe2bd9e27724d2c/tools/002-evidence-kubectl_previous_logs.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 3 项，实际采集 2 项，未采集 1 项，完整度 67%；其中真实环境证据 8/9 项，完整度 89%；实际执行工具 6 个，匹配计划 2 个，未规划证据 4 个","plan_total":3,"plan_collected":2,"plan_completeness":0.6666666666666666,"environment_evidence_total":9,"environment_evidence_collected":8,"environment_evidence_completeness":0.8888888888888888,"executed_tool_count":6,"matched_tool_count":2,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 的详细信息，包括 Last State、Exit Code、Reason 和重启次数等关键字段。","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e -o yaml","purpose":"验证异常 Pod 的详细状态信息，包括 Last State、Exit Code、Reason 和重启次数等。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 的崩溃前日志，用于分析容器启动失败的具体原因。","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e --previous --tail=200","purpose":"获取崩溃前日志，分析容器启动失败的具体原因。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod 的事件列表，用于检查 BackOff、probe failed、Killing 等关键事件。","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crashloop-command-not-found-5m3s-ago --sort-by='.lastTimestamp'","purpose":"获取异常 Pod 的事件列表，用于检查 BackOff、probe failed、Killing 等关键事件。","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_container_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e3(获取异常 Pod 的事件列表，用于检查 BackOff、probe failed、Killing 等关键事件。): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/3 项, 完整度: 89%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 获取异常 Pod 的详细信息，包括 Last State、Exit Code、Reason... | `kubectl get pod rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e ...` |
   | e2 | critical | ✅ | kubectl_previous_logs | 获取异常 Pod 的崩溃前日志，用于分析容器启动失败的具体原因。 | `kubectl logs rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e --p...` |
   | e3 | important | ❌ | kubectl_events | 获取异常 Pod 的事件列表，用于检查 BackOff、probe failed、Kill... | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crash...` |

   ⚠️ 未采集原因:
   - e3(获取异常 Pod 的事件列表，用于检查 BackOff、probe failed、Killing 等关键事件。): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (18.1s)
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
   ✅ [汇总总结] 完成 (1m 12.9s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4141 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 4.6s
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
| **兼容归因层** | L2 - container_resource |
| **问题分类** | CrashLoopBackOffRuntime（容器启动命令错误或缺失） |
| **置信度** | 高 (85%) |
| **证据完整度** | 2/3 (67%) |

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
| 错误信息 | command not found，sh: definitely-missing-command-for-rootcause: not found |

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod -n aiops-e2e` | `STATUS: CrashLoopBackOff, RESTARTS: 34` | Pod 处于持续重启状态 |
| 2 | 日志信息 | `kubectl logs rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e` | `RUNTIME_STARTUP_ERROR: command not found` | 容器启动命令缺失或错误 |
| 3 | 崩溃前日志 | `kubectl logs rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e --previous` | `sh: definitely-missing-command-for-rootcause: not found` | 确认命令缺失 |
| 4 | Pod YAML | `kubectl get pod rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e -o yaml` | `annotations: aiops.e2e/runbook: pod-crashloop-runtime.md` | 提供诊断上下文 |

### 证据关联分析
- **证据 #1 + #2 印证**：Pod 状态为 `CrashLoopBackOff` 且日志显示 `command not found`，表明容器启动命令错误或缺失。
- **证据链**：容器启动命令缺失 → 启动失败 → 容器退出 → Pod 重启 → 持续循环。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| Pod 事件列表 | important | 无法确认是否由探针失败或 BackOff 机制触发 |

---

## 🎯 根因分析
### 因果链
```
┌──────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                 │
│ 容器启动命令缺失或错误，具体表现为 'definitely-missing-command-for-rootcause: not found' │
└──────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                 │
│ 容器启动命令缺失或错误 → 容器启动失败 → 容器退出 → Pod 重启              │
└──────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                 │
│ 容器启动失败，Exit Code 为非 0（隐含于 CrashLoopBackOff）                │
└──────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                             │
│ Pod 状态为 CrashLoopBackOff，重启次数持续增加                           │
└──────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2 和 #3，容器启动命令缺失或错误，具体表现为 `definitely-missing-command-for-rootcause: not found`，导致容器启动失败，进而触发 `CrashLoopBackOff` 状态。  
**置信度**：高 (85%)  
- ✅ 日志明确指出 `command not found`  
- ✅ Pod 状态为 `CrashLoopBackOff`  
- ⚠️ 缺少事件列表，无法确认是否由探针失败或 BackOff 机制触发

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 修正容器启动命令**
```bash
kubectl edit deployment rc-crashloop-command-not-found -n aiops-e2e
```
*操作*：修改 `command` 或 `args` 字段，确保引用的命令在容器镜像中存在。  
*依据*：日志显示 `definitely-missing-command-for-rootcause: not found`。

**2. [可选] 查看崩溃前日志**
```bash
kubectl logs rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e --previous | tail -100
```
*目的*：确认容器启动失败的上下文。

### 后续优化
1. **验证命令存在性**：确保容器镜像中包含 `definitely-missing-command-for-rootcause`。
2. **配置健康检查**：添加 `livenessProbe` 和 `readinessProbe`，避免无限重启。
3. **日志监控**：配置日志告警，监控 `command not found` 等关键错误。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |
| 3. 查看日志 | `kubectl logs rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e` | 无 `command not found` 错误 |

---

## ⚠️ 注意事项
- 如果修改命令后问题仍未解决，需检查容器镜像是否包含所需命令。
- 避免使用不存在的命令或脚本作为容器入口点。
- 考虑在部署前进行镜像测试，确保命令存在并可执行。

---

## 📊 性能统计

├─ 总耗时: 4.1m
├─ 问题定位: 46.9s (19%) ✅
├─ 证据链采集: 106.6s (44%) ✅
├─ 根因分析: 18.1s (7%) ✅
├─ 汇总总结: 72.9s (30%) ✅
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
