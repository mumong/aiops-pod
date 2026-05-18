======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 8b11a559638d4995]

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
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-configmap-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
                  cni.projectcalico.org/containerID: c6590992f796724e303037
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 输出摘要: raw_chars=213 lines=3
Command failed (exit 1):
kubectl logs rc-config-configmap-key-missing -n aiops-e2e --previous
Error from server (BadRequest): previous terminated cont
   💭 [问题定位] 调用工具: kubectl_logs
   💭 [问题定位] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 输出摘要: raw_chars=220 lines=3
Command failed (exit 1):
kubectl logs rc-config-configmap-key-missing -n aiops-e2e
Error from server (BadRequest): container "app" in pod "rc-config-configmap-
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-config-configmap-key-missing
namespace: aiops-e2e
creationTimestamp: 2026-05-15T00:41:57Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
final
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "ConfigError",
  "confidence": 0.95,
  "reasoning": "Pod rc-config-configmap-key-missing 状态为 CreateContainerConfigError，describe 显示关键错误信息 'couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config'，表明配置缺失。日志未显示容器已启动，因此排除 OOMKilled、ImagePullFailed 等其他类型。该错误属于典型的 ConfigError，归类为 L4。",
  "abnormal_pods": [
    "rc-config-configmap-key-missing"
  ],
  "abnormal_groups": {
    "ConfigError": [
      "rc-config-configmap-key-missing"
    ]
  },
  "pod_status_keyword": "CreateContainerConfigError",
  "pod_abnormal_type": "ConfigError",
  "status_category": "ConfigError",
  "key_entities": [
    "ConfigMap aiops-e2e/rc-app-config",
    "Pod rc-config-configmap-key-missing",
    "app container in Pod rc-config-configmap-key-missing"
  ],
  "possible_scenarios": [
    "ConfigMap 缺失 key APP_BOOT_MODE，导致容器启动失败",
    "Pod 的 env/envFrom 引用了不存在的 ConfigMap key，导致配置解析失败",
    "ConfigMap 错误引用或未正确绑定到容器的环境变量"
  ]
}
   ✅ [问题定位] 完成 (42.4s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[]
   entities=[]
   reasoning=Pod rc-config-configmap-key-missing 状态为 CreateContainerConfigError，describe 显示关键错误信息 'couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config'，表明配置缺失。日志未显示容器已启动，因此排除 OOMKilled、ImagePullFailed 等其他类型。该错误属于典型的 ConfigError，归类为 L4。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.95, "reasoning": "Pod rc-config-configmap-key-missing 状态为 CreateContainerConfigError，describe 显示关键错误信息 'couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config'，表明配置缺失。日志未显示容器已启动，因此排除 OOMKilled、ImagePullFailed 等其他类型。该错误属于典型的 ConfigError，归类为 L4。", "abnormal_pods": [{"name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}], "pod_status_keyword": "CreateContainerConfigError", "pod_abnormal_type": "ConfigError", "status_category": "app_config", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-configmap-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-configmap-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-configmap-key-missing                     0/1     CreateContainerConfigError   0             86m     172.16.166.190   node1    <none>           <none>            app=rc-config-configmap-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/8b11a559638d4995/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/8b11a559638d4995/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/8b11a559638d4995/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME            DATA   AGE   LABELS
rc-app-config   1      88m   rootcause-e2e=true
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (1m 25.1s)
   📤 → 下游数据: evidence_items=6/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 ConfigMap 'rc-app-config' 是否存在以及其是否包含缺失的 key 'APP_BOOT_MODE'","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap rc-app-config -n aiops-e2e -o yaml","tool_args":{"kind":"ConfigMap","name":"rc-app-config","namespace":"aiops-e2e"},"purpose":"确认 ConfigMap 是否存在以及是否包含缺失的 key","evidence_type":"config_verification","target_scope":"aiops-e2e namespace","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e2","description":"检查 Pod 'rc-config-configmap-key-missing' 的事件信息，以确认配置错误的具体原因","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-configmap-key-missing","tool_args":{"kind":"Pod","name":"rc-config-configmap-key-missing","namespace":"aiops-e2e"},"purpose":"获取与异常 Pod 相关的事件信息","evidence_type":"event_analysis","target_scope":"aiops-e2e namespace","acceptable_tools":["kubectl_events"],"counts_for_completeness":true},{"id":"e3","description":"检查 Pod 'rc-config-configmap-key-missing' 的完整 YAML 配置，确认其引用的 ConfigMap 是否正确","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-config-configmap-key-missing -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-config-configmap-key-missing","namespace":"aiops-e2e"},"purpose":"检查 Pod 的 YAML 配置，确认 ConfigMap 引用是否正确","evidence_type":"yaml_configuration_check","target_scope":"aiops-e2e namespace","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME            DATA   AGE   LABELS\nrc-app-config   1      88m   rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/8b11a559638d4995/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/8b11a559638d4995/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/8b11a559638d4995/tools/001-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 3 项，实际采集 1 项，未采集 2 项，完整度 33%；其中真实环境证据 6/8 项，完整度 75%；实际执行工具 5 个，匹配计划 1 个，未规划证据 4 个","plan_total":3,"plan_collected":1,"plan_completeness":0.3333333333333333,"environment_evidence_total":8,"environment_evidence_collected":6,"environment_evidence_completeness":0.75,"executed_tool_count":5,"matched_tool_count":1,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"验证 ConfigMap 'rc-app-config' 是否存在以及其是否包含缺失的 key 'APP_BOOT_MODE'","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap rc-app-config -n aiops-e2e -o yaml","purpose":"确认 ConfigMap 是否存在以及是否包含缺失的 key","collected":false,"source":"planned","outcome":"unknown"},{"id":"e2","description":"检查 Pod 'rc-config-configmap-key-missing' 的事件信息，以确认配置错误的具体原因","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-configmap-key-missing","purpose":"获取与异常 Pod 相关的事件信息","collected":false,"source":"planned","outcome":"unknown"},{"id":"e3","description":"检查 Pod 'rc-config-configmap-key-missing' 的完整 YAML 配置，确认其引用的 ConfigMap 是否正确","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-config-configmap-key-missing -n aiops-e2e -o yaml","purpose":"检查 Pod 的 YAML 配置，确认 ConfigMap 引用是否正确","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":["e1(验证 ConfigMap 'rc-app-config' 是否存在以及其是否包含缺失的 key 'APP_BOOT_MODE'): 已规划但工具执行失败或无匹配结果","e2(检查 Pod 'rc-config-configmap-key-missing' 的事件信息，以确认配置错误的具体原因): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/3 项, 完整度: 75%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ❌ | kubectl_get_by_name | 验证 ConfigMap 'rc-app-config' 是否存在以及其是否包含缺失的 k... | `kubectl get configmap rc-app-config -n aiops-e2e -o yaml` |
   | e2 | important | ❌ | kubectl_events | 检查 Pod 'rc-config-configmap-key-missing' 的事件信... | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-confi...` |
   | e3 | important | ✅ | kubectl_get_yaml | 检查 Pod 'rc-config-configmap-key-missing' 的完整 ... | `kubectl get pod rc-config-configmap-key-missing -n aiops-e2e -o yaml` |

   ⚠️ 未采集原因:
   - e1(验证 ConfigMap 'rc-app-config' 是否存在以及其是否包含缺失的 key 'APP_BOOT_MODE'): 已规划但工具执行失败或无匹配结果
   - e2(检查 Pod 'rc-config-configmap-key-missing' 的事件信息，以确认配置错误的具体原因): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (12.7s)
   📤 → 下游数据: root_cause=Pod 'rc-config-configmap-key-missing' 状态为 CreateContainerConfigError，describe 显示关键错误信息 'couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config'，表明配置缺失。日志未显示容器已启动，因此排除 OOMKilled、ImagePullFailed 等其他类型。该错误属于典型的 ConfigError。
   confidence=95%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [], "causal_chain": {}, "root_cause": "Pod 'rc-config-configmap-key-missing' 状态为 CreateContainerConfigError，describe 显示关键错误信息 'couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config'，表明配置缺失。日志未显示容器已启动，因此排除 OOMKilled、ImagePullFailed 等其他类型。该错误属于典型的 ConfigError。", "root_cause_summary": "Pod 'rc-config-configmap-key-missing' 状态为 CreateContainerConfigError，describe 显示关键错误信息 'couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config'，表明配置缺失。日志未显示容器已启动，因此排除 OOMKilled、ImagePullFailed 等其他类型。该错误属于典型的 ConfigError。", "confidence": 0.95, "confidence_reason": "", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [], "limitations": "未验证 ConfigMap 'rc-app-config' 是否存在以及其是否包含缺失的 key 'APP_BOOT_MODE'，建议进一步检查。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'rc-config-configmap-key-missing' 状态为 CreateContainerConfigError，describe 显示关键错误信息 'couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-...
   置信度: 95%

📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 16.4s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4619 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 36.6s
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
| **置信度** | 高 (95%) |
| **证据完整度** | 1/3 (33%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | rc-config-configmap-key-missing |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | kubectl get pod | `STATUS: CreateContainerConfigError` | Pod 无法创建容器，配置错误 |
| 2 | Pod 详细信息 | kubectl describe pod rc-config-configmap-key-missing | `Reason: CreateContainerConfigError` | 事件显示配置缺失 |
| 3 | Pod YAML 配置 | kubectl get pod -o yaml | 引用了 ConfigMap `aiops-e2e/rc-app-config` | Pod 配置引用了不存在的 key |
| 4 | ConfigMap 存在性 | kubectl get configmap rc-app-config -n aiops-e2e | `DATA: 1` | ConfigMap 存在，但缺少 key `APP_BOOT_MODE` |
| 5 | 日志 | kubectl logs rc-config-configmap-key-missing -n aiops-e2e | `Error from server (BadRequest): container "app" in pod "rc-config-configmap-key-missing" is waiting to start: CreateContainerConfigError` | 容器未启动，原因是配置错误 |
| 6 | 上游工具摘要 | kubectl_get_by_kind_in_cluster | 异常行: `aiops-e2e rc-config-configmap-key-missing 0/1 CreateContainerConfigError` | 明确指出 Pod 配置错误 |

### 证据关联分析

- **证据 #1 + #2 + #3 印证**：Pod 状态为 `CreateContainerConfigError`，`kubectl describe` 显示 `Reason: CreateContainerConfigError`，`kubectl get pod -o yaml` 显示引用了 ConfigMap `aiops-e2e/rc-app-config`，但未找到 key `APP_BOOT_MODE`。
- **证据链**：Pod 引用了 ConfigMap 中不存在的 key `APP_BOOT_MODE` → 容器无法创建 → Pod 状态为 `CreateContainerConfigError`。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| Pod 事件信息 | critical | 无法确认配置错误的详细原因 |
| 容器启动前日志 | important | 无法确认容器启动失败的上下文 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ ConfigMap `aiops-e2e/rc-app-config` 缺失 key `APP_BOOT_MODE`     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Pod 引用了不存在的 key → 容器无法创建 → CreateContainerConfigError │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器配置错误（CreateContainerConfigError）                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CreateContainerConfigError，无法启动容器               │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Pod 状态为 CreateContainerConfigError) 和证据 #4 (ConfigMap 存在但缺少 key `APP_BOOT_MODE`)，问题的根本原因是 **Pod 引用了 ConfigMap 中不存在的 key `APP_BOOT_MODE`**，导致容器无法创建。  
**置信度**：高 (95%)  
- ✅ Pod 状态为 CreateContainerConfigError  
- ✅ describe 显示 `couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config`  
- ⚠️ 缺失事件信息，无法确认配置错误的详细原因  

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 在 ConfigMap 中添加缺失的 key `APP_BOOT_MODE`**

```bash
kubectl edit configmap rc-app-config -n aiops-e2e
```

*操作步骤*：
- 打开 ConfigMap `rc-app-config` 的编辑界面。
- 添加如下字段：
```yaml
data:
  APP_BOOT_MODE: "normal"
```
- 保存并退出。

*依据*：`kubectl describe pod` 显示 `couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config`，说明该 key 缺失。

**2. [可选] 检查 Pod 事件信息**

```bash
kubectl describe pod rc-config-configmap-key-missing -n aiops-e2e
```

*目的*：查看更详细的事件信息，确认配置错误的具体原因。

### 后续优化

1. **验证修复效果**
   - 等待 Pod 重新拉起。
   - 检查 Pod 是否变为 `Running` 状态。

2. **配置监控告警**
   - 对 ConfigMap 的变更设置监控告警，避免未来出现类似问题。
   - 使用 Prometheus 监控 Pod 状态，设置异常状态告警。

3. **文档记录**
   - 记录此次问题的原因和修复过程，为团队提供参考。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-config-configmap-key-missing -n aiops-e2e` | STATUS: Running |
| 2. 检查容器是否启动 | `kubectl describe pod rc-config-configmap-key-missing -n aiops-e2e` | 无 `CreateContainerConfigError` |
| 3. 检查 ConfigMap 是否包含 `APP_BOOT_MODE` | `kubectl get configmap rc-app-config -n aiops-e2e -o yaml` | data 中包含 `APP_BOOT_MODE` |

---

## ⚠️ 注意事项

- 确保在 ConfigMap 中添加的 key 值符合应用实际需求。
- 如果修复后 Pod 仍然异常，请检查其他相关配置（如环境变量、卷挂载等）。
- 可考虑设置 ConfigMap 的版本控制或使用 ConfigMap 模板化管理，避免未来出现类似问题。

---

## 📊 性能统计

├─ 总耗时: 3.6m
├─ 问题定位: 42.4s (20%) ✅
├─ 证据链采集: 85.1s (39%) ✅
├─ 根因分析: 12.7s (6%) ✅
├─ 汇总总结: 76.4s (35%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 8 次
```

📋 诊断追踪

- **核心 Runbook**: pod-config-error
- **参考 Runbook**: pod-config-error
- **工具调用**: 8 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
