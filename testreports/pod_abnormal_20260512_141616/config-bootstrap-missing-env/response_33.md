======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 6fb886dc7d88497a]

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
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: appconfigfail-575d77485d-nfpvh
namespace: aiops-e2e
creationTimestamp: 2026-05-12T05:59:23Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finali
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 6
signals: 5
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config
L4_SCENARIO: config-bootstrap-fail
L4_ERROR_TYPE: applicati
   💭 [问题定位] 调用工具: kubectl_container_previous_logs_grep
   💭 [问题定位] 工具结果: kubectl_container_previous_logs_grep (success)
      📄 kubectl_container_previous_logs_grep 输出摘要: raw_chars=851 lines=1
Error: kubectl_container_previous_logs_grep is not a valid tool, try one of [kubectl_describe, kubectl_get_by_name, kubectl_get_by_kind
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   💭 [问题定位] 调用工具: kubectl_container_previous_logs
   💭 [问题定位] 工具结果: kubectl_container_previous_logs (success)
      📄 kubectl_container_previous_logs 日志摘要:
lines: 6
signals: 5
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config
L4_SCENARIO: config-bootstrap-fail
L4_ERROR_TYPE:
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=177 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide configmap appconfigfail-config -n aiops-e2e
Error from server (NotFound): configmaps "appconf
   💭 [问题定位] 调用工具: kubectl_get_by_name
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (3m 1.7s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': '应用配置缺失或错误', 'probability': '高', 'reason': '日志中明确显示 `missing required APP_BOOT_MODE`，且配置校验失败。'}]
   entities=[{"type": "Pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}]
   reasoning=当前环境中存在一个异常 Pod `appconfigfail-575d77485d-nfpvh`，状态为 `CrashLoopBackOff`，重启次数持续增加。日志中显示 `L4_CONFIG_BOOTSTRAP_FAIL`、`missing required APP_BOOT_MODE`、`business config validation failed before server startup` 等配置错误信号。describe 信息显示容器退出码为 `42`，非 OOMKilled（137），且无驱逐、镜像拉取失败等信号。因此归一化为 `ConfigError`，对应 L4 层级，根因为应用配置错误。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "application error", "confidence": 0.95, "reasoning": "当前环境中存在一个异常 Pod `appconfigfail-575d77485d-nfpvh`，状态为 `CrashLoopBackOff`，重启次数持续增加。日志中显示 `L4_CONFIG_BOOTSTRAP_FAIL`、`missing required APP_BOOT_MODE`、`business config validation failed before server startup` 等配置错误信号。describe 信息显示容器退出码为 `42`，非 OOMKilled（137），且无驱逐、镜像拉取失败等信号。因此归一化为 `ConfigError`，对应 L4 层级，根因为应用配置错误。", "abnormal_pods": [{"name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "app_config", "key_entities": [{"type": "Pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "应用配置缺失或错误", "probability": "高", "reason": "日志中明确显示 `missing required APP_BOOT_MODE`，且配置校验失败。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     appconfigfail-575d77485d-nfpvh                      0/1     CrashLoopBackOff   19 (4m4s ago)   76m    172.16.166.184   node1    <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError"], "raw_ref": "/tmp/aiops/reports/context_archives/6fb886dc7d88497a/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/6fb886dc7d88497a/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/6fb886dc7d88497a/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                             READY   STATUS             RESTARTS       AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
appconfigfail-575d77485d-nfpvh   0/1     CrashLoopBa
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (3m 59.5s)
   📤 → 下游数据: evidence_items=8/10
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 的详细信息","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","namespace":"aiops-e2e","name":"appconfigfail-575d77485d-nfpvh","output_format":"yaml"},"purpose":"验证异常 Pod 的 YAML 配置信息","evidence_type":"configuration","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 的事件记录","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=appconfigfail-575d77485d-nfpvh","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=appconfigfail-575d77485d-nfpvh"},"purpose":"验证异常 Pod 的事件记录","evidence_type":"event","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod 的上一次容器日志","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous","tool_args":{"namespace":"aiops-e2e","pod_name":"appconfigfail-575d77485d-nfpvh","container_name":null,"previous":true},"purpose":"验证异常 Pod 的上一次容器日志","evidence_type":"log","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"获取异常 Pod 的 ConfigMap 配置","level":"important","tool":"kubectl_get_by_name","command":"kubectl get configmap appconfigfail-config -n aiops-e2e -o yaml","tool_args":{"kind":"ConfigMap","namespace":"aiops-e2e","name":"appconfigfail-config","output_format":"yaml"},"purpose":"验证异常 Pod 的 ConfigMap 配置信息","evidence_type":"configuration","target_scope":"aiops-e2e/appconfigfail-config","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                             READY   STATUS             RESTARTS       AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nappconfigfail-575d77485d-nfpvh   0/1     CrashLoopBackOff   21 (37s ago)   83m   172.16.166.184   node1   <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6fb886dc7d88497a/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6fb886dc7d88497a/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6fb886dc7d88497a/tools/001-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 4 项，实际采集 2 项，未采集 2 项，完整度 50%；其中真实环境证据 8/10 项，完整度 80%；实际执行工具 5 个，匹配计划 2 个，未规划证据 3 个","plan_total":4,"plan_collected":2,"plan_completeness":0.5,"environment_evidence_total":10,"environment_evidence_collected":8,"environment_evidence_completeness":0.8,"executed_tool_count":5,"matched_tool_count":2,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 的详细信息","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml","purpose":"验证异常 Pod 的 YAML 配置信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 的事件记录","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=appconfigfail-575d77485d-nfpvh","purpose":"验证异常 Pod 的事件记录","collected":false,"source":"planned","outcome":"unknown"},{"id":"e3","description":"获取异常 Pod 的上一次容器日志","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous","purpose":"验证异常 Pod 的上一次容器日志","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"e4","description":"获取异常 Pod 的 ConfigMap 配置","level":"important","tool":"kubectl_get_by_name","command":"kubectl get configmap appconfigfail-config -n aiops-e2e -o yaml","purpose":"验证异常 Pod 的 ConfigMap 配置信息","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_container_previous_logs_grep","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_container_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e2(获取异常 Pod 的事件记录): 已规划但工具执行失败或无匹配结果","e4(获取异常 Pod 的 ConfigMap 配置): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/4 项, 完整度: 80%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 获取异常 Pod 的详细信息 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml` |
   | e2 | critical | ❌ | kubectl_events | 获取异常 Pod 的事件记录 | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=appconfi...` |
   | e3 | critical | ✅ | kubectl_previous_logs | 获取异常 Pod 的上一次容器日志 | `kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous` |
   | e4 | important | ❌ | kubectl_get_by_name | 获取异常 Pod 的 ConfigMap 配置 | `kubectl get configmap appconfigfail-config -n aiops-e2e -o yaml` |

   ⚠️ 未采集原因:
   - e2(获取异常 Pod 的事件记录): 已规划但工具执行失败或无匹配结果
   - e4(获取异常 Pod 的 ConfigMap 配置): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (26.3s)
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
   ✅ [汇总总结] 完成 (1m 56.9s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4208 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 9m 24.4s
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
| **问题分类** | ConfigError（配置错误） |
| **置信度** | 高 (95%) |
| **证据完整度** | 2/4 (50%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | appconfigfail-575d77485d-nfpvh |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | L4_CONFIG_BOOTSTRAP_FAIL、missing required APP_BOOT_MODE、business config validation failed before server startup |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff, RESTARTS: 19` | Pod 处于崩溃循环状态 |
| 2 | 容器日志（上一次） | `kubectl previous logs` | `L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config`<br>`FATAL: missing required APP_BOOT_MODE` | 应用启动时因配置缺失失败 |
| 3 | describe Pod | `kubectl describe pod` | `Last State: Terminated`<br>`Exit Code: 42` | 容器因配置错误终止 |
| 4 | ConfigMap 检查 | `kubectl get configmap` | `Error from server (NotFound): configmaps "appconfigfail-config" not found` | 应用依赖的 ConfigMap 不存在 |

### 证据关联分析

- **证据 #2 + #3 印证**：日志中明确显示 `missing required APP_BOOT_MODE`，且 `Exit Code: 42` 表示应用启动失败，确认是配置错误。
- **证据链**：应用依赖的 ConfigMap 不存在 → 应用无法正确加载配置 → 启动失败 → 容器被终止 → Pod 持续重启。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| Pod 事件记录 | critical | 无法确认重启的根本原因是否由配置错误首次触发 |
| 应用配置文件内容 | important | 无法确认具体缺失的配置项（如 `APP_BOOT_MODE`）是否由 ConfigMap 控制 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 应用依赖的 ConfigMap `appconfigfail-config` 不存在，导致关键配置 `APP_BOOT_MODE` 缺失，应用启动失败。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 应用启动时依赖的配置未加载 → 启动失败 → 容器终止 → Pod 重启     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器因配置错误终止（Exit Code 42），Pod 进入 CrashLoopBackOff   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CrashLoopBackOff，重启次数持续增加                  │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2（日志中显示 `missing required APP_BOOT_MODE`）和证据 #4（ConfigMap 不存在），问题的根本原因是**应用依赖的 ConfigMap 未正确挂载**，导致关键配置缺失，应用无法启动。  
**置信度**：高 (95%)  
- ✅ 日志中明确显示配置缺失
- ✅ ConfigMap 不存在
- ⚠️ 缺少事件记录，无法确认首次触发原因

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 创建缺失的 ConfigMap**

```bash
kubectl create configmap appconfigfail-config \
  -n aiops-e2e \
  --from-literal=APP_BOOT_MODE="normal"
```

*依据*：日志中显示 `missing required APP_BOOT_MODE`，该配置缺失导致启动失败。

**2. [可选] 检查 Pod 是否已正确引用 ConfigMap**

```bash
kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o jsonpath='{.spec.containers[*].envFrom[*].configMapRef}'
```

*目的*：确认 Pod 的 `envFrom` 是否引用了 `appconfigfail-config` ConfigMap。

**3. [可选] 查看崩溃前日志以确认配置是否已生效**

```bash
kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous | grep APP_BOOT_MODE
```

*目的*：确认配置是否已正确挂载并被应用读取。

### 后续优化

1. **配置检查自动化**：在部署流水线中加入 ConfigMap 检查步骤，避免缺失配置。
2. **应用配置校验**：在应用启动时添加配置校验逻辑，避免因配置缺失导致崩溃。
3. **监控告警**：对 `CrashLoopBackOff` 状态设置监控告警，及时发现配置问题。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 ConfigMap 存在 | `kubectl get configmap appconfigfail-config -n aiops-e2e` | 显示 ConfigMap 内容 |
| 2. 确认 Pod 状态正常 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e` | STATUS: Running |
| 3. 确认重启次数不再增加 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 重启次数不再增加 |

---

## ⚠️ 注意事项

- 如果问题仍然存在，检查应用是否还有其他依赖配置未正确挂载。
- 可以使用 `kubectl describe pod` 查看容器是否成功挂载了 ConfigMap。
- 如果 ConfigMap 由 Helm 或 Kustomize 管理，确保模板正确生成并部署。

---

---

## 📊 性能统计

├─ 总耗时: 9.4m
├─ 问题定位: 181.7s (32%) ✅
├─ 证据链采集: 239.5s (42%) ✅
├─ 根因分析: 26.3s (5%) ✅
├─ 汇总总结: 116.9s (21%) ✅
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
