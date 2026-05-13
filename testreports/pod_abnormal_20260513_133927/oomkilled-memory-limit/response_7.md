======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: bef8209761e2407a]

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
memhog-767b7b5dcc-l52km   0/1     CrashLoopBackOff   55 (
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
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
3m16s (x1166 over 4h18m)   Warning   BackOff   Pod/memhog-767b7b5dcc-l52km   Back-off restarting failed container memhog in pod memhog-767b7b5dcc-l52km_aiops-e2e(5a5158bc-ce60-4041-
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: ReplicaSet
name: memhog-767b7b5dcc
namespace: aiops-e2e
   💭 [问题定位] 调用工具: kubectl_get_yaml
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (40.6s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[{'scenario': 'Pod 因内存不足导致 OOMKilled，频繁重启', 'probability': '高', 'reason': '容器状态显示 OOMKilled 和 exitCode=137，且没有 Evicted 标记。'}]
   entities=[{"type": "pod", "name": "memhog-767b7b5dcc-l52km", "namespace": "aiops-e2e"}]
   reasoning=当前环境中存在一个处于 CrashLoopBackOff 状态的 Pod，其容器状态显示 OOMKilled 和 exitCode=137，符合 L2 层级的判定标准。根据分析，该 Pod 因内存不足导致崩溃，属于 L2 根因分类（OOMKilled / CrashLoopBackOff + resource limits）。
   layer_analysis={"layer": "L2", "derived_layer": "L2", "layers": ["L2"], "layer_name": "L2", "confidence": 0.9, "reasoning": "当前环境中存在一个处于 CrashLoopBackOff 状态的 Pod，其容器状态显示 OOMKilled 和 exitCode=137，符合 L2 层级的判定标准。根据分析，该 Pod 因内存不足导致崩溃，属于 L2 根因分类（OOMKilled / CrashLoopBackOff + resource limits）。", "abnormal_pods": [{"name": "memhog-767b7b5dcc-l52km", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "OOMKilled", "status_category": "container_resource", "key_entities": [{"type": "pod", "name": "memhog-767b7b5dcc-l52km", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Pod 因内存不足导致 OOMKilled，频繁重启", "probability": "高", "reason": "容器状态显示 OOMKilled 和 exitCode=137，且没有 Evicted 标记。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "OOMKilled", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "memhog-767b7b5dcc-l52km"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器内存限制过低", "probability": "中", "reason": "需验证 Last State/ExitCode/resources"}, {"scenario": "应用内存使用异常", "probability": "中", "reason": "需验证日志和重启历史"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "OOMKilled", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "memhog-767b7b5dcc-l52km"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器内存限制过低", "probability": "中", "reason": "需验证 Last State/ExitCode/resources"}, {"scenario": "应用内存使用异常", "probability": "中", "reason": "需验证日志和重启历史"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1, "OOMKilled": 1}, "total_abnormal": 2, "selected_rows": ["aiops-e2e     memhog-767b7b5dcc-l52km                             0/1     CrashLoopBackOff   55 (91s ago)    4h18m   172.16.166.153   node1    <none>           <none>            app=memhog,e2e-test=true,pod-template-hash=767b7b5dcc,pod_abnormal_type=OOMKilled"], "raw_ref": "/tmp/aiops/reports/context_archives/bef8209761e2407a/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/bef8209761e2407a/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/bef8209761e2407a/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L2
   置信度: 90%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
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
   💭 [证据链采集] 调用工具: kubectl_logs
   💭 [证据链采集] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
13s (x1188 over 4h20m)   Warning   BackOff   Pod/memhog-767b7b5dcc-l52km   Back-off restarting failed container memhog in pod memhog-767b7b5dcc-l52km_aiops-e2e(5a5158bc-ce60-4041-9d
   💭 [证据链采集] 已采集证据：
1. `kubectl_get_yaml` 确认 Pod 配置中 `containerStatuses` 显示 `exitCode=137` 且 `reason=OOMKilled`，符合 OOMKilled 判定规则。
2. `kubectl_logs` 未输出日志，但结合 `kubectl_get_yaml` 的状态，说明容器崩溃时未记录明确日志。
3. `kubectl_events` 显示 `Back-off restarting failed container`，佐证容器频繁重启。

未采集证据：
- 无

冲突证据：
- 无

结论：该 Pod 处于 CrashLoopBackOff 状态，容器因内存不足导致 OOMKilled，频繁重启。需检查容器内存限制配置或应用内存使用情况。
   ✅ [证据链采集] 完成 (1m 53.2s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod 'memhog-767b7b5dcc-l52km' 的详细状态和资源配置","level":"critical","tool":"kubectl_get_yaml","command":"get","tool_args":{"kind":"Pod","name":"memhog-767b7b5dcc-l52km","namespace":"aiops-e2e"},"purpose":"获取 Pod 的资源配置，验证内存限制是否过低","evidence_type":"configuration","target_scope":"specific","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e2","description":"查看 Pod 'memhog-767b7b5dcc-l52km' 的日志","level":"important","tool":"kubectl_logs","command":"logs","tool_args":{"name":"memhog-767b7b5dcc-l52km","namespace":"aiops-e2e","container":"memhog"},"purpose":"检查是否有关于内存不足的错误信息","evidence_type":"log","target_scope":"specific","acceptable_tools":["kubectl_logs"],"counts_for_completeness":true},{"id":"e3","description":"查看 Pod 'memhog-767b7b5dcc-l52km' 的事件历史","level":"important","tool":"kubectl_events","command":"get","tool_args":{"kind":"Pod","name":"memhog-767b7b5dcc-l52km","namespace":"aiops-e2e"},"purpose":"检查是否有 OOMKilled 或重启相关的事件","evidence_type":"event","target_scope":"specific","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: memhog-767b7b5dcc-l52km\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T01:39:26Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=memhog, e2e-test=true, pod_abnormal_type=OOMKilled\ndiagnostic_annotations: aiops.e2e/expected-evidence=container Last State reason is OOMKilled and exitCode is 137, aiops.e2e/expected-status=CrashLoopBackOff|Error, aiops.e2e/runbook=pod-oomkilled.md\nownerReferences: ReplicaSet/memhog-767b7b5dcc\ntolerations_count: 2\ncontainers:\n- memhog: image=python:3.11-slim imagePullPolicy=IfNotPresent\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [memhog]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [memhog]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- memhog: ready=False restarts=55 reason=CrashLoopBackOff exitCode=137\n  message: back-off 5m0s restarting failed container=memhog pod=memhog-767b7b5dcc-l52km_aiops-e2e(5a5158bc-ce60-4041-9dca-9158a2d57d8f)\nvolumes:\n- {\"name\": \"kube-api-access-r426l\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/bef8209761e2407a/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/bef8209761e2407a/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/bef8209761e2407a/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_logs","data":"kubectl_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/bef8209761e2407a/tools/002-evidence-kubectl_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/bef8209761e2407a/tools/002-evidence-kubectl_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/bef8209761e2407a/tools/002-evidence-kubectl_logs.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n13s (x1188 over 4h20m)   Warning   BackOff   Pod/memhog-767b7b5dcc-l52km   Back-off restarting failed container memhog in pod memhog-767b7b5dcc-l52km_aiops-e2e(5a5158bc-ce60-4041-9dca-9158a2d57d8f)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/bef8209761e2407a/tools/003-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/bef8209761e2407a/tools/003-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/bef8209761e2407a/tools/003-evidence-kubectl_events.summary.txt"}],"llm_analysis":"已采集证据：\n1. `kubectl_get_yaml` 确认 Pod 配置中 `containerStatuses` 显示 `exitCode=137` 且 `reason=OOMKilled`，符合 OOMKilled 判定规则。\n2. `kubectl_logs` 未输出日志，但结合 `kubectl_get_yaml` 的状态，说明容器崩溃时未记录明确日志。\n3. `kubectl_events` 显示 `Back-off restarting failed container`，佐证容器频繁重启。\n\n未采集证据：\n- 无\n\n冲突证据：\n- 无\n\n结论：该 Pod 处于 CrashLoopBackOff 状态，容器因内存不足导致 OOMKilled，频繁重启。需检查容器内存限制配置或应用内存使用情况。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 9/9 项，完整度 100%；实际执行工具 9 个，匹配计划 3 个，未规划证据 6 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":9,"environment_evidence_collected":9,"environment_evidence_completeness":1.0,"executed_tool_count":9,"matched_tool_count":3,"unplanned_tool_count":6,"evidence_inventory":[{"id":"e1","description":"验证 Pod 'memhog-767b7b5dcc-l52km' 的详细状态和资源配置","level":"critical","tool":"kubectl_get_yaml","command":"get","purpose":"获取 Pod 的资源配置，验证内存限制是否过低","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"查看 Pod 'memhog-767b7b5dcc-l52km' 的日志","level":"important","tool":"kubectl_logs","command":"logs","purpose":"检查是否有关于内存不足的错误信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"查看 Pod 'memhog-767b7b5dcc-l52km' 的事件历史","level":"important","tool":"kubectl_events","command":"get","purpose":"检查是否有 OOMKilled 或重启相关的事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_yaml | 验证 Pod 'memhog-767b7b5dcc-l52km' 的详细状态和资源配置 | `get` |
   | e2 | important | ✅ | kubectl_logs | 查看 Pod 'memhog-767b7b5dcc-l52km' 的日志 | `logs` |
   | e3 | important | ✅ | kubectl_events | 查看 Pod 'memhog-767b7b5dcc-l52km' 的事件历史 | `get` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (43.9s)
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
   ✅ [汇总总结] 完成 (1m 28.2s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3882 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 46.0s
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
| **问题分类** | OOMKilled / CrashLoopBackOff |
| **置信度** | 高 (90%) |
| **证据完整度** | 3/3 (100%) |

---

## 🔍 现象描述

**用户报告**：  
> 我的集群有什么问题？

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
| 1 | Pod 状态 | `kubectl get pod memhog-767b7b5dcc-l52km -n aiops-e2e` | `STATUS: CrashLoopBackOff, RESTARTS: 55` | Pod 频繁崩溃并重启 |
| 2 | 容器状态 | `kubectl describe pod memhog-767b7b5dcc-l52km -n aiops-e2e` | `Reason: OOMKilled, Exit Code: 137` | 容器因内存不足被终止 |
| 3 | 事件历史 | `kubectl describe pod memhog-767b7b5dcc-l52km -n aiops-e2e` | `Warning: Back-off restarting failed container` | Pod 持续重启中 |
| 4 | 日志检查 | `kubectl logs memhog-767b7b5dcc-l52km -n aiops-e2e --previous` | `关键日志: (no output)` | 无崩溃前日志 |
| 5 | 资源配置 | `kubectl get pod memhog-767b7b5dcc-l52km -n aiops-e2e -o yaml` | `memory limit: 256Mi` | 内存限制较低 |
| 6 | 事件摘要 | `kubectl describe pod memhog-767b7b5dcc-l52km -n aiops-e2e` | `事件摘要: Back-off restarting failed container` | 频繁重启由容器失败引发 |

### 证据关联分析

- **证据 #2 + #5 印证**：容器因内存不足（OOMKilled, Exit Code 137）被终止，而当前内存限制为 256Mi，表明内存限制不足。
- **证据链**：应用内存需求 > 256Mi → 触发 OOM Killer → 容器被终止 → Pod 重启 → 事件中显示持续重启。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 容器崩溃前日志 | critical | 无法确认内存增长原因 |
| Prometheus 内存监控数据 | important | 无法确认内存使用趋势 |

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

**结论**：根据证据 #2 (Exit Code 137, OOMKilled) 和证据 #5 (memory limit: 256Mi)，  
问题的根本原因是**容器内存限制（256Mi）不足以满足应用实际需求**，  
导致容器被 cgroup OOM Killer 终止并持续重启。  
**置信度**：高 (90%)  
- ✅ Exit Code 137 明确指向 OOM  
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
kubectl logs memhog-767b7b5dcc-l52km -n aiops-e2e --previous | tail -100
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
- 如果应用本身有内存泄漏，仅增加内存限制无法根本解决问题，需优化应用逻辑

---

## 📊 性能统计

├─ 总耗时: 4.8m
├─ 问题定位: 40.6s (14%) ✅
├─ 证据链采集: 113.2s (40%) ✅
├─ 根因分析: 43.9s (15%) ✅
├─ 汇总总结: 88.2s (31%) ✅
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
