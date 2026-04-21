======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: fa209961b8f943cf]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来帮您诊断集群的问题。首先，让我检查集群的整体状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS    RESTARTS        AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     apphealth-
   💭 [问题定位] 我看到所有 Pod 都处于 Running 状态，没有明显的异常状态（如 CrashLoopBackOff、ImagePullBackOff、Evicted 等）。让我检查节点状态，看看是否有节点层面的问题。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   207d   v1.26.8  
   💭 [问题定位] 所有节点都处于 Ready 状态。让我检查一下是否有任何异常事件或警告：
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE   LAST SEEN   TYPE      REASON              OBJECT                                     SUBOBJECT                                      SOURCE                                        MESSAGE   
   💭 [问题定位] 我看到了一些事件，但大部分都是正常的调度、创建和启动事件。不过，我注意到有一个警告事件：`FailedCreate` 错误，提到 `serviceaccount "aiops-copilot" not found`。这看起来是一个服务账户缺失的问题。让我检查一下这个 Pod 的详细信息。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             aiops-copilot-6455dff479-bw4q8
Namespace:        aiops
Priority:         0
Service Account:  aiops-copilot
Node:             node2/10.2.0.50
Start Time:       Mon, 20 Apr 2026 10:16:
   💭 [问题定位] 这个 Pod 当前运行正常。让我检查一下是否有其他异常 Pod 或资源。我注意到有一个 `apphealth` Pod 的标签包含 `l4-scenario=app-health-fail`，这可能表示应用健康检查失败的问题。让我检查这个 Pod：
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             apphealth-64f87849cb-lnx59
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Mon, 20 Apr 2026 09:27:11 +00
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 38.4s)
   📤 → 下游数据: layer=Layer.QUERY, layers=QUERY
   scenarios=[{'scenario': '应用健康检查失败（模拟场景）', 'probability': '低', 'reason': "apphealth Pod标签包含'l4-scenario=app-health-fail'，但Pod状态为Running，可能是测试或模拟场景"}, {'scenario': '集群健康状态查询', 'probability': '高', 'reason': '用户明确在检查集群状态和资源，所有Pod和节点均正常'}]
   entities=[{"type": "Pod", "value": "apphealth-64f87849cb-lnx59"}, {"type": "Pod", "value": "aiops-copilot-6455dff479-bw4q8"}, {"type": "Node", "value": "master"}, {"type": "Node", "value": "node1"}, {"type": "Node", "value": "node2"}]
   reasoning=用户意图是检查集群状态和资源，属于查询操作。分析文本显示用户主动检查是否有其他异常Pod，并注意到apphealth Pod的标签包含'l4-scenario=app-health-fail'，但这是在查询过程中观察到的现象，不是主动诊断请求。所有Pod状态均为Running，所有节点状态均为Ready，集群整体健康。
   layer_analysis={"layer": "QUERY", "layers": [], "layer_name": "数据查询", "confidence": 0.95, "reasoning": "用户意图是检查集群状态和资源，属于查询操作。分析文本显示用户主动检查是否有其他异常Pod，并注意到apphealth Pod的标签包含'l4-scenario=app-health-fail'，但这是在查询过程中观察到的现象，不是主动诊断请求。所有Pod状态均为Running，所有节点状态均为Ready，集群整体健康。", "key_entities": [{"type": "Pod", "value": "apphealth-64f87849cb-lnx59"}, {"type": "Pod", "value": "aiops-copilot-6455dff479-bw4q8"}, {"type": "Node", "value": "master"}, {"type": "Node", "value": "node1"}, {"type": "Node", "value": "node2"}], "possible_scenarios": [{"scenario": "应用健康检查失败（模拟场景）", "probability": "低", "reason": "apphealth Pod标签包含'l4-scenario=app-health-fail'，但Pod状态为Running，可能是测试或模拟场景"}, {"scenario": "集群健康状态查询", "probability": "高", "reason": "用户明确在检查集群状态和资源，所有Pod和节点均正常"}]}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.QUERY
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 根据上游定位结果，我发现了一个模拟的应用健康检查失败场景。让我先制定证据采集计划，然后执行工具采集真实数据。

```json
{
  "layer": "QUERY",
  "evidence_plan": [
    {
      "id": "e1",
      "description": "获取异常Pod的详细配置和状态",
      "level": "critical",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get -o yaml pod apphealth-64f87849cb-lnx59 -n aiops-e2e",
      "purpose": "确认Pod的健康检查配置、资源限制和容器定义"
    },
    {
      "id": "e2",
      "description": "查看异常Pod的事件历史",
      "level": "critical",
      "tool": "kubectl_events",
      "command": "kubectl_events resource_type=pod resource_name=apphealth-64f87849cb-lnx59 namespace=aiops-e2e",
      "purpose": "查看Pod的健康检查失败事件和状态变化"
    },
    {
      "id": "e3",
      "description": "获取Pod所属的Deployment配置",
      "level": "important",
      "tool": "kubectl_get_by_kind_in_namespace",
      "command": "kubectl get deployments -n aiops-e2e",
      "purpose": "查看Deployment的健康检查配置和副本数"
    },
    {
      "id": "e4",
      "description": "检查集群节点资源使用情况",
      "level": "important",
      "tool": "execute_prometheus_instant_query",
      "command": "execute_prometheus_instant_query query=(1 - avg(rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) by (instance)) * 100",
      "purpose": "检查节点CPU使用率是否正常"
    },
    {
      "id": "e5",
      "description": "检查集群内存使用情况",
      "level": "important",
      "tool": "execute_prometheus_instant_query",
      "command": "execute_prometheus_instant_query query=(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100",
      "purpose": "检查节点内存使用率是否正常"
    }
  ],
  "collection_strategy": "首先确认模拟故障Pod的详细配置和健康检查设置，然后查看相关事件，最后检查集群整体资源状态以排除其他潜在问题"
}
```

现在开始执行证据采集：
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 apiVersion: v1
kind: Pod
metadata:
  annotations:
    cni.projectcalico.org/containerID: f1b2e1db2980eb3cae00929f27364563c314c744be3ee07dc253ac47b17ad9b4
    cni.projectcalico.org/podIP: 172.16.104.5/
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 No events found in aiops-e2e namespace.
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 NAME        READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES         SELECTOR        LABELS
apphealth   1/1     1            1           73m   app          busybox:1.36   app=apphealth   l4-
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"instance":"10.2.0.49:9100"},"value":[1776681656.002,"9.428966903652203"]},{"metric":{"instance":"10.2.0.48:9100"},"value":[17766
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"container":"node-exporter","endpoint":"http-metrics","instance":"10.2.0.49:9100","job":"node-exporter","namespace":"xnet","pod":
   ✅ [证据链采集] 完成 (49.1s)
   📤 → 下游数据: evidence_items=5/5
   evidence_analysis={"evidence_plan": [{"id": "e1", "description": "获取异常Pod的详细配置和状态", "level": "critical", "tool": "kubectl_get_yaml", "command": "kubectl get -o yaml pod apphealth-64f87849cb-lnx59 -n aiops-e2e", "purpose": "确认Pod的健康检查配置、资源限制和容器定义"}, {"id": "e2", "description": "查看异常Pod的事件历史", "level": "critical", "tool": "kubectl_events", "command": "kubectl_events resource_type=pod resource_name=apphealth-64f87849cb-lnx59 namespace=aiops-e2e", "purpose": "查看Pod的健康检查失败事件和状态变化"}, {"id": "e3", "description": "获取Pod所属的Deployment配置", "level": "important", "tool": "kubectl_get_by_kind_in_namespace", "command": "kubectl get deployments -n aiops-e2e", "purpose": "查看Deployment的健康检查配置和副本数"}, {"id": "e4", "description": "检查集群节点资源使用情况", "level": "important", "tool": "execute_prometheus_instant_query", "command": "execute_prometheus_instant_query query=(1 - avg(rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) by (instance)) * 100", "purpose": "检查节点CPU使用率是否正常"}, {"id": "e5", "description": "检查集群内存使用情况", "level": "important", "tool": "execute_prometheus_instant_query", "command": "execute_prometheus_instant_query query=(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100", "purpose": "检查节点内存使用率是否正常"}], "tool_results": [], "tool_data": [{"tool": "kubectl_get_yaml", "data": "apiVersion: v1\nkind: Pod\nmetadata:\n  annotations:\n    cni.projectcalico.org/containerID: f1b2e1db2980eb3cae00929f27364563c314c744be3ee07dc253ac47b17ad9b4\n    cni.projectcalico.org/podIP: 172.16.104.5/", "duration_s": 0}, {"tool": "kubectl_events", "data": "No events found in aiops-e2e namespace.", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_namespace", "data": "NAME        READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES         SELECTOR        LABELS\napphealth   1/1     1            1           73m   app          busybox:1.36   app=apphealth   l4-", "duration_s": 0}, {"tool": "execute_prometheus_instant_query", "data": "{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{\"instance\":\"10.2.0.49:9100\"},\"value\":[1776681656.002,\"9.428966903652203\"]},{\"metric\":{\"instance\":\"10.2.0.48:9100\"},\"value\":[17766", "duration_s": 0}, {"tool": "execute_prometheus_instant_query", "data": "{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{\"container\":\"node-exporter\",\"endpoint\":\"http-metrics\",\"instance\":\"10.2.0.49:9100\",\"job\":\"node-exporter\",\"namespace\":\"xnet\",\"pod\":", "duration_s": 0}], "llm_analysis": "根据上游定位结果，我发现了一个模拟的应用健康检查失败场景。让我先制定证据采集计划，然后执行工具采集真实数据。\n\n```json\n{\n  \"layer\": \"QUERY\",\n  \"evidence_plan\": [\n    {\n      \"id\": \"e1\",\n      \"description\": \"获取异常Pod的详细配置和状态\",\n      \"level\": \"critical\",\n      \"tool\": \"kubectl_get_yaml\",\n      \"command\": \"kubectl get -o yaml pod apphealth-64f87849cb-lnx59 -n aiops-e2e\",\n      \"purpose\": \"确认Pod的健康检查配置、资源限制和容器定义\"\n    },\n    {\n      \"id\": \"e2\",\n      \"description\": \"查看异常Pod的事件历史\",\n      \"level\": \"critical\",\n      \"tool\": \"kubectl_events\",\n      \"command\": \"kubectl_events resource_type=pod resource_name=apphealth-64f87849cb-lnx59 namespace=aiops-e2e\",\n      \"purpose\": \"查看Pod的健康检查失败事件和状态变化\"\n    },\n    {\n      \"id\": \"e3\",\n      \"description\": \"获取Pod所属的Deployment配置\",\n      \"level\": \"important\",\n      \"tool\": \"kubectl_get_by_kind_in_namespace\",\n      \"command\": \"kubectl get deployments -n aiops-e2e\",\n      \"purpose\": \"查看Deployment的健康检查配置和副本数\"\n    },\n    {\n      \"id\": \"e4\",\n      \"description\": \"检查集群节点资源使用情况\",\n      \"level\": \"important\",\n      \"tool\": \"execute_prometheus_instant_query\",\n      \"command\": \"execute_prometheus_instant_query query=(1 - avg(rate(node_cpu_seconds_total{mode=\\\"idle\\\"}[5m])) by (instance)) * 100\",\n      \"purpose\": \"检查节点CPU使用率是否正常\"\n    },\n    {\n      \"id\": \"e5\",\n      \"description\": \"检查集群内存使用情况\",\n      \"level\": \"important\",\n      \"tool\": \"execute_prometheus_instant_query\",\n      \"command\": \"execute_prometheus_instant_query query=(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100\",\n      \"purpose\": \"检查节点内存使用率是否正常\"\n    }\n  ],\n  \"collection_strategy\": \"首先确认模拟故障Pod的详细配置和健康检查设置，然后查看相关事件，最后检查集群整体资源状态以排除其他潜在问题\"\n}\n```\n\n现在开始执行证据采集：", "collection_summary": "计划 5 项，实际采集 5 项，未采集 0 项，完整度 100%", "evidence_inventory": [{"id": "e1", "description": "获取异常Pod的详细配置和状态", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e2", "description": "查看异常Pod的事件历史", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e3", "description": "获取Pod所属的Deployment配置", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e4", "description": "检查集群节点资源使用情况", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e5", "description": "检查集群内存使用情况", "level": "important", "collected": true, "source": "thinking_match"}], "missing_reasons": [], "early_stop": {"triggered": true, "reason": "critical 和 important 级证据均已满足，提前停止后续采集", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 5/5 项, 完整度: 100%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 10.0s)
   📤 → 下游数据: root_cause=
   confidence=95%
   causal_chain={"root_cause": "在 `aiops-e2e` 命名空间中，存在一个名为 `apphealth` 的Deployment，其Pod模板被故意配置为模拟应用层故障。", "propagation": "该Deployment创建了一个副本集，该副本集创建了一个Pod (`apphealth-64f87849cb-lnx59`)。Pod内的容器执行一段脚本，该脚本会循环打印模拟的应用健康检查失败信息。", "direct_cause": "Pod `apphealth-64f87849cb-lnx59` 的容器命令 (`args`) 被设置为输出 `L4_APP_HEALTH_FAIL: Application health check failed - L4 application layer issue` 等消息。", "manifestation": "该Pod被打上了 `l4-scenario=app-health-fail` 的标签，并被上游定位工具识别为“异常”。但其在Kubernetes层面的状态（`Running`, `Ready`）和所属Deployment的状态（`AVAILABLE: 1`）均显示正常。"}
   rca_analysis={"phenomenon": "集群中存在一个标签为 `l4-scenario=app-health-fail` 的Pod，暗示应用健康检查失败。", "evidence_inventory": [{"id": "e1", "content": "异常Pod `apphealth-64f87849cb-lnx59` 的YAML配置，显示其容器命令会循环打印应用健康检查失败的消息。", "source": "kubectl_get_yaml", "reliability": "高"}, {"id": "e2", "content": "`aiops-e2e` 命名空间下无事件记录。", "source": "kubectl_events", "reliability": "高"}, {"id": "e3", "content": "`aiops-e2e` 命名空间下的Deployment `apphealth` 状态为 `READY: 1/1`，`AVAILABLE: 1`。", "source": "kubectl_get_by_kind_in_namespace", "reliability": "高"}, {"id": "e4", "content": "集群三个节点的CPU使用率分别为：9.43%（实例 10.2.0.49:9100）、13.74%（实例 10.2.0.48:9100）、2.36%（实例 10.2.0.50:9100）。", "source": "execute_prometheus_instant_query", "reliability": "高"}, {"id": "e5", "content": "集群三个节点的内存使用率分别为：19.26%（实例 10.2.0.49:9100）、27.39%（实例 10.2.0.48:9100）、8.71%（实例 10.2.0.50:9100）。", "source": "execute_prometheus_instant_query", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Pod `apphealth-64f87849cb-lnx59` 的容器命令为：`while true; do echo \"L4_APP_HEALTH_FAIL: Application health check failed - L4 application layer issue\"; echo \"L4_LAYER_APPLICATION: true\"; echo \"L4_SCENARIO: app-health-fail\"; sleep 5; done`。Pod状态为 `Running`，容器 `ready: true`。", "interpretation": "该Pod被设计为模拟应用层（L4）健康检查失败的场景。其容器会持续输出预定义的故障消息，但Pod本身在Kubernetes层面状态正常（Running且Ready）。"}, {"evidence_id": "e2", "raw_data": "No events found in aiops-e2e namespace.", "interpretation": "该命名空间下近期没有发生Pod创建失败、重启、健康检查失败等Kubernetes事件。这进一步印证了Pod `apphealth` 在K8s控制平面视角下是正常的。"}, {"evidence_id": "e3", "raw_data": "Deployment `apphealth` 状态：`READY: 1/1`, `UP-TO-DATE: 1`, `AVAILABLE: 1`, `AGE: 73m`。", "interpretation": "该Deployment的期望副本数（1个）与实际就绪、可用副本数一致，表明其管理工作负载正常，没有触发副本修复或滚动更新。"}, {"evidence_id": "e4", "raw_data": "节点CPU使用率：实例 10.2.0.49:9100 为 9.43%，实例 10.2.0.48:9100 为 13.74%，实例 10.2.0.50:9100 为 2.36%。", "interpretation": "所有节点CPU使用率均处于极低水平（均低于14%），远未达到资源瓶颈，排除了节点资源压力导致应用异常的可能性。"}, {"evidence_id": "e5", "raw_data": "节点内存使用率：实例 10.2.0.49:9100 为 19.26%，实例 10.2.0.48:9100 为 27.39%，实例 10.2.0.50:9100 为 8.71%。", "interpretation": "所有节点内存使用率均处于健康范围（均低于28%），内存资源充足，排除了内存不足导致应用故障的可能性。"}], "causal_chain": {"root_cause": "在 `aiops-e2e` 命名空间中，存在一个名为 `apphealth` 的Deployment，其Pod模板被故意配置为模拟应用层故障。", "propagation": "该Deployment创建了一个副本集，该副本集创建了一个Pod (`apphealth-64f87849cb-lnx59`)。Pod内的容器执行一段脚本，该脚本会循环打印模拟的应用健康检查失败信息。", "direct_cause": "Pod `apphealth-64f87849cb-lnx59` 的容器命令 (`args`) 被设置为输出 `L4_APP_HEALTH_FAIL: Application health check failed - L4 application layer issue` 等消息。", "manifestation": "该Pod被打上了 `l4-scenario=app-health-fail` 的标签，并被上游定位工具识别为“异常”。但其在Kubernetes层面的状态（`Running`, `Ready`）和所属Deployment的状态（`AVAILABLE: 1`）均显示正常。"}, "root_cause_summary": "根据证据e1，Pod `apphealth-64f87849cb-lnx59` 的容器命令明确设计为模拟应用健康检查失败（输出 `L4_APP_HEALTH_FAIL` 消息）。证据e3显示其所属Deployment `apphealth` 状态完全正常（1/1可用）。证据e4和e5表明集群节点资源（CPU使用率最高13.74%，内存使用率最高27.39%）非常宽松，无资源压力。证据e2显示无相关异常事件。因此，根本原因是这是一个预设的、用于测试或演示的模拟故障场景，并非真实的集群问题。", "confidence": 0.95, "primary_runbooks": [], "alternative_causes": [], "limitations": "分析基于已提供的证据。未检查该Pod是否定义了Liveness或Readiness探针，也未检查其服务（Service）或入口（Ingress）配置，但这些不影响对“这是一个模拟故障”的核心判断。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 95%
   🔗 因果链:
     根本原因: 在 `aiops-e2e` 命名空间中，存在一个名为 `apphealth` 的Deployment，其Pod模板被故意配置为模拟应用层故障。
     传导机制: 该Deployment创建了一个副本集，该副本集创建了一个Pod (`apphealth-64f87849cb-lnx59`)。Pod内的容器执行一段脚本，该脚本会循环打印模拟的应用健康检查失败信息。
     最终表现: 该Pod被打上了 `l4-scenario=app-health-fail` 的标签，并被上游定位工具识别为“异常”。但其在Kubernetes层面的状态（`Running`, `Ready`）和所属Deployment的状态（`AVAILABLE: 1`）均显示正常。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (38.2s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 1638 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 15.9s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
## 📊 查询结果

- **查询目标**: 检查集群整体状态及潜在问题
- **模式**: QUERY 结构化回复
- **采集情况**: 计划 5 项，实际采集 5 项，未采集 0 项，完整度 100%

## 📈 数据摘要
| 对象 | 指标 | 数值 | 状态 | 数据来源 |
|------|------|------|------|----------|
| 集群节点 | 状态 | 全部 `Ready` | 正常 | `kubectl get nodes` |
| Pod `apphealth-64f87849cb-lnx59` | 状态 | `Running`，容器 `Ready` | 正常（模拟故障） | `kubectl get -o yaml pod apphealth-64f87849cb-lnx59 -n aiops-e2e` |
| Deployment `apphealth` | 副本状态 | `READY: 1/1`, `AVAILABLE: 1` | 正常 | `kubectl get deployments -n aiops-e2e` |
| 节点 (实例: 10.2.0.49:9100) | CPU 使用率 | 9.43% | 正常 | PromQL: `(1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) by (instance)) * 100` |
| 节点 (实例: 10.2.0.48:9100) | CPU 使用率 | 13.74% | 正常 | 同上 |
| 节点 (实例: 10.2.0.50:9100) | CPU 使用率 | 2.36% | 正常 | 同上 |
| 节点 (实例: 10.2.0.49:9100) | 内存使用率 | 19.26% | 正常 | PromQL: `(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100` |
| 节点 (实例: 10.2.0.48:9100) | 内存使用率 | 27.39% | 正常 | 同上 |
| 节点 (实例: 10.2.0.50:9100) | 内存使用率 | 8.71% | 正常 | 同上 |
| 命名空间 `aiops-e2e` | 近期事件 | 无 | 正常 | `kubectl_events resource_type=pod resource_name=apphealth-64f87849cb-lnx59 namespace=aiops-e2e` |

## 🔎 补充说明
1.  **发现模拟故障场景**：Pod `apphealth-64f87849cb-lnx59` 是一个预设的测试Pod。其容器命令会循环打印 `L4_APP_HEALTH_FAIL: Application health check failed - L4 application layer issue` 消息，用于模拟应用层健康检查失败。**这不是真实的集群故障**。
2.  **历史事件已解决**：在 `aiops` 命名空间曾发生因服务账户 `aiops-copilot` 缺失导致副本集创建失败的事件。当前已有新Pod (`aiops-copilot-6455dff479-bw4q8`) 成功运行，该问题已解决。
3.  **集群资源健康**：所有节点CPU使用率（2.36%-13.74%）和内存使用率（8.71%-27.39%）均处于极低水平，资源充足。
4.  **节点识别**：Prometheus查询结果中的实例IP（如 `10.2.0.49:9100`）对应具体的集群节点。根据阶段1信息，`master`、`node1`、`node2` 三个节点状态均为 `Ready`。

---

## 📊 性能统计

├─ 总耗时: 4.3m
├─ 问题定位: 98.4s (38%) ✅
├─ 证据链采集: 49.1s (19%) ✅
├─ 根因分析: 70.0s (27%) ✅
├─ 汇总总结: 38.2s (15%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 10 次
```

📋 诊断追踪

- **参考 Runbook**: 无
- **工具调用**: 10 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
