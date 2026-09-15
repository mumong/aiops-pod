## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-bntfh 在 kubernetes 注解中引用了不存在的 Multus 网络附加定义（NetworkAttachmentDefinition 'unavailable-network'），导致 Multus CNI 插件无法创建网络沙箱，从而使容器持续处于 ContainerCreating 状态（Pending）且无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `FailedCreatePodSandBox`：failed to setup network for sandbox, plugin type="multus" name="multus-cni-network" failed: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05) | 直接阻断容器启动，指明 Multus 尝试加载网络配置失败的具体原因 |
| 2 | K8s Event | Kubernetes | `NoNetworkFound`：cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05) (x47 次，最近 91s) | 持续验证集群中确实缺失名为 `unavailable-network` 的 CRD 对象 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (reason="ContainerCreating", value=1, sample_count=1) | 确认 Pod 处于持续的等待状态，与 CNI 初始化失败后的预期行为一致 |

**证据关联说明：**
1. `K8s Event` 中的 `FailedCreatePodSandBox` 详细日志证实 Multus 插件在尝试执行 `TryLoadPodDelegates` 时，因找不到 `unavailable-network` 定义而抛出错误，这是导致容器状态停滞的直接机制。
2. 大量重复的 `NoNetworkFound` 事件（如 #2）提供了时序上的持续性证据，确认该资源缺失是持续存在的状态而非偶发。
3. `Metric` (#3) 与事件状态相互印证，量化了该异常导致的 Pod 持续处于 `ContainerCreating` 的等待结果。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 注解中引用不存在的网络定义 'unavailable-network' → Multus CNI 插件执行网络委托查找失败 (GetKubernetesDelegate: not found) → 无法创建 Pod 沙箱网络 (FailedCreatePodSandBox) → Pod 持续处于 ContainerCreating 状态无法启动
```

### 根因结论

**已确认的根因：**
Pod `aiops-case-05/workload-5dbb5dcd6c-bntfh` 配置中引用了一个名为 `unavailable-network` 的 `NetworkAttachmentDefinition`，但该定义在 `aiops-case-05` 命名空间中实际并不存在。

*   **证据支撑**：`K8s Event` 明确报告 `cannot find a network-attachment-definition (unavailable-network) ... not found` [证据 #1, #2]。
*   **结果**：Multus 插件无法完成网络初始化，导致容器沙箱创建失败，Pod 长期卡在 `ContainerCreating` 状态 [证据 #3]。

---

## 📊 性能统计

```text
├─ 总耗时: 9.9m
├─ 问题定位: 16.4s
├─ 并发证据采集: 569.6s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 569.6s (Evidence 564.0s, RCA 5.5s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- 未调用 Runbook
