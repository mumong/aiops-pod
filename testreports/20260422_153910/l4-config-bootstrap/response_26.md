======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 3eb07defab54495c]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先快速查看集群的整体状态，包括节点、Pod 和关键资源。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 Command failed (exit 2):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,READY:'.status.conditions[] | select(.type=="Ready"
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   209d   v1.26.8  
   💭 [问题定位] 节点全部 Ready。让我换个方式查看异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS             RESTARTS        AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     a
   💭 [问题定位] 发现了异常 Pod。让我进一步查看。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             appconfigfail-7649c79dc5-q4zjz
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Wed, 22 Apr 2026 07:38:39
   💭 [问题定位] 这个 Pod 有明确的标签 `l4-scenario=config-bootstrap-fail`，且 Exit Code 42，日志明确输出"FATAL: missing required APP_BOOT_MODE"——这是典型的 L4 应用层配置校验失败场景。

让我也获取通用 runbook 和 L4 场景 runbook 做参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# L4 应用启动配置校验失败 (Config Bootstrap Fail)

> 层级: L4 - 应用层 | 场景: 应用在启动阶段因业务配置缺失或非法而主动退出

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | `CrashLoopBackOff` / `Error`，重启次数持续增加 |
| 容器日志 | 含
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# 私有化 Kubernetes 环境健康与高效排查参考手册

> 类型: reference | 适用: 私有化 Kubernetes 环境 | 环境特征: Calico + NFS + containerd

## 目的

本手册不是某个具体故障的处理步骤，而是一个**额外知识参考**：
- 帮助理解在私有化 Kubernetes 环境中，健康检查应重点关注哪些资源与信号

   💭 [问题定位] 现在让我查看一下该 Pod 的日志以确认根因。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                             READY   STATUS   RESTARTS         AGE   IP              NODE    NOMINATED NODE   READINESS GATES   LABELS
appconfigfail-7649c79dc5-q4zjz   0/1     Error    10 (5m13s a
   💭 [问题定位] 好了，信息已充分。让我输出诊断结果。

```json
{
  "layer": "L4",
  "layers": ["L4"],
  "layer_name": "应用层",
  "confidence": 0.98,
  "reasoning": "集群整体健康：3个节点全部 Ready，系统组件（Calico、CoreDNS、kube-apiserver、etcd 等）均正常运行。唯一的异常 Pod 为 aiops-e2e/appconfigfail-7649c79dc5-q4zjz，处于 CrashLoopBackOff/Error 状态，Exit Code 42。该 Pod 的容器日志明确输出 'FATAL: missing required APP_BOOT_MODE' 和 'business config validation failed before server startup'，且 Pod 标签为 l4-scenario=config-bootstrap-fail。无 OOMKilled（排除 L2）、无 ImagePullBackOff（排除 L3）、无 Evicted（排除 L0），确认为 L4 应用启动配置校验失败。",
  "key_entities": [
    {"type": "Pod", "value": "appconfigfail-7649c79dc5-q4zjz"},
    {"type": "Namespace", "value": "aiops-e2e"},
    {"type": "Node", "value": "node2"}
  ],
  "possible_scenarios": [
    {
      "scenario": "应用启动配置校验失败 (Config Bootstrap Fail)",
      "layer": "L4",
      "evidence": [
        "Pod STATUS=Error/CrashLoopBackOff",
        "Exit Code=42（非 OOM 的业务退出码）",
        "容器日志含 'FATAL: missing required APP_BOOT_MODE' 和 'business config validation failed'",
        "Pod 标签明确标记 l4-scenario=config-bootstrap-fail",
        "镜像 busybox:1.36 已存在，无镜像拉取问题",
        "无 OOMKilled、无 Evicted、无磁盘压力相关信号"
      ],
      "root_cause": "容器启动命令中检查 APP_BOOT_MODE 环境变量，该变量未设置，导致业务配置校验失败，主动退出（exit 42）",
      "suggestion": "为 Pod 设置 APP_BOOT_MODE 环境变量，或在 Deployment/ReplicaSet 的 spec.containers.env 中补充该配置"
    }
  ]
}
```
   ✅ [问题定位] 完成 (39.8s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': '应用启动配置校验失败 (Config Bootstrap Fail)', 'layer': 'L4', 'evidence': ['Pod STATUS=Error/CrashLoopBackOff', 'Exit Code=42（非 OOM 的业务退出码）', "容器日志含 'FATAL: missing required APP_BOOT_MODE' 和 'business config validation failed'", 'Pod 标签明确标记 l4-scenario=config-bootstrap-fail', '镜像 busybox:1.36 已存在，无镜像拉取问题', '无 OOMKilled、无 Evicted、无磁盘压力相关信号'], 'root_cause': '容器启动命令中检查 APP_BOOT_MODE 环境变量，该变量未设置，导致业务配置校验失败，主动退出（exit 42）', 'suggestion': '为 Pod 设置 APP_BOOT_MODE 环境变量，或在 Deployment/ReplicaSet 的 spec.containers.env 中补充该配置'}]
   entities=[{"type": "Pod", "value": "appconfigfail-7649c79dc5-q4zjz"}, {"type": "Namespace", "value": "aiops-e2e"}, {"type": "Node", "value": "node2"}]
   reasoning=集群整体健康：3个节点全部 Ready，系统组件（Calico、CoreDNS、kube-apiserver、etcd 等）均正常运行。唯一的异常 Pod 为 aiops-e2e/appconfigfail-7649c79dc5-q4zjz，处于 CrashLoopBackOff/Error 状态，Exit Code 42。该 Pod 的容器日志明确输出 'FATAL: missing required APP_BOOT_MODE' 和 'business config validation failed before server startup'，且 Pod 标签为 l4-scenario=config-bootstrap-fail。无 OOMKilled（排除 L2）、无 ImagePullBackOff（排除 L3）、无 Evicted（排除 L0），确认为 L4 应用启动配置校验失败。
   layer_analysis={"layer": "L4", "layers": ["L4"], "layer_name": "应用层", "confidence": 0.98, "reasoning": "集群整体健康：3个节点全部 Ready，系统组件（Calico、CoreDNS、kube-apiserver、etcd 等）均正常运行。唯一的异常 Pod 为 aiops-e2e/appconfigfail-7649c79dc5-q4zjz，处于 CrashLoopBackOff/Error 状态，Exit Code 42。该 Pod 的容器日志明确输出 'FATAL: missing required APP_BOOT_MODE' 和 'business config validation failed before server startup'，且 Pod 标签为 l4-scenario=config-bootstrap-fail。无 OOMKilled（排除 L2）、无 ImagePullBackOff（排除 L3）、无 Evicted（排除 L0），确认为 L4 应用启动配置校验失败。", "key_entities": [{"type": "Pod", "value": "appconfigfail-7649c79dc5-q4zjz"}, {"type": "Namespace", "value": "aiops-e2e"}, {"type": "Node", "value": "node2"}], "possible_scenarios": [{"scenario": "应用启动配置校验失败 (Config Bootstrap Fail)", "layer": "L4", "evidence": ["Pod STATUS=Error/CrashLoopBackOff", "Exit Code=42（非 OOM 的业务退出码）", "容器日志含 'FATAL: missing required APP_BOOT_MODE' 和 'business config validation failed'", "Pod 标签明确标记 l4-scenario=config-bootstrap-fail", "镜像 busybox:1.36 已存在，无镜像拉取问题", "无 OOMKilled、无 Evicted、无磁盘压力相关信号"], "root_cause": "容器启动命令中检查 APP_BOOT_MODE 环境变量，该变量未设置，导致业务配置校验失败，主动退出（exit 42）", "suggestion": "为 Pod 设置 APP_BOOT_MODE 环境变量，或在 Deployment/ReplicaSet 的 spec.containers.env 中补充该配置"}]}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 98%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我先看看集群的整体状态。
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 调用工具: helm_list_releases
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   209d   v1.26.8  
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS             RESTARTS        AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     a
   💭 [证据链采集] 工具结果: helm_list_releases (success)
      📄 [
  {
    "name": "observability",
    "namespace": "xnet",
    "revision": "1",
    "status": "deployed",
    "chart": "observability-1.0.2",
    "app_version": "1.0.0",
    "updated": "2026-03-30 15
   💭 [证据链采集] 集群整体正常，但有一个异常 Pod。让我深入看一下这个异常 Pod 的详细信息。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:             appconfigfail-7649c79dc5-q4zjz
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Wed, 22 Apr 2026 07:38:39
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 LAST SEEN              TYPE      REASON           OBJECT                               MESSAGE
26m                    Normal    Scheduled        Pod/appconfigfail-7649c79dc5-q4zjz   Successfully assig
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 NAME            READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES         SELECTOR            LABELS
appconfigfail   0/1     1            0           26m   app          busybox:1.36   app=app
   💭 [证据链采集] 让我再看看节点资源和 Deployment 的 YAML 配置。
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 apiVersion: apps/v1
kind: Deployment
metadata:
  annotations:
    deployment.kubernetes.io/revision: "1"
    kubectl.kubernetes.io/last-applied-configuration: |
      {"apiVersion":"apps/v1","kind":"D
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_LAYER_APPLICATION: true\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: appl
   💭 [证据链采集] 好了，我已经收集到足够的信息了。让我看看节点资源情况。
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"instance":"10.2.0.49:9100"},"value":[1776845142.289,"9.892748319113032"]},{"metric":{"instance":"10.2.0.48:9100"},"value":[17768
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"container":"node-exporter","device":"/dev/mapper/ubuntu--vg-ubuntu--lv","endpoint":"http-metrics","fstype":"ext4","instance":"10
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"container":"node-exporter","endpoint":"http-metrics","instance":"10.2.0.49:9100","job":"node-exporter","namespace":"xnet","pod":
   💭 [证据链采集] ## 集群状态总结

### 整体健康状况 ✅

| 维度 | 状态 | 详情 |
|------|------|------|
| **节点** | ✅ 全部 Ready | master, node1, node2 均正常运行 |
| **控制面** | ✅ 正常 | etcd, apiserver, scheduler, controller-manager 均 Running |
| **网络** | ✅ 正常 | Calico, CoreDNS, Multus 均正常运行 |
| **存储** | ✅ 正常 | NFS provisioner Running |

### 节点资源使用率

| 节点 | CPU | 内存 | 磁盘 |
|------|-----|------|------|
| **master** (10.2.0.48) | 14.96% | 30.95% | **82.74%** 🔴 |
| **node1** (10.2.0.49) | 9.89% | 19.61% | 52.89% |
| **node2** (10.2.0.50) | 2.24% | 9.35% | 54.99% |

> ⚠️ **注意**: master 节点的磁盘使用率已达 **82.74%**，需要关注。

---

### ❌ 唯一异常 Pod：`appconfigfail-7649c79dc5-q4zjz`

| 项目 | 值 |
|------|-----|
| **命名空间** | `aiops-e2e` |
| **状态** | `CrashLoopBackOff` |
| **重启次数** | 10 次 |
| **退出码** | `42`（业务自定义退出码，非 OOM） |
| **节点** | node2 (10.2.0.50) |
| **IP** | 172.16.104.57 |

#### 根因分析

容器启动命令会检查环境变量 `APP_BOOT_MODE`，但该变量**未设置**，导致业务配置校验失败并主动退出。

**容器日志**：
```
L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config
L4_LAYER_APPLICATION: true
L4_SCENARIO: config-bootstrap-fail
L4_ERROR_TYPE: application-config-validation
FATAL: missing required APP_BOOT_MODE
FATAL: business config validation failed before server startup
```

#### 修复方案

在 Deployment `appconfigfail` 的容器定义中补充环境变量：

```yaml
spec:
  template:
    spec:
      containers:
        - name: app
          env:
            - name: APP_BOOT_MODE
              value: "production"   # 或其他所需值
```

可以通过 `kubectl edit deployment appconfigfail -n aiops-e2e` 或修改 YAML 文件后 `kubectl apply` 来修复。
   ✅ [证据链采集] 完成 (36.6s)
   📤 → 下游数据: evidence_items=11/11
   evidence_analysis={"evidence_plan": [{"id": "cmd_0", "description": "执行命令: kubectl apply` 来修复。", "level": "important", "command": "kubectl apply` 来修复。", "tool": "kubectl", "purpose": "获取集群状态或资源信息"}], "tool_results": [], "tool_data": [{"tool": "kubectl_get_by_kind_in_cluster", "data": "NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nmaster   Ready    control-plane   209d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          209d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-174-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          209d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-174-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_cluster", "data": "NAMESPACE     NAME                                                READY   STATUS             RESTARTS        AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\naiops-e2e     appconfigfail-7649c79dc5-q4zjz                      0/1     CrashLoopBackOff   10 (26s ago)    26m     172.16.104.57    node2    <none>           <none>            app=appconfigfail,l4-scenario=config-bootstrap-fail,pod-template-hash=7649c79dc5\naiops         aiops-copilot-76779bb6df-4bcrf                      1/1     Running            0               6h27m   172.16.104.29    node2    <none>           <none>            app=aiops-copilot,pod-template-hash=76779bb6df\ndefault       dns-test-existing                                   1/1     Running            0               2d2h    172.16.166.148   node1    <none>           <none>            run=dns-test-existing\ndefault       exec-test                                           1/1     Running            0               2d4h    172.16.104.8     node2    <none>           <none>            run=exec-test\ndefault       network-test-from-running                           1/1     Running            0               2d2h    172.16.104.50    node2    <none>           <none>            run=network-test-from-running\ndefault       nfs-client-provisioner-6fcd4994c9-lczf6             1/1     Running            4 (5d1h ago)    86d     172.16.104.41    node2    <none>           <none>            app=nfs-client-provisioner,pod-template-hash=6fcd4994c9\nkube-system   calico-kube-controllers-6c67f9d475-2xcb7            1/1     Running            4 (5d1h ago)    28d     172.16.166.133   node1    <none>           <none>            k8s-app=calico-kube-controllers,pod-template-hash=6c67f9d475\nkube-system   calico-node-4kp26                                   1/1     Running            12 (5d1h ago)   183d    10.2.0.48        master   <none>           <none>            controller-revision-hash=65f554db6,k8s-app=calico-node,pod-template-generation=1\nkube-system   calico-node-d2dhp                                   1/1     Running            13 (5d1h ago)   183d    10.2.0.50        node2    <none>           <none>            controller-revision-hash=65f554db6,k8s-app=calico-node,pod-template-generation=1\nkube-system   calico-node-mnrjs                                   1/1     Running            12 (5d1h ago)   183d    10.2.0.49        node1    <none>           <none>            controller-revision-hash=65f554db6,k8s-app=calico-node,pod-template-generation=1\nkube-system   coredns-777df594b8-j4857                            1/1     Running            4 (5d1h ago)    28d     172.16.166.129   node1    <none>           <none>            k8s-app=kube-dns,pod-template-hash=777df594b8\nkube-system   coredns-777df594b8-s8r4n                            1/1     Running            4 (5d1h ago)    28d     172.16.166.185   node1    <none>           <none>            k8s-app=kube-dns,pod-template-hash=777df594b8\nkube-system   etcd-master                                         1/1     Running            13 (5d1h ago)   209d    10.2.0.48        master   <none>           <none>            component=etcd,tier=control-plane\nkube-system   kube-apiserver-master                               1/1     Running            13 (5d1h ago)   209d    10.2.0.48        master   <none>           <none>            component=kube-apiserver,tier=control-plane\nkube-system   kube-controller-manager-master                      1/1     Running            36 (5d1h ago)   209d    10.2.0.48        master   <none>           <none>            component=kube-controller-manager,tier=control-plane\nkube-system   kube-multus-ds-rnvbg                                1/1     Running            12 (5d1h ago)   183d    10.2.0.49        node1    <none>           <none>            app=multus,controller-revision-hash=6d4c8546fc,name=multus,pod-template-generation=1,tier=node\nkube-system   kube-multus-ds-sc2jn                                1/1     Running            4 (5d1h ago)    86d     10.2.0.48        master   <none>           <none>            app=multus,controller-revision-hash=6d4c8546fc,name=multus,pod-template-generation=1,tier=node\nkube-system   kube-multus-ds-x7h9s                                1/1     Running            13 (5d1h ago)   183d    10.2.0.50        node2    <none>           <none>            app=multus,controller-revision-hash=6d4c8546fc,name=multus,pod-template-generation=1,tier=node\nkube-system   kube-proxy-69zzr                                    1/1     Running            4 (5d1h ago)    28d     10.2.0.50        node2    <none>           <none>            controller-revision-hash=7d99996759,k8s-app=kube-proxy,pod-template-generation=1\nkube-system   kube-proxy-bblvc                                    1/1     Running            4 (5d1h ago)    28d     10.2.0.49        node1    <none>           <none>            controller-revision-hash=7d99996759,k8s-app=kube-proxy,pod-template-generation=1\nkube-system   kube-proxy-wbh4k                                    1/1     Running            4 (5d1h ago)    27d     10.2.0.48        master   <none>           <none>            controller-revision-hash=7d99996759,k8s-app=kube-proxy,pod-template-generation=1\nkube-system   kube-scheduler-master                               1/1     Running            38 (5d1h ago)   209d    10.2.0.48        master   <none>           <none>            component=kube-scheduler,tier=control-plane\nmcp           mcp-server-manager-8677f6896c-d4mr9                 1/1     Running            0               46h     172.16.104.59    node2    <none>           <none>            app=mcp-server-manager,pod-template-hash=8677f6896c\nxnet          alertmanager-observability-alertmanager-0           2/2     Running            8 (5d1h ago)    23d     172.16.166.161   node1    <none>           <none>            alertmanager=observability-alertmanager,app.kubernetes.io/instance=observability-alertmanager,app.kubernetes.io/managed-by=prometheus-operator,app.kubernetes.io/name=alertmanager,app.kubernetes.io/version=0.28.1,controller-revision-hash=alertmanager-observability-alertmanager-6c9cfbf844,statefulset.kubernetes.io/pod-name=alertmanager-observability-alertmanager-0\nxnet          api-server-6bd6bf8d6f-27svp                         1/1     Running            4 (5d1h ago)    23d     172.16.219.106   master   <none>           <none>            app=api-server,pod-template-hash=6bd6bf8d6f\nxnet          deepflow-agent-pcknn                                1/1     Running            9 (5d1h ago)    23d     172.16.166.181   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow-agent,app=deepflow,component=deepflow-agent,controller-revision-hash=54856d959b,pod-template-generation=1\nxnet          deepflow-agent-trc8k                                1/1     Running            7 (5d1h ago)    19d     172.16.104.7     node2    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow-agent,app=deepflow,component=deepflow-agent,controller-revision-hash=54856d959b,pod-template-generation=1\nxnet          deepflow-agent-whn22                                1/1     Running            8 (5d1h ago)    23d     172.16.219.97    master   <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow-agent,app=deepflow,component=deepflow-agent,controller-revision-hash=54856d959b,pod-template-generation=1\nxnet          elasticsearch-master-0                              1/1     Running            4 (5d1h ago)    23d     172.16.219.109   master   <none>           <none>            app=elasticsearch-master,chart=observability,controller-revision-hash=elasticsearch-master-695ff9864f,release=observability,statefulset.kubernetes.io/pod-name=elasticsearch-master-0\nxnet          ham-p9dxv                                           1/1     Running            14 (5d1h ago)   177d    172.16.104.21    node2    <none>           <none>            app=ham,controller-revision-hash=f65f887d,pod-template-generation=1\nxnet          ham-qzjg5                                           1/1     Running            4 (5d1h ago)    85d     172.16.219.112   master   <none>           <none>            app=ham,controller-revision-hash=f65f887d,pod-template-generation=1\nxnet          ham-wt9kh                                           1/1     Running            13 (5d1h ago)   177d    172.16.166.187   node1    <none>           <none>            app=ham,controller-revision-hash=f65f887d,pod-template-generation=1\nxnet          lgtm-5dc5c67d5f-sc286                               1/1     Running            4 (5d1h ago)    23d     172.16.166.151   node1    <none>           <none>            app=lgtm,pod-template-hash=5dc5c67d5f\nxnet          observability-clickhouse-0                          1/1     Running            4 (5d1h ago)    23d     172.16.166.137   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=clickhouse,app=deepflow,component=clickhouse,controller-revision-hash=observability-clickhouse-75b8d58ccc,statefulset.kubernetes.io/pod-name=observability-clickhouse-0\nxnet          observability-deepflow-app-654fcfbfbf-q8st6         1/1     Running            4 (5d1h ago)    23d     172.16.166.160   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow,app=deepflow,component=deepflow-app,pod-template-hash=654fcfbfbf\nxnet          observability-deepflow-server-774dd6c5b7-9c998      1/1     Running            14 (5d ago)     23d     172.16.166.135   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow,app=deepflow,component=deepflow-server,pod-template-hash=774dd6c5b7\nxnet          observability-filebeat-ffwsp                        1/1     Running            4 (5d1h ago)    23d     172.16.219.80    master   <none>           <none>            app=observability-filebeat,chart=observability-1.0.2,controller-revision-hash=57fb88b7c5,heritage=Helm,pod-template-generation=1,release=observability\nxnet          observability-filebeat-m58xw                        1/1     Running            5 (5d1h ago)    23d     172.16.166.134   node1    <none>           <none>            app=observability-filebeat,chart=observability-1.0.2,controller-revision-hash=57fb88b7c5,heritage=Helm,pod-template-generation=1,release=observability\nxnet          observability-filebeat-w6gtr                        1/1     Running            5 (5d1h ago)    19d     172.16.104.53    node2    <none>           <none>            app=observability-filebeat,chart=observability-1.0.2,controller-revision-hash=57fb88b7c5,heritage=Helm,pod-template-generation=1,release=observability\nxnet          observability-grafana-58bf9cfd6f-ndsxr              4/4     Running            36 (5d ago)     23d     172.16.166.144   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=grafana,app.kubernetes.io/version=12.0.2,helm.sh/chart=grafana-9.2.7,pod-template-hash=58bf9cfd6f\nxnet          observability-kepler-2sgrr                          1/1     Running            6 (5d1h ago)    23d     10.2.0.49        node1    <none>           <none>            app.kubernetes.io/component=exporter,app.kubernetes.io/name=kepler-kepler,controller-revision-hash=7c6c5f9bd6,pod-template-generation=1\nxnet          observability-kepler-7scjm                          1/1     Running            7 (5d1h ago)    23d     10.2.0.48        master   <none>           <none>            app.kubernetes.io/component=exporter,app.kubernetes.io/name=kepler-kepler,controller-revision-hash=7c6c5f9bd6,pod-template-generation=1\nxnet          observability-kepler-ggstf                          1/1     Running            8 (5d1h ago)    19d     10.2.0.50        node2    <none>           <none>            app.kubernetes.io/component=exporter,app.kubernetes.io/name=kepler-kepler,controller-revision-hash=7c6c5f9bd6,pod-template-generation=1\nxnet          observability-kibana-65d7c45f6d-tm4vv               1/1     Running            4 (5d1h ago)    23d     172.16.166.191   node1    <none>           <none>            app=observability-kibana,pod-template-hash=65d7c45f6d,release=observability\nxnet          observability-kube-state-metrics-798986b8b7-6z2dq   1/1     Running            4 (5d1h ago)    23d     172.16.219.65    master   <none>           <none>            app.kubernetes.io/component=metrics,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=kube-state-metrics,app.kubernetes.io/part-of=kube-state-metrics,app.kubernetes.io/version=2.15.0,helm.sh/chart=kube-state-metrics-5.37.0,pod-template-hash=798986b8b7,release=observability\nxnet          observability-mysql-764f9d5966-wh2bc                1/1     Running            4 (5d1h ago)    23d     172.16.219.98    master   <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=mysql,app=deepflow,component=mysql,pod-template-hash=764f9d5966\nxnet          observability-operator-d4495dc86-69lgw              1/1     Running            4 (5d1h ago)    23d     172.16.166.182   node1    <none>           <none>            app.kubernetes.io/component=prometheus-operator,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=observability-prometheus-operator,app.kubernetes.io/part-of=observability,app.kubernetes.io/version=1.0.2,app=observability-operator,chart=observability-1.0.2,heritage=Helm,pod-template-hash=d4495dc86,release=observability\nxnet          observability-prometheus-node-exporter-lj75r        1/1     Running            4 (5d1h ago)    23d     10.2.0.48        master   <none>           <none>            app.kubernetes.io/component=metrics,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=prometheus-node-exporter,app.kubernetes.io/part-of=prometheus-node-exporter,app.kubernetes.io/version=1.9.1,controller-revision-hash=74f4f4b87d,helm.sh/chart=prometheus-node-exporter-4.47.0,jobLabel=node-exporter,pod-template-generation=1,release=observability\nxnet          observability-prometheus-node-exporter-qp2qd        1/1     Running            4 (5d1h ago)    19d     10.2.0.50        node2    <none>           <none>            app.kubernetes.io/component=metrics,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=prometheus-node-exporter,app.kubernetes.io/part-of=prometheus-node-exporter,app.kubernetes.io/version=1.9.1,controller-revision-hash=74f4f4b87d,helm.sh/chart=prometheus-node-exporter-4.47.0,jobLabel=node-exporter,pod-template-generation=1,release=observability\nxnet          observability-prometheus-node-exporter-wnbb8        1/1     Running            4 (5d1h ago)    23d     10.2.0.49        node1    <none>           <none>            app.kubernetes.io/component=metrics,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=prometheus-node-exporter,app.kubernetes.io/part-of=prometheus-node-exporter,app.kubernetes.io/version=1.9.1,controller-revision-hash=74f4f4b87d,helm.sh/chart=prometheus-node-exporter-4.47.0,jobLabel=node-exporter,pod-template-generation=1,release=observability\nxnet          observability-telegraf-79f45d86-4kzkm               1/1     Running            4 (5d1h ago)    23d     172.16.219.113   master   <none>           <none>            app.kubernetes.io/component=telegraf,app.kubernetes.io/instance=observability,app.kubernetes.io/name=observability,pod-template-hash=79f45d86\nxnet          prometheus-observability-prometheus-0               2/2     Running            16 (5d1h ago)   23d     172.16.166.142   node1    <none>           <none>            app.kubernetes.io/instance=observability-prometheus,app.kubernetes.io/managed-by=prometheus-operator,app.kubernetes.io/name=prometheus,app.kubernetes.io/version=3.4.1,controller-revision-hash=prometheus-observability-prometheus-9467b46f7,operator.prometheus.io/name=observability-prometheus,operator.prometheus.io/shard=0,prometheus=observability-prometheus,statefulset.kubernetes.io/pod-name=prometheus-observability-prometheus-0\nxnet          xnet-agent-568f547566-jdsgp                         1/1     Running            4 (5d1h ago)    108d    172.16.104.40    node2    <none>           <none>            app=xnet-agent,pod-template-hash=568f547566", "duration_s": 0}, {"tool": "helm_list_releases", "data": "[\n  {\n    \"name\": \"observability\",\n    \"namespace\": \"xnet\",\n    \"revision\": \"1\",\n    \"status\": \"deployed\",\n    \"chart\": \"observability-1.0.2\",\n    \"app_version\": \"1.0.0\",\n    \"updated\": \"2026-03-30 15:18:36.057713534 +0800 +0800\"\n  },\n  {\n    \"name\": \"test1\",\n    \"namespace\": \"aaa\",\n    \"revision\": \"1\",\n    \"status\": \"deployed\",\n    \"chart\": \"redis-10.5.7\",\n    \"app_version\": \"5.0.7\",\n    \"updated\": \"2026-04-17 07:04:50.381039445 +0000 UTC\"\n  },\n  {\n    \"name\": \"xnet-agent\",\n    \"namespace\": \"xnet\",\n    \"revision\": \"1\",\n    \"status\": \"deployed\",\n    \"chart\": \"xnet-agent-1.0.0\",\n    \"app_version\": \"1.0.0\",\n    \"updated\": \"2025-09-25 17:55:23.849650741 +0800 +0800\"\n  }\n]", "duration_s": 0}, {"tool": "kubectl_describe", "data": "Name:             appconfigfail-7649c79dc5-q4zjz\nNamespace:        aiops-e2e\nPriority:         0\nService Account:  default\nNode:             node2/10.2.0.50\nStart Time:       Wed, 22 Apr 2026 07:38:39 +0000\nLabels:           app=appconfigfail\n                  l4-scenario=config-bootstrap-fail\n                  pod-template-hash=7649c79dc5\nAnnotations:      cni.projectcalico.org/containerID: c6399f913454284036a261148882084711e3bf6f9788cf1df749c56fbda41b6f\n                  cni.projectcalico.org/podIP: 172.16.104.57/32\n                  cni.projectcalico.org/podIPs: 172.16.104.57/32\n                  k8s.v1.cni.cncf.io/network-status:\n                    [{\n                        \"name\": \"k8s-pod-network\",\n                        \"ips\": [\n                            \"172.16.104.57\"\n                        ],\n                        \"default\": true,\n                        \"dns\": {}\n                    }]\n                  k8s.v1.cni.cncf.io/networks-status:\n                    [{\n                        \"name\": \"k8s-pod-network\",\n                        \"ips\": [\n                            \"172.16.104.57\"\n                        ],\n                        \"default\": true,\n                        \"dns\": {}\n                    }]\nStatus:           Running\nIP:               172.16.104.57\nIPs:\n  IP:           172.16.104.57\nControlled By:  ReplicaSet/appconfigfail-7649c79dc5\nContainers:\n  app:\n    Container ID:  containerd://b1aec2c351c9393961cd4305f15772302656a22fa514788eb3f1f92428e9e1e9\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Port:          <none>\n    Host Port:     <none>\n    Command:\n      sh\n      -c\n    Args:\n      echo \"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\"\n      echo \"L4_LAYER_APPLICATION: true\"\n      echo \"L4_SCENARIO: config-bootstrap-fail\"\n      echo \"L4_ERROR_TYPE: application-config-validation\"\n      if [ -z \"${APP_BOOT_MODE:-}\" ]; then\n        echo \"FATAL: missing required APP_BOOT_MODE\"\n        echo \"FATAL: business config validation failed before server startup\"\n        exit 42\n      fi\n      echo \"unexpected success\"\n      exit 1\n      \n    State:          Waiting\n      Reason:       CrashLoopBackOff\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42\n      Started:      Wed, 22 Apr 2026 08:04:59 +0000\n      Finished:     Wed, 22 Apr 2026 08:04:59 +0000\n    Ready:          False\n    Restart Count:  10\n    Environment:    <none>\n    Mounts:\n      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-zndsj (ro)\nConditions:\n  Type              Status\n  Initialized       True \n  Ready             False \n  ContainersReady   False \n  PodScheduled      True \nVolumes:\n  kube-api-access-zndsj:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    TokenExpirationSeconds:  3607\n    ConfigMapName:           kube-root-ca.crt\n    ConfigMapOptional:       <nil>\n    DownwardAPI:             true\nQoS Class:                   BestEffort\nNode-Selectors:              <none>\nTolerations:                 node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\n                             node.kubernetes.io/unreachable:NoExecute op=Exists for 300s\nEvents:\n  Type     Reason          Age                   From               Message\n  ----     ------          ----                  ----               -------\n  Normal   Scheduled       26m                   default-scheduler  Successfully assigned aiops-e2e/appconfigfail-7649c79dc5-q4zjz to node2\n  Normal   AddedInterface  26m                   multus             Add eth0 [172.16.104.57/32] from k8s-pod-network\n  Normal   Pulled          25m (x5 over 26m)     kubelet            Container image \"busybox:1.36\" already present on machine\n  Normal   Created         25m (x5 over 26m)     kubelet            Created container app\n  Normal   Started         25m (x5 over 26m)     kubelet            Started container app\n  Warning  BackOff         107s (x116 over 26m)  kubelet            Back-off restarting failed container app in pod appconfigfail-7649c79dc5-q4zjz_aiops-e2e(77ea5d65-2a07-47e0-b606-3f03812dcc6a)", "duration_s": 0}, {"tool": "kubectl_events", "data": "LAST SEEN              TYPE      REASON           OBJECT                               MESSAGE\n26m                    Normal    Scheduled        Pod/appconfigfail-7649c79dc5-q4zjz   Successfully assigned aiops-e2e/appconfigfail-7649c79dc5-q4zjz to node2\n26m                    Normal    AddedInterface   Pod/appconfigfail-7649c79dc5-q4zjz   Add eth0 [172.16.104.57/32] from k8s-pod-network\n25m (x5 over 26m)      Normal    Pulled           Pod/appconfigfail-7649c79dc5-q4zjz   Container image \"busybox:1.36\" already present on machine\n25m (x5 over 26m)      Normal    Created          Pod/appconfigfail-7649c79dc5-q4zjz   Created container app\n25m (x5 over 26m)      Normal    Started          Pod/appconfigfail-7649c79dc5-q4zjz   Started container app\n108s (x116 over 26m)   Warning   BackOff          Pod/appconfigfail-7649c79dc5-q4zjz   Back-off restarting failed container app in pod appconfigfail-7649c79dc5-q4zjz_aiops-e2e(77ea5d65-2a07-47e0-b606-3f03812dcc6a)", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_namespace", "data": "NAME            READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES         SELECTOR            LABELS\nappconfigfail   0/1     1            0           26m   app          busybox:1.36   app=appconfigfail   l4-scenario=config-bootstrap-fail", "duration_s": 0}, {"tool": "kubectl_get_yaml", "data": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  annotations:\n    deployment.kubernetes.io/revision: \"1\"\n    kubectl.kubernetes.io/last-applied-configuration: |\n      {\"apiVersion\":\"apps/v1\",\"kind\":\"Deployment\",\"metadata\":{\"annotations\":{},\"labels\":{\"l4-scenario\":\"config-bootstrap-fail\"},\"name\":\"appconfigfail\",\"namespace\":\"aiops-e2e\"},\"spec\":{\"replicas\":1,\"selector\":{\"matchLabels\":{\"app\":\"appconfigfail\"}},\"template\":{\"metadata\":{\"labels\":{\"app\":\"appconfigfail\",\"l4-scenario\":\"config-bootstrap-fail\"}},\"spec\":{\"containers\":[{\"args\":[\"echo \\\"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\\\"\\necho \\\"L4_LAYER_APPLICATION: true\\\"\\necho \\\"L4_SCENARIO: config-bootstrap-fail\\\"\\necho \\\"L4_ERROR_TYPE: application-config-validation\\\"\\nif [ -z \\\"${APP_BOOT_MODE:-}\\\" ]; then\\n  echo \\\"FATAL: missing required APP_BOOT_MODE\\\"\\n  echo \\\"FATAL: business config validation failed before server startup\\\"\\n  exit 42\\nfi\\necho \\\"unexpected success\\\"\\nexit 1\\n\"],\"command\":[\"sh\",\"-c\"],\"image\":\"busybox:1.36\",\"imagePullPolicy\":\"Never\",\"name\":\"app\"}]}}}}\n  creationTimestamp: \"2026-04-22T07:38:39Z\"\n  generation: 1\n  labels:\n    l4-scenario: config-bootstrap-fail\n  name: appconfigfail\n  namespace: aiops-e2e\n  resourceVersion: \"46415682\"\n  uid: 99cdabf8-f7bb-4fde-be0d-23711032bd1e\nspec:\n  progressDeadlineSeconds: 600\n  replicas: 1\n  revisionHistoryLimit: 10\n  selector:\n    matchLabels:\n      app: appconfigfail\n  strategy:\n    rollingUpdate:\n      maxSurge: 25%\n      maxUnavailable: 25%\n    type: RollingUpdate\n  template:\n    metadata:\n      creationTimestamp: null\n      labels:\n        app: appconfigfail\n        l4-scenario: config-bootstrap-fail\n    spec:\n      containers:\n      - args:\n        - |\n          echo \"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\"\n          echo \"L4_LAYER_APPLICATION: true\"\n          echo \"L4_SCENARIO: config-bootstrap-fail\"\n          echo \"L4_ERROR_TYPE: application-config-validation\"\n          if [ -z \"${APP_BOOT_MODE:-}\" ]; then\n            echo \"FATAL: missing required APP_BOOT_MODE\"\n            echo \"FATAL: business config validation failed before server startup\"\n            exit 42\n          fi\n          echo \"unexpected success\"\n          exit 1\n        command:\n        - sh\n        - -c\n        image: busybox:1.36\n        imagePullPolicy: Never\n        name: app\n        resources: {}\n        terminationMessagePath: /dev/termination-log\n        terminationMessagePolicy: File\n      dnsPolicy: ClusterFirst\n      restartPolicy: Always\n      schedulerName: default-scheduler\n      securityContext: {}\n      terminationGracePeriodSeconds: 30\nstatus:\n  conditions:\n  - lastTransitionTime: \"2026-04-22T07:38:39Z\"\n    lastUpdateTime: \"2026-04-22T07:38:39Z\"\n    message: Deployment does not have minimum availability.\n    reason: MinimumReplicasUnavailable\n    status: \"False\"\n    type: Available\n  - lastTransitionTime: \"2026-04-22T07:48:40Z\"\n    lastUpdateTime: \"2026-04-22T07:48:40Z\"\n    message: ReplicaSet \"appconfigfail-7649c79dc5\" has timed out progressing.\n    reason: ProgressDeadlineExceeded\n    status: \"False\"\n    type: Progressing\n  observedGeneration: 1\n  replicas: 1\n  unavailableReplicas: 1\n  updatedReplicas: 1", "duration_s": 0}, {"tool": "run_bash_command", "data": "{\"success\": true, \"stdout\": \"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\\nL4_LAYER_APPLICATION: true\\nL4_SCENARIO: config-bootstrap-fail\\nL4_ERROR_TYPE: application-config-validation\\nFATAL: missing required APP_BOOT_MODE\\nFATAL: business config validation failed before server startup\\n\", \"stderr\": \"\", \"returncode\": 0}", "duration_s": 0}, {"tool": "execute_prometheus_instant_query", "data": "{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{\"instance\":\"10.2.0.49:9100\"},\"value\":[1776845142.289,\"9.892748319113032\"]},{\"metric\":{\"instance\":\"10.2.0.48:9100\"},\"value\":[1776845142.289,\"14.959722222219074\"]},{\"metric\":{\"instance\":\"10.2.0.50:9100\"},\"value\":[1776845142.289,\"2.238303484662485\"]}]}}", "duration_s": 0}, {"tool": "execute_prometheus_instant_query", "data": "{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{\"container\":\"node-exporter\",\"device\":\"/dev/mapper/ubuntu--vg-ubuntu--lv\",\"endpoint\":\"http-metrics\",\"fstype\":\"ext4\",\"instance\":\"10.2.0.49:9100\",\"job\":\"node-exporter\",\"mountpoint\":\"/\",\"namespace\":\"xnet\",\"pod\":\"observability-prometheus-node-exporter-wnbb8\",\"service\":\"observability-prometheus-node-exporter\"},\"value\":[1776845142.363,\"52.89390014304315\"]},{\"metric\":{\"container\":\"node-exporter\",\"device\":\"/dev/mapper/ubuntu--vg-ubuntu--lv\",\"endpoint\":\"http-metrics\",\"fstype\":\"ext4\",\"instance\":\"10.2.0.48:9100\",\"job\":\"node-exporter\",\"mountpoint\":\"/\",\"namespace\":\"xnet\",\"pod\":\"observability-prometheus-node-exporter-lj75r\",\"service\":\"observability-prometheus-node-exporter\"},\"value\":[1776845142.363,\"82.7431229963863\"]},{\"metric\":{\"container\":\"node-exporter\",\"device\":\"/dev/mapper/ubuntu--vg-ubuntu--lv\",\"endpoint\":\"http-metrics\",\"fstype\":\"ext4\",\"instance\":\"10.2.0.50:9100\",\"job\":\"node-exporter\",\"mountpoint\":\"/\",\"namespace\":\"xnet\",\"pod\":\"observability-prometheus-node-exporter-qp2qd\",\"service\":\"observability-prometheus-node-exporter\"},\"value\":[1776845142.363,\"54.98577518610625\"]}]}}", "duration_s": 0}, {"tool": "execute_prometheus_instant_query", "data": "{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{\"container\":\"node-exporter\",\"endpoint\":\"http-metrics\",\"instance\":\"10.2.0.49:9100\",\"job\":\"node-exporter\",\"namespace\":\"xnet\",\"pod\":\"observability-prometheus-node-exporter-wnbb8\",\"service\":\"observability-prometheus-node-exporter\"},\"value\":[1776845142.370,\"19.606488866804938\"]},{\"metric\":{\"container\":\"node-exporter\",\"endpoint\":\"http-metrics\",\"instance\":\"10.2.0.48:9100\",\"job\":\"node-exporter\",\"namespace\":\"xnet\",\"pod\":\"observability-prometheus-node-exporter-lj75r\",\"service\":\"observability-prometheus-node-exporter\"},\"value\":[1776845142.370,\"30.95284061584006\"]},{\"metric\":{\"container\":\"node-exporter\",\"endpoint\":\"http-metrics\",\"instance\":\"10.2.0.50:9100\",\"job\":\"node-exporter\",\"namespace\":\"xnet\",\"pod\":\"observability-prometheus-node-exporter-qp2qd\",\"service\":\"observability-prometheus-node-exporter\"},\"value\":[1776845142.370,\"9.348638930576925\"]}]}}", "duration_s": 0}], "llm_analysis": "## 集群状态总结\n\n### 整体健康状况 ✅\n\n| 维度 | 状态 | 详情 |\n|------|------|------|\n| **节点** | ✅ 全部 Ready | master, node1, node2 均正常运行 |\n| **控制面** | ✅ 正常 | etcd, apiserver, scheduler, controller-manager 均 Running |\n| **网络** | ✅ 正常 | Calico, CoreDNS, Multus 均正常运行 |\n| **存储** | ✅ 正常 | NFS provisioner Running |\n\n### 节点资源使用率\n\n| 节点 | CPU | 内存 | 磁盘 |\n|------|-----|------|------|\n| **master** (10.2.0.48) | 14.96% | 30.95% | **82.74%** 🔴 |\n| **node1** (10.2.0.49) | 9.89% | 19.61% | 52.89% |\n| **node2** (10.2.0.50) | 2.24% | 9.35% | 54.99% |\n\n> ⚠️ **注意**: master 节点的磁盘使用率已达 **82.74%**，需要关注。\n\n---\n\n### ❌ 唯一异常 Pod：`appconfigfail-7649c79dc5-q4zjz`\n\n| 项目 | 值 |\n|------|-----|\n| **命名空间** | `aiops-e2e` |\n| **状态** | `CrashLoopBackOff` |\n| **重启次数** | 10 次 |\n| **退出码** | `42`（业务自定义退出码，非 OOM） |\n| **节点** | node2 (10.2.0.50) |\n| **IP** | 172.16.104.57 |\n\n#### 根因分析\n\n容器启动命令会检查环境变量 `APP_BOOT_MODE`，但该变量**未设置**，导致业务配置校验失败并主动退出。\n\n**容器日志**：\n```\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_LAYER_APPLICATION: true\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup\n```\n\n#### 修复方案\n\n在 Deployment `appconfigfail` 的容器定义中补充环境变量：\n\n```yaml\nspec:\n  template:\n    spec:\n      containers:\n        - name: app\n          env:\n            - name: APP_BOOT_MODE\n              value: \"production\"   # 或其他所需值\n```\n\n可以通过 `kubectl edit deployment appconfigfail -n aiops-e2e` 或修改 YAML 文件后 `kubectl apply` 来修复。", "collection_summary": "计划 11 项，实际采集 11 项，未采集 0 项，完整度 100%", "evidence_inventory": [{"id": "cmd_0", "description": "执行命令: kubectl apply` 来修复。", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "extra_1", "description": "工具采集: kubectl_get_by_kind_in_cluster", "level": "important", "collected": true, "source": "thinking_extra"}, {"id": "extra_2", "description": "工具采集: helm_list_releases", "level": "important", "collected": true, "source": "thinking_extra"}, {"id": "extra_3", "description": "工具采集: kubectl_describe", "level": "important", "collected": true, "source": "thinking_extra"}, {"id": "extra_4", "description": "工具采集: kubectl_events", "level": "important", "collected": true, "source": "thinking_extra"}, {"id": "extra_5", "description": "工具采集: kubectl_get_by_kind_in_namespace", "level": "important", "collected": true, "source": "thinking_extra"}, {"id": "extra_6", "description": "工具采集: kubectl_get_yaml", "level": "important", "collected": true, "source": "thinking_extra"}, {"id": "extra_7", "description": "工具采集: run_bash_command", "level": "important", "collected": true, "source": "thinking_extra"}, {"id": "extra_8", "description": "工具采集: execute_prometheus_instant_query", "level": "important", "collected": true, "source": "thinking_extra"}, {"id": "extra_9", "description": "工具采集: execute_prometheus_instant_query", "level": "important", "collected": true, "source": "thinking_extra"}, {"id": "extra_10", "description": "工具采集: execute_prometheus_instant_query", "level": "important", "collected": true, "source": "thinking_extra"}], "missing_reasons": [], "early_stop": {"triggered": true, "reason": "critical 和 important 级证据均已满足，提前停止后续采集", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 11/11 项, 完整度: 100%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (43.5s)
   📤 → 下游数据: root_cause=
   confidence=95%
   causal_chain={"root_cause": "Deployment appconfigfail 的 Pod 模板中未定义环境变量 APP_BOOT_MODE", "propagation": "容器启动时，启动脚本执行环境变量检查 → 发现 APP_BOOT_MODE 缺失 → 输出 FATAL 日志并调用 exit(42) 主动退出", "direct_cause": "容器启动命令中要求必须设置 APP_BOOT_MODE 环境变量，但未配置该变量", "manifestation": "Pod appconfigfail-7649c79dc5-q4zjz 处于 CrashLoopBackOff 状态，已重启 10 次"}
   rca_analysis={"phenomenon": "集群中存在一个处于 CrashLoopBackOff 状态的 Pod，且 master 节点磁盘使用率较高", "evidence_inventory": [{"id": "e1", "content": "节点列表：master、node1、node2 均为 Ready 状态", "source": "kubectl_get_by_kind_in_cluster", "reliability": "高"}, {"id": "e2", "content": "Pod appconfigfail-7649c79dc5-q4zjz 状态为 CrashLoopBackOff，已重启 10 次", "source": "kubectl_get_by_kind_in_cluster", "reliability": "高"}, {"id": "e3", "content": "Pod 退出码为 42（业务自定义退出码）", "source": "问题定位结果（layer 节点输出）", "reliability": "高"}, {"id": "e4", "content": "容器日志输出：FATAL: missing required APP_BOOT_MODE", "source": "run_bash_command", "reliability": "高"}, {"id": "e5", "content": "容器日志输出：FATAL: business config validation failed before server startup", "source": "run_bash_command", "reliability": "高"}, {"id": "e6", "content": "Deployment appconfigfail 使用镜像 busybox:1.36", "source": "kubectl_get_by_kind_in_namespace", "reliability": "高"}, {"id": "e7", "content": "master 节点 CPU 使用率 14.96%，node1 9.89%，node2 2.24%", "source": "execute_prometheus_instant_query (证据9)", "reliability": "高"}, {"id": "e8", "content": "master 节点内存使用率 30.95%，node1 19.61%，node2 9.35%", "source": "execute_prometheus_instant_query (证据11)", "reliability": "高"}, {"id": "e9", "content": "master 节点磁盘使用率 82.74%，node1 52.89%，node2 54.99%", "source": "execute_prometheus_instant_query (证据10)", "reliability": "高"}, {"id": "e10", "content": "Pod 调度到 node2，网络正常分配 IP 172.16.104.57/32", "source": "kubectl_events", "reliability": "高"}, {"id": "e11", "content": "镜像拉取正常（事件中显示 Pulled）", "source": "kubectl_events", "reliability": "高"}, {"id": "e12", "content": "Pod 标签包含 l4-scenario=config-bootstrap-fail", "source": "kubectl_describe", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "master: Ready, node1: Ready, node2: Ready", "interpretation": "所有集群节点均处于健康状态，无节点级故障"}, {"evidence_id": "e2", "raw_data": "appconfigfail-7649c79dc5-q4zjz: CrashLoopBackOff, RESTARTS=10 (26s ago)", "interpretation": "Pod 反复崩溃重启，当前处于退避状态"}, {"evidence_id": "e3", "raw_data": "Exit Code: 42", "interpretation": "退出码 42 是业务自定义退出码，排除 OOM 和系统级错误"}, {"evidence_id": "e4", "raw_data": "FATAL: missing required APP_BOOT_MODE", "interpretation": "容器启动时检测到环境变量 APP_BOOT_MODE 未设置，这是导致退出的直接原因"}, {"evidence_id": "e5", "raw_data": "FATAL: business config validation failed before server startup", "interpretation": "业务配置校验失败，应用主动终止启动流程"}, {"evidence_id": "e6", "raw_data": "Image: busybox:1.36, Available: 0/1", "interpretation": "Deployment 副本数为 1，但 0 个可用，镜像拉取无问题"}, {"evidence_id": "e7", "raw_data": "master: 14.96%, node1: 9.89%, node2: 2.24%", "interpretation": "各节点 CPU 使用率均在正常范围内，无资源瓶颈"}, {"evidence_id": "e8", "raw_data": "master: 30.95%, node1: 19.61%, node2: 9.35%", "interpretation": "各节点内存使用率正常，无内存压力"}, {"evidence_id": "e9", "raw_data": "master: 82.74%, node1: 52.89%, node2: 54.99%", "interpretation": "master 节点磁盘使用率较高（82.74%），但未触发节点级故障，与当前 Pod 问题无直接关联"}, {"evidence_id": "e10", "raw_data": "Pod assigned to node2, IP 172.16.104.57/32", "interpretation": "Pod 调度和网络配置均正常完成"}, {"evidence_id": "e11", "raw_data": "Pulled (x5 over 26m)", "interpretation": "镜像拉取成功，排除镜像问题"}, {"evidence_id": "e12", "raw_data": "Labels: l4-scenario=config-bootstrap-fail", "interpretation": "该 Pod 是测试场景配置启动失败的验证用例"}], "causal_chain": {"root_cause": "Deployment appconfigfail 的 Pod 模板中未定义环境变量 APP_BOOT_MODE", "propagation": "容器启动时，启动脚本执行环境变量检查 → 发现 APP_BOOT_MODE 缺失 → 输出 FATAL 日志并调用 exit(42) 主动退出", "direct_cause": "容器启动命令中要求必须设置 APP_BOOT_MODE 环境变量，但未配置该变量", "manifestation": "Pod appconfigfail-7649c79dc5-q4zjz 处于 CrashLoopBackOff 状态，已重启 10 次"}, "root_cause_summary": "Pod appconfigfail-7649c79dc5-q4zjz（命名空间 aiops-e2e，节点 node2，IP 172.16.104.57）处于 CrashLoopBackOff 状态，已重启 10 次。容器日志明确输出 'FATAL: missing required APP_BOOT_MODE' 和 'FATAL: business config validation failed before server startup'，退出码为 42（业务自定义退出码）。根因是 Deployment appconfigfail 的 Pod 模板中未设置环境变量 APP_BOOT_MODE，导致容器启动时业务配置校验失败并主动退出。该 Pod 的标签 l4-scenario=config-bootstrap-fail 也表明这是一个配置启动失败的测试场景。集群其他组件（节点、控制面、网络、存储）均正常，master 节点磁盘使用率 82.74% 需关注，但与当前 Pod 问题无关。", "confidence": 0.95, "primary_runbooks": [], "alternative_causes": [{"cause": "启动脚本逻辑错误", "reason": "若 APP_BOOT_MODE 不是必需的，但脚本强制要求，则属于应用代码问题，但标签和日志明确指向配置校验测试场景，因此可能性低"}], "limitations": "仅获取了 Pod 的容器日志和退出码，未查看 Deployment 的完整 YAML 定义（last-applied-configuration 被截断），无法确认当前是否有默认值配置。master 节点磁盘使用率 82.74% 的详细原因未深入分析，可能影响节点长期稳定性。Prometheus 数据为瞬时查询，未获取时间序列趋势。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 95%
   🔗 因果链:
     根本原因: Deployment appconfigfail 的 Pod 模板中未定义环境变量 APP_BOOT_MODE
     传导机制: 容器启动时，启动脚本执行环境变量检查 → 发现 APP_BOOT_MODE 缺失 → 输出 FATAL 日志并调用 exit(42) 主动退出
     最终表现: Pod appconfigfail-7649c79dc5-q4zjz 处于 CrashLoopBackOff 状态，已重启 10 次


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (50.6s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5608 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 50.6s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将根据您提供的三个阶段分析结果，为您生成一份详尽、完整的诊断报告。

---
## 📊 诊断概览

**针对您的核心问题「我的集群有什么问题」的总结：**

您的集群整体健康状况良好，但存在以下两个需关注的问题：

1.  **一个异常 Pod**：`aiops-e2e` 命名空间下的 `appconfigfail-7649c79dc5-q4zjz` 处于 `CrashLoopBackOff` 状态，无法正常运行。
2.  **一个资源预警**：`master` 节点（`10.2.0.48`）的磁盘使用率已达 **82.74%**，需要关注以防止未来出现磁盘空间不足问题。

| 项目 | 内容 |
|------|------|
| **问题层级** | L4 - 应用层 (主问题) / L0 - 基础设施层 (预警) |
| **问题分类** | 主问题: 应用启动配置校验失败 (Config Bootstrap Fail) <br> 预警: 节点磁盘空间使用率偏高 |
| **置信度** | 高 (95%) - 针对应用启动问题 |
| **证据完整度** | 11/11 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| 异常 Pod | `appconfigfail-7649c79dc5-q4zjz` |
| Namespace | `aiops-e2e` |
| Node | `node2` (Pod 所在节点) / `master` (磁盘预警节点) |
| 错误信息 (Pod) | `Exit Code: 42`, `FATAL: missing required APP_BOOT_MODE` |
| 状态 (Pod) | `CrashLoopBackOff`, 已重启 10 次 |
| 磁盘使用率 (master) | **82.74%** |

---

## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl_get_by_kind_in_cluster` | `aiops-e2e/appconfigfail-7649c79dc5-q4zjz` 状态 `CrashLoopBackOff`，重启 10 次 | Pod 持续崩溃重启，无法正常工作 |
| 2 | 退出码 | `kubectl_describe` | `Exit Code: 42` | 业务自定义退出码，非系统级错误（如 OOM） |
| 3 | 容器日志 | `run_bash_command` | `FATAL: missing required APP_BOOT_MODE` <br> `FATAL: business config validation failed before server startup` | 应用启动时因缺少必需的环境变量 `APP_BOOT_MODE` 而主动退出 |
| 4 | 资源配置 | `kubectl_get_yaml` | Deployment 的 Pod 模板中未定义 `env` 字段 | Pod 运行时未注入 `APP_BOOT_MODE` 环境变量 |
| 5 | 镜像拉取 | `kubectl_events` | `Container image "busybox:1.36" already present on machine` | 镜像拉取正常，排除镜像相关问题 |
| 6 | Pod 标签 | `kubectl_describe` | `l4-scenario=config-bootstrap-fail` | Pod 明确标记为“配置启动失败”测试场景，与日志和退出码吻合 |
| 7 | 节点磁盘 | `execute_prometheus_instant_query` | `master` 节点磁盘使用率 **82.74%**，`node1` 52.89%，`node2` 54.99% | Master 节点磁盘使用率偏高，已触发预警级别 |
| 8 | 节点状态 | `kubectl_get_by_kind_in_cluster` | `master`，`node1`，`node2` 均为 `Ready` 状态 | 节点均正常运行，无节点级故障 |

### 证据关联分析
- **证据 #1 + #2 + #3 + #4 印证**：Pod 持续重启（#1）是因业务自定义退出码 `42`（#2），由启动脚本检测到环境变量 `APP_BOOT_MODE` 缺失（#3）并主动退出导致，而该环境变量在 Deployment 配置中未被定义（#4）。
- **证据链**：Deployment 未定义环境变量 `APP_BOOT_MODE` → 容器启动时脚本检查失败 → 输出 FATAL 日志 → 执行 `exit 42` → Pod 状态变为 `Error` → Kubelet 持续重启 Pod → 最终进入 `CrashLoopBackOff`。
- **证据 #6** 的标签 `config-bootstrap-fail` 完美印证了整个问题场景。

### 缺失证据
本次分析证据完整，无缺失。

---

## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Deployment "appconfigfail" 的 Pod 模板未定义 APP_BOOT_MODE 变量  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器启动 → 执行启动脚本 → 检查 APP_BOOT_MODE 变量              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 脚本发现变量为空/未设置 → 输出 FATAL 日志 → 调用 exit(42)     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CrashLoopBackOff，持续重启，应用无法启动             │
└─────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #3 (日志 `FATAL: missing required APP_BOOT_MODE`) 和证据 #4 (Deployment YAML 无环境变量定义)，问题的根本原因是 **Deployment `appconfigfail` 的 Pod 模板中缺少 `APP_BOOT_MODE` 环境变量的定义**。这导致容器启动时业务配置校验失败，应用主动退出（Exit Code 42）并陷入 CrashLoopBackOff。

**置信度**：高 (95%)
- ✅ 容器日志明确指向变量缺失
- ✅ 退出码为业务自定义，排除了系统级错误
- ✅ Pod 标签与问题场景完全匹配
- ⚠️ master 节点磁盘使用率 82.74% 为预警，与当前 Pod 问题无直接关联，但需关注。

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [必须] 为 Deployment 添加缺失的环境变量 `APP_BOOT_MODE`**
**直接编辑 Deployment：**
```bash
kubectl edit deployment appconfigfail -n aiops-e2e
```
在 `spec.template.spec.containers[0]` 下添加 `env` 字段：
```yaml
...
spec:
  template:
    spec:
      containers:
        - name: app
          env:
            - name: APP_BOOT_MODE
              value: "production"   # 根据应用要求填写，例如 "production" 或 "development"
...
```

**或使用补丁命令直接修改：**
```bash
kubectl patch deployment appconfigfail -n aiops-e2e --type='json' -p='[{"op": "add", "path": "/spec/template/spec/containers/0/env", "value": [{"name": "APP_BOOT_MODE", "value": "production"}]}]'
```
*依据*：证据 #3 和 #4 表明缺失该变量是根因。

**2. [必须] 监控 master 节点磁盘使用率**
```bash
# 检查磁盘空间占用详情
ssh <master-node> 'df -h / && echo "---" && du -sh /var/log/* /var/lib/docker/* /tmp/* 2>/dev/null | sort -rh | head -20'
```
*目的*：找出占用磁盘空间的主要目录（如日志、镜像、临时文件）并进行清理。

### 后续优化
1. **监控告警**：为节点磁盘使用率配置告警（如 > 80% 触发 Warning，> 90% 触发 Critical）。
2. **资源配置**：对于应用所需的配置（如环境变量、配置文件），应通过 ConfigMap 或 Secret 统一管理，避免硬编码在启动脚本中。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 验证 Pod 正常启动 | `kubectl get pod appconfigfail-7649c79dc5-q4zjz -n aiops-e2e` | `STATUS: Running` |
| 2. 检查 Pod 重启次数 | `kubectl get pod appconfigfail-7649c79dc5-q4zjz -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 值为 `0`，不再增加 |
| 3. 检查 Deployment 可用性 | `kubectl get deployment appconfigfail -n aiops-e2e` | `AVAILABLE` 列为 `1` |
| 4. 验证 master 节点磁盘 | `kubectl top node master` (如不可用，通过 Prometheus 查询 `node_filesystem_avail_bytes`) | 磁盘使用率下降或保持稳定 |

---

## ⚠️ 注意事项
- 修复后，旧 Pod 会被新 Pod 替换，重启次数会归零。
- 如果 `APP_BOOT_MODE` 的值有特定要求，请根据应用文档或开发人员确认。示例中使用了 `production`。
- Master 节点磁盘使用率 82.74% 虽然目前未造成问题，但存在隐患，建议尽快进行排查和清理。

---

## 📊 性能统计

├─ 总耗时: 2.8m
├─ 问题定位: 39.8s (23%) ✅
├─ 证据链采集: 36.6s (21%) ✅
├─ 根因分析: 43.5s (26%) ✅
├─ 汇总总结: 50.6s (30%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 18 次
```

📋 诊断追踪

- **参考 Runbook**: l4-config-bootstrap-fail, private-k8s-health-reference
- **工具调用**: 18 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
