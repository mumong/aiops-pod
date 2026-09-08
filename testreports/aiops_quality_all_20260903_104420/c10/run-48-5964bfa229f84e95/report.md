## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | {'type': 'Warning', 'reason': 'Unhealthy', 'message': 'Warning  Unhealthy  36m (x69 over 136m)    kubelet  Liveness probe failed: HTTP probe failed with statuscode: 500'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `exit_code: 137` | 容器被强制终止的信号，常见于 SIGKILL 或 OOMKilled。 |
| 2 | K8s State | kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` | 探测端点返回服务端错误，表明容器在崩溃前处于运行状态且应用层异常。 |
| 3 | K8s State | kubernetes | `container.last_terminated_reason: Error` | 确认容器非正常退出，需结合具体原因分析。 |
| 4 | Logging | elasticsearch | `/work` 路径返回 `HTTP 200` (时间范围 `22:23:03` - `22:23:32`) | 证明在 Liveness Probe 失败后不久（或并行时间窗内），应用的 `/work` 接口仍响应正常。 |
| 5 | K8s Event | kubernetes | `Back-off restarting failed container app` (频率 `x495`) | 证实故障已演变为周期性重启循环。 |
| 6 | Metrics | prometheus | `kube_pod_container_status_restarts_total: 45` | 佐证了持续的重启状态。 |

**证据分析：**
1. **日志与探针行为的冲突**：`/work` 端点日志显示 HTTP 200（证据 4），这与 Liveness Probe 报告的 HTTP 500（证据 2）存在不一致，提示 Probe 可能请求了未提供日志记录的 `/health` 端点，或应用在不同请求间存在严重的不稳定性。
2. **进程终止原因不明**：退出码 137（证据 1）通常意味着收到 SIGKILL，但没有明确证据表明是 OOM（内存限制 `96Mi`，`20m` CPU 请求），也没有崩溃前的详细日志来解释是系统杀进程还是应用自身 panic。
3. **时间线断层**：现有的 `/work` 日志结束于 `22:23:32`，而 Liveness Probe 失败在 `36m` 前发生，缺乏连接“正常响应”到“致命终止”及“探针失败”的直接日志链条。

## 🎯 根因分析 · g1

### 因果链

```text
应用内部未确认的异常运行状态 → Liveness Probe 返回 HTTP 500 (与日志记录不一致) 且容器进程被 SIGKILL (Exit 137) → Kubelet 判定不健康并执行 BackOff 重启策略 → Pod 处于 CrashLoopBackOff 状态
```

### 根因结论

**证据不足，无法确诊根因。**

现有事实存在相互冲突或信息缺失，无法确定导致 CrashLoopBackOff 的单一直接原因：
1. **探针失败原因未明**：Liveness Probe 报告 HTTP 500（证据 2），但同时间窗口的 `/work` 日志显示 HTTP 200（证据 4）。由于缺乏 `/health` 端点的访问日志，无法判断是应用 Bug 导致健康检查失败，还是探针配置问题。
2. **强制终止原因未明**：容器退出码为 137（证据 1），这通常由 OOMKilled 或外部 SIGKILL 引起。虽然资源限制较低（96Mi 内存），但 Metrics 中未直接展示 OOMKilled 的持续特征，且缺乏崩溃瞬间的日志来确认是否内存溢出。

需要**崩溃前（Previous Container）的日志**来解释 137 码的具体触发机制，以及明确 Liveness Probe 端点的具体路径和响应日志，才能解开当前矛盾。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 14.5s
├─ 并发证据采集: 80.8s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 80.8s (Evidence 68.8s, RCA 11.9s)
└─ 汇总总结: 12.5s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime
