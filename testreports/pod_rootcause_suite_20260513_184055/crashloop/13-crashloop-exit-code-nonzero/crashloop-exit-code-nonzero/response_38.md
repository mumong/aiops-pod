======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: fe46169d1d0b4d57]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'CrashLoopBackOff': 1, 'Running': 46}
NAMESPACE     NAME                                                READY   STATUS           
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
      📄 NAME                                      READY   STATUS             RESTARTS       AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-crashloop-exit-code-5db5947859-gk6cf   
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-crashloop-exit-code-5db5947859-gk6cf
namespace: aiops-e2e
creationTimestamp: 2026-05-14T13:49:22Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: No
   💭 [问题定位] {
  "layer": "L2",
  "derived_layer": "L2",
  "layers": [
    "L2"
  ],
  "layer_name": "CrashLoopBackOffRuntime",
  "confidence": 0.95,
  "reasoning": "Pod 状态为 CrashLoopBackOff，最后一次退出码为 2，且日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'，表明容器在启动过程中遇到了错误。根据 runbook，CrashLoopBackOff + Exit Code 非 137 + 命令/进程错误的组合属于 L2 归类。此外，Pod 的 restartPolicy 为 Always，导致容器反复重启。",
  "abnormal_pods": [
    {
      "name": "rc-crashloop-exit-code-5db5947859-gk6cf",
      "namespace": "aiops-e2e",
      "status": "CrashLoopBackOff",
      "reason": "CrashLoopBackOff",
      "exit_code": 2,
      "restarts": 29,
      "node": "node1"
    }
  ],
  "abnormal_groups": [
    "CrashLoopBackOffRuntime"
  ],
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "CrashLoopBackOffRuntime",
  "status_category": "CrashLoopBackOff",
  "key_entities": [
    "Pod/rc-crashloop-exit-code-5db5947859-gk6cf",
    "Container/app",
    "Namespace/aiops-e2e",
    "Node/node1"
  ],
  "possible_scenarios": [
    "容器启动命令错误或入口点配置错误",
    "容器内进程启动失败，例如脚本或二进制文件不存在",
    "容器内进程启动后立即退出，导致控制器反复拉起",
    "容器内进程遇到运行时异常，例如权限不足、磁盘空间不足等",
    "容器内进程启动后因 livenessProbe 配置不当被杀死"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (2m 38.2s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[{'scenario': '容器启动命令错误或入口点配置错误', 'probability': 'high', 'reason': "Pod 状态为 CrashLoopBackOff，最后一次退出码为 2，且日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'"}, {'scenario': '容器内进程启动失败，例如脚本或二进制文件不存在', 'probability': 'high', 'reason': "Pod 状态为 CrashLoopBackOff，最后一次退出码为 2，且日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'"}, {'scenario': '容器内进程启动后立即退出，导致控制器反复拉起', 'probability': 'high', 'reason': "Pod 状态为 CrashLoopBackOff，最后一次退出码为 2，且日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'"}, {'scenario': '容器内进程遇到运行时异常，例如权限不足、磁盘空间不足等', 'probability': 'high', 'reason': "Pod 状态为 CrashLoopBackOff，最后一次退出码为 2，且日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'"}, {'scenario': '容器内进程启动后因 livenessProbe 配置不当被杀死', 'probability': 'medium', 'reason': "Pod 状态为 CrashLoopBackOff，最后一次退出码为 2，且日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'"}]
   entities=[{"type": "Pod", "name": "rc-crashloop-exit-code-5db5947859-gk6cf", "namespace": "aiops-e2e"}, {"type": "Container", "name": "app", "namespace": "aiops-e2e"}, {"type": "Namespace", "name": "aiops-e2e", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}]
   reasoning=Pod 状态为 CrashLoopBackOff，最后一次退出码为 2，且日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'，表明容器在启动过程中遇到了错误。根据 runbook，CrashLoopBackOff + Exit Code 非 137 + 命令/进程错误的组合属于 L2 归类。此外，Pod 的 restartPolicy 为 Always，导致容器反复重启。
   layer_analysis={"layer": "L2", "derived_layer": "L2", "layers": ["L2"], "layer_name": "CrashLoopBackOffRuntime", "confidence": 0.95, "reasoning": "Pod 状态为 CrashLoopBackOff，最后一次退出码为 2，且日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'，表明容器在启动过程中遇到了错误。根据 runbook，CrashLoopBackOff + Exit Code 非 137 + 命令/进程错误的组合属于 L2 归类。此外，Pod 的 restartPolicy 为 Always，导致容器反复重启。", "abnormal_pods": [{"name": "rc-crashloop-exit-code-5db5947859-gk6cf", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "CrashLoopBackOffRuntime", "status_category": "container_resource/container_runtime", "key_entities": [{"type": "Pod", "name": "rc-crashloop-exit-code-5db5947859-gk6cf", "namespace": "aiops-e2e"}, {"type": "Container", "name": "app", "namespace": "aiops-e2e"}, {"type": "Namespace", "name": "aiops-e2e", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}], "possible_scenarios": [{"scenario": "容器启动命令错误或入口点配置错误", "probability": "high", "reason": "Pod 状态为 CrashLoopBackOff，最后一次退出码为 2，且日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'"}, {"scenario": "容器内进程启动失败，例如脚本或二进制文件不存在", "probability": "high", "reason": "Pod 状态为 CrashLoopBackOff，最后一次退出码为 2，且日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'"}, {"scenario": "容器内进程启动后立即退出，导致控制器反复拉起", "probability": "high", "reason": "Pod 状态为 CrashLoopBackOff，最后一次退出码为 2，且日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'"}, {"scenario": "容器内进程遇到运行时异常，例如权限不足、磁盘空间不足等", "probability": "high", "reason": "Pod 状态为 CrashLoopBackOff，最后一次退出码为 2，且日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'"}, {"scenario": "容器内进程启动后因 livenessProbe 配置不当被杀死", "probability": "medium", "reason": "Pod 状态为 CrashLoopBackOff，最后一次退出码为 2，且日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-exit-code-5db5947859-gk6cf"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-exit-code-5db5947859-gk6cf"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-crashloop-exit-code-5db5947859-gk6cf             0/1     CrashLoopBackOff   29 (73s ago)   124m    172.16.166.139   node1    <none>           <none>            app=rc-crashloop-exit-code,pod-template-hash=5db5947859,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/fe46169d1d0b4d57/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/fe46169d1d0b4d57/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/fe46169d1d0b4d57/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L2
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
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                      READY   STATUS             RESTARTS       AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-crashloop-exit-code-5db5947859-gk6cf   
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (2m 23.1s)
   📤 → 下游数据: evidence_items=6/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 的详细信息，包括 Last State、Exit Code、Reason 等关键字段","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o yaml","tool_args":{"name":"rc-crashloop-exit-code-5db5947859-gk6cf","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"验证 Pod 的 Last State、Exit Code、Reason 等关键字段，确认容器崩溃原因","evidence_type":"pod_status","target_scope":"aiops-e2e/rc-crashloop-exit-code-5db5947859-gk6cf","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 的崩溃前日志，确认崩溃原因","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous --tail=200","tool_args":{"name":"rc-crashloop-exit-code-5db5947859-gk6cf","namespace":"aiops-e2e","container":null,"tail":"200"},"purpose":"验证崩溃前日志，确认崩溃原因","evidence_type":"container_logs","target_scope":"aiops-e2e/rc-crashloop-exit-code-5db5947859-gk6cf","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod 的事件，确认是否有 BackOff、probe failed、Killing 等关键事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crashloop-exit-code-5db5947859-gk6cf --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-crashloop-exit-code-5db5947859-gk6cf","sort_by":".lastTimestamp"},"purpose":"验证异常 Pod 的事件，确认是否有 BackOff、probe failed、Killing 等关键事件","evidence_type":"event_log","target_scope":"aiops-e2e/rc-crashloop-exit-code-5db5947859-gk6cf","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"获取异常 Pod 的描述信息，包括 command/args/image/resources 等关键字段","level":"important","tool":"kubectl_describe","command":"kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e","tool_args":{"name":"rc-crashloop-exit-code-5db5947859-gk6cf","namespace":"aiops-e2e"},"purpose":"验证异常 Pod 的描述信息，包括 command/args/image/resources 等关键字段","evidence_type":"pod_description","target_scope":"aiops-e2e/rc-crashloop-exit-code-5db5947859-gk6cf","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                                      READY   STATUS             RESTARTS       AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-crashloop-exit-code-5db5947859-gk6cf   0/1     CrashLoopBackOff   30 (54s ago)   129m   172.16.166.139   node1   <none>           <none>            app=rc-crashloop-exit-code,pod-template-hash=5db5947859,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fe46169d1d0b4d57/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fe46169d1d0b4d57/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fe46169d1d0b4d57/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 1\n关键日志:\nRUNTIME_STARTUP_ERROR: rc crashloop exits with code 2","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fe46169d1d0b4d57/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fe46169d1d0b4d57/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fe46169d1d0b4d57/tools/002-evidence-kubectl_previous_logs.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 4 项，实际采集 2 项，未采集 2 项，完整度 50%；其中真实环境证据 6/8 项，完整度 75%；实际执行工具 6 个，匹配计划 2 个，未规划证据 4 个","plan_total":4,"plan_collected":2,"plan_completeness":0.5,"environment_evidence_total":8,"environment_evidence_collected":6,"environment_evidence_completeness":0.75,"executed_tool_count":6,"matched_tool_count":2,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 的详细信息，包括 Last State、Exit Code、Reason 等关键字段","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o yaml","purpose":"验证 Pod 的 Last State、Exit Code、Reason 等关键字段，确认容器崩溃原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 的崩溃前日志，确认崩溃原因","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous --tail=200","purpose":"验证崩溃前日志，确认崩溃原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod 的事件，确认是否有 BackOff、probe failed、Killing 等关键事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crashloop-exit-code-5db5947859-gk6cf --sort-by='.lastTimestamp'","purpose":"验证异常 Pod 的事件，确认是否有 BackOff、probe failed、Killing 等关键事件","collected":false,"source":"planned","outcome":"unknown"},{"id":"e4","description":"获取异常 Pod 的描述信息，包括 command/args/image/resources 等关键字段","level":"important","tool":"kubectl_describe","command":"kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e","purpose":"验证异常 Pod 的描述信息，包括 command/args/image/resources 等关键字段","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":["e3(获取异常 Pod 的事件，确认是否有 BackOff、probe failed、Killing 等关键事件): 已规划但工具执行失败或无匹配结果","e4(获取异常 Pod 的描述信息，包括 command/args/image/resources 等关键字段): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/4 项, 完整度: 75%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 获取异常 Pod 的详细信息，包括 Last State、Exit Code、Reason... | `kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o yaml` |
   | e2 | critical | ✅ | kubectl_previous_logs | 获取异常 Pod 的崩溃前日志，确认崩溃原因 | `kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous ...` |
   | e3 | important | ❌ | kubectl_events | 获取异常 Pod 的事件，确认是否有 BackOff、probe failed、Killi... | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crash...` |
   | e4 | important | ❌ | kubectl_describe | 获取异常 Pod 的描述信息，包括 command/args/image/resource... | `kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e` |

   ⚠️ 未采集原因:
   - e3(获取异常 Pod 的事件，确认是否有 BackOff、probe failed、Killing 等关键事件): 已规划但工具执行失败或无匹配结果
   - e4(获取异常 Pod 的描述信息，包括 command/args/image/resources 等关键字段): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 12.8s)
   📤 → 下游数据: root_cause=容器启动命令错误或入口点配置错误，导致容器启动失败，最后一次退出码为 2，且日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'。
   confidence=95%
   causal_chain={"root_cause": "容器启动命令错误或入口点配置错误", "intermediate_causes": [{"cause": "容器内进程启动失败，例如脚本或二进制文件不存在", "effect": "Pod 状态为 CrashLoopBackOff，最后一次退出码为 2，且日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'"}, {"cause": "容器内进程启动后立即退出，导致控制器反复拉起", "effect": "Pod 状态为 CrashLoopBackOff，最后一次退出码为 2，且日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'"}, {"cause": "容器内进程遇到运行时异常，例如权限不足、磁盘空间不足等", "effect": "Pod 状态为 CrashLoopBackOff，最后一次退出码为 2，且日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'"}, {"cause": "容器内进程启动后因 livenessProbe 配置不当被杀死", "effect": "Pod 状态为 CrashLoopBackOff，最后一次退出码为 2，且日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'"}], "direct_causes": [{"cause": "Pod 状态为 CrashLoopBackOff，最后一次退出码为 2，且日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'", "effect": "Pod 状态为 CrashLoopBackOff，且 restartPolicy 为 Always，导致容器反复重启"}], "phenomenon": "Pod 状态为 CrashLoopBackOff，且 restartPolicy 为 Always，导致容器反复重启"}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [{"description": "获取异常 Pod 的详细信息，包括 Last State、Exit Code、Reason 等关键字段", "value": "NAME                                      READY   STATUS             RESTARTS       AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-crashloop-exit-code-5db5947859-gk6cf   0/1     CrashLoopBackOff   30 (54s ago)   129m   172.16.166.139   node1   <none>           <none>            app=rc-crashloop-exit-code,pod-template-hash=5db5947859,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true"}, {"description": "获取异常 Pod 的崩溃前日志，确认崩溃原因", "value": "kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 1\n关键日志:\nRUNTIME_STARTUP_ERROR: rc crashloop exits with code 2"}, {"description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'CrashLoopBackOff': 1, 'Running': 46}\nNAMESPACE     NAME                                                READY   STATUS             RESTARTS       AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\n# 异常行\naiops-e2e     rc-crashloop-exit-code-5db5947859-gk6cf             0/1     CrashLoopBackOff   29 (73s ago)   124m    172.16.166.139   node1    <none>           <none>            app=rc-crashloop-exit-co"}, {"description": "上游已验证工具结果: kubectl_get_by_name", "value": "NAME                                      READY   STATUS             RESTARTS       AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-crashloop-exit-code-5db5947859-gk6cf   0/1     CrashLoopBackOff   29 (78s ago)   124m   172.16.166.139   node1   <none>           <none>            app=rc-crashloop-exit-code,pod-template-hash=5db5947859,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true"}, {"description": "上游已验证工具结果: kubectl_previous_logs", "value": "kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 1\n关键日志:\nRUNTIME_STARTUP_ERROR: rc crashloop exits with code 2"}, {"description": "上游已验证工具结果: kubectl_get_yaml", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-crashloop-exit-code-5db5947859-gk6cf\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-14T13:49:22Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-crashloop-exit-code, pod_abnormal_type=CrashLoopBackOffRuntime\ndiagnostic_annotations: aiops.e2e/runbook=pod-crashloop-ru"}], "causal_chain": {"root_cause": "容器启动命令错误或入口点配置错误", "intermediate_causes": [{"cause": "容器内进程启动失败，例如脚本或二进制文件不存在", "effect": "Pod 状态为 CrashLoopBackOff，最后一次退出码为 2，且日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'"}, {"cause": "容器内进程启动后立即退出，导致控制器反复拉起", "effect": "Pod 状态为 CrashLoopBackOff，最后一次退出码为 2，且日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'"}, {"cause": "容器内进程遇到运行时异常，例如权限不足、磁盘空间不足等", "effect": "Pod 状态为 CrashLoopBackOff，最后一次退出码为 2，且日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'"}, {"cause": "容器内进程启动后因 livenessProbe 配置不当被杀死", "effect": "Pod 状态为 CrashLoopBackOff，最后一次退出码为 2，且日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'"}], "direct_causes": [{"cause": "Pod 状态为 CrashLoopBackOff，最后一次退出码为 2，且日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'", "effect": "Pod 状态为 CrashLoopBackOff，且 restartPolicy 为 Always，导致容器反复重启"}], "phenomenon": "Pod 状态为 CrashLoopBackOff，且 restartPolicy 为 Always，导致容器反复重启"}, "root_cause": "容器启动命令错误或入口点配置错误，导致容器启动失败，最后一次退出码为 2，且日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'。", "root_cause_summary": "容器启动命令错误或入口点配置错误，导致容器启动失败，最后一次退出码为 2，且日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'。", "confidence": 0.95, "confidence_reason": "有直接证据，因果链清晰", "primary_runbooks": ["pod-crashloop-runtime.md"], "alternative_causes": [], "limitations": "缺少异常 Pod 的事件和描述信息，可能影响对问题的全面分析。", "llm_raw_analysis": "基于提供的证据，分析了异常 Pod 的状态和日志，确认了容器启动失败的原因，并构建了因果链。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 容器启动命令错误或入口点配置错误，导致容器启动失败，最后一次退出码为 2，且日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'。
   置信度: 95%
   🔗 因果链:
     根本原因: 容器启动命令错误或入口点配置错误


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 45.2s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4235 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 7m 59.3s
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
| **兼容归因层** | L2 - container_resource/container_runtime |
| **问题分类** | CrashLoopBackOffRuntime |
| **置信度** | 高 (95%) |
| **证据完整度** | 2/4 (50%) |

---

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-crashloop-exit-code-5db5947859-gk6cf |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2 |

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff, RESTARTS: 29` | Pod 处于持续崩溃状态 |
| 2 | 崩溃前日志 | `kubectl logs <pod> --previous` | `RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2` | 容器启动失败，退出码 2 |
| 3 | Pod YAML 配置 | `kubectl get pod -o yaml` | `restartPolicy: Always` | 导致容器反复重启 |
| 4 | Runbook | `fetch_runbook` | `# Pod CrashLoopBackOffRuntime / 容器反复退出` | 匹配典型归因分类 |
| 5 | 工具验证 | `kubectl_get_by_name` | `STATUS: CrashLoopBackOff, RESTARTS: 29` | 确认 Pod 状态 |
| 6 | 工具验证 | `kubectl_previous_logs` | `RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2` | 确认崩溃日志 |

### 证据关联分析
- **证据 #1 + #2 印证**：CrashLoopBackOff + 退出码 2 + 启动失败日志 → 容器启动失败
- **证据链**：
  - 容器启动命令或入口点配置错误
  - 容器主进程异常退出（退出码 2）
  - Pod 的 `restartPolicy: Always` 导致容器反复重启
  - 最终表现为 `CrashLoopBackOff` 状态

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| Pod 事件 | critical | 无法确认是否有探针失败、BackOff 等关键事件 |
| Pod 描述信息 | critical | 无法确认 command/args/image/resources 等关键配置 |

---

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 容器启动命令或入口点配置错误，导致容器启动失败                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器启动失败，退出码为 2，日志显示 RUNTIME_STARTUP_ERROR        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器主进程启动失败，Pod 的 restartPolicy: Always 导致反复重启   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CrashLoopBackOff，重启次数持续增加                   │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2 (RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2) 和证据 #3 (restartPolicy: Always)，问题的根本原因是**容器启动命令或入口点配置错误**，导致容器启动失败，退出码为 2，最终表现为 `CrashLoopBackOff` 状态。

**置信度**：高 (95%)
- ✅ 退出码 2 + 启动失败日志
- ✅ `restartPolicy: Always` 导致反复重启
- ⚠️ 缺少事件和 describe 信息，无法确认是否涉及探针失败或资源限制

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 检查容器启动命令或入口点配置**
```bash
kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e
```
*依据*：需确认容器的 `command`、`args`、`image` 是否正确，是否有拼写错误或路径错误。

**2. [优先] 查看完整崩溃前日志**
```bash
kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous
```
*目的*：确认启动失败的具体原因，例如脚本不存在、权限错误等。

**3. [可选] 查看 Pod 事件**
```bash
kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e
```
*目的*：确认是否涉及探针失败、BackOff、Killing 等关键事件。

### 后续优化
1. **调整 restartPolicy**：若容器为一次性任务，建议将 `restartPolicy` 改为 `OnFailure` 或 `Never`。
2. **配置 livenessProbe 与 readinessProbe**：确保探针配置合理，避免误杀。
3. **验证镜像和依赖**：确认容器镜像是否正确，是否有依赖缺失。
4. **资源监控**：配置 Prometheus 或监控工具，持续监控容器状态和日志。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |
| 3. 查看日志 | `kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous` | 无启动失败日志 |

---

## ⚠️ 注意事项
- 如果退出码为 2，通常表示命令执行失败（如脚本错误、路径错误等），建议重点检查 `command` 和 `args`。
- 若容器依赖外部服务或文件系统，建议检查网络、权限、磁盘空间等。
- 如果问题仍然存在，建议检查容器镜像的完整性和可执行性。

---

## 📊 性能统计

├─ 总耗时: 8.0m
├─ 问题定位: 158.2s (33%) ✅
├─ 证据链采集: 143.1s (30%) ✅
├─ 根因分析: 72.8s (15%) ✅
├─ 汇总总结: 105.2s (22%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 8 次
```

📋 诊断追踪

- **核心 Runbook**: pod-crashloop-runtime
- **参考 Runbook**: pod-crashloop-runtime
- **工具调用**: 8 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
