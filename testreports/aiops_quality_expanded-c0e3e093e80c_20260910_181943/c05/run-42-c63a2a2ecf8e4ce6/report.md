## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod workload-5dbb5dcd6c-bntfh 卡在 Pending/ContainerCreating 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning FailedCreatePodSandBox 2m51s kubelet Failed to create pod sandbox: ... plugin type="multus" name="multus-cni-network" failed (add): Multus: [aiops-case-05/workload-5dbb5dcd6c-bntfh]: ... failed getting the delegate: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 直接证明网络插件 Multus 在创建沙箱时因找不到特定配置而失败 |
| 2 | K8s Event | Kubernetes | `Warning NoNetworkFound 59m multus cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io "unavailable-network" not found` | 确认为持续性的配置缺失错误，故障起始于 Pod 调度之前 |
| 3 | K8s State | Kubernetes | `status: ContainerWaiting, reason: ContainerCreating` | 证实 Pod 处于启动等待阶段，未发生 CrashLoopBackOff 等运行时故障 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason = 1` (labels: `container: app`, `reason: ContainerCreating`) | 验证 Pod 持续处于 ContainerCreating 状态，符合事件中的等待特征 |

**证据印证说明：**
- 证据 1 和 2 均明确指向 `network-attachment-definitions.k8s.cncf.io "unavailable-network" not found` 这一缺失的依赖，证据 1 给出了更详细的插件调用堆栈（Multus -> delegate），证据 2 提供了故障的历史时间线。
- 证据 3 和 4 分别从 K8s 状态机和 Metrics 维度确认了 Pod 未处于运行态，且处于“正在创建”的等待阶段，这与网络初始化失败的机制完全吻合。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 配置了引用不存在 CRD 的 Multus 注解 'unavailable-network' → Multus 插件找不到 NetworkAttachmentDefinition 资源导致沙箱创建失败 → Pod 持续卡在 ContainerCreating 状态
```

### 根因结论
- **已确认的根因：** Pod `aiops-case-05/workload-5dbb5dcd6c-bntfh` 的 Pod Spec 中配置了 Multus CNI 注解，要求关联一个名为 `unavailable-network` 的 `NetworkAttachmentDefinition` 资源，但该资源在 `aiops-case-05` 命名空间中并不存在（证据 1、证据 2）。
- **结论：** 该配置错误导致 kubelet 无法完成 Pod 网络沙箱的初始化，从而使得容器持续处于 `ContainerCreating` 状态（证据 3、证据 4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 27.6s
├─ 并发证据采集: 39.9s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 39.9s (Evidence 32.9s, RCA 6.9s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-imagepull-failed, pod-volume-mount-failed
