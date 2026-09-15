## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | 应用在处理 /work 请求时发生未捕获异常并主动退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning BackOff 102s (x134 over 31m) kubelet Back-off restarting failed container app` | 确认容器经历频繁重启，且重启退避延迟已拉长，表明崩溃持续发生 |
| 2 | K8s State | kubernetes | `container.waiting_reason`: `CrashLoopBackOff`; `exit_code`: `2` | 容器因进程异常退出（Exit 2）被 K8s 拉回等待状态 |
| 3 | Logging | elasticsearch | Pattern: `runtime process exiting`; `http_status: 500`; `path: /work`; Trace IDs: `b7890415...`, `9b9ea209...` | 确认应用主动退出，且退出发生在处理 `/work` 请求时伴随 500 错误 |
| 4 | Logging | elasticsearch | Pattern: `request completed`; `http_status: 200`; `path: /work` (occurrence_count: 5) | 确认 `/work` 接口此前曾正常返回 200，排除全量接口不可用 |
| 5 | K8s Config | kubernetes | `container.resource_limit.memory`: `96Mi` | 提供资源硬限制上下文，但内存使用记录显示未触及该限制 |
| 6 | Logging | elasticsearch | `numeric_fields`: `allocated_mib` (min: 0.0, max: 0.0) | 在报错和成功请求中，内存分配量均稳定为 0，排除应用内存耗尽导致崩溃的可能 |
| 7 | Metric | prometheus | `kube_pod_container_status_waiting_reason`=1 (`reason: CrashLoopBackOff`); `last_terminated_reason`=1 (`reason: Error`) | 验证当前容器确实处于因 Error 终止而等待的状态 |
| 8 | Metric | prometheus | `kube_pod_container_status_restarts_total`=10 | 量化重启次数，确认故障具有持续性而非偶发 |

**证据说明：**
K8s Event 和 Metric 证实了容器处于 `CrashLoopBackOff` 状态，且退出原因为 `Error`，与 `exit_code: 2` 一致。Logging 提供了具体的退出机制线索：应用在处理 `/work` 请求时主动触发 `runtime process exiting`（伴随 500 状态码），且由于内存分配量恒定为 0，排除了 OOM 的可能。K8s 事件中的 `BackOff` 频率与日志中的崩溃时间窗口相吻合，证据相互印证，指向应用内部异常。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码未捕获异常 → 进程主动退出 (exit code 2) → K8s 重启策略触发 → CrashLoopBackOff 状态
```

### 根因结论

**已确认根因**：应用在处理 `/work` 请求时发生未捕获异常并主动退出（Exit code 2）。

*   **机制与证据**：日志（Fact #3, #4）明确指出应用在执行 `/work` 请求后记录 `runtime process exiting` 且伴随 HTTP 500 错误，这与 K8s 记录的 `exit_code: 2` 和 `container.last_terminated_reason: Error`（Fact #2）完全吻合。
*   **排除其他原因**：日志中的 `allocated_mib` 字段在成功和失败请求中均为 0.0（Fact #5, #6），证明崩溃并非由内存超限（Limit 96Mi）引起；K8s 的 `BackOff` 事件（Fact #1）和 Metric 重启计数（Fact #8）证实了该行为是持续性的，而非瞬时网络抖动或外部因素导致。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 20.1s
├─ 并发证据采集: 84.3s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 84.3s (Evidence 78.1s, RCA 6.0s)
└─ 汇总总结: 12.7s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
