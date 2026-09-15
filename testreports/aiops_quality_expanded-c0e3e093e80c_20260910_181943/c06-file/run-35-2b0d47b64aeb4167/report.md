## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v09/workload` | CrashLoopBackOff | workload in CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff restarting failed container app in pod workload_aiops-case-v09(5746c496-b67c-4906-aabb-e71359674305)` | 直接描述崩溃循环现象 |
| 2 | K8s State | Kubernetes | `last_terminated_reason: Error`, `last_exit_code: 1` | 确认容器异常退出机制 |
| 3 | K8s Config | Kubernetes | `memory_request: 8Mi`, `memory_limit: 32Mi`, `cpu_request: 5m`, `cpu_limit: 50m` | 确认资源配额充足且合理 |
| 4 | Logging | Elasticsearch | `FileNotFoundError: [Errno 2] No such file or directory: '/input/app.conf'` | 揭示容器启动崩溃的具体原因 |
| 5 | Logging | Elasticsearch | `print(Path('/input/app.conf').read_text())` | 证明导致崩溃的代码行为 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1` (reason: CrashLoopBackOff) | 从监控维度印证 Pod 等待重启状态 |
| 7 | Metric | Prometheus | `kube_pod_container_status_restarts_total=13` | 佐证该容器已被重启多次 |

**证据关联说明：**
- 证据 1、2、6 共同指向 Pod 因异常退出而陷入 CrashLoopBackOff 状态。
- 证据 4 与 5 构成了因果链条中的核心环节，直接证明了 Python 脚本在执行 `Path('/input/app.conf').read_text()` 时因文件缺失而抛出异常。
- 证据 3 确认了内存和 CPU 限制并非导致崩溃的因素，排除了资源限制的可能。

## 🎯 根因分析 · g1

### 因果链
```text
EmptyDir 卷中缺少 '/input/app.conf' 文件 → Python 启动脚本执行 read_text 抛出 FileNotFoundError → 容器进程终止并退出码 1 → kubelet 触发 CrashLoopBackOff 循环重启
```

### 根因结论
已确认的根因为：**容器启动命令依赖的文件 `/input/app.conf` 不存在于挂载的 EmptyDir 卷中**。

日志中的 `FileNotFoundError` (证据 4) 直接印证了启动脚本 (证据 5) 因无法读取配置文件而崩溃，进而导致 Kubernetes 报告 `CrashLoopBackOff` (证据 1、6) 和异常退出 (证据 2)。监控数据 (证据 7) 进一步确认了容器已重启 13 次。现有证据链完整，足以解释该组异常的全部现象。

---

## 📊 性能统计

```text
├─ 总耗时: 53.2s
├─ 问题定位: 9.6s
├─ 并发证据采集: 34.4s
│  └─ g1 aiops-case-v09/workload: 34.4s (Evidence 27.1s, RCA 7.2s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- 未调用 Runbook
