======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 55bf425a67164ff3]

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
      📄 NAME                   READY   STATUS             RESTARTS        AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-notready-liveness   0/1     CrashLoopBackOff   10 (2m9s ag
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
   ✅ [问题定位] 完成 (26.0s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[]
   entities=[]
   reasoning=当前环境中存在1个Pod处于CrashLoopBackOff状态，且没有明确的ConfigMap/Secret/env缺失信号，符合L2层的CrashLoopBackOffRuntime异常类型。异常Pod名称为rc-notready-liveness，状态关键字为CrashLoopBackOff，归一化类型为NotReadyProbeFailed，对应状态分类为container_runtime。
   layer_analysis={"layer": "L2", "derived_layer": "", "layers": [], "layer_name": "", "confidence": 0.5, "reasoning": "当前环境中存在1个Pod处于CrashLoopBackOff状态，且没有明确的ConfigMap/Secret/env缺失信号，符合L2层的CrashLoopBackOffRuntime异常类型。异常Pod名称为rc-notready-liveness，状态关键字为CrashLoopBackOff，归一化类型为NotReadyProbeFailed，对应状态分类为container_runtime。", "abnormal_pods": [{"name": "rc-notready-liveness", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "", "status_category": "", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-notready-liveness                                0/1     CrashLoopBackOff   10 (2m4s ago)   17m    172.16.166.164   node1    <none>           <none>            app=rc-notready-liveness,pod_abnormal_type=NotReadyProbeFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/55bf425a67164ff3/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/55bf425a67164ff3/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/55bf425a67164ff3/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
name: rc-notready-liveness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Exit Code:    137
  Warning  Unhealthy       18m (x10 over 20m)    kubelet      
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
   ✅ [证据链采集] 完成 (2m 32.9s)
   📤 → 下游数据: evidence_items=8/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod rc-notready-liveness 的详细信息以验证其状态和原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","tool_args":{"pod":"rc-notready-liveness","namespace":"aiops-e2e"},"purpose":"验证 Pod 的 Last State、Exit Code、Reason、重启次数等关键信息","evidence_type":"state_verification","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod rc-notready-liveness 的崩溃前日志","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-notready-liveness -n aiops-e2e --previous --tail=200","tool_args":{"pod":"rc-notready-liveness","namespace":"aiops-e2e"},"purpose":"验证崩溃前的日志，查找命令错误、进程退出、业务异常等线索","evidence_type":"log_verification","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod rc-notready-liveness 的 YAML 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-liveness -n aiops-e2e -o yaml","tool_args":{"pod":"rc-notready-liveness","namespace":"aiops-e2e"},"purpose":"验证 Pod 的 command/args/image/resources 等配置","evidence_type":"configuration_verification","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"获取与异常 Pod rc-notready-liveness 相关的 Events","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-notready-liveness --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-notready-liveness"},"purpose":"验证 BackOff、probe failed、Killing 等事件","evidence_type":"event_verification","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-liveness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Exit Code:    137\n  Warning  Unhealthy       18m (x10 over 20m)    kubelet            Liveness probe failed: liveness endpoint failed\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         14s (x67 over 16m)    kubelet            Back-off restarting failed container app in pod rc-notready-liveness_aiops-e2e(74fed2e5-116f-4b55-900c-9d0d8b7e83ab)\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\n  Normal   Killing         18m (x3 over 20m)     kubelet            Container app failed liveness probe, will be restarted\nName:             rc-notready-liveness\nLabels:           app=rc-notready-liveness\n                  cni.projectcalico.org/containerID: c311a318e2ee0d3b13fe103b0767abd6b4dd610d9e1aae4c7cf82792fb942255\n                  cni.projectcalico.org/podIP: 172.16.166.164/32\n                  cni.projectcalico.org/podIPs: 172.16.166.164/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n  Normal   Scheduled       20m                   default-scheduler  Successfully assigned aiops-e2e/rc-notready-liveness to node1\n关键状态/事件:\n    State:          Waiting\n    Last State:     Terminated\n      Reason:       Error","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/55bf425a67164ff3/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/55bf425a67164ff3/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/55bf425a67164ff3/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/55bf425a67164ff3/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/55bf425a67164ff3/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/55bf425a67164ff3/tools/002-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-liveness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T11:40:37Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-liveness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=10 reason=CrashLoopBackOff exitCode=137\n  message: back-off 5m0s restarting failed container=app pod=rc-notready-liveness_aiops-e2e(74fed2e5-116f-4b55-900c-9d0d8b7e83ab)\nvolumes:\n- {\"name\": \"kube-api-access-lz5gb\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/55bf425a67164ff3/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/55bf425a67164ff3/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/55bf425a67164ff3/tools/003-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%；其中真实环境证据 8/9 项，完整度 89%；实际执行工具 6 个，匹配计划 3 个，未规划证据 3 个","plan_total":4,"plan_collected":3,"plan_completeness":0.75,"environment_evidence_total":9,"environment_evidence_collected":8,"environment_evidence_completeness":0.8888888888888888,"executed_tool_count":6,"matched_tool_count":3,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod rc-notready-liveness 的详细信息以验证其状态和原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","purpose":"验证 Pod 的 Last State、Exit Code、Reason、重启次数等关键信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod rc-notready-liveness 的崩溃前日志","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-notready-liveness -n aiops-e2e --previous --tail=200","purpose":"验证崩溃前的日志，查找命令错误、进程退出、业务异常等线索","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod rc-notready-liveness 的 YAML 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-liveness -n aiops-e2e -o yaml","purpose":"验证 Pod 的 command/args/image/resources 等配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"获取与异常 Pod rc-notready-liveness 相关的 Events","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-notready-liveness --sort-by='.lastTimestamp'","purpose":"验证 BackOff、probe failed、Killing 等事件","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_container_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_container_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e4(获取与异常 Pod rc-notready-liveness 相关的 Events): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 89%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取异常 Pod rc-notready-liveness 的详细信息以验证其状态和原因 | `kubectl describe pod rc-notready-liveness -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_previous_logs | 获取异常 Pod rc-notready-liveness 的崩溃前日志 | `kubectl logs rc-notready-liveness -n aiops-e2e --previous --tail=200` |
   | e3 | important | ✅ | kubectl_get_yaml | 获取异常 Pod rc-notready-liveness 的 YAML 配置 | `kubectl get pod rc-notready-liveness -n aiops-e2e -o yaml` |
   | e4 | important | ❌ | kubectl_events | 获取与异常 Pod rc-notready-liveness 相关的 Events | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-notre...` |

   ⚠️ 未采集原因:
   - e4(获取与异常 Pod rc-notready-liveness 相关的 Events): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (23.2s)
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
   ✅ [汇总总结] 完成 (1m 20.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3806 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 42.4s
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
| **兼容归因层** | L2 |
| **问题分类** | CrashLoopBackOffRuntime（容器运行时异常退出） |
| **置信度** | 中（50%） |
| **证据完整度** | 3/4 (75%) |

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
| 错误信息 | CrashLoopBackOff, Exit Code: 137, 10 次重启 |

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl describe pod rc-notready-liveness -n aiops-e2e` | `Exit Code: 137` | 容器因内存超限被 OOM Killer 终止 |
| 2 | Pod 重启记录 | `kubectl get pod rc-notready-liveness -n aiops-e2e` | `RESTARTS: 10 (2m9s ago)` | Pod 处于 CrashLoopBackOff 状态，持续重启中 |
| 3 | Pod YAML 配置 | `kubectl get pod rc-notready-liveness -n aiops-e2e -o yaml` | `memory limit: 256Mi` | 内存限制较低，可能不足 |
| 4 | 崩溃前日志 | `kubectl logs rc-notready-liveness -n aiops-e2e --previous` | `(no output)` | 未采集到崩溃前日志，无法确认崩溃原因 |

### 证据关联分析
- **证据 #1 + #3 印证**：Exit Code 137 (OOMKilled) + memory limit 256Mi → 内存限制不足
- **证据链**：应用内存需求 > 256Mi → 触发 OOM Killer → 容器被终止 → Pod 重启
- **证据 #2 印证**：Pod 重启次数为 10 次 → 明确显示容器持续崩溃并重启

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 与异常 Pod 相关的 Events | important | 无法确认重启触发的具体事件或错误信息 |

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
**结论**：根据证据 #1 (Exit Code 137, OOMKilled) 和证据 #3 (memory limit: 256Mi)，问题的根本原因是**容器内存限制（256Mi）不足以满足应用实际需求**，导致容器被 cgroup OOM Killer 终止并持续重启。  
**置信度**：中 (50%)  
- ✅ Exit Code 137 明确指向 OOM  
- ⚠️ 缺少崩溃前日志和 Events，无法确认内存增长或崩溃的具体原因  
- ⚠️ 未采集到容器启动命令或入口进程异常信息  

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
kubectl logs rc-notready-liveness -n aiops-e2e --previous | tail -100
```
*目的*：确认内存增长原因，排除内存泄漏

**3. [可选] 获取 Pod Events**
```bash
kubectl describe pod rc-notready-liveness -n aiops-e2e
```
*目的*：查看 Pod 的事件历史，确认重启触发的具体原因

### 后续优化
1. **监控告警**：配置内存使用率告警（>80% 预警）
2. **资源评估**：使用 Prometheus 或 `kubectl describe pod` 查看资源请求/限制与使用情况（本环境不可用 `kubectl top`）
3. **应用优化**：检查是否存在内存泄漏
4. **配置优化**：调整内存 limit 和 request，使其与应用实际需求匹配

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
- 如果应用需要长期运行，确保入口进程不会在启动后主动退出（例如 exit 0）
- 确保容器主进程不是一次性任务（例如脚本执行后退出）

---

## 📊 性能统计

├─ 总耗时: 4.7m
├─ 问题定位: 26.0s (9%) ✅
├─ 证据链采集: 152.9s (54%) ✅
├─ 根因分析: 23.2s (8%) ✅
├─ 汇总总结: 80.3s (28%) ✅
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
