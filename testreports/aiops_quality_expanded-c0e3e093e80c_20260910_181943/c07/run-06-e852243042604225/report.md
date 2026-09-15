## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | 容器应用启动后在运行时无法找到必需配置，导致在HTTP请求处理中抛出CONFIG_MISSING错误，随后以退出码78异常退出，引发CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-07/workload-dff5cbc6b-sjvxl` 状态为 `Running`，但容器 `app` 处于 `CrashLoopBackOff`，重启计数为 6（fact-086f26cbcb7f, fact-920efba5871e） | 确立应用进程频繁异常退出的事实 |
| 2 | K8s State | Kubernetes | 容器退出码为 78（fact-920efba5871e），Kubelet 报告 BackOff 警告（fact-bf95875a3f68） | 确认异常终止的具体退出码及调度器的反馈 |
| 3 | Logging | Elasticsearch | 日志聚合 8 次，显示 `CONFIG_MISSING` 错误（fact_type: log），HTTP 状态码 500，路径 `/work`（fact-405c0c23fe72 等） | 明确应用内部报错为配置缺失，这是导致退出的直接原因 |
| 4 | Tracing | Deepflow | 等价 L7 Flow 聚合 9 次，`GET /work` 返回 500，源 IP `172.16.104.8` 到目的 IP `172.16.104.63`（fact-615d6055f684 等） | 从网络层确认对 Pod IP 的访问均失败 |
| 5 | Tracing | Tempo | Span `GET /work` 记录 `aiops.observed_mode: config_missing_exit`，对应 Trace ID `a358165e4c5df7b2882c057473693f30`（fact-1b066c576e8b） | 追踪日志中出现的 Trace ID 与 Trace 数据中的自定义属性 `config_missing_exit` 相互印证，确认业务逻辑识别到了该状态 |

证据 1、2 与 3 构成了闭环：Pod 日志（证据 3）显示应用因为 `CONFIG_MISSING` 抛出 500 错误并终止，K8s 状态（证据 1、2）显示该终止伴随特定的退出码 78 并触发了重启循环。追踪数据（证据 5）通过 Trace ID 关联，在应用 Span 级别确认了 `config_missing_exit` 模式，排除了网络或基础设施层面的故障，证明是应用内部的配置加载问题。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动后未找到必需配置（CONFIG_MISSING） → 处理 HTTP 请求抛出 500 错误并捕获异常 → 进程以退出码 78 终止 → 容器进入 CrashLoopBackOff 循环重启
```

### 根因结论

已确认根因为：**应用容器因在运行时缺失必需配置导致崩溃重启。**

具体表现为容器 `app` 在启动后处理 HTTP 请求（路径 `/work`）时，由于配置缺失（`CONFIG_MISSING`）触发 `500` 错误，随后应用进程主动以 `exit_code=78` 终止。Kubernetes 检测到该非零退出码后，按照重启策略不断重启容器，直至触发 `CrashLoopBackOff` 状态。证据链中日志错误模式（fact-405c0c23fe72 等）、Trace 中的 `config_missing_exit` 状态（fact-1b066c576e8b）与 K8s 退出的退出码 78（fact-920efba5871e）完全吻合。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 21.4s
├─ 并发证据采集: 49.8s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 49.8s (Evidence 41.2s, RCA 8.5s)
└─ 汇总总结: 12.7s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
