## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod workload-5dbb5dcd6c-kbwsx in aiops-case-05 is stuck in ContainerCreating (Pending) state due to Multus CNI failure. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `NoNetworkFound`: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io "unavailable-network" not found | 持续报错，指向配置依赖的资源缺失 |
| 2 | K8s Event | Kubernetes | `FailedCreatePodSandBox`: failed to setup network for sandbox ... plugin type="multus" name="multus-cni-network" failed: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io "unavailable-network" not found | 导致 kubelet 无法创建沙箱，直接阻塞 Pod 状态 |
| 3 | K8s State | Kubernetes | `container.waiting_reason`: ContainerCreating (container: app) | 确认容器处于等待状态，与多起事件记录吻合 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason`: 1 (labels: container=app, reason=ContainerCreating) | 指标值与事件反映的等待原因一致，确认 Pod 状态未改变 |

**证据说明：**
Kubernetes 事件在长达 50 多分钟的时间窗口内，持续报告 `multus` 插件因找不到 `unavailable-network` 而失败，这是导致 `FailedCreatePodSandBox` 的直接原因。Metric 数据证实 Pod 一直处于 `ContainerCreating` 等待状态，未出现状态变更或恢复迹象，证据链条一致指向网络配置缺失导致的启动阻塞。

## 🎯 根因分析 · g1

### 因果链

```text
未定义的 NetworkAttachmentDefinition 'unavailable-network' → Multus 插件无法获取网络配置 → kubelet 创建 Pod 沙箱失败 (FailedCreatePodSandBox) → Pod 卡在 ContainerCreating 状态
```

### 根因结论

已确认根因为配置错误导致的依赖缺失。Pod 引用的 `NetworkAttachmentDefinition` 资源 `unavailable-network` 在 `aiops-case-05` 命名空间中不存在（证据 #1），导致 Multus CNI 插件无法完成网络配置，进而引发 kubelet 反复创建沙箱失败（证据 #2）。此缺失使得 Pod 无法进入运行状态，表现为持续的 `ContainerCreating` 等待状态（证据 #3, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 17.7s
├─ 并发证据采集: 51.3s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 51.3s (Evidence 43.8s, RCA 7.3s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-volume-mount-failed
