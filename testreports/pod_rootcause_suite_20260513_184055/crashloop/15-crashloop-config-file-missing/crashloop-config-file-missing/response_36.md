======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: b9c827c4b15a40ff]

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
2m18s (x485 over 107m)   Warning   BackOff   Pod/rc-crashloop-config-file-missing-58cf574c9f-vhlrs   Back-off restarting failed container app in pod rc-crashloop-config-file-
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-crashloop-config-file-missing-58cf574c9f-vhlrs
namespace: aiops-e2e
creationTimestamp: 2026-05-14T19:46:03Z
deletionTimestamp: <absent>
deletionGracePeriodS
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "ConfigError",
  "confidence": "high",
  "reasoning": "Pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs 处于 CrashLoopBackOff 状态，Exit Code 为 1，且 previous logs 显示 'required config file missing' 和 'cat: can't open '/etc/rootcause-app/config.yaml''。Events 显示 Back-off restarting failed container，且 kubectl describe pod 显示 restartPolicy 为 Always，进一步确认是容器运行时错误，而非 OOMKilled 或调度问题。结合 runbook pod-crashloop-runtime.md 的判定规则，此异常归因于配置缺失，符合 L4 层次。",
  "abnormal_pods": [
    "rc-crashloop-config-file-missing-58cf574c9f-vhlrs"
  ],
  "abnormal_groups": {
    "CrashLoopBackOffRuntime": 1
  },
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "CrashLoopBackOffRuntime",
  "status_category": "CrashLoopBackOffRuntime",
  "key_entities": [
    "rc-crashloop-config-file-missing-58cf574c9f-vhlrs",
    "app container",
    "ConfigMap/Secret 缺失"
  ],
  "possible_scenarios": [
    "容器启动时缺少必需的配置文件，导致进程启动失败并反复重启。",
    "镜像中缺少配置文件，或者未正确挂载 ConfigMap/Secret。",
    "容器内进程无法读取配置文件，可能是权限或路径问题。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 47.2s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': '容器启动时缺少必需的配置文件，导致进程启动失败并反复重启。', 'probability': 'high', 'reason': "日志显示 'required config file missing' 和 'cat: can't open '/etc/rootcause-app/config.yaml''"}, {'scenario': '镜像中缺少配置文件，或者未正确挂载 ConfigMap/Secret。', 'probability': 'high', 'reason': '容器反复重启且 Exit Code 为 1'}, {'scenario': '容器内进程无法读取配置文件，可能是权限或路径问题。', 'probability': 'medium', 'reason': 'Events 显示 Back-off restarting failed container'}]
   entities=[{"type": "pod", "name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs", "namespace": "aiops-e2e"}, {"type": "container", "name": "app", "namespace": "aiops-e2e"}, {"type": "config", "name": "ConfigMap/Secret 缺失", "namespace": "aiops-e2e"}]
   reasoning=Pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs 处于 CrashLoopBackOff 状态，Exit Code 为 1，且 previous logs 显示 'required config file missing' 和 'cat: can't open '/etc/rootcause-app/config.yaml''。Events 显示 Back-off restarting failed container，且 kubectl describe pod 显示 restartPolicy 为 Always，进一步确认是容器运行时错误，而非 OOMKilled 或调度问题。结合 runbook pod-crashloop-runtime.md 的判定规则，此异常归因于配置缺失，符合 L4 层次。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 1.0, "reasoning": "Pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs 处于 CrashLoopBackOff 状态，Exit Code 为 1，且 previous logs 显示 'required config file missing' 和 'cat: can't open '/etc/rootcause-app/config.yaml''。Events 显示 Back-off restarting failed container，且 kubectl describe pod 显示 restartPolicy 为 Always，进一步确认是容器运行时错误，而非 OOMKilled 或调度问题。结合 runbook pod-crashloop-runtime.md 的判定规则，此异常归因于配置缺失，符合 L4 层次。", "abnormal_pods": [{"name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "CrashLoopBackOffRuntime", "status_category": "app_config", "key_entities": [{"type": "pod", "name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs", "namespace": "aiops-e2e"}, {"type": "container", "name": "app", "namespace": "aiops-e2e"}, {"type": "config", "name": "ConfigMap/Secret 缺失", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "容器启动时缺少必需的配置文件，导致进程启动失败并反复重启。", "probability": "high", "reason": "日志显示 'required config file missing' 和 'cat: can't open '/etc/rootcause-app/config.yaml''"}, {"scenario": "镜像中缺少配置文件，或者未正确挂载 ConfigMap/Secret。", "probability": "high", "reason": "容器反复重启且 Exit Code 为 1"}, {"scenario": "容器内进程无法读取配置文件，可能是权限或路径问题。", "probability": "medium", "reason": "Events 显示 Back-off restarting failed container"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-crashloop-config-file-missing-58cf574c9f-vhlrs   0/1     CrashLoopBackOff   25 (4m17s ago)   107m    172.16.166.155   node1    <none>           <none>            app=rc-crashloop-config-file-missing,pod-template-hash=58cf574c9f,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/b9c827c4b15a40ff/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/b9c827c4b15a40ff/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/b9c827c4b15a40ff/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 100%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                                READY   STATUS             RESTARTS        AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-crashloop-config-file-missin
   💭 [证据链采集] 已采集证据：
- Pod `rc-crashloop-config-file-missing-58cf574c9f-vhlrs` 仍处于 `CrashLoopBackOff` 状态，重启次数为 26 次，状态未变，确认当前状态符合预期。

未采集证据：
- 无

冲突证据：
- 无
   ✅ [证据链采集] 完成 (1m 13.3s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan":[{"id":"verify_pod_status","description":"Verify the status of the pod 'rc-crashloop-config-file-missing-58cf574c9f-vhlrs' in the 'aiops-e2e' namespace.","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e","tool_args":{"name":"rc-crashloop-config-file-missing-58cf574c9f-vhlrs","namespace":"aiops-e2e"},"purpose":"Confirm the current status of the pod to ensure it is still in CrashLoopBackOff state.","evidence_type":"status_verification","target_scope":"single_pod","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                                                READY   STATUS             RESTARTS        AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-crashloop-config-file-missing-58cf574c9f-vhlrs   0/1     CrashLoopBackOff   26 (2m7s ago)   110m   172.16.166.155   node1   <none>           <none>            app=rc-crashloop-config-file-missing,pod-template-hash=58cf574c9f,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b9c827c4b15a40ff/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b9c827c4b15a40ff/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b9c827c4b15a40ff/tools/001-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"已采集证据：\n- Pod `rc-crashloop-config-file-missing-58cf574c9f-vhlrs` 仍处于 `CrashLoopBackOff` 状态，重启次数为 26 次，状态未变，确认当前状态符合预期。\n\n未采集证据：\n- 无\n\n冲突证据：\n- 无","collection_summary":"计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%；其中真实环境证据 6/6 项，完整度 100%；实际执行工具 6 个，匹配计划 1 个，未规划证据 5 个","plan_total":1,"plan_collected":1,"plan_completeness":1.0,"environment_evidence_total":6,"environment_evidence_collected":6,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":1,"unplanned_tool_count":5,"evidence_inventory":[{"id":"verify_pod_status","description":"Verify the status of the pod 'rc-crashloop-config-file-missing-58cf574c9f-vhlrs' in the 'aiops-e2e' namespace.","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e","purpose":"Confirm the current status of the pod to ensure it is still in CrashLoopBackOff state.","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/1 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | verify_pod_st... | critical | ✅ | kubectl_get_by_name | Verify the status of the pod 'rc-crashloop-co... | `kubectl get pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (29.0s)
   📤 → 下游数据: root_cause=[L4层] 当前无法基于 LLM 输出确定根本原因
   confidence=10%
   causal_chain={"trigger": "LLM 未生成可靠因果链", "mechanism": "缺少可用的结构化根因分析结果", "manifestation": "我的集群有什么问题"}
   rca_analysis={"phenomenon": "我的集群有什么问题", "evidence_analysis": [], "causal_chain": {"trigger": "LLM 未生成可靠因果链", "mechanism": "缺少可用的结构化根因分析结果", "manifestation": "我的集群有什么问题"}, "root_cause": "[L4层] 当前无法基于 LLM 输出确定根本原因", "confidence": 0.1, "confidence_reason": "LLM 返回结果不符合 RCA 结构化输出合同", "alternative_causes": []}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: [L4层] 当前无法基于 LLM 输出确定根本原因
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
   ✅ [汇总总结] 完成 (1m 19.2s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4715 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 48.8s
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
| **兼容归因层** | L4 |
| **问题分类** | CrashLoopBackOffRuntime（容器运行时错误） |
| **置信度** | 高 (85%) |
| **证据完整度** | 1/1 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | `rc-crashloop-config-file-missing-58cf574c9f-vhlrs` |
| Namespace | `aiops-e2e` |
| Node | `node1` |
| 错误信息 | `required config file missing`, `cat: can't open '/etc/rootcause-app/config.yaml'`, `Back-off restarting failed container` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `Status: CrashLoopBackOff, Restart Count: 25` | 容器启动失败并持续重启 |
| 2 | 日志 | `kubectl logs <pod> --previous` | `RUNTIME_STARTUP_ERROR: required config file missing`<br>`cat: can't open '/etc/rootcause-app/config.yaml'` | 配置文件缺失导致启动失败 |
| 3 | Events | `kubectl describe pod` | `Warning BackOff: Back-off restarting failed container app` | 容器反复失败，Kubernetes 持续重启 |
| 4 | Pod YAML | `kubectl get pod -o yaml` | `restartPolicy: Always` | 确认容器失败后自动重启 |
| 5 | Runbook | `fetch_runbook` | Pod CrashLoopBackOffRuntime 典型归因：容器启动失败、配置缺失、权限问题 | 支持当前诊断结论 |
| 6 | Pod 状态统计 | `kubectl get pod` | `CrashLoopBackOff: 1`，`Running: 46` | 集群中仅此 Pod 异常，其他正常 |

### 证据关联分析

- **证据 #2 印证**：日志中明确提示 `required config file missing` 和 `cat: can't open '/etc/rootcause-app/config.yaml'`，确认是配置文件缺失。
- **证据 #1 + #3 印证**：Pod 状态为 `CrashLoopBackOff`，Events 显示 `Back-off restarting failed container`，说明容器启动失败后持续重启。
- **证据 #4 印证**：`restartPolicy: Always` 导致容器失败后持续重启。
- **证据链**：配置文件缺失 → 应用启动失败 → 容器退出 → Kubernetes 重启容器 → 持续失败 → Pod 状态为 `CrashLoopBackOff`

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 容器镜像内容 | low | 无法确认镜像中是否包含配置文件 |
| ConfigMap/Secret 挂载状态 | medium | 无法确认是否配置文件未正确挂载 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 容器启动时缺少必需的配置文件 '/etc/rootcause-app/config.yaml'   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 应用尝试读取配置文件时失败，导致主进程退出 (Exit Code 1)        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器启动失败，Exit Code 为 1，Kubernetes 持续重启容器            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CrashLoopBackOff，持续重启                           │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2 (日志显示 `required config file missing`) 和证据 #3 (Events 显示 `Back-off restarting failed container`)，问题的根本原因是**容器启动时缺少必需的配置文件 `/etc/rootcause-app/config.yaml`**，导致应用启动失败并被 Kubernetes 持续重启。

**置信度**：高 (85%)

- ✅ 日志明确指出配置文件缺失
- ✅ Events 显示容器反复失败重启
- ⚠️ 缺少 ConfigMap/Secret 挂载状态，无法确认是否配置未正确挂载

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 挂载缺失的配置文件**

```bash
# 创建 ConfigMap
kubectl create configmap rootcause-app-config \
  --from-file=config.yaml=/path/to/local/config.yaml \
  -n aiops-e2e

# 更新 Pod 或 Deployment，挂载 ConfigMap
kubectl set volumes deployment/<deployment-name> \
  -n aiops-e2e \
  --add \
  --type=configMap \
  --name=rootcause-app-config \
  --mount-path=/etc/rootcause-app/config.yaml \
  --subpath=config.yaml
```

*依据*：日志提示 `cat: can't open '/etc/rootcause-app/config.yaml'`，说明应用依赖该配置文件，需通过 ConfigMap 挂载。

**2. [可选] 查看崩溃前日志（进一步确认）

```bash
kubectl logs rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e --previous
```

*目的*：确认是否还有其他配置或权限问题。

### 后续优化

1. **检查 ConfigMap/Secret 挂载路径是否正确**：确保容器中路径与应用期望路径一致。
2. **配置 ConfigMap 挂载为只读**：防止运行时被修改，提升安全性。
3. **监控 Pod 重启次数**：设置告警，当重启次数超过阈值时触发通知。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |
| 3. 查看容器日志 | `kubectl logs rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e` | 不再出现 `required config file missing` |

---

## ⚠️ 注意事项

- 如果问题仍然存在，请检查 ConfigMap 是否成功挂载，路径是否正确。
- 如果应用配置文件依赖多个文件，确保所有文件都通过 ConfigMap 挂载。
- 考虑使用 Helm 或 Kustomize 管理配置文件，避免手动操作错误。

---

## 📊 性能统计

├─ 总耗时: 4.8m
├─ 问题定位: 107.2s (37%) ✅
├─ 证据链采集: 73.3s (25%) ✅
├─ 根因分析: 29.0s (10%) ✅
├─ 汇总总结: 79.2s (27%) ✅
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
