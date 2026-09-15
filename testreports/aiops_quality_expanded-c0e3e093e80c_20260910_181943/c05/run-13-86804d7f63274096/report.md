## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod 被错误配置为引用不存在的 Multus 网络附加定义 'unavailable-network'，导致 CNI 插件无法创建网络沙箱，使 Pod 持续卡在 ContainerCreating 阶段。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` | `container`: `app`, `waiting_reason`: `ContainerCreating` (fact_id: `fact-a653433c600d`) | 确认应用容器 `app` 卡在容器创建阶段，未完成启动。 |
| 2 | K8s Event | `multus` | `NoNetworkFound`: `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (fact_id: `fact-0161fde73e2f`) | 明确指出 `multus` 插件找不到预期的网络附加定义 `unavailable-network`。 |
| 3 | K8s Event | `kubelet` | `FailedCreatePodSandBox`: `failed to setup network for sandbox ... plugin type="multus" ... getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (fact_id: `fact-01689fabf5a5`) | 提供失败机制的具体细节，确认底层原因是 Multus 在尝试加载 K8s delegates 时失败。 |
| 4 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason` = `1` (reason: `ContainerCreating`, fact_id: `fact-bf13021a19e7`) | 量化确认该 Pod 处于 `ContainerCreating` 等待状态（单一样本，持续状态）。 |

**证据综合分析：**
Kubernetes State 和 Metric 事实共同印证了 Pod 处于 `ContainerCreating` 状态 [1, 4]。K8s Event 事实 [2, 3] 直接揭示了阻塞该状态的机制：`multus` CNI 插件在初始化网络沙箱时，因为找不到名为 `unavailable-network` 的 `network-attachment-definition` 而报错，导致 `kubelet` 的 `FailedCreatePodSandBox`。这些证据链式闭合，排除了节点资源或镜像拉取等其他常见原因。Logging 和 Tracing 维度因容器未启动被判定为不相关，与当前网络配置错误导致的阻塞现象一致。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 注解配置了不存在的网络定义 'unavailable-network' → Multus CNI 插件在初始化时无法解析该定义 → Kubelet 创建 Pod 沙箱失败 (FailedCreatePodSandBox) → Pod 停留在 ContainerCreating 状态
```

### 根因结论

**已确认的根因：**
Pod `aiops-case-05/workload-5dbb5dcd6c-bntfh` 被错误配置为引用一个不存在的 Multus 网络附加定义（NetworkAttachmentDefinition）`unavailable-network`。
**影响机制：**
当 `kubelet` 尝试启动容器时，调用 `multus` CNI 插件配置网络。由于该网络定义在 `aiops-case-05` 命名空间中不存在，Multus 返回 `getKubernetesDelegate` 失败，导致 `FailedCreatePodSandBox` 错误（参考证据 [3]）。由于网络沙箱无法创建，Pod 被永远卡死在 `ContainerCreating` 状态（参考证据 [1, 2, 4]）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 12.9s
├─ 并发证据采集: 47.3s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 47.3s (Evidence 38.6s, RCA 8.6s)
└─ 汇总总结: 11.5s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-imagepull-failed, pod-sandbox-create-failed
