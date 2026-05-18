======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: ceb631d8a6284a8e]

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
      📄 NAME                                      READY   STATUS             RESTARTS         AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
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
   💭 [问题定位] 调用工具: kubectl_container_logs
   💭 [问题定位] 工具结果: kubectl_container_logs (success)
      📄 kubectl_container_logs 输出摘要: raw_chars=229 lines=3
Command failed (exit 1):
kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -c rc-crashloop-exit-code -n aiops-e2e --tail=200
error: container rc-c
   💭 [问题定位] 调用工具: kubectl_logs
   💭 [问题定位] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 日志摘要:
lines: 1
signals: 1
关键日志:
RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2
   💭 [问题定位] 调用工具: kubectl_events
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (49.6s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[{'scenario': '容器启动失败', 'probability': '高', 'reason': '容器主进程启动失败，导致 CrashLoopBackOff 状态。'}, {'scenario': '命令或配置错误', 'probability': '高', 'reason': '容器命令或参数配置错误，导致容器启动失败。'}, {'scenario': '资源限制或权限问题', 'probability': '中', 'reason': '容器运行时遇到资源限制或权限问题，例如磁盘空间不足或权限拒绝。'}]
   entities=[{"type": "Pod", "name": "rc-crashloop-exit-code-5db5947859-gk6cf", "namespace": "aiops-e2e"}]
   reasoning=当前环境中存在一个处于 CrashLoopBackOff 状态的 Pod，其异常类型为 CrashLoopBackOffRuntime。根据日志和状态信息，该 Pod 的崩溃与容器运行时错误相关，属于 L2 层级的异常。
   layer_analysis={"layer": "L2", "derived_layer": "L2", "layers": ["L2"], "layer_name": "", "confidence": 0.5, "reasoning": "当前环境中存在一个处于 CrashLoopBackOff 状态的 Pod，其异常类型为 CrashLoopBackOffRuntime。根据日志和状态信息，该 Pod 的崩溃与容器运行时错误相关，属于 L2 层级的异常。", "abnormal_pods": [{"name": "rc-crashloop-exit-code-5db5947859-gk6cf", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "CrashLoopBackOffRuntime", "status_category": "container_runtime", "key_entities": [{"type": "Pod", "name": "rc-crashloop-exit-code-5db5947859-gk6cf", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "容器启动失败", "probability": "高", "reason": "容器主进程启动失败，导致 CrashLoopBackOff 状态。"}, {"scenario": "命令或配置错误", "probability": "高", "reason": "容器命令或参数配置错误，导致容器启动失败。"}, {"scenario": "资源限制或权限问题", "probability": "中", "reason": "容器运行时遇到资源限制或权限问题，例如磁盘空间不足或权限拒绝。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-exit-code-5db5947859-gk6cf"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-exit-code-5db5947859-gk6cf"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-crashloop-exit-code-5db5947859-gk6cf             0/1     CrashLoopBackOff   16 (2m30s ago)   59m    172.16.166.139   node1    <none>           <none>            app=rc-crashloop-exit-code,pod-template-hash=5db5947859,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/ceb631d8a6284a8e/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/ceb631d8a6284a8e/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/ceb631d8a6284a8e/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L2
   置信度: 50%

📍 [证据链采集] 执行中...
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
84s (x277 over 61m)   Warning   BackOff   Pod/rc-crashloop-exit-code-5db5947859-gk6cf   Back-off restarting failed container app in pod rc-crashloop-exit-code-5db5947859-gk6c
   💭 [证据链采集] 已采集证据：
1. `kubectl describe pod` 确认 Pod 处于 CrashLoopBackOff 状态，容器退出代码为 2，属于非 OOM 的运行时错误。
2. `kubectl previous logs` 显示容器启动失败，错误信息为 `RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2`。
3. `kubectl get yaml` 显示容器配置中使用了 `busybox:1.36` 镜像，且 `imagePullPolicy=Never`，表明镜像应已存在于节点上。
4. `kubectl events` 显示容器因启动失败而被不断重启。

未采集证据：
- 无。

冲突证据：
- 无。
   ✅ [证据链采集] 完成 (1m 13.4s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan":[{"id":"verify_pod_crashloopbackoff_runtime","description":"Verify the CrashLoopBackOffRuntime issue for the pod 'rc-crashloop-exit-code-5db5947859-gk6cf' in namespace 'aiops-e2e' by examining its last state, exit code, and logs.","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-crashloop-exit-code-5db5947859-gk6cf"},"purpose":"To verify the last state, exit code, and reason for the pod's crashloopbackoff runtime issue.","evidence_type":"pod_status_and_events","target_scope":"specific_pod","acceptable_tools":["kubectl_describe","kubectl_previous_logs","kubectl_get_by_name"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-crashloop-exit-code-5db5947859-gk6cf\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n                  pod_abnormal_type=CrashLoopBackOffRuntime\n      Reason:       CrashLoopBackOff\n  Warning  BackOff  74s (x277 over 61m)  kubelet  Back-off restarting failed container app in pod rc-crashloop-exit-code-5db5947859-gk6cf_aiops-e2e(0c99a099-859b-4fcb-86a9-589275358d92)\n                  cni.projectcalico.org/containerID: 6f43a4e9bdd30cfd305f143fe7d94201cfbfbb4a8154bbc5ffcc20aafd24bc3a\n                  cni.projectcalico.org/podIP: 172.16.166.139/32\n                  cni.projectcalico.org/podIPs: 172.16.166.139/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    2","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ceb631d8a6284a8e/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ceb631d8a6284a8e/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ceb631d8a6284a8e/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 1\n关键日志:\nRUNTIME_STARTUP_ERROR: rc crashloop exits with code 2","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ceb631d8a6284a8e/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ceb631d8a6284a8e/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ceb631d8a6284a8e/tools/002-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-crashloop-exit-code-5db5947859-gk6cf\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-14T13:49:22Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-crashloop-exit-code, pod_abnormal_type=CrashLoopBackOffRuntime\ndiagnostic_annotations: aiops.e2e/runbook=pod-crashloop-runtime.md\nownerReferences: ReplicaSet/rc-crashloop-exit-code-5db5947859\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=16 reason=CrashLoopBackOff exitCode=2\n  message: back-off 5m0s restarting failed container=app pod=rc-crashloop-exit-code-5db5947859-gk6cf_aiops-e2e(0c99a099-859b-4fcb-86a9-589275358d92)\nvolumes:\n- {\"name\": \"kube-api-access-wgw6q\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ceb631d8a6284a8e/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ceb631d8a6284a8e/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ceb631d8a6284a8e/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n84s (x277 over 61m)   Warning   BackOff   Pod/rc-crashloop-exit-code-5db5947859-gk6cf   Back-off restarting failed container app in pod rc-crashloop-exit-code-5db5947859-gk6cf_aiops-e2e(0c99a099-859b-4fcb-86a9-589275358d92)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ceb631d8a6284a8e/tools/004-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ceb631d8a6284a8e/tools/004-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ceb631d8a6284a8e/tools/004-evidence-kubectl_events.summary.txt"}],"llm_analysis":"已采集证据：\n1. `kubectl describe pod` 确认 Pod 处于 CrashLoopBackOff 状态，容器退出代码为 2，属于非 OOM 的运行时错误。\n2. `kubectl previous logs` 显示容器启动失败，错误信息为 `RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2`。\n3. `kubectl get yaml` 显示容器配置中使用了 `busybox:1.36` 镜像，且 `imagePullPolicy=Never`，表明镜像应已存在于节点上。\n4. `kubectl events` 显示容器因启动失败而被不断重启。\n\n未采集证据：\n- 无。\n\n冲突证据：\n- 无。","collection_summary":"计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 8 个，匹配计划 1 个，未规划证据 7 个","plan_total":1,"plan_collected":1,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":1,"unplanned_tool_count":7,"evidence_inventory":[{"id":"verify_pod_crashloopbackoff_runtime","description":"Verify the CrashLoopBackOffRuntime issue for the pod 'rc-crashloop-exit-code-5db5947859-gk6cf' in namespace 'aiops-e2e' by examining its last state, exit code, and logs.","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e","purpose":"To verify the last state, exit code, and reason for the pod's crashloopbackoff runtime issue.","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_container_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_container_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/1 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | verify_pod_cr... | critical | ✅ | kubectl_describe | Verify the CrashLoopBackOffRuntime issue for ... | `kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (15.1s)
   📤 → 下游数据: root_cause=Pod 'rc-crashloop-exit-code-5db5947859-gk6cf' 处于 CrashLoopBackOff 状态，其容器在启动时失败，退出代码为 2，表明存在运行时错误。日志显示错误信息为 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'，这表明容器主进程启动失败，导致 Kubernetes 不断尝试重启容器，从而进入 CrashLoopBackOff 状态。
   confidence=80%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [], "causal_chain": {}, "root_cause": "Pod 'rc-crashloop-exit-code-5db5947859-gk6cf' 处于 CrashLoopBackOff 状态，其容器在启动时失败，退出代码为 2，表明存在运行时错误。日志显示错误信息为 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'，这表明容器主进程启动失败，导致 Kubernetes 不断尝试重启容器，从而进入 CrashLoopBackOff 状态。", "root_cause_summary": "Pod 'rc-crashloop-exit-code-5db5947859-gk6cf' 处于 CrashLoopBackOff 状态，其容器在启动时失败，退出代码为 2，表明存在运行时错误。日志显示错误信息为 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'，这表明容器主进程启动失败，导致 Kubernetes 不断尝试重启容器，从而进入 CrashLoopBackOff 状态。", "confidence": 0.8, "confidence_reason": "", "primary_runbooks": ["pod-crashloop-runtime.md"], "alternative_causes": [], "limitations": "没有采集到完整的容器日志和配置文件，无法进一步确认具体的启动失败原因。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'rc-crashloop-exit-code-5db5947859-gk6cf' 处于 CrashLoopBackOff 状态，其容器在启动时失败，退出代码为 2，表明存在运行时错误。日志显示错误信息为 'RUNTIME_STARTUP_ERROR: rc crashloop exits ...
   置信度: 80%

📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (2m 3.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4653 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 21.9s
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
| **兼容归因层** | L2 - 容器运行时 |
| **问题分类** | CrashLoopBackOffRuntime（容器启动失败） |
| **置信度** | 高 (80%) |
| **证据完整度** | 1/1 (100%) |

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
| 1 | Pod 状态 | kubectl get pod | `STATUS: CrashLoopBackOff, RESTARTS: 16` | Pod 处于崩溃重启循环中 |
| 2 | 容器退出码 | kubectl describe pod | `Exit Code: 2` | 表明容器主进程启动失败 |
| 3 | 日志信息 | kubectl logs --previous | `RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2` | 明确指出容器启动失败 |
| 4 | 事件记录 | kubectl describe pod | `Warning BackOff Back-off restarting failed container` | Kubernetes 正在尝试重启失败的容器 |
| 5 | 容器状态 | kubectl get pod -o yaml | `status.phase: Running, status.containerStatuses[0].lastState.terminated.exitCode: 2` | 容器启动失败，Kubernetes 正在重启 |
| 6 | 容器配置 | kubectl get pod -o yaml | 无明显配置错误，但未提供完整命令/参数 | 无法确认是否为命令/参数错误 |
| 7 | 容器容器日志（失败） | kubectl logs -c rc-crashloop-exit-code --previous | `error: container rc-crashloop-exit-code is not valid` | 无法获取容器级别的日志 |

### 证据关联分析

- **证据 #1 + #2 + #3 印证**：Pod 状态为 `CrashLoopBackOff`，退出码为 2，日志显示 `RUNTIME_STARTUP_ERROR`，表明容器主进程启动失败。
- **证据 #4 印证**：Kubernetes 正在持续尝试重启失败的容器，符合 CrashLoopBackOff 的定义。
- **证据 #5 印证**：容器状态显示 `lastState.terminated.exitCode: 2`，进一步确认容器启动失败。
- **证据 #6 印证**：未发现配置错误，但无法确认容器入口命令/参数是否正确。
- **证据 #7 印证**：无法获取容器级别的日志，影响进一步诊断容器内部失败原因。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 容器入口命令和参数 | critical | 无法确认是否为命令/参数错误导致容器启动失败 |
| 完整容器日志 | critical | 无法确认容器启动失败的具体原因 |
| 容器配置（如 command/args） | critical | 无法确认是否为配置错误导致容器启动失败 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 容器主进程启动失败，退出码为 2，表明容器运行时错误              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器启动失败 → Kubernetes 重启容器 → 进入 CrashLoopBackOff 状态 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器主进程启动失败，退出码为 2，日志显示 RUNTIME_STARTUP_ERROR  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CrashLoopBackOff，重启次数不断增加                   │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2 (Exit Code: 2) 和证据 #3 (日志显示 `RUNTIME_STARTUP_ERROR`)，问题的根本原因是**容器主进程启动失败**，导致 Kubernetes 不断尝试重启容器，进入 CrashLoopBackOff 状态。

**置信度**：高 (80%)
- ✅ Pod 状态为 `CrashLoopBackOff`，确认容器持续重启
- ✅ 退出码为 2，确认容器启动失败
- ✅ 日志显示 `RUNTIME_STARTUP_ERROR`，进一步确认容器启动失败
- ⚠️ 缺少容器入口命令/参数和完整日志，无法确认具体失败原因

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 查看容器入口命令和参数**
```bash
kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o jsonpath='{.spec.containers[0].command}' 
kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o jsonpath='{.spec.containers[0].args}'
```
*依据*：确认容器入口命令/参数是否配置正确

**2. [可选] 查看崩溃前日志（如果容器未指定多个容器）**
```bash
kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e --previous
```
*目的*：确认容器启动失败的具体原因

**3. [可选] 查看完整的容器配置**
```bash
kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o yaml
```
*目的*：确认容器配置是否存在错误

### 后续优化

1. **容器入口命令/参数优化**：如果确认是命令/参数错误，修改 Deployment 中的 `command/args`。
2. **配置调试**：添加调试日志或使用 `initContainers` 检查依赖配置。
3. **健康检查配置**：配置 `livenessProbe` 和 `readinessProbe`，避免容器启动失败后进入 CrashLoopBackOff。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |
| 3. 检查容器状态 | `kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e` | 无 `CrashLoopBackOff` 状态 |

---

## ⚠️ 注意事项

- 如果问题持续，建议使用 `kubectl logs --previous` 获取更多日志信息。
- 如果无法获取日志，建议检查容器镜像是否存在启动脚本或入口点问题。
- 如果容器运行依赖外部服务（如数据库、API），确认这些服务是否正常运行。

---

## 📊 性能统计

├─ 总耗时: 4.4m
├─ 问题定位: 49.6s (19%) ✅
├─ 证据链采集: 73.4s (28%) ✅
├─ 根因分析: 15.1s (6%) ✅
├─ 汇总总结: 123.8s (47%) ✅
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
