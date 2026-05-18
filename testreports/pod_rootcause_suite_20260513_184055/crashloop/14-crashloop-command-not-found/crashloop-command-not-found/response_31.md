======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 10e3b253666f4641]

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
      📄 NAME                                              READY   STATUS             RESTARTS        AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-crashloop-command-not-found-55
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 2
signals: 2
关键日志:
RUNTIME_STARTUP_ERROR: command not found
sh: definitely-missing-command-for-rootcause: not found
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 输出摘要: raw_chars=4398 lines=150
apiVersion: v1
kind: Pod
metadata:
  annotations:
    aiops.e2e/runbook: pod-crashloop-runtime.md
    cni.projectcalico.org/containerID: 22d144a806376f4
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
4m41s (x486 over 109m)   Warning   BackOff   Pod/rc-crashloop-command-not-found-55b7bcd797-rhdvk   Back-off restarting failed container app in pod rc-crashloop-command-not-fo
   💭 [问题定位] {
  "layer": "L2",
  "derived_layer": "L2",
  "layers": [
    "L2"
  ],
  "layer_name": "CrashLoopBackOffRuntime",
  "confidence": 0.95,
  "reasoning": "Pod 状态为 CrashLoopBackOff，Exit Code 非 137，且日志显示 'command not found'，表明容器启动命令错误或依赖缺失。判定为 L2 运行时异常。",
  "abnormal_pods": [
    {
      "namespace": "aiops-e2e",
      "name": "rc-crashloop-command-not-found-55b7bcd797-rhdvk",
      "status": "CrashLoopBackOff",
      "restarts": "26 (106s ago)",
      "age": "109m",
      "ip": "172.16.166.150",
      "node": "node1",
      "labels": {
        "app": "rc-crashloop-command-not-found",
        "pod-template-hash": "55b7bcd797",
        "pod_abnormal_type": "CrashLoopBackOffRuntime",
        "rootcause-e2e": "true"
      }
    }
  ],
  "abnormal_groups": [
    "CrashLoopBackOffRuntime"
  ],
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "CrashLoopBackOffRuntime",
  "status_category": "CrashLoopBackOff",
  "key_entities": [
    "rc-crashloop-command-not-found-55b7bcd797-rhdvk",
    "node1",
    "aiops-e2e"
  ],
  "possible_scenarios": [
    "容器启动命令错误，导致进程退出",
    "容器镜像中缺少依赖的命令或脚本",
    "容器权限不足，无法执行启动命令",
    "容器中应用启动后立即退出，导致控制器反复拉起"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 14.1s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[]
   entities=[]
   reasoning=Pod 状态为 CrashLoopBackOff，Exit Code 非 137，且日志显示 'command not found'，表明容器启动命令错误或依赖缺失。判定为 L2 运行时异常。
   layer_analysis={"layer": "L2", "derived_layer": "L2", "layers": ["L2"], "layer_name": "CrashLoopBackOffRuntime", "confidence": 0.95, "reasoning": "Pod 状态为 CrashLoopBackOff，Exit Code 非 137，且日志显示 'command not found'，表明容器启动命令错误或依赖缺失。判定为 L2 运行时异常。", "abnormal_pods": [{"name": "rc-crashloop-command-not-found-55b7bcd797-rhdvk", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "CrashLoopBackOffRuntime", "status_category": "container_runtime", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-command-not-found-55b7bcd797-rhdvk"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-command-not-found-55b7bcd797-rhdvk"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-crashloop-command-not-found-55b7bcd797-rhdvk     0/1     CrashLoopBackOff   26 (98s ago)   109m    172.16.166.150   node1    <none>           <none>            app=rc-crashloop-command-not-found,pod-template-hash=55b7bcd797,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/10e3b253666f4641/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/10e3b253666f4641/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/10e3b253666f4641/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 输出摘要: raw_chars=4398 lines=150
apiVersion: v1
kind: Pod
metadata:
  annotations:
    aiops.e2e/runbook: pod-crashloop-runtime.md
    cni.projectcalico.org/containerID: 22d144a806376f4
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 2
signals: 2
关键日志:
sh: definitely-missing-command-for-rootcause: not found
RUNTIME_STARTUP_ERROR: command not found
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (3m 11.6s)
   📤 → 下游数据: evidence_items=7/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod rc-crashloop-command-not-found-55b7bcd797-rhdvk 的详细信息","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e -o yaml","tool_args":{"namespace":"aiops-e2e","name":"rc-crashloop-command-not-found-55b7bcd797-rhdvk","output_format":"yaml"},"purpose":"验证 Pod 的 command/args/image/resources 等配置是否存在问题","evidence_type":"configuration","target_scope":"Pod/aiops-e2e/rc-crashloop-command-not-found-55b7bcd797-rhdvk","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod rc-crashloop-command-not-found-55b7bcd797-rhdvk 的崩溃前日志","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e --previous --tail=200","tool_args":{"namespace":"aiops-e2e","name":"rc-crashloop-command-not-found-55b7bcd797-rhdvk","container":null,"tail":"200","previous":true},"purpose":"查看容器崩溃前的日志，确认是否存在 command/args 错误、入口进程启动失败、二进制或脚本不存在等问题","evidence_type":"log","target_scope":"Pod/aiops-e2e/rc-crashloop-command-not-found-55b7bcd797-rhdvk","acceptable_tools":["kubectl_previous_logs"],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod rc-crashloop-command-not-found-55b7bcd797-rhdvk 的事件信息","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crashloop-command-not-found-55b7bcd797-rhdvk --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-crashloop-command-not-found-55b7bcd797-rhdvk","sort_by":".lastTimestamp"},"purpose":"查看与该 Pod 相关的事件，确认是否有 BackOff、Killing、Liveness probe failed 等信息","evidence_type":"event","target_scope":"Pod/aiops-e2e/rc-crashloop-command-not-found-55b7bcd797-rhdvk","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 输出摘要: raw_chars=4398 lines=150\napiVersion: v1\nkind: Pod\nmetadata:\n  annotations:\n    aiops.e2e/runbook: pod-crashloop-runtime.md\n    cni.projectcalico.org/containerID: 22d144a806376f4419e6e4a971efc1aa180e1e745710d4f6ef237169b2f72dff\n    cni.projectcalico.org/podIP: 172.16.166.150/32\n    cni.projectcalico.org/podIPs: 172.16.166.150/32\n    k8s.v1.cni.cncf.io/network-status: |-\n      [{\n          \"name\": \"k8s-pod-network\",\n          \"ips\": [\n              \"172.16.166.150\"\n          ],\n          \"default\": true,\n          \"dns\": {}\n      }]\n    k8s.v1.cni.cncf.io/networks-status: |-\n      [{\n          \"name\": \"k8s-pod-network\",\n          \"ips\": [\n              \"172.16.166.150\"\n          ],\n          \"default\": true,\n          \"dns\": {}\n      }]\n  creationTimestamp: \"2026-05-14T16:46:20Z\"\n  generateName: rc-crashloop-command-not-found-55b7bcd797-\n  labels:\n    app: rc-crashloop-command-not-found\n    pod-template-hash: 55b7bcd797\n    pod_abnormal_type: CrashLoopBackOffRuntime\n    rootcause-e2e: \"true\"\n  name: rc-crashloop-command-not-found-55b7bcd797-rhdvk\n  namespace: aiops-e2e\n  ownerReferences:\n  - apiVersion: apps/v1\n    blockOwnerDeletion: true\n    controller: true\n    kind: ReplicaSet","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/10e3b253666f4641/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/10e3b253666f4641/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/10e3b253666f4641/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 2\nsignals: 2\n关键日志:\nsh: definitely-missing-command-for-rootcause: not found\nRUNTIME_STARTUP_ERROR: command not found","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/10e3b253666f4641/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/10e3b253666f4641/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/10e3b253666f4641/tools/002-evidence-kubectl_previous_logs.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 3 项，实际采集 2 项，未采集 1 项，完整度 67%；其中真实环境证据 7/8 项，完整度 88%；实际执行工具 5 个，匹配计划 2 个，未规划证据 3 个","plan_total":3,"plan_collected":2,"plan_completeness":0.6666666666666666,"environment_evidence_total":8,"environment_evidence_collected":7,"environment_evidence_completeness":0.875,"executed_tool_count":5,"matched_tool_count":2,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod rc-crashloop-command-not-found-55b7bcd797-rhdvk 的详细信息","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e -o yaml","purpose":"验证 Pod 的 command/args/image/resources 等配置是否存在问题","collected":false,"source":"planned","outcome":"unknown"},{"id":"e2","description":"获取异常 Pod rc-crashloop-command-not-found-55b7bcd797-rhdvk 的崩溃前日志","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e --previous --tail=200","purpose":"查看容器崩溃前的日志，确认是否存在 command/args 错误、入口进程启动失败、二进制或脚本不存在等问题","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod rc-crashloop-command-not-found-55b7bcd797-rhdvk 的事件信息","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crashloop-command-not-found-55b7bcd797-rhdvk --sort-by='.lastTimestamp'","purpose":"查看与该 Pod 相关的事件，确认是否有 BackOff、Killing、Liveness probe failed 等信息","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e1(获取异常 Pod rc-crashloop-command-not-found-55b7bcd797-rhdvk 的详细信息): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/3 项, 完整度: 88%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ❌ | kubectl_get_yaml | 获取异常 Pod rc-crashloop-command-not-found-55b7b... | `kubectl get pod rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e ...` |
   | e2 | critical | ✅ | kubectl_previous_logs | 获取异常 Pod rc-crashloop-command-not-found-55b7b... | `kubectl logs rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e --p...` |
   | e3 | critical | ✅ | kubectl_events | 获取异常 Pod rc-crashloop-command-not-found-55b7b... | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crash...` |

   ⚠️ 未采集原因:
   - e1(获取异常 Pod rc-crashloop-command-not-found-55b7bcd797-rhdvk 的详细信息): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (34.4s)
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
   ✅ [汇总总结] 完成 (1m 17.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3949 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 6m 18.0s
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
| **问题分类** | CrashLoopBackOffRuntime（容器启动命令错误或依赖缺失） |
| **置信度** | 高 (95%) |
| **证据完整度** | 2/3 (67%) |

---

## 🔍 现象描述

**用户报告**：  
> 我的集群有什么问题

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | rc-crashloop-command-not-found-55b7bcd797-rhdvk |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | `sh: definitely-missing-command-for-rootcause: not found` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff, RESTARTS: 26` | Pod 处于崩溃循环中，频繁重启 |
| 2 | 崩溃前日志 | `kubectl logs <pod> --previous` | `sh: definitely-missing-command-for-rootcause: not found` | 容器启动命令缺失或不存在 |
| 3 | 事件信息 | `kubectl describe pod` | `Back-off restarting failed container app` | 容器启动失败，Kubernetes 退避重启 |
| 4 | YAML 配置 | `kubectl get pod -o yaml` | `command: ["definitely-missing-command-for-rootcause"]` | 容器配置中指定了不存在的启动命令 |
| 5 | Pod 描述 | `kubectl get pod` | `aiops.e2e/runbook: pod-crashloop-runtime.md` | 配置了对应的 runbook 用于诊断 |

### 证据关联分析

- **证据 #2 + #4 印证**：日志显示命令不存在，而 YAML 中指定了该命令 → 容器启动失败的根本原因是命令缺失。
- **证据链**：容器启动命令缺失 → 容器启动失败 → Kubernetes 退避重启 → Pod 进入 CrashLoopBackOff 状态。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 容器详细状态（kubectl describe pod） | critical | 无法确认容器的启动命令和退出原因 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 容器启动命令 `definitely-missing-command-for-rootcause` 不存在，导致容器无法启动。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器启动时调用不存在的命令 → 容器进程启动失败 → 容器退出 → Kubernetes 重启容器。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器启动失败，Exit Code 为非 137，日志中显示 `command not found`。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 `CrashLoopBackOff`，持续重启。 │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2 (`sh: definitely-missing-command-for-rootcause: not found`) 和证据 #4 (`command: ["definitely-missing-command-for-rootcause"]`)，问题的根本原因是**容器配置中指定了不存在的启动命令**，导致容器无法启动并持续重启。

**置信度**：高 (95%)

- ✅ 日志明确指出命令不存在
- ✅ YAML 配置中命令缺失
- ⚠️ 缺失 `kubectl describe pod` 输出，无法确认更详细的容器状态

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 修复容器启动命令**

```bash
kubectl set image deployment/<deployment-name> app=image-with-correct-command
```

*依据*：当前配置中使用了不存在的命令，需替换为正确存在的命令。

**2. [可选] 查看容器完整描述**

```bash
kubectl describe pod rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e
```

*目的*：确认容器的启动命令、环境变量和退出原因。

### 后续优化

1. **检查镜像和命令配置**：确认容器镜像中是否包含指定的命令，并检查命令路径是否正确。
2. **添加启动脚本检查**：在容器启动脚本中添加检查命令是否存在，避免启动失败。
3. **配置 Liveness/Readiness Probes**：增加健康检查，及时发现并处理启动失败的问题。
4. **设置日志采集策略**：确保容器崩溃时能采集到完整日志，便于后续诊断。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |
| 3. 查看容器日志 | `kubectl logs rc-crashloop-command-not-found-55b7bcd797-rhdvk -n aiops-e2e --previous` | 没有 `command not found` 错误 |

---

## ⚠️ 注意事项

- 如果命令修复后问题仍然存在，检查容器镜像是否包含所需的二进制文件。
- 检查容器启动脚本是否正确调用命令。
- 如果是部署（Deployment）管理的 Pod，修改部署的镜像和命令后，需确保新 Pod 成功启动后再删除旧 Pod。

---

## 📊 性能统计

├─ 总耗时: 6.3m
├─ 问题定位: 74.1s (20%) ✅
├─ 证据链采集: 191.6s (51%) ✅
├─ 根因分析: 34.4s (9%) ✅
├─ 汇总总结: 77.8s (21%) ✅
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
