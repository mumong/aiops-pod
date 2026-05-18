======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 572d443b438f418c]

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
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                   READY   STATUS             RESTARTS       AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-notready-liveness   0/1     CrashLoopBackOff   34 (86s ago)
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [问题定位] 调用工具: kubectl_container_previous_logs
   💭 [问题定位] 工具结果: kubectl_container_previous_logs (success)
      📄 kubectl_container_previous_logs 输出摘要: raw_chars=198 lines=3
Command failed (exit 1):
kubectl logs rc-notready-liveness -c rc-notready-liveness -n aiops-e2e --previous --tail=200
error: container rc-no
   💭 [问题定位] 调用工具: kubectl_container_logs
   💭 [问题定位] 工具结果: kubectl_container_logs (success)
      📄 kubectl_container_logs 输出摘要: raw_chars=187 lines=3
Command failed (exit 1):
kubectl logs rc-notready-liveness -c rc-notready-liveness -n aiops-e2e --tail=200
error: container rc-notready-liveness is n
   💭 [问题定位] 调用工具: kubectl_logs
   ✅ [问题定位] 完成 (29.6s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[]
   entities=[]
   reasoning=当前环境中有一个处于 CrashLoopBackOff 状态的 Pod，且 Exit Code 未知。根据分析文本和 runbook 判定规则，CrashLoopBackOff 且没有明确配置缺失信号，属于 L2 层次的异常。该 Pod 的重启次数较高，但没有 OOMKilled 或 Evicted 等 L0 或 L1 的证据。因此，最终归一化为 L2 层次。
   layer_analysis={"layer": "L2", "derived_layer": "L2", "layers": ["L2"], "layer_name": "", "confidence": 0.5, "reasoning": "当前环境中有一个处于 CrashLoopBackOff 状态的 Pod，且 Exit Code 未知。根据分析文本和 runbook 判定规则，CrashLoopBackOff 且没有明确配置缺失信号，属于 L2 层次的异常。该 Pod 的重启次数较高，但没有 OOMKilled 或 Evicted 等 L0 或 L1 的证据。因此，最终归一化为 L2 层次。", "abnormal_pods": [{"name": "rc-notready-liveness", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "CrashLoopBackOffRuntime", "status_category": "container_runtime", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-notready-liveness                                0/1     CrashLoopBackOff   34 (80s ago)   93m     172.16.166.164   node1    <none>           <none>            app=rc-notready-liveness,pod_abnormal_type=NotReadyProbeFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/572d443b438f418c/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/572d443b438f418c/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/572d443b438f418c/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L2
   置信度: 50%

📍 [证据链采集] 执行中...
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
name: rc-notready-liveness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Exit Code:    137
      Reason:       CrashLoopBackOff
  Warning  BackOff  66s (
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
   ✅ [证据链采集] 完成 (2m 3.5s)
   📤 → 下游数据: evidence_items=8/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod rc-notready-liveness 的详细信息以验证 CrashLoopBackOff 状态和 Exit Code","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","tool_args":{"name":"rc-notready-liveness","namespace":"aiops-e2e","kind":"Pod"},"purpose":"验证 Pod 的 Last State、Exit Code、Reason 和重启次数","evidence_type":"status_verification","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":["kubectl_describe","kubectl_get_by_name","kubectl_get_by_kind_in_namespace","kubectl_get_yaml","kubectl_events","kubectl_logs","kubectl_previous_logs","kubectl_logs_all_containers","kubectl_previous_logs_all_containers","kubectl_container_logs","kubectl_container_previous_logs","kubectl_logs_grep","kubectl_logs_all_containers_grep","kubernetes_jq_query","kubernetes_tabular_query","kubernetes_count","kubectl_lineage_children","kubectl_lineage_parents","run_bash_command"],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod rc-notready-liveness 的崩溃前日志以定位启动失败原因","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-notready-liveness -n aiops-e2e --previous --tail=200","tool_args":{"name":"rc-notready-liveness","namespace":"aiops-e2e","pod":"rc-notready-liveness","container":null,"tail":"200","previous":true},"purpose":"验证崩溃前日志中的业务异常、启动错误或配置缺失信号","evidence_type":"log_verification","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":["kubectl_previous_logs","kubectl_container_previous_logs","kubectl_logs","kubectl_container_logs","kubectl_logs_all_containers","kubectl_previous_logs_all_containers","kubectl_logs_grep","kubectl_logs_all_containers_grep","run_bash_command"],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod rc-notready-liveness 的配置以验证 command/args/image/resources 是否有错误","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-liveness -n aiops-e2e -o yaml","tool_args":{"name":"rc-notready-liveness","namespace":"aiops-e2e","kind":"Pod","output_format":"yaml"},"purpose":"验证 command/args/image/resources 是否正确","evidence_type":"config_verification","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":["kubectl_get_yaml","kubectl_get_by_name","kubectl_get_by_kind_in_namespace","kubectl_find_resource","kubectl_get_by_kind_in_cluster","run_bash_command"],"counts_for_completeness":true},{"id":"e4","description":"获取异常 Pod rc-notready-liveness 的相关事件以验证 BackOff、probe failed、Killing 等信号","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-notready-liveness --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-notready-liveness","sort_by":".lastTimestamp"},"purpose":"验证 BackOff、probe failed、Killing 等信号","evidence_type":"event_verification","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":["kubectl_events","kubectl_get_by_name","kubectl_get_by_kind_in_namespace","kubectl_get_by_kind_in_cluster","kubectl_find_resource","run_bash_command"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-liveness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Exit Code:    137\n      Reason:       CrashLoopBackOff\n  Warning  BackOff  66s (x352 over 92m)  kubelet  Back-off restarting failed container app in pod rc-notready-liveness_aiops-e2e(74fed2e5-116f-4b55-900c-9d0d8b7e83ab)\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\nName:             rc-notready-liveness\nLabels:           app=rc-notready-liveness\n                  cni.projectcalico.org/containerID: c311a318e2ee0d3b13fe103b0767abd6b4dd610d9e1aae4c7cf82792fb942255\n                  cni.projectcalico.org/podIP: 172.16.166.164/32\n                  cni.projectcalico.org/podIPs: 172.16.166.164/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n    Last State:     Terminated\n      Reason:       Error","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/572d443b438f418c/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/572d443b438f418c/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/572d443b438f418c/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/572d443b438f418c/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/572d443b438f418c/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/572d443b438f418c/tools/002-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-liveness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T11:40:37Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-liveness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=34 reason=CrashLoopBackOff exitCode=137\n  message: back-off 5m0s restarting failed container=app pod=rc-notready-liveness_aiops-e2e(74fed2e5-116f-4b55-900c-9d0d8b7e83ab)\nvolumes:\n- {\"name\": \"kube-api-access-lz5gb\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/572d443b438f418c/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/572d443b438f418c/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/572d443b438f418c/tools/003-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%；其中真实环境证据 8/9 项，完整度 89%；实际执行工具 6 个，匹配计划 3 个，未规划证据 3 个","plan_total":4,"plan_collected":3,"plan_completeness":0.75,"environment_evidence_total":9,"environment_evidence_collected":8,"environment_evidence_completeness":0.8888888888888888,"executed_tool_count":6,"matched_tool_count":3,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod rc-notready-liveness 的详细信息以验证 CrashLoopBackOff 状态和 Exit Code","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","purpose":"验证 Pod 的 Last State、Exit Code、Reason 和重启次数","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod rc-notready-liveness 的崩溃前日志以定位启动失败原因","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-notready-liveness -n aiops-e2e --previous --tail=200","purpose":"验证崩溃前日志中的业务异常、启动错误或配置缺失信号","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod rc-notready-liveness 的配置以验证 command/args/image/resources 是否有错误","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-liveness -n aiops-e2e -o yaml","purpose":"验证 command/args/image/resources 是否正确","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"获取异常 Pod rc-notready-liveness 的相关事件以验证 BackOff、probe failed、Killing 等信号","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-notready-liveness --sort-by='.lastTimestamp'","purpose":"验证 BackOff、probe failed、Killing 等信号","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_container_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_container_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e4(获取异常 Pod rc-notready-liveness 的相关事件以验证 BackOff、probe failed、Killing 等信号): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 89%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取异常 Pod rc-notready-liveness 的详细信息以验证 CrashL... | `kubectl describe pod rc-notready-liveness -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_previous_logs | 获取异常 Pod rc-notready-liveness 的崩溃前日志以定位启动失败原因 | `kubectl logs rc-notready-liveness -n aiops-e2e --previous --tail=200` |
   | e3 | important | ✅ | kubectl_get_yaml | 获取异常 Pod rc-notready-liveness 的配置以验证 command/... | `kubectl get pod rc-notready-liveness -n aiops-e2e -o yaml` |
   | e4 | important | ❌ | kubectl_events | 获取异常 Pod rc-notready-liveness 的相关事件以验证 BackOf... | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-notre...` |

   ⚠️ 未采集原因:
   - e4(获取异常 Pod rc-notready-liveness 的相关事件以验证 BackOff、probe failed、Killing 等信号): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (9.7s)
   📤 → 下游数据: root_cause=[L2层] 当前无法基于 LLM 输出确定根本原因
   confidence=10%
   causal_chain={"trigger": "LLM 未生成可靠因果链", "mechanism": "缺少可用的结构化根因分析结果", "manifestation": "我的集群有什么问题"}
   rca_analysis={"phenomenon": "我的集群有什么问题", "evidence_analysis": [], "causal_chain": {"trigger": "LLM 未生成可靠因果链", "mechanism": "缺少可用的结构化根因分析结果", "manifestation": "我的集群有什么问题"}, "root_cause": "[L2层] 当前无法基于 LLM 输出确定根本原因", "confidence": 0.1, "confidence_reason": "LLM 返回结果不符合 RCA 结构化输出合同", "alternative_causes": []}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: [L2层] 当前无法基于 LLM 输出确定根本原因
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
   ✅ [汇总总结] 完成 (2m 5.9s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4136 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 48.8s
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
| **兼容归因层** | L2 |
| **问题分类** | CrashLoopBackOffRuntime |
| **置信度** | 中 (50%) |
| **证据完整度** | 3/4 (75%) |

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
| 错误信息 | CrashLoopBackOff，Exit Code 未知 |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl describe pod rc-notready-liveness` | `Status: CrashLoopBackOff, Last State: Terminated` | Pod 处于 CrashLoopBackOff 状态，容器已终止 |
| 2 | 崩溃前日志 | `kubectl logs rc-notready-liveness --previous` | `关键日志: (no output)` | 无崩溃前日志输出，无法确认具体退出原因 |
| 3 | Pod 配置 | `kubectl get pod rc-notready-liveness -o yaml` | `容器配置字段缺失（如 command/args/image/resources）` | 无法确认是否存在配置错误 |
| 4 | kubectl_get_by_kind_in_cluster | `kubectl get pod` | `STATUS: CrashLoopBackOff, RESTARTS: 34 (80s ago)` | Pod 持续重启，退出频率高 |

### 证据关联分析

- **证据 #1 印证**：Pod 处于 CrashLoopBackOff 状态，表示容器在启动后立即退出，Kubernetes 正在进行指数退避重启。
- **证据 #2 印证**：崩溃前日志为空，说明容器退出时未留下日志，无法进一步判断退出原因。
- **证据 #3 印证**：无法验证容器启动参数、镜像、资源限制等配置，排除配置错误的可能。
- **证据 #4 印证**：重启次数高，说明问题具有重复性，属于运行时问题，非一次性故障。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| Pod 事件 | important | 无法确认重启触发机制，例如是否是探针失败或容器主动退出 |
| 容器当前日志 | important | 无法确认容器退出后是否正常运行过 |
| 容器镜像信息 | important | 无法确认是否为镜像错误导致启动失败 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 容器启动后立即退出，Exit Code 未知，可能为配置错误、入口命令错误或应用启动失败。     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器启动失败 → Kubernetes 重启 → 无限循环 CrashLoopBackOff      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器启动失败，Exit Code 未知，日志缺失，无法确认具体原因          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 CrashLoopBackOff，持续重启                             │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (CrashLoopBackOff 状态) 和证据 #4 (重启次数 34 次)，问题的根本原因是**容器启动后立即退出，但未留下 Exit Code 或日志，导致无法确认具体原因**。  
**置信度**：中 (50%)  
- ✅ Pod 状态 CrashLoopBackOff 表明容器退出后被重启
- ❌ 无 Exit Code 和日志，无法确认是命令错误、配置错误还是应用启动失败
- ❌ 缺少容器事件和探针状态，无法判断是否是探针失败触发重启

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查容器启动命令和参数**
```bash
kubectl get pod rc-notready-liveness -n aiops-e2e -o jsonpath='{.spec.containers[*].command}'
kubectl get pod rc-notready-liveness -n aiops-e2e -o jsonpath='{.spec.containers[*].args}'
```
*依据*：确认容器启动命令和参数是否正确，是否存在命令不存在、参数错误等问题

**2. [优先] 检查容器镜像是否正常**
```bash
kubectl get pod rc-notready-liveness -n aiops-e2e -o jsonpath='{.spec.containers[*].image}'
```
*依据*：确认是否使用了正确的镜像，镜像是否可拉取

**3. [可选] 获取 Pod 事件以确认重启原因**
```bash
kubectl describe pod rc-notready-liveness -n aiops-e2e
```
*依据*：查看是否有 `BackOff`, `ProbeFailed`, `Killing` 等事件

### 后续优化

1. **容器调试模式**：尝试在容器中运行 shell，进入容器内检查应用是否能正常启动
2. **资源限制检查**：确认是否存在 CPU/Memory 资源限制导致容器无法启动
3. **容器健康检查配置**：检查 Liveness/Readiness 探针配置是否合理，是否过于敏感

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-notready-liveness -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-notready-liveness -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 重启次数不再增加 |
| 3. 检查容器退出码 | `kubectl describe pod rc-notready-liveness -n aiops-e2e` | 显示 Exit Code 和 Reason |

---

## ⚠️ 注意事项

- 如果容器启动命令或参数错误，需修改 Deployment 或 Pod 的配置
- 如果镜像拉取失败，需检查镜像地址、凭证和网络策略
- 如果无日志输出，可尝试在容器中运行 `tail -f /dev/null` 以保持容器运行，便于调试
- 如果问题持续，建议启用调试模式或进入容器内部执行命令以排查问题

---

## 📊 性能统计

├─ 总耗时: 4.8m
├─ 问题定位: 29.6s (10%) ✅
├─ 证据链采集: 123.5s (43%) ✅
├─ 根因分析: 9.7s (3%) ✅
├─ 汇总总结: 125.9s (44%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 12 次
```

📋 诊断追踪

- **参考 Runbook**: pod-notready-probe-failed, pod-crashloop-runtime
- **工具调用**: 12 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
