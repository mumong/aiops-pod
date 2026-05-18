======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 09839b9c8ade4e69]

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
      📄 NAME                           READY   STATUS                       RESTARTS   AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-config-secret-key-missing   0/1     CreateCo
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 输出摘要: raw_chars=207 lines=3
Command failed (exit 1):
kubectl logs rc-config-secret-key-missing -n aiops-e2e --previous
Error from server (BadRequest): previous terminated contain
   💭 [问题定位] 调用工具: kubectl_logs
   💭 [问题定位] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 输出摘要: raw_chars=214 lines=3
Command failed (exit 1):
kubectl logs rc-config-secret-key-missing -n aiops-e2e
Error from server (BadRequest): container "app" in pod "rc-config-secret-key-mi
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-secret-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          7m13s (x12 over 9m9s)  kubelet            Error: co
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME            TYPE     DATA   AGE     LABELS
rc-app-secret   Opaque   1      9m11s   rootcause-e2e=true
   💭 [问题定位] 调用工具: kubectl_get_yaml
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (37.7s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'Secret 缺失 APP_SECRET_TOKEN 键', 'probability': '高', 'reason': "describe 明确指出 'Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret'，说明配置缺失。"}]
   entities=[{"type": "Pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "rc-app-secret", "namespace": "aiops-e2e"}]
   reasoning=当前环境中存在一个异常 Pod 'rc-config-secret-key-missing'，其状态为 'CreateContainerConfigError'，且事件中明确指出 'Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret'。这表明该异常属于 ConfigError 类型，归一化为 L4 层级，因为属于应用配置错误。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "应用配置错误", "confidence": 0.5, "reasoning": "当前环境中存在一个异常 Pod 'rc-config-secret-key-missing'，其状态为 'CreateContainerConfigError'，且事件中明确指出 'Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret'。这表明该异常属于 ConfigError 类型，归一化为 L4 层级，因为属于应用配置错误。", "abnormal_pods": [{"name": "rc-config-secret-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}], "pod_status_keyword": "CreateContainerConfigError", "pod_abnormal_type": "ConfigError", "status_category": "app_config/app_health", "key_entities": [{"type": "Pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "rc-app-secret", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Secret 缺失 APP_SECRET_TOKEN 键", "probability": "高", "reason": "describe 明确指出 'Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret'，说明配置缺失。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-secret-key-missing                        0/1     CreateContainerConfigError   0             8m58s   172.16.166.188   node1    <none>           <none>            app=rc-config-secret-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/09839b9c8ade4e69/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/09839b9c8ade4e69/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/09839b9c8ade4e69/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-config-secret-key-missing
namespace: aiops-e2e
creationTimestamp: 2026-05-15T02:31:48Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalize
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Secret
name: rc-app-secret
namespace: aiops-e2e
type: Opaque
data_keys: EXISTING_SECRET_KEY
has_dockerconfigjson: False
docker_secret_type_valid: False
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (1m 59.2s)
   📤 → 下游数据: evidence_items=10/10
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证异常 Pod 'rc-config-secret-key-missing' 的详细配置信息，特别是其引用的 Secret 和 volume 配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-config-secret-key-missing -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-config-secret-key-missing","namespace":"aiops-e2e","output":"yaml"},"purpose":"检查 Pod 的 YAML 配置，特别是其 env/volume 引用的 Secret，验证 APP_SECRET_TOKEN 键是否被正确引用","evidence_type":"Pod configuration","target_scope":"aiops-e2e/rc-config-secret-key-missing","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"验证 Secret 'rc-app-secret' 的内容，确认 APP_SECRET_TOKEN 键是否存在","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get secret rc-app-secret -n aiops-e2e -o yaml","tool_args":{"kind":"Secret","name":"rc-app-secret","namespace":"aiops-e2e","output":"yaml"},"purpose":"检查 Secret 的 YAML 内容，确认 APP_SECRET_TOKEN 键是否存在且值为 Base64 编码","evidence_type":"Secret content","target_scope":"aiops-e2e/rc-app-secret","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"检查异常 Pod 'rc-config-secret-key-missing' 的 Events，确认 'APP_SECRET_TOKEN' 键缺失的具体上下文","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-secret-key-missing","tool_args":{"kind":"Event","namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-config-secret-key-missing"},"purpose":"验证 Events 中是否包含 'Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret' 的具体上下文","evidence_type":"Event log","target_scope":"aiops-e2e/rc-config-secret-key-missing","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"验证异常 Pod 'rc-config-secret-key-missing' 的容器 spec，确认容器是否引用了正确的 Secret 键","level":"important","tool":"kubernetes_jq_query","command":"kubectl get pod rc-config-secret-key-missing -n aiops-e2e -o json | jq '.spec.containers[] | select(.name == 'app')'","tool_args":{"kind":"Pod","name":"rc-config-secret-key-missing","namespace":"aiops-e2e","jq_query":".spec.containers[] | select(.name == 'app')"},"purpose":"通过 jq 提取容器 spec，确认容器是否引用了正确的 Secret 键","evidence_type":"Container spec","target_scope":"aiops-e2e/rc-config-secret-key-missing","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-config-secret-key-missing\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T02:31:48Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-config-secret-key-missing, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/runbook=pod-config-error.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=CreateContainerConfigError exitCode=None\n  message: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret\nvolumes:\n- {\"name\": \"kube-api-access-74hmf\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/09839b9c8ade4e69/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/09839b9c8ade4e69/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/09839b9c8ade4e69/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Secret\nname: rc-app-secret\nnamespace: aiops-e2e\ntype: Opaque\ndata_keys: EXISTING_SECRET_KEY\nhas_dockerconfigjson: False\ndocker_secret_type_valid: False","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/09839b9c8ade4e69/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/09839b9c8ade4e69/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/09839b9c8ade4e69/tools/002-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 10/10 项，完整度 100%；实际执行工具 7 个，匹配计划 4 个，未规划证据 3 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":10,"environment_evidence_collected":10,"environment_evidence_completeness":1.0,"executed_tool_count":7,"matched_tool_count":4,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1","description":"验证异常 Pod 'rc-config-secret-key-missing' 的详细配置信息，特别是其引用的 Secret 和 volume 配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-config-secret-key-missing -n aiops-e2e -o yaml","purpose":"检查 Pod 的 YAML 配置，特别是其 env/volume 引用的 Secret，验证 APP_SECRET_TOKEN 键是否被正确引用","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"验证 Secret 'rc-app-secret' 的内容，确认 APP_SECRET_TOKEN 键是否存在","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get secret rc-app-secret -n aiops-e2e -o yaml","purpose":"检查 Secret 的 YAML 内容，确认 APP_SECRET_TOKEN 键是否存在且值为 Base64 编码","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"检查异常 Pod 'rc-config-secret-key-missing' 的 Events，确认 'APP_SECRET_TOKEN' 键缺失的具体上下文","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-secret-key-missing","purpose":"验证 Events 中是否包含 'Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret' 的具体上下文","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"e4","description":"验证异常 Pod 'rc-config-secret-key-missing' 的容器 spec，确认容器是否引用了正确的 Secret 键","level":"important","tool":"kubernetes_jq_query","command":"kubectl get pod rc-config-secret-key-missing -n aiops-e2e -o json | jq '.spec.containers[] | select(.name == 'app')'","purpose":"通过 jq 提取容器 spec，确认容器是否引用了正确的 Secret 键","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_yaml | 验证异常 Pod 'rc-config-secret-key-missing' 的详细配置... | `kubectl get pod rc-config-secret-key-missing -n aiops-e2e -o yaml` |
   | e2 | critical | ✅ | kubectl_get_yaml | 验证 Secret 'rc-app-secret' 的内容，确认 APP_SECRET_T... | `kubectl get secret rc-app-secret -n aiops-e2e -o yaml` |
   | e3 | important | ✅ | kubectl_events | 检查异常 Pod 'rc-config-secret-key-missing' 的 Eve... | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-confi...` |
   | e4 | important | ✅ | kubernetes_jq_query | 验证异常 Pod 'rc-config-secret-key-missing' 的容器 s... | `kubectl get pod rc-config-secret-key-missing -n aiops-e2e -o json | jq '.spec...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (16.6s)
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
   ✅ [汇总总结] 完成 (1m 57.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4211 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 51.3s
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
| **问题分类** | ConfigError |
| **置信度** | 高 |
| **证据完整度** | 4/4 (100%) |

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
| 错误信息 | Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CreateContainerConfigError` | 容器配置错误 |
| 2 | Pod 描述 | `kubectl describe pod rc-config-secret-key-missing` | `Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret` | 明确指出 Secret 缺失 |
| 3 | Secret 内容 | `kubectl get secret rc-app-secret -o yaml` | `data_keys: EXISTING_SECRET_KEY` | 缺失 `APP_SECRET_TOKEN` 键 |
| 4 | Pod 配置 | `kubectl get pod rc-config-secret-key-missing -o yaml` | `envFrom: - secretRef: name: rc-app-secret` | 容器依赖 `rc-app-secret` 中的 `APP_SECRET_TOKEN` |

### 证据关联分析

- **证据 #2 + #3 印证**：Pod 期望从 Secret 中获取 `APP_SECRET_TOKEN`，但 Secret 中并未包含该键。
- **证据链**：容器依赖的 Secret 缺少关键键 → 容器无法启动 → Pod 状态为 `CreateContainerConfigError`

### 缺失证据（无）

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Secret 'rc-app-secret' 缺失键 'APP_SECRET_TOKEN'                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器在启动时引用 Secret 中的 APP_SECRET_TOKEN 键，但该键不存在  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器因配置错误无法启动，导致 Pod 状态为 'CreateContainerConfigError' │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 'CreateContainerConfigError'，无法正常启动             │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2 和 #3，问题的根本原因是 **Secret `rc-app-secret` 缺失键 `APP_SECRET_TOKEN`**，导致容器在启动时无法正确读取配置，从而无法创建容器，Pod 状态为 `CreateContainerConfigError`。

**置信度**：高 (95%)
- ✅ `kubectl describe pod` 明确指出 `Error: couldn't find key APP_SECRET_TOKEN`
- ✅ `kubectl get secret` 显示 Secret 中确实没有该键
- ✅ Pod 配置确认其依赖该键

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 向 Secret 中添加缺失的 `APP_SECRET_TOKEN` 键**

```bash
kubectl patch secret rc-app-secret -n aiops-e2e -p '{"data":{"APP_SECRET_TOKEN":"base64_encoded_value"}}'
```

*说明*：将 `base64_encoded_value` 替换为实际的 base64 编码的 `APP_SECRET_TOKEN` 值。

**2. [验证] 重新查看 Pod 状态**

```bash
kubectl get pod rc-config-secret-key-missing -n aiops-e2e
```

*预期*：Pod 应该进入 `Running` 状态。

**3. [可选] 检查容器日志（如果需要进一步确认）**

```bash
kubectl logs rc-config-secret-key-missing -n aiops-e2e
```

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-config-secret-key-missing -n aiops-e2e` | STATUS: Running |
| 2. 确认 Secret 包含 APP_SECRET_TOKEN | `kubectl get secret rc-app-secret -n aiops-e2e -o jsonpath='{.data}'` | 包含 `APP_SECRET_TOKEN` 键 |
| 3. 确认容器启动无错误 | `kubectl logs rc-config-secret-key-missing -n aiops-e2e` | 无错误日志 |

---

## ⚠️ 注意事项

- 如果 Secret 的 `APP_SECRET_TOKEN` 值需要从外部导入（例如 CI/CD、手动输入），请确保其 base64 编码正确。
- 如果问题仍然存在，请检查容器的 `envFrom` 或 `env` 配置是否正确引用了 `APP_SECRET_TOKEN`。
- 建议对 Secret 的更新操作进行版本控制，防止配置错误。

---

## 📄 附录：关键命令汇总

| 命令 | 用途 |
|------|------|
| `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` | 查看 Pod 详细状态和事件 |
| `kubectl get secret rc-app-secret -n aiops-e2e -o yaml` | 查看 Secret 内容 |
| `kubectl patch secret rc-app-secret -n aiops-e2e -p '{"data":{"APP_SECRET_TOKEN":"base64_encoded_value"}}'` | 向 Secret 添加缺失的键 |
| `kubectl get pod rc-config-secret-key-missing -n aiops-e2e` | 查看 Pod 当前状态 |

---

## 📊 性能统计

├─ 总耗时: 4.9m
├─ 问题定位: 37.7s (13%) ✅
├─ 证据链采集: 119.2s (41%) ✅
├─ 根因分析: 16.6s (6%) ✅
├─ 汇总总结: 117.7s (40%) ✅
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
