======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: a1fc60f328ad4808]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，我来对集群进行健康检查。首先，我会先做轻量状态确认，查看节点和 Pod 的整体状态。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# 私有化 Kubernetes 环境健康与高效排查参考手册

> 类型: reference | 适用: 私有化 Kubernetes 环境 | 环境特征: Calico + NFS + containerd

## 目的

本手册不是某个具体故障的处理步骤，而是一个**额外知识参考**：
- 帮助理解在私有化 Kubernetes 环境中，健康检查应重点关注哪些资源与信号

   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS             RESTARTS      AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     app
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   209d   v1.26.8  
   💭 [问题定位] 我看到有一个明显的异常 Pod。让我进一步查看详情。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             appconfigfail-7649c79dc5-q4zjz
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Wed, 22 Apr 2026 07:38:39
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 NAME                             READY   STATUS             RESTARTS       AGE   IP              NODE    NOMINATED NODE   READINESS GATES   LABELS
appconfigfail-7649c79dc5-q4zjz   0/1     CrashLoopBac
   💭 [问题定位] 这个 Pod 的标签 `l4-scenario=config-bootstrap-fail` 明确标注了这是一个 L4 配置启动失败场景。让我获取相关的 runbook 进一步确认。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# L4 应用启动配置校验失败 (Config Bootstrap Fail)

> 层级: L4 - 应用层 | 场景: 应用在启动阶段因业务配置缺失或非法而主动退出

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | `CrashLoopBackOff` / `Error`，重启次数持续增加 |
| 容器日志 | 含
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                     TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)                                                                                               
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                               READY   UP-TO-DATE   AVAILABLE   AGE     CONTAINERS                                                                      IMAGES                        
   💭 [问题定位] 让我看一下节点 conditions 和 PVC 状态以完成全面检查。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE   NAME                                                 STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE     VOLUMEMODE   LABELS
aaa         re
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:               master
Roles:              control-plane
Labels:             beta.kubernetes.io/arch=amd64
                    beta.kubernetes.io/os=linux
                    kubernetes.io/arch=am
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
    
   💭 [问题定位] 现在我已经获得了足够的信息来进行完整诊断。以下是分析结果：

---

## 诊断结果

### 总体概况

集群整体**基本健康**，但存在 **1 个明确异常对象**。

### 检查面分析

| 检查面 | 状态 |
|--------|------|
| **节点 (Nodes)** | ✅ 全部 Ready（master/node1/node2），无 Pressure、无 Taint |
| **控制面组件** | ✅ etcd、kube-apiserver、kube-controller-manager、kube-scheduler、CoreDNS、Calico 均 Running |
| **Service/Endpoints** | ✅ 各 Service 有对应 Pod，无明显异常 |
| **存储 (PVC/PV)** | ✅ 所有 PVC 均 Bound，无 Pending |
| **工作负载** | ⚠️ **1 个异常 Pod** |

### 当前异常对象

Pod `appconfigfail-7649c79dc5-q4zjz`（命名空间 `aiops-e2e`）

| 属性 | 值 |
|------|-----|
| Status | `CrashLoopBackOff`（7 次重启） |
| Exit Code | **42**（非 137，非 OOM） |
| 容器日志 | 明确输出 `FATAL: missing required APP_BOOT_MODE` |
| 标签 | `l4-scenario=config-bootstrap-fail` |
| 镜像 | `busybox:1.36`，已存在于本地（非镜像拉取问题） |
| 无 | OOMKilled、Evicted、ImagePullBackOff |

```json
{
  "layer": "L4",
  "layers": ["L4"],
  "layer_name": "应用层",
  "confidence": 0.98,
  "reasoning": "Pod appconfigfail-7649c79dc5-q4zjz 处于 CrashLoopBackOff，Exit Code=42（业务退出码），容器日志明确输出 'FATAL: missing required APP_BOOT_MODE'，标签 l4-scenario=config-bootstrap-fail 也指向此场景。无 OOMKilled（排除 L2）、无 ImagePullBackOff（排除 L3）、无 Evicted/disk pressure（排除 L0）、节点均 Ready（排除 L1），因此确定为 L4 应用层问题。",
  "key_entities": [
    {"type": "Pod", "value": "appconfigfail-7649c79dc5-q4zjz"},
    {"type": "Namespace", "value": "aiops-e2e"},
    {"type": "Deployment", "value": "appconfigfail"}
  ],
  "possible_scenarios": [
    "应用启动配置校验失败 (L4 Config Bootstrap Fail) - 容器启动时缺少必填环境变量 APP_BOOT_MODE，导致业务配置校验失败主动退出"
  ]
}
```

### 简要说明

- **集群层面**：所有 3 个节点（master/node1/node2）均 Ready，无 MemoryPressure/DiskPressure/PIDPressure，控制面组件（etcd、apiserver、scheduler、controller-manager、CoreDNS、Calico、kube-proxy）全部正常。PVC 全部 Bound。整体集群基础设施健康。
- **唯一异常**：`aiops-e2e` 命名空间下的 `appconfigfail` Deployment 的 Pod 因**缺少必填环境变量 `APP_BOOT_MODE`** 而持续 CrashLoopBackOff（Exit Code 42），属于应用层（L4）配置问题。
- **建议修复**：为 Deployment 补充环境变量 `APP_BOOT_MODE` 的配置（通过 env、ConfigMap 或 Secret 注入）。
   ✅ [问题定位] 完成 (39.8s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=['应用启动配置校验失败 (L4 Config Bootstrap Fail) - 容器启动时缺少必填环境变量 APP_BOOT_MODE，导致业务配置校验失败主动退出']
   entities=[{"type": "Pod", "value": "appconfigfail-7649c79dc5-q4zjz"}, {"type": "Namespace", "value": "aiops-e2e"}, {"type": "Deployment", "value": "appconfigfail"}]
   reasoning=Pod appconfigfail-7649c79dc5-q4zjz 处于 CrashLoopBackOff，Exit Code=42（业务退出码），容器日志明确输出 'FATAL: missing required APP_BOOT_MODE'，标签 l4-scenario=config-bootstrap-fail 也指向此场景。无 OOMKilled（排除 L2）、无 ImagePullBackOff（排除 L3）、无 Evicted/disk pressure（排除 L0）、节点均 Ready（排除 L1），因此确定为 L4 应用层问题。
   layer_analysis={"layer": "L4", "layers": ["L4"], "layer_name": "应用层", "confidence": 0.98, "reasoning": "Pod appconfigfail-7649c79dc5-q4zjz 处于 CrashLoopBackOff，Exit Code=42（业务退出码），容器日志明确输出 'FATAL: missing required APP_BOOT_MODE'，标签 l4-scenario=config-bootstrap-fail 也指向此场景。无 OOMKilled（排除 L2）、无 ImagePullBackOff（排除 L3）、无 Evicted/disk pressure（排除 L0）、节点均 Ready（排除 L1），因此确定为 L4 应用层问题。", "key_entities": [{"type": "Pod", "value": "appconfigfail-7649c79dc5-q4zjz"}, {"type": "Namespace", "value": "aiops-e2e"}, {"type": "Deployment", "value": "appconfigfail"}], "possible_scenarios": ["应用启动配置校验失败 (L4 Config Bootstrap Fail) - 容器启动时缺少必填环境变量 APP_BOOT_MODE，导致业务配置校验失败主动退出"]}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 98%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我来全面检查集群的健康状况。
   💭 [证据链采集] 调用工具: TodoWrite
   💭 [证据链采集] 工具结果: TodoWrite (success)
      📄 Investigation plan updated with 4 tasks.

# CURRENT INVESTIGATION TASKS

**Task Status**: 0 completed, 1 in progress, 3 pending

[ ] [2] 检查系统组件Pod状态
[ ] [3] 检查异常工作负载
[ ] [4] 汇总问题并输出结果
[~] [1] 检查集群节点状态
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 调用工具: kubernetes_tabular_query
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   209d   v1.26.8  
   💭 [证据链采集] 工具结果: kubernetes_tabular_query (success)
      📄 NAME     STATUS   TAINTS
master   True     <none>
node1    True     <none>
node2    True     <none>
   💭 [证据链采集] 节点全部 Ready。继续检查系统组件和异常工作负载。
   💭 [证据链采集] 调用工具: TodoWrite
   💭 [证据链采集] 工具结果: TodoWrite (success)
      📄 Investigation plan updated with 4 tasks.

# CURRENT INVESTIGATION TASKS

**Task Status**: 1 completed, 1 in progress, 2 pending

[ ] [3] 检查异常工作负载
[ ] [4] 汇总问题并输出结果
[~] [2] 检查系统组件Pod状态
[✓] [1] 检查集群节点状态
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS             RESTARTS        AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     a
   💭 [证据链采集] 现在看看那个异常 Pod 的详细信息，以及 Deployments 状态。
   💭 [证据链采集] 调用工具: TodoWrite
   💭 [证据链采集] 工具结果: TodoWrite (success)
      📄 Investigation plan updated with 4 tasks.

# CURRENT INVESTIGATION TASKS

**Task Status**: 2 completed, 1 in progress, 1 pending

[ ] [4] 汇总问题并输出结果
[~] [3] 检查异常工作负载
[✓] [1] 检查集群节点状态
[✓] [2] 检查系统组件Pod状态
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:             appconfigfail-7649c79dc5-q4zjz
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Wed, 22 Apr 2026 07:38:39
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 LAST SEEN            TYPE      REASON           OBJECT                               MESSAGE
15m                  Normal    Scheduled        Pod/appconfigfail-7649c79dc5-q4zjz   Successfully assigned 
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 NAME            READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES         SELECTOR            LABELS
appconfigfail   0/1     1            0           15m   app          busybox:1.36   app=app
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE   NAME                                      READY   AGE   CONTAINERS                     IMAGES                                                                                               
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                               READY   UP-TO-DATE   AVAILABLE   AGE     CONTAINERS                                                                      IMAGES                        
   💭 [证据链采集] 让我看看这个异常 Pod 的日志来确认根因。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_LAYER_APPLICATION: true\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: appl
   💭 [证据链采集] 调用工具: TodoWrite
   💭 [证据链采集] 工具结果: TodoWrite (success)
      📄 Investigation plan updated with 4 tasks.

# CURRENT INVESTIGATION TASKS

**Task Status**: 3 completed, 1 in progress, 0 pending

[~] [4] 汇总问题并输出结果
[✓] [1] 检查集群节点状态
[✓] [2] 检查系统组件Pod状态
[✓] [3] 检查异常工作负载
   💭 [证据链采集] 调用工具: TodoWrite
   💭 [证据链采集] 工具结果: TodoWrite (success)
      📄 Investigation plan updated with 4 tasks.

# CURRENT INVESTIGATION TASKS

**Task Status**: 4 completed, 0 in progress, 0 pending

[✓] [1] 检查集群节点状态
[✓] [2] 检查系统组件Pod状态
[✓] [3] 检查异常工作负载
[✓] [4] 汇总问题并输出结果
   💭 [证据链采集] ---

## 📋 集群健康检查报告

### ✅ 集群整体健康概览

| 检查项 | 状态 |
|--------|------|
| **节点** | ✅ 3/3 Ready（master、node1、node2） |
| **节点 Taints** | ✅ 无异常 Taints |
| **系统组件** | ✅ 全部 Running（etcd、apiserver、scheduler、controller-manager、coredns、calico、kube-proxy、multus） |
| **工作负载** | ⚠️ **1 个异常**（见下方详情） |

---

### ⚠️ 发现的唯一问题：`aiops-e2e/appconfigfail`

| 字段 | 值 |
|------|-----|
| **Namespace** | `aiops-e2e` |
| **Pod** | `appconfigfail-7649c79dc5-q4zjz` |
| **状态** | `CrashLoopBackOff`（已重启 7 次） |
| **节点** | node2 (10.2.0.50) |
| **Deployment** | `appconfigfail` — **可用副本 0/1** |
| **退出码** | `42`（业务主动退出，非 OOM/信号终止） |

#### 🔍 根因分析

容器启动脚本中检查了环境变量 `APP_BOOT_MODE`：

```
FATAL: missing required APP_BOOT_MODE
FATAL: business config validation failed before server startup
```

Pod 的 `Environment: <none>` — 未设置任何环境变量，导致业务配置校验失败，主动退出（退出码 42）。

**层级**: L4（应用层 — 启动配置校验失败）

#### ✅ 已排除的其他层级问题

- ❌ L0（基础设施）— 无 Evicted、DiskPressure
- ❌ L1（节点）— 无 MemoryPressure/DiskPressure/PIDPressure
- ❌ L2（容器运行时）— 非 OOMKilled，退出码非 137
- ❌ L3（镜像/调度）— 镜像 `busybox:1.36` 已存在于本地，Pod 正常调度

---

### ✅ 其他所有工作负载均正常运行

包括 `aiops-copilot`、`nfs-client-provisioner`、`coredns`、`calico`、`xnet` 命名空间下的所有 observability 组件（Prometheus、Grafana、Elasticsearch、ClickHouse、Alertmanager 等）全部正常。

---

### 🛠 建议修复

在 Deployment `appconfigfail` 的 Pod 规格中为容器 `app` 添加必填环境变量：

```yaml
env:
- name: APP_BOOT_MODE
  value: "production"
```
   ✅ [证据链采集] 完成 (38.0s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan": [], "tool_results": [], "tool_data": [{"tool": "TodoWrite", "data": "Investigation plan updated with 4 tasks.\n\n# CURRENT INVESTIGATION TASKS\n\n**Task Status**: 0 completed, 1 in progress, 3 pending\n\n[ ] [2] 检查系统组件Pod状态\n[ ] [3] 检查异常工作负载\n[ ] [4] 汇总问题并输出结果\n[~] [1] 检查集群节点状态\n\n**Instructions**: Use TodoWrite tool to update task status as you work.", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_cluster", "data": "NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nmaster   Ready    control-plane   209d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          209d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-174-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          209d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-174-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux", "duration_s": 0}, {"tool": "kubernetes_tabular_query", "data": "NAME     STATUS   TAINTS\nmaster   True     <none>\nnode1    True     <none>\nnode2    True     <none>", "duration_s": 0}, {"tool": "TodoWrite", "data": "Investigation plan updated with 4 tasks.\n\n# CURRENT INVESTIGATION TASKS\n\n**Task Status**: 1 completed, 1 in progress, 2 pending\n\n[ ] [3] 检查异常工作负载\n[ ] [4] 汇总问题并输出结果\n[~] [2] 检查系统组件Pod状态\n[✓] [1] 检查集群节点状态\n\n**Instructions**: Use TodoWrite tool to update task status as you work.", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_cluster", "data": "NAMESPACE     NAME                                                READY   STATUS             RESTARTS        AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\naiops-e2e     appconfigfail-7649c79dc5-q4zjz                      0/1     CrashLoopBackOff   7 (4m47s ago)   15m     172.16.104.57    node2    <none>           <none>            app=appconfigfail,l4-scenario=config-bootstrap-fail,pod-template-hash=7649c79dc5\naiops         aiops-copilot-76779bb6df-4bcrf                      1/1     Running            0               6h16m   172.16.104.29    node2    <none>           <none>            app=aiops-copilot,pod-template-hash=76779bb6df\ndefault       dns-test-existing                                   1/1     Running            0               2d2h    172.16.166.148   node1    <none>           <none>            run=dns-test-existing\ndefault       exec-test                                           1/1     Running            0               2d4h    172.16.104.8     node2    <none>           <none>            run=exec-test\ndefault       network-test-from-running                           1/1     Running            0               2d2h    172.16.104.50    node2    <none>           <none>            run=network-test-from-running\ndefault       nfs-client-provisioner-6fcd4994c9-lczf6             1/1     Running            4 (5d ago)      86d     172.16.104.41    node2    <none>           <none>            app=nfs-client-provisioner,pod-template-hash=6fcd4994c9\nkube-system   calico-kube-controllers-6c67f9d475-2xcb7            1/1     Running            4 (5d ago)      28d     172.16.166.133   node1    <none>           <none>            k8s-app=calico-kube-controllers,pod-template-hash=6c67f9d475\nkube-system   calico-node-4kp26                                   1/1     Running            12 (5d1h ago)   183d    10.2.0.48        master   <none>           <none>            controller-revision-hash=65f554db6,k8s-app=calico-node,pod-template-generation=1\nkube-system   calico-node-d2dhp                                   1/1     Running            13 (5d ago)     183d    10.2.0.50        node2    <none>           <none>            controller-revision-hash=65f554db6,k8s-app=calico-node,pod-template-generation=1\nkube-system   calico-node-mnrjs                                   1/1     Running            12 (5d ago)     183d    10.2.0.49        node1    <none>           <none>            controller-revision-hash=65f554db6,k8s-app=calico-node,pod-template-generation=1\nkube-system   coredns-777df594b8-j4857                            1/1     Running            4 (5d ago)      28d     172.16.166.129   node1    <none>           <none>            k8s-app=kube-dns,pod-template-hash=777df594b8\nkube-system   coredns-777df594b8-s8r4n                            1/1     Running            4 (5d ago)      28d     172.16.166.185   node1    <none>           <none>            k8s-app=kube-dns,pod-template-hash=777df594b8\nkube-system   etcd-master                                         1/1     Running            13 (5d1h ago)   209d    10.2.0.48        master   <none>           <none>            component=etcd,tier=control-plane\nkube-system   kube-apiserver-master                               1/1     Running            13 (5d ago)     209d    10.2.0.48        master   <none>           <none>            component=kube-apiserver,tier=control-plane\nkube-system   kube-controller-manager-master                      1/1     Running            36 (5d1h ago)   209d    10.2.0.48        master   <none>           <none>            component=kube-controller-manager,tier=control-plane\nkube-system   kube-multus-ds-rnvbg                                1/1     Running            12 (5d ago)     183d    10.2.0.49        node1    <none>           <none>            app=multus,controller-revision-hash=6d4c8546fc,name=multus,pod-template-generation=1,tier=node\nkube-system   kube-multus-ds-sc2jn                                1/1     Running            4 (5d1h ago)    85d     10.2.0.48        master   <none>           <none>            app=multus,controller-revision-hash=6d4c8546fc,name=multus,pod-template-generation=1,tier=node\nkube-system   kube-multus-ds-x7h9s                                1/1     Running            13 (5d ago)     183d    10.2.0.50        node2    <none>           <none>            app=multus,controller-revision-hash=6d4c8546fc,name=multus,pod-template-generation=1,tier=node\nkube-system   kube-proxy-69zzr                                    1/1     Running            4 (5d ago)      28d     10.2.0.50        node2    <none>           <none>            controller-revision-hash=7d99996759,k8s-app=kube-proxy,pod-template-generation=1\nkube-system   kube-proxy-bblvc                                    1/1     Running            4 (5d ago)      28d     10.2.0.49        node1    <none>           <none>            controller-revision-hash=7d99996759,k8s-app=kube-proxy,pod-template-generation=1\nkube-system   kube-proxy-wbh4k                                    1/1     Running            4 (5d1h ago)    27d     10.2.0.48        master   <none>           <none>            controller-revision-hash=7d99996759,k8s-app=kube-proxy,pod-template-generation=1\nkube-system   kube-scheduler-master                               1/1     Running            38 (5d ago)     209d    10.2.0.48        master   <none>           <none>            component=kube-scheduler,tier=control-plane\nmcp           mcp-server-manager-8677f6896c-d4mr9                 1/1     Running            0               46h     172.16.104.59    node2    <none>           <none>            app=mcp-server-manager,pod-template-hash=8677f6896c\nxnet          alertmanager-observability-alertmanager-0           2/2     Running            8 (5d ago)      23d     172.16.166.161   node1    <none>           <none>            alertmanager=observability-alertmanager,app.kubernetes.io/instance=observability-alertmanager,app.kubernetes.io/managed-by=prometheus-operator,app.kubernetes.io/name=alertmanager,app.kubernetes.io/version=0.28.1,controller-revision-hash=alertmanager-observability-alertmanager-6c9cfbf844,statefulset.kubernetes.io/pod-name=alertmanager-observability-alertmanager-0\nxnet          api-server-6bd6bf8d6f-27svp                         1/1     Running            4 (5d1h ago)    23d     172.16.219.106   master   <none>           <none>            app=api-server,pod-template-hash=6bd6bf8d6f\nxnet          deepflow-agent-pcknn                                1/1     Running            9 (5d ago)      23d     172.16.166.181   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow-agent,app=deepflow,component=deepflow-agent,controller-revision-hash=54856d959b,pod-template-generation=1\nxnet          deepflow-agent-trc8k                                1/1     Running            7 (5d ago)      19d     172.16.104.7     node2    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow-agent,app=deepflow,component=deepflow-agent,controller-revision-hash=54856d959b,pod-template-generation=1\nxnet          deepflow-agent-whn22                                1/1     Running            8 (5d ago)      23d     172.16.219.97    master   <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow-agent,app=deepflow,component=deepflow-agent,controller-revision-hash=54856d959b,pod-template-generation=1\nxnet          elasticsearch-master-0                              1/1     Running            4 (5d ago)      23d     172.16.219.109   master   <none>           <none>            app=elasticsearch-master,chart=observability,controller-revision-hash=elasticsearch-master-695ff9864f,release=observability,statefulset.kubernetes.io/pod-name=elasticsearch-master-0\nxnet          ham-p9dxv                                           1/1     Running            14 (5d ago)     177d    172.16.104.21    node2    <none>           <none>            app=ham,controller-revision-hash=f65f887d,pod-template-generation=1\nxnet          ham-qzjg5                                           1/1     Running            4 (5d1h ago)    85d     172.16.219.112   master   <none>           <none>            app=ham,controller-revision-hash=f65f887d,pod-template-generation=1\nxnet          ham-wt9kh                                           1/1     Running            13 (5d ago)     177d    172.16.166.187   node1    <none>           <none>            app=ham,controller-revision-hash=f65f887d,pod-template-generation=1\nxnet          lgtm-5dc5c67d5f-sc286                               1/1     Running            4 (5d ago)      23d     172.16.166.151   node1    <none>           <none>            app=lgtm,pod-template-hash=5dc5c67d5f\nxnet          observability-clickhouse-0                          1/1     Running            4 (5d ago)      23d     172.16.166.137   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=clickhouse,app=deepflow,component=clickhouse,controller-revision-hash=observability-clickhouse-75b8d58ccc,statefulset.kubernetes.io/pod-name=observability-clickhouse-0\nxnet          observability-deepflow-app-654fcfbfbf-q8st6         1/1     Running            4 (5d ago)      23d     172.16.166.160   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow,app=deepflow,component=deepflow-app,pod-template-hash=654fcfbfbf\nxnet          observability-deepflow-server-774dd6c5b7-9c998      1/1     Running            14 (5d ago)     23d     172.16.166.135   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow,app=deepflow,component=deepflow-server,pod-template-hash=774dd6c5b7\nxnet          observability-filebeat-ffwsp                        1/1     Running            4 (5d1h ago)    23d     172.16.219.80    master   <none>           <none>            app=observability-filebeat,chart=observability-1.0.2,controller-revision-hash=57fb88b7c5,heritage=Helm,pod-template-generation=1,release=observability\nxnet          observability-filebeat-m58xw                        1/1     Running            5 (5d ago)      23d     172.16.166.134   node1    <none>           <none>            app=observability-filebeat,chart=observability-1.0.2,controller-revision-hash=57fb88b7c5,heritage=Helm,pod-template-generation=1,release=observability\nxnet          observability-filebeat-w6gtr                        1/1     Running            5 (5d ago)      19d     172.16.104.53    node2    <none>           <none>            app=observability-filebeat,chart=observability-1.0.2,controller-revision-hash=57fb88b7c5,heritage=Helm,pod-template-generation=1,release=observability\nxnet          observability-grafana-58bf9cfd6f-ndsxr              4/4     Running            36 (5d ago)     23d     172.16.166.144   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=grafana,app.kubernetes.io/version=12.0.2,helm.sh/chart=grafana-9.2.7,pod-template-hash=58bf9cfd6f\nxnet          observability-kepler-2sgrr                          1/1     Running            6 (5d ago)      23d     10.2.0.49        node1    <none>           <none>            app.kubernetes.io/component=exporter,app.kubernetes.io/name=kepler-kepler,controller-revision-hash=7c6c5f9bd6,pod-template-generation=1\nxnet          observability-kepler-7scjm                          1/1     Running            7 (5d1h ago)    23d     10.2.0.48        master   <none>           <none>            app.kubernetes.io/component=exporter,app.kubernetes.io/name=kepler-kepler,controller-revision-hash=7c6c5f9bd6,pod-template-generation=1\nxnet          observability-kepler-ggstf                          1/1     Running            8 (5d ago)      19d     10.2.0.50        node2    <none>           <none>            app.kubernetes.io/component=exporter,app.kubernetes.io/name=kepler-kepler,controller-revision-hash=7c6c5f9bd6,pod-template-generation=1\nxnet          observability-kibana-65d7c45f6d-tm4vv               1/1     Running            4 (5d ago)      23d     172.16.166.191   node1    <none>           <none>            app=observability-kibana,pod-template-hash=65d7c45f6d,release=observability\nxnet          observability-kube-state-metrics-798986b8b7-6z2dq   1/1     Running            4 (5d1h ago)    23d     172.16.219.65    master   <none>           <none>            app.kubernetes.io/component=metrics,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=kube-state-metrics,app.kubernetes.io/part-of=kube-state-metrics,app.kubernetes.io/version=2.15.0,helm.sh/chart=kube-state-metrics-5.37.0,pod-template-hash=798986b8b7,release=observability\nxnet          observability-mysql-764f9d5966-wh2bc                1/1     Running            4 (5d ago)      23d     172.16.219.98    master   <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=mysql,app=deepflow,component=mysql,pod-template-hash=764f9d5966\nxnet          observability-operator-d4495dc86-69lgw              1/1     Running            4 (5d ago)      23d     172.16.166.182   node1    <none>           <none>            app.kubernetes.io/component=prometheus-operator,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=observability-prometheus-operator,app.kubernetes.io/part-of=observability,app.kubernetes.io/version=1.0.2,app=observability-operator,chart=observability-1.0.2,heritage=Helm,pod-template-hash=d4495dc86,release=observability\nxnet          observability-prometheus-node-exporter-lj75r        1/1     Running            4 (5d1h ago)    23d     10.2.0.48        master   <none>           <none>            app.kubernetes.io/component=metrics,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=prometheus-node-exporter,app.kubernetes.io/part-of=prometheus-node-exporter,app.kubernetes.io/version=1.9.1,controller-revision-hash=74f4f4b87d,helm.sh/chart=prometheus-node-exporter-4.47.0,jobLabel=node-exporter,pod-template-generation=1,release=observability\nxnet          observability-prometheus-node-exporter-qp2qd        1/1     Running            4 (5d ago)      19d     10.2.0.50        node2    <none>           <none>            app.kubernetes.io/component=metrics,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=prometheus-node-exporter,app.kubernetes.io/part-of=prometheus-node-exporter,app.kubernetes.io/version=1.9.1,controller-revision-hash=74f4f4b87d,helm.sh/chart=prometheus-node-exporter-4.47.0,jobLabel=node-exporter,pod-template-generation=1,release=observability\nxnet          observability-prometheus-node-exporter-wnbb8        1/1     Running            4 (5d ago)      23d     10.2.0.49        node1    <none>           <none>            app.kubernetes.io/component=metrics,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=prometheus-node-exporter,app.kubernetes.io/part-of=prometheus-node-exporter,app.kubernetes.io/version=1.9.1,controller-revision-hash=74f4f4b87d,helm.sh/chart=prometheus-node-exporter-4.47.0,jobLabel=node-exporter,pod-template-generation=1,release=observability\nxnet          observability-telegraf-79f45d86-4kzkm               1/1     Running            4 (5d1h ago)    23d     172.16.219.113   master   <none>           <none>            app.kubernetes.io/component=telegraf,app.kubernetes.io/instance=observability,app.kubernetes.io/name=observability,pod-template-hash=79f45d86\nxnet          prometheus-observability-prometheus-0               2/2     Running            16 (5d ago)     23d     172.16.166.142   node1    <none>           <none>            app.kubernetes.io/instance=observability-prometheus,app.kubernetes.io/managed-by=prometheus-operator,app.kubernetes.io/name=prometheus,app.kubernetes.io/version=3.4.1,controller-revision-hash=prometheus-observability-prometheus-9467b46f7,operator.prometheus.io/name=observability-prometheus,operator.prometheus.io/shard=0,prometheus=observability-prometheus,statefulset.kubernetes.io/pod-name=prometheus-observability-prometheus-0\nxnet          xnet-agent-568f547566-jdsgp                         1/1     Running            4 (5d ago)      108d    172.16.104.40    node2    <none>           <none>            app=xnet-agent,pod-template-hash=568f547566", "duration_s": 0}, {"tool": "TodoWrite", "data": "Investigation plan updated with 4 tasks.\n\n# CURRENT INVESTIGATION TASKS\n\n**Task Status**: 2 completed, 1 in progress, 1 pending\n\n[ ] [4] 汇总问题并输出结果\n[~] [3] 检查异常工作负载\n[✓] [1] 检查集群节点状态\n[✓] [2] 检查系统组件Pod状态\n\n**Instructions**: Use TodoWrite tool to update task status as you work.", "duration_s": 0}, {"tool": "kubectl_describe", "data": "Name:             appconfigfail-7649c79dc5-q4zjz\nNamespace:        aiops-e2e\nPriority:         0\nService Account:  default\nNode:             node2/10.2.0.50\nStart Time:       Wed, 22 Apr 2026 07:38:39 +0000\nLabels:           app=appconfigfail\n                  l4-scenario=config-bootstrap-fail\n                  pod-template-hash=7649c79dc5\nAnnotations:      cni.projectcalico.org/containerID: c6399f913454284036a261148882084711e3bf6f9788cf1df749c56fbda41b6f\n                  cni.projectcalico.org/podIP: 172.16.104.57/32\n                  cni.projectcalico.org/podIPs: 172.16.104.57/32\n                  k8s.v1.cni.cncf.io/network-status:\n                    [{\n                        \"name\": \"k8s-pod-network\",\n                        \"ips\": [\n                            \"172.16.104.57\"\n                        ],\n                        \"default\": true,\n                        \"dns\": {}\n                    }]\n                  k8s.v1.cni.cncf.io/networks-status:\n                    [{\n                        \"name\": \"k8s-pod-network\",\n                        \"ips\": [\n                            \"172.16.104.57\"\n                        ],\n                        \"default\": true,\n                        \"dns\": {}\n                    }]\nStatus:           Running\nIP:               172.16.104.57\nIPs:\n  IP:           172.16.104.57\nControlled By:  ReplicaSet/appconfigfail-7649c79dc5\nContainers:\n  app:\n    Container ID:  containerd://b4a304e1363c33d4078e27893834e3a9bd9eb3979e5fea23e7071c88a806afe2\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Port:          <none>\n    Host Port:     <none>\n    Command:\n      sh\n      -c\n    Args:\n      echo \"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\"\n      echo \"L4_LAYER_APPLICATION: true\"\n      echo \"L4_SCENARIO: config-bootstrap-fail\"\n      echo \"L4_ERROR_TYPE: application-config-validation\"\n      if [ -z \"${APP_BOOT_MODE:-}\" ]; then\n        echo \"FATAL: missing required APP_BOOT_MODE\"\n        echo \"FATAL: business config validation failed before server startup\"\n        exit 42\n      fi\n      echo \"unexpected success\"\n      exit 1\n      \n    State:          Waiting\n      Reason:       CrashLoopBackOff\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42\n      Started:      Wed, 22 Apr 2026 07:49:32 +0000\n      Finished:     Wed, 22 Apr 2026 07:49:32 +0000\n    Ready:          False\n    Restart Count:  7\n    Environment:    <none>\n    Mounts:\n      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-zndsj (ro)\nConditions:\n  Type              Status\n  Initialized       True \n  Ready             False \n  ContainersReady   False \n  PodScheduled      True \nVolumes:\n  kube-api-access-zndsj:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    TokenExpirationSeconds:  3607\n    ConfigMapName:           kube-root-ca.crt\n    ConfigMapOptional:       <nil>\n    DownwardAPI:             true\nQoS Class:                   BestEffort\nNode-Selectors:              <none>\nTolerations:                 node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\n                             node.kubernetes.io/unreachable:NoExecute op=Exists for 300s\nEvents:\n  Type     Reason          Age                 From               Message\n  ----     ------          ----                ----               -------\n  Normal   Scheduled       15m                 default-scheduler  Successfully assigned aiops-e2e/appconfigfail-7649c79dc5-q4zjz to node2\n  Normal   AddedInterface  15m                 multus             Add eth0 [172.16.104.57/32] from k8s-pod-network\n  Normal   Pulled          14m (x5 over 15m)   kubelet            Container image \"busybox:1.36\" already present on machine\n  Normal   Created         14m (x5 over 15m)   kubelet            Created container app\n  Normal   Started         14m (x5 over 15m)   kubelet            Started container app\n  Warning  BackOff         43s (x70 over 15m)  kubelet            Back-off restarting failed container app in pod appconfigfail-7649c79dc5-q4zjz_aiops-e2e(77ea5d65-2a07-47e0-b606-3f03812dcc6a)", "duration_s": 0}, {"tool": "kubectl_events", "data": "LAST SEEN            TYPE      REASON           OBJECT                               MESSAGE\n15m                  Normal    Scheduled        Pod/appconfigfail-7649c79dc5-q4zjz   Successfully assigned aiops-e2e/appconfigfail-7649c79dc5-q4zjz to node2\n15m                  Normal    AddedInterface   Pod/appconfigfail-7649c79dc5-q4zjz   Add eth0 [172.16.104.57/32] from k8s-pod-network\n14m (x5 over 15m)    Normal    Pulled           Pod/appconfigfail-7649c79dc5-q4zjz   Container image \"busybox:1.36\" already present on machine\n14m (x5 over 15m)    Normal    Created          Pod/appconfigfail-7649c79dc5-q4zjz   Created container app\n14m (x5 over 15m)    Normal    Started          Pod/appconfigfail-7649c79dc5-q4zjz   Started container app\n44s (x70 over 15m)   Warning   BackOff          Pod/appconfigfail-7649c79dc5-q4zjz   Back-off restarting failed container app in pod appconfigfail-7649c79dc5-q4zjz_aiops-e2e(77ea5d65-2a07-47e0-b606-3f03812dcc6a)", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_namespace", "data": "NAME            READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES         SELECTOR            LABELS\nappconfigfail   0/1     1            0           15m   app          busybox:1.36   app=appconfigfail   l4-scenario=config-bootstrap-fail", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_cluster", "data": "NAMESPACE   NAME                                      READY   AGE   CONTAINERS                     IMAGES                                                                                                                                                           LABELS\nxnet        alertmanager-observability-alertmanager   1/1     23d   alertmanager,config-reloader   xnet.registry.io:8443/observability/prometheus/alertmanager:v0.28.1,xnet.registry.io:8443/observability/prometheus-operator/prometheus-config-reloader:v0.83.0   app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/part-of=observability,app.kubernetes.io/version=1.0.2,app=observability-alertmanager,chart=observability-1.0.2,heritage=Helm,managed-by=prometheus-operator,release=observability\nxnet        elasticsearch-master                      1/1     23d   observability                  xnet.registry.io:8443/observability/elasticsearch/elasticsearch:8.5.1                                                                                            app.kubernetes.io/managed-by=Helm,app=elasticsearch-master,chart=observability,heritage=Helm,release=observability\nxnet        observability-clickhouse                  1/1     23d   clickhouse                     xnet.registry.io:8443/observability/clickhouse-server:23.10                                                                                                      app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=clickhouse,app.kubernetes.io/version=21.8.15.7,app=deepflow,component=clickhouse,helm.sh/chart=clickhouse-0.1.000\nxnet        prometheus-observability-prometheus       1/1     23d   prometheus,config-reloader     xnet.registry.io:8443/observability/prometheus/prometheus:v3.4.1,xnet.registry.io:8443/observability/prometheus-operator/prometheus-config-reloader:v0.83.0      app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/part-of=observability,app.kubernetes.io/version=1.0.2,app=observability-prometheus,chart=observability-1.0.2,heritage=Helm,managed-by=prometheus-operator,operator.prometheus.io/mode=server,operator.prometheus.io/name=observability-prometheus,operator.prometheus.io/shard=0,release=observability", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_cluster", "data": "NAMESPACE     NAME                               READY   UP-TO-DATE   AVAILABLE   AGE     CONTAINERS                                                                      IMAGES                                                                                                                                                                                                                                           SELECTOR                                                                                                             LABELS\naiops-e2e     appconfigfail                      0/1     1            0           15m     app                                                                             busybox:1.36                                                                                                                                                                                                                                     app=appconfigfail                                                                                                    l4-scenario=config-bootstrap-fail\naiops         aiops-copilot                      1/1     1            1           6h16m   aiops-copilot                                                                   xnet.registry.io:8443/xnet-cloud/aiops-copilot:7.0.9                                                                                                                                                                                             app=aiops-copilot                                                                                                    <none>\ndefault       nfs-client-provisioner             1/1     1            1           209d    nfs-client-provisioner                                                          registry.cn-beijing.aliyuncs.com/xngczl/nfs-subdir-external-provisione:v4.0.0                                                                                                                                                                    app=nfs-client-provisioner                                                                                           app=nfs-client-provisioner\nkube-system   calico-kube-controllers            1/1     1            1           183d    calico-kube-controllers                                                         xnet.registry.io:8443/k8s/calico/kube-controllers:v3.26.1                                                                                                                                                                                        k8s-app=calico-kube-controllers                                                                                      k8s-app=calico-kube-controllers\nkube-system   coredns                            2/2     2            2           209d    coredns                                                                         xnet.registry.io:8443/k8s/registry.k8s.io/coredns:v1.9.3                                                                                                                                                                                         k8s-app=kube-dns                                                                                                     k8s-app=kube-dns\nmcp           mcp-server-manager                 1/1     1            1           46h     mcp-server-manager                                                              xnet.registry.io:8443/xnet-cloud/mcp-server-manager:7.0.6                                                                                                                                                                                        app=mcp-server-manager                                                                                               app=mcp-server-manager\nxnet          api-server                         1/1     1            1           23d     api-server                                                                      xnet.registry.io:8443/observability/apiserver:v1.0                                                                                                                                                                                               app=api-server                                                                                                       app.kubernetes.io/managed-by=Helm,app=api-server\nxnet          lgtm                               1/1     1            1           23d     lgtm                                                                            xnet.registry.io:8443/observability/grafana/otel-lgtm:latest                                                                                                                                                                                     app=lgtm                                                                                                             app.kubernetes.io/managed-by=Helm\nxnet          observability-deepflow-app         1/1     1            1           23d     deepflow-app                                                                    xnet.registry.io:8443/observability/deepflow-ce/deepflow-app:v7.0                                                                                                                                                                                app=deepflow,app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow,component=deepflow-app         app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=deepflow,app.kubernetes.io/version=1.0.0,app=deepflow,component=deepflow-app,helm.sh/chart=deepflow-1.0.2\nxnet          observability-deepflow-server      1/1     1            1           23d     deepflow-server                                                                 xnet.registry.io:8443/observability/deepflow-ce/deepflow-server:v7.0                                                                                                                                                                             app=deepflow,app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow,component=deepflow-server      app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=deepflow,app.kubernetes.io/version=1.0.0,app=deepflow,helm.sh/chart=deepflow-1.0.2\nxnet          observability-grafana              1/1     1            1           23d     grafana-sc-dashboard,grafana-sc-datasources,grafana,fix-grafana-db-dashboards   xnet.registry.io:8443/observability/kiwigrid/k8s-sidecar:1.30.0,xnet.registry.io:8443/observability/kiwigrid/k8s-sidecar:1.30.0,xnet.registry.io:8443/observability/grafana/grafana:12.0.2,xnet.registry.io:8443/observability/python:3-alpine   app.kubernetes.io/instance=observability,app.kubernetes.io/name=grafana                                              app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=grafana,app.kubernetes.io/version=12.0.2,helm.sh/chart=grafana-9.2.7\nxnet          observability-kibana               1/1     1            1           23d     kibana                                                                          xnet.registry.io:8443/observability/kibana/kibana:8.5.1                                                                                                                                                                                          app=observability-kibana,release=observability                                                                       app.kubernetes.io/managed-by=Helm,app=observability-kibana,heritage=Helm,release=observability\nxnet          observability-kube-state-metrics   1/1     1            1           23d     kube-state-metrics                                                              xnet.registry.io:8443/observability/kube-state-metrics/kube-state-metrics:v2.15.0                                                                                                                                                                app.kubernetes.io/instance=observability,app.kubernetes.io/name=kube-state-metrics                                   app.kubernetes.io/component=metrics,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=kube-state-metrics,app.kubernetes.io/part-of=kube-state-metrics,app.kubernetes.io/version=2.15.0,helm.sh/chart=kube-state-metrics-5.37.0,release=observability\nxnet          observability-mysql                1/1     1            1           23d     mysql                                                                           xnet.registry.io:8443/observability/mysql:8.0.39                                                                                                                                                                                                 app=deepflow,app.kubernetes.io/instance=observability,app.kubernetes.io/name=mysql,component=mysql                   app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=mysql,app.kubernetes.io/version=8.0.39,app=deepflow,component=mysql,helm.sh/chart=mysql-0.1.000\nxnet          observability-operator             1/1     1            1           23d     observability                                                                   xnet.registry.io:8443/observability/prometheus-operator/prometheus-operator:v0.83.0                                                                                                                                                              app=observability-operator,release=observability                                                                     app.kubernetes.io/component=prometheus-operator,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=observability-prometheus-operator,app.kubernetes.io/part-of=observability,app.kubernetes.io/version=1.0.2,app=observability-operator,chart=observability-1.0.2,heritage=Helm,release=observability\nxnet          observability-telegraf             1/1     1            1           23d     telegraf                                                                        xnet.registry.io:8443/observability/telegraf:1.32-alpine                                                                                                                                                                                         app.kubernetes.io/component=telegraf,app.kubernetes.io/instance=observability,app.kubernetes.io/name=observability   app.kubernetes.io/component=telegraf,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=observability,app.kubernetes.io/version=1.0.0,helm.sh/chart=observability-1.0.2\nxnet          xnet-agent                         1/1     1            1           208d    xnet-agent                                                                      xnet.registry.io:8443/xnet-cloud/xnet-agent:v0.0.1                                                                                                                                                                                               app=xnet-agent                                                                                                       app.kubernetes.io/managed-by=Helm,app=xnet-agent", "duration_s": 0}, {"tool": "run_bash_command", "data": "{\"success\": true, \"stdout\": \"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\\nL4_LAYER_APPLICATION: true\\nL4_SCENARIO: config-bootstrap-fail\\nL4_ERROR_TYPE: application-config-validation\\nFATAL: missing required APP_BOOT_MODE\\nFATAL: business config validation failed before server startup\\n\", \"stderr\": \"\", \"returncode\": 0}", "duration_s": 0}, {"tool": "TodoWrite", "data": "Investigation plan updated with 4 tasks.\n\n# CURRENT INVESTIGATION TASKS\n\n**Task Status**: 3 completed, 1 in progress, 0 pending\n\n[~] [4] 汇总问题并输出结果\n[✓] [1] 检查集群节点状态\n[✓] [2] 检查系统组件Pod状态\n[✓] [3] 检查异常工作负载\n\n**Instructions**: Use TodoWrite tool to update task status as you work.", "duration_s": 0}, {"tool": "TodoWrite", "data": "Investigation plan updated with 4 tasks.\n\n# CURRENT INVESTIGATION TASKS\n\n**Task Status**: 4 completed, 0 in progress, 0 pending\n\n[✓] [1] 检查集群节点状态\n[✓] [2] 检查系统组件Pod状态\n[✓] [3] 检查异常工作负载\n[✓] [4] 汇总问题并输出结果\n\n**Instructions**: Use TodoWrite tool to update task status as you work.", "duration_s": 0}], "llm_analysis": "---\n\n## 📋 集群健康检查报告\n\n### ✅ 集群整体健康概览\n\n| 检查项 | 状态 |\n|--------|------|\n| **节点** | ✅ 3/3 Ready（master、node1、node2） |\n| **节点 Taints** | ✅ 无异常 Taints |\n| **系统组件** | ✅ 全部 Running（etcd、apiserver、scheduler、controller-manager、coredns、calico、kube-proxy、multus） |\n| **工作负载** | ⚠️ **1 个异常**（见下方详情） |\n\n---\n\n### ⚠️ 发现的唯一问题：`aiops-e2e/appconfigfail`\n\n| 字段 | 值 |\n|------|-----|\n| **Namespace** | `aiops-e2e` |\n| **Pod** | `appconfigfail-7649c79dc5-q4zjz` |\n| **状态** | `CrashLoopBackOff`（已重启 7 次） |\n| **节点** | node2 (10.2.0.50) |\n| **Deployment** | `appconfigfail` — **可用副本 0/1** |\n| **退出码** | `42`（业务主动退出，非 OOM/信号终止） |\n\n#### 🔍 根因分析\n\n容器启动脚本中检查了环境变量 `APP_BOOT_MODE`：\n\n```\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup\n```\n\nPod 的 `Environment: <none>` — 未设置任何环境变量，导致业务配置校验失败，主动退出（退出码 42）。\n\n**层级**: L4（应用层 — 启动配置校验失败）\n\n#### ✅ 已排除的其他层级问题\n\n- ❌ L0（基础设施）— 无 Evicted、DiskPressure\n- ❌ L1（节点）— 无 MemoryPressure/DiskPressure/PIDPressure\n- ❌ L2（容器运行时）— 非 OOMKilled，退出码非 137\n- ❌ L3（镜像/调度）— 镜像 `busybox:1.36` 已存在于本地，Pod 正常调度\n\n---\n\n### ✅ 其他所有工作负载均正常运行\n\n包括 `aiops-copilot`、`nfs-client-provisioner`、`coredns`、`calico`、`xnet` 命名空间下的所有 observability 组件（Prometheus、Grafana、Elasticsearch、ClickHouse、Alertmanager 等）全部正常。\n\n---\n\n### 🛠 建议修复\n\n在 Deployment `appconfigfail` 的 Pod 规格中为容器 `app` 添加必填环境变量：\n\n```yaml\nenv:\n- name: APP_BOOT_MODE\n  value: \"production\"\n```", "collection_summary": "计划 9 项，实际采集 9 项，未采集 0 项，完整度 100%", "evidence_inventory": [{"id": "auto_0", "description": "工具采集: kubectl_get_by_kind_in_cluster", "level": "important", "collected": true, "source": "thinking_auto"}, {"id": "auto_1", "description": "工具采集: kubernetes_tabular_query", "level": "important", "collected": true, "source": "thinking_auto"}, {"id": "auto_2", "description": "工具采集: kubectl_get_by_kind_in_cluster", "level": "important", "collected": true, "source": "thinking_auto"}, {"id": "auto_3", "description": "工具采集: kubectl_describe", "level": "important", "collected": true, "source": "thinking_auto"}, {"id": "auto_4", "description": "工具采集: kubectl_events", "level": "important", "collected": true, "source": "thinking_auto"}, {"id": "auto_5", "description": "工具采集: kubectl_get_by_kind_in_namespace", "level": "important", "collected": true, "source": "thinking_auto"}, {"id": "auto_6", "description": "工具采集: kubectl_get_by_kind_in_cluster", "level": "important", "collected": true, "source": "thinking_auto"}, {"id": "auto_7", "description": "工具采集: kubectl_get_by_kind_in_cluster", "level": "important", "collected": true, "source": "thinking_auto"}, {"id": "auto_8", "description": "工具采集: run_bash_command", "level": "important", "collected": true, "source": "thinking_auto"}], "missing_reasons": [], "early_stop": {"triggered": false, "reason": "", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 9/9 项, 完整度: 100%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (31.4s)
   📤 → 下游数据: root_cause=
   confidence=98%
   causal_chain={"root_cause": "Deployment `appconfigfail` 的 Pod 规格中，容器 `app` 的 `.spec.containers[*].env` 字段为空，未定义启动脚本所依赖的必填环境变量 `APP_BOOT_MODE`。", "propagation": "Pod 启动 -> 容器启动脚本执行 -> 脚本调用业务配置校验逻辑 -> 校验逻辑检查环境变量 `APP_BOOT_MODE` -> 发现该变量为空（缺失） -> 校验失败。", "direct_cause": "容器启动脚本因缺少环境变量 `APP_BOOT_MODE`，执行了 `FATAL: missing required APP_BOOT_MODE` 逻辑，主动退出并返回业务退出码 42。", "manifestation": "Pod `appconfigfail-7649c79dc5-q4zjz` 持续进入 `CrashLoopBackOff` 状态，已重启 7 次，导致其所属 Deployment `appconfigfail` 可用副本数降为 0/1，服务不可用。"}
   rca_analysis={"phenomenon": "集群中 aiops-e2e 命名空间下的 appconfigfail Deployment 的 Pod appconfigfail-7649c79dc5-q4zjz 处于 CrashLoopBackOff 状态，已重启 7 次，可用副本为 0/1，导致该工作负载不可用。", "evidence_inventory": [{"id": "e1", "content": "3个节点(master, node1, node2)均处于 Ready 状态，无异常 Taints", "source": "kubectl_get_by_kind_in_cluster / kubernetes_tabular_query", "reliability": "高"}, {"id": "e2", "content": "Pod appconfigfail-7649c79dc5-q4zjz 状态 CrashLoopBackOff，重启次数 7，最后一次重启在 4分47秒前，Pod IP 172.16.104.57，运行在 node2", "source": "kubectl_get_by_kind_in_cluster / kubectl_describe", "reliability": "高"}, {"id": "e3", "content": "Pod 事件显示成功调度到 node2，成功添加网络接口，镜像 busybox:1.36 已 Pulled", "source": "kubectl_events", "reliability": "高"}, {"id": "e4", "content": "Deployment appconfigfail 可用副本 0/1，期望副本 1，镜像 busybox:1.36，标签 l4-scenario=config-bootstrap-fail", "source": "kubectl_get_by_kind_in_namespace / kubectl_describe", "reliability": "高"}, {"id": "e5", "content": "容器启动日志输出：FATAL: missing required APP_BOOT_MODE，FATAL: business config validation failed before server startup，退出码 42", "source": "run_bash_command / kubectl_describe (隐含退出码信息)", "reliability": "高"}, {"id": "e6", "content": "kubectl describe 显示 Pod 的 Environment: <none>，未设置任何环境变量", "source": "kubectl_describe", "reliability": "高"}, {"id": "e7", "content": "除 appconfigfail 外，其他工作负载（如 aiops-copilot、系统组件、xnet 命名空间下的 observability 组件等）均正常运行", "source": "kubectl_get_by_kind_in_cluster / 集群健康检查报告", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "节点状态：master Ready, node1 Ready, node2 Ready。Taints 全部为 <none>。", "interpretation": "集群基础设施层（L0）和节点层（L1）健康，无节点压力或异常 Taints，排除了节点级别的问题。"}, {"evidence_id": "e2", "raw_data": "Pod 名: appconfigfail-7649c79dc5-q4zjz, 状态: CrashLoopBackOff, 重启: 7次 (上次 4m47s前), IP: 172.16.104.57, 节点: node2 (10.2.0.50), 标签: l4-scenario=config-bootstrap-fail。", "interpretation": "Pod 持续崩溃重启，符合 CrashLoopBackOff 状态定义。标签 l4-scenario=config-bootstrap-fail 明确指示了场景为应用启动配置校验失败。"}, {"evidence_id": "e3", "raw_data": "事件: 15m前 Normal Scheduled 到 node2, 15m前 Normal AddedInterface (IP 172.16.104.57/32), 14m前 (x5) Normal Pulled 镜像 busybox:1.36。", "interpretation": "Pod 成功调度到节点，网络配置正常，镜像成功拉取（且已存在于本地），排除了 L3 层（镜像/调度）的问题。"}, {"evidence_id": "e4", "raw_data": "Deployment appconfigfail: 期望副本 1, 当前副本 1, 可用副本 0, 更新副本 1, 镜像 busybox:1.36, 标签 l4-scenario=config-bootstrap-fail。", "interpretation": "Deployment 期望运行一个副本，但当前可用的副本数为 0，因为唯一的 Pod 处于 CrashLoopBackOff 状态，导致服务不可用。"}, {"evidence_id": "e5", "raw_data": "启动日志: 'FATAL: missing required APP_BOOT_MODE', 'FATAL: business config validation failed before server startup', 'L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config'。退出码 42。", "interpretation": "这是最直接的根因证据。容器启动时，业务启动脚本（模拟）检查了必填环境变量 APP_BOOT_MODE，发现其缺失，因此打印致命错误日志并主动退出，退出码 42（业务自定义退出码），非系统 OOM（137）。"}, {"evidence_id": "e6", "raw_data": "kubectl describe 输出中无 'Environment:' 字段或显示 'Environment: <none>'。", "interpretation": "证实了 Pod 规格中没有定义任何环境变量，包括启动脚本所必需的 APP_BOOT_MODE，这与日志中的错误信息完全吻合。"}, {"evidence_id": "e7", "raw_data": "集群健康检查报告显示系统组件 Pod 全部 Running，其他工作负载正常。", "interpretation": "确认这是一个孤立的、应用配置相关的问题，不影响集群其他部分。"}], "causal_chain": {"root_cause": "Deployment `appconfigfail` 的 Pod 规格中，容器 `app` 的 `.spec.containers[*].env` 字段为空，未定义启动脚本所依赖的必填环境变量 `APP_BOOT_MODE`。", "propagation": "Pod 启动 -> 容器启动脚本执行 -> 脚本调用业务配置校验逻辑 -> 校验逻辑检查环境变量 `APP_BOOT_MODE` -> 发现该变量为空（缺失） -> 校验失败。", "direct_cause": "容器启动脚本因缺少环境变量 `APP_BOOT_MODE`，执行了 `FATAL: missing required APP_BOOT_MODE` 逻辑，主动退出并返回业务退出码 42。", "manifestation": "Pod `appconfigfail-7649c79dc5-q4zjz` 持续进入 `CrashLoopBackOff` 状态，已重启 7 次，导致其所属 Deployment `appconfigfail` 可用副本数降为 0/1，服务不可用。"}, "root_cause_summary": "根本原因是 Pod `appconfigfail-7649c79dc5-q4zjz` (IP: 172.16.104.57, 节点: node2) 的容器启动时，业务脚本因找不到必填的环境变量 `APP_BOOT_MODE` 而失败。日志证据显示 'FATAL: missing required APP_BOOT_MODE'，且 kubectl describe 确认该 Pod 的 Environment 字段为空 `<none>`，未设置任何环境变量。Pod 因此以业务退出码 42 退出，导致 CrashLoopBackOff 状态（已重启 7 次），Deployment 可用副本为 0/1。其他层级（L0-L3）均已被排除。", "confidence": 0.98, "primary_runbooks": [], "alternative_causes": [], "limitations": "证据充分，因果链清晰。由于是模拟场景，业务逻辑由脚本模拟，实际情况中环境变量缺失原因可能更复杂（如 ConfigMap/Secret 挂载失败）。但基于现有证据，已无其他合理替代原因。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 98%
   🔗 因果链:
     根本原因: Deployment `appconfigfail` 的 Pod 规格中，容器 `app` 的 `.spec.containers[*].env` 字段为空，未定义启动脚本所依赖的必填环境变量 `APP_BOOT_MODE`。
     传导机制: Pod 启动 -> 容器启动脚本执行 -> 脚本调用业务配置校验逻辑 -> 校验逻辑检查环境变量 `APP_BOOT_MODE` -> 发现该变量为空（缺失） -> 校验失败。
     最终表现: Pod `appconfigfail-7649c79dc5-q4zjz` 持续进入 `CrashLoopBackOff` 状态，已重启 7 次，导致其所属 Deployment `appconfigfail` 可用副本数降为 0/1，服务不可用。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (39.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5869 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 29.1s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，这是根据您提供的三个阶段分析结果生成的详尽诊断报告。

---
## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **问题层级** | L4 - 应用层 |
| **问题分类** | 应用启动配置校验失败 (Config Bootstrap Fail) |
| **置信度** | 高 (98%) |
| **证据完整度** | 9/9 (100%) |

**集群核心问题**：集群整体健康，**仅发现一个应用层问题**。Pod `appconfigfail-7649c79dc5-q4zjz` 因缺少必填环境变量 `APP_BOOT_MODE`，导致业务启动配置校验失败，持续处于 `CrashLoopBackOff` 状态，不可用。

| 资源类型 | 状态 |
| :--- | :--- |
| **节点** | ✅ 3/3 Ready (master, node1, node2)，无异常 Taints |
| **系统组件** | ✅ 所有系统 Pod (etcd, apiserver, scheduler, controller-manager, coredns, calico, kube-proxy) 均 Running |
| **工作负载** | ⚠️ **1 个异常**：`appconfigfail` (aiops-e2e 命名空间)，其余全部正常 |
| **Service** | ✅ 所有 Service 存在，Endpoints 正常 |
| **PVC** | ✅ 所有 PVC 均 Bound，无 Pending |

---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `appconfigfail-7649c79dc5-q4zjz` |
| Namespace | `aiops-e2e` |
| Node | `node2` (10.2.0.50) |
| Deployment | `appconfigfail` (可用副本 0/1) |
| 错误信息 | `FATAL: missing required APP_BOOT_MODE`, `Exit Code: 42` |
| Pod 标签 | `l4-scenario=config-bootstrap-fail` |

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | 节点状态 | `kubectl_get_by_kind_in_cluster` / `kubernetes_tabular_query` | 节点 `master`, `node1`, `node2` 状态均为 `Ready`，Taints 均为 `<none>` | 集群基础设施 (L0) 和节点层 (L1) 健康，排除节点问题 |
| 2 | Pod 状态 | `kubectl_get_by_kind_in_cluster` | `STATUS: CrashLoopBackOff`, `RESTARTS: 7 (4m47s ago)`, `IP: 172.16.104.57`, 运行在 `node2` | Pod 持续崩溃重启，符合 CrashLoopBackOff 状态 |
| 3 | Pod 事件 | `kubectl_events` | `Normal Scheduled` 到 `node2`, `Normal Pulled` 镜像 `busybox:1.36` | 镜像已存在于本地，成功调度，排除了镜像拉取和调度问题 (L3) |
| 4 | 容器退出码 | `kubectl_describe` | `Exit Code: 42`, `Reason: Error` | 退出码 42 是业务自定义退出码，非系统 OOM (137)，排除了容器运行时问题 (L2) |
| 5 | 容器日志 | `run_bash_command` | `FATAL: missing required APP_BOOT_MODE`<br>`FATAL: business config validation failed before server startup` | **直接根因证据**：业务启动脚本因缺少环境变量 `APP_BOOT_MODE` 而主动退出 |
| 6 | 资源配置 | `kubectl_describe` | `Environment: <none>` | 容器启动命令中未设置任何环境变量，确认了日志中的错误原因 |
| 7 | 工作负载状态 | `kubectl_get_by_kind_in_namespace` | Deployment `appconfigfail`: `AVAILABLE: 0`, `UP-TO-DATE: 1` | 由于 Pod 异常，导致 Deployment 可用副本为 0，服务不可用 |

### 证据关联分析
- **证据 #5 + #6 印证**：Pod 未设置任何环境变量 (`Environment: <none>`) + 日志报错 `FATAL: missing required APP_BOOT_MODE` → 根本原因明确。
- **证据 #4 + #5 印证**：Exit Code 42 (业务自定义) + 日志报错 `FATAL` → 确认是业务逻辑主动退出，而非系统层面错误。
- **证据链**：Deployment 未配置 `APP_BOOT_MODE` 环境变量 → Pod 启动时脚本检查该变量为空 → 打印致命错误日志并主动退出 (Exit Code 42) → Kubelet 检测到容器退出并重启 → Pod 进入 `CrashLoopBackOff` 状态。

### 缺失证据
| 证据 | 级别 | 影响 |
|------|------|------|
| 无 | - | 证据链完整，无需补充 |

---
## 🎯 根因分析
### 因果链
```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                                      │
│ Deployment `appconfigfail` 的 Pod 规格中，容器 `app` 的 `.spec.containers[*].env` 字段为空，    │
│ 未定义启动脚本所依赖的必填环境变量 `APP_BOOT_MODE`。                                            │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                                      │
│ Pod 启动 -> 容器启动脚本执行 -> 业务配置校验逻辑 -> 检查环境变量 `APP_BOOT_MODE` -> 发现其缺失    │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                                      │
│ 容器因环境变量缺失，执行 `exit 42` 逻辑主动退出，而非被系统 Kill。                                │
│ (Exit Code: 42，非 137/OOM)                                                                    │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                                  │
│ Pod `appconfigfail-7649c79dc5-q4zjz` 处于 `CrashLoopBackOff` 状态 (已重启 7 次)，              │
│ Deployment `appconfigfail` 可用副本为 0/1，业务不可用。                                         │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #5 (日志报错 `FATAL: missing required APP_BOOT_MODE`) 和证据 #6 (Pod 环境变量为空 `<none>`)，问题的根本原因是**Deployment `appconfigfail` 的 Pod 规格中未定义必填的环境变量 `APP_BOOT_MODE`**，导致容器启动时业务配置校验失败并主动退出。

**置信度**：高 (98%)
- ✅ 容器日志直接指出缺失环境变量
- ✅ `kubectl describe` 确认环境变量为空
- ✅ 退出码 42 与业务主动退出行为一致
- ✅ 已排除 L0-L3 层级的所有可能性

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 为 Deployment 添加缺失的环境变量**
```bash
kubectl set env deployment/appconfigfail -n aiops-e2e APP_BOOT_MODE=production
```
*依据*：直接补充缺失的配置，使 Pod 能够正常启动。

**2. [验证] 检查 Deployment YAML 确认配置正确**
```bash
kubectl edit deployment appconfigfail -n aiops-e2e
```
*目的*：确认环境变量已成功添加，或者检查是否有其他配置问题。你可以在 YAML 文件的 `spec.template.spec.containers[0].env` 下看到如下内容：
```yaml
env:
- name: APP_BOOT_MODE
  value: "production"
```

### 后续优化
1. **启动健康检查**：为关键应用添加 `startupProbe`，避免配置错误导致无限重启。
2. **配置管理**：建议使用 ConfigMap 或 Secret 管理应用配置，避免环境变量硬编码在 Deployment 中，便于集中管理和审计。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod -n aiops-e2e -l app=appconfigfail` | `STATUS: Running`，`READY: 1/1` |
| 2. 检查重启次数 | `kubectl get pod appconfigfail-xxx -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 重启次数不再增加，且 Pod 名称变为新的哈希值 |
| 3. 检查 Deployment 可用副本 | `kubectl get deployment appconfigfail -n aiops-e2e` | `AVAILABLE: 1` |

---
## ⚠️ 注意事项
- 此问题为单一应用配置问题，不影响集群中其他工作负载。
- 修复后旧的异常 Pod 会被新 Pod 替代，重启计数器会重置。

---

## 📊 性能统计

├─ 总耗时: 2.5m
├─ 问题定位: 39.8s (27%) ✅
├─ 证据链采集: 38.0s (25%) ✅
├─ 根因分析: 31.4s (21%) ✅
├─ 汇总总结: 39.8s (27%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 26 次
```

📋 诊断追踪

- **参考 Runbook**: private-k8s-health-reference, l4-config-bootstrap-fail
- **工具调用**: 26 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
