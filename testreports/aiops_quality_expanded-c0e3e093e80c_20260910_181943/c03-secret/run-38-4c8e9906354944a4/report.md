## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod `aiops-case-v04/workload` 卡在 `ContainerCreating` (Pending) 状态，无法启动容器。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `fact-43389e7f479c`: "Warning FailedMount... MountVolume.SetUp failed for volume \"input\" : secret \"unavailable-input\" not found" (x33 over 54m) | 直接证据：表明 Pod 试图挂载的 Secret 不存在，是导致挂载失败的直接原因 |
| 2 | K8s Event | kubernetes | `fact-9dc7e04005e9`: "Warning FailedMount... timed out waiting for the condition" (x20 over 52m) | 佐证：kubelet 在找不到 Secret 后持续重试，最终触发超时等待，阻碍容器创建 |
| 3 | K8s State | kubernetes | `fact-73d27b129115`: `container.waiting_reason` = "ContainerCreating" | 症状确认：Pod 处于挂载准备阶段，与 MountVolume 失败事件时间线一致 |
| 4 | K8s State | kubernetes | `fact-62f73f585159`: `pod.status` = "Pending" | 症状确认：Pod 整体处于 Pending 状态，未进入运行阶段 |
| 5 | Metric | prometheus | `fact-f54ba44f3845`: `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}` = 1 | 指标佐证：验证了容器处于等待创建状态的事实，与 K8s 状态一致 |

**证据互证说明：**
事实 1 提供了挂载失败的根本原因（Secret 缺失），事实 2 说明了该错误导致了 kubelet 的持续重试和超时。事实 3 和 4 从 Pod 状态（ContainerCreating/Pending）在宏观层面印证了挂载阻塞导致容器无法启动的结果。事实 5 的 Metrics 数据独立确认了这一等待状态，与 K8s 事件流相互印证，排除了短暂网络波动可能导致的临时假死。

## 🎯 根因分析 · g1

### 因果链

```text
Secret unavailable-input 不存在 → MountVolume.SetUp failed → timed out waiting for condition → 阻塞容器创建
```

### 根因结论

**已确认的根因：** Pod 定义中引用的 Secret `unavailable-input` 不存在。

**根因分析：**
1.  **核心错误**：Kubernetes 事件（事实 1）明确指出 `MountVolume.SetUp failed` 的原因是 `secret "unavailable-input" not found`。由于该 Volume 配置未设置为可选挂载（Optional），Kubelet 在启动阶段无法完成卷挂载。
2.  **阻塞机制**：Kubelet 持续重试挂载操作（事实 2 显示 54 分钟内尝试了 53 次），最终触发超时等待（timed out）。这导致 Pod 始终无法进入容器初始化阶段。
3.  **状态表现**：Pod 状态锁定在 `ContainerCreating`（事实 3）和 `Pending`（事实 4），Metrics 数据（事实 5）也确认了该等待状态。由于容器未能启动，没有日志和 Trace 数据产生，符合预期。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.0s
├─ 并发证据采集: 36.6s
│  └─ g1 aiops-case-v04/workload: 36.6s (Evidence 28.9s, RCA 7.6s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-sandbox-create-failed
