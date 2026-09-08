## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | Pod workload-dff5cbc6b-kmfxx 持续处于 CrashLoopBackOff 状态，容器 app 启动后立即退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s | `container.last_terminated_reason: Error` (Container `app`, fact-`b0c22264214b`) | 记录容器最后一次异常退出的直接原因 |
| 2 | K8s State | K8s | `pod.container.last_exit_code: 78` (Container `app`, fact-`56d614fb4173`) | 应用层返回的具体退出状态码，指向应用内部逻辑错误 |
| 3 | Logging | Elasticsearch | 日志模式：`event: http_request, level: error, message: CONFIG_MISSING, http_status: 500, path: /work` (fact-`1dfce90a25bc` 等8条) | 直接暴露了应用逻辑中“配置缺失”导致拒绝服务的具体原因 |
| 4 | Tracing | Tempo | `GET /work` Span, `http.response.status_code: 500`, `aiops.observed_mode: config_missing_exit` (Trace ID: `da9999ae734835080b2f252e105e1ce7`, fact-`9621698453cf`) | 追踪数据印证了应用进程在处理请求时检测到配置缺失并主动退出 |

以上证据高度一致，K8s 状态的异常终止 (Exit 78) 是 Logging 和 Tracing 中应用层检测配置缺失并报错 500 并退出的外在表现。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码执行时检测到配置文件缺失（CONFIG_MISSING） → 进程以应用层错误码 78 主动退出 → 容器状态进入 Terminated/Error → Pod 状态因重启失败进入 CrashLoopBackOff
```

### 根因结论

根因确认：应用容器 `app` 在启动或运行过程中，因未能加载必要的配置文件（触发 `CONFIG_MISSING` 异常），导致进程主动以退出码 `78` 终止。Kubelet 在尝试重启容器时反复遭遇相同的应用层错误，最终触发 `CrashLoopBackOff`。

- **已验证证据**：K8s 状态明确记录最后退出原因为 `Error`，退出码为 `78`。Elasticsearch 日志聚合事实显示，应用内部产生了 8 次 `CONFIG_MISSING` 错误（`http_status: 500`）。Tempo 追踪 Span 确认了该异常发生在处理 `/work` 请求时，并明确记录观察模式为 `config_missing_exit`。
- **关联性**：应用层返回的 78 号退出码与 Tracing 中的 `config_missing_exit` 模式以及日志的 `CONFIG_MISSING` 错误完全一致，证实了该异常为应用内部逻辑错误引发，而非资源耗尽或外部依赖故障。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 21.2s
├─ 并发证据采集: 59.7s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 59.7s (Evidence 51.7s, RCA 7.9s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
