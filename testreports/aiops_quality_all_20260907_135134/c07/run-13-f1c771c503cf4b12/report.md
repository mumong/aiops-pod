## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: app, Error | 确认异常终止的直接状态 |
| 2 | K8s State | kubernetes | `container.last_exit_code`: app, 78 | 确认应用异常退出码 |
| 3 | Logging | elasticsearch | Pattern: `CONFIG_MISSING`, HTTP 500, `/work` (发生 8 次) | 确认根因为配置缺失 |
| 4 | K8s Event | kubernetes | Warning BackOff: `4m38s (x86 over 24m)` | 确认故障表现为崩溃重启循环 |
| 5 | K8s Config | kubernetes | `container.resource_limit.memory`: app, 96Mi | 排除内存硬限制导致 OOM 的可能 |
| 6 | Tracing | deepflow+tempo | Flow: GET `/work` HTTP 500 (发生 9 次) | 确认应用对外提供 HTTP 服务失败 |

**证据印证说明：**
- 日志 (fact-35b86fb0867e) 中的 `CONFIG_MISSING` 与 K8s 状态中的 `last_terminated_reason: Error` 互相印证，说明进程是正常启动后检查到缺失项并主动退出的，而非崩溃。
- Tracing (fact-80dca9b68ddb) 显示的 500 错误与日志中的 `http_status: 500` 时间范围高度重合，证实了异常状态对外表现为 HTTP 服务不可用。
- K8s Event (fact-ce95d0935d53) 明确指出了 CrashLoopBackOff，这是前两项（退出码 78 及 500 错误）在 K8s 调度层面的直接后果。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动依赖的配置项缺失 → 应用启动逻辑捕获缺失并执行退出流程（exit code 78） → kubelet 检测到容器非零退出码并触发重启 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

**已确认的根因**：应用启动时因配置缺失（CONFIG_MISSING）导致初始化失败，以退出码 78 异常终止。

证据支撑：
- **直接失败**：K8s 事实显示容器 `app` 退出码为 `78` (fact-03c42a37ab03)，终止原因为 `Error` (fact-3cb07362eb1b)。
- **根因定位**：日志系统聚合事实 (fact-35b86fb0867e) 明确捕获了 `CONFIG_MISSING` 事件，且伴随 HTTP `500` 状态码。
- **现象确认**：K8s Event (fact-ce95d0935d53) 记录了过去 24 分钟内 8 次的 `BackOff` 重启警告，以及 Tracing (fact-80dca9b68ddb) 中 9 次 `GET /work` 的 `500` 响应。
- 综合以上事实，应用在启动阶段遇到环境配置缺失，导致进程退出；Kubelet 尝试重启后再次失败，进而进入 CrashLoopBackOff 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 24.6s
├─ 并发证据采集: 41.7s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 41.7s (Evidence 33.4s, RCA 8.1s)
└─ 汇总总结: 11.5s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-oomkilled, pod-crashloop-runtime
