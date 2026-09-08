## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod workload-5dbb5dcd6c-kbwsx in aiops-case-05 is stuck in ContainerCreating/Pending state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Reason: NoNetworkFound, Message: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 证明 `multus` 插件在多个时间点（近 1 小时内持续）反复报告找不到指定的网络定义资源 |
| 2 | K8s Event | Kubernetes | `Reason: FailedCreatePodSandBox, Message: ... failed setup network for sandbox: plugin type="multus" ... GetNetworkDelegates: failed getting the delegate: cannot find a network-attachment-definition ... "unavailable-network" not found` | 提供根本失败机制：由于网络插件失败导致 Pod 沙箱无法创建 |
| 3 | K8s State | Kubernetes | `container.waiting_reason: ContainerCreating` | 确认 Pod 处于挂起等待状态，符合因网络依赖资源缺失导致的启动阻塞表现 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` | 从监控维度客观确认了当前等待状态的存在，佐证了 Pod 未能进入运行阶段的事实 |

**证据关联说明：**
- 证据 1 的 K8s 事件表明 Multus 在 Pod 启动过程中反复尝试加载网络配置，但始终找不到名为 `unavailable-network` 的定义。
- 证据 2 进一步记录了该失败导致的直接后果——Pod 沙箱创建失败，这与证据 3 中的容器等待状态及证据 4 中的监控指标完全一致。

## 🎯 根因分析 · g1

### 因果链

```text
命名空间中缺少 NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 插件无法查找网络定义并配置网络 → Pod 沙箱创建失败，网络设置受阻 → Pod 状态卡在 ContainerCreating/Pending
```

### 根因结论

**已确认的根因：**
Pod spec 中包含了 Multus CNI 网络注解，引用了一个名为 `unavailable-network` 的网络资源，但在 `aiops-case-05` 命名空间中并不存在对应的 `NetworkAttachmentDefinition` 资源。这导致 Multus 插件无法完成网络配置，进而阻塞了 Pod 沙箱的创建。

**证据支持：**
- K8s 事件 `NoNetworkFound` 明确指出资源缺失（见证据 1）；
- K8s 事件 `FailedCreatePodSandBox` 确认了该缺失导致的多插件失败机制（见证据 2）；
- 状态与监控数据一致，均指向网络配置阶段的启动阻塞（见证据 3、4）。

**未确认事项：**
根据诊断报告中的 `unknowns` 字段，目前无法确定该 `NetworkAttachmentDefinition` 资源是意外被删除、从未创建，还是配置引用本身存在错误（即资源名是否拼写错误）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 22.0s
├─ 并发证据采集: 39.5s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 39.5s (Evidence 30.4s, RCA 8.9s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-volume-mount-failed, pod-sandbox-create-failed
