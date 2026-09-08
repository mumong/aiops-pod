## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod 注解引用了不存在的 NetworkAttachmentDefinition 'unavailable-network'，导致 multus CNI 插件无法配置网络，进而致使 kubelet 无法创建 Pod Sandbox。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubernetes` (fact-1453b9426b8d) | `Warning FailedCreatePodSandBox kubelet ... Failed to create pod sandbox: rpc error... plugin type="multus" name="multus-cni-network" failed (add) ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 直接失败：Kubelet 尝试创建 Pod Sandbox 时，Multus CNI 插件因找不到指定网络定义而抛出致命错误 |
| 2 | K8s Event | `kubernetes` (fact-0426a7827aeb) | `Warning NoNetworkFound multus ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` | 核心根因：多实例记录确认 Namespace `aiops-case-05` 中不存在名为 `unavailable-network` 的网络资源 |
| 3 | K8s State | `kubernetes` (fact-9ca6570de2cd) | `container: app, reason: ContainerCreating` | 当前状态：Pod 处于等待网络配置完成的停滞状态 |

**证据关联：**
事件 `fact-1453b9426b8d` 描述的 Sandbox 创建失败机制，其错误堆栈中明确指向了 `fact-0426a7827aeb` 所记录的同一资源缺失问题。`fact-0426a7827aeb` 与同组的其它 `NoNetworkFound` 事件（如 `fact-06f9d0fb6c9b` 等）在时间上呈现持续性（如 22m, 15m, 27m 等时间戳），印证了该网络定义缺失是持续存在的配置错误，直接导致了 `ContainerCreating` 状态的停滞。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用了不存在的网络定义 (unavailable-network) → Multus CNI 插件无法获取网络资源 → Kubelet 创建 Pod Sandbox 失败 (FailedCreatePodSandBox) → 容器状态卡在 ContainerCreating
```

### 根因结论

**已确认的根因：**
`aiops-case-05` 命名空间下的 Pod `workload-5dbb5dcd6c-nhd7v` 配置中引用了一个名为 `unavailable-network` 的 NetworkAttachmentDefinition。证据表明（见证据 #2），该资源在命名空间中不存在。

**结论支撑：**
1.  **资源缺失**：Kubernetes 事件日志（`NoNetworkFound`）明确指示 `network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found`，且该错误在观察窗口内多次发生。
2.  **故障传递**：Kubelet 事件日志（`FailedCreatePodSandBox`）确认 Multus 插件在初始化网络时因找不到上述定义而抛出 RPC 错误，这直接导致了 Pod Sandbox 的创建失败。
3.  **状态印证**：Pod 实体状态为 `ContainerCreating`，与上述配置错误导致的容器无法启动现象一致。

现有证据足以支撑上述结论，无需更多数据即可确认此异常。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 24.1s
├─ 并发证据采集: 40.2s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 40.2s (Evidence 34.8s, RCA 5.2s)
└─ 汇总总结: 11.9s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-volume-mount-failed, pod-sandbox-create-failed
