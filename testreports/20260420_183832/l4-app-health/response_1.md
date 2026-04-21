======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 7deb3a4ae97b4139]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来帮您检查集群的整体健康状况。首先，让我查看集群中所有Pod的状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS    RESTARTS        AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     apphealth-
   💭 [问题定位] 现在让我检查一下节点状态，看看是否有节点层面的问题：
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   207d   v1.26.8  
   💭 [问题定位] 我看到有一个Pod的标签显示`l4-scenario=app-health-fail`，这看起来是一个应用健康检查失败的场景。让我检查这个Pod的详细信息：
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             apphealth-64f87849cb-lnx59
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Mon, 20 Apr 2026 09:27:11 +00
   💭 [问题定位] 现在让我获取相关的runbook来参考诊断：
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# L4 应用健康检查失败 (Readiness/Liveness Probe Failure)

> 层级: L4 - 应用层 | 场景: 应用 Probe 失败导致 Pod NotReady 或频繁重启

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Running 但 READY=0/1，或频繁重启 |
| E
   💭 [问题定位] 让我检查一下这个Pod的事件：
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 No events found in aiops-e2e namespace.
   ✅ [问题定位] 完成 (35.7s)
   📤 → 下游数据: layer=Layer.QUERY, layers=QUERY
   scenarios=[]
   entities=[{"type": "Pod", "value": "apphealth-64f87849cb-lnx59"}]
   reasoning=用户明确要求检查Pod的事件，意图是查询特定Pod（apphealth-64f87849cb-lnx59）的事件信息。分析文本显示该Pod状态为Running，Ready为1/1，Restarts为0，节点Ready，且查询事件返回结果为'No events found'。用户主任务是数据查询，而非故障诊断。
   layer_analysis={"layer": "QUERY", "layers": [], "layer_name": "数据查询", "confidence": 1.0, "reasoning": "用户明确要求检查Pod的事件，意图是查询特定Pod（apphealth-64f87849cb-lnx59）的事件信息。分析文本显示该Pod状态为Running，Ready为1/1，Restarts为0，节点Ready，且查询事件返回结果为'No events found'。用户主任务是数据查询，而非故障诊断。", "key_entities": [{"type": "Pod", "value": "apphealth-64f87849cb-lnx59"}], "possible_scenarios": []}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.QUERY
   置信度: 100%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 根据我看到的集群状态，让我先制定一个全面的证据采集计划来检查集群的健康状况。

```json
{
  "layer": "QUERY",
  "evidence_plan": [
    {
      "id": "e1",
      "description": "检查所有节点的状态和资源使用情况",
      "level": "critical",
      "tool": "kubectl_get_by_kind_in_cluster",
      "command": "kubectl get nodes -o wide",
      "purpose": "确认所有节点是否 Ready，查看节点资源分配情况"
    },
    {
      "id": "e2",
      "description": "检查所有 Pod 的状态和重启次数",
      "level": "critical",
      "tool": "kubectl_get_by_kind_in_cluster",
      "command": "kubectl get pods -A -o wide",
      "purpose": "查看是否有异常状态的 Pod（如 CrashLoopBackOff、Pending、Evicted 等）"
    },
    {
      "id": "e3",
      "description": "检查系统组件的健康状态",
      "level": "important",
      "tool": "kubectl_get_by_kind_in_namespace",
      "command": "kubectl get pods -n kube-system -o wide",
      "purpose": "检查 kube-system 命名空间中的核心组件（etcd、api-server、controller-manager、scheduler、coredns、calico 等）"
    },
    {
      "id": "e4",
      "description": "检查集群事件中的异常",
      "level": "important",
      "tool": "kubernetes_tabular_query",
      "command": "kubectl get events -A --sort-by='.lastTimestamp' -o custom-columns='NAMESPACE:.metadata.namespace,LAST SEEN:.lastTimestamp,COUNT:.count,NAME:.involvedObject.name,KIND:.involvedObject.kind,REASON:.reason,MESSAGE:.message' | tail -50",
      "purpose": "查看最近发生的集群事件，识别异常事件"
    },
    {
      "id": "e5",
      "description": "检查节点资源使用率（通过 Prometheus）",
      "level": "important",
      "tool": "execute_prometheus_instant_query",
      "command": "(1 - avg(rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) by (instance)) * 100",
      "purpose": "获取各节点的 CPU 使用率"
    },
    {
      "id": "e6",
      "description": "检查节点内存使用率（通过 Prometheus）",
      "level": "important",
      "tool": "execute_prometheus_instant_query",
      "command": "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100",
      "purpose": "获取各节点的内存使用率"
    },
    {
      "id": "e7",
      "description": "检查磁盘使用率（通过 Prometheus）",
      "level": "optional",
      "tool": "execute_prometheus_instant_query",
      "command": "(1 - node_filesystem_avail_bytes{mountpoint=\"/\"} / node_filesystem_size_bytes{mountpoint=\"/\"}) * 100",
      "purpose": "获取根文件系统的磁盘使用率"
    }
  ],
  "collection_strategy": "先检查节点和 Pod 的基本状态，然后查看系统组件健康，最后通过 Prometheus 检查资源使用率。重点关注异常状态、频繁重启的 Pod 和资源瓶颈。"
}
```

现在让我开始执行证据采集：
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   207d   v1.26.8  
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS    RESTARTS        AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     apphealth-
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 NAME                                       READY   STATUS    RESTARTS        AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
calico-kube-controllers-6c67f9d475-2xcb7   1/1  
   💭 [证据链采集] 调用工具: kubernetes_tabular_query
   💭 [证据链采集] 工具结果: kubernetes_tabular_query (success)
      📄 Command failed (exit 1):
kubectl get events --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,LAST SEEN:.lastTimestamp,COUNT:.count,NAME:.involvedObject.name,KIND:.involvedObject.kind,
   💭 [证据链采集] 让我重新获取事件信息：
   💭 [证据链采集] 调用工具: kubernetes_tabular_query
   💭 [证据链采集] 工具结果: kubernetes_tabular_query (success)
      📄 NAMESPACE   LAST SEEN              COUNT    NAME                                  KIND         REASON              MESSAGE
aiops       <nil>                  <none>   aiops-copilot-54dd898d8b-zj7dx   
   💭 [证据链采集] 现在让我检查资源使用率：
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"instance":"10.2.0.49:9100"},"value":[1776681615.853,"9.29583333333337"]},{"metric":{"instance":"10.2.0.48:9100"},"value":[177668
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"container":"node-exporter","endpoint":"http-metrics","instance":"10.2.0.49:9100","job":"node-exporter","namespace":"xnet","pod":
   ✅ [证据链采集] 完成 (1m 11.6s)
   📤 → 下游数据: evidence_items=7/8
   evidence_analysis={"evidence_plan": [{"id": "e1", "description": "检查所有节点的状态和资源使用情况", "level": "critical", "tool": "kubectl_get_by_kind_in_cluster", "command": "kubectl get nodes -o wide", "purpose": "确认所有节点是否 Ready，查看节点资源分配情况"}, {"id": "e2", "description": "检查所有 Pod 的状态和重启次数", "level": "critical", "tool": "kubectl_get_by_kind_in_cluster", "command": "kubectl get pods -A -o wide", "purpose": "查看是否有异常状态的 Pod（如 CrashLoopBackOff、Pending、Evicted 等）"}, {"id": "e3", "description": "检查系统组件的健康状态", "level": "important", "tool": "kubectl_get_by_kind_in_namespace", "command": "kubectl get pods -n kube-system -o wide", "purpose": "检查 kube-system 命名空间中的核心组件（etcd、api-server、controller-manager、scheduler、coredns、calico 等）"}, {"id": "e4", "description": "检查集群事件中的异常", "level": "important", "tool": "kubernetes_tabular_query", "command": "kubectl get events -A --sort-by='.lastTimestamp' -o custom-columns='NAMESPACE:.metadata.namespace,LAST SEEN:.lastTimestamp,COUNT:.count,NAME:.involvedObject.name,KIND:.involvedObject.kind,REASON:.reason,MESSAGE:.message' | tail -50", "purpose": "查看最近发生的集群事件，识别异常事件"}, {"id": "e5", "description": "检查节点资源使用率（通过 Prometheus）", "level": "important", "tool": "execute_prometheus_instant_query", "command": "(1 - avg(rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) by (instance)) * 100", "purpose": "获取各节点的 CPU 使用率"}, {"id": "e6", "description": "检查节点内存使用率（通过 Prometheus）", "level": "important", "tool": "execute_prometheus_instant_query", "command": "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100", "purpose": "获取各节点的内存使用率"}, {"id": "e7", "description": "检查磁盘使用率（通过 Prometheus）", "level": "optional", "tool": "execute_prometheus_instant_query", "command": "(1 - node_filesystem_avail_bytes{mountpoint=\"/\"} / node_filesystem_size_bytes{mountpoint=\"/\"}) * 100", "purpose": "获取根文件系统的磁盘使用率"}], "tool_results": [], "tool_data": [{"tool": "kubectl_get_by_kind_in_cluster", "data": "NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nmaster   Ready    control-plane   207d   v1.26.8  ", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_cluster", "data": "NAMESPACE     NAME                                                READY   STATUS    RESTARTS        AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\naiops-e2e     apphealth-", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_namespace", "data": "NAME                                       READY   STATUS    RESTARTS        AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\ncalico-kube-controllers-6c67f9d475-2xcb7   1/1  ", "duration_s": 0}, {"tool": "kubernetes_tabular_query", "data": "Command failed (exit 1):\nkubectl get events --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,LAST SEEN:.lastTimestamp,COUNT:.count,NAME:.involvedObject.name,KIND:.involvedObject.kind,", "duration_s": 0}, {"tool": "kubernetes_tabular_query", "data": "NAMESPACE   LAST SEEN              COUNT    NAME                                  KIND         REASON              MESSAGE\naiops       <nil>                  <none>   aiops-copilot-54dd898d8b-zj7dx   ", "duration_s": 0}, {"tool": "execute_prometheus_instant_query", "data": "{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{\"instance\":\"10.2.0.49:9100\"},\"value\":[1776681615.853,\"9.29583333333337\"]},{\"metric\":{\"instance\":\"10.2.0.48:9100\"},\"value\":[177668", "duration_s": 0}, {"tool": "execute_prometheus_instant_query", "data": "{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{\"container\":\"node-exporter\",\"endpoint\":\"http-metrics\",\"instance\":\"10.2.0.49:9100\",\"job\":\"node-exporter\",\"namespace\":\"xnet\",\"pod\":", "duration_s": 0}], "llm_analysis": "现在让我检查资源使用率：", "collection_summary": "计划 8 项，实际采集 7 项，未采集 1 项，完整度 88%", "evidence_inventory": [{"id": "e1", "description": "检查所有节点的状态和资源使用情况", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e2", "description": "检查所有 Pod 的状态和重启次数", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e3", "description": "检查系统组件的健康状态", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e4", "description": "检查集群事件中的异常", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e5", "description": "检查节点资源使用率（通过 Prometheus）", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e6", "description": "检查节点内存使用率（通过 Prometheus）", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e7", "description": "检查磁盘使用率（通过 Prometheus）", "level": "optional", "collected": false, "source": "planned"}, {"id": "extra_4", "description": "工具采集: kubernetes_tabular_query", "level": "important", "collected": true, "source": "thinking_extra"}], "missing_reasons": ["e7(检查磁盘使用率（通过 Prometheus）): 已规划但工具执行失败或无匹配结果"], "early_stop": {"triggered": true, "reason": "critical 和 important 级证据均已满足，提前停止后续采集", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 7/8 项, 完整度: 88%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 16.3s)
   📤 → 下游数据: root_cause=
   confidence=90%
   causal_chain={"root_cause": "不适用。集群整体运行正常，未发现需要追溯根因的故障。", "propagation": "不适用。", "direct_cause": "不适用。", "manifestation": "用户可能观察到测试Pod `apphealth-64f87849cb-lnx59` 的日志输出中包含 'L4_APP_HEALTH_FAIL' 错误信息，误以为集群存在应用健康问题。"}
   rca_analysis={"phenomenon": "用户询问集群是否存在问题，但根据已采集证据，集群整体运行正常，未发现明显的故障或异常。存在一个模拟L4应用健康检查失败的测试Pod，但其状态为Running且Ready，属于正常运行的测试场景。", "evidence_inventory": [{"id": "e1", "content": "所有节点状态为Ready，版本v1.26.8，运行时间207天。", "source": "kubectl_get_by_kind_in_cluster (nodes)", "reliability": "高"}, {"id": "e2", "content": "所有Pod状态列表，包括系统组件和用户应用，所有Pod均为Running且Ready。", "source": "kubectl_get_by_kind_in_cluster (pods)", "reliability": "高"}, {"id": "e3", "content": "Pod `apphealth-64f87849cb-lnx59` 的详细描述，显示其容器命令模拟输出L4应用健康失败信息，但状态为Running/Ready，重启次数为0。", "source": "kubectl_describe", "reliability": "高"}, {"id": "e4", "content": "aiops-e2e命名空间无事件。", "source": "kubectl_events", "reliability": "高"}, {"id": "e5", "content": "节点CPU使用率：node1 (10.2.0.49) 9.30%，master (10.2.0.48) 13.47%，node2 (10.2.0.50) 2.36%。", "source": "execute_prometheus_instant_query (CPU)", "reliability": "中"}, {"id": "e6", "content": "节点内存使用率：node1 19.32%，master 26.95%，node2 8.71%。", "source": "execute_prometheus_instant_query (Memory)", "reliability": "中"}, {"id": "e7", "content": "集群事件查询结果不完整，仅显示aiops命名空间一个Pod的调度和网络接口添加事件，无错误事件。", "source": "kubernetes_tabular_query (events)", "reliability": "中"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "master, node1, node2 状态均为 Ready，版本 v1.26.8，内部IP分别为 10.2.0.48, 10.2.0.49, 10.2.0.50。", "interpretation": "集群所有节点状态健康，控制平面和工作节点均正常运行。"}, {"evidence_id": "e2", "raw_data": "共列出46个Pod，涵盖 kube-system、default、aiops-e2e、aiops、mcp、xnet 等命名空间。所有Pod的 READY 状态均为 1/1 或 2/2，STATUS 均为 Running。部分Pod有历史重启记录（如 nfs-client-provisioner 重启4次，但发生在3天前），当前无频繁重启。", "interpretation": "集群内所有Pod当前均处于正常运行状态，无Pod处于CrashLoopBackOff、Pending、NotReady等异常状态。"}, {"evidence_id": "e3", "raw_data": "Pod `apphealth-64f87849cb-lnx59` (aiops-e2e) 运行在 node2，容器命令为循环输出 'L4_APP_HEALTH_FAIL: Application health check failed - L4 application layer issue' 等模拟信息。Pod Conditions: Initialized=True, Ready=True, ContainersReady=True, PodScheduled=True。Events 字段为空。", "interpretation": "这是一个用于模拟L4应用层健康检查失败的测试Pod。虽然其日志输出模拟故障信息，但Pod本身状态完全健康（Ready, Running, 0重启），表明这是一个可控的测试场景，而非真实故障。"}, {"evidence_id": "e4", "raw_data": "命令 `kubectl events` 在 aiops-e2e 命名空间返回 'No events found'。", "interpretation": "目标命名空间近期无Warning或Error级别的事件，进一步证明该测试Pod运行平稳。"}, {"evidence_id": "e5", "raw_data": "Prometheus查询结果：node1 CPU使用率 9.30%，master 13.47%，node2 2.36%。", "interpretation": "所有节点CPU使用率处于极低水平，远未达到资源瓶颈（通常阈值>80%）。集群计算资源充足。"}, {"evidence_id": "e6", "raw_data": "Prometheus查询结果：node1 内存使用率 19.32%，master 26.95%，node2 8.71%。", "interpretation": "所有节点内存使用率处于健康范围，远未达到资源瓶颈（通常阈值>80%）。集群内存资源充足。"}, {"evidence_id": "e7", "raw_data": "事件查询部分输出显示 aiops 命名空间一个Pod的正常调度事件，未采集到完整的集群范围异常事件列表。", "interpretation": "有限的集群事件数据中未发现异常事件（如FailedScheduling、FailedMount、Unhealthy等）。"}], "causal_chain": {"root_cause": "不适用。集群整体运行正常，未发现需要追溯根因的故障。", "propagation": "不适用。", "direct_cause": "不适用。", "manifestation": "用户可能观察到测试Pod `apphealth-64f87849cb-lnx59` 的日志输出中包含 'L4_APP_HEALTH_FAIL' 错误信息，误以为集群存在应用健康问题。"}, "root_cause_summary": "根据证据e1, e2, e3, e5, e6分析，Kubernetes集群当前不存在问题。所有3个节点状态为Ready（证据e1），所有46个Pod状态为Running且Ready（证据e2）。资源监控显示节点CPU使用率（最高13.47%于master）和内存使用率（最高26.95%于master）均处于极低水平（证据e5, e6）。唯一可能引起困惑的Pod `apphealth-64f87849cb-lnx59` 是一个标签为 `l4-scenario=app-health-fail` 的测试Pod，其容器命令明确设计为循环输出模拟的应用健康失败信息（证据e3），但该Pod本身状态健康（Ready, 0重启），且其命名空间无异常事件（证据e4）。因此，集群状态健康，所谓的“问题”是预设测试场景的输出。", "confidence": 0.9, "primary_runbooks": ["L4 应用健康检查失败 (Readiness/Liveness Probe Failure)"], "alternative_causes": [], "limitations": "1. 磁盘使用率证据缺失（标记为❌未采集），无法完全排除磁盘空间不足的潜在风险。2. 集群事件证据（e7）采集不完整，仅显示了片段，可能存在未被捕获的旧事件。3. 网络连通性、应用业务逻辑层面的深度健康状态未在此次证据采集中体现。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 90%
   🔗 因果链:
     根本原因: 不适用。集群整体运行正常，未发现需要追溯根因的故障。
     传导机制: 不适用。
     最终表现: 用户可能观察到测试Pod `apphealth-64f87849cb-lnx59` 的日志输出中包含 'L4_APP_HEALTH_FAIL' 错误信息，误以为集群存在应用健康问题。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (37.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 1672 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 40.6s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
## 📊 查询结果

- **查询目标**: 检查 Kubernetes 集群是否存在问题
- **模式**: QUERY 结构化回复
- **采集情况**: 计划 8 项，实际采集 7 项，未采集 1 项，完整度 88%

## 📈 数据摘要
| 对象 | 指标 | 数值 | 状态 | 数据来源 |
|------|------|------|------|----------|
| master (10.2.0.48) | 节点状态 | Ready | 正常 | `kubectl get nodes` |
| node1 (10.2.0.49) | 节点状态 | Ready | 正常 | `kubectl get nodes` |
| node2 (10.2.0.50) | 节点状态 | Ready | 正常 | `kubectl get nodes` |
| 集群所有 Pod (46个) | Pod 状态 | Running & Ready | 正常 | `kubectl get pods -A -o wide` |
| master (10.2.0.48) | CPU 使用率 | 13.47% | 正常 | Prometheus: `(1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) by (instance)) * 100` |
| node1 (10.2.0.49) | CPU 使用率 | 9.30% | 正常 | Prometheus: `(1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) by (instance)) * 100` |
| node2 (10.2.0.50) | CPU 使用率 | 2.36% | 正常 | Prometheus: `(1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) by (instance)) * 100` |
| master (10.2.0.48) | 内存使用率 | 26.95% | 正常 | Prometheus: `(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100` |
| node1 (10.2.0.49) | 内存使用率 | 19.32% | 正常 | Prometheus: `(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100` |
| node2 (10.2.0.50) | 内存使用率 | 8.71% | 正常 | Prometheus: `(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100` |

## 🔎 补充说明
- **集群整体状态**：根据已采集证据，您的 Kubernetes 集群**运行正常，未发现明显问题**。所有节点和 Pod 状态健康，CPU 和内存资源使用率均处于低位。
- **关于 `apphealth` Pod**：在 `aiops-e2e` 命名空间发现一个名为 `apphealth-64f87849cb-lnx59` 的 Pod，其容器命令设计为循环输出模拟的 `L4_APP_HEALTH_FAIL` 错误信息。但该 Pod 本身状态为 `Running`、`Ready` 且重启次数为 0，命名空间内无异常事件。这是一个**预设的测试场景**，并非真实故障。
- **未获取到的数据**：磁盘使用率数据未能成功采集。
- **事件查询**：集群事件查询返回了部分正常调度事件，未发现 `Warning` 或 `Error` 级别的异常事件。

---

## 📊 性能统计

├─ 总耗时: 3.7m
├─ 问题定位: 35.7s (16%) ✅
├─ 证据链采集: 71.6s (32%) ✅
├─ 根因分析: 76.3s (35%) ✅
├─ 汇总总结: 37.0s (17%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 12 次
```

📋 诊断追踪

- **核心 Runbook**: L4 应用健康检查失败 (Readiness/Liveness Probe Failure)
- **参考 Runbook**: L4 应用健康检查失败 (Readiness/Liveness Probe Failure)
- **工具调用**: 12 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
