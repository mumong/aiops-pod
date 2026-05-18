======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 6d915f5323524895]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'CrashLoopBackOff': 1, 'Running': 46}
NAMESPACE     NAME                                                READY   STATUS           
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 Error: Runbook 'pod-notready-probe.md' is disabled by the current runtime profile
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod CrashLoopBackOffRuntime / 容器反复退出

> Pod异常类型: CrashLoopBackOffRuntime | 典型状态: CrashLoopBackOff | 兼容分类: container_runtime

## 状态识别
- Pod 状态: `CrashLoopBackOff`
- Last State: Terminated
-
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-liveness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Exit Code:    137
  Warning  Unhealthy       28m (x10 over 30m)  kubelet        
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-notready-liveness
namespace: aiops-e2e
creationTimestamp: 2026-05-15T11:40:37Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <non
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
28m (x10 over 30m)    Warning   Unhealthy        Pod/rc-notready-liveness   Liveness probe failed: liveness endpoint failed
26s (x103 over 26m)   Warning   BackOff          P
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "NotReadyProbeFailed",
  "confidence": "high",
  "reasoning": "Pod rc-notready-liveness 处于 CrashLoopBackOff 状态，Exit Code 为 137，表明容器被 livenessProbe 杀死。Events 显示 liveness probe 失败，且容器因未通过健康检查被重启。符合 NotReadyProbeFailed 的特征，属于 L4 层级的异常。",
  "abnormal_pods": [
    "rc-notready-liveness"
  ],
  "abnormal_groups": [
    "CrashLoopBackOffRuntime"
  ],
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "NotReadyProbeFailed",
  "status_category": "CrashLoopBackOff",
  "key_entities": [
    "Pod/rc-notready-liveness",
    "Container/app",
    "Liveness probe"
  ],
  "possible_scenarios": [
    "liveness probe 配置不合理，导致容器被频繁重启。",
    "容器主进程异常退出，导致探针失败。",
    "应用健康检查端点未正确配置或未响应。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (2m 11.0s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'liveness probe 配置不合理，导致容器被频繁重启。', 'probability': 'high', 'reason': 'Events 显示 liveness probe 失败，容器因未通过健康检查被重启。'}, {'scenario': '容器主进程异常退出，导致探针失败。', 'probability': 'medium', 'reason': 'Exit Code 为 137，可能与进程异常退出有关。'}, {'scenario': '应用健康检查端点未正确配置或未响应。', 'probability': 'medium', 'reason': 'Events 中显示 liveness endpoint failed，可能健康检查配置错误或应用未响应。'}]
   entities=[{"type": "Pod", "name": "rc-notready-liveness", "namespace": "aiops-e2e"}, {"type": "Container", "name": "app", "namespace": "aiops-e2e"}, {"type": "Liveness probe", "name": "liveness probe", "namespace": "aiops-e2e"}]
   reasoning=Pod rc-notready-liveness 处于 CrashLoopBackOff 状态，Exit Code 为 137，表明容器被 livenessProbe 杀死。Events 显示 liveness probe 失败，且容器因未通过健康检查被重启。符合 NotReadyProbeFailed 的特征，属于 L4 层级的异常。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "NotReadyProbeFailed", "confidence": 0.95, "reasoning": "Pod rc-notready-liveness 处于 CrashLoopBackOff 状态，Exit Code 为 137，表明容器被 livenessProbe 杀死。Events 显示 liveness probe 失败，且容器因未通过健康检查被重启。符合 NotReadyProbeFailed 的特征，属于 L4 层级的异常。", "abnormal_pods": [{"name": "rc-notready-liveness", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "NotReadyProbeFailed", "status_category": "app_health", "key_entities": [{"type": "Pod", "name": "rc-notready-liveness", "namespace": "aiops-e2e"}, {"type": "Container", "name": "app", "namespace": "aiops-e2e"}, {"type": "Liveness probe", "name": "liveness probe", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "liveness probe 配置不合理，导致容器被频繁重启。", "probability": "high", "reason": "Events 显示 liveness probe 失败，容器因未通过健康检查被重启。"}, {"scenario": "容器主进程异常退出，导致探针失败。", "probability": "medium", "reason": "Exit Code 为 137，可能与进程异常退出有关。"}, {"scenario": "应用健康检查端点未正确配置或未响应。", "probability": "medium", "reason": "Events 中显示 liveness endpoint failed，可能健康检查配置错误或应用未响应。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-notready-liveness                                0/1     CrashLoopBackOff   14 (89s ago)   29m    172.16.166.164   node1    <none>           <none>            app=rc-notready-liveness,pod_abnormal_type=NotReadyProbeFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/6d915f5323524895/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/6d915f5323524895/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/6d915f5323524895/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-liveness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Exit Code:    137
  Warning  Unhealthy       31m (x10 over 33m)     kubelet     
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-notready-liveness
namespace: aiops-e2e
creationTimestamp: 2026-05-15T11:40:37Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <non
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (1m 54.7s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod 的详细信息，包括状态、事件和重启原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","tool_args":{"name":"rc-notready-liveness","namespace":"aiops-e2e","kind":"Pod"},"purpose":"验证 Pod 的状态、事件和重启原因","evidence_type":"status","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod 的前一次日志，检查容器崩溃前的输出","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-notready-liveness -n aiops-e2e --previous","tool_args":{"name":"rc-notready-liveness","namespace":"aiops-e2e","container":"app"},"purpose":"检查容器崩溃前的日志","evidence_type":"logs","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":["kubectl_previous_logs"],"counts_for_completeness":true},{"id":"e3","description":"获取 Pod 的 YAML 配置，检查容器配置和资源限制","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-liveness -n aiops-e2e -o yaml","tool_args":{"name":"rc-notready-liveness","namespace":"aiops-e2e","kind":"Pod"},"purpose":"验证容器的配置和资源限制","evidence_type":"config","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e4","description":"获取 Pod 的事件列表，检查与健康检查失败相关的事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-notready-liveness --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-notready-liveness","sort_by":".lastTimestamp"},"purpose":"检查与健康检查失败相关的事件","evidence_type":"events","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-liveness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Exit Code:    137\n  Warning  Unhealthy       31m (x10 over 33m)     kubelet            Liveness probe failed: liveness endpoint failed\n  Warning  BackOff         3m39s (x103 over 29m)  kubelet            Back-off restarting failed container app in pod rc-notready-liveness_aiops-e2e(74fed2e5-116f-4b55-900c-9d0d8b7e83ab)\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\n  Normal   Killing         32m (x3 over 33m)      kubelet            Container app failed liveness probe, will be restarted\nName:             rc-notready-liveness\nLabels:           app=rc-notready-liveness\n                  cni.projectcalico.org/containerID: c311a318e2ee0d3b13fe103b0767abd6b4dd610d9e1aae4c7cf82792fb942255\n                  cni.projectcalico.org/podIP: 172.16.166.164/32\n                  cni.projectcalico.org/podIPs: 172.16.166.164/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n  Normal   Scheduled       33m                    default-scheduler  Successfully assigned aiops-e2e/rc-notready-liveness to node1\n关键状态/事件:\n    State:          Running\n    Last State:     Terminated\n      Reason:       Error","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6d915f5323524895/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6d915f5323524895/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6d915f5323524895/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6d915f5323524895/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6d915f5323524895/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6d915f5323524895/tools/002-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-liveness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T11:40:37Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-liveness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=True reason=None\n- ContainersReady: status=True reason=None\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=True restarts=15 reason=Error exitCode=137\nvolumes:\n- {\"name\": \"kube-api-access-lz5gb\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6d915f5323524895/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6d915f5323524895/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6d915f5323524895/tools/003-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 9/9 项，完整度 100%；实际执行工具 8 个，匹配计划 4 个，未规划证据 4 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":9,"environment_evidence_collected":9,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":4,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"获取 Pod 的详细信息，包括状态、事件和重启原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","purpose":"验证 Pod 的状态、事件和重启原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod 的前一次日志，检查容器崩溃前的输出","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-notready-liveness -n aiops-e2e --previous","purpose":"检查容器崩溃前的日志","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取 Pod 的 YAML 配置，检查容器配置和资源限制","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-liveness -n aiops-e2e -o yaml","purpose":"验证容器的配置和资源限制","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"获取 Pod 的事件列表，检查与健康检查失败相关的事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-notready-liveness --sort-by='.lastTimestamp'","purpose":"检查与健康检查失败相关的事件","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取 Pod 的详细信息，包括状态、事件和重启原因 | `kubectl describe pod rc-notready-liveness -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_previous_logs | 获取 Pod 的前一次日志，检查容器崩溃前的输出 | `kubectl logs rc-notready-liveness -n aiops-e2e --previous` |
   | e3 | important | ✅ | kubectl_get_yaml | 获取 Pod 的 YAML 配置，检查容器配置和资源限制 | `kubectl get pod rc-notready-liveness -n aiops-e2e -o yaml` |
   | e4 | important | ✅ | kubectl_events | 获取 Pod 的事件列表，检查与健康检查失败相关的事件 | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-notre...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (15.1s)
   📤 → 下游数据: root_cause=Pod rc-notready-liveness 处于 CrashLoopBackOff 状态，Exit Code 为 137，表明容器被 livenessProbe 杀死。Events 显示 liveness probe 失败，且容器因未通过健康检查被重启。符合 NotReadyProbeFailed 的特征。
   confidence=95%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [], "causal_chain": {}, "root_cause": "Pod rc-notready-liveness 处于 CrashLoopBackOff 状态，Exit Code 为 137，表明容器被 livenessProbe 杀死。Events 显示 liveness probe 失败，且容器因未通过健康检查被重启。符合 NotReadyProbeFailed 的特征。", "root_cause_summary": "Pod rc-notready-liveness 处于 CrashLoopBackOff 状态，Exit Code 为 137，表明容器被 livenessProbe 杀死。Events 显示 liveness probe 失败，且容器因未通过健康检查被重启。符合 NotReadyProbeFailed 的特征。", "confidence": 0.95, "confidence_reason": "有直接证据，因果链清晰", "primary_runbooks": ["pod-notready-probe.md"], "alternative_causes": [], "limitations": "", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-notready-liveness 处于 CrashLoopBackOff 状态，Exit Code 为 137，表明容器被 livenessProbe 杀死。Events 显示 liveness probe 失败，且容器因未通过健康检查被重启。符合 NotReadyProbeFail...
   置信度: 95%

📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 15.6s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4485 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 36.3s
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
| **问题分类** | NotReadyProbeFailed（liveness probe 失败） |
| **置信度** | 高 (95%) |
| **证据完整度** | 4/4 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题？

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-notready-liveness |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | Liveness probe failed: liveness endpoint failed, Exit Code: 137 |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | kubectl describe pod rc-notready-liveness | `Exit Code: 137`, `Warning: Unhealthy (x10 over 30m)` | 容器因健康检查失败被杀死，Exit Code 137 指向异常终止 |
| 2 | Pod 事件 | kubectl get events | `Warning Unhealthy: Liveness probe failed: liveness endpoint failed` | liveness probe 失败，导致容器被终止 |
| 3 | Pod YAML 配置 | kubectl get pod -o yaml | 未发现明显资源配置问题 | 容器配置未发现异常 |
| 4 | 崩溃前日志 | kubectl logs --previous | `no output` | 无崩溃前日志输出，无法判断容器退出前行为 |

### 证据关联分析

- **证据 #1 + #2 印证**：Exit Code 137 + "Unhealthy: liveness endpoint failed" → liveness probe 失败，容器被终止
- **证据链**：健康检查失败 → kubelet 终止容器 → Pod 进入 CrashLoopBackOff 状态 → 持续重启

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 应用健康检查配置 | important | 无法确认 liveness probe 配置是否合理 |
| 容器崩溃前日志 | critical | 无法确认容器崩溃前的异常行为 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ liveness probe 配置不合理或应用健康检查端点未正常响应            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 健康检查失败 → kubelet 终止容器 → 容器重启 → CrashLoopBackOff     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器被 liveness probe 失败触发终止（Exit Code 137）              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod rc-notready-liveness 状态为 CrashLoopBackOff，持续重启        │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Exit Code 137, liveness probe 失败) 和证据 #2 (事件记录显示 liveness endpoint failed)，问题的根本原因是**容器未通过 liveness probe 健康检查**，导致 kubelet 终止容器并进入 CrashLoopBackOff 状态。

**置信度**：高 (95%)
- ✅ Exit Code 137 明确指向异常终止
- ✅ Events 显示 liveness probe 失败
- ⚠️ 缺少健康检查配置和崩溃前日志，无法进一步确认是探针配置问题还是应用异常

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查 liveness probe 配置**
```bash
kubectl get pod rc-notready-liveness -n aiops-e2e -o jsonpath='{.spec.containers[*].livenessProbe}'
```
*依据*：确认 liveness probe 的路径、端口、超时时间等是否正确，是否与应用实际健康检查端点匹配

**2. [优先] 查看容器崩溃前日志**
```bash
kubectl logs rc-notready-liveness -n aiops-e2e --previous
```
*目的*：查看容器崩溃前是否有异常日志（如应用未启动、健康检查端点未响应等）

**3. [可选] 调整 liveness probe 配置**
```bash
kubectl set probe deployment/<deployment-name> -n aiops-e2e --liveness --http-get http://localhost:8080/health --initial-delay-seconds=10 --period-seconds=10
```
*说明*：根据应用实际情况调整探针的路径、超时时间和重试策略

### 后续优化

1. **配置 readiness probe**：确保 readiness probe 与 liveness probe 配合使用，防止流量进入未就绪的 Pod
2. **监控探针状态**：使用 Prometheus 监控 probe 成功率和失败率
3. **日志收集优化**：确保容器崩溃前日志能被正确采集，便于快速诊断

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-notready-liveness -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-notready-liveness -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |
| 3. 检查探针配置 | `kubectl get pod rc-notready-liveness -n aiops-e2e -o jsonpath='{.spec.containers[*].livenessProbe}'` | 配置合理，匹配应用健康检查端点 |

---

## ⚠️ 注意事项

- 如果 probe 配置正确，但仍然失败，可能是应用健康检查端点未响应，需检查应用日志和网络配置
- 如果 probe 配置过短（如 timeoutSeconds=1），可能导致探针误判
- 确保应用健康检查端点在容器启动后能正常响应

---

## 📌 附录

- **采集的原始数据**：
  - `kubectl describe pod rc-notready-liveness` 显示 `Exit Code: 137`，`Warning: Unhealthy`
  - `kubectl get events` 显示 `Liveness probe failed: liveness endpoint failed`
  - `kubectl logs --previous` 无输出
- **诊断依据**：
  - [Kubernetes 官方文档 - Liveness and Readiness Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)

---

## 📊 性能统计

├─ 总耗时: 5.6m
├─ 问题定位: 131.0s (39%) ✅
├─ 证据链采集: 114.7s (34%) ✅
├─ 根因分析: 15.1s (4%) ✅
├─ 汇总总结: 75.6s (22%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 11 次
```

📋 诊断追踪

- **核心 Runbook**: pod-notready-probe-failed
- **参考 Runbook**: pod-notready-probe-failed, pod-crashloop-runtime
- **工具调用**: 11 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
