======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: e1a571b21c4c4744]

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
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-crashloop-exit-code-5db5947859-gk6cf
namespace: aiops-e2e
creationTimestamp: 2026-05-14T13:49:22Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: No
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
3m40s (x161 over 38m)   Warning   BackOff          Pod/rc-crashloop-exit-code-5db5947859-gk6cf   Back-off restarting failed container app in pod rc-crashloop-exit-code-5db594
   💭 [问题定位] {
  "layer": "L2",
  "derived_layer": "L2",
  "layers": [
    "L2"
  ],
  "layer_name": "CrashLoopBackOffRuntime",
  "confidence": 0.98,
  "reasoning": "异常 Pod rc-crashloop-exit-code-5db5947859-gk6cf 状态为 CrashLoopBackOff，且 containerStatuses 的 exitCode=2，日志中显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'。结合 kubectl describe Pod 的信息，容器反复退出是由于进程启动失败导致。事件信息进一步确认了 BackOff 重启失败，符合 CrashLoopBackOffRuntime 的诊断特征。",
  "abnormal_pods": [
    "rc-crashloop-exit-code-5db5947859-gk6cf"
  ],
  "abnormal_groups": [
    "CrashLoopBackOffRuntime"
  ],
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "CrashLoopBackOffRuntime",
  "status_category": "CrashLoopBackOffRuntime",
  "key_entities": [
    "Pod/rc-crashloop-exit-code-5db5947859-gk6cf",
    "Container/app",
    "ExitCode/2",
    "Reason/CrashLoopBackOff"
  ],
  "possible_scenarios": [
    "容器主进程启动失败，导致容器退出并触发控制器重启",
    "镜像或命令配置错误，容器无法正常运行",
    "容器内应用因错误退出，控制器反复尝试拉起"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 42.0s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[{'scenario': '容器主进程启动失败，导致容器退出并触发控制器重启', 'probability': '高', 'reason': "日志中显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'"}, {'scenario': '镜像或命令配置错误，容器无法正常运行', 'probability': '高', 'reason': 'kubectl describe Pod 显示 Exit Code=2'}, {'scenario': '容器内应用因错误退出，控制器反复尝试拉起', 'probability': '高', 'reason': "事件信息显示 'Back-off restarting failed container app'"}]
   entities=[{"type": "Pod", "name": "rc-crashloop-exit-code-5db5947859-gk6cf", "namespace": "aiops-e2e"}, {"type": "Container", "name": "app", "namespace": "aiops-e2e"}, {"type": "ExitCode", "name": "2", "namespace": "aiops-e2e"}, {"type": "Reason", "name": "CrashLoopBackOff", "namespace": "aiops-e2e"}]
   reasoning=异常 Pod rc-crashloop-exit-code-5db5947859-gk6cf 状态为 CrashLoopBackOff，且 containerStatuses 的 exitCode=2，日志中显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'。结合 kubectl describe Pod 的信息，容器反复退出是由于进程启动失败导致。事件信息进一步确认了 BackOff 重启失败，符合 CrashLoopBackOffRuntime 的诊断特征。
   layer_analysis={"layer": "L2", "derived_layer": "L2", "layers": ["L2"], "layer_name": "CrashLoopBackOffRuntime", "confidence": 0.98, "reasoning": "异常 Pod rc-crashloop-exit-code-5db5947859-gk6cf 状态为 CrashLoopBackOff，且 containerStatuses 的 exitCode=2，日志中显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'。结合 kubectl describe Pod 的信息，容器反复退出是由于进程启动失败导致。事件信息进一步确认了 BackOff 重启失败，符合 CrashLoopBackOffRuntime 的诊断特征。", "abnormal_pods": [{"name": "rc-crashloop-exit-code-5db5947859-gk6cf", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "CrashLoopBackOffRuntime", "status_category": "container_runtime", "key_entities": [{"type": "Pod", "name": "rc-crashloop-exit-code-5db5947859-gk6cf", "namespace": "aiops-e2e"}, {"type": "Container", "name": "app", "namespace": "aiops-e2e"}, {"type": "ExitCode", "name": "2", "namespace": "aiops-e2e"}, {"type": "Reason", "name": "CrashLoopBackOff", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "容器主进程启动失败，导致容器退出并触发控制器重启", "probability": "高", "reason": "日志中显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'"}, {"scenario": "镜像或命令配置错误，容器无法正常运行", "probability": "高", "reason": "kubectl describe Pod 显示 Exit Code=2"}, {"scenario": "容器内应用因错误退出，控制器反复尝试拉起", "probability": "高", "reason": "事件信息显示 'Back-off restarting failed container app'"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-exit-code-5db5947859-gk6cf"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-exit-code-5db5947859-gk6cf"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-crashloop-exit-code-5db5947859-gk6cf             0/1     CrashLoopBackOff   12 (2m5s ago)   38m    172.16.166.139   node1    <none>           <none>            app=rc-crashloop-exit-code,pod-template-hash=5db5947859,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/e1a571b21c4c4744/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/e1a571b21c4c4744/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/e1a571b21c4c4744/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L2
   置信度: 98%

📍 [证据链采集] 执行中...
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
   💭 [证据链采集] 已采集证据：通过 `kubectl describe pod` 验证了异常 Pod 的状态为 CrashLoopBackOff，容器退出码为 2，最后一次状态为 Terminated，符合 CrashLoopBackOffRuntime 的特征。
   ✅ [证据链采集] 完成 (1m 27.7s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 的详细描述信息，验证其 Last State、Exit Code、Reason 和重启次数等关键信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e","tool_args":{"pod":"rc-crashloop-exit-code-5db5947859-gk6cf","namespace":"aiops-e2e"},"purpose":"验证异常 Pod 的 Last State、Exit Code 和 Reason，确认其是否符合 CrashLoopBackOffRuntime 的特征","evidence_type":"Pod status and configuration","target_scope":"aiops-e2e/rc-crashloop-exit-code-5db5947859-gk6cf","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-crashloop-exit-code-5db5947859-gk6cf\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n                  pod_abnormal_type=CrashLoopBackOffRuntime\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         86s (x184 over 41m)  kubelet            Back-off restarting failed container app in pod rc-crashloop-exit-code-5db5947859-gk6cf_aiops-e2e(0c99a099-859b-4fcb-86a9-589275358d92)\n                  cni.projectcalico.org/containerID: 6f43a4e9bdd30cfd305f143fe7d94201cfbfbb4a8154bbc5ffcc20aafd24bc3a\n                  cni.projectcalico.org/podIP: 172.16.166.139/32\n                  cni.projectcalico.org/podIPs: 172.16.166.139/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    2","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e1a571b21c4c4744/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e1a571b21c4c4744/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e1a571b21c4c4744/tools/001-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"已采集证据：通过 `kubectl describe pod` 验证了异常 Pod 的状态为 CrashLoopBackOff，容器退出码为 2，最后一次状态为 Terminated，符合 CrashLoopBackOffRuntime 的特征。","collection_summary":"计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%；其中真实环境证据 6/6 项，完整度 100%；实际执行工具 6 个，匹配计划 1 个，未规划证据 5 个","plan_total":1,"plan_collected":1,"plan_completeness":1.0,"environment_evidence_total":6,"environment_evidence_collected":6,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":1,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 的详细描述信息，验证其 Last State、Exit Code、Reason 和重启次数等关键信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e","purpose":"验证异常 Pod 的 Last State、Exit Code 和 Reason，确认其是否符合 CrashLoopBackOffRuntime 的特征","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/1 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取异常 Pod 的详细描述信息，验证其 Last State、Exit Code、Rea... | `kubectl describe pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (46.0s)
   📤 → 下游数据: root_cause=根因是容器主进程启动失败，导致容器退出并触发控制器重启。具体证据包括容器退出码为 2，kubectl describe Pod 显示容器状态为 Terminated，且有 CrashLoopBackOff 事件。
   confidence=98%
   causal_chain={"root_cause": "容器主进程启动失败，导致容器退出并触发控制器重启", "intermediate_causes": ["容器退出码为 2，表明容器启动失败", "kubectl describe Pod 显示容器状态为 Terminated，且有 CrashLoopBackOff 事件"], "immediate_causes": ["容器主进程启动失败", "控制器检测到容器失败并尝试重启"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [{"tool": "kubectl_describe", "summary": "Pod rc-crashloop-exit-code-5db5947859-gk6cf 的状态为 CrashLoopBackOff，容器退出码为 2，最后一次状态为 Terminated，表明容器启动失败。", "raw_data": "name: rc-crashloop-exit-code-5db5947859-gk6cf\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n                  pod_abnormal_type=CrashLoopBackOffRuntime\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         86s (x184 over 41m)  kubelet            Back-off restarting failed container app in pod rc-crashloop-exit-code-5db5947859-gk6cf_aiops-e2e(0c99a099-859b-4fcb-86a9-589275358d92)"}], "causal_chain": {"root_cause": "容器主进程启动失败，导致容器退出并触发控制器重启", "intermediate_causes": ["容器退出码为 2，表明容器启动失败", "kubectl describe Pod 显示容器状态为 Terminated，且有 CrashLoopBackOff 事件"], "immediate_causes": ["容器主进程启动失败", "控制器检测到容器失败并尝试重启"]}, "root_cause": "根因是容器主进程启动失败，导致容器退出并触发控制器重启。具体证据包括容器退出码为 2，kubectl describe Pod 显示容器状态为 Terminated，且有 CrashLoopBackOff 事件。", "root_cause_summary": "根因是容器主进程启动失败，导致容器退出并触发控制器重启。具体证据包括容器退出码为 2，kubectl describe Pod 显示容器状态为 Terminated，且有 CrashLoopBackOff 事件。", "confidence": 0.98, "confidence_reason": "有直接证据，因果链清晰", "primary_runbooks": ["pod-crashloop-runtime.md"], "alternative_causes": [], "limitations": "没有进一步的证据表明其他可能的原因，如镜像或命令配置错误，需要进一步检查容器的启动命令和配置。", "llm_raw_analysis": "根据提供的证据，可以确定异常 Pod rc-crashloop-exit-code-5db5947859-gk6cf 的状态为 CrashLoopBackOff，且容器退出码为 2。日志中显示 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'，表明容器主进程启动失败。kubectl describe Pod 的信息进一步确认了 BackOff 重启失败，符合 CrashLoopBackOffRuntime 的诊断特征。因此，根因是容器主进程启动失败，导致容器退出并触发控制器重启。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 根因是容器主进程启动失败，导致容器退出并触发控制器重启。具体证据包括容器退出码为 2，kubectl describe Pod 显示容器状态为 Terminated，且有 CrashLoopBackOff 事件。
   置信度: 98%
   🔗 因果链:
     根本原因: 容器主进程启动失败，导致容器退出并触发控制器重启


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 35.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4518 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 31.1s
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
| **问题分类** | CrashLoopBackOffRuntime（容器启动失败） |
| **置信度** | 高 (98%) |
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
| 1 | Pod 状态 | kubectl get pod | `STATUS: CrashLoopBackOff, RESTARTS: 12 (2m5s ago)` | 容器持续重启，处于崩溃循环状态 |
| 2 | 退出码 | kubectl describe pod | `Exit Code: 2, Reason: Error` | 容器主进程以错误码 2 退出，表明启动失败 |
| 3 | 崩溃前日志 | kubectl logs ... --previous | `RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2` | 明确提示启动失败 |
| 4 | K8s 事件 | kubectl describe pod | `Warning BackOff Pod/rc-crashloop-exit-code-5db5947859-gk6cf Back-off restarting failed container app` | 控制器持续尝试拉起失败容器 |
| 5 | Pod YAML 配置 | kubectl get pod -o yaml | `restartPolicy: Always` | 容器失败后会持续重启 |
| 6 | Runbook 诊断 | fetch_runbook | `Pod异常类型: CrashLoopBackOffRuntime | 典型状态: CrashLoopBackOff | 兼容分类: container_runtime` | 与当前情况高度匹配 |

### 证据关联分析
- **证据 #1 + #2 印证**：Pod 状态为 CrashLoopBackOff，Exit Code=2，确认容器启动失败。
- **证据 #3 印证**：崩溃前日志明确指出 `RUNTIME_STARTUP_ERROR`，进一步确认启动失败。
- **证据 #4 印证**：Kubernetes 事件记录了控制器持续尝试重启失败容器。
- **证据 #5 印证**：`restartPolicy: Always` 说明容器失败后会持续尝试重启。
- **证据 #6 印证**：Runbook 明确指出此为典型的 `CrashLoopBackOffRuntime`，即容器启动失败导致崩溃循环。

---

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 容器主进程启动失败，导致容器退出并触发控制器重启                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器启动失败 (Exit Code=2) → 控制器尝试重启 → 重启失败 → 崩溃循环 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器以 Exit Code=2 退出，日志显示 RUNTIME_STARTUP_ERROR        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CrashLoopBackOff，重启次数不断增加                  │
└─────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #1 (Pod 状态为 `CrashLoopBackOff`)、证据 #2 (Exit Code=2)、证据 #3 (日志显示 `RUNTIME_STARTUP_ERROR`) 和证据 #4 (事件显示 `Back-off restarting failed container`)，问题的根本原因是 **容器主进程启动失败**，导致 Kubernetes 控制器不断尝试重启容器，进入崩溃循环。
**置信度**：高 (98%)
- ✅ Exit Code=2 明确表明启动失败
- ✅ 日志显示 `RUNTIME_STARTUP_ERROR`
- ✅ 事件显示 `Back-off restarting failed container`
- ⚠️ 缺少容器启动命令和配置信息，无法确认失败的具体原因（如命令错误、权限问题、依赖缺失等）

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 查看容器启动命令和配置**
```bash
kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o jsonpath='{.spec.containers[0].command}'
kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o jsonpath='{.spec.containers[0].args}'
```
*目的*：确认容器启动命令是否正确，是否存在错误参数或路径问题。

**2. [优先] 查看容器镜像是否正确**
```bash
kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o jsonpath='{.spec.containers[0].image}'
```
*目的*：确认镜像名称是否正确，是否可拉取，是否存在版本不兼容问题。

**3. [可选] 检查容器环境变量**
```bash
kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o jsonpath='{.spec.containers[0].env}'
```
*目的*：确认是否缺少关键环境变量或配置错误。

### 后续优化
1. **修复启动脚本/命令**：根据日志和命令配置，修改容器启动方式，确保主进程能正常启动。
2. **添加启动探针（livenessProbe）**：避免无限重启，可定义更合理的健康检查逻辑。
3. **配置日志收集**：确保崩溃日志能被收集，便于快速诊断。
4. **考虑使用 init 容器**：如果启动失败是由于依赖未就绪，可使用 init 容器做前置检查。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e` | STATUS: Running |
| 2. 确认重启次数是否停止增加 | `kubectl get pod rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |
| 3. 确认容器正常运行 | `kubectl logs rc-crashloop-exit-code-5db5947859-gk6cf -n aiops-e2e` | 无错误信息 |

---

## ⚠️ 注意事项
- 如果修复后问题仍存在，建议查看容器启动日志（`kubectl logs --previous`）以确认是否有其他隐藏错误。
- 确保容器主进程不会在启动后立即退出，否则即使修复命令，也会导致重启循环。
- 如果容器是临时任务（非服务型），应考虑使用 Job 或 CronJob 而非 Deployment。

---

## 📊 性能统计

├─ 总耗时: 5.5m
├─ 问题定位: 102.0s (31%) ✅
├─ 证据链采集: 87.7s (27%) ✅
├─ 根因分析: 46.0s (14%) ✅
├─ 汇总总结: 95.3s (29%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 7 次
```

📋 诊断追踪

- **核心 Runbook**: pod-crashloop-runtime
- **参考 Runbook**: pod-crashloop-runtime
- **工具调用**: 7 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
