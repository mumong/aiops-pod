======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 23950440ddc84a87]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，我来检查集群的整体健康状况。先做轻量状态确认，从节点、Pod 和关键资源面入手。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,READY:.status.condition[?(@.type=='Ready')].status,
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   209d   v1.26.8  
   💭 [问题定位] 节点全部 Ready，异常 Pod 没有匹配到。让我用另一种方式确认所有 Pod 状态。
   💭 [问题定位] 调用工具: kubernetes_count
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_count (success)
      📄 Count for pods with jq...
1 results
---
53
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 NAMESPACE     NAME                                                STATUS    NODE
aiops-e2e     l1-test-nginx-6c69dc7c76-fwzgn                      Pending   <none>
aiops         aiops-copilot-76779bb6
   💭 [问题定位] 发现一个 **Pending** Pod。让我进一步查看它，同时检查节点条件等。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             l1-test-nginx-6c69dc7c76-fwzgn
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             <none>
Labels:           app=nginx
                  e2e-te
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 Executing jq query for nodes...
{
  "name": "master",
  "conditions": [
    {
      "type": "NetworkUnavailable",
      "status": "False",
      "reason": "CalicoIsUp"
    },
    {
      "type": "Memo
   💭 [问题定位] 让我看看那个 taint 的节点情况，以及检查一下关键系统组件。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   209d   v1.26.8  
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 NAME                                       READY   STATUS    RESTARTS      AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
calico-kube-controllers-6c67f9d475-2xcb7   1/1    
   💭 [问题定位] 让我看看 master 节点是否有 taint 标记。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:               master
Roles:              control-plane
Labels:             beta.kubernetes.io/arch=amd64
                    beta.kubernetes.io/os=linux
                    kubernetes.io/arch=am
   💭 [问题定位] 让我确认那个 taint 是哪个节点上的。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:               node2
Roles:              <none>
Labels:             beta.kubernetes.io/arch=amd64
                    beta.kubernetes.io/os=linux
                    kubernetes.io/arch=amd64
    
   💭 [问题定位] 现在情况很清楚了。让我再看一下 node1 是否有问题，同时看看是否有其他异常的 Services/Endpoints。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 NAME                             READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
l1-test-nginx-6c69dc7c76-fwzgn   0/1     Pending   0          22m   <non
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:               node1
Roles:              <none>
Labels:             beta.kubernetes.io/arch=amd64
                    beta.kubernetes.io/os=linux
                    kubernetes.io/arch=amd64
    
   💭 [问题定位] 好的，我已经完成了集群整体状态检查。让我总结一下发现。

现在来获取通用 runbook 作为参考（因为这是"集群健康检查"类请求）。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# 私有化 Kubernetes 环境健康与高效排查参考手册

> 类型: reference | 适用: 私有化 Kubernetes 环境 | 环境特征: Calico + NFS + containerd

## 目的

本手册不是某个具体故障的处理步骤，而是一个**额外知识参考**：
- 帮助理解在私有化 Kubernetes 环境中，健康检查应重点关注哪些资源与信号

   💭 [问题定位] 现在我已掌握全局情况，可以进行完整定层分析。

## 诊断结果

```json
{
  "layer": "L1",
  "layers": ["L1", "L3"],
  "layer_name": "集群节点层",
  "confidence": 0.9,
  "reasoning": "集群整体基本健康：3个节点均 Ready，系统组件（CoreDNS、Calico、kube-apiserver 等）正常运行。存在两个问题：(1) 节点 node2 有 'test-unschedulable=true:NoSchedule' 污点，属于测试/异常标记；(2) aiops-e2e/l1-test-nginx Pod 处于 Pending 状态，原因是该 Pod 有 nodeSelector 指定 node2，但 node2 有 NoSchedule taint 且不兼容该污点，同时 master 节点也有不可容忍的 taint。最底层根因是 node2 的 taint 导致调度失败，归为 L1 层。",
  "key_entities": [
    {"type": "Node", "value": "node2"},
    {"type": "Pod", "value": "l1-test-nginx-6c69dc7c76-fwzgn"},
    {"type": "Namespace", "value": "aiops-e2e"}
  ],
  "possible_scenarios": ["node2 被手动或自动标记了 test-unschedulable=true:NoSchedule 污点，导致所有不容忍该污点的 Pod 无法调度到 node2", "l1-test-nginx Pod 设置了 nodeSelector: kubernetes.io/hostname=node2，而 node2 有 NoSchedule taint，调度器无法分配"]
}
```

### 详细分析

**✅ 健康的部分：**
- **3 个节点全部 Ready**（master/node1/node2），无任何 Pressure
- **所有系统组件运行正常**：kube-apiserver、etcd、scheduler、controller-manager、CoreDNS、Calico、kube-proxy、Multus 全部 Running
- **53 个 Pod 中 52 个 Running，1 个 Pending**，无 CrashLoopBackOff、OOMKilled、ImagePullBackOff 等异常

**⚠️ 发现的问题：**

1. **node2 存在异常 Taint（L1 - 节点层）**
   - `test-unschedulable=true:NoSchedule`
   - 这个 taint 会阻止所有不主动容忍它的 Pod 调度到 node2
   - 当前 node2 上仍有 14 个 Pod 在运行（之前调度的），但新 Pod 无法调度上去
   - 可能原因是测试遗留或手动标记

2. **aiops-e2e/l1-test-nginx Pod 处于 Pending（L3 - 调度层）**
   - Pod 设置了 `nodeSelector: kubernetes.io/hostname=node2`
   - node2 有 `test-unschedulable=true:NoSchedule` 污点
   - master 有 `node-role.kubernetes.io/control-plane` 但无可调度标记
   - 因此 3 个节点都不满足条件：master 无对应 hostname，node2 有 taint，node1 不匹配 nodeSelector
   - 这个 Pod 名称带 `l1-test` 和 `e2e-test=true` 标签，可能是测试用 Pod，影响有限
   ✅ [问题定位] 完成 (35.8s)
   📤 → 下游数据: layer=Layer.L1, layers=L1+L3
   scenarios=['node2 被手动或自动标记了 test-unschedulable=true:NoSchedule 污点，导致所有不容忍该污点的 Pod 无法调度到 node2', 'l1-test-nginx Pod 设置了 nodeSelector: kubernetes.io/hostname=node2，而 node2 有 NoSchedule taint，调度器无法分配']
   entities=[{"type": "Node", "value": "node2"}, {"type": "Pod", "value": "l1-test-nginx-6c69dc7c76-fwzgn"}, {"type": "Namespace", "value": "aiops-e2e"}]
   reasoning=集群整体基本健康：3个节点均 Ready，系统组件（CoreDNS、Calico、kube-apiserver 等）正常运行。存在两个问题：(1) 节点 node2 有 'test-unschedulable=true:NoSchedule' 污点，属于测试/异常标记；(2) aiops-e2e/l1-test-nginx Pod 处于 Pending 状态，原因是该 Pod 有 nodeSelector 指定 node2，但 node2 有 NoSchedule taint 且不兼容该污点，同时 master 节点也有不可容忍的 taint。最底层根因是 node2 的 taint 导致调度失败，归为 L1 层。
   layer_analysis={"layer": "L1", "layers": ["L1", "L3"], "layer_name": "集群节点层", "confidence": 0.9, "reasoning": "集群整体基本健康：3个节点均 Ready，系统组件（CoreDNS、Calico、kube-apiserver 等）正常运行。存在两个问题：(1) 节点 node2 有 'test-unschedulable=true:NoSchedule' 污点，属于测试/异常标记；(2) aiops-e2e/l1-test-nginx Pod 处于 Pending 状态，原因是该 Pod 有 nodeSelector 指定 node2，但 node2 有 NoSchedule taint 且不兼容该污点，同时 master 节点也有不可容忍的 taint。最底层根因是 node2 的 taint 导致调度失败，归为 L1 层。", "key_entities": [{"type": "Node", "value": "node2"}, {"type": "Pod", "value": "l1-test-nginx-6c69dc7c76-fwzgn"}, {"type": "Namespace", "value": "aiops-e2e"}], "possible_scenarios": ["node2 被手动或自动标记了 test-unschedulable=true:NoSchedule 污点，导致所有不容忍该污点的 Pod 无法调度到 node2", "l1-test-nginx Pod 设置了 nodeSelector: kubernetes.io/hostname=node2，而 node2 有 NoSchedule taint，调度器无法分配"]}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L1 + L3（主层级: Layer.L1）
   置信度: 90%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我先根据上游定位结果，制定证据采集计划，然后逐项执行工具采集真实数据。

## 第一步：输出 JSON 证据采集计划

上游已定位为 **L1（节点调度异常）**，涉及 node2 的 taint 和 Pod 调度失败。我需要深入采集关键证据。

```json
{
  "layer": "L1",
  "evidence_plan": [
    {
      "id": "e1",
      "description": "查看 node2 的完整描述，确认 taint 详情和节点状态",
      "level": "critical",
      "tool": "kubectl_describe",
      "command": "kubectl describe node node2",
      "purpose": "确认 node2 的 Taints 字段、Conditions 状态、Allocated resources"
    },
    {
      "id": "e2",
      "description": "查看 l1-test-nginx Pod 的完整描述，确认调度事件和配置",
      "level": "critical",
      "tool": "kubectl_describe",
      "command": "kubectl describe pod l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e",
      "purpose": "确认 Pod 的 nodeSelector、tolerations、调度事件、状态"
    },
    {
      "id": "e3",
      "description": "获取 l1-test-nginx Pod 的完整 YAML 定义",
      "level": "important",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get pod l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e -o yaml",
      "purpose": "确认 Pod spec 中的 nodeSelector 和 tolerations 字段"
    },
    {
      "id": "e4",
      "description": "查看所有节点的 taint 和状态概览",
      "level": "important",
      "tool": "kubernetes_tabular_query",
      "command": "kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints,STATUS:.status.conditions[-1].type",
      "purpose": "确认集群所有节点的 taint 分布和状态"
    },
    {
      "id": "e5",
      "description": "查看 l1-test-nginx 相关事件",
      "level": "critical",
      "tool": "kubectl_events",
      "command": "kubectl events --for pod/l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e",
      "purpose": "确认调度失败的具体事件"
    },
    {
      "id": "e6",
      "description": "查看 aiops-e2e 命名空间中所有 Pod 的状态",
      "level": "important",
      "tool": "kubectl_get_by_kind_in_namespace",
      "command": "kubectl get pod -n aiops-e2e -o wide",
      "purpose": "确认命名空间内其他 Pod 是否正常运行"
    },
    {
      "id": "e7",
      "description": "检查节点资源使用情况（Prometheus）",
      "level": "optional",
      "tool": "execute_prometheus_instant_query",
      "command": "查询各节点 CPU 和内存使用率",
      "purpose": "辅助确认节点是否存在资源压力"
    }
  ],
  "collection_strategy": "先采集最关键的节点和 Pod 描述信息（e1, e2），同步采集节点概览（e4）和命名空间 Pod 状态（e6），然后获取 Pod YAML（e3）和事件（e5），最后用 Prometheus 验证资源情况（e7）"
}
```

## 第二步：逐项执行工具采集证据

先并行采集 e1、e2、e4、e6：
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubernetes_tabular_query
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:               node2
Roles:              <none>
Labels:             beta.kubernetes.io/arch=amd64
                    beta.kubernetes.io/os=linux
                    kubernetes.io/arch=amd64
    
   💭 [证据链采集] 工具结果: kubernetes_tabular_query (success)
      📄 NAME     TAINTS                                                       STATUS
master   <none>                                                       Ready
node1    <none>                                
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 NAME                             READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
l1-test-nginx-6c69dc7c76-fwzgn   0/1     Pending   0          23m   <non
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:             l1-test-nginx-6c69dc7c76-fwzgn
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             <none>
Labels:           app=nginx
                  e2e-te
   💭 [证据链采集] 很好，核心证据已经获取。让我继续获取 Pod YAML 和事件详情：
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_events
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
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 LAST SEEN           TYPE      REASON             OBJECT                               MESSAGE
23m                 Warning   FailedScheduling   Pod/l1-test-nginx-6c69dc7c76-fwzgn   0/3 nodes are availa
   ✅ [证据链采集] 完成 (17.0s)
   📤 → 下游数据: evidence_items=6/7
   evidence_analysis={"evidence_plan": [{"id": "e1", "description": "查看 node2 的完整描述，确认 taint 详情和节点状态", "level": "critical", "tool": "kubectl_describe", "command": "kubectl describe node node2", "purpose": "确认 node2 的 Taints 字段、Conditions 状态、Allocated resources"}, {"id": "e2", "description": "查看 l1-test-nginx Pod 的完整描述，确认调度事件和配置", "level": "critical", "tool": "kubectl_describe", "command": "kubectl describe pod l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e", "purpose": "确认 Pod 的 nodeSelector、tolerations、调度事件、状态"}, {"id": "e3", "description": "获取 l1-test-nginx Pod 的完整 YAML 定义", "level": "important", "tool": "kubectl_get_yaml", "command": "kubectl get pod l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e -o yaml", "purpose": "确认 Pod spec 中的 nodeSelector 和 tolerations 字段"}, {"id": "e4", "description": "查看所有节点的 taint 和状态概览", "level": "important", "tool": "kubernetes_tabular_query", "command": "kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints,STATUS:.status.conditions[-1].type", "purpose": "确认集群所有节点的 taint 分布和状态"}, {"id": "e5", "description": "查看 l1-test-nginx 相关事件", "level": "critical", "tool": "kubectl_events", "command": "kubectl events --for pod/l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e", "purpose": "确认调度失败的具体事件"}, {"id": "e6", "description": "查看 aiops-e2e 命名空间中所有 Pod 的状态", "level": "important", "tool": "kubectl_get_by_kind_in_namespace", "command": "kubectl get pod -n aiops-e2e -o wide", "purpose": "确认命名空间内其他 Pod 是否正常运行"}, {"id": "e7", "description": "检查节点资源使用情况（Prometheus）", "level": "optional", "tool": "execute_prometheus_instant_query", "command": "查询各节点 CPU 和内存使用率", "purpose": "辅助确认节点是否存在资源压力"}], "tool_results": [], "tool_data": [{"tool": "kubectl_describe", "data": "Name:               node2\nRoles:              <none>\nLabels:             beta.kubernetes.io/arch=amd64\n                    beta.kubernetes.io/os=linux\n                    kubernetes.io/arch=amd64\n                    kubernetes.io/hostname=node2\n                    kubernetes.io/os=linux\nAnnotations:        kubeadm.alpha.kubernetes.io/cri-socket: unix:///var/run/containerd/containerd.sock\n                    node.alpha.kubernetes.io/ttl: 0\n                    projectcalico.org/IPv4Address: 10.2.0.50/19\n                    projectcalico.org/IPv4IPIPTunnelAddr: 172.16.104.0\n                    volumes.kubernetes.io/controller-managed-attach-detach: true\nCreationTimestamp:  Thu, 25 Sep 2025 03:10:26 +0000\nTaints:             test-unschedulable=true:NoSchedule\nUnschedulable:      false\nLease:\n  HolderIdentity:  node2\n  AcquireTime:     <unset>\n  RenewTime:       Wed, 22 Apr 2026 07:14:41 +0000\nConditions:\n  Type                 Status  LastHeartbeatTime                 LastTransitionTime                Reason                       Message\n  ----                 ------  -----------------                 ------------------                ------                       -------\n  NetworkUnavailable   False   Fri, 17 Apr 2026 07:03:52 +0000   Fri, 17 Apr 2026 07:03:52 +0000   CalicoIsUp                   Calico is running on this node\n  MemoryPressure       False   Wed, 22 Apr 2026 07:12:28 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletHasSufficientMemory   kubelet has sufficient memory available\n  DiskPressure         False   Wed, 22 Apr 2026 07:12:28 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletHasNoDiskPressure     kubelet has no disk pressure\n  PIDPressure          False   Wed, 22 Apr 2026 07:12:28 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletHasSufficientPID      kubelet has sufficient PID available\n  Ready                True    Wed, 22 Apr 2026 07:12:28 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletReady                 kubelet is posting ready status. AppArmor enabled\nAddresses:\n  InternalIP:  10.2.0.50\n  Hostname:    node2\nCapacity:\n  cpu:                12\n  ephemeral-storage:  203770680Ki\n  hugepages-1Gi:      0\n  hugepages-2Mi:      0\n  memory:             32860484Ki\n  pods:               110\nAllocatable:\n  cpu:                12\n  ephemeral-storage:  187795058378\n  hugepages-1Gi:      0\n  hugepages-2Mi:      0\n  memory:             32758084Ki\n  pods:               110\nSystem Info:\n  Machine ID:                 6bb27862c82149418d0f5624411d0b22\n  System UUID:                0f5af30a-d385-493c-bc8b-5442fd024eee\n  Boot ID:                    0ea98079-ad10-4a20-85f5-19b34afd257e\n  Kernel Version:             5.15.0-174-generic\n  OS Image:                   Ubuntu 22.04.4 LTS\n  Operating System:           linux\n  Architecture:               amd64\n  Container Runtime Version:  containerd://1.6.32\n  Kubelet Version:            v1.26.8\n  Kube-Proxy Version:         v1.26.8\nNon-terminated Pods:          (14 in total)\n  Namespace                   Name                                            CPU Requests  CPU Limits  Memory Requests  Memory Limits  Age\n  ---------                   ----                                            ------------  ----------  ---------------  -------------  ---\n  aiops                       aiops-copilot-76779bb6df-4bcrf                  250m (2%)     1 (8%)      512Mi (1%)       2Gi (6%)       5h36m\n  default                     exec-test                                       0 (0%)        0 (0%)      0 (0%)           0 (0%)         2d3h\n  default                     network-test-from-running                       0 (0%)        0 (0%)      0 (0%)           0 (0%)         2d1h\n  default                     nfs-client-provisioner-6fcd4994c9-lczf6         0 (0%)        0 (0%)      0 (0%)           0 (0%)         85d\n  kube-system                 calico-node-d2dhp                               250m (2%)     0 (0%)      0 (0%)           0 (0%)         183d\n  kube-system                 kube-multus-ds-x7h9s                            100m (0%)     100m (0%)   50Mi (0%)        50Mi (0%)      183d\n  kube-system                 kube-proxy-69zzr                                0 (0%)        0 (0%)      0 (0%)           0 (0%)         28d\n  mcp                         mcp-server-manager-8677f6896c-d4mr9             200m (1%)     1 (8%)      1G (2%)          2560Mi (8%)    45h\n  xnet                        deepflow-agent-trc8k                            100m (0%)     1 (8%)      128Mi (0%)       768Mi (2%)     19d\n  xnet                        ham-p9dxv                                       0 (0%)        0 (0%)      0 (0%)           0 (0%)         177d\n  xnet                        observability-filebeat-w6gtr                    100m (0%)     1 (8%)      100Mi (0%)       200Mi (0%)     19d\n  xnet                        observability-kepler-ggstf                      0 (0%)        0 (0%)      0 (0%)           0 (0%)         19d\n  xnet                        observability-prometheus-node-exporter-qp2qd    0 (0%)        0 (0%)      0 (0%)           0 (0%)         19d\n  xnet                        xnet-agent-568f547566-jdsgp                     0 (0%)        0 (0%)      0 (0%)           0 (0%)         108d\nAllocated resources:\n  (Total limits may be over 100 percent, i.e., overcommitted.)\n  Resource           Requests         Limits\n  --------           --------         ------\n  cpu                1 (8%)           4100m (34%)\n  memory             1828375040 (5%)  5626Mi (17%)\n  ephemeral-storage  0 (0%)           0 (0%)\n  hugepages-1Gi      0 (0%)           0 (0%)\n  hugepages-2Mi      0 (0%)           0 (0%)\nEvents:              <none>", "duration_s": 0}, {"tool": "kubernetes_tabular_query", "data": "NAME     TAINTS                                                       STATUS\nmaster   <none>                                                       Ready\nnode1    <none>                                                       Ready\nnode2    [map[effect:NoSchedule key:test-unschedulable value:true]]   Ready", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_namespace", "data": "NAME                             READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS\nl1-test-nginx-6c69dc7c76-fwzgn   0/1     Pending   0          23m   <none>   <none>   <none>           <none>            app=nginx,e2e-test=true,pod-template-hash=6c69dc7c76", "duration_s": 0}, {"tool": "kubectl_describe", "data": "Name:             l1-test-nginx-6c69dc7c76-fwzgn\nNamespace:        aiops-e2e\nPriority:         0\nService Account:  default\nNode:             <none>\nLabels:           app=nginx\n                  e2e-test=true\n                  pod-template-hash=6c69dc7c76\nAnnotations:      <none>\nStatus:           Pending\nIP:               \nIPs:              <none>\nControlled By:    ReplicaSet/l1-test-nginx-6c69dc7c76\nContainers:\n  nginx:\n    Image:        nginx:alpine\n    Port:         <none>\n    Host Port:    <none>\n    Environment:  <none>\n    Mounts:\n      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-ww78k (ro)\nConditions:\n  Type           Status\n  PodScheduled   False \nVolumes:\n  kube-api-access-ww78k:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    TokenExpirationSeconds:  3607\n    ConfigMapName:           kube-root-ca.crt\n    ConfigMapOptional:       <nil>\n    DownwardAPI:             true\nQoS Class:                   BestEffort\nNode-Selectors:              kubernetes.io/hostname=node2\nTolerations:                 node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\n                             node.kubernetes.io/unreachable:NoExecute op=Exists for 300s\nEvents:\n  Type     Reason            Age                From               Message\n  ----     ------            ----               ----               -------\n  Warning  FailedScheduling  23m                default-scheduler  0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  13m (x2 over 18m)  default-scheduler  0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..", "duration_s": 0}, {"tool": "kubectl_get_yaml", "data": "apiVersion: v1\nkind: Pod\nmetadata:\n  creationTimestamp: \"2026-04-22T06:51:29Z\"\n  generateName: l1-test-nginx-6c69dc7c76-\n  labels:\n    app: nginx\n    e2e-test: \"true\"\n    pod-template-hash: 6c69dc7c76\n  name: l1-test-nginx-6c69dc7c76-fwzgn\n  namespace: aiops-e2e\n  ownerReferences:\n  - apiVersion: apps/v1\n    blockOwnerDeletion: true\n    controller: true\n    kind: ReplicaSet\n    name: l1-test-nginx-6c69dc7c76\n    uid: f0ae3eb5-88c2-4ca0-9efa-9db2e69389aa\n  resourceVersion: \"46405555\"\n  uid: f862460b-a1d6-4329-b5ad-1c9188af03cc\nspec:\n  containers:\n  - image: nginx:alpine\n    imagePullPolicy: IfNotPresent\n    name: nginx\n    resources: {}\n    terminationMessagePath: /dev/termination-log\n    terminationMessagePolicy: File\n    volumeMounts:\n    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount\n      name: kube-api-access-ww78k\n      readOnly: true\n  dnsPolicy: ClusterFirst\n  enableServiceLinks: true\n  nodeSelector:\n    kubernetes.io/hostname: node2\n  preemptionPolicy: PreemptLowerPriority\n  priority: 0\n  restartPolicy: Always\n  schedulerName: default-scheduler\n  securityContext: {}\n  serviceAccount: default\n  serviceAccountName: default\n  terminationGracePeriodSeconds: 30\n  tolerations:\n  - effect: NoExecute\n    key: node.kubernetes.io/not-ready\n    operator: Exists\n    tolerationSeconds: 300\n  - effect: NoExecute\n    key: node.kubernetes.io/unreachable\n    operator: Exists\n    tolerationSeconds: 300\n  volumes:\n  - name: kube-api-access-ww78k\n    projected:\n      defaultMode: 420\n      sources:\n      - serviceAccountToken:\n          expirationSeconds: 3607\n          path: token\n      - configMap:\n          items:\n          - key: ca.crt\n            path: ca.crt\n          name: kube-root-ca.crt\n      - downwardAPI:\n          items:\n          - fieldRef:\n              apiVersion: v1\n              fieldPath: metadata.namespace\n            path: namespace\nstatus:\n  conditions:\n  - lastProbeTime: null\n    lastTransitionTime: \"2026-04-22T06:51:29Z\"\n    message: '0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable:\n      true}, 2 node(s) didn''t match Pod''s node affinity/selector. preemption: 0/3\n      nodes are available: 3 Preemption is not helpful for scheduling..'\n    reason: Unschedulable\n    status: \"False\"\n    type: PodScheduled\n  phase: Pending\n  qosClass: BestEffort", "duration_s": 0}, {"tool": "kubectl_events", "data": "LAST SEEN           TYPE      REASON             OBJECT                               MESSAGE\n23m                 Warning   FailedScheduling   Pod/l1-test-nginx-6c69dc7c76-fwzgn   0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n13m (x2 over 18m)   Warning   FailedScheduling   Pod/l1-test-nginx-6c69dc7c76-fwzgn   0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..", "duration_s": 0}], "llm_analysis": "很好，核心证据已经获取。让我继续获取 Pod YAML 和事件详情：", "collection_summary": "计划 7 项，实际采集 6 项，未采集 1 项，完整度 86%", "evidence_inventory": [{"id": "e1", "description": "查看 node2 的完整描述，确认 taint 详情和节点状态", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e2", "description": "查看 l1-test-nginx Pod 的完整描述，确认调度事件和配置", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e3", "description": "获取 l1-test-nginx Pod 的完整 YAML 定义", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e4", "description": "查看所有节点的 taint 和状态概览", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e5", "description": "查看 l1-test-nginx 相关事件", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e6", "description": "查看 aiops-e2e 命名空间中所有 Pod 的状态", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e7", "description": "检查节点资源使用情况（Prometheus）", "level": "optional", "collected": false, "source": "planned"}], "missing_reasons": ["e7(检查节点资源使用情况（Prometheus）): 已规划但工具执行失败或无匹配结果"], "early_stop": {"triggered": true, "reason": "critical 和 important 级证据均已满足，提前停止后续采集", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 6/7 项, 完整度: 86%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (23.5s)
   📤 → 下游数据: root_cause=
   confidence=95%
   causal_chain={"root_cause": "node2 被标记了 test-unschedulable=true:NoSchedule 污点，该污点的设置目的可能是隔离测试节点，但未与使用 nodeSelector 指定 node2 的 Pod 进行协调", "propagation": "调度器检查 3 个节点: master 和 node1 不符合 nodeSelector 条件被排除 → node2 虽然符合 nodeSelector 但存在未容忍的 NoSchedule 污点被排除 → 所有节点均不可用", "direct_cause": "Pod l1-test-nginx-6c69dc7c76-fwzgn 的 nodeSelector (kubernetes.io/hostname=node2) 与 node2 的 test-unschedulable=true:NoSchedule 污点冲突，Pod 的 tolerations 中未包含该污点的容忍配置", "manifestation": "Pod 处于 Pending 状态，调度事件持续报 FailedScheduling，无法分配到任何节点运行"}
   rca_analysis={"phenomenon": "Pod l1-test-nginx-6c69dc7c76-fwzgn 在命名空间 aiops-e2e 中处于 Pending 状态，无法调度到任何节点", "evidence_inventory": [{"id": "e1", "content": "node2 存在 taint: test-unschedulable=true:NoSchedule", "source": "kubectl describe node node2", "reliability": "高"}, {"id": "e2", "content": "所有 3 个节点状态均为 Ready，master 和 node1 无 taint，node2 有 test-unschedulable=true:NoSchedule", "source": "kubectl get nodes -o wide", "reliability": "高"}, {"id": "e3", "content": "Pod l1-test-nginx 状态为 Pending，Age 23m，无分配节点", "source": "kubectl get pods -n aiops-e2e", "reliability": "高"}, {"id": "e4", "content": "Pod 定义了 nodeSelector: kubernetes.io/hostname=node2，但 tolerations 中仅包含 node.kubernetes.io/not-ready 和 node.kubernetes.io/unreachable，未容忍 test-unschedulable taint", "source": "kubectl describe pod l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e", "reliability": "高"}, {"id": "e5", "content": "调度事件: FailedScheduling - '0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector'", "source": "kubectl events -n aiops-e2e", "reliability": "高"}, {"id": "e6", "content": "Pod 的 YAML 配置确认 nodeSelector 为 kubernetes.io/hostname=node2，且 tolerations 无 test-unschedulable 容忍", "source": "kubectl get pod l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e -o yaml", "reliability": "高"}, {"id": "e7", "content": "node2 资源分配正常：CPU 请求 1 (8%)，内存请求 1828375040 (5%)，无资源压力", "source": "kubectl describe node node2", "reliability": "高"}, {"id": "e8", "content": "aiops-e2e 命名空间中只有一个 Pod l1-test-nginx-6c69dc7c76-fwzgn 处于 Pending 状态", "source": "kubectl get pods -n aiops-e2e", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Taints: test-unschedulable=true:NoSchedule", "interpretation": "node2 被标记了一个自定义污点，effect 为 NoSchedule，意味着任何没有对应 toleration 的 Pod 都无法调度到此节点"}, {"evidence_id": "e2", "raw_data": "master: Taints <none>, Ready; node1: Taints <none>, Ready; node2: Taints [map[effect:NoSchedule key:test-unschedulable value:true]], Ready", "interpretation": "集群中只有 node2 有污点，master 和 node1 没有污点，所有节点均处于 Ready 状态"}, {"evidence_id": "e3", "raw_data": "NAME: l1-test-nginx-6c69dc7c76-fwzgn, STATUS: Pending, AGE: 23m, NODE: <none>", "interpretation": "Pod 已经创建 23 分钟，但始终未能分配到节点，一直处于 Pending 状态"}, {"evidence_id": "e4", "raw_data": "Node-Selectors: kubernetes.io/hostname=node2; Tolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s, node.kubernetes.io/unreachable:NoExecute op=Exists for 300s", "interpretation": "Pod 通过 nodeSelector 强制要求调度到 node2，但 tolerations 仅包含标准的节点故障容忍，未包含对 test-unschedulable taint 的容忍，导致无法满足 node2 的调度条件"}, {"evidence_id": "e5", "raw_data": "0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector", "interpretation": "调度器明确报告：node2 因为未容忍的污点不可用，master 和 node1 因为不满足 nodeSelector 条件不可用，3 个节点均不可调度"}, {"evidence_id": "e6", "raw_data": "spec.nodeSelector: {kubernetes.io/hostname: node2}; spec.tolerations: [node.kubernetes.io/not-ready:NoExecute, node.kubernetes.io/unreachable:NoExecute]", "interpretation": "YAML 配置确认了 nodeSelector 和 tolerations 的精确内容，没有对 test-unschedulable 的容忍"}, {"evidence_id": "e7", "raw_data": "Allocated resources: cpu 1 (8%), memory 1828375040 (5%); Conditions: MemoryPressure False, DiskPressure False, PIDPressure False", "interpretation": "node2 的资源使用率很低，CPU 仅 8%，内存仅 5%，且无任何压力条件，排除了资源不足导致的调度失败"}, {"evidence_id": "e8", "raw_data": "Namespace aiops-e2e 中只有一个 Pod 且为 Pending", "interpretation": "该命名空间中无其他 Pod 干扰，问题仅限于这个 Pod"}], "causal_chain": {"root_cause": "node2 被标记了 test-unschedulable=true:NoSchedule 污点，该污点的设置目的可能是隔离测试节点，但未与使用 nodeSelector 指定 node2 的 Pod 进行协调", "propagation": "调度器检查 3 个节点: master 和 node1 不符合 nodeSelector 条件被排除 → node2 虽然符合 nodeSelector 但存在未容忍的 NoSchedule 污点被排除 → 所有节点均不可用", "direct_cause": "Pod l1-test-nginx-6c69dc7c76-fwzgn 的 nodeSelector (kubernetes.io/hostname=node2) 与 node2 的 test-unschedulable=true:NoSchedule 污点冲突，Pod 的 tolerations 中未包含该污点的容忍配置", "manifestation": "Pod 处于 Pending 状态，调度事件持续报 FailedScheduling，无法分配到任何节点运行"}, "root_cause_summary": "集群存在一个明确的调度冲突问题：Pod l1-test-nginx-6c69dc7c76-fwzgn 通过 nodeSelector 指定调度到 node2（IP: 10.2.0.50），但 node2 被设置了 test-unschedulable=true:NoSchedule 污点（证据 e1），而 Pod 的 tolerations 中仅包含 node.kubernetes.io/not-ready 和 node.kubernetes.io/unreachable 两个标准容忍，未包含对 test-unschedulable 的容忍（证据 e4、e6）。调度器日志显示 0/3 nodes available，其中 node2 因未容忍的污点不可用，master 和 node1 因不满足 nodeSelector 不可用（证据 e5）。node2 的资源使用率很低（CPU 8%，内存 5%），排除了资源压力（证据 e7）。", "confidence": 0.95, "primary_runbooks": [], "alternative_causes": [{"cause": "污点 test-unschedulable=true:NoSchedule 可能被自动化工具或人为误标记，导致 node2 被意外隔离", "likelihood": "中", "explanation": "污点名称 test-unschedulable 暗示可能是一个测试用途的污点，可能是人为误操作或测试后未清理"}, {"cause": "Pod 的 nodeSelector 可能配置错误，不应硬性绑定到 node2", "likelihood": "低", "explanation": "如果 Pod 本意是调度到任意可用节点，则 nodeSelector 配置不当；但 node2 上的污点表明可能是设计上要将 node2 作为隔离节点"}], "limitations": "Prometheus 指标数据未采集（证据 7 标记为未采集），无法提供更长时间维度的资源趋势分析；当前基于 kubectl 命令的即时数据已足够定位根因"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 95%
   🔗 因果链:
     根本原因: node2 被标记了 test-unschedulable=true:NoSchedule 污点，该污点的设置目的可能是隔离测试节点，但未与使用 nodeSelector 指定 node2 的 Pod 进行协调
     传导机制: 调度器检查 3 个节点: master 和 node1 不符合 nodeSelector 条件被排除 → node2 虽然符合 nodeSelector 但存在未容忍的 NoSchedule 污点被排除 → 所有节点均不可用
     最终表现: Pod 处于 Pending 状态，调度事件持续报 FailedScheduling，无法分配到任何节点运行


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (28.6s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6621 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 44.9s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我已对您集群的状态进行了全面分析。以下是详细的诊断报告。

---
## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **问题层级** | L1 - 集群节点层 |
| **问题分类** | Pod Pending / 调度冲突 |
| **置信度** | 高 (95%) |
| **证据完整度** | 6/7 (86%) |

**集群状态总结：**
您的集群整体运行健康，3个节点（`master`, `node1`, `node2`）均为 `Ready` 状态，核心系统组件（如 CoreDNS, Calico, etcd）均正常运行。

**核心问题：** 在 `aiops-e2e` 命名空间中，存在一个名为 `l1-test-nginx-6c69dc7c76-fwzgn` 的 Pod 处于 **Pending** 状态，无法调度运行。原因是**调度冲突**：该 Pod 的 `nodeSelector` 强制指定调度到 `node2`，但 `node2` 节点存在一个未经容忍的自定义污点 `test-unschedulable=true:NoSchedule`。

---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `l1-test-nginx-6c69dc7c76-fwzgn` |
| Namespace | `aiops-e2e` |
| Node | `node2` (IP: 10.2.0.50) |
| 错误信息 | `FailedScheduling: 0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector.` |

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Node 污点 | `kubectl describe node node2` | `Taints: test-unschedulable=true:NoSchedule` | `node2` 被标记了一个自定义 `NoSchedule` 污点，阻止未容忍此污点的 Pod 调度。 |
| 2 | 节点状态 | `kubectl get nodes -o custom-columns=...` | `node2: [map[effect:NoSchedule key:test-unschedulable value:true]]` | 集群中仅有 `node2` 有污点，`master` 和 `node1` 均无污点且为 `Ready` 状态。 |
| 3 | Pod 状态 | `kubectl get pod -n aiops-e2e` | `NAME: l1-test-nginx-... STATUS: Pending NODE: <none>` | Pod 持续处于 `Pending` 状态，未被分配到任何节点。 |
| 4 | Pod 配置 | `kubectl describe pod l1-test-nginx-... -n aiops-e2e` | `Node-Selectors: kubernetes.io/hostname=node2` <br> `Tolerations: node.kubernetes.io/not-ready:NoExecute...` | Pod 通过 `nodeSelector` **硬性要求**调度到 `node2`，但其 `tolerations` 中**没有**包含对 `test-unschedulable` 污点的容忍。 |
| 5 | 调度事件 | `kubectl events --for pod/l1-test-nginx-... -n aiops-e2e` | `Warning FailedScheduling: 0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector.` | 调度器报告：`node2` 因未容忍的污点不可用，`master` 和 `node1` 因不满足 `nodeSelector` 不可用。 |
| 6 | 资源使用 | `kubectl describe node node2` | `Allocated resources: cpu 1 (8%), memory 1828375040 (5%)` | `node2` 资源充足（CPU 8%，内存 5%），无内存或磁盘压力，排除了资源不足导致调度失败的可能。 |

### 证据关联分析
- **证据 #1 + 证据 #4 + 证据 #5 印证**：Pod 强制要求调度到 `node2` (证据 #4)，但 `node2` 有 `NoSchedule` 污点 (证据 #1)，Pod 未容忍此污点，导致调度器判定 `node2` 不可用 (证据 #5)。
- **证据链**：Pod `nodeSelector` 锁定 `node2` → `node2` 存在未经 Pod 容忍的 `NoSchedule` 污点 → 调度器排除所有节点 → Pod 持续 `Pending`。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 节点资源历史趋势（Prometheus） | optional | 当前 kubectl 命令数据已足够定位问题，缺失此项不影响诊断结论。 |

---
## 🎯 根因分析
### 因果链
```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                              │
│ node2 节点被标记了 `test-unschedulable=true:NoSchedule` 污点，而 Pod 未配置容忍此污点。│
│ 这可能是由于测试隔离或误操作导致，未与使用 nodeSelector 的 Pod 进行协调。               │
└──────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                              │
│ 调度器检查所有节点：                                                                   │
│ 1. master 和 node1: 不符合 Pod 的 nodeSelector (`kubernetes.io/hostname=node2`)，排除│
│ 2. node2: 虽然符合 nodeSelector，但存在未容忍的 `NoSchedule` 污点，排除              │
│ → 所有节点均不可用，调度失败                                                            │
└──────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                              │
│ Pod `l1-test-nginx-...` 的 `nodeSelector` 配置与 `node2` 的污点配置冲突，导致 Pod 被  │
│ 调度器判定为不可调度。                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                          │
│ Pod `l1-test-nginx-...` 在 `aiops-e2e` 命名空间中持续处于 `Pending` 状态，并反复报错 │
│ `FailedScheduling`。                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #1 (node2 taint), 证据 #4 (Pod nodeSelector), 和证据 #5 (调度事件)，
问题的根本原因是**Pod `l1-test-nginx-...` 的 `nodeSelector` 硬性指定调度到 `node2`，但 `node2` 上的 `test-unschedulable=true:NoSchedule` 污点阻止了该 Pod 的调度，而 Pod 本身未配置相应的容忍。** 这导致调度器无节点可用，Pod 持续 `Pending`。

**置信度**：高 (95%)
- ✅ 调度事件明确指示了 `untolerated taint` 和 `didn't match Pod's node affinity/selector`
- ✅ Pod 配置和 Node 配置完全印证了调度器日志
- ✅ 已排除节点资源不足等其他可能性

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）

**方案 1：[推荐] 移除 node2 上的污点**
这是最直接的解决方案，恢复 `node2` 的正常调度功能。
```bash
kubectl taint nodes node2 test-unschedulable=true:NoSchedule-
```
*依据*：证据 #1 显示 `node2` 上的 `test-unschedulable` 污点是导致问题的直接原因。移除它后，Pod 即可调度到 `node2`。

**方案 2：为 Pod 添加对 `test-unschedulable` 污点的容忍**
如果您希望保留 `node2` 的污点（例如用于隔离），则需要修改 Pod 的配置，为其添加容忍。
修改 `Deployment` (假设为 `l1-test-nginx`):
```bash
kubectl edit deployment l1-test-nginx -n aiops-e2e
```
在 Pod 模板的 `spec.tolerations` 下添加以下内容：
```yaml
tolerations:
- key: "test-unschedulable"
  operator: "Equal"
  value: "true"
  effect: "NoSchedule"
```
*依据*：证据 #4 显示 Pod 的 tolerations 中缺少此配置。添加后，调度器会允许该 Pod 调度到有该污点的节点。

**方案 3：修改 Pod 的 nodeSelector**
如果 Pod 不需要硬性绑定到 `node2`，可以移除 `nodeSelector`，让调度器自动分配。
```bash
kubectl patch deployment l1-test-nginx -n aiops-e2e -p '{"spec": {"template": {"spec": {"nodeSelector": null}}}}'
```
*依据*：证据 #4 显示 `nodeSelector` 是导致 Pod 只能调度到 `node2` 的限制条件。移除后，Pod 可以调度到 `master` 或 `node1`。

### 后续优化
1. **污点管理规范**：为测试或特殊用途节点设置污点时，应确保相关 Pod 已配置正确的容忍，或明确告知团队。
2. **配置审计**：审查 `aiops-e2e` 命名空间下其他资源的配置，确保没有类似的调度冲突。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 node2 污点被移除 | `kubectl describe node node2 \| grep Taints` | 输出为空，或不再包含 `test-unschedulable=true:NoSchedule` |
| 2. 确认 Pod 状态 | `kubectl get pod -n aiops-e2e -l app=nginx` | `STATUS: Running`，且 `NODE` 列为 `node2` (或其他节点) |
| 3. 检查 Pod 重启次数 | `kubectl get pod l1-test-nginx-... -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | `0`，表示 Pod 稳定运行 |

---
## ⚠️ 注意事项
- 执行 `taint` 移除命令后，Node 将立即允许所有未容忍该污点的 Pod 调度上去。请确认这是否符合您的预期。
- 如果采用方案2（添加容忍），请确保修改的是 `Deployment` 而非单个 Pod，否则 Pod 重建后配置会丢失。

---

## 📊 性能统计

├─ 总耗时: 1.7m
├─ 问题定位: 35.8s (34%) ✅
├─ 证据链采集: 17.0s (16%) ✅
├─ 根因分析: 23.5s (22%) ✅
├─ 汇总总结: 28.6s (27%) ✅
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
