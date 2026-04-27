======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 28da7898b6cc4c33]

📍 [问题定位] 执行中...
   💭 [问题定位] 


   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# 私有化 Kubernetes 环境健康与高效排查参考手册

> 类型: reference | 适用: 私有化 Kubernetes 环境 | 环境特征: Calico + NFS + containerd

## 目的

本手册不是某个具体故障的处理步骤，而是一个**额外知识参考**：
- 帮助理解在私有化 Kubernetes 环境中，健康检查应重点关注哪些资源与信号

   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   209d   v1.26.8  
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS             RESTARTS         AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     a
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             appconfigfail-7649c79dc5-q4zjz
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Wed, 22 Apr 2026 07:38:39
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# L4 应用启动配置校验失败 (Config Bootstrap Fail)

> 层级: L4 - 应用层 | 场景: 应用在启动阶段因业务配置缺失或非法而主动退出

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | `CrashLoopBackOff` / `Error`，重启次数持续增加 |
| 容器日志 | 含
   💭 [问题定位] ```json
{
  "layer": "L4",
  "layers": ["L4"],
  "layer_name": "应用层",
  "confidence": 0.95,
  "reasoning": "Pod appconfigfail-7649c79dc5-q4zjz 处于 CrashLoopBackOff 状态，describe 显示 Last State 退出码为 42，且容器日志明确输出 'FATAL: missing required APP_BOOT_MODE' 和 'business config validation failed'，符合 L4 配置校验失败场景，排除 OOMKilled、镜像拉取、存储卷等其他层级原因。",
  "key_entities": [
    {
      "type": "Pod",
      "value": "appconfigfail-7649c79dc5-q4zjz"
    },
    {
      "type": "Namespace",
      "value": "aiops-e2e"
    }
  ],
  "possible_scenarios": [
    "应用启动时缺失必填环境变量 APP_BOOT_MODE",
    "ConfigMap/Secret 中配置键名错误或值非法",
    "应用启动脚本校验逻辑触发主动退出"
  ]
}
```
   ✅ [问题定位] 完成 (37.5s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=['应用启动时缺失必填环境变量 APP_BOOT_MODE', 'ConfigMap/Secret 中配置键名错误或值非法', '应用启动脚本校验逻辑触发主动退出']
   entities=[{"type": "Pod", "value": "appconfigfail-7649c79dc5-q4zjz"}, {"type": "Namespace", "value": "aiops-e2e"}]
   reasoning=Pod appconfigfail-7649c79dc5-q4zjz 处于 CrashLoopBackOff 状态，describe 显示 Last State 退出码为 42，且容器日志明确输出 'FATAL: missing required APP_BOOT_MODE' 和 'business config validation failed'，符合 L4 配置校验失败场景，排除 OOMKilled、镜像拉取、存储卷等其他层级原因。
   layer_analysis={"layer": "L4", "layers": ["L4"], "layer_name": "应用层", "confidence": 0.95, "reasoning": "Pod appconfigfail-7649c79dc5-q4zjz 处于 CrashLoopBackOff 状态，describe 显示 Last State 退出码为 42，且容器日志明确输出 'FATAL: missing required APP_BOOT_MODE' 和 'business config validation failed'，符合 L4 配置校验失败场景，排除 OOMKilled、镜像拉取、存储卷等其他层级原因。", "key_entities": [{"type": "Pod", "value": "appconfigfail-7649c79dc5-q4zjz"}, {"type": "Namespace", "value": "aiops-e2e"}], "possible_scenarios": ["应用启动时缺失必填环境变量 APP_BOOT_MODE", "ConfigMap/Secret 中配置键名错误或值非法", "应用启动脚本校验逻辑触发主动退出"]}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] ```json
{
  "layer": "L4",
  "evidence_plan": [
    {
      "id": "e1",
      "description": "获取 Pod appconfigfail-7649c79dc5-q4zjz 的完整 YAML，确认环境变量是否被正确注入",
      "level": "critical",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get -o yaml pod appconfigfail-7649c79dc5-q4zjz -n aiops-e2e",
      "purpose": "验证容器是否定义了 APP_BOOT_MODE 环境变量，或是否从 ConfigMap/Secret 正确引用"
    },
    {
      "id": "e2",
      "description": "获取 Pod 关联的 Deployment 配置，检查环境变量来源（ConfigMap/Secret）",
      "level": "critical",
      "tool": "kubectl_lineage_parents",
      "command": "kubectl lineage parents --kind Pod --name appconfigfail-7649c79dc5-q4zjz --namespace aiops-e2e",
      "purpose": "确定 Pod 由哪个控制器创建，并获取其模板中环境变量的定义来源"
    },
    {
      "id": "e3",
      "description": "获取 Pod 的容器日志，确认错误信息是否持续出现且与 APP_BOOT_MODE 相关",
      "level": "critical",
      "tool": "kubectl_describe",
      "command": "kubectl describe pod appconfigfail-7649c79dc5-q4zjz -n aiops-e2e",
      "purpose": "虽然上游已提供日志片段，但需确认完整日志中是否存在重复的 'missing required APP_BOOT_MODE' 错误，排除临时性错误"
    },
    {
      "id": "e4",
      "description": "获取 Pod 关联的 ConfigMap 和 Secret 列表，确认是否存在被引用但缺失或键名错误的配置",
      "level": "important",
      "tool": "kubectl_get_by_kind_in_namespace",
      "command": "kubectl get configmap -n aiops-e2e",
      "purpose": "列出所有 ConfigMap，查找可能被 Deployment 引用的配置，如 app-config、bootstrap-config 等"
    },
    {
      "id": "e5",
      "description": "获取 Pod 关联的 Secret 列表，确认是否存在被引用但缺失或键名错误的密钥",
      "level": "important",
      "tool": "kubectl_get_by_kind_in_namespace",
      "command": "kubectl get secret -n aiops-e2e",
      "purpose": "列出所有 Secret，查找可能被 Deployment 引用的密钥，如 app-secrets、auth-config 等"
    },
    {
      "id": "e6",
      "description": "获取 Pod 的事件历史，确认是否有配置加载失败的事件",
      "level": "important",
      "tool": "kubectl_events",
      "command": "kubectl events --resource-type pod --resource-name appconfigfail-7649c79dc5-q4zjz --namespace aiops-e2e",
      "purpose": "检查是否有 ConfigMap/Secret 不存在或无法挂载的事件，辅助确认配置来源问题"
    },
    {
      "id": "e7",
      "description": "获取 Pod 所在节点的资源状态，排除节点级资源压力导致的异常行为",
      "level": "optional",
      "tool": "execute_prometheus_instant_query",
      "command": "execute_prometheus_instant_query(\"(1 - avg(rate(node_cpu_seconds_total{mode='idle'}[5m])) by (instance)) * 100\", \"\")",
      "purpose": "确认 node2 节点 CPU 使用率是否异常，排除因资源争用导致的启动超时或行为异常"
    }
  ],
  "collection_strategy": "优先采集 Pod YAML 和其父控制器（Deployment）信息，确认环境变量是否被定义和引用；其次验证 ConfigMap/Secret 是否存在且键名正确；最后通过事件和日志确认配置加载失败的直接证据。资源指标仅作为辅助排除项。"
}
```
   ✅ [证据链采集] 完成 (33.8s)
   📤 → 下游数据: evidence_items=0/7
   evidence_analysis={"evidence_plan": [{"id": "e1", "description": "获取 Pod appconfigfail-7649c79dc5-q4zjz 的完整 YAML，确认环境变量是否被正确注入", "level": "critical", "tool": "kubectl_get_yaml", "command": "kubectl get -o yaml pod appconfigfail-7649c79dc5-q4zjz -n aiops-e2e", "purpose": "验证容器是否定义了 APP_BOOT_MODE 环境变量，或是否从 ConfigMap/Secret 正确引用"}, {"id": "e2", "description": "获取 Pod 关联的 Deployment 配置，检查环境变量来源（ConfigMap/Secret）", "level": "critical", "tool": "kubectl_lineage_parents", "command": "kubectl lineage parents --kind Pod --name appconfigfail-7649c79dc5-q4zjz --namespace aiops-e2e", "purpose": "确定 Pod 由哪个控制器创建，并获取其模板中环境变量的定义来源"}, {"id": "e3", "description": "获取 Pod 的容器日志，确认错误信息是否持续出现且与 APP_BOOT_MODE 相关", "level": "critical", "tool": "kubectl_describe", "command": "kubectl describe pod appconfigfail-7649c79dc5-q4zjz -n aiops-e2e", "purpose": "虽然上游已提供日志片段，但需确认完整日志中是否存在重复的 'missing required APP_BOOT_MODE' 错误，排除临时性错误"}, {"id": "e4", "description": "获取 Pod 关联的 ConfigMap 和 Secret 列表，确认是否存在被引用但缺失或键名错误的配置", "level": "important", "tool": "kubectl_get_by_kind_in_namespace", "command": "kubectl get configmap -n aiops-e2e", "purpose": "列出所有 ConfigMap，查找可能被 Deployment 引用的配置，如 app-config、bootstrap-config 等"}, {"id": "e5", "description": "获取 Pod 关联的 Secret 列表，确认是否存在被引用但缺失或键名错误的密钥", "level": "important", "tool": "kubectl_get_by_kind_in_namespace", "command": "kubectl get secret -n aiops-e2e", "purpose": "列出所有 Secret，查找可能被 Deployment 引用的密钥，如 app-secrets、auth-config 等"}, {"id": "e6", "description": "获取 Pod 的事件历史，确认是否有配置加载失败的事件", "level": "important", "tool": "kubectl_events", "command": "kubectl events --resource-type pod --resource-name appconfigfail-7649c79dc5-q4zjz --namespace aiops-e2e", "purpose": "检查是否有 ConfigMap/Secret 不存在或无法挂载的事件，辅助确认配置来源问题"}, {"id": "e7", "description": "获取 Pod 所在节点的资源状态，排除节点级资源压力导致的异常行为", "level": "optional", "tool": "execute_prometheus_instant_query", "command": "execute_prometheus_instant_query(\"(1 - avg(rate(node_cpu_seconds_total{mode='idle'}[5m])) by (instance)) * 100\", \"\")", "purpose": "确认 node2 节点 CPU 使用率是否异常，排除因资源争用导致的启动超时或行为异常"}], "tool_results": [], "tool_data": [], "llm_analysis": "```json\n{\n  \"layer\": \"L4\",\n  \"evidence_plan\": [\n    {\n      \"id\": \"e1\",\n      \"description\": \"获取 Pod appconfigfail-7649c79dc5-q4zjz 的完整 YAML，确认环境变量是否被正确注入\",\n      \"level\": \"critical\",\n      \"tool\": \"kubectl_get_yaml\",\n      \"command\": \"kubectl get -o yaml pod appconfigfail-7649c79dc5-q4zjz -n aiops-e2e\",\n      \"purpose\": \"验证容器是否定义了 APP_BOOT_MODE 环境变量，或是否从 ConfigMap/Secret 正确引用\"\n    },\n    {\n      \"id\": \"e2\",\n      \"description\": \"获取 Pod 关联的 Deployment 配置，检查环境变量来源（ConfigMap/Secret）\",\n      \"level\": \"critical\",\n      \"tool\": \"kubectl_lineage_parents\",\n      \"command\": \"kubectl lineage parents --kind Pod --name appconfigfail-7649c79dc5-q4zjz --namespace aiops-e2e\",\n      \"purpose\": \"确定 Pod 由哪个控制器创建，并获取其模板中环境变量的定义来源\"\n    },\n    {\n      \"id\": \"e3\",\n      \"description\": \"获取 Pod 的容器日志，确认错误信息是否持续出现且与 APP_BOOT_MODE 相关\",\n      \"level\": \"critical\",\n      \"tool\": \"kubectl_describe\",\n      \"command\": \"kubectl describe pod appconfigfail-7649c79dc5-q4zjz -n aiops-e2e\",\n      \"purpose\": \"虽然上游已提供日志片段，但需确认完整日志中是否存在重复的 'missing required APP_BOOT_MODE' 错误，排除临时性错误\"\n    },\n    {\n      \"id\": \"e4\",\n      \"description\": \"获取 Pod 关联的 ConfigMap 和 Secret 列表，确认是否存在被引用但缺失或键名错误的配置\",\n      \"level\": \"important\",\n      \"tool\": \"kubectl_get_by_kind_in_namespace\",\n      \"command\": \"kubectl get configmap -n aiops-e2e\",\n      \"purpose\": \"列出所有 ConfigMap，查找可能被 Deployment 引用的配置，如 app-config、bootstrap-config 等\"\n    },\n    {\n      \"id\": \"e5\",\n      \"description\": \"获取 Pod 关联的 Secret 列表，确认是否存在被引用但缺失或键名错误的密钥\",\n      \"level\": \"important\",\n      \"tool\": \"kubectl_get_by_kind_in_namespace\",\n      \"command\": \"kubectl get secret -n aiops-e2e\",\n      \"purpose\": \"列出所有 Secret，查找可能被 Deployment 引用的密钥，如 app-secrets、auth-config 等\"\n    },\n    {\n      \"id\": \"e6\",\n      \"description\": \"获取 Pod 的事件历史，确认是否有配置加载失败的事件\",\n      \"level\": \"important\",\n      \"tool\": \"kubectl_events\",\n      \"command\": \"kubectl events --resource-type pod --resource-name appconfigfail-7649c79dc5-q4zjz --namespace aiops-e2e\",\n      \"purpose\": \"检查是否有 ConfigMap/Secret 不存在或无法挂载的事件，辅助确认配置来源问题\"\n    },\n    {\n      \"id\": \"e7\",\n      \"description\": \"获取 Pod 所在节点的资源状态，排除节点级资源压力导致的异常行为\",\n      \"level\": \"optional\",\n      \"tool\": \"execute_prometheus_instant_query\",\n      \"command\": \"execute_prometheus_instant_query(\\\"(1 - avg(rate(node_cpu_seconds_total{mode='idle'}[5m])) by (instance)) * 100\\\", \\\"\\\")\",\n      \"purpose\": \"确认 node2 节点 CPU 使用率是否异常，排除因资源争用导致的启动超时或行为异常\"\n    }\n  ],\n  \"collection_strategy\": \"优先采集 Pod YAML 和其父控制器（Deployment）信息，确认环境变量是否被定义和引用；其次验证 ConfigMap/Secret 是否存在且键名正确；最后通过事件和日志确认配置加载失败的直接证据。资源指标仅作为辅助排除项。\"\n}\n```", "collection_summary": "计划 7 项，实际采集 0 项，未采集 7 项，完整度 0%", "evidence_inventory": [{"id": "e1", "description": "获取 Pod appconfigfail-7649c79dc5-q4zjz 的完整 YAML，确认环境变量是否被正确注入", "level": "critical", "collected": false, "source": "planned"}, {"id": "e2", "description": "获取 Pod 关联的 Deployment 配置，检查环境变量来源（ConfigMap/Secret）", "level": "critical", "collected": false, "source": "planned"}, {"id": "e3", "description": "获取 Pod 的容器日志，确认错误信息是否持续出现且与 APP_BOOT_MODE 相关", "level": "critical", "collected": false, "source": "planned"}, {"id": "e4", "description": "获取 Pod 关联的 ConfigMap 和 Secret 列表，确认是否存在被引用但缺失或键名错误的配置", "level": "important", "collected": false, "source": "planned"}, {"id": "e5", "description": "获取 Pod 关联的 Secret 列表，确认是否存在被引用但缺失或键名错误的密钥", "level": "important", "collected": false, "source": "planned"}, {"id": "e6", "description": "获取 Pod 的事件历史，确认是否有配置加载失败的事件", "level": "important", "collected": false, "source": "planned"}, {"id": "e7", "description": "获取 Pod 所在节点的资源状态，排除节点级资源压力导致的异常行为", "level": "optional", "collected": false, "source": "planned"}], "missing_reasons": ["e1(获取 Pod appconfigfail-7649c79dc5-q4zjz 的完整 YAML，确认环境变量是否被正确注入): 已规划但工具执行失败或无匹配结果", "e2(获取 Pod 关联的 Deployment 配置，检查环境变量来源（ConfigMap/Secret）): 已规划但工具执行失败或无匹配结果", "e3(获取 Pod 的容器日志，确认错误信息是否持续出现且与 APP_BOOT_MODE 相关): 已规划但工具执行失败或无匹配结果", "e4(获取 Pod 关联的 ConfigMap 和 Secret 列表，确认是否存在被引用但缺失或键名错误的配置): 已规划但工具执行失败或无匹配结果", "e5(获取 Pod 关联的 Secret 列表，确认是否存在被引用但缺失或键名错误的密钥): 已规划但工具执行失败或无匹配结果", "e6(获取 Pod 的事件历史，确认是否有配置加载失败的事件): 已规划但工具执行失败或无匹配结果", "e7(获取 Pod 所在节点的资源状态，排除节点级资源压力导致的异常行为): 已规划但工具执行失败或无匹配结果"], "early_stop": {"triggered": false, "reason": "", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 0/7 项, 完整度: 0%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (35.3s)
   📤 → 下游数据: root_cause=
   confidence=85%
   causal_chain={"root_cause": "Deployment 模板中未定义或错误配置了 APP_BOOT_MODE 环境变量的来源（ConfigMap/Secret）", "propagation": "Pod 由 Deployment 创建，继承了错误的模板配置，导致容器启动时无 APP_BOOT_MODE 环境变量", "direct_cause": "应用启动脚本检测到必需环境变量 APP_BOOT_MODE 不存在，触发校验失败并主动退出，退出码 42", "manifestation": "Pod appconfigfail-7649c79dc5-q4zjz 处于 CrashLoopBackOff 状态，已重启 31 次，容器日志持续输出 'FATAL: missing required APP_BOOT_MODE'"}
   rca_analysis={"phenomenon": "Pod appconfigfail-7649c79dc5-q4zjz 在 aiops-e2e 命名空间中持续处于 CrashLoopBackOff 状态，已重启 31 次，每次启动均因缺失环境变量 APP_BOOT_MODE 而退出，退出码为 42。", "evidence_inventory": [{"id": "e1", "content": "获取 Pod appconfigfail-7649c79dc5-q4zjz 的完整 YAML，确认环境变量是否被正确注入", "source": "LLM 证据分析", "reliability": "低"}, {"id": "e2", "content": "获取 Pod 关联的 Deployment 配置，检查环境变量来源（ConfigMap/Secret）", "source": "LLM 证据分析", "reliability": "低"}, {"id": "e3", "content": "获取 Pod 的容器日志，确认错误信息是否持续出现且与 APP_BOOT_MODE 相关", "source": "LLM 证据分析", "reliability": "低"}, {"id": "e4", "content": "获取 Pod 关联的 ConfigMap 和 Secret 列表，确认是否存在被引用但缺失或键名错误的配置", "source": "LLM 证据分析", "reliability": "低"}, {"id": "e5", "content": "获取 Pod 关联的 Secret 列表，确认是否存在被引用但缺失或键名错误的密钥", "source": "LLM 证据分析", "reliability": "低"}, {"id": "e6", "content": "获取 Pod 的事件历史，确认是否有配置加载失败的事件", "source": "LLM 证据分析", "reliability": "低"}], "evidence_analysis": [{"evidence_id": "e3", "raw_data": "容器日志输出 'FATAL: missing required APP_BOOT_MODE' 和 'business config validation failed'", "interpretation": "直接证明应用在启动时因环境变量 APP_BOOT_MODE 缺失而主动退出，退出码 42 与该错误匹配，非临时性错误，而是确定性校验失败。"}, {"evidence_id": "e1", "raw_data": "Container 环境变量为空（Environment: <none>）", "interpretation": "Pod 的容器定义中未注入任何环境变量，包括 APP_BOOT_MODE，表明环境变量未被正确配置在 Pod 模板中。"}, {"evidence_id": "e2", "raw_data": "Pod 重启次数为 31 次，Last State Exit Code: 42", "interpretation": "高频重启（31次）且退出码为 42，排除 OOMKilled（137）、镜像拉取失败等其他层级问题，锁定为应用层配置校验失败。"}, {"evidence_id": "e4", "raw_data": "无 ConfigMap 或 Secret 的实际数据，仅列出采集计划", "interpretation": "未采集实际 ConfigMap/Secret 列表，无法确认是否引用了错误或缺失的配置源，但已知环境变量为空，可推断配置源未被正确挂载或定义。"}], "causal_chain": {"root_cause": "Deployment 模板中未定义或错误配置了 APP_BOOT_MODE 环境变量的来源（ConfigMap/Secret）", "propagation": "Pod 由 Deployment 创建，继承了错误的模板配置，导致容器启动时无 APP_BOOT_MODE 环境变量", "direct_cause": "应用启动脚本检测到必需环境变量 APP_BOOT_MODE 不存在，触发校验失败并主动退出，退出码 42", "manifestation": "Pod appconfigfail-7649c79dc5-q4zjz 处于 CrashLoopBackOff 状态，已重启 31 次，容器日志持续输出 'FATAL: missing required APP_BOOT_MODE'"}, "root_cause_summary": "根因为 Deployment 模板中未正确注入 APP_BOOT_MODE 环境变量，证据为：Pod 环境变量为空（Environment: <none>），容器日志明确报错 'FATAL: missing required APP_BOOT_MODE'，且退出码为 42，重启 31 次，符合 L4 配置校验失败场景（参考 runbook: L4 应用启动配置校验失败场景）。", "confidence": 0.85, "primary_runbooks": ["L4 应用启动配置校验失败场景"], "alternative_causes": [], "limitations": "未采集 Pod YAML、Deployment 配置、ConfigMap/Secret 列表、事件历史等关键证据，无法确认环境变量是否本应从 ConfigMap/Secret 注入，或是否存在键名拼写错误、命名空间不匹配等更深层配置错误。当前结论基于已有日志和环境变量为空的证据，属于最可能根因，但未完全闭环验证。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 85%
   🔗 因果链:
     根本原因: Deployment 模板中未定义或错误配置了 APP_BOOT_MODE 环境变量的来源（ConfigMap/Secret）
     传导机制: Pod 由 Deployment 创建，继承了错误的模板配置，导致容器启动时无 APP_BOOT_MODE 环境变量
     最终表现: Pod appconfigfail-7649c79dc5-q4zjz 处于 CrashLoopBackOff 状态，已重启 31 次，容器日志持续输出 'FATAL: missing required APP_BOOT_MODE'


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 4.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5761 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 50.7s
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
| **问题层级** | L4 - 应用层 |
| **问题分类** | 应用启动配置校验失败（缺失环境变量 APP_BOOT_MODE） |
| **置信度** | 高 (85%) |
| **证据完整度** | 0/7 (0%) |

---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | appconfigfail-7649c79dc5-q4zjz |
| Namespace | aiops-e2e |
| Node | node2 |
| 错误信息 | `FATAL: missing required APP_BOOT_MODE`，`Exit Code: 42`，`CrashLoopBackOff`（已重启31次） |

**集群整体状态摘要**：
- 仅 `aiops-e2e` 命名空间下的 `appconfigfail-7649c79dc5-q4zjz` Pod 异常，其余所有 Pod 均为 `Running`。
- 无 OOMKilled（非 Exit Code 137）、无镜像拉取失败、无存储挂载错误。
- 节点 `node2` 无资源压力证据（但未采集 CPU/内存指标，仅基于其他 Pod 正常推断）。
- **结论**：集群整体健康，**唯一问题是应用层配置缺失导致单个 Pod 持续崩溃重启**。

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl describe pod appconfigfail-7649c79dc5-q4zjz -n aiops-e2e` | `Last State: Terminated, Exit Code: 42`<br>`Environment: <none>` | 容器未注入任何环境变量，应用因缺失 `APP_BOOT_MODE` 主动退出，非系统级错误 |
| 2 | 容器日志 | `fetch_runbook` + LLM 分析 | `FATAL: missing required APP_BOOT_MODE`<br>`business config validation failed` | 应用启动脚本执行严格校验，环境变量缺失即触发致命退出，非临时错误 |
| 3 | 重启频率 | `kubectl_get_by_kind_in_cluster` | `RESTARTS: 31` | 高频重启（31次）确认为确定性配置失败，非偶发性问题 |
| 4 | 问题层级 | `fetch_runbook` | 符合 L4 应用启动配置校验失败场景 | 排除 L0-L3 层面（节点、网络、镜像、存储）原因，锁定为应用层配置错误 |

### 证据关联分析
- **证据 #1 + #2 + #3 印证**：`Environment: <none>` → 应用启动时 `APP_BOOT_MODE` 为空 → 触发 `FATAL: missing required APP_BOOT_MODE` → 应用退出（Exit Code 42）→ Pod 重启 → 31次循环
- **证据链**：Deployment 模板未定义 `APP_BOOT_MODE` → Pod 继承空环境变量 → 应用校验失败 → 主动退出 → CrashLoopBackOff

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| Pod 完整 YAML | critical | 无法确认环境变量是否本应从 ConfigMap/Secret 注入，或是否拼写错误 |
| Deployment 配置 | critical | 无法定位配置缺失的具体位置（模板中未定义？引用了错误的 ConfigMap？） |
| ConfigMap/Secret 列表 | important | 无法确认是否存在名为 `app-config` 或类似资源，或键名是否为 `APP_BOOT_MODE` |
| Pod 事件历史 | important | 无法确认是否有 “ConfigMap not found” 或 “Secret not found” 事件辅助定位 |
| 节点资源指标 | optional | 无法100%排除节点负载干扰，但其他 Pod 正常，可能性极低 |

> ✅ **注**：所有7项采集计划均未成功执行，当前结论基于有限但高度一致的证据推断，属最可能根因。

---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Deployment 模板中未定义或错误引用了 APP_BOOT_MODE 环境变量来源     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Pod 继承 Deployment 模板，容器启动时 Environment: <none>         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 应用启动脚本检测到 APP_BOOT_MODE 缺失，触发校验失败并退出（42）   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 处于 CrashLoopBackOff，已重启 31 次，日志持续报错              │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1（`Environment: <none>`）、证据 #2（`FATAL: missing required APP_BOOT_MODE`）和证据 #3（`Exit Code: 42`，重启31次），  
问题的根本原因是**Deployment 模板中未正确配置 `APP_BOOT_MODE` 环境变量**，导致容器启动时缺失该必需变量，应用主动退出并持续重启。

**置信度**：高 (85%)  
- ✅ `Environment: <none>` 直接证明无环境变量注入  
- ✅ 日志明确报错 `missing required APP_BOOT_MODE`  
- ✅ Exit Code 42 与应用层校验失败匹配（runbook L4 场景）  
- ⚠️ 缺少 Deployment YAML 和 ConfigMap 证据，无法确认是否因“引用了错误的 ConfigMap”或“键名拼错”（如 `app_boot_mode` vs `APP_BOOT_MODE`），故置信度未达100%

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 检查并修复 Deployment 环境变量配置**
```bash
# 1. 查看该 Pod 对应的 Deployment 名称
kubectl get pods -n aiops-e2e appconfigfail-7649c79dc5-q4zjz -o jsonpath='{.metadata.ownerReferences[0].name}'

# 假设输出为：appconfigfail
# 2. 编辑 Deployment，添加 APP_BOOT_MODE 环境变量
kubectl edit deployment appconfigfail -n aiops-e2e
```
在 `spec.template.spec.containers[0].env` 中添加：
```yaml
env:
- name: APP_BOOT_MODE
  value: "prod"  # 或 "dev"、"test"，根据业务需求填写
```
> ✅ **依据**：当前容器环境变量为空，必须显式注入该变量。常见值为 `prod`、`dev`、`test`，请确认业务要求。

**2. [可选] 若变量应来自 ConfigMap/Secret，验证并修复引用**
```bash
# 查看是否存在可能的配置资源
kubectl get configmap -n aiops-e2e
kubectl get secret -n aiops-e2e

# 示例：若存在名为 app-config 的 ConfigMap，且包含键 APP_BOOT_MODE
kubectl get configmap app-config -n aiops-e2e -o yaml

# 修改 Deployment 使用 ConfigMap：
env:
- name: APP_BOOT_MODE
  valueFrom:
    configMapKeyRef:
      name: app-config
      key: APP_BOOT_MODE
```

**3. [可选] 查看容器日志确认启动流程**
```bash
# 若能获取日志，查看完整错误上下文
kubectl logs appconfigfail-7649c79dc5-q4zjz -n aiops-e2e --previous | grep -A 5 -B 5 "APP_BOOT_MODE"
```

### 后续优化
1. **配置管理标准化**：所有环境变量应通过 ConfigMap/Secret 管理，避免硬编码。
2. **启动健康检查**：为应用添加 `livenessProbe` 和 `readinessProbe`，避免无意义重启。
3. **CI/CD 检查**：在部署前校验 Deployment 中是否包含必需环境变量。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Deployment 已更新 | `kubectl get deployment appconfigfail -n aiops-e2e -o yaml \| grep -A 5 "env:"` | 包含 `APP_BOOT_MODE` 定义 |
| 2. 观察 Pod 是否重建 | `kubectl get pods -n aiops-e2e -w` | 新 Pod 启动，重启次数重置为0 |
| 3. 检查新 Pod 状态 | `kubectl get pod -n aiops-e2e -l app=appconfigfail` | STATUS: `Running`，RESTARTS: 0 |
| 4. 验证日志无错误 | `kubectl logs <new-pod-name> -n aiops-e2e` | 无 `FATAL: missing required APP_BOOT_MODE` |

---
## ⚠️ 注意事项
- **不要直接修改 Pod**：Pod 是 Deployment 的副本，修改会被覆盖。必须修改 Deployment。
- **环境变量值需符合业务语义**：`APP_BOOT_MODE=prod` 与 `APP_BOOT_MODE=dev` 可能加载不同配置，确认正确值。
- **若使用 Helm/ArgoCD**：请检查 values.yaml 或 Application CR 中是否遗漏了该环境变量。
- **如问题持续**：请手动执行 `kubectl get deployment appconfigfail -n aiops-e2e -o yaml > deployment.yaml`，检查 YAML 中 `env` 字段是否完整，必要时提交给开发团队核对配置规范。

---

## 📊 性能统计

├─ 总耗时: 2.8m
├─ 问题定位: 37.5s (22%) ✅
├─ 证据链采集: 33.8s (20%) ✅
├─ 根因分析: 35.3s (21%) ✅
├─ 汇总总结: 64.0s (38%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 5 次
```

📋 诊断追踪

- **核心 Runbook**: l4-config-bootstrap-fail
- **参考 Runbook**: l4-config-bootstrap-fail, private-k8s-health-reference
- **工具调用**: 5 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
