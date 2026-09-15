## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod容器启动时因检测到应用配置缺失(CONFIG_MISSING)，主动抛出500错误并以退出码78终止进程。由于关键配置缺失问题未得到修正，Kubernetes反复重启容器并进入CrashLoopBackOff状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` | `BackOff  4m34s (x332 over 79m)` (fact-780104c50c0a) | 确认容器处于持续的 BackOff 重启循环中 |
| 2 | K8s State | K8s API | `waiting_reason: CrashLoopBackOff`, `last_terminated_reason: Error`, `exit_code: 78` (fact-b433a5a40519, fact-9cce0d23013e, fact-202ab42b0935) | 描述当前终止的具体状态与异常退出码 |
| 3 | Logging | `elasticsearch` | `event: http_request`, `level: error`, `message: CONFIG_MISSING`, `http_status: 500` (pattern repeated 8 times, fact-50b4402484fb) | 直接证实应用因配置缺失主动返回 500 错误 |
| 4 | Tracing | `tempo` | `span_id: 87f4788bf565213d`, `aiops.observed_mode: config_missing_exit`, `http.response.status_code: 500` (fact-04acb98e6dbc) | 独立观测维度验证了 500 状态码与 `config_missing_exit` 机制 |

上述证据形成闭环：K8s 记录的 `CrashLoopBackOff` 状态与 `exit_code=78`（证据2）与日志中捕获的 `CONFIG_MISSING` 错误（证据3）完全吻合。Tracing 数据（证据4）进一步独立证实了应用是在检测到配置缺失后主动返回 500 并退出的。

## 🎯 根因分析 · g1

### 因果链
```text
应用启动时检测到必需配置项缺失 → 应用程序记录CONFIG_MISSING错误并返回HTTP 500，随后以Exit Code 78主动退出 → Kubelet检测到容器异常退出并触发BackOff策略 → Pod状态进入CrashLoopBackOff，持续重启失败
```

### 根因结论
已确认根因为 Pod 内的 `app` 容器在启动阶段检测到关键配置项缺失，主动抛出 `CONFIG_MISSING` 错误并返回 HTTP 500，随后以退出码 78 终止进程，导致 Kubernetes 进入 CrashLoopBackOff 状态。该结论得到 K8s 退出码、日志错误模式和 Tracing 观测模式的三方印证（证据2、3、4）。由于缺失的具体配置项名称未在观测中捕获，其详细参数构成未知的局限性（unknowns）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 16.7s
├─ 并发证据采集: 69.0s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 69.0s (Evidence 58.5s, RCA 10.4s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
