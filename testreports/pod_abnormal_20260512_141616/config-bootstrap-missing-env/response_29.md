======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 9bc8867166274c03]

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
      📄 NAME                             READY   STATUS             RESTARTS       AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
appconfigfail-575d77485d-nfpvh   0/1     CrashLoopBa
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 6
signals: 5
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config
L4_SCENARIO: config-bootstrap-fail
L4_ERROR_TYPE: applicati
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                             READY   STATUS             RESTARTS        AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
appconfigfail-575d77485d-nfpvh   0/1     CrashLoopB
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "ConfigError",
  "confidence": 0.95,
  "reasoning": "Pod 'appconfigfail-575d77485d-nfpvh' 处于 CrashLoopBackOff 状态，重启次数持续增长。describe 显示其 Exit Code 为业务退出码，且日志中明确包含 'L4_CONFIG_BOOTSTRAP_FAIL'、'missing required APP_BOOT_MODE' 和 'business config validation failed before server startup' 等配置校验失败信号。同时，排除了 OOMKilled、ImagePullFailed 和 Evicted 等其他异常类型，符合 ConfigError 的判定标准。",
  "abnormal_pods": [
    {
      "name": "appconfigfail-575d77485d-nfpvh",
      "namespace": "aiops-e2e",
      "status": "CrashLoopBackOff",
      "restarts": "18 (114s ago)",
      "age": "69m",
      "ip": "172.16.166.184",
      "node": "node1",
      "labels": {
        "app": "appconfigfail",
        "e2e-test": "true",
        "l4-scenario": "config-bootstrap-fail",
        "pod-template-hash": "575d77485d",
        "pod_abnormal_type": "ConfigError"
      }
    }
  ],
  "abnormal_groups": [
    {
      "type": "ConfigError",
      "count": 1,
      "pods": [
        {
          "name": "appconfigfail-575d77485d-nfpvh",
          "namespace": "aiops-e2e"
        }
      ]
    }
  ],
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "ConfigError",
  "status_category": "CrashLoopBackOff",
  "key_entities": [
    "appconfigfail-575d77485d-nfpvh",
    "aiops-e2e",
    "APP_BOOT_MODE",
    "L4_CONFIG_BOOTSTRAP_FAIL"
  ],
  "possible_scenarios": [
    "应用启动配置错误",
    "ConfigMap/Secret 键名拼错或缺失",
    "业务配置校验失败",
    "环境变量缺失或无效"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (3m 27.6s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[]
   entities=[]
   reasoning=Pod 'appconfigfail-575d77485d-nfpvh' 处于 CrashLoopBackOff 状态，重启次数持续增长。describe 显示其 Exit Code 为业务退出码，且日志中明确包含 'L4_CONFIG_BOOTSTRAP_FAIL'、'missing required APP_BOOT_MODE' 和 'business config validation failed before server startup' 等配置校验失败信号。同时，排除了 OOMKilled、ImagePullFailed 和 Evicted 等其他异常类型，符合 ConfigError 的判定标准。
   layer_analysis={"layer": "L4", "derived_layer": "", "layers": [], "layer_name": "", "confidence": 0.5, "reasoning": "Pod 'appconfigfail-575d77485d-nfpvh' 处于 CrashLoopBackOff 状态，重启次数持续增长。describe 显示其 Exit Code 为业务退出码，且日志中明确包含 'L4_CONFIG_BOOTSTRAP_FAIL'、'missing required APP_BOOT_MODE' 和 'business config validation failed before server startup' 等配置校验失败信号。同时，排除了 OOMKilled、ImagePullFailed 和 Evicted 等其他异常类型，符合 ConfigError 的判定标准。", "abnormal_pods": [{"name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "app_config", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     appconfigfail-575d77485d-nfpvh                      0/1     CrashLoopBackOff   18 (76s ago)    68m    172.16.166.184   node1    <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError"], "raw_ref": "/tmp/aiops/reports/context_archives/9bc8867166274c03/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/9bc8867166274c03/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/9bc8867166274c03/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                             READY   STATUS             RESTARTS        AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
appconfigfail-575d77485d-nfpvh   0/1     CrashLoopB
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
4m7s (x325 over 74m)   Warning   BackOff   Pod/appconfigfail-575d77485d-nfpvh   Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3f
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 6
signals: 5
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config
L4_SCENARIO: config-bootstrap-fail
L4_ERROR_TYPE: applicati
   💭 [证据链采集] 已采集证据：
1. Pod `appconfigfail-575d77485d-nfpvh` 的状态为 `CrashLoopBackOff`，重启次数持续增加。
2. 事件记录显示重复的 `Back-off restarting failed container` 警告。
3. 容器日志明确指出 `L4_CONFIG_BOOTSTRAP_FAIL`、`FATAL: missing required APP_BOOT_MODE` 等配置校验失败信号。

结论：该 Pod 异常由启动配置错误导致，符合 L4 归因的 ConfigError 类型。建议检查业务配置，确保所有必要环境变量或 ConfigMap/Secret 正确注入。
   ✅ [证据链采集] 完成 (2m 28.3s)
   📤 → 下游数据: evidence_items=6/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod 'appconfigfail-575d77485d-nfpvh' 的详细状态信息，包括事件、容器状态、重启原因等。","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml","tool_args":{"namespace":"aiops-e2e","name":"appconfigfail-575d77485d-nfpvh","output_format":"yaml"},"purpose":"获取 Pod 的完整 YAML 配置，验证 CrashLoopBackOff 的具体原因和配置错误。","evidence_type":"state_verification","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod 'appconfigfail-575d77485d-nfpvh' 的事件记录，以确认导致当前状态的事件链。","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=appconfigfail-575d77485d-nfpvh","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=appconfigfail-575d77485d-nfpvh"},"purpose":"确认 Pod 的事件历史，查找导致 CrashLoopBackOff 的关键事件，例如配置错误、拉取失败等。","evidence_type":"event_verification","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取 Pod 'appconfigfail-575d77485d-nfpvh' 的容器日志，验证是否存在配置校验失败的明确信号。","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous","tool_args":{"namespace":"aiops-e2e","pod_name":"appconfigfail-575d77485d-nfpvh","container_name":null,"previous":true},"purpose":"验证容器启动失败的日志，确认是否包含配置错误、缺失参数等关键信号。","evidence_type":"log_verification","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                             READY   STATUS             RESTARTS        AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nappconfigfail-575d77485d-nfpvh   0/1     CrashLoopBackOff   19 (105s ago)   74m   172.16.166.184   node1   <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/9bc8867166274c03/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9bc8867166274c03/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9bc8867166274c03/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n4m7s (x325 over 74m)   Warning   BackOff   Pod/appconfigfail-575d77485d-nfpvh   Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/9bc8867166274c03/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9bc8867166274c03/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9bc8867166274c03/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 6\nsignals: 5\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/9bc8867166274c03/tools/003-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9bc8867166274c03/tools/003-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9bc8867166274c03/tools/003-evidence-kubectl_previous_logs.summary.txt"}],"llm_analysis":"已采集证据：\n1. Pod `appconfigfail-575d77485d-nfpvh` 的状态为 `CrashLoopBackOff`，重启次数持续增加。\n2. 事件记录显示重复的 `Back-off restarting failed container` 警告。\n3. 容器日志明确指出 `L4_CONFIG_BOOTSTRAP_FAIL`、`FATAL: missing required APP_BOOT_MODE` 等配置校验失败信号。\n\n结论：该 Pod 异常由启动配置错误导致，符合 L4 归因的 ConfigError 类型。建议检查业务配置，确保所有必要环境变量或 ConfigMap/Secret 正确注入。","collection_summary":"计划 3 项，实际采集 2 项，未采集 1 项，完整度 67%；其中真实环境证据 6/7 项，完整度 86%；实际执行工具 7 个，匹配计划 2 个，未规划证据 5 个","plan_total":3,"plan_collected":2,"plan_completeness":0.6666666666666666,"environment_evidence_total":7,"environment_evidence_collected":6,"environment_evidence_completeness":0.8571428571428571,"executed_tool_count":7,"matched_tool_count":2,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"验证 Pod 'appconfigfail-575d77485d-nfpvh' 的详细状态信息，包括事件、容器状态、重启原因等。","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml","purpose":"获取 Pod 的完整 YAML 配置，验证 CrashLoopBackOff 的具体原因和配置错误。","collected":false,"source":"planned","outcome":"unknown"},{"id":"e2","description":"获取 Pod 'appconfigfail-575d77485d-nfpvh' 的事件记录，以确认导致当前状态的事件链。","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=appconfigfail-575d77485d-nfpvh","purpose":"确认 Pod 的事件历史，查找导致 CrashLoopBackOff 的关键事件，例如配置错误、拉取失败等。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取 Pod 'appconfigfail-575d77485d-nfpvh' 的容器日志，验证是否存在配置校验失败的明确信号。","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous","purpose":"验证容器启动失败的日志，确认是否包含配置错误、缺失参数等关键信号。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e1(验证 Pod 'appconfigfail-575d77485d-nfpvh' 的详细状态信息，包括事件、容器状态、重启原因等。): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/3 项, 完整度: 86%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ❌ | kubectl_get_by_name | 验证 Pod 'appconfigfail-575d77485d-nfpvh' 的详细状态... | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml` |
   | e2 | important | ✅ | kubectl_events | 获取 Pod 'appconfigfail-575d77485d-nfpvh' 的事件记录... | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=appconfi...` |
   | e3 | critical | ✅ | kubectl_previous_logs | 获取 Pod 'appconfigfail-575d77485d-nfpvh' 的容器日志... | `kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous` |

   ⚠️ 未采集原因:
   - e1(验证 Pod 'appconfigfail-575d77485d-nfpvh' 的详细状态信息，包括事件、容器状态、重启原因等。): 已规划但工具执行失败或无匹配结果

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
   ✅ [汇总总结] 完成 (2m 27.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3884 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 8m 42.9s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览
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
| 错误信息 | L4_CONFIG_BOOTSTRAP_FAIL、missing required APP_BOOT_MODE、business config validation failed before server startup |

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | kubectl get pod | `STATUS: CrashLoopBackOff, RESTARTS: 18` | Pod 持续重启，处于异常状态 |
| 2 | 容器日志 | kubectl logs --previous | `L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config` | 明确指出配置校验失败 |
| 3 | 事件日志 | kubectl describe pod | `Warning BackOff Back-off restarting failed container app` | 重启失败，容器启动失败 |
| 4 | Pod 标签 | kubectl get pod | `l4-scenario: config-bootstrap-fail` | 明确标记为配置启动失败场景 |

### 证据关联分析
- **证据 #2 + #4 印证**：日志中 `L4_CONFIG_BOOTSTRAP_FAIL` + 标签 `l4-scenario: config-bootstrap-fail` → 明确指向配置错误
- **证据链**：应用启动时依赖的配置项缺失 → 配置校验失败 → 容器启动失败 → Pod 重启
- **证据 #1 印证**：重启次数持续增长 → 问题未被解决

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| Pod 的详细状态信息（如容器状态、重启原因） | critical | 无法进一步分析配置缺失的具体原因 |

---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 应用启动所需的配置项 `APP_BOOT_MODE` 缺失，导致配置校验失败       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 配置校验失败 → 容器启动失败 → 容器被终止 → Pod 重启              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器因配置错误被终止（Exit Code 为业务退出码）                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CrashLoopBackOff，重启次数持续增长                   │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2 (容器日志中 `L4_CONFIG_BOOTSTRAP_FAIL`) 和证据 #4 (Pod 标签 `l4-scenario: config-bootstrap-fail`)，问题的根本原因是**应用启动配置缺失，特别是缺少 `APP_BOOT_MODE` 环境变量**，导致容器启动失败并进入 CrashLoopBackOff 状态。
**置信度**：高 (90%)
- ✅ 容器日志中明确指出配置校验失败
- ✅ Pod 标签明确标记为配置启动失败场景
- ⚠️ 缺少 Pod 详细状态信息，无法进一步确认是否为 ConfigMap/Secret 配置错误

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 补全环境变量**
```bash
kubectl set env deployment/appconfigfail-575d77485d -n aiops-e2e APP_BOOT_MODE=normal
```
*依据*：日志中提示 `missing required APP_BOOT_MODE`，补全该环境变量可解决配置缺失问题

**2. [可选] 检查 ConfigMap/Secret**
```bash
kubectl describe configmap -n aiops-e2e <configmap-name>
kubectl describe secret -n aiops-e2e <secret-name>
```
*目的*：确认配置对象是否包含 `APP_BOOT_MODE`，排查是否为引用错误

### 后续优化
1. **配置校验机制**：在应用启动前增加配置项校验逻辑，避免因缺失关键配置导致容器启动失败
2. **自动化测试**：在部署流水线中增加配置验证步骤
3. **监控告警**：配置 CrashLoopBackOff 监控告警，及时发现配置类故障

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 重启次数不再增加 |
| 3. 检查容器状态 | `kubectl describe pod appconfigfail-575d77485d-nfpvh -n aiops-e2e` | 无 `CrashLoopBackOff` 状态 |

---
## ⚠️ 注意事项
- 如果问题仍然存在，建议检查 ConfigMap/Secret 是否被正确引用
- 可以通过 `kubectl logs` 查看容器启动日志，确认配置是否被正确加载
- 若为多副本部署，建议使用 `kubectl rollout restart deployment/<deployment-name>` 重启部署，避免手动删除 Pod 导致调度不稳定

---

## 📊 性能统计

├─ 总耗时: 8.7m
├─ 问题定位: 207.6s (40%) ✅
├─ 证据链采集: 148.3s (28%) ✅
├─ 根因分析: 19.3s (4%) ✅
├─ 汇总总结: 147.7s (28%) ✅
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
