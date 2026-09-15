## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod workload-dff5cbc6b-sjvxl 处于 CrashLoopBackOff，反复以 exitCode=78 崩溃，Ready=False |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod status: Running, ContainersReady: False (message: containers with unready status: [app]) | 确认 Pod 处于运行状态但容器无法就绪，存在持续性异常 |
| 2 | K8s Event | kubernetes | Warning BackOff 2m25s (x242 over 57m): Back-off restarting failed container app | 证实重启行为持续 57 分钟且频率极高，符合 CrashLoop 特征 |
| 3 | Logging | elasticsearch | pattern: `{"event": "http_request", "level": "error", "message": "CONFIG_MISSING", "http_status": 500, "path": "/work", "service": "aiops-lab-workload"}` (occurrence_count: 8) | 记录应用在处理 `/work` 请求时因配置缺失报错并返回 HTTP 500 |
| 4 | Tracing | deepflow | l7_flow: GET /work → HTTP 500 (src_ip: 172.16.104.8, dst_ip: 172.16.104.63), trace_ids: 与日志聚合中的 trace_id 一致 (如 `55c07e8b117659114ccbae9c7f582db0`) | 从流量层面验证了应用对 `/work` 请求返回 500 错误，且与日志的 Trace ID 跨维关联，确认同一故障现场 |
| 5 | K8s State | kubernetes | container.waiting_reason: CrashLoopBackOff; container.last_exit_code: 78 | 提供直接的状态证据，指明容器因退出码 78 终止并进入指数退避重启 |
| 6 | K8s Config | kubernetes | resource_limit.memory: 96Mi, resource_request.memory: 24Mi | 资源请求合理且处于限制范围内，非内存 OOM 导致 |

证据印证与冲突：
1. 日志中的 `CONFIG_MISSING` 错误与 Tracing 中的 `GET /work` 返回 `500` 状态码形成闭环，共同指向应用业务逻辑异常。
2. 应用日志记录的 `500` 错误及 `exitCode=78` 与 K8s 层面的 `CrashLoopBackOff` 状态完美对应，说明容器非因系统资源不足退出，而是应用代码主动退出。
3. 跨维度的 Trace ID（如 `55c07e8b117659114ccbae9c7f582db0`）在日志和 Tracing 事实中重合，排除了日志误报或无关错误的干扰。

## 🎯 根因分析 · g1

### 因果链

```text
关键配置缺失（CONFIG_MISSING） → 应用处理请求时抛出错误并返回 HTTP 500 → 进程以 exitCode=78 终止 → Pod 进入 CrashLoopBackOff，Ready=False
```

### 根因结论

已确认的根因是应用代码中关键配置项缺失。

- **证据支撑**：
  - 聚合日志明确报出 `message: "CONFIG_MISSING"` 且发生在处理 `path: "/work"` 时（事实 #3）。
  - 追踪记录（Tracing）证实该请求最终返回 `HTTP 500`（事实 #4）。
  - Kubernetes 状态显示容器反复以退出码 `78` 终止并处于 `CrashLoopBackOff` 状态（事实 #1, #5）。

- **未决事项**：虽然确认了配置缺失是退出原因，但尚未在证据中明确指出具体缺失的是哪个 ConfigMap 或环境变量键名（即“application_span”中仅记录 `aiops.observed_mode: config_missing_exit`，未展开具体字段名）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 17.5s
├─ 并发证据采集: 53.1s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 53.1s (Evidence 43.5s, RCA 9.4s)
└─ 汇总总结: 13.1s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
