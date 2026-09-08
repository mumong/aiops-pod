## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | Pod aiops-case-06/workload-7679bcf76-w9s9c 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` 状态: `CrashLoopBackOff`，退出码: `2` | 直接异常状态，确认进程存在致命非正常退出 |
| 2 | K8s Event | Kubernetes | `Warning BackOff`: 2m17s 内重试 497 次（累计 112 分钟） | 证实进程反复崩溃，符合 CrashLoopBackOff 行为特征 |
| 3 | K8s Config | Kubernetes | 容器资源限制：CPU `200m` / 内存 `96Mi`；请求值：CPU `20m` / 内存 `24Mi` | 辅助观察，非 OOMKill（因退出码为 2 而非 137） |
| 4 | Logging | Elasticsearch | 日志模式: `runtime process exiting` (HTTP 500, `/work`)；观察窗口内内存 `allocated_mib` 始终为 `0` | 确认应用层代码发生运行时错误并主动退出，排除内存不足 |
| 5 | Tracing | Deepflow | L7 Flow: `GET /work` 返回 `500`；耗时 5.2ms~29.1ms | 确认故障发生在特定 HTTP 请求处理期间 |
| 6 | Tracing | Deepflow | L7 Flow: `GET /work` 返回 `200`；耗时 18.5ms~21.4ms | 作为对照组，证明路由/服务正常，问题具有请求处理偶发性 |
| 7 | K8s State | Kubernetes | Pod IP: `172.16.104.17/32`；网络注解完整 | 确认网络层无阻断或注入异常，隔离出业务代码故障 |

**证据说明：**
1.  **K8s 状态与日志互相印证：** 容器反复退出且返回退出码 2，与日志中明确的 `runtime process exiting` 记录高度一致，确认为应用层主动退出。
2.  **Tracing 与 Logging 关联：** 返回 500 的 L7 Flow 对应了产生 `runtime process exiting` 日志的请求，排除了网络侧或外部健康检查（200 响应）引起的中断，精准定位到 `/work` 接口的特定执行路径。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码在处理 /work 请求时发生运行时错误 → 进程主动退出 (Exit Code 2) 并返回 HTTP 500 → Kubernetes 检测到容器非正常终止 → Pod 处于 CrashLoopBackOff 状态
```

### 根因结论

**已确认根因**：应用代码在处理 `GET /work` 请求时发生运行时异常（Runtime Error），导致应用进程主动终止（Exit Code 2）。

*   **证据支撑**：
    *   日志中捕获到明确的 `runtime process exiting` 模式，且伴随 500 状态码，直接指向代码级的运行时故障（证据 #4、#5）。
    *   容器退出码为 2（非 OOM 导致的 137），且日志内存指标持续为 0，排除了资源限制或 OOM 杀进程的可能性（证据 #1、#3、#4）。
    *   正常的 200 响应日志和 Tracing 证明服务框架本身是可运行的，故障具有偶发性或触发条件依赖性（证据 #6）。
    *   K8s 的 `CrashLoopBackOff` 状态和 `BackOff` 事件是该进程反复崩溃的直接结果（证据 #1、#2）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 17.8s
├─ 并发证据采集: 64.1s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 64.1s (Evidence 55.1s, RCA 8.9s)
└─ 汇总总结: 12.4s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
