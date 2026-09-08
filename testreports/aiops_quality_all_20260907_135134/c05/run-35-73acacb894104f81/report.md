## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod workload-5dbb5dcd6c-kbwsx stuck in Pending/ContainerCreating |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `reason: FailedCreatePodSandBox, message: ... plugin type="multus" name="multus-cni-network" failed (add): Multus: [aiops-case-05/workload-5dbb5dcd6c-kbwsx]: error loading k8s delegates k8s args: TryLoadPodDelegates: error in getting k8s network for pod: GetNetworkDelegates: failed getting the delegate: getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io "unavailable-network" not found` (fact-2decccaf7b66) | 直接归因：kubelet 创建沙箱失败，原因是 Multus 无法找到指定的 `unavailable-network` CNI 委托定义。 |
| 2 | K8s Event | kubernetes | `reason: NoNetworkFound, message: ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io "unavailable-network" not found` (fact-0fd2f88e29b3) | 现象确认：Multus 持续报错提示该网络定义缺失，覆盖了事件发生的时间窗口。 |
| 3 | K8s State | kubernetes | `container: app, reason: ContainerCreating` (fact-f04ce03b5030) | 状态锁定：Pod 无法通过沙箱创建阶段，容器持续处于等待状态。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason, reason: ContainerCreating, value: 1` (fact-b461cb8f2e50) | 指标佐证：Prometheus 监控确认容器因 `ContainerCreating` 原因处于等待状态。 |

**证据逻辑说明：**
Kubernetes 事件（事实 1 与事实 2）明确指出 `FailedCreatePodSandBox` 是由于 Multus CNI 无法找到 `aiops-case-05` 命名空间下的 `unavailable-network` 网络定义所致。这一配置层面的缺失直接解释了容器状态（事实 3）和指标（事实 4）中 `ContainerCreating` 长期卡死的现象。日志与追踪维度因容器未启动而被标记为不适用，证据链完整。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 引用了不存在的 NetworkAttachmentDefinition 'unavailable-network' (未确认/基于事件推断) → Multus CNI 无法加载该网络定义 (已确认：event fact-0fd2f88e29b3/fact-2decccaf7b66) → Kubelet 沙箱创建失败 (已确认：event fact-2decccaf7b66) → Pod 卡死在 Pending/ContainerCreating (已确认：state fact-f04ce03b5030/metric fact-b461cb8f2e50)
```

### 根因结论

**已确认的根因**：
Pod `workload-5dbb5dcd6c-kbwsx` 被配置为使用 Multus CNI 网络，但该配置引用了一个在 `aiops-case-05` 命名空间中不存在的 NetworkAttachmentDefinition 资源（名为 `unavailable-network`）。

**导致机制**：
1.  Kubernetes 调度 Pod 后，kubelet 尝试创建 Pod 沙箱。
2.  Multus CNI 插件根据 Pod 配置尝试加载 `unavailable-network` 定义（事实 1、2）。
3.  由于该定义不存在，Multus 抛出错误并拒绝配置网络。
4.  网络配置失败导致沙箱创建失败，Pod 无法进入运行阶段，从而卡在 `ContainerCreating` 状态（事实 3、4）。

现有证据（特别是 K8s 事件中的明确报错文本）足以支撑该结论，证据充分。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 32.0s
├─ 并发证据采集: 47.8s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 47.8s (Evidence 39.6s, RCA 8.0s)
└─ 汇总总结: 13.7s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-sandbox-create-failed
