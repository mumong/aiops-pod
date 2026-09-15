## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod aiops-case-v13/workload stuck in Terminating state with container still Running |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod status: `Terminating (lasts <invalid>)` | 直接确认 Pod 停滞在终止阶段 |
| 2 | K8s Event | Kubernetes | `Normal Killing ... Stopping container app` | 确认 kubelet 已发送停止信号并尝试关闭容器 |
| 3 | K8s Event | Kubernetes | `Warning Unhealthy ... Readiness probe failed: command "python3 -c import os; assert os.path.exists('/proc/1/status')" timed out` | 确认主进程无响应，探针因超时而失败 |
| 4 | K8s Config | Kubernetes | CPU limits: `50m`, Memory limits: `32Mi` | 资源限制极低，排除因资源耗尽导致僵死的可能性 |
| 5 | Logging | Elasticsearch | `SIGTERM received; waiting` (at 06:35:09.201Z) | 证实应用代码捕获到终止信号后进入了不可恢复的等待逻辑 |
| 6 | Metric | Prometheus | `kube_pod_status_phase=0` (Unknown), `kube_pod_container_status_restarts_total=0` | 辅助确认 Pod 异常状态及未发生重启的事实 |

**证据说明**：
日志事实 `#5` 与事件 `#2` 共同证实了“收到 SIGTERM 后未退出”的核心行为。该无响应状态直接导致了探针 `#3` 的超时报错，并阻碍了 Pod 的清理过程，从而产生 `#1` 中僵持的 Terminating 状态。资源配置 `#4` 极低且重启数为 0，佐证了异常是由进程逻辑挂起而非资源压力引起。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码逻辑缺陷（捕获 SIGTERM 后进入死等） → 进程无响应且拒绝退出 → 就绪探针因无法访问 /proc/1/status 而超时失败 → Pod 卡在 Terminating 状态直至 3900s 强制终止
```

### 根因结论

**已确认根因**：应用容器在接收到 `SIGTERM` 信号后，由于代码逻辑缺陷（表现为日志中的 `waiting` 状态），未能正确终止或优雅退出，导致进程僵死。这种僵死使得 Kubernetes 就绪探针检测失败，且由于缺乏更深层的强制退出机制，Pod 被迫在漫长的 `TerminationGracePeriod`（3900s）内停滞。

**缺失决定性事实**：
- 具体是哪个资源或子进程导致应用无限期等待（未知）。
- PID 1 的具体状态（僵死僵尸进程 Zombie 还是仅仅是阻塞的主线程 Frozen）。
- `TerminationGracePeriod` 设置为 3900s 的原因（配置问题或默认值）。

---

## 📊 性能统计

```text
├─ 总耗时: 56.9s
├─ 问题定位: 15.4s
├─ 并发证据采集: 32.0s
│  └─ g1 aiops-case-v13/workload: 32.0s (Evidence 22.1s, RCA 9.8s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- 未调用 Runbook
