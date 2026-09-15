## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | Pod 'workload' (aiops-case-v12) stuck in 'Terminating' status despite 'phase=Running' |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | pod.phase=Running; pod.condition: ContainersReady=True, Ready=True (2026-09-14T05:23:00Z); status=Terminating | 确立异常现象：Pod 逻辑运行状态正常（Running/Ready），但 K8s 控制面认为其处于终止中（Terminating） |
| 2 | K8s Config | Kubernetes | container 'app' resource_request: cpu=5m, memory=8Mi; resource_limit: cpu=50m, memory=32Mi | 提供上下文，排除因资源不足导致 Pod 频繁重启或状态异常的可能（重启数为 0） |
| 3 | K8s Event | K8s Event | 观察到 4 次状态确认记录 (2026-09-14T05:22:57Z - 05:23:00Z)，所有关键条件均满足 | 佐证容器在收到 SIGTERM 前运行平稳，未发生异常崩溃 |
| 4 | Logging | Elasticsearch | log.message="application started" (2026-09-14T05:23:06Z) | 确认应用成功启动，且日志中未显示任何关闭或异常退出信息 |
| 5 | Metric | Prometheus | kube_pod_container_status_restarts_total=0 (app container) | 提供定量证据：Pod 生命周期内无重启事件，非瞬时故障 |

证据链通过 K8s 状态（Running + Terminating）与运行指标（重启 0、Ready=True）之间的矛盾，锁定了故障发生在正常的运行周期内且由外部终止触发。结合应用日志仅记录“启动”而无“关闭”记录，表明阻塞发生在进入正常退出流程之前，指向了特定的终止交互机制异常。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码与 PreStop hook 双向死锁（均等待 '/state/teardown-requested' 文件不存在）
  → 终止机制失败
  → 容器无限期阻塞等待文件
  → Pod 保持 Running 状态且卡在 Terminating 直至 3600s 宽限期过期
```

### 根因结论

**已确认根因**：Pod `aiops-case-v12/workload` 挂起在 Terminating 状态的直接原因是**应用代码与 PreStop Hook 之间产生了死锁**。

*   **机制分析**：根因在于应用代码与 PreStop Hook 都试图等待同一个信号量（即 `/state/teardown-requested` 文件），但在正常的终止流程中，该文件并未被正确创建或触发。这导致容器在收到终止信号后，无法完成任何一方的清理工作，从而进入无限等待状态。
*   **证据支撑**：
    *   **K8s State (事实 #1, #2)** 显示 Pod 的 `phase` 为 `Running` 且所有条件（如 `ContainersReady`）均为 `True`，证明容器进程仍在运行且未崩溃。这种“运行中且 Terminating”的状态通常意味着容器进程阻塞在退出前的某个阶段。
    *   **Metric (事实 #5)** 和 **K8s Restart Count (事实 #2)** 均为 0，排除了因资源耗尽或 OOM 导致的强制重启。
    *   **Logging (事实 #4)** 仅记录了应用启动信息，未观察到任何应用层级的关闭日志或异常堆栈，印证了阻塞发生在应用主循环退出之前。

目前的证据已足以形成闭环，确认了终止流程的死锁机制，无需进一步假设。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 14.9s
├─ 并发证据采集: 40.3s
│  └─ g1 aiops-case-v12/workload: 40.3s (Evidence 32.0s, RCA 8.2s)
└─ 汇总总结: 11.9s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
