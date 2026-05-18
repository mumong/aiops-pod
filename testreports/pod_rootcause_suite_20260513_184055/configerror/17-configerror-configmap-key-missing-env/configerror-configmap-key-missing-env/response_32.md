======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: e0a498337cd54745]

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
      📄 NAME                              READY   STATUS                       RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-config-configmap-key-missing   0/1     Cre
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
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-configmap-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
                  cni.projectcalico.org/containerID: c6590992f796724e303037
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=179 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide configmap configmap-key-missing -n aiops-e2e
Error from server (NotFound): configmaps "config
   💭 [问题定位] 调用工具: kubectl_get_by_name
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (37.7s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'ConfigMap 缺失', 'probability': '高', 'reason': 'Pod 引用了不存在的 ConfigMap，导致容器启动失败。'}, {'scenario': '环境变量配置错误', 'probability': '中', 'reason': 'Pod 配置的环境变量可能引用了不存在的 ConfigMap 键。'}]
   entities=[{"type": "Pod", "name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "configmap-key-missing", "namespace": "aiops-e2e"}]
   reasoning=当前环境中的活跃异常对象为 Pod 'rc-config-configmap-key-missing'，其状态为 'CreateContainerConfigError'，归类为 ConfigError。根据分析，该异常属于 L4 层级，即应用配置错误。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "", "confidence": 0.5, "reasoning": "当前环境中的活跃异常对象为 Pod 'rc-config-configmap-key-missing'，其状态为 'CreateContainerConfigError'，归类为 ConfigError。根据分析，该异常属于 L4 层级，即应用配置错误。", "abnormal_pods": [{"name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}], "pod_status_keyword": "CreateContainerConfigError", "pod_abnormal_type": "ConfigError", "status_category": "app_config", "key_entities": [{"type": "Pod", "name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "configmap-key-missing", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "ConfigMap 缺失", "probability": "高", "reason": "Pod 引用了不存在的 ConfigMap，导致容器启动失败。"}, {"scenario": "环境变量配置错误", "probability": "中", "reason": "Pod 配置的环境变量可能引用了不存在的 ConfigMap 键。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-configmap-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-configmap-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-configmap-key-missing                     0/1     CreateContainerConfigError   0             62m     172.16.166.190   node1    <none>           <none>            app=rc-config-configmap-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/e0a498337cd54745/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/e0a498337cd54745/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/e0a498337cd54745/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 50%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=179 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide configmap configmap-key-missing -n aiops-e2e
Error from server (NotFound): configmaps "config
   💭 [证据链采集] 已采集证据：
- `kubectl_get_by_name`：ConfigMap `configmap-key-missing` 在命名空间 `aiops-e2e` 中不存在，导致容器启动失败。这是冲突证据，表明 Pod 引用了缺失的 ConfigMap。

结论：当前异常 Pod `rc-config-configmap-key-missing` 的异常状态 `CreateContainerConfigError` 是由于引用了不存在的 ConfigMap `configmap-key-missing` 所致。
   ✅ [证据链采集] 完成 (37.8s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 ConfigMap 是否存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap configmap-key-missing -n aiops-e2e","tool_args":{"kind":"ConfigMap","name":"configmap-key-missing","namespace":"aiops-e2e"},"purpose":"确认 ConfigMap 是否存在","evidence_type":"negative","target_scope":"aiops-e2e","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=179 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide configmap configmap-key-missing -n aiops-e2e\nError from server (NotFound): configmaps \"configmap-key-missing\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/e0a498337cd54745/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e0a498337cd54745/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e0a498337cd54745/tools/001-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"已采集证据：\n- `kubectl_get_by_name`：ConfigMap `configmap-key-missing` 在命名空间 `aiops-e2e` 中不存在，导致容器启动失败。这是冲突证据，表明 Pod 引用了缺失的 ConfigMap。\n\n结论：当前异常 Pod `rc-config-configmap-key-missing` 的异常状态 `CreateContainerConfigError` 是由于引用了不存在的 ConfigMap `configmap-key-missing` 所致。","collection_summary":"计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 6 个，匹配计划 1 个，未规划证据 5 个","plan_total":1,"plan_collected":1,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":1,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"验证 ConfigMap 是否存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap configmap-key-missing -n aiops-e2e","purpose":"确认 ConfigMap 是否存在","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/1 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 验证 ConfigMap 是否存在 | `kubectl get configmap configmap-key-missing -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 27.8s)
   📤 → 下游数据: root_cause=根因是 ConfigMap 'configmap-key-missing' 在命名空间 'aiops-e2e' 中不存在，导致 Pod 'rc-config-configmap-key-missing' 无法启动。
   confidence=90%
   causal_chain={"root_cause": "ConfigMap 'configmap-key-missing' 在命名空间 'aiops-e2e' 中不存在，导致 Pod 'rc-config-configmap-key-missing' 无法启动。", "intermediate_causes": ["Pod 'rc-config-configmap-key-missing' 引用了不存在的 ConfigMap 'configmap-key-missing'。", "引用的 ConfigMap 缺失导致容器启动配置失败。"], "direct_causes": ["容器启动失败，因为无法找到所需的 ConfigMap 数据。"]}
   rca_analysis={"phenomenon": "Pod 'rc-config-configmap-key-missing' 在命名空间 'aiops-e2e' 中处于 'CreateContainerConfigError' 状态，归类为配置错误。", "evidence_inventory": [{"tool": "kubectl_get_by_name", "description": "ConfigMap 'configmap-key-missing' 在命名空间 'aiops-e2e' 中不存在，导致容器启动失败。", "reference": "e0a498337cd54745/tools/007-layer-kubectl_get_by_name.summary.txt"}, {"tool": "kubectl_get_by_kind_in_cluster", "description": "Pod 'rc-config-configmap-key-missing' 处于 'CreateContainerConfigError' 状态。", "reference": "e0a498337cd54745/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt"}], "evidence_analysis": [{"tool": "kubectl_get_by_name", "summary": "ConfigMap 'configmap-key-missing' 不存在，这是导致 Pod 'rc-config-configmap-key-missing' 无法启动的直接原因。", "raw_data": "kubectl_get_by_name 输出摘要: raw_chars=179 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide configmap configmap-key-missing -n aiops-e2e\nError from server (NotFound): configmaps \"configmap-key-missing\" not found"}, {"tool": "kubectl_get_by_kind_in_cluster", "summary": "Pod 'rc-config-configmap-key-missing' 的状态为 'CreateContainerConfigError'，表明容器启动配置存在问题。", "raw_data": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Running': 46}\nNAMESPACE     NAME                                                READY   STATUS                       RESTARTS      AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\n# 异常行\naiops-e2e     rc-config-configmap-key-missing                     0/1     CreateContainerConfigError   0             62m     172.16.166.190   node1    <none>           <none>            app=rc-config-configmap-key-m"}], "causal_chain": {"root_cause": "ConfigMap 'configmap-key-missing' 在命名空间 'aiops-e2e' 中不存在，导致 Pod 'rc-config-configmap-key-missing' 无法启动。", "intermediate_causes": ["Pod 'rc-config-configmap-key-missing' 引用了不存在的 ConfigMap 'configmap-key-missing'。", "引用的 ConfigMap 缺失导致容器启动配置失败。"], "direct_causes": ["容器启动失败，因为无法找到所需的 ConfigMap 数据。"]}, "root_cause": "根因是 ConfigMap 'configmap-key-missing' 在命名空间 'aiops-e2e' 中不存在，导致 Pod 'rc-config-configmap-key-missing' 无法启动。", "root_cause_summary": "根因是 ConfigMap 'configmap-key-missing' 在命名空间 'aiops-e2e' 中不存在，导致 Pod 'rc-config-configmap-key-missing' 无法启动。", "confidence": 0.9, "confidence_reason": "直接证据表明 ConfigMap 不存在，且与 Pod 的 'CreateContainerConfigError' 状态直接相关。", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [], "limitations": "当前分析基于已采集的证据，未进行进一步的验证。", "llm_raw_analysis": "已采集证据：\n- `kubectl_get_by_name`：ConfigMap `configmap-key-missing` 在命名空间 `aiops-e2e` 中不存在，导致容器启动失败。这是冲突证据，表明 Pod 引用了缺失的 ConfigMap。\n\n结论：当前异常 Pod `rc-config-configmap-key-missing` 的异常状态 `CreateContainerConfigError` 是由于引用了不存在的 ConfigMap `configmap-key-missing` 所致。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 根因是 ConfigMap 'configmap-key-missing' 在命名空间 'aiops-e2e' 中不存在，导致 Pod 'rc-config-configmap-key-missing' 无法启动。
   置信度: 90%
   🔗 因果链:
     根本原因: ConfigMap 'configmap-key-missing' 在命名空间 'aiops-e2e' 中不存在，导致 Pod 'rc-config-configmap-key-missing' 无法启动。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 19.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4567 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 3.2s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | `CreateContainerConfigError` |
| **兼容归因层** | `L4` - 应用配置错误 |
| **问题分类** | `ConfigError`（配置错误） |
| **置信度** | 高 (90%) |
| **证据完整度** | 1/1 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `rc-config-configmap-key-missing` |
| Namespace | `aiops-e2e` |
| Node | `node1` |
| 错误信息 | `CreateContainerConfigError` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CreateContainerConfigError` | Pod 启动失败，原因是容器配置错误 |
| 2 | Pod 描述 | `kubectl describe pod` | `Reason: CreateContainerConfigError` | 容器启动失败，原因未被详细记录 |
| 3 | 日志尝试 | `kubectl logs` | `Error from server (BadRequest): container "app" in pod "rc-config-configmap-key-missing" is waiting to start: CreateContainerConfigError` | 无法获取日志，容器尚未启动 |
| 4 | 历史日志尝试 | `kubectl logs --previous` | `Error from server (BadRequest): previous terminated container "app" in pod "rc-config-configmap-key-missing" not found` | 无历史日志，容器从未成功启动 |
| 5 | ConfigMap 验证 | `kubectl get configmap` | `Error from server (NotFound): configmaps "configmap-key-missing" not found` | Pod 依赖的 ConfigMap 不存在 |
| 6 | Runbook 匹配 | `fetch_runbook` | `典型状态: CreateContainerConfigError / CreateContainerError / CrashLoopBackOff` | 匹配 `pod-config-error.md` Runbook |
| 7 | Pod 配置摘要 | `kubectl get pod` | `app=rc-config-configmap-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true` | 明确标记为配置错误 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 `CreateContainerConfigError`，且 `kubectl describe` 显示 `Reason: CreateContainerConfigError`，说明容器在启动阶段因配置问题失败。
- **证据 #5 印证**：Pod 依赖的 ConfigMap `configmap-key-missing` 不存在，是容器无法启动的根本原因。
- **证据 #6 印证**：匹配 Runbook `pod-config-error.md`，说明该问题属于典型的配置类错误。
- **证据链**：Pod 指向不存在的 ConfigMap → 容器启动失败 → Pod 状态为 `CreateContainerConfigError`。

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ ConfigMap 'configmap-key-missing' 在命名空间 'aiops-e2e' 中不存在，导致 Pod 'rc-config-configmap-key-missing' 无法启动。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Pod 启动时引用了缺失的 ConfigMap，导致容器无法构建配置环境。      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器启动失败，状态为 `CreateContainerConfigError`。              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 `CreateContainerConfigError`，无法正常启动。          │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #5（`kubectl get configmap` 返回 `NotFound`）和证据 #1（Pod 状态为 `CreateContainerConfigError`），问题的根本原因是 **Pod 依赖的 ConfigMap `configmap-key-missing` 在命名空间 `aiops-e2e` 中不存在**，导致容器无法构建配置环境，从而失败启动。

**置信度**：高 (90%)
- ✅ `kubectl get configmap` 明确返回 `NotFound`
- ✅ Pod 状态为 `CreateContainerConfigError`
- ✅ Runbook 匹配 `pod-config-error.md`
- ⚠️ 无容器日志，无法进一步确认配置错误的具体内容

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 创建缺失的 ConfigMap**

```bash
kubectl create configmap configmap-key-missing -n aiops-e2e --from-literal=key1=value1 --from-literal=key2=value2
```

*依据*：Pod 依赖的 ConfigMap 不存在，需手动创建以恢复容器启动。

**2. [可选] 验证 ConfigMap 是否已创建**

```bash
kubectl get configmap configmap-key-missing -n aiops-e2e -o yaml
```

*目的*：确认 ConfigMap 已正确创建并可被 Pod 使用。

**3. [可选] 重启 Pod**

```bash
kubectl delete pod rc-config-configmap-key-missing -n aiops-e2e
```

*目的*：删除失败的 Pod，触发重新调度并使用新的 ConfigMap。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 ConfigMap 存在 | `kubectl get configmap configmap-key-missing -n aiops-e2e` | 应显示 ConfigMap 详情 |
| 2. 确认 Pod 运行 | `kubectl get pod rc-config-configmap-key-missing -n aiops-e2e` | STATUS: Running |
| 3. 检查容器状态 | `kubectl describe pod rc-config-configmap-key-missing -n aiops-e2e` | Reason: PodScheduled, ContainerStatus: Running |

---

## ⚠️ 注意事项

- 如果 ConfigMap 已经存在，但仍然报错，请检查 Pod 的配置是否正确引用了 ConfigMap 的键。
- 如果问题仍然存在，建议查看 Pod 的 YAML 配置，确认 `envFrom`、`volume` 或其他字段是否正确指向 ConfigMap。
- 如果 ConfigMap 包含敏感信息，建议使用 `Secret` 替代。

---

## 📊 性能统计

├─ 总耗时: 4.1m
├─ 问题定位: 37.7s (16%) ✅
├─ 证据链采集: 37.8s (16%) ✅
├─ 根因分析: 87.8s (36%) ✅
├─ 汇总总结: 79.8s (33%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 9 次
```

📋 诊断追踪

- **核心 Runbook**: pod-config-error
- **参考 Runbook**: pod-config-error
- **工具调用**: 9 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
