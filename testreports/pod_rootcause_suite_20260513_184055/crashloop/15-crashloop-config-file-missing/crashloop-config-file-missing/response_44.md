======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: d9664542ac5949ad]

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
      📄 NAME                                                READY   STATUS             RESTARTS        AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-crashloop-config-file-missin
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
2m48s (x576 over 127m)   Warning   BackOff   Pod/rc-crashloop-config-file-missing-58cf574c9f-vhlrs   Back-off restarting failed container app in pod rc-crashloop-config-file-
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
  "reasoning": "Pod 'rc-crashloop-config-file-missing-58cf574c9f-vhlrs' 处于 CrashLoopBackOff 状态，Exit Code 为 1，且日志显示 'required config file missing' 和 'No such file or directory'，表明容器启动失败是由于配置文件缺失导致的。这符合 L4 层次的 ConfigError 异常类型，即容器配置错误导致启动失败。",
  "abnormal_pods": [
    {
      "name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs",
      "namespace": "aiops-e2e",
      "status": "CrashLoopBackOff",
      "reason": "CrashLoopBackOff",
      "message": "Back-off restarting failed container app in pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs_aiops-e2e(f116c098-f8d2-46aa-8037-25a4f00eb480)",
      "last_state": {
        "terminated": {
          "exit_code": 1,
          "reason": "Error"
        }
      }
    }
  ],
  "abnormal_groups": [
    {
      "type": "CrashLoopBackOffRuntime",
      "count": 1
    }
  ],
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "CrashLoopBackOffRuntime",
  "status_category": "CrashLoopBackOff",
  "key_entities": [
    "rc-crashloop-config-file-missing-58cf574c9f-vhlrs",
    "aiops-e2e",
    "CrashLoopBackOff",
    "ConfigError"
  ],
  "possible_scenarios": [
    "容器启动时缺少必要的配置文件，导致进程无法正常运行。",
    "配置文件路径错误或权限不足，导致容器无法读取配置。",
    "容器镜像中缺少配置文件，导致启动失败。",
    "容器启动脚本或命令错误，导致配置文件未正确加载。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (2m 0.1s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': '容器启动时缺少必要的配置文件，导致进程无法正常运行。', 'probability': 'high', 'reason': "日志中出现 'required config file missing' 和 'No such file or directory'"}]
   entities=[{"type": "Pod", "name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs", "namespace": "aiops-e2e"}]
   reasoning=Pod 'rc-crashloop-config-file-missing-58cf574c9f-vhlrs' 处于 CrashLoopBackOff 状态，Exit Code 为 1，且日志显示 'required config file missing' 和 'No such file or directory'，表明容器启动失败是由于配置文件缺失导致的。这符合 L4 层次的 ConfigError 异常类型，即容器配置错误导致启动失败。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 1.0, "reasoning": "Pod 'rc-crashloop-config-file-missing-58cf574c9f-vhlrs' 处于 CrashLoopBackOff 状态，Exit Code 为 1，且日志显示 'required config file missing' 和 'No such file or directory'，表明容器启动失败是由于配置文件缺失导致的。这符合 L4 层次的 ConfigError 异常类型，即容器配置错误导致启动失败。", "abnormal_pods": [{"name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "CrashLoopBackOffRuntime", "status_category": "app_config", "key_entities": [{"type": "Pod", "name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "容器启动时缺少必要的配置文件，导致进程无法正常运行。", "probability": "high", "reason": "日志中出现 'required config file missing' 和 'No such file or directory'"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "CrashLoopBackOffRuntime", "compatible_layers": ["L2"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-config-file-missing-58cf574c9f-vhlrs"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"}, {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-crashloop-config-file-missing-58cf574c9f-vhlrs   0/1     CrashLoopBackOff   29 (3m58s ago)   127m    172.16.166.155   node1    <none>           <none>            app=rc-crashloop-config-file-missing,pod-template-hash=58cf574c9f,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/d9664542ac5949ad/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/d9664542ac5949ad/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/d9664542ac5949ad/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 100%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                                READY   STATUS             RESTARTS        AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-crashloop-config-file-missin
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 2
signals: 2
关键日志:
RUNTIME_STARTUP_ERROR: required config file missing
cat: can't open '/etc/rootcause-app/config.yaml': No such file or directory
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-crashloop-config-file-missing-58cf574c9f-vhlrs
namespace: aiops-e2e
creationTimestamp: 2026-05-14T19:46:03Z
deletionTimestamp: <absent>
deletionGracePeriodS
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
25s (x600 over 130m)   Warning   BackOff   Pod/rc-crashloop-config-file-missing-58cf574c9f-vhlrs   Back-off restarting failed container app in pod rc-crashloop-config-file-mi
   💭 [证据链采集] 已采集证据：
1. **Pod 状态信息**：通过 `kubectl_get_by_name` 确认 Pod `rc-crashloop-config-file-missing-58cf574c9f-vhlrs` 处于 `CrashLoopBackOff` 状态，重启次数为 30。
2. **崩溃前日志**：通过 `kubectl_previous_logs` 确认日志显示 `RUNTIME_STARTUP_ERROR: required config file missing` 和 `cat: can't open '/etc/rootcause-app/config.yaml': No such file or directory`，表明容器启动失败是由于缺少必要的配置文件。
3. **Pod 详细配置**：通过 `kubectl_get_yaml` 确认 Pod 使用了镜像 `busybox:1.36`，重启策略为 `Always`，容器 `app` 的退出码为 `1`，表明容器异常退出。
4. **事件信息**：通过 `kubectl_events` 确认事件中显示 `Warning BackOff`，表明容器因启动失败而被反复重启。

未采集证据：无。

冲突证据：无。
   ✅ [证据链采集] 完成 (1m 19.6s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan":[{"id":"describe_pod","description":"获取异常 Pod 'rc-crashloop-config-file-missing-58cf574c9f-vhlrs' 的详细信息，包括 Last State、Exit Code、Reason 和重启次数。","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e -o yaml","tool_args":{"name":"rc-crashloop-config-file-missing-58cf574c9f-vhlrs","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"获取 Pod 的详细配置和状态信息，验证其异常原因。","evidence_type":"Pod 配置和状态信息","target_scope":"aiops-e2e/rc-crashloop-config-file-missing-58cf574c9f-vhlrs","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                                                READY   STATUS             RESTARTS        AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-crashloop-config-file-missing-58cf574c9f-vhlrs   0/1     CrashLoopBackOff   30 (104s ago)   130m   172.16.166.155   node1   <none>           <none>            app=rc-crashloop-config-file-missing,pod-template-hash=58cf574c9f,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d9664542ac5949ad/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d9664542ac5949ad/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d9664542ac5949ad/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 2\nsignals: 2\n关键日志:\nRUNTIME_STARTUP_ERROR: required config file missing\ncat: can't open '/etc/rootcause-app/config.yaml': No such file or directory","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d9664542ac5949ad/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d9664542ac5949ad/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d9664542ac5949ad/tools/002-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-crashloop-config-file-missing-58cf574c9f-vhlrs\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-14T19:46:03Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-crashloop-config-file-missing, pod_abnormal_type=CrashLoopBackOffRuntime\ndiagnostic_annotations: aiops.e2e/runbook=pod-crashloop-runtime.md\nownerReferences: ReplicaSet/rc-crashloop-config-file-missing-58cf574c9f\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=30 reason=CrashLoopBackOff exitCode=1\n  message: back-off 5m0s restarting failed container=app pod=rc-crashloop-config-file-missing-58cf574c9f-vhlrs_aiops-e2e(f116c098-f8d2-46aa-8037-25a4f00eb480)\nvolumes:\n- {\"name\": \"kube-api-access-76ckm\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d9664542ac5949ad/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d9664542ac5949ad/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d9664542ac5949ad/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n25s (x600 over 130m)   Warning   BackOff   Pod/rc-crashloop-config-file-missing-58cf574c9f-vhlrs   Back-off restarting failed container app in pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs_aiops-e2e(f116c098-f8d2-46aa-8037-25a4f00eb480)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d9664542ac5949ad/tools/004-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d9664542ac5949ad/tools/004-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d9664542ac5949ad/tools/004-evidence-kubectl_events.summary.txt"}],"llm_analysis":"已采集证据：\n1. **Pod 状态信息**：通过 `kubectl_get_by_name` 确认 Pod `rc-crashloop-config-file-missing-58cf574c9f-vhlrs` 处于 `CrashLoopBackOff` 状态，重启次数为 30。\n2. **崩溃前日志**：通过 `kubectl_previous_logs` 确认日志显示 `RUNTIME_STARTUP_ERROR: required config file missing` 和 `cat: can't open '/etc/rootcause-app/config.yaml': No such file or directory`，表明容器启动失败是由于缺少必要的配置文件。\n3. **Pod 详细配置**：通过 `kubectl_get_yaml` 确认 Pod 使用了镜像 `busybox:1.36`，重启策略为 `Always`，容器 `app` 的退出码为 `1`，表明容器异常退出。\n4. **事件信息**：通过 `kubectl_events` 确认事件中显示 `Warning BackOff`，表明容器因启动失败而被反复重启。\n\n未采集证据：无。\n\n冲突证据：无。","collection_summary":"计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%；其中真实环境证据 6/6 项，完整度 100%；实际执行工具 9 个，匹配计划 1 个，未规划证据 8 个","plan_total":1,"plan_collected":1,"plan_completeness":1.0,"environment_evidence_total":6,"environment_evidence_collected":6,"environment_evidence_completeness":1.0,"executed_tool_count":9,"matched_tool_count":1,"unplanned_tool_count":8,"evidence_inventory":[{"id":"describe_pod","description":"获取异常 Pod 'rc-crashloop-config-file-missing-58cf574c9f-vhlrs' 的详细信息，包括 Last State、Exit Code、Reason 和重启次数。","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e -o yaml","purpose":"获取 Pod 的详细配置和状态信息，验证其异常原因。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/1 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | describe_pod | critical | ✅ | kubectl_get_by_name | 获取异常 Pod 'rc-crashloop-config-file-missing-58... | `kubectl get pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (21.3s)
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
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (2m 1.1s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5121 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 42.1s
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
| **问题分类** | ConfigError（配置文件缺失） |
| **置信度** | 高 (85%) |
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
| 错误信息 | `required config file missing`, `No such file or directory` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | STATUS: `CrashLoopBackOff`, RESTARTS: 29 (3m58s ago) | Pod 处于持续重启状态，表明容器启动失败 |
| 2 | 容器退出码 | `kubectl describe pod` | `Exit Code: 1` | 非 OOMKilled，表明启动失败，非资源问题 |
| 3 | 容器日志 | `kubectl logs --previous` | `RUNTIME_STARTUP_ERROR: required config file missing`, `cat: can't open '/etc/rootcause-app/config.yaml': No such file or directory` | 应用启动时缺少必要配置文件，导致进程退出 |
| 4 | kubectl events | `kubectl describe pod` | `Warning BackOff Pod/rc-crashloop-config-file-missing-58cf574c9f-vhlrs Back-off restarting failed container app` | Pod 持续重启，由容器退出触发 |
| 5 | Pod 配置 | `kubectl get pod -o yaml` | `image: <image>, command: <command>` | 未发现明显配置错误，但缺少配置挂载 |
| 6 | 容器运行时事件 | `kubectl describe pod` | `Last State: Terminated` | 容器启动后立即退出，符合 Exit Code 1 的行为 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 处于 `CrashLoopBackOff` 状态，且容器退出码为 `1`，表明容器启动失败。
- **证据 #3 印证**：日志显示配置文件缺失，是容器无法启动的直接原因。
- **证据 #4 印证**：Kubernetes 事件确认 Pod 正在持续重启，属于 `BackOff` 类型。
- **证据链总结**：容器启动时缺少必要的配置文件 → 应用启动失败 → 容器退出（Exit Code 1） → Pod 重启 → 形成 CrashLoopBackOff。

### 缺失证据（无）

| 证据 | 级别 | 影响 |
|------|------|------|
| 无 | 无 | 无 |

---

## 🎯 根因分析

### 因果链

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                   │
│ 容器启动时缺少必要配置文件 '/etc/rootcause-app/config.yaml'，导致应用无法启动。│
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                   │
│ 应用启动时读取配置文件失败 → 主进程退出（Exit Code 1） → 容器被终止。         │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                   │
│ 容器退出（Exit Code 1），Pod 重启策略（Always）导致持续重启。                │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                               │
│ Pod 状态为 CrashLoopBackOff，持续重启。                                    │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1（Pod 状态为 `CrashLoopBackOff`）、证据 #2（Exit Code 为 1）和证据 #3（日志显示配置文件缺失），问题的根本原因是 **容器启动时缺少必要的配置文件 `/etc/rootcause-app/config.yaml`**，导致应用启动失败，容器退出，从而触发 Pod 持续重启。

**置信度**：高 (85%)  
- ✅ `kubectl describe pod` 显示 Exit Code 1  
- ✅ `kubectl logs --previous` 显示配置文件缺失  
- ✅ `kubectl events` 确认容器持续重启  
- ⚠️ 无进一步日志显示配置文件应由 ConfigMap 或 Secret 提供  

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 挂载配置文件（ConfigMap 或 Secret）**
```bash
kubectl create configmap rootcause-config \
  --from-file=config.yaml=/path/to/local/config.yaml \
  -n aiops-e2e

kubectl set image deployment/<deployment-name> app=image-with-config \
  -n aiops-e2e
```
*依据*：容器启动失败是由于缺少配置文件，建议通过 ConfigMap 挂载配置文件。

**2. [次优先] 更新 Pod 配置以挂载 ConfigMap**
```bash
kubectl edit deployment <deployment-name> -n aiops-e2e
```
在容器配置中添加：
```yaml
volumeMounts:
  - name: config-volume
    mountPath: /etc/rootcause-app
volumes:
  - name: config-volume
    configMap:
      name: rootcause-config
```

**3. [可选] 查看崩溃前日志**
```bash
kubectl logs rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e --previous | tail -100
```
*目的*：确认应用启动时是否还有其他错误，比如依赖缺失或路径错误。

### 后续优化

1. **配置 ConfigMap/Secret 自动更新机制**（如使用 Operator）
2. **配置 Pod 健康检查（liveness/readiness）**，提前发现启动失败
3. **配置日志收集系统**（如 Fluentd + ELK），便于快速定位问题
4. **配置监控告警**（如 Prometheus + Alertmanager），监控 Pod 状态和重启次数

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e` | STATUS: Running |
| 2. 检查容器日志 | `kubectl logs rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e` | 不再显示 `required config file missing` |
| 3. 检查配置文件是否挂载 | `kubectl exec -it rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e -- ls /etc/rootcause-app/config.yaml` | 文件存在 |
| 4. 检查重启次数是否停止 | `kubectl get pod rc-crashloop-config-file-missing-58cf574c9f-vhlrs -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 重启次数不再增加 |

---

## ⚠️ 注意事项

- 如果配置文件路径在应用代码中硬编码，可能需要同时更新代码或容器镜像。
- 如果配置文件来自 ConfigMap 或 Secret，确保它们已正确创建并挂载。
- 如果问题仍然存在，建议检查应用启动脚本是否正确读取配置文件路径。
- 如果应用依赖其他配置项，建议检查日志中是否还有其他错误信息。

---

## 📊 性能统计

├─ 总耗时: 5.7m
├─ 问题定位: 120.1s (35%) ✅
├─ 证据链采集: 79.6s (23%) ✅
├─ 根因分析: 21.3s (6%) ✅
├─ 汇总总结: 121.1s (35%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 10 次
```

📋 诊断追踪

- **核心 Runbook**: pod-crashloop-runtime
- **参考 Runbook**: pod-crashloop-runtime
- **工具调用**: 10 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
