## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | ConfigMap 'workload-code' 中缺少应用程序所需的配置文件，导致容器进程在处理 HTTP 请求时因 'CONFIG_MISSING' 异常退出（exitCode=78）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: CrashLoopBackOff; `container.last_terminated_reason`: Error (fact-0f6e9710aec6) | 确认容器处于反复崩溃重启状态 |
| 2 | K8s State | kubernetes | `container.last_exit_code`: 78 (fact-15276cebbd3f) | 提供具体的进程退出码，用于关联应用日志 |
| 3 | K8s Event | kubernetes | `BackOff restarting failed container app` (fact-e07fe903ced2) | 佐证重启循环现象 |
| 4 | Logging | elasticsearch | `CONFIG_MISSING` 错误日志 (8次) (fact-5c1f4e8b8b14) | 指出缺失核心配置文件，直接解释 exitCode=78 的原因 |
| 5 | Tracing | Deepflow | HTTP GET `/work` 返回 500，关联 Trace ID: `65684c8c...` (fact-124bc51d98af) | 证实业务请求因配置问题导致服务不可用 |
| 6 | Tracing | Tempo | Trace ID: `65684c8c...` Span 属性 `aiops.observed_mode=config_missing_exit` (fact-408947ed4dba) | 将异常 HTTP 请求与配置缺失日志在 Trace 层面关联 |
| 7 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 17 (fact-b6899f6ff399) | 量化重启频率，确认该状态为持续发生 |

证据链中，日志与 Trace 通过 Trace ID `65684c8c074b2b13bde640e742613caa` 精准关联，确认 `/work` 请求失败是由 `CONFIG_MISSING` 引起的。K8s 的 `CrashLoopBackOff` 状态与 `exit_code=78` 与日志中的异常退出机制一致。Metric 重启计数证实该故障为持续性现象。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'workload-code' 缺少应用所需配置文件 → 容器进程在处理 HTTP 请求时抛出 CONFIG_MISSING 异常 → 容器以 exitCode=78 退出 → K8s 触发重启循环并进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为 **ConfigMap 'workload-code' 中缺少应用程序所需的配置文件**。

该配置缺失导致应用在处理请求时抛出 `CONFIG_MISSING` 异常，进程随即以退出码 78 终止。这一过程由日志证据 (4)、Trace 证据 (5, 6) 及 K8s 退出码 (2) 直接证实。该异常引发容器反复重启，表现为 K8s `CrashLoopBackOff` (1) 和 Metric 中高达 17 次的重启计数 (7)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 22.7s
├─ 并发证据采集: 63.2s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 63.2s (Evidence 56.0s, RCA 7.0s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
