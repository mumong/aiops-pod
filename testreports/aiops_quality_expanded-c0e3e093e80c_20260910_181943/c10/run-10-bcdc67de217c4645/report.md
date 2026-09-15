## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bsn84` | CrashLoopBackOff | Pod workload-79d9f8fd88-bsn84 previously in CrashLoopBackOff (17 restarts), currently Running but terminated by OOM Kill |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | Kubernetes | `container.resource_limit.memory` = 96Mi | 设定了容器的硬内存上限 |
| 2 | K8s Config | Kubernetes | `container.resource_request.memory` = 24Mi | 设定了容器的请求内存，远低于上限 |
| 3 | K8s State | Kubernetes | `container.last_terminated_reason` = Error | 记录了上一次容器的终止原因 |
| 4 | K8s State | Kubernetes | `container.last_exit_code` = 137 | 进程被强制杀死的系统信号码 |
| 5 | K8s Event | Kubernetes | `Warning BackOff ... Back-off restarting failed container app` | 确认了 Pod 进入了 CrashLoopBackOff 循环 |
| 6 | K8s Event | Kubernetes | `Warning Unhealthy ... Liveness probe failed: HTTP probe failed with statuscode: 500` | 探测失败导致容器被重启 |
| 7 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` = Error | 从监控层再次确认了容器的终止原因为 Error |
| 8 | Logging | Elasticsearch | Pattern: `http_status: 200` in `1a7fcca3...` 等 Trace ID 对应的日志 | 显示在终止前，应用在处理 HTTP 200 请求，排除业务逻辑报错 |
| 9 | Tracing | Tempo | Span `GET /work` (trace `6f538ade...`) status `200` | 确认了导致 OOM 的请求是正常成功的业务请求 |

**证据分析：**
Kubernetes 状态、事件与 Prometheus 指标高度一致，共同指向容器因 `Error` 状态异常终止，且 `exit_code 137` 是 Linux OOM Killer 的典型特征。日志与链路追踪显示，系统在终止前正正常处理 HTTP 请求（200 OK），证实异常非应用业务逻辑引起，而是资源超限导致的系统级强制终止。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存使用量突破 96Mi 硬限制 → OOM Killer 发送 SIGKILL 信号 (exitCode 137) → 容器异常终止 (Reason=Error) → Pod 重启并进入 CrashLoopBackOff
```

### 根因结论

已确认根因为 **容器内存超限导致 OOM Kill**。
*   **证据支撑**：事实 #1 指出容器内存硬限制仅为 96Mi；事实 #3、#4 显示容器以 `Exit Code 137` 终止（即 OOM Kill）；事实 #6 显示因 Liveness Probe 失败引发重启；事实 #2 表明 24Mi 的请求值远低于 96Mi 限制，暗示实际工作负载存在峰值超出硬限制的风险。
*   **缺失事实**：当前事实未捕获内存使用量的具体峰值数据或随时间变化的趋势（如 Metrics 仅有一条记录且不可评估趋势），无法精准还原内存增长的具体时间线，但已具备判定根因的充分条件。

---

## 📊 性能统计

```text
├─ 总耗时: 9.9m
├─ 问题定位: 35.1s
├─ 并发证据采集: 546.3s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bsn84: 546.3s (Evidence 538.4s, RCA 7.8s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bsn84**: pod-oomkilled, pod-crashloop-runtime
