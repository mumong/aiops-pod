## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod annotation k8s.v1.cni.cncf.io/networks=unavailable-network 请求了不存在的 NetworkAttachmentDefinition 'unavailable-network'，导致 Multus CNI 插件因 NoNetworkFound 报错而反复失败，容器无法创建网络命名空间。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | multus | `Warning NoNetworkFound` 56m~11s 期间反复记录 `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` | 确认 Multus CNI 插件持续因找不到指定的网络定义而失败，形成高频重试证据 |
| 2 | K8s Event | kubelet | `Warning FailedCreatePodSandBox` (x333 over 73m) `failed to setup network for sandbox... plugin type="multus"... error in getting k8s network for pod... getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network)... not found` | 证实底层容器运行时因网络插件报错，导致 Pod 沙箱创建被 kubelet 持续拒绝 |
| 3 | K8s State | Kubernetes | `container.waiting_reason`: `Container`="app", `reason`="ContainerCreating" | 确认 Pod 当前卡在网络初始化阶段，未进入就绪或运行状态 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 值=1, `labels`={container="app", reason="ContainerCreating"} | 从集群层面确认该 Pod 处于因 ContainerCreating 导致的等待状态 |

**证据印证说明：**
Kubernetes 事件（#1, #2）直接暴露了故障根源：Pod 试图通过 Multus 插件加载名为 `unavailable-network` 的网络定义，但该资源在 `aiops-case-05` 命名空间中不存在。这一配置级错误直接导致容器运行时无法创建网络命名空间，从而表现为持续存在的 `ContainerCreating` 状态（#3）及对应的 Prometheus 指标记录（#4）。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了不存在的 NetworkAttachmentDefinition 资源 → Multus CNI 插件尝试加载该定义时查找失败 → kubelet 无法创建 Pod 网络沙箱（SandBox） → 容器进入 ContainerCreating 等待状态
```

### 根因结论

**已确认的根因：**
Pod `aiops-case-05/workload-5dbb5dcd6c-bntfh` 的注解 `k8s.v1.cni.cncf.io/networks` 指向了一个不存在的网络定义 `unavailable-network`。
- **机制印证：** 集群中大量 `NoNetworkFound` 警告（证据 #1）和 `FailedCreatePodSandBox` 错误（证据 #2）均明确指向 Multus 插件在尝试获取 `getKubernetesDelegate` 时，因找不到目标资源而报错。
- **状态印证：** 这种网络配置的持续缺失导致 kubelet 无法完成网络初始化，使 Pod 长期处于 `ContainerCreating` 状态（证据 #3, #4）。
- **结论：** 故障是由 Pod 侧错误的网络注解配置引起的。

**缺失或限制：**
由于 Pod 未成功启动，应用层面的日志（Logging）和 Trace（Tracing）数据不可用。`kubectl get network-attachment-definitions` 命令因 RBAC 限制执行失败，无法直接列举集群内现有的网络定义列表，但这不影响对当前 Pod 缺失指定资源这一事实的判断。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 44.3s
├─ 并发证据采集: 54.6s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 54.6s (Evidence 48.5s, RCA 5.9s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed
