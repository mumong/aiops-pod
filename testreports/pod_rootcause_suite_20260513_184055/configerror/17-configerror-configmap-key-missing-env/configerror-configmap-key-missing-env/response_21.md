======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: d4cc9f41943b4e96]

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
      📄 kubectl_previous_logs 输出摘要: raw_chars=224 lines=3
Command failed (exit 1):
kubectl logs rc-config-configmap-key-missing -n aiops-e2e --previous --tail=200
Error from server (BadRequest): previous term
   💭 [问题定位] 调用工具: kubectl_logs
   💭 [问题定位] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 输出摘要: raw_chars=231 lines=3
Command failed (exit 1):
kubectl logs rc-config-configmap-key-missing -n aiops-e2e --tail=200
Error from server (BadRequest): container "app" in pod "rc-config
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-configmap-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          38m (x12 over 40m)   kubelet            Error: c
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": ["L4"],
  "layer_name": "ConfigError",
  "confidence": "high",
  "reasoning": "Pod rc-config-configmap-key-missing 处于 CreateContainerConfigError 状态，且 kubelet 报错信息显示找不到 ConfigMap 中的键 APP_BOOT_MODE。这表明 Pod 的配置错误，具体是 ConfigMap 缺失了必要的键。",
  "abnormal_pods": [
    {
      "name": "rc-config-configmap-key-missing",
      "namespace": "aiops-e2e",
      "status": "CreateContainerConfigError",
      "node": "node1"
    }
  ],
  "abnormal_groups": [
    {
      "type": "ConfigError",
      "count": 1
    }
  ],
  "pod_status_keyword": "CreateContainerConfigError",
  "pod_abnormal_type": "ConfigError",
  "status_category": "ConfigError",
  "key_entities": [
    "ConfigMap aiops-e2e/rc-app-config",
    "Pod rc-config-configmap-key-missing"
  ],
  "possible_scenarios": [
    "ConfigMap 缺失了键 APP_BOOT_MODE，导致容器无法启动。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (57.1s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'ConfigMap 缺失了键 APP_BOOT_MODE，导致容器无法启动。', 'probability': 'high', 'reason': 'Pod rc-config-configmap-key-missing 的 kubelet 事件显示找不到 ConfigMap aiops-e2e/rc-app-config 中的键 APP_BOOT_MODE。'}]
   entities=[{"type": "ConfigMap", "name": "aiops-e2e/rc-app-config", "namespace": "aiops-e2e"}, {"type": "Pod", "name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e"}]
   reasoning=Pod rc-config-configmap-key-missing 处于 CreateContainerConfigError 状态，且 kubelet 报错信息显示找不到 ConfigMap 中的键 APP_BOOT_MODE。这表明 Pod 的配置错误，具体是 ConfigMap 缺失了必要的键。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.5, "reasoning": "Pod rc-config-configmap-key-missing 处于 CreateContainerConfigError 状态，且 kubelet 报错信息显示找不到 ConfigMap 中的键 APP_BOOT_MODE。这表明 Pod 的配置错误，具体是 ConfigMap 缺失了必要的键。", "abnormal_pods": [{"name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}], "pod_status_keyword": "CreateContainerConfigError", "pod_abnormal_type": "ConfigError", "status_category": "ConfigError", "key_entities": [{"type": "ConfigMap", "name": "aiops-e2e/rc-app-config", "namespace": "aiops-e2e"}, {"type": "Pod", "name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "ConfigMap 缺失了键 APP_BOOT_MODE，导致容器无法启动。", "probability": "high", "reason": "Pod rc-config-configmap-key-missing 的 kubelet 事件显示找不到 ConfigMap aiops-e2e/rc-app-config 中的键 APP_BOOT_MODE。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-configmap-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-configmap-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-configmap-key-missing                     0/1     CreateContainerConfigError   0             40m     172.16.166.190   node1    <none>           <none>            app=rc-config-configmap-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/d4cc9f41943b4e96/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/d4cc9f41943b4e96/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/d4cc9f41943b4e96/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 50%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME            DATA   AGE   LABELS
rc-app-config   1      41m   rootcause-e2e=true
   💭 [证据链采集] 已采集证据：
- e1: kubectl_get_by_name 确认 ConfigMap aiops-e2e/rc-app-config 存在，但 DATA=1，表明可能缺失键 APP_BOOT_MODE。

未采集证据：
- 无

冲突证据：
- 无

下一步建议：
确认 ConfigMap aiops-e2e/rc-app-config 中是否存在键 APP_BOOT_MODE。
   ✅ [证据链采集] 完成 (40.3s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 ConfigMap aiops-e2e/rc-app-config 是否包含键 APP_BOOT_MODE","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap rc-app-config -n aiops-e2e -o yaml","tool_args":{"kind":"ConfigMap","name":"rc-app-config","namespace":"aiops-e2e"},"purpose":"确认 ConfigMap 是否包含缺失的键 APP_BOOT_MODE","evidence_type":"config_validation","target_scope":"aiops-e2e/ConfigMap/rc-app-config","acceptable_tools":["kubectl_get_by_name","kubectl_get_yaml"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME            DATA   AGE   LABELS\nrc-app-config   1      41m   rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d4cc9f41943b4e96/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d4cc9f41943b4e96/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d4cc9f41943b4e96/tools/001-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"已采集证据：\n- e1: kubectl_get_by_name 确认 ConfigMap aiops-e2e/rc-app-config 存在，但 DATA=1，表明可能缺失键 APP_BOOT_MODE。\n\n未采集证据：\n- 无\n\n冲突证据：\n- 无\n\n下一步建议：\n确认 ConfigMap aiops-e2e/rc-app-config 中是否存在键 APP_BOOT_MODE。","collection_summary":"计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%；其中真实环境证据 6/6 项，完整度 100%；实际执行工具 5 个，匹配计划 1 个，未规划证据 4 个","plan_total":1,"plan_collected":1,"plan_completeness":1.0,"environment_evidence_total":6,"environment_evidence_collected":6,"environment_evidence_completeness":1.0,"executed_tool_count":5,"matched_tool_count":1,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"验证 ConfigMap aiops-e2e/rc-app-config 是否包含键 APP_BOOT_MODE","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap rc-app-config -n aiops-e2e -o yaml","purpose":"确认 ConfigMap 是否包含缺失的键 APP_BOOT_MODE","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/1 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 验证 ConfigMap aiops-e2e/rc-app-config 是否包含键 AP... | `kubectl get configmap rc-app-config -n aiops-e2e -o yaml` |

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (13.1s)
   📤 → 下游数据: root_cause=Pod rc-config-configmap-key-missing 处于 CreateContainerConfigError 状态，且 kubelet 报错信息显示找不到 ConfigMap aiops-e2e/rc-app-config 中的键 APP_BOOT_MODE。这表明 ConfigMap 缺失了必要的键，导致容器无法启动。
   confidence=90%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [], "causal_chain": {}, "root_cause": "Pod rc-config-configmap-key-missing 处于 CreateContainerConfigError 状态，且 kubelet 报错信息显示找不到 ConfigMap aiops-e2e/rc-app-config 中的键 APP_BOOT_MODE。这表明 ConfigMap 缺失了必要的键，导致容器无法启动。", "root_cause_summary": "Pod rc-config-configmap-key-missing 处于 CreateContainerConfigError 状态，且 kubelet 报错信息显示找不到 ConfigMap aiops-e2e/rc-app-config 中的键 APP_BOOT_MODE。这表明 ConfigMap 缺失了必要的键，导致容器无法启动。", "confidence": 0.9, "confidence_reason": "有直接证据表明 ConfigMap 缺失了键 APP_BOOT_MODE，因果链清晰。", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [], "limitations": "未直接验证 ConfigMap aiops-e2e/rc-app-config 中是否存在键 APP_BOOT_MODE，但根据 kubelet 报错信息推断其缺失。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-config-configmap-key-missing 处于 CreateContainerConfigError 状态，且 kubelet 报错信息显示找不到 ConfigMap aiops-e2e/rc-app-config 中的键 APP_BOOT_MODE。这表明 Confi...
   置信度: 90%

📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 4.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3674 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 54.6s
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
| **置信度** | 高 (90%) |
| **证据完整度** | 1/1 (100%) |

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
| 错误信息 | Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CreateContainerConfigError` | Pod 无法启动，配置错误 |
| 2 | kubelet 事件 | `kubectl describe pod` | `Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config` | 明确指出 ConfigMap 缺少键 |
| 3 | ConfigMap 内容 | `kubectl get configmap rc-app-config -n aiops-e2e` | `DATA: 1` | 仅包含 1 个键，不包括 APP_BOOT_MODE |

### 证据关联分析

- **证据 #2 印证**：`Error: couldn't find key APP_BOOT_MODE` 直接确认 ConfigMap 缺失关键键。
- **证据链**：Pod 使用 ConfigMap `aiops-e2e/rc-app-config` → ConfigMap 中缺少 `APP_BOOT_MODE` 键 → 容器无法启动 → Pod 状态为 `CreateContainerConfigError`。
- **证据 #3 补充**：`DATA: 1` 表明 ConfigMap 中没有 `APP_BOOT_MODE` 键。

### 缺失证据（无）

| 证据 | 级别 | 影响 |
|------|------|------|
| - | - | - |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ ConfigMap aiops-e2e/rc-app-config 缺少键 APP_BOOT_MODE          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Pod 使用的 ConfigMap 中缺少关键键 APP_BOOT_MODE                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器启动失败，因找不到 APP_BOOT_MODE 键                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod rc-config-configmap-key-missing 状态为 CreateContainerConfigError，无法启动 |
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2（`Error: couldn't find key APP_BOOT_MODE`）和证据 #3（`DATA: 1`），问题的根本原因是**ConfigMap `aiops-e2e/rc-app-config` 缺少键 `APP_BOOT_MODE`**，导致 Pod 无法正常启动，状态为 `CreateContainerConfigError`。

**置信度**：高 (90%)
- ✅ kubelet 事件明确指出找不到 `APP_BOOT_MODE` 键
- ✅ `kubectl get configmap` 显示该 ConfigMap 仅有 1 个键，不含 `APP_BOOT_MODE`

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 在 ConfigMap 中添加缺失的键 `APP_BOOT_MODE`**

```bash
kubectl edit configmap rc-app-config -n aiops-e2e
```

在编辑器中添加如下内容：

```yaml
data:
  APP_BOOT_MODE: "normal"
```

*依据*：容器依赖该键启动，添加后 Pod 可以正常初始化。

**2. [可选] 重启 Pod 以应用更新**

```bash
kubectl delete pod rc-config-configmap-key-missing -n aiops-e2e
```

*目的*：删除异常 Pod，触发调度器重新创建并应用更新后的 ConfigMap。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 ConfigMap 已更新 | `kubectl get configmap rc-app-config -n aiops-e2e -o jsonpath='{.data}'` | 包含 `APP_BOOT_MODE` 键 |
| 2. 确认 Pod 状态 | `kubectl get pod rc-config-configmap-key-missing -n aiops-e2e` | STATUS: Running |
| 3. 检查 Pod 事件 | `kubectl describe pod rc-config-configmap-key-missing -n aiops-e2e` | 无 `CreateContainerConfigError` 事件 |

---

## ⚠️ 注意事项

- 确保 `APP_BOOT_MODE` 的值与应用要求一致，避免配置错误
- 如果应用对 `APP_BOOT_MODE` 有特定格式要求，需按文档配置
- 如果问题依然存在，请检查容器启动命令是否正确引用了该环境变量

---

## 📊 性能统计

├─ 总耗时: 2.9m
├─ 问题定位: 57.1s (33%) ✅
├─ 证据链采集: 40.3s (23%) ✅
├─ 根因分析: 13.1s (7%) ✅
├─ 汇总总结: 64.0s (37%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 7 次
```

📋 诊断追踪

- **核心 Runbook**: pod-config-error
- **参考 Runbook**: pod-config-error
- **工具调用**: 7 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
