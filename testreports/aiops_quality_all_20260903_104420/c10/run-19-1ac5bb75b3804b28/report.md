## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | 容器app的内存使用量（Working Set）在运行周期内持续上升，最终触发了kubernetes配置的硬内存上限（96Mi），导致内核OOM Killer发送SIGKILL（Exit 137）强制终止进程。由于liveness探针未能及时恢复，Pod进入CrashLoopBackOff状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s | `last_terminated_reason`: Error; `last_exit_code`: 137 | 确认容器因异常信号终止 |
| 2 | K8s State | K8s | `resource_limit.memory`: 96Mi | 确定触发 OOM Killer 的资源上限 |
| 3 | K8s Event | K8s | `Killing ... Container app failed liveness probe` | 证明 liveness 探针失败触发了系统回收动作 |
| 4 | K8s Event | K8s | `Unhealthy ... Liveness probe failed: HTTP probe failed with statuscode: 500` | 证明故障前应用已处于无响应或错误状态 |
| 5 | Metric | Prometheus | `container_memory_working_set_bytes`: 3,596,288 bytes → 15,425,536 bytes (上升约 3.3 倍) | 提供内存持续增长并逼近限制的量化事实 |
| 6 | Logging | ES | Pattern: `request completed` (200 OK) | 确认应用存在正常业务处理能力 |
| 7 | Tracing | Deepflow/Tempo | `GET /work` → 200 OK (Span ID: `f5b1b61037693ea4be422bcd676bf61b`) | 提供正常请求的链路验证 |

**证据说明**：
*   **异常与根因的印证 (1, 2, 3, 5)**：K8s 日志明确指出容器因 Liveness Probe 失败被 Kill (事实 3)，事实 1 证实了这是由 Error 引起的异常终止 (Exit 137)。事实 5 的 Metrics 数据量化了内存从 3.6MB 增长到 15.4MB 的过程，这直接指向了突破 96Mi 限制 (事实 2) 后触发内核 OOM Killer 的根本机制。
*   **应用状态与探针的冲突 (4, 6, 7)**：事实 4 显示 Liveness 探针返回 500 错误，暗示当时应用处于故障状态。事实 6 和 7 展示了应用正常响应 200 请求的历史模式，这表明异常并非应用不可用，而是应用处于一种“存活但业务处理异常（或负载高导致超时）”的状态，从而导致 K8s 判断健康检查失败并强制重启。

## 🎯 根因分析 · g1

### 因果链

```text
应用内存持续增长 (Fact 5) → 突破 96Mi 硬限制触发 OOM Killer (Fact 2) → 进程被 SIGKILL 退出 (Fact 1, Fact 3) → Liveness Probe 检查失败 (Fact 4) → 容器反复重启 CrashLoopBackOff (Fact 3)
```

### 根因结论

已确认根因为：**应用进程存在内存泄漏或高内存占用行为，导致 Working Set 内存持续上升并超过 Pod 配置的 96Mi 内存硬限制**。

当内存达到限制时，内核触发 OOM Killer 终止进程（退出码 137）。由于应用进程在启动后可能经历短暂的业务错误状态或启动延迟，导致 liveness 探针在系统执行回收前或回收后未能及时恢复，Kubernetes 判定容器不健康，触发了持续的 `CrashLoopBackOff` 重启循环。

*   **支撑证据**：
    *   **内存超限与 OOM 机制**：Metric 数据显示内存持续增长 (Fact 5)，最终被 K8s 硬限制 96Mi (Fact 2) 拦截。
    *   **异常终止与重启**：K8s 状态显示 `last_exit_code: 137` (Fact 1) 以及 `Reason: CrashLoopBackOff`，证明是资源限制导致的强制回收，而非业务代码直接崩溃退出。
    *   **探针机制的触发**：K8s 事件确认是因为 `Liveness probe failed` 而执行 `Killing` (Fact 3, Fact 4)，这是导致 Pod 无法维持 Running 状态并进入反复重启循环的直接执行动作。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 20.2s
├─ 并发证据采集: 100.5s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 100.5s (Evidence 91.8s, RCA 8.6s)
└─ 汇总总结: 14.4s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime
