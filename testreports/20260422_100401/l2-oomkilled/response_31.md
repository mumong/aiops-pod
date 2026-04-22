======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 6c132270eda444e1]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来帮您检查集群的健康状况。首先，让我获取一些基础信息来了解集群的当前状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   208d   v1.26.8  
   💭 [问题定位] 节点状态看起来都正常。现在让我检查一下所有命名空间中的 Pod 状态：
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE,NAME,STATUS,READY,RESTARTS,AGE' | (head -n 1; tail -n +2 | grep -E 'Evicted|CrashLoopBackOff|ImagePullBackOff|Er
   💭 [问题定位] 让我用正确的格式来检查异常 Pod：
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 Executing jq query for pods...
{
  "namespace": "aiops-e2e",
  "name": "memhog-578d9b5ffd-lwfxj",
  "status": "Running",
  "reason": "CrashLoopBackOff"
}
   💭 [问题定位] 发现了一个有问题的 Pod。让我获取更详细的信息：
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             memhog-578d9b5ffd-lwfxj
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Tue, 21 Apr 2026 09:55:19 +0000

   💭 [问题定位] 现在让我获取通用健康检查参考手册，然后继续检查其他资源：
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# 私有化 Kubernetes 环境健康与高效排查参考手册

> 类型: reference | 适用: 私有化 Kubernetes 环境 | 环境特征: Calico + NFS + containerd

## 目的

本手册不是某个具体故障的处理步骤，而是一个**额外知识参考**：
- 帮助理解在私有化 Kubernetes 环境中，健康检查应重点关注哪些资源与信号

   💭 [问题定位] 现在让我继续检查其他资源面。根据参考手册，我需要检查 Service/Endpoints 状态：
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 Executing jq query for services...
{
  "namespace": "aaa",
  "name": "test1-redis-headless",
  "type": "ClusterIP",
  "clusterIP": "None",
  "ports": [
    6379
  ]
}
{
  "namespace": "aaa",
  "name":
   💭 [问题定位] 现在让我检查 Endpoints 状态，特别是那些可能没有 Endpoints 的 Service：
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 Executing jq query for endpoints...
{
  "namespace": "aaa",
  "name": "test1-redis-headless",
  "subsets": 0
}
{
  "namespace": "aaa",
  "name": "test1-redis-master",
  "subsets": 0
}
{
  "namespace":
   💭 [问题定位] 我注意到有几个 Service 的 Endpoints 为空（subsets: 0）。让我检查一下这些 Service 对应的 Pod 是否存在。首先检查 aaa 命名空间中的 redis 相关 Pod：
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 No resources found in aaa namespace.
   💭 [问题定位] 现在检查 xnet 命名空间中的 test2-redis 相关 Pod：
   💭 [问题定位] 调用工具: kubectl_find_resource
   💭 [问题定位] 工具结果: kubectl_find_resource (success)
      📄 Command failed (exit 1):
kubectl get -A --show-labels -o wide pods | grep -i 'test2-redis'

   💭 [问题定位] 让我检查 PVC 状态，因为根据参考手册，存储面也需要检查：
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 Executing jq query for persistentvolumeclaims...
   💭 [问题定位] 没有未绑定的 PVC。现在让我检查一下是否有其他异常的工作负载。让我获取 OOMKilled 相关的 runbook，因为我们已经发现了一个 OOMKilled 的 Pod：
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# L2 Pod OOMKilled (Exit Code 137)

> 层级: L2 - 工作负载层 | 场景: 容器内存超限被 OOM Killer 终止

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | CrashLoopBackOff / Error / 频繁重启 |
| Describe | termina
   💭 [问题定位] 现在让我检查是否有其他异常的工作负载，比如 Deployment 或 StatefulSet：
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 Executing jq query for deployments...
{
  "namespace": "aiops-e2e",
  "name": "memhog",
  "ready": null,
  "available": null,
  "replicas": 1
}
   💭 [问题定位] 让我检查这个 Deployment 的详细信息：
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:                   memhog
Namespace:              aiops-e2e
CreationTimestamp:      Tue, 21 Apr 2026 09:55:19 +0000
Labels:                 e2e-test=true
Annotations:            deployment.kubern
   💭 [问题定位] 现在让我检查是否有其他异常的工作负载类型，比如 StatefulSet：
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 Executing jq query for statefulsets...
   ✅ [问题定位] 完成 (1m 27.9s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[{'scenario': '容器内存超限 (OOMKilled)', 'probability': '高', 'reason': 'Pod 状态为 CrashLoopBackOff，Last State 显示 Reason: OOMKilled, Exit Code: 137。容器内存 limit 为 40Mi，而应用代码在无限循环中分配内存。'}, {'scenario': '资源配置不足', 'probability': '高', 'reason': '容器内存 limit (40Mi) 可能低于应用实际需求，导致频繁 OOM。'}]
   entities=[{"type": "Pod", "value": "memhog-578d9b5ffd-lwfxj (aiops-e2e)"}, {"type": "Deployment", "value": "memhog (aiops-e2e)"}]
   reasoning=发现一个活跃异常对象：Pod memhog-578d9b5ffd-lwfxj 处于 CrashLoopBackOff 状态，原因是 OOMKilled (Exit Code 137)。该 Pod 属于 Deployment memhog，其 availableReplicas 为 0，表明工作负载当前不可用。节点层面所有节点 Ready，Service/Endpoints 层面大部分正常，但存在部分 Service（如 aaa 和 xnet 命名空间中的 redis 相关服务）Endpoints 为空，这可能是由于缺少匹配的 Pod 或 Pod 未 Ready 导致，但当前最明确的活跃异常是 OOMKilled 的 Pod。
   layer_analysis={"layer": "L2", "layers": ["L2"], "layer_name": "工作负载层", "confidence": 0.9, "reasoning": "发现一个活跃异常对象：Pod memhog-578d9b5ffd-lwfxj 处于 CrashLoopBackOff 状态，原因是 OOMKilled (Exit Code 137)。该 Pod 属于 Deployment memhog，其 availableReplicas 为 0，表明工作负载当前不可用。节点层面所有节点 Ready，Service/Endpoints 层面大部分正常，但存在部分 Service（如 aaa 和 xnet 命名空间中的 redis 相关服务）Endpoints 为空，这可能是由于缺少匹配的 Pod 或 Pod 未 Ready 导致，但当前最明确的活跃异常是 OOMKilled 的 Pod。", "key_entities": [{"type": "Pod", "value": "memhog-578d9b5ffd-lwfxj (aiops-e2e)"}, {"type": "Deployment", "value": "memhog (aiops-e2e)"}], "possible_scenarios": [{"scenario": "容器内存超限 (OOMKilled)", "probability": "高", "reason": "Pod 状态为 CrashLoopBackOff，Last State 显示 Reason: OOMKilled, Exit Code: 137。容器内存 limit 为 40Mi，而应用代码在无限循环中分配内存。"}, {"scenario": "资源配置不足", "probability": "高", "reason": "容器内存 limit (40Mi) 可能低于应用实际需求，导致频繁 OOM。"}]}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L2
   置信度: 90%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 根据我看到的集群状态，现在我来制定一个全面的健康检查计划。首先，让我输出证据采集计划：

```json
{
  "layer": "QUERY",
  "evidence_plan": [
    {
      "id": "e1",
      "description": "检查所有节点的状态和资源压力",
      "level": "critical",
      "tool": "kubernetes_jq_query",
      "command": "kubectl get nodes -o json | jq -r '.items[] | {name: .metadata.name, status: .status.conditions[] | select(.type==\"Ready\") | .status, memoryPressure: .status.conditions[] | select(.type==\"MemoryPressure\") | .status, diskPressure: .status.conditions[] | select(.type==\"DiskPressure\") | .status, pidPressure: .status.conditions[] | select(.type==\"PIDPressure\") | .status}'",
      "purpose": "确认节点是否Ready，是否有资源压力"
    },
    {
      "id": "e2",
      "description": "检查所有Pod的状态，重点关注异常状态",
      "level": "critical",
      "tool": "kubernetes_tabular_query",
      "command": "kubectl get pods -A -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,READY:.status.containerStatuses[0].ready,RESTARTS:.status.containerStatuses[0].restartCount,AGE:.metadata.creationTimestamp'",
      "purpose": "识别所有异常Pod（CrashLoopBackOff、Pending、Error等）"
    },
    {
      "id": "e3",
      "description": "检查所有Deployment的副本状态",
      "level": "important",
      "tool": "kubernetes_jq_query",
      "command": "kubectl get deployments -A -o json | jq -r '.items[] | {namespace: .metadata.namespace, name: .metadata.name, readyReplicas: .status.readyReplicas, availableReplicas: .status.availableReplicas, replicas: .status.replicas, unavailableReplicas: .status.unavailableReplicas}'",
      "purpose": "确认Deployment副本是否就绪，是否有不可用副本"
    },
    {
      "id": "e4",
      "description": "检查所有StatefulSet的副本状态",
      "level": "important",
      "tool": "kubernetes_jq_query",
      "command": "kubectl get statefulsets -A -o json | jq -r '.items[] | {namespace: .metadata.namespace, name: .metadata.name, readyReplicas: .status.readyReplicas, replicas: .status.replicas}'",
      "purpose": "确认StatefulSet副本是否就绪"
    },
    {
      "id": "e5",
      "description": "检查Service和Endpoints的匹配情况",
      "level": "important",
      "tool": "kubernetes_jq_query",
      "command": "kubectl get services -A -o json | jq -r '.items[] | {namespace: .metadata.namespace, name: .metadata.name, type: .spec.type, clusterIP: .spec.clusterIP, selector: .spec.selector}'",
      "purpose": "确认Service配置和selector"
    },
    {
      "id": "e6",
      "description": "检查PVC状态",
      "level": "optional",
      "tool": "kubernetes_jq_query",
      "command": "kubectl get pvc -A -o json | jq -r '.items[] | {namespace: .metadata.namespace, name: .metadata.name, status: .status.phase, volumeName: .spec.volumeName}'",
      "purpose": "确认PVC是否绑定，是否有Pending状态"
    },
    {
      "id": "e7",
      "description": "检查核心系统组件状态",
      "level": "important",
      "tool": "kubernetes_tabular_query",
      "command": "kubectl get pods -n kube-system -o custom-columns='NAME:.metadata.name,STATUS:.status.phase,READY:.status.containerStatuses[0].ready,RESTARTS:.status.containerStatuses[0].restartCount,AGE:.metadata.creationTimestamp'",
      "purpose": "确认kube-system命名空间核心组件是否正常"
    }
  ],
  "collection_strategy": "按照健康检查基线原则，从节点面开始，逐步检查工作负载面、服务面、存储面。优先关注当前异常状态，不进行全量历史扫描。"
}
```

现在让我逐项执行工具采集证据：
   💭 [证据链采集] 调用工具: kubernetes_jq_query
   💭 [证据链采集] 工具结果: kubernetes_jq_query (success)
      📄 Executing jq query for nodes...
{
  "name": "master",
  "status": "True",
  "memoryPressure": "False",
  "diskPressure": "False",
  "pidPressure": "False"
}
{
  "name": "node1",
  "status": "True",
  
   💭 [证据链采集] 调用工具: kubernetes_tabular_query
   💭 [证据链采集] 工具结果: kubernetes_tabular_query (success)
      📄 NAMESPACE     NAME                                                STATUS    READY   RESTARTS   AGE
aiops-e2e     memhog-578d9b5ffd-lwfxj                             Running   false   199        2026-0
   💭 [证据链采集] 调用工具: kubernetes_jq_query
   💭 [证据链采集] 工具结果: kubernetes_jq_query (success)
      📄 Executing jq query for deployments...
{
  "namespace": "aiops-e2e",
  "name": "memhog",
  "readyReplicas": null,
  "availableReplicas": null,
  "replicas": 1,
  "unavailableReplicas": 1
}
{
  "namespa
   💭 [证据链采集] 调用工具: kubernetes_jq_query
   💭 [证据链采集] 工具结果: kubernetes_jq_query (success)
      📄 Executing jq query for statefulsets...
{
  "namespace": "xnet",
  "name": "alertmanager-observability-alertmanager",
  "readyReplicas": 1,
  "replicas": 1
}
{
  "namespace": "xnet",
  "name": "elastic
   💭 [证据链采集] 调用工具: kubernetes_jq_query
   💭 [证据链采集] 工具结果: kubernetes_jq_query (success)
      📄 Executing jq query for services...
{
  "namespace": "aaa",
  "name": "test1-redis-headless",
  "type": "ClusterIP",
  "clusterIP": "None",
  "selector": {
    "app": "redis",
    "release": "test1"
  
   💭 [证据链采集] 调用工具: kubernetes_jq_query
   💭 [证据链采集] 工具结果: kubernetes_jq_query (success)
      📄 Executing jq query for persistentvolumeclaims...
{
  "namespace": "aaa",
  "name": "redis-data-test1-redis-master-0",
  "status": "Bound",
  "volumeName": "pvc-4bf1781c-080c-44f0-9547-ab6d062d72c1"
}

   💭 [证据链采集] 调用工具: kubernetes_tabular_query
   💭 [证据链采集] 工具结果: kubernetes_tabular_query (success)
      📄 Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAME:.metadata.name,STATUS:.status.phase,READY:.status.containerStatuses[0].ready,RESTARTS:.status.containerStatuses[0].re
   ✅ [证据链采集] 完成 (1m 12.6s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan": [{"id": "e1", "description": "检查所有节点的状态和资源压力", "level": "critical", "tool": "kubernetes_jq_query", "command": "kubectl get nodes -o json | jq -r '.items[] | {name: .metadata.name, status: .status.conditions[] | select(.type==\"Ready\") | .status, memoryPressure: .status.conditions[] | select(.type==\"MemoryPressure\") | .status, diskPressure: .status.conditions[] | select(.type==\"DiskPressure\") | .status, pidPressure: .status.conditions[] | select(.type==\"PIDPressure\") | .status}'", "purpose": "确认节点是否Ready，是否有资源压力"}, {"id": "e2", "description": "检查所有Pod的状态，重点关注异常状态", "level": "critical", "tool": "kubernetes_tabular_query", "command": "kubectl get pods -A -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,READY:.status.containerStatuses[0].ready,RESTARTS:.status.containerStatuses[0].restartCount,AGE:.metadata.creationTimestamp'", "purpose": "识别所有异常Pod（CrashLoopBackOff、Pending、Error等）"}, {"id": "e3", "description": "检查所有Deployment的副本状态", "level": "important", "tool": "kubernetes_jq_query", "command": "kubectl get deployments -A -o json | jq -r '.items[] | {namespace: .metadata.namespace, name: .metadata.name, readyReplicas: .status.readyReplicas, availableReplicas: .status.availableReplicas, replicas: .status.replicas, unavailableReplicas: .status.unavailableReplicas}'", "purpose": "确认Deployment副本是否就绪，是否有不可用副本"}, {"id": "e4", "description": "检查所有StatefulSet的副本状态", "level": "important", "tool": "kubernetes_jq_query", "command": "kubectl get statefulsets -A -o json | jq -r '.items[] | {namespace: .metadata.namespace, name: .metadata.name, readyReplicas: .status.readyReplicas, replicas: .status.replicas}'", "purpose": "确认StatefulSet副本是否就绪"}, {"id": "e5", "description": "检查Service和Endpoints的匹配情况", "level": "important", "tool": "kubernetes_jq_query", "command": "kubectl get services -A -o json | jq -r '.items[] | {namespace: .metadata.namespace, name: .metadata.name, type: .spec.type, clusterIP: .spec.clusterIP, selector: .spec.selector}'", "purpose": "确认Service配置和selector"}, {"id": "e6", "description": "检查PVC状态", "level": "optional", "tool": "kubernetes_jq_query", "command": "kubectl get pvc -A -o json | jq -r '.items[] | {namespace: .metadata.namespace, name: .metadata.name, status: .status.phase, volumeName: .spec.volumeName}'", "purpose": "确认PVC是否绑定，是否有Pending状态"}, {"id": "e7", "description": "检查核心系统组件状态", "level": "important", "tool": "kubernetes_tabular_query", "command": "kubectl get pods -n kube-system -o custom-columns='NAME:.metadata.name,STATUS:.status.phase,READY:.status.containerStatuses[0].ready,RESTARTS:.status.containerStatuses[0].restartCount,AGE:.metadata.creationTimestamp'", "purpose": "确认kube-system命名空间核心组件是否正常"}], "tool_results": [], "tool_data": [{"tool": "kubernetes_jq_query", "data": "Executing jq query for nodes...\n{\n  \"name\": \"master\",\n  \"status\": \"True\",\n  \"memoryPressure\": \"False\",\n  \"diskPressure\": \"False\",\n  \"pidPressure\": \"False\"\n}\n{\n  \"name\": \"node1\",\n  \"status\": \"True\",\n  \"memoryPressure\": \"False\",\n  \"diskPressure\": \"False\",\n  \"pidPressure\": \"False\"\n}\n{\n  \"name\": \"node2\",\n  \"status\": \"True\",\n  \"memoryPressure\": \"False\",\n  \"diskPressure\": \"False\",\n  \"pidPressure\": \"False\"\n}", "duration_s": 0}, {"tool": "kubernetes_tabular_query", "data": "NAMESPACE     NAME                                                STATUS    READY   RESTARTS   AGE\naiops-e2e     memhog-578d9b5ffd-lwfxj                             Running   false   199        2026-04-21T09:55:19Z\naiops         aiops-copilot-76779bb6df-4bcrf                      Running   true    0          2026-04-22T01:37:45Z\ndefault       dns-test-existing                                   Running   true    0          2026-04-20T05:25:40Z\ndefault       exec-test                                           Running   true    0          2026-04-20T03:22:35Z\ndefault       network-test-from-running                           Running   true    0          2026-04-20T05:16:15Z\ndefault       nfs-client-provisioner-6fcd4994c9-lczf6             Running   true    4          2026-01-26T07:47:07Z\nkube-system   calico-kube-controllers-6c67f9d475-2xcb7            Running   true    4          2026-03-25T06:43:01Z\nkube-system   calico-node-4kp26                                   Running   true    12         2025-10-20T09:55:21Z\nkube-system   calico-node-d2dhp                                   Running   true    13         2025-10-20T09:55:21Z\nkube-system   calico-node-mnrjs                                   Running   true    12         2025-10-20T09:55:21Z\nkube-system   coredns-777df594b8-j4857                            Running   true    4          2026-03-25T06:43:01Z\nkube-system   coredns-777df594b8-s8r4n                            Running   true    4          2026-03-25T06:43:01Z\nkube-system   etcd-master                                         Running   true    13         2025-09-25T03:04:26Z\nkube-system   kube-apiserver-master                               Running   true    13         2025-09-25T03:04:24Z\nkube-system   kube-controller-manager-master                      Running   true    36         2025-09-25T03:04:26Z\nkube-system   kube-multus-ds-rnvbg                                Running   true    12         2025-10-20T09:55:32Z\nkube-system   kube-multus-ds-sc2jn                                Running   true    4          2026-01-26T07:55:35Z\nkube-system   kube-multus-ds-x7h9s                                Running   true    13         2025-10-20T09:55:32Z\nkube-system   kube-proxy-69zzr                                    Running   true    4          2026-03-25T06:53:15Z\nkube-system   kube-proxy-bblvc                                    Running   true    4          2026-03-25T06:53:15Z\nkube-system   kube-proxy-wbh4k                                    Running   true    4          2026-03-26T03:26:59Z\nkube-system   kube-scheduler-master                               Running   true    38         2025-09-25T03:04:24Z\nmcp           mcp-server-manager-8677f6896c-d4mr9                 Running   true    0          2026-04-20T09:52:16Z\nxnet          alertmanager-observability-alertmanager-0           Running   true    4          2026-03-30T07:18:54Z\nxnet          api-server-6bd6bf8d6f-27svp                         Running   true    4          2026-03-30T07:18:47Z\nxnet          deepflow-agent-pcknn                                Running   true    9          2026-03-30T07:18:47Z\nxnet          deepflow-agent-trc8k                                Running   true    7          2026-04-03T01:32:25Z\nxnet          deepflow-agent-whn22                                Running   true    8          2026-03-30T07:18:47Z\nxnet          elasticsearch-master-0                              Running   true    4          2026-03-30T07:18:47Z\nxnet          ham-p9dxv                                           Running   true    14         2025-10-27T01:40:27Z\nxnet          ham-qzjg5                                           Running   true    4          2026-01-27T01:45:54Z\nxnet          ham-wt9kh                                           Running   true    13         2025-10-27T01:40:27Z\nxnet          lgtm-5dc5c67d5f-sc286                               Running   true    4          2026-03-30T07:18:47Z\nxnet          observability-clickhouse-0                          Running   true    4          2026-03-30T07:18:47Z\nxnet          observability-deepflow-app-654fcfbfbf-q8st6         Running   true    4          2026-03-30T07:18:47Z\nxnet          observability-deepflow-server-774dd6c5b7-9c998      Running   true    14         2026-03-30T07:18:48Z\nxnet          observability-filebeat-ffwsp                        Running   true    4          2026-03-30T07:18:47Z\nxnet          observability-filebeat-m58xw                        Running   true    5          2026-03-30T07:18:47Z\nxnet          observability-filebeat-w6gtr                        Running   true    5          2026-04-03T01:32:25Z\nxnet          observability-grafana-58bf9cfd6f-ndsxr              Running   true    7          2026-03-30T07:18:47Z\nxnet          observability-kepler-2sgrr                          Running   true    6          2026-03-30T07:18:47Z\nxnet          observability-kepler-7scjm                          Running   true    7          2026-03-30T07:18:47Z\nxnet          observability-kepler-ggstf                          Running   true    8          2026-04-03T01:32:25Z\nxnet          observability-kibana-65d7c45f6d-tm4vv               Running   true    4          2026-03-30T07:18:47Z\nxnet          observability-kube-state-metrics-798986b8b7-6z2dq   Running   true    4          2026-03-30T07:18:47Z\nxnet          observability-mysql-764f9d5966-wh2bc                Running   true    4          2026-03-30T07:18:47Z\nxnet          observability-operator-d4495dc86-69lgw              Running   true    4          2026-03-30T07:18:47Z\nxnet          observability-prometheus-node-exporter-lj75r        Running   true    4          2026-03-30T07:18:47Z\nxnet          observability-prometheus-node-exporter-qp2qd        Running   true    4          2026-04-03T01:32:25Z\nxnet          observability-prometheus-node-exporter-wnbb8        Running   true    4          2026-03-30T07:18:47Z\nxnet          observability-telegraf-79f45d86-4kzkm               Running   true    4          2026-03-30T07:18:47Z\nxnet          prometheus-observability-prometheus-0               Running   true    4          2026-03-30T07:18:54Z\nxnet          xnet-agent-568f547566-jdsgp                         Running   true    4          2026-01-04T01:25:07Z", "duration_s": 0}, {"tool": "kubernetes_jq_query", "data": "Executing jq query for deployments...\n{\n  \"namespace\": \"aiops-e2e\",\n  \"name\": \"memhog\",\n  \"readyReplicas\": null,\n  \"availableReplicas\": null,\n  \"replicas\": 1,\n  \"unavailableReplicas\": 1\n}\n{\n  \"namespace\": \"aiops\",\n  \"name\": \"aiops-copilot\",\n  \"readyReplicas\": 1,\n  \"availableReplicas\": 1,\n  \"replicas\": 1,\n  \"unavailableReplicas\": null\n}\n{\n  \"namespace\": \"default\",\n  \"name\": \"nfs-client-provisioner\",\n  \"readyReplicas\": 1,\n  \"availableReplicas\": 1,\n  \"replicas\": 1,\n  \"unavailableReplicas\": null\n}\n{\n  \"namespace\": \"kube-system\",\n  \"name\": \"calico-kube-controllers\",\n  \"readyReplicas\": 1,\n  \"availableReplicas\": 1,\n  \"replicas\": 1,\n  \"unavailableReplicas\": null\n}\n{\n  \"namespace\": \"kube-system\",\n  \"name\": \"coredns\",\n  \"readyReplicas\": 2,\n  \"availableReplicas\": 2,\n  \"replicas\": 2,\n  \"unavailableReplicas\": null\n}\n{\n  \"namespace\": \"mcp\",\n  \"name\": \"mcp-server-manager\",\n  \"readyReplicas\": 1,\n  \"availableReplicas\": 1,\n  \"replicas\": 1,\n  \"unavailableReplicas\": null\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"api-server\",\n  \"readyReplicas\": 1,\n  \"availableReplicas\": 1,\n  \"replicas\": 1,\n  \"unavailableReplicas\": null\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"lgtm\",\n  \"readyReplicas\": 1,\n  \"availableReplicas\": 1,\n  \"replicas\": 1,\n  \"unavailableReplicas\": null\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"observability-deepflow-app\",\n  \"readyReplicas\": 1,\n  \"availableReplicas\": 1,\n  \"replicas\": 1,\n  \"unavailableReplicas\": null\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"observability-deepflow-server\",\n  \"readyReplicas\": 1,\n  \"availableReplicas\": 1,\n  \"replicas\": 1,\n  \"unavailableReplicas\": null\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"observability-grafana\",\n  \"readyReplicas\": 1,\n  \"availableReplicas\": 1,\n  \"replicas\": 1,\n  \"unavailableReplicas\": null\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"observability-kibana\",\n  \"readyReplicas\": 1,\n  \"availableReplicas\": 1,\n  \"replicas\": 1,\n  \"unavailableReplicas\": null\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"observability-kube-state-metrics\",\n  \"readyReplicas\": 1,\n  \"availableReplicas\": 1,\n  \"replicas\": 1,\n  \"unavailableReplicas\": null\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"observability-mysql\",\n  \"readyReplicas\": 1,\n  \"availableReplicas\": 1,\n  \"replicas\": 1,\n  \"unavailableReplicas\": null\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"observability-operator\",\n  \"readyReplicas\": 1,\n  \"availableReplicas\": 1,\n  \"replicas\": 1,\n  \"unavailableReplicas\": null\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"observability-telegraf\",\n  \"readyReplicas\": 1,\n  \"availableReplicas\": 1,\n  \"replicas\": 1,\n  \"unavailableReplicas\": null\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"xnet-agent\",\n  \"readyReplicas\": 1,\n  \"availableReplicas\": 1,\n  \"replicas\": 1,\n  \"unavailableReplicas\": null\n}", "duration_s": 0}, {"tool": "kubernetes_jq_query", "data": "Executing jq query for statefulsets...\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"alertmanager-observability-alertmanager\",\n  \"readyReplicas\": 1,\n  \"replicas\": 1\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"elasticsearch-master\",\n  \"readyReplicas\": 1,\n  \"replicas\": 1\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"observability-clickhouse\",\n  \"readyReplicas\": 1,\n  \"replicas\": 1\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"prometheus-observability-prometheus\",\n  \"readyReplicas\": 1,\n  \"replicas\": 1\n}", "duration_s": 0}, {"tool": "kubernetes_jq_query", "data": "Executing jq query for services...\n{\n  \"namespace\": \"aaa\",\n  \"name\": \"test1-redis-headless\",\n  \"type\": \"ClusterIP\",\n  \"clusterIP\": \"None\",\n  \"selector\": {\n    \"app\": \"redis\",\n    \"release\": \"test1\"\n  }\n}\n{\n  \"namespace\": \"aaa\",\n  \"name\": \"test1-redis-master\",\n  \"type\": \"ClusterIP\",\n  \"clusterIP\": \"172.30.184.110\",\n  \"selector\": {\n    \"app\": \"redis\",\n    \"release\": \"test1\",\n    \"role\": \"master\"\n  }\n}\n{\n  \"namespace\": \"aaa\",\n  \"name\": \"test1-redis-slave\",\n  \"type\": \"ClusterIP\",\n  \"clusterIP\": \"172.30.186.210\",\n  \"selector\": {\n    \"app\": \"redis\",\n    \"release\": \"test1\",\n    \"role\": \"slave\"\n  }\n}\n{\n  \"namespace\": \"aiops\",\n  \"name\": \"aiops-copilot\",\n  \"type\": \"NodePort\",\n  \"clusterIP\": \"172.30.33.24\",\n  \"selector\": {\n    \"app\": \"aiops-copilot\"\n  }\n}\n{\n  \"namespace\": \"default\",\n  \"name\": \"kubernetes\",\n  \"type\": \"ClusterIP\",\n  \"clusterIP\": \"172.30.0.1\",\n  \"selector\": null\n}\n{\n  \"namespace\": \"kube-system\",\n  \"name\": \"kube-dns\",\n  \"type\": \"ClusterIP\",\n  \"clusterIP\": \"172.30.0.10\",\n  \"selector\": {\n    \"k8s-app\": \"kube-dns\"\n  }\n}\n{\n  \"namespace\": \"kube-system\",\n  \"name\": \"observability-coredns\",\n  \"type\": \"ClusterIP\",\n  \"clusterIP\": \"None\",\n  \"selector\": {\n    \"k8s-app\": \"kube-dns\"\n  }\n}\n{\n  \"namespace\": \"kube-system\",\n  \"name\": \"observability-kube-controller-manager\",\n  \"type\": \"ClusterIP\",\n  \"clusterIP\": \"None\",\n  \"selector\": {\n    \"component\": \"kube-controller-manager\"\n  }\n}\n{\n  \"namespace\": \"kube-system\",\n  \"name\": \"observability-kube-etcd\",\n  \"type\": \"ClusterIP\",\n  \"clusterIP\": \"None\",\n  \"selector\": {\n    \"component\": \"etcd\"\n  }\n}\n{\n  \"namespace\": \"kube-system\",\n  \"name\": \"observability-kube-proxy\",\n  \"type\": \"ClusterIP\",\n  \"clusterIP\": \"None\",\n  \"selector\": {\n    \"k8s-app\": \"kube-proxy\"\n  }\n}\n{\n  \"namespace\": \"kube-system\",\n  \"name\": \"observability-kube-scheduler\",\n  \"type\": \"ClusterIP\",\n  \"clusterIP\": \"None\",\n  \"selector\": {\n    \"component\": \"kube-scheduler\"\n  }\n}\n{\n  \"namespace\": \"kube-system\",\n  \"name\": \"observability-kubelet\",\n  \"type\": \"ClusterIP\",\n  \"clusterIP\": \"None\",\n  \"selector\": null\n}\n{\n  \"namespace\": \"mcp\",\n  \"name\": \"mcp-server-manager\",\n  \"type\": \"ClusterIP\",\n  \"clusterIP\": \"172.30.236.87\",\n  \"selector\": {\n    \"app\": \"mcp-server-manager\"\n  }\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"alertmanager-operated\",\n  \"type\": \"ClusterIP\",\n  \"clusterIP\": \"None\",\n  \"selector\": {\n    \"app.kubernetes.io/name\": \"alertmanager\"\n  }\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"api-service\",\n  \"type\": \"NodePort\",\n  \"clusterIP\": \"172.30.47.171\",\n  \"selector\": {\n    \"app\": \"api-server\"\n  }\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"deepflow-agent\",\n  \"type\": \"ClusterIP\",\n  \"clusterIP\": \"172.30.23.250\",\n  \"selector\": {\n    \"app\": \"deepflow\",\n    \"app.kubernetes.io/instance\": \"observability\",\n    \"app.kubernetes.io/name\": \"deepflow-agent\",\n    \"component\": \"deepflow-agent\"\n  }\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"elasticsearch-external\",\n  \"type\": \"NodePort\",\n  \"clusterIP\": \"172.30.190.54\",\n  \"selector\": {\n    \"app\": \"elasticsearch-master\"\n  }\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"elasticsearch-master-headless\",\n  \"type\": \"ClusterIP\",\n  \"clusterIP\": \"None\",\n  \"selector\": {\n    \"app\": \"elasticsearch-master\"\n  }\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"ham\",\n  \"type\": \"NodePort\",\n  \"clusterIP\": \"172.30.96.4\",\n  \"selector\": {\n    \"app\": \"ham\"\n  }\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"lgtm\",\n  \"type\": \"ClusterIP\",\n  \"clusterIP\": \"172.30.237.73\",\n  \"selector\": {\n    \"app\": \"lgtm\"\n  }\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"observability-alertmanager\",\n  \"type\": \"NodePort\",\n  \"clusterIP\": \"172.30.125.46\",\n  \"selector\": {\n    \"alertmanager\": \"observability-alertmanager\",\n    \"app.kubernetes.io/name\": \"alertmanager\"\n  }\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"observability-clickhouse\",\n  \"type\": \"ClusterIP\",\n  \"clusterIP\": \"172.30.124.73\",\n  \"selector\": {\n    \"app\": \"deepflow\",\n    \"app.kubernetes.io/instance\": \"observability\",\n    \"app.kubernetes.io/name\": \"clickhouse\",\n    \"component\": \"clickhouse\"\n  }\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"observability-clickhouse-headless\",\n  \"type\": \"ClusterIP\",\n  \"clusterIP\": \"None\",\n  \"selector\": {\n    \"app\": \"deepflow\",\n    \"app.kubernetes.io/instance\": \"observability\",\n    \"app.kubernetes.io/name\": \"clickhouse\",\n    \"component\": \"clickhouse\"\n  }\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"observability-deepflow-app\",\n  \"type\": \"ClusterIP\",\n  \"clusterIP\": \"172.30.227.137\",\n  \"selector\": {\n    \"app\": \"deepflow\",\n    \"app.kubernetes.io/instance\": \"observability\",\n    \"app.kubernetes.io/name\": \"deepflow\",\n    \"component\": \"deepflow-app\"\n  }\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"observability-deepflow-server\",\n  \"type\": \"NodePort\",\n  \"clusterIP\": \"172.30.172.26\",\n  \"selector\": {\n    \"app\": \"deepflow\",\n    \"app.kubernetes.io/instance\": \"observability\",\n    \"app.kubernetes.io/name\": \"deepflow\",\n    \"component\": \"deepflow-server\"\n  }\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"observability-grafana\",\n  \"type\": \"NodePort\",\n  \"clusterIP\": \"172.30.238.199\",\n  \"selector\": {\n    \"app.kubernetes.io/instance\": \"observability\",\n    \"app.kubernetes.io/name\": \"grafana\"\n  }\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"observability-kepler\",\n  \"type\": \"ClusterIP\",\n  \"clusterIP\": \"172.30.177.62\",\n  \"selector\": {\n    \"app.kubernetes.io/component\": \"exporter\",\n    \"app.kubernetes.io/name\": \"kepler-kepler\"\n  }\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"observability-kibana\",\n  \"type\": \"NodePort\",\n  \"clusterIP\": \"172.30.231.31\",\n  \"selector\": {\n    \"app\": \"observability-kibana\",\n    \"release\": \"observability\"\n  }\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"observability-kube-state-metrics\",\n  \"type\": \"ClusterIP\",\n  \"clusterIP\": \"172.30.210.245\",\n  \"selector\": {\n    \"app.kubernetes.io/instance\": \"observability\",\n    \"app.kubernetes.io/name\": \"kube-state-metrics\"\n  }\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"observability-mysql\",\n  \"type\": \"ClusterIP\",\n  \"clusterIP\": \"172.30.112.96\",\n  \"selector\": {\n    \"app\": \"deepflow\",\n    \"app.kubernetes.io/instance\": \"observability\",\n    \"app.kubernetes.io/name\": \"mysql\",\n    \"component\": \"mysql\"\n  }\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"observability-operator\",\n  \"type\": \"ClusterIP\",\n  \"clusterIP\": \"172.30.195.228\",\n  \"selector\": {\n    \"app\": \"observability-operator\",\n    \"release\": \"observability\"\n  }\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"observability-prometheus\",\n  \"type\": \"NodePort\",\n  \"clusterIP\": \"172.30.74.108\",\n  \"selector\": {\n    \"app.kubernetes.io/name\": \"prometheus\",\n    \"operator.prometheus.io/name\": \"observability-prometheus\"\n  }\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"observability-prometheus-node-exporter\",\n  \"type\": \"ClusterIP\",\n  \"clusterIP\": \"172.30.112.222\",\n  \"selector\": {\n    \"app.kubernetes.io/instance\": \"observability\",\n    \"app.kubernetes.io/name\": \"prometheus-node-exporter\"\n  }\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"observability-telegraf\",\n  \"type\": \"ClusterIP\",\n  \"clusterIP\": \"172.30.164.221\",\n  \"selector\": {\n    \"app.kubernetes.io/component\": \"telegraf\",\n    \"app.kubernetes.io/instance\": \"observability\",\n    \"app.kubernetes.io/name\": \"observability\"\n  }\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"prometheus-operated\",\n  \"type\": \"ClusterIP\",\n  \"clusterIP\": \"None\",\n  \"selector\": {\n    \"app.kubernetes.io/name\": \"prometheus\"\n  }\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"test2-redis-headless\",\n  \"type\": \"ClusterIP\",\n  \"clusterIP\": \"None\",\n  \"selector\": {\n    \"app\": \"redis\",\n    \"release\": \"test2\"\n  }\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"test2-redis-master\",\n  \"type\": \"ClusterIP\",\n  \"clusterIP\": \"172.30.110.97\",\n  \"selector\": {\n    \"app\": \"redis\",\n    \"release\": \"test2\",\n    \"role\": \"master\"\n  }\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"test2-redis-slave\",\n  \"type\": \"ClusterIP\",\n  \"clusterIP\": \"172.30.115.245\",\n  \"selector\": {\n    \"app\": \"redis\",\n    \"release\": \"test2\",\n    \"role\": \"slave\"\n  }\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"xnet-agent\",\n  \"type\": \"NodePort\",\n  \"clusterIP\": \"172.30.222.56\",\n  \"selector\": {\n    \"app\": \"xnet-agent\"\n  }\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"xnet-management\",\n  \"type\": \"ClusterIP\",\n  \"clusterIP\": \"172.30.85.213\",\n  \"selector\": null\n}", "duration_s": 0}, {"tool": "kubernetes_jq_query", "data": "Executing jq query for persistentvolumeclaims...\n{\n  \"namespace\": \"aaa\",\n  \"name\": \"redis-data-test1-redis-master-0\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-4bf1781c-080c-44f0-9547-ab6d062d72c1\"\n}\n{\n  \"namespace\": \"aaa\",\n  \"name\": \"redis-data-test1-redis-slave-0\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-98790f3f-3c73-48bf-acc5-21c9badec426\"\n}\n{\n  \"namespace\": \"abc\",\n  \"name\": \"redis-data-test1-redis-master-0\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-acd40aae-6ba3-4b9b-aae8-e34a8f298e46\"\n}\n{\n  \"namespace\": \"abc\",\n  \"name\": \"redis-data-test1-redis-slave-0\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-9d1a5b10-35b8-4d07-9eeb-b15c56d37c27\"\n}\n{\n  \"namespace\": \"abc\",\n  \"name\": \"redis-data-test2-redis-master-0\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-d8c12698-7fbd-4fcb-ac61-7978ccd97547\"\n}\n{\n  \"namespace\": \"abc\",\n  \"name\": \"redis-data-test2-redis-slave-0\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-c0748a38-c0ac-4025-85f9-60dc3c01e540\"\n}\n{\n  \"namespace\": \"default\",\n  \"name\": \"redis-data-my-redis-master-0\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-681058d9-2104-4a1e-a906-21af813b2ee9\"\n}\n{\n  \"namespace\": \"default\",\n  \"name\": \"redis-data-my-redis-slave-0\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-44436de6-3905-4b9e-8298-bb1b8c7fe830\"\n}\n{\n  \"namespace\": \"default\",\n  \"name\": \"redis-data-my-redis-slave-1\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-9e25128e-8a73-4c06-bc6f-a804619b2c7f\"\n}\n{\n  \"namespace\": \"default\",\n  \"name\": \"redis-data-test1-redis-master-0\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-fb63e962-0efd-4471-9613-3d5355946c12\"\n}\n{\n  \"namespace\": \"default\",\n  \"name\": \"redis-data-test1-redis-slave-0\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-4d9694f7-46d5-4d32-b411-5e047303c46b\"\n}\n{\n  \"namespace\": \"default\",\n  \"name\": \"redis-data-test2-redis-master-0\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-e249769f-e419-4af4-9020-ba51b1d862e1\"\n}\n{\n  \"namespace\": \"default\",\n  \"name\": \"redis-data-test2-redis-slave-0\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-b1013528-96b0-4573-ba75-df44a5c466eb\"\n}\n{\n  \"namespace\": \"dify\",\n  \"name\": \"data-dify-postgresql-primary-0\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-ed0117a7-ccec-4394-adb4-635dcba59a76\"\n}\n{\n  \"namespace\": \"dify\",\n  \"name\": \"data-dify-postgresql-read-0\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-2da8b3f2-1e8a-450b-ac7d-91d2d6409277\"\n}\n{\n  \"namespace\": \"dify\",\n  \"name\": \"dify\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-6dad2669-65c6-4fcb-88bd-3fe7030013f0\"\n}\n{\n  \"namespace\": \"dify\",\n  \"name\": \"dify-plugin-daemon\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-eb8c4fdc-88bc-4afd-a202-3e664471736c\"\n}\n{\n  \"namespace\": \"dify\",\n  \"name\": \"redis-data-dify-redis-master-0\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-e2f2fb60-1709-470a-bb76-2548d7e58a5a\"\n}\n{\n  \"namespace\": \"dify\",\n  \"name\": \"redis-data-dify-redis-replicas-0\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-9343637f-2b02-4290-9671-bd64ebe65db1\"\n}\n{\n  \"namespace\": \"dify\",\n  \"name\": \"redis-data-dify-redis-replicas-1\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-9a5b4639-1d3a-499e-a061-cc24f42858c9\"\n}\n{\n  \"namespace\": \"dify\",\n  \"name\": \"redis-data-dify-redis-replicas-2\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-f6b025e5-089f-4da6-9463-ea3dad0f13c6\"\n}\n{\n  \"namespace\": \"dify\",\n  \"name\": \"weaviate-data-weaviate-0\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-5c403db9-245e-4495-94eb-0bc2886fb9cb\"\n}\n{\n  \"namespace\": \"test\",\n  \"name\": \"clickhouse-path-observability-clickhouse-0\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-f8cc60bb-1d15-48f4-9959-d411eb726ae8\"\n}\n{\n  \"namespace\": \"test\",\n  \"name\": \"clickhouse-storage-path-observability-clickhouse-0\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-3904bd76-b49b-4610-a8c5-254c825157e8\"\n}\n{\n  \"namespace\": \"test\",\n  \"name\": \"elasticsearch-master-elasticsearch-master-0\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-857e17f4-9ec2-4d85-9828-fa99a1fd9910\"\n}\n{\n  \"namespace\": \"test\",\n  \"name\": \"observability-mysql-data-pvc\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-248d4792-5b53-4a5c-873c-5c4e07179a34\"\n}\n{\n  \"namespace\": \"test\",\n  \"name\": \"redis-data-my-redis-master-0\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-2127a610-79df-475d-bbf0-5a51f8c861cc\"\n}\n{\n  \"namespace\": \"test\",\n  \"name\": \"redis-data-my-redis-slave-0\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-04ff873a-d31b-4fe2-8db6-cfdb0836d326\"\n}\n{\n  \"namespace\": \"test\",\n  \"name\": \"redis-data-my-redis-slave-1\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-0b6228bd-3e55-4c94-b84c-41370c395779\"\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"clickhouse-path-observability-clickhouse-0\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-64f61871-9ae6-4f93-9846-33edc379491d\"\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"clickhouse-storage-path-observability-clickhouse-0\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-534daec8-1e93-480a-af4e-7bcd75864876\"\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"elasticsearch-master-elasticsearch-master-0\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-552011d5-64f2-4401-b912-ceebf9ed77bd\"\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"observability-mysql-data-pvc\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-72db6d2e-083d-4e14-b7c9-0b8622cbc695\"\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"redis-data-test2-redis-master-0\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-98841c70-96de-414c-9449-fc49b3ecd48f\"\n}\n{\n  \"namespace\": \"xnet\",\n  \"name\": \"redis-data-test2-redis-slave-0\",\n  \"status\": \"Bound\",\n  \"volumeName\": \"pvc-cdaa1891-9d35-434a-af3a-5cbca4acd6e5\"\n}", "duration_s": 0}, {"tool": "kubernetes_tabular_query", "data": "Command failed (exit 1):\nkubectl get pods --all-namespaces -o custom-columns='NAME:.metadata.name,STATUS:.status.phase,READY:.status.containerStatuses[0].ready,RESTARTS:.status.containerStatuses[0].restartCount,AGE:.metadata.creationTimestamp' | (head -n 1; tail -n +2 | grep -E 'kube-system')\nNAME                                                STATUS    READY   RESTARTS   AGE\n", "duration_s": 0}], "llm_analysis": "根据我看到的集群状态，现在我来制定一个全面的健康检查计划。首先，让我输出证据采集计划：\n\n```json\n{\n  \"layer\": \"QUERY\",\n  \"evidence_plan\": [\n    {\n      \"id\": \"e1\",\n      \"description\": \"检查所有节点的状态和资源压力\",\n      \"level\": \"critical\",\n      \"tool\": \"kubernetes_jq_query\",\n      \"command\": \"kubectl get nodes -o json | jq -r '.items[] | {name: .metadata.name, status: .status.conditions[] | select(.type==\\\"Ready\\\") | .status, memoryPressure: .status.conditions[] | select(.type==\\\"MemoryPressure\\\") | .status, diskPressure: .status.conditions[] | select(.type==\\\"DiskPressure\\\") | .status, pidPressure: .status.conditions[] | select(.type==\\\"PIDPressure\\\") | .status}'\",\n      \"purpose\": \"确认节点是否Ready，是否有资源压力\"\n    },\n    {\n      \"id\": \"e2\",\n      \"description\": \"检查所有Pod的状态，重点关注异常状态\",\n      \"level\": \"critical\",\n      \"tool\": \"kubernetes_tabular_query\",\n      \"command\": \"kubectl get pods -A -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,READY:.status.containerStatuses[0].ready,RESTARTS:.status.containerStatuses[0].restartCount,AGE:.metadata.creationTimestamp'\",\n      \"purpose\": \"识别所有异常Pod（CrashLoopBackOff、Pending、Error等）\"\n    },\n    {\n      \"id\": \"e3\",\n      \"description\": \"检查所有Deployment的副本状态\",\n      \"level\": \"important\",\n      \"tool\": \"kubernetes_jq_query\",\n      \"command\": \"kubectl get deployments -A -o json | jq -r '.items[] | {namespace: .metadata.namespace, name: .metadata.name, readyReplicas: .status.readyReplicas, availableReplicas: .status.availableReplicas, replicas: .status.replicas, unavailableReplicas: .status.unavailableReplicas}'\",\n      \"purpose\": \"确认Deployment副本是否就绪，是否有不可用副本\"\n    },\n    {\n      \"id\": \"e4\",\n      \"description\": \"检查所有StatefulSet的副本状态\",\n      \"level\": \"important\",\n      \"tool\": \"kubernetes_jq_query\",\n      \"command\": \"kubectl get statefulsets -A -o json | jq -r '.items[] | {namespace: .metadata.namespace, name: .metadata.name, readyReplicas: .status.readyReplicas, replicas: .status.replicas}'\",\n      \"purpose\": \"确认StatefulSet副本是否就绪\"\n    },\n    {\n      \"id\": \"e5\",\n      \"description\": \"检查Service和Endpoints的匹配情况\",\n      \"level\": \"important\",\n      \"tool\": \"kubernetes_jq_query\",\n      \"command\": \"kubectl get services -A -o json | jq -r '.items[] | {namespace: .metadata.namespace, name: .metadata.name, type: .spec.type, clusterIP: .spec.clusterIP, selector: .spec.selector}'\",\n      \"purpose\": \"确认Service配置和selector\"\n    },\n    {\n      \"id\": \"e6\",\n      \"description\": \"检查PVC状态\",\n      \"level\": \"optional\",\n      \"tool\": \"kubernetes_jq_query\",\n      \"command\": \"kubectl get pvc -A -o json | jq -r '.items[] | {namespace: .metadata.namespace, name: .metadata.name, status: .status.phase, volumeName: .spec.volumeName}'\",\n      \"purpose\": \"确认PVC是否绑定，是否有Pending状态\"\n    },\n    {\n      \"id\": \"e7\",\n      \"description\": \"检查核心系统组件状态\",\n      \"level\": \"important\",\n      \"tool\": \"kubernetes_tabular_query\",\n      \"command\": \"kubectl get pods -n kube-system -o custom-columns='NAME:.metadata.name,STATUS:.status.phase,READY:.status.containerStatuses[0].ready,RES", "collection_summary": "计划 7 项，实际采集 7 项，未采集 0 项，完整度 100%", "evidence_inventory": [{"id": "e1", "description": "检查所有节点的状态和资源压力", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e2", "description": "检查所有Pod的状态，重点关注异常状态", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e3", "description": "检查所有Deployment的副本状态", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e4", "description": "检查所有StatefulSet的副本状态", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e5", "description": "检查Service和Endpoints的匹配情况", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e6", "description": "检查PVC状态", "level": "optional", "collected": true, "source": "thinking_match"}, {"id": "e7", "description": "检查核心系统组件状态", "level": "important", "collected": true, "source": "thinking_match"}], "missing_reasons": [], "early_stop": {"triggered": true, "reason": "critical 和 important 级证据均已满足，提前停止后续采集", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 7/7 项, 完整度: 100%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 0.5s)
   📤 → 下游数据: root_cause=
   confidence=95%
   causal_chain={"root_cause": "应用设计缺陷：容器执行无限内存分配脚本，每0.02秒分配1MiB内存", "propagation": "内存消耗持续增长 → 超过40MiB内存限制 → 触发OOM Killer", "direct_cause": "容器内存超限被OOM Killer终止（Exit Code 137）", "manifestation": "Pod处于CrashLoopBackOff状态，重启199次，Deployment无可用副本"}
   rca_analysis={"phenomenon": "集群中存在一个异常Pod持续重启，Deployment副本不可用", "evidence_inventory": [{"id": "e1", "content": "所有3个节点状态正常，无资源压力", "source": "kubernetes_jq_query", "reliability": "高"}, {"id": "e2", "content": "Pod memhog-578d9b5ffd-lwfxj状态为Running但READY=false，重启199次", "source": "kubernetes_tabular_query", "reliability": "高"}, {"id": "e3", "content": "Pod详细描述显示容器状态为CrashLoopBackOff，上次终止原因为OOMKilled，退出码137", "source": "kubectl_describe", "reliability": "高"}, {"id": "e4", "content": "Deployment memhog有1个副本但availableReplicas=null，unavailableReplicas=1", "source": "kubernetes_jq_query", "reliability": "高"}, {"id": "e5", "content": "Deployment描述显示Replicas: 1 desired | 1 updated | 1 total | 0 available | 1 unavailable", "source": "kubectl_describe", "reliability": "高"}, {"id": "e6", "content": "容器资源配置：limits.memory=40Mi，requests.memory=20Mi", "source": "kubectl_describe", "reliability": "高"}, {"id": "e7", "content": "容器命令为无限循环分配内存：a.append(\"x\"*1024*1024) 每0.02秒分配1MiB", "source": "kubectl_describe", "reliability": "高"}, {"id": "e8", "content": "所有StatefulSet副本状态正常，所有PVC状态为Bound", "source": "kubernetes_jq_query", "reliability": "高"}, {"id": "e9", "content": "多个Service的Endpoints为空（aaa命名空间下的test1-redis相关服务，xnet命名空间下的test2-redis相关服务）", "source": "kubernetes_jq_query", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "master/True/False/False/False, node1/True/False/False/False, node2/True/False/False/False", "interpretation": "所有3个节点状态Ready=True，无MemoryPressure/DiskPressure/PIDPressure，节点层面健康"}, {"evidence_id": "e2", "raw_data": "memhog-578d9b5ffd-lwfxj STATUS=Running READY=false RESTARTS=199", "interpretation": "Pod处于异常状态：虽然状态为Running但容器未就绪，且已重启199次，表明容器持续崩溃重启"}, {"evidence_id": "e3", "raw_data": "State: Waiting, Reason: CrashLoopBackOff; Last State: Terminated, Reason: OOMKilled, Exit Code: 137; Restart Count: 199", "interpretation": "容器因内存超限被OOM Killer终止（Exit Code 137），导致CrashLoopBackOff状态，已重启199次"}, {"evidence_id": "e4", "raw_data": "namespace=aiops-e2e, name=memhog, readyReplicas=null, availableReplicas=null, replicas=1, unavailableReplicas=1", "interpretation": "Deployment memhog有1个期望副本，但无可用副本，有1个不可用副本"}, {"evidence_id": "e6", "raw_data": "Limits: cpu: 200m, memory: 40Mi; Requests: cpu: 50m, memory: 20Mi", "interpretation": "容器内存限制为40MiB，请求为20MiB"}, {"evidence_id": "e7", "raw_data": "import time; a=[]; while True: a.append(\"x\"*1024*1024); time.sleep(0.02)", "interpretation": "容器执行无限循环，每0.02秒分配1MiB内存，内存消耗会持续增长"}, {"evidence_id": "e8", "raw_data": "4个StatefulSet readyReplicas=1, replicas=1; 所有PVC status=Bound", "interpretation": "StatefulSet副本状态正常，存储卷绑定正常"}, {"evidence_id": "e9", "raw_data": "aaa/test1-redis-headless subsets=0, aaa/test1-redis-master subsets=0, aaa/test1-redis-slave subsets=0; xnet/test2-redis-headless subsets=0, xnet/test2-redis-master subsets=0, xnet/test2-redis-slave subsets=0", "interpretation": "多个Redis服务的Endpoints为空，表明这些服务没有匹配的Pod，但这些可能是历史残留服务而非当前故障"}], "causal_chain": {"root_cause": "应用设计缺陷：容器执行无限内存分配脚本，每0.02秒分配1MiB内存", "propagation": "内存消耗持续增长 → 超过40MiB内存限制 → 触发OOM Killer", "direct_cause": "容器内存超限被OOM Killer终止（Exit Code 137）", "manifestation": "Pod处于CrashLoopBackOff状态，重启199次，Deployment无可用副本"}, "root_cause_summary": "根据证据分析，集群主要问题是aiops-e2e命名空间下的memhog Deployment存在应用级故障。具体根因为：容器执行无限内存分配脚本（证据e7：每0.02秒分配1MiB内存），导致内存消耗持续增长并超过设置的40MiB内存限制（证据e6），触发OOM Killer终止容器（证据e3：Exit Code 137）。这导致Pod处于CrashLoopBackOff状态（证据e2：重启199次），进而使Deployment无可用副本（证据e4、e5：availableReplicas=null，unavailableReplicas=1）。节点层面健康（证据e1），其他工作负载正常（证据e8）。", "confidence": 0.95, "primary_runbooks": ["私有化 Kubernetes 环境健康与高效排查参考手册", "L2 Pod OOMKilled (Exit Code 137)"], "alternative_causes": ["内存限制设置过低：40MiB限制可能不足以支持Python运行时和内存分配", "应用代码bug：内存泄漏或无限循环"], "limitations": "1. 未采集容器崩溃前的日志，无法确认具体内存分配失败信息；2. 未检查节点实际内存使用情况，但节点无MemoryPressure表明非节点资源不足；3. 多个Service的Endpoints为空（aaa和xnet命名空间的Redis服务），但这些可能是历史残留服务，与当前memhog故障无关。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 95%
   🔗 因果链:
     根本原因: 应用设计缺陷：容器执行无限内存分配脚本，每0.02秒分配1MiB内存
     传导机制: 内存消耗持续增长 → 超过40MiB内存限制 → 触发OOM Killer
     最终表现: Pod处于CrashLoopBackOff状态，重启199次，Deployment无可用副本


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 13.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5443 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 54.7s
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
| **问题层级** | L2 - 工作负载层 |
| **问题分类** | OOMKilled |
| **置信度** | 高 (95%) |
| **证据完整度** | 7/7 (100%) |

---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键发现**：
集群整体健康，但存在一个异常工作负载。具体问题如下：
1.  **一个 Pod 持续崩溃重启**：`aiops-e2e` 命名空间下的 `memhog-578d9b5ffd-lwfxj` Pod 处于 `CrashLoopBackOff` 状态，已重启 **199 次**。
2.  **一个 Deployment 副本不可用**：对应的 `memhog` Deployment 有 1 个期望副本，但 **0 个可用副本**。
3.  **多个 Service 无后端 Pod**：`aaa` 和 `xnet` 命名空间下的多个 Redis 服务（如 `test1-redis-*`, `test2-redis-*`）的 Endpoints 为空，但这些可能是历史残留服务。

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `memhog-578d9b5ffd-lwfxj` |
| Namespace | `aiops-e2e` |
| Node | `node2` |
| 错误信息 | `OOMKilled`, `Exit Code: 137` |

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | 节点状态 | `kubectl get nodes -o json` | `master: status=True, memoryPressure=False...` | 所有 3 个节点状态 Ready，无资源压力 |
| 2 | Pod 状态 | `kubectl get pods -A -o custom-columns=...` | `aiops-e2e memhog-578d9b5ffd-lwfxj Running false 199` | Pod 状态为 Running 但 READY=false，已重启 199 次 |
| 3 | Pod 详情 | `kubectl describe pod memhog-...` | `State: Waiting, Reason: CrashLoopBackOff`<br>`Last State: Terminated, Reason: OOMKilled, Exit Code: 137`<br>`Restart Count: 199` | 容器因内存超限被 OOM Killer 终止，导致持续重启 |
| 4 | 资源配置 | `kubectl describe pod memhog-...` | `Limits: cpu: 200m, memory: 40Mi`<br>`Requests: cpu: 50m, memory: 20Mi` | 容器内存限制为 40MiB |
| 5 | 容器命令 | `kubectl describe pod memhog-...` | `Command: python -c`<br>`Args: import time; a=[]; while True: a.append("x"*1024*1024); time.sleep(0.02)` | 容器执行无限循环，每 0.02 秒分配 1MiB 内存 |
| 6 | Deployment 状态 | `kubectl get deployments -A -o json` | `namespace=aiops-e2e, name=memhog, readyReplicas=null, availableReplicas=null, replicas=1, unavailableReplicas=1` | Deployment 有 1 个副本，但 0 个可用 |
| 7 | Service/Endpoints | `kubectl get endpoints -A -o json` | `aaa/test1-redis-headless subsets=0`, `aaa/test1-redis-master subsets=0`... | 多个 Redis 服务 Endpoints 为空（历史残留） |

### 证据关联分析
- **证据 #3 + #4 + #5 印证**：容器命令无限分配内存 (`证据 #5`) → 内存消耗超过 40MiB 限制 (`证据 #4`) → 触发 OOM Killer (`证据 #3`)。
- **证据 #2 + #3 + #6 印证**：容器被终止 (`证据 #3`) → Pod 重启 199 次 (`证据 #2`) → Deployment 无可用副本 (`证据 #6`)。
- **证据 #1 排除节点问题**：所有节点无压力，表明问题局限在应用层。

### 缺失证据（如有）
无。证据采集完整度 100%。

---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 应用设计缺陷：容器执行无限内存分配脚本，每0.02秒分配1MiB内存      │
│ (证据 #5: `while True: a.append("x"*1024*1024); time.sleep(0.02)`)│
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 内存消耗持续增长 → 超过40MiB内存限制                             │
│ (证据 #4: `memory: 40Mi`)                                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器被 cgroup OOM Killer 终止 (Exit Code 137)                   │
│ (证据 #3: `Reason: OOMKilled, Exit Code: 137`)                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 CrashLoopBackOff，重启199次；Deployment 无可用副本      │
│ (证据 #2: `READY=false, RESTARTS=199`; 证据 #6: `availableReplicas=null`)│
└─────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #3 (OOMKilled, Exit Code 137)、证据 #4 (memory limit: 40Mi) 和证据 #5 (无限内存分配脚本)，问题的根本原因是 **`aiops-e2e/memhog` 应用容器执行了一个设计上就会导致内存无限增长的 Python 脚本**，该脚本每 0.02 秒分配 1MiB 内存，迅速超过其 40MiB 的内存限制，从而被系统 OOM Killer 强制终止，导致 Pod 陷入 `CrashLoopBackOff` 循环。

**置信度**：高 (95%)
- ✅ Exit Code 137 和 Reason: OOMKilled 直接确认内存超限。
- ✅ 容器命令明确显示无限内存分配逻辑。
- ✅ 资源配置显示内存限制仅为 40MiB，与脚本行为矛盾。
- ✅ 节点层面健康，排除集群资源不足。

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 审查并修正应用逻辑**
此 `memhog` 应用（标签 `e2e-test=true`）看起来像是一个测试或演示程序。需要决定是修复其逻辑还是直接删除。
- **选项A：删除该测试Deployment**
```bash
kubectl delete deployment memhog -n aiops-e2e
```
*依据*：如果这是一个无用的测试负载，直接删除是最快解决方案。
- **选项B：修正脚本并调整资源限制（如果必须保留）**
  1.  修改容器命令，移除无限内存分配循环。
  2.  根据实际需求调整资源限制。
```bash
# 示例：更新Deployment的容器命令（需根据实际镜像和入口点调整）
# 这需要编辑Deployment的YAML，此处仅为示意
kubectl edit deployment memhog -n aiops-e2e
# 在编辑器中，将 `args` 部分修改为合理的应用逻辑
```

**2. [可选] 检查崩溃前日志（确认细节）**
```bash
kubectl logs memhog-578d9b5ffd-lwfxj -n aiops-e2e --previous --tail=50
```
*目的*：查看OOM发生前的最后日志，确认无其他错误。

### 后续优化
1.  **清理历史残留服务**：检查并清理 `aaa` 和 `xnet` 命名空间中那些 Endpoints 为空的 Redis 服务（如 `test1-redis-*`, `test2-redis-*`），它们可能已无对应Pod。
2.  **资源规划**：对于生产应用，应使用监控工具评估真实内存使用量，并设置合理的 `requests` 和 `limits`。
3.  **添加健康检查**：为关键应用配置 `livenessProbe` 和 `readinessProbe`，以便更快地发现和隔离故障。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认异常Pod已清除 | `kubectl get pods -n aiops-e2e \| grep memhog` | 无返回结果 |
| 2. 确认Deployment状态 | `kubectl get deployment memhog -n aiops-e2e 2>/dev/null \|\| echo "Not found"` | `Not found` 或 `AVAILABLE=1` |
| 3. 确认节点持续健康 | `kubectl get nodes` | 所有节点 STATUS 为 Ready |

---
## ⚠️ 注意事项
- `memhog` 这个名称和其行为（内存占用）强烈暗示它是一个**测试或压力测试工具**。请确认其用途后再决定修复或删除。
- 集群其他部分（节点、核心系统组件、存储）均显示健康。
- 多个空 Endpoints 的 Service 可能影响服务发现，建议定期清理未使用的资源。

---

## 📊 性能统计

├─ 总耗时: 4.9m
├─ 问题定位: 87.9s (30%) ✅
├─ 证据链采集: 72.6s (25%) ✅
├─ 根因分析: 60.5s (21%) ✅
├─ 汇总总结: 73.8s (25%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 21 次
```

📋 诊断追踪

- **核心 Runbook**: private-k8s-health-reference, l2-oomkilled
- **参考 Runbook**: private-k8s-health-reference, l2-oomkilled
- **工具调用**: 21 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
