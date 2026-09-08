## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-kbwsx stuck in ContainerCreating (Pending) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `fact-accfcf205091`: `ContainerCreating` (Container: app) | 确认 Pod 当前停滞在容器启动等待阶段 |
| 2 | K8s Event | kubernetes | `fact-14792d1e6ff2`: `FailedCreatePodSandBox` (Multus error, 出现 x335, 持续 75m) | 提供导致容器无法启动的直接故障堆栈 |
| 3 | K8s Event | kubernetes | `fact-bd c2630521d5` 等 45 条 `NoNetworkFound` (间隔数秒至数分钟) | 证明 Multus 在启动窗口期内持续且一致地找不到网络配置 |
| 4 | Metric | prometheus | `fact-d357127fe1c8`: `kube_pod_container_status_waiting_reason` = 1, reason=`ContainerCreating` | 独立指标确认 Pod 处于 `ContainerCreating` 状态且原因符合预期 |

上述证据相互印证：Metric 确认了整体状态，K8s 状态验证了该状态的持续性，而 Event 记录了导致该状态的重复性具体错误。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用不存在的 NAD 'unavailable-network' → Multus 查找失败 [K8s Event #2, #3] → FailedCreatePodSandBox 失败，容器无法创建 [K8s Event #2] → Pod 卡在 ContainerCreating 状态 [K8s State #1, Metric #4]
```

### 根因结论

已确认根因为：Pod `aiops-case-05/workload-5dbb5dcd6c-kbwsx` 的 Spec 定义了一个名为 `unavailable-network` 的网络附件定义（NetworkAttachmentDefinition），但 Multus CNI 插件在尝试挂载网络时无法在 `aiops-case-05` 命名空间中找到该定义（**K8s Event #2, #3**）。这一配置缺失导致 Multus 返回错误并阻止了 Pod Sandbox 的创建，致使容器始终处于等待状态（**K8s State #1, Metric #4**）。

根据输入事实，关于该 NAD 是否在其他命名空间存在的信息未被提供（unknowns 标记）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 41.2s
├─ 并发证据采集: 49.3s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 49.3s (Evidence 41.7s, RCA 7.4s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-imagepull-failed
