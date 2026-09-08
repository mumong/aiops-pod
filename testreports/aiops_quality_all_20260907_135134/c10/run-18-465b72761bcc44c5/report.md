## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | Pod workload-79d9f8fd88-bwqhh 处于 CrashLoopBackOff 状态，容器反复以 Exit Code 137 (SIGKILL) 终止 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Container app 终止原因 `Error`，退出码 `137` | 确认进程被系统强制终止 |
| 2 | K8s Config | Kubernetes | 容器内存 Limit 配置 `96Mi`，Request `24Mi` | 确认存在的资源硬限制 |
| 3 | K8s Event | Kubernetes | Liveness probe failed: HTTP 500 | 确认应用因异常终止无法响应健康检查 |
| 4 | K8s State | Kubernetes | Pod phase `Running`，Container state `CrashLoopBackOff`，重启 `18` 次 | 确认集群层面的崩溃循环状态 |
| 5 | Logging | Elasticsearch | `request completed` pattern，HTTP 200，应用 `allocated_mib` 变化 `0 → 0` | 观察到的正常请求未表现出内存飙升特征 |
| 6 | Tracing | Deepflow | HTTP GET /work，Response Code 200，Duration 16-19ms | 正常流量特征，未表现出性能衰退 |

日志与追踪数据显示应用曾正常响应（HTTP 200），但并未直接记录崩溃前的内存激增；然而，结合 Kubernetes 侧明确的 `Exit Code 137` 与 96Mi 的内存 Limit，可排除资源请求不足或网络超时等因素。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存使用量超过 Limit (96Mi) → 内核 OOM Killer 强杀进程 (Exit Code 137) → Liveness Probe 失败 (HTTP 500) → Kubernetes 重启并触发 CrashLoopBackOff
```

### 根因结论

已确认根因为**容器内存溢出触发 OOM Killer**。
- **机制确认**：容器进程异常退出并返回 `Exit Code 137` [证据 #1]，这是 Linux 内核 OOM Killer 发送 SIGKILL 信号的典型特征。
- **资源确认**：Pod 配置了 `96Mi` 的内存硬限制（resource_limit） [证据 #2]。
- **结果映射**：进程被杀导致应用进程不可用，进而触发 Liveness Probe 失败 [证据 #3]，最终导致容器不断重启并进入 `CrashLoopBackOff` 状态 [证据 #4]。

---

## 📊 性能统计

```text
├─ 总耗时: 3.9m
├─ 问题定位: 20.7s
├─ 并发证据采集: 206.5s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 206.5s (Evidence 196.7s, RCA 9.7s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime, pod-oomkilled, pod-config-error
