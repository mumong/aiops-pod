======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 1345f74578fa4472]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来先快速看一下集群的整体状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS    RESTARTS      AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     l1-test-ngin
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   209d   v1.26.8  
   💭 [问题定位] 发现有一个 Pending 的 Pod。让我进一步查看详情。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             l1-test-nginx-6c69dc7c76-fwzgn
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             <none>
Labels:           app=nginx
                  e2e-te
   💭 [问题定位] 让我也看一下集群的整体健康情况，包括关键系统组件和事件。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# 私有化 Kubernetes 环境健康与高效排查参考手册

> 类型: reference | 适用: 私有化 Kubernetes 环境 | 环境特征: Calico + NFS + containerd

## 目的

本手册不是某个具体故障的处理步骤，而是一个**额外知识参考**：
- 帮助理解在私有化 Kubernetes 环境中，健康检查应重点关注哪些资源与信号

   💭 [问题定位] 现在让我再检查一下节点是否有异常条件和系统组件状态。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:               node2
Roles:              <none>
Labels:             beta.kubernetes.io/arch=amd64
                    beta.kubernetes.io/os=linux
                    kubernetes.io/arch=amd64
    
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:               node1
Roles:              <none>
Labels:             beta.kubernetes.io/arch=amd64
                    beta.kubernetes.io/os=linux
                    kubernetes.io/arch=amd64
    
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:               master
Roles:              control-plane
Labels:             beta.kubernetes.io/arch=amd64
                    beta.kubernetes.io/os=linux
                    kubernetes.io/arch=am
   💭 [问题定位] 现在我已经有了足够的信息来做判断。让我确认一下这个 Pending Pod 的情况——它使用了 `nodeSelector` 指定了 `node2`，但 node2 有一个 `test-unschedulable=true:NoSchedule` 的 taint，且 Pod 没有对应的 toleration。

让我也快速看一下关键系统组件的健康状况。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,READY:.status.containerStatuses[0].ready' | (head -
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 NAMESPACE     NAME                                                STATUS
aiops-e2e     l1-test-nginx-6c69dc7c76-fwzgn                      Pending
aiops         aiops-copilot-76779bb6df-4bcrf         
   💭 [问题定位] 好的，所有信息已经收集完毕。以下是诊断结果：

---

```json
{
  "layer": "L1",
  "layers": ["L1"],
  "layer_name": "集群节点层",
  "confidence": 0.95,
  "reasoning": "集群存在一个明确的异常对象：aiops-e2e/l1-test-nginx-6c69dc7c76-fwzgn Pod 处于 Pending 状态。根因是 node2 节点存在 test-unschedulable=true:NoSchedule taint，而该 Pod 通过 nodeSelector 指定了 kubernetes.io/hostname=node2 但没有对应 toleration，导致调度器无法将其分配到任何节点。3个节点中：master 无 taint 但不符合 nodeSelector，node1 不符合 nodeSelector，node2 有 taint 且 Pod 无 toleration。这是一个 L1（节点层 Taint 导致不可调度）问题。除此之外，集群其他所有 Pod 均为 Running，节点均 Ready，无其他活跃异常。",
  "key_entities": [
    {"type": "Pod", "value": "l1-test-nginx-6c69dc7c76-fwzgn"},
    {"type": "Namespace", "value": "aiops-e2e"},
    {"type": "Node", "value": "node2"}
  ],
  "possible_scenarios": [
    "node2 节点被标记了 test-unschedulable=true:NoSchedule taint，导致指定调度到 node2 的 Pod 无法被调度"
  ]
}
```

### 简要说明

**只有一个活跃异常：**

| 对象 | 问题 | 层级 |
|------|------|------|
| `aiops-e2e/l1-test-nginx-6c69dc7c76-fwzgn` | **Pending** — 该 Pod 通过 `nodeSelector` 指定 `kubernetes.io/hostname=node2`，但 **node2 节点带有 `test-unschedulable=true:NoSchedule` taint**，且 Pod 没有对应的 toleration，导致调度器无法分配节点 | **L1（节点层）** |

**其他方面：**
- 3 个节点均为 **Ready**，无 MemoryPressure/DiskPressure/PIDPressure
- 所有系统组件（etcd、apiserver、coredns、calico、kube-proxy 等）均 Running
- 其余 50+ Pod 全部 Running，无 CrashLoopBackOff、OOMKilled、ImagePullBackOff 等异常

**结论：集群整体健康，只有一个已知的 L1 调度问题（node2 的 taint 导致指定调度到该节点的 Pod Pending）。** 该 Pod 是 `aiops-e2e` 命名空间下的 e2e 测试 Pod（`e2e-test=true`），可能是测试场景的一部分。
   ✅ [问题定位] 完成 (27.9s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=['node2 节点被标记了 test-unschedulable=true:NoSchedule taint，导致指定调度到 node2 的 Pod 无法被调度']
   entities=[{"type": "Pod", "value": "l1-test-nginx-6c69dc7c76-fwzgn"}, {"type": "Namespace", "value": "aiops-e2e"}, {"type": "Node", "value": "node2"}]
   reasoning=集群存在一个明确的异常对象：aiops-e2e/l1-test-nginx-6c69dc7c76-fwzgn Pod 处于 Pending 状态。根因是 node2 节点存在 test-unschedulable=true:NoSchedule taint，而该 Pod 通过 nodeSelector 指定了 kubernetes.io/hostname=node2 但没有对应 toleration，导致调度器无法将其分配到任何节点。3个节点中：master 无 taint 但不符合 nodeSelector，node1 不符合 nodeSelector，node2 有 taint 且 Pod 无 toleration。这是一个 L1（节点层 Taint 导致不可调度）问题。除此之外，集群其他所有 Pod 均为 Running，节点均 Ready，无其他活跃异常。
   layer_analysis={"layer": "L1", "layers": ["L1"], "layer_name": "集群节点层", "confidence": 0.95, "reasoning": "集群存在一个明确的异常对象：aiops-e2e/l1-test-nginx-6c69dc7c76-fwzgn Pod 处于 Pending 状态。根因是 node2 节点存在 test-unschedulable=true:NoSchedule taint，而该 Pod 通过 nodeSelector 指定了 kubernetes.io/hostname=node2 但没有对应 toleration，导致调度器无法将其分配到任何节点。3个节点中：master 无 taint 但不符合 nodeSelector，node1 不符合 nodeSelector，node2 有 taint 且 Pod 无 toleration。这是一个 L1（节点层 Taint 导致不可调度）问题。除此之外，集群其他所有 Pod 均为 Running，节点均 Ready，无其他活跃异常。", "key_entities": [{"type": "Pod", "value": "l1-test-nginx-6c69dc7c76-fwzgn"}, {"type": "Namespace", "value": "aiops-e2e"}, {"type": "Node", "value": "node2"}], "possible_scenarios": ["node2 节点被标记了 test-unschedulable=true:NoSchedule taint，导致指定调度到 node2 的 Pod 无法被调度"]}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我来分析上游的定位结果，并制定证据采集计划来深入确认这个 L1 问题。

## 第一步：输出 JSON 证据采集计划

根据上游定位，这是一个典型的 **L1 - Node Taint 导致 Pod 无法调度** 问题。我需要采集以下关键证据来确认：

```json
{
  "layer": "L1",
  "evidence_plan": [
    {
      "id": "e1",
      "description": "确认 Pending Pod 的详细信息（事件、调度器消息）",
      "level": "critical",
      "tool": "kubectl_describe",
      "command": "kubectl describe pod l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e",
      "purpose": "确认调度失败事件和调度器消息"
    },
    {
      "id": "e2",
      "description": "确认 node2 节点的 taint 配置",
      "level": "critical",
      "tool": "kubectl_describe",
      "command": "kubectl describe node node2",
      "purpose": "确认 test-unschedulable=true:NoSchedule taint 是否存在"
    },
    {
      "id": "e3",
      "description": "获取 Pending Pod 的完整 YAML 定义（含 nodeSelector 和 tolerations）",
      "level": "critical",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get -o yaml pod l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e",
      "purpose": "确认 Pod 的 nodeSelector 和 tolerations 配置"
    },
    {
      "id": "e4",
      "description": "检查 node2 节点上的所有 Pod 分布情况",
      "level": "important",
      "tool": "kubernetes_tabular_query",
      "command": "kubectl get pods -A -o wide --field-selector spec.nodeName=node2",
      "purpose": "确认 node2 上是否还有其他受影响的 Pod"
    },
    {
      "id": "e5",
      "description": "检查 node2 节点的条件和资源状态",
      "level": "important",
      "tool": "kubectl_get_by_name",
      "command": "kubectl get node node2 --show-labels -o wide",
      "purpose": "确认节点标签和状态"
    },
    {
      "id": "e6",
      "description": "检查所有节点的 taint 分布",
      "level": "important",
      "tool": "kubernetes_jq_query",
      "command": "kubectl get nodes -o json | jq ...",
      "purpose": "确认是否只有 node2 有 taint"
    }
  ],
  "collection_strategy": "先采集 critical 级证据确认根本原因，再采集 important 级证据补充完整信息"
}
```

现在开始逐项执行。

## 第二步：逐项执行工具采集证据

### e1: 确认 Pending Pod 详情
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:             l1-test-nginx-6c69dc7c76-fwzgn
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             <none>
Labels:           app=nginx
                  e2e-te
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:               node2
Roles:              <none>
Labels:             beta.kubernetes.io/arch=amd64
                    beta.kubernetes.io/os=linux
                    kubernetes.io/arch=amd64
    
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 apiVersion: v1
kind: Pod
metadata:
  creationTimestamp: "2026-04-22T06:51:29Z"
  generateName: l1-test-nginx-6c69dc7c76-
  labels:
    app: nginx
    e2e-test: "true"
    pod-template-hash: 6c69dc7c76
   💭 [证据链采集] ### e4: 检查 node2 上的所有 Pod 分布
   💭 [证据链采集] 调用工具: kubernetes_tabular_query
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubernetes_tabular_query (success)
      📄 NAMESPACE     NAME                                                STATUS    NODE
default       exec-test                                           Running   node2
default       network-test-from-runni
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
node2   Ready    <none>   209d   v1.26.8   10.2.0.50     <
   💭 [证据链采集] ### e6: 检查所有节点的 taint 分布
   💭 [证据链采集] 调用工具: kubernetes_jq_query
   💭 [证据链采集] 工具结果: kubernetes_jq_query (success)
      📄 Executing jq query for nodes...
{
  "name": "master",
  "taints": null
}
{
  "name": "node1",
  "taints": null
}
{
  "name": "node2",
  "taints": [
    {
      "effect": "NoSchedule",
      "key": "te
   ✅ [证据链采集] 完成 (16.1s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan": [{"id": "e1", "description": "确认 Pending Pod 的详细信息（事件、调度器消息）", "level": "critical", "tool": "kubectl_describe", "command": "kubectl describe pod l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e", "purpose": "确认调度失败事件和调度器消息"}, {"id": "e2", "description": "确认 node2 节点的 taint 配置", "level": "critical", "tool": "kubectl_describe", "command": "kubectl describe node node2", "purpose": "确认 test-unschedulable=true:NoSchedule taint 是否存在"}, {"id": "e3", "description": "获取 Pending Pod 的完整 YAML 定义（含 nodeSelector 和 tolerations）", "level": "critical", "tool": "kubectl_get_yaml", "command": "kubectl get -o yaml pod l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e", "purpose": "确认 Pod 的 nodeSelector 和 tolerations 配置"}, {"id": "e4", "description": "检查 node2 节点上的所有 Pod 分布情况", "level": "important", "tool": "kubernetes_tabular_query", "command": "kubectl get pods -A -o wide --field-selector spec.nodeName=node2", "purpose": "确认 node2 上是否还有其他受影响的 Pod"}, {"id": "e5", "description": "检查 node2 节点的条件和资源状态", "level": "important", "tool": "kubectl_get_by_name", "command": "kubectl get node node2 --show-labels -o wide", "purpose": "确认节点标签和状态"}, {"id": "e6", "description": "检查所有节点的 taint 分布", "level": "important", "tool": "kubernetes_jq_query", "command": "kubectl get nodes -o json | jq ...", "purpose": "确认是否只有 node2 有 taint"}], "tool_results": [], "tool_data": [{"tool": "kubectl_describe", "data": "Name:             l1-test-nginx-6c69dc7c76-fwzgn\nNamespace:        aiops-e2e\nPriority:         0\nService Account:  default\nNode:             <none>\nLabels:           app=nginx\n                  e2e-test=true\n                  pod-template-hash=6c69dc7c76\nAnnotations:      <none>\nStatus:           Pending\nIP:               \nIPs:              <none>\nControlled By:    ReplicaSet/l1-test-nginx-6c69dc7c76\nContainers:\n  nginx:\n    Image:        nginx:alpine\n    Port:         <none>\n    Host Port:    <none>\n    Environment:  <none>\n    Mounts:\n      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-ww78k (ro)\nConditions:\n  Type           Status\n  PodScheduled   False \nVolumes:\n  kube-api-access-ww78k:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    TokenExpirationSeconds:  3607\n    ConfigMapName:           kube-root-ca.crt\n    ConfigMapOptional:       <nil>\n    DownwardAPI:             true\nQoS Class:                   BestEffort\nNode-Selectors:              kubernetes.io/hostname=node2\nTolerations:                 node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\n                             node.kubernetes.io/unreachable:NoExecute op=Exists for 300s\nEvents:\n  Type     Reason            Age                From               Message\n  ----     ------            ----               ----               -------\n  Warning  FailedScheduling  26m                default-scheduler  0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  16m (x2 over 21m)  default-scheduler  0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..", "duration_s": 0}, {"tool": "kubectl_describe", "data": "Name:               node2\nRoles:              <none>\nLabels:             beta.kubernetes.io/arch=amd64\n                    beta.kubernetes.io/os=linux\n                    kubernetes.io/arch=amd64\n                    kubernetes.io/hostname=node2\n                    kubernetes.io/os=linux\nAnnotations:        kubeadm.alpha.kubernetes.io/cri-socket: unix:///var/run/containerd/containerd.sock\n                    node.alpha.kubernetes.io/ttl: 0\n                    projectcalico.org/IPv4Address: 10.2.0.50/19\n                    projectcalico.org/IPv4IPIPTunnelAddr: 172.16.104.0\n                    volumes.kubernetes.io/controller-managed-attach-detach: true\nCreationTimestamp:  Thu, 25 Sep 2025 03:10:26 +0000\nTaints:             test-unschedulable=true:NoSchedule\nUnschedulable:      false\nLease:\n  HolderIdentity:  node2\n  AcquireTime:     <unset>\n  RenewTime:       Wed, 22 Apr 2026 07:17:45 +0000\nConditions:\n  Type                 Status  LastHeartbeatTime                 LastTransitionTime                Reason                       Message\n  ----                 ------  -----------------                 ------------------                ------                       -------\n  NetworkUnavailable   False   Fri, 17 Apr 2026 07:03:52 +0000   Fri, 17 Apr 2026 07:03:52 +0000   CalicoIsUp                   Calico is running on this node\n  MemoryPressure       False   Wed, 22 Apr 2026 07:17:34 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletHasSufficientMemory   kubelet has sufficient memory available\n  DiskPressure         False   Wed, 22 Apr 2026 07:17:34 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletHasNoDiskPressure     kubelet has no disk pressure\n  PIDPressure          False   Wed, 22 Apr 2026 07:17:34 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletHasSufficientPID      kubelet has sufficient PID available\n  Ready                True    Wed, 22 Apr 2026 07:17:34 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletReady                 kubelet is posting ready status. AppArmor enabled\nAddresses:\n  InternalIP:  10.2.0.50\n  Hostname:    node2\nCapacity:\n  cpu:                12\n  ephemeral-storage:  203770680Ki\n  hugepages-1Gi:      0\n  hugepages-2Mi:      0\n  memory:             32860484Ki\n  pods:               110\nAllocatable:\n  cpu:                12\n  ephemeral-storage:  187795058378\n  hugepages-1Gi:      0\n  hugepages-2Mi:      0\n  memory:             32758084Ki\n  pods:               110\nSystem Info:\n  Machine ID:                 6bb27862c82149418d0f5624411d0b22\n  System UUID:                0f5af30a-d385-493c-bc8b-5442fd024eee\n  Boot ID:                    0ea98079-ad10-4a20-85f5-19b34afd257e\n  Kernel Version:             5.15.0-174-generic\n  OS Image:                   Ubuntu 22.04.4 LTS\n  Operating System:           linux\n  Architecture:               amd64\n  Container Runtime Version:  containerd://1.6.32\n  Kubelet Version:            v1.26.8\n  Kube-Proxy Version:         v1.26.8\nNon-terminated Pods:          (14 in total)\n  Namespace                   Name                                            CPU Requests  CPU Limits  Memory Requests  Memory Limits  Age\n  ---------                   ----                                            ------------  ----------  ---------------  -------------  ---\n  aiops                       aiops-copilot-76779bb6df-4bcrf                  250m (2%)     1 (8%)      512Mi (1%)       2Gi (6%)       5h40m\n  default                     exec-test                                       0 (0%)        0 (0%)      0 (0%)           0 (0%)         2d3h\n  default                     network-test-from-running                       0 (0%)        0 (0%)      0 (0%)           0 (0%)         2d2h\n  default                     nfs-client-provisioner-6fcd4994c9-lczf6         0 (0%)        0 (0%)      0 (0%)           0 (0%)         85d\n  kube-system                 calico-node-d2dhp                               250m (2%)     0 (0%)      0 (0%)           0 (0%)         183d\n  kube-system                 kube-multus-ds-x7h9s                            100m (0%)     100m (0%)   50Mi (0%)        50Mi (0%)      183d\n  kube-system                 kube-proxy-69zzr                                0 (0%)        0 (0%)      0 (0%)           0 (0%)         28d\n  mcp                         mcp-server-manager-8677f6896c-d4mr9             200m (1%)     1 (8%)      1G (2%)          2560Mi (8%)    45h\n  xnet                        deepflow-agent-trc8k                            100m (0%)     1 (8%)      128Mi (0%)       768Mi (2%)     19d\n  xnet                        ham-p9dxv                                       0 (0%)        0 (0%)      0 (0%)           0 (0%)         177d\n  xnet                        observability-filebeat-w6gtr                    100m (0%)     1 (8%)      100Mi (0%)       200Mi (0%)     19d\n  xnet                        observability-kepler-ggstf                      0 (0%)        0 (0%)      0 (0%)           0 (0%)         19d\n  xnet                        observability-prometheus-node-exporter-qp2qd    0 (0%)        0 (0%)      0 (0%)           0 (0%)         19d\n  xnet                        xnet-agent-568f547566-jdsgp                     0 (0%)        0 (0%)      0 (0%)           0 (0%)         108d\nAllocated resources:\n  (Total limits may be over 100 percent, i.e., overcommitted.)\n  Resource           Requests         Limits\n  --------           --------         ------\n  cpu                1 (8%)           4100m (34%)\n  memory             1828375040 (5%)  5626Mi (17%)\n  ephemeral-storage  0 (0%)           0 (0%)\n  hugepages-1Gi      0 (0%)           0 (0%)\n  hugepages-2Mi      0 (0%)           0 (0%)\nEvents:              <none>", "duration_s": 0}, {"tool": "kubectl_get_yaml", "data": "apiVersion: v1\nkind: Pod\nmetadata:\n  creationTimestamp: \"2026-04-22T06:51:29Z\"\n  generateName: l1-test-nginx-6c69dc7c76-\n  labels:\n    app: nginx\n    e2e-test: \"true\"\n    pod-template-hash: 6c69dc7c76\n  name: l1-test-nginx-6c69dc7c76-fwzgn\n  namespace: aiops-e2e\n  ownerReferences:\n  - apiVersion: apps/v1\n    blockOwnerDeletion: true\n    controller: true\n    kind: ReplicaSet\n    name: l1-test-nginx-6c69dc7c76\n    uid: f0ae3eb5-88c2-4ca0-9efa-9db2e69389aa\n  resourceVersion: \"46405555\"\n  uid: f862460b-a1d6-4329-b5ad-1c9188af03cc\nspec:\n  containers:\n  - image: nginx:alpine\n    imagePullPolicy: IfNotPresent\n    name: nginx\n    resources: {}\n    terminationMessagePath: /dev/termination-log\n    terminationMessagePolicy: File\n    volumeMounts:\n    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount\n      name: kube-api-access-ww78k\n      readOnly: true\n  dnsPolicy: ClusterFirst\n  enableServiceLinks: true\n  nodeSelector:\n    kubernetes.io/hostname: node2\n  preemptionPolicy: PreemptLowerPriority\n  priority: 0\n  restartPolicy: Always\n  schedulerName: default-scheduler\n  securityContext: {}\n  serviceAccount: default\n  serviceAccountName: default\n  terminationGracePeriodSeconds: 30\n  tolerations:\n  - effect: NoExecute\n    key: node.kubernetes.io/not-ready\n    operator: Exists\n    tolerationSeconds: 300\n  - effect: NoExecute\n    key: node.kubernetes.io/unreachable\n    operator: Exists\n    tolerationSeconds: 300\n  volumes:\n  - name: kube-api-access-ww78k\n    projected:\n      defaultMode: 420\n      sources:\n      - serviceAccountToken:\n          expirationSeconds: 3607\n          path: token\n      - configMap:\n          items:\n          - key: ca.crt\n            path: ca.crt\n          name: kube-root-ca.crt\n      - downwardAPI:\n          items:\n          - fieldRef:\n              apiVersion: v1\n              fieldPath: metadata.namespace\n            path: namespace\nstatus:\n  conditions:\n  - lastProbeTime: null\n    lastTransitionTime: \"2026-04-22T06:51:29Z\"\n    message: '0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable:\n      true}, 2 node(s) didn''t match Pod''s node affinity/selector. preemption: 0/3\n      nodes are available: 3 Preemption is not helpful for scheduling..'\n    reason: Unschedulable\n    status: \"False\"\n    type: PodScheduled\n  phase: Pending\n  qosClass: BestEffort", "duration_s": 0}, {"tool": "kubernetes_tabular_query", "data": "NAMESPACE     NAME                                                STATUS    NODE\ndefault       exec-test                                           Running   node2\ndefault       network-test-from-running                           Running   node2\ndefault       nfs-client-provisioner-6fcd4994c9-lczf6             Running   node2\nkube-system   calico-node-d2dhp                                   Running   node2\nkube-system   kube-multus-ds-x7h9s                                Running   node2\nkube-system   kube-proxy-69zzr                                    Running   node2\nmcp           mcp-server-manager-8677f6896c-d4mr9                 Running   node2\nxnet          deepflow-agent-trc8k                                Running   node2\nxnet          ham-p9dxv                                           Running   node2\nxnet          observability-filebeat-w6gtr                        Running   node2\nxnet          observability-kepler-ggstf                          Running   node2\nxnet          observability-prometheus-node-exporter-qp2qd        Running   node2\nxnet          xnet-agent-568f547566-jdsgp                         Running   node2", "duration_s": 0}, {"tool": "kubectl_get_by_name", "data": "NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nnode2   Ready    <none>   209d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-174-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux", "duration_s": 0}, {"tool": "kubernetes_jq_query", "data": "Executing jq query for nodes...\n{\n  \"name\": \"master\",\n  \"taints\": null\n}\n{\n  \"name\": \"node1\",\n  \"taints\": null\n}\n{\n  \"name\": \"node2\",\n  \"taints\": [\n    {\n      \"effect\": \"NoSchedule\",\n      \"key\": \"test-unschedulable\",\n      \"value\": \"true\"\n    }\n  ]\n}", "duration_s": 0}], "llm_analysis": "### e6: 检查所有节点的 taint 分布", "collection_summary": "计划 6 项，实际采集 6 项，未采集 0 项，完整度 100%", "evidence_inventory": [{"id": "e1", "description": "确认 Pending Pod 的详细信息（事件、调度器消息）", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e2", "description": "确认 node2 节点的 taint 配置", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e3", "description": "获取 Pending Pod 的完整 YAML 定义（含 nodeSelector 和 tolerations）", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e4", "description": "检查 node2 节点上的所有 Pod 分布情况", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e5", "description": "检查 node2 节点的条件和资源状态", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e6", "description": "检查所有节点的 taint 分布", "level": "important", "collected": true, "source": "thinking_match"}], "missing_reasons": [], "early_stop": {"triggered": true, "reason": "critical 和 important 级证据均已满足，提前停止后续采集", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 6/6 项, 完整度: 100%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (19.9s)
   📤 → 下游数据: root_cause=
   confidence=100%
   causal_chain={"root_cause": "node2 节点上被人为添加了 `test-unschedulable=true:NoSchedule` taint（证据 e2, e6），这是一个非系统内置的自定义 taint。", "propagation": "该 taint 设置后，Kubernetes 调度器对所有尝试调度到 node2 的 Pod 进行检查。由于该 taint 的 effect 为 NoSchedule，任何没有对应 toleration 的 Pod 都会被拒绝调度（证据 e1）。", "direct_cause": "Pod `l1-test-nginx-6c69dc7c76-fwzgn` 通过 nodeSelector 硬性要求调度到 `kubernetes.io/hostname=node2`（证据 e3），但其 tolerations 列表中缺少针对 `test-unschedulable=true:NoSchedule` 的 toleration。同时，node1 和 master 节点不匹配 Pod 的 nodeSelector（证据 e1）。", "manifestation": "Pod 处于 Pending 状态超过 25 分钟，调度器持续报告 `0/3 nodes are available: 1 node(s) had untolerated taint, 2 node(s) didn't match Pod's node affinity/selector`（证据 e1）。"}
   rca_analysis={"phenomenon": "Pod `l1-test-nginx-6c69dc7c76-fwzgn` 在命名空间 `aiops-e2e` 中持续处于 Pending 状态，调度器无法将其调度到任何节点上。", "evidence_inventory": [{"id": "e1", "content": "Pending Pod 的详细信息（事件、调度器消息）", "source": "kubectl_describe (l1-test-nginx)", "reliability": "高"}, {"id": "e2", "content": "node2 节点的 taint 配置及资源状态", "source": "kubectl_describe (node2)", "reliability": "高"}, {"id": "e3", "content": "Pending Pod 的完整 YAML 定义（含 nodeSelector 和 tolerations）", "source": "kubectl_get_yaml (l1-test-nginx)", "reliability": "高"}, {"id": "e4", "content": "node2 节点上的所有 Pod 分布情况", "source": "kubernetes_tabular_query (node2 pods)", "reliability": "高"}, {"id": "e5", "content": "node2 节点的条件和资源状态", "source": "kubectl_get_by_name (node2)", "reliability": "高"}, {"id": "e6", "content": "所有节点的 taint 分布", "source": "kubernetes_jq_query (nodes taints)", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Pod 状态: Pending, 条件: PodScheduled=False, 事件: '0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector.'", "interpretation": "调度器明确拒绝调度该 Pod，因为所有 3 个节点都不满足调度条件：node2 存在无法容忍的 taint，node1 和 master 不匹配 nodeSelector。"}, {"evidence_id": "e2", "raw_data": "node2 Taints: test-unschedulable=true:NoSchedule, 节点 Ready, CPU 请求 1/12 (8%), 内存请求 1828375040 bytes (5%), 资源充足。", "interpretation": "node2 节点健康且资源充足，但带有一个 `test-unschedulable=true:NoSchedule` 的 taint，这会阻止所有没有对应 toleration 的 Pod 调度到该节点。"}, {"evidence_id": "e3", "raw_data": "Pod spec.nodeSelector: kubernetes.io/hostname=node2, spec.tolerations: [node.kubernetes.io/not-ready:NoExecute, node.kubernetes.io/unreachable:NoExecute]", "interpretation": "Pod 通过 nodeSelector 强制要求调度到 node2，但 Pod 的 tolerations 只包含默认的 `not-ready` 和 `unreachable`，不包含针对 `test-unschedulable` 的 toleration。"}, {"evidence_id": "e4", "raw_data": "node2 上运行着 13 个 Pod（exec-test, network-test-from-running, nfs-client-provisioner, calico-node, kube-multus, kube-proxy, mcp-server-manager, deepflow-agent, ham, filebeat, kepler, prometheus-node-exporter, xnet-agent）。", "interpretation": "node2 节点本身运行正常，可以调度和运行 Pod。这些已在运行的 Pod 要么没有 nodeSelector 约束（可被调度到其他节点），要么有对应的 toleration（如 DaemonSet Pod）。"}, {"evidence_id": "e5", "raw_data": "node2 状态: Ready, 节点条件全部正常 (NetworkUnavailable=False, MemoryPressure=False, DiskPressure=False, PIDPressure=False)。", "interpretation": "node2 节点处于健康状态，没有资源压力或网络问题，因此 Pod 无法调度不是由节点故障或资源不足引起的。"}, {"evidence_id": "e6", "raw_data": "master: taints=null, node1: taints=null, node2: taints=[{key: test-unschedulable, value: true, effect: NoSchedule}]", "interpretation": "集群中只有 node2 节点有 taint，其他两个节点（master 和 node1）没有任何 taint。这意味着 Pod 如果 nodeSelector 匹配 node1 或 master，是可以正常调度的。"}], "causal_chain": {"root_cause": "node2 节点上被人为添加了 `test-unschedulable=true:NoSchedule` taint（证据 e2, e6），这是一个非系统内置的自定义 taint。", "propagation": "该 taint 设置后，Kubernetes 调度器对所有尝试调度到 node2 的 Pod 进行检查。由于该 taint 的 effect 为 NoSchedule，任何没有对应 toleration 的 Pod 都会被拒绝调度（证据 e1）。", "direct_cause": "Pod `l1-test-nginx-6c69dc7c76-fwzgn` 通过 nodeSelector 硬性要求调度到 `kubernetes.io/hostname=node2`（证据 e3），但其 tolerations 列表中缺少针对 `test-unschedulable=true:NoSchedule` 的 toleration。同时，node1 和 master 节点不匹配 Pod 的 nodeSelector（证据 e1）。", "manifestation": "Pod 处于 Pending 状态超过 25 分钟，调度器持续报告 `0/3 nodes are available: 1 node(s) had untolerated taint, 2 node(s) didn't match Pod's node affinity/selector`（证据 e1）。"}, "root_cause_summary": "根因是 node2 节点被添加了自定义 taint `test-unschedulable=true:NoSchedule`（证据 e2, e6），而 Pod `l1-test-nginx-6c69dc7c76-fwzgn` 通过 nodeSelector `kubernetes.io/hostname=node2` 强制绑定到 node2（证据 e3），但 Pod 的 tolerations 中没有包含对该 taint 的容忍（证据 e3）。这导致调度器无法将 Pod 调度到唯一匹配的 node2（因 taint 被拒），也无法调度到其他节点（因 nodeSelector 不匹配），最终 Pod 永久 Pending（证据 e1）。", "confidence": 1.0, "primary_runbooks": [], "alternative_causes": [{"cause": "node2 节点资源不足", "reason": "证据 e2 显示 node2 CPU 请求仅 8%、内存请求仅 5%，资源非常充裕，此可能性被排除。"}, {"cause": "node2 节点故障", "reason": "证据 e5 显示 node2 处于 Ready 状态且所有条件正常，证据 e4 显示 node2 上 13 个 Pod 均正常运行，排除节点故障。"}], "limitations": "本次分析未追溯 taint 的添加来源（是由管理员手动添加还是自动化工具添加），也未分析该 Pod 的 ReplicaSet 配置（是否所有副本都有相同问题）。但这对根因结论无影响。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 100%
   🔗 因果链:
     根本原因: node2 节点上被人为添加了 `test-unschedulable=true:NoSchedule` taint（证据 e2, e6），这是一个非系统内置的自定义 taint。
     传导机制: 该 taint 设置后，Kubernetes 调度器对所有尝试调度到 node2 的 Pod 进行检查。由于该 taint 的 effect 为 NoSchedule，任何没有对应 toleration 的 Pod 都会被拒绝调度（证据 e1）。
     最终表现: Pod 处于 Pending 状态超过 25 分钟，调度器持续报告 `0/3 nodes are available: 1 node(s) had untolerated taint, 2 node(s) didn't match Pod's node affinity/selector`（证据 e1）。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (27.9s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6608 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 31.8s
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
| **问题层级** | L1 - 调度问题 |
| **问题分类** | Pod Pending (Taint/NodeSelector 冲突) |
| **置信度** | 高 (100%) |
| **证据完整度** | 6/6 (100%) |

---

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**集群当前状态总结**：
- **整体健康**：集群 3 个节点均 **Ready**，52 个 Pod 正常运行
- **唯一异常**：命名空间 `aiops-e2e` 下 1 个 Pod (`l1-test-nginx-6c69dc7c76-fwzgn`) 持续处于 **Pending** 状态，时长超过 25 分钟
- **核心问题**：Pod 因 `taint` 与 `nodeSelector` 冲突导致无法调度

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `l1-test-nginx-6c69dc7c76-fwzgn` |
| Namespace | `aiops-e2e` |
| Node (目标) | `node2` |
| 错误信息 | `0/3 nodes available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector` |

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态及事件 | `kubectl describe pod l1-test-nginx -n aiops-e2e` | 状态: `Pending`；条件: `PodScheduled=False`；事件: `Warning FailedScheduling`，消息: `0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector.` | 调度器因 taint 和 nodeSelector 不匹配拒绝调度 |
| 2 | node2 taint 配置 | `kubectl describe node node2` | `Taints: test-unschedulable=true:NoSchedule`；节点状态: `Ready`；CPU 请求: 1/12 (8%)，内存请求: 5% | node2 健康且资源充足，但带有一个 NoSchedule taint |
| 3 | Pod YAML 定义 | `kubectl get -o yaml pod l1-test-nginx -n aiops-e2e` | `nodeSelector: kubernetes.io/hostname=node2`；`tolerations: [node.kubernetes.io/not-ready:NoExecute, node.kubernetes.io/unreachable:NoExecute]` | Pod 强制调度到 node2，但 tolerations 中缺少对 `test-unschedulable` 的容忍 |
| 4 | node2 节点 Pod 分布 | `kubectl get pods -A -o wide --field-selector spec.nodeName=node2` | 13 个 Pod 全部 `Running`（exec-test, calico-node, kube-proxy, deepflow-agent 等） | node2 节点本身功能正常，可调度运行 Pod |
| 5 | node2 节点状态 | `kubectl get node node2` | `STATUS: Ready`；所有条件正常 (NetworkUnavailable=False, MemoryPressure=False, DiskPressure=False, PIDPressure=False) | 节点健康，无资源压力或网络问题 |
| 6 | 所有节点 taint 分布 | `kubectl get nodes -o json \| jq` | `master`: taints=null；`node1`: taints=null；`node2`: taints=[{key: test-unschedulable, value: true, effect: NoSchedule}] | 集群中仅有 node2 有 taint |

### 证据关联分析
- **证据 #1 + #3 印证**：调度器消息显示 `1 node(s) had untolerated taint` 且 `2 node(s) didn't match Pod's node affinity/selector`，与 Pod 的 `nodeSelector: hostname=node2` 和缺少对应 toleration 完全吻合。
- **证据 #2 + #6 印证**：仅 `node2` 有自定义 taint `test-unschedulable=true:NoSchedule`，其他节点无任何 taint。
- **证据 #2 + #4 + #5 印证**：node2 节点健康且资源充足，Node 本身不存在故障或资源瓶颈，问题完全出在调度策略上。
- **证据链**：Pod nodeSelector=node2 → 唯一匹配 node2 → node2 有 NoSchedule taint → Pod 无对应 toleration → 调度被拒 → 其他节点不匹配 nodeSelector → Pod 永久 Pending

### 缺失证据
无。所有 critical 和 important 级证据均已完整采集。

---

## 🎯 根因分析
### 因果链
```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                                  │
│ node2 节点被人为添加了自定义 taint `test-unschedulable=true:NoSchedule` (证据 e2, e6)      │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                                  │
│ NoSchedule taint 使调度器拒绝所有没有对应 toleration 的 Pod 调度到 node2                   │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                                  │
│ Pod `l1-test-nginx` 通过 nodeSelector 强制要求调度到 `kubernetes.io/hostname=node2`       │
│ 但 Pod 的 tolerations 列表中缺少针对 `test-unschedulable=true:NoSchedule` 的容忍          │
│ 同时 node1 和 master 不匹配 Pod 的 nodeSelector (证据 e1, e3)                             │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                              │
│ Pod 持续处于 Pending 状态 >25 分钟，调度器消息明确提示 taint 和 nodeSelector 冲突          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1（调度器消息明确拒绝）、证据 #2（node2 taint 配置）、证据 #3（Pod nodeSelector 和 tolerations）、证据 #6（仅 node2 有 taint），问题的根本原因是 **Pod 的 nodeSelector 强制绑定到带 `test-unschedulable=true:NoSchedule` taint 的 node2 节点，但 Pod 缺少对该 taint 的 toleration**，导致 Pod 永远无法被调度。

**置信度**：高 (100%)
- ✅ 所有关键证据完整且一致
- ✅ 调度器消息直接指出 taint 和 nodeSelector 冲突
- ✅ 排除节点资源不足和节点故障（证据 #2, #4, #5）

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [推荐] 移除 node2 的 taint**
```bash
kubectl taint nodes node2 test-unschedulable=true:NoSchedule-
```
*效果*：移除 taint 后，Pod 会自动调度到 node2 上
*注意*：如果该 taint 是用于维护或隔离节点的，请谨慎执行

**2. [替代方案] 为 Pod 添加 toleration**
编辑 Deployment/ReplicaSet 的 YAML 或使用 patch 命令：
```bash
kubectl patch deployment l1-test-nginx -n aiops-e2e --type='json' -p='[{"op": "add", "path": "/spec/template/spec/tolerations/-", "value": {"key": "test-unschedulable", "operator": "Exists", "effect": "NoSchedule"}}]'
```
*效果*：Pod 带上 toleration 后即可调度到 node2

**3. [可选] 修改 nodeSelector 调度到其他节点**
```bash
kubectl patch deployment l1-test-nginx -n aiops-e2e --type='json' -p='[{"op": "replace", "path": "/spec/template/spec/nodeSelector/kubernetes.io~1hostname", "value": "node1"}]'
```
*效果*：Pod 改为调度到无 taint 的 node1

### 后续优化
1. **清理不必要的 taint**：检查集群中所有 taint，确保只有真正需要隔离的节点才添加 taint
2. **规范使用 nodeSelector**：使用 `nodeSelector` 时确保目标节点无阻止调度的 taint
3. **添加调度策略文档**：记录节点 taint 用途和对应 Pod 的 toleration 配置

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 调度 | `kubectl get pod l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e` | STATUS 从 `Pending` 变为 `Running` |
| 2. 确认 Pod 所在节点 | `kubectl get pod l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e -o wide` | NODE 显示 `node2`（或修改后的节点名） |
| 3. 确认节点 taint 已移除 | `kubectl describe node node2 \| grep Taints` | Taints 为空或仅保留必需的 taint |
| 4. 检查集群整体状态 | `kubectl get pods -A --field-selector status.phase=Pending` | 无 Pending Pod |

---

## ⚠️ 注意事项
- **taint 的用途确认**：移除 taint 前请确认该 taint 是否被用于特定维护目的（如节点下线前驱逐 Pod）。如果是为了隔离 node2，则建议采用方案 2（添加 toleration）
- **节点标签冲突**：确认无其他 Pod 也因 nodeSelector 绑定到 node2 但缺少 toleration
- **DaemonSet 不受影响**：证据 #4 显示 node2 上的 calico-node、kube-proxy 等 DaemonSet Pod 正常运行，因为它们默认会带有容忍 `test-unschedulable` 等 taint 的逻辑

---

## 📊 性能统计

├─ 总耗时: 1.5m
├─ 问题定位: 27.9s (30%) ✅
├─ 证据链采集: 16.1s (17%) ✅
├─ 根因分析: 19.9s (22%) ✅
├─ 汇总总结: 27.9s (30%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 15 次
```

📋 诊断追踪

- **核心 Runbook**: private-k8s-health-reference
- **参考 Runbook**: private-k8s-health-reference
- **工具调用**: 15 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
