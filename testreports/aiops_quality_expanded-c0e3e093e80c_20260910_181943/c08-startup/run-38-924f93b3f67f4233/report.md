## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | 容器内存资源限制(64Mi)严重低于应用程序启动时申请的内存大小(256Mi)，导致Linux内核OOM Killer强制终止进程，引发CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | container.last_terminated_reason | container=app, reason=OOMKilled | 确证触发 OOM Killer 的直接原因 |
| 2 | K8s State | container.last_exit_code | container=app, exit_code=137 | 对应 OOM Kill 的标准退出码 |
| 3 | K8s Config | container.resource_limit.memory | container=app, value=64Mi | 设定了极低的内存硬限制 |
| 4 | K8s Config | container.resource_request.memory | container=app, value=8Mi | 资源请求量与限制量差异巨大 |
| 5 | Logging | log.message | timestamp=2026-09-14T10:49:20.610Z, message="startup allocation 256Mi" | 证实应用启动需求远超限制容量 |
| 6 | Metric | kube_pod_container_status_waiting_reason | timestamp=2026-09-14T11:02:04Z, value=1, reason=CrashLoopBackOff | 验证 Pod 处于持续的重启等待状态 |
| 7 | Metric | kube_pod_container_status_restarts_total | timestamp=2026-09-14T11:02:04Z, value=23 | 显示重启频率极高，符合 CrashLoopBackOff 特征 |

**证据互证说明：**
日志中的启动需求（256Mi）与 Kubernetes 配置中的硬限制（64Mi）形成直接的数量级冲突；这种资源超额使用被 OOM Killer 捕捉后产生退出码 137 和 OOMKilled 终止原因；Kubernetes 事件和 Metrics 数据进一步印证了系统因无法稳定维持容器状态而进入 CrashLoopBackOff 循环的事实。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存 Limit (64Mi) 配置过低 → 应用启动申请 256Mi 导致资源超额 → 触发 OOM Killer 发送 SIGKILL (Exit 137) → 容器终止并重启，陷入 CrashLoopBackOff
```

### 根因结论

已确认的根因是容器内存资源配置严重不足（限制 64Mi 低于应用启动需求 256Mi）。这种资源不匹配导致 Linux 内核 OOM Killer 强制终止进程，直接表现为容器异常退出及后续的 CrashLoopBackOff 状态。证据编号 [1, 2, 3, 5, 6, 7] 从配置、日志、内核状态及运行结果四个维度完整闭环印证了这一结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 22.8s
├─ 并发证据采集: 39.2s
│  └─ g1 aiops-case-v15/workload: 39.2s (Evidence 31.3s, RCA 7.7s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
