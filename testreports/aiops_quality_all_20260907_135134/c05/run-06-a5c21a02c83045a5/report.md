## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod workload-5dbb5dcd6c-kbwsx stuck in ContainerCreating (Pending) due to network attachment failure |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | multus | `Warning NoNetworkFound ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (如 `fact-00e69a97f044`) | 直接指出 Multus 插件在 Pod 所在命名空间找不到指定的 NAD 资源 |
| 2 | K8s Event | kubelet | `Warning FailedCreatePodSandBox ... failed to setup network for sandbox ... plugin type="multus" name="multus-cni-network" failed (add)` (如 `fact-09d2407d774e`) | 确认 CNI 插件初始化失败是导致容器沙箱创建失败的根本原因 |
| 3 | K8s State | kubelet | `ContainerCreating` (fact `fact-0592a96915ed`) | 证实 Pod 处于等待容器启动的挂起状态 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = 1, label `reason="ContainerCreating"` (fact `fact-146e7b1470f8`) | 从指标层佐证容器状态为因网络创建失败而挂起 |

证据表明，Pod 因引用的 `unavailable-network` NAD 不存在，导致 Multus CNI 插件在执行网络初始化时报错，进而使 kubelet 无法创建 Pod 沙箱，最终表现为 Pod 长期处于 `ContainerCreating` 状态。

## 🎯 根因分析 · g1

### 因果链

```text
缺少 NAD 资源 'unavailable-network' → Multus CNI 插件初始化网络失败 → kubelet 创建容器沙箱 (FailedCreatePodSandBox) → Pod 挂起在 ContainerCreating
```

### 根因结论

已确认根因为：Pod `workload-5dbb5dcd6c-kbwsx` 配置的 CNI 网络依赖 `aiops-case-05` 命名空间下的 `unavailable-network` NetworkAttachmentDefinition 资源，但该资源在集群中不存在。

这一缺失导致 Multus 插件无法获取必要的网络委托配置（事实 `fact-00e69a97f044`），进而致使 kubelet 执行网络初始化时抛出 `FailedCreatePodSandBox` 错误（事实 `fact-09d2407d774e`），最终导致容器无法启动并永久处于 `ContainerCreating` 状态（事实 `fact-0592a96915ed`）。

---

## 📊 性能统计

```text
├─ 总耗时: 6.6m
├─ 问题定位: 30.6s
├─ 并发证据采集: 356.9s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 356.9s (Evidence 346.6s, RCA 10.1s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-imagepull-failed
