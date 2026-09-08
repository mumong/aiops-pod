## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | CrashLoopBackOff (exitCode=78) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.exit_code: 78`, `restart_count: 21` (fact-9a07b758b511, fact-1de97e9354b7) | 确认应用进程反复异常退出 |
| 2 | K8s State | Kubernetes | `container.waiting_reason: CrashLoopBackOff`, `reason: Error` (fact-8f5699dd9688, fact-024db4e49e30) | 确认 K8s 层面已进入重启退避循环 |
| 3 | K8s Event | Kubernetes | `BackOff 6s (x377 over 84m)`, `kubelet` (fact-beaab333efea) | 描述 kubelet 观察到反复失败后的具体退避行为 |
| 4 | Logging | Elasticsearch | `pattern: CONFIG_MISSING`, `http_status: 500`, `path: /work` (fact-3cad91ff2a13 等) | 定位到具体的应用错误类型：配置缺失 |
| 5 | Tracing | Deepflow/Tempo | `Flow: GET /work → 500`, `aiops.observed_mode: config_missing_exit` (fact-056e308a9210, fact-6247a5ec1776 等) | 关联了 HTTP 请求失败与应用配置异常退出状态 |

**证据说明**：
Kubernetes 的 `CrashLoopBackOff` 状态（#2）由 `exitCode=78`（#1）触发。应用日志明确报出 `CONFIG_MISSING` 错误（#4），而 Tracing 证据进一步确认了该错误发生在处理 `/work` 请求时，且模式为 `config_missing_exit`（#5）。这三者形成了完整的闭环证据，证明应用因内部配置缺失导致进程终止，进而引发 K8s 的重启。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap workload-code 缺少应用关键配置键 → 请求触发 CONFIG_MISSING 报错并终止进程 → 容器以 exitCode 78 退出 → CrashLoopBackOff (exitCode=78)
```

### 根因结论

**已确认的根因**：应用代码运行依赖的 ConfigMap (`workload-code`) 中缺失了关键配置项。

这一配置缺失导致应用在处理请求（如 `GET /work`）时触发 `CONFIG_MISSING` 错误，直接致使进程以退出码 `78` 终止。该异常退出状态被 K8s 监控并判定为失败，最终触发 `CrashLoopBackOff` 状态。

**已知局限**：虽然确认为“配置缺失”，但具体的缺失键名称未在观测数据中提供（见 `unknowns`）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 17.8s
├─ 并发证据采集: 81.4s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 81.4s (Evidence 74.4s, RCA 6.8s)
└─ 汇总总结: 10.1s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
