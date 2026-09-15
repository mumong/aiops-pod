## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-bntfh stuck in Pending/ContainerCreating state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (kubelet) | `FailedCreatePodSandBox` over 70m, `rpc error: ... failed to setup network for sandbox`: plugin type="multus" name="multus-cni-network" failed | 确认 Pod 因网络插件失败导致容器沙箱无法创建，停留在 Pending/ContainerCreating 状态 |
| 2 | K8s Event | kubernetes (multus) | `NoNetworkFound`: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found | 直接指出缺失的具体资源标识符 `unavailable-network` 及其所在 Namespace，构成根因证据 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason`="ContainerCreating" (value=1, sample_count=1) | 确认 Pod 处于等待容器的状态，验证了 K8s 事件反映的阻塞现象 |

**证据印证**：Kubernetes Event (fact-06d32c4caf63, fact-bd75701a8382) 提供了从 Multus 拒绝到 Kubelet 失败调用链的完整错误信息。Metric (fact-424c0fb1e2a4) 从时序数据侧证实了 Pod 状态。Logging 与 Tracing 因 Pod 未启动被标记为 `not_applicable`，符合“因网络配置错误导致 Pod 无法创建，进而无法产生业务日志”的物理逻辑。

## 🎯 根因分析 · g1

### 因果链

```text
Namespace 'aiops-case-05' 中缺少 CR 'unavailable-network' → Multus CNI 无法解析 Pod 注解引用的 delegate 网络 → Kubelet 创建 Pod 沙箱失败 (rpc error: Unknown desc) → Pod 永久卡在 Pending / ContainerCreating 状态
```

### 根因结论

**已确认的根因**：Pod `aiops-case-05/workload-5dbb5dcd6c-bntfh` 在 K8s 注解（或 Multus CNI 配置）中引用了一个名为 `unavailable-network` 的 `NetworkAttachmentDefinition`，但该 CR 在 `aiops-case-05` 命名空间中实际上并不存在（Fact #2）。

这导致 Multus CNI 插件在尝试初始化网络时抛出 `NoNetworkFound` 错误，进而引发 `FailedCreatePodSandBox` 事件（Fact #1），最终表现为 Pod 长时间处于 `ContainerCreating` 状态且无法获得 IP 或启动容器（Fact #3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 18.8s
├─ 并发证据采集: 48.0s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 48.0s (Evidence 40.1s, RCA 7.8s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed
