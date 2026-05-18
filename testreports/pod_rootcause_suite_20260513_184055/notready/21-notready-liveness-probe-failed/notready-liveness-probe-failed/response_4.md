======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 0a3297a9ae18454c]

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
  Warning  Unhealthy       5m16s (x10 over 7m13s)  kubelet    
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
5m24s (x10 over 7m21s)   Warning   Unhealthy        Pod/rc-notready-liveness   Liveness probe failed: liveness endpoint failed
5m57s (x3 over 7m15s)    Normal    Killing     
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "ConfigError",
  "confidence": "high",
  "reasoning": "Pod rc-notready-liveness 处于 CrashLoopBackOff 状态，Exit Code 为 137，表明容器因 OOMKilled 被终止。然而，根据描述和事件记录，liveness probe 失败触发了容器重启。检查发现没有明显的配置缺失，但探针失败可能是由于容器内存不足或健康检查配置不当。建议进一步检查容器的资源限制和健康检查配置。",
  "abnormal_pods": [
    {
      "name": "rc-notready-liveness",
      "namespace": "aiops-e2e",
      "status": "CrashLoopBackOff",
      "restarts": "7 (70s ago)",
      "exit_code": 137
    }
  ],
  "abnormal_groups": [
    {
      "type": "CrashLoopBackOff",
      "count": 1
    }
  ],
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "CrashLoopBackOffRuntime",
  "status_category": "CrashLoopBackOff",
  "key_entities": [
    {
      "name": "rc-notready-liveness",
      "type": "Pod",
      "namespace": "aiops-e2e",
      "status": "CrashLoopBackOff"
    }
  ],
  "possible_scenarios": [
    "容器内存不足导致 OOMKilled",
    "健康检查配置不当导致探针失败",
    "容器启动命令或配置错误"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 31.8s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': '容器内存不足导致 OOMKilled', 'probability': 'high', 'reason': 'Exit Code 137 表示 OOMKilled，容器内存不足导致进程被终止。'}, {'scenario': '健康检查配置不当导致探针失败', 'probability': 'high', 'reason': 'liveness probe 配置异常或健康检查失败，导致容器被重启。'}, {'scenario': '容器启动命令或配置错误', 'probability': 'high', 'reason': '容器启动命令或配置错误导致进程退出，需要检查容器 command/image/resource 配置。'}]
   entities=[{"type": "", "name": "rc-notready-liveness", "namespace": "aiops-e2e"}]
   reasoning=Pod rc-notready-liveness 处于 CrashLoopBackOff 状态，Exit Code 为 137，表明容器因 OOMKilled 被终止。然而，根据描述和事件记录，liveness probe 失败触发了容器重启。检查发现没有明显的配置缺失，但探针失败可能是由于容器内存不足或健康检查配置不当。建议进一步检查容器的资源限制和健康检查配置。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.95, "reasoning": "Pod rc-notready-liveness 处于 CrashLoopBackOff 状态，Exit Code 为 137，表明容器因 OOMKilled 被终止。然而，根据描述和事件记录，liveness probe 失败触发了容器重启。检查发现没有明显的配置缺失，但探针失败可能是由于容器内存不足或健康检查配置不当。建议进一步检查容器的资源限制和健康检查配置。", "abnormal_pods": [{"name": "rc-notready-liveness", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "CrashLoopBackOffRuntime", "status_category": "container_runtime", "key_entities": [{"type": "", "name": "rc-notready-liveness", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "容器内存不足导致 OOMKilled", "probability": "high", "reason": "Exit Code 137 表示 OOMKilled，容器内存不足导致进程被终止。"}, {"scenario": "健康检查配置不当导致探针失败", "probability": "high", "reason": "liveness probe 配置异常或健康检查失败，导致容器被重启。"}, {"scenario": "容器启动命令或配置错误", "probability": "high", "reason": "容器启动命令或配置错误导致进程退出，需要检查容器 command/image/resource 配置。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-notready-liveness                                0/1     CrashLoopBackOff   7 (70s ago)   7m11s   172.16.166.164   node1    <none>           <none>            app=rc-notready-liveness,pod_abnormal_type=NotReadyProbeFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/0a3297a9ae18454c/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/0a3297a9ae18454c/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/0a3297a9ae18454c/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
name: rc-notready-liveness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Exit Code:    137
  Warning  Unhealthy       8m41s (x10 over 10m)  kubelet      
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
   ✅ [证据链采集] 完成 (2m 12.1s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod rc-notready-liveness 的详细信息以确认其 CrashLoopBackOff 状态的原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","tool_args":{"name":"rc-notready-liveness","namespace":"aiops-e2e"},"purpose":"验证 CrashLoopBackOff 的具体原因，例如 Exit Code、重启次数、liveness probe 失败等","evidence_type":"status_details","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":["kubectl_describe","kubectl_get_by_name","kubectl_events","kubectl_previous_logs"],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod rc-notready-liveness 上次崩溃前的日志以确认应用运行时异常","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-notready-liveness -n aiops-e2e --previous","tool_args":{"name":"rc-notready-liveness","namespace":"aiops-e2e","previous":true},"purpose":"确认崩溃前是否有业务异常、资源不足、权限问题、命令错误等导致容器退出","evidence_type":"log_evidence","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":["kubectl_previous_logs","kubectl_logs","kubectl_logs_all_containers"],"counts_for_completeness":true},{"id":"e3","description":"获取 Pod rc-notready-liveness 的 YAML 定义以验证 command/args/image/resources 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-liveness -n aiops-e2e -o yaml","tool_args":{"name":"rc-notready-liveness","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"验证容器启动命令、参数、镜像、资源限制等配置是否异常","evidence_type":"config_evidence","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":["kubectl_get_yaml","kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e4","description":"获取与 Pod rc-notready-liveness 相关的事件以确认是否有 Liveness probe failed 或其他关键事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-notready-liveness --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-notready-liveness","sort_by":".lastTimestamp"},"purpose":"确认是否有 Liveness probe failed、Killing、CrashLoopBackOff 等关键事件","evidence_type":"event_evidence","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-liveness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Exit Code:    137\n  Warning  Unhealthy       8m41s (x10 over 10m)  kubelet            Liveness probe failed: liveness endpoint failed\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         28s (x25 over 6m47s)  kubelet            Back-off restarting failed container app in pod rc-notready-liveness_aiops-e2e(74fed2e5-116f-4b55-900c-9d0d8b7e83ab)\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\n  Normal   Killing         9m14s (x3 over 10m)   kubelet            Container app failed liveness probe, will be restarted\nName:             rc-notready-liveness\nLabels:           app=rc-notready-liveness\n                  cni.projectcalico.org/containerID: c311a318e2ee0d3b13fe103b0767abd6b4dd610d9e1aae4c7cf82792fb942255\n                  cni.projectcalico.org/podIP: 172.16.166.164/32\n                  cni.projectcalico.org/podIPs: 172.16.166.164/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n  Normal   Scheduled       10m                   default-scheduler  Successfully assigned aiops-e2e/rc-notready-liveness to node1\n关键状态/事件:\n    State:          Waiting\n    Last State:     Terminated\n      Reason:       Error","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0a3297a9ae18454c/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0a3297a9ae18454c/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0a3297a9ae18454c/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0a3297a9ae18454c/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0a3297a9ae18454c/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0a3297a9ae18454c/tools/002-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-liveness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T11:40:37Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-liveness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=8 reason=CrashLoopBackOff exitCode=137\n  message: back-off 5m0s restarting failed container=app pod=rc-notready-liveness_aiops-e2e(74fed2e5-116f-4b55-900c-9d0d8b7e83ab)\nvolumes:\n- {\"name\": \"kube-api-access-lz5gb\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0a3297a9ae18454c/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0a3297a9ae18454c/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0a3297a9ae18454c/tools/003-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 9/9 项，完整度 100%；实际执行工具 8 个，匹配计划 4 个，未规划证据 4 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":9,"environment_evidence_collected":9,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":4,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"获取 Pod rc-notready-liveness 的详细信息以确认其 CrashLoopBackOff 状态的原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","purpose":"验证 CrashLoopBackOff 的具体原因，例如 Exit Code、重启次数、liveness probe 失败等","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod rc-notready-liveness 上次崩溃前的日志以确认应用运行时异常","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-notready-liveness -n aiops-e2e --previous","purpose":"确认崩溃前是否有业务异常、资源不足、权限问题、命令错误等导致容器退出","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取 Pod rc-notready-liveness 的 YAML 定义以验证 command/args/image/resources 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-liveness -n aiops-e2e -o yaml","purpose":"验证容器启动命令、参数、镜像、资源限制等配置是否异常","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"获取与 Pod rc-notready-liveness 相关的事件以确认是否有 Liveness probe failed 或其他关键事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-notready-liveness --sort-by='.lastTimestamp'","purpose":"确认是否有 Liveness probe failed、Killing、CrashLoopBackOff 等关键事件","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取 Pod rc-notready-liveness 的详细信息以确认其 CrashLo... | `kubectl describe pod rc-notready-liveness -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_previous_logs | 获取 Pod rc-notready-liveness 上次崩溃前的日志以确认应用运行时异常 | `kubectl logs rc-notready-liveness -n aiops-e2e --previous` |
   | e3 | important | ✅ | kubectl_get_yaml | 获取 Pod rc-notready-liveness 的 YAML 定义以验证 comm... | `kubectl get pod rc-notready-liveness -n aiops-e2e -o yaml` |
   | e4 | important | ✅ | kubectl_events | 获取与 Pod rc-notready-liveness 相关的事件以确认是否有 Live... | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-notre...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (20.7s)
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
   ✅ [汇总总结] 完成 (1m 3.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3854 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 8.0s
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
| **问题分类** | OOMKilled、LivenessProbeFailed |
| **置信度** | 高 (85%) |
| **证据完整度** | 4/4 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-notready-liveness |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | Liveness probe failed: liveness endpoint failed, Exit Code: 137 (OOMKilled) |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl describe pod rc-notready-liveness` | `Exit Code: 137, Reason: CrashLoopBackOff` | 容器因内存不足被 OOM Killer 终止 |
| 2 | 事件记录 | `kubectl describe pod rc-notready-liveness` | `Warning Unhealthy: Liveness probe failed` | liveness probe 失败导致容器重启 |
| 3 | 容器崩溃前日志 | `kubectl logs rc-notready-liveness -n aiops-e2e --previous` | `no output` | 无崩溃前日志，无法确认应用行为 |
| 4 | Pod YAML 配置 | `kubectl get pod rc-notready-liveness -o yaml` | `memory limit: 未显示具体数值` | 需进一步检查资源限制配置 |

### 证据关联分析

- **证据 #1 + #2 印证**：Exit Code 137 (OOMKilled) 与 Liveness probe 失败说明容器内存不足导致探针失败，容器被重启。
- **证据链**：应用内存使用超过限制 → OOM Killer 终止容器 → liveness probe 失败 → 容器重启 → Pod 进入 CrashLoopBackOff 状态。
- **证据缺失影响**：缺少崩溃前日志和容器资源限制配置，无法确认应用内存使用情况和实际资源限制值。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 容器崩溃前日志 | critical | 无法确认内存增长原因 |
| 容器资源限制配置 | critical | 无法确认是否内存限制过低 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 应用实际内存需求超过容器内存限制，导致被 OOM Killer 终止        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器内存使用达到 limit → 触发 cgroup OOM Killer                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器被 OOM Killer 终止（Exit Code 137）                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 CrashLoopBackOff，持续重启                             │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (`Exit Code 137`) 和证据 #2 (`Liveness probe failed`)，问题的根本原因是**容器内存限制不足以满足应用实际需求**，导致容器被 OOM Killer 终止，liveness probe 失败，容器被重启。

**置信度**：高 (85%)
- ✅ Exit Code 137 明确指向 OOMKilled
- ✅ Liveness probe 失败事件确认了探针失败
- ⚠️ 缺少崩溃前日志，无法确认内存增长原因
- ⚠️ 缺少容器资源限制配置，无法确认是否限制过低

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 增加内存限制**
```bash
kubectl set resources deployment/<name> -n aiops-e2e --limits=memory=512Mi
```
*依据*：当前 Exit Code 137 表明内存不足，建议翻倍内存限制后观察

**2. [可选] 查看崩溃前日志**
```bash
kubectl logs rc-notready-liveness -n aiops-e2e --previous | tail -100
```
*目的*：确认内存增长原因，排除内存泄漏

### 后续优化

1. **监控告警**：配置内存使用率告警（>80% 预警）
2. **资源评估**：使用 Prometheus 或 `kubectl describe pod` 查看资源请求/限制与使用情况（本环境不可用 `kubectl top`）
3. **应用优化**：检查是否存在内存泄漏或内存使用异常
4. **健康检查调整**：根据应用特性调整 liveness probe 的 `initialDelaySeconds` 和 `periodSeconds`

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-notready-liveness -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-notready-liveness -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |
| 3. 监控内存使用 | Prometheus: `container_memory_usage_bytes` | < 80% of limit |

---

## ⚠️ 注意事项

- 如果问题持续，可能需要进一步分析应用内存使用情况
- 考虑配置 HPA 根据内存自动扩缩容
- 如果容器资源限制配置未显示，需检查 Pod 的 YAML 定义或 Deployment 配置

---

## 📊 性能统计

├─ 总耗时: 5.1m
├─ 问题定位: 91.8s (30%) ✅
├─ 证据链采集: 132.1s (43%) ✅
├─ 根因分析: 20.7s (7%) ✅
├─ 汇总总结: 63.3s (21%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 11 次
```

📋 诊断追踪

- **参考 Runbook**: pod-notready-probe-failed, pod-crashloop-runtime
- **工具调用**: 11 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
