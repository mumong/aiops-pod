## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | 容器启动时因缺少必需的环境变量 `APP_REQUIRED_CONFIG` 而主动退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning BackOff 2m (x375 over 82m) ... Back-off restarting failed container app` | 证明容器处于持续崩溃重启状态，故障持续时间长（82分钟） |
| 2 | Logging | elasticsearch | `APP_REQUIRED_CONFIG environment variable is missing` | 直接指出容器启动失败的具体错误原因 |
| 3 | K8s State | kubernetes | `last_terminated_reason: Error`, `last_exit_code: 78` | 确认容器以错误码 78 异常终止，符合应用层主动退出的特征 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason: 1 (CrashLoopBackOff)`, `kube_pod_container_status_restarts_total: 20` | 从监控侧独立证实了 Pod 的等待状态和 20 次重启事实 |
| 5 | K8s Config | kubernetes | `cpu limit: 50m`, `memory limit: 32Mi` | 提供资源上下文，排除资源超限（OOM/CPU Throttling）的可能性 |
| 6 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason: 1 (Error)` | 监控侧确认最近一次终止原因分类为 Error，与 K8s Event 一致 |

**证据总结：**
日志记录了明确的缺失变量错误，K8s Event 和 Metric 均确认了因 Error 导致的 CrashLoopBackOff 和频繁重启状态，Exit Code 78 进一步印证了这是容器内部主动退出而非系统资源限制导致的崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
环境变量 `APP_REQUIRED_CONFIG` 未配置 → 容器启动脚本检测变量缺失，打印错误并执行 `sys.exit(78)` → 容器以异常码 78 终止 → Pod 触发 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因为 **容器启动时因缺少必需的环境变量 `APP_REQUIRED_CONFIG` 而主动退出**。

证据支持：
- **直接证据**：日志明确记录 `APP_REQUIRED_CONFIG environment variable is missing` [证据#2]。
- **终止确认**：Exit Code 78 [证据#3] 与日志中的应用逻辑（`sys.exit`）一致，排除了 OOMKilled 等 K8s 驱逐机制 [证据#5]。
- **状态佐证**：375 次 BackOff 警告 [证据#1] 和 20 次重启 [证据#4] 证明该启动失败处于循环重试中。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 13.9s
├─ 并发证据采集: 40.4s
│  └─ g1 aiops-case-v10/workload: 40.4s (Evidence 33.6s, RCA 6.7s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime, pod-config-error
