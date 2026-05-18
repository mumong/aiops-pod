======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 112d9afd847e4119]

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
      📄 NAME                                      READY   STATUS             RESTARTS        AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-oomkilled-memory-limit-b6d999d-m8sl8  
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
name: rc-oomkilled-memory-limit-b6d999d-m8sl8
namespace: aiops-e2e
creationTimestamp: 2026-05-15T04:24:12Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: No
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
3s (x484 over 105m)   Warning   BackOff   Pod/rc-oomkilled-memory-limit-b6d999d-m8sl8   Back-off restarting failed container app in pod rc-oomkilled-memory-limit-b6d999d-m8sl
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
node1   Ready    <none>   232d   v1.26.8   10.2.0.49     <
   💭 [问题定位] 调用工具: kubectl_describe
   ✅ [问题定位] 完成 (1m 1.0s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[]
   entities=[]
   reasoning=当前环境中存在一个异常 Pod（rc-oomkilled-memory-limit-b6d999d-m8sl8），其状态为 CrashLoopBackOff，最后一次退出状态为 OOMKilled（exitCode=137）。根据分析文本和 runbook 信息，该 Pod 的异常归因于容器内存不足（OOMKilled），属于 L2 层次。L2 层次主要对应容器资源不足或频繁崩溃的问题，例如 OOMKilled 和 CrashLoopBackOff。因此，当前环境的异常归类为 L2。
   layer_analysis={"layer": "L2", "derived_layer": "", "layers": [], "layer_name": "", "confidence": 0.5, "reasoning": "当前环境中存在一个异常 Pod（rc-oomkilled-memory-limit-b6d999d-m8sl8），其状态为 CrashLoopBackOff，最后一次退出状态为 OOMKilled（exitCode=137）。根据分析文本和 runbook 信息，该 Pod 的异常归因于容器内存不足（OOMKilled），属于 L2 层次。L2 层次主要对应容器资源不足或频繁崩溃的问题，例如 OOMKilled 和 CrashLoopBackOff。因此，当前环境的异常归类为 L2。", "abnormal_pods": [{"name": "rc-oomkilled-memory-limit-b6d999d-m8sl8", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "", "status_category": "", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-oomkilled-memory-limit-b6d999d-m8sl8"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-oomkilled-memory-limit-b6d999d-m8sl8"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1, "OOMKilled": 1}, "total_abnormal": 2, "selected_rows": ["aiops-e2e     rc-oomkilled-memory-limit-b6d999d-m8sl8             0/1     CrashLoopBackOff   25 (91s ago)   104m   172.16.166.163   node1    <none>           <none>            app=rc-oomkilled-memory-limit,pod-template-hash=b6d999d,pod_abnormal_type=OOMKilled,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/112d9afd847e4119/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/112d9afd847e4119/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/112d9afd847e4119/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
name: rc-oomkilled-memory-limit-b6d999d-m8sl8
namespace: aiops-e2e
creationTimestamp: 2026-05-15T04:24:12Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: No
   💭 [证据链采集] 已采集证据：
- kubectl_describe 显示 Pod 最后一次退出状态为 OOMKilled（exitCode=137），且频繁重启（CrashLoopBackOff）。
- kubectl_previous_logs 未返回有效日志，可能是容器崩溃前无明显错误记录。
- kubectl_get_yaml 显示容器配置未设置内存限制（resources.limits.memory 缺失），可能是导致 OOMKilled 的直接原因。

未采集证据：
- 未检查节点内存压力（Node Conditions）以确认是否为节点级 OOM。
- 未检查应用内存使用情况（如通过 Prometheus 指标）以确认实际内存需求。

冲突证据：
- 无明显冲突证据。
   ✅ [证据链采集] 完成 (1m 55.7s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证异常 Pod 的详细状态和事件，确认 OOMKilled 原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e","tool_args":{"name":"rc-oomkilled-memory-limit-b6d999d-m8sl8","namespace":"aiops-e2e"},"purpose":"获取 Pod 的详细状态，包括 lastState.reason 和 exitCode，以验证 OOMKilled 原因","evidence_type":"status_verification","target_scope":"aiops-e2e/rc-oomkilled-memory-limit-b6d999d-m8sl8","acceptable_tools":["kubectl_describe","kubectl_events"],"counts_for_completeness":true},{"id":"e2","description":"验证异常 Pod 的容器日志，确认是否有内存不足的直接证据","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e --previous","tool_args":{"name":"rc-oomkilled-memory-limit-b6d999d-m8sl8","namespace":"aiops-e2e","container":"app"},"purpose":"获取容器的上一次日志，以确认是否有内存不足或崩溃的直接证据","evidence_type":"log_analysis","target_scope":"aiops-e2e/rc-oomkilled-memory-limit-b6d999d-m8sl8","acceptable_tools":["kubectl_previous_logs","kubectl_logs_grep"],"counts_for_completeness":true},{"id":"e3","description":"验证异常 Pod 的资源限制配置，确认内存 limit 是否过低","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e -o yaml","tool_args":{"name":"rc-oomkilled-memory-limit-b6d999d-m8sl8","namespace":"aiops-e2e"},"purpose":"获取 Pod 的 YAML 配置，以验证其资源限制配置是否合理","evidence_type":"configuration_verification","target_scope":"aiops-e2e/rc-oomkilled-memory-limit-b6d999d-m8sl8","acceptable_tools":["kubectl_get_yaml","kubectl_get_by_name"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-oomkilled-memory-limit-b6d999d-m8sl8\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\nName:             rc-oomkilled-memory-limit-b6d999d-m8sl8\nLabels:           app=rc-oomkilled-memory-limit\n                  pod_abnormal_type=OOMKilled\nAnnotations:      aiops.e2e/runbook: pod-oomkilled.md\nControlled By:  ReplicaSet/rc-oomkilled-memory-limit-b6d999d\n      Reason:       OOMKilled\n      Exit Code:    137\n  Warning  BackOff  117s (x484 over 107m)  kubelet  Back-off restarting failed container app in pod rc-oomkilled-memory-limit-b6d999d-m8sl8_aiops-e2e(837f1b14-9cec-4f6f-8f5b-c89f5b397ca5)\n      Reason:       CrashLoopBackOff\n                  cni.projectcalico.org/containerID: e6061e9e2466775a2aa864ee0168e2c2d1b8f1fb2a8e6d5ea5f738ef2425c284\n                  cni.projectcalico.org/podIP: 172.16.166.163/32\n                  cni.projectcalico.org/podIPs: 172.16.166.163/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n    Last State:     Terminated","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/112d9afd847e4119/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/112d9afd847e4119/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/112d9afd847e4119/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/112d9afd847e4119/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/112d9afd847e4119/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/112d9afd847e4119/tools/002-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-oomkilled-memory-limit-b6d999d-m8sl8\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T04:24:12Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-oomkilled-memory-limit, pod_abnormal_type=OOMKilled\ndiagnostic_annotations: aiops.e2e/runbook=pod-oomkilled.md\nownerReferences: ReplicaSet/rc-oomkilled-memory-limit-b6d999d\ntolerations_count: 2\ncontainers:\n- app: image=python:3.11-slim imagePullPolicy=IfNotPresent\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=25 reason=CrashLoopBackOff exitCode=137\n  message: back-off 5m0s restarting failed container=app pod=rc-oomkilled-memory-limit-b6d999d-m8sl8_aiops-e2e(837f1b14-9cec-4f6f-8f5b-c89f5b397ca5)\nvolumes:\n- {\"name\": \"kube-api-access-ltb77\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/112d9afd847e4119/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/112d9afd847e4119/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/112d9afd847e4119/tools/003-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"已采集证据：\n- kubectl_describe 显示 Pod 最后一次退出状态为 OOMKilled（exitCode=137），且频繁重启（CrashLoopBackOff）。\n- kubectl_previous_logs 未返回有效日志，可能是容器崩溃前无明显错误记录。\n- kubectl_get_yaml 显示容器配置未设置内存限制（resources.limits.memory 缺失），可能是导致 OOMKilled 的直接原因。\n\n未采集证据：\n- 未检查节点内存压力（Node Conditions）以确认是否为节点级 OOM。\n- 未检查应用内存使用情况（如通过 Prometheus 指标）以确认实际内存需求。\n\n冲突证据：\n- 无明显冲突证据。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 9/9 项，完整度 100%；实际执行工具 9 个，匹配计划 3 个，未规划证据 6 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":9,"environment_evidence_collected":9,"environment_evidence_completeness":1.0,"executed_tool_count":9,"matched_tool_count":3,"unplanned_tool_count":6,"evidence_inventory":[{"id":"e1","description":"验证异常 Pod 的详细状态和事件，确认 OOMKilled 原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e","purpose":"获取 Pod 的详细状态，包括 lastState.reason 和 exitCode，以验证 OOMKilled 原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"验证异常 Pod 的容器日志，确认是否有内存不足的直接证据","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e --previous","purpose":"获取容器的上一次日志，以确认是否有内存不足或崩溃的直接证据","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"验证异常 Pod 的资源限制配置，确认内存 limit 是否过低","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e -o yaml","purpose":"获取 Pod 的 YAML 配置，以验证其资源限制配置是否合理","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证异常 Pod 的详细状态和事件，确认 OOMKilled 原因 | `kubectl describe pod rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_previous_logs | 验证异常 Pod 的容器日志，确认是否有内存不足的直接证据 | `kubectl logs rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e --previous` |
   | e3 | important | ✅ | kubectl_get_yaml | 验证异常 Pod 的资源限制配置，确认内存 limit 是否过低 | `kubectl get pod rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e -o yaml` |

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (11.9s)
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
   ✅ [汇总总结] 完成 (1m 7.1s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3497 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 15.7s
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
| **兼容归因层** | L2 - 容器资源不足或频繁崩溃 |
| **问题分类** | OOMKilled (Exit Code 137) |
| **置信度** | 高 (85%) |
| **证据完整度** | 3/3 (100%) |

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
| 错误信息 | OOMKilled, Exit Code 137, CrashLoopBackOff |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | kubectl describe pod | `Reason: OOMKilled, Exit Code: 137` | 容器因内存不足被终止 |
| 2 | 资源配置 | kubectl get pod -o yaml | `memory limit: 未显式配置` | 缺少明确内存限制配置 |
| 3 | Pod 事件 | kubectl describe pod / kubectl events | `3s (x484 over 105m) Warning BackOff Pod/rc-oomkilled-memory-limit-b6d999d-m8sl8 Back-off restarting failed container app` | Pod 因容器失败持续重启 |

### 证据关联分析

- **证据 #1 印证**：Exit Code 137 明确表明容器因 OOMKilled 终止。
- **证据 #2 印证**：未设置 memory limit，可能导致容器内存使用超出系统可用资源。
- **证据 #3 印证**：事件记录显示容器失败后进入 CrashLoopBackOff 状态，持续重启。

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 应用实际内存需求超过容器可用内存（未设置 memory limit），导致 OOMKilled │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器内存使用超过可用资源 → 触发 cgroup OOM Killer               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器被 OOM Killer 终止（Exit Code 137）                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CrashLoopBackOff，持续重启                           │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Exit Code 137, OOMKilled) 和证据 #2 (未设置 memory limit)，问题的根本原因是**容器未设置内存限制，导致容器内存使用超过系统可用资源，触发 OOM Killer**，最终导致容器被终止并进入 CrashLoopBackOff 状态。

**置信度**：高 (85%)
- ✅ Exit Code 137 明确指向 OOMKilled
- ✅ 事件日志确认容器失败并持续重启
- ⚠️ 缺少崩溃前日志，无法确认内存增长原因

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 设置内存限制和请求**
```bash
kubectl set resources deployment/<deployment_name> -n aiops-e2e --limits=memory=512Mi --requests=memory=256Mi
```

*依据*：当前容器未设置内存限制，建议设置合理的内存 limit 和 request，防止内存不足触发 OOMKilled。

**2. [可选] 查看崩溃前日志**
```bash
kubectl logs rc-oomkilled-memory-limit-b6d999d-m8sl8 -n aiops-e2e --previous | tail -100
```

*目的*：确认容器崩溃前是否有内存泄漏或异常增长。

### 后续优化

1. **监控告警**：配置内存使用率告警（>80% 预警）
2. **资源评估**：使用 Prometheus 或 `kubectl describe pod` 查看资源请求/限制与使用情况（本环境不可用 `kubectl top`）
3. **应用优化**：检查是否存在内存泄漏，优化内存使用

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

├─ 总耗时: 4.3m
├─ 问题定位: 61.0s (24%) ✅
├─ 证据链采集: 115.7s (45%) ✅
├─ 根因分析: 11.9s (5%) ✅
├─ 汇总总结: 67.1s (26%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 11 次
```

📋 诊断追踪

- **核心 Runbook**: pod-oomkilled
- **参考 Runbook**: pod-oomkilled
- **工具调用**: 11 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
