## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | 容器 `app` 的 YAML 配置中缺失必需的环境变量 `APP_REQUIRED_CONFIG`，导致主进程启动时读取失败并调用 `sys.exit(78)` 退出，进而触发 Kubernetes 的 CrashLoopBackOff 机制。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `container.last_exit_code` (fact-05cf46931b60) | `exit_code: 78` | 证明进程以非零状态码（通常为配置错误）强制终止 |
| 2 | Logging | `log.message` (fact-1aeaadf9bbec) | `APP_REQUIRED_CONFIG environment variable is missing` | 直接暴露导致 `sys.exit(78)` 的具体缺失配置项 |
| 3 | K8s State | `container.waiting_reason` (fact-911b0055f499) | `CrashLoopBackOff` | 确认集群层面的异常表现状态 |
| 4 | K8s State | `container.waiting_message` (fact-1008651b2cee) | `back-off 5m0s restarting failed container=app pod=workload_aiops-case-v10...` | 提供退避时间戳与 Pod ID，佐证重启频繁触发退避策略 |
| 5 | Metrics | `kube_pod_container_status_last_terminated_reason` (fact-b6669b5455e6) | `reason: Error` | 独立于 Kubernetes 状态机，确认容器以 Error 状态退出 |
| 6 | K8s State | `container.resource_request.cpu` (fact-271dc0dcd6d8) | `5m` | 排除 CPU 资源不足导致 OOMKilled 或资源调度异常 |

**证据分析：**
Kubernetes 状态机（`fact-3`, `fact-4`）显示 `CrashLoopBackOff`，其直接原因是 `Exit Code 78`（`fact-1`）和 `Error`（`fact-5`）。日志（`fact-2`）提供了 `fact-1` 的决定性解释：因缺少环境变量导致程序显式退出。资源限制（`fact-6`）排除了资源超限的可能，逻辑闭环完整。

## 🎯 根因分析 · g1

### 因果链

```text
YAML 配置缺失环境变量 `APP_REQUIRED_CONFIG` (Logging) → 应用读取缺失并执行 `sys.exit(78)` (K8s State / Metrics) → Kubernetes 重启退避机制触发 (K8s State) → Pod 处于 CrashLoopBackOff 状态 (K8s State / Metrics)
```

### 根因结论

已确认根因：应用 `workload` (namespace: `aiops-case-v10`) 的 YAML 配置中缺失必需的环境变量 `APP_REQUIRED_CONFIG`（证据编号 2）。这导致应用主进程启动时直接以退出码 `78` 终止（证据编号 1），进而引发 Kubernetes 的 CrashLoopBackOff 重启机制（证据编号 3、4、5）。证据之间通过日志明确原因与退出码形成因果闭环，结论成立。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 15.1s
├─ 并发证据采集: 38.5s
│  └─ g1 aiops-case-v10/workload: 38.5s (Evidence 31.0s, RCA 7.4s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
