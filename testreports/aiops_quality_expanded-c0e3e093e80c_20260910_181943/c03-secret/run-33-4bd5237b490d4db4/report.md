## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod 'aiops-case-v04/workload' 定义中引用了不存在的 Secret 'unavailable-input' (Optional=false)，导致 kubelet 挂载卷 'input' 失败，容器无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found` (fact-7e033d12eac5) | 直接证明 Pod 定义中引用的 Secret 不存在，导致卷挂载失败 |
| 2 | K8s State | kubernetes | 容器 `app` 状态为 `ContainerCreating`，Pod 处于 `Pending` 且 `ContainersReady=False` (fact-c3095df671e2, fact-8188557bee0d) | 确认容器因前置卷依赖失败而卡在启动前的等待状态 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}` 值为 `1` (fact-25917507a5be) | 从监控指标侧印证容器正处于等待状态，与 K8s 状态一致 |
| 4 | K8s State | kubernetes | 容器 `app` 重启次数 `restart_count=0` (fact-0042f9c7380a) | 证明容器从未真正启动运行过，排除了运行时崩溃导致的等待 |

证据说明：
- **证据 1 与 证据 2 因果互补**：`failedMount` 事件（证据 1）给出了容器卡在 `ContainerCreating`（证据 2）的确切技术原因，即 Secret 缺失导致的挂载阶段阻断。
- **证据 3 验证了等待状态**：Prometheus 的 `waiting_reason` 指标（证据 3）独立验证了容器处于非运行状态，且原因与 `ContainerCreating` 事件匹配。
- **证据 4 排除了运行时故障**：重启次数为 0（证据 4）确认故障发生在容器启动前（挂载阶段），而非容器启动后的应用层崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
Spec 定义 Volume 'input' 引用不存在的 Secret 'unavailable-input' → kubelet 挂载卷阶段失败 (MountVolume.SetUp failed) → 容器无法进入 Running 状态，卡在 ContainerCreating → Pod 持续处于 Pending 状态
```

### 根因结论

**已确认的根因**：Pod 定义中引用了一个不存在的 Secret (`unavailable-input`)。
这一事实通过 K8s Event (`secret "unavailable-input" not found`) 直接确证（证据 1），该事件触发了挂载失败机制，导致容器停留在 `ContainerCreating` 阶段（证据 2）。监控数据（证据 3）和重启计数（证据 4）作为补充证据，分别独立印证了容器的等待状态和启动前的故障阶段，形成了完整的证据闭环。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 31.5s
├─ 并发证据采集: 46.2s
│  └─ g1 aiops-case-v04/workload: 46.2s (Evidence 39.4s, RCA 6.4s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-imagepull-failed, pod-volume-mount-failed
