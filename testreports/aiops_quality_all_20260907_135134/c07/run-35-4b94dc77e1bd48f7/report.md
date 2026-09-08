## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | Running | Pod aiops-case-07/workload-dff5cbc6b-fkzvn 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `workload-dff5cbc6b-fkzvn` (Pod), status: `Running`, phenomenon: `CrashLoopBackOff` | 呈现容器频繁崩溃且无法稳定运行的最终状态 |
| 2 | K8s Event | Prometheus | `kube_pod_container_status_waiting_reason` = `CrashLoopBackOff` (sample: 1) | 确认 kubelet 处于等待容器重启的退避状态 |
| 3 | K8s Event | Prometheus | `kube_pod_container_status_last_terminated_reason` = `Error` (sample: 1) | 证实容器进程此前以异常方式终止 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 18 | 提供容器反复重启的具体频次证据 |
| 5 | Logging | Elasticsearch | Pattern `CONFIG_MISSING`, HTTP status 500, path `/work`, 8 occurrences (trace_ids: `016132e7...` 等) | 记录具体的应用错误类型、HTTP 响应码及发生频率 |
| 6 | Tracing | Deepflow/Tempo | Flow: `GET /work` → 500 (9 occurrences); Span trace_id: `7ed664affe6fdd8e75610015d3c8e3a3`, attribute `aiops.observed_mode: config_missing_exit` | 关联底层网络请求与日志模式，明确根因指向配置缺失 |

**证据说明：**
1. 指标层（证据 2、3、4）与现象描述（证据 1）互证，确认了容器因异常退出（`Error`）被 Kubernetes 反复重启（`restarts: 18`），且当前处于 CrashLoopBackOff 状态。
2. 日志层（证据 5）与追踪层（证据 6）提供了崩溃的具体上下文：应用在处理 `/work` 请求时明确返回 `CONFIG_MISSING` 错误导致 HTTP 500。追踪数据中的 `config_missing_exit` 标记进一步锁定了配置缺失是导致进程终止的直接原因。

## 🎯 根因分析 · g1

### 因果链

```text
应用缺失必需配置 (CONFIG_MISSING) → 应用处理请求失败 (HTTP 500) → 容器进程崩溃退出 → 用户可见现象 (CrashLoopBackOff)
```

### 根因结论

已确认根因为：应用启动或运行时因缺失必需配置（`CONFIG_MISSING`），在处理请求时抛出异常并返回 HTTP 500 错误，进而导致容器进程非正常退出。

该配置缺失问题直接触发了 Kubernetes 的重启机制。由于进程不断崩溃退出（证据 2、3、5、6），kubelet 执行指数退避重启策略，最终使 Pod 进入 `CrashLoopBackOff` 状态（证据 1、4）。

缺失的具体配置名称或 ConfigMap/Secret 键值，以及导致该配置缺失的部署配置源头，当前证据不足。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 22.7s
├─ 并发证据采集: 75.0s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 75.0s (Evidence 64.9s, RCA 10.0s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-oomkilled
