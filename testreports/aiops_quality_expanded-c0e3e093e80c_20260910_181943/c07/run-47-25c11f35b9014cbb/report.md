## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod aiops-case-07/workload-dff5cbc6b-sjvxl 处于 CrashLoopBackOff 状态，app 容器退出码 78 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Back-off restarting failed container app in pod workload-dff5cbc6b-sjvxl` (频率: x332 over 82m) | 记录容器 `app` 进入 CrashLoopBackOff 的直接状态与重启频率 |
| 2 | K8s State | Kubernetes | 退出码 78 (`container.last_exit_code`, `container.last_terminated_reason`) | 确认应用进程非正常退出 |
| 3 | Logging | Elasticsearch | 错误日志模式：`CONFIG_MISSING` (HTTP status 500, path `/work`, service `aiops-lab-workload`), 出现 8 次 | 证明应用因缺失配置在运行期间异常退出 |
| 4 | Tracing | Tempo/Deepflow | L7 聚合流：GET `/work` 返回 HTTP 500 (9次); Span `GET /work` 属性 `aiops.observed_mode: config_missing_exit` (Trace ID: `35171f43b5d98aebd6019469374b813c`) | 验证 HTTP 请求失败的具体原因是配置缺失，并关联了应用层的观测模式 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` (Reason: Error, 值: 1); `kube_pod_container_status_restarts_total` (20) | 持续观测到因 Error 导致的重启总数达到 20 |

**证据说明：**
- K8s 状态（#1, #2）与 Metric 数据（#5）一致确认了 `app` 容器处于频繁重启且因 Error 退出的事实。
- 日志（#3）与追踪（#4）提供了根因证据：日志中反复出现的 `CONFIG_MISSING` 模式与追踪 Span 中的 `config_missing_exit` 观测模式相互印证，说明应用因找不到必需配置而主动抛出异常退出（Exit 78）。

## 🎯 根因分析 · g1

### 因果链
```text
应用代码读取配置缺失 (CONFIG_MISSING) → 服务进程抛出异常并退出 (exitCode 78) → K8s 重启策略触发容器频繁重启 → Pod 进入 CrashLoopBackOff 状态，Ready=False
```

### 根因结论
根因已确认：应用启动或请求处理时缺失必需的配置（`CONFIG_MISSING`），导致进程非正常退出（退出码 78）。

- **证据印证**：
  - 应用内部明确记录了 `CONFIG_MISSING` 错误（日志 #3）；
  - 追踪系统明确观测到 `config_missing_exit` 模式（追踪 #4）；
  - 这一退出机制直接导致了 Kubernetes 的 `BackOff` 重启与 `CrashLoopBackOff` 状态（K8s #1, #2, Metric #5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 24.4s
├─ 并发证据采集: 51.7s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 51.7s (Evidence 44.2s, RCA 7.3s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime, pod-oomkilled, pod-config-error
