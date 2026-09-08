## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | Pod aiops-case-07/workload-dff5cbc6b-kmfxx 处于 CrashLoopBackOff 状态，重启13次，容器进程因应用层错误连续非正常退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-07/workload-dff5cbc6b-kmfxx` 处于 `Running`，容器 `app` 重启 13 次，最后终止原因为 `Error`，退出码 `78` | 确认应用进程持续非正常退出的直接表现 |
| 2 | K8s Event | kubernetes | `Warning BackOff` 97s (x202 over 46m)：`Back-off restarting failed container app` | 确认崩溃已持续约 46 分钟且触发指数退避 |
| 3 | K8s Config | kubernetes | 容器 `app` 内存 Limit `96Mi`，Request `24Mi`；CPU Limit `200m`，Request `20m` | 资源规格上下文：内存配置较紧，但退出码非 OOMKill |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total` = 13 (标签 `container: app`)；`status_last_terminated_reason` 持续为 1 (标签 `reason: Error`) | 量化重启次数及终止原因模式为 `Error` |
| 5 | Logging | elasticsearch | `http_request` ERROR 模式出现 8 次：`message: "CONFIG_MISSING"`，`http_status: 500`，`path: "/work"` (2026-09-03 14:16 - 14:42) | 捕获触发崩溃的具体错误模式与业务路径 |
| 6 | Tracing | tempo | `GET /work` Span (e.g., trace `9e99fbd9...`, `da9999ae...`)，属性 `aiops.observed_mode: config_missing_exit`，响应 500 | 链路追踪确认异常发生在特定业务调用栈中 |

**证据印证说明：**
- **编号 1、2、4** 共同证实了 `CrashLoopBackOff` 状态及其高频率重启特征，`Exit Code 78` 指向非系统信号（如 OOM）导致的进程终止。
- **编号 3** 排除了因资源硬限制（OOM）导致退出码为 137 的可能性，且内存 Limit `96Mi` 与退出码 `78` 无直接关联。
- **编号 5、6** 直接锁定了崩溃机制：应用在处理 `/work` 接口时，因 `CONFIG_MISSING` 触发业务逻辑异常（500），随后进程以代码 78 退出。Tracing 的 `config_missing_exit` 模式与日志的 `CONFIG_MISSING` 相互印证。

## 🎯 根因分析 · g1

### 因果链

```text
应用运行环境缺少必要配置项 (CONFIG_MISSING) → 处理 /work 请求时触发业务逻辑异常 (HTTP 500) → 进程非正常退出 (Exit Code 78) → K8s 容器重启机制进入 CrashLoopBackOff
```

### 根因结论

已确认的根因是：**应用代码在运行环境中缺失关键配置项（`CONFIG_MISSING`），导致在处理 HTTP 请求（`/work`）时触发未处理或退出的业务异常，使容器进程以退出码 78 终止。**

**依据：**
- **K8s 事实 (Fact #1, #2)** 显示容器持续以 `Error` 状态退出并触发 `CrashLoopBackOff`。
- **Logging 事实 (Fact #5)** 和 **Tracing 事实 (Fact #6)** 明确捕获到 `CONFIG_MISSING` 错误模式及 `aiops.observed_mode: config_missing_exit` 的链路标记，且时间范围与崩溃周期吻合。
- **Metric 事实 (Fact #4)** 确认了终止原因为 `Error` 且重启次数达 13 次，排除了瞬时故障。

**缺失信息：**
- 缺失具体的配置项 Key 名称，无法进一步定位配置中心或 ConfigMap 的具体错误源。
- 退出码 78 对应的具体业务含义未被当前事实定义覆盖。

---

## 📊 性能统计

```text
├─ 总耗时: 2.6m
├─ 问题定位: 16.0s
├─ 并发证据采集: 125.1s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 125.1s (Evidence 114.1s, RCA 10.8s)
└─ 汇总总结: 14.1s
```

📋 Runbook 参考

- 未调用 Runbook
