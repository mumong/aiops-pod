## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v09/workload` | CrashLoopBackOff | Pod workload (aiops-case-v09) 处于 CrashLoopBackOff 状态，kubelet 在过去 54 分钟内记录了 245 次 BackOff 警告，重启次数达到 15 次。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff (x245 over 54m) kubelet Back-off restarting failed container app` | 确认 Pod 正处于 CrashLoopBackOff 状态且频繁重启 |
| 2 | K8s State | Kubernetes | `last_terminated_reason: Error`, `last_exit_code: 1` | 确认容器异常退出及退出原因 |
| 3 | Logging | Elasticsearch | `FileNotFoundError` / `Path('/input/app.conf').read_text()` 调用栈 | 证明进程因读取缺失文件导致崩溃 |
| 4 | K8s Config | Kubernetes | `resource_request.cpu: 5m`, `resource_limit.cpu: 50m`, `resource_request.memory: 8Mi`, `resource_limit.memory: 32Mi` | 确认资源配置极小，排除资源超限（OOM/CPU Throttling）作为根因 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason=1` (reason: Error), `kube_pod_container_status_restarts_total=15` | 独立指标佐证容器以 Error 状态终止及重启计数 |

**证据关联性说明：**
K8s 事件与状态指标共同确立了故障现象（CrashLoopBackOff），而 Elasticsearch 日志中关于 `read_text()` 抛出 `FileNotFoundError` 的异常堆栈（第 3 行），结合 K8s 状态中记录的 `Error` 原因和 `exit_code: 1`（第 2 行），形成了完整的因果闭环，直接指向了根因。资源配置证据（第 4 行）则排除了基础设施层面的资源瓶颈。

## 🎯 根因分析 · g1

### 因果链

```text
配置文件 /input/app.conf 缺失 → Python 读取文件时抛出 FileNotFoundError → 容器进程以 Exit Code 1 异常退出 → Kubernetes 触发 CrashLoopBackOff
```

### 根因结论

**已确认根因**：应用程序启动脚本尝试读取的配置文件 `/input/app.conf` 不存在或挂载错误。

证据链（证据 1、2、3）高度一致：日志明确显示应用尝试使用 `Path('/input/app.conf').read_text()` 打开文件时发生 `FileNotFoundError`，导致 Python 进程终止。这一具体错误解释了 K8s 记录的 `last_terminated_reason: Error` 和 `exit_code: 1`，同时也解释了 kubelet 为何在 54 分钟内触发了 245 次 `BackOff` 警告。资源监控数据确认了该故障与资源限制无关。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 23.2s
├─ 并发证据采集: 55.6s
│  └─ g1 aiops-case-v09/workload: 55.6s (Evidence 47.1s, RCA 8.3s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-v09/workload**: pod-crashloop-runtime, pod-config-error, pod-oomkilled
