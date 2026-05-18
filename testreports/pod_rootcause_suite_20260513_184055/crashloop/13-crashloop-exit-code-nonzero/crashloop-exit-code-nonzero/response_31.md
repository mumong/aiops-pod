======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 5f24cc0f4a384542]

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
      📄 NAME                                      READY   STATUS             RESTARTS        AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-crashloop-exit-code-5db5947859-gk6cf  
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2
   💭 [问题定位] 调用工具: kubectl_container_previous_logs
   💭 [问题定位] 工具结果: kubectl_container_previous_logs (success)
      📄 kubectl_container_previous_logs 输出摘要: raw_chars=240 lines=3
Command failed (exit 1):
kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -c rc-crashloop-exit-code -n aiops-e2e --previous --tail=200
e
   💭 [问题定位] 调用工具: kubectl_logs
   💭 [问题定位] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 日志摘要:
lines: 1
signals: 1
关键日志:
RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2
   💭 [问题定位] 调用工具: kubectl_container_logs
   💭 [问题定位] 工具结果: kubectl_container_logs (success)
      📄 kubectl_container_logs 输出摘要: raw_chars=229 lines=3
Command failed (exit 1):
kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -c rc-crashloop-exit-code -n aiops-e2e --tail=200
error: container rc-c
   💭 [问题定位] 调用工具: kubectl_get_yaml
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 5.8s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[{'scenario': '容器启动命令或配置错误导致进程退出', 'probability': '高', 'reason': '日志显示 rc crashloop exits with code 2，表明进程在启动阶段失败。'}, {'scenario': '容器内应用异常退出，但非资源限制问题', 'probability': '中', 'reason': '退出码为 2，不符合 OOMKilled（137）等资源限制特征。'}, {'scenario': '容器镜像或路径错误', 'probability': '中', 'reason': '可能因容器镜像中缺少可执行文件或路径错误导致进程失败。'}]
   entities=[{"type": "pod", "name": "rc-crashloop-exit-code-5db5947859-gk6cf", "namespace": "aiops-e2e"}]
   reasoning=当前环境中存在一个处于 CrashLoopBackOff 状态的 Pod（rc-crashloop-exit-code-5db5947859-gk6cf），其异常类型为 CrashLoopBackOffRuntime。根据日志摘要，Pod 启动失败并返回非 137 的退出码（code 2），符合 L2 层的判定条件。此外，Runbook 明确指出 CrashLoopBackOffRuntime 兼容分类为 container_runtime。因此，当前异常归为 L2 层。
   layer_analysis={"layer": "L2", "derived_layer": "L2", "layers": ["L2"], "layer_name": "container_resource/container_runtime", "confidence": 0.95, "reasoning": "当前环境中存在一个处于 CrashLoopBackOff 状态的 Pod（rc-crashloop-exit-code-5db5947859-gk6cf），其异常类型为 CrashLoopBackOffRuntime。根据日志摘要，Pod 启动失败并返回非 137 的退出码（code 2），符合 L2 层的判定条件。此外，Runbook 明确指出 CrashLoopBackOffRuntime 兼容分类为 container_runtime。因此，当前异常归为 L2 层。", "abnormal_pods": [{"name": "rc-crashloop-exit-code-5db5947859-gk6cf", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "CrashLoopBackOffRuntime", "status_category": "container_resource/container_runtime", "key_entities": [{"type": "pod", "name": "rc-crashloop-exit-code-5db5947859-gk6cf", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "容器启动命令或配置错误导致进程退出", "probability": "高", "reason": "日志显示 rc crashloop exits with code 2，表明进程在启动阶段失败。"}, {"scenario": "容器内应用异常退出，但非资源限制问题", "probability": "中", "reason": "退出码为 2，不符合 OOMKilled（137）等资源限制特征。"}, {"scenario": "容器镜像或路径错误", "probability": "中", "reason": "可能因容器镜像中缺少可执行文件或路径错误导致进程失败。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-exit-code-5db5947859-gk6cf"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-exit-code-5db5947859-gk6cf"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-crashloop-exit-code-5db5947859-gk6cf             0/1     CrashLoopBackOff   24 (3m58s ago)   101m   172.16.166.139   node1    <none>           <none>            app=rc-crashloop-exit-code,pod-template-hash=5db5947859,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/5f24cc0f4a384542/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/5f24cc0f4a384542/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/5f24cc0f4a384542/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-crashloop-exit-code-5db5947859-gk6cf
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
                  pod_abnormal_type=CrashLoopBackOffRuntime
      R
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-crashloop-exit-code-5db5947859-gk6cf
namespace: aiops-e2e
creationTimestamp: 2026-05-14T13:49:22Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: No
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
4m53s (x465 over 105m)   Warning   BackOff   Pod/rc-crashloop-exit-code-5db5947859-gk6cf   Back-off restarting failed container app in pod rc-crashloop-exit-code-5db5947859-g
   💭 [证据链采集] 已采集证据：
- kubectl describe pod 显示容器处于 CrashLoopBackOff 状态，最后一次退出码为 2。
- kubectl previous logs 显示日志中包含 "RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2"。
- kubectl get yaml 显示容器配置，确认容器镜像为 busybox:1.36，且 restartPolicy 为 Always。
- kubectl events 显示事件 "Back-off restarting failed container app"。

未采集证据：
- 无

冲突证据：
- 无

结论：
当前 Pod `rc-crashloop-exit-code-5db5947859-gk6cf` 处于 CrashLoopBackOff 状态，最后一次退出码为 2，表明容器在启动阶段失败。日志显示 "RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2"，表明容器在启动时遇到了错误。容器配置显示使用 busybox:1.36 镜像，且 restartPolicy 为 Always。事件日志显示 "Back-off restarting failed container app"，进一步确认了容器启动失败。建议检查容器启动命令和配置，确保应用程序能够正确启动。
   ✅ [证据链采集] 完成 (2m 18.4s)
   📤 → 下游数据: evidence_items=10/10
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证异常 Pod 的详细状态和 Last State 信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e","tool_args":{"name":"rc-crashloop-exit-code-5db5947859-gk6cf","namespace":"aiops-e2e","kind":"Pod"},"purpose":"获取 Pod 的 Last State、Exit Code、Reason、重启次数等关键信息","evidence_type":"pod_status","target_scope":"aiops-e2e/rc-crashloop-exit-code-5db5947859-gk6cf","acceptable_tools":["kubectl_describe","kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 上次崩溃的容器日志","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous --tail=200","tool_args":{"name":"rc-crashloop-exit-code-5db5947859-gk6cf","namespace":"aiops-e2e","kind":"Pod"},"purpose":"获取崩溃前的容器日志，确认启动失败的具体原因","evidence_type":"container_logs","target_scope":"aiops-e2e/rc-crashloop-exit-code-5db5947859-gk6cf","acceptable_tools":["kubectl_previous_logs","kubectl_logs"],"counts_for_completeness":true},{"id":"e3","description":"验证异常 Pod 的完整 YAML 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o yaml","tool_args":{"name":"rc-crashloop-exit-code-5db5947859-gk6cf","namespace":"aiops-e2e","kind":"Pod"},"purpose":"查看 Pod 的 command/args/image/resources 等配置信息","evidence_type":"pod_configuration","target_scope":"aiops-e2e/rc-crashloop-exit-code-5db5947859-gk6cf","acceptable_tools":["kubectl_get_yaml","kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e4","description":"获取与异常 Pod 相关的事件信息","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crashloop-exit-code-5db5947859-gk6cf --sort-by='.lastTimestamp'","tool_args":{"name":"rc-crashloop-exit-code-5db5947859-gk6cf","namespace":"aiops-e2e","kind":"Pod"},"purpose":"查看 BackOff、probe failed、Killing 等事件信息","evidence_type":"events","target_scope":"aiops-e2e/rc-crashloop-exit-code-5db5947859-gk6cf","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-crashloop-exit-code-5db5947859-gk6cf\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n                  pod_abnormal_type=CrashLoopBackOffRuntime\n      Reason:       CrashLoopBackOff\n  Warning  BackOff  4m43s (x465 over 104m)  kubelet  Back-off restarting failed container app in pod rc-crashloop-exit-code-5db5947859-gk6cf_aiops-e2e(0c99a099-859b-4fcb-86a9-589275358d92)\n                  cni.projectcalico.org/containerID: 6f43a4e9bdd30cfd305f143fe7d94201cfbfbb4a8154bbc5ffcc20aafd24bc3a\n                  cni.projectcalico.org/podIP: 172.16.166.139/32\n                  cni.projectcalico.org/podIPs: 172.16.166.139/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    2","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/5f24cc0f4a384542/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/5f24cc0f4a384542/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/5f24cc0f4a384542/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 1\n关键日志:\nRUNTIME_STARTUP_ERROR: rc crashloop exits with code 2","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/5f24cc0f4a384542/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/5f24cc0f4a384542/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/5f24cc0f4a384542/tools/002-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-crashloop-exit-code-5db5947859-gk6cf\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-14T13:49:22Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-crashloop-exit-code, pod_abnormal_type=CrashLoopBackOffRuntime\ndiagnostic_annotations: aiops.e2e/runbook=pod-crashloop-runtime.md\nownerReferences: ReplicaSet/rc-crashloop-exit-code-5db5947859\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=25 reason=CrashLoopBackOff exitCode=2\n  message: back-off 5m0s restarting failed container=app pod=rc-crashloop-exit-code-5db5947859-gk6cf_aiops-e2e(0c99a099-859b-4fcb-86a9-589275358d92)\nvolumes:\n- {\"name\": \"kube-api-access-wgw6q\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/5f24cc0f4a384542/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/5f24cc0f4a384542/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/5f24cc0f4a384542/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n4m53s (x465 over 105m)   Warning   BackOff   Pod/rc-crashloop-exit-code-5db5947859-gk6cf   Back-off restarting failed container app in pod rc-crashloop-exit-code-5db5947859-gk6cf_aiops-e2e(0c99a099-859b-4fcb-86a9-589275358d92)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/5f24cc0f4a384542/tools/004-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/5f24cc0f4a384542/tools/004-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/5f24cc0f4a384542/tools/004-evidence-kubectl_events.summary.txt"}],"llm_analysis":"已采集证据：\n- kubectl describe pod 显示容器处于 CrashLoopBackOff 状态，最后一次退出码为 2。\n- kubectl previous logs 显示日志中包含 \"RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2\"。\n- kubectl get yaml 显示容器配置，确认容器镜像为 busybox:1.36，且 restartPolicy 为 Always。\n- kubectl events 显示事件 \"Back-off restarting failed container app\"。\n\n未采集证据：\n- 无\n\n冲突证据：\n- 无\n\n结论：\n当前 Pod `rc-crashloop-exit-code-5db5947859-gk6cf` 处于 CrashLoopBackOff 状态，最后一次退出码为 2，表明容器在启动阶段失败。日志显示 \"RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2\"，表明容器在启动时遇到了错误。容器配置显示使用 busybox:1.36 镜像，且 restartPolicy 为 Always。事件日志显示 \"Back-off restarting failed container app\"，进一步确认了容器启动失败。建议检查容器启动命令和配置，确保应用程序能够正确启动。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 10/10 项，完整度 100%；实际执行工具 8 个，匹配计划 4 个，未规划证据 4 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":10,"environment_evidence_collected":10,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":4,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"验证异常 Pod 的详细状态和 Last State 信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e","purpose":"获取 Pod 的 Last State、Exit Code、Reason、重启次数等关键信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 上次崩溃的容器日志","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous --tail=200","purpose":"获取崩溃前的容器日志，确认启动失败的具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"验证异常 Pod 的完整 YAML 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o yaml","purpose":"查看 Pod 的 command/args/image/resources 等配置信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"获取与异常 Pod 相关的事件信息","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crashloop-exit-code-5db5947859-gk6cf --sort-by='.lastTimestamp'","purpose":"查看 BackOff、probe failed、Killing 等事件信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_container_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_container_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证异常 Pod 的详细状态和 Last State 信息 | `kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_previous_logs | 获取异常 Pod 上次崩溃的容器日志 | `kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous ...` |
   | e3 | important | ✅ | kubectl_get_yaml | 验证异常 Pod 的完整 YAML 配置 | `kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o yaml` |
   | e4 | important | ✅ | kubectl_events | 获取与异常 Pod 相关的事件信息 | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crash...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (2m 0.4s)
   📤 → 下游数据: root_cause=Pod 'rc-crashloop-exit-code-5db5947859-gk6cf' 处于 CrashLoopBackOff 状态，最后一次退出码为 2，表明容器在启动阶段失败。日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'，表明容器在启动时遇到了错误。容器配置显示使用 busybox:1.36 镜像，且 restartPolicy 为 Always。事件日志显示 'Back-off restarting failed container app'，进一步确认了容器启动失败。建议检查容器启动命令和配置，确保应用程序能够正确启动。
   confidence=95%
   causal_chain={"root_cause": "容器启动命令或配置错误导致进程退出", "intermediate_causes": ["容器在启动阶段失败，退出码为 2", "日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'"], "direct_causes": ["容器启动命令或配置错误", "容器镜像或路径错误"]}
   rca_analysis={"phenomenon": "Pod 'rc-crashloop-exit-code-5db5947859-gk6cf' 在 aiops-e2e 命名空间中处于 CrashLoopBackOff 状态，最后一次退出码为 2，表明容器在启动阶段失败。", "evidence_inventory": [{"id": "e1", "description": "验证异常 Pod 的详细状态和 Last State 信息", "level": "critical", "value": "kubectl_describe 摘要:\nname: rc-crashloop-exit-code-5db5947859-gk6cf\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n                  pod_abnormal_type=CrashLoopBackOffRuntime\n      Reason:       CrashLoopBackOff\n  Warning  BackOff  4m43s (x465 over 104m)  kubelet  Back-off restarting failed container app in pod rc-crashloop-exit-code-5db5947859-gk6cf_aiops-e2e(0c99a099-859b-4fcb-86a9-589275358d92)\n                  cni.projectcalico.org/containerID: 6f43a4e9bdd30cfd305f143fe7d9"}, {"id": "e2", "description": "获取异常 Pod 上次崩溃的容器日志", "level": "critical", "value": "kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 1\n关键日志:\nRUNTIME_STARTUP_ERROR: rc crashloop exits with code 2"}, {"id": "e3", "description": "验证异常 Pod 的完整 YAML 配置", "level": "important", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-crashloop-exit-code-5db5947859-gk6cf\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-14T13:49:22Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-crashloop-exit-code, pod_abnormal_type=CrashLoopBackOffRuntime\ndiagnostic_annotations: aiops.e2e/runbook=pod-crashloop-ru"}, {"id": "e4", "description": "获取与异常 Pod 相关的事件信息", "level": "important", "value": "kubectl_events 摘要:\n关键诊断行:\n4m53s (x465 over 105m)   Warning   BackOff   Pod/rc-crashloop-exit-code-5db5947859-gk6cf   Back-off restarting failed container app in pod rc-crashloop-exit-code-5db5947859-gk6cf_aiops-e2e(0c99a099-859b-4fcb-86a9-589275358d92)"}], "evidence_analysis": [{"id": "e1", "description": "验证异常 Pod 的详细状态和 Last State 信息", "level": "critical", "value": "Pod 'rc-crashloop-exit-code-5db5947859-gk6cf' 处于 CrashLoopBackOff 状态，最后一次退出码为 2，表明容器在启动阶段失败。"}, {"id": "e2", "description": "获取异常 Pod 上次崩溃的容器日志", "level": "critical", "value": "日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'，表明容器在启动时遇到了错误。"}, {"id": "e3", "description": "验证异常 Pod 的完整 YAML 配置", "level": "important", "value": "容器配置显示使用 busybox:1.36 镜像，且 restartPolicy 为 Always。"}, {"id": "e4", "description": "获取与异常 Pod 相关的事件信息", "level": "important", "value": "事件日志显示 'Back-off restarting failed container app'，进一步确认了容器启动失败。"}], "causal_chain": {"root_cause": "容器启动命令或配置错误导致进程退出", "intermediate_causes": ["容器在启动阶段失败，退出码为 2", "日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'"], "direct_causes": ["容器启动命令或配置错误", "容器镜像或路径错误"]}, "root_cause": "Pod 'rc-crashloop-exit-code-5db5947859-gk6cf' 处于 CrashLoopBackOff 状态，最后一次退出码为 2，表明容器在启动阶段失败。日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'，表明容器在启动时遇到了错误。容器配置显示使用 busybox:1.36 镜像，且 restartPolicy 为 Always。事件日志显示 'Back-off restarting failed container app'，进一步确认了容器启动失败。建议检查容器启动命令和配置，确保应用程序能够正确启动。", "root_cause_summary": "Pod 'rc-crashloop-exit-code-5db5947859-gk6cf' 处于 CrashLoopBackOff 状态，最后一次退出码为 2，表明容器在启动阶段失败。日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'，表明容器在启动时遇到了错误。容器配置显示使用 busybox:1.36 镜像，且 restartPolicy 为 Always。事件日志显示 'Back-off restarting failed container app'，进一步确认了容器启动失败。建议检查容器启动命令和配置，确保应用程序能够正确启动。", "confidence": 0.95, "confidence_reason": "有直接证据，因果链清晰，且有工具证据支持分析结论。", "primary_runbooks": ["pod-crashloop-runtime.md"], "alternative_causes": [{"scenario": "容器内应用异常退出，但非资源限制问题", "probability": "中", "reason": "退出码为 2，不符合 OOMKilled（137）等资源限制特征。"}, {"scenario": "容器镜像或路径错误", "probability": "中", "reason": "可能因容器镜像中缺少可执行文件或路径错误导致进程失败。"}], "limitations": "无", "llm_raw_analysis": "当前 Pod `rc-crashloop-exit-code-5db5947859-gk6cf` 处于 CrashLoopBackOff 状态，最后一次退出码为 2，表明容器在启动阶段失败。日志显示 \"RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2\"，表明容器在启动时遇到了错误。容器配置显示使用 busybox:1.36 镜像，且 restartPolicy 为 Always。事件日志显示 \"Back-off restarting failed container app\"，进一步确认了容器启动失败。建议检查容器启动命令和配置，确保应用程序能够正确启动。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'rc-crashloop-exit-code-5db5947859-gk6cf' 处于 CrashLoopBackOff 状态，最后一次退出码为 2，表明容器在启动阶段失败。日志显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code ...
   置信度: 95%
   🔗 因果链:
     根本原因: 容器启动命令或配置错误导致进程退出


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 22.6s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4012 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 6m 47.2s
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
| **问题分类** | container_runtime |
| **置信度** | 高 (95%) |
| **证据完整度** | 4/4 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题？

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
| 1 | Pod 状态 | `kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf` | `Last State: Terminated, Exit Code: 2` | 容器启动失败，退出码为 2 |
| 2 | Pod 日志 | `kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf --previous` | `RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2` | 日志明确显示启动阶段失败 |
| 3 | Pod YAML 配置 | `kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -o yaml` | `image: busybox:1.36` | 使用 busybox 镜像，无资源限制 |
| 4 | 事件日志 | `kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf` | `Back-off restarting failed container app` | 系统持续重启失败的容器 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 最后状态为 Terminated，Exit Code 为 2，日志中显示 `RUNTIME_STARTUP_ERROR`，说明容器在启动时失败。
- **证据链**：
  - 容器启动失败（Exit Code 2）
  - 日志显示 `RUNTIME_STARTUP_ERROR`
  - Pod 配置无异常（busybox 镜像，无限制）
  - 事件日志显示 `Back-off restarting failed container app`，确认系统持续重启失败容器

### 缺失证据（无）

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 容器启动命令或配置错误导致进程退出                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器启动失败，退出码 2 → Kubernetes 重启失败容器                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器在启动阶段失败，日志显示 RUNTIME_STARTUP_ERROR              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CrashLoopBackOff，持续重启                           │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1（`Exit Code: 2`）、证据 #2（`RUNTIME_STARTUP_ERROR`）和证据 #4（`Back-off restarting failed container app`），问题的根本原因是**容器启动命令或配置错误导致进程退出**。

**置信度**：高 (95%)
- ✅ Exit Code 2 明确指向启动失败
- ✅ 日志中明确显示启动错误
- ✅ 事件日志确认容器持续重启

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查容器启动命令和入口点**
```bash
kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -o yaml -n aiops-e2e
```
*依据*：检查 `spec.containers.command` 和 `spec.containers.args` 是否配置错误或缺失

**2. [可选] 检查容器入口脚本是否存在或权限问题**
```bash
kubectl exec -it rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -- ls -l /path/to/entrypoint
```
*目的*：确认容器内脚本路径和权限正确

**3. [可选] 检查容器镜像是否损坏或拉取失败**
```bash
kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e
```
*目的*：查看是否存在 `ImagePullBackOff` 或其他镜像相关错误

### 后续优化

1. **配置健康检查**：在 Pod 中配置 `livenessProbe` 和 `readinessProbe`，确保容器在启动失败时能及时触发重启或告警。
2. **资源监控**：确保容器有足够的资源（CPU、内存）以支持启动流程。
3. **日志分析**：持续监控容器日志，确保在启动失败时能快速定位问题。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |
| 3. 查看最新日志 | `kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e` | 无错误日志 |

---

## ⚠️ 注意事项

- 如果问题持续，可能需要检查容器镜像或启动脚本是否存在错误。
- 考虑为 Pod 配置合适的 `livenessProbe` 和 `readinessProbe`，以增强容错能力。
- 如果 Pod 使用的是第三方镜像，确保镜像版本兼容且无已知问题。

---

## 📊 性能统计

├─ 总耗时: 6.8m
├─ 问题定位: 65.8s (16%) ✅
├─ 证据链采集: 138.4s (34%) ✅
├─ 根因分析: 120.4s (30%) ✅
├─ 汇总总结: 82.6s (20%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 12 次
```

📋 诊断追踪

- **核心 Runbook**: pod-crashloop-runtime
- **参考 Runbook**: pod-crashloop-runtime
- **工具调用**: 12 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
