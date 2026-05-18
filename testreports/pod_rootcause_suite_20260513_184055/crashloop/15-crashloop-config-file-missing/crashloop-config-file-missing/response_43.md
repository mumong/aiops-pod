======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 4de915031d9a42b4]

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
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
83s (x576 over 126m)   Warning   BackOff   Pod/rc-crashloop-config-file-missing-58cf574c9f-vhlrs   Back-off restarting failed container app in pod rc-crashloop-config-file-mi
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-crashloop-config-file-missing-58cf574c9f-vhlrs
namespace: aiops-e2e
creationTimestamp: 2026-05-14T19:46:03Z
deletionTimestamp: <absent>
deletionGracePeriodS
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                          DESIRED   CURRENT   READY   AGE    CONTAINERS   IMAGES         SELECTOR                                                            LABELS
rc-crashloop-con
   💭 [问题定位] 调用工具: kubectl_get_by_name
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (42.7s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[{'scenario': '容器主进程启动失败，缺少必要的配置文件', 'probability': '高', 'reason': "日志中显示 'RUNTIME_STARTUP_ERROR: required config file missing' 和 'cat: can't open '/etc/rootcause-app/config.yaml': No such file or directory'，表明容器启动失败是由于缺少配置文件。"}]
   entities=[{"type": "Pod", "name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs", "namespace": "aiops-e2e"}]
   reasoning=当前环境中存在一个异常 Pod，状态为 CrashLoopBackOff，重启次数为 29 次。结合日志和事件信息，Pod 的异常类型归一化为 CrashLoopBackOffRuntime，属于 L2 层级（容器资源或运行时异常）。异常 Pod 的状态关键字为 CrashLoopBackOff，异常类型为 CrashLoopBackOffRuntime，归类于 container_resource/container_runtime 类别。
   layer_analysis={"layer": "L2", "derived_layer": "L2", "layers": ["L2"], "layer_name": "", "confidence": 0.5, "reasoning": "当前环境中存在一个异常 Pod，状态为 CrashLoopBackOff，重启次数为 29 次。结合日志和事件信息，Pod 的异常类型归一化为 CrashLoopBackOffRuntime，属于 L2 层级（容器资源或运行时异常）。异常 Pod 的状态关键字为 CrashLoopBackOff，异常类型为 CrashLoopBackOffRuntime，归类于 container_resource/container_runtime 类别。", "abnormal_pods": [{"name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "CrashLoopBackOffRuntime", "status_category": "container_resource/container_runtime", "key_entities": [{"type": "Pod", "name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "容器主进程启动失败，缺少必要的配置文件", "probability": "高", "reason": "日志中显示 'RUNTIME_STARTUP_ERROR: required config file missing' 和 'cat: can't open '/etc/rootcause-app/config.yaml': No such file or directory'，表明容器启动失败是由于缺少配置文件。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-crashloop-config-file-missing-58cf574c9f-vhlrs   0/1     CrashLoopBackOff   29 (2m49s ago)   126m    172.16.166.155   node1    <none>           <none>            app=rc-crashloop-config-file-missing,pod-template-hash=58cf574c9f,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/4de915031d9a42b4/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/4de915031d9a42b4/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/4de915031d9a42b4/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                                READY   STATUS   RESTARTS         AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-crashloop-config-file-missing-58cf574
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 0
关键日志:
unable to retrieve container logs for containerd://18ed02f2898875ba2fd7c87729e7f0a23e67a3b6477d85d3e7a4900ec5d1086b
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (1m 51.2s)
   📤 → 下游数据: evidence_items=8/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod 的详细状态、重启次数、Last State、Exit Code、Events、Reason 等关键字段","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e -o yaml","tool_args":{"name":"rc-crashloop-config-file-missing-58cf574c9f-vhlrs","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"获取 Pod 的完整 YAML，验证 Last State、Exit Code、Events、Reason、重启策略等关键字段","evidence_type":"pod_state","target_scope":"aiops-e2e/rc-crashloop-config-file-missing-58cf574c9f-vhlrs","acceptable_tools":["kubectl_get_by_name","kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e2","description":"查看崩溃前的日志以确认容器启动失败的具体原因","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e --previous --tail=200","tool_args":{"name":"rc-crashloop-config-file-missing-58cf574c9f-vhlrs","namespace":"aiops-e2e","container":"app","tail_lines":200},"purpose":"查看容器崩溃前的日志，确认启动失败的具体原因，例如缺少配置文件、命令错误、权限问题等","evidence_type":"container_logs","target_scope":"aiops-e2e/rc-crashloop-config-file-missing-58cf574c9f-vhlrs/app","acceptable_tools":["kubectl_previous_logs","kubectl_logs","kubectl_previous_logs_all_containers"],"counts_for_completeness":true},{"id":"e3","description":"查看 Pod 的事件以确认崩溃和重启的原因","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crashloop-config-file-missing-58cf574c9f-vhlrs --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-crashloop-config-file-missing-58cf574c9f-vhlrs","sort_by":".lastTimestamp"},"purpose":"查看 Pod 的事件，确认容器崩溃和重启的具体原因，例如 BackOff、Killing、Liveness probe failed 等","evidence_type":"pod_events","target_scope":"aiops-e2e/rc-crashloop-config-file-missing-58cf574c9f-vhlrs","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                                                READY   STATUS   RESTARTS         AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-crashloop-config-file-missing-58cf574c9f-vhlrs   0/1     Error    30 (5m12s ago)   128m   172.16.166.155   node1   <none>           <none>            app=rc-crashloop-config-file-missing,pod-template-hash=58cf574c9f,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4de915031d9a42b4/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4de915031d9a42b4/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4de915031d9a42b4/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\nunable to retrieve container logs for containerd://18ed02f2898875ba2fd7c87729e7f0a23e67a3b6477d85d3e7a4900ec5d1086b","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4de915031d9a42b4/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4de915031d9a42b4/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4de915031d9a42b4/tools/002-evidence-kubectl_previous_logs.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 3 项，实际采集 2 项，未采集 1 项，完整度 67%；其中真实环境证据 8/9 项，完整度 89%；实际执行工具 8 个，匹配计划 2 个，未规划证据 6 个","plan_total":3,"plan_collected":2,"plan_completeness":0.6666666666666666,"environment_evidence_total":9,"environment_evidence_collected":8,"environment_evidence_completeness":0.8888888888888888,"executed_tool_count":8,"matched_tool_count":2,"unplanned_tool_count":6,"evidence_inventory":[{"id":"e1","description":"验证 Pod 的详细状态、重启次数、Last State、Exit Code、Events、Reason 等关键字段","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e -o yaml","purpose":"获取 Pod 的完整 YAML，验证 Last State、Exit Code、Events、Reason、重启策略等关键字段","collected":false,"source":"planned","outcome":"unknown"},{"id":"e2","description":"查看崩溃前的日志以确认容器启动失败的具体原因","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e --previous --tail=200","purpose":"查看容器崩溃前的日志，确认启动失败的具体原因，例如缺少配置文件、命令错误、权限问题等","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"查看 Pod 的事件以确认崩溃和重启的原因","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crashloop-config-file-missing-58cf574c9f-vhlrs --sort-by='.lastTimestamp'","purpose":"查看 Pod 的事件，确认容器崩溃和重启的具体原因，例如 BackOff、Killing、Liveness probe failed 等","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e1(验证 Pod 的详细状态、重启次数、Last State、Exit Code、Events、Reason 等关键字段): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/3 项, 完整度: 89%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ❌ | kubectl_get_by_name | 验证 Pod 的详细状态、重启次数、Last State、Exit Code、Events... | `kubectl get pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2...` |
   | e2 | critical | ✅ | kubectl_previous_logs | 查看崩溃前的日志以确认容器启动失败的具体原因 | `kubectl logs rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e -...` |
   | e3 | critical | ✅ | kubectl_events | 查看 Pod 的事件以确认崩溃和重启的原因 | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crash...` |

   ⚠️ 未采集原因:
   - e1(验证 Pod 的详细状态、重启次数、Last State、Exit Code、Events、Reason 等关键字段): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (17.6s)
   📤 → 下游数据: root_cause=当前环境中存在一个异常 Pod，状态为 CrashLoopBackOff，重启次数为 29 次。结合日志和事件信息，Pod 的异常类型归一化为 CrashLoopBackOffRuntime，属于 L2 层级（容器资源或运行时异常）。异常 Pod 的状态关键字为 CrashLoopBackOff，异常类型为 CrashLoopBackOffRuntime，归类于 container_resource/container_runtime 类别。
   confidence=80%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [], "causal_chain": {}, "root_cause": "当前环境中存在一个异常 Pod，状态为 CrashLoopBackOff，重启次数为 29 次。结合日志和事件信息，Pod 的异常类型归一化为 CrashLoopBackOffRuntime，属于 L2 层级（容器资源或运行时异常）。异常 Pod 的状态关键字为 CrashLoopBackOff，异常类型为 CrashLoopBackOffRuntime，归类于 container_resource/container_runtime 类别。", "root_cause_summary": "当前环境中存在一个异常 Pod，状态为 CrashLoopBackOff，重启次数为 29 次。结合日志和事件信息，Pod 的异常类型归一化为 CrashLoopBackOffRuntime，属于 L2 层级（容器资源或运行时异常）。异常 Pod 的状态关键字为 CrashLoopBackOff，异常类型为 CrashLoopBackOffRuntime，归类于 container_resource/container_runtime 类别。", "confidence": 0.8, "confidence_reason": "", "primary_runbooks": ["pod-crashloop-runtime.md"], "alternative_causes": [], "limitations": "缺少 Pod 的详细状态、重启次数、Last State、Exit Code、Events、Reason 等关键字段的验证。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 当前环境中存在一个异常 Pod，状态为 CrashLoopBackOff，重启次数为 29 次。结合日志和事件信息，Pod 的异常类型归一化为 CrashLoopBackOffRuntime，属于 L2 层级（容器资源或运行时异常）。异常 Pod 的状态关键字为 CrashLoopBackOff，异...
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
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (2m 19.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5298 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 11.1s
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
| **兼容归因层** | L2（container_resource/container_runtime） |
| **问题分类** | CrashLoopBackOffRuntime（容器启动失败） |
| **置信度** | 高（80%） |
| **证据完整度** | 2/3 (67%) |

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
| 错误信息 | `RUNTIME_STARTUP_ERROR: required config file missing`, `cat: can't open '/etc/rootcause-app/config.yaml': No such file or directory` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff, RESTARTS: 29` | Pod 由于容器反复失败而进入 CrashLoopBackOff 状态 |
| 2 | 崩溃前日志 | `kubectl logs <pod> --previous` | `RUNTIME_STARTUP_ERROR: required config file missing`, `cat: can't open '/etc/rootcause-app/config.yaml': No such file or directory` | 容器启动失败，缺少配置文件 |
| 3 | Pod 事件 | `kubectl describe pod` | `Warning BackOff: Back-off restarting failed container app` | Pod 事件表明容器启动失败后进入重启回退 |
| 4 | Pod YAML | `kubectl get pod -o yaml` | `image: busybox:1.36`, `restartPolicy: Always` | Pod 使用 busybox 镜像，配置为 Always 重启 |
| 5 | Pod 列表摘要 | `kubectl get pod` | `NAMESPACE: aiops-e2e, NAME: rc-crashloop-config-file-missing-58cf574c9f-vhlrs, STATUS: CrashLoopBackOff` | 确认 Pod 所在命名空间和状态 |

### 证据关联分析

- **证据 #2 印证**：日志中明确指出 `required config file missing`，即容器启动失败的原因是配置文件缺失，符合 CrashLoopBackOffRuntime 的典型场景。
- **证据 #3 印证**：Pod 事件中显示 `Back-off restarting failed container app`，说明容器启动失败后被自动重启，进入 CrashLoopBackOff。
- **证据 #4 印证**：Pod 使用 `busybox:1.36` 镜像，但没有正确配置挂载 ConfigMap 或 Secret，导致配置文件缺失。
- **证据链总结**：  
  容器启动 → 缺少配置文件 `/etc/rootcause-app/config.yaml` → 启动失败 → Pod 进入 CrashLoopBackOff → 持续重启

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| Pod 详细状态（如 Exit Code、Last State） | critical | 无法确认容器退出状态是否为非正常值 |
| 完整的容器描述信息（kubectl describe pod） | important | 无法确认容器启动失败的具体原因 |

---

## 🎯 根因分析

### 因果链

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                     │
│ 容器启动时缺少必要的配置文件 `/etc/rootcause-app/config.yaml`                │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                     │
│ 容器启动时无法读取配置文件 → 启动失败 → Pod 进入 CrashLoopBackOff            │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                     │
│ 容器启动失败，Exit Code 非 0，触发 Pod 重启策略                              │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                 │
│ Pod 状态为 CrashLoopBackOff，重启次数为 29 次                                │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2 (`RUNTIME_STARTUP_ERROR: required config file missing`) 和证据 #3 (`Back-off restarting failed container app`)，  
问题的根本原因是 **容器启动时缺少必要的配置文件 `/etc/rootcause-app/config.yaml`**，导致容器启动失败并被持续重启。

**置信度**：高 (80%)  
- ✅ 日志中明确指出配置文件缺失
- ✅ Pod 事件表明容器启动失败后被重启
- ⚠️ 缺少 `kubectl describe pod` 的 Exit Code 等信息，无法进一步确认容器退出状态

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 挂载 ConfigMap 或 Secret 提供配置文件**

```bash
# 创建 ConfigMap（假设 config.yaml 内容为 "key: value"）
kubectl create configmap config-map --from-file=config.yaml

# 更新 Deployment 挂载 ConfigMap
kubectl patch deployment rc-crashloop-config-file-missing -n aiops-e2e \
  -p '{"spec":{"template":{"spec":{"volumes":[{"name":"config","configMap":{"name":"config-map"}}]},"containers":[{"name":"app","volumeMounts":[{"name":"config","mountPath":"/etc/rootcause-app"}]}]}}}'
```

*依据*：容器启动失败的根本原因是配置文件缺失，通过挂载 ConfigMap 可提供缺失的配置文件。

**2. [可选] 查看崩溃前日志（已采集，可复核）**

```bash
kubectl logs rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e --previous
```

*目的*：确认是否还有其他配置文件缺失或启动错误。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 重启次数不再增加 |
| 3. 检查容器是否挂载了 ConfigMap | `kubectl get pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e -o yaml` | `volumes` 中包含 `config-map`，`volumeMounts` 中包含 `/etc/rootcause-app` |

---

## ⚠️ 注意事项

- 如果问题仍然存在，请检查 ConfigMap 是否正确挂载、路径是否匹配
- 确认 ConfigMap 内容是否符合容器启动所需的格式
- 如果容器使用的是 Secret 而非 ConfigMap，请相应地创建和挂载 Secret

---

## 📌 附录

### 工具命令参考

- `kubectl logs <pod> --previous`：查看崩溃前的日志
- `kubectl describe pod <pod>`：查看 Pod 的详细状态、事件、Exit Code 等
- `kubectl get pod -o yaml <pod>`：查看 Pod 的完整 YAML 配置
- `kubectl get configmap <configmap-name>`：查看 ConfigMap 内容

---

## 📊 性能统计

├─ 总耗时: 5.2m
├─ 问题定位: 42.7s (14%) ✅
├─ 证据链采集: 111.2s (36%) ✅
├─ 根因分析: 17.6s (6%) ✅
├─ 汇总总结: 139.5s (45%) ✅
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
