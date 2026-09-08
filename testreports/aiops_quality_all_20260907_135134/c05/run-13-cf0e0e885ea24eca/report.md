## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-kbwsx stuck in Pending/ContainerCreating |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `ContainerCreating` | 确认应用容器持续处于等待状态，Pod 无法进入 Running。 |
| 2 | K8s Event | Multus | `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io "unavailable-network" not found` | 核心故障证据：多路复用 CNI (Multus) 在初始化阶段无法定位网络资源。 |
| 3 | K8s Event | Kubelet | `Failed to create pod sandbox... failed to setup network for sandbox... Multus... failed getting the delegate...` | 底层失败机制：由于网络依赖未满足，容器运行时 (Container Runtime) 无法创建 Pod 沙箱。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` | 指标层面证实了 Pod 持续卡在 `ContainerCreating` 状态，未随时间恢复。 |

**证据关联：**
- 证据 1 和 4 互为表里，从 Pod 状态和监控指标两方面锁定了“卡死”现象。
- 证据 2 与 3 形成因果闭环：Kubelet 报错（证据 3）直接由 Multus 报找不到指定网络定义（证据 2）导致。由于日志/追踪不可用，此 Kubernetes 层面证据为决定性证据。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用不存在的 NetworkAttachmentDefinition → Multus CNI 无法解析网络资源 → 容器运行时创建 Pod Sandbox 失败 → Pod 持续停留在 ContainerCreating 状态
```

### 根因结论

已确认根因为：**`aiops-case-05` 命名空间内引用了不存在的 `NetworkAttachmentDefinition` (“unavailable-network”)。**

Pod `workload-5dbb5dcd6c-kbwsx` 的 Spec 中声明了 Multus CNI 网络附件，但在该命名空间中实际缺少名为 `unavailable-network` 的定义资源（见证据 #2）。这导致 Multus 插件在初始化阶段报错，进而触发 kubelet 的 `FailedCreatePodSandBox`（见证据 #3），最终使 Pod 无法启动并保持 `ContainerCreating` 状态（见证据 #1, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 14.0s
├─ 并发证据采集: 43.3s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 43.3s (Evidence 36.5s, RCA 6.6s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-imagepull-failed, pod-volume-mount-failed, pod-pending-unschedulable, pod-sandbox-create-failed, pod-config-error
