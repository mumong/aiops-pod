======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 34abdb2ba07b4195]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来帮您检查集群的健康状况。首先，让我获取一些基本的集群状态信息。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   209d   v1.26.8  
   💭 [问题定位] 节点状态看起来都是 Ready。现在让我检查一下 Pod 的整体状态：
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE,NAME,STATUS,RESTARTS,AGE,IP,NODE' | (head -n 1; tail -n +2 | grep -E 'Evicted|CrashLoopBackOff|ImagePullBackOff|
   💭 [问题定位] 让我用正确的格式重新查询：
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,RESTARTS:.status.containerStatuses[0].restartCount,
   💭 [问题定位] 看起来没有匹配到异常状态的 Pod。让我获取所有 Pod 的状态概览：
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 Executing jq query for pods...
   💭 [问题定位] 让我先获取通用健康检查参考手册，然后继续检查：
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# 私有化 Kubernetes 环境健康与高效排查参考手册

> 类型: reference | 适用: 私有化 Kubernetes 环境 | 环境特征: Calico + NFS + containerd

## 目的

本手册不是某个具体故障的处理步骤，而是一个**额外知识参考**：
- 帮助理解在私有化 Kubernetes 环境中，健康检查应重点关注哪些资源与信号

   💭 [问题定位] 现在让我继续检查集群状态。根据参考手册，我需要先做最小检查。让我查看所有 Pod 的状态：
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 Executing jq query for pods...
{
  "namespace": "aiops-e2e",
  "name": "l1-test-nginx-6c69dc7c76-fwzgn",
  "phase": "Pending",
  "node": null,
  "restartCount": 0
}
{
  "namespace": "kube-system",
  "
   💭 [问题定位] 我发现了一个 Pending 状态的 Pod，以及一些重启次数较多的系统组件。让我先检查这个 Pending 的 Pod：
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             l1-test-nginx-6c69dc7c76-fwzgn
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             <none>
Labels:           app=nginx
                  e2e-te
   💭 [问题定位] 现在让我检查节点是否有 taint：
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:               node2
Roles:              <none>
Labels:             beta.kubernetes.io/arch=amd64
                    beta.kubernetes.io/os=linux
                    kubernetes.io/arch=amd64
    
   💭 [问题定位] 现在让我检查其他节点的状态，并查看是否有其他异常：
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 Executing jq query for pods...
   💭 [问题定位] 让我检查一下 Service 和 Endpoints 的状态：
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 Executing jq query for services...
{
  "namespace": "aaa",
  "name": "test1-redis-headless",
  "type": "ClusterIP",
  "clusterIP": "None",
  "ports": [
    {
      "name": "redis",
      "port": 6379,
   💭 [问题定位] 现在让我检查 PVC 状态：
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 Executing jq query for persistentvolumeclaims...
{
  "namespace": "aaa",
  "name": "redis-data-test1-redis-master-0",
  "status": "Bound",
  "storageClass": "nfs-storage",
  "volumeName": "pvc-4bf1781
   💭 [问题定位] 现在让我检查一些关键的系统组件状态，特别是那些重启次数较多的：
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:                 kube-scheduler-master
Namespace:            kube-system
Priority:             2000001000
Priority Class Name:  system-node-critical
Node:                 master/10.2.0.48
Start T
   💭 [问题定位] 让我检查 kube-controller-manager：
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:                 kube-controller-manager-master
Namespace:            kube-system
Priority:             2000001000
Priority Class Name:  system-node-critical
Node:                 master/10.2.0.4
   💭 [问题定位] 基于我的检查，我发现以下问题：

1. **节点 taint 问题**：node2 节点有 `test-unschedulable=true:NoSchedule` taint，导致 Pod `l1-test-nginx-6c69dc7c76-fwzgn` 无法调度到该节点，处于 Pending 状态。

2. **控制平面组件重启频繁**：kube-scheduler 重启了 38 次，kube-controller-manager 重启了 36 次，etcd 和 kube-apiserver 也重启了 13 次。这表明控制平面可能有不稳定情况。

3. **Calico 组件重启频繁**：calico-node Pod 重启了 12-13 次，这可能影响网络稳定性。

根据五层模型，节点 taint 问题属于 L1（集群节点层），控制平面组件重启频繁也属于 L1 范畴。

```json
{
  "layer": "L1",
  "layers": ["L1"],
  "layer_name": "集群节点层",
  "confidence": 0.9,
  "reasoning": "1. node2 节点存在 test-unschedulable=true:NoSchedule taint，导致 Pod 无法调度（Pending）。2. 控制平面组件（kube-scheduler、kube-controller-manager、etcd、kube-apiserver）重启频繁（13-38次），表明集群节点层存在稳定性问题。3. Calico 网络组件也重启频繁（12-13次），可能影响网络稳定性。",
  "key_entities": [
    {"type": "Node", "value": "node2"},
    {"type": "Pod", "value": "l1-test-nginx-6c69dc7c76-fwzgn"},
    {"type": "Namespace", "value": "aiops-e2e"},
    {"type": "Pod", "value": "kube-scheduler-master"},
    {"type": "Namespace", "value": "kube-system"},
    {"type": "Pod", "value": "kube-controller-manager-master"},
    {"type": "Namespace", "value": "kube-system"}
  ],
  "possible_scenarios": ["节点 taint 导致调度失败", "控制平面组件不稳定", "网络组件频繁重启"]
}
```
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (2m 0.6s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=['节点 taint 导致调度失败', '控制平面组件不稳定', '网络组件频繁重启']
   entities=[{"type": "Node", "value": "node2"}, {"type": "Pod", "value": "l1-test-nginx-6c69dc7c76-fwzgn"}, {"type": "Namespace", "value": "aiops-e2e"}, {"type": "Pod", "value": "kube-scheduler-master"}, {"type": "Namespace", "value": "kube-system"}, {"type": "Pod", "value": "kube-controller-manager-master"}, {"type": "Namespace", "value": "kube-system"}]
   reasoning=1. node2 节点存在 test-unschedulable=true:NoSchedule taint，导致 Pod 无法调度（Pending）。2. 控制平面组件（kube-scheduler、kube-controller-manager、etcd、kube-apiserver）重启频繁（13-38次），表明集群节点层存在稳定性问题。3. Calico 网络组件也重启频繁（12-13次），可能影响网络稳定性。
   layer_analysis={"layer": "L1", "layers": ["L1"], "layer_name": "集群节点层", "confidence": 0.9, "reasoning": "1. node2 节点存在 test-unschedulable=true:NoSchedule taint，导致 Pod 无法调度（Pending）。2. 控制平面组件（kube-scheduler、kube-controller-manager、etcd、kube-apiserver）重启频繁（13-38次），表明集群节点层存在稳定性问题。3. Calico 网络组件也重启频繁（12-13次），可能影响网络稳定性。", "key_entities": [{"type": "Node", "value": "node2"}, {"type": "Pod", "value": "l1-test-nginx-6c69dc7c76-fwzgn"}, {"type": "Namespace", "value": "aiops-e2e"}, {"type": "Pod", "value": "kube-scheduler-master"}, {"type": "Namespace", "value": "kube-system"}, {"type": "Pod", "value": "kube-controller-manager-master"}, {"type": "Namespace", "value": "kube-system"}], "possible_scenarios": ["节点 taint 导致调度失败", "控制平面组件不稳定", "网络组件频繁重启"]}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 90%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 根据上游定位结果，您的集群存在多个问题。我将制定证据采集计划并执行工具采集真实数据。

```json
{
  "layer": "L1",
  "evidence_plan": [
    {
      "id": "e1",
      "description": "确认节点污点状态",
      "level": "critical",
      "tool": "kubectl_describe",
      "command": "kubectl describe node node2",
      "purpose": "确认 node2 节点是否存在 test-unschedulable=true:NoSchedule 污点"
    },
    {
      "id": "e2",
      "description": "检查 Pending Pod 的详细状态",
      "level": "critical",
      "tool": "kubectl_describe",
      "command": "kubectl describe pod l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e",
      "purpose": "确认 Pod 调度失败的具体原因和事件"
    },
    {
      "id": "e3",
      "description": "检查控制平面组件重启情况",
      "level": "important",
      "tool": "kubectl_describe",
      "command": "kubectl describe pod kube-scheduler-master -n kube-system",
      "purpose": "确认 kube-scheduler 重启原因和退出码"
    },
    {
      "id": "e4",
      "description": "检查控制器管理器重启情况",
      "level": "important",
      "tool": "kubectl_describe",
      "command": "kubectl describe pod kube-controller-manager-master -n kube-system",
      "purpose": "确认 kube-controller-manager 重启原因和退出码"
    },
    {
      "id": "e5",
      "description": "检查 etcd 重启情况",
      "level": "important",
      "tool": "kubectl_describe",
      "command": "kubectl describe pod etcd-master -n kube-system",
      "purpose": "确认 etcd 重启原因和退出码"
    },
    {
      "id": "e6",
      "description": "检查 Calico 网络组件重启情况",
      "level": "important",
      "tool": "kubernetes_jq_query",
      "command": "kubectl get pods -n kube-system -o json | jq -r '.items[] | select(.metadata.name | startswith(\"calico-node\")) | {name: .metadata.name, restarts: (.status.containerStatuses[0].restartCount // 0), state: .status.containerStatuses[0].state}'",
      "purpose": "确认所有 Calico 节点的重启次数和当前状态"
    },
    {
      "id": "e7",
      "description": "检查集群事件",
      "level": "optional",
      "tool": "kubectl_get_by_kind_in_cluster",
      "command": "kubectl get events -A",
      "purpose": "查看集群范围内的重要事件和警告"
    }
  ],
  "collection_strategy": "首先确认污点导致的调度问题，然后深入调查控制平面和网络组件频繁重启的根本原因"
}
```

现在开始逐项执行证据采集：
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:               node2
Roles:              <none>
Labels:             beta.kubernetes.io/arch=amd64
                    beta.kubernetes.io/os=linux
                    kubernetes.io/arch=amd64
    
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:             l1-test-nginx-6c69dc7c76-fwzgn
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             <none>
Labels:           app=nginx
                  e2e-te
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:                 kube-scheduler-master
Namespace:            kube-system
Priority:             2000001000
Priority Class Name:  system-node-critical
Node:                 master/10.2.0.48
Start T
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:                 kube-controller-manager-master
Namespace:            kube-system
Priority:             2000001000
Priority Class Name:  system-node-critical
Node:                 master/10.2.0.4
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:                 etcd-master
Namespace:            kube-system
Priority:             2000001000
Priority Class Name:  system-node-critical
Node:                 master/10.2.0.48
Start Time:      
   💭 [证据链采集] 调用工具: kubernetes_jq_query
   💭 [证据链采集] 工具结果: kubernetes_jq_query (success)
      📄 Executing jq query for pods...
{
  "name": "calico-node-4kp26",
  "namespace": "kube-system",
  "node": "master",
  "restarts": 12,
  "state": {
    "running": {
      "startedAt": "2026-04-17T07:03:4
   ✅ [证据链采集] 完成 (49.1s)
   📤 → 下游数据: evidence_items=6/7
   evidence_analysis={"evidence_plan": [{"id": "e1", "description": "确认节点污点状态", "level": "critical", "tool": "kubectl_describe", "command": "kubectl describe node node2", "purpose": "确认 node2 节点是否存在 test-unschedulable=true:NoSchedule 污点"}, {"id": "e2", "description": "检查 Pending Pod 的详细状态", "level": "critical", "tool": "kubectl_describe", "command": "kubectl describe pod l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e", "purpose": "确认 Pod 调度失败的具体原因和事件"}, {"id": "e3", "description": "检查控制平面组件重启情况", "level": "important", "tool": "kubectl_describe", "command": "kubectl describe pod kube-scheduler-master -n kube-system", "purpose": "确认 kube-scheduler 重启原因和退出码"}, {"id": "e4", "description": "检查控制器管理器重启情况", "level": "important", "tool": "kubectl_describe", "command": "kubectl describe pod kube-controller-manager-master -n kube-system", "purpose": "确认 kube-controller-manager 重启原因和退出码"}, {"id": "e5", "description": "检查 etcd 重启情况", "level": "important", "tool": "kubectl_describe", "command": "kubectl describe pod etcd-master -n kube-system", "purpose": "确认 etcd 重启原因和退出码"}, {"id": "e6", "description": "检查 Calico 网络组件重启情况", "level": "important", "tool": "kubernetes_jq_query", "command": "kubectl get pods -n kube-system -o json | jq -r '.items[] | select(.metadata.name | startswith(\"calico-node\")) | {name: .metadata.name, restarts: (.status.containerStatuses[0].restartCount // 0), state: .status.containerStatuses[0].state}'", "purpose": "确认所有 Calico 节点的重启次数和当前状态"}, {"id": "e7", "description": "检查集群事件", "level": "optional", "tool": "kubectl_get_by_kind_in_cluster", "command": "kubectl get events -A", "purpose": "查看集群范围内的重要事件和警告"}], "tool_results": [], "tool_data": [{"tool": "kubectl_describe", "data": "Name:               node2\nRoles:              <none>\nLabels:             beta.kubernetes.io/arch=amd64\n                    beta.kubernetes.io/os=linux\n                    kubernetes.io/arch=amd64\n                    kubernetes.io/hostname=node2\n                    kubernetes.io/os=linux\nAnnotations:        kubeadm.alpha.kubernetes.io/cri-socket: unix:///var/run/containerd/containerd.sock\n                    node.alpha.kubernetes.io/ttl: 0\n                    projectcalico.org/IPv4Address: 10.2.0.50/19\n                    projectcalico.org/IPv4IPIPTunnelAddr: 172.16.104.0\n                    volumes.kubernetes.io/controller-managed-attach-detach: true\nCreationTimestamp:  Thu, 25 Sep 2025 03:10:26 +0000\nTaints:             test-unschedulable=true:NoSchedule\nUnschedulable:      false\nLease:\n  HolderIdentity:  node2\n  AcquireTime:     <unset>\n  RenewTime:       Wed, 22 Apr 2026 07:00:03 +0000\nConditions:\n  Type                 Status  LastHeartbeatTime                 LastTransitionTime                Reason                       Message\n  ----                 ------  -----------------                 ------------------                ------                       -------\n  NetworkUnavailable   False   Fri, 17 Apr 2026 07:03:52 +0000   Fri, 17 Apr 2026 07:03:52 +0000   CalicoIsUp                   Calico is running on this node\n  MemoryPressure       False   Wed, 22 Apr 2026 06:57:10 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletHasSufficientMemory   kubelet has sufficient memory available\n  DiskPressure         False   Wed, 22 Apr 2026 06:57:10 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletHasNoDiskPressure     kubelet has no disk pressure\n  PIDPressure          False   Wed, 22 Apr 2026 06:57:10 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletHasSufficientPID      kubelet has sufficient PID available\n  Ready                True    Wed, 22 Apr 2026 06:57:10 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletReady                 kubelet is posting ready status. AppArmor enabled\nAddresses:\n  InternalIP:  10.2.0.50\n  Hostname:    node2\nCapacity:\n  cpu:                12\n  ephemeral-storage:  203770680Ki\n  hugepages-1Gi:      0\n  hugepages-2Mi:      0\n  memory:             32860484Ki\n  pods:               110\nAllocatable:\n  cpu:                12\n  ephemeral-storage:  187795058378\n  hugepages-1Gi:      0\n  hugepages-2Mi:      0\n  memory:             32758084Ki\n  pods:               110\nSystem Info:\n  Machine ID:                 6bb27862c82149418d0f5624411d0b22\n  System UUID:                0f5af30a-d385-493c-bc8b-5442fd024eee\n  Boot ID:                    0ea98079-ad10-4a20-85f5-19b34afd257e\n  Kernel Version:             5.15.0-174-generic\n  OS Image:                   Ubuntu 22.04.4 LTS\n  Operating System:           linux\n  Architecture:               amd64\n  Container Runtime Version:  containerd://1.6.32\n  Kubelet Version:            v1.26.8\n  Kube-Proxy Version:         v1.26.8\nNon-terminated Pods:          (14 in total)\n  Namespace                   Name                                            CPU Requests  CPU Limits  Memory Requests  Memory Limits  Age\n  ---------                   ----                                            ------------  ----------  ---------------  -------------  ---\n  aiops                       aiops-copilot-76779bb6df-4bcrf                  250m (2%)     1 (8%)      512Mi (1%)       2Gi (6%)       5h22m\n  default                     exec-test                                       0 (0%)        0 (0%)      0 (0%)           0 (0%)         2d3h\n  default                     network-test-from-running                       0 (0%)        0 (0%)      0 (0%)           0 (0%)         2d1h\n  default                     nfs-client-provisioner-6fcd4994c9-lczf6         0 (0%)        0 (0%)      0 (0%)           0 (0%)         85d\n  kube-system                 calico-node-d2dhp                               250m (2%)     0 (0%)      0 (0%)           0 (0%)         183d\n  kube-system                 kube-multus-ds-x7h9s                            100m (0%)     100m (0%)   50Mi (0%)        50Mi (0%)      183d\n  kube-system                 kube-proxy-69zzr                                0 (0%)        0 (0%)      0 (0%)           0 (0%)         28d\n  mcp                         mcp-server-manager-8677f6896c-d4mr9             200m (1%)     1 (8%)      1G (2%)          2560Mi (8%)    45h\n  xnet                        deepflow-agent-trc8k                            100m (0%)     1 (8%)      128Mi (0%)       768Mi (2%)     19d\n  xnet                        ham-p9dxv                                       0 (0%)        0 (0%)      0 (0%)           0 (0%)         177d\n  xnet                        observability-filebeat-w6gtr                    100m (0%)     1 (8%)      100Mi (0%)       200Mi (0%)     19d\n  xnet                        observability-kepler-ggstf                      0 (0%)        0 (0%)      0 (0%)           0 (0%)         19d\n  xnet                        observability-prometheus-node-exporter-qp2qd    0 (0%)        0 (0%)      0 (0%)           0 (0%)         19d\n  xnet                        xnet-agent-568f547566-jdsgp                     0 (0%)        0 (0%)      0 (0%)           0 (0%)         108d\nAllocated resources:\n  (Total limits may be over 100 percent, i.e., overcommitted.)\n  Resource           Requests         Limits\n  --------           --------         ------\n  cpu                1 (8%)           4100m (34%)\n  memory             1828375040 (5%)  5626Mi (17%)\n  ephemeral-storage  0 (0%)           0 (0%)\n  hugepages-1Gi      0 (0%)           0 (0%)\n  hugepages-2Mi      0 (0%)           0 (0%)\nEvents:              <none>", "duration_s": 0}, {"tool": "kubectl_describe", "data": "Name:             l1-test-nginx-6c69dc7c76-fwzgn\nNamespace:        aiops-e2e\nPriority:         0\nService Account:  default\nNode:             <none>\nLabels:           app=nginx\n                  e2e-test=true\n                  pod-template-hash=6c69dc7c76\nAnnotations:      <none>\nStatus:           Pending\nIP:               \nIPs:              <none>\nControlled By:    ReplicaSet/l1-test-nginx-6c69dc7c76\nContainers:\n  nginx:\n    Image:        nginx:alpine\n    Port:         <none>\n    Host Port:    <none>\n    Environment:  <none>\n    Mounts:\n      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-ww78k (ro)\nConditions:\n  Type           Status\n  PodScheduled   False \nVolumes:\n  kube-api-access-ww78k:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    TokenExpirationSeconds:  3607\n    ConfigMapName:           kube-root-ca.crt\n    ConfigMapOptional:       <nil>\n    DownwardAPI:             true\nQoS Class:                   BestEffort\nNode-Selectors:              kubernetes.io/hostname=node2\nTolerations:                 node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\n                             node.kubernetes.io/unreachable:NoExecute op=Exists for 300s\nEvents:\n  Type     Reason            Age    From               Message\n  ----     ------            ----   ----               -------\n  Warning  FailedScheduling  8m44s  default-scheduler  0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  3m36s  default-scheduler  0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..", "duration_s": 0}, {"tool": "kubectl_describe", "data": "Name:                 kube-scheduler-master\nNamespace:            kube-system\nPriority:             2000001000\nPriority Class Name:  system-node-critical\nNode:                 master/10.2.0.48\nStart Time:           Thu, 16 Apr 2026 02:25:00 +0000\nLabels:               component=kube-scheduler\n                      tier=control-plane\nAnnotations:          kubernetes.io/config.hash: 72bfebd94b72414618c5ea0c9fbb85bc\n                      kubernetes.io/config.mirror: 72bfebd94b72414618c5ea0c9fbb85bc\n                      kubernetes.io/config.seen: 2025-09-25T11:04:20.467283329+08:00\n                      kubernetes.io/config.source: file\nStatus:               Running\nSeccompProfile:       RuntimeDefault\nIP:                   10.2.0.48\nIPs:\n  IP:           10.2.0.48\nControlled By:  Node/master\nContainers:\n  kube-scheduler:\n    Container ID:  containerd://129d5e39c8a18565511625fc40111ba601a01763e049497cf4450b823f30e72a\n    Image:         xnet.registry.io:8443/k8s/registry.k8s.io/kube-scheduler:v1.26.8\n    Image ID:      xnet.registry.io:8443/k8s/registry.k8s.io/kube-scheduler@sha256:6366da41955a8e855d4788e7e443545e9e84bc790ff4ec5e81c12e01bee8d214\n    Port:          <none>\n    Host Port:     <none>\n    Command:\n      kube-scheduler\n      --authentication-kubeconfig=/etc/kubernetes/scheduler.conf\n      --authorization-kubeconfig=/etc/kubernetes/scheduler.conf\n      --bind-address=127.0.0.1\n      --kubeconfig=/etc/kubernetes/scheduler.conf\n      --leader-elect=true\n    State:          Running\n      Started:      Fri, 17 Apr 2026 07:03:37 +0000\n    Last State:     Terminated\n      Reason:       Unknown\n      Exit Code:    255\n      Started:      Thu, 16 Apr 2026 03:06:13 +0000\n      Finished:     Fri, 17 Apr 2026 07:03:26 +0000\n    Ready:          True\n    Restart Count:  38\n    Requests:\n      cpu:        100m\n    Liveness:     http-get https://127.0.0.1:10259/healthz delay=10s timeout=15s period=10s #success=1 #failure=8\n    Startup:      http-get https://127.0.0.1:10259/healthz delay=10s timeout=15s period=10s #success=1 #failure=24\n    Environment:  <none>\n    Mounts:\n      /etc/kubernetes/scheduler.conf from kubeconfig (ro)\nConditions:\n  Type              Status\n  Initialized       True \n  Ready             True \n  ContainersReady   True \n  PodScheduled      True \nVolumes:\n  kubeconfig:\n    Type:          HostPath (bare host directory volume)\n    Path:          /etc/kubernetes/scheduler.conf\n    HostPathType:  FileOrCreate\nQoS Class:         Burstable\nNode-Selectors:    <none>\nTolerations:       :NoExecute op=Exists\nEvents:            <none>", "duration_s": 0}, {"tool": "kubectl_describe", "data": "Name:                 kube-controller-manager-master\nNamespace:            kube-system\nPriority:             2000001000\nPriority Class Name:  system-node-critical\nNode:                 master/10.2.0.48\nStart Time:           Thu, 26 Mar 2026 06:29:41 +0000\nLabels:               component=kube-controller-manager\n                      tier=control-plane\nAnnotations:          kubernetes.io/config.hash: b1691284519b54204c6fcbc5b5f0fcee\n                      kubernetes.io/config.mirror: b1691284519b54204c6fcbc5b5f0fcee\n                      kubernetes.io/config.seen: 2025-09-25T11:04:25.758461328+08:00\n                      kubernetes.io/config.source: file\nStatus:               Running\nSeccompProfile:       RuntimeDefault\nIP:                   10.2.0.48\nIPs:\n  IP:           10.2.0.48\nControlled By:  Node/master\nContainers:\n  kube-controller-manager:\n    Container ID:  containerd://9ed3565dd0b992baed8aa2d3ec66834e05766b3baeb4471f6ff6974e1b3b42bc\n    Image:         xnet.registry.io:8443/k8s/registry.k8s.io/kube-controller-manager:v1.26.8\n    Image ID:      xnet.registry.io:8443/k8s/registry.k8s.io/kube-controller-manager@sha256:1fa317adf598d8af53e8cb14d75e210572cecec94685157a18834be1358d5b18\n    Port:          <none>\n    Host Port:     <none>\n    Command:\n      kube-controller-manager\n      --authentication-kubeconfig=/etc/kubernetes/controller-manager.conf\n      --authorization-kubeconfig=/etc/kubernetes/controller-manager.conf\n      --bind-address=127.0.0.1\n      --client-ca-file=/etc/kubernetes/pki/ca.crt\n      --cluster-name=kubernetes\n      --cluster-signing-cert-file=/etc/kubernetes/pki/ca.crt\n      --cluster-signing-key-file=/etc/kubernetes/pki/ca.key\n      --controllers=*,bootstrapsigner,tokencleaner\n      --kubeconfig=/etc/kubernetes/controller-manager.conf\n      --leader-elect=true\n      --requestheader-client-ca-file=/etc/kubernetes/pki/front-proxy-ca.crt\n      --root-ca-file=/etc/kubernetes/pki/ca.crt\n      --service-account-private-key-file=/etc/kubernetes/pki/sa.key\n      --use-service-account-credentials=true\n    State:          Running\n      Started:      Fri, 17 Apr 2026 07:03:37 +0000\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    2\n      Started:      Thu, 16 Apr 2026 03:06:13 +0000\n      Finished:     Fri, 17 Apr 2026 06:53:41 +0000\n    Ready:          True\n    Restart Count:  36\n    Requests:\n      cpu:        200m\n    Liveness:     http-get https://127.0.0.1:10257/healthz delay=10s timeout=15s period=10s #success=1 #failure=8\n    Startup:      http-get https://127.0.0.1:10257/healthz delay=10s timeout=15s period=10s #success=1 #failure=24\n    Environment:  <none>\n    Mounts:\n      /etc/ca-certificates from etc-ca-certificates (ro)\n      /etc/kubernetes/controller-manager.conf from kubeconfig (ro)\n      /etc/kubernetes/pki from k8s-certs (ro)\n      /etc/pki from etc-pki (ro)\n      /etc/ssl/certs from ca-certs (ro)\n      /usr/libexec/kubernetes/kubelet-plugins/volume/exec from flexvolume-dir (rw)\n      /usr/local/share/ca-certificates from usr-local-share-ca-certificates (ro)\n      /usr/share/ca-certificates from usr-share-ca-certificates (ro)\nConditions:\n  Type              Status\n  Initialized       True \n  Ready             True \n  ContainersReady   True \n  PodScheduled      True \nVolumes:\n  ca-certs:\n    Type:          HostPath (bare host directory volume)\n    Path:          /etc/ssl/certs\n    HostPathType:  DirectoryOrCreate\n  etc-ca-certificates:\n    Type:          HostPath (bare host directory volume)\n    Path:          /etc/ca-certificates\n    HostPathType:  DirectoryOrCreate\n  etc-pki:\n    Type:          HostPath (bare host directory volume)\n    Path:          /etc/pki\n    HostPathType:  DirectoryOrCreate\n  flexvolume-dir:\n    Type:          HostPath (bare host directory volume)\n    Path:          /usr/libexec/kubernetes/kubelet-plugins/volume/exec\n    HostPathType:  DirectoryOrCreate\n  k8s-certs:\n    Type:          HostPath (bare host directory volume)\n    Path:          /etc/kubernetes/pki\n    HostPathType:  DirectoryOrCreate\n  kubeconfig:\n    Type:          HostPath (bare host directory volume)\n    Path:          /etc/kubernetes/controller-manager.conf\n    HostPathType:  FileOrCreate\n  usr-local-share-ca-certificates:\n    Type:          HostPath (bare host directory volume)\n    Path:          /usr/local/share/ca-certificates\n    HostPathType:  DirectoryOrCreate\n  usr-share-ca-certificates:\n    Type:          HostPath (bare host directory volume)\n    Path:          /usr/share/ca-certificates\n    HostPathType:  DirectoryOrCreate\nQoS Class:         Burstable\nNode-Selectors:    <none>\nTolerations:       :NoExecute op=Exists\nEvents:            <none>", "duration_s": 0}, {"tool": "kubectl_describe", "data": "Name:                 etcd-master\nNamespace:            kube-system\nPriority:             2000001000\nPriority Class Name:  system-node-critical\nNode:                 master/10.2.0.48\nStart Time:           Thu, 26 Mar 2026 06:29:41 +0000\nLabels:               component=etcd\n                      tier=control-plane\nAnnotations:          kubeadm.kubernetes.io/etcd.advertise-client-urls: https://10.2.0.48:2379\n                      kubernetes.io/config.hash: 3b8118962619d42f7240703c01c1db82\n                      kubernetes.io/config.mirror: 3b8118962619d42f7240703c01c1db82\n                      kubernetes.io/config.seen: 2025-09-25T11:04:25.758455565+08:00\n                      kubernetes.io/config.source: file\nStatus:               Running\nSeccompProfile:       RuntimeDefault\nIP:                   10.2.0.48\nIPs:\n  IP:           10.2.0.48\nControlled By:  Node/master\nContainers:\n  etcd:\n    Container ID:  containerd://269f0c5bf49a29535de4eef4ea22082828fc179802e5b41cbb2c06e0e2c1dd34\n    Image:         xnet.registry.io:8443/k8s/registry.k8s.io/etcd:3.5.6-0\n    Image ID:      xnet.registry.io:8443/k8s/registry.k8s.io/etcd@sha256:8bc59eb31110952ce6555623b989d4f45fabc2e6dab7c06ca56d1ab0224ba0b2\n    Port:          <none>\n    Host Port:     <none>\n    Command:\n      etcd\n      --advertise-client-urls=https://10.2.0.48:2379\n      --cert-file=/etc/kubernetes/pki/etcd/server.crt\n      --client-cert-auth=true\n      --data-dir=/var/lib/etcd\n      --experimental-initial-corrupt-check=true\n      --experimental-watch-progress-notify-interval=5s\n      --initial-advertise-peer-urls=https://10.2.0.48:2380\n      --initial-cluster=master=https://10.2.0.48:2380\n      --key-file=/etc/kubernetes/pki/etcd/server.key\n      --listen-client-urls=https://127.0.0.1:2379,https://10.2.0.48:2379\n      --listen-metrics-urls=http://127.0.0.1:2381\n      --listen-peer-urls=https://10.2.0.48:2380\n      --name=master\n      --peer-cert-file=/etc/kubernetes/pki/etcd/peer.crt\n      --peer-client-cert-auth=true\n      --peer-key-file=/etc/kubernetes/pki/etcd/peer.key\n      --peer-trusted-ca-file=/etc/kubernetes/pki/etcd/ca.crt\n      --snapshot-count=10000\n      --trusted-ca-file=/etc/kubernetes/pki/etcd/ca.crt\n    State:          Running\n      Started:      Fri, 17 Apr 2026 07:03:37 +0000\n    Last State:     Terminated\n      Reason:       Completed\n      Exit Code:    0\n      Started:      Thu, 16 Apr 2026 03:06:13 +0000\n      Finished:     Fri, 17 Apr 2026 06:53:41 +0000\n    Ready:          True\n    Restart Count:  13\n    Requests:\n      cpu:        100m\n      memory:     100Mi\n    Liveness:     http-get http://127.0.0.1:2381/health%3Fexclude=NOSPACE&serializable=true delay=10s timeout=15s period=10s #success=1 #failure=8\n    Startup:      http-get http://127.0.0.1:2381/health%3Fserializable=false delay=10s timeout=15s period=10s #success=1 #failure=24\n    Environment:  <none>\n    Mounts:\n      /etc/kubernetes/pki/etcd from etcd-certs (rw)\n      /var/lib/etcd from etcd-data (rw)\nConditions:\n  Type              Status\n  Initialized       True \n  Ready             True \n  ContainersReady   True \n  PodScheduled      True \nVolumes:\n  etcd-certs:\n    Type:          HostPath (bare host directory volume)\n    Path:          /etc/kubernetes/pki/etcd\n    HostPathType:  DirectoryOrCreate\n  etcd-data:\n    Type:          HostPath (bare host directory volume)\n    Path:          /var/lib/etcd\n    HostPathType:  DirectoryOrCreate\nQoS Class:         Burstable\nNode-Selectors:    <none>\nTolerations:       :NoExecute op=Exists\nEvents:            <none>", "duration_s": 0}, {"tool": "kubernetes_jq_query", "data": "Executing jq query for pods...\n{\n  \"name\": \"calico-node-4kp26\",\n  \"namespace\": \"kube-system\",\n  \"node\": \"master\",\n  \"restarts\": 12,\n  \"state\": {\n    \"running\": {\n      \"startedAt\": \"2026-04-17T07:03:48Z\"\n    }\n  },\n  \"ready\": true\n}\n{\n  \"name\": \"calico-node-d2dhp\",\n  \"namespace\": \"kube-system\",\n  \"node\": \"node2\",\n  \"restarts\": 13,\n  \"state\": {\n    \"running\": {\n      \"startedAt\": \"2026-04-17T07:03:51Z\"\n    }\n  },\n  \"ready\": true\n}\n{\n  \"name\": \"calico-node-mnrjs\",\n  \"namespace\": \"kube-system\",\n  \"node\": \"node1\",\n  \"restarts\": 12,\n  \"state\": {\n    \"running\": {\n      \"startedAt\": \"2026-04-17T07:04:20Z\"\n    }\n  },\n  \"ready\": true\n}", "duration_s": 0}], "llm_analysis": "根据上游定位结果，您的集群存在多个问题。我将制定证据采集计划并执行工具采集真实数据。\n\n```json\n{\n  \"layer\": \"L1\",\n  \"evidence_plan\": [\n    {\n      \"id\": \"e1\",\n      \"description\": \"确认节点污点状态\",\n      \"level\": \"critical\",\n      \"tool\": \"kubectl_describe\",\n      \"command\": \"kubectl describe node node2\",\n      \"purpose\": \"确认 node2 节点是否存在 test-unschedulable=true:NoSchedule 污点\"\n    },\n    {\n      \"id\": \"e2\",\n      \"description\": \"检查 Pending Pod 的详细状态\",\n      \"level\": \"critical\",\n      \"tool\": \"kubectl_describe\",\n      \"command\": \"kubectl describe pod l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e\",\n      \"purpose\": \"确认 Pod 调度失败的具体原因和事件\"\n    },\n    {\n      \"id\": \"e3\",\n      \"description\": \"检查控制平面组件重启情况\",\n      \"level\": \"important\",\n      \"tool\": \"kubectl_describe\",\n      \"command\": \"kubectl describe pod kube-scheduler-master -n kube-system\",\n      \"purpose\": \"确认 kube-scheduler 重启原因和退出码\"\n    },\n    {\n      \"id\": \"e4\",\n      \"description\": \"检查控制器管理器重启情况\",\n      \"level\": \"important\",\n      \"tool\": \"kubectl_describe\",\n      \"command\": \"kubectl describe pod kube-controller-manager-master -n kube-system\",\n      \"purpose\": \"确认 kube-controller-manager 重启原因和退出码\"\n    },\n    {\n      \"id\": \"e5\",\n      \"description\": \"检查 etcd 重启情况\",\n      \"level\": \"important\",\n      \"tool\": \"kubectl_describe\",\n      \"command\": \"kubectl describe pod etcd-master -n kube-system\",\n      \"purpose\": \"确认 etcd 重启原因和退出码\"\n    },\n    {\n      \"id\": \"e6\",\n      \"description\": \"检查 Calico 网络组件重启情况\",\n      \"level\": \"important\",\n      \"tool\": \"kubernetes_jq_query\",\n      \"command\": \"kubectl get pods -n kube-system -o json | jq -r '.items[] | select(.metadata.name | startswith(\\\"calico-node\\\")) | {name: .metadata.name, restarts: (.status.containerStatuses[0].restartCount // 0), state: .status.containerStatuses[0].state}'\",\n      \"purpose\": \"确认所有 Calico 节点的重启次数和当前状态\"\n    },\n    {\n      \"id\": \"e7\",\n      \"description\": \"检查集群事件\",\n      \"level\": \"optional\",\n      \"tool\": \"kubectl_get_by_kind_in_cluster\",\n      \"command\": \"kubectl get events -A\",\n      \"purpose\": \"查看集群范围内的重要事件和警告\"\n    }\n  ],\n  \"collection_strategy\": \"首先确认污点导致的调度问题，然后深入调查控制平面和网络组件频繁重启的根本原因\"\n}\n```\n\n现在开始逐项执行证据采集：", "collection_summary": "计划 7 项，实际采集 6 项，未采集 1 项，完整度 86%", "evidence_inventory": [{"id": "e1", "description": "确认节点污点状态", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e2", "description": "检查 Pending Pod 的详细状态", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e3", "description": "检查控制平面组件重启情况", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e4", "description": "检查控制器管理器重启情况", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e5", "description": "检查 etcd 重启情况", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e6", "description": "检查 Calico 网络组件重启情况", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e7", "description": "检查集群事件", "level": "optional", "collected": false, "source": "planned"}], "missing_reasons": ["e7(检查集群事件): 已规划但工具执行失败或无匹配结果"], "early_stop": {"triggered": true, "reason": "critical 和 important 级证据均已满足，提前停止后续采集", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 6/7 项, 完整度: 86%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 13.8s)
   📤 → 下游数据: root_cause=
   confidence=85%
   causal_chain={"root_cause": "集群 master 节点 (`10.2.0.48`) 经历了不稳定的运行状态，可能由于硬件问题、系统负载过高、内核问题或计划外重启，导致运行在其上的所有静态 Pod（包括控制平面组件和 Calico）被反复终止和重启。同时，存在针对节点 `node2` 的人工或自动化运维操作，为其添加了 `test-unschedulable=true:NoSchedule` 污点。", "propagation": "1) Master 节点不稳定 → kubelet 重启 → 所有静态 Pod (kube-apiserver, etcd, kube-scheduler, kube-controller-manager, calico-node) 重启。2) 节点污点设置 → 调度器过滤节点 → 无法匹配污点容忍度的 Pod 调度失败。", "direct_cause": "1) Pod `l1-test-nginx-6c69dc7c76-fwzgn` 调度失败的直接原因是其节点选择器指定了 `node2`，但 `node2` 存在 `test-unschedulable` 污点且 Pod 未容忍该污点。2) 控制平面和网络组件频繁重启的直接原因是它们所运行的 master 节点经历了不稳定性事件。", "manifestation": "1) Pod `l1-test-nginx-6c69dc7c76-fwzgn` 状态为 Pending。2) 核心组件 Pod (`kube-scheduler-master`, `kube-controller-manager-master`, `etcd-master`, `kube-apiserver-master`) 重启次数异常（13-38次）。3) 网络组件 Pod (`calico-node-*`) 在所有节点上重启频繁（12-13次）。"}
   rca_analysis={"phenomenon": "集群存在两个主要问题：1) Pod `l1-test-nginx-6c69dc7c76-fwzgn` 处于 Pending 状态，无法调度；2) 多个核心控制平面组件和网络组件频繁重启，表明集群控制层和网络层存在稳定性问题。", "evidence_inventory": [{"id": "e1", "content": "节点 node2 存在污点 `test-unschedulable=true:NoSchedule`，节点状态 Ready，资源充足。", "source": "kubectl describe node node2", "reliability": "高"}, {"id": "e2", "content": "Pod `l1-test-nginx-6c69dc7c76-fwzgn` 状态为 Pending，PodScheduled 条件为 False，事件显示调度失败原因为 `1 node(s) had untolerated taint {test-unschedulable: true}`，节点选择器为 `kubernetes.io/hostname=node2`。", "source": "kubectl describe pod l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e", "reliability": "高"}, {"id": "e3", "content": "Pod `kube-scheduler-master` 重启 38 次，最后一次终止原因为 Unknown，退出码 255，当前状态 Running。", "source": "kubectl describe pod kube-scheduler-master -n kube-system", "reliability": "高"}, {"id": "e4", "content": "Pod `kube-controller-manager-master` 重启 36 次，最后一次终止原因为 Error，退出码 2，当前状态 Running。", "source": "kubectl describe pod kube-controller-manager-master -n kube-system", "reliability": "高"}, {"id": "e5", "content": "Pod `etcd-master` 重启 13 次，最后一次终止原因为 Completed，退出码 0，当前状态 Running。", "source": "kubectl describe pod etcd-master -n kube-system", "reliability": "高"}, {"id": "e6", "content": "Calico 网络组件在所有节点上频繁重启：`calico-node-4kp26` (master) 重启 12 次，`calico-node-d2dhp` (node2) 重启 13 次，`calico-node-mnrjs` (node1) 重启 12 次。", "source": "kubernetes_jq_query (Calico pods)", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Taints: test-unschedulable=true:NoSchedule", "interpretation": "节点 node2 被手动或通过脚本添加了污点 `test-unschedulable=true:NoSchedule`，此污点会阻止没有相应容忍度的 Pod 被调度到该节点。"}, {"evidence_id": "e2", "raw_data": "Node-Selectors: kubernetes.io/hostname=node2; Events: Warning FailedScheduling ... 1 node(s) had untolerated taint {test-unschedulable: true}", "interpretation": "Pod `l1-test-nginx-6c69dc7c76-fwzgn` 通过节点选择器 (`kubernetes.io/hostname=node2`) 被强制要求调度到 node2，但由于 node2 存在 `test-unschedulable` 污点且该 Pod 没有容忍此污点，导致调度失败，Pod 处于 Pending 状态。"}, {"evidence_id": "e3", "raw_data": "Restart Count: 38; Last State: Terminated Reason: Unknown Exit Code: 255", "interpretation": "kube-scheduler 组件极不稳定，已重启 38 次。最后一次异常终止的退出码 255 通常表示进程被外部信号终止或发生了严重错误，原因标记为 Unknown，表明可能发生了非预期的崩溃或节点重启。"}, {"evidence_id": "e4", "raw_data": "Restart Count: 36; Last State: Terminated Reason: Error Exit Code: 2", "interpretation": "kube-controller-manager 组件极不稳定，已重启 36 次。退出码 2 通常表示命令行参数解析错误或配置错误，表明该组件可能因配置问题或内部错误而反复崩溃。"}, {"evidence_id": "e5", "raw_data": "Restart Count: 13; Last State: Terminated Reason: Completed Exit Code: 0", "interpretation": "etcd 组件已重启 13 次，但最后一次终止是正常退出 (Exit Code 0, Reason: Completed)。结合其与控制平面组件几乎同时重启（证据 e3, e4 显示相近的 Finished 时间），强烈暗示 master 节点曾经历过一次或多次整体重启或 kubelet 服务重启，导致所有静态 Pod 被重新启动。"}, {"evidence_id": "e6", "raw_data": "calico-node-4kp26 restarts:12, calico-node-d2dhp restarts:13, calico-node-mnrjs restarts:12", "interpretation": "Calico 网络守护进程在所有三个节点 (master, node1, node2) 上均经历了频繁重启（12-13次）。这通常与节点重启、网络配置冲突、或与底层系统（如内核模块、IPtables）的交互问题有关，会影响 Pod 间的网络连通性。"}], "causal_chain": {"root_cause": "集群 master 节点 (`10.2.0.48`) 经历了不稳定的运行状态，可能由于硬件问题、系统负载过高、内核问题或计划外重启，导致运行在其上的所有静态 Pod（包括控制平面组件和 Calico）被反复终止和重启。同时，存在针对节点 `node2` 的人工或自动化运维操作，为其添加了 `test-unschedulable=true:NoSchedule` 污点。", "propagation": "1) Master 节点不稳定 → kubelet 重启 → 所有静态 Pod (kube-apiserver, etcd, kube-scheduler, kube-controller-manager, calico-node) 重启。2) 节点污点设置 → 调度器过滤节点 → 无法匹配污点容忍度的 Pod 调度失败。", "direct_cause": "1) Pod `l1-test-nginx-6c69dc7c76-fwzgn` 调度失败的直接原因是其节点选择器指定了 `node2`，但 `node2` 存在 `test-unschedulable` 污点且 Pod 未容忍该污点。2) 控制平面和网络组件频繁重启的直接原因是它们所运行的 master 节点经历了不稳定性事件。", "manifestation": "1) Pod `l1-test-nginx-6c69dc7c76-fwzgn` 状态为 Pending。2) 核心组件 Pod (`kube-scheduler-master`, `kube-controller-manager-master`, `etcd-master`, `kube-apiserver-master`) 重启次数异常（13-38次）。3) 网络组件 Pod (`calico-node-*`) 在所有节点上重启频繁（12-13次）。"}, "root_cause_summary": "根据证据分析，集群问题的根因是复合型的：\n1.  **调度阻塞**：节点 `node2` 上存在污点 `test-unschedulable=true:NoSchedule`（证据 e1），导致指定调度到该节点的 Pod `l1-test-nginx-6c69dc7c76-fwzgn` 因无法容忍该污点而处于 `Pending` 状态（证据 e2）。\n2.  **控制平面不稳定**：Master 节点 (`10.2.0.48`) 存在严重的稳定性问题，导致运行其上的所有核心控制平面静态 Pod 频繁重启：`kube-scheduler` 重启 38 次（证据 e3），`kube-controller-manager` 重启 36 次（证据 e4），`etcd` 重启 13 次（证据 e5）。`etcd` 的正常退出和相近的终止时间点暗示了节点级或 kubelet 级的重启事件。\n3.  **网络组件不稳定**：作为 DaemonSet 部署的 `calico-node` 在所有三个节点上均频繁重启（12-13次）（证据 e6），这与控制平面不稳定可能源于同一底层节点问题，或存在独立的网络配置冲突。", "confidence": 0.85, "primary_runbooks": [], "alternative_causes": ["可能存在针对整个集群的维护操作（如节点排空、升级），同时影响了 `node2` 的污点和 master 节点的稳定性。", "`kube-controller-manager` 的退出码 2 可能指向特定的配置错误，需要检查其日志以确认。", "Calico 重启可能与特定的网络策略更新或 IP 池冲突有关。"], "limitations": "1. 证据 e7（集群事件）未成功采集，缺少全局事件视角来确认 master 节点重启的具体原因和时间线。2. 未采集控制平面组件和 Calico 的日志，无法确定其崩溃的具体错误信息。3. 未检查 `kube-apiserver-master` 的详细描述，仅从定位结果中得知其重启 13 次。4. 未检查系统日志（如 journalctl）或节点资源监控数据，无法确定 master 节点不稳定的根本原因（如内存溢出、CPU 死锁等）。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 85%
   🔗 因果链:
     根本原因: 集群 master 节点 (`10.2.0.48`) 经历了不稳定的运行状态，可能由于硬件问题、系统负载过高、内核问题或计划外重启，导致运行在其上的所有静态 Pod（包括控制平面组件和 Calico）被反复终止和重启。同时，存在针对节点 `node2` 的人工或自动化运维操作，为其添加了 `test-unschedulable=true:NoSchedule` 污点。
     传导机制: 1) Master 节点不稳定 → kubelet 重启 → 所有静态 Pod (kube-apiserver, etcd, kube-scheduler, kube-controller-manager, calico-node) 重启。2) 节点污点设置 → 调度器过滤节点 → 无法匹配污点容忍度的 Pod 调度失败。
     最终表现: 1) Pod `l1-test-nginx-6c69dc7c76-fwzgn` 状态为 Pending。2) 核心组件 Pod (`kube-scheduler-master`, `kube-controller-manager-master`, `etcd-master`, `kube-apiserver-master`) 重启次数异常（13-38次）。3) 网络组件 Pod (`calico-node-*`) 在所有节点上重启频繁（12-13次）。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 13.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6181 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 17.2s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **问题层级** | L1 - 资源与调度 |
| **问题分类** | NodeTaint、ControlPlaneUnstable |
| **置信度** | 高 (85%) |
| **证据完整度** | 6/7 (86%) |
---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `l1-test-nginx-6c69dc7c76-fwzgn` |
| Namespace | `aiops-e2e` |
| Node | `node2` (污点节点), `master` (不稳定节点) |
| 错误信息 | `1 node(s) had untolerated taint {test-unschedulable: true}` |
---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | 节点污点 | `kubectl describe node node2` | `Taints: test-unschedulable=true:NoSchedule` | 节点 `node2` 存在阻止调度的污点 |
| 2 | Pod调度失败 | `kubectl describe pod l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e` | `Node-Selectors: kubernetes.io/hostname=node2` <br> `Events: ... 1 node(s) had untolerated taint {test-unschedulable: true}` | Pod 强制调度到 `node2`，但因污点无法容忍而 `Pending` |
| 3 | 调度器重启 | `kubectl describe pod kube-scheduler-master -n kube-system` | `Restart Count: 38` <br> `Last State: Terminated Reason: Unknown Exit Code: 255` | `kube-scheduler` 极不稳定，异常退出 |
| 4 | 控制器重启 | `kubectl describe pod kube-controller-manager-master -n kube-system` | `Restart Count: 36` <br> `Last State: Terminated Reason: Error Exit Code: 2` | `kube-controller-manager` 极不稳定，配置或内部错误导致退出 |
| 5 | etcd重启 | `kubectl describe pod etcd-master -n kube-system` | `Restart Count: 13` <br> `Last State: Terminated Reason: Completed Exit Code: 0` | `etcd` 频繁重启，但为正常退出，暗示节点级重启 |
| 6 | 网络组件重启 | `kubernetes_jq_query` (Calico pods) | `calico-node-4kp26 restarts:12` <br> `calico-node-d2dhp restarts:13` <br> `calico-node-mnrjs restarts:12` | Calico 网络组件在所有节点上频繁重启 |

### 证据关联分析
- **证据 #1 + #2 印证**：节点 `node2` 存在污点 `test-unschedulable` + Pod 节点选择器指定 `node2` → Pod 调度失败，状态 `Pending`。
- **证据 #3 + #4 + #5 印证**：`kube-scheduler` (退出码255)、`kube-controller-manager` (退出码2)、`etcd` (退出码0) 均在相近时间点频繁重启，且 `etcd` 为正常退出 → 强烈暗示 **master 节点 (`10.2.0.48`) 经历了整体重启或 kubelet 服务重启**。
- **证据 #6 关联**：Calico 组件在所有节点（包括 master）上同步重启，进一步支持了节点级不稳定事件的推断。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 集群事件 (`kubectl get events -A`) | optional | 无法从全局视角确认 master 节点重启的具体原因和时间线 |
| 控制平面组件日志 | critical | 无法确定 `kube-scheduler` 和 `kube-controller-manager` 崩溃的具体错误信息 |
| 系统日志 (journalctl) | important | 无法确定 master 节点不稳定的根本原因（如硬件、内核、负载） |
---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                     │
│ 1. 节点 `node2` 被添加了 `test-unschedulable=true:NoSchedule` 污点。         │
│ 2. Master 节点 (`10.2.0.48`) 存在严重稳定性问题，导致 kubelet 或节点整体重启。 │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                     │
│ 1. 污点阻止调度 → 调度器过滤 node2 → Pod 因无容忍度而调度失败。                │
│ 2. 节点不稳定 → 所有静态 Pod (控制平面+Calico) 被终止 → kubelet 重启后重建。   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                     │
│ 1. Pod `l1-test-nginx-6c69dc7c76-fwzgn` 状态为 `Pending`。                   │
│ 2. 控制平面组件重启 13-38 次，网络组件重启 12-13 次。                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                 │
│ 1. 特定 Pod 无法运行。                                                       │
│ 2. 集群控制层和网络层存在稳定性风险。                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据链，您的集群存在两个独立但可能关联的问题：
1.  **调度阻塞**：节点 `node2` 存在污点 `test-unschedulable=true:NoSchedule`（证据 #1），导致指定调度到该节点的 Pod `l1-test-nginx-6c69dc7c76-fwzgn` 无法调度，处于 `Pending` 状态（证据 #2）。
2.  **控制平面与网络不稳定**：Master 节点 (`10.2.0.48`) 经历了严重的不稳定事件（可能为重启），导致运行其上的所有核心控制平面静态 Pod (`kube-scheduler`, `kube-controller-manager`, `etcd` 等) 频繁重启（证据 #3, #4, #5），同时网络组件 `calico-node` 也在所有节点上频繁重启（证据 #6）。

**置信度**：高 (85%)
- ✅ 污点与调度失败原因直接匹配。
- ✅ 多个核心组件几乎同时重启，且 `etcd` 为正常退出，强烈指向节点级事件。
- ⚠️ 缺少组件日志和系统日志，无法精确定位 master 节点不稳定的根本原因。
---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 移除节点污点，恢复 Pod 调度**
```bash
kubectl taint nodes node2 test-unschedulable:NoSchedule-
```
*依据*：证据 #1 显示污点是导致 Pod `l1-test-nginx-6c69dc7c76-fwzgn` 无法调度的直接原因。
*目的*：使 Pod 能够被调度到 `node2` 并运行。

**2. [优先] 检查 Master 节点稳定性并查看组件日志**
```bash
# 检查 master 节点系统负载和最近重启记录 (需要在 master 节点上执行)
uptime
journalctl --since "2026-04-16" --until "2026-04-17 07:10" | grep -E "(reboot|kubelet|Out of memory|kernel panic)"

# 查看 kube-controller-manager 崩溃前的日志 (退出码2，可能为配置错误)
kubectl logs -n kube-system kube-controller-manager-master --previous
```
*依据*：证据 #3, #4, #5 表明 master 节点不稳定，且 `kube-controller-manager` 因错误退出。
*目的*：定位节点不稳定及组件崩溃的根本原因。

### 后续优化
1.  **审查污点管理流程**：确认 `test-unschedulable` 污点的添加是计划内的维护操作还是误操作，并建立规范的污点管理流程。
2.  **加强监控告警**：对控制平面 Pod 的重启次数 (`kube_pod_container_status_restarts_total`) 和节点就绪状态设置告警。
3.  **评估节点健康度**：持续监控 master 节点的资源使用（CPU、内存、磁盘I/O），排查硬件或内核问题。
---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认污点已移除 | `kubectl describe node node2 \| grep Taints` | `Taints: <none>` |
| 2. 确认 Pod 已调度并运行 | `kubectl get pod l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e` | `STATUS: Running` |
| 3. 监控控制平面重启次数 | `kubectl get pods -n kube-system -l tier=control-plane -o jsonpath='{range .items[*]}{.metadata.name}:{.status.containerStatuses[0].restartCount}{\"\\n\"}{end}'` | 重启次数不再增加 |
| 4. 检查 Calico 节点状态 | `kubectl get pods -n kube-system -l k8s-app=calico-node -o wide` | 所有 Pod `STATUS: Running`，`READY: 1/1` |
---
## ⚠️ 注意事项
- 移除污点后，`l1-test-nginx` Pod 应能自动调度并启动。如果仍为 `Pending`，请检查其他调度约束（如资源请求）。
- Master 节点的稳定性问题是潜在风险，即使组件当前在运行，也需彻底调查根本原因，防止再次发生。
- 如果 `kube-controller-manager` 日志显示特定配置错误，可能需要修复对应的配置文件（如 `/etc/kubernetes/manifests/kube-controller-manager.yaml`）并重启 kubelet。

---

## 📊 性能统计

├─ 总耗时: 5.3m
├─ 问题定位: 120.6s (38%) ✅
├─ 证据链采集: 49.1s (15%) ✅
├─ 根因分析: 73.8s (23%) ✅
├─ 汇总总结: 73.7s (23%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 19 次
```

📋 诊断追踪

- **核心 Runbook**: private-k8s-health-reference
- **参考 Runbook**: private-k8s-health-reference
- **工具调用**: 19 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
