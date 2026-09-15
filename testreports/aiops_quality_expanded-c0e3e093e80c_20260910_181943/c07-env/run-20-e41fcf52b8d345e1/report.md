## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod aiops-case-v10/workload 处于 CrashLoopBackOff 状态，容器 `app` 反复重启且无法就绪。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | Warning BackOff: Back-off restarting failed container app in pod workload_aiops-case-v10(d3e0dc86-6f8b-4f29-a50c-826bf2a1f1e6) | 证实 kubelet 观察到容器反复崩溃并正在退避重启 |
| 2 | K8s Config | Kubernetes | container.resource_request.memory=8Mi; container.resource_limit.memory=32Mi; container.resource_request.cpu=5m; container.resource_limit.cpu=50m | 确认容器资源约束极小，排除资源超限导致 OOM 杀进程的可能 |
| 3 | Logging | Elasticsearch | "APP_REQUIRED_CONFIG environment variable is missing" | 提供应用启动失败的直接业务错误原因，证实配置变量缺失 |
| 4 | K8s State | Kubernetes | container.last_exit_code=78 | 确认进程异常退出，结合日志指向应用自身主动终止 |
| 5 | K8s State | Kubernetes | pod.condition: ContainersReady=False, reason=ContainersNotReady | 确认当前 Pod 就绪检查失败，处于不可用状态 |

上述证据链高度一致：Elasticsearch 日志显示应用因环境变量 `APP_REQUIRED_CONFIG` 缺失而报错，这解释了为何 kubelet 记录到的容器以 Exit Code 78 错误退出（而非 OOMKilled 等常见原因），进而导致 Pod 陷入 CrashLoopBackOff 状态。资源配置极低的事实排除了内存溢出导致异常退出的可能。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置缺失环境变量 APP_REQUIRED_CONFIG → 应用启动命令检测到变量缺失并执行 sys.exit(78) → 容器以 Error 状态终止 (Exit Code 78) → kubelet 持续重启容器导致 CrashLoopBackOff
```

### 根因结论

已确认的根因为：容器 `app` 的启动逻辑强制依赖环境变量 `APP_REQUIRED_CONFIG`，但该 Pod 的 manifests 配置中未提供该变量。

- **支持证据**：
  - 日志显示明确的错误信息 `"APP_REQUIRED_CONFIG environment variable is missing"` (fact-15fa015b88a8)。
  - 容器以退出码 78 异常终止 (fact-f340e20d875f)，配合资源限制极小（8Mi/32Mi 内存，5m/50m CPU）的事实，排除了资源不足导致内核杀进程的可能。
  - 事件与状态证实了该启动失败直接导致了 Kubernetes 层面的 `CrashLoopBackOff` 状态 (fact-bb9f2fce2e0f, fact-1f3d3b8028c1)。

- **未知项**：`APP_REQUIRED_CONFIG` 应当被设置的具体有效值未在事实中提供，仅能确认缺失导致启动失败，无法直接给出配置建议。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 33.3s
├─ 并发证据采集: 46.2s
│  └─ g1 aiops-case-v10/workload: 46.2s (Evidence 36.7s, RCA 9.4s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
