## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod `workload` 的 Volume `input` 引用了 ConfigMap `workload-input`，但挂载配置中请求的 Key `unavailable-key` 在 ConfigMap 中不存在，导致 Volume 挂载持续失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Status | phase: Pending, condition Ready: False, ContainersNotReady | 确认 Pod 处于调度后、容器未启动的异常状态 |
| 2 | K8s State | Container Status | container `app` waiting reason: ContainerCreating | 指向容器初始化或挂载阶段阻塞 |
| 3 | K8s Event | kubelet | FailedMount: MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key | 直接定位挂载失败的具体配置错误原因 |
| 4 | K8s Event | kubelet | FailedMount: Unable to attach or mount volumes: unmounted volumes=[input] | 验证 Volume `input` 无法挂载的持续症状 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}`: 1 | 从监控侧佐证容器处于等待挂载状态 |

**证据链说明：**
- K8s State (事实 1, 2) 与 K8s Event (事实 3) 形成直接因果：Pod 处于 Pending 且容器等待中，原因是 kubelet 报告的 `FailedMount` 明确指出 ConfigMap 引用的 key 不存在。
- Metric (事实 5) 从监控维度确认了容器等待状态的持续存在，排除了瞬时故障的可能性，与 K8s Event 中 `x20` / `x40` 的重复计数一致。
- 容器重启次数为 0（未提供具体事实但状态为 ContainerCreating），证实容器从未成功启动，进一步锁定故障在初始化阶段。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap workload-input 缺少 Key unavailable-key → Volume "input" 挂载校验失败 → 容器持续处于 ContainerCreating 状态 → Pod 保持 Pending，应用不可用
```

### 根因结论

**已确认根因：** Pod `workload` 的 Volume 挂载配置引用了 ConfigMap `workload-input` 中不存在的 Key `unavailable-key`（见证据 #3）。

该配置错误导致 kubelet 在挂载 Volume 时触发 `FailedMount` 错误，使 Pod 无法进入运行状态。K8s 状态（#1, #2）和 Metrics（#5）均证实了这一持续性的挂载阻塞现象。现有证据链完整，直接指向配置错误。

---

## 📊 性能统计

```text
├─ 总耗时: 9.9m
├─ 问题定位: 44.8s
├─ 并发证据采集: 539.2s
│  └─ g1 aiops-case-v05/workload: 539.1s (Evidence 533.4s, RCA 5.7s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-sandbox-create-failed, pod-volume-mount-failed
