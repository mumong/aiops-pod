## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod 'aiops-case-v04/workload' stuck in ContainerCreating (Pending) state, unable to start container 'app'. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-v04/workload` status: `Pending` | 确认 Pod 处于未就绪状态 |
| 2 | K8s State | kubernetes | container `app` waiting reason: `ContainerCreating` | 明确容器卡在创建阶段 |
| 3 | K8s Event | kubernetes | `Warning FailedMount 54s (x18 over 39m) kubelet Unable to attach or mount volumes: unmounted volumes=[input]` | 关键证据：证实挂载卷失败，指向 Volume 依赖问题 |
| 4 | K8s Event | kubernetes | `Warning FailedMount 10m (x23 over 41m) kubelet MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found` | 关键证据：直接指出 `unavailable-input` Secret 缺失 |
| 5 | K8s Config | kubernetes | container `app` resource_limit memory: `32Mi`, cpu: `50m` | 排除内存/CPU 资源不足作为启动失败的根因 |
| 6 | Metric | prometheus | `kube_pod_container_status_waiting_reason` `container="app"` value `1` (Pending) | 独立观测：确认容器处于 Waiting 状态 |
| 7 | Metric | prometheus | `kube_pod_container_status_restarts_total` `container="app"` value `0` | 排除容器启动崩溃（CrashLoopBackOff）的可能性 |

**证据分析：**
K8s Event 明确记录了 `FailedMount` 错误，且原因指向 Secret `unavailable-input` 不存在（证据 #4）。K8s State 显示 Pod 持续处于 `Pending` 且容器 `waiting_reason` 为 `ContainerCreating`（证据 #1, #2）。Metrics 独立验证了容器未运行且从未重启过（证据 #6, #7）。所有事实一致指向因依赖 Secret 缺失导致的挂载失败，进而阻止容器启动。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 'unavailable-input' 在命名空间 'aiops-case-v04' 中不存在 → kubelet 无法挂载名为 'input' 的 Volume → Pod 卡在 ContainerCreating/Pending 状态，无法创建容器 → 用户观测到 Pod 无法启动
```

### 根因结论

已确认根因为 **Pod 引用的 Secret `unavailable-input` 不存在**。

K8s Event 明确指出挂载卷失败的原因是 `secret "unavailable-input" not found`（证据 #4）。这导致 kubelet 无法完成卷挂载，Pod 因此一直停留在 `Pending` 状态，容器 `app` 始终处于 `ContainerCreating` 且 `restart_count` 为 0（证据 #1, #2, #7）。资源限制配置正常（证据 #5），排除了资源不足的可能。

---

## 📊 性能统计

```text
├─ 总耗时: 56.1s
├─ 问题定位: 19.9s
├─ 并发证据采集: 26.5s
│  └─ g1 aiops-case-v04/workload: 26.4s (Evidence 17.3s, RCA 8.9s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-volume-mount-failed
