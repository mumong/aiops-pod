## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod workload-5b5fc86c8c-2xgjz 处于 Pending/ContainerCreating 状态，无法进入 Running。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning FailedMount 58s (x33 over 51m) kubelet MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (fact-50aee70ac577) | 直接指明挂载失败的错误源与缺失资源 |
| 2 | K8s Event | Kubernetes | `Warning FailedMount 6m38s (x20 over 49m) Unable to attach or mount volumes: unmounted volumes=[input]...` (fact-9159b88bb2e9) | 证明故障持续存在且挂载阻塞 |
| 3 | K8s State | Kubernetes | `ContainerCreating` (fact-3ff74222294d) | 确认容器处于创建阻塞阶段 |
| 4 | K8s Config | Kubernetes | `configmap "unavailable-config" not found` (fact-50aee70ac577) | 确认配置缺失的直接事实 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1` (reason: `ContainerCreating`) (fact-baa30ad90880) | 数值上确认容器处于等待状态，无重启 (fact-e303f2e839f8 restarts=0) |

K8s 事件 `fact-50aee70ac577` 提供了最直接的错误原因（ConfigMap 缺失），与 `fact-3ff74222294d` 的 `ContainerCreating` 状态一致，`fact-baa30ad90880` 的 Metric 数据进一步佐证了容器卡在等待状态的现状。

## 🎯 根因分析 · g1

### 因果链

```text
Volume 'input' 引用缺失的 ConfigMap 'unavailable-config' → kubelet 挂载失败 (MountVolume.SetUp failed) → Pod 持续阻塞在 ContainerCreating/Pending → 容器无法启动
```

### 根因结论

已确认根因为**Volume 定义引用了不存在的 ConfigMap `unavailable-config`**，导致 `kubelet` 在 `MountVolume.SetUp` 阶段持续失败。

- 支撑事实：K8s Event 明确指出 `configmap "unavailable-config" not found` (fact-50aee70ac577)，导致挂载动作 `FailedMount` (fact-50aee70ac577, fact-9159b88bb2e9)。
- 状态确认：Pod 因此卡在 `ContainerCreating` (fact-3ff74222294d) 和 `Pending` (fact-334ab632d0d2) 状态，且容器未发生重启 (fact-9b740370c258)。

---

## 📊 性能统计

```text
├─ 总耗时: 56.6s
├─ 问题定位: 14.0s
├─ 并发证据采集: 32.7s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 32.7s (Evidence 25.3s, RCA 7.3s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-sandbox-create-failed
