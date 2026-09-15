## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod workload-5b5fc86c8c-xn974 处于 ContainerCreating/Pending 状态，容器无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | Kubernetes | `container.resource_limit.memory: 32Mi`, `cpu: 50m` | 排除资源限制导致容器启动失败的可能性，证明配置合理。 |
| 2 | K8s Config | Kubernetes | `container.resource_request.memory: 8Mi`, `cpu: 5m` | 证明调度所需的请求量较小，排除了资源不足导致的调度阻塞。 |
| 3 | K8s Event | Kubernetes | `FailedMount: MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 直接证据：明确指出了 Pod 处于挂载卷失败状态的原因（ConfigMap 缺失）。 |
| 4 | K8s Event | Kubernetes | `FailedMount: Unable to attach or mount volumes: unmounted volumes=[input]... timed out waiting for the condition` | 辅助证据：证实挂载动作长期处于等待状态且多次重试失败。 |
| 5 | K8s State | Kubernetes | `pod.status: Pending` | 证实 Pod 当前状态停滞，未进入运行期。 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason = 1` (reason=ContainerCreating) | 指标验证：与 K8s 事件中的 `ContainerCreating` 状态完全对应。 |
| 7 | Metric | Prometheus | `kube_pod_container_status_restarts_total = 0` | 排除因容器崩溃反复重启的问题，证明问题发生于启动前阶段。 |

**证据印证说明：**
- **证据 1-2 vs 证据 3-4**：资源请求与限制正常，排除了资源瓶颈，而 K8s 事件明确指向了外部依赖（ConfigMap）的缺失，将故障范围锁定在配置引用错误。
- **证据 3 vs 证据 6**：Metric 确认了容器处于 `ContainerCreating` 状态，而 Event 揭示了造成该状态停滞的具体技术原因，两者因果逻辑闭环。
- **日志/Trace 不可用说明**：由于容器未能成功启动，物理上未产生应用日志与业务 Trace，因此 `Logging` 与 `Tracing` 维度的 `not_applicable` 状态符合故障现象，不影响当前根因判断。

## 🎯 根因分析 · g1

### 因果链

```text
Pod YAML 引用了不存在的 ConfigMap 'unavailable-config' → Kubelet 尝试挂载名为 'input' 的卷失败并无限期重试 → Pod 状态持续为 Pending/ContainerCreating，等待挂载超时 → 应用容器无法启动，呈现 ContainerCreating 状态且无重启记录
```

### 根因结论

已确认根因：**Pod 定义中错误引用了不存在的 ConfigMap 'unavailable-config'，且该卷配置为必填，导致 Kubelet 挂载卷失败。**

该根因由以下事实支撑（见证据表）：
- **直接错误**：K8s Event 明确报出 `MountVolume.SetUp failed ... configmap "unavailable-config" not found`（证据 3）。
- **状态一致性**：Pod 处于 `Pending` 且 `restart_count` 为 0（证据 5, 7），说明故障发生在容器进程启动之前，与挂载失败的现象完全吻合。
- **环境合理性**：资源请求与限制配置正常（证据 1, 2），排除了其他常见的调度或 OOM 原因。

日志与 Trace 缺失是因为容器未启动所致，并非诊断缺陷。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 22.5s
├─ 并发证据采集: 33.7s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 33.7s (Evidence 25.3s, RCA 8.2s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-volume-mount-failed
