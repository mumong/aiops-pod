## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Multus CNI 插件在 aiops-case-05 命名空间中查找 annotation 指定的 'unavailable-network' NetworkAttachmentDefinition 资源时失败（资源不存在），导致 Pod 沙箱创建持续失败并维持在 ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kube-system/kubernetes` | `container.waiting_reason`: `ContainerCreating` (container: app) | 确认 Pod 处于持续等待状态，未进入运行。 |
| 2 | K8s Event | `multus` | `NoNetworkFound`: `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (58m - 3m1s 间 36 次触发) | 证明 Multus CNI 插件反复尝试查找指定网络定义但失败，且缺失该资源。 |
| 3 | K8s Event | `kubelet` | `FailedCreatePodSandBox`: `failed to setup network for sandbox ... plugin type="multus" ... failed getting the delegate ... "unavailable-network" not found` (58m - 16s 间多次触发) | 确认底层沙箱创建因 Multus 插件返回网络查找错误而失败，导致容器无法启动。 |
| 4 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason`: `1` (labels: `reason="ContainerCreating"`) | 提供容器状态为 `ContainerCreating` 的时序观测，佐证容器未启动的持续状态。 |

**证据分析：**
1. **状态与事件的因果闭环**：Pod 维持在 `ContainerCreating` 状态（证据1），由 Kubelet 报告沙箱创建失败（证据3）直接导致。
2. **错误归因确认**：Kubelet 明确报错 CNI 插件类型为 `multus`，且 Multus 插件自身的 Event（证据2）明确指出了失败原因是找不到 `aiops-case-05` 命名空间下的 `unavailable-network` 网络定义。
3. **一致性**：Metric 观测到的等待状态（证据4）与事件记录的时间跨度一致，确认为当前持续发生的异常。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用不存在的 'unavailable-network' 网络定义 → Multus CNI 插件在 API Server 查找 CRD 资源失败 → 容器网络插件初始化 (CNI ADD) 报错 → Pod 沙箱创建失败，维持 ContainerCreating 状态
```

### 根因结论

**已确认的根因：**
Pod 配置中引用的 NetworkAttachmentDefinition 资源 `'unavailable-network'` 在 `aiops-case-05` 命名空间中不存在（[证据2](#evidence-2)、[证据3](#evidence-3)）。Multus CNI 插件在初始化网络时无法获取该定义，直接导致底层网络沙箱创建失败，使 Pod 无法脱离 `ContainerCreating` 状态。

**未知信息：**
- `'unavailable-network'` 资源缺失的具体原因（如：资源未创建、名称拼写错误或已被删除）未在日志或事件中体现。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 41.6s
├─ 并发证据采集: 55.3s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 55.3s (Evidence 47.2s, RCA 7.8s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-volume-mount-failed
