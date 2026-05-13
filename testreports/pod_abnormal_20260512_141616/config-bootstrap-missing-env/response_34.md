======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 9c0597670ec84dcd]

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
   💭 [问题定位] 调用工具: kubectl_logs
   💭 [问题定位] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 日志摘要:
lines: 6
signals: 5
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config
L4_SCENARIO: config-bootstrap-fail
L4_ERROR_TYPE: application-config
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
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
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 表格摘要: rows=1 abnormal=0 status_counts={}
NAME               DATA   AGE    LABELS
# 样例行
kube-root-ca.crt   1      108d   <none>
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (3m 9.0s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': '配置缺失', 'probability': '高', 'reason': '日志中明确显示 missing required APP_BOOT_MODE'}, {'scenario': '配置格式错误', 'probability': '中', 'reason': '日志中提到 business config validation failed before server startup'}]
   entities=[{"type": "Pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}]
   reasoning=当前环境中存在一个处于 CrashLoopBackOff 状态的 Pod（appconfigfail-575d77485d-nfpvh），且容器退出码为 42，日志中明确包含 L4_CONFIG_BOOTSTRAP_FAIL、missing required APP_BOOT_MODE 和 business config validation failed before server startup 等信号。根据 runbook 的判定规则，这些特征符合 ConfigError 的归因分类，属于 L4 层级的问题。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "application error", "confidence": 0.95, "reasoning": "当前环境中存在一个处于 CrashLoopBackOff 状态的 Pod（appconfigfail-575d77485d-nfpvh），且容器退出码为 42，日志中明确包含 L4_CONFIG_BOOTSTRAP_FAIL、missing required APP_BOOT_MODE 和 business config validation failed before server startup 等信号。根据 runbook 的判定规则，这些特征符合 ConfigError 的归因分类，属于 L4 层级的问题。", "abnormal_pods": [{"name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "app_config/app_health", "key_entities": [{"type": "Pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "配置缺失", "probability": "高", "reason": "日志中明确显示 missing required APP_BOOT_MODE"}, {"scenario": "配置格式错误", "probability": "中", "reason": "日志中提到 business config validation failed before server startup"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     appconfigfail-575d77485d-nfpvh                      0/1     CrashLoopBackOff   19 (4m59s ago)   77m    172.16.166.184   node1    <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError"], "raw_ref": "/tmp/aiops/reports/context_archives/9c0597670ec84dcd/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/9c0597670ec84dcd/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/9c0597670ec84dcd/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: appconfigfail-575d77485d-nfpvh
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键状态/事件:
                  aiops.e2e/expected-status: CrashLoopBackOff|CreateContai
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: appconfigfail-575d77485d-nfpvh
namespace: aiops-e2e
creationTimestamp: 2026-05-12T05:59:23Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finali
   💭 [证据链采集] 调用工具: kubectl_logs
   💭 [证据链采集] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 日志摘要:
lines: 6
signals: 5
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config
L4_SCENARIO: config-bootstrap-fail
L4_ERROR_TYPE: application-config
   💭 [证据链采集] 调用工具: kubectl_container_previous_logs
   ✅ [证据链采集] 完成 (3m 51.8s)
   📤 → 下游数据: evidence_items=10/10
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证异常 Pod 的描述信息，包括状态、重启次数和最后一次退出状态","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod appconfigfail-575d77485d-nfpvh -n aiops-e2e","tool_args":{"kind":"Pod","name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e"},"purpose":"验证异常 Pod 的描述信息，包括状态、重启次数和最后一次退出状态","evidence_type":"pod_status","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"检查 Pod 的完整 YAML 配置，确认是否存在配置错误","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e"},"purpose":"检查 Pod 的完整 YAML 配置，确认是否存在配置错误","evidence_type":"pod_config","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod 的日志，确认是否存在配置缺失或格式错误","level":"important","tool":"kubectl_logs","command":"kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e","tool_args":{"kind":"Pod","name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e"},"purpose":"获取异常 Pod 的日志，确认是否存在配置缺失或格式错误","evidence_type":"pod_logs","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":["kubectl_logs"],"counts_for_completeness":true},{"id":"e4","description":"获取异常 Pod 上次容器的日志，确认是否存在配置缺失或格式错误","level":"important","tool":"kubectl_container_previous_logs","command":"kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous","tool_args":{"kind":"Pod","name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e"},"purpose":"获取异常 Pod 上次容器的日志，确认是否存在配置缺失或格式错误","evidence_type":"pod_previous_logs","target_scope":"aiops-e2e/appconfigfail-575d77485d-nfpvh","acceptable_tools":["kubectl_container_previous_logs"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: appconfigfail-575d77485d-nfpvh\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键状态/事件:\n                  aiops.e2e/expected-status: CrashLoopBackOff|CreateContainerConfigError|CreateContainerError\n    State:          Waiting\n      Reason:       CrashLoopBackOff\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42\n  Warning  BackOff  4m1s (x371 over 84m)  kubelet  Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/9c0597670ec84dcd/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9c0597670ec84dcd/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9c0597670ec84dcd/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: appconfigfail-575d77485d-nfpvh\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-12T05:59:23Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=appconfigfail, e2e-test=true, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/expected-evidence=previous logs contain L4_CONFIG_BOOTSTRAP_FAIL and missing required APP_BOOT_MODE, aiops.e2e/expected-status=CrashLoopBackOff|CreateContainerConfigError|CreateContainerError, aiops.e2e/runbook=pod-config-error.md\nownerReferences: ReplicaSet/appconfigfail-575d77485d\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=21 reason=CrashLoopBackOff exitCode=42\n  message: back-off 5m0s restarting failed container=app pod=appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)\nvolumes:\n- {\"name\": \"kube-api-access-r4t7x\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/9c0597670ec84dcd/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9c0597670ec84dcd/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9c0597670ec84dcd/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_logs","data":"kubectl_logs 日志摘要:\nlines: 6\nsignals: 5\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/9c0597670ec84dcd/tools/003-evidence-kubectl_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9c0597670ec84dcd/tools/003-evidence-kubectl_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9c0597670ec84dcd/tools/003-evidence-kubectl_logs.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'container_name' is a required property","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 10/10 项，完整度 100%；实际执行工具 8 个，匹配计划 4 个，未规划证据 4 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":10,"environment_evidence_collected":10,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":4,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"验证异常 Pod 的描述信息，包括状态、重启次数和最后一次退出状态","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod appconfigfail-575d77485d-nfpvh -n aiops-e2e","purpose":"验证异常 Pod 的描述信息，包括状态、重启次数和最后一次退出状态","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"检查 Pod 的完整 YAML 配置，确认是否存在配置错误","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml","purpose":"检查 Pod 的完整 YAML 配置，确认是否存在配置错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod 的日志，确认是否存在配置缺失或格式错误","level":"important","tool":"kubectl_logs","command":"kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e","purpose":"获取异常 Pod 的日志，确认是否存在配置缺失或格式错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"获取异常 Pod 上次容器的日志，确认是否存在配置缺失或格式错误","level":"important","tool":"kubectl_container_previous_logs","command":"kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous","purpose":"获取异常 Pod 上次容器的日志，确认是否存在配置缺失或格式错误","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_container_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证异常 Pod 的描述信息，包括状态、重启次数和最后一次退出状态 | `kubectl describe pod appconfigfail-575d77485d-nfpvh -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_get_yaml | 检查 Pod 的完整 YAML 配置，确认是否存在配置错误 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml` |
   | e3 | important | ✅ | kubectl_logs | 获取异常 Pod 的日志，确认是否存在配置缺失或格式错误 | `kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e` |
   | e4 | important | ✅ | kubectl_container_previou... | 获取异常 Pod 上次容器的日志，确认是否存在配置缺失或格式错误 | `kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous` |

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (10.3s)
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
   ✅ [汇总总结] 完成 (1m 35.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4013 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 8m 46.6s
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
| **问题分类** | ConfigError（配置错误） |
| **置信度** | 高 (95%) |
| **证据完整度** | 4/4 (100%) |

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
| 错误信息 | L4_CONFIG_BOOTSTRAP_FAIL, missing required APP_BOOT_MODE, business config validation failed before server startup |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | kubectl get pod | `STATUS: CrashLoopBackOff, RESTARTS: 19 (4m59s ago), NAME: appconfigfail-575d77485d-nfpvh` | Pod 处于持续重启状态 |
| 2 | 容器日志 | kubectl logs | `L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config` | 应用启动失败，因配置无效 |
| 3 | 容器上次日志 | kubectl logs --previous | `FATAL: missing required APP_BOOT_MODE` | 明确指出缺少必要配置参数 APP_BOOT_MODE |
| 4 | Pod YAML | kubectl get pod -o yaml | `namespace: aiops-e2e, labels: {pod_abnormal_type: ConfigError}` | 标签表明此 Pod 被归类为配置错误 |

### 证据关联分析

- **证据 #1 + #2 + #3 印证**：Pod 状态为 CrashLoopBackOff，容器日志中明确指出 `missing required APP_BOOT_MODE` 和 `business config validation failed`，表明配置缺失或格式错误导致启动失败。
- **证据链**：应用缺少关键配置项 APP_BOOT_MODE → 配置校验失败 → 应用启动失败 → 容器被终止 → Pod 重启 → 形成 CrashLoopBackOff 状态。
- **证据 #4 印证**：Pod 标签 `pod_abnormal_type: ConfigError` 与日志中的配置错误信息一致。

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
│ 缺失关键配置项 APP_BOOT_MODE，导致业务配置校验失败              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 应用启动时依赖的配置项缺失 → 配置校验失败 → 应用无法启动        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器因配置错误退出（Exit Code 42）                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 CrashLoopBackOff，持续重启                             │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (CrashLoopBackOff 状态)、证据 #2 (日志中出现 `L4_CONFIG_BOOTSTRAP_FAIL`)、证据 #3 (缺少 `APP_BOOT_MODE`) 和证据 #4 (Pod 标签 `ConfigError`)，问题的根本原因是**应用启动所需的配置项 APP_BOOT_MODE 缺失**，导致配置校验失败，容器无法正常启动。

**置信度**：高 (95%)
- ✅ 日志中明确指出 `missing required APP_BOOT_MODE`
- ✅ Pod 标签表明此为配置错误
- ✅ CrashLoopBackOff 与 Exit Code 42 印证了配置错误

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 注入缺失的环境变量 APP_BOOT_MODE**

```bash
kubectl set env deployment/<deployment_name> -n aiops-e2e APP_BOOT_MODE=your_value
```

*依据*：日志中明确指出 `missing required APP_BOOT_MODE`，需要设置此变量

**2. [可选] 查看容器上次日志**

```bash
kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous
```

*目的*：确认是否还有其他配置缺失或格式问题

### 后续优化

1. **配置检查自动化**：在 CI/CD 流程中增加配置验证步骤，避免缺失关键参数
2. **Pod 自愈机制**：考虑使用 InitContainer 或 livenessProbe 进行启动前配置校验
3. **监控告警**：配置 CrashLoopBackOff 告警，及时发现配置类故障

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |
| 3. 查看容器日志 | `kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e` | 不再出现 L4_CONFIG_BOOTSTRAP_FAIL |

---

## ⚠️ 注意事项

- 如果问题仍持续，建议检查 ConfigMap、Secret 或环境变量是否被正确挂载
- 可以通过 `kubectl describe pod` 查看事件信息，确认配置是否被正确加载
- 考虑增加应用层的配置校验逻辑，避免启动失败

---

## 📊 性能统计

├─ 总耗时: 8.8m
├─ 问题定位: 189.0s (36%) ✅
├─ 证据链采集: 231.8s (44%) ✅
├─ 根因分析: 10.3s (2%) ✅
├─ 汇总总结: 95.5s (18%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 12 次
```

📋 诊断追踪

- **核心 Runbook**: pod-config-error
- **参考 Runbook**: pod-config-error
- **工具调用**: 12 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
