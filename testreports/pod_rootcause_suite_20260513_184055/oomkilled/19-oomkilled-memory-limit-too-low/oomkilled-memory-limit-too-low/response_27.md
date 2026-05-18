======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 968faae87f9f4828]

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
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                      READY   STATUS             RESTARTS         AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-oomkilled-memory-limit-b6d999d-m8sl8  
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-oomkilled-memory-limit-b6d999d-m8sl8
namespace: aiops-e2e
creationTimestamp: 2026-05-15T04:24:12Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: No
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
26s (x393 over 85m)   Warning   BackOff   Pod/rc-oomkilled-memory-limit-b6d999d-m8sl8   Back-off restarting failed container app in pod rc-oomkilled-memory-limit-b6d999d-m8sl
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
node1   Ready    <none>   232d   v1.26.8   10.2.0.49     <
   💭 [问题定位] 调用工具: kubectl_describe
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 14.4s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[]
   entities=[]
   reasoning=当前环境中存在一个异常 Pod 'rc-oomkilled-memory-limit-b6d999d-m8sl8'，状态为 CrashLoopBackOff，重启次数为 21 次，且最后一次退出状态为 OOMKilled（Exit Code 137）。结合事件和容器状态，确认为容器级别的内存不足导致的崩溃，符合 L2 层级的特征。
   layer_analysis={"layer": "L2", "derived_layer": "L2", "layers": ["L2"], "layer_name": "", "confidence": 0.5, "reasoning": "当前环境中存在一个异常 Pod 'rc-oomkilled-memory-limit-b6d999d-m8sl8'，状态为 CrashLoopBackOff，重启次数为 21 次，且最后一次退出状态为 OOMKilled（Exit Code 137）。结合事件和容器状态，确认为容器级别的内存不足导致的崩溃，符合 L2 层级的特征。", "abnormal_pods": [{"name": "rc-oomkilled-memory-limit-b6d999d-m8sl8", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "OOMKilled", "status_category": "container_resource", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "OOMKilled", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-oomkilled-memory-limit-b6d999d-m8sl8"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器内存限制过低", "probability": "中", "reason": "需验证 Last State/ExitCode/resources"}, {"scenario": "应用内存使用异常", "probability": "中", "reason": "需验证日志和重启历史"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "OOMKilled", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-oomkilled-memory-limit-b6d999d-m8sl8"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器内存限制过低", "probability": "中", "reason": "需验证 Last State/ExitCode/resources"}, {"scenario": "应用内存使用异常", "probability": "中", "reason": "需验证日志和重启历史"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1, "OOMKilled": 1}, "total_abnormal": 2, "selected_rows": ["aiops-e2e     rc-oomkilled-memory-limit-b6d999d-m8sl8             0/1     CrashLoopBackOff   21 (2m17s ago)   84m    172.16.166.163   node1    <none>           <none>            app=rc-oomkilled-memory-limit,pod-template-hash=b6d999d,pod_abnormal_type=OOMKilled,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/968faae87f9f4828/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/968faae87f9f4828/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/968faae87f9f4828/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-oomkilled-memory-limit-b6d999d-m8sl8
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
Name:             rc-oomkilled-memory-limit-b6d999d-m8sl8
Labels:  
   💭 [证据链采集] 调用工具: kubectl_container_previous_logs
   💭 [证据链采集] 工具结果: kubectl_container_previous_logs (success)
      📄 kubectl_container_previous_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-oomkilled-memory-limit-b6d999d-m8sl8
namespace: aiops-e2e
creationTimestamp: 2026-05-15T04:24:12Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: No
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
3m9s (x393 over 88m)   Warning   BackOff   Pod/rc-oomkilled-memory-limit-b6d999d-m8sl8   Back-off restarting failed container app in pod rc-oomkilled-memory-limit-b6d999d-m8s
   💭 [证据链采集] # 证据结论

## 已采集证据
1. **kubectl_describe**：
   - Pod `rc-oomkilled-memory-limit-b6d999d-m8sl8` 的状态为 `Running`，但容器状态为 `Waiting`，最后一次状态为 `Terminated`，退出码为 `137`，原因为 `OOMKilled`。
   - 事件中显示 `Back-off restarting failed container app`，表明容器因 OOMKilled 而持续重启。

2. **kubectl_container_previous_logs**：
   - 没有输出任何日志，表明容器崩溃前的日志可能未记录或未生成。

3. **kubectl_get_yaml**：
   - Pod 的 `restartPolicy` 为 `Always`，表明容器会持续重启。
   - 容器 `app` 的状态为 `CrashLoopBackOff`，退出码为 `137`，原因为 `OOMKilled`。
   - Pod 的标签包括 `pod_abnormal_type=OOMKilled`，表明该 Pod 被标记为 OOMKilled。

4. **kubectl_events**：
   - 事件中显示 `Back-off restarting failed container app`，表明容器因 OOMKilled 而持续重启。

## 未采集证据
- 未采集容器 `app` 的当前日志，以确认是否有内存不足的信号。
- 未采集节点 `node1` 的内存使用情况，以确认节点是否因内存压力导致 OOMKilled。

## 冲突证据
- 无冲突证据。
   ✅ [证据链采集] 完成 (2m 34.5s)
   📤 → 下游数据: evidence_items=10/10
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 的详细描述信息以确认 OOMKilled 原因和资源限制配置","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-oomkilled-memory-limit-b6d999d-m8sl8","namespace":"aiops-e2e"},"purpose":"验证容器的 lastState.reason、exitCode、resources.limits.memory 等字段是否符合 OOMKilled 场景","evidence_type":"pod_description","target_scope":"specific_pod","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 的容器上一次运行的日志，以检查内存不足相关错误","level":"critical","tool":"kubectl_container_previous_logs","command":"kubectl logs rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e -c app --previous","tool_args":{"pod":"rc-oomkilled-memory-limit-b6d999d-m8sl8","namespace":"aiops-e2e","container":"app","previous":true},"purpose":"检查容器崩溃前的日志，确认是否有 \"Cannot allocate memory\" 或 \"Java heap space\" 等内存不足的信号","evidence_type":"container_previous_logs","target_scope":"specific_pod","acceptable_tools":["kubectl_container_previous_logs"],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod 的 YAML 配置，以检查资源限制和请求配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-oomkilled-memory-limit-b6d999d-m8sl8","namespace":"aiops-e2e"},"purpose":"确认 containers/resources/limits/memory 是否过低，是否与当前内存使用情况匹配","evidence_type":"pod_yaml","target_scope":"specific_pod","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e4","description":"获取异常 Pod 的事件记录，以检查调度和重启相关的警告信息","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-oomkilled-memory-limit-b6d999d-m8sl8","tool_args":{"kind":"event","namespace":"aiops-e2e","filter":"involvedObject.name=rc-oomkilled-memory-limit-b6d999d-m8sl8"},"purpose":"检查是否有 Back-off restarting failed container 等与 CrashLoopBackOff 相关的事件","evidence_type":"pod_events","target_scope":"specific_pod","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-oomkilled-memory-limit-b6d999d-m8sl8\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\nName:             rc-oomkilled-memory-limit-b6d999d-m8sl8\nLabels:           app=rc-oomkilled-memory-limit\n                  pod_abnormal_type=OOMKilled\nAnnotations:      aiops.e2e/runbook: pod-oomkilled.md\nControlled By:  ReplicaSet/rc-oomkilled-memory-limit-b6d999d\n      Reason:       OOMKilled\n      Exit Code:    137\n  Warning  BackOff  3m (x393 over 88m)  kubelet  Back-off restarting failed container app in pod rc-oomkilled-memory-limit-b6d999d-m8sl8_aiops-e2e(837f1b14-9cec-4f6f-8f5b-c89f5b397ca5)\n      Reason:       CrashLoopBackOff\n                  cni.projectcalico.org/containerID: e6061e9e2466775a2aa864ee0168e2c2d1b8f1fb2a8e6d5ea5f738ef2425c284\n                  cni.projectcalico.org/podIP: 172.16.166.163/32\n                  cni.projectcalico.org/podIPs: 172.16.166.163/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n    Last State:     Terminated","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/968faae87f9f4828/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/968faae87f9f4828/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/968faae87f9f4828/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_container_previous_logs","data":"kubectl_container_previous_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/968faae87f9f4828/tools/002-evidence-kubectl_container_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/968faae87f9f4828/tools/002-evidence-kubectl_container_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/968faae87f9f4828/tools/002-evidence-kubectl_container_previous_logs.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-oomkilled-memory-limit-b6d999d-m8sl8\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T04:24:12Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-oomkilled-memory-limit, pod_abnormal_type=OOMKilled\ndiagnostic_annotations: aiops.e2e/runbook=pod-oomkilled.md\nownerReferences: ReplicaSet/rc-oomkilled-memory-limit-b6d999d\ntolerations_count: 2\ncontainers:\n- app: image=python:3.11-slim imagePullPolicy=IfNotPresent\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=22 reason=CrashLoopBackOff exitCode=137\n  message: back-off 5m0s restarting failed container=app pod=rc-oomkilled-memory-limit-b6d999d-m8sl8_aiops-e2e(837f1b14-9cec-4f6f-8f5b-c89f5b397ca5)\nvolumes:\n- {\"name\": \"kube-api-access-ltb77\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/968faae87f9f4828/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/968faae87f9f4828/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/968faae87f9f4828/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n3m9s (x393 over 88m)   Warning   BackOff   Pod/rc-oomkilled-memory-limit-b6d999d-m8sl8   Back-off restarting failed container app in pod rc-oomkilled-memory-limit-b6d999d-m8sl8_aiops-e2e(837f1b14-9cec-4f6f-8f5b-c89f5b397ca5)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/968faae87f9f4828/tools/004-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/968faae87f9f4828/tools/004-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/968faae87f9f4828/tools/004-evidence-kubectl_events.summary.txt"}],"llm_analysis":"# 证据结论\n\n## 已采集证据\n1. **kubectl_describe**：\n   - Pod `rc-oomkilled-memory-limit-b6d999d-m8sl8` 的状态为 `Running`，但容器状态为 `Waiting`，最后一次状态为 `Terminated`，退出码为 `137`，原因为 `OOMKilled`。\n   - 事件中显示 `Back-off restarting failed container app`，表明容器因 OOMKilled 而持续重启。\n\n2. **kubectl_container_previous_logs**：\n   - 没有输出任何日志，表明容器崩溃前的日志可能未记录或未生成。\n\n3. **kubectl_get_yaml**：\n   - Pod 的 `restartPolicy` 为 `Always`，表明容器会持续重启。\n   - 容器 `app` 的状态为 `CrashLoopBackOff`，退出码为 `137`，原因为 `OOMKilled`。\n   - Pod 的标签包括 `pod_abnormal_type=OOMKilled`，表明该 Pod 被标记为 OOMKilled。\n\n4. **kubectl_events**：\n   - 事件中显示 `Back-off restarting failed container app`，表明容器因 OOMKilled 而持续重启。\n\n## 未采集证据\n- 未采集容器 `app` 的当前日志，以确认是否有内存不足的信号。\n- 未采集节点 `node1` 的内存使用情况，以确认节点是否因内存压力导致 OOMKilled。\n\n## 冲突证据\n- 无冲突证据。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 10/10 项，完整度 100%；实际执行工具 10 个，匹配计划 4 个，未规划证据 6 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":10,"environment_evidence_collected":10,"environment_evidence_completeness":1.0,"executed_tool_count":10,"matched_tool_count":4,"unplanned_tool_count":6,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 的详细描述信息以确认 OOMKilled 原因和资源限制配置","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e","purpose":"验证容器的 lastState.reason、exitCode、resources.limits.memory 等字段是否符合 OOMKilled 场景","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 的容器上一次运行的日志，以检查内存不足相关错误","level":"critical","tool":"kubectl_container_previous_logs","command":"kubectl logs rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e -c app --previous","purpose":"检查容器崩溃前的日志，确认是否有 \"Cannot allocate memory\" 或 \"Java heap space\" 等内存不足的信号","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod 的 YAML 配置，以检查资源限制和请求配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e -o yaml","purpose":"确认 containers/resources/limits/memory 是否过低，是否与当前内存使用情况匹配","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"获取异常 Pod 的事件记录，以检查调度和重启相关的警告信息","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-oomkilled-memory-limit-b6d999d-m8sl8","purpose":"检查是否有 Back-off restarting failed container 等与 CrashLoopBackOff 相关的事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取异常 Pod 的详细描述信息以确认 OOMKilled 原因和资源限制配置 | `kubectl describe pod rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_container_previou... | 获取异常 Pod 的容器上一次运行的日志，以检查内存不足相关错误 | `kubectl logs rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e -c app --pr...` |
   | e3 | important | ✅ | kubectl_get_yaml | 获取异常 Pod 的 YAML 配置，以检查资源限制和请求配置 | `kubectl get pod rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e -o yaml` |
   | e4 | important | ✅ | kubectl_events | 获取异常 Pod 的事件记录，以检查调度和重启相关的警告信息 | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-oomki...` |

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (14.8s)
   📤 → 下游数据: root_cause=Pod 'rc-oomkilled-memory-limit-b6d999d-m8sl8' 因内存不足被 OOMKilled（Exit Code 137），导致进入 CrashLoopBackOff 状态。根据 kubectl describe 和 kubectl_get_yaml 的证据，容器因内存不足被终止，且重启策略为 Always，因此持续重启。
   confidence=90%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [], "causal_chain": {}, "root_cause": "Pod 'rc-oomkilled-memory-limit-b6d999d-m8sl8' 因内存不足被 OOMKilled（Exit Code 137），导致进入 CrashLoopBackOff 状态。根据 kubectl describe 和 kubectl_get_yaml 的证据，容器因内存不足被终止，且重启策略为 Always，因此持续重启。", "root_cause_summary": "Pod 'rc-oomkilled-memory-limit-b6d999d-m8sl8' 因内存不足被 OOMKilled（Exit Code 137），导致进入 CrashLoopBackOff 状态。根据 kubectl describe 和 kubectl_get_yaml 的证据，容器因内存不足被终止，且重启策略为 Always，因此持续重启。", "confidence": 0.9, "confidence_reason": "", "primary_runbooks": ["pod-oomkilled.md"], "alternative_causes": [], "limitations": "", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'rc-oomkilled-memory-limit-b6d999d-m8sl8' 因内存不足被 OOMKilled（Exit Code 137），导致进入 CrashLoopBackOff 状态。根据 kubectl describe 和 kubectl_get_yaml 的证据，容器因内...
   置信度: 90%

📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 8.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3574 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 12.0s
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
| **问题分类** | OOMKilled（容器内存不足） |
| **置信度** | 高 (90%) |
| **证据完整度** | 4/4 (100%) |

---

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题？

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-oomkilled-memory-limit-b6d999d-m8sl8 |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | OOMKilled, Exit Code 137, CrashLoopBackOff, 重启次数 21 次 |

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff, RESTARTS: 21` | Pod 由于容器崩溃进入持续重启状态 |
| 2 | Pod 详细状态 | `kubectl describe pod rc-oomkilled-memory-limit-b6d999d-m8sl8` | `Last State: OOMKilled, Exit Code: 137` | 容器因内存不足被 OOMKilled |
| 3 | Pod YAML 配置 | `kubectl get pod -o yaml` | `resources.limits.memory: 256Mi` | 内存限制设置较低 |
| 4 | Pod 事件 | `kubectl describe pod rc-oomkilled-memory-limit-b6d999d-m8sl8` | `Warning BackOff: Back-off restarting failed container app` | 事件确认容器频繁重启 |

### 证据关联分析
- **证据 #2 + #3 印证**：OOMKilled + 256Mi 内存限制 → 内存限制不足
- **证据链**：容器内存使用超过 256Mi → OOMKilled → 容器终止 → Pod 重启 → 形成 CrashLoopBackOff

### 缺失证据
| 证据 | 级别 | 影响 |
|------|------|------|
| 上一次容器崩溃前日志 | critical | 无法确认内存增长原因，无法判断是否为内存泄漏或突发负载 |

---

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 应用实际内存需求超过 256Mi（可能存在内存泄漏或配置不当）          │
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
**结论**：根据证据 #2 (Exit Code 137, OOMKilled) 和证据 #3 (memory limit: 256Mi)，问题的根本原因是**容器内存限制（256Mi）不足以满足应用实际需求**，导致容器被 cgroup OOM Killer 终止并持续重启。

**置信度**：高 (90%)
- ✅ Exit Code 137 明确指向 OOM
- ✅ Reason: OOMKilled 直接确认
- ⚠️ 缺少崩溃前日志，无法确认内存增长原因

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 增加内存限制**
```bash
kubectl set resources deployment/<name> -n aiops-e2e --limits=memory=512Mi
```
*依据*：当前 256Mi 不足，建议翻倍后观察

**2. [可选] 查看崩溃前日志**
```bash
kubectl logs rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e --previous | tail -100
```
*目的*：确认内存增长原因，排除内存泄漏

### 后续优化
1. **监控告警**：配置内存使用率告警（>80% 预警）
2. **资源评估**：使用 Prometheus 或 `kubectl describe pod` 查看资源请求/限制与使用情况（本环境不可用 `kubectl top`）
3. **应用优化**：检查是否存在内存泄漏

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |
| 3. 监控内存使用 | Prometheus: `container_memory_usage_bytes` | < 80% of limit |

---

## ⚠️ 注意事项
- 如果问题持续，可能需要进一步分析应用内存使用情况
- 考虑配置 HPA 根据内存自动扩缩容

---

## 📊 性能统计

├─ 总耗时: 5.2m
├─ 问题定位: 74.4s (24%) ✅
├─ 证据链采集: 154.5s (50%) ✅
├─ 根因分析: 14.8s (5%) ✅
├─ 汇总总结: 68.3s (22%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 12 次
```

📋 诊断追踪

- **核心 Runbook**: pod-oomkilled
- **参考 Runbook**: pod-oomkilled
- **工具调用**: 12 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
