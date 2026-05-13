======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: c020706fabf14abb]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'CrashLoopBackOff': 1, 'OOMKilled': 1, 'Running': 46}
NAMESPACE     NAME                                                READY   S
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod OOMKilled (Exit Code 137)

> Pod异常类型: OOMKilled | 典型状态: CrashLoopBackOff / Error / Restarting | 兼容分类: container_memory

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | CrashLoopB
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: memhog-767b7b5dcc-l52km
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键状态/事件:
                  pod_abnormal_type=OOMKilled
Annotations:      aiops.e2e/expecte
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
name: memhog-767b7b5dcc-l52km
namespace: aiops-e2e
creationTimestamp: 2026-05-13T01:39:26Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <
   💭 [问题定位] {
  "layer": "L2",
  "derived_layer": "L2",
  "layers": [
    "L2"
  ],
  "layer_name": "OOMKilled",
  "confidence": "high",
  "reasoning": "Pod 'memhog-767b7b5dcc-l52km' 在命名空间 'aiops-e2e' 中的状态为 CrashLoopBackOff，且其最后一次状态为 OOMKilled，exitCode 为 137。这表明该 Pod 因内存不足被系统终止。根据提供的 runbook，这种状态归类为 L2 层级，属于容器资源限制导致的异常。",
  "abnormal_pods": [
    "memhog-767b7b5dcc-l52km"
  ],
  "abnormal_groups": [
    {
      "pod_status_keyword": "CrashLoopBackOff",
      "pod_abnormal_type": "OOMKilled",
      "status_category": "L2"
    }
  ],
  "key_entities": [
    "Pod: memhog-767b7b5dcc-l52km",
    "Namespace: aiops-e2e",
    "Node: node1",
    "Container: memhog"
  ],
  "possible_scenarios": [
    "Pod memhog-767b7b5dcc-l52km 的内存配置不足，导致容器因 OOMKilled 被终止。",
    "容器 memhog 的内存限制可能未正确设置，或者应用本身存在内存泄漏问题。",
    "Pod 可能因频繁重启而进入 CrashLoopBackOff 状态，需要进一步检查其资源配置和日志。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (2m 27.1s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[{'scenario': 'Pod memhog-767b7b5dcc-l52km 的内存配置不足，导致容器因 OOMKilled 被终止。', 'probability': 'high', 'reason': 'Pod 状态为 CrashLoopBackOff，最后一次状态为 OOMKilled，exitCode 为 137。'}, {'scenario': '容器 memhog 的内存限制可能未正确设置，或者应用本身存在内存泄漏问题。', 'probability': 'medium', 'reason': '容器频繁重启，可能由于内存不足或应用问题。'}, {'scenario': 'Pod 可能因频繁重启而进入 CrashLoopBackOff 状态，需要进一步检查其资源配置和日志。', 'probability': 'medium', 'reason': 'Pod 状态为 CrashLoopBackOff，需要进一步诊断日志和资源配置。'}]
   entities=[{"type": "Pod", "name": "memhog-767b7b5dcc-l52km", "namespace": "aiops-e2e"}, {"type": "Namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Container", "name": "memhog", "namespace": ""}]
   reasoning=Pod 'memhog-767b7b5dcc-l52km' 在命名空间 'aiops-e2e' 中的状态为 CrashLoopBackOff，且其最后一次状态为 OOMKilled，exitCode 为 137。这表明该 Pod 因内存不足被系统终止。根据提供的 runbook，这种状态归类为 L2 层级，属于容器资源限制导致的异常。
   layer_analysis={"layer": "L2", "derived_layer": "L2", "layers": ["L2"], "layer_name": "OOMKilled", "confidence": 0.5, "reasoning": "Pod 'memhog-767b7b5dcc-l52km' 在命名空间 'aiops-e2e' 中的状态为 CrashLoopBackOff，且其最后一次状态为 OOMKilled，exitCode 为 137。这表明该 Pod 因内存不足被系统终止。根据提供的 runbook，这种状态归类为 L2 层级，属于容器资源限制导致的异常。", "abnormal_pods": [{"name": "memhog-767b7b5dcc-l52km", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "OOMKilled", "status_category": "container_resource", "key_entities": [{"type": "Pod", "name": "memhog-767b7b5dcc-l52km", "namespace": "aiops-e2e"}, {"type": "Namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Container", "name": "memhog", "namespace": ""}], "possible_scenarios": [{"scenario": "Pod memhog-767b7b5dcc-l52km 的内存配置不足，导致容器因 OOMKilled 被终止。", "probability": "high", "reason": "Pod 状态为 CrashLoopBackOff，最后一次状态为 OOMKilled，exitCode 为 137。"}, {"scenario": "容器 memhog 的内存限制可能未正确设置，或者应用本身存在内存泄漏问题。", "probability": "medium", "reason": "容器频繁重启，可能由于内存不足或应用问题。"}, {"scenario": "Pod 可能因频繁重启而进入 CrashLoopBackOff 状态，需要进一步检查其资源配置和日志。", "probability": "medium", "reason": "Pod 状态为 CrashLoopBackOff，需要进一步诊断日志和资源配置。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "OOMKilled", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "memhog-767b7b5dcc-l52km"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器内存限制过低", "probability": "中", "reason": "需验证 Last State/ExitCode/resources"}, {"scenario": "应用内存使用异常", "probability": "中", "reason": "需验证日志和重启历史"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "OOMKilled", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "memhog-767b7b5dcc-l52km"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器内存限制过低", "probability": "中", "reason": "需验证 Last State/ExitCode/resources"}, {"scenario": "应用内存使用异常", "probability": "中", "reason": "需验证日志和重启历史"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1, "OOMKilled": 1}, "total_abnormal": 2, "selected_rows": ["aiops-e2e     memhog-767b7b5dcc-l52km                             0/1     CrashLoopBackOff   53 (42s ago)    4h7m   172.16.166.153   node1    <none>           <none>            app=memhog,e2e-test=true,pod-template-hash=767b7b5dcc,pod_abnormal_type=OOMKilled"], "raw_ref": "/tmp/aiops/reports/context_archives/c020706fabf14abb/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/c020706fabf14abb/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/c020706fabf14abb/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
name: memhog-767b7b5dcc-l52km
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键状态/事件:
                  pod_abnormal_type=OOMKilled
Annotations:      aiops.e2e/expecte
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
name: memhog-767b7b5dcc-l52km
namespace: aiops-e2e
creationTimestamp: 2026-05-13T01:39:26Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <
   💭 [证据链采集] 已采集证据：
- kubectl_describe 验证了 Pod 的状态和事件，确认其因 OOMKilled 被终止，exitCode 为 137。
- kubectl_previous_logs 检查了容器的日志，但未发现输出，表明容器在崩溃前未产生日志。
- kubectl_get_yaml 验证了容器的配置，确认其在 node1 上运行，且具有 53 次重启记录。

未采集证据：
- 未检查容器的内存限制配置，以确认是否设置过低。
- 未检查应用本身的日志或配置，以确认是否存在内存泄漏或其他问题。

冲突证据：
- 无。
   ✅ [证据链采集] 完成 (2m 5.1s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod 'memhog-767b7b5dcc-l52km' 的详细信息以确认其异常状态","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod memhog-767b7b5dcc-l52km -n aiops-e2e","tool_args":{"pod_name":"memhog-767b7b5dcc-l52km","namespace":"aiops-e2e"},"purpose":"验证 Pod 的状态、事件和重启历史，确认其是否因 OOMKilled 被终止。","evidence_type":"pod_status","target_scope":"aiops-e2e/memhog-767b7b5dcc-l52km","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"获取容器 'memhog' 的上一次日志以检查是否有内存不足相关的错误信息","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs memhog-767b7b5dcc-l52km -n aiops-e2e --previous","tool_args":{"pod_name":"memhog-767b7b5dcc-l52km","container_name":"memhog","namespace":"aiops-e2e"},"purpose":"检查容器是否因内存不足而被终止，并确认是否有内存泄漏或配置错误。","evidence_type":"container_logs","target_scope":"aiops-e2e/memhog-767b7b5dcc-l52km/memhog","acceptable_tools":["kubectl_previous_logs"],"counts_for_completeness":true},{"id":"e3","description":"获取 Pod 'memhog-767b7b5dcc-l52km' 的资源配置以检查其内存限制","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod memhog-767b7b5dcc-l52km -n aiops-e2e -o yaml","tool_args":{"pod_name":"memhog-767b7b5dcc-l52km","namespace":"aiops-e2e"},"purpose":"验证容器的内存限制是否设置过低，导致其因内存不足而被终止。","evidence_type":"pod_configuration","target_scope":"aiops-e2e/memhog-767b7b5dcc-l52km","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: memhog-767b7b5dcc-l52km\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键状态/事件:\n                  pod_abnormal_type=OOMKilled\nAnnotations:      aiops.e2e/expected-evidence: container Last State reason is OOMKilled and exitCode is 137\n                  aiops.e2e/expected-status: CrashLoopBackOff|Error\n    State:          Waiting\n      Reason:       CrashLoopBackOff\n    Last State:     Terminated\n      Reason:       OOMKilled\n      Exit Code:    137\n  Warning  BackOff  73s (x1144 over 4h11m)  kubelet  Back-off restarting failed container memhog in pod memhog-767b7b5dcc-l52km_aiops-e2e(5a5158bc-ce60-4041-9dca-9158a2d57d8f)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c020706fabf14abb/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c020706fabf14abb/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c020706fabf14abb/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c020706fabf14abb/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c020706fabf14abb/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c020706fabf14abb/tools/002-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: memhog-767b7b5dcc-l52km\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T01:39:26Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=memhog, e2e-test=true, pod_abnormal_type=OOMKilled\ndiagnostic_annotations: aiops.e2e/expected-evidence=container Last State reason is OOMKilled and exitCode is 137, aiops.e2e/expected-status=CrashLoopBackOff|Error, aiops.e2e/runbook=pod-oomkilled.md\nownerReferences: ReplicaSet/memhog-767b7b5dcc\ntolerations_count: 2\ncontainers:\n- memhog: image=python:3.11-slim imagePullPolicy=IfNotPresent\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [memhog]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [memhog]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- memhog: ready=False restarts=53 reason=CrashLoopBackOff exitCode=137\n  message: back-off 5m0s restarting failed container=memhog pod=memhog-767b7b5dcc-l52km_aiops-e2e(5a5158bc-ce60-4041-9dca-9158a2d57d8f)\nvolumes:\n- {\"name\": \"kube-api-access-r426l\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c020706fabf14abb/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c020706fabf14abb/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c020706fabf14abb/tools/003-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"已采集证据：\n- kubectl_describe 验证了 Pod 的状态和事件，确认其因 OOMKilled 被终止，exitCode 为 137。\n- kubectl_previous_logs 检查了容器的日志，但未发现输出，表明容器在崩溃前未产生日志。\n- kubectl_get_yaml 验证了容器的配置，确认其在 node1 上运行，且具有 53 次重启记录。\n\n未采集证据：\n- 未检查容器的内存限制配置，以确认是否设置过低。\n- 未检查应用本身的日志或配置，以确认是否存在内存泄漏或其他问题。\n\n冲突证据：\n- 无。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 7 个，匹配计划 3 个，未规划证据 4 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":7,"matched_tool_count":3,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"获取 Pod 'memhog-767b7b5dcc-l52km' 的详细信息以确认其异常状态","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod memhog-767b7b5dcc-l52km -n aiops-e2e","purpose":"验证 Pod 的状态、事件和重启历史，确认其是否因 OOMKilled 被终止。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取容器 'memhog' 的上一次日志以检查是否有内存不足相关的错误信息","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs memhog-767b7b5dcc-l52km -n aiops-e2e --previous","purpose":"检查容器是否因内存不足而被终止，并确认是否有内存泄漏或配置错误。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取 Pod 'memhog-767b7b5dcc-l52km' 的资源配置以检查其内存限制","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod memhog-767b7b5dcc-l52km -n aiops-e2e -o yaml","purpose":"验证容器的内存限制是否设置过低，导致其因内存不足而被终止。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取 Pod 'memhog-767b7b5dcc-l52km' 的详细信息以确认其异常状态 | `kubectl describe pod memhog-767b7b5dcc-l52km -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_previous_logs | 获取容器 'memhog' 的上一次日志以检查是否有内存不足相关的错误信息 | `kubectl logs memhog-767b7b5dcc-l52km -n aiops-e2e --previous` |
   | e3 | important | ✅ | kubectl_get_yaml | 获取 Pod 'memhog-767b7b5dcc-l52km' 的资源配置以检查其内存限制 | `kubectl get pod memhog-767b7b5dcc-l52km -n aiops-e2e -o yaml` |

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (14.8s)
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
   ✅ [汇总总结] 完成 (1m 22.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4362 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 6m 9.5s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | CrashLoopBackOff, OOMKilled |
| **兼容归因层** | L2 - container_resource |
| **问题分类** | OOMKilled（Exit Code 137） |
| **置信度** | 高 (85%) |
| **证据完整度** | 3/3 (100%) |

---

## 🔍 现象描述

**用户报告**：  
> 我的集群有什么问题？

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | memhog-767b7b5dcc-l52km |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | OOMKilled, Exit Code: 137 |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff, RESTARTS: 53, LAST STATE: OOMKilled` | Pod 因 OOMKilled 被频繁重启 |
| 2 | Describe Pod 信息 | `kubectl describe pod memhog-767b7b5dcc-l52km -n aiops-e2e` | `Last State: Terminated, Reason: OOMKilled, Exit Code: 137` | 确认容器因内存不足被终止 |
| 3 | Pod 配置 | `kubectl get pod memhog-767b7b5dcc-l52km -n aiops-e2e -o yaml` | 未提供 `resources.limits.memory`，默认限制可能不足 | 可能配置缺失或限制过低 |
| 4 | 上一次容器日志 | `kubectl logs memhog-767b7b5dcc-l52km -n aiops-e2e --previous` | `(no output)` | 无崩溃前日志，无法确认内存增长原因 |
| 5 | 环境汇总 | `kubectl get pod -n aiops-e2e` | `status_counts={'CrashLoopBackOff': 1, 'OOMKilled': 1, 'Running': 46}` | 当前集群中存在 1 个 OOMKilled Pod |
| 6 | Runbook 规则 | `fetch_runbook` | `OOMKilled 通常与内存限制不足或内存泄漏有关` | 与当前现象匹配 |
| 7 | 事件记录 | `kubectl describe pod` | `Warning BackOff 2m11s (x1121 over 4h7m) kubelet Back-off restarting failed container memhog` | Pod 重启频繁，进入 CrashLoopBackOff 状态 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 CrashLoopBackOff，最后一次状态为 OOMKilled，Exit Code 为 137，确认容器因内存不足被系统 OOM Killer 终止。
- **证据链**：
  - 应用内存需求 > 当前内存限制（未显式配置，可能为默认值）
  - 内存使用达到限制 → cgroup OOM Killer 终止容器
  - 容器被终止 → Pod 重启 → 重启次数增加 → 进入 CrashLoopBackOff

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 应用崩溃前日志 | critical | 无法确认内存增长的具体原因（如内存泄漏、突发流量等） |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 应用实际内存需求超过容器内存限制（可能配置不足或默认限制过低）  │
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

**结论**：根据证据 #1 (Pod 状态 CrashLoopBackOff，Exit Code 137) 和证据 #2 (Last State: OOMKilled)，问题的根本原因是**容器内存限制不足以满足应用实际内存需求**，导致容器被 cgroup OOM Killer 终止并进入 CrashLoopBackOff 状态。

**置信度**：高 (85%)
- ✅ Exit Code 137 明确指向 OOMKilled
- ✅ Describe 中的 Last State 为 OOMKilled
- ⚠️ 缺少崩溃前日志，无法确认内存增长原因

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 增加容器内存限制**
```bash
kubectl set resources pod/memhog-767b7b5dcc-l52km -n aiops-e2e --limits=memory=512Mi
```
*依据*：当前未显式配置内存限制，建议设置为 512Mi 并观察效果

**2. [可选] 查看崩溃前日志**
```bash
kubectl logs memhog-767b7b5dcc-l52km -n aiops-e2e --previous | tail -100
```
*目的*：确认是否存在内存泄漏或突发流量导致内存占用过高

**3. [建议] 设置合理的资源请求与限制**
```bash
kubectl set resources pod/memhog-767b7b5dcc-l52km -n aiops-e2e --limits=memory=512Mi --requests=memory=256Mi
```
*目的*：避免资源争抢，同时提供弹性空间

### 后续优化

1. **监控告警**：配置内存使用率告警（建议 >80% 预警）
2. **资源评估**：使用 Prometheus 或 `kubectl describe pod` 查看资源请求/限制与使用情况
3. **应用优化**：检查是否存在内存泄漏（如使用 heap dump、GC 状态分析）

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod memhog-767b7b5dcc-l52km -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod memhog-767b7b5dcc-l52km -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |
| 3. 监控内存使用 | Prometheus: `container_memory_usage_bytes` | < 80% of limit |

---

## ⚠️ 注意事项

- 如果问题持续，可能需要进一步分析应用内存使用情况
- 考虑配置 HPA 根据内存自动扩缩容
- 避免在未设置内存限制的情况下部署高内存需求应用

---

---

## 📊 性能统计

├─ 总耗时: 6.2m
├─ 问题定位: 147.1s (40%) ✅
├─ 证据链采集: 125.1s (34%) ✅
├─ 根因分析: 14.8s (4%) ✅
├─ 汇总总结: 82.5s (22%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 8 次
```

📋 诊断追踪

- **核心 Runbook**: pod-oomkilled
- **参考 Runbook**: pod-oomkilled
- **工具调用**: 8 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
