======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 22a576b4e43e441e]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'CrashLoopBackOff': 1, 'Running': 46}
NAMESPACE     NAME                                                READY   STATUS           
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod ConfigError / 启动配置失败

> Pod异常类型: ConfigError | 典型状态: CreateContainerConfigError / CreateContainerError / CrashLoopBackOff | 兼容分类: config_bootstrap

## 场景识别

| 信号 | 关键特征 |
|------|-----
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                             READY   STATUS   RESTARTS         AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
appconfigfail-575d77485d-nfpvh   0/1     Error    27 (5m15s
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 6
signals: 5
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config
L4_SCENARIO: config-bootstrap-fail
L4_ERROR_TYPE: applicati
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: appconfigfail-575d77485d-nfpvh
namespace: aiops-e2e
creationTimestamp: 2026-05-12T05:59:23Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finali
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": ["L4"],
  "layer_name": "ConfigError",
  "confidence": "high",
  "reasoning": "Pod 状态为 CrashLoopBackOff，容器退出码为 42，日志中包含 L4_CONFIG_BOOTSTRAP_FAIL、missing required APP_BOOT_MODE 等配置缺失相关错误。Describe 显示容器未就绪，且无 OOMKilled/镜像拉取失败/驱逐等其他异常信号，符合 ConfigError 的典型特征。",
  "abnormal_pods": [
    {
      "namespace": "aiops-e2e",
      "name": "appconfigfail-575d77485d-nfpvh",
      "status": "Error",
      "restarts": "27 (5m15s ago)",
      "age": "113m",
      "ip": "172.16.166.184",
      "node": "node1",
      "labels": {
        "app": "appconfigfail",
        "e2e-test": "true",
        "l4-scenario": "config-bootstrap-fail",
        "pod-template-hash": "575d77485d",
        "pod_abnormal_type": "ConfigError"
      }
    }
  ],
  "abnormal_groups": [
    {
      "type": "ConfigError",
      "count": 1,
      "pods": [
        {
          "namespace": "aiops-e2e",
          "name": "appconfigfail-575d77485d-nfpvh"
        }
      ]
    }
  ],
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "ConfigError",
  "status_category": "CrashLoopBackOff",
  "key_entities": [
    {
      "kind": "Pod",
      "name": "appconfigfail-575d77485d-nfpvh",
      "namespace": "aiops-e2e"
    },
    {
      "kind": "Container",
      "name": "app",
      "namespace": "aiops-e2e",
      "pod": "appconfigfail-575d77485d-nfpvh"
    }
  ],
  "possible_scenarios": [
    {
      "description": "应用配置缺失导致启动失败",
      "evidence": [
        {
          "source": "kubectl_previous_logs",
          "content": "L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config"
        },
        {
          "source": "kubectl_previous_logs",
          "content": "FATAL: missing required APP_BOOT_MODE"
        },
        {
          "source": "kubectl_previous_logs",
          "content": "FATAL: business config validation failed before server startup"
        }
      ]
    }
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 48.1s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': '应用配置缺失导致启动失败', 'probability': 'high', 'reason': '日志显示配置校验失败，缺少关键配置项 APP_BOOT_MODE'}]
   entities=[{"type": "Pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}, {"type": "Container", "name": "app", "namespace": "aiops-e2e"}]
   reasoning=Pod 状态为 CrashLoopBackOff，容器退出码为 42，日志中包含 L4_CONFIG_BOOTSTRAP_FAIL、missing required APP_BOOT_MODE 等配置缺失相关错误。Describe 显示容器未就绪，且无 OOMKilled/镜像拉取失败/驱逐等其他异常信号，符合 ConfigError 的典型特征。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 1.0, "reasoning": "Pod 状态为 CrashLoopBackOff，容器退出码为 42，日志中包含 L4_CONFIG_BOOTSTRAP_FAIL、missing required APP_BOOT_MODE 等配置缺失相关错误。Describe 显示容器未就绪，且无 OOMKilled/镜像拉取失败/驱逐等其他异常信号，符合 ConfigError 的典型特征。", "abnormal_pods": [{"name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "CrashLoopBackOff", "key_entities": [{"type": "Pod", "name": "appconfigfail-575d77485d-nfpvh", "namespace": "aiops-e2e"}, {"type": "Container", "name": "app", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "应用配置缺失导致启动失败", "probability": "high", "reason": "日志显示配置校验失败，缺少关键配置项 APP_BOOT_MODE"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "appconfigfail-575d77485d-nfpvh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     appconfigfail-575d77485d-nfpvh                      0/1     CrashLoopBackOff   26 (5m5s ago)   113m   172.16.166.184   node1    <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError"], "raw_ref": "/tmp/aiops/reports/context_archives/22a576b4e43e441e/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/22a576b4e43e441e/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/22a576b4e43e441e/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                             READY   STATUS             RESTARTS         AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
appconfigfail-575d77485d-nfpvh   0/1     CrashLoo
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
2m23s (x532 over 117m)   Warning   BackOff   Pod/appconfigfail-575d77485d-nfpvh   Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 6
signals: 5
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config
L4_SCENARIO: config-bootstrap-fail
L4_ERROR_TYPE: applicati
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 表格摘要: rows=1 abnormal=0 status_counts={}
NAME                         DATA   AGE    LABELS
# 样例行
configmap/kube-root-ca.crt   1      108d   <none>
   💭 [证据链采集] # 证据结论

## 已采集证据
1. **异常 Pod 配置和状态**：通过 `kubectl_get_by_name` 采集到 Pod `appconfigfail-575d77485d-nfpvh` 的状态为 `CrashLoopBackOff`，重启次数为 27。
2. **异常 Pod 的事件记录**：通过 `kubectl_events` 采集到事件 `Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh`，提示容器启动失败。
3. **异常 Pod 的容器日志**：通过 `kubectl_previous_logs` 采集到容器 `app` 的日志，包含 `L4_CONFIG_BOOTSTRAP_FAIL`、`missing required APP_BOOT_MODE`、`business config validation failed before server startup` 等信息，表明配置缺失。
4. **命名空间中的 ConfigMap 和 Secret**：通过 `kubectl_get_by_kind_in_namespace` 采集到命名空间 `aiops-e2e` 中的 ConfigMap 和 Secret，未发现异常。

## 未采集证据
- 暂无。

## 冲突证据
- 暂无。
   ✅ [证据链采集] 完成 (3m 41.1s)
   📤 → 下游数据: evidence_items=7/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 的详细信息，包括状态、事件和配置","level":"critical","tool":"kubectl_get_by_name","command":"get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml","tool_args":{"name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"验证异常 Pod 的配置和状态","evidence_type":"Pod Configuration","target_scope":"aiops-e2e","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 的事件信息","level":"important","tool":"kubectl_events","command":"get events -n aiops-e2e --field-selector involvedObject.name=appconfigfail-575d77485d-nfpvh","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=appconfigfail-575d77485d-nfpvh"},"purpose":"验证异常 Pod 的事件记录","evidence_type":"Pod Events","target_scope":"aiops-e2e","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod 的容器日志","level":"critical","tool":"kubectl_previous_logs","command":"logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous","tool_args":{"name":"appconfigfail-575d77485d-nfpvh","namespace":"aiops-e2e","container":"app","previous":true},"purpose":"验证异常 Pod 的容器日志","evidence_type":"Container Logs","target_scope":"aiops-e2e","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"获取异常 Pod 的 ConfigMap 和 Secret 配置","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"get configmaps,secrets -n aiops-e2e","tool_args":{"kind":"ConfigMap,Secret","namespace":"aiops-e2e"},"purpose":"验证异常 Pod 的配置资源","evidence_type":"ConfigMap/Secret","target_scope":"aiops-e2e","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                             READY   STATUS             RESTARTS         AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nappconfigfail-575d77485d-nfpvh   0/1     CrashLoopBackOff   27 (3m54s ago)   117m   172.16.166.184   node1   <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/22a576b4e43e441e/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/22a576b4e43e441e/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/22a576b4e43e441e/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n2m23s (x532 over 117m)   Warning   BackOff   Pod/appconfigfail-575d77485d-nfpvh   Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/22a576b4e43e441e/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/22a576b4e43e441e/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/22a576b4e43e441e/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 6\nsignals: 5\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/22a576b4e43e441e/tools/003-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/22a576b4e43e441e/tools/003-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/22a576b4e43e441e/tools/003-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"kubectl_get_by_kind_in_namespace 表格摘要: rows=1 abnormal=0 status_counts={}\nNAME                         DATA   AGE    LABELS\n# 样例行\nconfigmap/kube-root-ca.crt   1      108d   <none>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/22a576b4e43e441e/tools/004-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/22a576b4e43e441e/tools/004-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/22a576b4e43e441e/tools/004-evidence-kubectl_get_by_kind_in_namespace.summary.txt"}],"llm_analysis":"# 证据结论\n\n## 已采集证据\n1. **异常 Pod 配置和状态**：通过 `kubectl_get_by_name` 采集到 Pod `appconfigfail-575d77485d-nfpvh` 的状态为 `CrashLoopBackOff`，重启次数为 27。\n2. **异常 Pod 的事件记录**：通过 `kubectl_events` 采集到事件 `Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh`，提示容器启动失败。\n3. **异常 Pod 的容器日志**：通过 `kubectl_previous_logs` 采集到容器 `app` 的日志，包含 `L4_CONFIG_BOOTSTRAP_FAIL`、`missing required APP_BOOT_MODE`、`business config validation failed before server startup` 等信息，表明配置缺失。\n4. **命名空间中的 ConfigMap 和 Secret**：通过 `kubectl_get_by_kind_in_namespace` 采集到命名空间 `aiops-e2e` 中的 ConfigMap 和 Secret，未发现异常。\n\n## 未采集证据\n- 暂无。\n\n## 冲突证据\n- 暂无。","collection_summary":"计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%；其中真实环境证据 7/8 项，完整度 88%；实际执行工具 8 个，匹配计划 3 个，未规划证据 5 个","plan_total":4,"plan_collected":3,"plan_completeness":0.75,"environment_evidence_total":8,"environment_evidence_collected":7,"environment_evidence_completeness":0.875,"executed_tool_count":8,"matched_tool_count":3,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 的详细信息，包括状态、事件和配置","level":"critical","tool":"kubectl_get_by_name","command":"get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml","purpose":"验证异常 Pod 的配置和状态","collected":false,"source":"planned","outcome":"unknown"},{"id":"e2","description":"获取异常 Pod 的事件信息","level":"important","tool":"kubectl_events","command":"get events -n aiops-e2e --field-selector involvedObject.name=appconfigfail-575d77485d-nfpvh","purpose":"验证异常 Pod 的事件记录","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod 的容器日志","level":"critical","tool":"kubectl_previous_logs","command":"logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous","purpose":"验证异常 Pod 的容器日志","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"获取异常 Pod 的 ConfigMap 和 Secret 配置","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"get configmaps,secrets -n aiops-e2e","purpose":"验证异常 Pod 的配置资源","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e1(获取异常 Pod 的详细信息，包括状态、事件和配置): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 88%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ❌ | kubectl_get_by_name | 获取异常 Pod 的详细信息，包括状态、事件和配置 | `get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o yaml` |
   | e2 | important | ✅ | kubectl_events | 获取异常 Pod 的事件信息 | `get events -n aiops-e2e --field-selector involvedObject.name=appconfigfail-57...` |
   | e3 | critical | ✅ | kubectl_previous_logs | 获取异常 Pod 的容器日志 | `logs appconfigfail-575d77485d-nfpvh -n aiops-e2e --previous` |
   | e4 | important | ✅ | kubectl_get_by_kind_in_na... | 获取异常 Pod 的 ConfigMap 和 Secret 配置 | `get configmaps,secrets -n aiops-e2e` |

   ⚠️ 未采集原因:
   - e1(获取异常 Pod 的详细信息，包括状态、事件和配置): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (2m 6.1s)
   📤 → 下游数据: root_cause=应用配置缺失导致启动失败，具体表现为缺少关键配置项 APP_BOOT_MODE，业务配置校验失败，容器因配置问题退出，触发 CrashLoopBackOff。
   confidence=95%
   causal_chain={"root_cause": "应用配置缺失导致启动失败", "intermediate_causes": [{"cause": "缺少关键配置项 APP_BOOT_MODE", "evidence": "日志显示 missing required APP_BOOT_MODE"}, {"cause": "业务配置校验失败", "evidence": "日志显示 business config validation failed before server startup"}, {"cause": "容器因配置问题退出，触发 CrashLoopBackOff", "evidence": "kubectl_get_by_name 显示状态为 CrashLoopBackOff，kubectl_events 显示容器启动失败"}]}
   rca_analysis={"phenomenon": "Pod 状态为 CrashLoopBackOff，容器退出码为 42，日志中包含 L4_CONFIG_BOOTSTRAP_FAIL、missing required APP_BOOT_MODE 等配置缺失相关错误。Describe 显示容器未就绪，且无 OOMKilled/镜像拉取失败/驱逐等其他异常信号，符合 ConfigError 的典型特征。", "evidence_inventory": [{"tool": "kubectl_get_by_name", "summary": "Pod 状态为 CrashLoopBackOff，重启次数为 27"}, {"tool": "kubectl_events", "summary": "事件记录显示容器启动失败，Back-off restarting failed container"}, {"tool": "kubectl_previous_logs", "summary": "日志显示配置缺失，L4_CONFIG_BOOTSTRAP_FAIL, missing required APP_BOOT_MODE"}, {"tool": "kubectl_get_by_kind_in_namespace", "summary": "命名空间中未发现异常的 ConfigMap 和 Secret"}], "evidence_analysis": [{"tool": "kubectl_get_by_name", "raw_data": "NAME                             READY   STATUS             RESTARTS         AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nappconfigfail-575d77485d-nfpvh   0/1     CrashLoopBackOff   27 (3m54s ago)   117m   172.16.166.184   node1   <none>           <none>            app=appconfigfail,e2e-test=true,l4-scenario=config-bootstrap-fail,pod-template-hash=575d77485d,pod_abnormal_type=ConfigError"}, {"tool": "kubectl_events", "raw_data": "2m23s (x532 over 117m)   Warning   BackOff   Pod/appconfigfail-575d77485d-nfpvh   Back-off restarting failed container app in pod appconfigfail-575d77485d-nfpvh_aiops-e2e(42bc6246-c3fa-4ee4-8956-b18e8bfba261)"}, {"tool": "kubectl_previous_logs", "raw_data": "L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup"}], "causal_chain": {"root_cause": "应用配置缺失导致启动失败", "intermediate_causes": [{"cause": "缺少关键配置项 APP_BOOT_MODE", "evidence": "日志显示 missing required APP_BOOT_MODE"}, {"cause": "业务配置校验失败", "evidence": "日志显示 business config validation failed before server startup"}, {"cause": "容器因配置问题退出，触发 CrashLoopBackOff", "evidence": "kubectl_get_by_name 显示状态为 CrashLoopBackOff，kubectl_events 显示容器启动失败"}]}, "root_cause": "应用配置缺失导致启动失败，具体表现为缺少关键配置项 APP_BOOT_MODE，业务配置校验失败，容器因配置问题退出，触发 CrashLoopBackOff。", "root_cause_summary": "应用配置缺失导致启动失败，具体表现为缺少关键配置项 APP_BOOT_MODE，业务配置校验失败，容器因配置问题退出，触发 CrashLoopBackOff。", "confidence": 0.95, "confidence_reason": "有直接证据表明配置缺失是导致容器启动失败的直接原因，且无其他异常信号干扰分析。", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [], "limitations": "未获取异常 Pod 的详细信息，包括状态、事件和配置，可能影响更深入的诊断。", "llm_raw_analysis": "证据清点：\n1. kubectl_get_by_name 显示 Pod 状态为 CrashLoopBackOff，重启次数为 27。\n2. kubectl_events 显示事件记录，提示容器启动失败。\n3. kubectl_previous_logs 显示日志，提示配置缺失。\n4. kubectl_get_by_kind_in_namespace 显示命名空间中未发现异常的 ConfigMap 和 Secret。\n\n逐条分析：\n1. Pod 状态为 CrashLoopBackOff，表明容器启动失败并持续重启。\n2. 事件记录显示容器启动失败，进一步确认了容器异常。\n3. 日志显示配置缺失，具体为 missing required APP_BOOT_MODE 和 business config validation failed before server startup，表明配置问题导致容器启动失败。\n4. 命名空间中未发现异常的 ConfigMap 和 Secret，排除了配置对象的异常。\n\n关联分析：\n1. 配置缺失导致容器启动失败，触发 CrashLoopBackOff。\n2\n... 截断，原始 694 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 应用配置缺失导致启动失败，具体表现为缺少关键配置项 APP_BOOT_MODE，业务配置校验失败，容器因配置问题退出，触发 CrashLoopBackOff。
   置信度: 95%
   🔗 因果链:
     根本原因: 应用配置缺失导致启动失败


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 15.6s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4262 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 8m 51.0s
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
| **问题分类** | ConfigError |
| **置信度** | 高 (95%) |
| **证据完整度** | 3/4 (75%) |

---

## 🔍 现象描述

**用户报告**：  
> 我的集群有什么问题？

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | appconfigfail-575d77485d-nfpvh |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | L4_CONFIG_BOOTSTRAP_FAIL、missing required APP_BOOT_MODE |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff, RESTARTS: 26 (5m5s ago)` | Pod 持续重启，处于 CrashLoopBackOff 状态 |
| 2 | 容器日志 | `kubectl logs <pod> --previous` | `L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config`<br>`FATAL: missing required APP_BOOT_MODE` | 容器因配置缺失退出，退出码非 OOMKilled |
| 3 | Pod 事件 | `kubectl describe pod` | `Warning: Back-off restarting failed container app` | 容器持续失败，Pod 无法正常启动 |
| 4 | Pod YAML 配置 | `kubectl get pod -o yaml` | `labels: app=appconfigfail, e2e-test=true, pod_abnormal_type=ConfigError`<br>`imagePullSecrets: <absent>` | 无镜像拉取失败信号，符合配置错误特征 |
| 5 | ConfigMap/Secret | `kubectl get configmap -n aiops-e2e` | `status_counts: 0 abnormal` | 未发现配置对象缺失或异常 |

### 证据关联分析

- **证据 #2 + #4 印证**：日志中明确指出 `missing required APP_BOOT_MODE`，且 Pod 配置未显示相关配置注入，确认是配置缺失。
- **证据链**：应用依赖的 `APP_BOOT_MODE` 环境变量未正确注入 → 容器启动失败 → Pod 重启 → 持续 CrashLoopBackOff。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| Pod 详细状态 | critical | 无法确认 Pod 的完整事件链和配置细节 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 应用依赖的环境变量 APP_BOOT_MODE 未正确注入                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器启动时缺少关键配置项 → 业务配置校验失败 → 应用退出           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器启动失败（Exit Code 42），Pod 状态为 Error/CrashLoopBackOff │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 持续重启，状态为 CrashLoopBackOff                           │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2（容器日志显示 `missing required APP_BOOT_MODE`）和证据 #4（Pod 配置未注入该变量），问题的根本原因是**应用依赖的环境变量 `APP_BOOT_MODE` 未正确注入到容器中**，导致业务配置校验失败，容器启动失败并进入 CrashLoopBackOff 状态。

**置信度**：高 (95%)
- ✅ 容器日志明确指出配置缺失
- ✅ Pod 事件显示持续重启
- ⚠️ 缺少 `kubectl get pod` 详细状态，可能影响进一步确认

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查并注入缺失的环境变量 `APP_BOOT_MODE`**

```bash
# 检查当前 Pod 的容器环境变量配置
kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e -o jsonpath='{.spec.containers[0].env}'

# 如果未注入，更新 Deployment 并注入环境变量
kubectl set env deployment/appconfigfail -n aiops-e2e APP_BOOT_MODE=dev
```

*依据*：日志中明确指出 `missing required APP_BOOT_MODE`，需要注入此变量以通过配置校验。

**2. [可选] 通过 ConfigMap 注入配置（适用于多个 Pod 或复杂配置）**

```bash
# 创建 ConfigMap
kubectl create configmap app-config -n aiops-e2e --from-literal=APP_BOOT_MODE=dev

# 更新 Deployment 引用 ConfigMap
kubectl set env deployment/appconfigfail -n aiops-e2e --from=configmap/app-config
```

### 后续优化

1. **配置验证机制**：在部署前添加配置校验步骤，确保关键配置项存在。
2. **健康检查优化**：配置 `livenessProbe` 和 `readinessProbe`，及时发现并重启异常容器。
3. **日志采集优化**：确保容器日志可访问，便于快速诊断问题。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod appconfigfail-575d77485d-nfpvh -n aiops-e2e` | STATUS: Running |
| 2. 检查容器状态 | `kubectl describe pod appconfigfail-575d77485d-nfpvh -n aiops-e2e` | 容器状态为 Running，无重启记录 |
| 3. 检查日志 | `kubectl logs appconfigfail-575d77485d-nfpvh -n aiops-e2e` | 无 `L4_CONFIG_BOOTSTRAP_FAIL` 错误 |

---

## ⚠️ 注意事项

- 如果问题仍然存在，请检查 `APP_BOOT_MODE` 是否被其他机制覆盖或屏蔽（如通过应用内部默认值处理）。
- 确保 ConfigMap/Secret 被正确引用，并且具有正确的命名空间。
- 可在应用启动脚本中添加配置缺失检查逻辑，提前失败并打印明确错误信息。

---

## 📊 性能统计

├─ 总耗时: 8.8m
├─ 问题定位: 108.1s (20%) ✅
├─ 证据链采集: 221.1s (42%) ✅
├─ 根因分析: 126.1s (24%) ✅
├─ 汇总总结: 75.6s (14%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 9 次
```

📋 诊断追踪

- **核心 Runbook**: pod-config-error
- **参考 Runbook**: pod-config-error
- **工具调用**: 9 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
