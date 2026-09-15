## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod 配置了 Multus CNI 注解引用名为 'unavailable-network' 的 NetworkAttachmentDefinition，但该资源在 aiops-case-05 命名空间中不存在，导致 Multus 插件无法配置网络，进而引发 kubelet 创建 Pod Sandbox 失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes (Multus) | `NoNetworkFound`: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05) | 确认 Pod 配置了不存在的网络引用，导致 CNI 插件初始化失败 |
| 2 | K8s Event | Kubernetes (Kubelet) | `FailedCreatePodSandBox`: rpc error: code = Unknown desc = failed to setup network for sandbox: plugin type="multus" name="multus-cni-network" failed: cannot find a network-attachment-definition (unavailable-network)... not found | 确认网络插件失败直接导致 Pod 容器沙箱创建失败 |
| 3 | K8s State | Kubernetes (State) | `ContainerCreating`: container "app" 处于等待状态 | 对应上层网络插件失败导致的 Pod 调度停滞状态 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 值为 `1` (reason: `ContainerCreating`) | 量化确认了该容器处于等待网络/状态创建阶段的当前状态 |

**证据分析**：
Kubernetes Event 明确指出了 `NoNetworkFound` (fact-1) 和 `FailedCreatePodSandBox` (fact-2) 之间的直接因果关系。由于 Multus 插件找不到名为 `unavailable-network` 的 NetworkAttachmentDefinition，网络配置步骤中止，导致 Kubelet 无法创建沙箱，从而使得容器状态 (fact-3) 永久停留在 `ContainerCreating`。Metric 数据 (fact-4) 与 Event 状态一致，确认了当前等待的持续性。Logging/Tracing 因容器未启动而不可用，但 Event 级别的证据已足够闭环。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用了不存在的 NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 插件无法找到目标网络定义 → Kubelet 创建 Pod Sandbox 失败 (网络配置阶段报错) → Pod 状态卡在 ContainerCreating，容器未启动
```

### 根因结论

已确认根因为 **Pod 配置了不存在的网络依赖**。
证据表明，Pod 在 `aiops-case-05` 命名空间中请求了名为 `unavailable-network` 的 Multus 网络，但该 `NetworkAttachmentDefinition` 资源不存在 (fact-1)。这导致 Multus 插件在初始化网络时直接报错 (fact-2)，进而阻断了 Pod 沙箱的创建流程，使容器长期处于 `ContainerCreating` 状态 (fact-3, fact-4)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 23.0s
├─ 并发证据采集: 47.6s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 47.6s (Evidence 39.7s, RCA 7.7s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed, pod-sandbox-create-failed
