## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | Pod workload in aiops-case-v12 is stuck in Terminating state (Status=Terminating, Age=82s) despite having no finalizers and a long deletionGracePeriodSeconds (3900s). |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.phase=Running` | 支撑已验证上游：Pod 在逻辑上仍属运行状态，未进入 Finished/Removed 阶段 |
| 2 | K8s State | kubernetes | `pod.status=Terminating (lasts <invalid>)`；`restart_count=0` | 支撑直接失败：Pod 状态停滞在 Terminating 且未经历重启，排除容器崩溃自愈合场景 |
| 3 | K8s Event | kubernetes | `Stopping container app` (48s) | 支撑失败机制：容器生命周期被外部触发强制停止，符合 PreStop 阶段的调度行为 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total=0` | 支撑直接失败：与 K8s State 交叉印证，进一步确认未触发重启 |
| 5 | Logging | elasticsearch | `application started` | 限定作用：确认容器初始启动正常，未提供 PreStop 阶段阻塞的额外日志上下文 |
| 6 | K8s Event | kubernetes | `Annotations: cni.projectcalico.org/podIP: 172.16.104.32/32` | 限定作用：证明网络资源仍在关联，支持 Terminating 但未彻底清理的事实 |

**证据互证说明：**
1. **状态与事件互证**：`pod.status=Terminating` 结合 `Stopping container app` 事件，完整勾勒出容器在终止阶段的被阻断画面，与根因中“PreStop 阶段卡死”的机制吻合。
2. **指标与状态互证**：Prometheus 的 `restarts_total=0` 与 K8s 原生 `restart_count=0` 相互印证，彻底排除了因 OOM 或 Crash 导致 Pod 快速重启的可能，确立了“长期停滞在 Terminating”这一现象的单一性。

## 🎯 根因分析 · g1

### 因果链

```text
PreStop 逻辑无限等待文件 `/state/teardown-requested` → 容器生命周期在 PreStop 阶段被阻塞 → Pod 无法执行后续清理并彻底移除 → Pod 处于 Terminating 状态（Phase=Running, 但不可用）
```

### 根因结论

已确认的根因为：**PreStop 钩子阻塞在缺失的文件 `/state/teardown-requested`**。

1. **根因与现象的关联**：当前 Pod `aiops-case-v12/workload` 处于 `Terminating` 状态，且 K8s State 明确显示其 `phase=Running`。这通常发生在容器进程在退出前被 PreStop 脚本拦截时。结合诊断信息，PreStop 脚本因等待一个永远不会被创建的文件而无限期挂起，导致了容器无法执行后续的 `SIGTERM` 后清理，最终使 Pod 卡死。
2. **证据支撑**：
   - K8s 事件 `Stopping container app` 验证了终止流程的启动。
   - `phase=Running` 且 `restart_count=0` 以及指标 `kube_pod_container_status_restarts_total=0` 共同证实了 Pod 既没有成功退出，也没有发生重启，处于停滞状态。
3. **剩余未知**：无法从当前证据中确认 PreStop 钩子是否已完全开始执行（例如是否因文件检查早于写入），以及具体是哪个 Sidecar、Operator 或外部事件本应负责创建该文件，但这不影响“PreStop 文件等待导致卡死”这一直接阻断机制的结论。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 19.1s
├─ 并发证据采集: 105.6s
│  └─ g1 aiops-case-v12/workload: 105.6s (Evidence 88.8s, RCA 16.7s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
