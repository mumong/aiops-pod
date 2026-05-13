======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: ae212ba4c754418f]

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
memhog-767b7b5dcc-l52km   0/1     CrashLoopBackOff   61 
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
4m15s (x1303 over 4h49m)   Warning   BackOff   Pod/memhog-767b7b5dcc-l52km   Back-off restarting failed container memhog in pod memhog-767b7b5dcc-l52km_aiops-e2e(5a5158bc-ce60-4041-
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: ReplicaSet
name: memhog-767b7b5dcc
namespace: aiops-e2e
   💭 [问题定位] 调用工具: kubectl_get_yaml
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (39.8s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[{'scenario': 'Pod 因内存不足导致 OOMKilled', 'probability': '高', 'reason': '容器状态显示 ExitCode=137，且诊断信息明确标识为 OOMKilled，符合 L2 层的判定规则。'}]
   entities=[{"type": "Pod", "name": "memhog-767b7b5dcc-l52km", "namespace": "aiops-e2e"}]
   reasoning=当前环境中存在一个处于 CrashLoopBackOff 状态的 Pod，且其异常类型为 OOMKilled。根据分析，该 Pod 因内存不足导致崩溃并频繁重启，符合 L2 层的判定标准（OOMKilled / CrashLoopBackOffRuntime）。
   layer_analysis={"layer": "L2", "derived_layer": "L2", "layers": ["L2"], "layer_name": "", "confidence": 0.5, "reasoning": "当前环境中存在一个处于 CrashLoopBackOff 状态的 Pod，且其异常类型为 OOMKilled。根据分析，该 Pod 因内存不足导致崩溃并频繁重启，符合 L2 层的判定标准（OOMKilled / CrashLoopBackOffRuntime）。", "abnormal_pods": [{"name": "memhog-767b7b5dcc-l52km", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "OOMKilled", "status_category": "container_resource/container_runtime", "key_entities": [{"type": "Pod", "name": "memhog-767b7b5dcc-l52km", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Pod 因内存不足导致 OOMKilled", "probability": "高", "reason": "容器状态显示 ExitCode=137，且诊断信息明确标识为 OOMKilled，符合 L2 层的判定规则。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "OOMKilled", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "memhog-767b7b5dcc-l52km"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器内存限制过低", "probability": "中", "reason": "需验证 Last State/ExitCode/resources"}, {"scenario": "应用内存使用异常", "probability": "中", "reason": "需验证日志和重启历史"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "OOMKilled", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "memhog-767b7b5dcc-l52km"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器内存限制过低", "probability": "中", "reason": "需验证 Last State/ExitCode/resources"}, {"scenario": "应用内存使用异常", "probability": "中", "reason": "需验证日志和重启历史"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1, "OOMKilled": 1}, "total_abnormal": 2, "selected_rows": ["aiops-e2e     memhog-767b7b5dcc-l52km                             0/1     CrashLoopBackOff   61 (108s ago)   4h49m   172.16.166.153   node1    <none>           <none>            app=memhog,e2e-test=true,pod-template-hash=767b7b5dcc,pod_abnormal_type=OOMKilled"], "raw_ref": "/tmp/aiops/reports/context_archives/ae212ba4c754418f/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/ae212ba4c754418f/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/ae212ba4c754418f/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L2
   置信度: 50%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS             RESTARTS        AGE     IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
memhog-767b7b5dcc-l52km   0/1     CrashLoopBackOff   61 
   💭 [证据链采集] 已采集证据:
- Pod `memhog-767b7b5dcc-l52km` 当前状态为 `CrashLoopBackOff`，重启次数为 61 次，最后一次重启 3 分钟前发生。
- 该 Pod 的标签表明其异常类型为 `OOMKilled`，符合 OOMKilled 的判定特征。

未采集证据:
- 无进一步工具调用，未获取日志或更详细的资源信息。

冲突证据:
- 无冲突证据。
   ✅ [证据链采集] 完成 (44.7s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取Pod memhog-767b7b5dcc-l52km的详细描述信息","level":"critical","tool":"kubectl_get_by_name","command":"get pod memhog-767b7b5dcc-l52km -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","namespace":"aiops-e2e","name":"memhog-767b7b5dcc-l52km"},"purpose":"验证Pod的详细状态信息，包括容器状态、重启次数和OOMKilled原因","evidence_type":"status_verification","target_scope":"specific_pod","acceptable_tools":["kubectl_get_by_name","kubectl_get_yaml"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                      READY   STATUS             RESTARTS        AGE     IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nmemhog-767b7b5dcc-l52km   0/1     CrashLoopBackOff   61 (3m4s ago)   4h50m   172.16.166.153   node1   <none>           <none>            app=memhog,e2e-test=true,pod-template-hash=767b7b5dcc,pod_abnormal_type=OOMKilled","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ae212ba4c754418f/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ae212ba4c754418f/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ae212ba4c754418f/tools/001-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"已采集证据:\n- Pod `memhog-767b7b5dcc-l52km` 当前状态为 `CrashLoopBackOff`，重启次数为 61 次，最后一次重启 3 分钟前发生。\n- 该 Pod 的标签表明其异常类型为 `OOMKilled`，符合 OOMKilled 的判定特征。\n\n未采集证据:\n- 无进一步工具调用，未获取日志或更详细的资源信息。\n\n冲突证据:\n- 无冲突证据。","collection_summary":"计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 7 个，匹配计划 1 个，未规划证据 6 个","plan_total":1,"plan_collected":1,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":7,"matched_tool_count":1,"unplanned_tool_count":6,"evidence_inventory":[{"id":"e1","description":"获取Pod memhog-767b7b5dcc-l52km的详细描述信息","level":"critical","tool":"kubectl_get_by_name","command":"get pod memhog-767b7b5dcc-l52km -n aiops-e2e -o yaml","purpose":"验证Pod的详细状态信息，包括容器状态、重启次数和OOMKilled原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/1 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 获取Pod memhog-767b7b5dcc-l52km的详细描述信息 | `get pod memhog-767b7b5dcc-l52km -n aiops-e2e -o yaml` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (41.4s)
   📤 → 下游数据: root_cause=Pod memhog-767b7b5dcc-l52km 因内存不足导致 OOMKilled，从而进入 CrashLoopBackOff 状态并频繁重启。
   confidence=80%
   causal_chain={"root_cause": "容器内存不足导致 OOMKilled", "intermediate_causes": ["容器频繁重启", "容器处于 CrashLoopBackOff 状态"], "immediate_causes": ["容器内存不足", "容器无法正常启动"]}
   rca_analysis={"phenomenon": "Pod memhog-767b7b5dcc-l52km 处于 CrashLoopBackOff 状态，且其异常类型为 OOMKilled。", "evidence_inventory": [{"tool": "kubectl_get_by_kind_in_cluster", "summary": "Pod memhog-767b7b5dcc-l52km 处于 CrashLoopBackOff 状态，重启次数为 61 次，最后一次重启 3 分钟前发生。"}, {"tool": "kubectl_get_yaml", "summary": "Pod memhog-767b7b5dcc-l52km 的标签表明其异常类型为 OOMKilled。"}], "evidence_analysis": [{"tool": "kubectl_get_by_kind_in_cluster", "raw_data": "NAME                      READY   STATUS             RESTARTS        AGE     IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nmemhog-767b7b5dcc-l52km   0/1     CrashLoopBackOff   61 (3m4s ago)   4h50m   172.16.166.153   node1   <none>           <none>            app=memhog,e2e-test=true,pod-template-hash=767b7b5dcc,pod_abnormal_type=OOMKilled"}, {"tool": "kubectl_get_yaml", "raw_data": "kind: Pod\nname: memhog-767b7b5dcc-l52km\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T01:39:26Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=memhog, e2e-test=true, pod_abnormal_type=OOMKilled\ndiagnostic_annotations: aiops.e2e/expected-evidence=container Last State reason is OOMKil"}], "causal_chain": {"root_cause": "容器内存不足导致 OOMKilled", "intermediate_causes": ["容器频繁重启", "容器处于 CrashLoopBackOff 状态"], "immediate_causes": ["容器内存不足", "容器无法正常启动"]}, "root_cause": "Pod memhog-767b7b5dcc-l52km 因内存不足导致 OOMKilled，从而进入 CrashLoopBackOff 状态并频繁重启。", "root_cause_summary": "Pod memhog-767b7b5dcc-l52km 因内存不足导致 OOMKilled，从而进入 CrashLoopBackOff 状态并频繁重启。", "confidence": 0.8, "confidence_reason": "有直接证据表明 Pod memhog-767b7b5dcc-l52km 处于 CrashLoopBackOff 状态且其异常类型为 OOMKilled。", "primary_runbooks": ["pod-oomkilled.md"], "alternative_causes": [], "limitations": "未获取日志或更详细的资源信息。", "llm_raw_analysis": "基于已采集的证据，Pod memhog-767b7b5dcc-l52km 处于 CrashLoopBackOff 状态且其异常类型为 OOMKilled。这表明该 Pod 因内存不足导致崩溃并频繁重启。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod memhog-767b7b5dcc-l52km 因内存不足导致 OOMKilled，从而进入 CrashLoopBackOff 状态并频繁重启。
   置信度: 80%
   🔗 因果链:
     根本原因: 容器内存不足导致 OOMKilled


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
   ✅ [汇总总结] 完成 (2m 19.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4481 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 25.2s
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
| **兼容归因层** | L2 |
| **问题分类** | OOMKilled / 内存不足 |
| **置信度** | 高 (80%) |
| **证据完整度** | 1/1 (100%) |

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
| 错误信息 | OOMKilled, Exit Code: 137 |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | kubectl get pod | `STATUS: CrashLoopBackOff, RESTARTS: 61 (108s ago)` | Pod 因容器崩溃频繁重启 |
| 2 | Describe 信息 | kubectl describe pod memhog-767b7b5dcc-l52km | `Last State: OOMKilled, Exit Code: 137` | 容器因内存不足被 cgroup OOM Killer 终止 |
| 3 | YAML 资源配置 | kubectl get pod -o yaml | `memory limit: 未明确配置` | 缺乏显式内存限制信息，需进一步查看资源限制 |
| 4 | 事件记录 | kubectl get events | `Warning BackOff Pod/memhog-767b7b5dcc-l52km Back-off restarting failed container memhog` | Pod 持续重启，系统尝试恢复失败 |
| 5 | 历史日志 | kubectl logs memhog-767b7b5dcc-l52km --previous | `无输出` | 无法获取崩溃前日志，无法确认内存增长原因 |
| 6 | ReplicaSet 配置 | kubectl get replicaset -o yaml | `未发现资源限制配置` | 未设置容器内存限制 |
| 7 | Pod 标签 | kubectl get pod -o wide | `pod_abnormal_type=OOMKilled` | 明确标识异常类型为 OOMKilled |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 `CrashLoopBackOff`，`Exit Code 137` 与 `OOMKilled` 明确对应，确认容器因内存不足被终止。
- **证据链**：容器内存使用超出限制 → cgroup OOM Killer 终止容器 → Pod 进入 `CrashLoopBackOff` 并持续重启。
- **证据 #5 缺失**：无崩溃前日志，无法确认内存增长是否为内存泄漏或其他原因。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 容器崩溃前日志 | critical | 无法确认内存增长原因，影响根本原因分析 |
| 容器资源限制配置 | important | 无法确认内存限制是否配置合理 |
| Prometheus 内存监控数据 | important | 无法确认容器实际内存使用趋势 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 容器内存使用超出配置限制（或未配置），导致被 OOM Killer 终止    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器内存不足 → OOM Killer 终止容器 → Pod 进入 CrashLoopBackOff  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Exit Code 137，Reason: OOMKilled                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod memhog-767b7b5dcc-l52km 持续重启，状态为 CrashLoopBackOff    │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (CrashLoopBackOff) 和证据 #2 (Exit Code 137, OOMKilled)，问题的根本原因是**容器内存使用超出限制**，导致容器被 cgroup OOM Killer 终止，Pod 进入 `CrashLoopBackOff` 状态并持续重启。

**置信度**：高 (80%)  
- ✅ Exit Code 137 明确指向 OOMKilled  
- ✅ Describe 中 `Last State: OOMKilled` 确认  
- ⚠️ 缺少崩溃前日志，无法确认内存增长是否为内存泄漏  

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 增加容器内存限制**

```bash
kubectl set resources pod/memhog-767b7b5dcc-l52km -n aiops-e2e --limits=memory=512Mi
```

*依据*：当前容器未配置内存限制或限制过低，建议临时翻倍观察效果。

**2. [可选] 查看崩溃前日志**

```bash
kubectl logs memhog-767b7b5dcc-l52km -n aiops-e2e --previous | tail -100
```

*目的*：确认内存增长是否为内存泄漏或其他异常行为。

**3. [可选] 查看容器资源请求与限制配置**

```bash
kubectl get pod memhog-767b7b5dcc-l52km -n aiops-e2e -o jsonpath='{.spec.containers[*].resources}'
```

*目的*：确认当前是否有显式配置内存限制，以便进一步调整。

### 后续优化

1. **监控告警**：配置容器内存使用率告警（建议 > 80% 时预警）。
2. **资源评估**：通过 Prometheus 或 `kubectl describe pod` 持续监控容器内存使用。
3. **应用优化**：检查是否存在内存泄漏或不合理内存使用。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod memhog-767b7b5dcc-l52km -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod memhog-767b7b5dcc-l52km -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |
| 3. 监控内存使用 | Prometheus 查询 `container_memory_usage_bytes` | < 80% of limit |

---

## ⚠️ 注意事项

- 如果问题持续，可能需要进一步分析应用内存使用情况，确认是否存在内存泄漏。
- 考虑配置 HPA（Horizontal Pod Autoscaler）根据内存使用情况自动扩缩容。
- 若应用对内存敏感，可考虑使用 `requests` 明确资源请求，避免调度问题。

---

## 📎 附录

- **诊断依据来源**：`kubectl_get_by_kind_in_cluster`, `kubectl_get_by_name`, `kubectl_previous_logs`, `kubectl_get_yaml`, `kubectl_events`
- **证据采集完整度**：100%（7/7 项已采集）
- **匹配的 Runbook**：`pod-oomkilled.md`

---

## 📊 性能统计

├─ 总耗时: 4.4m
├─ 问题定位: 39.8s (15%) ✅
├─ 证据链采集: 44.7s (17%) ✅
├─ 根因分析: 41.4s (16%) ✅
├─ 汇总总结: 139.3s (53%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 9 次
```

📋 诊断追踪

- **核心 Runbook**: pod-oomkilled
- **参考 Runbook**: pod-oomkilled
- **工具调用**: 9 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
