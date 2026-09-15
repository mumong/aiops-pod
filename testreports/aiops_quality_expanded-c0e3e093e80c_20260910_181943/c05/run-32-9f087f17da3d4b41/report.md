## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-bntfh 依赖 Multus CNI 插件配置名为 'unavailable-network' 的网络附件定义（NetworkAttachmentDefinition），但该资源在当前命名空间中不存在，导致 Multus 持续报 NoNetworkFound 错误，kubelet 无法创建 Pod 沙箱。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Multus | `Warning NoNetworkFound ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (持续约 60 分钟) | 直接确认 Pod 引用的特定网络资源缺失，导致网络配置阶段失败 |
| 2 | K8s Event | kubelet | `Warning FailedCreatePodSandBox ... failed to setup network for sandbox ... plugin type="multus" ... failed: cannot find a network-attachment-definition (unavailable-network)` | 证实 Multus 插件调用失败是 Pod 沙箱创建受阻的直接原因 |
| 3 | K8s State | Kubernetes | `ContainerCreating` (容器: app) | 确认 Pod 调度成功但容器生命周期因前置条件（网络）未满足而停滞 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` | 从指标层面印证了 Pod 持续处于等待状态，与事件日志时间线一致 |

**证据印证说明：**
Kubernetes 事件（#1, #2）提供了完整的因果细节，明确指出了 Multus 插件因找不到 `unavailable-network` 定义而报错，这直接导致了 kubelet 无法创建 Pod 沙箱（#2），最终使 Pod 保持 `ContainerCreating` 状态（#3）。Metric 数据（#4）从聚合维度确认了这一等待状态的持续性，与长达一小时的 Event 日志完全吻合。

## 🎯 根因分析 · g1

### 因果链

```text
NetworkAttachmentDefinition 'unavailable-network' 缺失 → Multus 插件无法解析网络配置并抛出 NoNetworkFound → kubelet 无法建立 Pod 网络沙箱 (FailedCreatePodSandBox) → Pod 卡死在 ContainerCreating 状态
```

### 根因结论

已确认根因为 **Pod 依赖的 CNI 网络定义资源不存在**。

`aiops-case-05/workload-5dbb5dcd6c-bntfh` 配置了 Multus CNI 插件，显式引用了名为 `unavailable-network` 的网络附件定义。Kubernetes 集群中该命名空间下缺乏此资源，导致 Multus 在尝试为 Pod 配置网络时持续报错（证据 #1, #2）。kubelet 因网络配置失败而拒绝创建 Pod 沙箱，致使 Pod 无法进入运行阶段，长期停留在 `ContainerCreating` 状态（证据 #3）。

Logging 和 Tracing 维度因容器未启动、无 IP 且未产生流量被标记为 `not_applicable`，但这不影响基于 Kubernetes 状态与事件对网络配置故障的定责。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 15.1s
├─ 并发证据采集: 51.8s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 51.8s (Evidence 43.9s, RCA 7.8s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed
