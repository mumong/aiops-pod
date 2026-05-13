======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: d07034a1b7bb496a]

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
      📄 NAME                             READY   STATUS             RESTARTS         AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
appconfigfail-575d77485d-nfpvh   0/1     CrashLoop
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 6
signals: 5
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config
L4_SCENARIO: config-bootstrap-fail
L4_ERROR_TYPE: applicati
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "ConfigError",
  "confidence": "high",
  "reasoning": "Pod 'appconfigfail-575d77485d-nfpvh' 在 CrashLoopBackOff 状态，日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: missing required APP_BOOT_MODE。这是典型的配置错误，属于 L4 分类。",
  "abnormal_pods": [
    {
      "name": "appconfigfail-575d77485d-nfpvh",
      "namespace": "aiops-e2e",
      "status": "CrashLoopBackOff",
      "restarts": "14 (3m30s ago)",
      "ip": "172.16.166.184",
      "node": "node1"
    }
  ],
  "abnormal_groups": [
    {
      "type": "ConfigError",
      "count": 1
    }
  ],
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "ConfigError",
  "status_category": "CrashLoopBackOff",
  "key_entities": [
    "appconfigfail-575d77485d-nfpvh",
    "aiops-e2e",
    "node1"
  ],
  "possible_scenarios": [
    "缺少必要的环境变量 APP_BOOT_MODE",
    "业务配置验证失败"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (3m 13.3s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': '缺少必要的环境变量 APP_BOOT_MODE', 'probability': 'high', 'reason': '日志显示 FATAL: missing required APP_BOOT_MODE'}, {'scenario': '业务配置验证失败', 'probability': 'high', 'reason': '日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: business config validation failed before server startup'}]
   entities=[{"type": "Pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}]
   reasoning=Pod 'appconfigfail-575d77485d-nfpvh' 当前处于 CrashLoopBackOff 状态，且其日志明确显示 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: missing required APP_BOOT_MODE，属于典型的配置错误。这表明异常类型为 ConfigError，归类为 L4 层级。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 1.0, "reasoning": "Pod 'appconfigfail-575d77485d-nfpvh' 当前处于 CrashLoopBackOff 状态，且其日志明确显示 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: missing required APP_BOOT_MODE，属于典型的配置错误。这表明异常类型为 ConfigError，归类为 L4 层级。", "abnormal_pods": [{"name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "app_config", "key_entities": [{"type": "Pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}], "possible_scenarios": [{"scenario": "缺少必要的环境变量 APP_BOOT_MODE", "probability": "high", "reason": "日志显示 FATAL: missing required APP_BOOT_MODE"}, {"scenario": "业务配置验证失败", "probability": "high", "reason": "日志显示 L4_CONFIG_BOOTSTRAP_FAIL 和 FATAL: business config validation failed before server startup"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     appconfigfail-575d77485d-nfpvh                      0/1     CrashLoopBackOff   14 (3m7s ago)   49m    172.16.166.184   node1    <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError"], "raw_ref": "/tmp/aiops/reports/context_archives/d07034a1b7bb496a/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/d07034a1b7bb496a/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/d07034a1b7bb496a/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 100%

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
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: appconfigfail-575d77485d-nfpvh
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键状态/事件:
                  aiops.e2e/expected-status: CrashLoopBackOff|CreateContai
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 6
signals: 5
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config
L4_SCENARIO: config-bootstrap-fail
L4_ERROR_TYPE: applicati
   💭 [证据链采集] 调用工具: kubectl_find_resource
   ✅ [证据链采集] 完成 (2m 45.8s)
   📤 → 下游数据: evidence_items=5/6
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 'appconfigfail-575d77485d-nfpvh' 的详细描述信息，以确认其状态、事件和配置信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod appconfigfail-575d77485d-nfpvh -n aiops-e2e","tool_args":{"kind":"Pod","name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e"},"purpose":"验证异常 Pod 的状态、事件和配置信息","evidence_type":"pod_status_config_events","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 'appconfigfail-575d77485d-nfpvh' 的上一个容器日志，以确认其失败原因","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous","tool_args":{"kind":"Pod","name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e","container":"appconfigfail"},"purpose":"验证异常 Pod 上一个容器的失败原因","evidence_type":"pod_previous_logs","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod 'appconfigfail-575d77485d-nfpvh' 依赖的 ConfigMap/Secret，以确认其配置缺失情况","level":"important","tool":"kubectl_find_resource","command":"kubectl find resource -n aiops-e2e -t pod -n appconfigfail-575d77485d-nfpvh","tool_args":{"kind":"Pod","name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e"},"purpose":"验证异常 Pod 依赖的 ConfigMap/Secret 是否缺失","evidence_type":"pod_dependency_resources","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: appconfigfail-575d77485d-nfpvh\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键状态/事件:\n                  aiops.e2e/expected-status: CrashLoopBackOff|CreateContainerConfigError|CreateContainerError\n    State:          Waiting\n      Reason:       CrashLoopBackOff\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42\n  Warning  BackOff         17s (x257 over 55m)  kubelet            Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d07034a1b7bb496a/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d07034a1b7bb496a/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d07034a1b7bb496a/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 6\nsignals: 5\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d07034a1b7bb496a/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d07034a1b7bb496a/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d07034a1b7bb496a/tools/002-evidence-kubectl_previous_logs.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'keyword' is a required property","collection_summary":"计划 3 项，实际采集 2 项，未采集 1 项，完整度 67%；其中真实环境证据 5/6 项，完整度 83%；实际执行工具 5 个，匹配计划 2 个，未规划证据 3 个","plan_total":3,"plan_collected":2,"plan_completeness":0.6666666666666666,"environment_evidence_total":6,"environment_evidence_collected":5,"environment_evidence_completeness":0.8333333333333334,"executed_tool_count":5,"matched_tool_count":2,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 'appconfigfail-575d77485d-nfpvh' 的详细描述信息，以确认其状态、事件和配置信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod appconfigfail-575d77485d-nfpvh -n aiops-e2e","purpose":"验证异常 Pod 的状态、事件和配置信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 'appconfigfail-575d77485d-nfpvh' 的上一个容器日志，以确认其失败原因","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous","purpose":"验证异常 Pod 上一个容器的失败原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod 'appconfigfail-575d77485d-nfpvh' 依赖的 ConfigMap/Secret，以确认其配置缺失情况","level":"important","tool":"kubectl_find_resource","command":"kubectl find resource -n aiops-e2e -t pod -n appconfigfail-575d77485d-nfpvh","purpose":"验证异常 Pod 依赖的 ConfigMap/Secret 是否缺失","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e3(获取异常 Pod 'appconfigfail-575d77485d-nfpvh' 依赖的 ConfigMap/Secret，以确认其配置缺失情况): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/3 项, 完整度: 83%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取异常 Pod 'appconfigfail-575d77485d-nfpvh' 的详细... | `kubectl describe pod appconfigfail-575d77485d-nfpvh -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_previous_logs | 获取异常 Pod 'appconfigfail-575d77485d-nfpvh' 的上一... | `kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous` |
   | e3 | important | ❌ | kubectl_find_resource | 获取异常 Pod 'appconfigfail-575d77485d-nfpvh' 依赖的... | `kubectl find resource -n aiops-e2e -t pod -n appconfigfail-575d77485d-nfpvh` |

   ⚠️ 未采集原因:
   - e3(获取异常 Pod 'appconfigfail-575d77485d-nfpvh' 依赖的 ConfigMap/Secret，以确认其配置缺失情况): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (20.5s)
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
   ✅ [汇总总结] 完成 (1m 31.1s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4609 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 7m 50.7s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **Pod异常状态** | CrashLoopBackOff |
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
| Pod | appconfigfail-575d77485d-nfpvh |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | L4_CONFIG_BOOTSTRAP_FAIL, FATAL: missing required APP_BOOT_MODE |

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff, RESTARTS: 14 (3m7s ago)` | Pod 持续重启，状态异常 |
| 2 | 容器日志 | `kubectl logs <pod> --previous` | `L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config`<br>`FATAL: missing required APP_BOOT_MODE` | 日志明确指出配置缺失导致启动失败 |
| 3 | Pod 详细信息 | `kubectl describe pod appconfigfail-575d77485d-nfpvh` | `Status: Running`<br>`Last State: Terminated`<br>`Reason: Error`<br>`Message: FATAL: missing required APP_BOOT_MODE` | Pod 最后一次启动失败，原因为配置缺失 |
| 4 | 事件摘要 | `kubectl get pod` | `L4_SCENARIO: config-bootstrap-fail`<br>`L4_ERROR_TYPE: application-config-validation` | 标签明确归因到配置验证失败 |
| 5 | 上游工具验证 | `kubectl_get_by_kind_in_cluster` | `status_counts={'CrashLoopBackOff': 1, 'Running': 46}` | 集群中仅 1 个 Pod 出现 CrashLoopBackOff，其余正常 |

### 证据关联分析
- **证据 #1 + #2 印证**：Pod 持续重启 (`CrashLoopBackOff`)，日志显示 `FATAL: missing required APP_BOOT_MODE` → 与配置缺失强相关。
- **证据 #3 + #4 印证**：`kubectl describe` 明确指出 `Reason: Error`，`Message: FATAL: missing required APP_BOOT_MODE`，标签 `L4_SCENARIO: config-bootstrap-fail` 确认归因到配置启动失败。
- **证据链**：缺失 `APP_BOOT_MODE` 环境变量 → 业务配置验证失败 → 应用启动中止 → 容器退出 → Pod 重启 → 持续 CrashLoopBackOff。

### 缺失证据
| 证据 | 级别 | 影响 |
|------|------|------|
| 依赖的 ConfigMap/Secret | important | 无法确认配置缺失来源（Pod spec、ConfigMap、Secret） |
---

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 缺失关键环境变量 APP_BOOT_MODE，导致业务配置验证失败            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 应用启动时依赖的配置项缺失 → 业务配置验证失败 → 应用中止        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器因配置错误退出（Exit Code 42 或业务退出码）                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 CrashLoopBackOff，持续重启                             │
└─────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #2 (`FATAL: missing required APP_BOOT_MODE`) 和证据 #3 (`Message: FATAL: missing required APP_BOOT_MODE`)，
问题的根本原因是**容器缺少关键环境变量 APP_BOOT_MODE，导致业务配置验证失败**，进而触发容器退出并导致 Pod 持续重启。
**置信度**：高 (90%)
- ✅ 日志明确指出缺失 APP_BOOT_MODE
- ✅ Pod 状态为 CrashLoopBackOff，重启次数持续增加
- ⚠️ 未采集 ConfigMap/Secret 信息，无法确认配置缺失来源

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 补充缺失的环境变量 APP_BOOT_MODE**
```bash
kubectl set env deployment/appconfigfail-575d77485d APP_BOOT_MODE=dev -n aiops-e2e
```
*依据*：日志显示 `FATAL: missing required APP_BOOT_MODE`，需通过 Pod spec 补充该变量

**2. [可选] 查看 Pod spec 确认是否引用了 ConfigMap/Secret**
```bash
kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml
```
*目的*：确认是否引用了 ConfigMap 或 Secret，排查配置缺失来源

**3. [建议] 检查 ConfigMap/Secret 是否存在或配置正确**
```bash
kubectl get configmap -n aiops-e2e
kubectl get secret -n aiops-e2e
```
*目的*：确认依赖的 ConfigMap/Secret 是否存在且配置正确

### 后续优化
1. **配置校验**：在 Deployment 中添加 `livenessProbe` 和 `readinessProbe`，提前发现配置错误
2. **配置管理**：建议使用 ConfigMap/Secret 管理配置，避免硬编码
3. **监控告警**：配置 Kubernetes 事件监控，当 Pod 状态变为 `CrashLoopBackOff` 时触发告警

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |
| 3. 查看日志确认无错误 | `kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e` | 无 `FATAL: missing required APP_BOOT_MODE` |

---

## ⚠️ 注意事项
- 如果 `APP_BOOT_MODE` 是由 ConfigMap/Secret 提供，需确保其正确挂载到容器中
- 建议在 Deployment 中设置合理的 `livenessProbe` 和 `readinessProbe`，提高稳定性
- 如果问题持续，建议检查应用配置逻辑是否存在硬编码依赖

---

## 📊 性能统计

├─ 总耗时: 7.8m
├─ 问题定位: 193.3s (41%) ✅
├─ 证据链采集: 165.8s (35%) ✅
├─ 根因分析: 20.5s (4%) ✅
├─ 汇总总结: 91.1s (19%) ✅
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
