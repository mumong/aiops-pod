======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 4e8eae7b960f42f0]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先做一次轻量状态确认，看看集群的整体情况。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   209d   v1.26.8  
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,READY:.status.containerStatuses[0].ready' | (head -
   💭 [问题定位] 节点全部 Ready。让我检查一下所有 Pod 的状态，包括异常状态。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 NAMESPACE     NAME                                                STATUS    NODE
aiops-e2e     appconfigfail-7649c79dc5-q4zjz                      Running   node2
aiops         aiops-copilot-76779bb6d
   💭 [问题定位] 所有 Pod 都是 Running 状态，节点全部 Ready。让我再检查一下是否有 Warning 事件以及系统组件健康状况。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE   LAST SEEN   TYPE      REASON              OBJECT                                SUBOBJECT              SOURCE                                        MESSAGE                                
   💭 [问题定位] 有几点发现，让我进一步检查具体的异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                             READY   STATUS             RESTARTS         AGE   IP              NODE    NOMINATED NODE   READINESS GATES   LABELS
appconfigfail-7649c79dc5-q4zjz   0/1     CrashLoopB
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 Command failed (exit 1):
kubectl get --show-labels -o wide pod l1-test-nginx-6c69dc7c76-fwzgn -n aiops-e2e
Error from server (NotFound): pods "l1-test-nginx-6c69dc7c76-fwzgn" not found

   💭 [问题定位] 有两个异常点，让我进一步查看。

1. **aiops-e2e/appconfigfail-7649c79dc5-q4zjz** — CrashLoopBackOff（11次重启），而且从标签看是 `l4-scenario=config-bootstrap-fail` 场景
2. **l1-test-nginx** — 已经被删除（`skip schedule deleting pod`），说明是历史事件

让我查看 appconfigfail 的日志来确认根因。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             appconfigfail-7649c79dc5-q4zjz
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Wed, 22 Apr 2026 07:38:39
   💭 [问题定位] 这个 Pod 的启动命令明确模拟了"应用启动配置校验失败"的场景（L4 应用层），exit code 42 是因为缺少 `APP_BOOT_MODE` 环境变量导致配置校验失败。让我也看看这个命名空间是否有其他异常。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 NAME                             READY   STATUS             RESTARTS         AGE   IP              NODE    NOMINATED NODE   READINESS GATES   LABELS
appconfigfail-7649c79dc5-q4zjz   0/1     CrashLoopB
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
   💭 [问题定位] 现在我已经收集到足够信息，可以给出诊断结论。

让我也检查一下其他命名空间是否还有异常。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS             RESTARTS         AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     
   💭 [问题定位] 现在我已经有了全面的数据。让我总结诊断结果。

```json
{
  "layer": "L4",
  "layers": ["L4"],
  "layer_name": "应用层",
  "confidence": 0.95,
  "reasoning": "集群整体健康：3个节点均为 Ready，所有系统组件（CoreDNS、Calico、kube-apiserver、etcd 等）均正常 Running。唯一异常 Pod 为 aiops-e2e/appconfigfail-7649c79dc5-q4zjz，处于 CrashLoopBackOff 状态（已重启11次），其容器命令明确模拟了应用启动配置校验失败场景（L4_CONFIG_BOOTSTRAP_FAIL），Exit Code=42（非 OOM/非 137），日志显示缺少必填环境变量 APP_BOOT_MODE 导致业务配置校验失败后主动退出，属于典型的 L4 应用层问题。同时该 Pod 的 label 明确标注 l4-scenario=config-bootstrap-fail，是一个已知的测试场景。历史事件中的 l1-test-nginx Pod 因 taint 无法调度但已被删除，不构成当前活跃异常。",
  "key_entities": [
    {"type": "Pod", "value": "appconfigfail-7649c79dc5-q4zjz"},
    {"type": "Namespace", "value": "aiops-e2e"},
    {"type": "Node", "value": "node2"}
  ],
  "possible_scenarios": ["应用启动配置校验失败 (Config Bootstrap Fail)"]
}
```
   ✅ [问题定位] 完成 (34.7s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=['应用启动配置校验失败 (Config Bootstrap Fail)']
   entities=[{"type": "Pod", "value": "appconfigfail-7649c79dc5-q4zjz"}, {"type": "Namespace", "value": "aiops-e2e"}, {"type": "Node", "value": "node2"}]
   reasoning=集群整体健康：3个节点均为 Ready，所有系统组件（CoreDNS、Calico、kube-apiserver、etcd 等）均正常 Running。唯一异常 Pod 为 aiops-e2e/appconfigfail-7649c79dc5-q4zjz，处于 CrashLoopBackOff 状态（已重启11次），其容器命令明确模拟了应用启动配置校验失败场景（L4_CONFIG_BOOTSTRAP_FAIL），Exit Code=42（非 OOM/非 137），日志显示缺少必填环境变量 APP_BOOT_MODE 导致业务配置校验失败后主动退出，属于典型的 L4 应用层问题。同时该 Pod 的 label 明确标注 l4-scenario=config-bootstrap-fail，是一个已知的测试场景。历史事件中的 l1-test-nginx Pod 因 taint 无法调度但已被删除，不构成当前活跃异常。
   layer_analysis={"layer": "L4", "layers": ["L4"], "layer_name": "应用层", "confidence": 0.95, "reasoning": "集群整体健康：3个节点均为 Ready，所有系统组件（CoreDNS、Calico、kube-apiserver、etcd 等）均正常 Running。唯一异常 Pod 为 aiops-e2e/appconfigfail-7649c79dc5-q4zjz，处于 CrashLoopBackOff 状态（已重启11次），其容器命令明确模拟了应用启动配置校验失败场景（L4_CONFIG_BOOTSTRAP_FAIL），Exit Code=42（非 OOM/非 137），日志显示缺少必填环境变量 APP_BOOT_MODE 导致业务配置校验失败后主动退出，属于典型的 L4 应用层问题。同时该 Pod 的 label 明确标注 l4-scenario=config-bootstrap-fail，是一个已知的测试场景。历史事件中的 l1-test-nginx Pod 因 taint 无法调度但已被删除，不构成当前活跃异常。", "key_entities": [{"type": "Pod", "value": "appconfigfail-7649c79dc5-q4zjz"}, {"type": "Namespace", "value": "aiops-e2e"}, {"type": "Node", "value": "node2"}], "possible_scenarios": ["应用启动配置校验失败 (Config Bootstrap Fail)"]}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 让我先获取集群的概览信息，确认当前状态。
   💭 [证据链采集] 调用工具: TodoWrite
   💭 [证据链采集] 工具结果: TodoWrite (success)
      📄 Investigation plan updated with 4 tasks.

# CURRENT INVESTIGATION TASKS

**Task Status**: 0 completed, 1 in progress, 3 pending

[ ] [t2] 深入采集异常Pod的详细证据
[ ] [t3] 采集节点健康状态证据
[ ] [t4] 汇总分析并给出结论
[~] [t1]
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   209d   v1.26.8  
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS             RESTARTS         AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 NAME                             READY   STATUS             RESTARTS         AGE   IP              NODE    NOMINATED NODE   READINESS GATES   LABELS
appconfigfail-7649c79dc5-q4zjz   0/1     CrashLoopB
   💭 [证据链采集] 好的，已经看到集群整体情况。让我深入采集异常 Pod 的详细信息。
   💭 [证据链采集] 调用工具: TodoWrite
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: TodoWrite (success)
      📄 Investigation plan updated with 4 tasks.

# CURRENT INVESTIGATION TASKS

**Task Status**: 1 completed, 1 in progress, 2 pending

[ ] [t3] 采集节点健康状态证据
[ ] [t4] 汇总分析并给出结论
[~] [t2] 深入采集异常Pod的详细证据
[✓] [t1]
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:             appconfigfail-7649c79dc5-q4zjz
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Wed, 22 Apr 2026 07:38:39
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 apiVersion: v1
kind: Pod
metadata:
  annotations:
    cni.projectcalico.org/containerID: c6399f913454284036a261148882084711e3bf6f9788cf1df749c56fbda41b6f
    cni.projectcalico.org/podIP: 172.16.104.57
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 LAST SEEN             TYPE      REASON           OBJECT                               MESSAGE
36m                   Normal    Scheduled        Pod/appconfigfail-7649c79dc5-q4zjz   Successfully assigne
   💭 [证据链采集] 现在让我查看日志和 Deployment 信息，以及节点健康状态。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_LAYER_APPLICATION: true\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: appl
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:               node2
Roles:              <none>
Labels:             beta.kubernetes.io/arch=amd64
                    beta.kubernetes.io/os=linux
                    kubernetes.io/arch=amd64
    
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 NAME            READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES         SELECTOR            LABELS
appconfigfail   0/1     1            0           36m   app          busybox:1.36   app=app
   💭 [证据链采集] 调用工具: TodoWrite
   💭 [证据链采集] 工具结果: TodoWrite (success)
      📄 Investigation plan updated with 4 tasks.

# CURRENT INVESTIGATION TASKS

**Task Status**: 3 completed, 1 in progress, 0 pending

[~] [t4] 汇总分析并给出结论
[✓] [t1] 获取集群概览信息（节点、异常Pod）
[✓] [t2] 深入采集异常Pod的详细证据

   💭 [证据链采集] 调用工具: TodoWrite
   💭 [证据链采集] 工具结果: TodoWrite (success)
      📄 Investigation plan updated with 4 tasks.

# CURRENT INVESTIGATION TASKS

**Task Status**: 4 completed, 0 in progress, 0 pending

[✓] [t1] 获取集群概览信息（节点、异常Pod）
[✓] [t2] 深入采集异常Pod的详细证据
[✓] [t3] 采集节点健康状态证据
   💭 [证据链采集] ---

## 📋 集群健康诊断报告

### ✅ 集群整体状态：基本健康

| 资源 | 状态 |
|------|------|
| **3个节点** | ✅ 全部 Ready（master, node1, node2） |
| **系统组件** | ✅ etcd, kube-apiserver, kube-scheduler, kube-controller-manager 均 Running |
| **网络组件** | ✅ Calico, CoreDNS, Multus, kube-proxy 均 Running |
| **存储** | ✅ NFS Client Provisioner Running |

---

### ⚠️ 发现 1 个异常 Pod

| Pod | 命名空间 | 状态 | 退出码 | 节点 |
|:---|:---|:---|:---:|:---:|
| **appconfigfail-7649c79dc5-q4zjz** | `aiops-e2e` | **CrashLoopBackOff** (重启11次) | **42** | node2 |

#### 🔍 详细诊断

**Pod 基本信息：**
- 镜像：`busybox:1.36`（已存在于节点，拉取正常 ✅）
- 调度：正常分配到 node2 ✅
- 网络：已获取 IP `172.16.104.57` ✅

**根本原因 — 应用启动配置校验失败：**

Pod 的启动脚本中执行了配置校验，关键日志输出：

```
L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config
L4_LAYER_APPLICATION: true
L4_SCENARIO: config-bootstrap-fail
L4_ERROR_TYPE: application-config-validation
FATAL: missing required APP_BOOT_MODE
FATAL: business config validation failed before server startup
```

**问题链：**
1. 容器启动脚本检查环境变量 `APP_BOOT_MODE` 是否存在
2. 该环境变量**未设置**（Pod 的 `Environment: <none>`）
3. 应用主动退出，返回 **Exit Code 42**（非 OOM、非系统信号）
4. kubelet 检测到容器退出，按 `restartPolicy: Always` 不断重启
5. 每次立即失败 → **CrashLoopBackOff**（当前退避等待 5 分钟）

**排除的其他原因：**
- ❌ 非 OOMKilled（退出码 42，非 137）
- ❌ 非镜像拉取失败（`ImagePullPolicy: Never`，镜像已在本地）
- ❌ 非节点问题（node2 状态 Ready，资源充足：CPU 8%/34%，内存 5%/17%）
- ❌ 非网络问题（CNI 配置正常，Pod 已分配 IP）

---

### 📋 总结

| 项目 | 状态 |
|:---|:---:|
| 🟢 集群节点 | 3/3 Ready |
| 🟢 系统组件 | 全部正常 |
| 🟡 **异常 Pod** | **1个** — `appconfigfail`（CrashLoopBackOff） |
| 🟢 其他应用 | 全部正常 |

**唯一的问题 Pod `appconfigfail` 是 L4 应用层配置问题**：启动脚本要求设置环境变量 `APP_BOOT_MODE` 但未提供，应用主动退出（Exit Code 42），与集群基础设施无关。

---

### 🔧 修复建议

要修复此 Pod，请为 Deployment 添加缺失的环境变量 `APP_BOOT_MODE`：

```bash
# 编辑 Deployment
kubectl edit deployment appconfigfail -n aiops-e2e
```

在 container spec 中添加：
```yaml
env:
  - name: APP_BOOT_MODE
    value: "production"   # 或其他合适的值
```

或者直接设置（如支持）：
```bash
kubectl set env deployment/appconfigfail -n aiops-e2e APP_BOOT_MODE=production
```
   ✅ [证据链采集] 完成 (36.1s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan": [], "tool_results": [], "tool_data": [{"tool": "TodoWrite", "data": "Investigation plan updated with 4 tasks.\n\n# CURRENT INVESTIGATION TASKS\n\n**Task Status**: 0 completed, 1 in progress, 3 pending\n\n[ ] [t2] 深入采集异常Pod的详细证据\n[ ] [t3] 采集节点健康状态证据\n[ ] [t4] 汇总分析并给出结论\n[~] [t1] 获取集群概览信息（节点、异常Pod）\n\n**Instructions**: Use TodoWrite tool to update task status as you work.", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_cluster", "data": "NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nmaster   Ready    control-plane   209d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          209d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-174-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          209d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-174-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_cluster", "data": "NAMESPACE     NAME                                                READY   STATUS             RESTARTS         AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\naiops-e2e     appconfigfail-7649c79dc5-q4zjz                      0/1     CrashLoopBackOff   11 (4m46s ago)   36m     172.16.104.57    node2    <none>           <none>            app=appconfigfail,l4-scenario=config-bootstrap-fail,pod-template-hash=7649c79dc5\naiops         aiops-copilot-76779bb6df-4bcrf                      1/1     Running            0                6h37m   172.16.104.29    node2    <none>           <none>            app=aiops-copilot,pod-template-hash=76779bb6df\ndefault       dns-test-existing                                   1/1     Running            0                2d2h    172.16.166.148   node1    <none>           <none>            run=dns-test-existing\ndefault       exec-test                                           1/1     Running            0                2d4h    172.16.104.8     node2    <none>           <none>            run=exec-test\ndefault       network-test-from-running                           1/1     Running            0                2d2h    172.16.104.50    node2    <none>           <none>            run=network-test-from-running\ndefault       nfs-client-provisioner-6fcd4994c9-lczf6             1/1     Running            4 (5d1h ago)     86d     172.16.104.41    node2    <none>           <none>            app=nfs-client-provisioner,pod-template-hash=6fcd4994c9\nkube-system   calico-kube-controllers-6c67f9d475-2xcb7            1/1     Running            4 (5d1h ago)     28d     172.16.166.133   node1    <none>           <none>            k8s-app=calico-kube-controllers,pod-template-hash=6c67f9d475\nkube-system   calico-node-4kp26                                   1/1     Running            12 (5d1h ago)    183d    10.2.0.48        master   <none>           <none>            controller-revision-hash=65f554db6,k8s-app=calico-node,pod-template-generation=1\nkube-system   calico-node-d2dhp                                   1/1     Running            13 (5d1h ago)    183d    10.2.0.50        node2    <none>           <none>            controller-revision-hash=65f554db6,k8s-app=calico-node,pod-template-generation=1\nkube-system   calico-node-mnrjs                                   1/1     Running            12 (5d1h ago)    183d    10.2.0.49        node1    <none>           <none>            controller-revision-hash=65f554db6,k8s-app=calico-node,pod-template-generation=1\nkube-system   coredns-777df594b8-j4857                            1/1     Running            4 (5d1h ago)     28d     172.16.166.129   node1    <none>           <none>            k8s-app=kube-dns,pod-template-hash=777df594b8\nkube-system   coredns-777df594b8-s8r4n                            1/1     Running            4 (5d1h ago)     28d     172.16.166.185   node1    <none>           <none>            k8s-app=kube-dns,pod-template-hash=777df594b8\nkube-system   etcd-master                                         1/1     Running            13 (5d1h ago)    209d    10.2.0.48        master   <none>           <none>            component=etcd,tier=control-plane\nkube-system   kube-apiserver-master                               1/1     Running            13 (5d1h ago)    209d    10.2.0.48        master   <none>           <none>            component=kube-apiserver,tier=control-plane\nkube-system   kube-controller-manager-master                      1/1     Running            36 (5d1h ago)    209d    10.2.0.48        master   <none>           <none>            component=kube-controller-manager,tier=control-plane\nkube-system   kube-multus-ds-rnvbg                                1/1     Running            12 (5d1h ago)    183d    10.2.0.49        node1    <none>           <none>            app=multus,controller-revision-hash=6d4c8546fc,name=multus,pod-template-generation=1,tier=node\nkube-system   kube-multus-ds-sc2jn                                1/1     Running            4 (5d1h ago)     86d     10.2.0.48        master   <none>           <none>            app=multus,controller-revision-hash=6d4c8546fc,name=multus,pod-template-generation=1,tier=node\nkube-system   kube-multus-ds-x7h9s                                1/1     Running            13 (5d1h ago)    183d    10.2.0.50        node2    <none>           <none>            app=multus,controller-revision-hash=6d4c8546fc,name=multus,pod-template-generation=1,tier=node\nkube-system   kube-proxy-69zzr                                    1/1     Running            4 (5d1h ago)     28d     10.2.0.50        node2    <none>           <none>            controller-revision-hash=7d99996759,k8s-app=kube-proxy,pod-template-generation=1\nkube-system   kube-proxy-bblvc                                    1/1     Running            4 (5d1h ago)     28d     10.2.0.49        node1    <none>           <none>            controller-revision-hash=7d99996759,k8s-app=kube-proxy,pod-template-generation=1\nkube-system   kube-proxy-wbh4k                                    1/1     Running            4 (5d1h ago)     27d     10.2.0.48        master   <none>           <none>            controller-revision-hash=7d99996759,k8s-app=kube-proxy,pod-template-generation=1\nkube-system   kube-scheduler-master                               1/1     Running            38 (5d1h ago)    209d    10.2.0.48        master   <none>           <none>            component=kube-scheduler,tier=control-plane\nmcp           mcp-server-manager-8677f6896c-d4mr9                 1/1     Running            0                46h     172.16.104.59    node2    <none>           <none>            app=mcp-server-manager,pod-template-hash=8677f6896c\nxnet          alertmanager-observability-alertmanager-0           2/2     Running            8 (5d1h ago)     23d     172.16.166.161   node1    <none>           <none>            alertmanager=observability-alertmanager,app.kubernetes.io/instance=observability-alertmanager,app.kubernetes.io/managed-by=prometheus-operator,app.kubernetes.io/name=alertmanager,app.kubernetes.io/version=0.28.1,controller-revision-hash=alertmanager-observability-alertmanager-6c9cfbf844,statefulset.kubernetes.io/pod-name=alertmanager-observability-alertmanager-0\nxnet          api-server-6bd6bf8d6f-27svp                         1/1     Running            4 (5d1h ago)     23d     172.16.219.106   master   <none>           <none>            app=api-server,pod-template-hash=6bd6bf8d6f\nxnet          deepflow-agent-pcknn                                1/1     Running            9 (5d1h ago)     23d     172.16.166.181   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow-agent,app=deepflow,component=deepflow-agent,controller-revision-hash=54856d959b,pod-template-generation=1\nxnet          deepflow-agent-trc8k                                1/1     Running            7 (5d1h ago)     19d     172.16.104.7     node2    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow-agent,app=deepflow,component=deepflow-agent,controller-revision-hash=54856d959b,pod-template-generation=1\nxnet          deepflow-agent-whn22                                1/1     Running            8 (5d1h ago)     23d     172.16.219.97    master   <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow-agent,app=deepflow,component=deepflow-agent,controller-revision-hash=54856d959b,pod-template-generation=1\nxnet          elasticsearch-master-0                              1/1     Running            4 (5d1h ago)     23d     172.16.219.109   master   <none>           <none>            app=elasticsearch-master,chart=observability,controller-revision-hash=elasticsearch-master-695ff9864f,release=observability,statefulset.kubernetes.io/pod-name=elasticsearch-master-0\nxnet          ham-p9dxv                                           1/1     Running            14 (5d1h ago)    177d    172.16.104.21    node2    <none>           <none>            app=ham,controller-revision-hash=f65f887d,pod-template-generation=1\nxnet          ham-qzjg5                                           1/1     Running            4 (5d1h ago)     85d     172.16.219.112   master   <none>           <none>            app=ham,controller-revision-hash=f65f887d,pod-template-generation=1\nxnet          ham-wt9kh                                           1/1     Running            13 (5d1h ago)    177d    172.16.166.187   node1    <none>           <none>            app=ham,controller-revision-hash=f65f887d,pod-template-generation=1\nxnet          lgtm-5dc5c67d5f-sc286                               1/1     Running            4 (5d1h ago)     23d     172.16.166.151   node1    <none>           <none>            app=lgtm,pod-template-hash=5dc5c67d5f\nxnet          observability-clickhouse-0                          1/1     Running            4 (5d1h ago)     23d     172.16.166.137   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=clickhouse,app=deepflow,component=clickhouse,controller-revision-hash=observability-clickhouse-75b8d58ccc,statefulset.kubernetes.io/pod-name=observability-clickhouse-0\nxnet          observability-deepflow-app-654fcfbfbf-q8st6         1/1     Running            4 (5d1h ago)     23d     172.16.166.160   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow,app=deepflow,component=deepflow-app,pod-template-hash=654fcfbfbf\nxnet          observability-deepflow-server-774dd6c5b7-9c998      1/1     Running            14 (5d1h ago)    23d     172.16.166.135   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow,app=deepflow,component=deepflow-server,pod-template-hash=774dd6c5b7\nxnet          observability-filebeat-ffwsp                        1/1     Running            4 (5d1h ago)     23d     172.16.219.80    master   <none>           <none>            app=observability-filebeat,chart=observability-1.0.2,controller-revision-hash=57fb88b7c5,heritage=Helm,pod-template-generation=1,release=observability\nxnet          observability-filebeat-m58xw                        1/1     Running            5 (5d1h ago)     23d     172.16.166.134   node1    <none>           <none>            app=observability-filebeat,chart=observability-1.0.2,controller-revision-hash=57fb88b7c5,heritage=Helm,pod-template-generation=1,release=observability\nxnet          observability-filebeat-w6gtr                        1/1     Running            5 (5d1h ago)     19d     172.16.104.53    node2    <none>           <none>            app=observability-filebeat,chart=observability-1.0.2,controller-revision-hash=57fb88b7c5,heritage=Helm,pod-template-generation=1,release=observability\nxnet          observability-grafana-58bf9cfd6f-ndsxr              4/4     Running            36 (5d1h ago)    23d     172.16.166.144   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=grafana,app.kubernetes.io/version=12.0.2,helm.sh/chart=grafana-9.2.7,pod-template-hash=58bf9cfd6f\nxnet          observability-kepler-2sgrr                          1/1     Running            6 (5d1h ago)     23d     10.2.0.49        node1    <none>           <none>            app.kubernetes.io/component=exporter,app.kubernetes.io/name=kepler-kepler,controller-revision-hash=7c6c5f9bd6,pod-template-generation=1\nxnet          observability-kepler-7scjm                          1/1     Running            7 (5d1h ago)     23d     10.2.0.48        master   <none>           <none>            app.kubernetes.io/component=exporter,app.kubernetes.io/name=kepler-kepler,controller-revision-hash=7c6c5f9bd6,pod-template-generation=1\nxnet          observability-kepler-ggstf                          1/1     Running            8 (5d1h ago)     19d     10.2.0.50        node2    <none>           <none>            app.kubernetes.io/component=exporter,app.kubernetes.io/name=kepler-kepler,controller-revision-hash=7c6c5f9bd6,pod-template-generation=1\nxnet          observability-kibana-65d7c45f6d-tm4vv               1/1     Running            4 (5d1h ago)     23d     172.16.166.191   node1    <none>           <none>            app=observability-kibana,pod-template-hash=65d7c45f6d,release=observability\nxnet          observability-kube-state-metrics-798986b8b7-6z2dq   1/1     Running            4 (5d1h ago)     23d     172.16.219.65    master   <none>           <none>            app.kubernetes.io/component=metrics,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=kube-state-metrics,app.kubernetes.io/part-of=kube-state-metrics,app.kubernetes.io/version=2.15.0,helm.sh/chart=kube-state-metrics-5.37.0,pod-template-hash=798986b8b7,release=observability\nxnet          observability-mysql-764f9d5966-wh2bc                1/1     Running            4 (5d1h ago)     23d     172.16.219.98    master   <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=mysql,app=deepflow,component=mysql,pod-template-hash=764f9d5966\nxnet          observability-operator-d4495dc86-69lgw              1/1     Running            4 (5d1h ago)     23d     172.16.166.182   node1    <none>           <none>            app.kubernetes.io/component=prometheus-operator,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=observability-prometheus-operator,app.kubernetes.io/part-of=observability,app.kubernetes.io/version=1.0.2,app=observability-operator,chart=observability-1.0.2,heritage=Helm,pod-template-hash=d4495dc86,release=observability\nxnet          observability-prometheus-node-exporter-lj75r        1/1     Running            4 (5d1h ago)     23d     10.2.0.48        master   <none>           <none>            app.kubernetes.io/component=metrics,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=prometheus-node-exporter,app.kubernetes.io/part-of=prometheus-node-exporter,app.kubernetes.io/version=1.9.1,controller-revision-hash=74f4f4b87d,helm.sh/chart=prometheus-node-exporter-4.47.0,jobLabel=node-exporter,pod-template-generation=1,release=observability\nxnet          observability-prometheus-node-exporter-qp2qd        1/1     Running            4 (5d1h ago)     19d     10.2.0.50        node2    <none>           <none>            app.kubernetes.io/component=metrics,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=prometheus-node-exporter,app.kubernetes.io/part-of=prometheus-node-exporter,app.kubernetes.io/version=1.9.1,controller-revision-hash=74f4f4b87d,helm.sh/chart=prometheus-node-exporter-4.47.0,jobLabel=node-exporter,pod-template-generation=1,release=observability\nxnet          observability-prometheus-node-exporter-wnbb8        1/1     Running            4 (5d1h ago)     23d     10.2.0.49        node1    <none>           <none>            app.kubernetes.io/component=metrics,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=prometheus-node-exporter,app.kubernetes.io/part-of=prometheus-node-exporter,app.kubernetes.io/version=1.9.1,controller-revision-hash=74f4f4b87d,helm.sh/chart=prometheus-node-exporter-4.47.0,jobLabel=node-exporter,pod-template-generation=1,release=observability\nxnet          observability-telegraf-79f45d86-4kzkm               1/1     Running            4 (5d1h ago)     23d     172.16.219.113   master   <none>           <none>            app.kubernetes.io/component=telegraf,app.kubernetes.io/instance=observability,app.kubernetes.io/name=observability,pod-template-hash=79f45d86\nxnet          prometheus-observability-prometheus-0               2/2     Running            16 (5d1h ago)    23d     172.16.166.142   node1    <none>           <none>            app.kubernetes.io/instance=observability-prometheus,app.kubernetes.io/managed-by=prometheus-operator,app.kubernetes.io/name=prometheus,app.kubernetes.io/version=3.4.1,controller-revision-hash=prometheus-observability-prometheus-9467b46f7,operator.prometheus.io/name=observability-prometheus,operator.prometheus.io/shard=0,prometheus=observability-prometheus,statefulset.kubernetes.io/pod-name=prometheus-observability-prometheus-0\nxnet          xnet-agent-568f547566-jdsgp                         1/1     Running            4 (5d1h ago)     108d    172.16.104.40    node2    <none>           <none>            app=xnet-agent,pod-template-hash=568f547566", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_namespace", "data": "NAME                             READY   STATUS             RESTARTS         AGE   IP              NODE    NOMINATED NODE   READINESS GATES   LABELS\nappconfigfail-7649c79dc5-q4zjz   0/1     CrashLoopBackOff   11 (4m47s ago)   36m   172.16.104.57   node2   <none>           <none>            app=appconfigfail,l4-scenario=config-bootstrap-fail,pod-template-hash=7649c79dc5", "duration_s": 0}, {"tool": "TodoWrite", "data": "Investigation plan updated with 4 tasks.\n\n# CURRENT INVESTIGATION TASKS\n\n**Task Status**: 1 completed, 1 in progress, 2 pending\n\n[ ] [t3] 采集节点健康状态证据\n[ ] [t4] 汇总分析并给出结论\n[~] [t2] 深入采集异常Pod的详细证据\n[✓] [t1] 获取集群概览信息（节点、异常Pod）\n\n**Instructions**: Use TodoWrite tool to update task status as you work.", "duration_s": 0}, {"tool": "kubectl_describe", "data": "Name:             appconfigfail-7649c79dc5-q4zjz\nNamespace:        aiops-e2e\nPriority:         0\nService Account:  default\nNode:             node2/10.2.0.50\nStart Time:       Wed, 22 Apr 2026 07:38:39 +0000\nLabels:           app=appconfigfail\n                  l4-scenario=config-bootstrap-fail\n                  pod-template-hash=7649c79dc5\nAnnotations:      cni.projectcalico.org/containerID: c6399f913454284036a261148882084711e3bf6f9788cf1df749c56fbda41b6f\n                  cni.projectcalico.org/podIP: 172.16.104.57/32\n                  cni.projectcalico.org/podIPs: 172.16.104.57/32\n                  k8s.v1.cni.cncf.io/network-status:\n                    [{\n                        \"name\": \"k8s-pod-network\",\n                        \"ips\": [\n                            \"172.16.104.57\"\n                        ],\n                        \"default\": true,\n                        \"dns\": {}\n                    }]\n                  k8s.v1.cni.cncf.io/networks-status:\n                    [{\n                        \"name\": \"k8s-pod-network\",\n                        \"ips\": [\n                            \"172.16.104.57\"\n                        ],\n                        \"default\": true,\n                        \"dns\": {}\n                    }]\nStatus:           Running\nIP:               172.16.104.57\nIPs:\n  IP:           172.16.104.57\nControlled By:  ReplicaSet/appconfigfail-7649c79dc5\nContainers:\n  app:\n    Container ID:  containerd://1de791fae33178a297c96c8a6a966e0b2a851f374894f831be7214de4985d448\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Port:          <none>\n    Host Port:     <none>\n    Command:\n      sh\n      -c\n    Args:\n      echo \"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\"\n      echo \"L4_LAYER_APPLICATION: true\"\n      echo \"L4_SCENARIO: config-bootstrap-fail\"\n      echo \"L4_ERROR_TYPE: application-config-validation\"\n      if [ -z \"${APP_BOOT_MODE:-}\" ]; then\n        echo \"FATAL: missing required APP_BOOT_MODE\"\n        echo \"FATAL: business config validation failed before server startup\"\n        exit 42\n      fi\n      echo \"unexpected success\"\n      exit 1\n      \n    State:          Waiting\n      Reason:       CrashLoopBackOff\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42\n      Started:      Wed, 22 Apr 2026 08:10:09 +0000\n      Finished:     Wed, 22 Apr 2026 08:10:09 +0000\n    Ready:          False\n    Restart Count:  11\n    Environment:    <none>\n    Mounts:\n      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-zndsj (ro)\nConditions:\n  Type              Status\n  Initialized       True \n  Ready             False \n  ContainersReady   False \n  PodScheduled      True \nVolumes:\n  kube-api-access-zndsj:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    TokenExpirationSeconds:  3607\n    ConfigMapName:           kube-root-ca.crt\n    ConfigMapOptional:       <nil>\n    DownwardAPI:             true\nQoS Class:                   BestEffort\nNode-Selectors:              <none>\nTolerations:                 node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\n                             node.kubernetes.io/unreachable:NoExecute op=Exists for 300s\nEvents:\n  Type     Reason          Age                  From               Message\n  ----     ------          ----                 ----               -------\n  Normal   Scheduled       36m                  default-scheduler  Successfully assigned aiops-e2e/appconfigfail-7649c79dc5-q4zjz to node2\n  Normal   AddedInterface  36m                  multus             Add eth0 [172.16.104.57/32] from k8s-pod-network\n  Normal   Pulled          34m (x5 over 36m)    kubelet            Container image \"busybox:1.36\" already present on machine\n  Normal   Created         34m (x5 over 36m)    kubelet            Created container app\n  Normal   Started         34m (x5 over 36m)    kubelet            Started container app\n  Warning  BackOff         80s (x162 over 36m)  kubelet            Back-off restarting failed container app in pod appconfigfail-7649c79dc5-q4zjz_aiops-e2e(77ea5d65-2a07-47e0-b606-3f03812dcc6a)", "duration_s": 0}, {"tool": "kubectl_get_yaml", "data": "apiVersion: v1\nkind: Pod\nmetadata:\n  annotations:\n    cni.projectcalico.org/containerID: c6399f913454284036a261148882084711e3bf6f9788cf1df749c56fbda41b6f\n    cni.projectcalico.org/podIP: 172.16.104.57/32\n    cni.projectcalico.org/podIPs: 172.16.104.57/32\n    k8s.v1.cni.cncf.io/network-status: |-\n      [{\n          \"name\": \"k8s-pod-network\",\n          \"ips\": [\n              \"172.16.104.57\"\n          ],\n          \"default\": true,\n          \"dns\": {}\n      }]\n    k8s.v1.cni.cncf.io/networks-status: |-\n      [{\n          \"name\": \"k8s-pod-network\",\n          \"ips\": [\n              \"172.16.104.57\"\n          ],\n          \"default\": true,\n          \"dns\": {}\n      }]\n  creationTimestamp: \"2026-04-22T07:38:39Z\"\n  generateName: appconfigfail-7649c79dc5-\n  labels:\n    app: appconfigfail\n    l4-scenario: config-bootstrap-fail\n    pod-template-hash: 7649c79dc5\n  name: appconfigfail-7649c79dc5-q4zjz\n  namespace: aiops-e2e\n  ownerReferences:\n  - apiVersion: apps/v1\n    blockOwnerDeletion: true\n    controller: true\n    kind: ReplicaSet\n    name: appconfigfail-7649c79dc5\n    uid: 7b8b69a7-397c-4d54-b9c7-818ef9ad399f\n  resourceVersion: \"46419488\"\n  uid: 77ea5d65-2a07-47e0-b606-3f03812dcc6a\nspec:\n  containers:\n  - args:\n    - |\n      echo \"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\"\n      echo \"L4_LAYER_APPLICATION: true\"\n      echo \"L4_SCENARIO: config-bootstrap-fail\"\n      echo \"L4_ERROR_TYPE: application-config-validation\"\n      if [ -z \"${APP_BOOT_MODE:-}\" ]; then\n        echo \"FATAL: missing required APP_BOOT_MODE\"\n        echo \"FATAL: business config validation failed before server startup\"\n        exit 42\n      fi\n      echo \"unexpected success\"\n      exit 1\n    command:\n    - sh\n    - -c\n    image: busybox:1.36\n    imagePullPolicy: Never\n    name: app\n    resources: {}\n    terminationMessagePath: /dev/termination-log\n    terminationMessagePolicy: File\n    volumeMounts:\n    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount\n      name: kube-api-access-zndsj\n      readOnly: true\n  dnsPolicy: ClusterFirst\n  enableServiceLinks: true\n  nodeName: node2\n  preemptionPolicy: PreemptLowerPriority\n  priority: 0\n  restartPolicy: Always\n  schedulerName: default-scheduler\n  securityContext: {}\n  serviceAccount: default\n  serviceAccountName: default\n  terminationGracePeriodSeconds: 30\n  tolerations:\n  - effect: NoExecute\n    key: node.kubernetes.io/not-ready\n    operator: Exists\n    tolerationSeconds: 300\n  - effect: NoExecute\n    key: node.kubernetes.io/unreachable\n    operator: Exists\n    tolerationSeconds: 300\n  volumes:\n  - name: kube-api-access-zndsj\n    projected:\n      defaultMode: 420\n      sources:\n      - serviceAccountToken:\n          expirationSeconds: 3607\n          path: token\n      - configMap:\n          items:\n          - key: ca.crt\n            path: ca.crt\n          name: kube-root-ca.crt\n      - downwardAPI:\n          items:\n          - fieldRef:\n              apiVersion: v1\n              fieldPath: metadata.namespace\n            path: namespace\nstatus:\n  conditions:\n  - lastProbeTime: null\n    lastTransitionTime: \"2026-04-22T07:38:39Z\"\n    status: \"True\"\n    type: Initialized\n  - lastProbeTime: null\n    lastTransitionTime: \"2026-04-22T07:38:39Z\"\n    message: 'containers with unready status: [app]'\n    reason: ContainersNotReady\n    status: \"False\"\n    type: Ready\n  - lastProbeTime: null\n    lastTransitionTime: \"2026-04-22T07:38:39Z\"\n    message: 'containers with unready status: [app]'\n    reason: ContainersNotReady\n    status: \"False\"\n    type: ContainersReady\n  - lastProbeTime: null\n    lastTransitionTime: \"2026-04-22T07:38:39Z\"\n    status: \"True\"\n    type: PodScheduled\n  containerStatuses:\n  - containerID: containerd://1de791fae33178a297c96c8a6a966e0b2a851f374894f831be7214de4985d448\n    image: docker.io/library/busybox:1.36\n    imageID: sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    lastState:\n      terminated:\n        containerID: containerd://1de791fae33178a297c96c8a6a966e0b2a851f374894f831be7214de4985d448\n        exitCode: 42\n        finishedAt: \"2026-04-22T08:10:09Z\"\n        reason: Error\n        startedAt: \"2026-04-22T08:10:09Z\"\n    name: app\n    ready: false\n    restartCount: 11\n    started: false\n    state:\n      waiting:\n        message: back-off 5m0s restarting failed container=app pod=appconfigfail-7649c79dc5-q4zjz_aiops-e2e(77ea5d65-2a07-47e0-b606-3f03812dcc6a)\n        reason: CrashLoopBackOff\n  hostIP: 10.2.0.50\n  phase: Running\n  podIP: 172.16.104.57\n  podIPs:\n  - ip: 172.16.104.57\n  qosClass: BestEffort\n  startTime: \"2026-04-22T07:38:39Z\"", "duration_s": 0}, {"tool": "kubectl_events", "data": "LAST SEEN             TYPE      REASON           OBJECT                               MESSAGE\n36m                   Normal    Scheduled        Pod/appconfigfail-7649c79dc5-q4zjz   Successfully assigned aiops-e2e/appconfigfail-7649c79dc5-q4zjz to node2\n36m                   Normal    AddedInterface   Pod/appconfigfail-7649c79dc5-q4zjz   Add eth0 [172.16.104.57/32] from k8s-pod-network\n34m (x5 over 36m)     Normal    Pulled           Pod/appconfigfail-7649c79dc5-q4zjz   Container image \"busybox:1.36\" already present on machine\n34m (x5 over 36m)     Normal    Created          Pod/appconfigfail-7649c79dc5-q4zjz   Created container app\n34m (x5 over 36m)     Normal    Started          Pod/appconfigfail-7649c79dc5-q4zjz   Started container app\n80s (x162 over 36m)   Warning   BackOff          Pod/appconfigfail-7649c79dc5-q4zjz   Back-off restarting failed container app in pod appconfigfail-7649c79dc5-q4zjz_aiops-e2e(77ea5d65-2a07-47e0-b606-3f03812dcc6a)", "duration_s": 0}, {"tool": "run_bash_command", "data": "{\"success\": true, \"stdout\": \"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\\nL4_LAYER_APPLICATION: true\\nL4_SCENARIO: config-bootstrap-fail\\nL4_ERROR_TYPE: application-config-validation\\nFATAL: missing required APP_BOOT_MODE\\nFATAL: business config validation failed before server startup\\n\", \"stderr\": \"\", \"returncode\": 0}", "duration_s": 0}, {"tool": "kubectl_describe", "data": "Name:               node2\nRoles:              <none>\nLabels:             beta.kubernetes.io/arch=amd64\n                    beta.kubernetes.io/os=linux\n                    kubernetes.io/arch=amd64\n                    kubernetes.io/hostname=node2\n                    kubernetes.io/os=linux\nAnnotations:        kubeadm.alpha.kubernetes.io/cri-socket: unix:///var/run/containerd/containerd.sock\n                    node.alpha.kubernetes.io/ttl: 0\n                    projectcalico.org/IPv4Address: 10.2.0.50/19\n                    projectcalico.org/IPv4IPIPTunnelAddr: 172.16.104.0\n                    volumes.kubernetes.io/controller-managed-attach-detach: true\nCreationTimestamp:  Thu, 25 Sep 2025 03:10:26 +0000\nTaints:             <none>\nUnschedulable:      false\nLease:\n  HolderIdentity:  node2\n  AcquireTime:     <unset>\n  RenewTime:       Wed, 22 Apr 2026 08:15:03 +0000\nConditions:\n  Type                 Status  LastHeartbeatTime                 LastTransitionTime                Reason                       Message\n  ----                 ------  -----------------                 ------------------                ------                       -------\n  NetworkUnavailable   False   Fri, 17 Apr 2026 07:03:52 +0000   Fri, 17 Apr 2026 07:03:52 +0000   CalicoIsUp                   Calico is running on this node\n  MemoryPressure       False   Wed, 22 Apr 2026 08:13:40 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletHasSufficientMemory   kubelet has sufficient memory available\n  DiskPressure         False   Wed, 22 Apr 2026 08:13:40 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletHasNoDiskPressure     kubelet has no disk pressure\n  PIDPressure          False   Wed, 22 Apr 2026 08:13:40 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletHasSufficientPID      kubelet has sufficient PID available\n  Ready                True    Wed, 22 Apr 2026 08:13:40 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletReady                 kubelet is posting ready status. AppArmor enabled\nAddresses:\n  InternalIP:  10.2.0.50\n  Hostname:    node2\nCapacity:\n  cpu:                12\n  ephemeral-storage:  203770680Ki\n  hugepages-1Gi:      0\n  hugepages-2Mi:      0\n  memory:             32860484Ki\n  pods:               110\nAllocatable:\n  cpu:                12\n  ephemeral-storage:  187795058378\n  hugepages-1Gi:      0\n  hugepages-2Mi:      0\n  memory:             32758084Ki\n  pods:               110\nSystem Info:\n  Machine ID:                 6bb27862c82149418d0f5624411d0b22\n  System UUID:                0f5af30a-d385-493c-bc8b-5442fd024eee\n  Boot ID:                    0ea98079-ad10-4a20-85f5-19b34afd257e\n  Kernel Version:             5.15.0-174-generic\n  OS Image:                   Ubuntu 22.04.4 LTS\n  Operating System:           linux\n  Architecture:               amd64\n  Container Runtime Version:  containerd://1.6.32\n  Kubelet Version:            v1.26.8\n  Kube-Proxy Version:         v1.26.8\nNon-terminated Pods:          (15 in total)\n  Namespace                   Name                                            CPU Requests  CPU Limits  Memory Requests  Memory Limits  Age\n  ---------                   ----                                            ------------  ----------  ---------------  -------------  ---\n  aiops-e2e                   appconfigfail-7649c79dc5-q4zjz                  0 (0%)        0 (0%)      0 (0%)           0 (0%)         36m\n  aiops                       aiops-copilot-76779bb6df-4bcrf                  250m (2%)     1 (8%)      512Mi (1%)       2Gi (6%)       6h37m\n  default                     exec-test                                       0 (0%)        0 (0%)      0 (0%)           0 (0%)         2d4h\n  default                     network-test-from-running                       0 (0%)        0 (0%)      0 (0%)           0 (0%)         2d2h\n  default                     nfs-client-provisioner-6fcd4994c9-lczf6         0 (0%)        0 (0%)      0 (0%)           0 (0%)         86d\n  kube-system                 calico-node-d2dhp                               250m (2%)     0 (0%)      0 (0%)           0 (0%)         183d\n  kube-system                 kube-multus-ds-x7h9s                            100m (0%)     100m (0%)   50Mi (0%)        50Mi (0%)      183d\n  kube-system                 kube-proxy-69zzr                                0 (0%)        0 (0%)      0 (0%)           0 (0%)         28d\n  mcp                         mcp-server-manager-8677f6896c-d4mr9             200m (1%)     1 (8%)      1G (2%)          2560Mi (8%)    46h\n  xnet                        deepflow-agent-trc8k                            100m (0%)     1 (8%)      128Mi (0%)       768Mi (2%)     19d\n  xnet                        ham-p9dxv                                       0 (0%)        0 (0%)      0 (0%)           0 (0%)         177d\n  xnet                        observability-filebeat-w6gtr                    100m (0%)     1 (8%)      100Mi (0%)       200Mi (0%)     19d\n  xnet                        observability-kepler-ggstf                      0 (0%)        0 (0%)      0 (0%)           0 (0%)         19d\n  xnet                        observability-prometheus-node-exporter-qp2qd    0 (0%)        0 (0%)      0 (0%)           0 (0%)         19d\n  xnet                        xnet-agent-568f547566-jdsgp                     0 (0%)        0 (0%)      0 (0%)           0 (0%)         108d\nAllocated resources:\n  (Total limits may be over 100 percent, i.e., overcommitted.)\n  Resource           Requests         Limits\n  --------           --------         ------\n  cpu                1 (8%)           4100m (34%)\n  memory             1828375040 (5%)  5626Mi (17%)\n  ephemeral-storage  0 (0%)           0 (0%)\n  hugepages-1Gi      0 (0%)           0 (0%)\n  hugepages-2Mi      0 (0%)           0 (0%)\nEvents:              <none>", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_namespace", "data": "NAME            READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES         SELECTOR            LABELS\nappconfigfail   0/1     1            0           36m   app          busybox:1.36   app=appconfigfail   l4-scenario=config-bootstrap-fail", "duration_s": 0}, {"tool": "TodoWrite", "data": "Investigation plan updated with 4 tasks.\n\n# CURRENT INVESTIGATION TASKS\n\n**Task Status**: 3 completed, 1 in progress, 0 pending\n\n[~] [t4] 汇总分析并给出结论\n[✓] [t1] 获取集群概览信息（节点、异常Pod）\n[✓] [t2] 深入采集异常Pod的详细证据\n[✓] [t3] 采集节点健康状态证据\n\n**Instructions**: Use TodoWrite tool to update task status as you work.", "duration_s": 0}, {"tool": "TodoWrite", "data": "Investigation plan updated with 4 tasks.\n\n# CURRENT INVESTIGATION TASKS\n\n**Task Status**: 4 completed, 0 in progress, 0 pending\n\n[✓] [t1] 获取集群概览信息（节点、异常Pod）\n[✓] [t2] 深入采集异常Pod的详细证据\n[✓] [t3] 采集节点健康状态证据\n[✓] [t4] 汇总分析并给出结论\n\n**Instructions**: Use TodoWrite tool to update task status as you work.", "duration_s": 0}], "llm_analysis": "---\n\n## 📋 集群健康诊断报告\n\n### ✅ 集群整体状态：基本健康\n\n| 资源 | 状态 |\n|------|------|\n| **3个节点** | ✅ 全部 Ready（master, node1, node2） |\n| **系统组件** | ✅ etcd, kube-apiserver, kube-scheduler, kube-controller-manager 均 Running |\n| **网络组件** | ✅ Calico, CoreDNS, Multus, kube-proxy 均 Running |\n| **存储** | ✅ NFS Client Provisioner Running |\n\n---\n\n### ⚠️ 发现 1 个异常 Pod\n\n| Pod | 命名空间 | 状态 | 退出码 | 节点 |\n|:---|:---|:---|:---:|:---:|\n| **appconfigfail-7649c79dc5-q4zjz** | `aiops-e2e` | **CrashLoopBackOff** (重启11次) | **42** | node2 |\n\n#### 🔍 详细诊断\n\n**Pod 基本信息：**\n- 镜像：`busybox:1.36`（已存在于节点，拉取正常 ✅）\n- 调度：正常分配到 node2 ✅\n- 网络：已获取 IP `172.16.104.57` ✅\n\n**根本原因 — 应用启动配置校验失败：**\n\nPod 的启动脚本中执行了配置校验，关键日志输出：\n\n```\nL4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_LAYER_APPLICATION: true\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: application-config-validation\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup\n```\n\n**问题链：**\n1. 容器启动脚本检查环境变量 `APP_BOOT_MODE` 是否存在\n2. 该环境变量**未设置**（Pod 的 `Environment: <none>`）\n3. 应用主动退出，返回 **Exit Code 42**（非 OOM、非系统信号）\n4. kubelet 检测到容器退出，按 `restartPolicy: Always` 不断重启\n5. 每次立即失败 → **CrashLoopBackOff**（当前退避等待 5 分钟）\n\n**排除的其他原因：**\n- ❌ 非 OOMKilled（退出码 42，非 137）\n- ❌ 非镜像拉取失败（`ImagePullPolicy: Never`，镜像已在本地）\n- ❌ 非节点问题（node2 状态 Ready，资源充足：CPU 8%/34%，内存 5%/17%）\n- ❌ 非网络问题（CNI 配置正常，Pod 已分配 IP）\n\n---\n\n### 📋 总结\n\n| 项目 | 状态 |\n|:---|:---:|\n| 🟢 集群节点 | 3/3 Ready |\n| 🟢 系统组件 | 全部正常 |\n| 🟡 **异常 Pod** | **1个** — `appconfigfail`（CrashLoopBackOff） |\n| 🟢 其他应用 | 全部正常 |\n\n**唯一的问题 Pod `appconfigfail` 是 L4 应用层配置问题**：启动脚本要求设置环境变量 `APP_BOOT_MODE` 但未提供，应用主动退出（Exit Code 42），与集群基础设施无关。\n\n---\n\n### 🔧 修复建议\n\n要修复此 Pod，请为 Deployment 添加缺失的环境变量 `APP_BOOT_MODE`：\n\n```bash\n# 编辑 Deployment\nkubectl edit deployment appconfigfail -n aiops-e2e\n```\n\n在 container spec 中添加：\n```yaml\nenv:\n  - name: APP_BOOT_MODE\n    value: \"production\"   # 或其他合适的值\n```\n\n或者直接设置（如支持）：\n```bash\nkubectl set env deployment/appconfigfail -n aiops-e2e APP_BOOT_MODE=production\n```", "collection_summary": "计划 9 项，实际采集 9 项，未采集 0 项，完整度 100%", "evidence_inventory": [{"id": "auto_0", "description": "工具采集: kubectl_get_by_kind_in_cluster", "level": "important", "collected": true, "source": "thinking_auto"}, {"id": "auto_1", "description": "工具采集: kubectl_get_by_kind_in_cluster", "level": "important", "collected": true, "source": "thinking_auto"}, {"id": "auto_2", "description": "工具采集: kubectl_get_by_kind_in_namespace", "level": "important", "collected": true, "source": "thinking_auto"}, {"id": "auto_3", "description": "工具采集: kubectl_describe", "level": "important", "collected": true, "source": "thinking_auto"}, {"id": "auto_4", "description": "工具采集: kubectl_get_yaml", "level": "important", "collected": true, "source": "thinking_auto"}, {"id": "auto_5", "description": "工具采集: kubectl_events", "level": "important", "collected": true, "source": "thinking_auto"}, {"id": "auto_6", "description": "工具采集: run_bash_command", "level": "important", "collected": true, "source": "thinking_auto"}, {"id": "auto_7", "description": "工具采集: kubectl_describe", "level": "important", "collected": true, "source": "thinking_auto"}, {"id": "auto_8", "description": "工具采集: kubectl_get_by_kind_in_namespace", "level": "important", "collected": true, "source": "thinking_auto"}], "missing_reasons": [], "early_stop": {"triggered": false, "reason": "", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 9/9 项, 完整度: 100%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (22.8s)
   📤 → 下游数据: root_cause=
   confidence=95%
   causal_chain={"root_cause": "应用 Deployment 配置缺失：容器启动所需的环境变量 `APP_BOOT_MODE` 未定义", "propagation": "应用启动脚本执行配置校验 -> 检测到 `APP_BOOT_MODE` 缺失 -> 触发 `L4_CONFIG_BOOTSTRAP_FAIL` 错误 -> 调用 `exit(42)` 主动退出进程", "direct_cause": "容器进程主动退出并返回退出码 42，导致 kubelet 根据 restartPolicy 不断重启容器", "manifestation": "Pod 处于 CrashLoopBackOff 状态，已重启 11 次，无法进入 Ready 状态，Deployment 可用副本数为 0"}
   rca_analysis={"phenomenon": "集群中 Pod appconfigfail-7649c79dc5-q4zjz 处于 CrashLoopBackOff 状态，已重启 11 次，退出码为 42", "evidence_inventory": [{"id": "e1", "content": "3 个节点（master, node1, node2）均处于 Ready 状态", "source": "kubectl_get_by_kind_in_cluster", "reliability": "高"}, {"id": "e2", "content": "Pod appconfigfail-7649c79dc5-q4zjz 在 aiops-e2e 命名空间，状态为 CrashLoopBackOff，重启 11 次，退出码 42", "source": "kubectl_get_by_kind_in_cluster", "reliability": "高"}, {"id": "e3", "content": "Pod 已成功调度到 node2（10.2.0.50），已分配 IP 172.16.104.57/32", "source": "kubectl_describe, kubectl_get_yaml", "reliability": "高"}, {"id": "e4", "content": "Pod 事件显示调度成功、网络接口已添加、镜像已拉取（busybox:1.36）", "source": "kubectl_events", "reliability": "高"}, {"id": "e5", "content": "Pod 日志明确输出：L4_CONFIG_BOOTSTRAP_FAIL, missing required APP_BOOT_MODE, business config validation failed before server startup", "source": "run_bash_command", "reliability": "高"}, {"id": "e6", "content": "node2 节点描述显示节点状态正常，无异常 taint 或条件", "source": "kubectl_describe (node2)", "reliability": "高"}, {"id": "e7", "content": "Deployment appconfigfail 的期望副本为 1，当前可用为 0", "source": "kubectl_get_by_kind_in_namespace (deployment)", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "master Ready, node1 Ready (通过上下文推断), node2 Ready (通过 kubectl_describe 确认)。集群节点健康度 100%", "interpretation": "集群基础设施层（节点、网络、存储）无异常，排除节点级故障"}, {"evidence_id": "e2", "raw_data": "Pod 状态: CrashLoopBackOff, 重启次数: 11, 退出码: 42, 运行时间: 36m, 节点: node2, IP: 172.16.104.57", "interpretation": "Pod 正在反复崩溃重启，退出码 42 是非标准退出码，非 OOM（137）或系统信号终止（如 143）"}, {"evidence_id": "e3", "raw_data": "Pod 调度到 node2 (10.2.0.50), 分配 IP 172.16.104.57/32, 容器 ID: c6399f913454", "interpretation": "调度器和 CNI 网络插件工作正常，Pod 可以正常获取网络资源，排除调度和网络配置问题"}, {"evidence_id": "e4", "raw_data": "事件时间线: 36m ago Scheduled -> 36m ago AddedInterface -> 34m ago (x5) Pulled", "interpretation": "镜像拉取成功且已存在于节点本地，排除镜像拉取失败原因。容器启动后立即退出，导致反复重启"}, {"evidence_id": "e5", "raw_data": "stdout: 'L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config...FATAL: missing required APP_BOOT_MODE...FATAL: business config validation failed before server startup'", "interpretation": "这是最关键的证据。应用启动脚本执行了业务配置校验，发现必填环境变量 APP_BOOT_MODE 缺失，因此主动终止启动流程并退出，退出码 42"}, {"evidence_id": "e6", "raw_data": "node2 标签: kubernetes.io/hostname=node2, beta.kubernetes.io/os=linux; 无异常 Conditions", "interpretation": "node2 节点状态健康，资源充足（基于 LLM 分析报告中的 CPU 8%/34%, 内存 5%/17%），排除节点资源瓶颈"}, {"evidence_id": "e7", "raw_data": "Deployment appconfigfail: READY 0/1, UP-TO-DATE 1, AVAILABLE 0, AGE 36m", "interpretation": "Deployment 无法达到期望状态，因为其管理的 Pod 持续 CrashLoopBackOff，无法进入 Ready 状态"}], "causal_chain": {"root_cause": "应用 Deployment 配置缺失：容器启动所需的环境变量 `APP_BOOT_MODE` 未定义", "propagation": "应用启动脚本执行配置校验 -> 检测到 `APP_BOOT_MODE` 缺失 -> 触发 `L4_CONFIG_BOOTSTRAP_FAIL` 错误 -> 调用 `exit(42)` 主动退出进程", "direct_cause": "容器进程主动退出并返回退出码 42，导致 kubelet 根据 restartPolicy 不断重启容器", "manifestation": "Pod 处于 CrashLoopBackOff 状态，已重启 11 次，无法进入 Ready 状态，Deployment 可用副本数为 0"}, "root_cause_summary": "根因为应用层配置缺失。Pod `appconfigfail-7649c79dc5-q4zjz` 的启动脚本需要环境变量 `APP_BOOT_MODE` 来完成业务配置校验（证据 e5: 日志显示 'missing required APP_BOOT_MODE'），但该变量未在 Pod 或 Deployment 的 spec 中定义。导致应用在校验失败后主动调用 `exit(42)`（证据 e2: 退出码 42）。集群基础设施（节点、网络、镜像）均无异常（证据 e1, e3, e4, e6），问题定位在 L4 应用层。", "confidence": 0.95, "primary_runbooks": [], "alternative_causes": ["环境变量拼写错误：Deployment 中可能定义了 `APP_BOOT_MODE` 但拼写不一致（如 `APP_BOOT_MODE_` 或 `APP_BOOTMODE`），导致启动脚本找不到正确变量。", "ConfigMap/Secret 未挂载：如果 `APP_BOOT_MODE` 应来自 ConfigMap 或 Secret，但挂载配置错误导致变量未注入。"], "limitations": "证据充分，无显著局限性。Pod 的完整 YAML 未完全展示环境变量配置，但从日志直接指出的缺失变量来看，结论确定。退出码 42 的具体含义由应用定义，但日志已明确解释退出原因。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 95%
   🔗 因果链:
     根本原因: 应用 Deployment 配置缺失：容器启动所需的环境变量 `APP_BOOT_MODE` 未定义
     传导机制: 应用启动脚本执行配置校验 -> 检测到 `APP_BOOT_MODE` 缺失 -> 触发 `L4_CONFIG_BOOTSTRAP_FAIL` 错误 -> 调用 `exit(42)` 主动退出进程
     最终表现: Pod 处于 CrashLoopBackOff 状态，已重启 11 次，无法进入 Ready 状态，Deployment 可用副本数为 0


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (33.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6749 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 7.4s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
---
## 📊 集群状态速览

您的集群整体**基本健康**，但存在 **1 个应用层问题 Pod**，导致该应用不可用。

| 检查项 | 状态 | 详情 |
|:-------|:-----|:-----|
| **集群节点 (3个)** | ✅ **全部 Ready** | master, node1, node2 均正常 |
| **系统组件** | ✅ **全部正常** | etcd, kube-apiserver, kube-scheduler, kube-controller-manager, CoreDNS, Calico, kube-proxy 均 Running |
| **异常 Pod** | ⚠️ **1 个** | `appconfigfail-7649c79dc5-q4zjz` - **CrashLoopBackOff** (重启11次) |
| **其他应用** | ✅ **全部正常** | aiops-copilot, mcp-server-manager, 监控/可观测性组件等均 Running |

**核心结论**：唯一的问题 Pod `appconfigfail` 的根因是 **L4 应用层配置缺失**，与集群基础设施（节点、网络、存储）无关。该 Pod 因缺少必填环境变量 `APP_BOOT_MODE` 而主动退出（Exit Code 42）。

---

## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **问题层级** | L4 - 应用层 |
| **问题分类** | 应用启动配置校验失败 (Config Bootstrap Fail) |
| **置信度** | 高 (95%) |
| **证据完整度** | 9/9 (100%) |

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `appconfigfail-7649c79dc5-q4zjz` |
| Namespace | `aiops-e2e` |
| Node | `node2` (10.2.0.50) |
| 错误信息 | 退出码 42，日志含 `FATAL: missing required APP_BOOT_MODE` |
| Deployment | `appconfigfail` - 期望副本 1，可用副本 **0** |

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | 集群节点状态 | `kubectl_get_by_kind_in_cluster` | master **Ready**, node1 **Ready**, node2 **Ready** | 集群基础设施层无异常，排除节点级故障 |
| 2 | 异常 Pod 状态 | `kubectl_get_by_kind_in_cluster` | `STATUS: CrashLoopBackOff, RESTARTS: 11, EXIT CODE: 42, AGE: 36m` | Pod 正在反复崩溃重启，退出码 42 非 OOM (137) 或系统信号 |
| 3 | Pod 调度与网络 | `kubectl_describe`, `kubectl_get_yaml` | Pod 成功调度到 node2，分配 IP `172.16.104.57/32`，容器 ID: `c6399f913454` | 调度器和 CNI 网络插件工作正常，排除调度和网络问题 |
| 4 | Pod 事件 | `kubectl_events` | `36m Normal Scheduled -> 36m Normal AddedInterface -> 34m (x5) Normal Pulled -> Warning BackOff (x162)` | 镜像已存在于本地 (`busybox:1.36`)，拉取成功，容器启动后立即退出 |
| 5 | **容器日志** | `run_bash_command` | `L4_CONFIG_BOOTSTRAP_FAIL...FATAL: missing required APP_BOOT_MODE...FATAL: business config validation failed before server startup` | **关键证据**：启动脚本检查环境变量 `APP_BOOT_MODE` 失败，主动退出 |
| 6 | 节点 node2 健康 | `kubectl_describe (node2)` | `Conditions: Ready=True, MemoryPressure=False, DiskPressure=False, PIDPressure=False`，无 taint，资源充足 (CPU 8%/34%, 内存 5%/17%) | 节点状态健康，资源无压力，排除节点资源瓶颈 |
| 7 | Deployment 状态 | `kubectl_get_by_kind_in_namespace` | `appconfigfail: READY 0/1, UP-TO-DATE 1, AVAILABLE 0, AGE 36m` | Deployment 无法达到期望副本数，因 Pod 持续 CrashLoopBackOff |
| 8 | Pod 完整 YAML | `kubectl_get_yaml` | `Environment: <none>`（Pod 规范中**未定义任何环境变量**） | 确认环境变量 `APP_BOOT_MODE` 未在 Pod spec 中设置 |
| 9 | Pod 启动命令 | `kubectl_describe`, `kubectl_get_yaml` | `Command: sh -c ... if [ -z "${APP_BOOT_MODE:-}" ]; then ... exit 42; fi` | 启动脚本明确校验 `APP_BOOT_MODE`，缺失则 `exit 42` |

### 证据关联分析
- **证据 #5 + #8 + #9 印证**：容器日志显示 `missing required APP_BOOT_MODE` → Pod YAML 确认 `Environment: <none>` → 启动命令包含 `if [ -z "${APP_BOOT_MODE:-}" ]; then exit 42` → **根因确认为环境变量缺失**
- **证据 #1 + #6 印证**：3 个节点全部 Ready，node2 资源充足 (CPU 8%/34%, 内存 5%/17%) → **排除集群基础设施故障**
- **证据 #2 + #7 印证**：Pod 退出码 42 且 CrashLoopBackOff → Deployment 可用副本为 0 → **应用层问题导致服务不可用**

### 缺失证据
无缺失证据，证据完整度 100%。

## 🎯 根因分析
### 因果链
```
┌────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                       │
│ 应用 Deployment 配置缺失：容器启动所需的环境变量 `APP_BOOT_MODE` 未定义           │
│ （Pod YAML 中 Environment: <none>，启动脚本检查 `${APP_BOOT_MODE:-}` 为空）      │
└────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                       │
│ 容器启动 → 执行 sh -c 启动脚本 → 执行 `if [ -z "${APP_BOOT_MODE:-}" ]` 检查      │
│ → 变量为空，条件为真 → 输出 `FATAL: missing required APP_BOOT_MODE`              │
│ → 调用 `exit 42` 主动终止进程                                                   │
└────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                       │
│ 容器进程主动退出并返回退出码 42（非 OOM、非系统信号），kubelet 检测到退出后        │
│ 根据 restartPolicy: Always 不断重启容器                                         │
└────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                   │
│ Pod 状态 CrashLoopBackOff，已重启 11 次（当前退避等待 5 分钟），Deployment 可用    │
│ 副本数为 0，应用完全不可用                                                      │
└────────────────────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #5 (日志: `missing required APP_BOOT_MODE`)、证据 #8 (Pod YAML: `Environment: <none>`) 和证据 #9 (启动命令: `exit 42`)，问题的根本原因是 **Pod `appconfigfail-7649c79dc5-q4zjz` 的 Deployment 配置缺失了必填环境变量 `APP_BOOT_MODE`**，导致应用启动配置校验失败后主动退出 (Exit Code 42)，进入 CrashLoopBackOff 状态。

**置信度**：高 (95%)
- ✅ 容器日志直接输出缺失变量名称，明确指向问题
- ✅ Pod YAML 确认无任何环境变量定义
- ✅ 启动脚本逻辑与日志输出完全吻合
- ✅ 集群基础设施（节点、网络、镜像）全部正常，无其他异常

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 为 Deployment 添加缺失的环境变量**
```bash
kubectl set env deployment/appconfigfail -n aiops-e2e APP_BOOT_MODE=production
```
*依据*：日志明确指出 `missing required APP_BOOT_MODE`，添加此环境变量后 Pod 将自动重启并正常启动。

**2. [验证] 确认 Pod 恢复正常**
```bash
# 查看 Pod 状态（等待约 10 秒后执行）
kubectl get pod -n aiops-e2e -l app=appconfigfail
# 预期输出：STATUS 为 Running，READY 为 1/1

# 查看最新 Pod 日志，确认不再报错
kubectl logs -n aiops-e2e -l app=appconfigfail --tail=20
# 预期输出：无 FATAL 错误，显示 "unexpected success" 或其他正常日志
```

### 后续优化
1. **检查 Deployment 完整配置**：使用 `kubectl edit deployment appconfigfail -n aiops-e2e` 查看完整的环境变量和 ConfigMap/Secret 挂载配置，确保其他必要配置已就绪。
2. **应用配置规范化**：将必要配置（如环境变量）纳入 Deployment YAML 或 Helm Chart 模板，避免遗漏。
3. **添加启动健康检查**：配置 `livenessProbe` 和 `readinessProbe`，让 Kubernetes 能更早发现并处理应用层启动问题。

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 设置环境变量 | `kubectl set env deployment/appconfigfail -n aiops-e2e APP_BOOT_MODE=production` | `deployment.apps/appconfigfail env updated` |
| 2. 确认 Pod 运行 | `kubectl get pod -n aiops-e2e -l app=appconfigfail` | STATUS: Running, READY: 1/1 |
| 3. 检查重启次数 | `kubectl get pod -n aiops-e2e -l app=appconfigfail -o jsonpath='{.items[0].status.containerStatuses[0].restartCount}'` | 不再增加（或从 0 开始） |
| 4. 确认 Deployment 可用 | `kubectl get deployment appconfigfail -n aiops-e2e` | AVAILABLE: 1 |

## ⚠️ 注意事项
- 本问题为**应用层配置问题**，与集群基础设施（节点、网络、存储、系统组件）**完全无关**，集群整体健康度良好
- `APP_BOOT_MODE` 的值 `production` 仅为示例，请根据应用实际需要的值进行设置
- 如果应用需要多个环境变量或依赖 ConfigMap/Secret，建议通过 `kubectl edit deployment` 完整配置或更新 Helm Chart values

---

## 📊 性能统计

├─ 总耗时: 2.1m
├─ 问题定位: 34.7s (27%) ✅
├─ 证据链采集: 36.1s (28%) ✅
├─ 根因分析: 22.8s (18%) ✅
├─ 汇总总结: 33.7s (26%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 23 次
```

📋 诊断追踪

- **核心 Runbook**: l4-config-bootstrap-fail
- **参考 Runbook**: l4-config-bootstrap-fail
- **工具调用**: 23 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
