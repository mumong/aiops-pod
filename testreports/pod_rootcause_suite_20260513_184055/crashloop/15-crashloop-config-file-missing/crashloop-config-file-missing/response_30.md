======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 09dfb67e00494a4b]

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
      📄 NAME                                                READY   STATUS             RESTARTS       AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-crashloop-config-file-missing-
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
4m4s (x393 over 89m)   Warning   BackOff   Pod/rc-crashloop-config-file-missing-58cf574c9f-vhlrs   Back-off restarting failed container app in pod rc-crashloop-config-file-mi
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "ConfigError",
  "confidence": "high",
  "reasoning": "Pod 'rc-crashloop-config-file-missing-58cf574c9f-vhlrs' 处于 CrashLoopBackOff 状态，Exit Code 为 1，日志中显示 'required config file missing' 和 'cat: can't open '/etc/rootcause-app/config.yaml''，表明容器启动时缺少必要的配置文件。根据 runbook pod-crashloop-runtime.md，这属于 ConfigError 类型。进一步检查 Pod 的 YAML 配置，发现未指定 ConfigMap 或 Secret 挂载，也没有提供本地配置文件。因此，异常归因于配置缺失。建议检查应用的配置需求，并确保正确挂载配置文件。",
  "abnormal_pods": [
    "rc-crashloop-config-file-missing-58cf574c9f-vhlrs"
  ],
  "abnormal_groups": [
    "CrashLoopBackOffRuntime"
  ],
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "ConfigError",
  "status_category": "CrashLoopBackOffRuntime",
  "key_entities": [
    "Pod: rc-crashloop-config-file-missing-58cf574c9f-vhlrs",
    "Namespace: aiops-e2e",
    "Container: app",
    "Image: busybox:1.36"
  ],
  "possible_scenarios": [
    "配置文件缺失导致容器启动失败",
    "ConfigMap 或 Secret 未正确挂载",
    "容器内命令或脚本错误"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 10.7s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': '配置文件缺失导致容器启动失败', 'probability': 'high', 'reason': "日志中显示 'required config file missing' 和 'cat: can't open '/etc/rootcause-app/config.yaml''"}, {'scenario': 'ConfigMap 或 Secret 未正确挂载', 'probability': 'high', 'reason': 'Pod 的 YAML 配置未指定 ConfigMap 或 Secret 挂载'}, {'scenario': '容器内命令或脚本错误', 'probability': 'medium', 'reason': '容器启动失败可能由于命令或脚本错误'}]
   entities=[{"type": "Pod", "name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs", "namespace": "aiops-e2e"}, {"type": "Namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "Container", "name": "app", "namespace": ""}, {"type": "Image", "name": "busybox:1.36", "namespace": ""}]
   reasoning=Pod 'rc-crashloop-config-file-missing-58cf574c9f-vhlrs' 处于 CrashLoopBackOff 状态，Exit Code 为 1，日志中显示 'required config file missing' 和 'cat: can't open '/etc/rootcause-app/config.yaml''，表明容器启动时缺少必要的配置文件。根据 runbook pod-crashloop-runtime.md，这属于 ConfigError 类型。进一步检查 Pod 的 YAML 配置，发现未指定 ConfigMap 或 Secret 挂载，也没有提供本地配置文件。因此，异常归因于配置缺失。建议检查应用的配置需求，并确保正确挂载配置文件。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.95, "reasoning": "Pod 'rc-crashloop-config-file-missing-58cf574c9f-vhlrs' 处于 CrashLoopBackOff 状态，Exit Code 为 1，日志中显示 'required config file missing' 和 'cat: can't open '/etc/rootcause-app/config.yaml''，表明容器启动时缺少必要的配置文件。根据 runbook pod-crashloop-runtime.md，这属于 ConfigError 类型。进一步检查 Pod 的 YAML 配置，发现未指定 ConfigMap 或 Secret 挂载，也没有提供本地配置文件。因此，异常归因于配置缺失。建议检查应用的配置需求，并确保正确挂载配置文件。", "abnormal_pods": [{"name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "CrashLoopBackOffRuntime", "key_entities": [{"type": "Pod", "name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs", "namespace": "aiops-e2e"}, {"type": "Namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "Container", "name": "app", "namespace": ""}, {"type": "Image", "name": "busybox:1.36", "namespace": ""}], "possible_scenarios": [{"scenario": "配置文件缺失导致容器启动失败", "probability": "high", "reason": "日志中显示 'required config file missing' 和 'cat: can't open '/etc/rootcause-app/config.yaml''"}, {"scenario": "ConfigMap 或 Secret 未正确挂载", "probability": "high", "reason": "Pod 的 YAML 配置未指定 ConfigMap 或 Secret 挂载"}, {"scenario": "容器内命令或脚本错误", "probability": "medium", "reason": "容器启动失败可能由于命令或脚本错误"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-crashloop-config-file-missing-58cf574c9f-vhlrs   0/1     CrashLoopBackOff   22 (79s ago)   89m     172.16.166.155   node1    <none>           <none>            app=rc-crashloop-config-file-missing,pod-template-hash=58cf574c9f,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/09dfb67e00494a4b/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/09dfb67e00494a4b/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/09dfb67e00494a4b/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 95%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-crashloop-config-file-missing-58cf574c9f-vhlrs
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
                  pod_abnormal_type=CrashLoopBackOffRunti
   💭 [证据链采集] 已采集证据：
1. Pod `rc-crashloop-config-file-missing-58cf574c9f-vhlrs` 的状态为 `Running`，但容器处于 `CrashLoopBackOff`，最后一次退出状态码为 `1`，表明容器启动失败。
2. Events 显示 `Back-off restarting failed container app`，说明 kubelet 正在尝试重启失败的容器。
3. Pod 的标签中包含 `pod_abnormal_type=CrashLoopBackOffRuntime`，确认属于该异常类型。
4. 无冲突证据，对象仍然存在且状态与预期异常一致。

下一步建议：
- 查看容器崩溃前的日志（`kubectl_previous_logs`），确认具体失败原因。
- 检查 Pod 的 YAML 配置，查看是否存在 command/args 错误或配置缺失。
   ✅ [证据链采集] 完成 (1m 3.0s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取Pod的详细描述信息，包括Last State、Exit Code、Reason等关键信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e","tool_args":{"pod":"rc-crashloop-config-file-missing-58cf574c9f-vhlrs","namespace":"aiops-e2e"},"purpose":"验证Pod的CrashLoopBackOff状态和Exit Code","evidence_type":"Pod状态验证","target_scope":"aiops-e2e/rc-crashloop-config-file-missing-58cf574c9f-vhlrs","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-crashloop-config-file-missing-58cf574c9f-vhlrs\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n                  pod_abnormal_type=CrashLoopBackOffRuntime\n      Reason:       CrashLoopBackOff\n  Warning  BackOff  58s (x414 over 90m)  kubelet  Back-off restarting failed container app in pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs_aiops-e2e(f116c098-f8d2-46aa-8037-25a4f00eb480)\n                  cni.projectcalico.org/containerID: a7a8a8c3d3f0bc5caf66ae708d1a08e87edea82f85cfac27d31143bfa1250099\n                  cni.projectcalico.org/podIP: 172.16.166.155/32\n                  cni.projectcalico.org/podIPs: 172.16.166.155/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    1","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/09dfb67e00494a4b/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/09dfb67e00494a4b/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/09dfb67e00494a4b/tools/001-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"已采集证据：\n1. Pod `rc-crashloop-config-file-missing-58cf574c9f-vhlrs` 的状态为 `Running`，但容器处于 `CrashLoopBackOff`，最后一次退出状态码为 `1`，表明容器启动失败。\n2. Events 显示 `Back-off restarting failed container app`，说明 kubelet 正在尝试重启失败的容器。\n3. Pod 的标签中包含 `pod_abnormal_type=CrashLoopBackOffRuntime`，确认属于该异常类型。\n4. 无冲突证据，对象仍然存在且状态与预期异常一致。\n\n下一步建议：\n- 查看容器崩溃前的日志（`kubectl_previous_logs`），确认具体失败原因。\n- 检查 Pod 的 YAML 配置，查看是否存在 command/args 错误或配置缺失。","collection_summary":"计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%；其中真实环境证据 6/6 项，完整度 100%；实际执行工具 6 个，匹配计划 1 个，未规划证据 5 个","plan_total":1,"plan_collected":1,"plan_completeness":1.0,"environment_evidence_total":6,"environment_evidence_collected":6,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":1,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"获取Pod的详细描述信息，包括Last State、Exit Code、Reason等关键信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e","purpose":"验证Pod的CrashLoopBackOff状态和Exit Code","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/1 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取Pod的详细描述信息，包括Last State、Exit Code、Reason等关键信息 | `kubectl describe pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aio...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (35.3s)
   📤 → 下游数据: root_cause=Pod 'rc-crashloop-config-file-missing-58cf574c9f-vhlrs' 处于 CrashLoopBackOff 状态，Exit Code 为 1，日志中显示 'required config file missing' 和 'cat: can't open '/etc/rootcause-app/config.yaml''，表明容器启动时缺少必要的配置文件。根据 runbook pod-crashloop-runtime.md，这属于 ConfigError 类型。进一步检查 Pod 的 YAML 配置，发现未指定 ConfigMap 或 Secret 挂载，也没有提供本地配置文件。因此，异常归因于配置缺失。建议检查应用的配置需求，并确保正确挂载配置文件。
   confidence=95%
   causal_chain={"root_cause": "配置缺失", "intermediate_causes": ["容器启动时缺少必要的配置文件", "Pod 的 YAML 配置未指定 ConfigMap 或 Secret 挂载"], "immediate_causes": ["容器启动失败，Exit Code 为 1", "Events 显示 'Back-off restarting failed container app'"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"tool": "kubectl_get_by_kind_in_cluster", "description": "获取集群中所有 Pod 的状态信息", "result": "发现 1 个 Pod 处于 CrashLoopBackOff 状态，其他 48 个 Pod 正常运行"}, {"tool": "kubectl_previous_logs", "description": "获取容器崩溃前的日志", "result": "日志显示 'required config file missing' 和 'cat: can't open '/etc/rootcause-app/config.yaml''"}, {"tool": "kubectl_get_yaml", "description": "获取 Pod 的 YAML 配置", "result": "未指定 ConfigMap 或 Secret 挂载，也没有提供本地配置文件"}], "evidence_analysis": [{"tool": "kubectl_get_by_kind_in_cluster", "analysis": "发现 Pod 'rc-crashloop-config-file-missing-58cf574c9f-vhlrs' 处于 CrashLoopBackOff 状态，表明容器启动失败"}, {"tool": "kubectl_previous_logs", "analysis": "日志显示 'required config file missing' 和 'cat: can't open '/etc/rootcause-app/config.yaml''，表明容器启动时缺少必要的配置文件"}, {"tool": "kubectl_get_yaml", "analysis": "未指定 ConfigMap 或 Secret 挂载，也没有提供本地配置文件，表明配置缺失"}], "causal_chain": {"root_cause": "配置缺失", "intermediate_causes": ["容器启动时缺少必要的配置文件", "Pod 的 YAML 配置未指定 ConfigMap 或 Secret 挂载"], "immediate_causes": ["容器启动失败，Exit Code 为 1", "Events 显示 'Back-off restarting failed container app'"]}, "root_cause": "Pod 'rc-crashloop-config-file-missing-58cf574c9f-vhlrs' 处于 CrashLoopBackOff 状态，Exit Code 为 1，日志中显示 'required config file missing' 和 'cat: can't open '/etc/rootcause-app/config.yaml''，表明容器启动时缺少必要的配置文件。根据 runbook pod-crashloop-runtime.md，这属于 ConfigError 类型。进一步检查 Pod 的 YAML 配置，发现未指定 ConfigMap 或 Secret 挂载，也没有提供本地配置文件。因此，异常归因于配置缺失。建议检查应用的配置需求，并确保正确挂载配置文件。", "root_cause_summary": "Pod 'rc-crashloop-config-file-missing-58cf574c9f-vhlrs' 处于 CrashLoopBackOff 状态，Exit Code 为 1，日志中显示 'required config file missing' 和 'cat: can't open '/etc/rootcause-app/config.yaml''，表明容器启动时缺少必要的配置文件。根据 runbook pod-crashloop-runtime.md，这属于 ConfigError 类型。进一步检查 Pod 的 YAML 配置，发现未指定 ConfigMap 或 Secret 挂载，也没有提供本地配置文件。因此，异常归因于配置缺失。建议检查应用的配置需求，并确保正确挂载配置文件。", "confidence": 0.95, "confidence_reason": "有直接证据，因果链清晰", "primary_runbooks": ["pod-crashloop-runtime.md"], "alternative_causes": [{"cause": "容器内命令或脚本错误", "probability": "medium", "reason": "容器启动失败可能由于命令或脚本错误"}], "limitations": "无", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'rc-crashloop-config-file-missing-58cf574c9f-vhlrs' 处于 CrashLoopBackOff 状态，Exit Code 为 1，日志中显示 'required config file missing' 和 'cat: can't open '...
   置信度: 95%
   🔗 因果链:
     根本原因: 配置缺失


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 16.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4595 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 5.3s
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
| **兼容归因层** | L4 |
| **问题分类** | ConfigError |
| **置信度** | 高 (95%) |
| **证据完整度** | 1/1 (100%) |

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
| 错误信息 | `required config file missing`, `cat: can't open '/etc/rootcause-app/config.yaml'` |

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff, RESTARTS: 22` | Pod 持续崩溃并重启 |
| 2 | 容器退出码 | `kubectl describe pod` | `Exit Code: 1, Reason: Error` | 容器启动失败，Exit Code 为 1 |
| 3 | 容器日志 | `kubectl logs --previous` | `RUNTIME_STARTUP_ERROR: required config file missing`<br>`cat: can't open '/etc/rootcause-app/config.yaml'` | 启动失败原因为配置文件缺失 |
| 4 | Pod YAML 配置 | `kubectl get pod -o yaml` | 未挂载 ConfigMap 或 Secret，也未指定本地配置文件 | 缺少配置文件挂载 |
| 5 | Pod 事件 | `kubectl describe pod` | `Warning BackOff Pod/rc-crashloop-config-file-missing-58cf574c9f-vhlrs Back-off restarting failed container app` | 容器持续失败，Kubernetes 正在 BackOff |
| 6 | Runbook 分析 | `fetch_runbook` | `pod-crashloop-runtime.md` 归类为 `ConfigError` 类型 | 根据 Runbook，问题归因于配置缺失 |

### 证据关联分析
- **证据 #3 + #4 印证**：容器崩溃日志中提示配置文件缺失，而 YAML 中未挂载任何配置文件 → 确认是配置缺失导致容器启动失败。
- **证据链**：配置文件缺失 → 容器启动失败 → Pod 进入 CrashLoopBackOff → Kubernetes 持续重启失败的容器。

### 缺失证据
| 证据 | 级别 | 影响 |
|------|------|------|
| 无 | 无 | 证据完整度为 100%，无需补充 |

---

## 🎯 根因分析
### 因果链
```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                          │
│ 应用容器启动时缺少必要的配置文件 '/etc/rootcause-app/config.yaml'，导致启动失败。     │
└──────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                          │
│ 应用尝试读取配置文件失败 → 启动命令失败 → 容器退出 → Pod 进入 CrashLoopBackOff 状态。 │
└──────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                          │
│ 容器退出码为 1，日志中提示 'required config file missing'，确认为配置文件缺失。         │
└──────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                      │
│ Pod 状态为 CrashLoopBackOff，持续重启，无法正常运行。                                │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #3 (`RUNTIME_STARTUP_ERROR: required config file missing`) 和证据 #4 (Pod YAML 中未挂载配置文件)，问题的根本原因是**容器启动时缺少必要的配置文件 `/etc/rootcause-app/config.yaml`**，导致容器启动失败并进入 CrashLoopBackOff 状态。

**置信度**：高 (95%)
- ✅ Exit Code 1 明确指向启动失败
- ✅ 日志明确提示配置文件缺失
- ✅ YAML 配置未挂载配置文件
- ✅ Runbook 明确认定为 ConfigError 类型

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 挂载缺失的配置文件**
```bash
kubectl set image deployment/<deployment-name> app=image-with-config
# 或者
kubectl apply -f <path-to-pod-or-deployment-with-config.yaml>
```
*依据*：容器需要 `/etc/rootcause-app/config.yaml`，应在 Pod YAML 中挂载 ConfigMap 或 Secret，或者直接挂载本地配置文件。

**2. [可选] 检查 ConfigMap/Secret 是否存在**
```bash
kubectl get configmap -n aiops-e2e
kubectl get secret -n aiops-e2e
```
*目的*：确认是否存在预期的配置文件资源。

**3. [可选] 查看崩溃前日志**
```bash
kubectl logs rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e --previous
```
*目的*：确认是否还有其他导致启动失败的异常。

### 后续优化
1. **验证配置挂载路径**：确认容器内的路径与实际挂载路径一致。
2. **增加健康检查**：在 Pod YAML 中配置 `livenessProbe` 和 `readinessProbe`，避免容器进入 CrashLoopBackOff。
3. **配置告警**：监控 Pod 状态，及时发现类似问题。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e` | STATUS: Running |
| 2. 检查容器日志 | `kubectl logs rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e` | 无启动错误信息 |
| 3. 检查配置文件是否挂载 | `kubectl exec -it rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e -- ls /etc/rootcause-app/` | 包含 `config.yaml` |

---

## ⚠️ 注意事项
- 如果配置文件需要动态更新，建议使用 ConfigMap 或 Secret 动态挂载。
- 如果问题仍存在，请检查容器启动命令是否正确读取配置文件。
- 请确保挂载路径在容器内与应用期望一致，避免路径错误导致的文件未找到问题。

---

## 📊 性能统计

├─ 总耗时: 4.1m
├─ 问题定位: 70.7s (29%) ✅
├─ 证据链采集: 63.0s (26%) ✅
├─ 根因分析: 35.3s (14%) ✅
├─ 汇总总结: 76.3s (31%) ✅
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
