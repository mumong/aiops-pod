======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 33a3b90b0e1a4f99]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，我先做轻量状态确认，查看集群的整体健康情况。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   209d   v1.26.8  
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS             RESTARTS        AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     a
   💭 [问题定位] 好的，集群概况很清晰了。让我进一步查看这个异常 Pod 的详情。

发现一个异常 Pod：`appconfigfail-7649c79dc5-q4zjz` 在 `aiops-e2e` 命名空间中，状态为 `CrashLoopBackOff`。让我进一步查看详情。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             appconfigfail-7649c79dc5-q4zjz
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Wed, 22 Apr 2026 07:38:39
   💭 [问题定位] 这个 Pod 有明显的标签 `l4-scenario=config-bootstrap-fail`，而且日志中明确输出 "FATAL: missing required APP_BOOT_MODE" 并以 exit code 42 退出。让我查看相关 runbook 确认。
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
   💭 [问题定位] 现在让我获取上一次崩溃的日志来进一步确认。
   💭 [问题定位] 调用工具: run_bash_command
   💭 [问题定位] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_LAYER_APPLICATION: true\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: appl
   💭 [问题定位] 现在数据足够了。让我再快速看一下节点条件确认整体健康。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:               node1
Roles:              <none>
Labels:             beta.kubernetes.io/arch=amd64
                    beta.kubernetes.io/os=linux
                    kubernetes.io/arch=amd64
    
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
   💭 [问题定位] 所有节点均 Ready，无 DiskPressure/MemoryPressure/PIDPressure，无 Taint。现在可以给出完整的诊断结论了。

```json
{
  "layer": "L4",
  "layers": ["L4"],
  "layer_name": "应用层",
  "confidence": 0.98,
  "reasoning": "集群整体健康：3个节点均 Ready、无 Taint、无 DiskPressure/MemoryPressure。唯一异常 Pod 为 aiops-e2e/appconfigfail-7649c79dc5-q4zjz，状态 CrashLoopBackOff，Exit Code=42（业务退出码，非137），容器日志明确输出 'L4_CONFIG_BOOTSTRAP_FAIL'、'FATAL: missing required APP_BOOT_MODE'、'business config validation failed before server startup'。Pod 标签也显式标注 l4-scenario=config-bootstrap-fail。无 OOMKilled/Evicted/ImagePullBackOff 信号。符合 L4 应用启动配置校验失败场景。",
  "key_entities": [
    {"type": "Pod", "value": "appconfigfail-7649c79dc5-q4zjz"},
    {"type": "Namespace", "value": "aiops-e2e"},
    {"type": "Node", "value": "node2"}
  ],
  "possible_scenarios": [
    "应用启动配置校验失败 — 容器启动脚本检测到环境变量 APP_BOOT_MODE 缺失，主动以 exit code 42 退出，属于业务层配置错误"
  ]
}
```
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (10m 28.9s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=['应用启动配置校验失败 — 容器启动脚本检测到环境变量 APP_BOOT_MODE 缺失，主动以 exit code 42 退出，属于业务层配置错误']
   entities=[{"type": "Pod", "value": "appconfigfail-7649c79dc5-q4zjz"}, {"type": "Namespace", "value": "aiops-e2e"}, {"type": "Node", "value": "node2"}]
   reasoning=集群整体健康：3个节点均 Ready、无 Taint、无 DiskPressure/MemoryPressure。唯一异常 Pod 为 aiops-e2e/appconfigfail-7649c79dc5-q4zjz，状态 CrashLoopBackOff，Exit Code=42（业务退出码，非137），容器日志明确输出 'L4_CONFIG_BOOTSTRAP_FAIL'、'FATAL: missing required APP_BOOT_MODE'、'business config validation failed before server startup'。Pod 标签也显式标注 l4-scenario=config-bootstrap-fail。无 OOMKilled/Evicted/ImagePullBackOff 信号。符合 L4 应用启动配置校验失败场景。
   layer_analysis={"layer": "L4", "layers": ["L4"], "layer_name": "应用层", "confidence": 0.98, "reasoning": "集群整体健康：3个节点均 Ready、无 Taint、无 DiskPressure/MemoryPressure。唯一异常 Pod 为 aiops-e2e/appconfigfail-7649c79dc5-q4zjz，状态 CrashLoopBackOff，Exit Code=42（业务退出码，非137），容器日志明确输出 'L4_CONFIG_BOOTSTRAP_FAIL'、'FATAL: missing required APP_BOOT_MODE'、'business config validation failed before server startup'。Pod 标签也显式标注 l4-scenario=config-bootstrap-fail。无 OOMKilled/Evicted/ImagePullBackOff 信号。符合 L4 应用启动配置校验失败场景。", "key_entities": [{"type": "Pod", "value": "appconfigfail-7649c79dc5-q4zjz"}, {"type": "Namespace", "value": "aiops-e2e"}, {"type": "Node", "value": "node2"}], "possible_scenarios": ["应用启动配置校验失败 — 容器启动脚本检测到环境变量 APP_BOOT_MODE 缺失，主动以 exit code 42 退出，属于业务层配置错误"]}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 98%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我先快速查看集群的整体状态，然后根据发现的问题进行深入采集。
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS             RESTARTS        AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     a
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   209d   v1.26.8  
   💭 [证据链采集] 发现一个异常 Pod。让我进一步查看详情。
   💭 [证据链采集] 调用工具: TodoWrite
   💭 [证据链采集] 工具结果: TodoWrite (success)
      📄 Investigation plan updated with 5 tasks.

# CURRENT INVESTIGATION TASKS

**Task Status**: 0 completed, 1 in progress, 4 pending

[ ] [t2] 查看异常 Pod 的容器日志
[ ] [t3] 查看异常 Pod 的 Deployment/Controller 配置
[ 
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:             appconfigfail-7649c79dc5-q4zjz
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Wed, 22 Apr 2026 07:38:39
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 LAST SEEN               TYPE      REASON           OBJECT                               MESSAGE
28m                     Normal    Scheduled        Pod/appconfigfail-7649c79dc5-q4zjz   Successfully ass
   💭 [证据链采集] 调用工具: TodoWrite
   💭 [证据链采集] 工具结果: TodoWrite (success)
      📄 Investigation plan updated with 5 tasks.

# CURRENT INVESTIGATION TASKS

**Task Status**: 1 completed, 1 in progress, 3 pending

[ ] [t3] 查看异常 Pod 的 Deployment/Controller 配置
[ ] [t4] 检查节点 node2 的健康状况

   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 NAME            READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES         SELECTOR            LABELS
appconfigfail   0/1     1            0           28m   app          busybox:1.36   app=app
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 NAME                             READY   STATUS             RESTARTS         AGE   IP              NODE    NOMINATED NODE   READINESS GATES   LABELS
appconfigfail-7649c79dc5-q4zjz   0/1     CrashLoopB
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME            READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES         SELECTOR            LABELS
appconfigfail   0/1     1            0           28m   app          busybox:1.36   app=app
   💭 [证据链采集] 现在检查节点和集群整体健康状态。
   💭 [证据链采集] 调用工具: TodoWrite
   💭 [证据链采集] 工具结果: TodoWrite (success)
      📄 Investigation plan updated with 5 tasks.

# CURRENT INVESTIGATION TASKS

**Task Status**: 3 completed, 1 in progress, 1 pending

[ ] [t5] 检查集群整体资源使用情况
[~] [t4] 检查节点 node2 的健康状况
[✓] [t1] 查看异常 Pod appco
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:               node2
Roles:              <none>
Labels:             beta.kubernetes.io/arch=amd64
                    beta.kubernetes.io/os=linux
                    kubernetes.io/arch=amd64
    
   💭 [证据链采集] 节点 node2 完全健康。现在检查集群整体资源使用情况。
   💭 [证据链采集] 调用工具: TodoWrite
   💭 [证据链采集] 工具结果: TodoWrite (success)
      📄 Investigation plan updated with 5 tasks.

# CURRENT INVESTIGATION TASKS

**Task Status**: 4 completed, 1 in progress, 0 pending

[~] [t5] 检查集群整体资源使用情况
[✓] [t1] 查看异常 Pod appconfigfail 的详细描述和事件
[✓] [t2]
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:               node1
Roles:              <none>
Labels:             beta.kubernetes.io/arch=amd64
                    beta.kubernetes.io/os=linux
                    kubernetes.io/arch=amd64
    
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:               master
Roles:              control-plane
Labels:             beta.kubernetes.io/arch=amd64
                    beta.kubernetes.io/os=linux
                    kubernetes.io/arch=am
   💭 [证据链采集] 调用工具: TodoWrite
   💭 [证据链采集] 工具结果: TodoWrite (success)
      📄 Investigation plan updated with 5 tasks.

# CURRENT INVESTIGATION TASKS

**Task Status**: 5 completed, 0 in progress, 0 pending

[✓] [t1] 查看异常 Pod appconfigfail 的详细描述和事件
[✓] [t2] 查看异常 Pod 的容器日志
[✓] [t
   💭 [证据链采集] ## 集群健康检查报告

### 📊 整体概况

| 项目 | 状态 |
|------|------|
| **集群节点** | 3/3 Ready（master, node1, node2） |
| **所有 Pod** | 大部分 Running，**1 个异常** |
| **集群版本** | v1.26.8 |
| **容器运行时** | containerd 1.6.32 |
| **网络** | Calico 正常 |

---

### ❌ 唯一异常：Pod `appconfigfail-7649c79dc5-q4zjz`

| 字段 | 值 |
|------|-----|
| **命名空间** | `aiops-e2e` |
| **节点** | node2 (10.2.0.50) |
| **状态** | `CrashLoopBackOff` |
| **重启次数** | 10 次 |
| **退出码** | **42**（业务自定义退出码） |
| **镜像** | `busybox:1.36` |

#### 根本原因分析

该 Pod 的启动命令是一个 shell 脚本，其中检查了 `APP_BOOT_MODE` 环境变量：

```
if [ -z "${APP_BOOT_MODE:-}" ]; then
    echo "FATAL: missing required APP_BOOT_MODE"
    echo "FATAL: business config validation failed before server startup"
    exit 42
fi
```

**容器日志输出**：
- `L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config`
- `FATAL: missing required APP_BOOT_MODE`
- `FATAL: business config validation failed before server startup`

**Pod 配置中没有任何环境变量设置**（`Environment: <none>`），所以 `APP_BOOT_MODE` 始终为空，导致每次启动都立即以 exit code 42 退出。

---

### ✅ 集群健康状态（其他方面）

| 检查项 | 结果 |
|--------|------|
| **所有 3 个节点** | ✅ Ready，无 Taint |
| **节点资源** | ✅ CPU/内存/磁盘/PID 均正常（无压力） |
| **系统组件** | ✅ etcd, kube-apiserver, kube-controller-manager, kube-scheduler, coredns, calico, kube-proxy 均正常 |
| **网络** | ✅ Calico 正常运行，Pod 网络连通 |
| **镜像拉取** | ✅ `busybox:1.36` 已存在于节点本地 |

---

### 📋 总结

集群整体健康，**只有一个问题 Pod**：`appconfigfail`（位于 `aiops-e2e` 命名空间）。该问题属于 **L4 业务层配置错误** — Deployment 未设置 `APP_BOOT_MODE` 环境变量，导致容器启动脚本检测到该变量缺失后主动以 exit code 42 退出，进入 `CrashLoopBackOff`。

**建议修复**：在 Deployment 的 Pod template 中为容器添加环境变量 `APP_BOOT_MODE`，例如：
```yaml
env:
  - name: APP_BOOT_MODE
    value: "production"
```
   ✅ [证据链采集] 完成 (1m 10.7s)
   📤 → 下游数据: evidence_items=10/10
   evidence_analysis={"evidence_plan": [], "tool_results": [], "tool_data": [{"tool": "kubectl_get_by_kind_in_cluster", "data": "NAMESPACE     NAME                                                READY   STATUS             RESTARTS        AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\naiops-e2e     appconfigfail-7649c79dc5-q4zjz                      0/1     CrashLoopBackOff   10 (100s ago)   28m     172.16.104.57    node2    <none>           <none>            app=appconfigfail,l4-scenario=config-bootstrap-fail,pod-template-hash=7649c79dc5\naiops         aiops-copilot-76779bb6df-4bcrf                      1/1     Running            0               6h28m   172.16.104.29    node2    <none>           <none>            app=aiops-copilot,pod-template-hash=76779bb6df\ndefault       dns-test-existing                                   1/1     Running            0               2d2h    172.16.166.148   node1    <none>           <none>            run=dns-test-existing\ndefault       exec-test                                           1/1     Running            0               2d4h    172.16.104.8     node2    <none>           <none>            run=exec-test\ndefault       network-test-from-running                           1/1     Running            0               2d2h    172.16.104.50    node2    <none>           <none>            run=network-test-from-running\ndefault       nfs-client-provisioner-6fcd4994c9-lczf6             1/1     Running            4 (5d1h ago)    86d     172.16.104.41    node2    <none>           <none>            app=nfs-client-provisioner,pod-template-hash=6fcd4994c9\nkube-system   calico-kube-controllers-6c67f9d475-2xcb7            1/1     Running            4 (5d1h ago)    28d     172.16.166.133   node1    <none>           <none>            k8s-app=calico-kube-controllers,pod-template-hash=6c67f9d475\nkube-system   calico-node-4kp26                                   1/1     Running            12 (5d1h ago)   183d    10.2.0.48        master   <none>           <none>            controller-revision-hash=65f554db6,k8s-app=calico-node,pod-template-generation=1\nkube-system   calico-node-d2dhp                                   1/1     Running            13 (5d1h ago)   183d    10.2.0.50        node2    <none>           <none>            controller-revision-hash=65f554db6,k8s-app=calico-node,pod-template-generation=1\nkube-system   calico-node-mnrjs                                   1/1     Running            12 (5d1h ago)   183d    10.2.0.49        node1    <none>           <none>            controller-revision-hash=65f554db6,k8s-app=calico-node,pod-template-generation=1\nkube-system   coredns-777df594b8-j4857                            1/1     Running            4 (5d1h ago)    28d     172.16.166.129   node1    <none>           <none>            k8s-app=kube-dns,pod-template-hash=777df594b8\nkube-system   coredns-777df594b8-s8r4n                            1/1     Running            4 (5d1h ago)    28d     172.16.166.185   node1    <none>           <none>            k8s-app=kube-dns,pod-template-hash=777df594b8\nkube-system   etcd-master                                         1/1     Running            13 (5d1h ago)   209d    10.2.0.48        master   <none>           <none>            component=etcd,tier=control-plane\nkube-system   kube-apiserver-master                               1/1     Running            13 (5d1h ago)   209d    10.2.0.48        master   <none>           <none>            component=kube-apiserver,tier=control-plane\nkube-system   kube-controller-manager-master                      1/1     Running            36 (5d1h ago)   209d    10.2.0.48        master   <none>           <none>            component=kube-controller-manager,tier=control-plane\nkube-system   kube-multus-ds-rnvbg                                1/1     Running            12 (5d1h ago)   183d    10.2.0.49        node1    <none>           <none>            app=multus,controller-revision-hash=6d4c8546fc,name=multus,pod-template-generation=1,tier=node\nkube-system   kube-multus-ds-sc2jn                                1/1     Running            4 (5d1h ago)    86d     10.2.0.48        master   <none>           <none>            app=multus,controller-revision-hash=6d4c8546fc,name=multus,pod-template-generation=1,tier=node\nkube-system   kube-multus-ds-x7h9s                                1/1     Running            13 (5d1h ago)   183d    10.2.0.50        node2    <none>           <none>            app=multus,controller-revision-hash=6d4c8546fc,name=multus,pod-template-generation=1,tier=node\nkube-system   kube-proxy-69zzr                                    1/1     Running            4 (5d1h ago)    28d     10.2.0.50        node2    <none>           <none>            controller-revision-hash=7d99996759,k8s-app=kube-proxy,pod-template-generation=1\nkube-system   kube-proxy-bblvc                                    1/1     Running            4 (5d1h ago)    28d     10.2.0.49        node1    <none>           <none>            controller-revision-hash=7d99996759,k8s-app=kube-proxy,pod-template-generation=1\nkube-system   kube-proxy-wbh4k                                    1/1     Running            4 (5d1h ago)    27d     10.2.0.48        master   <none>           <none>            controller-revision-hash=7d99996759,k8s-app=kube-proxy,pod-template-generation=1\nkube-system   kube-scheduler-master                               1/1     Running            38 (5d1h ago)   209d    10.2.0.48        master   <none>           <none>            component=kube-scheduler,tier=control-plane\nmcp           mcp-server-manager-8677f6896c-d4mr9                 1/1     Running            0               46h     172.16.104.59    node2    <none>           <none>            app=mcp-server-manager,pod-template-hash=8677f6896c\nxnet          alertmanager-observability-alertmanager-0           2/2     Running            8 (5d1h ago)    23d     172.16.166.161   node1    <none>           <none>            alertmanager=observability-alertmanager,app.kubernetes.io/instance=observability-alertmanager,app.kubernetes.io/managed-by=prometheus-operator,app.kubernetes.io/name=alertmanager,app.kubernetes.io/version=0.28.1,controller-revision-hash=alertmanager-observability-alertmanager-6c9cfbf844,statefulset.kubernetes.io/pod-name=alertmanager-observability-alertmanager-0\nxnet          api-server-6bd6bf8d6f-27svp                         1/1     Running            4 (5d1h ago)    23d     172.16.219.106   master   <none>           <none>            app=api-server,pod-template-hash=6bd6bf8d6f\nxnet          deepflow-agent-pcknn                                1/1     Running            9 (5d1h ago)    23d     172.16.166.181   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow-agent,app=deepflow,component=deepflow-agent,controller-revision-hash=54856d959b,pod-template-generation=1\nxnet          deepflow-agent-trc8k                                1/1     Running            7 (5d1h ago)    19d     172.16.104.7     node2    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow-agent,app=deepflow,component=deepflow-agent,controller-revision-hash=54856d959b,pod-template-generation=1\nxnet          deepflow-agent-whn22                                1/1     Running            8 (5d1h ago)    23d     172.16.219.97    master   <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow-agent,app=deepflow,component=deepflow-agent,controller-revision-hash=54856d959b,pod-template-generation=1\nxnet          elasticsearch-master-0                              1/1     Running            4 (5d1h ago)    23d     172.16.219.109   master   <none>           <none>            app=elasticsearch-master,chart=observability,controller-revision-hash=elasticsearch-master-695ff9864f,release=observability,statefulset.kubernetes.io/pod-name=elasticsearch-master-0\nxnet          ham-p9dxv                                           1/1     Running            14 (5d1h ago)   177d    172.16.104.21    node2    <none>           <none>            app=ham,controller-revision-hash=f65f887d,pod-template-generation=1\nxnet          ham-qzjg5                                           1/1     Running            4 (5d1h ago)    85d     172.16.219.112   master   <none>           <none>            app=ham,controller-revision-hash=f65f887d,pod-template-generation=1\nxnet          ham-wt9kh                                           1/1     Running            13 (5d1h ago)   177d    172.16.166.187   node1    <none>           <none>            app=ham,controller-revision-hash=f65f887d,pod-template-generation=1\nxnet          lgtm-5dc5c67d5f-sc286                               1/1     Running            4 (5d1h ago)    23d     172.16.166.151   node1    <none>           <none>            app=lgtm,pod-template-hash=5dc5c67d5f\nxnet          observability-clickhouse-0                          1/1     Running            4 (5d1h ago)    23d     172.16.166.137   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=clickhouse,app=deepflow,component=clickhouse,controller-revision-hash=observability-clickhouse-75b8d58ccc,statefulset.kubernetes.io/pod-name=observability-clickhouse-0\nxnet          observability-deepflow-app-654fcfbfbf-q8st6         1/1     Running            4 (5d1h ago)    23d     172.16.166.160   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow,app=deepflow,component=deepflow-app,pod-template-hash=654fcfbfbf\nxnet          observability-deepflow-server-774dd6c5b7-9c998      1/1     Running            14 (5d1h ago)   23d     172.16.166.135   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow,app=deepflow,component=deepflow-server,pod-template-hash=774dd6c5b7\nxnet          observability-filebeat-ffwsp                        1/1     Running            4 (5d1h ago)    23d     172.16.219.80    master   <none>           <none>            app=observability-filebeat,chart=observability-1.0.2,controller-revision-hash=57fb88b7c5,heritage=Helm,pod-template-generation=1,release=observability\nxnet          observability-filebeat-m58xw                        1/1     Running            5 (5d1h ago)    23d     172.16.166.134   node1    <none>           <none>            app=observability-filebeat,chart=observability-1.0.2,controller-revision-hash=57fb88b7c5,heritage=Helm,pod-template-generation=1,release=observability\nxnet          observability-filebeat-w6gtr                        1/1     Running            5 (5d1h ago)    19d     172.16.104.53    node2    <none>           <none>            app=observability-filebeat,chart=observability-1.0.2,controller-revision-hash=57fb88b7c5,heritage=Helm,pod-template-generation=1,release=observability\nxnet          observability-grafana-58bf9cfd6f-ndsxr              4/4     Running            36 (5d ago)     23d     172.16.166.144   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=grafana,app.kubernetes.io/version=12.0.2,helm.sh/chart=grafana-9.2.7,pod-template-hash=58bf9cfd6f\nxnet          observability-kepler-2sgrr                          1/1     Running            6 (5d1h ago)    23d     10.2.0.49        node1    <none>           <none>            app.kubernetes.io/component=exporter,app.kubernetes.io/name=kepler-kepler,controller-revision-hash=7c6c5f9bd6,pod-template-generation=1\nxnet          observability-kepler-7scjm                          1/1     Running            7 (5d1h ago)    23d     10.2.0.48        master   <none>           <none>            app.kubernetes.io/component=exporter,app.kubernetes.io/name=kepler-kepler,controller-revision-hash=7c6c5f9bd6,pod-template-generation=1\nxnet          observability-kepler-ggstf                          1/1     Running            8 (5d1h ago)    19d     10.2.0.50        node2    <none>           <none>            app.kubernetes.io/component=exporter,app.kubernetes.io/name=kepler-kepler,controller-revision-hash=7c6c5f9bd6,pod-template-generation=1\nxnet          observability-kibana-65d7c45f6d-tm4vv               1/1     Running            4 (5d1h ago)    23d     172.16.166.191   node1    <none>           <none>            app=observability-kibana,pod-template-hash=65d7c45f6d,release=observability\nxnet          observability-kube-state-metrics-798986b8b7-6z2dq   1/1     Running            4 (5d1h ago)    23d     172.16.219.65    master   <none>           <none>            app.kubernetes.io/component=metrics,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=kube-state-metrics,app.kubernetes.io/part-of=kube-state-metrics,app.kubernetes.io/version=2.15.0,helm.sh/chart=kube-state-metrics-5.37.0,pod-template-hash=798986b8b7,release=observability\nxnet          observability-mysql-764f9d5966-wh2bc                1/1     Running            4 (5d1h ago)    23d     172.16.219.98    master   <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=mysql,app=deepflow,component=mysql,pod-template-hash=764f9d5966\nxnet          observability-operator-d4495dc86-69lgw              1/1     Running            4 (5d1h ago)    23d     172.16.166.182   node1    <none>           <none>            app.kubernetes.io/component=prometheus-operator,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=observability-prometheus-operator,app.kubernetes.io/part-of=observability,app.kubernetes.io/version=1.0.2,app=observability-operator,chart=observability-1.0.2,heritage=Helm,pod-template-hash=d4495dc86,release=observability\nxnet          observability-prometheus-node-exporter-lj75r        1/1     Running            4 (5d1h ago)    23d     10.2.0.48        master   <none>           <none>            app.kubernetes.io/component=metrics,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=prometheus-node-exporter,app.kubernetes.io/part-of=prometheus-node-exporter,app.kubernetes.io/version=1.9.1,controller-revision-hash=74f4f4b87d,helm.sh/chart=prometheus-node-exporter-4.47.0,jobLabel=node-exporter,pod-template-generation=1,release=observability\nxnet          observability-prometheus-node-exporter-qp2qd        1/1     Running            4 (5d1h ago)    19d     10.2.0.50        node2    <none>           <none>            app.kubernetes.io/component=metrics,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=prometheus-node-exporter,app.kubernetes.io/part-of=prometheus-node-exporter,app.kubernetes.io/version=1.9.1,controller-revision-hash=74f4f4b87d,helm.sh/chart=prometheus-node-exporter-4.47.0,jobLabel=node-exporter,pod-template-generation=1,release=observability\nxnet          observability-prometheus-node-exporter-wnbb8        1/1     Running            4 (5d1h ago)    23d     10.2.0.49        node1    <none>           <none>            app.kubernetes.io/component=metrics,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=prometheus-node-exporter,app.kubernetes.io/part-of=prometheus-node-exporter,app.kubernetes.io/version=1.9.1,controller-revision-hash=74f4f4b87d,helm.sh/chart=prometheus-node-exporter-4.47.0,jobLabel=node-exporter,pod-template-generation=1,release=observability\nxnet          observability-telegraf-79f45d86-4kzkm               1/1     Running            4 (5d1h ago)    23d     172.16.219.113   master   <none>           <none>            app.kubernetes.io/component=telegraf,app.kubernetes.io/instance=observability,app.kubernetes.io/name=observability,pod-template-hash=79f45d86\nxnet          prometheus-observability-prometheus-0               2/2     Running            16 (5d1h ago)   23d     172.16.166.142   node1    <none>           <none>            app.kubernetes.io/instance=observability-prometheus,app.kubernetes.io/managed-by=prometheus-operator,app.kubernetes.io/name=prometheus,app.kubernetes.io/version=3.4.1,controller-revision-hash=prometheus-observability-prometheus-9467b46f7,operator.prometheus.io/name=observability-prometheus,operator.prometheus.io/shard=0,prometheus=observability-prometheus,statefulset.kubernetes.io/pod-name=prometheus-observability-prometheus-0\nxnet          xnet-agent-568f547566-jdsgp                         1/1     Running            4 (5d1h ago)    108d    172.16.104.40    node2    <none>           <none>            app=xnet-agent,pod-template-hash=568f547566", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_cluster", "data": "NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nmaster   Ready    control-plane   209d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          209d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-174-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          209d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-174-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux", "duration_s": 0}, {"tool": "TodoWrite", "data": "Investigation plan updated with 5 tasks.\n\n# CURRENT INVESTIGATION TASKS\n\n**Task Status**: 0 completed, 1 in progress, 4 pending\n\n[ ] [t2] 查看异常 Pod 的容器日志\n[ ] [t3] 查看异常 Pod 的 Deployment/Controller 配置\n[ ] [t4] 检查节点 node2 的健康状况\n[ ] [t5] 检查集群整体资源使用情况\n[~] [t1] 查看异常 Pod appconfigfail 的详细描述和事件\n\n**Instructions**: Use TodoWrite tool to update task status as you work.", "duration_s": 0}, {"tool": "kubectl_describe", "data": "Name:             appconfigfail-7649c79dc5-q4zjz\nNamespace:        aiops-e2e\nPriority:         0\nService Account:  default\nNode:             node2/10.2.0.50\nStart Time:       Wed, 22 Apr 2026 07:38:39 +0000\nLabels:           app=appconfigfail\n                  l4-scenario=config-bootstrap-fail\n                  pod-template-hash=7649c79dc5\nAnnotations:      cni.projectcalico.org/containerID: c6399f913454284036a261148882084711e3bf6f9788cf1df749c56fbda41b6f\n                  cni.projectcalico.org/podIP: 172.16.104.57/32\n                  cni.projectcalico.org/podIPs: 172.16.104.57/32\n                  k8s.v1.cni.cncf.io/network-status:\n                    [{\n                        \"name\": \"k8s-pod-network\",\n                        \"ips\": [\n                            \"172.16.104.57\"\n                        ],\n                        \"default\": true,\n                        \"dns\": {}\n                    }]\n                  k8s.v1.cni.cncf.io/networks-status:\n                    [{\n                        \"name\": \"k8s-pod-network\",\n                        \"ips\": [\n                            \"172.16.104.57\"\n                        ],\n                        \"default\": true,\n                        \"dns\": {}\n                    }]\nStatus:           Running\nIP:               172.16.104.57\nIPs:\n  IP:           172.16.104.57\nControlled By:  ReplicaSet/appconfigfail-7649c79dc5\nContainers:\n  app:\n    Container ID:  containerd://b1aec2c351c9393961cd4305f15772302656a22fa514788eb3f1f92428e9e1e9\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Port:          <none>\n    Host Port:     <none>\n    Command:\n      sh\n      -c\n    Args:\n      echo \"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\"\n      echo \"L4_LAYER_APPLICATION: true\"\n      echo \"L4_SCENARIO: config-bootstrap-fail\"\n      echo \"L4_ERROR_TYPE: application-config-validation\"\n      if [ -z \"${APP_BOOT_MODE:-}\" ]; then\n        echo \"FATAL: missing required APP_BOOT_MODE\"\n        echo \"FATAL: business config validation failed before server startup\"\n        exit 42\n      fi\n      echo \"unexpected success\"\n      exit 1\n      \n    State:          Waiting\n      Reason:       CrashLoopBackOff\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42\n      Started:      Wed, 22 Apr 2026 08:04:59 +0000\n      Finished:     Wed, 22 Apr 2026 08:04:59 +0000\n    Ready:          False\n    Restart Count:  10\n    Environment:    <none>\n    Mounts:\n      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-zndsj (ro)\nConditions:\n  Type              Status\n  Initialized       True \n  Ready             False \n  ContainersReady   False \n  PodScheduled      True \nVolumes:\n  kube-api-access-zndsj:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    TokenExpirationSeconds:  3607\n    ConfigMapName:           kube-root-ca.crt\n    ConfigMapOptional:       <nil>\n    DownwardAPI:             true\nQoS Class:                   BestEffort\nNode-Selectors:              <none>\nTolerations:                 node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\n                             node.kubernetes.io/unreachable:NoExecute op=Exists for 300s\nEvents:\n  Type     Reason          Age                    From               Message\n  ----     ------          ----                   ----               -------\n  Normal   Scheduled       28m                    default-scheduler  Successfully assigned aiops-e2e/appconfigfail-7649c79dc5-q4zjz to node2\n  Normal   AddedInterface  28m                    multus             Add eth0 [172.16.104.57/32] from k8s-pod-network\n  Normal   Pulled          26m (x5 over 28m)      kubelet            Container image \"busybox:1.36\" already present on machine\n  Normal   Created         26m (x5 over 28m)      kubelet            Created container app\n  Normal   Started         26m (x5 over 28m)      kubelet            Started container app\n  Warning  BackOff         3m13s (x116 over 28m)  kubelet            Back-off restarting failed container app in pod appconfigfail-7649c79dc5-q4zjz_aiops-e2e(77ea5d65-2a07-47e0-b606-3f03812dcc6a)", "duration_s": 0}, {"tool": "kubectl_events", "data": "LAST SEEN               TYPE      REASON           OBJECT                               MESSAGE\n28m                     Normal    Scheduled        Pod/appconfigfail-7649c79dc5-q4zjz   Successfully assigned aiops-e2e/appconfigfail-7649c79dc5-q4zjz to node2\n28m                     Normal    AddedInterface   Pod/appconfigfail-7649c79dc5-q4zjz   Add eth0 [172.16.104.57/32] from k8s-pod-network\n26m (x5 over 28m)       Normal    Pulled           Pod/appconfigfail-7649c79dc5-q4zjz   Container image \"busybox:1.36\" already present on machine\n26m (x5 over 28m)       Normal    Created          Pod/appconfigfail-7649c79dc5-q4zjz   Created container app\n26m (x5 over 28m)       Normal    Started          Pod/appconfigfail-7649c79dc5-q4zjz   Started container app\n3m13s (x116 over 28m)   Warning   BackOff          Pod/appconfigfail-7649c79dc5-q4zjz   Back-off restarting failed container app in pod appconfigfail-7649c79dc5-q4zjz_aiops-e2e(77ea5d65-2a07-47e0-b606-3f03812dcc6a)", "duration_s": 0}, {"tool": "TodoWrite", "data": "Investigation plan updated with 5 tasks.\n\n# CURRENT INVESTIGATION TASKS\n\n**Task Status**: 1 completed, 1 in progress, 3 pending\n\n[ ] [t3] 查看异常 Pod 的 Deployment/Controller 配置\n[ ] [t4] 检查节点 node2 的健康状况\n[ ] [t5] 检查集群整体资源使用情况\n[~] [t2] 查看异常 Pod 的容器日志\n[✓] [t1] 查看异常 Pod appconfigfail 的详细描述和事件\n\n**Instructions**: Use TodoWrite tool to update task status as you work.", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_namespace", "data": "NAME            READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES         SELECTOR            LABELS\nappconfigfail   0/1     1            0           28m   app          busybox:1.36   app=appconfigfail   l4-scenario=config-bootstrap-fail", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_namespace", "data": "NAME                             READY   STATUS             RESTARTS         AGE   IP              NODE    NOMINATED NODE   READINESS GATES   LABELS\nappconfigfail-7649c79dc5-q4zjz   0/1     CrashLoopBackOff   10 (2m10s ago)   28m   172.16.104.57   node2   <none>           <none>            app=appconfigfail,l4-scenario=config-bootstrap-fail,pod-template-hash=7649c79dc5", "duration_s": 0}, {"tool": "kubectl_get_by_name", "data": "NAME            READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES         SELECTOR            LABELS\nappconfigfail   0/1     1            0           28m   app          busybox:1.36   app=appconfigfail   l4-scenario=config-bootstrap-fail", "duration_s": 0}, {"tool": "TodoWrite", "data": "Investigation plan updated with 5 tasks.\n\n# CURRENT INVESTIGATION TASKS\n\n**Task Status**: 3 completed, 1 in progress, 1 pending\n\n[ ] [t5] 检查集群整体资源使用情况\n[~] [t4] 检查节点 node2 的健康状况\n[✓] [t1] 查看异常 Pod appconfigfail 的详细描述和事件\n[✓] [t2] 查看异常 Pod 的容器日志\n[✓] [t3] 查看异常 Pod 的 Deployment/Controller 配置\n\n**Instructions**: Use TodoWrite tool to update task status as you work.", "duration_s": 0}, {"tool": "kubectl_describe", "data": "Name:               node2\nRoles:              <none>\nLabels:             beta.kubernetes.io/arch=amd64\n                    beta.kubernetes.io/os=linux\n                    kubernetes.io/arch=amd64\n                    kubernetes.io/hostname=node2\n                    kubernetes.io/os=linux\nAnnotations:        kubeadm.alpha.kubernetes.io/cri-socket: unix:///var/run/containerd/containerd.sock\n                    node.alpha.kubernetes.io/ttl: 0\n                    projectcalico.org/IPv4Address: 10.2.0.50/19\n                    projectcalico.org/IPv4IPIPTunnelAddr: 172.16.104.0\n                    volumes.kubernetes.io/controller-managed-attach-detach: true\nCreationTimestamp:  Thu, 25 Sep 2025 03:10:26 +0000\nTaints:             <none>\nUnschedulable:      false\nLease:\n  HolderIdentity:  node2\n  AcquireTime:     <unset>\n  RenewTime:       Wed, 22 Apr 2026 08:07:14 +0000\nConditions:\n  Type                 Status  LastHeartbeatTime                 LastTransitionTime                Reason                       Message\n  ----                 ------  -----------------                 ------------------                ------                       -------\n  NetworkUnavailable   False   Fri, 17 Apr 2026 07:03:52 +0000   Fri, 17 Apr 2026 07:03:52 +0000   CalicoIsUp                   Calico is running on this node\n  MemoryPressure       False   Wed, 22 Apr 2026 08:03:29 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletHasSufficientMemory   kubelet has sufficient memory available\n  DiskPressure         False   Wed, 22 Apr 2026 08:03:29 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletHasNoDiskPressure     kubelet has no disk pressure\n  PIDPressure          False   Wed, 22 Apr 2026 08:03:29 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletHasSufficientPID      kubelet has sufficient PID available\n  Ready                True    Wed, 22 Apr 2026 08:03:29 +0000   Thu, 16 Apr 2026 02:25:06 +0000   KubeletReady                 kubelet is posting ready status. AppArmor enabled\nAddresses:\n  InternalIP:  10.2.0.50\n  Hostname:    node2\nCapacity:\n  cpu:                12\n  ephemeral-storage:  203770680Ki\n  hugepages-1Gi:      0\n  hugepages-2Mi:      0\n  memory:             32860484Ki\n  pods:               110\nAllocatable:\n  cpu:                12\n  ephemeral-storage:  187795058378\n  hugepages-1Gi:      0\n  hugepages-2Mi:      0\n  memory:             32758084Ki\n  pods:               110\nSystem Info:\n  Machine ID:                 6bb27862c82149418d0f5624411d0b22\n  System UUID:                0f5af30a-d385-493c-bc8b-5442fd024eee\n  Boot ID:                    0ea98079-ad10-4a20-85f5-19b34afd257e\n  Kernel Version:             5.15.0-174-generic\n  OS Image:                   Ubuntu 22.04.4 LTS\n  Operating System:           linux\n  Architecture:               amd64\n  Container Runtime Version:  containerd://1.6.32\n  Kubelet Version:            v1.26.8\n  Kube-Proxy Version:         v1.26.8\nNon-terminated Pods:          (15 in total)\n  Namespace                   Name                                            CPU Requests  CPU Limits  Memory Requests  Memory Limits  Age\n  ---------                   ----                                            ------------  ----------  ---------------  -------------  ---\n  aiops-e2e                   appconfigfail-7649c79dc5-q4zjz                  0 (0%)        0 (0%)      0 (0%)           0 (0%)         28m\n  aiops                       aiops-copilot-76779bb6df-4bcrf                  250m (2%)     1 (8%)      512Mi (1%)       2Gi (6%)       6h29m\n  default                     exec-test                                       0 (0%)        0 (0%)      0 (0%)           0 (0%)         2d4h\n  default                     network-test-from-running                       0 (0%)        0 (0%)      0 (0%)           0 (0%)         2d2h\n  default                     nfs-client-provisioner-6fcd4994c9-lczf6         0 (0%)        0 (0%)      0 (0%)           0 (0%)         86d\n  kube-system                 calico-node-d2dhp                               250m (2%)     0 (0%)      0 (0%)           0 (0%)         183d\n  kube-system                 kube-multus-ds-x7h9s                            100m (0%)     100m (0%)   50Mi (0%)        50Mi (0%)      183d\n  kube-system                 kube-proxy-69zzr                                0 (0%)        0 (0%)      0 (0%)           0 (0%)         28d\n  mcp                         mcp-server-manager-8677f6896c-d4mr9             200m (1%)     1 (8%)      1G (2%)          2560Mi (8%)    46h\n  xnet                        deepflow-agent-trc8k                            100m (0%)     1 (8%)      128Mi (0%)       768Mi (2%)     19d\n  xnet                        ham-p9dxv                                       0 (0%)        0 (0%)      0 (0%)           0 (0%)         177d\n  xnet                        observability-filebeat-w6gtr                    100m (0%)     1 (8%)      100Mi (0%)       200Mi (0%)     19d\n  xnet                        observability-kepler-ggstf                      0 (0%)        0 (0%)      0 (0%)           0 (0%)         19d\n  xnet                        observability-prometheus-node-exporter-qp2qd    0 (0%)        0 (0%)      0 (0%)           0 (0%)         19d\n  xnet                        xnet-agent-568f547566-jdsgp                     0 (0%)        0 (0%)      0 (0%)           0 (0%)         108d\nAllocated resources:\n  (Total limits may be over 100 percent, i.e., overcommitted.)\n  Resource           Requests         Limits\n  --------           --------         ------\n  cpu                1 (8%)           4100m (34%)\n  memory             1828375040 (5%)  5626Mi (17%)\n  ephemeral-storage  0 (0%)           0 (0%)\n  hugepages-1Gi      0 (0%)           0 (0%)\n  hugepages-2Mi      0 (0%)           0 (0%)\nEvents:              <none>", "duration_s": 0}, {"tool": "TodoWrite", "data": "Investigation plan updated with 5 tasks.\n\n# CURRENT INVESTIGATION TASKS\n\n**Task Status**: 4 completed, 1 in progress, 0 pending\n\n[~] [t5] 检查集群整体资源使用情况\n[✓] [t1] 查看异常 Pod appconfigfail 的详细描述和事件\n[✓] [t2] 查看异常 Pod 的容器日志\n[✓] [t3] 查看异常 Pod 的 Deployment/Controller 配置\n[✓] [t4] 检查节点 node2 的健康状况\n\n**Instructions**: Use TodoWrite tool to update task status as you work.", "duration_s": 0}, {"tool": "kubectl_describe", "data": "Name:               node1\nRoles:              <none>\nLabels:             beta.kubernetes.io/arch=amd64\n                    beta.kubernetes.io/os=linux\n                    kubernetes.io/arch=amd64\n                    kubernetes.io/hostname=node1\n                    kubernetes.io/os=linux\nAnnotations:        kubeadm.alpha.kubernetes.io/cri-socket: unix:///var/run/containerd/containerd.sock\n                    node.alpha.kubernetes.io/ttl: 0\n                    projectcalico.org/IPv4Address: 10.2.0.49/19\n                    projectcalico.org/IPv4IPIPTunnelAddr: 172.16.166.128\n                    volumes.kubernetes.io/controller-managed-attach-detach: true\nCreationTimestamp:  Thu, 25 Sep 2025 03:19:31 +0000\nTaints:             <none>\nUnschedulable:      false\nLease:\n  HolderIdentity:  node1\n  AcquireTime:     <unset>\n  RenewTime:       Wed, 22 Apr 2026 08:07:20 +0000\nConditions:\n  Type                 Status  LastHeartbeatTime                 LastTransitionTime                Reason                       Message\n  ----                 ------  -----------------                 ------------------                ------                       -------\n  NetworkUnavailable   False   Fri, 17 Apr 2026 07:04:20 +0000   Fri, 17 Apr 2026 07:04:20 +0000   CalicoIsUp                   Calico is running on this node\n  MemoryPressure       False   Wed, 22 Apr 2026 08:04:01 +0000   Thu, 16 Apr 2026 02:25:26 +0000   KubeletHasSufficientMemory   kubelet has sufficient memory available\n  DiskPressure         False   Wed, 22 Apr 2026 08:04:01 +0000   Thu, 16 Apr 2026 02:25:26 +0000   KubeletHasNoDiskPressure     kubelet has no disk pressure\n  PIDPressure          False   Wed, 22 Apr 2026 08:04:01 +0000   Thu, 16 Apr 2026 02:25:26 +0000   KubeletHasSufficientPID      kubelet has sufficient PID available\n  Ready                True    Wed, 22 Apr 2026 08:04:01 +0000   Thu, 16 Apr 2026 02:25:26 +0000   KubeletReady                 kubelet is posting ready status. AppArmor enabled\nAddresses:\n  InternalIP:  10.2.0.49\n  Hostname:    node1\nCapacity:\n  cpu:                12\n  ephemeral-storage:  203770680Ki\n  hugepages-1Gi:      0\n  hugepages-2Mi:      0\n  memory:             32860468Ki\n  pods:               110\nAllocatable:\n  cpu:                12\n  ephemeral-storage:  187795058378\n  hugepages-1Gi:      0\n  hugepages-2Mi:      0\n  memory:             32758068Ki\n  pods:               110\nSystem Info:\n  Machine ID:                 6bb27862c82149418d0f5624411d0b22\n  System UUID:                8a5d626f-7b8e-44a2-8db9-b44970c46669\n  Boot ID:                    88dded04-4dc6-446d-9d1f-5a88d3983062\n  Kernel Version:             5.15.0-174-generic\n  OS Image:                   Ubuntu 22.04.4 LTS\n  Operating System:           linux\n  Architecture:               amd64\n  Container Runtime Version:  containerd://1.6.32\n  Kubelet Version:            v1.26.8\n  Kube-Proxy Version:         v1.26.8\nNon-terminated Pods:          (21 in total)\n  Namespace                   Name                                              CPU Requests  CPU Limits  Memory Requests  Memory Limits  Age\n  ---------                   ----                                              ------------  ----------  ---------------  -------------  ---\n  default                     dns-test-existing                                 0 (0%)        0 (0%)      0 (0%)           0 (0%)         2d2h\n  kube-system                 calico-kube-controllers-6c67f9d475-2xcb7          0 (0%)        0 (0%)      0 (0%)           0 (0%)         28d\n  kube-system                 calico-node-mnrjs                                 250m (2%)     0 (0%)      0 (0%)           0 (0%)         183d\n  kube-system                 coredns-777df594b8-j4857                          100m (0%)     0 (0%)      70Mi (0%)        170Mi (0%)     28d\n  kube-system                 coredns-777df594b8-s8r4n                          100m (0%)     0 (0%)      70Mi (0%)        170Mi (0%)     28d\n  kube-system                 kube-multus-ds-rnvbg                              100m (0%)     100m (0%)   50Mi (0%)        50Mi (0%)      183d\n  kube-system                 kube-proxy-bblvc                                  0 (0%)        0 (0%)      0 (0%)           0 (0%)         28d\n  xnet                        alertmanager-observability-alertmanager-0         25m (0%)      50m (0%)    128Mi (0%)       256Mi (0%)     23d\n  xnet                        deepflow-agent-pcknn                              100m (0%)     1 (8%)      128Mi (0%)       768Mi (2%)     23d\n  xnet                        ham-wt9kh                                         0 (0%)        0 (0%)      0 (0%)           0 (0%)         177d\n  xnet                        lgtm-5dc5c67d5f-sc286                             0 (0%)        0 (0%)      0 (0%)           0 (0%)         23d\n  xnet                        observability-clickhouse-0                        0 (0%)        0 (0%)      0 (0%)           0 (0%)         23d\n  xnet                        observability-deepflow-app-654fcfbfbf-q8st6       0 (0%)        0 (0%)      0 (0%)           0 (0%)         23d\n  xnet                        observability-deepflow-server-774dd6c5b7-9c998    0 (0%)        0 (0%)      0 (0%)           0 (0%)         23d\n  xnet                        observability-filebeat-m58xw                      100m (0%)     1 (8%)      100Mi (0%)       200Mi (0%)     23d\n  xnet                        observability-grafana-58bf9cfd6f-ndsxr            0 (0%)        0 (0%)      0 (0%)           0 (0%)         23d\n  xnet                        observability-kepler-2sgrr                        0 (0%)        0 (0%)      0 (0%)           0 (0%)         23d\n  xnet                        observability-kibana-65d7c45f6d-tm4vv             1 (8%)        1 (8%)      2Gi (6%)         2Gi (6%)       23d\n  xnet                        observability-operator-d4495dc86-69lgw            0 (0%)        0 (0%)      0 (0%)           0 (0%)         23d\n  xnet                        observability-prometheus-node-exporter-wnbb8      0 (0%)        0 (0%)      0 (0%)           0 (0%)         23d\n  xnet                        prometheus-observability-prometheus-0             50m (0%)      100m (0%)   256Mi (0%)       512Mi (1%)     23d\nAllocated resources:\n  (Total limits may be over 100 percent, i.e., overcommitted.)\n  Resource           Requests     Limits\n  --------           --------     ------\n  cpu                1825m (15%)  3250m (27%)\n  memory             2850Mi (8%)  4174Mi (13%)\n  ephemeral-storage  0 (0%)       0 (0%)\n  hugepages-1Gi      0 (0%)       0 (0%)\n  hugepages-2Mi      0 (0%)       0 (0%)\nEvents:              <none>", "duration_s": 0}, {"tool": "kubectl_describe", "data": "Name:               master\nRoles:              control-plane\nLabels:             beta.kubernetes.io/arch=amd64\n                    beta.kubernetes.io/os=linux\n                    kubernetes.io/arch=amd64\n                    kubernetes.io/hostname=master\n                    kubernetes.io/os=linux\n                    node-role.kubernetes.io/control-plane=\n                    node.kubernetes.io/exclude-from-external-load-balancers=\nAnnotations:        kubeadm.alpha.kubernetes.io/cri-socket: unix:///var/run/containerd/containerd.sock\n                    node.alpha.kubernetes.io/ttl: 0\n                    projectcalico.org/IPv4Address: 10.2.0.48/19\n                    projectcalico.org/IPv4IPIPTunnelAddr: 172.16.219.64\n                    volumes.kubernetes.io/controller-managed-attach-detach: true\nCreationTimestamp:  Thu, 25 Sep 2025 03:04:22 +0000\nTaints:             <none>\nUnschedulable:      false\nLease:\n  HolderIdentity:  master\n  AcquireTime:     <unset>\n  RenewTime:       Wed, 22 Apr 2026 08:07:23 +0000\nConditions:\n  Type                 Status  LastHeartbeatTime                 LastTransitionTime                Reason                       Message\n  ----                 ------  -----------------                 ------------------                ------                       -------\n  NetworkUnavailable   False   Fri, 17 Apr 2026 07:03:48 +0000   Fri, 17 Apr 2026 07:03:48 +0000   CalicoIsUp                   Calico is running on this node\n  MemoryPressure       False   Wed, 22 Apr 2026 08:06:02 +0000   Thu, 26 Mar 2026 06:29:35 +0000   KubeletHasSufficientMemory   kubelet has sufficient memory available\n  DiskPressure         False   Wed, 22 Apr 2026 08:06:02 +0000   Thu, 26 Mar 2026 06:29:35 +0000   KubeletHasNoDiskPressure     kubelet has no disk pressure\n  PIDPressure          False   Wed, 22 Apr 2026 08:06:02 +0000   Thu, 26 Mar 2026 06:29:35 +0000   KubeletHasSufficientPID      kubelet has sufficient PID available\n  Ready                True    Wed, 22 Apr 2026 08:06:02 +0000   Thu, 26 Mar 2026 06:29:51 +0000   KubeletReady                 kubelet is posting ready status. AppArmor enabled\nAddresses:\n  InternalIP:  10.2.0.48\n  Hostname:    master\nCapacity:\n  cpu:                12\n  ephemeral-storage:  305947200Ki\n  hugepages-1Gi:      0\n  hugepages-2Mi:      0\n  memory:             32860480Ki\n  pods:               110\nAllocatable:\n  cpu:                12\n  ephemeral-storage:  281960939054\n  hugepages-1Gi:      0\n  hugepages-2Mi:      0\n  memory:             32758080Ki\n  pods:               110\nSystem Info:\n  Machine ID:                 6bb27862c82149418d0f5624411d0b22\n  System UUID:                474c1770-4235-4ffa-8e94-f5bb287cb508\n  Boot ID:                    bbadb6a3-ee9c-480b-bc49-b9f0f468e895\n  Kernel Version:             5.15.0-173-generic\n  OS Image:                   Ubuntu 22.04.4 LTS\n  Operating System:           linux\n  Architecture:               amd64\n  Container Runtime Version:  containerd://1.6.32\n  Kubelet Version:            v1.26.8\n  Kube-Proxy Version:         v1.26.8\nNon-terminated Pods:          (17 in total)\n  Namespace                   Name                                                 CPU Requests  CPU Limits  Memory Requests  Memory Limits  Age\n  ---------                   ----                                                 ------------  ----------  ---------------  -------------  ---\n  kube-system                 calico-node-4kp26                                    250m (2%)     0 (0%)      0 (0%)           0 (0%)         183d\n  kube-system                 etcd-master                                          100m (0%)     0 (0%)      100Mi (0%)       0 (0%)         209d\n  kube-system                 kube-apiserver-master                                250m (2%)     0 (0%)      0 (0%)           0 (0%)         209d\n  kube-system                 kube-controller-manager-master                       200m (1%)     0 (0%)      0 (0%)           0 (0%)         209d\n  kube-system                 kube-multus-ds-sc2jn                                 100m (0%)     100m (0%)   50Mi (0%)        50Mi (0%)      86d\n  kube-system                 kube-proxy-wbh4k                                     0 (0%)        0 (0%)      0 (0%)           0 (0%)         27d\n  kube-system                 kube-scheduler-master                                100m (0%)     0 (0%)      0 (0%)           0 (0%)         209d\n  xnet                        api-server-6bd6bf8d6f-27svp                          0 (0%)        0 (0%)      0 (0%)           0 (0%)         23d\n  xnet                        deepflow-agent-whn22                                 100m (0%)     1 (8%)      128Mi (0%)       768Mi (2%)     23d\n  xnet                        elasticsearch-master-0                               1 (8%)        1 (8%)      2Gi (6%)         2Gi (6%)       23d\n  xnet                        ham-qzjg5                                            0 (0%)        0 (0%)      0 (0%)           0 (0%)         85d\n  xnet                        observability-filebeat-ffwsp                         100m (0%)     1 (8%)      100Mi (0%)       200Mi (0%)     23d\n  xnet                        observability-kepler-7scjm                           0 (0%)        0 (0%)      0 (0%)           0 (0%)         23d\n  xnet                        observability-kube-state-metrics-798986b8b7-6z2dq    0 (0%)        0 (0%)      0 (0%)           0 (0%)         23d\n  xnet                        observability-mysql-764f9d5966-wh2bc                 0 (0%)        0 (0%)      0 (0%)           0 (0%)         23d\n  xnet                        observability-prometheus-node-exporter-lj75r         0 (0%)        0 (0%)      0 (0%)           0 (0%)         23d\n  xnet                        observability-telegraf-79f45d86-4kzkm                2 (16%)       4 (33%)     4Gi (12%)        8Gi (25%)      23d\nAllocated resources:\n  (Total limits may be over 100 percent, i.e., overcommitted.)\n  Resource           Requests      Limits\n  --------           --------      ------\n  cpu                4200m (35%)   7100m (59%)\n  memory             6522Mi (20%)  11258Mi (35%)\n  ephemeral-storage  0 (0%)        0 (0%)\n  hugepages-1Gi      0 (0%)        0 (0%)\n  hugepages-2Mi      0 (0%)        0 (0%)\nEvents:              <none>", "duration_s": 0}, {"tool": "TodoWrite", "data": "Investigation plan updated with 5 tasks.\n\n# CURRENT INVESTIGATION TASKS\n\n**Task Status**: 5 completed, 0 in progress, 0 pending\n\n[✓] [t1] 查看异常 Pod appconfigfail 的详细描述和事件\n[✓] [t2] 查看异常 Pod 的容器日志\n[✓] [t3] 查看异常 Pod 的 Deployment/Controller 配置\n[✓] [t4] 检查节点 node2 的健康状况\n[✓] [t5] 检查集群整体资源使用情况\n\n**Instructions**: Use TodoWrite tool to update task status as you work.", "duration_s": 0}], "llm_analysis": "## 集群健康检查报告\n\n### 📊 整体概况\n\n| 项目 | 状态 |\n|------|------|\n| **集群节点** | 3/3 Ready（master, node1, node2） |\n| **所有 Pod** | 大部分 Running，**1 个异常** |\n| **集群版本** | v1.26.8 |\n| **容器运行时** | containerd 1.6.32 |\n| **网络** | Calico 正常 |\n\n---\n\n### ❌ 唯一异常：Pod `appconfigfail-7649c79dc5-q4zjz`\n\n| 字段 | 值 |\n|------|-----|\n| **命名空间** | `aiops-e2e` |\n| **节点** | node2 (10.2.0.50) |\n| **状态** | `CrashLoopBackOff` |\n| **重启次数** | 10 次 |\n| **退出码** | **42**（业务自定义退出码） |\n| **镜像** | `busybox:1.36` |\n\n#### 根本原因分析\n\n该 Pod 的启动命令是一个 shell 脚本，其中检查了 `APP_BOOT_MODE` 环境变量：\n\n```\nif [ -z \"${APP_BOOT_MODE:-}\" ]; then\n    echo \"FATAL: missing required APP_BOOT_MODE\"\n    echo \"FATAL: business config validation failed before server startup\"\n    exit 42\nfi\n```\n\n**容器日志输出**：\n- `L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config`\n- `FATAL: missing required APP_BOOT_MODE`\n- `FATAL: business config validation failed before server startup`\n\n**Pod 配置中没有任何环境变量设置**（`Environment: <none>`），所以 `APP_BOOT_MODE` 始终为空，导致每次启动都立即以 exit code 42 退出。\n\n---\n\n### ✅ 集群健康状态（其他方面）\n\n| 检查项 | 结果 |\n|--------|------|\n| **所有 3 个节点** | ✅ Ready，无 Taint |\n| **节点资源** | ✅ CPU/内存/磁盘/PID 均正常（无压力） |\n| **系统组件** | ✅ etcd, kube-apiserver, kube-controller-manager, kube-scheduler, coredns, calico, kube-proxy 均正常 |\n| **网络** | ✅ Calico 正常运行，Pod 网络连通 |\n| **镜像拉取** | ✅ `busybox:1.36` 已存在于节点本地 |\n\n---\n\n### 📋 总结\n\n集群整体健康，**只有一个问题 Pod**：`appconfigfail`（位于 `aiops-e2e` 命名空间）。该问题属于 **L4 业务层配置错误** — Deployment 未设置 `APP_BOOT_MODE` 环境变量，导致容器启动脚本检测到该变量缺失后主动以 exit code 42 退出，进入 `CrashLoopBackOff`。\n\n**建议修复**：在 Deployment 的 Pod template 中为容器添加环境变量 `APP_BOOT_MODE`，例如：\n```yaml\nenv:\n  - name: APP_BOOT_MODE\n    value: \"production\"\n```", "collection_summary": "计划 10 项，实际采集 10 项，未采集 0 项，完整度 100%", "evidence_inventory": [{"id": "auto_0", "description": "工具采集: kubectl_get_by_kind_in_cluster", "level": "important", "collected": true, "source": "thinking_auto"}, {"id": "auto_1", "description": "工具采集: kubectl_get_by_kind_in_cluster", "level": "important", "collected": true, "source": "thinking_auto"}, {"id": "auto_2", "description": "工具采集: kubectl_describe", "level": "important", "collected": true, "source": "thinking_auto"}, {"id": "auto_3", "description": "工具采集: kubectl_events", "level": "important", "collected": true, "source": "thinking_auto"}, {"id": "auto_4", "description": "工具采集: kubectl_get_by_kind_in_namespace", "level": "important", "collected": true, "source": "thinking_auto"}, {"id": "auto_5", "description": "工具采集: kubectl_get_by_kind_in_namespace", "level": "important", "collected": true, "source": "thinking_auto"}, {"id": "auto_6", "description": "工具采集: kubectl_get_by_name", "level": "important", "collected": true, "source": "thinking_auto"}, {"id": "auto_7", "description": "工具采集: kubectl_describe", "level": "important", "collected": true, "source": "thinking_auto"}, {"id": "auto_8", "description": "工具采集: kubectl_describe", "level": "important", "collected": true, "source": "thinking_auto"}, {"id": "auto_9", "description": "工具采集: kubectl_describe", "level": "important", "collected": true, "source": "thinking_auto"}], "missing_reasons": [], "early_stop": {"triggered": false, "reason": "", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 10/10 项, 完整度: 100%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (40.4s)
   📤 → 下游数据: root_cause=
   confidence=95%
   causal_chain={"root_cause": "Deployment appconfigfail 的 Pod template 中未定义 APP_BOOT_MODE 环境变量", "propagation": "容器启动时执行 shell 脚本，检查 ${APP_BOOT_MODE:-} 是否为空 -> 变量不存在导致条件成立 -> 脚本输出 FATAL 日志 -> 主动调用 exit 42", "direct_cause": "容器启动脚本因 APP_BOOT_MODE 环境变量缺失而主动退出，返回业务退出码 42", "manifestation": "Pod 状态为 CrashLoopBackOff，已重启 10 次，Deployment 0/1 副本可用"}
   rca_analysis={"phenomenon": "集群中存在一个异常 Pod appconfigfail-7649c79dc5-q4zjz 处于 CrashLoopBackOff 状态，已重启 10 次", "evidence_inventory": [{"id": "e1", "content": "Pod appconfigfail-7649c79dc5-q4zjz 状态为 CrashLoopBackOff，重启 10 次，退出码 42", "source": "kubectl_get_by_kind_in_cluster", "reliability": "高"}, {"id": "e2", "content": "Pod 容器日志输出：FATAL: missing required APP_BOOT_MODE，FATAL: business config validation failed，L4_CONFIG_BOOTSTRAP_FAIL", "source": "LLM 证据分析", "reliability": "高"}, {"id": "e3", "content": "Pod 配置中 Environment: <none>，未设置任何环境变量", "source": "kubectl_describe", "reliability": "高"}, {"id": "e4", "content": "Deployment appconfigfail 的镜像为 busybox:1.36，0/1 可用，28 分钟前创建", "source": "kubectl_get_by_name", "reliability": "高"}, {"id": "e5", "content": "集群 3 个节点（master, node1, node2）全部 Ready，资源正常，系统组件正常", "source": "LLM 证据分析", "reliability": "高"}, {"id": "e6", "content": "事件记录显示 Pod 成功调度到 node2，镜像拉取成功（5 次 Pulled 事件）", "source": "kubectl_events", "reliability": "高"}, {"id": "e7", "content": "节点 node2 状态 Ready，无异常标签或 Taint", "source": "kubectl_describe", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Pod: appconfigfail-7649c79dc5-q4zjz, Status: CrashLoopBackOff, Restarts: 10, Exit Code: 42, Node: node2 (10.2.0.50), IP: 172.16.104.57", "interpretation": "Pod 在 28 分钟内已重启 10 次，退出码 42 为业务自定义退出码（非系统信号 137），表明容器进程主动退出而非被 OOM Kill 或节点驱逐"}, {"evidence_id": "e2", "raw_data": "容器日志行: 'L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config', 'FATAL: missing required APP_BOOT_MODE', 'FATAL: business config validation failed before server startup'", "interpretation": "日志明确显示业务启动时因缺少 APP_BOOT_MODE 环境变量而主动终止，属于 L4 业务层配置错误"}, {"evidence_id": "e3", "raw_data": "Pod spec 中 Environment 字段值为 '<none>'，未定义任何环境变量", "interpretation": "Deployment 的 Pod template 中未配置 env 字段，导致 APP_BOOT_MODE 环境变量缺失，与日志中的 FATAL 错误完全吻合"}, {"evidence_id": "e4", "raw_data": "Deployment: appconfigfail, Ready: 0/1, Up-to-date: 1, Available: 0, Age: 28m, Image: busybox:1.36", "interpretation": "Deployment 期望 1 个副本，但 0 个可用，因为唯一的 Pod 持续 CrashLoopBackOff"}, {"evidence_id": "e5", "raw_data": "3/3 nodes Ready, all system components (etcd, kube-apiserver, calico, coredns, etc.) healthy, no resource pressure", "interpretation": "集群基础设施和节点均正常，不存在节点级或集群级故障"}, {"evidence_id": "e6", "raw_data": "Events: Scheduled (28m ago) -> AddedInterface (28m ago) -> Pulled (x5 over 26m)", "interpretation": "Pod 调度和镜像拉取均成功，容器能够正常启动，但随后因业务逻辑退出，排除了调度和镜像问题"}, {"evidence_id": "e7", "raw_data": "Node: node2, Status: Ready, No Taints, No resource pressure symptoms", "interpretation": "运行该 Pod 的节点 node2 完全健康，排除了节点级问题导致 Pod 异常的可能性"}], "causal_chain": {"root_cause": "Deployment appconfigfail 的 Pod template 中未定义 APP_BOOT_MODE 环境变量", "propagation": "容器启动时执行 shell 脚本，检查 ${APP_BOOT_MODE:-} 是否为空 -> 变量不存在导致条件成立 -> 脚本输出 FATAL 日志 -> 主动调用 exit 42", "direct_cause": "容器启动脚本因 APP_BOOT_MODE 环境变量缺失而主动退出，返回业务退出码 42", "manifestation": "Pod 状态为 CrashLoopBackOff，已重启 10 次，Deployment 0/1 副本可用"}, "root_cause_summary": "集群唯一的异常是 Pod appconfigfail-7649c79dc5-q4zjz（aiops-e2e 命名空间，运行于 node2）处于 CrashLoopBackOff 状态，已重启 10 次。根因是 Deployment appconfigfail 的 Pod template 中未设置 APP_BOOT_MODE 环境变量（证据 e3：Environment: <none>），导致容器启动脚本检测到该变量缺失后，输出 'FATAL: missing required APP_BOOT_MODE'（证据 e2）并主动以退出码 42 退出（证据 e1）。集群整体健康：3/3 节点 Ready（证据 e5），节点 node2 正常（证据 e7），镜像拉取和调度均成功（证据 e6）。", "confidence": 0.95, "primary_runbooks": [], "alternative_causes": [{"cause": "ConfigMap 或 Secret 引用错误导致环境变量未注入", "reason": "已排除：Pod 配置中未引用任何 ConfigMap 或 Secret，且 Environment 字段为 <none>"}, {"cause": "容器镜像 entrypoint 脚本有 bug", "reason": "已排除：日志明确指示是 APP_BOOT_MODE 缺失导致的退出，属于配置问题而非代码 bug"}], "limitations": "容器启动脚本的完整源码未采集，但基于日志输出和退出码 42 已可确认根因；节点资源使用数据（CPU/内存百分比）未提供，但集群健康报告显示无压力，不影响根因判断"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 95%
   🔗 因果链:
     根本原因: Deployment appconfigfail 的 Pod template 中未定义 APP_BOOT_MODE 环境变量
     传导机制: 容器启动时执行 shell 脚本，检查 ${APP_BOOT_MODE:-} 是否为空 -> 变量不存在导致条件成立 -> 脚本输出 FATAL 日志 -> 主动调用 exit 42
     最终表现: Pod 状态为 CrashLoopBackOff，已重启 10 次，Deployment 0/1 副本可用


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (42.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5349 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 13m 2.5s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将为您分析集群的当前状态。

---
## 📊 诊断概览

**集群核心问题总结：**
您的集群整体运行**非常健康**，但存在 **1 个业务层面的配置问题 Pod**，正处于持续重启状态。

| 项目 | 内容 |
|------|------|
| **集群节点状态** | ✅ 全部正常 (3/3 Ready: master, node1, node2) |
| **集群资源压力** | ✅ 无 (CPU/内存/Disk/PID 均正常) |
| **系统组件健康** | ✅ 全部正常 (etcd, kube-apiserver, coredns, calico 等) |
| **问题数量** | **1 个** |
| **问题层级** | L4 - 应用层 |
| **问题分类** | 应用启动配置校验失败 (Config Bootstrap Fail) |
| **置信度** | **高 (95%)** |
| **证据完整度** | 10/10 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| **问题 Pod** | `appconfigfail-7649c79dc5-q4zjz` |
| **命名空间** | `aiops-e2e` |
| **所属 Node** | `node2` (10.2.0.50) |
| **Pod 状态** | `CrashLoopBackOff` |
| **容器退出码** | **42** (业务自定义退出码) |
| **已重启次数** | 10 次 (28分钟内) |

---

## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl_get_by_kind_in_cluster` | `STATUS: CrashLoopBackOff, RESTARTS: 10, Exit Code: 42` | Pod 持续重启，退出码 42 为业务主动退出，非系统级 OOM |
| 2 | 容器日志 | `run_bash_command` | `L4_CONFIG_BOOTSTRAP_FAIL: ... abort due to invalid config` <br> `FATAL: missing required APP_BOOT_MODE` <br> `FATAL: business config validation failed...` | 应用启动时明确因**缺少 `APP_BOOT_MODE` 环境变量**而主动终止 |
| 3 | Pod 配置 | `kubectl_describe` | `Environment: <none>` | Pod 的容器定义中**未设置任何环境变量**，导致 `APP_BOOT_MODE` 缺失 |
| 4 | Deployment 状态 | `kubectl_get_by_name` | `Deployment: appconfigfail, READY: 0/1, AVAILABLE: 0` | 期望 1 个副本，但 0 个可用，因为唯一的 Pod 持续崩溃 |
| 5 | 节点健康 | `kubectl_describe` (node2) | `Status: Ready, Conditions: all False (健康), Taints: <none>` | 运行 Pod 的节点 `node2` 完全正常，无资源压力或污点 |
| 6 | 集群节点 | `kubectl_get_by_kind_in_cluster` | `3 Nodes (master, node1, node2) all Ready` | 集群基础设施健康 |
| 7 | Pod 事件 | `kubectl_events` | `Scheduled -> AddedInterface -> Pulled (x5)` | Pod 调度、网络、镜像拉取均成功，排除了基础环境问题 |

### 证据关联分析
- **证据 #2 + 证据 #3 印证**：日志明确报错 “missing required APP_BOOT_MODE”，同时 Pod 配置显示 `Environment: <none>`，根因指向 **Deployment 配置遗漏**。
- **证据 #1 + 证据 #4 印证**：退出码 42 是脚本主动执行 `exit 42` 的结果，导致 Pod 状态为 `CrashLoopBackOff`，进而使 Deployment 0 个副本可用。
- **证据 #5 + 证据 #6 + 证据 #7 排除**：节点、集群基础设施和 Pod 调度/网络均正常，问题被限定在**业务配置层 (L4)**。

### 缺失证据（如有）
无。所有关键证据均已采集，完整度 100%。

---

## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                    │
│ Deployment `appconfigfail` 的 Pod template 中**未定义 `APP_BOOT_MODE`** 环境变量 │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                    │
│ 容器启动时执行 shell 脚本 → `if [ -z "${APP_BOOT_MODE:-}" ]` 条件成立 → 脚本报错  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                    │
│ 容器启动脚本检测到 `APP_BOOT_MODE` 缺失，主动调用 `exit 42` 退出进程               │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                │
│ Pod `appconfigfail` 状态 `CrashLoopBackOff`，已重启 10 次，Deployment 0/1 可用  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2 (FATAL: missing required APP_BOOT_MODE) 和证据 #3 (Environment: <none>)，问题的根本原因是 **`appconfigfail` 这个 Deployment 在 Pod template 中遗漏了 `APP_BOOT_MODE` 环境变量的定义**。容器启动脚本检测到此缺失后，主动以业务退出码 42 退出，导致 Pod 陷入 `CrashLoopBackOff`。

**置信度**：高 (95%)
- ✅ 容器日志与 Pod 配置完美印证，排除了所有其他可能性。
- ✅ 集群和节点均健康，排除了基础设施问题。

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）
**1. [优先] 为 Deployment 添加缺失的环境变量**
这是一个配置错误，通过在 Deployment 中定义环境变量即可解决。

```bash
# 方法一：直接编辑 Deployment 添加环境变量
kubectl set env deployment/appconfigfail -n aiops-e2e APP_BOOT_MODE=production
```
*依据*：根因是环境变量缺失，`kubectl set env` 是快速修复此问题的最佳实践。命令执行后，K8s 会自动触发滚动更新，重建 Pod。

**2. [验证] 确认修复是否生效**
```bash
# 查看 Pod 状态，应变为 Running
kubectl get pod -n aiops-e2e -l app=appconfigfail

# 查看 Pod 的事件，确认新 Pod 启动成功
kubectl describe pod -n aiops-e2e -l app=appconfigfail | tail -20
```

### 后续优化
1. **完善 Deployment 配置**：在 `appconfigfail` 的 YAML 定义中显式声明所有必需的环境变量，避免类似遗漏。
2. **配置检查**：在 CI/CD 流程中增加对 Deployment 配置的校验，确保所有必需的 ConfigMap 和 Env 已正确设置。
3. **应用优化**：容器启动脚本中的错误信息应包含更具体的建议（如 “请设置 APP_BOOT_MODE=production”），而非仅仅报错。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认修复执行 | `kubectl set env deployment/appconfigfail -n aiops-e2e APP_BOOT_MODE=production` | `deployment.apps/appconfigfail env updated` |
| 2. 确认新 Pod 创建 | `kubectl get pod -n aiops-e2e -l app=appconfigfail -w` | 旧 Pod 终止，新 Pod 状态变为 `Running` |
| 3. 检查 Pod 重启次数 | `kubectl get pod -n aiops-e2e -l app=appconfigfail -o jsonpath='{.items[0].status.containerStatuses[0].restartCount}'` | 重启次数停止增加 |
| 4. 确认 Deployment 可用 | `kubectl get deployment appconfigfail -n aiops-e2e` | `READY: 1/1, AVAILABLE: 1` |

---

## ⚠️ 注意事项
- 此次问题属于**业务配置错误**，不影响集群核心组件和其他业务 Pod 的运行。
- 当前设置的 `APP_BOOT_MODE=production` 为测试值，请根据实际业务需求替换为正确的模式值（如 `development`、`staging` 等）。

---

## 📊 性能统计

├─ 总耗时: 13.0m
├─ 问题定位: 628.9s (80%) ✅
├─ 证据链采集: 70.7s (9%) ✅
├─ 根因分析: 40.4s (5%) ✅
├─ 汇总总结: 42.5s (5%) ✅
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
