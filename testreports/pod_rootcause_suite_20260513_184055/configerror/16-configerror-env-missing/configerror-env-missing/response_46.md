======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 0d81bdb5e1dc4e99]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'CrashLoopBackOff': 1, 'Running': 46}
NAMESPACE     NAME                                                READY   STATUS           
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
name: rc-config-env-missing-5d9b8b766c-cstkh
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Reason:       CrashLoopBackOff
  Warning  BackOff  2m39s (x582
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                     READY   STATUS             RESTARTS         AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-config-env-missing-5d9b8b766c-cstkh   
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-config-env-missing-5d9b8b766c-cstkh
namespace: aiops-e2e
creationTimestamp: 2026-05-14T22:19:01Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: Non
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "ConfigError",
  "confidence": 0.95,
  "reasoning": "Pod rc-config-env-missing-5d9b8b766c-cstkh 在 aiops-e2e 命名空间中处于 CrashLoopBackOff 状态，且其上一次崩溃日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE。describe 显示 Exit Code 为 42，无 OOMKilled 或镜像拉取失败的迹象，符合 ConfigError 的典型特征。Pod 的标签中已标注 pod_abnormal_type=ConfigError。",
  "abnormal_pods": [
    {
      "namespace": "aiops-e2e",
      "name": "rc-config-env-missing-5d9b8b766c-cstkh",
      "status": "CrashLoopBackOff",
      "reason": "Error",
      "exit_code": 42
    }
  ],
  "abnormal_groups": [
    "CrashLoopBackOff"
  ],
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "ConfigError",
  "status_category": "CrashLoopBackOff",
  "key_entities": [
    "rc-config-env-missing-5d9b8b766c-cstkh",
    "aiops-e2e",
    "APP_BOOT_MODE",
    "ConfigError"
  ],
  "possible_scenarios": [
    "环境变量 APP_BOOT_MODE 缺失导致容器启动失败",
    "ConfigMap 或 Secret 配置缺失或拼写错误",
    "容器启动脚本或配置校验失败"
  ]
}
   ✅ [问题定位] 完成 (59.1s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[]
   entities=[]
   reasoning=Pod rc-config-env-missing-5d9b8b766c-cstkh 在 aiops-e2e 命名空间中处于 CrashLoopBackOff 状态，且其上一次崩溃日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE。describe 显示 Exit Code 为 42，无 OOMKilled 或镜像拉取失败的迹象，符合 ConfigError 的典型特征。Pod 的标签中已标注 pod_abnormal_type=ConfigError。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.95, "reasoning": "Pod rc-config-env-missing-5d9b8b766c-cstkh 在 aiops-e2e 命名空间中处于 CrashLoopBackOff 状态，且其上一次崩溃日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE。describe 显示 Exit Code 为 42，无 OOMKilled 或镜像拉取失败的迹象，符合 ConfigError 的典型特征。Pod 的标签中已标注 pod_abnormal_type=ConfigError。", "abnormal_pods": [{"name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "app_config", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-cstkh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-cstkh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-env-missing-5d9b8b766c-cstkh              0/1     CrashLoopBackOff   29 (4m16s ago)   127m    172.16.166.152   node1    <none>           <none>            app=rc-config-env-missing,pod-template-hash=5d9b8b766c,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/0d81bdb5e1dc4e99/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/0d81bdb5e1dc4e99/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/0d81bdb5e1dc4e99/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 95%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (53.3s)
   📤 → 下游数据: evidence_items=5/6
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证异常 Pod rc-config-env-missing-5d9b8b766c-cstkh 的详细事件记录，确认其 CrashLoopBackOff 的根本原因","level":"critical","tool":"kubectl_events","command":"kubectl get events --namespace=aiops-e2e --field-selector=involvedObject.name=rc-config-env-missing-5d9b8b766c-cstkh","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-config-env-missing-5d9b8b766c-cstkh"},"purpose":"确认异常 Pod 的关键事件信息，尤其是导致 CrashLoopBackOff 的原因","evidence_type":"event","target_scope":"aiops-e2e/rc-config-env-missing-5d9b8b766c-cstkh","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 1 项，实际采集 0 项，未采集 1 项，完整度 0%；其中真实环境证据 5/6 项，完整度 83%；实际执行工具 5 个，匹配计划 0 个，未规划证据 5 个","plan_total":1,"plan_collected":0,"plan_completeness":0.0,"environment_evidence_total":6,"environment_evidence_collected":5,"environment_evidence_completeness":0.8333333333333334,"executed_tool_count":5,"matched_tool_count":0,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"验证异常 Pod rc-config-env-missing-5d9b8b766c-cstkh 的详细事件记录，确认其 CrashLoopBackOff 的根本原因","level":"critical","tool":"kubectl_events","command":"kubectl get events --namespace=aiops-e2e --field-selector=involvedObject.name=rc-config-env-missing-5d9b8b766c-cstkh","purpose":"确认异常 Pod 的关键事件信息，尤其是导致 CrashLoopBackOff 的原因","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":["e1(验证异常 Pod rc-config-env-missing-5d9b8b766c-cstkh 的详细事件记录，确认其 CrashLoopBackOff 的根本原因): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 0/1 项, 完整度: 83%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ❌ | kubectl_events | 验证异常 Pod rc-config-env-missing-5d9b8b766c-cst... | `kubectl get events --namespace=aiops-e2e --field-selector=involvedObject.name...` |

   ⚠️ 未采集原因:
   - e1(验证异常 Pod rc-config-env-missing-5d9b8b766c-cstkh 的详细事件记录，确认其 CrashLoopBackOff 的根本原因): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (8.4s)
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
   ✅ [汇总总结] 完成 (1m 8.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3923 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 9.4s
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
| **Pod异常状态** | CrashLoopBackOff |
| **兼容归因层** | L4 |
| **问题分类** | ConfigError |
| **置信度** | 高 (95%) |
| **证据完整度** | 0/1 (0%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | rc-config-env-missing-5d9b8b766c-cstkh |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | kubectl get pod | `STATUS: CrashLoopBackOff` | Pod 正在持续重启 |
| 2 | describe 信息 | kubectl describe pod | `Reason: CrashLoopBackOff` | Pod 启动失败，进入 CrashLoopBackOff 状态 |
| 3 | 崩溃前日志 | kubectl logs --previous | `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE` | 配置缺失导致启动失败 |
| 4 | Pod YAML 配置 | kubectl get pod -o yaml | `labels: app=rc-config-env-missing, pod_abnormal_type=ConfigError` | Pod 明确标注配置错误 |
| 5 | Runbook 匹配 | fetch_runbook | `ConfigError | 典型状态: CrashLoopBackOff` | 与已知配置错误场景匹配 |

### 证据关联分析

- **证据 #1 + #2 + #3 印证**：Pod 状态为 `CrashLoopBackOff`，崩溃前日志显示 `APP_BOOT_MODE` 缺失 → 明确为配置错误。
- **证据链**：`APP_BOOT_MODE` 未定义 → 应用启动失败 → 容器崩溃 → Pod 重启 → 持续循环。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| Pod 事件详情 | critical | 无法确认是否还有其他配置错误或环境问题 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 缺少环境变量 `APP_BOOT_MODE`，导致应用启动失败                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 应用启动依赖 `APP_BOOT_MODE` 配置，缺失时直接退出               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器因配置缺失退出（Exit Code 42）                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 CrashLoopBackOff，持续重启                             │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #3 (`L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`) 和证据 #4 (`pod_abnormal_type=ConfigError`)，
问题的根本原因是 **容器缺少关键环境变量 `APP_BOOT_MODE`**，导致应用启动失败并持续重启。

**置信度**：高 (95%)
- ✅ 崩溃前日志明确指出配置缺失
- ✅ Pod 标签中明确标注 `ConfigError`
- ⚠️ 缺少事件详情，无法确认是否还有其他配置问题

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 补全环境变量 `APP_BOOT_MODE`**
```bash
kubectl set env deployment/<deployment_name> -n aiops-e2e APP_BOOT_MODE=<correct_value>
```
*依据*：崩溃日志提示缺失 `APP_BOOT_MODE`，需补充该值

**2. [可选] 通过 ConfigMap/Secret 补充环境变量**
```bash
kubectl create configmap app-config -n aiops-e2e --from-literal=APP_BOOT_MODE=<correct_value>
```
```yaml
# 在 Deployment 中引用
- name: APP_BOOT_MODE
  valueFrom:
    configMapKeyRef:
      name: app-config
      key: APP_BOOT_MODE
```

### 后续优化

1. **配置校验机制**：在部署流水线中加入配置校验步骤，确保关键环境变量存在
2. **默认值机制**：为关键配置项提供合理的默认值，避免缺失导致崩溃
3. **日志记录增强**：在应用启动时记录完整配置信息，便于快速定位缺失项

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 0 |
| 3. 查看日志 | `kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` | 无 L4_CONFIG_BOOTSTRAP_FAIL 错误 |

---

## ⚠️ 注意事项

- 如果环境变量补全后问题仍然存在，建议检查是否存在其他配置缺失或依赖问题
- 建议在部署流水线中加入配置检查，防止类似问题重复出现
- 若该 Pod 是由 Deployment 管理，建议检查 Deployment 中的 `env` 配置是否完整

---

---

## 📊 性能统计

├─ 总耗时: 3.2m
├─ 问题定位: 59.1s (31%) ✅
├─ 证据链采集: 53.3s (28%) ✅
├─ 根因分析: 8.4s (4%) ✅
├─ 汇总总结: 68.7s (36%) ✅
├─ LLM 调用: 5 次
└─ 工具调用: 8 次
```

📋 诊断追踪

- **核心 Runbook**: pod-config-error
- **参考 Runbook**: pod-config-error
- **工具调用**: 8 次
- **LLM 调用**: 5 次


======================================================================
✅ 诊断完成!
======================================================================
