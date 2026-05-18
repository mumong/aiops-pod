======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 5991e424b7084d18]

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
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE
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
  "layers": ["L4"],
  "layer_name": "ConfigError",
  "confidence": "high",
  "reasoning": "Pod 处于 CrashLoopBackOff 状态，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，表明应用配置缺失。此问题属于配置错误，归类为 L4。",
  "abnormal_pods": [
    {
      "namespace": "aiops-e2e",
      "name": "rc-config-env-missing-5d9b8b766c-cstkh",
      "status": "CrashLoopBackOff",
      "restarts": "14 (102s ago)",
      "labels": {
        "app": "rc-config-env-missing",
        "pod_template_hash": "5d9b8b766c",
        "pod_abnormal_type": "ConfigError",
        "rootcause-e2e": "true"
      }
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
    "rc-config-env-missing-5d9b8b766c-cstkh",
    "APP_BOOT_MODE",
    "ConfigMap",
    "Secret"
  ],
  "possible_scenarios": [
    "Pod 的环境变量 APP_BOOT_MODE 缺失，导致容器启动失败。",
    "ConfigMap 或 Secret 配置错误，导致容器无法正常启动。",
    "容器启动命令或入口点配置错误，导致容器崩溃。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (59.8s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'Pod 的环境变量 APP_BOOT_MODE 缺失，导致容器启动失败。', 'probability': 'high', 'reason': '日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE'}, {'scenario': 'ConfigMap 或 Secret 配置错误，导致容器无法正常启动。', 'probability': 'high', 'reason': 'describe 中显示 CrashLoopBackOff，且日志表明配置校验失败'}, {'scenario': '容器启动命令或入口点配置错误，导致容器崩溃。', 'probability': 'medium', 'reason': '需要进一步查看容器的启动命令和入口点配置'}]
   entities=[{"type": "Pod", "name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "APP_BOOT_MODE", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "missing", "namespace": "aiops-e2e"}]
   reasoning=当前集群中存在一个处于 CrashLoopBackOff 状态的 Pod，日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，表明是应用配置缺失导致的启动失败。根据 runbook 和诊断流程，确认是配置错误，属于 L4 层级问题。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.95, "reasoning": "当前集群中存在一个处于 CrashLoopBackOff 状态的 Pod，日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，表明是应用配置缺失导致的启动失败。根据 runbook 和诊断流程，确认是配置错误，属于 L4 层级问题。", "abnormal_pods": [{"name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "app_config", "key_entities": [{"type": "Pod", "name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "APP_BOOT_MODE", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "missing", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Pod 的环境变量 APP_BOOT_MODE 缺失，导致容器启动失败。", "probability": "high", "reason": "日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE"}, {"scenario": "ConfigMap 或 Secret 配置错误，导致容器无法正常启动。", "probability": "high", "reason": "describe 中显示 CrashLoopBackOff，且日志表明配置校验失败"}, {"scenario": "容器启动命令或入口点配置错误，导致容器崩溃。", "probability": "medium", "reason": "需要进一步查看容器的启动命令和入口点配置"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-cstkh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-cstkh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-env-missing-5d9b8b766c-cstkh              0/1     CrashLoopBackOff   14 (102s ago)   48m     172.16.166.152   node1    <none>           <none>            app=rc-config-env-missing,pod-template-hash=5d9b8b766c,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/5991e424b7084d18/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/5991e424b7084d18/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/5991e424b7084d18/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-env-missing-5d9b8b766c-cstkh
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Reason:       CrashLoopBackOff
  Warning  BackOff         63s 
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (2m 14.5s)
   📤 → 下游数据: evidence_items=6/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 的详细信息以确认其配置和状态","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e","tool_args":{"name":"rc-config-env-missing-5d9b8b766c-cstkh","namespace":"aiops-e2e","kind":"Pod"},"purpose":"验证 Pod 的当前状态、重启次数、Events 中的错误原因，以及配置是否缺失","evidence_type":"pod_status_and_events","target_scope":"aiops-e2e/rc-config-env-missing-5d9b8b766c-cstkh","acceptable_tools":["kubectl_describe","kubectl_events","kubectl_previous_logs"],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 的事件记录以确认其配置缺失的详细原因","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-env-missing-5d9b8b766c-cstkh","tool_args":{"kind":"Pod","name":"rc-config-env-missing-5d9b8b766c-cstkh","namespace":"aiops-e2e"},"purpose":"确认 Pod 的事件中是否包含 ConfigMap/Secret 缺失、环境变量未设置等配置错误信号","evidence_type":"pod_events","target_scope":"aiops-e2e/rc-config-env-missing-5d9b8b766c-cstkh","acceptable_tools":["kubectl_events","kubectl_describe","kubectl_previous_logs"],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod 的上一次容器日志以确认配置错误的具体原因","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e --previous","tool_args":{"name":"rc-config-env-missing-5d9b8b766c-cstkh","namespace":"aiops-e2e","container":"rc-config-env-missing","previous":true},"purpose":"确认日志中是否包含 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE 等配置缺失错误","evidence_type":"container_logs","target_scope":"aiops-e2e/rc-config-env-missing-5d9b8b766c-cstkh","acceptable_tools":["kubectl_previous_logs","kubectl_logs","kubectl_logs_grep"],"counts_for_completeness":true},{"id":"e4","description":"验证 Pod 的容器启动命令或入口点是否配置错误","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o yaml","tool_args":{"name":"rc-config-env-missing-5d9b8b766c-cstkh","namespace":"aiops-e2e","kind":"Pod"},"purpose":"确认容器 spec 中的 command/args/image 是否正确，是否引用了缺失的 ConfigMap/Secret","evidence_type":"pod_yaml_config","target_scope":"aiops-e2e/rc-config-env-missing-5d9b8b766c-cstkh","acceptable_tools":["kubectl_get_yaml","kubectl_describe"],"counts_for_completeness":true},{"id":"e5","description":"验证 ConfigMap APP_BOOT_MODE 是否存在并包含正确的环境变量","level":"important","tool":"kubectl_get_by_name","command":"kubectl get configmap APP_BOOT_MODE -n aiops-e2e -o yaml","tool_args":{"name":"APP_BOOT_MODE","namespace":"aiops-e2e","kind":"ConfigMap"},"purpose":"确认 ConfigMap 是否存在，其 data 字段是否包含 APP_BOOT_MODE 环境变量","evidence_type":"configmap_data","target_scope":"aiops-e2e/APP_BOOT_MODE","acceptable_tools":["kubectl_get_by_name","kubectl_get_yaml"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-env-missing-5d9b8b766c-cstkh\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         63s (x234 over 51m)  kubelet            Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-cstkh_aiops-e2e(5ed47e61-9e99-459d-88de-ee30d25b1def)\n                  cni.projectcalico.org/containerID: b609d3199474fd0c991fb51944c653ad8de49c03971407f25be4cb50f1498fc2\n                  cni.projectcalico.org/podIP: 172.16.166.152/32\n                  cni.projectcalico.org/podIPs: 172.16.166.152/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/5991e424b7084d18/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/5991e424b7084d18/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/5991e424b7084d18/tools/001-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 5 项，实际采集 3 项，未采集 2 项，完整度 60%；其中真实环境证据 6/8 项，完整度 75%；实际执行工具 4 个，匹配计划 3 个，未规划证据 1 个","plan_total":5,"plan_collected":3,"plan_completeness":0.6,"environment_evidence_total":8,"environment_evidence_collected":6,"environment_evidence_completeness":0.75,"executed_tool_count":4,"matched_tool_count":3,"unplanned_tool_count":1,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 的详细信息以确认其配置和状态","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e","purpose":"验证 Pod 的当前状态、重启次数、Events 中的错误原因，以及配置是否缺失","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 的事件记录以确认其配置缺失的详细原因","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-env-missing-5d9b8b766c-cstkh","purpose":"确认 Pod 的事件中是否包含 ConfigMap/Secret 缺失、环境变量未设置等配置错误信号","collected":false,"source":"planned","outcome":"unknown"},{"id":"e3","description":"获取异常 Pod 的上一次容器日志以确认配置错误的具体原因","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e --previous","purpose":"确认日志中是否包含 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE 等配置缺失错误","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"e4","description":"验证 Pod 的容器启动命令或入口点是否配置错误","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o yaml","purpose":"确认容器 spec 中的 command/args/image 是否正确，是否引用了缺失的 ConfigMap/Secret","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"e5","description":"验证 ConfigMap APP_BOOT_MODE 是否存在并包含正确的环境变量","level":"important","tool":"kubectl_get_by_name","command":"kubectl get configmap APP_BOOT_MODE -n aiops-e2e -o yaml","purpose":"确认 ConfigMap 是否存在，其 data 字段是否包含 APP_BOOT_MODE 环境变量","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":["e2(获取异常 Pod 的事件记录以确认其配置缺失的详细原因): 已规划但工具执行失败或无匹配结果","e5(验证 ConfigMap APP_BOOT_MODE 是否存在并包含正确的环境变量): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/5 项, 完整度: 75%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取异常 Pod 的详细信息以确认其配置和状态 | `kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` |
   | e2 | critical | ❌ | kubectl_events | 获取异常 Pod 的事件记录以确认其配置缺失的详细原因 | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-confi...` |
   | e3 | critical | ✅ | kubectl_previous_logs | 获取异常 Pod 的上一次容器日志以确认配置错误的具体原因 | `kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e --previous` |
   | e4 | important | ✅ | kubectl_get_yaml | 验证 Pod 的容器启动命令或入口点是否配置错误 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o yaml` |
   | e5 | important | ❌ | kubectl_get_by_name | 验证 ConfigMap APP_BOOT_MODE 是否存在并包含正确的环境变量 | `kubectl get configmap APP_BOOT_MODE -n aiops-e2e -o yaml` |

   ⚠️ 未采集原因:
   - e2(获取异常 Pod 的事件记录以确认其配置缺失的详细原因): 已规划但工具执行失败或无匹配结果
   - e5(验证 ConfigMap APP_BOOT_MODE 是否存在并包含正确的环境变量): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (15.3s)
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
   ✅ [汇总总结] 完成 (2m 9.9s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4150 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 39.4s
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
| **置信度** | 高 (95%) |
| **证据完整度** | 3/5 (60%) |

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
| 1 | Pod 状态 | kubectl get pod | `STATUS: CrashLoopBackOff` | Pod 处于持续崩溃重启状态 |
| 2 | Pod 日志 | kubectl logs --previous | `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE` | 明确指出 APP_BOOT_MODE 环境变量缺失 |
| 3 | Pod 配置 | kubectl get pod -o yaml | `app=rc-config-env-missing, pod_abnormal_type=ConfigError` | 标记为配置错误类型 |
| 4 | 事件记录 | kubectl describe pod | `Reason: CrashLoopBackOff` | 确认崩溃机制 |
| 5 | Runbook 匹配 | fetch_runbook | `# Pod ConfigError / 启动配置失败` | 问题符合配置错误的典型特征 |
| 6 | 环境状态 | kubectl_get_by_kind_in_cluster | `status_counts={'CrashLoopBackOff': 1, 'Running': 46}` | 仅 1 个 Pod 异常，其余正常 |

### 证据关联分析
- **证据 #2 + #3 印证**：日志中指出 APP_BOOT_MODE 缺失 + Pod 被标记为 ConfigError → 明确指向配置错误
- **证据链**：容器启动时依赖 APP_BOOT_MODE 环境变量 → 变量缺失 → 启动失败 → CrashLoopBackOff → Pod 重启

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| Pod 事件详细记录 | critical | 无法确认配置缺失的具体原因（例如 ConfigMap 是否被正确引用） |
| ConfigMap APP_BOOT_MODE 是否存在 | important | 无法确认是 ConfigMap 未挂载，还是环境变量未正确设置 |

---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ APP_BOOT_MODE 环境变量缺失，导致容器启动失败                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器启动脚本依赖 APP_BOOT_MODE 环境变量                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器启动失败（日志: L4_CONFIG_BOOTSTRAP_FAIL）                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CrashLoopBackOff，持续重启                           │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2 (`L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`) 和证据 #3 (`pod_abnormal_type=ConfigError`)，问题的根本原因是**Pod 缺失了 APP_BOOT_MODE 环境变量，导致容器启动失败**。  
**置信度**：高 (95%)  
- ✅ 日志直接指出配置缺失
- ✅ Pod 被标记为 ConfigError
- ⚠️ 缺少 ConfigMap APP_BOOT_MODE 是否存在的证据

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 为 Pod 设置 APP_BOOT_MODE 环境变量**
```bash
kubectl set env deployment/<deployment-name> -n aiops-e2e APP_BOOT_MODE=local
```
*依据*：日志提示 APP_BOOT_MODE 缺失，需要在启动时提供该变量

**2. [可选] 检查 ConfigMap APP_BOOT_MODE 是否存在**
```bash
kubectl get configmap APP_BOOT_MODE -n aiops-e2e
```
*目的*：确认是否 ConfigMap 挂载错误或不存在

**3. [可选] 检查 Pod 的环境变量是否正确引用**
```bash
kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o jsonpath='{.spec.containers[0].env}'
```
*目的*：确认 APP_BOOT_MODE 是否被正确挂载或设置

### 后续优化
1. **配置校验**：在部署流程中添加配置校验，确保关键环境变量不为空
2. **ConfigMap 管理**：将 APP_BOOT_MODE 等关键配置集中管理，避免手动设置错误
3. **监控告警**：配置 Pod 状态告警（如 CrashLoopBackOff），及时发现类似问题

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 重启次数不再增加 |
| 3. 检查环境变量 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o jsonpath='{.spec.containers[0].env}'` | 包含 APP_BOOT_MODE |

---
## ⚠️ 注意事项
- 如果问题持续，建议检查容器启动脚本是否依赖其他配置项
- 建议配置 ConfigMap 的自动挂载或环境变量注入
- 确保所有依赖环境变量的容器都有默认值或校验逻辑

---

## 📊 性能统计

├─ 总耗时: 5.7m
├─ 问题定位: 59.8s (18%) ✅
├─ 证据链采集: 134.5s (40%) ✅
├─ 根因分析: 15.3s (4%) ✅
├─ 汇总总结: 129.9s (38%) ✅
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
