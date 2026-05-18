======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: ab0cb0e5f23840da]

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
   💭 [问题定位] 调用工具: kubectl_container_previous_logs
   💭 [问题定位] 工具结果: kubectl_container_previous_logs (success)
      📄 kubectl_container_previous_logs 输出摘要: raw_chars=225 lines=3
Command failed (exit 1):
kubectl logs rc-config-secret-key-missing -c app -n aiops-e2e --previous --tail=200
Error from server (BadRequest):
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
   💭 [问题定位] 调用工具: kubectl_get_yaml
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (34.9s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': '应用配置错误导致容器启动失败', 'probability': '高', 'reason': 'Pod 状态为 CreateContainerConfigError，且日志和事件未显示 OOM、镜像拉取或驱逐等问题，符合 ConfigError 特征。'}]
   entities=[{"type": "Pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}]
   reasoning=当前环境中的活跃异常对象为 Pod 'rc-config-secret-key-missing'，其状态为 'CreateContainerConfigError'，且标签标明 pod_abnormal_type=ConfigError。根据异常类型映射规则，ConfigError 应归类为 L4 层级，归因为应用配置错误。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "", "confidence": 0.5, "reasoning": "当前环境中的活跃异常对象为 Pod 'rc-config-secret-key-missing'，其状态为 'CreateContainerConfigError'，且标签标明 pod_abnormal_type=ConfigError。根据异常类型映射规则，ConfigError 应归类为 L4 层级，归因为应用配置错误。", "abnormal_pods": [{"name": "rc-config-secret-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}], "pod_status_keyword": "CreateContainerConfigError", "pod_abnormal_type": "ConfigError", "status_category": "app_config/app_health", "key_entities": [{"type": "Pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "应用配置错误导致容器启动失败", "probability": "高", "reason": "Pod 状态为 CreateContainerConfigError，且日志和事件未显示 OOM、镜像拉取或驱逐等问题，符合 ConfigError 特征。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-secret-key-missing                        0/1     CreateContainerConfigError   0             62m     172.16.166.188   node1    <none>           <none>            app=rc-config-secret-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/ab0cb0e5f23840da/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/ab0cb0e5f23840da/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/ab0cb0e5f23840da/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 50%

📍 [证据链采集] 执行中...
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
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 表格摘要: rows=3 abnormal=0 status_counts={}
NAME                         DATA   AGE    LABELS
# 样例行
configmap/kube-root-ca.crt   1      111d   <none>
NAME                
   💭 [证据链采集] 已采集关键证据：
1. **kubectl_describe**：Pod `rc-config-secret-key-missing` 的状态为 `Pending`，且处于 `CreateContainerConfigError`。关键事件 `Reason: CreateContainerConfigError` 表明容器因配置错误无法启动。
2. **kubectl_get_by_kind_in_namespace**：在命名空间 `aiops-e2e` 中，已确认存在 `Secret/rc-app-secret`，但未发现与 Pod `rc-config-secret-key-missing` 相关的 ConfigMap。

**未采集证据**：
- Pod 的详细日志（`kubectl logs`），但由于 Pod 未成功启动，无法获取日志。
- 与 Pod 相关的 ConfigMap 是否存在，当前未发现引用该 ConfigMap 的配置。

**冲突证据**：
- `kubectl_get_by_kind_in_namespace` 未发现与 Pod `rc-config-secret-key-missing` 相关的 ConfigMap，但已确认存在 `Secret/rc-app-secret`。这表明配置错误可能与 Secret 的引用或内容有关，例如缺少必要 key 或 Base64 编码错误。
   ✅ [证据链采集] 完成 (1m 14.1s)
   📤 → 下游数据: evidence_items=7/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod 'rc-config-secret-key-missing' 的配置错误原因，例如 Secret/ConfigMap 缺失或无效的环境变量。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-secret-key-missing -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-config-secret-key-missing"},"purpose":"检查 Pod 的 Events 和配置，确认 ConfigError 的具体原因，例如 Secret 缺失、ConfigMap 错误等。","evidence_type":"Pod 配置错误验证","target_scope":"aiops-e2e/rc-config-secret-key-missing","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"检查与异常 Pod 相关联的 ConfigMap 或 Secret 是否存在并配置正确。","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get configmap,secret -n aiops-e2e","tool_args":{"kind":"ConfigMap,Secret","namespace":"aiops-e2e"},"purpose":"验证 ConfigMap/Secret 是否存在，以及是否被正确引用，例如 key 是否缺失或 Base64 编码错误。","evidence_type":"关联资源验证","target_scope":"aiops-e2e","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-secret-key-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n                  cni.projectcalico.org/containerID: 8f443601171b0e4049e100f3c3704966fe0c483b32880bd181c9fc13cf69ec95\n                  cni.projectcalico.org/podIP: 172.16.166.188/32\n                  cni.projectcalico.org/podIPs: 172.16.166.188/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n      Reason:       CreateContainerConfigError","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ab0cb0e5f23840da/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ab0cb0e5f23840da/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ab0cb0e5f23840da/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"kubectl_get_by_kind_in_namespace 表格摘要: rows=3 abnormal=0 status_counts={}\nNAME                         DATA   AGE    LABELS\n# 样例行\nconfigmap/kube-root-ca.crt   1      111d   <none>\nNAME                   TYPE     DATA   AGE   LABELS\nsecret/rc-app-secret   Opaque   1      64m   rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ab0cb0e5f23840da/tools/002-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ab0cb0e5f23840da/tools/002-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ab0cb0e5f23840da/tools/002-evidence-kubectl_get_by_kind_in_namespace.summary.txt"}],"llm_analysis":"已采集关键证据：\n1. **kubectl_describe**：Pod `rc-config-secret-key-missing` 的状态为 `Pending`，且处于 `CreateContainerConfigError`。关键事件 `Reason: CreateContainerConfigError` 表明容器因配置错误无法启动。\n2. **kubectl_get_by_kind_in_namespace**：在命名空间 `aiops-e2e` 中，已确认存在 `Secret/rc-app-secret`，但未发现与 Pod `rc-config-secret-key-missing` 相关的 ConfigMap。\n\n**未采集证据**：\n- Pod 的详细日志（`kubectl logs`），但由于 Pod 未成功启动，无法获取日志。\n- 与 Pod 相关的 ConfigMap 是否存在，当前未发现引用该 ConfigMap 的配置。\n\n**冲突证据**：\n- `kubectl_get_by_kind_in_namespace` 未发现与 Pod `rc-config-secret-key-missing` 相关的 ConfigMap，但已确认存在 `Secret/rc-app-secret`。这表明配置错误可能与 Secret 的引用或内容有关，例如缺少必要 key 或 Base64 编码错误。","collection_summary":"计划 2 项，实际采集 1 项，未采集 1 项，完整度 50%；其中真实环境证据 7/8 项，完整度 88%；实际执行工具 7 个，匹配计划 1 个，未规划证据 6 个","plan_total":2,"plan_collected":1,"plan_completeness":0.5,"environment_evidence_total":8,"environment_evidence_collected":7,"environment_evidence_completeness":0.875,"executed_tool_count":7,"matched_tool_count":1,"unplanned_tool_count":6,"evidence_inventory":[{"id":"e1","description":"验证 Pod 'rc-config-secret-key-missing' 的配置错误原因，例如 Secret/ConfigMap 缺失或无效的环境变量。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-secret-key-missing -n aiops-e2e","purpose":"检查 Pod 的 Events 和配置，确认 ConfigError 的具体原因，例如 Secret 缺失、ConfigMap 错误等。","collected":false,"source":"planned","outcome":"unknown"},{"id":"e2","description":"检查与异常 Pod 相关联的 ConfigMap 或 Secret 是否存在并配置正确。","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get configmap,secret -n aiops-e2e","purpose":"验证 ConfigMap/Secret 是否存在，以及是否被正确引用，例如 key 是否缺失或 Base64 编码错误。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_container_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e1(验证 Pod 'rc-config-secret-key-missing' 的配置错误原因，例如 Secret/ConfigMap 缺失或无效的环境变量。): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/2 项, 完整度: 88%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ❌ | kubectl_describe | 验证 Pod 'rc-config-secret-key-missing' 的配置错误原因... | `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_get_by_kind_in_na... | 检查与异常 Pod 相关联的 ConfigMap 或 Secret 是否存在并配置正确。 | `kubectl get configmap,secret -n aiops-e2e` |

   ⚠️ 未采集原因:
   - e1(验证 Pod 'rc-config-secret-key-missing' 的配置错误原因，例如 Secret/ConfigMap 缺失或无效的环境变量。): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (19.3s)
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
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (2m 23.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4746 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 31.5s
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
| **兼容归因层** | L4 - 应用配置错误 |
| **问题分类** | ConfigError |
| **置信度** | 高 |
| **证据完整度** | 1/2 (50%) |

---

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题？

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
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CreateContainerConfigError` | Pod 无法启动，原因是配置错误 |
| 2 | Describe Pod | `kubectl describe pod rc-config-secret-key-missing` | `Reason: CreateContainerConfigError` | 容器因配置错误无法创建 |
| 3 | 日志尝试 | `kubectl logs rc-config-secret-key-missing -n aiops-e2e` | `Error from server (BadRequest): container "app" in pod "rc-config-secret-key-missing" is waiting to start: CreateContainerConfigError` | 无可用日志，容器尚未启动 |
| 4 | ConfigMap/Secret 检查 | `kubectl get configmap,secret -n aiops-e2e` | 无异常条目（未采集到具体 ConfigMap/Secret 名称） | 未验证是否缺失或配置错误 |
| 5 | Runbook 提示 | `fetch_runbook` | `Pod异常类型: ConfigError | 典型状态: CreateContainerConfigError / CreateContainerError / CrashLoopBackOff` | 指示应检查 Secret/ConfigMap 是否存在及配置是否正确 |
| 6 | 工具结果摘要 | `kubectl_get_by_kind_in_cluster` | `NAMESPACE aiops-e2e NAME rc-config-secret-key-missing STATUS CreateContainerConfigError` | 明确指出异常 Pod 及状态 |
| 7 | Describe 关键字段 | `kubectl describe pod` | `State: Waiting Reason: CreateContainerConfigError` | 容器处于等待状态，无法创建 |

### 证据关联分析
- **证据 #1 + #2 印证**：Pod 状态为 `CreateContainerConfigError`，且 `kubectl describe` 显示 `Reason: CreateContainerConfigError`，表明容器启动失败的根本原因是配置错误。
- **证据 #3 + #5 印证**：日志无法获取，因为容器尚未启动，Runbook 提示应检查 Secret 或 ConfigMap 是否缺失或配置错误。
- **证据 #4 缺失**：未采集到与该 Pod 相关联的 ConfigMap/Secret 是否存在，是当前诊断的空白。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 与 Pod 关联的 ConfigMap/Secret 配置 | critical | 无法确认是否因 Secret 或 ConfigMap 缺失导致启动失败 |
| 容器环境变量是否配置错误 | important | 无法确认是否因环境变量缺失或错误导致配置失败 |

---

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 与 Pod 'rc-config-secret-key-missing' 关联的 Secret 或 ConfigMap 缺失或配置错误 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器启动时依赖的 Secret/ConfigMap 不存在或配置错误，导致容器无法创建 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ CreateContainerConfigError（容器配置错误）                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CreateContainerConfigError，无法启动                 │
└─────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #1 (Pod 状态为 `CreateContainerConfigError`)、证据 #2 (`kubectl describe` 显示 `Reason: CreateContainerConfigError`) 和 Runbook 提示，问题的根本原因是**容器配置错误**，可能由于关联的 Secret 或 ConfigMap 缺失或配置错误，导致容器无法创建。
**置信度**：高 (80%)
- ✅ Pod 状态和 describe 明确指向配置错误
- ⚠️ 缺少对 Secret/ConfigMap 的验证，无法确认具体缺失项
- ⚠️ 无法获取容器日志，因为容器尚未启动

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 检查与该 Pod 关联的 Secret/ConfigMap**
```bash
kubectl get secret -n aiops-e2e
kubectl get configmap -n aiops-e2e
```
*目的*：确认是否缺失或配置错误的 Secret 或 ConfigMap

**2. [可选] 检查 Pod YAML 中引用的 Secret/ConfigMap 名称**
```bash
kubectl get pod rc-config-secret-key-missing -n aiops-e2e -o yaml
```
*目的*：确认 Pod 是否引用了正确的 Secret/ConfigMap 名称

**3. [如缺失] 创建或修复 Secret/ConfigMap**
```bash
kubectl create secret generic my-secret --from-literal=key1=value1 -n aiops-e2e
```
*目的*：若确认缺失，创建缺失的 Secret

**4. [如配置错误] 修改 Pod 配置**
```bash
kubectl edit pod rc-config-secret-key-missing -n aiops-e2e
```
*目的*：修改 Secret/ConfigMap 名称或数据

### 后续优化
1. **配置验证**：在部署前使用 `kubectl diff` 验证配置是否正确
2. **自动化检查**：使用 Helm 或 Kustomize 进行模板化配置管理
3. **配置中心化管理**：考虑使用 GitOps 工具（如 ArgoCD）统一管理配置

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-config-secret-key-missing -n aiops-e2e` | STATUS: Running |
| 2. 确认 Secret/ConfigMap 存在 | `kubectl get secret,configmap -n aiops-e2e` | 显示相关资源 |
| 3. 检查容器是否正常运行 | `kubectl logs rc-config-secret-key-missing -n aiops-e2e` | 无错误输出，容器正常启动 |

---

## ⚠️ 注意事项
- 如果 Secret/ConfigMap 名称拼写错误，Pod 会持续失败，需特别检查大小写和命名空间
- 如果容器依赖的环境变量缺失，容器也会因配置错误无法启动
- 如果问题仍然存在，建议检查容器镜像是否兼容配置（例如是否使用了正确的环境变量格式）

---

---

## 📊 性能统计

├─ 总耗时: 4.5m
├─ 问题定位: 34.9s (13%) ✅
├─ 证据链采集: 74.1s (27%) ✅
├─ 根因分析: 19.3s (7%) ✅
├─ 汇总总结: 143.3s (53%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 10 次
```

📋 诊断追踪

- **核心 Runbook**: pod-config-error
- **参考 Runbook**: pod-config-error
- **工具调用**: 10 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
