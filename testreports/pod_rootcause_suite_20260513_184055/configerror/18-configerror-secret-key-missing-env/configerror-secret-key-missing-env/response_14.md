======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 970de2f3c1e64123]

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
  Warning  Failed          24m (x12 over 25m)   kubelet            Error: coul
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME            TYPE     DATA   AGE   LABELS
rc-app-secret   Opaque   1      26m   rootcause-e2e=true
   💭 [问题定位] 调用工具: kubectl_get_by_name
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 13.6s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'Pod 配置错误', 'probability': '高', 'reason': "describe 日志显示 Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret，表明这是一个 ConfigError 类型的异常，属于 L4 层级（应用配置错误）"}]
   entities=[{"type": "Pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "rc-app-secret", "namespace": "aiops-e2e"}]
   reasoning=当前环境中存在一个处于 CreateContainerConfigError 状态的 Pod rc-config-secret-key-missing。describe 日志显示 Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret，表明这是一个 ConfigError 类型的异常，属于 L4 层级（应用配置错误）。没有其他当前仍异常的 Pod，也没有更深层的根因证据，因此归一化到 L4。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "", "confidence": 0.5, "reasoning": "当前环境中存在一个处于 CreateContainerConfigError 状态的 Pod rc-config-secret-key-missing。describe 日志显示 Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret，表明这是一个 ConfigError 类型的异常，属于 L4 层级（应用配置错误）。没有其他当前仍异常的 Pod，也没有更深层的根因证据，因此归一化到 L4。", "abnormal_pods": [{"name": "rc-config-secret-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}], "pod_status_keyword": "CreateContainerConfigError", "pod_abnormal_type": "ConfigError", "status_category": "app_config", "key_entities": [{"type": "Pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "rc-app-secret", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Pod 配置错误", "probability": "高", "reason": "describe 日志显示 Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret，表明这是一个 ConfigError 类型的异常，属于 L4 层级（应用配置错误）"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-secret-key-missing                        0/1     CreateContainerConfigError   0             25m     172.16.166.188   node1    <none>           <none>            app=rc-config-secret-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/970de2f3c1e64123/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/970de2f3c1e64123/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/970de2f3c1e64123/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-secret-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          26m (x12 over 28m)     kubelet            Error: co
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME            TYPE     DATA   AGE   LABELS
rc-app-secret   Opaque   1      28m   rootcause-e2e=true
   💭 [证据链采集] 调用工具: kubectl_logs
   💭 [证据链采集] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 输出摘要: raw_chars=225 lines=3
Command failed (exit 1):
kubectl logs rc-config-secret-key-missing -n aiops-e2e --tail=200
Error from server (BadRequest): container "app" in pod "rc-config-se
   💭 [证据链采集] # 证据结论

## 已采集证据
1. **Pod 详细信息**：`rc-config-secret-key-missing` 处于 `Pending` 状态，且事件中显示 `Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret`，这表明 Pod 无法启动是因为缺少配置中的关键 Secret。
2. **Secret 验证**：`rc-app-secret` 存在且类型为 `Opaque`，但数据字段为 1，意味着可能缺少 `APP_SECRET_TOKEN` 这个键。
3. **容器日志**：尝试获取容器日志失败，错误信息指出容器尚未启动，因为存在 `CreateContainerConfigError`。

## 未采集证据
- 无。

## 冲突证据
- 无。
   ✅ [证据链采集] 完成 (1m 20.6s)
   📤 → 下游数据: evidence_items=8/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod rc-config-secret-key-missing 的详细状态和关键事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-secret-key-missing -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-config-secret-key-missing","kind":"Pod"},"purpose":"获取 Pod 的详细状态、事件和诊断信息，验证其 CreateContainerConfigError 的根本原因","evidence_type":"status_events","target_scope":"aiops-e2e/rc-config-secret-key-missing","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"验证 Secret rc-app-secret 是否存在及其内容","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get secret rc-app-secret -n aiops-e2e -o yaml","tool_args":{"namespace":"aiops-e2e","name":"rc-app-secret","kind":"Secret"},"purpose":"确认 Secret 是否存在以及其数据是否包含 APP_SECRET_TOKEN 键","evidence_type":"config_dependency","target_scope":"aiops-e2e/rc-app-secret","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"验证 Pod rc-config-secret-key-missing 的容器日志","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-config-secret-key-missing -n aiops-e2e --tail=200","tool_args":{"namespace":"aiops-e2e","name":"rc-config-secret-key-missing","container":"app","tail":"200"},"purpose":"获取容器日志以确认是否存在配置错误或启动失败的详细信息","evidence_type":"container_logs","target_scope":"aiops-e2e/rc-config-secret-key-missing/app","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-secret-key-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed          26m (x12 over 28m)     kubelet            Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret\n                  cni.projectcalico.org/containerID: 8f443601171b0e4049e100f3c3704966fe0c483b32880bd181c9fc13cf69ec95\n                  cni.projectcalico.org/podIP: 172.16.166.188/32\n                  cni.projectcalico.org/podIPs: 172.16.166.188/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n      Reason:       CreateContainerConfigError","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/970de2f3c1e64123/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/970de2f3c1e64123/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/970de2f3c1e64123/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME            TYPE     DATA   AGE   LABELS\nrc-app-secret   Opaque   1      28m   rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/970de2f3c1e64123/tools/002-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/970de2f3c1e64123/tools/002-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/970de2f3c1e64123/tools/002-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_logs","data":"kubectl_logs 输出摘要: raw_chars=225 lines=3\nCommand failed (exit 1):\nkubectl logs rc-config-secret-key-missing -n aiops-e2e --tail=200\nError from server (BadRequest): container \"app\" in pod \"rc-config-secret-key-missing\" is waiting to start: CreateContainerConfigError","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/970de2f3c1e64123/tools/003-evidence-kubectl_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/970de2f3c1e64123/tools/003-evidence-kubectl_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/970de2f3c1e64123/tools/003-evidence-kubectl_logs.summary.txt"}],"llm_analysis":"# 证据结论\n\n## 已采集证据\n1. **Pod 详细信息**：`rc-config-secret-key-missing` 处于 `Pending` 状态，且事件中显示 `Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret`，这表明 Pod 无法启动是因为缺少配置中的关键 Secret。\n2. **Secret 验证**：`rc-app-secret` 存在且类型为 `Opaque`，但数据字段为 1，意味着可能缺少 `APP_SECRET_TOKEN` 这个键。\n3. **容器日志**：尝试获取容器日志失败，错误信息指出容器尚未启动，因为存在 `CreateContainerConfigError`。\n\n## 未采集证据\n- 无。\n\n## 冲突证据\n- 无。","collection_summary":"计划 3 项，实际采集 2 项，未采集 1 项，完整度 67%；其中真实环境证据 8/9 项，完整度 89%；实际执行工具 7 个，匹配计划 2 个，未规划证据 5 个","plan_total":3,"plan_collected":2,"plan_completeness":0.6666666666666666,"environment_evidence_total":9,"environment_evidence_collected":8,"environment_evidence_completeness":0.8888888888888888,"executed_tool_count":7,"matched_tool_count":2,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"验证 Pod rc-config-secret-key-missing 的详细状态和关键事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-secret-key-missing -n aiops-e2e","purpose":"获取 Pod 的详细状态、事件和诊断信息，验证其 CreateContainerConfigError 的根本原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"验证 Secret rc-app-secret 是否存在及其内容","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get secret rc-app-secret -n aiops-e2e -o yaml","purpose":"确认 Secret 是否存在以及其数据是否包含 APP_SECRET_TOKEN 键","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"验证 Pod rc-config-secret-key-missing 的容器日志","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-config-secret-key-missing -n aiops-e2e --tail=200","purpose":"获取容器日志以确认是否存在配置错误或启动失败的详细信息","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e3(验证 Pod rc-config-secret-key-missing 的容器日志): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/3 项, 完整度: 89%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证 Pod rc-config-secret-key-missing 的详细状态和关键事件 | `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_by_name | 验证 Secret rc-app-secret 是否存在及其内容 | `kubectl get secret rc-app-secret -n aiops-e2e -o yaml` |
   | e3 | important | ❌ | kubectl_logs | 验证 Pod rc-config-secret-key-missing 的容器日志 | `kubectl logs rc-config-secret-key-missing -n aiops-e2e --tail=200` |

   ⚠️ 未采集原因:
   - e3(验证 Pod rc-config-secret-key-missing 的容器日志): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (15.4s)
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
   ✅ [汇总总结] 完成 (1m 6.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4230 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 56.4s
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
| **兼容归因层** | L4 |
| **问题分类** | ConfigError |
| **置信度** | 高 |
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
| 错误信息 | Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl describe pod rc-config-secret-key-missing` | `Warning Failed 24m (x12 over 25m) kubelet Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret` | Pod 无法启动，原因是 Secret 中缺少指定的 key `APP_SECRET_TOKEN` |
| 2 | Secret 内容 | `kubectl get secret rc-app-secret` | `NAME: rc-app-secret, TYPE: Opaque, DATA: 1` | Secret 存在，但未包含 `APP_SECRET_TOKEN` 这个 key |

### 证据关联分析

- **证据 #1 印证**：`Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret` 明确指出容器配置错误，无法找到所需的 key。
- **证据 #2 印证**：Secret `rc-app-secret` 存在，但只包含 1 个数据项，未包含 `APP_SECRET_TOKEN`，说明配置不完整或 key 名称不匹配。
- **因果链**：Pod 定义中引用了 `APP_SECRET_TOKEN`，但 Secret 中缺少该 key → 容器无法启动 → Pod 状态为 `CreateContainerConfigError`。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 容器日志 | important | 无法确认容器在启动时的完整行为，但由于容器未成功启动，此证据价值较低 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Secret aiops-e2e/rc-app-secret 中缺少 key APP_SECRET_TOKEN        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Pod 定义中引用了 APP_SECRET_TOKEN，但该 key 不存在于 Secret 中    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器启动失败（CreateContainerConfigError）                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod rc-config-secret-key-missing 状态为 CreateContainerConfigError，无法启动 |
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (`Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret`) 和证据 #2 (`Secret rc-app-secret DATA: 1`)，问题的根本原因是**Secret `aiops-e2e/rc-app-secret` 中缺少 key `APP_SECRET_TOKEN`**，导致 Pod `rc-config-secret-key-missing` 无法启动并持续报错 `CreateContainerConfigError`。

**置信度**：高 (90%)
- ✅ `kubectl describe pod` 明确指出配置错误
- ✅ `kubectl get secret` 确认 Secret 中缺少关键 key
- ⚠️ 缺少容器日志，但由于容器未成功启动，此证据价值较低

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 向 Secret 中添加缺失的 key `APP_SECRET_TOKEN`**

```bash
kubectl create secret generic rc-app-secret \
  --from-literal=APP_SECRET_TOKEN="your-secret-value" \
  --namespace=aiops-e2e \
  --dry-run=client -o yaml | kubectl apply -f -
```

*依据*：Pod 启动失败的直接原因是缺少该 key，添加后应能正常启动

**2. [可选] 检查 Pod 定义中是否引用了正确的 Secret key**

```bash
kubectl get pod rc-config-secret-key-missing -n aiops-e2e -o yaml
```

*目的*：确认是否引用了 `APP_SECRET_TOKEN`，并确保 key 名称与 Secret 中一致

### 后续优化

1. **配置自动检测机制**：在 CI/CD 流程中添加对 Secret 键值的校验，避免部署时出现缺失 key 的问题。
2. **文档化 Secret 使用规范**：确保团队成员了解哪些 Secret key 是必须的。
3. **使用 ConfigMap 或其他配置管理工具**：如果 Secret 只用于配置，可考虑使用 ConfigMap。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Secret 中已包含 `APP_SECRET_TOKEN` | `kubectl get secret rc-app-secret -n aiops-e2e -o jsonpath='{.data}'` | 应包含 `APP_SECRET_TOKEN` 的 base64 编码值 |
| 2. 确认 Pod 已成功启动 | `kubectl get pod rc-config-secret-key-missing -n aiops-e2e` | STATUS: Running |
| 3. 检查 Pod 日志确认无错误 | `kubectl logs rc-config-secret-key-missing -n aiops-e2e` | 无错误信息，正常输出 |

---

## ⚠️ 注意事项

- 如果 Secret 由外部系统（如 Vault、ArgoCD）管理，请确认同步机制是否正常。
- 如果使用 Helm 或 Kustomize 部署，请检查模板中是否正确引用了 Secret。
- 如果 Secret 在多个环境（如 dev/staging/prod）中使用，请确认所有环境都已正确配置。

---

## 📊 性能统计

├─ 总耗时: 3.9m
├─ 问题定位: 73.6s (31%) ✅
├─ 证据链采集: 80.6s (34%) ✅
├─ 根因分析: 15.4s (7%) ✅
├─ 汇总总结: 66.8s (28%) ✅
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
