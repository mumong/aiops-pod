## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod aiops-case-v10/workload 的容器配置中缺失必需环境变量 APP_REQUIRED_CONFIG，导致应用启动时读取到空值并执行 sys.exit(78) 主动退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: `CrashLoopBackOff` (app) | 确认 Pod 当前处于重启背退的异常生命周期 |
| 2 | K8s State | Kubernetes | `container.last_exit_code`: `78` (app) | 提供进程退出的具体代码，指向应用层主动终止 |
| 3 | K8s Event | Kubernetes | `BackOff restarting failed container app` (kubelet, x375) | 记录 Kubelet 检测到频繁重启的行为及频次 |
| 4 | Logging | Elasticsearch | `APP_REQUIRED_CONFIG environment variable is missing` | 直接记录应用启动失败的具体原因 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` (reason=Error, value=1) | 独立于 K8s 事件观测到容器因 Error 终止的状态 |

应用日志明确指出了缺失 `APP_REQUIRED_CONFIG` 环境变量，K8s 状态显示容器以此退出，随后由 Kubelet 触发 `CrashLoopBackOff`，三者在因果逻辑上完全自洽。

## 🎯 根因分析 · g1

### 因果链

```text
容器配置缺失环境变量 APP_REQUIRED_CONFIG → 应用启动时读取空值并执行 sys.exit(78) → 进程非正常退出触发重启策略 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

根因确认为 Pod `aiops-case-v10/workload` 的配置中缺失必需的环境变量 `APP_REQUIRED_CONFIG`。应用启动逻辑检测到该关键变量缺失后，主动执行 `sys.exit(78)` 终止进程（证据 #2），Kubelet 捕获到非零退出码并判定容器失败，进而启动重启机制，最终导致 Pod 陷入 `CrashLoopBackOff`（证据 #1、#3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 24.4s
├─ 并发证据采集: 30.9s
│  └─ g1 aiops-case-v10/workload: 30.9s (Evidence 23.1s, RCA 7.7s)
└─ 汇总总结: 6.7s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
