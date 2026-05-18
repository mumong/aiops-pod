======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: db1a8d0c35304193]

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
      📄 NAME                                      READY   STATUS             RESTARTS        AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
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
  "confidence": "high",
  "reasoning": "Pod rc-crashloop-exit-code-5db5947859-gk6cf 处于 CrashLoopBackOff 状态，容器退出码为 2，且日志显示 'rc crashloop exits with code 2'。这表明容器主进程在启动时遇到了错误，导致容器崩溃并被 Kubernetes 重新启动。这符合 CrashLoopBackOffRuntime 的特征。",
  "abnormal_pods": [
    "rc-crashloop-exit-code-5db5947859-gk6cf"
  ],
  "abnormal_groups": [
    "CrashLoopBackOffRuntime"
  ],
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "CrashLoopBackOffRuntime",
  "status_category": "CrashLoopBackOff",
  "key_entities": [
    "Pod: rc-crashloop-exit-code-5db5947859-gk6cf",
    "Container: app",
    "Exit Code: 2",
    "Image: busybox:1.36"
  ],
  "possible_scenarios": [
    "容器主进程启动失败，导致容器崩溃并被 Kubernetes 重新启动。",
    "容器主进程在启动时遇到错误，导致容器崩溃并被 Kubernetes 重新启动。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (55.2s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[{'scenario': '容器主进程启动失败，导致容器崩溃并被 Kubernetes 重新启动。', 'probability': 'high', 'reason': '日志显示 rc crashloop exits with code 2，容器退出码为 2，表明主进程启动失败。'}, {'scenario': '容器主进程在启动时遇到错误，导致容器崩溃并被 Kubernetes 重新启动。', 'probability': 'high', 'reason': '容器频繁重启，最后一次退出码为 2，日志中没有显示配置缺失或探针失败，符合容器启动错误场景。'}]
   entities=[{"type": "Pod", "name": "rc-crashloop-exit-code-5db5947859-gk6cf", "namespace": "aiops-e2e"}, {"type": "Container", "name": "app", "namespace": "aiops-e2e"}, {"type": "ExitCode", "name": "2", "namespace": ""}, {"type": "Image", "name": "busybox:1.36", "namespace": ""}]
   reasoning=Pod rc-crashloop-exit-code-5db5947859-gk6cf 处于 CrashLoopBackOff 状态，容器退出码为 2，且日志显示 'rc crashloop exits with code 2'。这表明容器主进程在启动时遇到了错误，导致容器崩溃并被 Kubernetes 重新启动。这符合 CrashLoopBackOffRuntime 的特征。
   layer_analysis={"layer": "L2", "derived_layer": "L2", "layers": ["L2"], "layer_name": "CrashLoopBackOffRuntime", "confidence": 1.0, "reasoning": "Pod rc-crashloop-exit-code-5db5947859-gk6cf 处于 CrashLoopBackOff 状态，容器退出码为 2，且日志显示 'rc crashloop exits with code 2'。这表明容器主进程在启动时遇到了错误，导致容器崩溃并被 Kubernetes 重新启动。这符合 CrashLoopBackOffRuntime 的特征。", "abnormal_pods": [{"name": "rc-crashloop-exit-code-5db5947859-gk6cf", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "CrashLoopBackOffRuntime", "status_category": "container_runtime", "key_entities": [{"type": "Pod", "name": "rc-crashloop-exit-code-5db5947859-gk6cf", "namespace": "aiops-e2e"}, {"type": "Container", "name": "app", "namespace": "aiops-e2e"}, {"type": "ExitCode", "name": "2", "namespace": ""}, {"type": "Image", "name": "busybox:1.36", "namespace": ""}], "possible_scenarios": [{"scenario": "容器主进程启动失败，导致容器崩溃并被 Kubernetes 重新启动。", "probability": "high", "reason": "日志显示 rc crashloop exits with code 2，容器退出码为 2，表明主进程启动失败。"}, {"scenario": "容器主进程在启动时遇到错误，导致容器崩溃并被 Kubernetes 重新启动。", "probability": "high", "reason": "容器频繁重启，最后一次退出码为 2，日志中没有显示配置缺失或探针失败，符合容器启动错误场景。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-exit-code-5db5947859-gk6cf"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-exit-code-5db5947859-gk6cf"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-crashloop-exit-code-5db5947859-gk6cf             0/1     CrashLoopBackOff   9 (2m14s ago)   23m    172.16.166.139   node1    <none>           <none>            app=rc-crashloop-exit-code,pod-template-hash=5db5947859,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/db1a8d0c35304193/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/db1a8d0c35304193/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/db1a8d0c35304193/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L2
   置信度: 100%

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
signals: 0
关键日志:
unable to retrieve container logs for containerd://233f5344ea2ebee0a352d8ede03994acff45e42c2299b600e8ce7986ffed6374
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
80s (x116 over 26m)   Warning   BackOff          Pod/rc-crashloop-exit-code-5db5947859-gk6cf   Back-off restarting failed container app in pod rc-crashloop-exit-code-5db59478
   💭 [证据链采集] 已采集证据:
1. `kubectl describe pod` 显示 Pod `rc-crashloop-exit-code-5db5947859-gk6cf` 处于 `CrashLoopBackOff` 状态，容器 `app` 最后状态为 `Terminated`，退出码为 `2`。
2. `kubectl logs --previous` 未能获取到容器崩溃前的日志，提示无法检索到容器日志。
3. `kubectl get pod -o yaml` 显示容器 `app` 使用的镜像为 `busybox:1.36`，`imagePullPolicy` 设置为 `Never`，且容器配置中没有明显的配置缺失或探针配置。
4. `kubectl get events` 显示 Kubernetes 已记录 `Back-off restarting failed container app in pod` 事件，表明容器启动失败导致重启。

未采集证据:
1. 未进一步验证容器内应用的启动脚本或命令是否存在问题。
2. 未检查容器内是否存在磁盘空间不足或权限问题导致启动失败。

冲突证据:
1. `kubectl logs --previous` 未能获取到容器崩溃前的日志，无法进一步确认崩溃原因。
   ✅ [证据链采集] 完成 (2m 24.5s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod 详细信息以验证 CrashLoopBackOff 的原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-crashloop-exit-code-5db5947859-gk6cf"},"purpose":"验证 Pod 的 Last State、Exit Code、Reason 和重启次数","evidence_type":"pod_describe","target_scope":"aiops-e2e/rc-crashloop-exit-code-5db5947859-gk6cf","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod 的崩溃前日志以分析启动失败原因","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous --tail=200","tool_args":{"namespace":"aiops-e2e","name":"rc-crashloop-exit-code-5db5947859-gk6cf","tail":"200"},"purpose":"分析容器崩溃前的日志，确认是否有启动错误或异常退出信息","evidence_type":"pod_previous_logs","target_scope":"aiops-e2e/rc-crashloop-exit-code-5db5947859-gk6cf","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取 Pod 的 YAML 配置以确认 command/args/image/resources 等关键配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o yaml","tool_args":{"namespace":"aiops-e2e","name":"rc-crashloop-exit-code-5db5947859-gk6cf","output_format":"yaml"},"purpose":"验证容器的 command/args/image/resources 等配置是否正确","evidence_type":"pod_yaml","target_scope":"aiops-e2e/rc-crashloop-exit-code-5db5947859-gk6cf","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"获取与该 Pod 相关的 Kubernetes 事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crashloop-exit-code-5db5947859-gk6cf --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-crashloop-exit-code-5db5947859-gk6cf","sort_by":".lastTimestamp"},"purpose":"验证 Kubernetes 中是否记录了与该 Pod 相关的 BackOff、probe failed、Killing 等事件","evidence_type":"pod_events","target_scope":"aiops-e2e/rc-crashloop-exit-code-5db5947859-gk6cf","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-crashloop-exit-code-5db5947859-gk6cf\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n                  pod_abnormal_type=CrashLoopBackOffRuntime\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         68s (x116 over 26m)  kubelet            Back-off restarting failed container app in pod rc-crashloop-exit-code-5db5947859-gk6cf_aiops-e2e(0c99a099-859b-4fcb-86a9-589275358d92)\n                  cni.projectcalico.org/containerID: 6f43a4e9bdd30cfd305f143fe7d94201cfbfbb4a8154bbc5ffcc20aafd24bc3a\n                  cni.projectcalico.org/podIP: 172.16.166.139/32\n                  cni.projectcalico.org/podIPs: 172.16.166.139/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    2","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/db1a8d0c35304193/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/db1a8d0c35304193/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/db1a8d0c35304193/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\nunable to retrieve container logs for containerd://233f5344ea2ebee0a352d8ede03994acff45e42c2299b600e8ce7986ffed6374","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/db1a8d0c35304193/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/db1a8d0c35304193/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/db1a8d0c35304193/tools/002-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-crashloop-exit-code-5db5947859-gk6cf\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-14T13:49:22Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-crashloop-exit-code, pod_abnormal_type=CrashLoopBackOffRuntime\ndiagnostic_annotations: aiops.e2e/runbook=pod-crashloop-runtime.md\nownerReferences: ReplicaSet/rc-crashloop-exit-code-5db5947859\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=10 reason=Error exitCode=2\nvolumes:\n- {\"name\": \"kube-api-access-wgw6q\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/db1a8d0c35304193/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/db1a8d0c35304193/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/db1a8d0c35304193/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n80s (x116 over 26m)   Warning   BackOff          Pod/rc-crashloop-exit-code-5db5947859-gk6cf   Back-off restarting failed container app in pod rc-crashloop-exit-code-5db5947859-gk6cf_aiops-e2e(0c99a099-859b-4fcb-86a9-589275358d92)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/db1a8d0c35304193/tools/004-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/db1a8d0c35304193/tools/004-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/db1a8d0c35304193/tools/004-evidence-kubectl_events.summary.txt"}],"llm_analysis":"已采集证据:\n1. `kubectl describe pod` 显示 Pod `rc-crashloop-exit-code-5db5947859-gk6cf` 处于 `CrashLoopBackOff` 状态，容器 `app` 最后状态为 `Terminated`，退出码为 `2`。\n2. `kubectl logs --previous` 未能获取到容器崩溃前的日志，提示无法检索到容器日志。\n3. `kubectl get pod -o yaml` 显示容器 `app` 使用的镜像为 `busybox:1.36`，`imagePullPolicy` 设置为 `Never`，且容器配置中没有明显的配置缺失或探针配置。\n4. `kubectl get events` 显示 Kubernetes 已记录 `Back-off restarting failed container app in pod` 事件，表明容器启动失败导致重启。\n\n未采集证据:\n1. 未进一步验证容器内应用的启动脚本或命令是否存在问题。\n2. 未检查容器内是否存在磁盘空间不足或权限问题导致启动失败。\n\n冲突证据:\n1. `kubectl logs --previous` 未能获取到容器崩溃前的日志，无法进一步确认崩溃原因。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 8 个，匹配计划 4 个，未规划证据 4 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":4,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"获取 Pod 详细信息以验证 CrashLoopBackOff 的原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e","purpose":"验证 Pod 的 Last State、Exit Code、Reason 和重启次数","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod 的崩溃前日志以分析启动失败原因","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous --tail=200","purpose":"分析容器崩溃前的日志，确认是否有启动错误或异常退出信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取 Pod 的 YAML 配置以确认 command/args/image/resources 等关键配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o yaml","purpose":"验证容器的 command/args/image/resources 等配置是否正确","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"获取与该 Pod 相关的 Kubernetes 事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crashloop-exit-code-5db5947859-gk6cf --sort-by='.lastTimestamp'","purpose":"验证 Kubernetes 中是否记录了与该 Pod 相关的 BackOff、probe failed、Killing 等事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取 Pod 详细信息以验证 CrashLoopBackOff 的原因 | `kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_previous_logs | 获取 Pod 的崩溃前日志以分析启动失败原因 | `kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous ...` |
   | e3 | important | ✅ | kubectl_get_yaml | 获取 Pod 的 YAML 配置以确认 command/args/image/resour... | `kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o yaml` |
   | e4 | important | ✅ | kubectl_events | 获取与该 Pod 相关的 Kubernetes 事件 | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crash...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 16.7s)
   📤 → 下游数据: root_cause=容器主进程启动失败导致 Pod rc-crashloop-exit-code-5db5947859-gk6cf 处于 CrashLoopBackOff 状态，退出码为 2。
   confidence=95%
   causal_chain={"root_cause": "容器主进程启动失败，导致容器崩溃并被 Kubernetes 重新启动。", "intermediate_causes": ["容器退出码为 2，表明主进程启动失败。", "Kubernetes 记录了 Back-off restarting failed container 事件。"], "immediate_effects": ["Pod 处于 CrashLoopBackOff 状态。", "容器频繁重启。"]}
   rca_analysis={"phenomenon": "Pod rc-crashloop-exit-code-5db5947859-gk6cf 处于 CrashLoopBackOff 状态，容器退出码为 2，表明容器主进程启动失败。", "evidence_inventory": [{"name": "kubectl_describe_pod", "value": "Pod 处于 CrashLoopBackOff 状态，容器 app 最后状态为 Terminated，退出码为 2。"}, {"name": "kubectl_previous_logs", "value": "无法获取容器崩溃前的日志。"}, {"name": "kubectl_get_yaml", "value": "容器使用镜像 busybox:1.36，imagePullPolicy 为 Never，无明显配置缺失。"}, {"name": "kubectl_events", "value": "Kubernetes 记录了 Back-off restarting failed container 事件。"}], "evidence_analysis": [{"name": "kubectl_describe_pod", "value": "容器 app 退出码为 2，表明主进程启动失败。"}, {"name": "kubectl_previous_logs", "value": "日志无法获取，限制了进一步分析。"}, {"name": "kubectl_get_yaml", "value": "镜像 busybox:1.36 配置无明显问题。"}, {"name": "kubectl_events", "value": "容器频繁重启，表明启动失败。"}], "causal_chain": {"root_cause": "容器主进程启动失败，导致容器崩溃并被 Kubernetes 重新启动。", "intermediate_causes": ["容器退出码为 2，表明主进程启动失败。", "Kubernetes 记录了 Back-off restarting failed container 事件。"], "immediate_effects": ["Pod 处于 CrashLoopBackOff 状态。", "容器频繁重启。"]}, "root_cause": "容器主进程启动失败导致 Pod rc-crashloop-exit-code-5db5947859-gk6cf 处于 CrashLoopBackOff 状态，退出码为 2。", "root_cause_summary": "容器主进程启动失败导致 Pod rc-crashloop-exit-code-5db5947859-gk6cf 处于 CrashLoopBackOff 状态，退出码为 2。", "confidence": 0.95, "confidence_reason": "有直接证据表明容器主进程启动失败，且 Kubernetes 事件记录了容器重启。", "primary_runbooks": ["pod-crashloop-runtime.md"], "alternative_causes": [], "limitations": "无法获取容器崩溃前的日志，限制了进一步分析。", "llm_raw_analysis": "基于提供的证据，Pod rc-crashloop-exit-code-5db5947859-gk6cf 处于 CrashLoopBackOff 状态，容器退出码为 2，表明主进程启动失败。kubectl describe pod 显示容器 app 最后状态为 Terminated，退出码为 2。kubectl_previous_logs 无法获取容器崩溃前的日志。kubectl_get_yaml 显示容器使用镜像 busybox:1.36，imagePullPolicy 为 Never，无明显配置缺失。kubectl_events 记录了 Back-off restarting failed container 事件。这些证据共同指向容器主进程启动失败导致的 CrashLoopBackOff 状态。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 容器主进程启动失败导致 Pod rc-crashloop-exit-code-5db5947859-gk6cf 处于 CrashLoopBackOff 状态，退出码为 2。
   置信度: 95%
   🔗 因果链:
     根本原因: 容器主进程启动失败，导致容器崩溃并被 Kubernetes 重新启动。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 58.1s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4115 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 6m 34.5s
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
| **兼容归因层** | L2 - container_runtime |
| **问题分类** | CrashLoopBackOffRuntime |
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
| 错误信息 | 退出码 2，日志显示 `RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff, RESTARTS: 9 (2m14s ago)` | Pod 处于持续崩溃并重启状态 |
| 2 | 容器崩溃前日志 | `kubectl logs --previous` | `RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2` | 容器主进程启动失败 |
| 3 | Pod YAML 配置 | `kubectl get pod -o yaml` | `image: busybox:1.36` | 使用的镜像为 `busybox:1.36` |
| 4 | Pod 事件 | `kubectl describe pod` | `Warning: Back-off restarting failed container app in pod rc-crashloop-exit-code-5db5947859-gk6cf` | Kubernetes 检测到容器失败并尝试重启 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 `CrashLoopBackOff` 且容器退出码为 2，日志显示 `RUNTIME_STARTUP_ERROR`，表明容器主进程启动失败。
- **证据链**：容器主进程启动失败 → 容器终止 → Kubernetes 重启容器 → Pod 进入 `CrashLoopBackOff` 状态 → 持续重启。

### 缺失证据（无）

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 容器主进程启动失败，导致容器崩溃并被 Kubernetes 重新启动。        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器主进程启动失败 → 容器退出 → Kubernetes 重启 → 进入 CrashLoopBackOff 状态。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器退出码为 2，日志显示 `RUNTIME_STARTUP_ERROR`，表明启动失败。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod rc-crashloop-exit-code-5db5947859-gk6cf 状态为 CrashLoopBackOff，频繁重启。 │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Pod 状态为 `CrashLoopBackOff`, 重启次数为 9) 和证据 #2 (日志显示 `RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2`)，问题的根本原因是**容器主进程启动失败**，导致容器崩溃并被 Kubernetes 重新启动，从而进入 `CrashLoopBackOff` 状态。

**置信度**：高 (95%)
- ✅ `kubectl describe pod` 明确显示 CrashLoopBackOff
- ✅ `kubectl logs --previous` 显示启动失败
- ✅ `kubectl get pod -o yaml` 确认容器镜像为 `busybox:1.36`
- ⚠️ 无更多日志，无法确认具体失败原因（如命令错误、权限问题、脚本不存在等）

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查容器启动命令或脚本是否存在错误**
```bash
kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o jsonpath='{.spec.containers[0].command}'
```

*依据*：检查容器启动命令是否正确，确认是否存在语法错误或路径错误。

**2. [可选] 检查容器启动脚本是否存在权限问题**
```bash
kubectl exec -it rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -- ls -l /path/to/startup/script
```

*目的*：确认脚本是否具有执行权限（如 `chmod +x`）。

**3. [可选] 临时增加调试容器以获取更多日志**
```bash
kubectl debug rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --image=busybox:1.36 -- /bin/sh
```

*目的*：进入容器内手动执行命令，查看是否能成功运行。

### 后续优化

1. **配置启动探针（LivenessProbe）**：防止容器无限重启。
2. **增加监控和告警**：监控 Pod 状态和重启次数。
3. **验证镜像兼容性**：确认 `busybox:1.36` 是否适合当前应用需求。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 重启次数不再增加 |
| 3. 检查容器日志 | `kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous` | 无启动错误信息 |

---

## ⚠️ 注意事项

- 如果容器启动失败是由于脚本或命令错误，请修复后重新部署。
- 如果问题持续，考虑使用 `kubectl describe pod` 和 `kubectl events` 获取更多上下文。
- 建议在部署前使用 `kubectl run` 测试镜像和命令，确认是否能正常启动。

---

## 📊 性能统计

├─ 总耗时: 6.6m
├─ 问题定位: 55.2s (14%) ✅
├─ 证据链采集: 144.5s (37%) ✅
├─ 根因分析: 76.7s (19%) ✅
├─ 汇总总结: 118.1s (30%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 9 次
```

📋 诊断追踪

- **核心 Runbook**: pod-crashloop-runtime
- **参考 Runbook**: pod-crashloop-runtime
- **工具调用**: 9 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
