## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod spec 中定义的 ConfigMap volume 'input' 引用了 ConfigMap 'workload-input' 中不存在的 key 'unavailable-key'，且未标记为 optional，导致 kubelet 挂载卷持续失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning FailedMount`：`MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key` (fact-8172d5e7044a) | 直接证明 ConfigMap key 缺失导致挂载卷失败 |
| 2 | K8s State | Kubernetes | Pod 状态 `Pending`，容器 `app` 等待原因 `ContainerCreating` (fact-8b778e339b46, fact-a6dad8262207) | 描述故障表现：容器因挂载问题卡在启动阶段 |
| 3 | K8s State | Kubernetes | Pod 条件 `ContainersReady: False`，消息 `containers with unready status: [app]` (fact-3469800b7750) | 确认容器未就绪的直接状态 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1` (reason=ContainerCreating) (fact-bac134843177) | 通过指标证实容器持续处于 Waiting 状态 |

**证据总结：**
Kubernetes 事件明确记录了挂载失败的直接原因是引用了不存在的 ConfigMap key `unavailable-key`，这解释了为什么 Pod 处于 `Pending` 且容器状态为 `ContainerCreating` (fact-1, fact-2)。指标数据进一步佐证了容器持续处于等待状态而非运行或错误退出 (fact-4)。日志与 Tracing 因容器未启动不可用，但 Kubernetes 维度的状态与事件已构成闭环证据。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 定义了引用不存在 key 'unavailable-key' 的 ConfigMap volume → kubelet 挂载卷校验失败并持续重试 → Pod 卡在 Pending/ContainerCreating 阶段 → 容器无法启动
```

### 根因结论

**已确认的根因**：Pod 的卷配置错误地引用了 ConfigMap `workload-input` 中不存在的 key `unavailable-key`，且未标记为 `optional`。

**证据支撑**：
- **Kubernetes 事件 (fact-1)** 明确指出 `configmap references non-existent config key: unavailable-key`，这是导致挂载失败的唯一具体错误信息。
- **Kubernetes 状态 (fact-2, fact-3)** 显示 Pod 因挂载失败卡在 `Pending`，容器处于 `ContainerCreating` 状态。
- **Metric (fact-4)** 确认了等待状态的持续性。

该配置错误直接导致 kubelet 无法完成卷挂载，进而阻塞了容器的启动过程。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 47.9s
├─ 并发证据采集: 46.7s
│  └─ g1 aiops-case-v05/workload: 46.7s (Evidence 40.7s, RCA 5.9s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-imagepull-failed, pod-volume-mount-failed
