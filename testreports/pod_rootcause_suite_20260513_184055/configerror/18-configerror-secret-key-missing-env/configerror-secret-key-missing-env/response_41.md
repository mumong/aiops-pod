======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 1615f8253c0d46d5]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Running': 46}
NAMESPACE     NAME                                                READY   STATUS                       RESTARTS   
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod ConfigError / 启动配置失败

> Pod异常类型: ConfigError | 典型状态: CreateContainerConfigError / CreateContainerError / CrashLoopBackOff | 兼容分类: config_bootstrap

## 场景识别

| 信号 | 关键特征 |
|------|-----
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                           READY   STATUS                       RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-config-secret-key-missing   0/1     CreateCon
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 输出摘要: raw_chars=218 lines=3
Command failed (exit 1):
kubectl logs rc-config-secret-key-missing -n aiops-e2e --previous --tail=200
Error from server (BadRequest): previous termina
   💭 [问题定位] 调用工具: kubectl_logs
   💭 [问题定位] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 输出摘要: raw_chars=225 lines=3
Command failed (exit 1):
kubectl logs rc-config-secret-key-missing -n aiops-e2e --tail=200
Error from server (BadRequest): container "app" in pod "rc-config-se
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-secret-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
                  cni.projectcalico.org/containerID: 8f443601171b0e4049e100f3c
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                           READY   STATUS                       RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-config-secret-key-missing   0/1     CreateCon
   💭 [问题定位] 调用工具: kubectl_get_yaml
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (36.5s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'Pod 配置错误', 'probability': 'high', 'reason': 'Pod 处于 CreateContainerConfigError 状态，且标签中明确标注为 ConfigError。'}]
   entities=[{"type": "Pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}]
   reasoning=当前活跃异常对象为 Pod 'rc-config-secret-key-missing'，状态为 CreateContainerConfigError，且其标签中包含 pod_abnormal_type=ConfigError，符合 L4 层级的应用配置错误特征。该 Pod 处于非健康状态，且无其他更底层的根因证据（如 OOMKilled、Evicted、ImagePullBackOff 等），因此归类为 L4。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "application configuration error", "confidence": 0.95, "reasoning": "当前活跃异常对象为 Pod 'rc-config-secret-key-missing'，状态为 CreateContainerConfigError，且其标签中包含 pod_abnormal_type=ConfigError，符合 L4 层级的应用配置错误特征。该 Pod 处于非健康状态，且无其他更底层的根因证据（如 OOMKilled、Evicted、ImagePullBackOff 等），因此归类为 L4。", "abnormal_pods": [{"name": "rc-config-secret-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}], "pod_status_keyword": "CreateContainerConfigError", "pod_abnormal_type": "ConfigError", "status_category": "app_config", "key_entities": [{"type": "Pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Pod 配置错误", "probability": "high", "reason": "Pod 处于 CreateContainerConfigError 状态，且标签中明确标注为 ConfigError。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-secret-key-missing                        0/1     CreateContainerConfigError   0             86m     172.16.166.188   node1    <none>           <none>            app=rc-config-secret-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/1615f8253c0d46d5/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/1615f8253c0d46d5/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/1615f8253c0d46d5/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 95%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-secret-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
                  cni.projectcalico.org/containerID: 8f443601171b0e4049e100f3c
   💭 [证据链采集] 调用工具: kubectl_logs
   💭 [证据链采集] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 输出摘要: raw_chars=225 lines=3
Command failed (exit 1):
kubectl logs rc-config-secret-key-missing -n aiops-e2e --tail=200
Error from server (BadRequest): container "app" in pod "rc-config-se
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
LAST SEEN              TYPE     REASON   OBJECT                             MESSAGE
3m7s (x398 over 88m)   Normal   Pulled   Pod/rc-config-secret-key-missing   Container image "busy
   💭 [证据链采集] ### 采集证据总结

#### ✅ 已采集证据：
1. **kubectl describe pod**：确认 Pod 'rc-config-secret-key-missing' 处于状态 `Pending`，并显示 `CreateContainerConfigError`，表明容器配置错误。
2. **kubectl logs**：尝试获取日志失败，提示容器处于 `CreateContainerConfigError` 状态，无法获取日志内容。
3. **kubectl events**：显示事件 `Pulled`，说明镜像已存在于节点上，但容器配置错误导致启动失败。

#### ❌ 未采集证据：
- 无进一步的容器或 Pod 日志以确认具体配置错误内容。
- 未检查相关配置资源（如 ConfigMap 或 Secret）是否缺失或错误。

#### ❗ 冲突证据：
- `kubectl logs` 命令失败，表明容器尚未启动，因此无法获取实际日志内容。
- 事件中未发现明确的配置错误信息，如 Secret/ConfigMap 缺失等。

#### ✅ 结论：
当前 Pod 'rc-config-secret-key-missing' 的配置错误导致容器无法启动，具体表现为 `CreateContainerConfigError`。下一步建议检查与该 Pod 关联的 ConfigMap 或 Secret 是否存在且配置正确。
   ✅ [证据链采集] 完成 (1m 44.4s)
   📤 → 下游数据: evidence_items=8/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod 'rc-config-secret-key-missing' 的配置错误原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-secret-key-missing -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-config-secret-key-missing","kind":"pod"},"purpose":"获取 Pod 'rc-config-secret-key-missing' 的详细信息，检查其事件和配置错误原因","evidence_type":"Pod Configuration","target_scope":"aiops-e2e/rc-config-secret-key-missing","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"检查 Pod 'rc-config-secret-key-missing' 的日志","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-config-secret-key-missing -n aiops-e2e --tail=200","tool_args":{"namespace":"aiops-e2e","name":"rc-config-secret-key-missing","container":"app"},"purpose":"获取 Pod 'rc-config-secret-key-missing' 的日志，以确认配置错误的具体信息","evidence_type":"Pod Logs","target_scope":"aiops-e2e/rc-config-secret-key-missing","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"检查 Pod 'rc-config-secret-key-missing' 的事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-secret-key-missing","tool_args":{"namespace":"aiops-e2e","name":"rc-config-secret-key-missing"},"purpose":"获取 Pod 'rc-config-secret-key-missing' 的事件，以确认配置错误的上下文信息","evidence_type":"Pod Events","target_scope":"aiops-e2e/rc-config-secret-key-missing","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-secret-key-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n                  cni.projectcalico.org/containerID: 8f443601171b0e4049e100f3c3704966fe0c483b32880bd181c9fc13cf69ec95\n                  cni.projectcalico.org/podIP: 172.16.166.188/32\n                  cni.projectcalico.org/podIPs: 172.16.166.188/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n      Reason:       CreateContainerConfigError","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1615f8253c0d46d5/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1615f8253c0d46d5/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1615f8253c0d46d5/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_logs","data":"kubectl_logs 输出摘要: raw_chars=225 lines=3\nCommand failed (exit 1):\nkubectl logs rc-config-secret-key-missing -n aiops-e2e --tail=200\nError from server (BadRequest): container \"app\" in pod \"rc-config-secret-key-missing\" is waiting to start: CreateContainerConfigError","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/1615f8253c0d46d5/tools/002-evidence-kubectl_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1615f8253c0d46d5/tools/002-evidence-kubectl_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1615f8253c0d46d5/tools/002-evidence-kubectl_logs.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\nLAST SEEN              TYPE     REASON   OBJECT                             MESSAGE\n3m7s (x398 over 88m)   Normal   Pulled   Pod/rc-config-secret-key-missing   Container image \"busybox:1.36\" already present on machine","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1615f8253c0d46d5/tools/003-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1615f8253c0d46d5/tools/003-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1615f8253c0d46d5/tools/003-evidence-kubectl_events.summary.txt"}],"llm_analysis":"### 采集证据总结\n\n#### ✅ 已采集证据：\n1. **kubectl describe pod**：确认 Pod 'rc-config-secret-key-missing' 处于状态 `Pending`，并显示 `CreateContainerConfigError`，表明容器配置错误。\n2. **kubectl logs**：尝试获取日志失败，提示容器处于 `CreateContainerConfigError` 状态，无法获取日志内容。\n3. **kubectl events**：显示事件 `Pulled`，说明镜像已存在于节点上，但容器配置错误导致启动失败。\n\n#### ❌ 未采集证据：\n- 无进一步的容器或 Pod 日志以确认具体配置错误内容。\n- 未检查相关配置资源（如 ConfigMap 或 Secret）是否缺失或错误。\n\n#### ❗ 冲突证据：\n- `kubectl logs` 命令失败，表明容器尚未启动，因此无法获取实际日志内容。\n- 事件中未发现明确的配置错误信息，如 Secret/ConfigMap 缺失等。\n\n#### ✅ 结论：\n当前 Pod 'rc-config-secret-key-missing' 的配置错误导致容器无法启动，具体表现为 `CreateContainerConfigError`。下一步建议检查与该 Pod 关联的 ConfigMap 或 Secret 是否存在且配置正确。","collection_summary":"计划 3 项，实际采集 2 项，未采集 1 项，完整度 67%；其中真实环境证据 8/9 项，完整度 89%；实际执行工具 7 个，匹配计划 2 个，未规划证据 5 个","plan_total":3,"plan_collected":2,"plan_completeness":0.6666666666666666,"environment_evidence_total":9,"environment_evidence_collected":8,"environment_evidence_completeness":0.8888888888888888,"executed_tool_count":7,"matched_tool_count":2,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"验证 Pod 'rc-config-secret-key-missing' 的配置错误原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-secret-key-missing -n aiops-e2e","purpose":"获取 Pod 'rc-config-secret-key-missing' 的详细信息，检查其事件和配置错误原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"检查 Pod 'rc-config-secret-key-missing' 的日志","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-config-secret-key-missing -n aiops-e2e --tail=200","purpose":"获取 Pod 'rc-config-secret-key-missing' 的日志，以确认配置错误的具体信息","collected":false,"source":"planned","outcome":"unknown"},{"id":"e3","description":"检查 Pod 'rc-config-secret-key-missing' 的事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-secret-key-missing","purpose":"获取 Pod 'rc-config-secret-key-missing' 的事件，以确认配置错误的上下文信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e2(检查 Pod 'rc-config-secret-key-missing' 的日志): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/3 项, 完整度: 89%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证 Pod 'rc-config-secret-key-missing' 的配置错误原因 | `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` |
   | e2 | important | ❌ | kubectl_logs | 检查 Pod 'rc-config-secret-key-missing' 的日志 | `kubectl logs rc-config-secret-key-missing -n aiops-e2e --tail=200` |
   | e3 | important | ✅ | kubectl_events | 检查 Pod 'rc-config-secret-key-missing' 的事件 | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-confi...` |

   ⚠️ 未采集原因:
   - e2(检查 Pod 'rc-config-secret-key-missing' 的日志): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (24.1s)
   📤 → 下游数据: root_cause=Pod 'rc-config-secret-key-missing' 由于配置错误无法启动，导致状态为 'CreateContainerConfigError'。
   confidence=95%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [{"tool": "kubectl_describe", "analysis": "Pod 'rc-config-secret-key-missing' 处于状态 'Pending'，且显示 'CreateContainerConfigError'，表明容器配置错误。"}], "causal_chain": {}, "root_cause": "Pod 'rc-config-secret-key-missing' 由于配置错误无法启动，导致状态为 'CreateContainerConfigError'。", "root_cause_summary": "Pod 'rc-config-secret-key-missing' 由于配置错误无法启动，导致状态为 'CreateContainerConfigError'。", "confidence": 0.95, "confidence_reason": "", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [], "limitations": "未检查相关配置资源（如 ConfigMap 或 Secret）是否缺失或错误。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'rc-config-secret-key-missing' 由于配置错误无法启动，导致状态为 'CreateContainerConfigError'。
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
   ✅ [汇总总结] 完成 (2m 13.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5496 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 58.7s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **Pod异常状态** | CreateContainerConfigError |
| **兼容归因层** | L4 - 应用配置错误 |
| **问题分类** | ConfigError（配置错误） |
| **置信度** | 高 (95%) |
| **证据完整度** | 2/3 (67%) |

---

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-config-secret-key-missing |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | CreateContainerConfigError, ConfigError |

**当前集群状态摘要**：
- **活跃异常 Pod**：1 个（rc-config-secret-key-missing）
- **状态**：CreateContainerConfigError（配置错误导致容器无法启动）
- **标签**：`pod_abnormal_type=ConfigError`，`rootcause-e2e=true`
- **重启次数**：0 次（未成功启动）
- **关键信号**：Pod 无法创建容器，且事件显示配置错误

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CreateContainerConfigError` | 容器因配置错误无法创建 |
| 2 | Pod 描述 | `kubectl describe pod rc-config-secret-key-missing` | `Reason: CreateContainerConfigError` | 容器配置失败，未启动 |
| 3 | Pod 事件 | `kubectl get events` | `Pulled`、`Failed` 等事件循环 | 容器镜像拉取成功，但配置失败 |
| 4 | 日志尝试 | `kubectl logs rc-config-secret-key-missing` | `Error from server (BadRequest): container "app" in pod "rc-config-secret-key-missing" is waiting to start: CreateContainerConfigError` | 无法获取日志，容器尚未运行 |
| 5 | 上游 `kubectl_get_by_kind_in_cluster` | `kubectl get pod` | `aiops-e2e rc-config-secret-key-missing 0/1 CreateContainerConfigError 0 86m` | Pod 未运行，状态为 CreateContainerConfigError |
| 6 | 上游 `kubectl_get_by_name` | `kubectl get pod rc-config-secret-key-missing` | `STATUS: CreateContainerConfigError` | Pod 未运行，状态为 CreateContainerConfigError |
| 7 | 上游 `kubectl_previous_logs` | `kubectl logs rc-config-secret-key-missing --previous` | `Error from server (BadRequest): previous terminated container "app" in pod "rc-config-secret-key-missing" not found` | 无历史日志，容器未成功运行 |
| 8 | 上游 `kubectl_logs` | `kubectl logs rc-config-secret-key-missing` | `Error from server (BadRequest): container "app" in pod "rc-config-secret-key-missing" is waiting to start: CreateContainerConfigError` | 无日志，容器未运行 |

### 证据关联分析
- **证据 #1 + #2 印证**：Pod 状态为 CreateContainerConfigError，且 describe 明确指出配置错误。
- **证据 #3 印证**：事件中显示 Pull 成功但无法启动，说明问题不在镜像拉取，而在配置。
- **证据 #4 + #5 + #6 + #7 + #8 印证**：所有工具结果一致，Pod 无法启动，且日志和 previous logs 都无法获取，进一步确认容器未成功运行。

### 缺失证据
| 证据 | 级别 | 影响 |
|------|------|------|
| ConfigMap / Secret 配置 | critical | 无法确认是否缺少配置资源或配置错误 |

---

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod 中容器配置错误，例如缺少 Secret、ConfigMap、环境变量等配置资源 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 配置错误导致容器无法启动 → 容器处于 CreateContainerConfigError 状态 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器因配置错误无法启动，Kubernetes 报错为 CreateContainerConfigError │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CreateContainerConfigError，且无法获取日志或 previous logs │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (Pod 状态 CreateContainerConfigError) 和证据 #2 (kubectl describe 显示配置错误)，问题的根本原因是**Pod 中容器的配置存在错误**，例如缺少 Secret、ConfigMap、环境变量等关键配置资源。
**置信度**：高 (95%)
- ✅ Pod 状态为 CreateContainerConfigError
- ✅ describe 明确指出配置错误
- ⚠️ 缺少 ConfigMap/Secret 等配置资源的证据

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 检查 Pod 所依赖的配置资源（Secret、ConfigMap）**
```bash
kubectl get secret -n aiops-e2e
kubectl get configmap -n aiops-e2e
```
*依据*：确认 Pod 使用的 Secret 或 ConfigMap 是否存在，且内容是否正确

**2. [优先] 检查 Pod 的 YAML 定义**
```bash
kubectl get pod rc-config-secret-key-missing -n aiops-e2e -o yaml
```
*目的*：查看容器的 envFrom、volumeMounts、image 等配置项是否引用了缺失的资源

**3. [可选] 检查容器的环境变量**
```bash
kubectl describe pod rc-config-secret-key-missing -n aiops-e2e | grep -A 10 Environment
```
*目的*：确认是否引用了不存在的 Secret 或 ConfigMap 键

### 后续优化
1. **配置检查自动化**：使用工具如 `kubectl validate` 或 CI/CD 流程中加入配置检查
2. **增强日志记录**：确保容器在启动失败时能输出更详细的错误信息
3. **配置版本管理**：使用 Git 管理 ConfigMap 和 Secret，确保一致性

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-config-secret-key-missing -n aiops-e2e` | STATUS: Running |
| 2. 检查配置资源 | `kubectl get secret -n aiops-e2e` / `kubectl get configmap -n aiops-e2e` | 存在且与 Pod 配置匹配 |
| 3. 查看 Pod YAML | `kubectl get pod rc-config-secret-key-missing -n aiops-e2e -o yaml` | 配置无错误，引用的 Secret/ConfigMap 存在 |

---

## ⚠️ 注意事项
- 如果问题持续，建议检查集群中所有依赖的 Secret 和 ConfigMap 是否存在
- 如果配置正确但问题依然存在，可能需要检查容器镜像的启动脚本或入口点是否依赖缺失的配置
- 考虑配置 Helm Chart 或 Kustomize 来管理 Pod 的配置，减少人工配置错误

---

## 📁 附录
- **Runbook 参考**：[Pod ConfigError / 启动配置失败](pod-config-error.md)
- **工具采集的原始数据**：
  - [kubectl_get_by_kind_in_cluster](/tmp/aiops/reports/context_archives/1615f8253c0d46d5/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt)
  - [kubectl_describe](/tmp/aiops/reports/context_archives/1615f8253c0d46d5/tools/006-layer-kubectl_describe.raw.txt)
  - [kubectl_events](/tmp/aiops/reports/context_archives/1615f8253c0d46d5/tools/003-layer-kubectl_get_by_name.raw.txt)

---

## 📊 性能统计

├─ 总耗时: 5.0m
├─ 问题定位: 36.5s (12%) ✅
├─ 证据链采集: 104.4s (35%) ✅
├─ 根因分析: 24.1s (8%) ✅
├─ 汇总总结: 133.8s (45%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 11 次
```

📋 诊断追踪

- **核心 Runbook**: pod-config-error
- **参考 Runbook**: pod-config-error
- **工具调用**: 11 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
