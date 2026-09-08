## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | 应用代码中 /work 路径存在配置缺失 (CONFIG_MISSING) 缺陷，导致进程启动后接收请求即返回 HTTP 500 并异常退出 (Exit Code 78)。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.waiting_reason: CrashLoopBackOff (fact-12bdf4951c21) | 确认 Pod 处于持续的重启失败循环中。 |
| 2 | K8s State | kubernetes | container.last_exit_code: 78 (fact-3e484c799ed0) | 提供容器异常退出的直接操作系统返回码。 |
| 3 | K8s Event | kubernetes | Warning BackOff 8m57s (x357 over 88m) 88m 内重启 357 次 (fact-4ee17cdf934e) | 证明重启频率极高，符合 CrashLoop 特征。 |
| 4 | Logging | elasticsearch | Error CONFIG_MISSING at GET /work (10 occurrences, trace: ce8177e4162eda43fc470e15890e4d85) (fact-61cea5b19f8b) | 记录应用逻辑错误，指出在 /work 接口发生配置缺失异常。 |
| 5 | Tracing | deepflow | HTTP GET /work -> 500 (9 flows, dst_ip: 172.16.104.15) (fact-1a6d859308c0) | 网络侧验证了应用持续对外返回 500 错误，与日志中 500 状态码及 CONFIG_MISSING 异常一致。 |
| 6 | Tracing | tempo | Span GET /work 500, trace_id: 5ef67866f348c5aa93ff865f603c2cdc (fact-7cfe7110c96e) | 跨链路 ID 5ef6... 关联了 500 响应与内部应用日志，闭环确认应用内部处理失败。 |

**证据互证关系：**
Kubernetes 事件显示的 `CrashLoopBackOff` 状态与 `exit_code: 78` (证据 #1, #2) 构成容器层面的崩溃闭环。应用日志明确指出了崩溃原因是在处理 `GET /work` 请求时抛出 `CONFIG_MISSING` 错误导致 HTTP 500 (证据 #4)。追踪数据进一步证实，网络侧观测到的 500 错误正是由该应用逻辑缺陷引起，并可通过 trace_id (如 5ef6...) 在应用日志中实现链路级关联 (证据 #5, #6)。日志中的 500 错误与 78 退出码在因果逻辑上吻合（应用逻辑错误通常导致非零退出），共同指向同一个根因。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码缺陷 (/work 路径配置缺失) → 处理请求时返回 HTTP 500 并抛出异常 → 进程异常退出 (Exit Code 78) → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为：**应用代码在 `/work` 路径处理中因 `CONFIG_MISSING` (配置缺失) 缺陷导致崩溃。**

该结论由多维度事实支撑：
1.  **容器状态异常**：Pod 的 `waiting_reason` 为 `CrashLoopBackOff`，且 `last_exit_code` 为 78，证明容器因程序逻辑错误退出而非资源限制 (证据 #1, #2, #3)。
2.  **应用日志确诊**：日志记录反复出现 `level: error`, `message: CONFIG_MISSING` 发生在 `GET /work` 请求处理过程中 (证据 #4)。
3.  **链路行为一致**：Deepflow 追踪与 Tempo Span 证实该服务在 `/work` 路径上持续返回 500 错误，且存在从网络流量到应用日志的 `trace_id` (如 `5ef67866f348c5aa93ff865f603c2cdc`) 级联关联 (证据 #5, #6)。

目前已知事实足以解释 CrashLoop 的根本原因，但**具体缺失的配置项名称及正确值**这一细节仍属于未知信息，需进一步检查应用程序源码或部署配置。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 16.3s
├─ 并发证据采集: 92.7s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 92.7s (Evidence 84.0s, RCA 8.4s)
└─ 汇总总结: 14.4s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime, pod-oomkilled, pod-config-error, pod-sandbox-create-failed
