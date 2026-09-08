## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod 配置引用了不存在的 Multus NetworkAttachmentDefinition 'unavailable-network'，导致 Multus 插件无法为 Pod 创建网络沙箱（CNI setup failed），进而使 kubelet 无法启动容器，Pod 卡在 ContainerCreating/Pending 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | Warning NoNetworkFound: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found | 明确证实 Pod 引用了未定义的 Multus 网络资源 |
| 2 | K8s Event | kubernetes | Warning FailedCreatePodSandBox: failed to setup network for sandbox "cbb3642bde1cf3127161add39b393513dbd1ae5b0811fa892a4d4aec7a95e63c": plugin type="multus" name="multus-cni-network" failed (add) | 证实 CNI 插件因上述缺失依赖导致网络沙箱创建失败 |
| 3 | K8s State | kubernetes | Pod `aiops-case-05/workload-5dbb5dcd6c-kbwsx` 状态: ContainerCreating | 证实容器因 CNI 准备失败而处于阻塞状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` value="1", reason="ContainerCreating" | 从指标层确认 Pod 处于因等待资源（此处为网络配置）而被挂起的等待状态 |

**证据说明：**
- **K8s Event (1, 2)** 构成了完整的因果链条：缺少 `unavailable-network` 定义（事实 1）直接导致了 Multus 插件调用失败（事实 2）。
- **K8s State (3)** 验证了上述网络错误对 Pod 生命周期的最终影响，即 Pod 无法推进到 Running 状态。
- **Metric (4)** 提供了指标视角的佐证，确认了 `ContainerCreating` 是一个持续的等待状态，而非临时波动。
- 日志与追踪未采集（因容器未启动），但 K8s 核心事件与指标已足以形成闭环。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义引用了不存在的 NetworkAttachmentDefinition 'unavailable-network' (K8s State/Config) 
→ Multus CNI 插件调用失败，无法创建网络沙箱 (K8s Event) 
→ kubelet 无法完成 Pod 容器初始化 (K8s State) 
→ Pod 永久卡在 ContainerCreating 状态 (User Phenomenon)
```

### 根因结论

已确认根因为 **Pod 配置错误引用了不存在的 Multus 网络附件定义**。

集群中的 Pod `aiops-case-05/workload-5dbb5dcd6c-kbwsx` 在 Spec 中配置了名为 `unavailable-network` 的网络挂载，但该资源在 `aiops-case-05` 命名空间中并不存在。这导致 Kubernetes 调度器尝试通过 Multus CNI 插件创建网络时，插件因找不到目标定义而报错（`NoNetworkFound`），进而引发 `FailedCreatePodSandBox` 事件。由于网络配置是容器启动的前置条件，Pod 被永久阻塞在 `ContainerCreating` 状态，表现为 `ContainerCreating` 指标持续为 1。现有 K8s 事件与指标证据充分，排除其他资源瓶颈可能。

---

## 📊 性能统计

```text
├─ 总耗时: 10.2m
├─ 问题定位: 32.3s
├─ 并发证据采集: 569.1s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 569.1s (Evidence 563.8s, RCA 5.1s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- 未调用 Runbook
