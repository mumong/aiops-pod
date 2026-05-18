======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: b9dfeff0728045e6]

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
      📄 NAME                                                READY   STATUS             RESTARTS      AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-crashloop-config-file-missing-5
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
   💭 [问题定位] {
  "abnormal_pods": [
    {
      "namespace": "aiops-e2e",
      "name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs",
      "status": "CrashLoopBackOff",
      "reason": "Error",
      "message": "required config file missing",
      "restarts": "3 (44s ago)",
      "age": "90s",
      "ip": "172.16.166.155",
      "node": "node1",
      "labels": {
        "app": "rc-crashloop-config-file-missing",
        "pod-template-hash": "58cf574c9f",
        "pod_abnormal_type": "CrashLoopBackOffRuntime",
        "rootcause-e2e": "true"
      }
    }
  ],
  "abnormal_groups": [
    {
      "pod_status_keyword": "CrashLoopBackOff",
      "pod_abnormal_type": "CrashLoopBackOffRuntime",
      "status_category": "CrashLoopBackOffRuntime",
      "count": 1
    }
  ],
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "CrashLoopBackOffRuntime",
  "status_category": "CrashLoopBackOffRuntime",
  "key_entities": [
    "Pod: rc-crashloop-config-file-missing-58cf574c9f-vhlrs",
    "Container: app",
    "Node: node1",
    "Image: busybox:1.36"
  ],
  "possible_scenarios": [
    "容器启动时缺少必需的配置文件（如 /etc/rootcause-app/config.yaml）",
    "容器入口命令执行失败，导致容器立即退出",
    "容器内进程启动后立即退出，触发 CrashLoopBackOff",
    "容器镜像缺失关键依赖或配置，导致启动失败"
  ],
  "layer": "L2",
  "derived_layer": "L2",
  "layers": [
    "L2"
  ],
  "layer_name": "CrashLoopBackOffRuntime",
  "confidence": "high",
  "reasoning": "Pod 状态为 CrashLoopBackOff，容器退出代码为 1，日志显示缺少必需的配置文件，符合 CrashLoopBackOffRuntime 的特征。"
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 34.5s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[{'scenario': '容器启动时缺少必需的配置文件（如 /etc/rootcause-app/config.yaml）', 'probability': 'high', 'reason': '日志中显示 required config file missing 和 No such file or directory'}]
   entities=[{"type": "Pod", "name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs", "namespace": ""}, {"type": "Container", "name": "app", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Image", "name": "busybox:1.36", "namespace": ""}]
   reasoning=Pod 状态为 CrashLoopBackOff，容器退出代码为 1，日志显示缺少必需的配置文件，符合 CrashLoopBackOffRuntime 的特征。
   layer_analysis={"layer": "L2", "derived_layer": "", "layers": [], "layer_name": "", "confidence": 0.5, "reasoning": "Pod 状态为 CrashLoopBackOff，容器退出代码为 1，日志显示缺少必需的配置文件，符合 CrashLoopBackOffRuntime 的特征。", "abnormal_pods": [{"name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "CrashLoopBackOffRuntime", "status_category": "CrashLoopBackOffRuntime", "key_entities": [{"type": "Pod", "name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs", "namespace": ""}, {"type": "Container", "name": "app", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Image", "name": "busybox:1.36", "namespace": ""}], "possible_scenarios": [{"scenario": "容器启动时缺少必需的配置文件（如 /etc/rootcause-app/config.yaml）", "probability": "high", "reason": "日志中显示 required config file missing 和 No such file or directory"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-crashloop-config-file-missing-58cf574c9f-vhlrs   0/1     CrashLoopBackOff   3 (39s ago)   85s     172.16.166.155   node1    <none>           <none>            app=rc-crashloop-config-file-missing,pod-template-hash=58cf574c9f,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/b9dfeff0728045e6/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/b9dfeff0728045e6/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/b9dfeff0728045e6/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                                READY   STATUS             RESTARTS        AGE     IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-crashloop-config-file-missi
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 2
signals: 2
关键日志:
RUNTIME_STARTUP_ERROR: required config file missing
cat: can't open '/etc/rootcause-app/config.yaml': No such file or directory
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (2m 47.7s)
   📤 → 下游数据: evidence_items=6/7
   evidence_analysis={"evidence_plan":[{"id":"verify_pod_crashloop_runtime","description":"验证 CrashLoopBackOffRuntime 异常 Pod 的 Last State、Exit Code、Reason 和重启次数","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e -o yaml","tool_args":{"name":"rc-crashloop-config-file-missing-58cf574c9f-vhlrs","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"验证 Pod 的 Last State、Exit Code、Reason 和重启次数","evidence_type":"Pod 状态验证","target_scope":"aiops-e2e/rc-crashloop-config-file-missing-58cf574c9f-vhlrs","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true},{"id":"verify_pod_previous_logs","description":"验证 CrashLoopBackOffRuntime 异常 Pod 的崩溃前日志","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e --previous --tail=200","tool_args":{"pod_name":"rc-crashloop-config-file-missing-58cf574c9f-vhlrs","namespace":"aiops-e2e","tail_lines":200},"purpose":"验证崩溃前日志，确认是否存在配置文件缺失等异常","evidence_type":"Pod 日志验证","target_scope":"aiops-e2e/rc-crashloop-config-file-missing-58cf574c9f-vhlrs","acceptable_tools":["kubectl_previous_logs"],"counts_for_completeness":true},{"id":"verify_pod_events","description":"验证 CrashLoopBackOffRuntime 异常 Pod 的关键事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crashloop-config-file-missing-58cf574c9f-vhlrs --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-crashloop-config-file-missing-58cf574c9f-vhlrs","sort_by":".lastTimestamp"},"purpose":"验证 Pod 关键事件，确认是否存在 BackOff、probe failed、Killing 等信号","evidence_type":"Pod 事件验证","target_scope":"aiops-e2e/rc-crashloop-config-file-missing-58cf574c9f-vhlrs","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                                                READY   STATUS             RESTARTS        AGE     IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-crashloop-config-file-missing-58cf574c9f-vhlrs   0/1     CrashLoopBackOff   5 (2m22s ago)   5m25s   172.16.166.155   node1   <none>           <none>            app=rc-crashloop-config-file-missing,pod-template-hash=58cf574c9f,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b9dfeff0728045e6/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b9dfeff0728045e6/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b9dfeff0728045e6/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 2\nsignals: 2\n关键日志:\nRUNTIME_STARTUP_ERROR: required config file missing\ncat: can't open '/etc/rootcause-app/config.yaml': No such file or directory","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b9dfeff0728045e6/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b9dfeff0728045e6/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b9dfeff0728045e6/tools/002-evidence-kubectl_previous_logs.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 3 项，实际采集 2 项，未采集 1 项，完整度 67%；其中真实环境证据 6/7 项，完整度 86%；实际执行工具 6 个，匹配计划 2 个，未规划证据 4 个","plan_total":3,"plan_collected":2,"plan_completeness":0.6666666666666666,"environment_evidence_total":7,"environment_evidence_collected":6,"environment_evidence_completeness":0.8571428571428571,"executed_tool_count":6,"matched_tool_count":2,"unplanned_tool_count":4,"evidence_inventory":[{"id":"verify_pod_crashloop_runtime","description":"验证 CrashLoopBackOffRuntime 异常 Pod 的 Last State、Exit Code、Reason 和重启次数","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e -o yaml","purpose":"验证 Pod 的 Last State、Exit Code、Reason 和重启次数","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"verify_pod_previous_logs","description":"验证 CrashLoopBackOffRuntime 异常 Pod 的崩溃前日志","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e --previous --tail=200","purpose":"验证崩溃前日志，确认是否存在配置文件缺失等异常","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"verify_pod_events","description":"验证 CrashLoopBackOffRuntime 异常 Pod 的关键事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crashloop-config-file-missing-58cf574c9f-vhlrs --sort-by='.lastTimestamp'","purpose":"验证 Pod 关键事件，确认是否存在 BackOff、probe failed、Killing 等信号","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":["verify_pod_events(验证 CrashLoopBackOffRuntime 异常 Pod 的关键事件): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/3 项, 完整度: 86%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | verify_pod_cr... | critical | ✅ | kubectl_get_by_name | 验证 CrashLoopBackOffRuntime 异常 Pod 的 Last Stat... | `kubectl get pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2...` |
   | verify_pod_pr... | critical | ✅ | kubectl_previous_logs | 验证 CrashLoopBackOffRuntime 异常 Pod 的崩溃前日志 | `kubectl logs rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e -...` |
   | verify_pod_ev... | important | ❌ | kubectl_events | 验证 CrashLoopBackOffRuntime 异常 Pod 的关键事件 | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crash...` |

   ⚠️ 未采集原因:
   - verify_pod_events(验证 CrashLoopBackOffRuntime 异常 Pod 的关键事件): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (13.8s)
   📤 → 下游数据: root_cause=Pod 'rc-crashloop-config-file-missing-58cf574c9f-vhlrs' 的容器启动失败，日志显示无法打开配置文件 '/etc/rootcause-app/config.yaml'，导致容器退出代码为 1，进入 CrashLoopBackOff 状态。
   confidence=90%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [], "causal_chain": {}, "root_cause": "Pod 'rc-crashloop-config-file-missing-58cf574c9f-vhlrs' 的容器启动失败，日志显示无法打开配置文件 '/etc/rootcause-app/config.yaml'，导致容器退出代码为 1，进入 CrashLoopBackOff 状态。", "root_cause_summary": "Pod 'rc-crashloop-config-file-missing-58cf574c9f-vhlrs' 的容器启动失败，日志显示无法打开配置文件 '/etc/rootcause-app/config.yaml'，导致容器退出代码为 1，进入 CrashLoopBackOff 状态。", "confidence": 0.9, "confidence_reason": "有直接证据表明容器因缺少配置文件而退出，因果链清晰。", "primary_runbooks": ["pod-crashloop-runtime.md"], "alternative_causes": [], "limitations": "未验证 Pod 的关键事件，可能遗漏其他潜在原因。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'rc-crashloop-config-file-missing-58cf574c9f-vhlrs' 的容器启动失败，日志显示无法打开配置文件 '/etc/rootcause-app/config.yaml'，导致容器退出代码为 1，进入 CrashLoopBackOff 状态。
   置信度: 90%

📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 21.2s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4408 字符

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
| **兼容归因层** | L2 |
| **问题分类** | CrashLoopBackOffRuntime（容器启动失败） |
| **置信度** | 高 (90%) |
| **证据完整度** | 2/3 (67%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | rc-crashloop-config-file-missing-58cf574c9f-vhlrs |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | RUNTIME_STARTUP_ERROR: required config file missing, cat: can't open '/etc/rootcause-app/config.yaml': No such file or directory |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff, RESTARTS: 3 (44s ago), REASON: Exit Code 1` | Pod 正处于 CrashLoopBackOff 状态，容器退出代码为 1 |
| 2 | 崩溃前日志 | `kubectl logs <pod> --previous` | `RUNTIME_STARTUP_ERROR: required config file missing`, `cat: can't open '/etc/rootcause-app/config.yaml': No such file or directory` | 容器启动失败，原因是缺少必需的配置文件 `/etc/rootcause-app/config.yaml` |
| 3 | Pod 配置 | `kubectl get pod -o yaml` | `image: busybox:1.36`, `restartPolicy: Always` | 使用了 busybox:1.36 镜像，容器退出后自动重启 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 CrashLoopBackOff，容器退出代码为 1，且崩溃前日志显示配置文件缺失 → **容器启动失败**
- **证据链**：配置文件缺失 → 容器启动失败（Exit Code 1） → 容器被终止 → Pod 进入 CrashLoopBackOff 并持续重启

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| Pod 事件 | important | 无法确认是否有其他异常事件触发容器崩溃，例如镜像拉取失败、卷挂载失败等 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 容器启动时缺少必需的配置文件 `/etc/rootcause-app/config.yaml`  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 配置文件缺失 → 容器启动失败（Exit Code 1）                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器启动失败（Exit Code 1）                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CrashLoopBackOff，容器持续重启                       │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Pod 状态为 CrashLoopBackOff, Exit Code 1) 和证据 #2 (崩溃前日志显示配置文件缺失)，问题的根本原因是**容器启动时缺少必需的配置文件 `/etc/rootcause-app/config.yaml`**，导致容器启动失败并进入 CrashLoopBackOff 状态。

**置信度**：高 (90%)
- ✅ Pod 状态和退出代码明确指向容器启动失败
- ✅ 崩溃前日志显示配置文件缺失
- ⚠️ 缺少 Pod 事件，无法确认是否有其他因素影响容器启动

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 提供缺失的配置文件**
```bash
kubectl create configmap config-map-rootcause-app \
  --from-file=/etc/rootcause-app/config.yaml \
  -n aiops-e2e
```
*依据*：容器启动失败原因是缺少配置文件，需通过 ConfigMap 提供该文件

**2. [优先] 更新 Pod 使用 ConfigMap**
```bash
kubectl patch deployment <deployment-name> -n aiops-e2e \
  -p '{"spec":{"template":{"spec":{"containers":[{"name":"app","volumeMounts":[{"name":"config","mountPath":"/etc/rootcause-app"}]}],"volumes":[{"name":"config","configMap":{"name":"config-map-rootcause-app"}}]}'
```
*依据*：容器需要挂载 ConfigMap 提供的配置文件

**3. [可选] 查看 Pod 事件**
```bash
kubectl describe pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e
```
*目的*：确认是否有其他异常事件触发容器崩溃（如镜像拉取失败等）

### 后续优化

1. **配置 ConfigMap 自动更新**：确保配置文件变更后能自动同步到容器
2. **配置健康检查**：添加 `livenessProbe` 和 `readinessProbe`，避免容器因启动失败导致服务不可用
3. **监控日志**：配置日志采集系统，实时监控容器启动失败日志

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 0 |
| 3. 检查配置文件是否挂载 | `kubectl exec -it rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e -- cat /etc/rootcause-app/config.yaml` | 显示配置文件内容 |

---

## ⚠️ 注意事项

- 如果问题仍然存在，请检查 ConfigMap 是否正确挂载，并确认配置文件内容是否正确
- 可以通过 `kubectl describe pod` 查看是否有其他事件导致容器启动失败
- 如果使用的是 Deployment，建议更新 Deployment 后使用 `kubectl rollout status` 确认更新成功

---

---

## 📊 性能统计

├─ 总耗时: 6.0m
├─ 问题定位: 94.5s (26%) ✅
├─ 证据链采集: 167.7s (47%) ✅
├─ 根因分析: 13.8s (4%) ✅
├─ 汇总总结: 81.2s (23%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 8 次
```

📋 诊断追踪

- **核心 Runbook**: pod-crashloop-runtime
- **参考 Runbook**: pod-crashloop-runtime
- **工具调用**: 8 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
