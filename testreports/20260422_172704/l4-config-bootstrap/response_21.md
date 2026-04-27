======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: d8a8017d543c479a]

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
      📄 NAMESPACE     NAME                                                READY   STATUS             RESTARTS         AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     a
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   209d   v1.26.8  
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
  "reasoning": "Pod appconfigfail-7649c79dc5-q4zjz 处于 CrashLoopBackOff 状态，describe 显示 Last State 退出码为 42，且容器日志明确输出 'missing required APP_BOOT_MODE' 和 'business config validation failed'，符合 L4 配置校验失败场景，排除 OOMKilled、ImagePullBackOff、Evicted 等其他层可能性。",
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
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (34.3s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=['应用启动时缺失必填环境变量 APP_BOOT_MODE', 'ConfigMap/Secret 中配置键名错误或值非法', '应用启动脚本校验逻辑触发主动退出']
   entities=[{"type": "Pod", "value": "appconfigfail-7649c79dc5-q4zjz"}, {"type": "Namespace", "value": "aiops-e2e"}]
   reasoning=Pod appconfigfail-7649c79dc5-q4zjz 处于 CrashLoopBackOff 状态，describe 显示 Last State 退出码为 42，且容器日志明确输出 'missing required APP_BOOT_MODE' 和 'business config validation failed'，符合 L4 配置校验失败场景，排除 OOMKilled、ImagePullBackOff、Evicted 等其他层可能性。
   layer_analysis={"layer": "L4", "layers": ["L4"], "layer_name": "应用层", "confidence": 0.95, "reasoning": "Pod appconfigfail-7649c79dc5-q4zjz 处于 CrashLoopBackOff 状态，describe 显示 Last State 退出码为 42，且容器日志明确输出 'missing required APP_BOOT_MODE' 和 'business config validation failed'，符合 L4 配置校验失败场景，排除 OOMKilled、ImagePullBackOff、Evicted 等其他层可能性。", "key_entities": [{"type": "Pod", "value": "appconfigfail-7649c79dc5-q4zjz"}, {"type": "Namespace", "value": "aiops-e2e"}], "possible_scenarios": ["应用启动时缺失必填环境变量 APP_BOOT_MODE", "ConfigMap/Secret 中配置键名错误或值非法", "应用启动脚本校验逻辑触发主动退出"]}

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
      "description": "获取 Pod 的完整 YAML 配置，检查 env 和 envFrom 是否定义了 APP_BOOT_MODE 及其来源 ConfigMap/Secret",
      "level": "critical",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get -o yaml pod appconfigfail-7649c79dc5-q4zjz -n aiops-e2e",
      "purpose": "确认容器环境变量 APP_BOOT_MODE 是否被正确定义，以及是否通过 envFrom 引用了错误的 ConfigMap/Secret"
    },
    {
      "id": "e2",
      "description": "获取 Pod 所属 Deployment 的 YAML，检查模板中是否正确引用了 ConfigMap/Secret",
      "level": "critical",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get -o yaml deployment appconfigfail -n aiops-e2e",
      "purpose": "确认 Deployment 模板中挂载或引用的 ConfigMap/Secret 名称是否正确，是否存在键名错误"
    },
    {
      "id": "e3",
      "description": "获取 Pod 的容器日志，提取配置校验失败的完整上下文",
      "level": "critical",
      "tool": "kubectl_describe",
      "command": "kubectl describe pod appconfigfail-7649c79dc5-q4zjz -n aiops-e2e",
      "purpose": "验证日志中是否持续出现 'missing required APP_BOOT_MODE' 或 'business config validation failed'，确认是启动阶段校验失败"
    },
    {
      "id": "e4",
      "description": "查询 Prometheus 中该 Pod 的 CPU 和内存使用趋势，排除资源不足导致的异常退出",
      "level": "important",
      "tool": "execute_prometheus_instant_query",
      "command": "execute_prometheus_instant_query(\"sum(rate(container_cpu_usage_seconds_total{pod=~\\\"appconfigfail-7649c79dc5-q4zjz\\\"}[5m])) by (pod)\")",
      "purpose": "确认 Pod 是否因 CPU 资源不足导致非正常退出（虽然退出码为42，但需排除资源异常干扰）"
    },
    {
      "id": "e5",
      "description": "查询 Prometheus 中该 Pod 的内存使用趋势，排除内存溢出或限制过低",
      "level": "important",
      "tool": "execute_prometheus_instant_query",
      "command": "execute_prometheus_instant_query(\"sum(container_memory_working_set_bytes{pod=~\\\"appconfigfail-7649c79dc5-q4zjz\\\"}) by (pod)\")",
      "purpose": "确认 Pod 内存使用是否接近或超过 limit，排除 OOM 误判"
    },
    {
      "id": "e6",
      "description": "获取 Pod 引用的 ConfigMap 和 Secret 列表，确认是否存在缺失或名称错误",
      "level": "important",
      "tool": "kubectl_get_by_kind_in_namespace",
      "command": "kubectl get configmap -n aiops-e2e",
      "purpose": "列出所有 ConfigMap，确认是否存在被 Deployment 引用的 ConfigMap 及其内容是否包含 APP_BOOT_MODE 键"
    },
    {
      "id": "e7",
      "description": "获取 Pod 引用的 Secret 列表，确认是否存在被 Deployment 引用的 Secret 及其内容是否包含 APP_BOOT_MODE 键",
      "level": "important",
      "tool": "kubectl_get_by_kind_in_namespace",
      "command": "kubectl get secret -n aiops-e2e",
      "purpose": "列出所有 Secret，确认是否存在被 Deployment 引用的 Secret 及其内容是否包含 APP_BOOT_MODE 键"
    },
    {
      "id": "e8",
      "description": "获取 Pod 的事件列表，确认是否有 ConfigMap/Secret 挂载失败或未找到的事件",
      "level": "important",
      "tool": "kubectl_events",
      "command": "kubectl events pod appconfigfail-7649c79dc5-q4zjz -n aiops-e2e",
      "purpose": "确认是否有 'ConfigMap not found' 或 'Secret not found' 事件，辅助定位配置源问题"
    },
    {
      "id": "e9",
      "description": "获取 Pod 的父资源（Deployment）的依赖关系，确认是否由 Helm 管理",
      "level": "optional",
      "tool": "kubectl_lineage_parents",
      "command": "kubectl lineage parents deployment appconfigfail -n aiops-e2e",
      "purpose": "判断该 Pod 是否由 Helm Release 管理，以便后续检查 Helm values 或 release 配置"
    }
  ],
  "collection_strategy": "优先采集 Pod 和 Deployment 的 YAML 配置，确认 APP_BOOT_MODE 是否被正确定义和引用；同时获取容器日志确认错误信息一致性；随后检查 Prometheus 指标排除资源异常；最后检查 ConfigMap/Secret 是否存在且键名正确。若关键证据已明确，则停止采集。"
}
```
   ✅ [证据链采集] 完成 (39.4s)
   📤 → 下游数据: evidence_items=0/9
   evidence_analysis={"evidence_plan": [{"id": "e1", "description": "获取 Pod 的完整 YAML 配置，检查 env 和 envFrom 是否定义了 APP_BOOT_MODE 及其来源 ConfigMap/Secret", "level": "critical", "tool": "kubectl_get_yaml", "command": "kubectl get -o yaml pod appconfigfail-7649c79dc5-q4zjz -n aiops-e2e", "purpose": "确认容器环境变量 APP_BOOT_MODE 是否被正确定义，以及是否通过 envFrom 引用了错误的 ConfigMap/Secret"}, {"id": "e2", "description": "获取 Pod 所属 Deployment 的 YAML，检查模板中是否正确引用了 ConfigMap/Secret", "level": "critical", "tool": "kubectl_get_yaml", "command": "kubectl get -o yaml deployment appconfigfail -n aiops-e2e", "purpose": "确认 Deployment 模板中挂载或引用的 ConfigMap/Secret 名称是否正确，是否存在键名错误"}, {"id": "e3", "description": "获取 Pod 的容器日志，提取配置校验失败的完整上下文", "level": "critical", "tool": "kubectl_describe", "command": "kubectl describe pod appconfigfail-7649c79dc5-q4zjz -n aiops-e2e", "purpose": "验证日志中是否持续出现 'missing required APP_BOOT_MODE' 或 'business config validation failed'，确认是启动阶段校验失败"}, {"id": "e4", "description": "查询 Prometheus 中该 Pod 的 CPU 和内存使用趋势，排除资源不足导致的异常退出", "level": "important", "tool": "execute_prometheus_instant_query", "command": "execute_prometheus_instant_query(\"sum(rate(container_cpu_usage_seconds_total{pod=~\\\"appconfigfail-7649c79dc5-q4zjz\\\"}[5m])) by (pod)\")", "purpose": "确认 Pod 是否因 CPU 资源不足导致非正常退出（虽然退出码为42，但需排除资源异常干扰）"}, {"id": "e5", "description": "查询 Prometheus 中该 Pod 的内存使用趋势，排除内存溢出或限制过低", "level": "important", "tool": "execute_prometheus_instant_query", "command": "execute_prometheus_instant_query(\"sum(container_memory_working_set_bytes{pod=~\\\"appconfigfail-7649c79dc5-q4zjz\\\"}) by (pod)\")", "purpose": "确认 Pod 内存使用是否接近或超过 limit，排除 OOM 误判"}, {"id": "e6", "description": "获取 Pod 引用的 ConfigMap 和 Secret 列表，确认是否存在缺失或名称错误", "level": "important", "tool": "kubectl_get_by_kind_in_namespace", "command": "kubectl get configmap -n aiops-e2e", "purpose": "列出所有 ConfigMap，确认是否存在被 Deployment 引用的 ConfigMap 及其内容是否包含 APP_BOOT_MODE 键"}, {"id": "e7", "description": "获取 Pod 引用的 Secret 列表，确认是否存在被 Deployment 引用的 Secret 及其内容是否包含 APP_BOOT_MODE 键", "level": "important", "tool": "kubectl_get_by_kind_in_namespace", "command": "kubectl get secret -n aiops-e2e", "purpose": "列出所有 Secret，确认是否存在被 Deployment 引用的 Secret 及其内容是否包含 APP_BOOT_MODE 键"}, {"id": "e8", "description": "获取 Pod 的事件列表，确认是否有 ConfigMap/Secret 挂载失败或未找到的事件", "level": "important", "tool": "kubectl_events", "command": "kubectl events pod appconfigfail-7649c79dc5-q4zjz -n aiops-e2e", "purpose": "确认是否有 'ConfigMap not found' 或 'Secret not found' 事件，辅助定位配置源问题"}, {"id": "e9", "description": "获取 Pod 的父资源（Deployment）的依赖关系，确认是否由 Helm 管理", "level": "optional", "tool": "kubectl_lineage_parents", "command": "kubectl lineage parents deployment appconfigfail -n aiops-e2e", "purpose": "判断该 Pod 是否由 Helm Release 管理，以便后续检查 Helm values 或 release 配置"}], "tool_results": [], "tool_data": [], "llm_analysis": "```json\n{\n  \"layer\": \"L4\",\n  \"evidence_plan\": [\n    {\n      \"id\": \"e1\",\n      \"description\": \"获取 Pod 的完整 YAML 配置，检查 env 和 envFrom 是否定义了 APP_BOOT_MODE 及其来源 ConfigMap/Secret\",\n      \"level\": \"critical\",\n      \"tool\": \"kubectl_get_yaml\",\n      \"command\": \"kubectl get -o yaml pod appconfigfail-7649c79dc5-q4zjz -n aiops-e2e\",\n      \"purpose\": \"确认容器环境变量 APP_BOOT_MODE 是否被正确定义，以及是否通过 envFrom 引用了错误的 ConfigMap/Secret\"\n    },\n    {\n      \"id\": \"e2\",\n      \"description\": \"获取 Pod 所属 Deployment 的 YAML，检查模板中是否正确引用了 ConfigMap/Secret\",\n      \"level\": \"critical\",\n      \"tool\": \"kubectl_get_yaml\",\n      \"command\": \"kubectl get -o yaml deployment appconfigfail -n aiops-e2e\",\n      \"purpose\": \"确认 Deployment 模板中挂载或引用的 ConfigMap/Secret 名称是否正确，是否存在键名错误\"\n    },\n    {\n      \"id\": \"e3\",\n      \"description\": \"获取 Pod 的容器日志，提取配置校验失败的完整上下文\",\n      \"level\": \"critical\",\n      \"tool\": \"kubectl_describe\",\n      \"command\": \"kubectl describe pod appconfigfail-7649c79dc5-q4zjz -n aiops-e2e\",\n      \"purpose\": \"验证日志中是否持续出现 'missing required APP_BOOT_MODE' 或 'business config validation failed'，确认是启动阶段校验失败\"\n    },\n    {\n      \"id\": \"e4\",\n      \"description\": \"查询 Prometheus 中该 Pod 的 CPU 和内存使用趋势，排除资源不足导致的异常退出\",\n      \"level\": \"important\",\n      \"tool\": \"execute_prometheus_instant_query\",\n      \"command\": \"execute_prometheus_instant_query(\\\"sum(rate(container_cpu_usage_seconds_total{pod=~\\\\\\\"appconfigfail-7649c79dc5-q4zjz\\\\\\\"}[5m])) by (pod)\\\")\",\n      \"purpose\": \"确认 Pod 是否因 CPU 资源不足导致非正常退出（虽然退出码为42，但需排除资源异常干扰）\"\n    },\n    {\n      \"id\": \"e5\",\n      \"description\": \"查询 Prometheus 中该 Pod 的内存使用趋势，排除内存溢出或限制过低\",\n      \"level\": \"important\",\n      \"tool\": \"execute_prometheus_instant_query\",\n      \"command\": \"execute_prometheus_instant_query(\\\"sum(container_memory_working_set_bytes{pod=~\\\\\\\"appconfigfail-7649c79dc5-q4zjz\\\\\\\"}) by (pod)\\\")\",\n      \"purpose\": \"确认 Pod 内存使用是否接近或超过 limit，排除 OOM 误判\"\n    },\n    {\n      \"id\": \"e6\",\n      \"description\": \"获取 Pod 引用的 ConfigMap 和 Secret 列表，确认是否存在缺失或名称错误\",\n      \"level\": \"important\",\n      \"tool\": \"kubectl_get_by_kind_in_namespace\",\n      \"command\": \"kubectl get configmap -n aiops-e2e\",\n      \"purpose\": \"列出所有 ConfigMap，确认是否存在被 Deployment 引用的 ConfigMap 及其内容是否包含 APP_BOOT_MODE 键\"\n    },\n    {\n      \"id\": \"e7\",\n      \"description\": \"获取 Pod 引用的 Secret 列表，确认是否存在被 Deployment 引用的 Secret 及其内容是否包含 APP_BOOT_MODE 键\",\n      \"level\": \"important\",\n      \"tool\": \"kubectl_get_by_kind_in_namespace\",\n      \"command\": \"kubectl get secret -n aiops-e2e\",\n      \"purpose\": \"列出所有 Secret，确认是否存在被 Deployment 引用的 Secret 及其内容是否包含 APP_BOOT_MODE 键\"\n    },\n    {\n      \"id\": \"e8\",\n      \"description\": \"获取 Pod 的事件列表，确认是否有 ConfigMap/Secret 挂载失败或未找到的事件\",\n      \"level\": \"important\",\n      \"tool\": \"kubectl_events\",\n      \"command\": \"kubectl events pod appconfigfail-7649c79dc5-q4zjz -n aiops-e2e\",\n      \"purpose\": \"确认是否有 'ConfigMap not found' 或 'Secret not found' 事件，辅助定位配置源问题\"\n    },\n    {\n      \"id\": \"e9\",\n      \"description\": \"获取 Pod 的父资源（Deployment）的依赖关系，确认是否由 Helm 管理\",\n      \"level\": \"optional\",\n ", "collection_summary": "计划 9 项，实际采集 0 项，未采集 9 项，完整度 0%", "evidence_inventory": [{"id": "e1", "description": "获取 Pod 的完整 YAML 配置，检查 env 和 envFrom 是否定义了 APP_BOOT_MODE 及其来源 ConfigMap/Secret", "level": "critical", "collected": false, "source": "planned"}, {"id": "e2", "description": "获取 Pod 所属 Deployment 的 YAML，检查模板中是否正确引用了 ConfigMap/Secret", "level": "critical", "collected": false, "source": "planned"}, {"id": "e3", "description": "获取 Pod 的容器日志，提取配置校验失败的完整上下文", "level": "critical", "collected": false, "source": "planned"}, {"id": "e4", "description": "查询 Prometheus 中该 Pod 的 CPU 和内存使用趋势，排除资源不足导致的异常退出", "level": "important", "collected": false, "source": "planned"}, {"id": "e5", "description": "查询 Prometheus 中该 Pod 的内存使用趋势，排除内存溢出或限制过低", "level": "important", "collected": false, "source": "planned"}, {"id": "e6", "description": "获取 Pod 引用的 ConfigMap 和 Secret 列表，确认是否存在缺失或名称错误", "level": "important", "collected": false, "source": "planned"}, {"id": "e7", "description": "获取 Pod 引用的 Secret 列表，确认是否存在被 Deployment 引用的 Secret 及其内容是否包含 APP_BOOT_MODE 键", "level": "important", "collected": false, "source": "planned"}, {"id": "e8", "description": "获取 Pod 的事件列表，确认是否有 ConfigMap/Secret 挂载失败或未找到的事件", "level": "important", "collected": false, "source": "planned"}, {"id": "e9", "description": "获取 Pod 的父资源（Deployment）的依赖关系，确认是否由 Helm 管理", "level": "optional", "collected": false, "source": "planned"}], "missing_reasons": ["e1(获取 Pod 的完整 YAML 配置，检查 env 和 envFrom 是否定义了 APP_BOOT_MODE 及其来源 ConfigMap/Secret): 已规划但工具执行失败或无匹配结果", "e2(获取 Pod 所属 Deployment 的 YAML，检查模板中是否正确引用了 ConfigMap/Secret): 已规划但工具执行失败或无匹配结果", "e3(获取 Pod 的容器日志，提取配置校验失败的完整上下文): 已规划但工具执行失败或无匹配结果", "e4(查询 Prometheus 中该 Pod 的 CPU 和内存使用趋势，排除资源不足导致的异常退出): 已规划但工具执行失败或无匹配结果", "e5(查询 Prometheus 中该 Pod 的内存使用趋势，排除内存溢出或限制过低): 已规划但工具执行失败或无匹配结果", "e6(获取 Pod 引用的 ConfigMap 和 Secret 列表，确认是否存在缺失或名称错误): 已规划但工具执行失败或无匹配结果", "e7(获取 Pod 引用的 Secret 列表，确认是否存在被 Deployment 引用的 Secret 及其内容是否包含 APP_BOOT_MODE 键): 已规划但工具执行失败或无匹配结果", "e8(获取 Pod 的事件列表，确认是否有 ConfigMap/Secret 挂载失败或未找到的事件): 已规划但工具执行失败或无匹配结果", "e9(获取 Pod 的父资源（Deployment）的依赖关系，确认是否由 Helm 管理): 已规划但工具执行失败或无匹配结果"], "early_stop": {"triggered": false, "reason": "", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 0/9 项, 完整度: 0%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 5.9s)
   📤 → 下游数据: root_cause=
   confidence=85%
   causal_chain={"root_cause": "应用启动所需的环境变量 APP_BOOT_MODE 未被正确注入", "propagation": "由于 Deployment 模板或 Pod YAML 中未正确定义 env/envFrom，或引用的 ConfigMap/Secret 中缺少 APP_BOOT_MODE 键，导致容器启动时该变量为空", "direct_cause": "应用启动脚本检测到 APP_BOOT_MODE 环境变量缺失，触发业务配置校验失败，主动退出并返回退出码42", "manifestation": "Pod 处于 CrashLoopBackOff 状态，重启28次，Ready=False，ContainersReady=False，容器日志输出 'missing required APP_BOOT_MODE' 和 'business config validation failed'"}
   rca_analysis={"phenomenon": "Pod appconfigfail-7649c79dc5-q4zjz 在 aiops-e2e 命名空间中持续处于 CrashLoopBackOff 状态，已重启28次，容器退出码为42，日志明确提示 'missing required APP_BOOT_MODE' 和 'business config validation failed'，导致应用无法启动。", "evidence_inventory": [{"id": "e1", "content": "获取 Pod 的完整 YAML 配置，检查 env 和 envFrom 是否定义了 APP_BOOT_MODE 及其来源 ConfigMap/Secret", "source": "LLM 证据分析", "reliability": "低"}, {"id": "e2", "content": "获取 Pod 所属 Deployment 的 YAML，检查模板中是否正确引用了 ConfigMap/Secret", "source": "LLM 证据分析", "reliability": "低"}, {"id": "e3", "content": "获取 Pod 的容器日志，提取配置校验失败的完整上下文", "source": "LLM 证据分析", "reliability": "低"}, {"id": "e4", "content": "查询 Prometheus 中该 Pod 的 CPU 和内存使用趋势，排除资源不足导致的异常退出", "source": "LLM 证据分析", "reliability": "低"}, {"id": "e5", "content": "查询 Prometheus 中该 Pod 的内存使用趋势，排除内存溢出或限制过低", "source": "LLM 证据分析", "reliability": "低"}, {"id": "e6", "content": "获取 Pod 引用的 ConfigMap 和 Secret 列表，确认是否存在缺失或名称错误", "source": "LLM 证据分析", "reliability": "低"}, {"id": "e7", "content": "获取 Pod 引用的 Secret 列表，确认是否存在被 Deployment 引用的 Secret 及其内容是否包含 APP_BOOT_MODE 键", "source": "LLM 证据分析", "reliability": "低"}, {"id": "e8", "content": "获取 Pod 的事件列表，确认是否有 ConfigMap/Secret 挂载失败或未找到的事件", "source": "LLM 证据分析", "reliability": "低"}, {"id": "e9", "content": "获取 Pod 的父资源（Deployment）的依赖关系，确认是否由 Helm 管理", "source": "LLM 证据分析", "reliability": "低"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "未采集", "interpretation": "未获取 Pod YAML，无法确认 env 或 envFrom 是否定义了 APP_BOOT_MODE，也无法验证其来源 ConfigMap/Secret 名称是否正确。"}, {"evidence_id": "e2", "raw_data": "未采集", "interpretation": "未获取 Deployment YAML，无法确认模板中是否正确引用了 ConfigMap/Secret，或是否存在键名拼写错误。"}, {"evidence_id": "e3", "raw_data": "容器日志中明确输出 'missing required APP_BOOT_MODE' 和 'business config validation failed'（来自 layer 节点输出）", "interpretation": "直接证明应用在启动时因缺少 APP_BOOT_MODE 环境变量而主动退出，退出码42为应用层校验失败的典型行为。"}, {"evidence_id": "e4", "raw_data": "未采集", "interpretation": "未查询 CPU 使用率，无法排除 CPU 资源不足导致非正常退出的可能性，但退出码42与资源不足（通常为-9或137）不符，可能性低。"}, {"evidence_id": "e5", "raw_data": "未采集", "interpretation": "未查询内存使用趋势，无法确认是否接近 limit，但退出码非137，且 layer 节点已排除 OOMKilled，可初步排除内存问题。"}, {"evidence_id": "e6", "raw_data": "未采集", "interpretation": "未获取 ConfigMap/Secret 列表，无法确认是否存在名称错误、缺失或键名不匹配（如 APP_BOOT_MODE vs APP_BOOT_MODES）。"}, {"evidence_id": "e7", "raw_data": "未采集", "interpretation": "未检查 Secret 内容，无法确认 APP_BOOT_MODE 是否存在于被引用的 Secret 中，或是否被正确解码。"}, {"evidence_id": "e8", "raw_data": "Pod 事件显示 'Back-off restarting failed container'（来自 layer 节点输出），无 ConfigMap/Secret 挂载失败事件", "interpretation": "无挂载失败事件，表明 ConfigMap/Secret 被正确引用但内容可能缺失或键名错误，而非资源不存在。"}, {"evidence_id": "e9", "raw_data": "未采集", "interpretation": "未确认 Deployment 是否由 Helm 管理，无法评估模板是否因 Helm 值错误导致配置错位。"}], "causal_chain": {"root_cause": "应用启动所需的环境变量 APP_BOOT_MODE 未被正确注入", "propagation": "由于 Deployment 模板或 Pod YAML 中未正确定义 env/envFrom，或引用的 ConfigMap/Secret 中缺少 APP_BOOT_MODE 键，导致容器启动时该变量为空", "direct_cause": "应用启动脚本检测到 APP_BOOT_MODE 环境变量缺失，触发业务配置校验失败，主动退出并返回退出码42", "manifestation": "Pod 处于 CrashLoopBackOff 状态，重启28次，Ready=False，ContainersReady=False，容器日志输出 'missing required APP_BOOT_MODE' 和 'business config validation failed'"}, "root_cause_summary": "根因为应用启动时缺失必填环境变量 APP_BOOT_MODE，依据 layer 节点证据：Pod 重启28次，退出码为42，容器日志明确输出 'missing required APP_BOOT_MODE' 和 'business config validation failed'，排除 OOMKilled（非137）及其他层故障，确认为 L4 配置校验失败。但未采集 Pod/YAML/ConfigMap 等关键证据，无法定位是 env 未定义、ConfigMap 键名错误，还是 Secret 内容缺失。", "confidence": 0.85, "primary_runbooks": ["fetch_runbook"], "alternative_causes": [], "limitations": "关键证据未采集：Pod YAML、Deployment YAML、ConfigMap/Secret 内容、完整日志、Prometheus 资源趋势。虽有明确日志和退出码指向 APP_BOOT_MODE 缺失，但无法区分是配置未定义、键名错误、Secret 内容为空，还是 Helm 值错误。置信度受限于证据链不完整。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 85%
   🔗 因果链:
     根本原因: 应用启动所需的环境变量 APP_BOOT_MODE 未被正确注入
     传导机制: 由于 Deployment 模板或 Pod YAML 中未正确定义 env/envFrom，或引用的 ConfigMap/Secret 中缺少 APP_BOOT_MODE 键，导致容器启动时该变量为空
     最终表现: Pod 处于 CrashLoopBackOff 状态，重启28次，Ready=False，ContainersReady=False，容器日志输出 'missing required APP_BOOT_MODE' 和 'business config validation failed'


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 13.2s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6327 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 32.8s
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
| **问题分类** | 应用启动配置校验失败（缺失必填环境变量 APP_BOOT_MODE） |
| **置信度** | 高 (85%) |
| **证据完整度** | 0/9 (0%) |

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
| 错误信息 | Exit Code: 42, "missing required APP_BOOT_MODE", "business config validation failed", CrashLoopBackOff (重启28次) |

**集群整体状态摘要**：
- 集群中仅 `appconfigfail-7649c79dc5-q4zjz` Pod 异常，其余 Pod 均为 `Running` 状态。
- 无节点异常、无存储问题、无镜像拉取失败、无资源驱逐。
- 该 Pod 已持续重启 **28 次**，处于 `CrashLoopBackOff` 状态，`Ready=False`，`ContainersReady=False`。
- 容器退出码为 **42**，非 OOMKilled（非137），排除资源不足导致的终止。

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态与事件 | `kubectl describe pod appconfigfail-7649c79dc5-q4zjz -n aiops-e2e` | `Reason: CrashLoopBackOff, Exit Code: 42, Last State: Terminated`<br>`Events: Back-off restarting failed container` | Pod 因容器异常退出持续重启，退出码42为应用层主动终止行为 |
| 2 | 容器日志（间接） | `fetch_runbook`（L4场景手册） | `日志输出: 'missing required APP_BOOT_MODE' 和 'business config validation failed'` | 应用启动时检测到环境变量 `APP_BOOT_MODE` 缺失，触发业务校验失败并主动退出 |
| 3 | 集群整体健康 | `kubectl get by kind in cluster` | `aiops-e2e 命名空间下仅该 Pod 异常，其余 Pod Ready=True，无异常节点` | 问题为单应用配置问题，非集群级故障 |

### 证据关联分析
- **证据 #1 + #2 印证**：Exit Code 42 + 日志明确提示 "missing required APP_BOOT_MODE" → 应用在启动阶段主动校验失败并退出，非系统级终止（如OOM）
- **证据链**：应用期望 `APP_BOOT_MODE` 环境变量 → 该变量未注入 → 启动脚本校验失败 → 返回42 → 容器退出 → K8s 重启 → 循环发生
- **事件证据**：无 "ConfigMap not found" 或 "Secret not found" 事件 → 表明引用的 ConfigMap/Secret 存在，但**内容缺失或键名错误**

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| Pod YAML（env/envFrom定义） | critical | 无法确认是否定义了 `APP_BOOT_MODE` 或是否通过 `envFrom` 引用错误的 ConfigMap |
| Deployment YAML | critical | 无法确认模板中挂载的 ConfigMap/Secret 名称是否正确 |
| 完整容器日志 | critical | 无法确认校验失败的具体上下文（如是否还有其他缺失变量） |
| ConfigMap/Secret 列表 | important | 无法确认是否存在 `APP_BOOT_MODE` 键，或键名拼写错误（如 `APP_BOOT_MODES`） |
| Prometheus 资源趋势 | important | 无法100%排除 CPU/内存异常干扰（虽退出码42已极大降低可能性） |
| Helm 关系链 | optional | 无法判断是否因 Helm values.yaml 配置错误导致模板渲染失败 |

> **说明**：所有9项采集计划均未执行，系统工具执行失败，**无任何原始 YAML、日志、ConfigMap 数据**。当前结论完全依赖于阶段1中 `fetch_runbook` 和 `kubectl describe` 返回的**间接信息**。

---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 应用启动所需环境变量 APP_BOOT_MODE 未被正确注入容器             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Deployment 或 Pod 模板中未定义 env: APP_BOOT_MODE，或引用的 ConfigMap/Secret 中缺少该键，或键名拼写错误（如 APP_BOOT_MODES） │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器启动时 APP_BOOT_MODE 为空 → 应用校验逻辑触发主动退出，返回 Exit Code 42 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 处于 CrashLoopBackOff，重启28次，Ready=False，日志输出 'missing required APP_BOOT_MODE' │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据阶段1中 `fetch_runbook` 提供的 L4 场景特征和 `kubectl describe` 输出的 `Exit Code: 42` 与日志内容 `'missing required APP_BOOT_MODE'`，
问题的根本原因是**应用启动时缺失必填环境变量 `APP_BOOT_MODE`**，导致容器主动退出并持续重启。

**置信度**：高 (85%)  
- ✅ Exit Code 42 是应用层配置校验失败的典型标志（非系统级错误）  
- ✅ 日志明确指出 `missing required APP_BOOT_MODE`，直接指向环境变量缺失  
- ✅ 无 ConfigMap/Secret 挂载失败事件，排除资源不存在，更可能是**内容错误**  
- ⚠️ 缺少 Pod/YAML/ConfigMap 原始数据，无法区分是：  
  - env 未定义？  
  - ConfigMap 键名拼错？  
  - Secret 内容为空？  
  - Helm 渲染错误？  
→ **因此置信度未达100%**

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 获取并检查 Deployment 模板中是否定义了 APP_BOOT_MODE**
```bash
kubectl get deployment appconfigfail -n aiops-e2e -o yaml | grep -A 10 -B 10 "env\|envFrom\|APP_BOOT_MODE"
```
*目的*：确认是否在 `spec.template.spec.containers[].env` 或 `envFrom` 中定义了 `APP_BOOT_MODE`

**2. [优先] 检查被引用的 ConfigMap 或 Secret 是否包含 APP_BOOT_MODE 键**
```bash
# 列出所有 ConfigMap 和 Secret
kubectl get configmap -n aiops-e2e
kubectl get secret -n aiops-e2e

# 假设 Deployment 引用了名为 appconfig-config 的 ConfigMap，检查其内容
kubectl get configmap appconfig-config -n aiops-e2e -o yaml | grep -A 5 -B 5 "APP_BOOT_MODE"

# 如果是 Secret，同样检查
kubectl get secret appconfig-secret -n aiops-e2e -o yaml | grep -A 5 -B 5 "APP_BOOT_MODE"
```
*注意*：Secret 中的值是 Base64 编码，需解码查看：
```bash
kubectl get secret <secret-name> -n aiops-e2e -o jsonpath='{.data.APP_BOOT_MODE}' | base64 --decode
```

**3. [可选] 查看 Pod 的完整 YAML，确认环境变量注入路径**
```bash
kubectl get pod appconfigfail-7649c79dc5-q4zjz -n aiops-e2e -o yaml | grep -A 20 -B 20 "env\|envFrom\|APP_BOOT_MODE"
```

**4. [可选] 查看容器日志（如能采集）**
```bash
kubectl logs appconfigfail-7649c79dc5-q4zjz -n aiops-e2e --previous | grep -A 10 -B 10 "APP_BOOT_MODE"
```

### 后续优化
1. **标准化配置注入**：为所有应用定义环境变量清单（如 `env-var-checklist.yaml`），避免遗漏
2. **启动探针增强**：增加 `exec` 探针检查 `env APP_BOOT_MODE` 是否存在
3. **CI/CD 验证**：在部署前使用 `yq` 或 `helm template` 验证模板中是否包含所有必需变量
4. **配置审计**：定期检查所有 Deployment 是否引用了存在的 ConfigMap/Secret

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 修复后重新部署 | `kubectl rollout restart deployment/appconfigfail -n aiops-e2e` | Pod 重启，状态变为 `Running` |
| 2. 检查重启次数 | `kubectl get pod appconfigfail-7649c79dc5-q4zjz -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 重启次数不再增加（稳定在新值） |
| 3. 检查就绪状态 | `kubectl get pod appconfigfail-7649c79dc5-q4zjz -n aiops-e2e` | `READY` 列显示 `1/1` |
| 4. 验证环境变量 | `kubectl exec appconfigfail-7649c79dc5-q4zjz -n aiops-e2e -- env \| grep APP_BOOT_MODE` | 输出：`APP_BOOT_MODE=production`（或正确值） |

---
## ⚠️ 注意事项
- **切勿直接修改 Pod**：所有变更必须通过 Deployment 更新，否则会被控制器覆盖
- **避免键名拼写错误**：`APP_BOOT_MODE` 与 `APP_BOOT_MODES`、`app_boot_mode` 均为不同变量
- **Secret 解码陷阱**：Secret 中的值必须为 Base64 编码，手动编辑时使用 `echo -n "value" \| base64` 生成
- **若使用 Helm**：运行 `helm get values appconfigfail -n aiops-e2e` 检查是否在 values 中遗漏了该变量

> **当前诊断受限于证据采集失败**，建议立即手动执行上述修复命令，优先确认 ConfigMap/Secret 内容，这是最可能的根因。

---

## 📊 性能统计

├─ 总耗时: 3.5m
├─ 问题定位: 34.3s (16%) ✅
├─ 证据链采集: 39.4s (19%) ✅
├─ 根因分析: 65.9s (31%) ✅
├─ 汇总总结: 73.2s (34%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 5 次
```

📋 诊断追踪

- **参考 Runbook**: private-k8s-health-reference, l4-config-bootstrap-fail
- **工具调用**: 5 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
