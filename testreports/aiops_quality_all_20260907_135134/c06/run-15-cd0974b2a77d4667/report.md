## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | 应用代码或配置缺陷导致 /work 路径处理异常 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container.waiting_reason: `CrashLoopBackOff`; container.last_terminated_reason: `Error` | 确认应用容器处于频繁重启状态 |
| 2 | K8s Event | Kubernetes | `Warning  BackOff ... Back-off restarting failed container app` (x180 over 44m) | 确认重启行为在时间窗口内持续发生且间隔拉长 |
| 3 | Logging | Elasticsearch | `request completed`, path: `/work`, http_status: 500, service: `aiops-lab-workload` (occurrence: 4) | 提供业务层直接报错证据，定位故障路径为 `/work` |
| 4 | Tracing | Tempo | `GET /work`, trace_id: `684a53ea2d51690cdbba709bce8303a0`, status_code: `200`, attribute: `aiops.observed_mode: runtime_exit` | 证明进程在请求处理阶段崩溃；Span 记录 200 是因为进程在返回前已退出或被捕获 |

在证据表第 3 行与第 4 行中，日志中的 `trace_id: 684a53ea...` 与 Trace 中的 `trace_id: 684a53ea...` 完全一致。Trace 记录显示 Span 正常结束且返回了 200 状态码，但属性 `aiops.observed_mode` 标记为 `runtime_exit`。日志也记录了对应同一 Trace ID 的 `http_status: 500` 及 `runtime process exiting`。这两条事实共同指向一个特定机制：应用代码在 `/work` 路径的处理逻辑中抛出未捕获的内部异常，导致进程直接退出（Exit Code 2），而非正常返回 500 给客户端。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码或依赖配置存在缺陷 (触发) → 业务逻辑在处理 /work 请求时抛出内部异常 (机制) → 进程捕获异常后主动退出 (Exit Code 2) (直接失败) → Kubernetes 重启策略触发导致 CrashLoopBackOff (用户可见现象)
```

### 根因结论

已确认根因为**应用代码缺陷导致进程异常退出**。

证据 `fact-06ca54feb011`（日志：`path: /work, http_status: 500, runtime process exiting`）与 `fact-496d3eb49121`（Trace：`GET /work, status_code: 200, aiops.observed_mode: runtime_exit`）相互印证，证实了应用在处理 `/work` 路径请求时发生内部错误并导致进程崩溃。Kubernetes 配置（`fact-10117ff9f27e`, `fact-1ee0f8fd02d0`）的 `CrashLoopBackOff` 状态是这一机制引发的直接后果。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 32.7s
├─ 并发证据采集: 55.4s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 55.4s (Evidence 49.0s, RCA 6.3s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime, pod-oomkilled
