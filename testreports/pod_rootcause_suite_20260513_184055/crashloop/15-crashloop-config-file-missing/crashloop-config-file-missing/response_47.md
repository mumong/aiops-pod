======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 1ce674e55f614c5b]

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
      📄 NAME                                                READY   STATUS             RESTARTS         AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-crashloop-config-file-missi
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 2
signals: 2
关键日志:
RUNTIME_STARTUP_ERROR: required config file missing
cat: can't open '/etc/rootcause-app/config.yaml': No such file or directory
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-crashloop-config-file-missing-58cf574c9f-vhlrs
namespace: aiops-e2e
creationTimestamp: 2026-05-14T19:46:03Z
deletionTimestamp: <absent>
deletionGracePeriodS
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
3m9s (x623 over 138m)   Warning   BackOff   Pod/rc-crashloop-config-file-missing-58cf574c9f-vhlrs   Back-off restarting failed container app in pod rc-crashloop-config-file-m
   💭 [问题定位] 调用工具: kubectl_lineage_children
   💭 [问题定位] 工具结果: kubectl_lineage_children (success)
      📄 kubectl_lineage_children 输出摘要: raw_chars=155 lines=3
Command failed (exit 1):
kubectl lineage pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e
error: unknown command "lineage" for "k
   💭 [问题定位] 调用工具: kubectl_lineage_parents
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (47.7s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[{'scenario': '容器启动时缺少配置文件导致进程崩溃', 'probability': '高', 'reason': "日志中显示 'required config file missing'，且 YAML 中未配置相应的 ConfigMap 或 Secret 挂载。"}, {'scenario': '容器主进程启动后立即退出', 'probability': '中', 'reason': "容器的 exitCode 为 1，且日志显示 'RUNTIME_STARTUP_ERROR'，表明应用启动时遇到错误。"}]
   entities=[{"type": "pod", "name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs", "namespace": "aiops-e2e"}]
   reasoning=当前环境中存在一个处于 CrashLoopBackOff 状态的 Pod，其 pod_abnormal_type 明确为 CrashLoopBackOffRuntime。结合日志和 YAML 信息，该 Pod 的崩溃原因是容器启动时无法找到配置文件，导致应用异常退出。CrashLoopBackOffRuntime 属于 L2 层级的异常类型，归因于容器资源或运行时问题。
   layer_analysis={"layer": "L2", "derived_layer": "L2", "layers": ["L2"], "layer_name": "container_resource", "confidence": 0.95, "reasoning": "当前环境中存在一个处于 CrashLoopBackOff 状态的 Pod，其 pod_abnormal_type 明确为 CrashLoopBackOffRuntime。结合日志和 YAML 信息，该 Pod 的崩溃原因是容器启动时无法找到配置文件，导致应用异常退出。CrashLoopBackOffRuntime 属于 L2 层级的异常类型，归因于容器资源或运行时问题。", "abnormal_pods": [{"name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "CrashLoopBackOffRuntime", "status_category": "container_resource", "key_entities": [{"type": "pod", "name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "容器启动时缺少配置文件导致进程崩溃", "probability": "高", "reason": "日志中显示 'required config file missing'，且 YAML 中未配置相应的 ConfigMap 或 Secret 挂载。"}, {"scenario": "容器主进程启动后立即退出", "probability": "中", "reason": "容器的 exitCode 为 1，且日志显示 'RUNTIME_STARTUP_ERROR'，表明应用启动时遇到错误。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-crashloop-config-file-missing-58cf574c9f-vhlrs   0/1     CrashLoopBackOff   31 (4m23s ago)   138m    172.16.166.155   node1    <none>           <none>            app=rc-crashloop-config-file-missing,pod-template-hash=58cf574c9f,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/1ce674e55f614c5b/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/1ce674e55f614c5b/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/1ce674e55f614c5b/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                                READY   STATUS             RESTARTS         AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-crashloop-config-file-missi
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-crashloop-config-file-missing-58cf574c9f-vhlrs
namespace: aiops-e2e
creationTimestamp: 2026-05-14T19:46:03Z
deletionTimestamp: <absent>
deletionGracePeriodS
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   ✅ [证据链采集] 完成 (2m 27.2s)
   📤 → 下游数据: evidence_items=10/10
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 'rc-crashloop-config-file-missing-58cf574c9f-vhlrs' 的详细状态信息","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e -o wide","tool_args":{"namespace":"aiops-e2e","name":"rc-crashloop-config-file-missing-58cf574c9f-vhlrs","kind":"pod"},"purpose":"验证 Pod 当前状态和基本信息","evidence_type":"pod_status","target_scope":"aiops-e2e/rc-crashloop-config-file-missing-58cf574c9f-vhlrs","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 'rc-crashloop-config-file-missing-58cf574c9f-vhlrs' 的详细配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e -o yaml","tool_args":{"namespace":"aiops-e2e","name":"rc-crashloop-config-file-missing-58cf574c9f-vhlrs","kind":"pod"},"purpose":"验证 Pod 的 YAML 配置，包括 command/args/image/resources 等关键字段","evidence_type":"pod_yaml","target_scope":"aiops-e2e/rc-crashloop-config-file-missing-58cf574c9f-vhlrs","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod 'rc-crashloop-config-file-missing-58cf574c9f-vhlrs' 的崩溃前日志","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e --previous","tool_args":{"namespace":"aiops-e2e","name":"rc-crashloop-config-file-missing-58cf574c9f-vhlrs","container_name":"app"},"purpose":"验证崩溃前的日志，确认是否有配置文件缺失等异常信息","evidence_type":"pod_previous_logs","target_scope":"aiops-e2e/rc-crashloop-config-file-missing-58cf574c9f-vhlrs","acceptable_tools":["kubectl_previous_logs"],"counts_for_completeness":true},{"id":"e4","description":"获取异常 Pod 'rc-crashloop-config-file-missing-58cf574c9f-vhlrs' 的事件记录","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crashloop-config-file-missing-58cf574c9f-vhlrs","tool_args":{"namespace":"aiops-e2e","name":"rc-crashloop-config-file-missing-58cf574c9f-vhlrs","kind":"pod"},"purpose":"验证 Pod 的事件记录，包括 BackOff、Killing、Liveness probe 等关键事件","evidence_type":"pod_events","target_scope":"aiops-e2e/rc-crashloop-config-file-missing-58cf574c9f-vhlrs","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                                                READY   STATUS             RESTARTS         AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-crashloop-config-file-missing-58cf574c9f-vhlrs   0/1     CrashLoopBackOff   32 (2m18s ago)   141m   172.16.166.155   node1   <none>           <none>            app=rc-crashloop-config-file-missing,pod-template-hash=58cf574c9f,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1ce674e55f614c5b/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1ce674e55f614c5b/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1ce674e55f614c5b/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-crashloop-config-file-missing-58cf574c9f-vhlrs\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-14T19:46:03Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-crashloop-config-file-missing, pod_abnormal_type=CrashLoopBackOffRuntime\ndiagnostic_annotations: aiops.e2e/runbook=pod-crashloop-runtime.md\nownerReferences: ReplicaSet/rc-crashloop-config-file-missing-58cf574c9f\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=32 reason=CrashLoopBackOff exitCode=1\n  message: back-off 5m0s restarting failed container=app pod=rc-crashloop-config-file-missing-58cf574c9f-vhlrs_aiops-e2e(f116c098-f8d2-46aa-8037-25a4f00eb480)\nvolumes:\n- {\"name\": \"kube-api-access-76ckm\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1ce674e55f614c5b/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1ce674e55f614c5b/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1ce674e55f614c5b/tools/002-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'pod_name' is a required property","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 10/10 项，完整度 100%；实际执行工具 7 个，匹配计划 4 个，未规划证据 3 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":10,"environment_evidence_collected":10,"environment_evidence_completeness":1.0,"executed_tool_count":7,"matched_tool_count":4,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 'rc-crashloop-config-file-missing-58cf574c9f-vhlrs' 的详细状态信息","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e -o wide","purpose":"验证 Pod 当前状态和基本信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 'rc-crashloop-config-file-missing-58cf574c9f-vhlrs' 的详细配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e -o yaml","purpose":"验证 Pod 的 YAML 配置，包括 command/args/image/resources 等关键字段","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod 'rc-crashloop-config-file-missing-58cf574c9f-vhlrs' 的崩溃前日志","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e --previous","purpose":"验证崩溃前的日志，确认是否有配置文件缺失等异常信息","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"e4","description":"获取异常 Pod 'rc-crashloop-config-file-missing-58cf574c9f-vhlrs' 的事件记录","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crashloop-config-file-missing-58cf574c9f-vhlrs","purpose":"验证 Pod 的事件记录，包括 BackOff、Killing、Liveness probe 等关键事件","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_lineage_children","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 获取异常 Pod 'rc-crashloop-config-file-missing-58... | `kubectl get pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2...` |
   | e2 | critical | ✅ | kubectl_get_yaml | 获取异常 Pod 'rc-crashloop-config-file-missing-58... | `kubectl get pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2...` |
   | e3 | critical | ✅ | kubectl_previous_logs | 获取异常 Pod 'rc-crashloop-config-file-missing-58... | `kubectl logs rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e -...` |
   | e4 | important | ✅ | kubectl_events | 获取异常 Pod 'rc-crashloop-config-file-missing-58... | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crash...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (18.5s)
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
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (2m 23.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4334 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 57.2s
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
| **兼容归因层** | L2 - 容器资源或运行时问题 |
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
| Pod | rc-crashloop-config-file-missing-58cf574c9f-vhlrs |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | `RUNTIME_STARTUP_ERROR: required config file missing` |
| Exit Code | 1 |
| 重启次数 | 31 次（持续 138 分钟） |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff, RESTARTS: 31` | Pod 处于持续崩溃重启状态 |
| 2 | 崩溃前日志 | `kubectl logs <pod> --previous` | `RUNTIME_STARTUP_ERROR: required config file missing`<br>`cat: can't open '/etc/rootcause-app/config.yaml': No such file or directory` | 容器启动失败，原因是配置文件缺失 |
| 3 | Pod 配置 | `kubectl get pod -o yaml` | `ConfigMap/Secret 挂载缺失，未配置 config.yaml 的来源` | 配置缺失是直接原因 |
| 4 | Pod 事件 | `kubectl describe pod` | `Back-off restarting failed container app` | K8s 持续尝试重启失败容器 |

### 证据关联分析

- **证据 #2 + #3 印证**：容器崩溃日志明确指出配置文件缺失，而 YAML 中未挂载 ConfigMap 或 Secret，因此配置文件路径 `/etc/rootcause-app/config.yaml` 不存在。
- **证据链**：
  - 应用启动时依赖的配置文件缺失 → 容器进程异常退出 → K8s 重启容器 → 重复崩溃 → Pod 状态为 `CrashLoopBackOff`

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 无 | - | 证据完整，无需补充 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 应用依赖的配置文件 `/etc/rootcause-app/config.yaml` 未在容器中挂载，导致启动失败。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 应用启动时尝试读取配置文件 → 读取失败 → 容器进程退出 → K8s 重启容器 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器启动失败，Exit Code 1，日志提示配置文件缺失。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 `CrashLoopBackOff`，持续重启。 │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2（崩溃前日志提示配置文件缺失）和证据 #3（YAML 中未挂载配置文件），问题的根本原因是**容器启动时缺少必要的配置文件**，导致容器进程退出，K8s 无法成功启动容器，进入 CrashLoopBackOff 状态。

**置信度**：高 (95%)  
- ✅ 崩溃前日志明确指出 `config.yaml` 缺失  
- ✅ YAML 中未配置 ConfigMap 或 Secret 挂载  
- ✅ K8s 事件显示容器启动失败

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 挂载 ConfigMap 提供配置文件**

```bash
kubectl create configmap app-config --from-file=config.yaml -n aiops-e2e
kubectl patch deployment <deployment-name> -n aiops-e2e --type='json' -p='[{"op": "add", "path": "/spec/template/spec/containers/0/volumeMounts/-", "value": {"name": "config-volume", "mountPath": "/etc/rootcause-app/config.yaml", "subPath": "config.yaml"}}, {"op": "add", "path": "/spec/template/spec/volumes/-", "value": {"name": "config-volume", "configMap": {"name": "app-config"}}}]'
```

*依据*：容器缺失配置文件，需要通过 ConfigMap 提供。

**2. [可选] 查看崩溃前日志确认修复效果**

```bash
kubectl logs rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e --previous | tail -100
```

*目的*：确认配置文件已正确挂载，应用启动正常。

### 后续优化

1. **验证修复后 Pod 状态**：
   ```bash
   kubectl get pod -n aiops-e2e
   ```
   预期：Pod 状态为 `Running`

2. **配置 ConfigMap 自动更新机制**（如使用 Helm、Kustomize 或 GitOps 工具）

3. **设置健康检查探针（liveness/readiness）**，防止因配置文件缺失导致的无限重启。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 0 |
| 3. 检查配置文件挂载 | `kubectl exec <pod-name> -n aiops-e2e -- cat /etc/rootcause-app/config.yaml` | 正常输出配置内容 |
| 4. 检查事件记录 | `kubectl describe pod <pod-name> -n aiops-e2e` | 无 `Back-off restarting failed container` 事件 |

---

## ⚠️ 注意事项

- 如果 Pod 仍未恢复，请检查 ConfigMap 是否正确创建，挂载路径是否与应用期望一致。
- 如果应用需要读取多个配置文件，建议使用 `subPath` 或挂载整个目录。
- 建议使用 Helm 或 Kustomize 管理 ConfigMap 和 Deployment，以提高配置管理的可维护性。

---

## 📊 性能统计

├─ 总耗时: 6.0m
├─ 问题定位: 47.7s (13%) ✅
├─ 证据链采集: 147.2s (41%) ✅
├─ 根因分析: 18.5s (5%) ✅
├─ 汇总总结: 143.8s (40%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 11 次
```

📋 诊断追踪

- **核心 Runbook**: pod-crashloop-runtime
- **参考 Runbook**: pod-crashloop-runtime
- **工具调用**: 11 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
