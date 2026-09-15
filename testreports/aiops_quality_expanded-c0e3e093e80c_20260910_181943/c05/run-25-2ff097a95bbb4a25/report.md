## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-bntfh 处于 Pending/ContainerCreating 状态，Kubelet 重复报错 FailedCreatePodSandBox。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: `ContainerCreating` (fact-4d378f668914) | 确认 Pod 停滞在等待状态，未进入运行阶段 |
| 2 | K8s Event | Kubernetes | `FailedCreatePodSandBox`: `Failed to create pod sandbox: rpc error... failed to setup network for sandbox... plugin type="multus" name="multus-cni-network" failed (add)... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (fact-97ed64a805cb) | 直接指向网络插件 Multus 在创建 Pod 沙箱时因缺少网络定义而失败 |
| 3 | K8s Event | Kubernetes | `NoNetworkFound` (x46): `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` (fact-049b7dbcff30 等) | 持续复现同一错误，确认缺失资源未被创建或命名错误 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = `1` (reason: `ContainerCreating`) (fact-e055039119a0) | 监控指标确认 Pod 处于等待状态的数值事实 |

**证据关联说明：**
- 状态 (E1) 确认了现象，Metric (E4) 提供了量化佐证。
- 核心证据在于 Kubelet 尝试配置网络时的具体报错 (E2)，明确指出了失败机制是 Multus 插件无法找到名为 `unavailable-network` 的网络定义。
- E3 提供了大量重复的 Warning 事件，证明了该网络定义的缺失是一个持续存在的、未被自动修复的拓扑问题。

## 🎯 根因分析 · g1

### 因果链

```text
Namespace aiops-case-05 中缺失 NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 插件无法加载网络代理并配置网络 → Kubelet 创建 Pod Sandbox 失败 (FailedCreatePodSandBox) → Pod aiops-case-05/workload-5dbb5dcd6c-bntfh 停滞在 Pending/ContainerCreating 状态
```

### 根因结论

已确认根因：Pod `workload-5dbb5dcd6c-bntfh` 在其网络配置中引用了名为 `unavailable-network` 的 `NetworkAttachmentDefinition`，但该资源在 `aiops-case-05` 命名空间中不存在。

- **证据支撑**：Kubelet 的 `FailedCreatePodSandBox` 事件明确报错 `cannot find a network-attachment-definition (unavailable-network)`，且伴随 46 次相同的 `NoNetworkFound` 警告事件。
- **结论**：Pod 无法正常启动是因为底层网络插件 Multus 无法完成网络挂载，直接导致容器生命周期停留在 `ContainerCreating` 阶段。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 22.6s
├─ 并发证据采集: 53.3s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 53.3s (Evidence 45.0s, RCA 8.1s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed
