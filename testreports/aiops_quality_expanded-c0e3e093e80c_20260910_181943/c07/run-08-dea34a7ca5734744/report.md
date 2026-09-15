## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod aiops-case-07/workload-dff5cbc6b-sjvxl 处于 CrashLoopBackOff 状态，容器反复重启 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` 状态 `Waiting`: `CrashLoopBackOff` | 确认 Pod 当前处于异常循环重启状态 |
| 2 | K8s Event | Kubernetes | 事件 `BackOff`: `Back-off restarting failed container app ... 4m25s (x42 over 14m)` | 证实容器反复退出，kubelet 正在实施退避机制 |
| 3 | K8s State | Kubernetes | 退出原因 `last_terminated_reason`: `Error`; 退出码 `last_exit_code`: `78` | 表明应用异常退出且返回非标准 0/1 码，指向应用层逻辑错误 |
| 4 | Logging | Elasticsearch | 日志模式 `CONFIG_MISSING` (HTTP 500); 出现 8 次; `numeric_fields`: `allocated_mib` 始终为 0 | 日志直接记录了应用检测配置缺失并返回 500 错误的事实 |
| 5 | Tracing | Tempo | Trace `a358165e4c5df7b2882c057473693f30`: `GET /work` 返回 500, 属性 `aiops.observed_mode`: `config_missing_exit` | 与日志关联，确认应用因特定模式主动终止，内存占用为 0 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: `7`; `reason`: `Error` | 独立观测到容器重启次数与异常终止原因 |

日志记录的 `CONFIG_MISSING` 错误、Trace 中记录的 `config_missing_exit` 模式以及退出码 `78` 高度一致，共同指向容器内部业务逻辑的异常。Prometheus 指标确认了该错误导致的实际重启行为。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置项 FAILURE_MODE 被设为 config_missing_exit → 应用启动检测到该模式，主动返回 HTTP 500 并报错 CONFIG_MISSING → 容器以 Exit Code 78 异常终止 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为**应用容器内部配置触发了预期的异常退出逻辑**。

依据证据：
1.  **退出特征明确**：容器以 `Exit Code 78` 退出，结合日志 `CONFIG_MISSING` [4] 和 Trace 属性 `aiops.observed_mode: config_missing_exit` [5]，表明应用并非崩溃，而是根据特定配置 `FAILURE_MODE=config_missing_exit` 主动抛错退出。
2.  **重启循环确认**：K8s 事件 [2] 和 Metrics [6] 确认了因该退出机制（Reason: `Error`）导致的 `CrashLoopBackOff` 状态。

现有证据链完整，确认该现象由应用内建的特殊测试/故障模式（`config_missing_exit`）导致。

---

## 📊 性能统计

```text
├─ 总耗时: 3.0m
├─ 问题定位: 18.2s
├─ 并发证据采集: 150.2s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 150.2s (Evidence 139.5s, RCA 10.5s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
