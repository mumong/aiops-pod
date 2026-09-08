## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-kbwsx 的注解 k8s.v1.cni.cni.cncf.io/networks 引用了不存在的 NetworkAttachmentDefinition 'unavailable-network'，导致 Multus CNI 插件创建 Pod 沙箱（sandbox）时因找不到网络定义而持续报错失败，Pod 因此一直卡在 Pending / ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Failed to create pod sandbox: ... plugin type="multus" ... failed getting the delegate: getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (`fact-0e0fb6264a67`) | 确认 Pod 沙箱创建失败，根本原因为 Multus 无法找到指定名称的 CNI 网络定义。 |
| 2 | K8s Event | kubernetes | `Warning NoNetworkFound ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (`fact-5abab3b3160b`) | 在观测窗口内持续重复报错（累计约 40+ 次），确认资源缺失为持续状态。 |
| 3 | K8s State | kubernetes | `container.waiting_reason: ContainerCreating` (`fact-63a3a7b90584`) | 确认 Pod 当前处于非就绪状态，容器未启动，符合网络配置导致的启动阻断特征。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值为 1 (`fact-2db3d625cb32`) | 提供容器处于等待状态的量化指标，佐证启动被阻断。 |
| 5 | Logging | elasticsearch | 无（容器未启动，物理上不会产生应用日志） | 排除应用层或侧车日志异常，证实瓶颈位于 Pod 调度前的沙箱构建阶段。 |

证据之间互相印证：Kubernetes 事件明确指出了 `unavailable-network` 网络定义在 `aiops-case-05` 命名空间中不存在，导致 Multus 插件执行失败（事实 1, 2）；这直接解释了为什么容器状态卡在 `ContainerCreating`（事实 3）且没有业务日志产生（事实 5）。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 注解引用不存在的 NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 执行 network setup 触发 NoNetworkFound 错误 → Pod 沙箱创建失败（FailedCreatePodSandBox），kubelet 持续重试 → Pod 状态持续处于 ContainerCreating（Pending）
```

### 根因结论

已确认的根因为 **Pod `aiops-case-05/workload-5dbb5dcd6c-kbwsx` 的网络配置引用错误**。

Pod 的注解 `k8s.v1.cni.cni.cncf.io/networks` 指向了一个名为 `unavailable-network` 的 `NetworkAttachmentDefinition` 资源，但该资源在 `aiops-case-05` 命名空间中并不存在（事实 1, 2）。这导致 Multus CNI 插件在尝试为 Pod 创建网络沙箱时失败，进而导致 kubelet 持续重试创建 Pod 沙箱，最终表现为 Pod 状态长时间停留在 `ContainerCreating`（事实 3, 4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 27.1s
├─ 并发证据采集: 58.3s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 58.3s (Evidence 48.9s, RCA 9.3s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-imagepull-failed, pod-volume-mount-failed, pod-sandbox-create-failed
