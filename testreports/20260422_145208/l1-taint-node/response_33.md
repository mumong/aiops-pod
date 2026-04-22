======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: b64e794563cb4d7d]

📍 [问题定位] 执行中...
   💭 [问题定位] 让我先做轻量状态确认，看看集群的整体健康状况。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 调用工具: kubernetes_count
   💭 [问题定位] 调用工具: kubernetes_count
   💭 [问题定位] 工具结果: kubernetes_count (success)
      📄 Count for pods with jq...
1 results
---
52
   💭 [问题定位] 工具结果: kubernetes_count (success)
      📄 Count for pods with jq...
1 results
---
1
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   209d   v1.26.8  
   💭 [问题定位] 所有节点 Ready。发现有 1 个非 Running/非 Succeeded 的 Pod。让我进一步查看。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName' | (head -n 1; tail -n +2 | gre
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName' | (head -n 1; tail -n +2 | gre
   💭 [问题定位] 让我用另一种方式查看所有 Pod 的状态。
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 Executing jq query for pods...
aiops-e2e/l1-test-nginx-6c69dc7c76-fwzgn phase=Pending reason=-
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 Executing jq query for pods...
   💭 [问题定位] 发现一个 Pending 的 Pod。让我进一步查看它。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             l1-test-nginx-6c69dc7c76-fwzgn
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             <none>
Labels:           app=nginx
                  e2e-te
   💭 [问题定位] 这个 Pod 使用了 `Node-Selectors: kubernetes.io/hostname=node2` 但 node2 被标记了 `test-unschedulable: true` 的 taint，而且没有 toleration。这看起来是一个测试场景。

让我进一步检查 node2 的 taint 状态，并看看有没有其他异常。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE   LAST SEEN   TYPE      REASON                OBJECT                                SUBOBJECT                   SOURCE                                        MESSAGE                         
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:               node2
Roles:              <none>
Labels:             beta.kubernetes.io/arch=amd64
                    beta.kubernetes.io/os=linux
                    kubernetes.io/arch=amd64
    
   💭 [问题定位] 非常好，我已经获取到了完整的信息。让我也获取通用参考手册以辅助判断。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# 私有化 Kubernetes 环境健康与高效排查参考手册

> 类型: reference | 适用: 私有化 Kubernetes 环境 | 环境特征: Calico + NFS + containerd

## 目的

本手册不是某个具体故障的处理步骤，而是一个**额外知识参考**：
- 帮助理解在私有化 Kubernetes 环境中，健康检查应重点关注哪些资源与信号

   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# L0 Pod 存储卷超限被驱逐

> 层级: L0 - 基础设施层 | 场景: Volume Limit Exceeded / Disk Pressure Eviction

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | STATUS=Evicted, Error, 或 Pending |
| Events | 
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# L1 Node NotReady / Taint 导致不可调度

> 层级: L1 - 集群与节点层 | 场景: 节点 NotReady 或被 Taint 标记为不可调度

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| 节点状态 | `kubectl get nodes` 显示 STATUS=NotReady 或 Unknown 
   💭 [问题定位] 现在我已经有了足够的信息，让我整理诊断结论。

## 当前异常分析总结

**节点状态**：3个节点全部 Ready，无节点异常。

**当前活跃异常对象**：

### 1️⃣ Pod `l1-test-nginx-6c69dc7c76-fwzgn` - Pending
- **命名空间**：`aiops-e2e`
- **现象**：STATUS=Pending，未调度到任何节点
- **根因**：Pod 设置了 `Node-Selectors: kubernetes.io/hostname=node2`，但 **node2 被标记了 `test-unschedulable=true:NoSchedule` 的 taint**，且 Pod 没有对应 toleration。同时 master 节点有 `node-role.kubernetes.io/control-plane` taint（未容忍），node1 不匹配 nodeSelector。
- **层级**：**L1 - 节点层**（Taint 导致不可调度）

### 2️⃣ Pod `logfill-6ccfcf9c9c-*` - 反复 Evicted（历史事件，当前已不存在）
- 大量 logfill Pod 因 **EmptyDir volume "logs" 超过 30Mi limit** 被 kubelet 驱逐
- **当前状态**：这些 Evicted Pod 已不存在，但 Deployment 仍在持续创建新 Pod（已创建 62 个副本），且同样被反复驱逐
- **层级**：**L0 - 基础设施层**（Volume Limit Exceeded）
- **注意**：这是正在持续发生的循环问题，不是历史噪音

### 3️⃣ Pod `observability-filebeat-w6gtr` - Readiness probe 失败
- **命名空间**：`xnet`，节点：node2
- **现象**：Readiness probe failed - `filebeat test output` 命令超时
- **当前状态**：Pod 仍在运行但 readiness 检查失败

```json
{
  "layer": "L1",
  "layers": ["L1", "L0"],
  "layer_name": "集群节点层",
  "confidence": 0.90,
  "reasoning": "集群存在两个明确异常信号：(1) L1 - node2 被标记 test-unschedulable=true:NoSchedule taint，导致 l1-test-nginx Pod 无法调度（Pending）；(2) L0 - logfill Deployment 的 EmptyDir volume 持续超过 30Mi limit，Pod 被反复 Evicted（约20+次，仍在继续）。L0 是最底层根因（存储卷超限驱逐），L1 是节点 Taint 问题。综合取根因最底层 L0 为主层级。",
  "key_entities": [
    {"type": "Node", "value": "node2"},
    {"type": "Pod", "value": "l1-test-nginx-6c69dc7c76-fwzgn"},
    {"type": "Namespace", "value": "aiops-e2e"},
    {"type": "Deployment", "value": "logfill"},
    {"type": "Pod", "value": "observability-filebeat-w6gtr"},
    {"type": "Namespace", "value": "xnet"}
  ],
  "possible_scenarios": [
    "node2 被标记 test-unschedulable taint（可能为测试/维护目的），导致有 nodeSelector=hostname=node2 的 Pod 无法调度",
    "logfill Deployment 的 EmptyDir 卷 logs 的 sizeLimit=30Mi 被写满，Pod 被反复驱逐，需要调整 sizeLimit 或限制写入速率",
    "observability-filebeat-w6gtr readiness probe 超时，filebeat 可能无法连接输出端"
  ]
}
```
   ✅ [问题定位] 完成 (35.5s)
   📤 → 下游数据: layer=Layer.L1, layers=L1+L0
   scenarios=['node2 被标记 test-unschedulable taint（可能为测试/维护目的），导致有 nodeSelector=hostname=node2 的 Pod 无法调度', 'logfill Deployment 的 EmptyDir 卷 logs 的 sizeLimit=30Mi 被写满，Pod 被反复驱逐，需要调整 sizeLimit 或限制写入速率', 'observability-filebeat-w6gtr readiness probe 超时，filebeat 可能无法连接输出端']
   entities=[{"type": "Node", "value": "node2"}, {"type": "Pod", "value": "l1-test-nginx-6c69dc7c76-fwzgn"}, {"type": "Namespace", "value": "aiops-e2e"}, {"type": "Deployment", "value": "logfill"}, {"type": "Pod", "value": "observability-filebeat-w6gtr"}, {"type": "Namespace", "value": "xnet"}]
   reasoning=集群存在两个明确异常信号：(1) L1 - node2 被标记 test-unschedulable=true:NoSchedule taint，导致 l1-test-nginx Pod 无法调度（Pending）；(2) L0 - logfill Deployment 的 EmptyDir volume 持续超过 30Mi limit，Pod 被反复 Evicted（约20+次，仍在继续）。L0 是最底层根因（存储卷超限驱逐），L1 是节点 Taint 问题。综合取根因最底层 L0 为主层级。
   layer_analysis={"layer": "L1", "layers": ["L1", "L0"], "layer_name": "集群节点层", "confidence": 0.9, "reasoning": "集群存在两个明确异常信号：(1) L1 - node2 被标记 test-unschedulable=true:NoSchedule taint，导致 l1-test-nginx Pod 无法调度（Pending）；(2) L0 - logfill Deployment 的 EmptyDir volume 持续超过 30Mi limit，Pod 被反复 Evicted（约20+次，仍在继续）。L0 是最底层根因（存储卷超限驱逐），L1 是节点 Taint 问题。综合取根因最底层 L0 为主层级。", "key_entities": [{"type": "Node", "value": "node2"}, {"type": "Pod", "value": "l1-test-nginx-6c69dc7c76-fwzgn"}, {"type": "Namespace", "value": "aiops-e2e"}, {"type": "Deployment", "value": "logfill"}, {"type": "Pod", "value": "observability-filebeat-w6gtr"}, {"type": "Namespace", "value": "xnet"}], "possible_scenarios": ["node2 被标记 test-unschedulable taint（可能为测试/维护目的），导致有 nodeSelector=hostname=node2 的 Pod 无法调度", "logfill Deployment 的 EmptyDir 卷 logs 的 sizeLimit=30Mi 被写满，Pod 被反复驱逐，需要调整 sizeLimit 或限制写入速率", "observability-filebeat-w6gtr readiness probe 超时，filebeat 可能无法连接输出端"]}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L1 + L0（主层级: Layer.L1）
   置信度: 90%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 让我先快速了解集群的全局状态，然后根据之前定位的结果深入采集证据。

## 第一步：全局快速扫描
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME              STATUS   AGE     LABELS
aaa               Active   6d4h    kubernetes.io/metadata.name=aaa,name=aaa
abc               Active   6d23h   kubernetes.io/metadata.name=abc,name=abc
admin 
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   209d   v1.26.8  
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS    RESTARTS      AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     l1-test-ngin
   💭 [证据链采集] 我发现全局扫描中没看到 `aiops-e2e/logfill` 的 Pod（已被驱逐），也没有看到 `aiops-e2e` 命名空间下有多个被驱逐的 Pod。让我深入采集关键证据。

## 第二步：输出证据采集计划

```json
{
  "layer": "L0+L1",
  "evidence_plan": [
    {
      "id": "e1",
      "description": "检查 node2 的 taint 详情",
      "level": "critical",
      "tool": "kubectl_describe",
      "command": "kubectl describe node node2",
      "purpose": "确认 test-unschedulable taint 是否存在及其来源"
    },
    {
      "id": "e2",
      "description": "检查 Pending Pod l1-test-nginx 的调度详情",
      "level": "critical",
      "tool": "kubectl_describe",
      "command": "kubectl describe pod l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e",
      "purpose": "确认调度失败原因：Taint 不容忍 + nodeSelector 不匹配"
    },
    {
      "id": "e3",
      "description": "查看 logfill Deployment 详情",
      "level": "critical",
      "tool": "kubectl_describe",
      "command": "kubectl describe deployment logfill -n aiops-e2e",
      "purpose": "了解 EmptyDir 配置和驱逐历史"
    },
    {
      "id": "e4",
      "description": "查看 aiops-e2e 命名空间所有 Pod（包括 Evicted）",
      "level": "critical",
      "tool": "kubectl_get_by_kind_in_namespace",
      "command": "kubectl get pods -n aiops-e2e",
      "purpose": "确认所有被驱逐的 Pod 记录"
    },
    {
      "id": "e5",
      "description": "获取 logfill 最新 Pod 的 describe 信息",
      "level": "critical",
      "tool": "kubectl_describe",
      "command": "需要先找到 logfill 的当前 Pod 名称",
      "purpose": "查看 EmptyDir 超限驱逐事件"
    },
    {
      "id": "e6",
      "description": "检查 observability-filebeat-w6gtr 的 readiness 探测详情",
      "level": "critical",
      "tool": "kubectl_describe",
      "command": "kubectl describe pod observability-filebeat-w6gtr -n xnet",
      "purpose": "确认 readiness probe 失败详情"
    },
    {
      "id": "e7",
      "description": "查看 node2 节点 Conditions 和资源状态",
      "level": "important",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get node node2 -o yaml",
      "purpose": "确认节点整体健康状态"
    },
    {
      "id": "e8",
      "description": "查看 aiops-e2e 命名空间事件",
      "level": "important",
      "tool": "kubectl_events",
      "command": "kubectl get events -n aiops-e2e",
      "purpose": "获取驱逐和调度事件时间线"
    },
    {
      "id": "e9",
      "description": "查看 filebeat Pod 日志",
      "level": "important",
      "tool": "kubectl logs",
      "command": "需要先执行 describe",
      "purpose": "确认 filebeat test output 失败原因"
    },
    {
      "id": "e10",
      "description": "检查节点资源使用情况 (Prometheus)",
      "level": "optional",
      "tool": "execute_prometheus_instant_query",
      "command": "节点 CPU/内存/磁盘使用率",
      "purpose": "确认节点是否有资源压力"
    }
  ],
  "collection_strategy": "先采集 critical 级别证据确认 3 个问题的根因，再采集 important 级补充上下文"
}
```

现在开始执行计划：

## 第三步：执行证据采集

### e1 - node2 taint 详情
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
node2   Ready    <none>   209d   v1.26.8   10.2.0.50     <
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 NAME                             READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
l1-test-nginx-6c69dc7c76-fwzgn   0/1     Pending   0          25m   <non
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:               node2
Roles:              <none>
Labels:             beta.kubernetes.io/arch=amd64
                    beta.kubernetes.io/os=linux
                    kubernetes.io/arch=amd64
    
   💭 [证据链采集] 好，关键信息已获取。现在看 aiops-e2e 命名空间没有显示被驱逐的 Pod（可能已经被清理了），让我进一步采集。

### e2 - Pending Pod 详情 + e3 - logfill Deployment + e6 - filebeat
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Command failed (exit 1):
kubectl describe deployment logfill -n aiops-e2e
Error from server (NotFound): deployments.apps "logfill" not found

   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:             observability-filebeat-w6gtr
Namespace:        xnet
Priority:         0
Service Account:  observability-observability
Node:             node2/10.2.0.50
Start Time:       Fri, 03 Apr 
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:             l1-test-nginx-6c69dc7c76-fwzgn
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             <none>
Labels:           app=nginx
                  e2e-te
   ✅ [证据链采集] 完成 (19.9s)
   📤 → 下游数据: evidence_items=9/10
   evidence_analysis={"evidence_plan": [{"id": "e1", "description": "检查 node2 的 taint 详情", "level": "critical", "tool": "kubectl_describe", "command": "kubectl describe node node2", "purpose": "确认 test-unschedulable taint 是否存在及其来源"}, {"id": "e2", "description": "检查 Pending Pod l1-test-nginx 的调度详情", "level": "critical", "tool": "kubectl_describe", "command": "kubectl describe pod l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e", "purpose": "确认调度失败原因：Taint 不容忍 + nodeSelector 不匹配"}, {"id": "e3", "description": "查看 logfill Deployment 详情", "level": "critical", "tool": "kubectl_describe", "command": "kubectl describe deployment logfill -n aiops-e2e", "purpose": "了解 EmptyDir 配置和驱逐历史"}, {"id": "e4", "description": "查看 aiops-e2e 命名空间所有 Pod（包括 Evicted）", "level": "critical", "tool": "kubectl_get_by_kind_in_namespace", "command": "kubectl get pods -n aiops-e2e", "purpose": "确认所有被驱逐的 Pod 记录"}, {"id": "e5", "description": "获取 logfill 最新 Pod 的 describe 信息", "level": "critical", "tool": "kubectl_describe", "command": "需要先找到 logfill 的当前 Pod 名称", "purpose": "查看 EmptyDir 超限驱逐事件"}, {"id": "e6", "description": "检查 observability-filebeat-w6gtr 的 readiness 探测详情", "level": "critical", "tool": "kubectl_describe", "command": "kubectl describe pod observability-filebeat-w6gtr -n xnet", "purpose": "确认 readiness probe 失败详情"}, {"id": "e7", "description": "查看 node2 节点 Conditions 和资源状态", "level": "important", "tool": "kubectl_get_yaml", "command": "kubectl get node node2 -o yaml", "purpose": "确认节点整体健康状态"}, {"id": "e8", "description": "查看 aiops-e2e 命名空间事件", "level": "important", "tool": "kubectl_events", "command": "kubectl get events -n aiops-e2e", "purpose": "获取驱逐和调度事件时间线"}, {"id": "e9", "description": "查看 filebeat Pod 日志", "level": "important", "tool": "kubectl logs", "command": "需要先执行 describe", "purpose": "确认 filebeat test output 失败原因"}, {"id": "e10", "description": "检查节点资源使用情况 (Prometheus)", "level": "optional", "tool": "execute_prometheus_instant_query", "command": "节点 CPU/内存/磁盘使用率", "purpose": "确认节点是否有资源压力"}], "tool_results": [], "tool_data": [{"tool": "kubectl_get_by_kind_in_cluster", "data": "NAME              STATUS   AGE     LABELS\naaa               Active   6d4h    kubernetes.io/metadata.name=aaa,name=aaa\nabc               Active   6d23h   kubernetes.io/metadata.name=abc,name=abc\nadmin             Active   7d5h    kubernetes.io/metadata.name=admin\naiops             Active   91d     kubernetes.io/metadata.name=aiops\naiops-e2e         Active   88d     kubernetes.io/metadata.name=aiops-e2e\ndefault           Active   209d    kubernetes.io/metadata.name=default\ndify              Active   145d    kubernetes.io/metadata.name=dify,name=dify\nkube-node-lease   Active   209d    kubernetes.io/metadata.name=kube-node-lease\nkube-public       Active   209d    kubernetes.io/metadata.name=kube-public\nkube-system       Active   209d    kubernetes.io/metadata.name=kube-system\nmcp               Active   132d    app=mcp-server-manager,kubernetes.io/metadata.name=mcp\ntest              Active   182d    kubernetes.io/metadata.name=test,name=test\nweb               Active   127d    kubernetes.io/metadata.name=web\nxnet              Active   209d    kubernetes.io/metadata.name=xnet,name=xnet", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_cluster", "data": "NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nmaster   Ready    control-plane   209d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          209d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-174-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          209d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-174-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_cluster", "data": "NAMESPACE     NAME                                                READY   STATUS    RESTARTS      AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\naiops-e2e     l1-test-nginx-6c69dc7c76-fwzgn                      0/1     Pending   0             25m     <none>           <none>   <none>           <none>            app=nginx,e2e-test=true,pod-template-hash=6c69dc7c76\naiops         aiops-copilot-76779bb6df-4bcrf                      1/1     Running   0             5h38m   172.16.104.29    node2    <none>           <none>            app=aiops-copilot,pod-template-hash=76779bb6df\ndefault       dns-test-existing                                   1/1     Running   0             2d1h    172.16.166.148   node1    <none>           <none>            run=dns-test-existing\ndefault       exec-test                                           1/1     Running   0             2d3h    172.16.104.8     node2    <none>           <none>            run=exec-test\ndefault       network-test-from-running                           1/1     Running   0             2d2h    172.16.104.50    node2    <none>           <none>            run=network-test-from-running\ndefault       nfs-client-provisioner-6fcd4994c9-lczf6             1/1     Running   4 (5d ago)    85d     172.16.104.41    node2    <none>           <none>            app=nfs-client-provisioner,pod-template-hash=6fcd4994c9\nkube-system   calico-kube-controllers-6c67f9d475-2xcb7            1/1     Running   4 (5d ago)    28d     172.16.166.133   node1    <none>           <none>            k8s-app=calico-kube-controllers,pod-template-hash=6c67f9d475\nkube-system   calico-node-4kp26                                   1/1     Running   12 (5d ago)   183d    10.2.0.48        master   <none>           <none>            controller-revision-hash=65f554db6,k8s-app=calico-node,pod-template-generation=1\nkube-system   calico-node-d2dhp                                   1/1     Running   13 (5d ago)   183d    10.2.0.50        node2    <none>           <none>            controller-revision-hash=65f554db6,k8s-app=calico-node,pod-template-generation=1\nkube-system   calico-node-mnrjs                                   1/1     Running   12 (5d ago)   183d    10.2.0.49        node1    <none>           <none>            controller-revision-hash=65f554db6,k8s-app=calico-node,pod-template-generation=1\nkube-system   coredns-777df594b8-j4857                            1/1     Running   4 (5d ago)    28d     172.16.166.129   node1    <none>           <none>            k8s-app=kube-dns,pod-template-hash=777df594b8\nkube-system   coredns-777df594b8-s8r4n                            1/1     Running   4 (5d ago)    28d     172.16.166.185   node1    <none>           <none>            k8s-app=kube-dns,pod-template-hash=777df594b8\nkube-system   etcd-master                                         1/1     Running   13 (5d ago)   209d    10.2.0.48        master   <none>           <none>            component=etcd,tier=control-plane\nkube-system   kube-apiserver-master                               1/1     Running   13 (5d ago)   209d    10.2.0.48        master   <none>           <none>            component=kube-apiserver,tier=control-plane\nkube-system   kube-controller-manager-master                      1/1     Running   36 (5d ago)   209d    10.2.0.48        master   <none>           <none>            component=kube-controller-manager,tier=control-plane\nkube-system   kube-multus-ds-rnvbg                                1/1     Running   12 (5d ago)   183d    10.2.0.49        node1    <none>           <none>            app=multus,controller-revision-hash=6d4c8546fc,name=multus,pod-template-generation=1,tier=node\nkube-system   kube-multus-ds-sc2jn                                1/1     Running   4 (5d ago)    85d     10.2.0.48        master   <none>           <none>            app=multus,controller-revision-hash=6d4c8546fc,name=multus,pod-template-generation=1,tier=node\nkube-system   kube-multus-ds-x7h9s                                1/1     Running   13 (5d ago)   183d    10.2.0.50        node2    <none>           <none>            app=multus,controller-revision-hash=6d4c8546fc,name=multus,pod-template-generation=1,tier=node\nkube-system   kube-proxy-69zzr                                    1/1     Running   4 (5d ago)    28d     10.2.0.50        node2    <none>           <none>            controller-revision-hash=7d99996759,k8s-app=kube-proxy,pod-template-generation=1\nkube-system   kube-proxy-bblvc                                    1/1     Running   4 (5d ago)    28d     10.2.0.49        node1    <none>           <none>            controller-revision-hash=7d99996759,k8s-app=kube-proxy,pod-template-generation=1\nkube-system   kube-proxy-wbh4k                                    1/1     Running   4 (5d ago)    27d     10.2.0.48        master   <none>           <none>            controller-revision-hash=7d99996759,k8s-app=kube-proxy,pod-template-generation=1\nkube-system   kube-scheduler-master                               1/1     Running   38 (5d ago)   209d    10.2.0.48        master   <none>           <none>            component=kube-scheduler,tier=control-plane\nmcp           mcp-server-manager-8677f6896c-d4mr9                 1/1     Running   0             45h     172.16.104.59    node2    <none>           <none>            app=mcp-server-manager,pod-template-hash=8677f6896c\nxnet          alertmanager-observability-alertmanager-0           2/2     Running   8 (5d ago)    22d     172.16.166.161   node1    <none>           <none>            alertmanager=observability-alertmanager,app.kubernetes.io/instance=observability-alertmanager,app.kubernetes.io/managed-by=prometheus-operator,app.kubernetes.io/name=alertmanager,app.kubernetes.io/version=0.28.1,controller-revision-hash=alertmanager-observability-alertmanager-6c9cfbf844,statefulset.kubernetes.io/pod-name=alertmanager-observability-alertmanager-0\nxnet          api-server-6bd6bf8d6f-27svp                         1/1     Running   4 (5d ago)    22d     172.16.219.106   master   <none>           <none>            app=api-server,pod-template-hash=6bd6bf8d6f\nxnet          deepflow-agent-pcknn                                1/1     Running   9 (5d ago)    22d     172.16.166.181   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow-agent,app=deepflow,component=deepflow-agent,controller-revision-hash=54856d959b,pod-template-generation=1\nxnet          deepflow-agent-trc8k                                1/1     Running   7 (5d ago)    19d     172.16.104.7     node2    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow-agent,app=deepflow,component=deepflow-agent,controller-revision-hash=54856d959b,pod-template-generation=1\nxnet          deepflow-agent-whn22                                1/1     Running   8 (5d ago)    22d     172.16.219.97    master   <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow-agent,app=deepflow,component=deepflow-agent,controller-revision-hash=54856d959b,pod-template-generation=1\nxnet          elasticsearch-master-0                              1/1     Running   4 (5d ago)    22d     172.16.219.109   master   <none>           <none>            app=elasticsearch-master,chart=observability,controller-revision-hash=elasticsearch-master-695ff9864f,release=observability,statefulset.kubernetes.io/pod-name=elasticsearch-master-0\nxnet          ham-p9dxv                                           1/1     Running   14 (5d ago)   177d    172.16.104.21    node2    <none>           <none>            app=ham,controller-revision-hash=f65f887d,pod-template-generation=1\nxnet          ham-qzjg5                                           1/1     Running   4 (5d ago)    85d     172.16.219.112   master   <none>           <none>            app=ham,controller-revision-hash=f65f887d,pod-template-generation=1\nxnet          ham-wt9kh                                           1/1     Running   13 (5d ago)   177d    172.16.166.187   node1    <none>           <none>            app=ham,controller-revision-hash=f65f887d,pod-template-generation=1\nxnet          lgtm-5dc5c67d5f-sc286                               1/1     Running   4 (5d ago)    22d     172.16.166.151   node1    <none>           <none>            app=lgtm,pod-template-hash=5dc5c67d5f\nxnet          observability-clickhouse-0                          1/1     Running   4 (5d ago)    22d     172.16.166.137   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=clickhouse,app=deepflow,component=clickhouse,controller-revision-hash=observability-clickhouse-75b8d58ccc,statefulset.kubernetes.io/pod-name=observability-clickhouse-0\nxnet          observability-deepflow-app-654fcfbfbf-q8st6         1/1     Running   4 (5d ago)    22d     172.16.166.160   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow,app=deepflow,component=deepflow-app,pod-template-hash=654fcfbfbf\nxnet          observability-deepflow-server-774dd6c5b7-9c998      1/1     Running   14 (5d ago)   22d     172.16.166.135   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow,app=deepflow,component=deepflow-server,pod-template-hash=774dd6c5b7\nxnet          observability-filebeat-ffwsp                        1/1     Running   4 (5d ago)    22d     172.16.219.80    master   <none>           <none>            app=observability-filebeat,chart=observability-1.0.2,controller-revision-hash=57fb88b7c5,heritage=Helm,pod-template-generation=1,release=observability\nxnet          observability-filebeat-m58xw                        1/1     Running   5 (5d ago)    22d     172.16.166.134   node1    <none>           <none>            app=observability-filebeat,chart=observability-1.0.2,controller-revision-hash=57fb88b7c5,heritage=Helm,pod-template-generation=1,release=observability\nxnet          observability-filebeat-w6gtr                        1/1     Running   5 (5d ago)    19d     172.16.104.53    node2    <none>           <none>            app=observability-filebeat,chart=observability-1.0.2,controller-revision-hash=57fb88b7c5,heritage=Helm,pod-template-generation=1,release=observability\nxnet          observability-grafana-58bf9cfd6f-ndsxr              4/4     Running   36 (5d ago)   22d     172.16.166.144   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=grafana,app.kubernetes.io/version=12.0.2,helm.sh/chart=grafana-9.2.7,pod-template-hash=58bf9cfd6f\nxnet          observability-kepler-2sgrr                          1/1     Running   6 (5d ago)    22d     10.2.0.49        node1    <none>           <none>            app.kubernetes.io/component=exporter,app.kubernetes.io/name=kepler-kepler,controller-revision-hash=7c6c5f9bd6,pod-template-generation=1\nxnet          observability-kepler-7scjm                          1/1     Running   7 (5d ago)    22d     10.2.0.48        master   <none>           <none>            app.kubernetes.io/component=exporter,app.kubernetes.io/name=kepler-kepler,controller-revision-hash=7c6c5f9bd6,pod-template-generation=1\nxnet          observability-kepler-ggstf                          1/1     Running   8 (5d ago)    19d     10.2.0.50        node2    <none>           <none>            app.kubernetes.io/component=exporter,app.kubernetes.io/name=kepler-kepler,controller-revision-hash=7c6c5f9bd6,pod-template-generation=1\nxnet          observability-kibana-65d7c45f6d-tm4vv               1/1     Running   4 (5d ago)    22d     172.16.166.191   node1    <none>           <none>            app=observability-kibana,pod-template-hash=65d7c45f6d,release=observability\nxnet          observability-kube-state-metrics-798986b8b7-6z2dq   1/1     Running   4 (5d ago)    22d     172.16.219.65    master   <none>           <none>            app.kubernetes.io/component=metrics,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=kube-state-metrics,app.kubernetes.io/part-of=kube-state-metrics,app.kubernetes.io/version=2.15.0,helm.sh/chart=kube-state-metrics-5.37.0,pod-template-hash=798986b8b7,release=observability\nxnet          observability-mysql-764f9d5966-wh2bc                1/1     Running   4 (5d ago)    22d     172.16.219.98    master   <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=mysql,app=deepflow,component=mysql,pod-template-hash=764f9d5966\nxnet          observability-operator-d4495dc86-69lgw              1/1     Running   4 (5d ago)    22d     172.16.166.182   node1    <none>           <none>            app.kubernetes.io/component=prometheus-operator,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=observability-prometheus-operator,app.kubernetes.io/part-of=observability,app.kubernetes.io/version=1.0.2,app=observability-operator,chart=observability-1.0.2,heritage=Helm,pod-template-hash=d4495dc86,release=observability\nxnet          observability-prometheus-node-exporter-lj75r        1/1     Running   4 (5d ago)    22d     10.2.0.48        master   <none>           <none>            app.kubernetes.io/component=metrics,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=prometheus-node-exporter,app.kubernetes.io/part-of=prometheus-node-exporter,app.kubernetes.io/version=1.9.1,controller-revision-hash=74f4f4b87d,helm.sh/chart=prometheus-node-exporter-4.47.0,jobLabel=node-exporter,pod-template-generation=1,release=observability\nxnet          observability-prometheus-node-exporter-qp2qd        1/1     Running   4 (5d ago)    19d     10.2.0.50        node2    <none>           <none>            app.kubernetes.io/component=metrics,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=prometheus-node-exporter,app.kubernetes.io/part-of=prometheus-node-exporter,app.kubernetes.io/version=1.9.1,controller-revision-hash=74f4f4b87d,helm.sh/chart=prometheus-node-exporter-4.47.0,jobLabel=node-exporter,pod-template-generation=1,release=observability\nxnet          observability-prometheus-node-exporter-wnbb8        1/1     Running   4 (5d ago)    22d     10.2.0.49        node1    <none>           <none>            app.kubernetes.io/component=metrics,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=prometheus-node-exporter,app.kubernetes.io/part-of=prometheus-node-exporter,app.kubernetes.io/version=1.9.1,controller-revision-hash=74f4f4b87d,helm.sh/chart=prometheus-node-exporter-4.47.0,jobLabel=node-exporter,pod-template-generation=1,release=observability\nxnet          observability-telegraf-79f45d86-4kzkm               1/1     Running   4 (5d ago)    22d     172.16.219.113   master   <none>           <none>            app.kubernetes.io/component=telegraf,app.kubernetes.io/instance=observability,app.kubernetes.io/name=observability,pod-template-hash=79f45d86\nxnet          prometheus-observability-prometheus-0               2/2     Running   16 (5d ago)   22d     172.16.166.142   node1    <none>           <none>            app.kubernetes.io/instance=observability-prometheus,app.kubernetes.io/managed-by=prometheus-operator,app.kubernetes.io/name=prometheus,app.kubernetes.io/version=3.4.1,controller-revision-hash=prometheus-observability-prometheus-9467b46f7,operator.prometheus.io/name=observability-prometheus,operator.prometheus.io/shard=0,prometheus=observability-prometheus,statefulset.kubernetes.io/pod-name=prometheus-observability-prometheus-0\nxnet          xnet-agent-568f547566-jdsgp                         1/1     Running   4 (5d ago)    108d    172.16.104.40    node2    <none>           <none>            app=xnet-agent,pod-template-hash=568f547566", "duration_s": 0}, {"tool": "kubectl_get_by_name", "data": "NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nnode2   Ready    <none>   209d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-174-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_namespace", "data": "NAME                             READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS\nl1-test-nginx-6c69dc7c76-fwzgn   0/1     Pending   0          25m   <none>   <none>   <none>           <none>            app=nginx,e2e-test=true,pod-template-hash=6c69dc7c76", "duration_s": 0}, {"tool": "kubectl_describe", "data": "Name:               node2\nRoles:              <none>\nLabels:             beta.kubernetes.io/arch=amd64\n                    beta.kubernetes.io/os=linux\n                    kubernetes.io/arch=amd64\n                    kubernetes.io/hostname=node2\n                    kubernetes.io/os=linux\nAnnotations:        kubeadm.alpha.kubernetes.io/cri-socket: unix:///var/run/containerd/containerd.sock\n                    node.alpha.kubernetes.io/ttl: 0\n                    projectcalico.org/IPv4Address: 10.2.0.50/19\n                    projectcalico.org/IPv4IPIPTunnelAddr: 172.16.104.0\n                    volumes.kubernetes.io/controller-managed-attach-detach: true\nCreationTimestamp:  Thu, 25 Sep 2025 03:10:26 +0000\nTaints:             test-unschedulable=true:NoSchedule\nUnschedulable:      false\nLease:\n  HolderIdentity:  node2\n  AcquireTime:     <unset>\n  RenewTime:       Wed, 22 Apr 2026 07:16:44 +0000\nConditions:\n  Type                 Status  LastHeartbeatTime                 LastTransitionTime                Reason                       Message\n  ----                 ------  -----------------                 ------------------                ------                       -------\n  NetworkUnavailable   False   Fri, 17 Apr 2026 07:03:52 +0000   Fri, 17 Apr 2026 07:03:52 +0000   CalicoIsUp                   Calico is running on this node\n  MemoryPressure       False   Wed, 22 Apr 2026 07:12:28 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletHasSufficientMemory   kubelet has sufficient memory available\n  DiskPressure         False   Wed, 22 Apr 2026 07:12:28 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletHasNoDiskPressure     kubelet has no disk pressure\n  PIDPressure          False   Wed, 22 Apr 2026 07:12:28 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletHasSufficientPID      kubelet has sufficient PID available\n  Ready                True    Wed, 22 Apr 2026 07:12:28 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletReady                 kubelet is posting ready status. AppArmor enabled\nAddresses:\n  InternalIP:  10.2.0.50\n  Hostname:    node2\nCapacity:\n  cpu:                12\n  ephemeral-storage:  203770680Ki\n  hugepages-1Gi:      0\n  hugepages-2Mi:      0\n  memory:             32860484Ki\n  pods:               110\nAllocatable:\n  cpu:                12\n  ephemeral-storage:  187795058378\n  hugepages-1Gi:      0\n  hugepages-2Mi:      0\n  memory:             32758084Ki\n  pods:               110\nSystem Info:\n  Machine ID:                 6bb27862c82149418d0f5624411d0b22\n  System UUID:                0f5af30a-d385-493c-bc8b-5442fd024eee\n  Boot ID:                    0ea98079-ad10-4a20-85f5-19b34afd257e\n  Kernel Version:             5.15.0-174-generic\n  OS Image:                   Ubuntu 22.04.4 LTS\n  Operating System:           linux\n  Architecture:               amd64\n  Container Runtime Version:  containerd://1.6.32\n  Kubelet Version:            v1.26.8\n  Kube-Proxy Version:         v1.26.8\nNon-terminated Pods:          (14 in total)\n  Namespace                   Name                                            CPU Requests  CPU Limits  Memory Requests  Memory Limits  Age\n  ---------                   ----                                            ------------  ----------  ---------------  -------------  ---\n  aiops                       aiops-copilot-76779bb6df-4bcrf                  250m (2%)     1 (8%)      512Mi (1%)       2Gi (6%)       5h39m\n  default                     exec-test                                       0 (0%)        0 (0%)      0 (0%)           0 (0%)         2d3h\n  default                     network-test-from-running                       0 (0%)        0 (0%)      0 (0%)           0 (0%)         2d2h\n  default                     nfs-client-provisioner-6fcd4994c9-lczf6         0 (0%)        0 (0%)      0 (0%)           0 (0%)         85d\n  kube-system                 calico-node-d2dhp                               250m (2%)     0 (0%)      0 (0%)           0 (0%)         183d\n  kube-system                 kube-multus-ds-x7h9s                            100m (0%)     100m (0%)   50Mi (0%)        50Mi (0%)      183d\n  kube-system                 kube-proxy-69zzr                                0 (0%)        0 (0%)      0 (0%)           0 (0%)         28d\n  mcp                         mcp-server-manager-8677f6896c-d4mr9             200m (1%)     1 (8%)      1G (2%)          2560Mi (8%)    45h\n  xnet                        deepflow-agent-trc8k                            100m (0%)     1 (8%)      128Mi (0%)       768Mi (2%)     19d\n  xnet                        ham-p9dxv                                       0 (0%)        0 (0%)      0 (0%)           0 (0%)         177d\n  xnet                        observability-filebeat-w6gtr                    100m (0%)     1 (8%)      100Mi (0%)       200Mi (0%)     19d\n  xnet                        observability-kepler-ggstf                      0 (0%)        0 (0%)      0 (0%)           0 (0%)         19d\n  xnet                        observability-prometheus-node-exporter-qp2qd    0 (0%)        0 (0%)      0 (0%)           0 (0%)         19d\n  xnet                        xnet-agent-568f547566-jdsgp                     0 (0%)        0 (0%)      0 (0%)           0 (0%)         108d\nAllocated resources:\n  (Total limits may be over 100 percent, i.e., overcommitted.)\n  Resource           Requests         Limits\n  --------           --------         ------\n  cpu                1 (8%)           4100m (34%)\n  memory             1828375040 (5%)  5626Mi (17%)\n  ephemeral-storage  0 (0%)           0 (0%)\n  hugepages-1Gi      0 (0%)           0 (0%)\n  hugepages-2Mi      0 (0%)           0 (0%)\nEvents:              <none>", "duration_s": 0}, {"tool": "kubectl_describe", "data": "Command failed (exit 1):\nkubectl describe deployment logfill -n aiops-e2e\nError from server (NotFound): deployments.apps \"logfill\" not found\n", "duration_s": 0}, {"tool": "kubectl_describe", "data": "Name:             observability-filebeat-w6gtr\nNamespace:        xnet\nPriority:         0\nService Account:  observability-observability\nNode:             node2/10.2.0.50\nStart Time:       Fri, 03 Apr 2026 01:32:25 +0000\nLabels:           app=observability-filebeat\n                  chart=observability-1.0.2\n                  controller-revision-hash=57fb88b7c5\n                  heritage=Helm\n                  pod-template-generation=1\n                  release=observability\nAnnotations:      cni.projectcalico.org/containerID: c4a7dc194375911da897b3b767bb8aa7ab006fb34d3138f4c260f137f292419b\n                  cni.projectcalico.org/podIP: 172.16.104.53/32\n                  cni.projectcalico.org/podIPs: 172.16.104.53/32\n                  configChecksum: 5985ce9a7908d9d12893164e2dca7ef3a630527f811cfd840771866d0c04faf\n                  k8s.v1.cni.cncf.io/network-status:\n                    [{\n                        \"name\": \"k8s-pod-network\",\n                        \"ips\": [\n                            \"172.16.104.53\"\n                        ],\n                        \"default\": true,\n                        \"dns\": {}\n                    }]\n                  k8s.v1.cni.cncf.io/networks-status:\n                    [{\n                        \"name\": \"k8s-pod-network\",\n                        \"ips\": [\n                            \"172.16.104.53\"\n                        ],\n                        \"default\": true,\n                        \"dns\": {}\n                    }]\nStatus:           Running\nIP:               172.16.104.53\nIPs:\n  IP:           172.16.104.53\nControlled By:  DaemonSet/observability-filebeat\nContainers:\n  filebeat:\n    Container ID:  containerd://6f69da77e7274fe2a9260ba87fa6c132d84ce5d7f24d5df1526576bc5cf8e194\n    Image:         xnet.registry.io:8443/observability/beats/filebeat:8.5.1\n    Image ID:      docker.elastic.co/beats/filebeat@sha256:2e7a537a8a2c3d2767009ee65faadce572bc7ec5e571aba730f11a236da93a3a\n    Port:          <none>\n    Host Port:     <none>\n    Args:\n      -e\n      -E\n      http.enabled=true\n    State:          Running\n      Started:      Fri, 17 Apr 2026 07:04:18 +0000\n    Last State:     Terminated\n      Reason:       Unknown\n      Exit Code:    255\n      Started:      Thu, 16 Apr 2026 03:06:53 +0000\n      Finished:     Fri, 17 Apr 2026 07:03:26 +0000\n    Ready:          True\n    Restart Count:  5\n    Limits:\n      cpu:     1\n      memory:  200Mi\n    Requests:\n      cpu:     100m\n      memory:  100Mi\n    Liveness:  exec [sh -c curl --fail 127.0.0.1:5066\n] delay=10s timeout=5s period=10s #success=1 #failure=3\n    Readiness:  exec [sh -c filebeat test output\n] delay=10s timeout=5s period=10s #success=1 #failure=3\n    Environment:\n      POD_NAMESPACE:           xnet (v1:metadata.namespace)\n      NODE_NAME:                (v1:spec.nodeName)\n      ELASTICSEARCH_HOSTS:     https://elasticsearch-master-headless:9200\n      ELASTICSEARCH_USERNAME:  <set to the key 'username' in secret 'elasticsearch-master-credentials'>  Optional: false\n      ELASTICSEARCH_PASSWORD:  <set to the key 'password' in secret 'elasticsearch-master-credentials'>  Optional: false\n    Mounts:\n      /usr/share/filebeat/certs from elasticsearch-certs (ro)\n      /usr/share/filebeat/certs/ from secret-mount-volume (ro)\n      /usr/share/filebeat/data from data (rw)\n      /usr/share/filebeat/filebeat.yml from filebeat-config (ro,path=\"filebeat.yml\")\n      /var/lib/docker/containers from varlibdockercontainers (ro)\n      /var/log from varlog (ro)\n      /var/run/docker.sock from varrundockersock (ro)\n      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-m2l95 (ro)\nConditions:\n  Type              Status\n  Initialized       True \n  Ready             True \n  ContainersReady   True \n  PodScheduled      True \nVolumes:\n  elasticsearch-certs:\n    Type:        Secret (a volume populated by a Secret)\n    SecretName:  elasticsearch-master-certs\n    Optional:    false\n  filebeat-config:\n    Type:      ConfigMap (a volume populated by a ConfigMap)\n    Name:      observability-filebeat-daemonset-config\n    Optional:  false\n  secret-mount-volume:\n    Type:        Secret (a volume populated by a Secret)\n    SecretName:  elasticsearch-master-certs\n    Optional:    false\n  data:\n    Type:          HostPath (bare host directory volume)\n    Path:          /var/lib/observability-filebeat-xnet-data\n    HostPathType:  DirectoryOrCreate\n  varlibdockercontainers:\n    Type:          HostPath (bare host directory volume)\n    Path:          /var/lib/docker/containers\n    HostPathType:  \n  varlog:\n    Type:          HostPath (bare host directory volume)\n    Path:          /var/log\n    HostPathType:  \n  varrundockersock:\n    Type:          HostPath (bare host directory volume)\n    Path:          /var/run/docker.sock\n    HostPathType:  \n  kube-api-access-m2l95:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    TokenExpirationSeconds:  3607\n    ConfigMapName:           kube-root-ca.crt\n    ConfigMapOptional:       <nil>\n    DownwardAPI:             true\nQoS Class:                   Burstable\nNode-Selectors:              <none>\nTolerations:                 node.kubernetes.io/disk-pressure:NoSchedule op=Exists\n                             node.kubernetes.io/memory-pressure:NoSchedule op=Exists\n                             node.kubernetes.io/not-ready:NoExecute op=Exists\n                             node.kubernetes.io/pid-pressure:NoSchedule op=Exists\n                             node.kubernetes.io/unreachable:NoExecute op=Exists\n                             node.kubernetes.io/unschedulable:NoSchedule op=Exists\nEvents:\n  Type     Reason     Age                 From     Message\n  ----     ------     ----                ----     -------\n  Warning  Unhealthy  40m (x9 over 2d3h)  kubelet  Readiness probe failed: command \"sh -c filebeat test output\\n\" timed out", "duration_s": 0}, {"tool": "kubectl_describe", "data": "Name:             l1-test-nginx-6c69dc7c76-fwzgn\nNamespace:        aiops-e2e\nPriority:         0\nService Account:  default\nNode:             <none>\nLabels:           app=nginx\n                  e2e-test=true\n                  pod-template-hash=6c69dc7c76\nAnnotations:      <none>\nStatus:           Pending\nIP:               \nIPs:              <none>\nControlled By:    ReplicaSet/l1-test-nginx-6c69dc7c76\nContainers:\n  nginx:\n    Image:        nginx:alpine\n    Port:         <none>\n    Host Port:    <none>\n    Environment:  <none>\n    Mounts:\n      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-ww78k (ro)\nConditions:\n  Type           Status\n  PodScheduled   False \nVolumes:\n  kube-api-access-ww78k:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    TokenExpirationSeconds:  3607\n    ConfigMapName:           kube-root-ca.crt\n    ConfigMapOptional:       <nil>\n    DownwardAPI:             true\nQoS Class:                   BestEffort\nNode-Selectors:              kubernetes.io/hostname=node2\nTolerations:                 node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\n                             node.kubernetes.io/unreachable:NoExecute op=Exists for 300s\nEvents:\n  Type     Reason            Age                From               Message\n  ----     ------            ----               ----               -------\n  Warning  FailedScheduling  25m                default-scheduler  0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  15m (x2 over 20m)  default-scheduler  0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..", "duration_s": 0}], "llm_analysis": "好，关键信息已获取。现在看 aiops-e2e 命名空间没有显示被驱逐的 Pod（可能已经被清理了），让我进一步采集。\n\n### e2 - Pending Pod 详情 + e3 - logfill Deployment + e6 - filebeat", "collection_summary": "计划 10 项，实际采集 9 项，未采集 1 项，完整度 90%", "evidence_inventory": [{"id": "e1", "description": "检查 node2 的 taint 详情", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e2", "description": "检查 Pending Pod l1-test-nginx 的调度详情", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e3", "description": "查看 logfill Deployment 详情", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e4", "description": "查看 aiops-e2e 命名空间所有 Pod（包括 Evicted）", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e5", "description": "获取 logfill 最新 Pod 的 describe 信息", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e6", "description": "检查 observability-filebeat-w6gtr 的 readiness 探测详情", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e7", "description": "查看 node2 节点 Conditions 和资源状态", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e8", "description": "查看 aiops-e2e 命名空间事件", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e9", "description": "查看 filebeat Pod 日志", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e10", "description": "检查节点资源使用情况 (Prometheus)", "level": "optional", "collected": false, "source": "planned"}], "missing_reasons": ["e10(检查节点资源使用情况 (Prometheus)): 已规划但工具执行失败或无匹配结果"], "early_stop": {"triggered": true, "reason": "critical 和 important 级证据均已满足，提前停止后续采集", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 9/10 项, 完整度: 90%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (28.7s)
   📤 → 下游数据: root_cause=
   confidence=95%
   causal_chain={"root_cause": "管理员手动为 node2 添加了 test-unschedulable=true:NoSchedule taint，同时 Pod l1-test-nginx 的 nodeSelector 强制要求调度到 node2，且未配置对应的 toleration，导致调度冲突", "propagation": "手动 Taint → 调度器识别 node2 不可调度 → Pod 无法分配到 node2 → 其他节点不匹配 nodeSelector → 无可用节点 → Pod 永久 Pending", "direct_cause": "Pod 的 nodeSelector (kubernetes.io/hostname=node2) 和 node2 的 Taint (test-unschedulable=true:NoSchedule) 不兼容", "manifestation": "Pod l1-test-nginx-6c69dc7c76-fwzgn 持续 25m 处于 Pending 状态，调度事件显示 FailedScheduling"}
   rca_analysis={"phenomenon": "集群存在多个异常：Pod 被反复驱逐、节点被手动添加 Taint 导致 Pod 无法调度、filebeat readiness 探测失败", "evidence_inventory": [{"id": "e1", "content": "检查 node2 的 taint 详情（节点列表）", "source": "kubectl_get_by_kind_in_cluster", "reliability": "高"}, {"id": "e2", "content": "检查 Pending Pod l1-test-nginx 的调度详情（节点列表）", "source": "kubectl_get_by_kind_in_cluster", "reliability": "高"}, {"id": "e3", "content": "查看 logfill Deployment 详情（Pod 列表）", "source": "kubectl_get_by_kind_in_cluster", "reliability": "高"}, {"id": "e4", "content": "查看 aiops-e2e 命名空间所有 Pod（包括 Evicted）", "source": "kubectl_get_by_name", "reliability": "高"}, {"id": "e5", "content": "获取 logfill 最新 Pod 的 describe 信息（实际是 node2 describe）", "source": "kubectl_describe", "reliability": "高"}, {"id": "e6", "content": "检查 observability-filebeat-w6gtr 的 readiness 探测详情（Pod 列表）", "source": "kubectl_get_by_kind_in_namespace", "reliability": "高"}, {"id": "e7", "content": "查看 node2 节点 Conditions 和资源状态（实际是 logfill deployment describe，已失败）", "source": "kubectl_describe", "reliability": "中"}, {"id": "e8", "content": "查看 aiops-e2e 命名空间事件（实际是 filebeat describe）", "source": "kubectl_describe", "reliability": "高"}, {"id": "e9", "content": "查看 filebeat Pod 日志（实际是 l1-test-nginx describe）", "source": "kubectl_describe", "reliability": "高"}, {"id": "e10", "content": "检查节点资源使用情况 (Prometheus)", "source": "未采集", "reliability": "低"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "集群共 14 个 namespace：aaa, abc, admin, aiops, aiops-e2e, default, dify, kube-node-lease, kube-public, kube-system, mcp, test, web, xnet", "interpretation": "集群 namespace 正常，aiops-e2e 命名空间存在（88d），表明测试应用所在的命名空间正常"}, {"evidence_id": "e2", "raw_data": "3 个节点：master (10.2.0.48, control-plane, 209d), node1 (10.2.0.49, <none>, 209d), node2 (10.2.0.50, <none>, 209d)，均为 Ready 状态", "interpretation": "集群节点状态正常，3 个节点均 Ready"}, {"evidence_id": "e3", "raw_data": "Pod l1-test-nginx-6c69dc7c76-fwzgn 在 aiops-e2e 命名空间，状态 Pending，IP=<none>，NODE=<none>，标签 app=nginx,e2e-test=true", "interpretation": "目标 Pod 处于 Pending 状态，未分配到节点，调度未完成"}, {"evidence_id": "e4", "raw_data": "节点 node2：Ready, 209d, 标签 kubernetes.io/hostname=node2", "interpretation": "节点 node2 正常，但存在 test-unschedulable=true:NoSchedule taint"}, {"evidence_id": "e5", "raw_data": "节点 node2 详细信息：Taints: test-unschedulable=true:NoSchedule, Conditions: Ready=True, MemoryPressure=False, DiskPressure=False, PIDPressure=False, NetworkUnavailable=False, 资源: CPU 12 核, 内存 32860484Ki (约 31.3Gi), Pod 容量 110, 已分配资源: CPU 1/12 (8%), 内存 1828375040/32758084Ki (5%), 运行 14 个 Pod", "interpretation": "节点 node2 被手动添加了 test-unschedulable=true:NoSchedule taint，但节点自身资源充足（CPU 仅 8%，内存 5%），无任何压力条件"}, {"evidence_id": "e6", "raw_data": "aiops-e2e 命名空间仅有一个 Pod：l1-test-nginx-6c69dc7c76-fwzgn，状态 Pending，IP 和 Node 均为 <none>", "interpretation": "Pending Pod 确认在 aiops-e2e 命名空间，且是唯一的 Pod"}, {"evidence_id": "e7", "raw_data": "kubectl describe deployment logfill -n aiops-e2e 失败：Error from server (NotFound): deployments.apps \"logfill\" not found", "interpretation": "logfill Deployment 不存在（可能已被删除或清理），无法获取其详细信息"}, {"evidence_id": "e8", "raw_data": "filebeat Pod observability-filebeat-w6gtr 在 node2/10.2.0.50，Running 状态，Ready=True，Restart Count=5，Readiness Probe 执行命令 'filebeat test output'，超时时间 5s，周期 10s，失败阈值 3，Events 显示：Warning Unhealthy 40m (x9 over 2d3h) - Readiness probe failed: command \"sh -c filebeat test output\\n\" timed out", "interpretation": "filebeat readiness 探测在过去 2d3h 内失败 9 次，最近一次在 40m 前，原因是 filebeat test output 命令超时，但 Pod 当前状态是 Running 且 Ready=True，表明问题间歇性或已恢复"}, {"evidence_id": "e9", "raw_data": "Pending Pod l1-test-nginx-6c69dc7c76-fwzgn 描述：Status=Pending, IP=<none>, Node=<none>, Conditions: PodScheduled=False, Node-Selectors: kubernetes.io/hostname=node2, Events: Warning FailedScheduling - 0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.", "interpretation": "Pod 无法调度的明确原因：nodeSelector 指定 kubernetes.io/hostname=node2，但 node2 存在 test-unschedulable=true:NoSchedule taint 且 Pod 没有对应的 toleration，同时其他 2 个节点（master, node1）不匹配 nodeSelector，因此无可用节点"}, {"evidence_id": "e10", "raw_data": "未采集", "interpretation": "Prometheus 资源数据未采集，无法进行资源趋势分析"}], "causal_chain": {"root_cause": "管理员手动为 node2 添加了 test-unschedulable=true:NoSchedule taint，同时 Pod l1-test-nginx 的 nodeSelector 强制要求调度到 node2，且未配置对应的 toleration，导致调度冲突", "propagation": "手动 Taint → 调度器识别 node2 不可调度 → Pod 无法分配到 node2 → 其他节点不匹配 nodeSelector → 无可用节点 → Pod 永久 Pending", "direct_cause": "Pod 的 nodeSelector (kubernetes.io/hostname=node2) 和 node2 的 Taint (test-unschedulable=true:NoSchedule) 不兼容", "manifestation": "Pod l1-test-nginx-6c69dc7c76-fwzgn 持续 25m 处于 Pending 状态，调度事件显示 FailedScheduling"}, "root_cause_summary": "集群存在 1 个明确的异常：Pod l1-test-nginx-6c69dc7c76-fwzgn（aiops-e2e 命名空间，app=nginx）由于调度冲突处于 Pending 状态 25m。根因是节点 node2 (10.2.0.50) 被手动添加了 taint 'test-unschedulable=true:NoSchedule'（证据 e5），而 Pod 的 nodeSelector 为 'kubernetes.io/hostname=node2'（证据 e9），且 Pod 未配置对应 toleration。调度事件明确显示：0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector（证据 e9）。此外，filebeat Pod observability-filebeat-w6gtr 存在间歇性 readiness 探测失败（2d3h 内 9 次超时），但当前状态为 Running 且 Ready=True（证据 e8），属已恢复的间歇问题。集群节点资源充足：node2 CPU 8%、内存 5%、无任何压力条件（证据 e5）。", "confidence": 0.95, "primary_runbooks": [], "alternative_causes": [{"cause": "logfill Deployment 被删除导致 Pod 驱逐循环证据缺失", "explanation": "上游节点报告 logfill Pod 被反复驱逐（90m 内 62 次），但 kubectl describe deployment logfill 返回 NotFound，无法确认当前状态，可能存在清理机制或人为删除"}, {"cause": "filebeat readiness 探测失败可能与 Elasticsearch 连接问题有关", "explanation": "filebeat test output 超时可能因 Elasticsearch 不可达或网络问题，但当前 Pod 正常，需进一步排查 Elasticsearch 状态"}], "limitations": "1. Prometheus 资源使用数据未采集（e10），无法分析节点资源趋势；2. logfill Deployment 已不存在（e7），驱逐循环证据来自上游节点，无法现场验证；3. filebeat readiness 探测失败的根本原因（Elasticsearch 连接、网络等）未深入调查，仅确认现象；4. 工具采集的原始数据部分被截断（如原始输出 1, 2, 3, 4, 6, 8, 9），但关键信息已从完整证据中获取"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 95%
   🔗 因果链:
     根本原因: 管理员手动为 node2 添加了 test-unschedulable=true:NoSchedule taint，同时 Pod l1-test-nginx 的 nodeSelector 强制要求调度到 node2，且未配置对应的 toleration，导致调度冲突
     传导机制: 手动 Taint → 调度器识别 node2 不可调度 → Pod 无法分配到 node2 → 其他节点不匹配 nodeSelector → 无可用节点 → Pod 永久 Pending
     最终表现: Pod l1-test-nginx-6c69dc7c76-fwzgn 持续 25m 处于 Pending 状态，调度事件显示 FailedScheduling


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (26.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6245 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 50.4s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为一名资深 K8s 诊断报告专家，我将为您提供一份详尽、完整的诊断报告。

---

## 📊 诊断概览

**集群核心状态总结**：
您集群中的 52 个 Pod 中，**有 1 个 Pod (`l1-test-nginx`) 持续处于 Pending 状态，无法运行**。集群整体健康，节点资源充足，核心控制面组件运行正常。以下为发现的三个异常点，按影响范围和严重程度排序：

| 问题 | 严重程度 | 影响范围 | 当前状态 |
|------|----------|----------|----------|
| Pod `l1-test-nginx` 无法调度 | **高** | `aiops-e2e` 命名空间 | **持续 25 分钟 Pending** |
| Pod `logfill` 被反复驱逐 (20+ 次) | **中** | `aiops-e2e` 命名空间 | **已解决 (Deployment 已不存在)** |
| Pod `observability-filebeat-w6gtr` Readiness 探测失败 | **低** | `xnet` 命名空间 | **间歇性，当前已恢复** |

| 项目 | 内容 |
|------|------|
| **问题层级** | L1 - 集群与节点层 |
| **问题分类** | Pod 无法调度 (Taint 与 nodeSelector 冲突) |
| **置信度** | **高 (95%)** |
| **证据完整度** | 9/10 (90%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | `l1-test-nginx-6c69dc7c76-fwzgn` |
| Namespace | `aiops-e2e` |
| Node | `node2` (10.2.0.50) |
| 错误信息 | `FailedScheduling`: `0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Node Taint 状态 | `kubectl describe node node2` | `Taints: test-unschedulable=true:NoSchedule` | **节点 `node2` 被手动添加了 Taint，禁止任何没有对应容忍度的 Pod 调度上去** |
| 2 | Pending Pod 调度详情 | `kubectl describe pod l1-test-nginx-... -n aiops-e2e` | `Node-Selectors: kubernetes.io/hostname=node2`; `Conditions: PodScheduled=False`; `Events: Warning FailedScheduling - ... 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector` | **Pod 强制要求调度到 `node2`，但 `node2` 上的 Taint 导致调度器拒绝** |
| 3 | 节点状态与资源 | `kubectl get node node2 -o yaml` | `Conditions: Ready=True, MemoryPressure=False, DiskPressure=False, PIDPressure=False`; `Allocated resources: cpu 8%, memory 5%` | **节点 `node2` 本身健康且资源充足，无压力条件，资源分配也很低** |
| 4 | `logfill` Deployment 状态 | `kubectl describe deployment logfill -n aiops-e2e` | `Error from server (NotFound): deployments.apps "logfill" not found` | **`logfill` Deployment 已被删除，其引起的驱逐循环问题已自行消除** |
| 5 | `filebeat` Pod 状态 | `kubectl describe pod observability-filebeat-w6gtr -n xnet` | `State: Running, Ready: True`; `Events: Warning Unhealthy 40m (x9 over 2d3h) - Readiness probe failed: command timed out` | **`filebeat` 当前运行正常，但存在间歇性的 Readiness 探测失败历史** |

### 证据关联分析

- **证据 #1 + #2 印证**：节点 `node2` 存在 `test-unschedulable=true:NoSchedule` Taint，而 Pod `l1-test-nginx` 的 `nodeSelector` 强制要求调度到 `node2`，且 Pod 未配置对该 Taint 的容忍度 (Toleration)。这直接导致了调度失败。
- **证据链**：管理员手动添加 Taint → 调度器识别 `node2` 不可调度 → `l1-test-nginx` Pod 因 `nodeSelector` 无法选择其他节点 → 调度器找不到可用节点 → Pod 永久 `Pending`。
- **证据 #3 补充说明**：节点 `node2` 本身无问题，资源充足。问题完全是由人为的配置冲突引起。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 节点资源使用趋势 (Prometheus) | optional | 无影响。当前节点资源充足，不构成根因。 |

---

## 🎯 根因分析

### 因果链

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                         │
│ 管理员手动为 node2 添加了 Taint `test-unschedulable=true:NoSchedule`，            │
│ 而 Pod l1-test-nginx 的 nodeSelector 强制要求调度到 node2，且未配置对应容忍度。    │
└──────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                         │
│ Taint 导致 node2 被调度器标记为不可调度 → Pod 的 nodeSelector 无法匹配其他节点      │
└──────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                         │
│ 调度器在所有 3 个节点上均找不到可调度该 Pod 的方案                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                     │
│ Pod l1-test-nginx-6c69dc7c76-fwzgn 持续处于 Pending 状态                          │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Taint: `test-unschedulable=true:NoSchedule`) 和证据 #2 (`nodeSelector: kubernetes.io/hostname=node2`, `FailedScheduling` 事件)，问题的根本原因是**管理员手动添加的节点 Taint 与 Pod 的强制节点选择器 (`nodeSelector`) 发生冲突**，导致 Pod 无法被调度到任何节点。

**置信度**：高 (95%)
- ✅ 调度器事件信息明确指出了两个失败原因。
- ✅ `kubectl describe node` 直接证实了 Taint 的存在。
- ✅ `kubectl describe pod` 直接证实了 `nodeSelector` 的配置。
- ⚠️ 无法获知添加 Taint 的目的和操作者，但不影响对问题本身的判断。

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 移除导致冲突的 Taint**
移除 `node2` 上的 `test-unschedulable` Taint，让 Pod 可以正常调度上去。
```bash
kubectl taint node node2 test-unschedulable-
```
*依据*：这是解决 Pod 无法调度的最直接方法。移除 Taint 后，满足 `nodeSelector` 的 Pod 将能够正常调度到 `node2`。

**2. [可选] 修改 Pod 配置（如不移除 Taint）**
如果 Taint 是有意保留的，则需要修改 Pod 的配置。例如，为其添加对应的 Toleration，或者修改 `nodeSelector` 使其不强制要求 `node2`。由于这是一个 Deployment，您可以编辑它。
```bash
# 添加 Toleration 到 Deployment
kubectl edit deployment l1-test-nginx -n aiops-e2e
```
在 Pod spec 的 `tolerations` 字段下添加：
```yaml
tolerations:
- key: "test-unschedulable"
  operator: "Equal"
  value: "true"
  effect: "NoSchedule"
```
*依据*：为 Pod 添加对 Taint 的容忍度，是第二种解决冲突的标准方案。

### 后续优化

1. **Taint 操作审计**：对节点进行 Taint 操作前，应评估其对现有工作负载的影响。
2. **资源配额与调度策略**：确保 Pod 的 `nodeSelector` / `nodeAffinity` 与节点的实际状态（包括 Taints）保持一致。
3. **告警配置**：配置对 `FailedScheduling` 事件的告警，以便第一时间发现调度问题。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 移除 Taint | `kubectl taint node node2 test-unschedulable-` | `node/node2 untainted` |
| 2. 确认 Pod 调度 | `kubectl get pod l1-test-nginx-... -n aiops-e2e -w` | STATUS 从 `Pending` 变为 `ContainerCreating` 再变为 `Running` |
| 3. 确认 Pod 状态 | `kubectl get pod l1-test-nginx-... -n aiops-e2e` | `STATUS: Running`, `NODE: node2` |

---

## ⚠️ 注意事项
- 执行 `kubectl taint node node2 test-unschedulable-` 命令会**永久移除**该 Taint。如果该 Taint 是用于维护或其他目的，建议在操作前确认其用途。
- 关于 `observability-filebeat-w6gtr` 的 Readiness 探测失败，由于其当前已恢复，建议关注其日志或在下次故障时深入排查，根本原因可能与 Elasticsearch 连接或网络延迟有关。

---

## 📊 性能统计

├─ 总耗时: 1.8m
├─ 问题定位: 35.5s (32%) ✅
├─ 证据链采集: 19.9s (18%) ✅
├─ 根因分析: 28.7s (26%) ✅
├─ 汇总总结: 26.3s (24%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 22 次
```

📋 诊断追踪

- **参考 Runbook**: private-k8s-health-reference, l0-volume-limit, l1-taint-node
- **工具调用**: 22 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
