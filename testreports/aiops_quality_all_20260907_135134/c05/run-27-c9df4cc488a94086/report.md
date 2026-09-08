## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod workload-5dbb5dcd6c-kbwsx (aiops-case-05) 卡在 ContainerCreating 阶段，Pod Phase 为 Pending。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `workload-5dbb5dcd6c-kbwsx` 状态：`ContainerCreating` | 确认应用容器未被调度启动，处于等待资源阶段 |
| 2 | K8s Event | Multus | `NoNetworkFound`: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05) (持续约 60m, 频率高) | 核心证据，直接指出依赖的网络定义资源不存在 |
| 3 | K8s Event | Kubelet | `FailedCreatePodSandBox`: plugin type="multus" name="multus-cni-network" failed (add) ... cannot find a network-attachment-definition ... not found | 确认底层沙箱创建因网络插件报错而失败 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = 1 (labels: `container="app"`, `reason="ContainerCreating"`) | 监控数据与事件状态一致，量化了等待现象的持续性 |

**证据关联说明：**
Kubernetes 事件（#2, #3）在时间线上连续记录了多分钟，指出 Multus 插件找不到 `unavailable-network` 定义，直接导致 Kubelet 无法创建沙箱；Kubernetes 状态（#1）和指标（#4）则从宏观层面证实了该 Pod 因此一直处于等待状态，未发生资源争用等其他问题。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 注解引用不存在的网络定义 -> Multus CNI 报错 NoNetworkFound -> Kubelet 无法创建 Pod 沙箱 (FailedCreatePodSandBox) -> Pod 持续处于 ContainerCreating 状态
```

### 根因结论

**已确认根因：** Pod `workload-5dbb5dcd6c-kbwsx` 的注解中引用的 NetworkAttachmentDefinition 资源 `unavailable-network` 在命名空间 `aiops-case-05` 中不存在。

*   **机制：** Multus CNI 插件在尝试为 Pod 配置网络时，找不到对应的 `NetworkAttachmentDefinition` CRD 对象，导致沙箱创建失败。
*   **证据支撑：** 这一结论由 Kubernetes Event 中的 `NoNetworkFound` 和 `FailedCreatePodSandBox` 错误原文直接证实（证据 #2, #3），并由 Metrics 中的等待状态作为辅助印证（证据 #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 17.3s
├─ 并发证据采集: 51.6s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 51.6s (Evidence 43.2s, RCA 8.2s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-volume-mount-failed, pod-imagepull-failed, pod-config-error
