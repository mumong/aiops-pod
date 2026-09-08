## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod 在 aiops-case-05 命名空间中引用了不存在的 NetworkAttachmentDefinition 'unavailable-network'，导致 Multus CNI 无法创建网络沙箱，使容器卡死在 ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | 容器 `app` 处于 `waiting_reason: ContainerCreating` 状态 | 确认 Pod 卡死在容器创建阶段，尚未进入运行态 |
| 2 | K8s Event | multus (NoNetworkFound) | 连续报出 `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)`，覆盖过去 57 分钟以上 | 证明 Multus 在持续尝试加载网络沙箱时，因找不到目标网络定义而反复失败 |
| 3 | K8s Event | kubelet (FailedCreatePodSandBox) | `rpc error: code = Unknown desc = failed to setup network for sandbox... plugin type="multus"... error in getting k8s network for pod` | 确认底层 CNI 插件执行失败直接导致了 Pod Sandbox 无法创建，与 ContainerCreating 状态互为因果 |

**证据关联说明：**
- `fact-68e1589721d3`（ContainerCreating 状态）是结果表征；
- `fact-77c7c7c7c7c7` 等 `NoNetworkFound` 事件揭示了中间过程：Multus 找不到 `unavailable-network`；
- `fact-7322212624fb`（FailedCreatePodSandBox）是最终执行层的直接失败报错；
- 三者共同指向同一个缺失资源导致的容器启动阻塞。

## 🎯 根因分析 · g1

### 因果链
```text
引用不存在的 NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 无法解析网络委托配置 → 容器网络沙箱创建失败 (FailedCreatePodSandBox) → 容器状态卡死在 ContainerCreating
```

### 根因结论
已确认的根因是 **Pod 配置引用了未定义的 Multus 网络资源**。
Pod `aiops-case-05/workload-5dbb5dcd6c-nhd7v` 在其声明中指定了 NetworkAttachmentDefinition `unavailable-network`，但该资源在 `aiops-case-05` 命名空间中不存在。这导致 Multus CNI 插件在尝试为 Pod 建立网络环境时查找失败，进而引发 kubelet 创建 Pod Sandbox 报错，最终表现为容器长时间处于 `ContainerCreating` 状态。

支撑证据：
- `fact-68e1589721d3`：确认了容器处于 `ContainerCreating` 状态。
- `fact-7322212624fb`：kubelet 明确报告了 `multus` 插件失败及 `cannot find a network-attachment-definition` 错误。
- 多个 `NoNetworkFound` 事件（如 `fact-2ffbd4a24435`, `fact-321c171134ba` 等）持续验证了该网络定义缺失是当前的活跃错误。

---

## 📊 性能统计

```text
├─ 总耗时: 9.6m
├─ 问题定位: 24.0s
├─ 并发证据采集: 544.2s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 544.2s (Evidence 538.5s, RCA 5.6s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-volume-mount-failed, pod-imagepull-failed
