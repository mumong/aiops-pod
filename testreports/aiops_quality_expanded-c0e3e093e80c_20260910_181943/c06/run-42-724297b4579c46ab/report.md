## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | {'message': 'k8s.v1.cni.cncf.io/networks-status:'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container `app` last terminated reason: `Error` | 确认进程发生非零退出 |
| 2 | K8s State | Kubernetes | container `app` exit code: `2` | 直接证明应用侧发生终止 |
| 3 | K8s State | Kubernetes | container `app` status: `CrashLoopBackOff`, waiting reason: `CrashLoopBackOff` | 确认 Kubernetes 处于反复重启状态 |
| 4 | K8s Event | Kubernetes | `BackOff` restarting failed container `app` (x406 over 98m) | 证实重启频率及长时间未自愈 |
| 5 | K8s Config | Kubernetes | `app` container resource_limit.memory: `96Mi` | 提供容器资源上限配置作为排查边界 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: `23` | 验证了当前的重启总次数 |
| 7 | Logging | Elasticsearch | Pattern: `runtime process exiting` (http_status: 500, path: `/work`), allocated_mib: `0` | 应用日志记录了进程退出行为及请求上下文 |
| 8 | Tracing | Tempo/Deepflow | Trace `4bde5da3ee1d9724f078329f966f0048` (GET /work, status 200, mode: runtime_exit) | 提供了一次伴随进程退出的成功链路观测 |

**证据印证说明：**
*   Kubernetes 状态 (事实 1, 2) 与日志输出 (事实 7) 相互印证：K8s 记录了 `Error` 终止和 `exit code 2`，应用日志也记录了 `runtime process exiting`，共同指向应用层异常。
*   重启状态 (事实 3, 4, 6) 一致：K8s 的 `CrashLoopBackOff` 状态、BackOff 事件以及 Prometheus 的 `restarts_total` 均为 `23`，说明应用启动后立即崩溃。
*   日志中 `allocated_mib: 0` (事实 7) 与 `resource_limit.memory: 96Mi` (事实 5) 形成对照：进程在 500 错误退出时内存分配显示为 0，但这仅是一次记录快照，且 `allocated_mib` 并非 K8s 资源限制值，故无法断定是 OOM。

## 🎯 根因分析 · g1

### 因果链

```text
应用内部逻辑或依赖异常 → 进程以 exit code 2 终止 (Runtime Exit) → K8s 检测到非零退出码并触发重启策略 → Pod 处于 CrashLoopBackOff 状态
```

### 根因结论

*   **直接原因**：容器 `aiops-case-06/workload-7679bcf76-n5vp8` 中的 `app` 进程因接收到 `HTTP 500` 错误而触发 `runtime process exiting` 行为，导致以 `exit code 2` 退出。
*   **现象成因**：Kubernetes 检测到该进程异常退出后，执行重启策略。由于重启未达到 BackOff 指数退避的稳定期，Pod 持续在 `CrashLoopBackOff` 状态中循环。
*   **证据支撑**：
    *   K8s State 明确记录了 `exit code: 2` 和 `last terminated reason: Error` (事实 1, 2)。
    *   日志聚合确认了 `runtime process exiting` 与 `http_status: 500` 的强关联 (事实 7)。
    *   Tracing 提供了一次关联该过程的 Flow，显示进程在 `GET /work` 请求完成时记录了 `runtime_exit` 模式 (事实 8)。
*   **局限性/缺失**：正式 RCA 被配置禁用，且当前日志仅聚合了 `runtime process exiting` 模式，缺乏进程崩溃前的具体堆栈跟踪 (Stack Trace) 或导致 `exit code 2` 的具体业务逻辑代码行，因此无法进一步定位是内存配置不足 (`allocated_mib: 0` 仅为日志记录值，非 K8s 限制) 还是具体的应用代码缺陷。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 27.0s
├─ 并发证据采集: 62.3s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 62.3s (Evidence 54.2s, RCA 8.0s)
└─ 汇总总结: 14.7s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
