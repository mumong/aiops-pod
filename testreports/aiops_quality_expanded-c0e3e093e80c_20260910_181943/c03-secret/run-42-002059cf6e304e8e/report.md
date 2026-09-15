## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod workload 持续处于 ContainerCreating (Pending) 状态，因卷挂载失败而阻塞。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `FailedMount ... MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found` | 明确指出 Pod 因无法找到 Secret 'unavailable-input' 导致挂载失败 |
| 2 | K8s State | Kubernetes | `container.waiting_reason`: `ContainerCreating`; `pod.phase`: `Pending` | 确认 Pod 阻塞在启动前的挂载阶段，未进入运行态 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}` = `1` | 独立观测确认容器等待原因与 K8s 状态一致 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = `0` | 确认容器未启动过，排除了启动后崩溃退出的可能性 |

**证据印证说明：**
K8s 事件 (fact-2e76b269ec5e) 提供了根本原因的定性描述（Secret 缺失），这与 K8s 状态 (fact-2d303e9e6eb5) 和 Prometheus 指标 (fact-8e96b5f72547) 的定量观测相互印证。由于指标重启计数 (fact-47cfaa42621b) 为 0，证实了故障发生在容器生命周期启动之前，而非运行中。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 'unavailable-input' 缺失 → 挂载卷 'input' 失败 → 容器启动阻塞，状态保持 ContainerCreating → Pod 处于 Pending 状态
```

### 根因结论

已确认根因为：Pod 定义中引用的 Secret `unavailable-input` 在命名空间 `aiops-case-v04` 中不存在。

**证据引用：**
- K8s Event (fact-2e76b269ec5e) 直接指出 `secret "unavailable-input" not found`。
- K8s 状态 (fact-1e8d83b19c62, fact-5ffb16edb4a9) 验证了由此导致的 Pod 阻塞现象。

现有证据已充分构成因果链闭环，无需补充决定性事实。

---

## 📊 性能统计

```text
├─ 总耗时: 58.2s
├─ 问题定位: 16.8s
├─ 并发证据采集: 33.6s
│  └─ g1 aiops-case-v04/workload: 33.6s (Evidence 26.9s, RCA 6.6s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-volume-mount-failed
