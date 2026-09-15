## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod workload (aiops-case-v04) is stuck in ContainerCreating/Pending state due to volume mount failure. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `fact-1de8f9d716d6` | `Warning FailedMount 95s kubelet Unable to attach or mount volumes: unmounted volumes=[input]` | 确认 Pod 因挂载卷失败导致启动阻塞 |
| 2 | K8s Event | `fact-7683eb3a75fd` | `Warning FailedMount 90s kubelet MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found` | 指明挂载失败的具体原因是 Secret 不存在 |
| 3 | K8s State | `fact-e59cb66c2e28` | `Pod status: Pending` | 证实 Pod 处于 Pending 状态 |
| 4 | K8s State | `fact-448758c46e66` | `ContainersReady=False (ContainersNotReady: [app])` | 确认容器未就绪状态 |
| 5 | K8s State | `fact-fa734786efe7` | `Container "app" waiting_reason: ContainerCreating` | 定位等待状态发生在容器创建阶段 |
| 6 | Metric | `fact-b95f588585b0` | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"} = 1` | 从 Prometheus 维度确认容器处于 ContainerCreating 等待状态 |

证据关联：K8s Event 中的 `secret "unavailable-input" not found` 错误（事实 2）是引发 `Unable to mount`（事实 1）的直接原因，进而导致 Pod 处于 Pending 状态且容器卡在 ContainerCreating（事实 3、4、5），Metric 监控结果（事实 6）与该等待状态一致。Logging 和 Tracing 维度因容器未启动而未采集到数据。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 'unavailable-input' 在命名空间 aiops-case-v04 中不存在 → Pod 'workload' 尝试挂载指向该 Secret 的卷 'input' 且未设置为 Optional → Kubelet 在挂载卷时失败并报告 'secret not found' → 容器无法完成创建，Pod 陷入 Pending/ContainerCreating 状态
```

### 根因结论

已确认根因：Pod 的 YAML 配置中声明了一个名为 `input` 的卷，该卷映射到 Secret `unavailable-input`，但该 Secret 在命名空间 `aiops-case-v04` 中不存在。

根据事实 1 和 2，Kubelet 在尝试挂载卷时明确报错 `secret "unavailable-input" not found`，这直接导致了 Pod 的挂载失败（FailedMount）。由于该卷挂载失败，容器 `app` 一直处于 `ContainerCreating` 状态，无法启动，进而导致整个 Pod 维持在 `Pending` 状态且无法就绪。

缺失的决定性事实：
- 缺失关于 Secret `unavailable-input` 为何缺失的信息（是拼写错误、尚未创建还是被误删除）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 21.9s
├─ 并发证据采集: 35.3s
│  └─ g1 aiops-case-v04/workload: 35.3s (Evidence 26.9s, RCA 8.3s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-volume-mount-failed, pod-imagepull-failed, pod-config-error, pod-sandbox-create-failed
