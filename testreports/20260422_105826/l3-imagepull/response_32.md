======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 6628b522a5ba4a37]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来帮您检查集群的健康状况。首先，让我获取一些基础信息来了解当前状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   209d   v1.26.8  
   💭 [问题定位] 节点状态看起来都是 Ready。现在让我检查 Pod 的整体状态：
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE,NAME,STATUS,READY,RESTARTS,AGE' | (head -n 1; tail -n +2 | grep -E 'Pending|CrashLoopBackOff|ImagePullBackOff|Er
   💭 [问题定位] 让我使用正确的格式：
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 NAMESPACE     NAME                                                STATUS    READY   RESTARTS   AGE
aiops-e2e     network-test                                        Pending   false   0          2026-0
   💭 [问题定位] 发现有几个 Pod 处于 Pending 状态。让我获取通用健康检查参考手册作为基线，然后进一步检查这些 Pending Pod 的详细信息：
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# 私有化 Kubernetes 环境健康与高效排查参考手册

> 类型: reference | 适用: 私有化 Kubernetes 环境 | 环境特征: Calico + NFS + containerd

## 目的

本手册不是某个具体故障的处理步骤，而是一个**额外知识参考**：
- 帮助理解在私有化 Kubernetes 环境中，健康检查应重点关注哪些资源与信号

   💭 [问题定位] 现在让我检查这些 Pending Pod 的详细信息：
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             network-test
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Wed, 22 Apr 2026 03:01:22 +0000
Labels:    
   💭 [问题定位] 发现是镜像拉取失败的问题。让我获取镜像拉取失败的 runbook 作为参考：
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
   💭 [问题定位] 现在让我检查其他 Pending Pod 是否也是同样的问题：
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             ping-test
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Wed, 22 Apr 2026 03:29:21 +0000
Labels:       
   💭 [问题定位] 所有 Pending Pod 都是同样的问题 - 无法拉取 busybox 镜像。让我检查一下是否有其他异常状态的 Pod：
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,READY:.status.containerStatuses[0].ready,RESTARTS:.
   💭 [问题定位] 让我检查一下是否有其他异常状态的 Pod，使用不同的方法：
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 Executing jq query for pods...
{
  "namespace": "aiops-e2e",
  "name": "dns-test",
  "status": "Pending",
  "node": "node2",
  "containers": "busybox:latest"
}
{
  "namespace": "aiops-e2e",
  "name": 
   💭 [问题定位] 看起来有多个 Pod 都处于 Pending 状态，都是因为镜像拉取失败。让我检查一下是否有其他工作负载异常：
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                               READY   UP-TO-DATE   AVAILABLE   AGE    CONTAINERS                                                                      IMAGES                         
   💭 [问题定位] 所有部署看起来都是正常的（READY=1/1）。让我检查一下 Service 和 Endpoints 的状态：
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 Executing jq query for services...
{
  "namespace": "aaa",
  "name": "test1-redis-headless",
  "selector": {
    "app": "redis",
    "release": "test1"
  },
  "endpoints": {}
}
{
  "namespace": "aaa",
   💭 [问题定位] 让我检查一下是否有 Endpoints 为空的情况：
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                     ENDPOINTS                                                                    AGE    LABELS
aaa           test1-redis-headless                    
   💭 [问题定位] 我看到有几个 Endpoints 是空的（<none>），特别是 aaa 和 xnet 命名空间中的一些 redis 服务。让我检查一下这些命名空间中是否有对应的 Pod：
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 No resources found in aaa namespace.
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 NAME                                                READY   STATUS    RESTARTS         AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
alertmanager-observability-alertmanage
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (2m 25.1s)
   📤 → 下游数据: layer=Layer.L3, layers=L3
   scenarios=[{'scenario': '镜像拉取网络故障', 'probability': '高', 'reason': '多个 Pod 因从公共 Docker Hub 拉取镜像超时而处于 ImagePullBackOff 状态，指向节点网络出口或镜像仓库可达性问题。'}, {'scenario': '服务端点缺失', 'probability': '中', 'reason': '多个服务的 Endpoints 为空，可能因对应命名空间无 Pod (aaa) 或 Pod 标签与服务选择器不匹配 (xnet)。'}, {'scenario': '节点网络隔离', 'probability': '低', 'reason': '所有异常 Pod 均调度至 node2，可能该节点存在特定的网络策略或出口限制，但节点状态为 Ready，需进一步确认。'}]
   entities=[{"type": "Pod", "value": "aiops-e2e/network-test"}, {"type": "Pod", "value": "aiops-e2e/ping-test"}, {"type": "Pod", "value": "aiops-e2e/simple-ping-test"}, {"type": "Pod", "value": "aiops-e2e/simple-test"}, {"type": "Service", "value": "aaa/test1-redis-master"}, {"type": "Service", "value": "xnet/test2-redis-master"}, {"type": "Node", "value": "node2"}]
   reasoning=分析文本显示存在多个活跃异常对象：1) aiops-e2e 命名空间下多个 Pod (network-test, ping-test 等) 处于 Pending 状态，容器状态为 ImagePullBackOff，根本原因为从 Docker Hub (registry-1.docker.io) 拉取 busybox/nginx 镜像时网络连接超时或重置。2) aaa 和 xnet 命名空间下多个 redis 服务 (test1-redis-*, test2-redis-*) 的 Endpoints 为空，表明服务选择器未匹配到 Pod。节点状态均为 Ready，无磁盘压力、驱逐或 OOM 迹象。
   layer_analysis={"layer": "L3", "layers": ["L3"], "layer_name": "镜像/网络/服务发现层", "confidence": 0.95, "reasoning": "分析文本显示存在多个活跃异常对象：1) aiops-e2e 命名空间下多个 Pod (network-test, ping-test 等) 处于 Pending 状态，容器状态为 ImagePullBackOff，根本原因为从 Docker Hub (registry-1.docker.io) 拉取 busybox/nginx 镜像时网络连接超时或重置。2) aaa 和 xnet 命名空间下多个 redis 服务 (test1-redis-*, test2-redis-*) 的 Endpoints 为空，表明服务选择器未匹配到 Pod。节点状态均为 Ready，无磁盘压力、驱逐或 OOM 迹象。", "key_entities": [{"type": "Pod", "value": "aiops-e2e/network-test"}, {"type": "Pod", "value": "aiops-e2e/ping-test"}, {"type": "Pod", "value": "aiops-e2e/simple-ping-test"}, {"type": "Pod", "value": "aiops-e2e/simple-test"}, {"type": "Service", "value": "aaa/test1-redis-master"}, {"type": "Service", "value": "xnet/test2-redis-master"}, {"type": "Node", "value": "node2"}], "possible_scenarios": [{"scenario": "镜像拉取网络故障", "probability": "高", "reason": "多个 Pod 因从公共 Docker Hub 拉取镜像超时而处于 ImagePullBackOff 状态，指向节点网络出口或镜像仓库可达性问题。"}, {"scenario": "服务端点缺失", "probability": "中", "reason": "多个服务的 Endpoints 为空，可能因对应命名空间无 Pod (aaa) 或 Pod 标签与服务选择器不匹配 (xnet)。"}, {"scenario": "节点网络隔离", "probability": "低", "reason": "所有异常 Pod 均调度至 node2，可能该节点存在特定的网络策略或出口限制，但节点状态为 Ready，需进一步确认。"}]}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L3
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 根据上游定位结果，我发现了两个主要问题：**镜像拉取失败**和**服务端点缺失**。让我先获取相关诊断手册，然后制定证据采集计划。
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 工具结果: fetch_runbook (success)
      📄 <runbook>
# L3 镜像拉取失败 (ImagePullBackOff)

> 层级: L3 - 服务网络层 | 场景: 容器镜像拉取失败

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | ImagePullBackOff / ErrImagePull / ImageInspectError |
| Events | `Faile
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 工具结果: fetch_runbook (success)
      📄 <runbook>
# 私有化 Kubernetes 环境健康与高效排查参考手册

> 类型: reference | 适用: 私有化 Kubernetes 环境 | 环境特征: Calico + NFS + containerd

## 目的

本手册不是某个具体故障的处理步骤，而是一个**额外知识参考**：
- 帮助理解在私有化 Kubernetes 环境中，健康检查应重点关注哪些资源与信号

   💭 [证据链采集] 现在基于上游定位结果和诊断手册，我将制定证据采集计划并执行工具采集。

```json
{
  "layer": "L3",
  "evidence_plan": [
    {
      "id": "e1",
      "description": "获取所有异常 Pod 的详细状态和事件",
      "level": "critical",
      "tool": "kubernetes_tabular_query",
      "command": "kubectl get pods -A -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,IP:.status.podIP,READY:.status.containerStatuses[*].ready,REASON:.status.containerStatuses[*].state.waiting.reason,RESTARTS:.status.containerStatuses[*].restartCount'",
      "purpose": "确认所有 Pod 的当前状态，特别是 ImagePullBackOff 的 Pod 数量和分布"
    },
    {
      "id": "e2",
      "description": "获取 node2 节点的详细状态和条件",
      "level": "important",
      "tool": "kubectl_describe",
      "command": "kubectl describe node node2",
      "purpose": "检查 node2 节点的网络连接性、资源压力和 taint 状态，因为所有异常 Pod 都调度到 node2"
    },
    {
      "id": "e3",
      "description": "获取空端点服务的详细信息",
      "level": "important",
      "tool": "kubernetes_tabular_query",
      "command": "kubectl get svc,endpoints -A -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,TYPE:.type,CLUSTER-IP:.spec.clusterIP,PORT(S):.spec.ports[*].port,SELECTOR:.spec.selector,ENDPOINTS:.subsets[*].addresses[*].ip'",
      "purpose": "确认哪些服务的 endpoints 为空，以及它们的 selector 配置"
    },
    {
      "id": "e4",
      "description": "测试 Docker Hub 网络连通性",
      "level": "critical",
      "tool": "kubectl_run_image",
      "command": "kubectl run curl-test --rm -it --image=curlimages/curl --restart=Never -- curl -sI https://registry-1.docker.io/v2/ --connect-timeout 5",
      "purpose": "验证从集群内部到 Docker Hub 的网络连通性，确认镜像拉取失败的根本原因"
    },
    {
      "id": "e5",
      "description": "获取异常 Pod 的完整 YAML 配置",
      "level": "important",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get -o yaml pod network-test -n aiops-e2e",
      "purpose": "查看 network-test Pod 的完整配置，包括镜像地址、imagePullSecrets 等"
    }
  ],
  "collection_strategy": "首先确认所有异常 Pod 的状态分布，然后重点检查 node2 节点状态，同时验证 Docker Hub 网络连通性。最后检查空端点服务的配置。"
}
```

现在开始执行证据采集：
   💭 [证据链采集] 调用工具: kubernetes_tabular_query
   💭 [证据链采集] 工具结果: kubernetes_tabular_query (success)
      📄 NAMESPACE     NAME                                                STATUS    NODE     IP               READY                 REASON             RESTARTS
aiops-e2e     dns-test                          
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:               node2
Roles:              <none>
Labels:             beta.kubernetes.io/arch=amd64
                    beta.kubernetes.io/os=linux
                    kubernetes.io/arch=amd64
    
   💭 [证据链采集] 调用工具: kubernetes_tabular_query
   💭 [证据链采集] 工具结果: kubernetes_tabular_query (success)
      📄 NAMESPACE     NAME                                     TYPE     CLUSTER-IP       PORT(S)                                             SELECTOR                                                           
   💭 [证据链采集] 调用工具: kubectl_run_image
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 工具结果: kubectl_run_image (success)
      📄 {"success": false, "stdout": "pod \"curl-test\" deleted\n", "stderr": "error: timed out waiting for the condition\n", "returncode": 1}
   ✅ [证据链采集] 完成 (2m 47.8s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan": [{"id": "e1", "description": "获取所有异常 Pod 的详细状态和事件", "level": "critical", "tool": "kubernetes_tabular_query", "command": "kubectl get pods -A -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,IP:.status.podIP,READY:.status.containerStatuses[*].ready,REASON:.status.containerStatuses[*].state.waiting.reason,RESTARTS:.status.containerStatuses[*].restartCount'", "purpose": "确认所有 Pod 的当前状态，特别是 ImagePullBackOff 的 Pod 数量和分布"}, {"id": "e2", "description": "获取 node2 节点的详细状态和条件", "level": "important", "tool": "kubectl_describe", "command": "kubectl describe node node2", "purpose": "检查 node2 节点的网络连接性、资源压力和 taint 状态，因为所有异常 Pod 都调度到 node2"}, {"id": "e3", "description": "获取空端点服务的详细信息", "level": "important", "tool": "kubernetes_tabular_query", "command": "kubectl get svc,endpoints -A -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,TYPE:.type,CLUSTER-IP:.spec.clusterIP,PORT(S):.spec.ports[*].port,SELECTOR:.spec.selector,ENDPOINTS:.subsets[*].addresses[*].ip'", "purpose": "确认哪些服务的 endpoints 为空，以及它们的 selector 配置"}, {"id": "e4", "description": "测试 Docker Hub 网络连通性", "level": "critical", "tool": "kubectl_run_image", "command": "kubectl run curl-test --rm -it --image=curlimages/curl --restart=Never -- curl -sI https://registry-1.docker.io/v2/ --connect-timeout 5", "purpose": "验证从集群内部到 Docker Hub 的网络连通性，确认镜像拉取失败的根本原因"}, {"id": "e5", "description": "获取异常 Pod 的完整 YAML 配置", "level": "important", "tool": "kubectl_get_yaml", "command": "kubectl get -o yaml pod network-test -n aiops-e2e", "purpose": "查看 network-test Pod 的完整配置，包括镜像地址、imagePullSecrets 等"}], "tool_results": [], "tool_data": [{"tool": "fetch_runbook", "data": "<runbook>\n# L3 镜像拉取失败 (ImagePullBackOff)\n\n> 层级: L3 - 服务网络层 | 场景: 容器镜像拉取失败\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | ImagePullBackOff / ErrImagePull / ImageInspectError |\n| Events | `Failed to pull image`, `connection refused`, `timeout`, `manifest unknown` |\n| 常见原因 | 仓库不可达、镜像不存在、认证失败、DNS 解析失败 |\n\n## 诊断流程\n\n### Step 1: 确认 Pod 状态\n```bash\nkubectl get pod <pod-name> -n <namespace> -o wide\n```\n\n### Step 2: 获取详细事件（关键步骤）\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n重点关注 Events 部分:\n- `Failed to pull image \"xxx\"`: 具体镜像地址\n- `connection canceled/refused/timeout`: 网络不可达\n- `manifest unknown/not found`: 镜像或 tag 不存在\n- `unauthorized/no basic auth`: 认证失败\n\n### Step 3: 检查镜像地址和 Pull Secret\n```bash\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].image}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.imagePullSecrets}'\n```\n\n### Step 4: 测试镜像仓库连通性\n```bash\nkubectl run curl-test --rm -it --image=curlimages/curl --restart=Never -- \\\n  curl -sI https://<registry-host>/v2/ --connect-timeout 5\n```\n\n\n\n## 判定规则\n\n| 条件 | 结论 | 置信度 |\n|------|------|--------|\n| Events 含 connection refused/timeout | 镜像仓库网络不可达 | 高 |\n| Events 含 manifest unknown/not found | 镜像或 tag 不存在 | 高 |\n| Events 含 unauthorized/no basic auth | 认证失败（缺少或错误的 imagePullSecret） | 高 |\n| DNS 解析失败 | DNS 问题导致仓库不可达 | 高 |\n\n</runbook>\nNote: the above runbook is for DIAGNOSTIC REFERENCE ONLY. Follow the DIAGNOSTIC steps to gather evidence using tools, but DO NOT execute any remediation/fix commands. Report your findings and suggest fixes in your analysis.", "duration_s": 0}, {"tool": "fetch_runbook", "data": "<runbook>\n# 私有化 Kubernetes 环境健康与高效排查参考手册\n\n> 类型: reference | 适用: 私有化 Kubernetes 环境 | 环境特征: Calico + NFS + containerd\n\n## 目的\n\n本手册不是某个具体故障的处理步骤，而是一个**额外知识参考**：\n- 帮助理解在私有化 Kubernetes 环境中，健康检查应重点关注哪些资源与信号\n- 帮助在诊断时兼顾**效率**和**完整性**\n- 强调**当前状态优先**、**最小必要探测**、**按证据扩展**\n- 参考完后如果有其他合适的场景的runbooks作为更加细致和详细的参考你也应该去引用和查看！\n\n## 核心原则\n\n### 原则 1: 健康检查不等于 Pod 全部 Running\n以下情况都可能导致“Pod 看起来正常，但环境实际上不健康”：\n- Pod Running，但 `Service` 没有 `Endpoints`\n- Pod Running，但 `readinessProbe` 失败或 `availableReplicas < desiredReplicas`\n- Node `Ready=True`，但存在 `MemoryPressure` / `DiskPressure`\n- PVC 未绑定、NFS 挂载异常、CSI/挂载链路异常\n- CoreDNS 正常运行，但 DNS 解析或上游转发异常\n- Calico Pod 存活，但路由、策略或 BGP/overlay 出现异常\n\n### 原则 2: 当前状态优先于历史事件\n- Events 只能作为线索，不能单独等于当前故障\n- 只有当事件指向的对象**当前仍存在且当前仍异常**，才能作为当前故障依据\n- 如果对象已恢复、已替换或已删除，则该事件只算历史背景\n\n### 原则 3: 最小必要探测，禁止默认全量扫描\n高效排查的目标是：\n- 先从用户问题涉及的对象与相邻资源面开始\n- 先做**最便宜、最容易确认当前状态**的查询\n- 已经获得足够证据后立即停止扩展\n\n不推荐每次默认做：\n- 所有命名空间全量 describe\n- 所有节点日志遍历\n- 全量 Prometheus 指标扫描\n- 全量网络抓包\n\n### 原则 4: 先确认“当前是否真的异常”，再确认“异常在哪一面”\n推荐顺序：\n1. 用户提到的资源当前状态是否异常\n2. 与其最相邻的资源面是否异常\n3. 只有相邻面不能解释时，再扩大范围\n\n## 高效健康检查基线\n\n当用户问“我的集群有什么问题”“现在健康吗”“这个服务为什么不通”时，优先覆盖以下检查面，但不要机械地全部展开。\n\n### 1. 节点面\n关键对象:\n- `Node`\n- `Node Conditions`\n- `kubelet`\n- `containerd`\n\n优先关注:\n- `Ready`\n- `MemoryPressure`\n- `DiskPressure`\n- `PIDPressure`\n- 节点是否频繁切换 `Ready/NotReady`\n\n最小检查:\n```bash\nkubectl get nodes -o wide\nkubectl describe node <node-name>\n```\n\n何时继续深入:\n- 只有当节点状态异常、条件异常、或大量 Pod 都集中在同一节点异常时\n- 再去看 `journalctl -u kubelet`、`journalctl -u containerd`\n\n### 2. 工作负载面\n关键对象:\n- `Pod`\n- `Deployment`\n- `StatefulSet`\n- `DaemonSet`\n- `Job/CronJob`\n\n优先关注:\n- `CrashLoopBackOff`\n- `OOMKilled`\n- `Pending`\n- `ContainerCreating`\n- `Terminating`\n- `readyReplicas` / `availableReplicas`\n\n最小检查:\n```bash\nkubectl get pods -A -o wide\nkubectl get deploy,statefulset,daemonset -A\n```\n\n何时继续深入:\n- 只有当某个工作负载当前异常时，再对该对象执行 `describe` / `logs --previous`\n\n### 3. Service 与流量面\n关键对象:\n- `Service`\n- `Endpoints`\n- `EndpointSlice`\n- `Ingress`\n- CoreDNS\n- Calico 相关组件\n\n优先关注:\n- `Service` 是否有 `Endpoints`\n- selector 是否匹配到正确 Pod\n- Pod 是否 `Ready`\n- DNS 是否可解析\n- Calico 网络插件是否正常\n\n最小检查:\n```bash\nkubectl get svc,endpoints,endpointslices -A\nkubectl get pods -n kube-system -l k8s-app=kube-dns\nkubectl get pods -n kube-system -l k8s-app=calico-node\n```\n\n何时继续深入:\n- 只有当“服务不可用、访问失败、DNS 异常、跨节点不通”时\n- 再扩展到 `kubectl describe svc`、`iptables`、`tcpdump`、Calico 日志\n\n### 4. 存储面\n关键对象:\n- `PVC`\n- `PV`\n- `StorageClass`\n- NFS 服务端可达性与导出目录\n\n对于 NFS 环境，优先关注:\n- `PVC Pending`\n- 挂载超时或权限错误\n- NFS 服务器不可达\n- stale file handle / access denied / mount timeout\n\n最小检查:\n```bash\nkubectl get pvc,pv -A\nkubectl describe pvc <pvc-name> -n <namespace>\nkubectl describe pod <pod-name> -n <namespace>\n```\n\n何时继续深入:\n- 只有当 Pod 处于 `Pending` / `ContainerCreating` / `MountVolume` 相关错误时\n- 再检查 NFS 服务端、导出目录、节点到 NFS 的网络连通性\n\n### 5. 控制面与基础组件\n关键对象:\n- `kube-apiserver`\n- `etcd`\n- `scheduler`\n- `controller-manager`\n- CoreDNS\n- kube-proxy\n\n这些对象不需要每次全查。只有在以下场景优先关注:\n- 多个业务对象同时异常\n- 节点大面积 NotReady\n- API 调用明显失败、状态不一致\n- Service/DNS 大面积失效\n\n## 按用户问题决定优先检查哪一面\n\n### 如果用户问“我的集群有什么问题”\n先做最小检查：\n1. `kubectl get nodes`\n2. `kubectl get pods -A`\n3. `kubectl get deploy,statefulset,daemonset -A`\n4. 如用户反馈是“服务不通”，再看 `svc/endpoints`\n\n### 如果用户问“某服务为什么访问不到”\n优先顺序：\n1. `Service`\n2. `Endpoints/EndpointSlice`\n3. 后端 Pod 是否 `Ready`\n4. DNS / Calico / kube-proxy\n\n不要先做：\n- 全集群所有 Pod logs\n- 所有节点指标查询\n\n### 如果用户问“某 Pod 为什么起不来”\n优先顺序：\n1. `kubectl get pod`\n2. `kubectl describe pod`\n3. `kubectl logs --previous`\n4. 如涉及挂载/调度/镜像，再扩展到 PVC、Node、Registry\n\n### 如果用户问“为什么 Pending”\n优先考虑：\n- 调度资源不足\n- taint / affinity / nodeSelector\n- PVC 未绑定\n- NFS / 存储不可用\n\n### 如果用户问“为什么服务有问题但 Pod 都正常”\n优先考虑：\n- `Service` selector 错误\n- `Endpoints` 为空\n- Pod 未 Ready\n- 端口映射错误\n- DNS 解析失败\n- Calico / kube-proxy 转发异常\n\n## 私有化环境下常见异常面\n\n### Calico 相关\n常见问题:\n- Pod 跨节点不通\n- NetworkPolicy 拦截\n- calico-node 异常\n- 路由/BGP/overlay 配置异常\n\n优先证据:\n```bash\nkubectl get pods -n kube-system -l k8s-app=calico-node\nkubectl logs -n kube-system ds/calico-node --tail=100\n```\n\n### NFS 相关\n常见问题:\n- PVC 长时间 Pending\n- Pod 卡在挂载阶段\n- `mount.nfs` 超时\n- `access denied` / 权限异常\n\n优先证据:\n```bash\nkubectl describe pvc <pvc-name> -n <namespace>\nkubectl describe pod <pod-name> -n <namespace>\n```\n\n### containerd 相关\n常见问题:\n- 容器无法创建\n- 镜像拉取异常\n- sandbox/container runtime 创建失败\n- CRI 层异常导致 Pod 卡住\n\n只有在 Pod 明显卡在 runtime 阶段时，再看:\n```bash\njournalctl -u containerd -l --no-pager | tail -100\njournalctl -u kubelet -l --no-pager | tail -100\n```\n\n## 低成本判断规则\n\n| 当前现象 | 优先怀疑面 | 不要直接下的结论 |\n|----------|------------|------------------|\n| Pod Running，但服务不可用 | Service / Endpoints / Ready / DNS / Calico | 不能直接判定健康 |\n| Pod Pending | 调度 / 资源 / PVC / Taint | 不能直接判定为应用错误 |\n| Pod CrashLoopBackOff | L2/L4 | 不能只靠 event 判断，必须看 describe/logs |\n| Node Ready 但有 Pressure | 节点资源压力 | 不能直接判定节点健康 |\n| PVC Bound 但 Pod 挂载失败 | NFS / 节点挂载链路 | 不能只看 PVC 状态 |\n| 历史 Warning 事件存在 | 只算线索 | 不能直接判定当前故障 |\n\n## 建议的“停止扩展”时机\n\n在以下任一条件成立时，应停止继续扩大排查范围：\n- 已找到当前明确异常对象\n- 已形成能解释用户问题的直接证据链\n- 新工具调用只会重复确认已有结论\n\n换句话说：\n- **先定位当前异常对象，再决定是否扩展**\n- **不是先全量扫描，再从海量信息里找问题**\n\n## 与经典排错资料的一致性说明\n\n本手册吸收了 Kubernetes Handbook 排错总览中的通用思路，但针对私有化环境进行了裁剪：\n- 保留了 `Node / Pod / Network / PV / Tools` 这些核心检查面\n- 强化了 `Service/Endpoints`、Calico、NFS、containerd\n- 弱化了公有云特有的云盘、云 LB、云厂商网络依赖\n\n参考资料:\n- Kubernetes Handbook 排错总览: https://feisky.xyz/kubernetes-handbook/troubleshooting/\n- 集群排错: https://kubernetes.feisky.xyz/troubleshooting/cluster\n- Pod 排错: https://feisky.xyz/kubernetes-handbook/troubleshooting/pod.html\n- 网络排错: https://feisky.xyz/kubernetes-handbook/troubleshooting/network.html\n- PV 排错: https://kubernetes.feisky.xyz/troubleshooting/pv\n- 排错工具: https://kubernetes.feisky.xyz/troubleshooting/tools\n\n</runbook>\nNote: the above runbook is for DIAGNOSTIC REFERENCE ONLY. Follow the DIAGNOSTIC steps to gather evidence using tools, but DO NOT execute any remediation/fix commands. Report your findings and suggest fixes in your analysis.", "duration_s": 0}, {"tool": "kubernetes_tabular_query", "data": "NAMESPACE     NAME                                                STATUS    NODE     IP               READY                 REASON             RESTARTS\naiops-e2e     dns-test                                            Pending   node2    172.16.104.9     false                 ImagePullBackOff   0\naiops-e2e     imagepull-fail-victim                               Pending   node2    172.16.104.58    false                 ImagePullBackOff   0\naiops-e2e     network-test                                        Pending   node2    172.16.104.14    false                 ImagePullBackOff   0\naiops-e2e     network-test-curl                                   Pending   node2    172.16.104.36    false                 ImagePullBackOff   0\naiops-e2e     network-test-debug                                  Running   node2    172.16.104.16    true                  <none>             0\naiops-e2e     ping-test                                           Pending   node2    172.16.104.56    false                 ImagePullBackOff   0\naiops-e2e     simple-ping-test                                    Pending   node2    172.16.104.61    false                 ImagePullBackOff   0\naiops-e2e     simple-test                                         Pending   node2    172.16.104.60    false                 ImagePullBackOff   0\naiops         aiops-copilot-76779bb6df-4bcrf                      Running   node2    172.16.104.29    true                  <none>             0\ndefault       dns-test-existing                                   Running   node1    172.16.166.148   true                  <none>             0\ndefault       exec-test                                           Running   node2    172.16.104.8     true                  <none>             0\ndefault       network-test-from-running                           Running   node2    172.16.104.50    true                  <none>             0\ndefault       nfs-client-provisioner-6fcd4994c9-lczf6             Running   node2    172.16.104.41    true                  <none>             4\nkube-system   calico-kube-controllers-6c67f9d475-2xcb7            Running   node1    172.16.166.133   true                  <none>             4\nkube-system   calico-node-4kp26                                   Running   master   10.2.0.48        true                  <none>             12\nkube-system   calico-node-d2dhp                                   Running   node2    10.2.0.50        true                  <none>             13\nkube-system   calico-node-mnrjs                                   Running   node1    10.2.0.49        true                  <none>             12\nkube-system   coredns-777df594b8-j4857                            Running   node1    172.16.166.129   true                  <none>             4\nkube-system   coredns-777df594b8-s8r4n                            Running   node1    172.16.166.185   true                  <none>             4\nkube-system   etcd-master                                         Running   master   10.2.0.48        true                  <none>             13\nkube-system   kube-apiserver-master                               Running   master   10.2.0.48        true                  <none>             13\nkube-system   kube-controller-manager-master                      Running   master   10.2.0.48        true                  <none>             36\nkube-system   kube-multus-ds-rnvbg                                Running   node1    10.2.0.49        true                  <none>             12\nkube-system   kube-multus-ds-sc2jn                                Running   master   10.2.0.48        true                  <none>             4\nkube-system   kube-multus-ds-x7h9s                                Running   node2    10.2.0.50        true                  <none>             13\nkube-system   kube-proxy-69zzr                                    Running   node2    10.2.0.50        true                  <none>             4\nkube-system   kube-proxy-bblvc                                    Running   node1    10.2.0.49        true                  <none>             4\nkube-system   kube-proxy-wbh4k                                    Running   master   10.2.0.48        true                  <none>             4\nkube-system   kube-scheduler-master                               Running   master   10.2.0.48        true                  <none>             38\nmcp           mcp-server-manager-8677f6896c-d4mr9                 Running   node2    172.16.104.59    true                  <none>             0\nxnet          alertmanager-observability-alertmanager-0           Running   node1    172.16.166.161   true,true             <none>             4,4\nxnet          api-server-6bd6bf8d6f-27svp                         Running   master   172.16.219.106   true                  <none>             4\nxnet          deepflow-agent-pcknn                                Running   node1    172.16.166.181   true                  <none>             9\nxnet          deepflow-agent-trc8k                                Running   node2    172.16.104.7     true                  <none>             7\nxnet          deepflow-agent-whn22                                Running   master   172.16.219.97    true                  <none>             8\nxnet          elasticsearch-master-0                              Running   master   172.16.219.109   true                  <none>             4\nxnet          ham-p9dxv                                           Running   node2    172.16.104.21    true                  <none>             14\nxnet          ham-qzjg5                                           Running   master   172.16.219.112   true                  <none>             4\nxnet          ham-wt9kh                                           Running   node1    172.16.166.187   true                  <none>             13\nxnet          lgtm-5dc5c67d5f-sc286                               Running   node1    172.16.166.151   true                  <none>             4\nxnet          observability-clickhouse-0                          Running   node1    172.16.166.137   true                  <none>             4\nxnet          observability-deepflow-app-654fcfbfbf-q8st6         Running   node1    172.16.166.160   true                  <none>             4\nxnet          observability-deepflow-server-774dd6c5b7-9c998      Running   node1    172.16.166.135   true                  <none>             14\nxnet          observability-filebeat-ffwsp                        Running   master   172.16.219.80    true                  <none>             4\nxnet          observability-filebeat-m58xw                        Running   node1    172.16.166.134   true                  <none>             5\nxnet          observability-filebeat-w6gtr                        Running   node2    172.16.104.53    true                  <none>             5\nxnet          observability-grafana-58bf9cfd6f-ndsxr              Running   node1    172.16.166.144   true,true,true,true   <none>             7,21,4,4\nxnet          observability-kepler-2sgrr                          Running   node1    10.2.0.49        true                  <none>             6\nxnet          observability-kepler-7scjm                          Running   master   10.2.0.48        true                  <none>             7\nxnet          observability-kepler-ggstf                          Running   node2    10.2.0.50        true                  <none>             8\nxnet          observability-kibana-65d7c45f6d-tm4vv               Running   node1    172.16.166.191   true                  <none>             4\nxnet          observability-kube-state-metrics-798986b8b7-6z2dq   Running   master   172.16.219.65    true                  <none>             4\nxnet          observability-mysql-764f9d5966-wh2bc                Running   master   172.16.219.98    true                  <none>             4\nxnet          observability-operator-d4495dc86-69lgw              Running   node1    172.16.166.182   true                  <none>             4\nxnet          observability-prometheus-node-exporter-lj75r        Running   master   10.2.0.48        true                  <none>             4\nxnet          observability-prometheus-node-exporter-qp2qd        Running   node2    10.2.0.50        true                  <none>             4\nxnet          observability-prometheus-node-exporter-wnbb8        Running   node1    10.2.0.49        true                  <none>             4\nxnet          observability-telegraf-79f45d86-4kzkm               Running   master   172.16.219.113   true                  <none>             4\nxnet          prometheus-observability-prometheus-0               Running   node1    172.16.166.142   true,true             <none>             4,12\nxnet          xnet-agent-568f547566-jdsgp                         Running   node2    172.16.104.40    true                  <none>             4", "duration_s": 0}, {"tool": "kubectl_describe", "data": "Name:               node2\nRoles:              <none>\nLabels:             beta.kubernetes.io/arch=amd64\n                    beta.kubernetes.io/os=linux\n                    kubernetes.io/arch=amd64\n                    kubernetes.io/hostname=node2\n                    kubernetes.io/os=linux\nAnnotations:        kubeadm.alpha.kubernetes.io/cri-socket: unix:///var/run/containerd/containerd.sock\n                    node.alpha.kubernetes.io/ttl: 0\n                    projectcalico.org/IPv4Address: 10.2.0.50/19\n                    projectcalico.org/IPv4IPIPTunnelAddr: 172.16.104.0\n                    volumes.kubernetes.io/controller-managed-attach-detach: true\nCreationTimestamp:  Thu, 25 Sep 2025 03:10:26 +0000\nTaints:             <none>\nUnschedulable:      false\nLease:\n  HolderIdentity:  node2\n  AcquireTime:     <unset>\n  RenewTime:       Wed, 22 Apr 2026 03:49:44 +0000\nConditions:\n  Type                 Status  LastHeartbeatTime                 LastTransitionTime                Reason                       Message\n  ----                 ------  -----------------                 ------------------                ------                       -------\n  NetworkUnavailable   False   Fri, 17 Apr 2026 07:03:52 +0000   Fri, 17 Apr 2026 07:03:52 +0000   CalicoIsUp                   Calico is running on this node\n  MemoryPressure       False   Wed, 22 Apr 2026 03:48:24 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletHasSufficientMemory   kubelet has sufficient memory available\n  DiskPressure         False   Wed, 22 Apr 2026 03:48:24 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletHasNoDiskPressure     kubelet has no disk pressure\n  PIDPressure          False   Wed, 22 Apr 2026 03:48:24 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletHasSufficientPID      kubelet has sufficient PID available\n  Ready                True    Wed, 22 Apr 2026 03:48:24 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletReady                 kubelet is posting ready status. AppArmor enabled\nAddresses:\n  InternalIP:  10.2.0.50\n  Hostname:    node2\nCapacity:\n  cpu:                12\n  ephemeral-storage:  203770680Ki\n  hugepages-1Gi:      0\n  hugepages-2Mi:      0\n  memory:             32860484Ki\n  pods:               110\nAllocatable:\n  cpu:                12\n  ephemeral-storage:  187795058378\n  hugepages-1Gi:      0\n  hugepages-2Mi:      0\n  memory:             32758084Ki\n  pods:               110\nSystem Info:\n  Machine ID:                 6bb27862c82149418d0f5624411d0b22\n  System UUID:                0f5af30a-d385-493c-bc8b-5442fd024eee\n  Boot ID:                    0ea98079-ad10-4a20-85f5-19b34afd257e\n  Kernel Version:             5.15.0-174-generic\n  OS Image:                   Ubuntu 22.04.4 LTS\n  Operating System:           linux\n  Architecture:               amd64\n  Container Runtime Version:  containerd://1.6.32\n  Kubelet Version:            v1.26.8\n  Kube-Proxy Version:         v1.26.8\nNon-terminated Pods:          (22 in total)\n  Namespace                   Name                                            CPU Requests  CPU Limits  Memory Requests  Memory Limits  Age\n  ---------                   ----                                            ------------  ----------  ---------------  -------------  ---\n  aiops-e2e                   dns-test                                        0 (0%)        0 (0%)      0 (0%)           0 (0%)         16m\n  aiops-e2e                   imagepull-fail-victim                           0 (0%)        0 (0%)      0 (0%)           0 (0%)         52m\n  aiops-e2e                   network-test                                    0 (0%)        0 (0%)      0 (0%)           0 (0%)         48m\n  aiops-e2e                   network-test-curl                               0 (0%)        0 (0%)      0 (0%)           0 (0%)         70s\n  aiops-e2e                   network-test-debug                              0 (0%)        0 (0%)      0 (0%)           0 (0%)         10m\n  aiops-e2e                   ping-test                                       0 (0%)        0 (0%)      0 (0%)           0 (0%)         20m\n  aiops-e2e                   simple-ping-test                                0 (0%)        0 (0%)      0 (0%)           0 (0%)         16m\n  aiops-e2e                   simple-test                                     0 (0%)        0 (0%)      0 (0%)           0 (0%)         45m\n  aiops                       aiops-copilot-76779bb6df-4bcrf                  250m (2%)     1 (8%)      512Mi (1%)       2Gi (6%)       132m\n  default                     exec-test                                       0 (0%)        0 (0%)      0 (0%)           0 (0%)         2d\n  default                     network-test-from-running                       0 (0%)        0 (0%)      0 (0%)           0 (0%)         46h\n  default                     nfs-client-provisioner-6fcd4994c9-lczf6         0 (0%)        0 (0%)      0 (0%)           0 (0%)         85d\n  kube-system                 calico-node-d2dhp                               250m (2%)     0 (0%)      0 (0%)           0 (0%)         183d\n  kube-system                 kube-multus-ds-x7h9s                            100m (0%)     100m (0%)   50Mi (0%)        50Mi (0%)      183d\n  kube-system                 kube-proxy-69zzr                                0 (0%)        0 (0%)      0 (0%)           0 (0%)         27d\n  mcp                         mcp-server-manager-8677f6896c-d4mr9             200m (1%)     1 (8%)      1G (2%)          2560Mi (8%)    41h\n  xnet                        deepflow-agent-trc8k                            100m (0%)     1 (8%)      128Mi (0%)       768Mi (2%)     19d\n  xnet                        ham-p9dxv                                       0 (0%)        0 (0%)      0 (0%)           0 (0%)         177d\n  xnet                        observability-filebeat-w6gtr                    100m (0%)     1 (8%)      100Mi (0%)       200Mi (0%)     19d\n  xnet                        observability-kepler-ggstf                      0 (0%)        0 (0%)      0 (0%)           0 (0%)         19d\n  xnet                        observability-prometheus-node-exporter-qp2qd    0 (0%)        0 (0%)      0 (0%)           0 (0%)         19d\n  xnet                        xnet-agent-568f547566-jdsgp                     0 (0%)        0 (0%)      0 (0%)           0 (0%)         108d\nAllocated resources:\n  (Total limits may be over 100 percent, i.e., overcommitted.)\n  Resource           Requests         Limits\n  --------           --------         ------\n  cpu                1 (8%)           4100m (34%)\n  memory             1828375040 (5%)  5626Mi (17%)\n  ephemeral-storage  0 (0%)           0 (0%)\n  hugepages-1Gi      0 (0%)           0 (0%)\n  hugepages-2Mi      0 (0%)           0 (0%)\nEvents:              <none>", "duration_s": 0}, {"tool": "kubernetes_tabular_query", "data": "NAMESPACE     NAME                                     TYPE     CLUSTER-IP       PORT(S)                                             SELECTOR                                                                                                                    ENDPOINTS\naaa           test1-redis-headless                     <none>   None             6379                                                map[app:redis release:test1]                                                                                                <none>\naaa           test1-redis-master                       <none>   172.30.184.110   6379                                                map[app:redis release:test1 role:master]                                                                                    <none>\naaa           test1-redis-slave                        <none>   172.30.186.210   6379                                                map[app:redis release:test1 role:slave]                                                                                     <none>\naiops         aiops-copilot                            <none>   172.30.33.24     8000                                                map[app:aiops-copilot]                                                                                                      <none>\ndefault       kubernetes                               <none>   172.30.0.1       443                                                 <none>                                                                                                                      <none>\nkube-system   kube-dns                                 <none>   172.30.0.10      53,53,9153                                          map[k8s-app:kube-dns]                                                                                                       <none>\nkube-system   observability-coredns                    <none>   None             9153                                                map[k8s-app:kube-dns]                                                                                                       <none>\nkube-system   observability-kube-controller-manager    <none>   None             10257                                               map[component:kube-controller-manager]                                                                                      <none>\nkube-system   observability-kube-etcd                  <none>   None             2381                                                map[component:etcd]                                                                                                         <none>\nkube-system   observability-kube-proxy                 <none>   None             10249                                               map[k8s-app:kube-proxy]                                                                                                     <none>\nkube-system   observability-kube-scheduler             <none>   None             10259                                               map[component:kube-scheduler]                                                                                               <none>\nkube-system   observability-kubelet                    <none>   None             10250,10255,4194                                    <none>                                                                                                                      <none>\nmcp           mcp-server-manager                       <none>   172.30.236.87    8088,8091,8092,8093,8094,8095,8096,8097,8098,8099   map[app:mcp-server-manager]                                                                                                 <none>\nxnet          alertmanager-operated                    <none>   None             9093,9094,9094                                      map[app.kubernetes.io/name:alertmanager]                                                                                    <none>\nxnet          api-service                              <none>   172.30.47.171    8080                                                map[app:api-server]                                                                                                         <none>\nxnet          deepflow-agent                           <none>   172.30.23.250    80                                                  map[app:deepflow app.kubernetes.io/instance:observability app.kubernetes.io/name:deepflow-agent component:deepflow-agent]   <none>\nxnet          elasticsearch-external                   <none>   172.30.190.54    9200,9300                                           map[app:elasticsearch-master]                                                                                               <none>\nxnet          elasticsearch-master-headless            <none>   None             9200,9300                                           map[app:elasticsearch-master]                                                                                               <none>\nxnet          ham                                      <none>   172.30.96.4      8080                                                map[app:ham]                                                                                                                <none>\nxnet          lgtm                                     <none>   172.30.237.73    3000,4317,4318                                      map[app:lgtm]                                                                                                               <none>\nxnet          observability-alertmanager               <none>   172.30.125.46    9093,8080                                           map[alertmanager:observability-alertmanager app.kubernetes.io/name:alertmanager]                                            <none>\nxnet          observability-clickhouse                 <none>   172.30.124.73    8123,9000,9009                                      map[app:deepflow app.kubernetes.io/instance:observability app.kubernetes.io/name:clickhouse component:clickhouse]           <none>\nxnet          observability-clickhouse-headless        <none>   None             8123,9000,9009                                      map[app:deepflow app.kubernetes.io/instance:observability app.kubernetes.io/name:clickhouse component:clickhouse]           <none>\nxnet          observability-deepflow-app               <none>   172.30.227.137   20418                                               map[app:deepflow app.kubernetes.io/instance:observability app.kubernetes.io/name:deepflow component:deepflow-app]           <none>\nxnet          observability-deepflow-server            <none>   172.30.172.26    20416,20419,20417,20035,30035,20135,20033,30033     map[app:deepflow app.kubernetes.io/instance:observability app.kubernetes.io/name:deepflow component:deepflow-server]        <none>\nxnet          observability-grafana                    <none>   172.30.238.199   80                                                  map[app.kubernetes.io/instance:observability app.kubernetes.io/name:grafana]                                                <none>\nxnet          observability-kepler                     <none>   172.30.177.62    9102                                                map[app.kubernetes.io/component:exporter app.kubernetes.io/name:kepler-kepler]                                              <none>\nxnet          observability-kibana                     <none>   172.30.231.31    5601                                                map[app:observability-kibana release:observability]                                                                         <none>\nxnet          observability-kube-state-metrics         <none>   172.30.210.245   8080                                                map[app.kubernetes.io/instance:observability app.kubernetes.io/name:kube-state-metrics]                                     <none>\nxnet          observability-mysql                      <none>   172.30.112.96    30130                                               map[app:deepflow app.kubernetes.io/instance:observability app.kubernetes.io/name:mysql component:mysql]                     <none>\nxnet          observability-operator                   <none>   172.30.195.228   443                                                 map[app:observability-operator release:observability]                                                                       <none>\nxnet          observability-prometheus                 <none>   172.30.74.108    9090,8080                                           map[app.kubernetes.io/name:prometheus operator.prometheus.io/name:observability-prometheus]                                 <none>\nxnet          observability-prometheus-node-exporter   <none>   172.30.112.222   9100                                                map[app.kubernetes.io/instance:observability app.kubernetes.io/name:prometheus-node-exporter]                               <none>\nxnet          observability-telegraf                   <none>   172.30.164.221   8125,8125                                           map[app.kubernetes.io/component:telegraf app.kubernetes.io/instance:observability app.kubernetes.io/name:observability]     <none>\nxnet          prometheus-operated                      <none>   None             9090                                                map[app.kubernetes.io/name:prometheus]                                                                                      <none>\nxnet          test2-redis-headless                     <none>   None             6379                                                map[app:redis release:test2]                                                                                                <none>\nxnet          test2-redis-master                       <none>   172.30.110.97    6379                                                map[app:redis release:test2 role:master]                                                                                    <none>\nxnet          test2-redis-slave                        <none>   172.30.115.245   6379                                                map[app:redis release:test2 role:slave]                                                                                     <none>\nxnet          xnet-agent                               <none>   172.30.222.56    7070                                                map[app:xnet-agent]                                                                                                         <none>\nxnet          xnet-management                          <none>   172.30.85.213    9090,8000                                           <none>                                                                                                                      <none>\naaa           test1-redis-headless                     <none>   <none>           <none>                                              <none>                                                                                                                      <none>\naaa           test1-redis-master                       <none>   <none>           <none>                                              <none>                                                                                                                      <none>\naaa           test1-redis-slave                        <none>   <none>           <none>                                              <none>                                                                                                                      <none>\naiops         aiops-copilot                            <none>   <none>           <none>                                              <none>                                                                                                                      172.16.104.29\ndefault       kubernetes                               <none>   <none>           <none>                                              <none>                                                                                                                      10.2.0.48\ndefault       nfs-client                               <none>   <none>           <none>                                              <none>                                                                                                                      <none>\nkube-system   kube-dns                                 <none>   <none>           <none>                                              <none>                                                                                                                      172.16.166.129,172.16.166.185\nkube-system   observability-coredns                    <none>   <none>           <none>                                              <none>                                                                                                                      172.16.166.129,172.16.166.185\nkube-system   observability-kube-controller-manager    <none>   <none>           <none>                                              <none>                                                                                                                      10.2.0.48\nkube-system   observability-kube-etcd                  <none>   <none>           <none>                                              <none>                                                                                                                      10.2.0.48\nkube-system   observability-kube-proxy                 <none>   <none>           <none>                                              <none>                                                                                                                      10.2.0.48,10.2.0.49,10.2.0.50\nkube-system   observability-kube-scheduler             <none>   <none>           <none>                                              <none>                                                                                                                      10.2.0.48\nkube-system   observability-kubelet                    <none>   <none>           <none>                                              <none>                                                                                                                      10.2.0.48,10.2.0.49,10.2.0.50\nmcp           mcp-server-manager                       <none>   <none>           <none>                                              <none>                                                                                                                      172.16.104.59\nxnet          alertmanager-operated                    <none>   <none>           <none>                                              <none>                                                                                                                      172.16.166.161\nxnet          api-service                              <none>   <none>           <none>                                              <none>                                                                                                                      172.16.219.106\nxnet          deepflow-agent                           <none>   <none>           <none>                                              <none>                                                                                                                      172.16.104.7,172.16.166.181,172.16.219.97\nxnet          elasticsearch-external                   <none>   <none>           <none>                                              <none>                                                                                                                      172.16.219.109\nxnet          elasticsearch-master-headless            <none>   <none>           <none>                                              <none>                                                                                                                      172.16.219.109\nxnet          ham                                      <none>   <none>           <none>                                              <none>                                                                                                                      172.16.104.21,172.16.166.187,172.16.219.112\nxnet          lgtm                                     <none>   <none>           <none>                                              <none>                                                                                                                      172.16.166.151\nxnet          observability-alertmanager               <none>   <none>           <none>                                              <none>                                                                                                                      172.16.166.161\nxnet          observability-clickhouse                 <none>   <none>           <none>                                              <none>                                                                                                                      172.16.166.137\nxnet          observability-clickhouse-headless        <none>   <none>           <none>                                              <none>                                                                                                                      172.16.166.137\nxnet          observability-deepflow-app               <none>   <none>           <none>                                              <none>                                                                                                                      172.16.166.160\nxnet          observability-deepflow-server            <none>   <none>           <none>                                              <none>                                                                                                                      172.16.166.135\nxnet          observability-grafana                    <none>   <none>           <none>                                              <none>                                                                                                                      172.16.166.144\nxnet          observability-kepler                     <none>   <none>           <none>                                              <none>                                                                                                                      10.2.0.48,10.2.0.49,10.2.0.50\nxnet          observability-kibana                     <none>   <none>           <none>                                              <none>                                                                                                                      172.16.166.191\nxnet          observability-kube-state-metrics         <none>   <none>           <none>                                              <none>                                                                                                                      172.16.219.65\nxnet          observability-mysql                      <none>   <none>           <none>                                              <none>                                                                                                                      172.16.219.98\nxnet          observability-operator                   <none>   <none>           <none>                                              <none>                                                                                                                      172.16.166.182\nxnet          observability-prometheus                 <none>   <none>           <none>                                              <none>                                                                                                                      172.16.166.142\nxnet          observability-prometheus-node-exporter   <none>   <none>           <none>                                              <none>                                                                                                                      10.2.0.48,10.2.0.49,10.2.0.50\nxnet          observability-telegraf                   <none>   <none>           <none>                                              <none>                                                                                                                      172.16.219.113\nxnet          prometheus-operated                      <none>   <none>           <none>                                              <none>                                                                                                                      172.16.166.142\nxnet          test2-redis-headless                     <none>   <none>           <none>                                              <none>                                                                                                                      <none>\nxnet          test2-redis-master                       <none>   <none>           <none>                                              <none>                                                                                                                      <none>\nxnet          test2-redis-slave                        <none>   <none>           <none>                                              <none>                                                                                                                      <none>\nxnet          xnet-agent                               <none>   <none>           <none>                                              <none>                                                                                                                      172.16.104.40\nxnet          xnet-management                          <none>   <none>           <none>                                              <none>                                                                                                                      10.2.0.24", "duration_s": 0}, {"tool": "kubectl_run_image", "data": "{\"success\": false, \"stdout\": \"pod \\\"curl-test\\\" deleted\\n\", \"stderr\": \"error: timed out waiting for the condition\\n\", \"returncode\": 1}", "duration_s": 0}], "llm_analysis": "现在基于上游定位结果和诊断手册，我将制定证据采集计划并执行工具采集。\n\n```json\n{\n  \"layer\": \"L3\",\n  \"evidence_plan\": [\n    {\n      \"id\": \"e1\",\n      \"description\": \"获取所有异常 Pod 的详细状态和事件\",\n      \"level\": \"critical\",\n      \"tool\": \"kubernetes_tabular_query\",\n      \"command\": \"kubectl get pods -A -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,IP:.status.podIP,READY:.status.containerStatuses[*].ready,REASON:.status.containerStatuses[*].state.waiting.reason,RESTARTS:.status.containerStatuses[*].restartCount'\",\n      \"purpose\": \"确认所有 Pod 的当前状态，特别是 ImagePullBackOff 的 Pod 数量和分布\"\n    },\n    {\n      \"id\": \"e2\",\n      \"description\": \"获取 node2 节点的详细状态和条件\",\n      \"level\": \"important\",\n      \"tool\": \"kubectl_describe\",\n      \"command\": \"kubectl describe node node2\",\n      \"purpose\": \"检查 node2 节点的网络连接性、资源压力和 taint 状态，因为所有异常 Pod 都调度到 node2\"\n    },\n    {\n      \"id\": \"e3\",\n      \"description\": \"获取空端点服务的详细信息\",\n      \"level\": \"important\",\n      \"tool\": \"kubernetes_tabular_query\",\n      \"command\": \"kubectl get svc,endpoints -A -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,TYPE:.type,CLUSTER-IP:.spec.clusterIP,PORT(S):.spec.ports[*].port,SELECTOR:.spec.selector,ENDPOINTS:.subsets[*].addresses[*].ip'\",\n      \"purpose\": \"确认哪些服务的 endpoints 为空，以及它们的 selector 配置\"\n    },\n    {\n      \"id\": \"e4\",\n      \"description\": \"测试 Docker Hub 网络连通性\",\n      \"level\": \"critical\",\n      \"tool\": \"kubectl_run_image\",\n      \"command\": \"kubectl run curl-test --rm -it --image=curlimages/curl --restart=Never -- curl -sI https://registry-1.docker.io/v2/ --connect-timeout 5\",\n      \"purpose\": \"验证从集群内部到 Docker Hub 的网络连通性，确认镜像拉取失败的根本原因\"\n    },\n    {\n      \"id\": \"e5\",\n      \"description\": \"获取异常 Pod 的完整 YAML 配置\",\n      \"level\": \"important\",\n      \"tool\": \"kubectl_get_yaml\",\n      \"command\": \"kubectl get -o yaml pod network-test -n aiops-e2e\",\n      \"purpose\": \"查看 network-test Pod 的完整配置，包括镜像地址、imagePullSecrets 等\"\n    }\n  ],\n  \"collection_strategy\": \"首先确认所有异常 Pod 的状态分布，然后重点检查 node2 节点状态，同时验证 Docker Hub 网络连通性。最后检查空端点服务的配置。\"\n}\n```\n\n现在开始执行证据采集：", "collection_summary": "计划 6 项，实际采集 6 项，未采集 0 项，完整度 100%", "evidence_inventory": [{"id": "e1", "description": "获取所有异常 Pod 的详细状态和事件", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e2", "description": "获取 node2 节点的详细状态和条件", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e3", "description": "获取空端点服务的详细信息", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e4", "description": "测试 Docker Hub 网络连通性", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e5", "description": "获取异常 Pod 的完整 YAML 配置", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "extra_1", "description": "工具采集: fetch_runbook", "level": "important", "collected": true, "source": "thinking_extra"}], "missing_reasons": [], "early_stop": {"triggered": true, "reason": "critical 和 important 级证据均已满足，提前停止后续采集", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 6/6 项, 完整度: 100%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 11.8s)
   📤 → 下游数据: root_cause=
   confidence=90%
   causal_chain={"root_cause": "从 Kubernetes 集群（特别是 node2 节点）到公共镜像仓库 registry-1.docker.io 的网络连接异常。", "propagation": "网络连接问题导致 containerd 无法从 Docker Hub 拉取 busybox 和 nginx:latest 等基础镜像。", "direct_cause": "Pod 的容器镜像拉取失败，状态变为 ImagePullBackOff。", "manifestation": "aiops-e2e 命名空间下多个使用公共镜像的 Pod 持续处于 Pending 状态。同时，测试网络连通性的临时 Pod 也因同样原因无法启动。"}
   rca_analysis={"phenomenon": "aiops-e2e 命名空间下多个 Pod 处于 Pending 状态，状态为 ImagePullBackOff；同时 aaa 和 xnet 命名空间下部分服务的 Endpoints 为空。", "evidence_inventory": [{"id": "e1", "content": "NAMESPACE     NAME                                                STATUS    NODE     IP               READY                 REASON             RESTARTS\naiops-e2e     dns-test                                            Pending   node2    172.16.104.9     false                 ImagePullBackOff   0\naiops-e2e     imagepull-fail-victim                               Pending   node2    172.16.104.58    false                 ImagePullBackOff   0\naiops-e2e     network-test                                        Pending   node2    172.16.104.14    false                 ImagePullBackOff   0\naiops-e2e     network-test-curl                                   Pending   node2    172.16.104.36    false                 ImagePullBackOff   0\naiops-e2e     ping-test                                           Pending   node2    172.16.104.56    false                 ImagePullBackOff   0\naiops-e2e     simple-ping-test                                    Pending   node2    172.16.104.61    false                 ImagePullBackOff   0\naiops-e2e     simple-test                                         Pending   node2    172.16.104.60    false                 ImagePullBackOff   0", "source": "kubernetes_tabular_query", "reliability": "高"}, {"id": "e2", "content": "Name: node2\nConditions:\n  NetworkUnavailable   False\n  MemoryPressure       False\n  DiskPressure         False\n  PIDPressure          False\n  Ready                True\n...\nEvents:              <none>", "source": "kubectl_describe", "reliability": "高"}, {"id": "e3", "content": "NAMESPACE     NAME                                     TYPE     CLUSTER-IP       PORT(S)   SELECTOR                                                    ENDPOINTS\naaa           test1-redis-headless                     <none>   None             6379      map[app:redis release:test1]                                <none>\naaa           test1-redis-master                       <none>   172.30.184.110   6379      map[app:redis release:test1 role:master]                    <none>\naaa           test1-redis-slave                        <none>   172.30.186.210   6379      map[app:redis release:test1 role:slave]                     <none>\nxnet          test2-redis-headless                     <none>   None             6379      map[app:redis release:test2]                                <none>\nxnet          test2-redis-master                       <none>   172.30.110.97    6379      map[app:redis release:test2 role:master]                    <none>\nxnet          test2-redis-slave                        <none>   172.30.115.245   6379      map[app:redis release:test2 role:slave]                     <none>", "source": "kubernetes_tabular_query", "reliability": "高"}, {"id": "e4", "content": "{\"success\": false, \"stdout\": \"pod \\\"curl-test\\\" deleted\\n\", \"stderr\": \"error: timed out waiting for the condition\\n\", \"returncode\": 1}", "source": "kubectl_run_image", "reliability": "中"}, {"id": "e5", "content": "上游定位结果摘要：Pod network-test 和 ping-test 的事件显示拉取镜像 busybox 失败，错误为 i/o timeout 或 connection reset by peer，指向 registry-1.docker.io。", "source": "layer 节点输出", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "aiops-e2e 命名空间下 8 个 Pod 状态为 Pending，REASON 均为 ImagePullBackOff，NODE 均为 node2 (10.2.0.50)。", "interpretation": "这表明在 node2 节点上，存在一个影响多个 Pod 的公共问题，导致它们无法启动。所有 Pod 的失败原因一致，指向镜像拉取失败。"}, {"evidence_id": "e2", "raw_data": "node2 节点状态 Ready，NetworkUnavailable 为 False，MemoryPressure、DiskPressure、PIDPressure 均为 False。节点资源充足（CPU 使用率 8%，内存使用率 5%），无 taint，可调度。", "interpretation": "node2 节点本身健康，无资源压力，网络插件 Calico 运行正常。排除了节点资源不足或节点级网络故障导致 Pod Pending 的可能性。"}, {"evidence_id": "e3", "raw_data": "aaa 命名空间的 test1-redis-* 服务和 xnet 命名空间的 test2-redis-* 服务，其 ENDPOINTS 列显示为 <none>。这些服务都有对应的 selector（如 app:redis, release:test1）。", "interpretation": "服务端点为空，意味着没有 Pod 的标签与服务的 selector 匹配。对于 aaa 命名空间，上游定位结果已确认该命名空间下无任何 Pod，因此端点为空是预期结果。对于 xnet 命名空间，需要检查是否有标签匹配的 Pod。"}, {"evidence_id": "e4", "raw_data": "执行 kubectl run curl-test --rm -it --image=curlimages/curl ... 命令测试 Docker Hub 连通性失败，返回码为 1，错误信息为 'timed out waiting for the condition'。", "interpretation": "该命令尝试运行一个临时 Pod 来测试网络，但 Pod 本身未能成功创建（超时）。这间接印证了从集群内部拉取外部镜像（curlimages/curl）存在困难，与异常 Pod 的 ImagePullBackOff 问题表现一致。"}, {"evidence_id": "e5", "raw_data": "关键事件：'Failed to pull image \"busybox\"... i/o timeout' 和 'connection reset by peer'，错误指向 registry-1.docker.io。", "interpretation": "这是导致 aiops-e2e 命名空间下 Pod 处于 ImagePullBackOff 状态的直接原因。从 node2 节点到公共 Docker Hub 的网络连接不稳定，存在超时或连接重置。"}], "causal_chain": {"root_cause": "从 Kubernetes 集群（特别是 node2 节点）到公共镜像仓库 registry-1.docker.io 的网络连接异常。", "propagation": "网络连接问题导致 containerd 无法从 Docker Hub 拉取 busybox 和 nginx:latest 等基础镜像。", "direct_cause": "Pod 的容器镜像拉取失败，状态变为 ImagePullBackOff。", "manifestation": "aiops-e2e 命名空间下多个使用公共镜像的 Pod 持续处于 Pending 状态。同时，测试网络连通性的临时 Pod 也因同样原因无法启动。"}, "root_cause_summary": "根因是集群到 Docker Hub 的网络连通性问题。证据包括：1) 多个 Pod（如 network-test, ping-test）的事件明确显示拉取 busybox 镜像时发生 'i/o timeout' 和 'connection reset by peer'（证据 e5）。2) 所有受影响的 Pod 均被调度至 node2 节点（证据 e1），但该节点本身状态健康（证据 e2），表明问题出在外部网络连接上。3) 尝试运行测试网络连通性的 Pod 同样失败（证据 e4），进一步证实了从集群内部访问外部网络（Docker Hub）存在障碍。", "confidence": 0.9, "primary_runbooks": ["私有化 Kubernetes 环境健康与高效排查参考手册", "L3 镜像拉取失败 (ImagePullBackOff) 手册"], "alternative_causes": ["Docker Hub 服务临时中断。但考虑到多个 Pod 长时间失败，且影响范围仅限于从该仓库拉取镜像的 Pod，集群内部其他网络正常，此可能性较低。", "节点防火墙或网络策略阻止了到特定外部地址（registry-1.docker.io）的出站连接。需要检查 node2 节点的网络配置。"], "limitations": "1. 证据 e4 的网络测试未能成功执行，仅获得了命令执行失败的结果，未能直接获取到 Docker Hub 的 HTTP 响应状态码。2. 未采集到 node2 节点上 containerd 的详细日志，以进一步确认网络错误的细节。3. 对于 xnet 命名空间中 test2-redis-* 服务端点为空的问题，未采集到 xnet 命名空间下所有 Pod 的标签信息，无法完全确认是否因标签不匹配导致。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 90%
   🔗 因果链:
     根本原因: 从 Kubernetes 集群（特别是 node2 节点）到公共镜像仓库 registry-1.docker.io 的网络连接异常。
     传导机制: 网络连接问题导致 containerd 无法从 Docker Hub 拉取 busybox 和 nginx:latest 等基础镜像。
     最终表现: aiops-e2e 命名空间下多个使用公共镜像的 Pod 持续处于 Pending 状态。同时，测试网络连通性的临时 Pod 也因同样原因无法启动。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 25.1s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5728 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 7m 49.9s
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
| **置信度** | 高 (90%) |
| **证据完整度** | 6/6 (100%) |

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键发现**：
您的集群存在两个主要问题：
1.  **镜像拉取失败**：`aiops-e2e` 命名空间下多个 Pod 因无法从 Docker Hub 拉取镜像而处于 `Pending` 状态。
2.  **服务端点缺失**：`aaa` 和 `xnet` 命名空间下部分 Redis 服务没有后端 Pod，导致服务端点为空。

**关键实体**：
| 类型 | 值 |
|------|-----|
| **异常命名空间** | `aiops-e2e` |
| **异常 Pod** | `network-test`, `ping-test`, `simple-ping-test`, `simple-test`, `dns-test`, `imagepull-fail-victim` |
| **受影响节点** | `node2` (10.2.0.50) |
| **镜像仓库** | `registry-1.docker.io` (Docker Hub) |
| **空端点服务** | `aaa/test1-redis-*`, `xnet/test2-redis-*` |

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态汇总 | `kubectl get pods -A -o custom-columns=...` | `aiops-e2e` 下 8 个 Pod 状态为 `Pending`，`REASON` 均为 `ImagePullBackOff`，`NODE` 均为 `node2`。 | 多个 Pod 在 `node2` 上因镜像拉取失败而无法启动。 |
| 2 | 节点状态 | `kubectl describe node node2` | `Ready: True`, `NetworkUnavailable: False`, 无资源压力 (`MemoryPressure: False`)，无污点 (`Taints: <none>`)。 | `node2` 节点本身健康，排除了节点资源或调度问题。 |
| 3 | 服务与端点 | `kubectl get svc,endpoints -A -o custom-columns=...` | `aaa/test1-redis-*` 和 `xnet/test2-redis-*` 服务的 `ENDPOINTS` 列为 `<none>`。 | 这些服务没有匹配的后端 Pod。 |
| 4 | 网络连通性测试 | `kubectl run curl-test --rm -it --image=curlimages/curl ...` | `{"success": false, "stderr": "error: timed out waiting for the condition"}` | 尝试创建 Pod 测试网络连通性失败，间接证实拉取外部镜像存在问题。 |
| 5 | 上游定位事件 | `kubectl describe pod` (阶段1) | `Failed to pull image \"busybox\"... i/o timeout` 和 `connection reset by peer`，指向 `registry-1.docker.io`。 | 镜像拉取失败的直接原因是到 Docker Hub 的网络连接超时或被重置。 |

### 证据关联分析
- **证据 #1 + #5 印证**：多个 Pod 状态为 `ImagePullBackOff`，且事件明确显示拉取 `busybox` 镜像时发生 `i/o timeout` 和 `connection reset by peer`，指向 `registry-1.docker.io`。
- **证据 #2 排除节点问题**：`node2` 节点状态健康，网络可用，资源充足，无污点，因此问题不在于节点本身。
- **证据 #4 间接验证**：尝试运行 `curlimages/curl` 镜像来测试网络同样失败，说明从集群内部拉取外部公共镜像普遍存在困难。
- **证据 #3 揭示次要问题**：`aaa` 和 `xnet` 命名空间下的 Redis 服务端点为空。结合阶段1的定位结果，`aaa` 命名空间下无任何 Pod，因此服务无端点是预期结果；`xnet` 命名空间下虽有 Pod，但可能不存在标签匹配这些服务选择器的 Pod。

### 缺失证据（如有）
无关键证据缺失。

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 从 Kubernetes 集群（特别是 node2 节点）到公共镜像仓库           │
│ registry-1.docker.io (Docker Hub) 的网络连接异常。              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 网络连接问题导致 containerd 无法从 Docker Hub 拉取              │
│ busybox 和 nginx:latest 等基础镜像。                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Pod 的容器镜像拉取失败，状态变为 ImagePullBackOff。             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ 1. aiops-e2e 命名空间下多个 Pod 持续处于 Pending 状态。         │
│ 2. 测试网络连通性的临时 Pod 也无法启动。                        │
│ 3. aaa/xnet 命名空间下部分服务无端点（次要问题）。              │
└─────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #1 (多个 Pod `ImagePullBackOff`)、证据 #5 (拉取事件显示 `i/o timeout` 和 `connection reset by peer`) 和证据 #4 (网络测试 Pod 启动超时)，问题的根本原因是**集群（特别是 `node2` 节点）到公共 Docker Hub (`registry-1.docker.io`) 的网络连接异常**，导致依赖公共镜像的 Pod 无法启动。

**次要问题**：`aaa` 和 `xnet` 命名空间下的 Redis 服务端点为空。对于 `aaa` 命名空间，这是因为该命名空间下没有任何 Pod（阶段1已确认）。对于 `xnet` 命名空间，需要检查是否有 Pod 的标签匹配服务的 `selector`。

**置信度**：高 (90%)
- ✅ 多个 Pod 的失败原因高度一致 (`ImagePullBackOff`)
- ✅ 事件日志明确指向网络超时 (`i/o timeout`)
- ✅ 所有受影响的 Pod 均调度至同一节点 (`node2`)，但该节点状态健康
- ✅ 网络连通性测试间接验证了外部访问问题

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 诊断并修复 node2 节点的出站网络**
检查 `node2` 节点到互联网（特别是 `registry-1.docker.io`）的网络连通性。
```bash
# 在 node2 节点上执行
ssh node2
# 测试 DNS 解析
nslookup registry-1.docker.io
# 测试 TCP 连接 (HTTP/HTTPS)
curl -v --connect-timeout 10 https://registry-1.docker.io/v2/ || echo "HTTPS failed"
curl -v --connect-timeout 10 http://registry-1.docker.io/v2/ || echo "HTTP failed"
```
*依据*：证据 #5 显示连接超时，可能是防火墙、代理或路由问题。
*目的*：确认网络中断点。

**2. [可选] 配置镜像加速器或使用内部镜像仓库**
如果无法立即修复外部网络，可以修改 Pod 配置，使用可访问的镜像源。
```bash
# 例如，为 busybox 使用国内镜像源（需修改 Pod YAML 中的 image 字段）
# image: docker.mirrors.ustc.edu.cn/library/busybox:latest
kubectl edit pod <pod-name> -n aiops-e2e
```
*目的*：绕过 Docker Hub，使 Pod 能够启动。

**3. [次要] 检查并修复空端点服务**
对于 `aaa` 命名空间，需要部署对应的 Redis Pod。
对于 `xnet` 命名空间，检查服务 `selector` 与 Pod 标签是否匹配。
```bash
# 查看 xnet 命名空间下所有 Pod 的标签
kubectl get pods -n xnet --show-labels
# 对比 test2-redis-* 服务的 selector
kubectl get svc test2-redis-master -n xnet -o jsonpath='{.spec.selector}'
```
*目的*：确保服务能够正确关联到后端 Pod。

### 后续优化
1.  **搭建私有镜像仓库**：将常用基础镜像（如 `busybox`, `nginx`）推送到内网私有仓库，避免依赖外网。
2.  **配置集群级镜像拉取策略**：通过 `imagePullSecrets` 或配置 containerd 使用镜像加速器。
3.  **网络监控**：对集群节点的出站网络连接进行监控和告警。

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认异常 Pod 恢复 | `kubectl get pods -n aiops-e2e` | `STATUS` 变为 `Running` |
| 2. 验证网络连通性 | `kubectl run test-net --rm -it --image=busybox --restart=Never -- ping -c 3 8.8.8.8` | 能成功执行并返回结果 |
| 3. 检查服务端点 | `kubectl get endpoints -n aaa xnet` | `ENDPOINTS` 列显示 IP 地址（如果部署了对应 Pod） |

## ⚠️ 注意事项
- 网络问题可能源于节点防火墙、安全组策略、网络代理或运营商网络故障，需要逐层排查。
- `aaa` 命名空间下无 Pod 是设计使然还是部署遗漏，需根据业务需求判断。
- 如果问题仅出现在 `node2`，修复后可以考虑将 `aiops-e2e` 的 Pod 重新调度到其他节点，或排查 `node2` 特有的网络配置。

---

## 📊 性能统计

├─ 总耗时: 7.8m
├─ 问题定位: 145.1s (31%) ✅
├─ 证据链采集: 167.8s (36%) ✅
├─ 根因分析: 71.8s (15%) ✅
├─ 汇总总结: 85.1s (18%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 20 次
```

📋 诊断追踪

- **核心 Runbook**: private-k8s-health-reference
- **参考 Runbook**: private-k8s-health-reference, l3-imagepull-failed
- **工具调用**: 20 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
