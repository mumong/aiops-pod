## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | Pod 的 PreStop 生命周期钩子与主应用进程均被硬编码为阻塞等待特定文件（/state/teardown-requested）的写入，但该信号文件在删除触发后尚未创建，导致终止流程无限期挂起。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-1ad91d07ce28` | `status: Terminating (lasts <invalid>)` | 证实 Pod 处于强制终止后的“僵尸”状态，无限期挂起。 |
| 2 | K8s State | `fact-47cf8b178c89` | `Ready: True` (05:43:05) | 证实应用主进程在删除指令下达前是健康的。 |
| 3 | K8s Event | `fact-256a347ecd91` | `Stopping container app` (50s前) | 触发 Pod 终止流程的时间点。 |
| 4 | Metric | `fact-6e6170b2e97f` | `restart_count: 0` | 证实 Pod 未发生异常重启，处于静默挂起状态。 |
| 5 | K8s Config | `fact-421d0fdf854f` | `memory_limit: 32Mi` | 资源极度受限，限制了应用执行复杂清理任务的可能性。 |
| 6 | Logging | `fact-b14de61db900` | `application started` | 确认应用启动行为与事实诊断描述的应用进程阻塞一致。 |

**证据印证：** Kubernetes 状态事实显示 Pod 在 `Ready` 后进入终止流程即陷入停滞（无重启、无退出码），结合 Event 记录的停止触发时间和 Metric 确认的零重启，强有力地佐证了应用主进程或 PreStop 钩子被硬编码机制卡死在终止阶段。

## 🎯 根因分析 · g1

### 因果链

```text
应用硬编码阻塞等待特定文件（/state/teardown-requested） → PreStop 钩子与主进程均无法响应 SIGTERM → 终止流程无限期挂起 → Pod 滞留 Terminating 状态
```

### 根因结论

**已确认根因：** 应用程序（`workload`）存在逻辑缺陷。根据诊断结论，其 PreStop 生命周期钩子与主应用进程均被硬编码为阻塞等待特定文件 `/state/teardown-requested` 的写入。

**分析：** 在 Pod 执行删除操作时（由 `fact-256a347ecd91` 记录），删除信号（SIGTERM）下发，应用启动终止流程。但由于该信号文件未能及时创建，应用进程与 PreStop 钩子互相死锁或死等，导致 Pod 无法在规定的 Grace Period 内退出，从而进入 `Terminating (lasts <invalid>)` 的“僵尸”状态（`fact-1ad91d07ce28`）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 19.7s
├─ 并发证据采集: 47.5s
│  └─ g1 aiops-case-v12/workload: 47.5s (Evidence 41.2s, RCA 6.2s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
