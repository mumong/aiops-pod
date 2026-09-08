## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-kbwsx 的注解引用了命名空间 'aiops-case-05' 中不存在的 NetworkAttachmentDefinition 'unavailable-network'，导致 Multus CNI 插件无法找到网络配置，进而引发 FailedCreatePodSandBox 错误，使 Pod 停留在 ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | multus | `Warning NoNetworkFound ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (记录 46 条，持续时间 58m) | 确认 Multus CNI 插件持续因找不到网络配置而报错，是引发沙箱创建失败的根本触发条件 |
| 2 | K8s Event | kubelet | `Warning FailedCreatePodSandBox ... rpc error: code = Unknown desc = failed to setup network ... plugin type="multus" name="multus-cni-network" failed (add)` | 确认 Multus 网络初始化失败导致了底层容器沙箱无法创建 |
| 3 | K8s State | kubernetes | 容器 `app` 状态：`ContainerCreating` (原因: `ContainerCreating`) | 确认 Pod 由于网络初始化阻塞停留在等待阶段，未进入运行状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"}` = 1 (单样本) | 通过监控系统确认当前等待原因为 ContainerCreating，与 K8s 状态一致 |

**证据交叉印证说明：**
K8s Event 中的 `NoNetworkFound` (证据 #1) 和 `FailedCreatePodSandBox` (证据 #2) 构成了完整的因果链：由于找不到 `unavailable-network` 定义，导致 Multus 插件失败，进而导致 kubelet 无法创建沙箱。K8s State (证据 #3) 和 Metric (证据 #4) 作为状态验证，确认了 Pod 因上述网络配置缺失而卡在 `ContainerCreating` 阶段。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 注解引用了不存在的 NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 插件无法找到网络配置 (NoNetworkFound) → 容器运行时无法创建 Pod 沙箱 (FailedCreatePodSandBox) → Pod 停滞在 ContainerCreating 状态
```

### 根因结论
**已确认的根因**：Pod `aiops-case-05/workload-5dbb5dcd6c-kbwsx` 的注解引用了命名空间 `aiops-case-05` 中不存在的 NetworkAttachmentDefinition 资源 `unavailable-network`。这导致 Multus CNI 插件无法拉取网络配置，进而引发 `FailedCreatePodSandBox` 错误，使 Pod 卡在 `ContainerCreating` 状态（证据 #1, #2, #3）。

**未知项**：现有证据确认了配置缺失的现象，但无法确定该 NetworkAttachmentDefinition 资源 `unavailable-network` 缺失的根本原因（例如：是否被误删、从未创建，或者是配置拼写错误）。

---

## 📊 性能统计

```text
├─ 总耗时: 6.5m
├─ 问题定位: 29.6s
├─ 并发证据采集: 350.7s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 350.7s (Evidence 340.6s, RCA 9.9s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-volume-mount-failed
