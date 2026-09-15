## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod aiops-case-07/workload-dff5cbc6b-sjvxl 处于 CrashLoopBackOff，容器 app 以 exitCode 78 反复退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: Error; `exit_code`: 78; `restart_count`: 17 | 确认应用进程频繁异常退出及具体终止原因 |
| 2 | K8s Event | Kubernetes | `BackOff restarting failed container app` (286次/69m) | 确认容器处于 CrashLoopBackOff 状态且重启频繁 |
| 3 | Logging | Elasticsearch | Pattern `CONFIG_MISSING` (8次); `http_status`: 500; `path`: `/work`; `service`: `aiops-lab-workload` | 直接指出应用内部检测到的配置缺失故障 |
| 4 | Tracing | Tempo | `aiops.observed_mode`: `config_missing_exit`; `http.response.status_code`: 500 | 提供应用级逻辑视角，证实退出是配置缺失导致的预期行为 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason`=1 (`reason`: Error); `kube_pod_container_status_restarts_total`=17 | 独立数据源验证了容器的终止状态和重启计数 |

**证据综合分析：**
日志（#3）与追踪（#4）高度一致，揭示了应用退出前的具体行为：处理 `/work` 请求时因配置缺失抛出 500 并主动退出。Kubernetes 事件（#2）和指标（#5）证实了这一退出行为导致了持续的 CrashLoopBackOff。日志和追踪中相同的 HTTP 500 响应码与 Kubernetes 记录的终止原因 `Error` 和退出码 `78` 形成闭环，证明应用是按自身逻辑执行退出而非被系统 OOMKilled 或 Liveness 探测误杀。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置缺失 (CONFIG_MISSING) → 业务逻辑检测失败 → 应用进程主动以 exitCode 78 退出 → Kubernetes 触发重启，最终进入 CrashLoopBackOff
```

### 根因结论

**已确认的根因：** 应用因依赖的配置缺失或无效（`CONFIG_MISSING`），在处理 `/work` 端点请求时触发内部错误处理逻辑，主动以 HTTP 500 状态码响应并以 `exitCode 78` 退出进程。

这一机制导致了当前的 `CrashLoopBackOff` 现象。Kubernetes 监控到的终止原因（#1, #5）与应用程序日志（#3, #4）完全吻合，证实了进程退出是应用层面的主动行为。缺少的是关于具体哪一项配置缺失的详细信息，但这不影响根因性质的判定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 28.9s
├─ 并发证据采集: 66.6s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 66.6s (Evidence 57.6s, RCA 8.8s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
