## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod `workload` in `aiops-case-v10` namespace is in `CrashLoopBackOff` state. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | Kubernetes | `resource_request.memory: 8Mi`, `resource_limit.memory: 32Mi` | 提供资源约束上下文；限制极低但非本次启动失败的主因 |
| 2 | Logging | Elasticsearch | `APP_REQUIRED_CONFIG environment variable is missing` (fact-15fa015b88a8) | 直接定位应用启动失败的根本原因，指出缺失必需的环境变量 |
| 3 | K8s Event | Kubernetes | `Warning BackOff ... Back-off restarting failed container app` (fact-51499269e5c4) | 确认容器持续崩溃导致 K8s 进入指数退避重启状态 |
| 4 | K8s State | Kubernetes | `container.last_exit_code: 78` (fact-028e9dabba34), `container.last_terminated_reason: Error` (fact-a8233e1bd668) | 验证应用进程因错误代码 78 被强制终止，印证启动配置缺失导致退出 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 9` (fact-f5ed062dde42) | 确认该异常已引发多次重启循环，符合 CrashLoopBackOff 特征 |

**证据关联分析：**
日志 (fact-2) 明确记录了应用启动失败的直接原因（缺失配置），直接导致容器以退出码 78 终止 (fact-4)；Kubernetes 事件 (fact-3) 和指标 (fact-5) 分别描述了系统层面的重启退避现象及重启次数，这些维度共同构成了“应用启动失败 -> 退出 -> 集群重启”的完整证据链。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 中缺失 `APP_REQUIRED_CONFIG` 环境变量 (fact-2) → 应用启动时检测到配置缺失并调用 sys.exit(78) (fact-4) → 容器以 Error 状态终止并触发 K8s 重启退避 (fact-3) → Pod 处于 CrashLoopBackOff 状态 (fact-1, fact-5)
```

### 根因结论

**已确认的根因**：应用 `workload` 启动失败的根本原因是其配置缺失。

日志事实明确指出 `APP_REQUIRED_CONFIG environment variable is missing` (fact-2)，这导致应用程序无法正常启动并以退出码 78 终止 (fact-4)。这种应用层面的启动崩溃直接触发了 Kubernetes 的重启机制，并在连续失败后进入 CrashLoopBackOff 状态 (fact-3, fact-1)。Kubernetes 事件与 Prometheus 指标 (fact-5) 验证了重启循环的持续性。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 14.9s
├─ 并发证据采集: 72.6s
│  └─ g1 aiops-case-v10/workload: 72.6s (Evidence 65.6s, RCA 6.9s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime, pod-notready-probe-failed
