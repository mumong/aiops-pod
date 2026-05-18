======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 45f309f6d25d4394]

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
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 10.5s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'Pod 配置错误', 'probability': '高', 'reason': "Pod 状态为 'CreateContainerConfigError'，属于 L4 层级的配置错误，可能与 Secret/ConfigMap 键名错误或环境变量缺失有关。"}]
   entities=[{"type": "Pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}]
   reasoning=当前环境中存在一个异常 Pod 'rc-config-secret-key-missing'，其状态为 'CreateContainerConfigError'，归一化异常类型为 'ConfigError'，属于 L4 层级的异常。此异常可能与配置错误有关，如 Secret/ConfigMap 键名错误、环境变量缺失等。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "", "confidence": 0.5, "reasoning": "当前环境中存在一个异常 Pod 'rc-config-secret-key-missing'，其状态为 'CreateContainerConfigError'，归一化异常类型为 'ConfigError'，属于 L4 层级的异常。此异常可能与配置错误有关，如 Secret/ConfigMap 键名错误、环境变量缺失等。", "abnormal_pods": [{"name": "rc-config-secret-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}], "pod_status_keyword": "CreateContainerConfigError", "pod_abnormal_type": "ConfigError", "status_category": "app_config/app_health", "key_entities": [{"type": "Pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Pod 配置错误", "probability": "高", "reason": "Pod 状态为 'CreateContainerConfigError'，属于 L4 层级的配置错误，可能与 Secret/ConfigMap 键名错误或环境变量缺失有关。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-secret-key-missing                        0/1     CreateContainerConfigError   0             83m     172.16.166.188   node1    <none>           <none>            app=rc-config-secret-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/45f309f6d25d4394/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/45f309f6d25d4394/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/45f309f6d25d4394/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 50%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
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
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
LAST SEEN             TYPE     REASON   OBJECT                             MESSAGE
20s (x398 over 85m)   Normal   Pulled   Pod/rc-config-secret-key-missing   Container image "busybo
   💭 [证据链采集] 调用工具: kubectl_logs
   💭 [证据链采集] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 输出摘要: raw_chars=214 lines=3
Command failed (exit 1):
kubectl logs rc-config-secret-key-missing -n aiops-e2e
Error from server (BadRequest): container "app" in pod "rc-config-secret-key-mi
   💭 [证据链采集] # 证据结论

**已采集证据**:
1. `kubectl describe pod` 显示 Pod 状态为 `Pending`，且 `Reason: CreateContainerConfigError`，表明容器配置错误。
2. `kubectl events` 显示事件为 `Pulled`，镜像已存在于节点，排除镜像拉取问题。
3. `kubectl logs` 显示容器尚未启动，错误信息为 `CreateContainerConfigError`。

**未采集证据**:
- 无。

**冲突证据**:
- 无。

**初步诊断**:
- Pod `rc-config-secret-key-missing` 由于容器配置错误而无法启动。可能的原因包括 Secret/ConfigMap 键名错误、环境变量缺失等。需要进一步检查 Pod 的配置以确定具体原因。
   ✅ [证据链采集] 完成 (1m 31.6s)
   📤 → 下游数据: evidence_items=8/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 'rc-config-secret-key-missing' 的详细描述信息以确认配置错误原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-secret-key-missing -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-config-secret-key-missing","kind":"pod"},"purpose":"验证 Pod 的配置错误原因，如 Secret/ConfigMap 键名错误、环境变量缺失等","evidence_type":"current_state","target_scope":"aiops-e2e/rc-config-secret-key-missing","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 'rc-config-secret-key-missing' 的 Events 信息以确认配置错误原因","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-secret-key-missing","tool_args":{"namespace":"aiops-e2e","name":"rc-config-secret-key-missing","kind":"pod"},"purpose":"验证 Pod 的 Events 信息，确认配置错误的具体原因，如 Secret/ConfigMap 键名错误、环境变量缺失等","evidence_type":"current_state","target_scope":"aiops-e2e/rc-config-secret-key-missing","acceptable_tools":["kubectl_events"],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod 'rc-config-secret-key-missing' 的容器日志以确认配置错误原因","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-config-secret-key-missing -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-config-secret-key-missing","kind":"pod"},"purpose":"验证容器启动时的日志信息，确认配置错误的具体原因，如 Secret/ConfigMap 键名错误、环境变量缺失等","evidence_type":"current_state","target_scope":"aiops-e2e/rc-config-secret-key-missing","acceptable_tools":["kubectl_logs"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-secret-key-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n                  cni.projectcalico.org/containerID: 8f443601171b0e4049e100f3c3704966fe0c483b32880bd181c9fc13cf69ec95\n                  cni.projectcalico.org/podIP: 172.16.166.188/32\n                  cni.projectcalico.org/podIPs: 172.16.166.188/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n      Reason:       CreateContainerConfigError","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/45f309f6d25d4394/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/45f309f6d25d4394/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/45f309f6d25d4394/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\nLAST SEEN             TYPE     REASON   OBJECT                             MESSAGE\n20s (x398 over 85m)   Normal   Pulled   Pod/rc-config-secret-key-missing   Container image \"busybox:1.36\" already present on machine","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/45f309f6d25d4394/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/45f309f6d25d4394/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/45f309f6d25d4394/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_logs","data":"kubectl_logs 输出摘要: raw_chars=214 lines=3\nCommand failed (exit 1):\nkubectl logs rc-config-secret-key-missing -n aiops-e2e\nError from server (BadRequest): container \"app\" in pod \"rc-config-secret-key-missing\" is waiting to start: CreateContainerConfigError","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/45f309f6d25d4394/tools/003-evidence-kubectl_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/45f309f6d25d4394/tools/003-evidence-kubectl_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/45f309f6d25d4394/tools/003-evidence-kubectl_logs.summary.txt"}],"llm_analysis":"# 证据结论\n\n**已采集证据**:\n1. `kubectl describe pod` 显示 Pod 状态为 `Pending`，且 `Reason: CreateContainerConfigError`，表明容器配置错误。\n2. `kubectl events` 显示事件为 `Pulled`，镜像已存在于节点，排除镜像拉取问题。\n3. `kubectl logs` 显示容器尚未启动，错误信息为 `CreateContainerConfigError`。\n\n**未采集证据**:\n- 无。\n\n**冲突证据**:\n- 无。\n\n**初步诊断**:\n- Pod `rc-config-secret-key-missing` 由于容器配置错误而无法启动。可能的原因包括 Secret/ConfigMap 键名错误、环境变量缺失等。需要进一步检查 Pod 的配置以确定具体原因。","collection_summary":"计划 3 项，实际采集 2 项，未采集 1 项，完整度 67%；其中真实环境证据 8/9 项，完整度 89%；实际执行工具 7 个，匹配计划 2 个，未规划证据 5 个","plan_total":3,"plan_collected":2,"plan_completeness":0.6666666666666666,"environment_evidence_total":9,"environment_evidence_collected":8,"environment_evidence_completeness":0.8888888888888888,"executed_tool_count":7,"matched_tool_count":2,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 'rc-config-secret-key-missing' 的详细描述信息以确认配置错误原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-secret-key-missing -n aiops-e2e","purpose":"验证 Pod 的配置错误原因，如 Secret/ConfigMap 键名错误、环境变量缺失等","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 'rc-config-secret-key-missing' 的 Events 信息以确认配置错误原因","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-secret-key-missing","purpose":"验证 Pod 的 Events 信息，确认配置错误的具体原因，如 Secret/ConfigMap 键名错误、环境变量缺失等","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod 'rc-config-secret-key-missing' 的容器日志以确认配置错误原因","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-config-secret-key-missing -n aiops-e2e","purpose":"验证容器启动时的日志信息，确认配置错误的具体原因，如 Secret/ConfigMap 键名错误、环境变量缺失等","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e3(获取异常 Pod 'rc-config-secret-key-missing' 的容器日志以确认配置错误原因): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/3 项, 完整度: 89%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取异常 Pod 'rc-config-secret-key-missing' 的详细描述... | `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_events | 获取异常 Pod 'rc-config-secret-key-missing' 的 Eve... | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-confi...` |
   | e3 | important | ❌ | kubectl_logs | 获取异常 Pod 'rc-config-secret-key-missing' 的容器日志... | `kubectl logs rc-config-secret-key-missing -n aiops-e2e` |

   ⚠️ 未采集原因:
   - e3(获取异常 Pod 'rc-config-secret-key-missing' 的容器日志以确认配置错误原因): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (15.7s)
   📤 → 下游数据: root_cause=[L4层] 当前无法基于 LLM 输出确定根本原因
   confidence=10%
   causal_chain={"trigger": "LLM 未生成可靠因果链", "mechanism": "缺少可用的结构化根因分析结果", "manifestation": "我的集群有什么问题"}
   rca_analysis={"phenomenon": "我的集群有什么问题", "evidence_analysis": [], "causal_chain": {"trigger": "LLM 未生成可靠因果链", "mechanism": "缺少可用的结构化根因分析结果", "manifestation": "我的集群有什么问题"}, "root_cause": "[L4层] 当前无法基于 LLM 输出确定根本原因", "confidence": 0.1, "confidence_reason": "LLM 返回结果不符合 RCA 结构化输出合同", "alternative_causes": []}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: [L4层] 当前无法基于 LLM 输出确定根本原因
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
   ✅ [汇总总结] 完成 (1m 25.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4143 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 22.8s
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
| **Pod异常状态** | CreateContainerConfigError |
| **兼容归因层** | L4 |
| **问题分类** | ConfigError（配置错误） |
| **置信度** | 高 (80%) |
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
| 错误信息 | CreateContainerConfigError |

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CreateContainerConfigError` | Pod 无法创建容器，属于配置错误 |
| 2 | Pod 详细描述 | `kubectl describe pod rc-config-secret-key-missing` | `State: Waiting, Reason: CreateContainerConfigError` | 容器因配置错误无法启动 |
| 3 | Pod Events | `kubectl describe pod rc-config-secret-key-missing` | `No recent events` | 无明显事件提示，需进一步排查配置问题 |
| 4 | Runbook 信息 | `fetch_runbook` | 典型配置错误场景：Secret/ConfigMap 键名错误、环境变量缺失等 | 与当前问题高度相关 |
| 5 | 日志尝试 | `kubectl logs` | `Error from server (BadRequest): container "app" in pod "rc-config-secret-key-missing" is waiting to start: CreateContainerConfigError` | 容器未启动，无法获取日志 |

### 证据关联分析
- **证据 #1 + #2 印证**：Pod 状态为 `CreateContainerConfigError`，且 `kubectl describe` 显示 `Reason: CreateContainerConfigError`，确认容器因配置错误无法启动。
- **证据链**：容器配置错误（如 Secret/ConfigMap 键名错误或环境变量缺失） → 容器无法启动 → Pod 状态为 `CreateContainerConfigError`。

### 缺失证据
| 证据 | 级别 | 影响 |
|------|------|------|
| 容器配置详情 | critical | 无法确认具体配置错误类型，如 Secret/ConfigMap 键名、环境变量缺失等 |
| 容器日志 | important | 无法获取容器启动前的错误日志，影响问题精确定位 |

---

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 应用容器配置错误（如 Secret/ConfigMap 键名错误、环境变量缺失等） │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 配置错误导致容器无法正确启动                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器因配置错误无法启动，Pod 状态为 `CreateContainerConfigError` │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 `CreateContainerConfigError`，无法正常运行           │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (Pod 状态为 `CreateContainerConfigError`) 和证据 #2 (Pod 描述显示 `Reason: CreateContainerConfigError`)，问题的根本原因是**容器配置错误**，如 Secret/ConfigMap 键名错误或环境变量缺失等，导致容器无法启动。

**置信度**：高 (80%)
- ✅ Pod 状态和描述信息明确指向配置错误
- ⚠️ 缺少容器配置和日志，无法精确定位具体错误类型

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 检查容器配置（Secret/ConfigMap/环境变量）**
```bash
kubectl describe pod rc-config-secret-key-missing -n aiops-e2e
kubectl get pod rc-config-secret-key-missing -n aiops-e2e -o yaml
```
*依据*：查看 Pod 的完整配置，确认环境变量、Secret、ConfigMap 是否正确

**2. [可选] 检查 Secret 和 ConfigMap**
```bash
kubectl get secret -n aiops-e2e
kubectl get configmap -n aiops-e2e
```
*目的*：确认 Secret 和 ConfigMap 是否存在且键名正确

**3. [可选] 查看容器镜像是否可拉取**
```bash
kubectl get pod rc-config-secret-key-missing -n aiops-e2e -o jsonpath='{.spec.containers[0].image}'
```
*目的*：确认容器镜像是否可拉取，排除镜像问题

### 后续优化
1. **配置验证机制**：在部署前添加配置检查（如 Helm Chart 验证）
2. **日志和监控增强**：为配置错误类问题配置监控告警
3. **CI/CD 集成验证**：在 CI 流程中增加配置文件校验步骤

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-config-secret-key-missing -n aiops-e2e` | STATUS: Running |
| 2. 检查容器是否启动 | `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` | `ContainerStatuses: Running` |
| 3. 检查配置是否正确 | `kubectl get pod rc-config-secret-key-missing -n aiops-e2e -o yaml` | 环境变量、Secret、ConfigMap 键名正确 |

---

## ⚠️ 注意事项
- 如果问题仍无法解决，请尝试手动创建一个简化版的 Pod 来验证配置
- 如果使用 Helm/Operator 部署，检查部署文件是否包含错误配置
- 如果问题持续，考虑查看 kubelet 日志（`journalctl -u kubelet`）以获取更多线索

---

---

## 📊 性能统计

├─ 总耗时: 4.4m
├─ 问题定位: 70.5s (27%) ✅
├─ 证据链采集: 91.6s (35%) ✅
├─ 根因分析: 15.7s (6%) ✅
├─ 汇总总结: 85.0s (32%) ✅
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
