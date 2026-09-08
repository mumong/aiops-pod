## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | Pod aiops-case-06/workload-7679bcf76-jwr8b 处于 CrashLoopBackOff 状态，容器反复崩溃。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: Error (`fact-22fea7c1c7ca`) | 确认进程异常退出状态 |
| 2 | K8s State | Kubernetes | `container.waiting_reason`: CrashLoopBackOff (`fact-51f569e0ae07`) | 确认容器处于反复崩溃重启循环中 |
| 3 | K8s State | Kubernetes | `container.last_exit_code`: 2 (`fact-7384bc9736b5`) | 提供非零退出码这一直接退出依据 |
| 4 | K8s Event | Kubernetes | `BackOff` 事件：`Back-off restarting failed container app` (`fact-a0da7c3686fe`) | 描述重启退避机制的触发现象 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason`: 1 (`fact-587f51c5bb2b`) | 辅助确认容器异常终止状态与 K8s 事实一致 |
| 6 | Logging | Elasticsearch | Pattern: `http_request` | `http_status`: 500, `message`: "runtime process exiting", Path: `/work` (`fact-56801ebae375`) | 提供进程崩溃前的最后业务状态及错误上下文 |
| 7 | Tracing | Deepflow | L7 Flow: `GET /work` -> `response_code: 500`, `occurrence_count: 5` (`fact-8370ded3b5ce`) | 从流量层观测到大量失败的 HTTP 请求，印证应用内部错误 |

**证据交叉印证说明：**
- K8s 层面，`last_terminated_reason: Error` 与 `exit_code: 2` 证实容器非正常退出，且伴随 `CrashLoopBackOff` 状态，说明重启循环是持续且高频的（重启 21 次）。
- 日志层面，`http_status: 500` 与 `runtime process exiting` 直接解释了退出原因：进程因内部运行时错误导致主动退出。
- 流量层面，Deepflow 的 500 错误 L7 Flow 与日志中的 500 状态码完全对应，排除了网络侧或入口配置问题，锁定在应用内部处理 `/work` 端点时发生故障。
- 资源层面，当前资源请求（24Mi内存/20m CPU）与限制（96Mi内存/200m CPU）配置并未直接导致 OOMKill 等典型资源故障，故障根因更指向代码逻辑。

## 🎯 根因分析 · g1

### 因果链
```text
应用逻辑或依赖引发内部运行时错误 → 进程处理 /work 请求时返回 500 并记录 "runtime process exiting" → 容器异常退出（Exit Code 2） → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论
已确认根因：**应用进程在处理 `GET /work` 请求时遭遇运行时错误，主动退出导致反复重启。**

具体而言：
- 应用在处理 `/work` 端点时发生运行时异常（日志明确记录 `http_status: 500` 和 `runtime process exiting`）。
- 该异常导致容器进程以非零退出码（2）终止，触发 Kubernetes 的重启机制。
- 由于导致 500 错误的内部逻辑未修复，容器重启后立即再次崩溃，形成 CrashLoopBackOff。

当前证据已能确定“应用内部运行时错误”是崩溃的直接原因，但关于**具体导致 500 错误的代码逻辑细节**（如空指针、未捕获异常等）以及**是否由外部依赖缺失或不可用引起**，尚缺乏决定性事实（如缺少崩溃前的详细业务堆栈或外部依赖日志），无法进一步精确定位到具体代码行或依赖项。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 20.7s
├─ 并发证据采集: 71.5s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 71.5s (Evidence 59.6s, RCA 11.8s)
└─ 汇总总结: 13.3s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime
