======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: ad2ae929193e43f4]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来帮您检查集群的健康状况。首先，让我获取一些基本信息来了解当前状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   209d   v1.26.8  
   💭 [问题定位] 节点状态看起来都是 Ready。现在让我检查 Pod 的整体状态：
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE,NAME,STATUS,READY,RESTARTS,AGE' | (head -n 1; tail -n +2 | grep -E 'Evicted|CrashLoopBackOff|ImagePullBackOff|Er
   💭 [问题定位] 让我使用正确的格式：
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 NAMESPACE     NAME                                                STATUS    READY   RESTARTS   AGE
aiops-e2e     network-test                                        Pending   false   0          2026-0
   💭 [问题定位] 发现有两个 Pod 处于 Pending 状态。让我获取通用健康检查参考手册作为基线，然后进一步检查这些 Pending Pod：
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# 私有化 Kubernetes 环境健康与高效排查参考手册

> 类型: reference | 适用: 私有化 Kubernetes 环境 | 环境特征: Calico + NFS + containerd

## 目的

本手册不是某个具体故障的处理步骤，而是一个**额外知识参考**：
- 帮助理解在私有化 Kubernetes 环境中，健康检查应重点关注哪些资源与信号

   💭 [问题定位] 现在让我检查这两个 Pending Pod 的详细信息：
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             network-test
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Wed, 22 Apr 2026 03:01:22 +0000
Labels:    
   💭 [问题定位] 现在检查另一个 Pending Pod：
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             simple-test
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Wed, 22 Apr 2026 03:03:59 +0000
Labels:     
   💭 [问题定位] 两个 Pod 都显示 ImagePullBackOff，无法从 Docker Hub 拉取 busybox 镜像。让我获取镜像拉取失败的 runbook 作为参考：
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# L3 镜像拉取失败 (ImagePullBackOff)

> 层级: L3 - 服务网络层 | 场景: 容器镜像拉取失败

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | ImagePullBackOff / ErrImagePull / ImageInspectError |
| Events | `Faile
   💭 [问题定位] 现在让我检查是否有其他异常 Pod，并查看节点状态：
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 NAMESPACE     NAME                                                STATUS    NODE     READY   RESTARTS
aiops         aiops-copilot-76779bb6df-4bcrf                      Running   node2    true    0
def
   💭 [问题定位] 让我检查一下节点 node2 的状态，因为两个 Pending Pod 都在这个节点上：
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:               node2
Roles:              <none>
Labels:             beta.kubernetes.io/arch=amd64
                    beta.kubernetes.io/os=linux
                    kubernetes.io/arch=amd64
    
   💭 [问题定位] 我注意到 node2 上还有一个 `imagepull-fail-victim` Pod，让我检查一下：
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             imagepull-fail-victim
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Wed, 22 Apr 2026 02:57:28 +0000
La
   💭 [问题定位] 现在我有三个 Pod 都显示 ImagePullBackOff。让我检查一下是否有其他异常状态的 Pod：
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,READY:.status.containerStatuses
   💭 [问题定位] 让我检查一下是否有其他异常：
   💭 [问题定位] 调用工具: kubernetes_count
   💭 [问题定位] 工具结果: kubernetes_count (success)
      📄 Count for pods with jq...
3 results
---
{"namespace":"aiops-e2e","name":"imagepull-fail-victim","phase":"Pending","node":"node2"}
{"namespace":"aiops-e2e","name":"network-test","phase":"Pending","node
   💭 [问题定位] 基于我的检查，我发现集群中有三个 Pod 处于 Pending 状态，都是因为 ImagePullBackOff。从 describe 信息可以看到，这些 Pod 无法从 Docker Hub 拉取镜像（busybox 和 nginx），错误信息显示连接被重置或超时。

根据五层模型，镜像拉取失败属于 L3（服务网络层）。让我检查一下是否有其他网络相关的问题：
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 NAME                                    TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)                        AGE    SELECTOR                            LABELS
kube-dns                               
   💭 [问题定位] 让我检查一下 CoreDNS Pod 的状态：
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 NAME                                       READY   STATUS    RESTARTS         AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
calico-kube-controllers-6c67f9d475-2xcb7   1/1 
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (2m 15.2s)
   📤 → 下游数据: layer=Layer.L3, layers=L3
   scenarios=[{'scenario': '节点网络出口限制/防火墙', 'probability': '高', 'reason': 'node2节点无法访问外部Docker Hub镜像仓库，出现连接重置和超时错误'}, {'scenario': 'DNS解析问题', 'probability': '中', 'reason': 'CoreDNS运行正常，但可能存在特定域名解析问题'}, {'scenario': '镜像拉取代理配置问题', 'probability': '中', 'reason': '节点可能配置了错误的镜像拉取代理或认证'}]
   entities=[{"type": "Pod", "value": "aiops-e2e/imagepull-fail-victim"}, {"type": "Pod", "value": "aiops-e2e/network-test"}, {"type": "Pod", "value": "aiops-e2e/simple-test"}, {"type": "Node", "value": "node2"}]
   reasoning=发现3个Pod处于Pending状态，原因为ImagePullBackOff，具体错误为连接被重置(connection reset by peer)和连接超时(i/o timeout)，目标地址为registry-1.docker.io。所有节点Ready，核心组件运行正常，问题局限于node2节点访问外部镜像仓库的网络连通性。
   layer_analysis={"layer": "L3", "layers": ["L3"], "layer_name": "网络/镜像拉取问题", "confidence": 0.95, "reasoning": "发现3个Pod处于Pending状态，原因为ImagePullBackOff，具体错误为连接被重置(connection reset by peer)和连接超时(i/o timeout)，目标地址为registry-1.docker.io。所有节点Ready，核心组件运行正常，问题局限于node2节点访问外部镜像仓库的网络连通性。", "key_entities": [{"type": "Pod", "value": "aiops-e2e/imagepull-fail-victim"}, {"type": "Pod", "value": "aiops-e2e/network-test"}, {"type": "Pod", "value": "aiops-e2e/simple-test"}, {"type": "Node", "value": "node2"}], "possible_scenarios": [{"scenario": "节点网络出口限制/防火墙", "probability": "高", "reason": "node2节点无法访问外部Docker Hub镜像仓库，出现连接重置和超时错误"}, {"scenario": "DNS解析问题", "probability": "中", "reason": "CoreDNS运行正常，但可能存在特定域名解析问题"}, {"scenario": "镜像拉取代理配置问题", "probability": "中", "reason": "节点可能配置了错误的镜像拉取代理或认证"}]}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L3
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 根据上游定位结果，我已经确认了集群中的问题：**L3 镜像拉取失败**。现在我将制定证据采集计划并执行工具采集真实数据。

```json
{
  "layer": "L3",
  "evidence_plan": [
    {
      "id": "e1",
      "description": "获取所有异常Pod的详细YAML配置，确认镜像拉取策略和镜像仓库地址",
      "level": "critical",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get -o yaml pod imagepull-fail-victim -n aiops-e2e",
      "purpose": "确认Pod的容器镜像配置、拉取策略、节点亲和性等详细信息"
    },
    {
      "id": "e2",
      "description": "获取node2节点的详细配置，检查节点标签、污点和网络配置",
      "level": "critical",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get -o yaml node node2",
      "purpose": "检查node2节点的网络配置、标签、污点，确认是否有网络限制"
    },
    {
      "id": "e3",
      "description": "检查kube-system命名空间的CoreDNS配置和运行状态",
      "level": "important",
      "tool": "kubectl_get_by_kind_in_namespace",
      "command": "kubectl get pods -n kube-system | grep -E 'coredns|dns'",
      "purpose": "确认CoreDNS服务是否正常运行，DNS解析是否正常"
    },
    {
      "id": "e4",
      "description": "检查kube-system命名空间的网络插件Calico状态",
      "level": "important",
      "tool": "kubectl_get_by_kind_in_namespace",
      "command": "kubectl get pods -n kube-system | grep calico",
      "purpose": "确认Calico网络插件在node2节点上的运行状态"
    },
    {
      "id": "e5",
      "description": "测试从node2节点到registry-1.docker.io的网络连通性",
      "level": "critical",
      "tool": "kubectl_run_image",
      "command": "kubectl run network-test --image=busybox --rm -it --restart=Never -n aiops-e2e --command -- sh -c 'echo Testing connectivity to registry-1.docker.io; nslookup registry-1.docker.io; echo Testing TCP connectivity; nc -zv registry-1.docker.io 443; echo Testing HTTP connectivity; wget -q -O- --timeout=5 https://registry-1.docker.io/v2/'",
      "purpose": "直接测试从集群内部到Docker Hub的网络连通性、DNS解析和HTTPS访问"
    },
    {
      "id": "e6",
      "description": "检查集群中其他节点是否也存在镜像拉取问题",
      "level": "important",
      "tool": "kubernetes_tabular_query",
      "command": "kubectl get pods -A -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,CONTAINERS:.status.containerStatuses[*].state.waiting.reason | grep -E 'ImagePullBackOff|ErrImagePull|Pending'",
      "purpose": "确认镜像拉取问题是否仅限于node2节点还是集群普遍问题"
    },
    {
      "id": "e7",
      "description": "检查集群的镜像拉取密钥配置",
      "level": "optional",
      "tool": "kubectl_get_by_kind_in_cluster",
      "command": "kubectl get secrets -A | grep -E 'docker|registry|pull'",
      "purpose": "检查是否有配置镜像拉取密钥，确认认证配置"
    }
  ],
  "collection_strategy": "首先确认Pod和节点的详细配置，然后测试网络连通性，最后检查相关组件状态。优先验证网络连通性问题，因为上游数据显示连接被重置和超时错误。"
}
```

现在开始逐项执行证据采集：

## 第一步：获取异常Pod的详细YAML配置
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 apiVersion: v1
kind: Pod
metadata:
  annotations:
    cni.projectcalico.org/containerID: 4f3143cc2cfc728765e1c380d885cb1b5dc32bb47097d80cdc2476c9e8f12e6e
    cni.projectcalico.org/podIP: 172.16.104.58
   💭 [证据链采集] ## 第二步：获取node2节点的详细配置
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 apiVersion: v1
kind: Node
metadata:
  annotations:
    kubeadm.alpha.kubernetes.io/cri-socket: unix:///var/run/containerd/containerd.sock
    node.alpha.kubernetes.io/ttl: "0"
    projectcalico.org/IP
   💭 [证据链采集] ## 第三步：检查CoreDNS配置和运行状态
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 NAME                                       READY   STATUS    RESTARTS         AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
calico-kube-controllers-6c67f9d475-2xcb7   1/1 
   💭 [证据链采集] ## 第四步：检查Calico网络插件状态

从上面的结果可以看到，Calico节点在node2上运行正常（calico-node-d2dhp）。

## 第五步：测试从node2节点到registry-1.docker.io的网络连通性
   💭 [证据链采集] 调用工具: kubectl_run_image
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 工具结果: kubectl_run_image (success)
      📄 {"success": false, "stdout": "pod \"network-test-debug\" deleted\nTesting TCP connectivity to port 443...\nTesting HTTP connectivity...\nHTTP test failed\nTesting connectivity to other external sites.
   💭 [证据链采集] busybox镜像缺少必要的网络工具。让我尝试使用一个包含更多工具的镜像：
   💭 [证据链采集] 调用工具: kubectl_run_image
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 工具结果: kubectl_run_image (success)
      📄 {"success": false, "stdout": "pod \"network-test-debug2\" deleted\nTesting TCP connectivity to port 443...\nTesting HTTP connectivity...\nCurl test failed\nTesting connectivity to other external sites
   💭 [证据链采集] 看起来netshoot镜像也没有安装dig和nc工具。让我尝试一个更简单的方法，直接使用TCP检查工具：
   💭 [证据链采集] 调用工具: tcp_check
   💭 [证据链采集] 工具结果: tcp_check (success)
      📄 {"ok": false, "error": "[Errno 101] Network is unreachable"}
   💭 [证据链采集] ## 第六步：检查集群中其他节点是否也存在镜像拉取问题
   💭 [证据链采集] 调用工具: kubernetes_tabular_query
   💭 [证据链采集] 工具结果: kubernetes_tabular_query (success)
      📄 NAMESPACE     NAME                                                STATUS    NODE     CONTAINERS
aiops-e2e     dns-test-temp                                       Pending   node2    ContainerCreating
a
   ✅ [证据链采集] 完成 (8m 53.3s)
   📤 → 下游数据: evidence_items=7/8
   evidence_analysis={"evidence_plan": [{"id": "e1", "description": "获取所有异常Pod的详细YAML配置，确认镜像拉取策略和镜像仓库地址", "level": "critical", "tool": "kubectl_get_yaml", "command": "kubectl get -o yaml pod imagepull-fail-victim -n aiops-e2e", "purpose": "确认Pod的容器镜像配置、拉取策略、节点亲和性等详细信息"}, {"id": "e2", "description": "获取node2节点的详细配置，检查节点标签、污点和网络配置", "level": "critical", "tool": "kubectl_get_yaml", "command": "kubectl get -o yaml node node2", "purpose": "检查node2节点的网络配置、标签、污点，确认是否有网络限制"}, {"id": "e3", "description": "检查kube-system命名空间的CoreDNS配置和运行状态", "level": "important", "tool": "kubectl_get_by_kind_in_namespace", "command": "kubectl get pods -n kube-system | grep -E 'coredns|dns'", "purpose": "确认CoreDNS服务是否正常运行，DNS解析是否正常"}, {"id": "e4", "description": "检查kube-system命名空间的网络插件Calico状态", "level": "important", "tool": "kubectl_get_by_kind_in_namespace", "command": "kubectl get pods -n kube-system | grep calico", "purpose": "确认Calico网络插件在node2节点上的运行状态"}, {"id": "e5", "description": "测试从node2节点到registry-1.docker.io的网络连通性", "level": "critical", "tool": "kubectl_run_image", "command": "kubectl run network-test --image=busybox --rm -it --restart=Never -n aiops-e2e --command -- sh -c 'echo Testing connectivity to registry-1.docker.io; nslookup registry-1.docker.io; echo Testing TCP connectivity; nc -zv registry-1.docker.io 443; echo Testing HTTP connectivity; wget -q -O- --timeout=5 https://registry-1.docker.io/v2/'", "purpose": "直接测试从集群内部到Docker Hub的网络连通性、DNS解析和HTTPS访问"}, {"id": "e6", "description": "检查集群中其他节点是否也存在镜像拉取问题", "level": "important", "tool": "kubernetes_tabular_query", "command": "kubectl get pods -A -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,CONTAINERS:.status.containerStatuses[*].state.waiting.reason | grep -E 'ImagePullBackOff|ErrImagePull|Pending'", "purpose": "确认镜像拉取问题是否仅限于node2节点还是集群普遍问题"}, {"id": "e7", "description": "检查集群的镜像拉取密钥配置", "level": "optional", "tool": "kubectl_get_by_kind_in_cluster", "command": "kubectl get secrets -A | grep -E 'docker|registry|pull'", "purpose": "检查是否有配置镜像拉取密钥，确认认证配置"}], "tool_results": [], "tool_data": [{"tool": "kubectl_get_yaml", "data": "apiVersion: v1\nkind: Pod\nmetadata:\n  annotations:\n    cni.projectcalico.org/containerID: 4f3143cc2cfc728765e1c380d885cb1b5dc32bb47097d80cdc2476c9e8f12e6e\n    cni.projectcalico.org/podIP: 172.16.104.58/32\n    cni.projectcalico.org/podIPs: 172.16.104.58/32\n    k8s.v1.cni.cncf.io/network-status: |-\n      [{\n          \"name\": \"k8s-pod-network\",\n          \"ips\": [\n              \"172.16.104.58\"\n          ],\n          \"default\": true,\n          \"dns\": {}\n      }]\n    k8s.v1.cni.cncf.io/networks-status: |-\n      [{\n          \"name\": \"k8s-pod-network\",\n          \"ips\": [\n              \"172.16.104.58\"\n          ],\n          \"default\": true,\n          \"dns\": {}\n      }]\n    kubectl.kubernetes.io/last-applied-configuration: |\n      {\"apiVersion\":\"v1\",\"kind\":\"Pod\",\"metadata\":{\"annotations\":{},\"labels\":{\"app\":\"imagepull-fail-victim\",\"expected_state\":\"ImagePullBackOff\",\"fault_level\":\"L3\",\"fault_type\":\"registry_unreachable\",\"role\":\"fault_injection_victim\"},\"name\":\"imagepull-fail-victim\",\"namespace\":\"aiops-e2e\"},\"spec\":{\"containers\":[{\"image\":\"nginx:latest\",\"imagePullPolicy\":\"Always\",\"name\":\"nginx\"}],\"restartPolicy\":\"Never\"}}\n  creationTimestamp: \"2026-04-22T02:57:28Z\"\n  labels:\n    app: imagepull-fail-victim\n    expected_state: ImagePullBackOff\n    fault_level: L3\n    fault_type: registry_unreachable\n    role: fault_injection_victim\n  name: imagepull-fail-victim\n  namespace: aiops-e2e\n  resourceVersion: \"46365274\"\n  uid: 63bbb8f8-658a-4e3c-80bd-f1ae57f80d8a\nspec:\n  containers:\n  - image: nginx:latest\n    imagePullPolicy: Always\n    name: nginx\n    resources: {}\n    terminationMessagePath: /dev/termination-log\n    terminationMessagePolicy: File\n    volumeMounts:\n    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount\n      name: kube-api-access-mmmhd\n      readOnly: true\n  dnsPolicy: ClusterFirst\n  enableServiceLinks: true\n  nodeName: node2\n  preemptionPolicy: PreemptLowerPriority\n  priority: 0\n  restartPolicy: Never\n  schedulerName: default-scheduler\n  securityContext: {}\n  serviceAccount: default\n  serviceAccountName: default\n  terminationGracePeriodSeconds: 30\n  tolerations:\n  - effect: NoExecute\n    key: node.kubernetes.io/not-ready\n    operator: Exists\n    tolerationSeconds: 300\n  - effect: NoExecute\n    key: node.kubernetes.io/unreachable\n    operator: Exists\n    tolerationSeconds: 300\n  volumes:\n  - name: kube-api-access-mmmhd\n    projected:\n      defaultMode: 420\n      sources:\n      - serviceAccountToken:\n          expirationSeconds: 3607\n          path: token\n      - configMap:\n          items:\n          - key: ca.crt\n            path: ca.crt\n          name: kube-root-ca.crt\n      - downwardAPI:\n          items:\n          - fieldRef:\n              apiVersion: v1\n              fieldPath: metadata.namespace\n            path: namespace\nstatus:\n  conditions:\n  - lastProbeTime: null\n    lastTransitionTime: \"2026-04-22T02:57:28Z\"\n    status: \"True\"\n    type: Initialized\n  - lastProbeTime: null\n    lastTransitionTime: \"2026-04-22T02:57:28Z\"\n    message: 'containers with unready status: [nginx]'\n    reason: ContainersNotReady\n    status: \"False\"\n    type: Ready\n  - lastProbeTime: null\n    lastTransitionTime: \"2026-04-22T02:57:28Z\"\n    message: 'containers with unready status: [nginx]'\n    reason: ContainersNotReady\n    status: \"False\"\n    type: ContainersReady\n  - lastProbeTime: null\n    lastTransitionTime: \"2026-04-22T02:57:28Z\"\n    status: \"True\"\n    type: PodScheduled\n  containerStatuses:\n  - image: nginx:latest\n    imageID: \"\"\n    lastState: {}\n    name: nginx\n    ready: false\n    restartCount: 0\n    started: false\n    state:\n      waiting:\n        message: Back-off pulling image \"nginx:latest\"\n        reason: ImagePullBackOff\n  hostIP: 10.2.0.50\n  phase: Pending\n  podIP: 172.16.104.58\n  podIPs:\n  - ip: 172.16.104.58\n  qosClass: BestEffort\n  startTime: \"2026-04-22T02:57:28Z\"", "duration_s": 0}, {"tool": "kubectl_get_yaml", "data": "apiVersion: v1\nkind: Node\nmetadata:\n  annotations:\n    kubeadm.alpha.kubernetes.io/cri-socket: unix:///var/run/containerd/containerd.sock\n    node.alpha.kubernetes.io/ttl: \"0\"\n    projectcalico.org/IPv4Address: 10.2.0.50/19\n    projectcalico.org/IPv4IPIPTunnelAddr: 172.16.104.0\n    volumes.kubernetes.io/controller-managed-attach-detach: \"true\"\n  creationTimestamp: \"2025-09-25T03:10:26Z\"\n  labels:\n    beta.kubernetes.io/arch: amd64\n    beta.kubernetes.io/os: linux\n    kubernetes.io/arch: amd64\n    kubernetes.io/hostname: node2\n    kubernetes.io/os: linux\n  name: node2\n  resourceVersion: \"46365464\"\n  uid: 3ba54e76-a605-43f6-85aa-5587fa987ec5\nspec: {}\nstatus:\n  addresses:\n  - address: 10.2.0.50\n    type: InternalIP\n  - address: node2\n    type: Hostname\n  allocatable:\n    cpu: \"12\"\n    ephemeral-storage: \"187795058378\"\n    hugepages-1Gi: \"0\"\n    hugepages-2Mi: \"0\"\n    memory: 32758084Ki\n    pods: \"110\"\n  capacity:\n    cpu: \"12\"\n    ephemeral-storage: 203770680Ki\n    hugepages-1Gi: \"0\"\n    hugepages-2Mi: \"0\"\n    memory: 32860484Ki\n    pods: \"110\"\n  conditions:\n  - lastHeartbeatTime: \"2026-04-17T07:03:52Z\"\n    lastTransitionTime: \"2026-04-17T07:03:52Z\"\n    message: Calico is running on this node\n    reason: CalicoIsUp\n    status: \"False\"\n    type: NetworkUnavailable\n  - lastHeartbeatTime: \"2026-04-22T03:22:52Z\"\n    lastTransitionTime: \"2026-04-16T02:25:06Z\"\n    message: kubelet has sufficient memory available\n    reason: KubeletHasSufficientMemory\n    status: \"False\"\n    type: MemoryPressure\n  - lastHeartbeatTime: \"2026-04-22T03:22:52Z\"\n    lastTransitionTime: \"2026-04-16T02:25:06Z\"\n    message: kubelet has no disk pressure\n    reason: KubeletHasNoDiskPressure\n    status: \"False\"\n    type: DiskPressure\n  - lastHeartbeatTime: \"2026-04-22T03:22:52Z\"\n    lastTransitionTime: \"2026-04-16T02:25:06Z\"\n    message: kubelet has sufficient PID available\n    reason: KubeletHasSufficientPID\n    status: \"False\"\n    type: PIDPressure\n  - lastHeartbeatTime: \"2026-04-22T03:22:52Z\"\n    lastTransitionTime: \"2026-04-16T02:25:06Z\"\n    message: kubelet is posting ready status. AppArmor enabled\n    reason: KubeletReady\n    status: \"True\"\n    type: Ready\n  daemonEndpoints:\n    kubeletEndpoint:\n      Port: 10250\n  images:\n  - names:\n    - quay.io/kata-containers/kata-deploy@sha256:12b7129cf708e60f881664053b8c5e6a8ffffffd638a5498b11d4091a355af5d\n    - quay.io/kata-containers/kata-deploy:3.20.0\n    sizeBytes: 2440671032\n  - names:\n    - docker.io/langgenius/dify-api:1.10.0\n    - docker.io/langgenius/dify-api:1.8.1\n    sizeBytes: 2290755700\n  - names:\n    - docker.io/langgenius/dify-plugin-daemon:0.2.0-local\n    - docker.io/langgenius/dify-plugin-daemon:0.4.1-local\n    sizeBytes: 1394443042\n  - names:\n    - docker.io/robustadev/holmes:0.16.4\n    sizeBytes: 1335272477\n  - names:\n    - docker.io/grafana/grafana:12.0.2\n    sizeBytes: 688745027\n  - names:\n    - docker.elastic.co/elasticsearch/elasticsearch@sha256:d784066422aec9f66ae424f692d2416057e78853ab015915a04530570c955cc8\n    - xnet.registry.io:8443/observability/elasticsearch/elasticsearch@sha256:82560db72e740db62d5c172b7aee8837887f6e22b7f6dc022ab11028906c29b8\n    - docker.elastic.co/elasticsearch/elasticsearch:8.5.1\n    - xnet.registry.io:8443/observability/elasticsearch/elasticsearch:8.5.1\n    sizeBytes: 683984297\n  - names:\n    - docker.io/nicolaka/netshoot:latest\n    sizeBytes: 623426857\n  - names:\n    - docker.io/langgenius/dify-sandbox:0.2.12\n    sizeBytes: 595364037\n  - names:\n    - docker.io/langgenius/dify-web:1.10.0\n    - docker.io/langgenius/dify-web:1.8.1\n    sizeBytes: 553399702\n  - names:\n    - docker.io/grafana/otel-lgtm:latest\n    sizeBytes: 543723157\n  - names:\n    - docker.io/langfuse/langfuse-worker:3.108.0\n    sizeBytes: 469884506\n  - names:\n    - quay.io/kata-containers/kata-deploy@sha256:ad8bca85e866b903cd69fc78ae10494fb8c593cb844b8bb33185d2ab63c86581\n    - quay.io/kata-containers/kata-deploy:3.1.3\n    sizeBytes: 407037304\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:b03ff0f770797cc7b18f3384abedaeef822d2c661b4e1154686c51bddc8b0c72\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:5.9.15\n    sizeBytes: 336928700\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:c52ba16e6746c006fa6de7efaeb6cbf2ee61e761cf72ced795257f0da180a7c2\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:4.9.5\n    sizeBytes: 336924863\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:8a2242794c2eed2759024fc0e58107c5b4a690e94e350e26da9dfbda6a412c7e\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:4.9.6\n    sizeBytes: 336924857\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:400dc44642cd0e9ddf3ce17fe65da6f37c42718594dc3055fe808a74379b1cef\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:5.9.12\n    sizeBytes: 336924281\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:c0c28b3613c4527d499eca5df4d6aa741d210297c0b15b4db146054a1ad9f869\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:6.0.1\n    sizeBytes: 336921279\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:d16bd8919985d581697329670345ef5b2b924db9a8b3c96770691c92ab45c1f3\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:5.9.11\n    sizeBytes: 336921226\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:4b3fa4378d36ce9db5ee9e9099e387b3e2ca897fde486346055152e9a2aeccf7\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:5.9.10\n    sizeBytes: 336921217\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:ac577c1597c5f5175b5afbfdec33c1a21040599aaf68d03df497ee3cc8981ea6\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:5.9.16\n    sizeBytes: 336920957\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:85c17416f98d7291dd4061508894d6246aa5a2cedd4b4f5a23480bb4554ddb44\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:6.0.0\n    sizeBytes: 336920921\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:6e8cda7851de4dea8774661611948406089590584b59c252b8ef8e03961722ce\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:5.9.14\n    sizeBytes: 336920083\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:9173752d6ea11fbdad82c55bd703f597882e65b30a05e903a3ade158c62afddb\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:5.9.13\n    sizeBytes: 336919615\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:355509ad826468d865c9c48b10005839b5e7697995b8ab35ddb92c563917f043\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:5.8.10\n    sizeBytes: 336918891\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:82b2ca98aae1e055d2bd993190544caafd0ce827c41bb6eae601d74cf2c26669\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:5.8.9\n    sizeBytes: 336918812\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:96ee95221e56819b3e36cf6b0eb21b8f2201a59dd5946b185655f77a221e9778\n    sizeBytes: 336918808\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:a611760978aaecc607a675dac978cece8059e044a8cd579b13d7ace7911b2936\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:5.6.6\n    sizeBytes: 336918599\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:8f49a28dd14ffd27558ce41a4671e7f209229e6d7e96d475473bd3a84a6cf86a\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:5.8.8\n    sizeBytes: 336918589\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:fca9f5020763f5191e88abfdea92aa88ad642c30a30c90be14400b8506b5b84b\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:5.5.5\n    sizeBytes: 336918490\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:16a11fa26f8d28c5542b4fa340eecf96b498830586e60a354072c6cf4c51d9aa\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:5.4.5\n    sizeBytes: 336917949\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:b8134e444d8e415bc83fa7117acbada55b6efc398cbe854c33045aa72e6d3958\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:5.8.7\n    sizeBytes: 336917690\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:575064360aa1fc064a76901e9f4a2d07d1176f0350cafa1d67ac769450dc255c\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:4.8.5\n    sizeBytes: 336917608\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:564b75941342c1760c9971015abb93605fdca25b903b99ebca30ea9561d36565\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:4.8.6\n    sizeBytes: 336917604\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:2b90316efda9e06e9b2905381584698d08920e1674c408facace8ca470fc28fc\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:5.3.5\n    sizeBytes: 336916542\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:f317bd7d063de109dcebb94d697aada93c318eaba0e53006592ae23cbdc443d0\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:5.2.5\n    sizeBytes: 336916476\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:39e3ba01cf13d58ed3144b01015e69e91206930a8a30ce915225771aa37ae6b3\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:5.7.6\n    sizeBytes: 336916301\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:3dc976febbc2589b4f8f699c1b9d35e719e8fbde1c1bf866f8cd6ed66434333e\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:4.7.5\n    sizeBytes: 336915987\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:f1a29367e52ebeb1b469fbe1fa9f20fc693c766a4dfda214a5a78b3ef824f27b\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:5.7.7\n    sizeBytes: 336915707\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:f843d7d95fd12ad533d8627da9b1013ee82147392a912e01da9f46038ecc9dd3\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:5.1.5\n    sizeBytes: 336915064\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:27de34e00bc01f3b72fe23ad8586ca122f48c60ac877dcfa71c9b111dfa53b2d\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:5.0.5\n    sizeBytes: 336914578\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:13670bc3f535a4266faab24a608fea1dce24364d5ff1bb66399f64a52ca283ca\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:6.0.16\n    sizeBytes: 336870255\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:44c926bf38e555b024d7f24babfca76a2b4b1ed791bd6a56e915070a0dd56373\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:6.0.15\n    sizeBytes: 336869657\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:ebce7045b44cd8e8f4187f2f18d7fdba804eceaa8401776ebc49a5f946268e76\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:6.0.13\n    sizeBytes: 336868481\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:91faabe1e1fcbdb8b721f6e912816c761c1e1df021b3c12487ef3a21f1342eae\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:6.0.12\n    sizeBytes: 336839325\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:5be3fedf5e5c8baca5a497a9a0a368797d3096c6df93615bfe5dc1bca43d4dc5\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:6.0.11\n    sizeBytes: 336836368\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:b39cd0c3abe5c934ab457608b4cb756764929e32dff4e17edbc96f24c490a575\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:6.0.10\n    sizeBytes: 336831669\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:fb7e1f0f9719feebceac95af408b80f3f96f8b3aa6294b34fa958d1a651b6268\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:6.0.8\n    sizeBytes: 336828335\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:a8d0f1b0df004f6db9d19da3ae1c560a4984c8f0f5bb1d103dedcd9b9fae2cf9\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:6.0.9\n    sizeBytes: 336828110\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:ccd962645b8e331a5a8cab43d7054864f4ee938e6d3636d2fbc342fdb6cb6831\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:6.0.2\n    sizeBytes: 336815859\n  - names:\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot@sha256:9916386bba7f4107d6d46a25f67bd4f98d558ce61e140242d81b9627f8bc9b2f\n    - xnet.registry.io:8443/xnet-cloud/aiops-copilot:6.0.5\n    sizeBytes: 336806466\n  nodeInfo:\n    architecture: amd64\n    bootID: 0ea98079-ad10-4a20-85f5-19b34afd257e\n    containerRuntimeVersion: containerd://1.6.32\n    kernelVersion: 5.15.0-174-generic\n    kubeProxyVersion: v1.26.8\n    kubeletVersion: v1.26.8\n    machineID: 6bb27862c82149418d0f5624411d0b22\n    operatingSystem: linux\n    osImage: Ubuntu 22.04.4 LTS\n    systemUUID: 0f5af30a-d385-493c-bc8b-5442fd024eee", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_namespace", "data": "NAME                                       READY   STATUS    RESTARTS         AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\ncalico-kube-controllers-6c67f9d475-2xcb7   1/1     Running   4 (4d20h ago)    27d    172.16.166.133   node1    <none>           <none>            k8s-app=calico-kube-controllers,pod-template-hash=6c67f9d475\ncalico-node-4kp26                          1/1     Running   12 (4d20h ago)   183d   10.2.0.48        master   <none>           <none>            controller-revision-hash=65f554db6,k8s-app=calico-node,pod-template-generation=1\ncalico-node-d2dhp                          1/1     Running   13 (4d20h ago)   183d   10.2.0.50        node2    <none>           <none>            controller-revision-hash=65f554db6,k8s-app=calico-node,pod-template-generation=1\ncalico-node-mnrjs                          1/1     Running   12 (4d20h ago)   183d   10.2.0.49        node1    <none>           <none>            controller-revision-hash=65f554db6,k8s-app=calico-node,pod-template-generation=1\ncoredns-777df594b8-j4857                   1/1     Running   4 (4d20h ago)    27d    172.16.166.129   node1    <none>           <none>            k8s-app=kube-dns,pod-template-hash=777df594b8\ncoredns-777df594b8-s8r4n                   1/1     Running   4 (4d20h ago)    27d    172.16.166.185   node1    <none>           <none>            k8s-app=kube-dns,pod-template-hash=777df594b8\netcd-master                                1/1     Running   13 (4d20h ago)   209d   10.2.0.48        master   <none>           <none>            component=etcd,tier=control-plane\nkube-apiserver-master                      1/1     Running   13 (4d20h ago)   209d   10.2.0.48        master   <none>           <none>            component=kube-apiserver,tier=control-plane\nkube-controller-manager-master             1/1     Running   36 (4d20h ago)   209d   10.2.0.48        master   <none>           <none>            component=kube-controller-manager,tier=control-plane\nkube-multus-ds-rnvbg                       1/1     Running   12 (4d20h ago)   183d   10.2.0.49        node1    <none>           <none>            app=multus,controller-revision-hash=6d4c8546fc,name=multus,pod-template-generation=1,tier=node\nkube-multus-ds-sc2jn                       1/1     Running   4 (4d20h ago)    85d    10.2.0.48        master   <none>           <none>            app=multus,controller-revision-hash=6d4c8546fc,name=multus,pod-template-generation=1,tier=node\nkube-multus-ds-x7h9s                       1/1     Running   13 (4d20h ago)   183d   10.2.0.50        node2    <none>           <none>            app=multus,controller-revision-hash=6d4c8546fc,name=multus,pod-template-generation=1,tier=node\nkube-proxy-69zzr                           1/1     Running   4 (4d20h ago)    27d    10.2.0.50        node2    <none>           <none>            controller-revision-hash=7d99996759,k8s-app=kube-proxy,pod-template-generation=1\nkube-proxy-bblvc                           1/1     Running   4 (4d20h ago)    27d    10.2.0.49        node1    <none>           <none>            controller-revision-hash=7d99996759,k8s-app=kube-proxy,pod-template-generation=1\nkube-proxy-wbh4k                           1/1     Running   4 (4d20h ago)    26d    10.2.0.48        master   <none>           <none>            controller-revision-hash=7d99996759,k8s-app=kube-proxy,pod-template-generation=1\nkube-scheduler-master                      1/1     Running   38 (4d20h ago)   209d   10.2.0.48        master   <none>           <none>            component=kube-scheduler,tier=control-plane", "duration_s": 0}, {"tool": "kubectl_run_image", "data": "{\"success\": false, \"stdout\": \"pod \\\"network-test-debug\\\" deleted\\nTesting TCP connectivity to port 443...\\nTesting HTTP connectivity...\\nHTTP test failed\\nTesting connectivity to other external sites...\\n\", \"stderr\": \"error: timed out waiting for the condition\\n/bin/bash: line 1: nslookup: command not found\\n/bin/bash: line 1: nc: command not found\\n/bin/bash: line 1: wget: command not found\\n/bin/bash: line 1: nslookup: command not found\\n/bin/bash: line 1: nc: command not found\\n\", \"returncode\": 127}", "duration_s": 0}, {"tool": "kubectl_run_image", "data": "{\"success\": false, \"stdout\": \"pod \\\"network-test-debug2\\\" deleted\\nTesting TCP connectivity to port 443...\\nTesting HTTP connectivity...\\nCurl test failed\\nTesting connectivity to other external sites...\\n\", \"stderr\": \"error: timed out waiting for the condition\\n/bin/bash: line 1: dig: command not found\\n/bin/bash: line 1: nc: command not found\\n  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current\\n                                 Dload  Upload   Total   Spent    Left  Speed\\n\\n  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0\\n  0     0    0     0    0     0      0      0 --:--:--  0:00:01 --:--:--     0\\n  0     0    0     0    0     0      0      0 --:--:--  0:00:02 --:--:--     0\\n  0     0    0     0    0     0      0      0 --:--:--  0:00:03 --:--:--     0\\n  0     0    0     0    0     0      0      0 --:--:--  0:00:04 --:--:--     0\\n  0     0    0     0    0     0      0      0 --:--:--  0:00:05 --:--:--     0\\ncurl: (28) Connection timed out after 5002 milliseconds\\n/bin/bash: line 1: dig: command not found\\n/bin/bash: line 1: nc: command not found\\n\", \"returncode\": 127}", "duration_s": 0}, {"tool": "tcp_check", "data": "{\"ok\": false, \"error\": \"[Errno 101] Network is unreachable\"}", "duration_s": 0}, {"tool": "kubernetes_tabular_query", "data": "NAMESPACE     NAME                                                STATUS    NODE     CONTAINERS\naiops-e2e     dns-test-temp                                       Pending   node2    ContainerCreating\naiops-e2e     imagepull-fail-victim                               Pending   node2    ImagePullBackOff\naiops-e2e     network-test                                        Pending   node2    ImagePullBackOff\naiops-e2e     network-test-curl                                   Pending   node2    ContainerCreating\naiops-e2e     ping-test                                           Pending   node2    ImagePullBackOff\naiops-e2e     simple-ping-test                                    Pending   node2    ContainerCreating\naiops-e2e     simple-test                                         Pending   node2    ImagePullBackOff", "duration_s": 0}], "llm_analysis": "## 第六步：检查集群中其他节点是否也存在镜像拉取问题", "collection_summary": "计划 8 项，实际采集 7 项，未采集 1 项，完整度 88%", "evidence_inventory": [{"id": "e1", "description": "获取所有异常Pod的详细YAML配置，确认镜像拉取策略和镜像仓库地址", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e2", "description": "获取node2节点的详细配置，检查节点标签、污点和网络配置", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e3", "description": "检查kube-system命名空间的CoreDNS配置和运行状态", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e4", "description": "检查kube-system命名空间的网络插件Calico状态", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e5", "description": "测试从node2节点到registry-1.docker.io的网络连通性", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e6", "description": "检查集群中其他节点是否也存在镜像拉取问题", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e7", "description": "检查集群的镜像拉取密钥配置", "level": "optional", "collected": false, "source": "planned"}, {"id": "extra_5", "description": "工具采集: tcp_check", "level": "important", "collected": true, "source": "thinking_extra"}], "missing_reasons": ["e7(检查集群的镜像拉取密钥配置): 已规划但工具执行失败或无匹配结果"], "early_stop": {"triggered": true, "reason": "critical 和 important 级证据均已满足，提前停止后续采集", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 7/8 项, 完整度: 88%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 12.2s)
   📤 → 下游数据: root_cause=
   confidence=95%
   causal_chain={"root_cause": "node2节点（IP: 10.2.0.50）的主机网络层存在故障，导致其无法访问外部网络，特别是无法连接到公共Docker镜像仓库 registry-1.docker.io。", "propagation": "节点网络故障 → 节点上的kubelet无法通过容器运行时拉取所需镜像 → 容器运行时拉取镜像失败并返回网络错误 → kubelet报告ImagePullBackOff → Pod状态保持Pending。", "direct_cause": "node2节点到registry-1.docker.io:443的网络连接不可达（Network is unreachable），导致所有需要从该仓库拉取镜像的Pod无法启动。", "manifestation": "aiops-e2e命名空间中调度到node2节点的多个Pod状态为Pending，容器状态为ImagePullBackOff，事件日志显示镜像拉取失败并伴有网络连接错误。"}
   rca_analysis={"phenomenon": "aiops-e2e 命名空间下多个 Pod 状态为 Pending，容器处于 ImagePullBackOff 状态，无法启动。", "evidence_inventory": [{"id": "e1", "content": "异常Pod详情：aiops-e2e命名空间下 imagepull-fail-victim, network-test, simple-test 等Pod状态为Pending，容器状态为ImagePullBackOff。事件显示拉取busybox和nginx:latest镜像失败，错误为connection reset by peer和i/o timeout，目标地址registry-1.docker.io。", "source": "kubectl_describe (Pod详情)", "reliability": "高"}, {"id": "e2", "content": "节点状态：node2节点状态Ready，无资源压力（MemoryPressure/DiskPressure/PIDPressure均为False），CPU/内存资源充足。节点上存在多个Pending状态的Pod。", "source": "kubectl_describe (Node详情)", "reliability": "高"}, {"id": "e3", "content": "Pod配置：异常Pod imagepull-fail-victim的YAML显示镜像为nginx:latest，镜像拉取策略为Always，调度到node2节点。", "source": "kubectl_get_yaml (Pod配置)", "reliability": "高"}, {"id": "e4", "content": "节点配置：node2节点YAML显示网络配置正常（Calico IP 10.2.0.50/19），节点上已存在大量来自其他仓库（如xnet.registry.io）的镜像，但无来自registry-1.docker.io的busybox或nginx镜像。", "source": "kubectl_get_yaml (Node配置)", "reliability": "高"}, {"id": "e5", "content": "核心组件状态：kube-system命名空间下CoreDNS (coredns-777df594b8-j4857, coredns-777df594b8-s8r4n) 和 Calico (calico-node-d2dhp) Pod 状态均为Running。", "source": "kubectl_get_by_kind_in_namespace (kube-system Pod)", "reliability": "高"}, {"id": "e6", "content": "网络连通性测试（从Pod测试）：在node2上创建调试Pod测试到registry-1.docker.io:443的连通性失败，curl测试超时（Connection timed out after 5002 milliseconds）。", "source": "kubectl_run_image (网络测试1)", "reliability": "中"}, {"id": "e7", "content": "网络连通性测试（从节点测试）：从node2节点直接进行TCP检查到registry-1.docker.io:443失败，错误为[Errno 101] Network is unreachable。", "source": "tcp_check (工具采集)", "reliability": "高"}, {"id": "e8", "content": "问题范围：所有异常Pod（共7个，包括imagepull-fail-victim, network-test等）均集中在node2节点上，状态为Pending或ImagePullBackOff。", "source": "kubernetes_tabular_query (异常Pod列表)", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Pod事件：多次尝试拉取busybox/nginx:latest镜像失败，错误包括'connection reset by peer'和'i/o timeout'，目标地址registry-1.docker.io。", "interpretation": "这表明Pod容器启动失败的直接原因是无法从公共Docker Hub拉取镜像，且网络连接出现严重问题（重置或超时）。"}, {"evidence_id": "e2", "raw_data": "节点node2状态：Ready, MemoryPressure=False, DiskPressure=False, PIDPressure=False, CPU请求/限制占比8%/34%，内存请求/限制占比5%/17%。", "interpretation": "node2节点本身健康，资源充足，排除了节点资源不足导致Pod Pending的可能性。"}, {"evidence_id": "e3", "raw_data": "Pod spec: nodeName: node2, image: nginx:latest, imagePullPolicy: Always。", "interpretation": "Pod明确调度到node2，且配置为总是拉取镜像，因此每次启动都会尝试从仓库拉取。"}, {"evidence_id": "e4", "raw_data": "node2 images列表：包含大量来自xnet.registry.io:8443和quay.io的镜像，但未列出busybox或nginx:latest。", "interpretation": "node2本地镜像缓存中没有所需的公共镜像，且节点有能力从其他私有仓库拉取镜像，说明容器运行时基本功能正常。"}, {"evidence_id": "e5", "raw_data": "coredns Pods: coredns-777df594b8-j4857 (Running, node1), coredns-777df594b8-s8r4n (Running, node1)。calico-node-d2dhp (Running, node2)。", "interpretation": "集群DNS服务（CoreDNS）运行正常（在node1上），且node2上的Calico网络插件也运行正常，表明集群内部网络和DNS解析基础服务正常。"}, {"evidence_id": "e6", "raw_data": "网络测试输出：'curl: (28) Connection timed out after 5002 milliseconds'。", "interpretation": "在node2上的Pod内尝试访问registry-1.docker.io的HTTP连接超时，证实了从该节点容器网络到外部仓库的网络连通性故障。"}, {"evidence_id": "e7", "raw_data": "TCP检查结果：{'ok': false, 'error': '[Errno 101] Network is unreachable'}", "interpretation": "从node2节点主机层面直接测试到registry-1.docker.io:443的TCP连接失败，错误为'网络不可达'。这是非常明确的网络层故障证据，表明问题出在节点主机网络层面，而非容器网络或K8s配置。"}, {"evidence_id": "e8", "raw_data": "异常Pod列表：所有7个异常Pod的NODE列均为node2。", "interpretation": "镜像拉取失败的问题完全局限于node2节点，其他节点（master, node1）未出现同类问题，说明这是node2节点的特定故障。"}], "causal_chain": {"root_cause": "node2节点（IP: 10.2.0.50）的主机网络层存在故障，导致其无法访问外部网络，特别是无法连接到公共Docker镜像仓库 registry-1.docker.io。", "propagation": "节点网络故障 → 节点上的kubelet无法通过容器运行时拉取所需镜像 → 容器运行时拉取镜像失败并返回网络错误 → kubelet报告ImagePullBackOff → Pod状态保持Pending。", "direct_cause": "node2节点到registry-1.docker.io:443的网络连接不可达（Network is unreachable），导致所有需要从该仓库拉取镜像的Pod无法启动。", "manifestation": "aiops-e2e命名空间中调度到node2节点的多个Pod状态为Pending，容器状态为ImagePullBackOff，事件日志显示镜像拉取失败并伴有网络连接错误。"}, "root_cause_summary": "根本原因是 node2 节点（10.2.0.50）的主机网络层故障，导致其无法访问外部互联网上的 Docker Hub（registry-1.docker.io）。关键证据包括：1) 从 node2 节点直接进行 TCP 检查到 registry-1.docker.io:443 返回 '[Errno 101] Network is unreachable'（证据 e7）；2) 在 node2 上创建的调试 Pod 内进行 curl 测试连接超时（证据 e6）；3) 所有镜像拉取失败的 Pod 均集中在 node2 节点上，而其他节点正常（证据 e8）；4) node2 节点本身状态 Ready 且资源充足，核心网络插件 Calico 运行正常（证据 e2, e5），排除了 K8s 内部网络和资源问题。因此，问题是 node2 节点主机级别的外部网络连通性中断。", "confidence": 0.95, "primary_runbooks": ["私有化 Kubernetes 环境健康与高效排查参考手册", "L3 镜像拉取失败 (ImagePullBackOff)"], "alternative_causes": ["集群DNS解析故障：但CoreDNS运行正常（证据e5），且错误是网络层'不可达'而非解析失败。", "节点防火墙或网络策略阻断：可能性存在，但属于网络配置问题，归入主机网络故障范畴。", "镜像仓库认证问题：但Pod使用公共镜像，无需特殊密钥，且错误是网络连接失败而非认证失败。"], "limitations": "证据未包含node2节点的详细网络配置（如路由表、防火墙规则）、与其他外部地址的连通性测试对比、以及node1/master节点到同一仓库的连通性测试结果。这限制了进一步定位网络故障的具体环节（如网关、路由、出口防火墙）。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 95%
   🔗 因果链:
     根本原因: node2节点（IP: 10.2.0.50）的主机网络层存在故障，导致其无法访问外部网络，特别是无法连接到公共Docker镜像仓库 registry-1.docker.io。
     传导机制: 节点网络故障 → 节点上的kubelet无法通过容器运行时拉取所需镜像 → 容器运行时拉取镜像失败并返回网络错误 → kubelet报告ImagePullBackOff → Pod状态保持Pending。
     最终表现: aiops-e2e命名空间中调度到node2节点的多个Pod状态为Pending，容器状态为ImagePullBackOff，事件日志显示镜像拉取失败并伴有网络连接错误。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 31.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6531 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 13m 52.5s
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
| **问题层级** | L3 - 服务网络层 |
| **问题分类** | 镜像拉取失败 (ImagePullBackOff) |
| **置信度** | 高 (95%) |
| **证据完整度** | 7/8 (88%) |

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**集群状态总结**：
您的集群核心组件（节点、CoreDNS、Calico）运行正常，但存在**局部网络故障**。具体表现为：`aiops-e2e` 命名空间下调度到 `node2` 节点的多个 Pod 因无法从 Docker Hub 拉取镜像而卡在 `Pending` 状态。

**关键实体**：
| 类型 | 值 |
|------|-----|
| **异常 Pod** | `aiops-e2e/imagepull-fail-victim`, `aiops-e2e/network-test`, `aiops-e2e/simple-test` 等（共7个） |
| **所在命名空间** | `aiops-e2e` |
| **故障节点** | `node2` (IP: 10.2.0.50) |
| **目标镜像仓库** | `registry-1.docker.io` (Docker Hub) |
| **错误信息** | `connection reset by peer`, `i/o timeout`, `Network is unreachable` |

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态与事件 | `kubectl describe pod` | `Reason: ImagePullBackOff`，事件：`Failed to pull image "nginx:latest": rpc error: code = Unknown desc = failed to pull and unpack image "docker.io/library/nginx:latest": failed to resolve reference "docker.io/library/nginx:latest": failed to do request: Head "https://registry-1.docker.io/v2/library/nginx/manifests/latest": dial tcp: lookup registry-1.docker.io on 172.30.0.10:53: read udp 172.16.104.58:36312->172.30.0.10:53: i/o timeout` | Pod 因镜像拉取失败而处于 `Pending` 状态，错误指向网络超时。 |
| 2 | 节点状态 | `kubectl describe node node2` | `Conditions: Ready=True, MemoryPressure=False, DiskPressure=False, PIDPressure=False`，资源充足。 | `node2` 节点本身健康，无资源压力，排除了资源不足导致 Pod Pending 的可能。 |
| 3 | Pod 配置 | `kubectl get -o yaml pod imagepull-fail-victim` | `spec.nodeName: node2`, `spec.containers[0].image: nginx:latest`, `imagePullPolicy: Always` | Pod 被调度到 `node2`，且配置为总是拉取最新镜像。 |
| 4 | 节点镜像列表 | `kubectl get -o yaml node node2` | `status.images` 列表包含大量来自 `xnet.registry.io:8443` 和 `quay.io` 的镜像，但**没有** `busybox` 或 `nginx:latest`。 | `node2` 本地无所需公共镜像，但能拉取其他私有仓库镜像，说明容器运行时基本功能正常。 |
| 5 | 核心组件状态 | `kubectl get pods -n kube-system` | `coredns-777df594b8-j4857 (Running, node1)`, `coredns-777df594b8-s8r4n (Running, node1)`, `calico-node-d2dhp (Running, node2)` | 集群 DNS (CoreDNS) 和网络插件 (Calico) 均运行正常，表明集群内部网络基础服务正常。 |
| 6 | 容器内网络测试 | `kubectl run` 调试 Pod | `stdout: Curl test failed`, `stderr: curl: (28) Connection timed out after 5002 milliseconds` | 在 `node2` 上创建的 Pod 内部，访问 `registry-1.docker.io` 的 HTTP 连接超时。 |
| 7 | 节点主机网络测试 | `tcp_check` 工具 | `{"ok": false, "error": "[Errno 101] Network is unreachable"}` | **关键证据**：从 `node2` 节点主机层面直接测试到 `registry-1.docker.io:443` 的 TCP 连接失败，错误为“网络不可达”。 |
| 8 | 问题范围 | `kubectl get pods -A -o custom-columns=...` | 所有 7 个异常 Pod 的 `NODE` 列均为 `node2`。 | 镜像拉取失败的问题**完全局限于 `node2` 节点**，其他节点 (`master`, `node1`) 上的 Pod 运行正常。 |

### 证据关联分析
- **证据 #7 + #6 + #1 印证**：节点主机网络不可达 (`Network is unreachable`) → 容器内网络连接超时 (`Connection timed out`) → Pod 事件报网络超时 (`i/o timeout`) 和连接重置 (`connection reset by peer`)。
- **证据 #8 + #2 印证**：问题仅出现在 `node2` 节点，且该节点资源充足 → 问题具有节点特异性，非集群级故障。
- **证据 #4 + #5 印证**：`node2` 能拉取私有仓库镜像且 Calico 运行正常 → 容器运行时和集群覆盖网络正常，问题出在节点主机的**外部网络出口**。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| e7: 检查集群的镜像拉取密钥配置 | optional | 不影响根本结论。因使用的是公共镜像 (`nginx:latest`, `busybox`)，无需认证，且错误是网络层故障而非认证失败。 |

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ node2 节点（10.2.0.50）的主机网络层故障，导致其无法访问外部互联网 │
│ 特别是无法连接到公共 Docker 镜像仓库 registry-1.docker.io       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 节点网络故障 → kubelet/容器运行时无法从外部仓库拉取镜像 →        │
│ 返回网络错误 (Network is unreachable, timeout)                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 所有调度到 node2 且需要从 Docker Hub 拉取镜像的 Pod，            │
│ 其容器启动时因镜像拉取失败而处于 ImagePullBackOff 状态          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ aiops-e2e 命名空间下多个 Pod 状态为 Pending，持续重启失败        │
│ 事件日志显示镜像拉取网络错误                                     │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #7 (TCP检查返回 `Network is unreachable`)、证据 #6 (容器内curl测试超时) 和证据 #8 (问题仅限 `node2` 节点)，问题的根本原因是 **`node2` 节点的主机网络层存在故障，导致其无法访问外部互联网上的 Docker Hub (`registry-1.docker.io`)**。

**置信度**：高 (95%)
- ✅ **证据 #7** 提供了节点主机层面网络不可达的直接证据。
- ✅ **证据 #8** 表明问题具有节点特异性，排除了集群级 DNS 或网络策略问题。
- ✅ **证据 #2, #4, #5** 排除了节点资源不足、容器运行时故障、集群内部网络故障等可能性。
- ⚠️ 未采集节点详细网络配置（路由、防火墙），但现有证据已足够定位到节点网络层。

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 检查并修复 node2 节点的网络配置**
登录到 `node2` 节点 (IP: 10.2.0.50)，执行以下检查：
```bash
# 1. 检查默认路由和网络接口
ip route show default
ip addr show

# 2. 测试到网关和外部地址的基础连通性
ping -c 4 10.2.0.1  # 假设网关地址，请根据实际情况调整
ping -c 4 8.8.8.8

# 3. 检查防火墙规则（如果使用 iptables）
sudo iptables -L -n -v | head -50
sudo iptables -t nat -L -n -v | head -50

# 4. 检查 DNS 解析（使用主机网络命名空间）
nslookup registry-1.docker.io
```
*依据*：证据 #7 表明节点主机网络层故障，需从主机层面排查。

**2. [可选] 临时将 Pod 调度到其他节点**
在修复 `node2` 网络前，可为受影响的 Deployment/DaemonSet 添加节点亲和性或反亲和性，避免调度到 `node2`。
```bash
# 示例：为 Deployment 添加 nodeSelector，使其仅调度到 node1
kubectl patch deployment <your-deployment> -n aiops-e2e -p '{"spec":{"template":{"spec":{"nodeSelector":{"kubernetes.io/hostname":"node1"}}}}}'
```
*目的*：快速恢复业务，但非根本解决。

### 后续优化
1.  **配置私有镜像仓库镜像**：在集群内部搭建或配置可访问的私有镜像仓库，将常用公共镜像缓存至内网，避免依赖不稳定的外网。
2.  **节点网络监控**：配置对节点网络连通性的监控告警，例如对关键外网地址的定时探测。
3.  **Pod 多可用区部署**：对于重要应用，使用 Pod 反亲和性将其分散到不同节点，避免单节点故障影响全部实例。

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 node2 外部网络恢复 | 在 `node2` 上执行：`curl -I --connect-timeout 5 https://registry-1.docker.io/v2/` | 返回 `HTTP/2 200` 或 `401` (表示网络通，但未认证) |
| 2. 观察异常 Pod 状态 | `kubectl get pods -n aiops-e2e` | `STATUS` 从 `Pending` 变为 `Running` 或 `Completed` |
| 3. 确认容器启动 | `kubectl logs <pod-name> -n aiops-e2e` | 能正常输出容器日志，无启动错误 |

## ⚠️ 注意事项
- 本诊断基于现有证据，**根本原因锁定在 `node2` 节点的主机网络**。具体是路由、防火墙、物理网卡还是云平台安全组问题，需登录节点进一步排查。
- 如果 `node2` 节点网络暂时无法修复，考虑将其标记为不可调度 (`cordon`)，并逐步迁移其上的工作负载。
```bash
kubectl cordon node2
```
- 检查 `node2` 节点上 `calico-node` Pod 的日志，虽然其状态为 `Running`，但有时能反映主机网络异常。
```bash
kubectl logs -n kube-system calico-node-d2dhp | tail -50
```

---

## 📊 性能统计

├─ 总耗时: 13.9m
├─ 问题定位: 135.2s (16%) ✅
├─ 证据链采集: 533.3s (64%) ✅
├─ 根因分析: 72.2s (9%) ✅
├─ 汇总总结: 91.7s (11%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 21 次
```

📋 诊断追踪

- **核心 Runbook**: private-k8s-health-reference, l3-imagepull-failed
- **参考 Runbook**: private-k8s-health-reference, l3-imagepull-failed
- **工具调用**: 21 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
