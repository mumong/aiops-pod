## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | 容器内运行进程在处理请求时发生运行时异常退出（exit code 2） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: Error | 确认应用容器非正常退出 |
| 2 | K8s Event | kubernetes | `kubelet` BackOff restarting failed container app (BackOff 103s x384 over 86m) | 确认故障持续且进入指数退避恢复期 |
| 3 | K8s State | kubernetes | `container.waiting_reason`: CrashLoopBackOff | 确认当前阻塞状态 |
| 4 | K8s State | kubernetes | `container.last_exit_code`: 2 | 定位退出码为应用层逻辑/运行时错误 |
| 5 | K8s Config | kubernetes | `container.resource_limit.memory`: 96Mi | 确认内存资源硬限制（资源请求 24Mi） |
| 6 | K8s Config | kubernetes | `container.resource_limit.cpu`: 200m | 确认 CPU 资源限制 |
| 7 | Metric | prometheus | `restart_count`: 21, `CrashLoopBackOff`: 1 | 量化验证高频重启状态 |
| 8 | Metric | prometheus | `last_terminated_reason`: Error | 从监控视角印证容器退出原因为 Error |
| 9 | Logging | elasticsearch | Pattern: `runtime process exiting` (HTTP 500, path `/work`, level error) | 记录进程在接收 HTTP 请求时主动崩溃退出 |
| 10 | Logging | elasticsearch | Pattern: `request completed` (HTTP 200, path `/work`, level info) | 记录进程在崩溃前曾成功处理请求，确认运行时环境初始正常 |
| 11 | Tracing | deepflow | Flow: `GET /work` response_code 500 (occurrences 4, duration 5.6ms-9.8ms) | 从网络侧确认 `/work` 接口在故障期间持续返回 500 |
| 12 | Tracing | deepflow/Tempo | Flow/Span: `GET /work` response_code 200 (trace_id `1608...`) 与日志 Pattern 2 关联 | 证明应用并非整体不可用，而是特定运行时状态下崩溃 |

证据间相互印证关系：
- Kubernetes 状态（Exit Code 2、CrashLoopBackOff）、Prometheus 指标（重启次数 21、终止原因 Error）与 Elasticsearch 日志（`runtime process exiting`）共同指向应用容器内部进程主动异常退出。
- Tracing 数据（Flow `response_code: 500`）与日志（`http_status: 500`）在网络与应用日志层面交叉验证了 `/work` 端点在应用崩溃时的表现。

## 🎯 根因分析 · g1

### 因果链
```text
应用运行时环境或内部状态异常（未确认具体触发代码/配置） → 进程在处理 /work 请求时抛出异常退出 → exit code 2 → CrashLoopBackOff 与 500 错误
```

### 根因结论
- **已确认现象**：Pod `workload-7679bcf76-w9s9c` 因应用容器（app）进程运行时异常退出（exit code 2）陷入 `CrashLoopBackOff`。
- **根因证据**：
  1. K8s 指标与状态确认终止原因为 `Error`，非 OOMKilled（未提供 OOMKilled 证据）或 Liveness/Readiness Probe 失败导致的 Kill。
  2. 日志与追踪明确显示进程是在处理 `GET /work` HTTP 请求时主动退出（`runtime process exiting`），且伴随 HTTP 500 响应。
- **证据不足说明**：现有数据仅证明进程以 code 2 崩溃，未捕获崩溃时的堆栈追踪（Stack Trace）或具体的内存/CPU 瞬时飙升日志。资源限制（Memory 96Mi, CPU 200m）为上下文信息，虽不能完全排除边界溢出可能，但缺乏直接导致崩溃的资源耗尽证据（如 `OOMKilled` 标记或资源限制触发的 `Throttled` 记录）。因此，确切的应用代码/逻辑错误根因需结合应用侧调试日志或核心转储确认。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 16.8s
├─ 并发证据采集: 46.7s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 46.7s (Evidence 41.6s, RCA 5.0s)
└─ 汇总总结: 14.4s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime, pod-oomkilled, pod-evicted
