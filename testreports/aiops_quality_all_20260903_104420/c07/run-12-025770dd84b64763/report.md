## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | Pod aiops-case-07/workload-dff5cbc6b-kmfxx 处于 CrashLoopBackOff 状态，容器 app 因进程异常退出（Exit 78）而持续重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container app last_terminated_reason=Error, exit_code=78, restart_count=8 | 直接确认应用进程异常退出及高频率重启现象 |
| 2 | K8s Event | Kubernetes | BackOff 89 次/20m | 确认 K8s 执行了持续的重启与退避策略 |
| 3 | K8s Config | Kubernetes | resource_request.cpu=20m, memory=24Mi; resource_limit.cpu=200m, memory=96Mi | 确认非资源超限（OOM/CPU Throttling）导致的异常 |
| 4 | Metric | Prometheus | kube_pod_container_status_last_terminated_reason[reason="Error"] | 辅助确认最近一次退出原因为 Error |
| 5 | Metric | Prometheus | kube_pod_container_status_waiting_reason[reason="CrashLoopBackOff"] | 辅助确认容器当前处于等待重试状态 |
| 6 | Metric | Prometheus | kube_pod_container_status_restarts_total=8 | 辅助量化重启次数，与 K8s 状态一致 |
| 7 | Logging | Elasticsearch | http_request level="error", message="CONFIG_MISSING", path="/work", status=500 (8次) | 提供应用层直接失败原因为配置缺失 |
| 8 | Tracing | Tempo/Deepflow | Flow GET /work 500 (9次), 关联 Trace ID (如 e6d07428...) | 提供 L7 流量证据，确认 500 错误与日志日志一致 |

**证据分析：**
Kubernetes 状态确认 Pod 因进程退出（Code 78）进入重启循环。Logging 和 Tracing 均一致指向 `/work` 路径上的 `CONFIG_MISSING` 错误（HTTP 500）。Kubernetes 配置资源限制较低但异常代码与事件均非资源不足特征，Metric 维度作为重复观测确认了退出原因与重启状态。应用进程在检测到配置缺失后主动终止（Exit 78），导致 Pod 崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
应用关键配置缺失 (CONFIG_MISSING) → 应用处理请求抛出异常并返回 500 → 进程以 Exit Code 78 终止 → Pod CrashLoopBackOff
```

### 根因结论

**已确认根因：应用进程因检测到 `CONFIG_MISSING`（关键配置缺失）而主动终止。**

应用日志中 8 次捕获到 `CONFIG_MISSING` 错误（来源 #7），Tracing 数据证实了 9 次针对 `/work` 接口的 500 错误响应（来源 #8）。应用进程以退出码 78 退出，导致 Kubernetes 触发重启机制并进入 CrashLoopBackOff 状态（来源 #1, #2）。

**未知与局限性：**
虽然确认了“配置缺失”是导致应用退出的直接原因，但输入事实中未包含 ConfigMap 或 Secret 的挂载状态与注入结果，因此无法确认配置项是否未在 Pod 中正确定义、挂载失败或环境变量注入失败。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 15.0s
├─ 并发证据采集: 59.4s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 59.4s (Evidence 48.0s, RCA 11.3s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime, pod-oomkilled, pod-config-error, pod-imagepull-failed
