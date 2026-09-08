## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-nhd7v 处于 Pending/ContainerCreating 状态，未能启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: container="app", reason="ContainerCreating" | 确认容器当前处于创建等待阶段 |
| 2 | K8s Event | kubernetes | `event.message` (fact-0e03ad62c75e): `Failed to create pod sandbox: ... plugin type="multus" name="multus-cni-network" failed (add): ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 直接捕获 kubelet 创建 Pod Sandbox 失败的具体错误栈 |
| 3 | K8s Event | kubernetes | `event.message` (fact-08c1618ac6f1): `Warning  NoNetworkFound ... multus ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io "unavailable-network" not found` | 持续报告网络插件找不到指定网络定义资源，频次高 (46次) |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason`: labels={container="app", reason="ContainerCreating"}, value=1, timestamp=2026-09-03T11:16:36.120000Z | 独立观测印证容器因处于 ContainerCreating 状态而处于等待 |

**证据关联说明：**
Kubernetes 事件与 Metric 共同锁定了容器的异常状态为 `ContainerCreating`。在事件维度，`FailedCreatePodSandBox` 与 `NoNetworkFound` 提供了因果全貌：Kubelet 尝试调用 Multus 插件创建网络时，因找不到 `aiops-case-05` 命名空间下的 `unavailable-network` 资源而报错，直接导致 Pod 无法完成启动。

## 🎯 根因分析 · g1

### 因果链

```text
缺失 NetworkAttachmentDefinition 资源 → Multus CNI 无法加载网络委托配置 → FailedCreatePodSandBox (kubelet 创建沙箱失败) → Pod 卡在 ContainerCreating 状态
```

### 根因结论

已确认的根因为 `aiops-case-05` 命名空间中缺失名为 `unavailable-network` 的 `NetworkAttachmentDefinition` 资源。Pod 启动时配置引用了该资源，导致 Multus CNI 插件在执行网络设置时因找不到目标定义而报错（见证据 #2, #3），进而造成 Pod Sandbox 创建失败，容器长时间处于 `ContainerCreating` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 6.7m
├─ 问题定位: 38.1s
├─ 并发证据采集: 352.8s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 352.8s (Evidence 344.3s, RCA 8.4s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-volume-mount-failed, pod-sandbox-create-failed
