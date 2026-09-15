## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | aiops-case-v04/workload Pod 处于 ContainerCreating/Pending 状态，容器未启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedMount`: "Warning FailedMount 11m (x23 over 42m) kubelet MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found" (fact-cfef60c1a1b1) | 证实卷挂载失败的确切原因是 Secret 缺失，直接导致容器无法启动 |
| 2 | K8s State | kubernetes | `pod.status: Pending`, `status: ContainerCreating` (fact-6a81d20dbc34) | 描述 Pod 当前的阻塞状态，与 Mount 失败的现象一致 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason = 1` (reason: ContainerCreating) (fact-54524a6a4e95) | 独立观测容器始终处于等待阶段，无重启记录 (value=0, fact-41bc6703c79f) |

上述证据均指向同一结论：Kubernetes 调度成功但由于依赖资源（Secret）不可用，导致挂载阶段永久阻塞，容器未能进入运行或重启状态。

## 🎯 根因分析 · g1

### 因果链
```text
Pod Spec 引用不存在的 Secret 'unavailable-input' (非可选卷) → kubelet 尝试挂载失败 (secret not found) → FailedMount 持续警告 → Pod 卡在 Pending/ContainerCreating 状态，应用未运行
```

### 根因结论
已确认的根因：`Pod` 的 `Spec` 中配置了名为 `input` 的卷挂载，该卷指向不存在的 Secret `unavailable-input`。由于引用未设为可选（`Optional: false`），`kubelet` 在卷挂载阶段阻塞，导致 Pod 无法启动。证据 [1] 的事件日志和 [3] 的等待指标一致证实了这一机制。

---

## 📊 性能统计

```text
├─ 总耗时: 51.3s
├─ 问题定位: 17.6s
├─ 并发证据采集: 26.9s
│  └─ g1 aiops-case-v04/workload: 26.9s (Evidence 19.2s, RCA 7.5s)
└─ 汇总总结: 6.7s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-volume-mount-failed
