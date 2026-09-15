## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-bntfh 在 Pod Spec 中配置了引用 'unavailable-network' 的 Multus 网络附件，但该 NetworkAttachmentDefinition 资源在目标 namespace aiops-case-05 中不存在，导致 Multus CNI 插件在创建 Pod 沙箱时失败，Pod 持续处于 ContainerCreating/Pending 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: `ContainerCreating` (container: app) | 确认 Pod 卡在容器启动阶段，未进入 Running 状态 |
| 2 | K8s Event | kubelet | `FailedCreatePodSandBox`: `failed to setup network for sandbox "...": plugin type="multus" name="multus-cni-network" failed (add)` | 直接定位到 Multus CNI 插件在创建 Pod 沙箱网络时失败 |
| 3 | K8s Event | multus | `NoNetworkFound`: `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 明确缺失资源为 `unavailable-network`，且该资源在 `aiops-case-05` 命名空间中不存在 |

证据 2 和证据 3 共同指向同一失败路径：Multus 插件尝试加载网络定义失败。证据 3 提供了根本缺失项的具体名称（`unavailable-network`）及所在命名空间，解释了证据 2 中 CNI 插件报错的具体原因。证据 1 的状态与 CNI 初始化失败直接对应，形成完整证据链。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 配置引用不存在的网络资源 → Multus CNI 插件无法找到 network-attachment-definition → 创建 Pod 沙箱网络失败 (FailedCreatePodSandBox) → Pod 持续处于 ContainerCreating 状态
```

### 根因结论

已确认根因为：Pod `aiops-case-05/workload-5dbb5dcd6c-bntfh` 的规格中配置了 Multus 网络附件引用了名为 `unavailable-network` 的 `NetworkAttachmentDefinition` 资源，但该资源在目标命名空间 `aiops-case-05` 中不存在（证据 #3）。这导致 Multus CNI 插件在初始化网络时因找不到定义而报错（证据 #2），最终致使 Pod 无法正常创建沙箱，卡在 `ContainerCreating` 状态（证据 #1）。现有证据充分，逻辑闭环完整。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 33.5s
├─ 并发证据采集: 47.9s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 47.9s (Evidence 40.3s, RCA 7.4s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed
