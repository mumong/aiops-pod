## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | Pod aiops-case-07/workload-dff5cbc6b-kmfxx 处于 CrashLoopBackOff 状态，容器反复重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `BackOff 3m47s (x44 over 13m)` | 证实容器已反复重启并被系统限制，进入退避机制 |
| 2 | K8s State | Kubernetes | `exit_code: 78` | 定位进程异常退出的具体退出码 |
| 3 | K8s State | Kubernetes | `container.waiting_reason: CrashLoopBackOff` | 确认异常状态与用户报告一致 |
| 4 | Logging | Elasticsearch | `message: "CONFIG_MISSING", http_status: 500, path: "/work", level: "error"` (8次聚合) | 确认进程在退出前因配置缺失抛出了 500 错误 |
| 5 | Metric | Prometheus | `restarts_total: 7 (13次采样, min: 1.0, last: 7.0)` | 提供量化证据，显示容器在短时间内从 1 次飙升至 7 次重启 |
| 6 | Tracing | Deepflow/Tempo | `GET /work` 返回 `500` (9次聚合), 采样 `span_id: 31c3bc9e6fee046d` | 验证了错误发生在服务处理 HTTP 请求时，与日志中的 `path` 匹配 |

**证据印证说明：**
K8s 状态（#2, #3）与 Metrics 趋势（#5）证实了“反复重启”的持续性；Logging（#4）与 Tracing（#6）共同指向了同一请求路径 `/work` 和同一错误类型 `CONFIG_MISSING`，并明确了 500 状态码；Event（#1）则确认了重启行为已触发 K8s 的 BackOff 控制逻辑。

## 🎯 根因分析 · g1

### 因果链

```text
应用缺失必要配置 (CONFIG_MISSING) → 进程抛出 500 错误并异常退出 (exitCode=78) → 容器频繁重启 (重启 7 次) → K8s 触发 BackOff 策略进入 CrashLoopBackOff 状态
```

### 根因结论

**已确认根因：应用启动或请求处理期间因缺失关键配置（Key 未知）主动退出。**

- 证据 #4 (Logging) 与证据 #6 (Tracing) 共同证实，应用在处理 `GET /work` 时明确记录了 `CONFIG_MISSING` 错误并返回 500。
- 证据 #2 (K8s State) 显示容器以退出码 78 终止，这与业务层处理失败主动退出的行为相符，排除了 OOM 或资源限制导致的系统级杀进程（通常退出码为 137）。
- 证据 #1 (Event) 与证据 #5 (Metric) 证实了该异常行为导致了频繁的容器重启，最终触发 Kubernetes 的重启退避机制（CrashLoopBackOff）。
- 缺少的决定性事实：具体的配置键名（Key）以及 `workload-code` ConfigMap 中实际存在的键值对，用于精确修复配置映射。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 25.6s
├─ 并发证据采集: 53.0s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 53.0s (Evidence 42.2s, RCA 10.7s)
└─ 汇总总结: 10.7s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
