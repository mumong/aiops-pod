## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | aiops-case-v04/workload pod stuck in ContainerCreating (Pending) due to volume mount failure |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | Warning FailedMount: MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found | 明确指出挂载失败的原因是 Secret 资源缺失，构成直接证据 |
| 2 | K8s State | kubernetes | pod.phase: Pending; container.waiting_reason: ContainerCreating | 确认 Pod 因前置依赖未就绪而处于等待状态，未发生重启 |
| 3 | K8s Config | kubernetes | container.resource_request: memory=8Mi, cpu=5m; limits: memory=32Mi, cpu=50m | 资源请求极低，排除因资源不足导致 Pending 的可能 |
| 4 | Metric | prometheus | kube_pod_container_status_waiting_reason: 1 (ContainerCreating); kube_pod_container_status_restarts_total: 0 | 指标层面证实容器持续处于等待状态且无重启行为，印证了启动阶段阻塞 |

**证据关系说明**
- `fact-c7cf7fda3bb0` (Event) 提供了确切的失败原因（找不到 Secret `unavailable-input`），解释了为何 Pod 停留在 `Pending` 状态。
- `fact-55a9b7de2191` (State) 与 `fact-6adc0dc6a276` (Metric) 分别从集群状态和控制平面指标两个维度确认了 Pod 正处于等待中，且没有发生 CrashLoopBackOff，与“启动阶段被阻塞”的现象一致。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 'unavailable-input' 在 aiops-case-v04 中不存在 → kubelet 尝试挂载 volume 'input' 失败 → 挂载失败导致容器无法启动 → Pod 持续处于 Pending/ContainerCreating 状态
```

### 根因结论

已确认根因：Pod 规范中引用了不存在的 Secret `unavailable-input` 作为 Volume，且未将 `optional: true` 设置为允许缺失。这导致 `kubelet` 在挂载卷阶段失败，无法启动 `app` 容器。

相关证据：
- `fact-c7cf7fda3bb0`：Event 明确记录 `secret "unavailable-input" not found`。
- `fact-47454abcf2fb`：容器状态为 `ContainerCreating`。
- `fact-55a9b7de2191`：Pod 处于 `Pending` 阶段。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 23.8s
├─ 并发证据采集: 47.2s
│  └─ g1 aiops-case-v04/workload: 47.2s (Evidence 36.8s, RCA 10.3s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-imagepull-failed, pod-volume-mount-failed, pod-sandbox-create-failed, pod-config-error
