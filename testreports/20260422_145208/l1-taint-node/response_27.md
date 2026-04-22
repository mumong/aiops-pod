======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 4dc9da076d51485a]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来先做一个快速的全局状态检查，看看集群当前是否存在异常对象。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 调用工具: kubernetes_count
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,READY:.status.containerStatuses[0].ready' | (head -
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   209d   v1.26.8  
   💭 [问题定位] 工具结果: kubernetes_count (success)
      📄 Count for pods with jq...
1 results
---
l1-test-nginx-6c69dc7c76-fwzgn
   💭 [问题定位] 所有节点 Ready，但有一个 Pod 不是 Running 状态。让我进一步查看详情。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName' | (head -n 1; tail -n +2 | gre
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 Command failed (exit 1):
kubectl get --show-labels -o wide pod l1-test-nginx-6c69dc7c76-fwzgn -n default
Error from server (NotFound): pods "l1-test-nginx-6c69dc7c76-fwzgn" not found

   💭 [问题定位] 这个 Pod 可能已经不存在了（被删除了）。让我确认当前所有 Pod 的状态。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 NAMESPACE     NAME                                                STATUS    READY
aiops-e2e     l1-test-nginx-6c69dc7c76-fwzgn                      Pending   <none>
aiops         aiops-copilot-76779bb
   💭 [问题定位] 有一个 Pending Pod。让我进一步查看它的详情，同时获取通用 runbook 作为参考。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# 私有化 Kubernetes 环境健康与高效排查参考手册

> 类型: reference | 适用: 私有化 Kubernetes 环境 | 环境特征: Calico + NFS + containerd

## 目的

本手册不是某个具体故障的处理步骤，而是一个**额外知识参考**：
- 帮助理解在私有化 Kubernetes 环境中，健康检查应重点关注哪些资源与信号

   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             l1-test-nginx-6c69dc7c76-fwzgn
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             <none>
Labels:           app=nginx
                  e2e-te
   💭 [问题定位] 现在我看到了关键的异常信息。这个 Pod 因为调度问题 Pending。让我进一步确认节点 taint 和调度情况。
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
      📄 Name:               master
Roles:              control-plane
Labels:             beta.kubernetes.io/arch=amd64
                    beta.kubernetes.io/os=linux
                    kubernetes.io/arch=am
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:               node1
Roles:              <none>
Labels:             beta.kubernetes.io/arch=amd64
                    beta.kubernetes.io/os=linux
                    kubernetes.io/arch=amd64
    
   💭 [问题定位] 现在情况非常清楚了。让我再确认一下这个 Deployment/ReplicaSet 的信息。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 NAME                            READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES         SELECTOR    LABELS
deployment.apps/l1-test-nginx   0/1     1            0           22m   nginx      
   💭 [问题定位] 好的，现在我已经获得了完整的诊断信息。让我输出定位结果。

```json
{
  "layer": "L1",
  "layers": ["L1"],
  "layer_name": "集群节点层",
  "confidence": 1.0,
  "reasoning": "集群整体健康（3节点均 Ready、所有系统组件 Running、无存储问题），但存在一个明确异常对象：aiops-e2e/l1-test-nginx-6c69dc7c76-fwzgn 持续 Pending 无法调度。根因是 node2 节点上有 test-unschedulable=true:NoSchedule taint，而该 Pod 的 nodeSelector 强制要求调度到 kubernetes.io/hostname=node2，导致调度器无可用节点（node2 被 taint 且 Pod 未 toleration；master/node1 不满足 nodeSelector）。这是一个由节点 Taint 导致的调度问题，属于 L1 层。",
  "key_entities": [
    {"type": "Pod", "value": "l1-test-nginx-6c69dc7c76-fwzgn"},
    {"type": "Namespace", "value": "aiops-e2e"},
    {"type": "Node", "value": "node2"},
    {"type": "Deployment", "value": "l1-test-nginx"}
  ],
  "possible_scenarios": ["Taint/NodeSelector 冲突导致无法调度"]
}
```

### 简要说明

**当前活跃异常：1 个**
- **Pod `l1-test-nginx-6c69dc7c76-fwzgn`**（aiops-e2e 命名空间）处于 **Pending** 状态

**根因分析：**
- Pod 设置了 `nodeSelector: kubernetes.io/hostname=node2`，只能调度到 node2
- 但 **node2** 节点上有 `test-unschedulable=true:NoSchedule` 的 taint
- Pod 没有对应的 toleration，因此无法调度到 node2
- master 和 node1 不满足 nodeSelector，也不可用
- 结果是 0/3 节点可用，Pod 一直 Pending

**其他层面均正常：**
- 所有 3 个节点 Ready，Conditions 正常
- 所有系统组件（etcd、apiserver、scheduler、controller-manager、CoreDNS、Calico、kube-proxy）均 Running
- 无存储/PVC问题
- 无 OOMKilled、CrashLoopBackOff、ImagePullBackOff 等其他异常
   ✅ [问题定位] 完成 (29.6s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=['Taint/NodeSelector 冲突导致无法调度']
   entities=[{"type": "Pod", "value": "l1-test-nginx-6c69dc7c76-fwzgn"}, {"type": "Namespace", "value": "aiops-e2e"}, {"type": "Node", "value": "node2"}, {"type": "Deployment", "value": "l1-test-nginx"}]
   reasoning=集群整体健康（3节点均 Ready、所有系统组件 Running、无存储问题），但存在一个明确异常对象：aiops-e2e/l1-test-nginx-6c69dc7c76-fwzgn 持续 Pending 无法调度。根因是 node2 节点上有 test-unschedulable=true:NoSchedule taint，而该 Pod 的 nodeSelector 强制要求调度到 kubernetes.io/hostname=node2，导致调度器无可用节点（node2 被 taint 且 Pod 未 toleration；master/node1 不满足 nodeSelector）。这是一个由节点 Taint 导致的调度问题，属于 L1 层。
   layer_analysis={"layer": "L1", "layers": ["L1"], "layer_name": "集群节点层", "confidence": 1.0, "reasoning": "集群整体健康（3节点均 Ready、所有系统组件 Running、无存储问题），但存在一个明确异常对象：aiops-e2e/l1-test-nginx-6c69dc7c76-fwzgn 持续 Pending 无法调度。根因是 node2 节点上有 test-unschedulable=true:NoSchedule taint，而该 Pod 的 nodeSelector 强制要求调度到 kubernetes.io/hostname=node2，导致调度器无可用节点（node2 被 taint 且 Pod 未 toleration；master/node1 不满足 nodeSelector）。这是一个由节点 Taint 导致的调度问题，属于 L1 层。", "key_entities": [{"type": "Pod", "value": "l1-test-nginx-6c69dc7c76-fwzgn"}, {"type": "Namespace", "value": "aiops-e2e"}, {"type": "Node", "value": "node2"}, {"type": "Deployment", "value": "l1-test-nginx"}], "possible_scenarios": ["Taint/NodeSelector 冲突导致无法调度"]}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 100%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 让我先获取相关 runbook 来确认诊断步骤。

根据上游的定位结果，问题已经被精确定位为 **L1 层级 - Taint/NodeSelector 冲突导致 Pod 无法调度**。让我制定证据采集计划并采集关键证据来验证。

## 第一步：输出 JSON 证据采集计划

```json
{
  "layer": "L1",
  "evidence_plan": [
    {
      "id": "e1",
      "description": "Pod 详细描述 — 确认调度失败事件和原因",
      "level": "critical",
      "tool": "kubectl_describe",
      "command": "kubectl describe pod l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e",
      "purpose": "查看 FailedScheduling 事件详情，确认调度器报错信息"
    },
    {
      "id": "e2",
      "description": "Pod YAML — 确认 nodeSelector 和 tolerations 配置",
      "level": "critical",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get pod l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e -o yaml",
      "purpose": "查看 Pod 的 nodeSelector 和 tolerations 字段"
    },
    {
      "id": "e3",
      "description": "Node node2 详情 — 确认 taint 和 conditions",
      "level": "critical",
      "tool": "kubectl_describe",
      "command": "kubectl describe node node2",
      "purpose": "查看 node2 上的 taint 和节点条件"
    },
    {
      "id": "e4",
      "description": "所有节点 Taints 一览",
      "level": "important",
      "tool": "kubernetes_tabular_query",
      "command": "kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints",
      "purpose": "查看所有节点的 taint 状态，确认只有 node2 有 taint"
    },
    {
      "id": "e5",
      "description": "Deployment 状态确认",
      "level": "important",
      "tool": "kubectl_get_by_name",
      "command": "kubectl get deployment l1-test-nginx -n aiops-e2e -o wide",
      "purpose": "确认 Deployment 的可用副本数"
    },
    {
      "id": "e6",
      "description": "Pod Events 详情",
      "level": "important",
      "tool": "kubectl_events",
      "command": "kubectl events for pod l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e",
      "purpose": "获取调度失败的具体事件记录"
    },
    {
      "id": "e7",
      "description": "所有节点 Ready 状态确认",
      "level": "important",
      "tool": "kubectl_get_by_kind_in_cluster",
      "command": "kubectl get nodes",
      "purpose": "确认集群节点整体健康状态"
    }
  ],
  "collection_strategy": "先采集 Pod 和 Node 的核心证据，确认 Taint/NodeSelector 冲突是唯一原因，再补充辅助确认数据"
}
```

现在开始逐项执行：
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubernetes_tabular_query
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubernetes_tabular_query (success)
      📄 NAME     TAINTS
master   <none>
node1    <none>
node2    [map[effect:NoSchedule key:test-unschedulable value:true]]
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:             l1-test-nginx-6c69dc7c76-fwzgn
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             <none>
Labels:           app=nginx
                  e2e-te
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME            READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES         SELECTOR    LABELS
l1-test-nginx   0/1     1            0           23m   nginx        nginx:alpine   app=nginx   e2e
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
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   209d   v1.26.8  
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:               node2
Roles:              <none>
Labels:             beta.kubernetes.io/arch=amd64
                    beta.kubernetes.io/os=linux
                    kubernetes.io/arch=amd64
    
   💭 [证据链采集] 让我再补充一个 Pod events 的信息来完善证据。
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 LAST SEEN           TYPE      REASON             OBJECT                               MESSAGE
23m                 Warning   FailedScheduling   Pod/l1-test-nginx-6c69dc7c76-fwzgn   0/3 nodes are availa
   ✅ [证据链采集] 完成 (15.7s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan": [{"id": "e1", "description": "Pod 详细描述 — 确认调度失败事件和原因", "level": "critical", "tool": "kubectl_describe", "command": "kubectl describe pod l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e", "purpose": "查看 FailedScheduling 事件详情，确认调度器报错信息"}, {"id": "e2", "description": "Pod YAML — 确认 nodeSelector 和 tolerations 配置", "level": "critical", "tool": "kubectl_get_yaml", "command": "kubectl get pod l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e -o yaml", "purpose": "查看 Pod 的 nodeSelector 和 tolerations 字段"}, {"id": "e3", "description": "Node node2 详情 — 确认 taint 和 conditions", "level": "critical", "tool": "kubectl_describe", "command": "kubectl describe node node2", "purpose": "查看 node2 上的 taint 和节点条件"}, {"id": "e4", "description": "所有节点 Taints 一览", "level": "important", "tool": "kubernetes_tabular_query", "command": "kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints", "purpose": "查看所有节点的 taint 状态，确认只有 node2 有 taint"}, {"id": "e5", "description": "Deployment 状态确认", "level": "important", "tool": "kubectl_get_by_name", "command": "kubectl get deployment l1-test-nginx -n aiops-e2e -o wide", "purpose": "确认 Deployment 的可用副本数"}, {"id": "e6", "description": "Pod Events 详情", "level": "important", "tool": "kubectl_events", "command": "kubectl events for pod l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e", "purpose": "获取调度失败的具体事件记录"}, {"id": "e7", "description": "所有节点 Ready 状态确认", "level": "important", "tool": "kubectl_get_by_kind_in_cluster", "command": "kubectl get nodes", "purpose": "确认集群节点整体健康状态"}], "tool_results": [], "tool_data": [{"tool": "kubernetes_tabular_query", "data": "NAME     TAINTS\nmaster   <none>\nnode1    <none>\nnode2    [map[effect:NoSchedule key:test-unschedulable value:true]]", "duration_s": 0}, {"tool": "kubectl_describe", "data": "Name:             l1-test-nginx-6c69dc7c76-fwzgn\nNamespace:        aiops-e2e\nPriority:         0\nService Account:  default\nNode:             <none>\nLabels:           app=nginx\n                  e2e-test=true\n                  pod-template-hash=6c69dc7c76\nAnnotations:      <none>\nStatus:           Pending\nIP:               \nIPs:              <none>\nControlled By:    ReplicaSet/l1-test-nginx-6c69dc7c76\nContainers:\n  nginx:\n    Image:        nginx:alpine\n    Port:         <none>\n    Host Port:    <none>\n    Environment:  <none>\n    Mounts:\n      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-ww78k (ro)\nConditions:\n  Type           Status\n  PodScheduled   False \nVolumes:\n  kube-api-access-ww78k:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    TokenExpirationSeconds:  3607\n    ConfigMapName:           kube-root-ca.crt\n    ConfigMapOptional:       <nil>\n    DownwardAPI:             true\nQoS Class:                   BestEffort\nNode-Selectors:              kubernetes.io/hostname=node2\nTolerations:                 node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\n                             node.kubernetes.io/unreachable:NoExecute op=Exists for 300s\nEvents:\n  Type     Reason            Age                From               Message\n  ----     ------            ----               ----               -------\n  Warning  FailedScheduling  23m                default-scheduler  0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  13m (x2 over 18m)  default-scheduler  0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..", "duration_s": 0}, {"tool": "kubectl_get_by_name", "data": "NAME            READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES         SELECTOR    LABELS\nl1-test-nginx   0/1     1            0           23m   nginx        nginx:alpine   app=nginx   e2e-test=true", "duration_s": 0}, {"tool": "kubectl_get_yaml", "data": "apiVersion: v1\nkind: Pod\nmetadata:\n  creationTimestamp: \"2026-04-22T06:51:29Z\"\n  generateName: l1-test-nginx-6c69dc7c76-\n  labels:\n    app: nginx\n    e2e-test: \"true\"\n    pod-template-hash: 6c69dc7c76\n  name: l1-test-nginx-6c69dc7c76-fwzgn\n  namespace: aiops-e2e\n  ownerReferences:\n  - apiVersion: apps/v1\n    blockOwnerDeletion: true\n    controller: true\n    kind: ReplicaSet\n    name: l1-test-nginx-6c69dc7c76\n    uid: f0ae3eb5-88c2-4ca0-9efa-9db2e69389aa\n  resourceVersion: \"46405555\"\n  uid: f862460b-a1d6-4329-b5ad-1c9188af03cc\nspec:\n  containers:\n  - image: nginx:alpine\n    imagePullPolicy: IfNotPresent\n    name: nginx\n    resources: {}\n    terminationMessagePath: /dev/termination-log\n    terminationMessagePolicy: File\n    volumeMounts:\n    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount\n      name: kube-api-access-ww78k\n      readOnly: true\n  dnsPolicy: ClusterFirst\n  enableServiceLinks: true\n  nodeSelector:\n    kubernetes.io/hostname: node2\n  preemptionPolicy: PreemptLowerPriority\n  priority: 0\n  restartPolicy: Always\n  schedulerName: default-scheduler\n  securityContext: {}\n  serviceAccount: default\n  serviceAccountName: default\n  terminationGracePeriodSeconds: 30\n  tolerations:\n  - effect: NoExecute\n    key: node.kubernetes.io/not-ready\n    operator: Exists\n    tolerationSeconds: 300\n  - effect: NoExecute\n    key: node.kubernetes.io/unreachable\n    operator: Exists\n    tolerationSeconds: 300\n  volumes:\n  - name: kube-api-access-ww78k\n    projected:\n      defaultMode: 420\n      sources:\n      - serviceAccountToken:\n          expirationSeconds: 3607\n          path: token\n      - configMap:\n          items:\n          - key: ca.crt\n            path: ca.crt\n          name: kube-root-ca.crt\n      - downwardAPI:\n          items:\n          - fieldRef:\n              apiVersion: v1\n              fieldPath: metadata.namespace\n            path: namespace\nstatus:\n  conditions:\n  - lastProbeTime: null\n    lastTransitionTime: \"2026-04-22T06:51:29Z\"\n    message: '0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable:\n      true}, 2 node(s) didn''t match Pod''s node affinity/selector. preemption: 0/3\n      nodes are available: 3 Preemption is not helpful for scheduling..'\n    reason: Unschedulable\n    status: \"False\"\n    type: PodScheduled\n  phase: Pending\n  qosClass: BestEffort", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_cluster", "data": "NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nmaster   Ready    control-plane   209d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          209d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-174-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          209d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-174-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux", "duration_s": 0}, {"tool": "kubectl_describe", "data": "Name:               node2\nRoles:              <none>\nLabels:             beta.kubernetes.io/arch=amd64\n                    beta.kubernetes.io/os=linux\n                    kubernetes.io/arch=amd64\n                    kubernetes.io/hostname=node2\n                    kubernetes.io/os=linux\nAnnotations:        kubeadm.alpha.kubernetes.io/cri-socket: unix:///var/run/containerd/containerd.sock\n                    node.alpha.kubernetes.io/ttl: 0\n                    projectcalico.org/IPv4Address: 10.2.0.50/19\n                    projectcalico.org/IPv4IPIPTunnelAddr: 172.16.104.0\n                    volumes.kubernetes.io/controller-managed-attach-detach: true\nCreationTimestamp:  Thu, 25 Sep 2025 03:10:26 +0000\nTaints:             test-unschedulable=true:NoSchedule\nUnschedulable:      false\nLease:\n  HolderIdentity:  node2\n  AcquireTime:     <unset>\n  RenewTime:       Wed, 22 Apr 2026 07:14:51 +0000\nConditions:\n  Type                 Status  LastHeartbeatTime                 LastTransitionTime                Reason                       Message\n  ----                 ------  -----------------                 ------------------                ------                       -------\n  NetworkUnavailable   False   Fri, 17 Apr 2026 07:03:52 +0000   Fri, 17 Apr 2026 07:03:52 +0000   CalicoIsUp                   Calico is running on this node\n  MemoryPressure       False   Wed, 22 Apr 2026 07:12:28 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletHasSufficientMemory   kubelet has sufficient memory available\n  DiskPressure         False   Wed, 22 Apr 2026 07:12:28 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletHasNoDiskPressure     kubelet has no disk pressure\n  PIDPressure          False   Wed, 22 Apr 2026 07:12:28 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletHasSufficientPID      kubelet has sufficient PID available\n  Ready                True    Wed, 22 Apr 2026 07:12:28 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletReady                 kubelet is posting ready status. AppArmor enabled\nAddresses:\n  InternalIP:  10.2.0.50\n  Hostname:    node2\nCapacity:\n  cpu:                12\n  ephemeral-storage:  203770680Ki\n  hugepages-1Gi:      0\n  hugepages-2Mi:      0\n  memory:             32860484Ki\n  pods:               110\nAllocatable:\n  cpu:                12\n  ephemeral-storage:  187795058378\n  hugepages-1Gi:      0\n  hugepages-2Mi:      0\n  memory:             32758084Ki\n  pods:               110\nSystem Info:\n  Machine ID:                 6bb27862c82149418d0f5624411d0b22\n  System UUID:                0f5af30a-d385-493c-bc8b-5442fd024eee\n  Boot ID:                    0ea98079-ad10-4a20-85f5-19b34afd257e\n  Kernel Version:             5.15.0-174-generic\n  OS Image:                   Ubuntu 22.04.4 LTS\n  Operating System:           linux\n  Architecture:               amd64\n  Container Runtime Version:  containerd://1.6.32\n  Kubelet Version:            v1.26.8\n  Kube-Proxy Version:         v1.26.8\nNon-terminated Pods:          (14 in total)\n  Namespace                   Name                                            CPU Requests  CPU Limits  Memory Requests  Memory Limits  Age\n  ---------                   ----                                            ------------  ----------  ---------------  -------------  ---\n  aiops                       aiops-copilot-76779bb6df-4bcrf                  250m (2%)     1 (8%)      512Mi (1%)       2Gi (6%)       5h37m\n  default                     exec-test                                       0 (0%)        0 (0%)      0 (0%)           0 (0%)         2d3h\n  default                     network-test-from-running                       0 (0%)        0 (0%)      0 (0%)           0 (0%)         2d1h\n  default                     nfs-client-provisioner-6fcd4994c9-lczf6         0 (0%)        0 (0%)      0 (0%)           0 (0%)         85d\n  kube-system                 calico-node-d2dhp                               250m (2%)     0 (0%)      0 (0%)           0 (0%)         183d\n  kube-system                 kube-multus-ds-x7h9s                            100m (0%)     100m (0%)   50Mi (0%)        50Mi (0%)      183d\n  kube-system                 kube-proxy-69zzr                                0 (0%)        0 (0%)      0 (0%)           0 (0%)         28d\n  mcp                         mcp-server-manager-8677f6896c-d4mr9             200m (1%)     1 (8%)      1G (2%)          2560Mi (8%)    45h\n  xnet                        deepflow-agent-trc8k                            100m (0%)     1 (8%)      128Mi (0%)       768Mi (2%)     19d\n  xnet                        ham-p9dxv                                       0 (0%)        0 (0%)      0 (0%)           0 (0%)         177d\n  xnet                        observability-filebeat-w6gtr                    100m (0%)     1 (8%)      100Mi (0%)       200Mi (0%)     19d\n  xnet                        observability-kepler-ggstf                      0 (0%)        0 (0%)      0 (0%)           0 (0%)         19d\n  xnet                        observability-prometheus-node-exporter-qp2qd    0 (0%)        0 (0%)      0 (0%)           0 (0%)         19d\n  xnet                        xnet-agent-568f547566-jdsgp                     0 (0%)        0 (0%)      0 (0%)           0 (0%)         108d\nAllocated resources:\n  (Total limits may be over 100 percent, i.e., overcommitted.)\n  Resource           Requests         Limits\n  --------           --------         ------\n  cpu                1 (8%)           4100m (34%)\n  memory             1828375040 (5%)  5626Mi (17%)\n  ephemeral-storage  0 (0%)           0 (0%)\n  hugepages-1Gi      0 (0%)           0 (0%)\n  hugepages-2Mi      0 (0%)           0 (0%)\nEvents:              <none>", "duration_s": 0}, {"tool": "kubectl_events", "data": "LAST SEEN           TYPE      REASON             OBJECT                               MESSAGE\n23m                 Warning   FailedScheduling   Pod/l1-test-nginx-6c69dc7c76-fwzgn   0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n13m (x2 over 18m)   Warning   FailedScheduling   Pod/l1-test-nginx-6c69dc7c76-fwzgn   0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..", "duration_s": 0}], "llm_analysis": "让我再补充一个 Pod events 的信息来完善证据。", "collection_summary": "计划 7 项，实际采集 7 项，未采集 0 项，完整度 100%", "evidence_inventory": [{"id": "e1", "description": "Pod 详细描述 — 确认调度失败事件和原因", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e2", "description": "Pod YAML — 确认 nodeSelector 和 tolerations 配置", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e3", "description": "Node node2 详情 — 确认 taint 和 conditions", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e4", "description": "所有节点 Taints 一览", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e5", "description": "Deployment 状态确认", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e6", "description": "Pod Events 详情", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e7", "description": "所有节点 Ready 状态确认", "level": "important", "collected": true, "source": "thinking_match"}], "missing_reasons": [], "early_stop": {"triggered": true, "reason": "critical 和 important 级证据均已满足，提前停止后续采集", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 7/7 项, 完整度: 100%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (24.4s)
   📤 → 下游数据: root_cause=
   confidence=95%
   causal_chain={"root_cause": "Pod 的 `nodeSelector: kubernetes.io/hostname=node2` 与 `node2` 上的 `test-unschedulable=true:NoSchedule` taint 共同导致调度冲突。Pod 配置了强制的节点选择，却没有配置对应的容忍，而 `master` 和 `node1` 不符合选择条件。", "propagation": "1. 运维人员（或自动化工具）在 `node2` 上添加了 `test-unschedulable` taint 进行测试或维护。\n2. 用户创建了 Deployment `l1-test-nginx`，其 Pod 模板定义了 nodeSelector 固定到 `node2`。\n3. Pod 无法容忍 `node2` 的 taint，也无法调度到其他节点。\n4. 调度器反复重试均失败，Pod 始终处于 Pending 状态。", "direct_cause": "Pod `l1-test-nginx-6c69dc7c76-fwzgn` 缺少对 `test-unschedulable=true:NoSchedule` taint 的 toleration。", "manifestation": "Pod 状态为 Pending，Deployment `l1-test-nginx` 的可用副本数为 0/1，服务不可访问。调度器 Events 明确报告 '0/3 nodes are available'。"}
   rca_analysis={"phenomenon": "Deployment `l1-test-nginx` 的 Pod `l1-test-nginx-6c69dc7c76-fwzgn` 在 namespace `aiops-e2e` 中处于 Pending 状态，持续 23 分钟，无法获得 Ready 副本，服务不可用。", "evidence_inventory": [{"id": "e1", "content": "Pod 详细描述，包括状态、Node-Selector、Tolerations 和 Events", "source": "kubectl describe pod l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e", "reliability": "高"}, {"id": "e2", "content": "Pod 的完整 YAML 定义，确认 nodeSelector 和 tolerations", "source": "kubectl get pod l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e -o yaml", "reliability": "高"}, {"id": "e3", "content": "Node node2 的详细信息，包括 taint 和 conditions", "source": "kubectl describe node node2", "reliability": "高"}, {"id": "e4", "content": "所有节点的 taints 列表", "source": "kubernetes_tabular_query 工具", "reliability": "高"}, {"id": "e5", "content": "Deployment 状态", "source": "kubectl get deployment l1-test-nginx -n aiops-e2e", "reliability": "高"}, {"id": "e6", "content": "所有节点的 Ready 状态", "source": "kubectl get nodes -o wide", "reliability": "高"}, {"id": "e7", "content": "Pod 相关 Events", "source": "kubectl events --for Pod/l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Status: Pending, Node: <none>, Node-Selectors: kubernetes.io/hostname=node2, Tolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s, node.kubernetes.io/unreachable:NoExecute op=Exists for 300s, Events: Warning FailedScheduling - '0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector.'", "interpretation": "Pod 明确要求调度到 `node2`，但默认调度器报告 3 个节点均不可用：`node2` 有未被容忍的 taint，`master` 和 `node1` 不满足 nodeSelector 条件。Pod 的 tolerations 只覆盖了 not-ready 和 unreachable 的 NoExecute 效果，没有覆盖 `test-unschedulable=true:NoSchedule` taint。"}, {"evidence_id": "e2", "raw_data": "spec.nodeSelector: kubernetes.io/hostname: node2, spec.tolerations: [{key: node.kubernetes.io/not-ready, operator: Exists, effect: NoExecute, tolerationSeconds: 300}, {key: node.kubernetes.io/unreachable, operator: Exists, effect: NoExecute, tolerationSeconds: 300}], status.conditions[0].message: '0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector.'", "interpretation": "Pod 配置确认只有默认的容忍项，缺少对 `test-unschedulable=true:NoSchedule` 的容忍，这与 e1 的事件信息完全一致。"}, {"evidence_id": "e3", "raw_data": "Taints: test-unschedulable=true:NoSchedule, Conditions: MemoryPressure=False, DiskPressure=False, PIDPressure=False, Ready=True", "interpretation": "`node2` 节点本身运行正常（Ready，无资源压力），但被人为添加了一个 `test-unschedulable=true:NoSchedule` taint，导致所有没有对应 toleration 的 Pod 都无法调度到该节点。"}, {"evidence_id": "e4", "raw_data": "master: <none>, node1: <none>, node2: [map[effect:NoSchedule key:test-unschedulable value:true]]", "interpretation": "集群中仅 `node2` 有此特殊 taint，`master` 和 `node1` 没有 taint。但由于 Pod 的 nodeSelector 限定了只能调度到 `node2`，其他节点即使没有 taint 也不符合调度条件。"}, {"evidence_id": "e5", "raw_data": "NAME: l1-test-nginx, READY: 0/1, UP-TO-DATE: 1, AVAILABLE: 0, AGE: 23m", "interpretation": "Deployment 期望 1 个副本，ReplicaSet 已创建 1 个 Pod，但 Pod 无法 Ready，导致 Deployment 可用副本为 0。这证实了该 Pod 的 Pending 状态已对上层工作负载造成直接影响。"}, {"evidence_id": "e6", "raw_data": "master: Ready (10.2.0.48), node1: Ready (10.2.0.49), node2: Ready (10.2.0.50)", "interpretation": "3 个节点均处于 Ready 状态，说明调度失败与节点健康或资源无关。这与 e3 中 node2 的 conditions 相符。"}, {"evidence_id": "e7", "raw_data": "23m ago Warning FailedScheduling: '0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector.', 13m ago (x2 over 18m) Warning FailedScheduling: (same message)", "interpretation": "调度器在 23 分钟内持续尝试调度该 Pod 共 3 次，均因同一原因失败，确认这是一个持续性的调度阻塞问题，而非临时故障。"}], "causal_chain": {"root_cause": "Pod 的 `nodeSelector: kubernetes.io/hostname=node2` 与 `node2` 上的 `test-unschedulable=true:NoSchedule` taint 共同导致调度冲突。Pod 配置了强制的节点选择，却没有配置对应的容忍，而 `master` 和 `node1` 不符合选择条件。", "propagation": "1. 运维人员（或自动化工具）在 `node2` 上添加了 `test-unschedulable` taint 进行测试或维护。\n2. 用户创建了 Deployment `l1-test-nginx`，其 Pod 模板定义了 nodeSelector 固定到 `node2`。\n3. Pod 无法容忍 `node2` 的 taint，也无法调度到其他节点。\n4. 调度器反复重试均失败，Pod 始终处于 Pending 状态。", "direct_cause": "Pod `l1-test-nginx-6c69dc7c76-fwzgn` 缺少对 `test-unschedulable=true:NoSchedule` taint 的 toleration。", "manifestation": "Pod 状态为 Pending，Deployment `l1-test-nginx` 的可用副本数为 0/1，服务不可访问。调度器 Events 明确报告 '0/3 nodes are available'。"}, "root_cause_summary": "Pod `l1-test-nginx-6c69dc7c76-fwzgn` 无法调度是因为其 `nodeSelector` 限定在 `node2`（证据 e1, e2），而 `node2` 存在 `test-unschedulable=true:NoSchedule` taint（证据 e3, e4），Pod 未配置对应的 toleration，导致调度器拒绝将其调度到 `node2`。同时，`master` 和 `node1` 虽然无 taint，但不满足 `nodeSelector` 条件（证据 e6）。此冲突导致调度器在 23 分钟内连续 3 次调度失败（证据 e7），Deployment 始终处于 0/1 可用状态（证据 e5）。", "confidence": 0.95, "primary_runbooks": ["Pod Pending 调度失败排查"], "alternative_causes": [{"cause": "node2 可能被错误地添加了 taint，但无明确证据表明此 taint 的意图。", "probability": "低"}], "limitations": "根因分析准确，但无法确定 `node2` 上的 `test-unschedulable=true:NoSchedule` taint 是由谁、在何时、因何种目的添加的。仅从现有集群状态看，其他所有系统组件和 DaemonSet（如 calico-node、kube-proxy）均正常运行在 node2 上，说明这些组件有相应的 toleration，但用户创建的 Pod 没有。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 95%
   🔗 因果链:
     根本原因: Pod 的 `nodeSelector: kubernetes.io/hostname=node2` 与 `node2` 上的 `test-unschedulable=true:NoSchedule` taint 共同导致调度冲突。Pod 配置了强制的节点选择，却没有配置对应的容忍，而 `master` 和 `node1` 不符合选择条件。
     传导机制: 1. 运维人员（或自动化工具）在 `node2` 上添加了 `test-unschedulable` taint 进行测试或维护。
2. 用户创建了 Deployment `l1-test-nginx`，其 Pod 模板定义了 nodeSelector 固定到 `node2`。
3. Pod 无法容忍 `node2` 的 taint，也无法调度到其他节点。
4. 调度器反复重试均失败，Pod 始终处于 Pending 状态。
     最终表现: Pod 状态为 Pending，Deployment `l1-test-nginx` 的可用副本数为 0/1，服务不可访问。调度器 Events 明确报告 '0/3 nodes are available'。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (27.6s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6240 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 37.3s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将基于您提供的分析结果，生成一份详尽的诊断报告。

---
## 📊 诊断概览

**核心问题总结：**

您的集群整体健康，所有节点（master, node1, node2）均处于 Ready 状态，核心系统组件运行正常。但存在 **1 个部署问题**：

-   **问题工作负载**：`aiops-e2e` 命名空间下的 `l1-test-nginx` Deployment 的 Pod `l1-test-nginx-6c69dc7c76-fwzgn` 处于 **Pending** 状态，无法提供服务。
-   **根因**：Pod 配置了 `nodeSelector: kubernetes.io/hostname=node2`，强制要求调度到 `node2`，但 `node2` 节点上存在一个未被 Pod 容忍的 `test-unschedulable=true:NoSchedule` 污点（Taint），导致调度冲突。

| 项目 | 内容 |
|------|------|
| **问题层级** | L3 - 应用/工作负载层问题 |
| **问题分类** | Pod 调度失败 (Taint/NodeSelector 冲突) |
| **置信度** | 高 (95%) |
| **证据完整度** | 7/7 (100%) |

---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 | 状态 |
|------|-----|------|
| Pod | `l1-test-nginx-6c69dc7c76-fwzgn` | Pending |
| Namespace | `aiops-e2e` | - |
| Deployment | `l1-test-nginx` | 0/1 available |
| Node | `node2` | Ready (但存在 `test-unschedulable` Taint) |
| Node | `master`, `node1` | Ready |

**错误信息**：
```
调度器事件：Warning FailedScheduling - 0/3 nodes are available: 
1 node(s) had untolerated taint {test-unschedulable: true}, 
2 node(s) didn't match Pod's node affinity/selector.
```

---
## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 事件 | `kubectl events for pod ...` | `0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector.` | 调度器明确报告：`node2` 有未被容忍的 taint，`master` 和 `node1` 不满足 nodeSelector。 |
| 2 | Pod 配置 | `kubectl get pod ... -o yaml` | `spec.nodeSelector: kubernetes.io/hostname: node2` | Pod 强制要求调度到 `node2`。 |
| 3 | Pod 配置 | `kubectl get pod ... -o yaml` | `spec.tolerations: [{key: node.kubernetes.io/not-ready ...}, {key: node.kubernetes.io/unreachable ...}]` | Pod 没有配置容忍 `test-unschedulable=true:NoSchedule` 的条目。 |
| 4 | Node 详情 | `kubectl describe node node2` | `Taints: test-unschedulable=true:NoSchedule` | `node2` 节点上存在人为添加的 `test-unschedulable` taint。 |
| 5 | 集群节点 | `kubectl get nodes ...` | `master: <none>`, `node1: <none>`, `node2: [map[effect:NoSchedule key:test-unschedulable value:true]]` | 只有 `node2` 有 taint，`master` 和 `node1` 没有。 |
| 6 | 节点状态 | `kubectl get nodes` | 所有节点 STATUS 均为 `Ready` | 集群节点本身健康，问题与节点资源无关。 |
| 7 | 工作负载 | `kubectl get deployment ...` | `NAME: l1-test-nginx, READY: 0/1, AVAILABLE: 0` | Pod Pending 已直接影响上层服务，导致 0 个可用副本。 |

### 证据关联分析
- **证据 #1 + #2 + #4 印证**：Pod 强制要求调度到 `node2`，而 `node2` 有 `test-unschedulable` taint，Pod 没有对应的 toleration，因此调度失败。
- **证据 #1 + #5 印证**：调度器报告“2 node(s) didn't match Pod's node affinity/selector”，这是因为 `master` 和 `node1` 虽然无 taint，但它们的 hostname 不是 `node2`，不满足 Pod 的 `nodeSelector`。
- **证据链**：Pod `nodeSelector` 约束 + Node `taint` 约束 + Pod `toleration` 缺失 → Pod 无法被调度到任何节点 → Pod 状态为 Pending → Deployment 不可用。

### 缺失证据
| 证据 | 级别 | 影响 |
|------|------|------|
| `test-unschedulable` taint 的添加者/时间 | 低 | 不影响根因定位，仅影响事后追责或自动化流程修复。 |

---
## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod `nodeSelector` 与 Node `taint` 冲突                         │
│ Pod 强制要求调度到 node2，但 node2 存在不可容忍的 taint        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 1. node2 有 taint (test-unschedulable=true:NoSchedule)          │
│ 2. Pod 有 nodeSelector (kubernetes.io/hostname=node2)           │
│ 3. Pod 无对应 toleration                                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 调度器评估所有节点后，发现无一可用                              │
│ (master/node1 不符 nodeSelector, node2 不符 taint)             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 Pending，Deployment 0/1 available，服务不可用          │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (调度器事件)、#2 (Pod nodeSelector) 和 #4 (Node taint)，
问题的根本原因是 **Pod `l1-test-nginx-6c69dc7c76-fwzgn` 的 `nodeSelector: kubernetes.io/hostname=node2` 与 `node2` 上的 `test-unschedulable=true:NoSchedule` taint 产生了冲突**。Pod 被强制要求调度到 `node2`，但又无法容忍该节点上的 taint，而其他节点又不满足调度条件，导致 Pod 永远无法被调度，服务不可用。

**置信度**：高 (95%)
- ✅ 调度器事件消息直接指明了两个冲突原因。
- ✅ Pod YAML 和 Node 描述完全印证了调度器消息。
- ✅ Deployment 状态为 0/1 available，确认了业务影响。

---
## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [推荐] 移除 node2 上的 taint（如果不再需要）**
这是最直接的修复方式，可以让所有 Pod 都能调度到 node2。
```bash
kubectl taint nodes node2 test-unschedulable=true:NoSchedule-
```
*依据*：移除 taint 后，`node2` 将不再有调度限制，Pod 的 `nodeSelector` 可以正常工作。

**2. [可选] 为 Pod 添加对应的 toleration（如果 taint 是必要的）**
如果您需要保留 node2 上的 taint（例如用于维护），则需要修改 Deployment，为其 Pod 添加容忍。
修改 `l1-test-nginx` Deployment 的 YAML 配置：
```yaml
# ... 在 spec.template.spec 下添加
tolerations:
- key: "test-unschedulable"
  operator: "Equal"
  value: "true"
  effect: "NoSchedule"
```
应用修改：
```bash
kubectl edit deployment l1-test-nginx -n aiops-e2e
# 将上述 tolerations 内容添加到 spec.template.spec.tolerations 下
```
*依据*：添加 toleration 后，Pod 就能被调度到 `node2` 上。

### 后续优化
1. **审查 nodeSelector 策略**：评估是否真的需要将 Pod 固定到特定节点。在大多数情况下，让调度器自动选择合适的节点是更优的策略。如需固定，请确保了解并管理好目标节点的 taint。
2. **配置门禁/审查**：考虑使用准入控制器（如 OPA/Gatekeeper）来防止创建 `nodeSelector` 与节点 `taint` 不匹配的 Pod。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 应用修复（选一） | 执行上方修复建议 #1 或 #2 | 命令执行成功 |
| 2. 检查 Pod 调度 | `kubectl get pod -n aiops-e2e -w` | Pod 状态从 `Pending` 变为 `Running` |
| 3. 确认 Deployment 状态 | `kubectl get deployment l1-test-nginx -n aiops-e2e` | `READY` 列为 `1/1`，`AVAILABLE` 列为 `1` |
| 4. 检查节点 taint（如果执行了 #1） | `kubectl describe node node2 | grep Taints` | `Taints: <none>` |

---
## ⚠️ 注意事项
- 该问题是由配置冲突导致的，不是集群硬件故障或资源瓶颈。
- 如果执行了移除 taint 的操作，请确保该操作符合您的运维流程（例如，如果该 taint 是用来标记维护中节点的）。
- 如果 Pod 仍然无法调度，请检查 Pod 事件是否有新的错误信息。

---

## 📊 性能统计

├─ 总耗时: 1.6m
├─ 问题定位: 29.6s (30%) ✅
├─ 证据链采集: 15.7s (16%) ✅
├─ 根因分析: 24.4s (25%) ✅
├─ 汇总总结: 27.6s (28%) ✅
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
