======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 783e6afa0a374c05]

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
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                     READY   STATUS             RESTARTS         AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-config-env-missing-5d9b8b766c-cstkh   
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
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "ConfigError",
  "confidence": 0.95,
  "reasoning": "Pod 'rc-config-env-missing-5d9b8b766c-cstkh' 处于 CrashLoopBackOff 状态，日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE。这表明配置错误导致容器启动失败，属于 ConfigError 异常类型。",
  "abnormal_pods": [
    "rc-config-env-missing-5d9b8b766c-cstkh"
  ],
  "abnormal_groups": {
    "ConfigError": 1
  },
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "ConfigError",
  "status_category": "CrashLoopBackOff",
  "key_entities": [
    "rc-config-env-missing-5d9b8b766c-cstkh",
    "APP_BOOT_MODE",
    "ConfigError"
  ],
  "possible_scenarios": [
    "缺失环境变量 APP_BOOT_MODE 导致容器启动失败",
    "ConfigMap 或 Secret 引用错误导致配置加载失败",
    "应用配置校验失败，导致启动失败"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (49.9s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': '缺失环境变量 APP_BOOT_MODE 导致容器启动失败', 'probability': 'high', 'reason': "日志中明确提示 'L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE'。"}, {'scenario': 'ConfigMap 或 Secret 引用错误导致配置加载失败', 'probability': 'medium', 'reason': 'Pod 的 env 或 envFrom 可能引用了错误的 ConfigMap 或 Secret。'}, {'scenario': '应用配置校验失败，导致启动失败', 'probability': 'medium', 'reason': 'Pod 启动后，应用校验配置失败，导致容器崩溃。'}]
   entities=[{"type": "Pod", "name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e"}, {"type": "ConfigError", "name": "APP_BOOT_MODE", "namespace": "aiops-e2e"}]
   reasoning=Pod 'rc-config-env-missing-5d9b8b766c-cstkh' 处于 CrashLoopBackOff 状态，日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE。这表明配置错误导致容器启动失败，属于 ConfigError 异常类型。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.95, "reasoning": "Pod 'rc-config-env-missing-5d9b8b766c-cstkh' 处于 CrashLoopBackOff 状态，日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE。这表明配置错误导致容器启动失败，属于 ConfigError 异常类型。", "abnormal_pods": [{"name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "CrashLoopBackOff", "key_entities": [{"type": "Pod", "name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e"}, {"type": "ConfigError", "name": "APP_BOOT_MODE", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "缺失环境变量 APP_BOOT_MODE 导致容器启动失败", "probability": "high", "reason": "日志中明确提示 'L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE'。"}, {"scenario": "ConfigMap 或 Secret 引用错误导致配置加载失败", "probability": "medium", "reason": "Pod 的 env 或 envFrom 可能引用了错误的 ConfigMap 或 Secret。"}, {"scenario": "应用配置校验失败，导致启动失败", "probability": "medium", "reason": "Pod 启动后，应用校验配置失败，导致容器崩溃。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-cstkh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-cstkh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-env-missing-5d9b8b766c-cstkh              0/1     CrashLoopBackOff   26 (2m8s ago)   110m    172.16.166.152   node1    <none>           <none>            app=rc-config-env-missing,pod-template-hash=5d9b8b766c,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/783e6afa0a374c05/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/783e6afa0a374c05/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/783e6afa0a374c05/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 95%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-env-missing-5d9b8b766c-cstkh
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Reason:       CrashLoopBackOff
  Warning  BackOff  85s (x512 o
   💭 [证据链采集] 已采集证据：
1. **Pod 事件**：`kubectl describe` 显示 Pod 处于 `CrashLoopBackOff` 状态，事件 `BackOff` 显示容器 `app` 启动失败，错误原因为 `Error`，Exit Code 为 42。
2. **Exit Code 42**：表明容器启动失败，且不是 OOMKilled（137）或其他常见错误代码，可能为业务配置错误。
3. **日志信号**：`kubectl_previous_logs` 显示日志 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`，进一步确认是配置错误导致容器启动失败。

未采集证据：
- 无

冲突证据：
- 无

结论：Pod `rc-config-env-missing-5d9b8b766c-cstkh` 处于 `CrashLoopBackOff` 状态，Exit Code 为 42，且日志提示 `APP_BOOT_MODE` 配置缺失，符合 `ConfigError` 类型的异常。建议检查 Pod 的 `env` 配置或引用的 ConfigMap/Secret，确认 `APP_BOOT_MODE` 是否定义正确。
   ✅ [证据链采集] 完成 (56.6s)
   📤 → 下游数据: evidence_items=5/5
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 'rc-config-env-missing-5d9b8b766c-cstkh' 的详细描述，检查其配置错误和事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-config-env-missing-5d9b8b766c-cstkh"},"purpose":"验证异常 Pod 的配置错误和事件，确认导致 CrashLoopBackOff 的原因","evidence_type":"configuration","target_scope":"Pod","acceptable_tools":["kubectl_describe","kubectl_events","kubectl_previous_logs"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-env-missing-5d9b8b766c-cstkh\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Reason:       CrashLoopBackOff\n  Warning  BackOff  85s (x512 over 111m)  kubelet  Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-cstkh_aiops-e2e(5ed47e61-9e99-459d-88de-ee30d25b1def)\n                  cni.projectcalico.org/containerID: b609d3199474fd0c991fb51944c653ad8de49c03971407f25be4cb50f1498fc2\n                  cni.projectcalico.org/podIP: 172.16.166.152/32\n                  cni.projectcalico.org/podIPs: 172.16.166.152/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/783e6afa0a374c05/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/783e6afa0a374c05/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/783e6afa0a374c05/tools/001-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"已采集证据：\n1. **Pod 事件**：`kubectl describe` 显示 Pod 处于 `CrashLoopBackOff` 状态，事件 `BackOff` 显示容器 `app` 启动失败，错误原因为 `Error`，Exit Code 为 42。\n2. **Exit Code 42**：表明容器启动失败，且不是 OOMKilled（137）或其他常见错误代码，可能为业务配置错误。\n3. **日志信号**：`kubectl_previous_logs` 显示日志 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`，进一步确认是配置错误导致容器启动失败。\n\n未采集证据：\n- 无\n\n冲突证据：\n- 无\n\n结论：Pod `rc-config-env-missing-5d9b8b766c-cstkh` 处于 `CrashLoopBackOff` 状态，Exit Code 为 42，且日志提示 `APP_BOOT_MODE` 配置缺失，符合 `ConfigError` 类型的异常。建议检查 Pod 的 `env` 配置或引用的 ConfigMap/Secret，确认 `APP_BOOT_MODE` 是否定义正确。","collection_summary":"计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%；其中真实环境证据 5/5 项，完整度 100%；实际执行工具 5 个，匹配计划 1 个，未规划证据 4 个","plan_total":1,"plan_collected":1,"plan_completeness":1.0,"environment_evidence_total":5,"environment_evidence_collected":5,"environment_evidence_completeness":1.0,"executed_tool_count":5,"matched_tool_count":1,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 'rc-config-env-missing-5d9b8b766c-cstkh' 的详细描述，检查其配置错误和事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e","purpose":"验证异常 Pod 的配置错误和事件，确认导致 CrashLoopBackOff 的原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/1 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取异常 Pod 'rc-config-env-missing-5d9b8b766c-cs... | `kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` |

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (7.9s)
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
   ✅ [汇总总结] 完成 (1m 32.9s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4296 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 27.4s
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
| **兼容归因层** | L4 - 应用配置错误 |
| **问题分类** | ConfigError（L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE） |
| **置信度** | 高 (95%) |
| **证据完整度** | 1/1 (100%) |

---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题？

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
| 1 | Pod 状态 | kubectl get pod | `STATUS: CrashLoopBackOff, RESTARTS: 26` | Pod 持续崩溃并重启 |
| 2 | Pod 详细信息 | kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh | `Reason: CrashLoopBackOff` | 容器启动失败，进入崩溃循环 |
| 3 | 日志信息 | kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e --previous | `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE` | 明确提示缺少关键环境变量 |
| 4 | kubectl_get_by_kind_in_cluster | kubectl get pod -n aiops-e2e | `status_counts={'CrashLoopBackOff': 1, 'Running': 46}` | 当前集群中只有 1 个异常 Pod |
| 5 | Runbook 信息 | fetch_runbook | `典型状态: CrashLoopBackOff，兼容分类: config_bootstrap` | 与当前问题高度匹配 |

### 证据关联分析
- **证据 #3 + #2 印证**：`L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE` + `Reason: CrashLoopBackOff` → 说明容器在启动时因缺少环境变量 `APP_BOOT_MODE` 而失败，并进入崩溃循环。
- **证据链**：缺少环境变量 → 应用无法启动 → 容器崩溃 → Pod 重启 → 持续进入 CrashLoopBackOff 状态。

### 缺失证据（无）
| 证据 | 级别 | 影响 |
|------|------|------|
| 无 | - | - |

---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 缺失环境变量 APP_BOOT_MODE                                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 应用启动时依赖 APP_BOOT_MODE，但未提供 → 启动失败               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器启动失败，Reason: CrashLoopBackOff                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 CrashLoopBackOff，重启次数持续增加                     │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2 (Reason: CrashLoopBackOff) 和证据 #3 (`L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`)，问题的根本原因是**容器缺少必需的环境变量 `APP_BOOT_MODE`**，导致应用启动失败并进入崩溃循环。
**置信度**：高 (95%)
- ✅ 日志中明确提示缺失 `APP_BOOT_MODE`
- ✅ Pod 状态显示 `CrashLoopBackOff`，重启次数持续增加
- ✅ Runbook 明确匹配配置错误场景

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 添加缺失环境变量 `APP_BOOT_MODE`**
```bash
kubectl set env deployment/rc-config-env-missing -n aiops-e2e APP_BOOT_MODE=your_value
```
*依据*：日志提示缺少 `APP_BOOT_MODE`，需提供有效值以完成启动

**2. [可选] 检查 Pod 的 envFrom 配置**
```bash
kubectl get deployment rc-config-env-missing -n aiops-e2e -o jsonpath='{.spec.template.spec.containers[0].envFrom}'
```
*目的*：确认是否从 ConfigMap 或 Secret 中加载环境变量，若缺失则补充

**3. [可选] 检查 ConfigMap/Secret 是否存在**
```bash
kubectl get configmap -n aiops-e2e
kubectl get secret -n aiops-e2e
```
*目的*：确认是否引用了不存在的 ConfigMap 或 Secret

### 后续优化
1. **配置校验机制**：在应用启动前进行配置校验，避免因缺失配置导致崩溃。
2. **配置管理最佳实践**：使用 ConfigMap/Secret 管理环境变量，避免硬编码。
3. **监控告警**：配置 Pod 状态告警，及时发现 CrashLoopBackOff 等异常状态。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |
| 3. 查看容器日志 | `kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` | 无 L4_CONFIG_BOOTSTRAP_FAIL 错误 |

---
## ⚠️ 注意事项
- 如果添加了 `APP_BOOT_MODE` 仍无法启动，需进一步检查其他环境变量或配置是否完整。
- 建议在部署前通过 `kubectl describe pod` 检查 env 配置是否正确。
- 如果此 Pod 是由 Deployment 管理的，建议使用 `kubectl rollout restart` 触发更新。

---

---

## 📊 性能统计

├─ 总耗时: 3.5m
├─ 问题定位: 49.9s (24%) ✅
├─ 证据链采集: 56.6s (27%) ✅
├─ 根因分析: 7.9s (4%) ✅
├─ 汇总总结: 92.9s (45%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 6 次
```

📋 诊断追踪

- **核心 Runbook**: pod-config-error
- **参考 Runbook**: pod-config-error
- **工具调用**: 6 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
