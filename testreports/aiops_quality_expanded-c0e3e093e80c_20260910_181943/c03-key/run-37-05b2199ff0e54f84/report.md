## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod aiops-case-v05/workload 卡在 ContainerCreating/Pending 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-v05/workload` 状态为 `Pending` (fact-4513e7e7a220)，容器 `app` 状态为 `ContainerCreating` (fact-77f967bf8120)，重启次数为 0 (fact-893262227a2e)。 | 确认故障发生在启动前阶段，且无重启波动。 |
| 2 | K8s Event | Kubernetes | `Warning FailedMount` (fact-9c55af686031): `MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key`。 | **直接因果证据**：指明挂载失败的具体原因。 |
| 3 | K8s Event | Kubernetes | `Warning FailedMount` (fact-a3bf03fbd096): `timed out waiting for the condition`，持续 52 分钟以上 (x20 over 52m)。 | 确认失败是持续性的，导致 Pod 长期处于阻塞状态。 |
| 4 | K8s Config | Kubernetes | 容器 `app` 内存限制 `32Mi` (fact-0761a6941354)，CPU 限制 `50m` (fact-104392c8bb5f)。 | 排除资源硬限制导致的 OOMKilled 或限流问题。 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 为 1，标签 `reason: ContainerCreating` (fact-1365ea1adaa8)。 | 量化证实容器处于等待启动状态，与 K8s 状态一致。 |
| 6 | Metric | Prometheus | `kube_pod_status_phase` 为 1，标签 `phase: Pending` (fact-0c2684d8a995)。 | 从集群层面确认 Pod 整体未进入运行状态。 |

**证据说明：**
1. K8s Event (`#2`) 中的具体错误原文 `configmap references non-existent config key: unavailable-key` 解释了为何 Volume `input` 无法挂载，这是导致 `#1` 中 `ContainerCreating` 状态的直接机制。
2. Metric (`#5`) 和 K8s State (`#1`) 互相印证了当前故障停留在挂载等待阶段，且重启计数为 0 (`#1`) 表明容器从未进入运行态。

## 🎯 根因分析 · g1

### 因果链
```text
Pod spec 配置引用了不存在的 ConfigMap key `unavailable-key` → Kubelet 挂载 Volume `input` 时校验失败 (FailedMount) → 挂载持续超时且无法就绪 → 容器 `app` 卡在 ContainerCreating 状态，Pod 处于 Pending
```

### 根因结论
**已确认的根因**：Pod `aiops-case-v05/workload` 的 Volume `input` 引用了 ConfigMap 中不存在的 Key `unavailable-key`，导致 Kubelet 无法挂载卷。

- **证据支持**：
  - 事件日志 (`#2`) 明确指出 `configmap references non-existent config key: unavailable-key` 以及 `MountVolume.SetUp failed`。
  - 事件日志 (`#3`) 证实该失败已持续 52 分钟以上，属于持续性阻塞。
- **结论**：资源定义错误导致存储挂载失败，进而使容器无法启动。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 17.0s
├─ 并发证据采集: 50.2s
│  └─ g1 aiops-case-v05/workload: 50.2s (Evidence 42.5s, RCA 7.6s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-volume-mount-failed
