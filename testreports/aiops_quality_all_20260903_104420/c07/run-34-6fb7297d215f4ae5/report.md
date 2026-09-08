## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | Pod workload-dff5cbc6b-kmfxx 处于 CrashLoopBackOff 状态，容器反复重启且 HTTP 服务返回 500 错误。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff ... Back-off restarting failed container app` (over 60m) | 确认容器崩溃触发 Kubelet 的退避重启机制 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason: Error`, `exit_code: 78` | 确认容器因应用层错误非正常退出 |
| 3 | Logging | Elasticsearch | `ERROR CONFIG_MISSING` at `/work`, HTTP Status 500, `service: aiops-lab-workload` (8 occurrences) | 揭示应用崩溃的直接原因为配置缺失 |
| 4 | Tracing | Deepflow/Tempo | Span: `GET /work`, HTTP Status 500, `aiops.observed_mode: config_missing_exit` | 验证请求失败的具体路径及模式，并关联到同一组 `trace_id` |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = 1 (CrashLoopBackOff), `restarts_total` = 16 | 量化观察窗内的重启频率与当前停滞状态 |

**证据互证说明：**
证据 2（Exit Code 78）与证据 3（CONFIG_MISSING 日志）及证据 4（`config_missing_exit` Span）形成闭环，证明异常源于应用启动/运行逻辑中的硬编码错误而非资源调度。证据 1（K8s Event）与证据 5（Prometheus Metrics）从调度器与采集器视角，交叉确认了该异常导致的 CrashLoopBackOff 现象。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动/运行配置缺失 (CONFIG_MISSING) → 应用进程捕获错误并退出 (Exit Code 78) → 直接失败 → Pod 处于 CrashLoopBackOff 状态，HTTP 服务持续返回 500
```

### 根因结论

**已确认根因**：应用代码存在硬编码缺陷，在处理 `/work` 请求时因缺失必要配置（`CONFIG_MISSING`）主动终止进程。

该配置缺失导致应用进程以 `Exit Code 78` 异常退出。Kubernetes 调度器检测到该退出后，触发指数退避重启策略（Back-off），导致容器反复重启且无法进入 Running 状态。证据 3（日志中的 `CONFIG_MISSING`）与证据 4（Tracing 中的 `config_missing_exit` 模式）为直接定性证据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.0s
├─ 并发证据采集: 40.8s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 40.8s (Evidence 33.4s, RCA 7.2s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime, pod-oomkilled
