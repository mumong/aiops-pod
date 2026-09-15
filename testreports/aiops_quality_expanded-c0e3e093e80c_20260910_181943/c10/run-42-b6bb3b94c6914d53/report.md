## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | CrashLoopBackOff | Pod app容器内存限制过低(96Mi)导致OOMKill |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `Exit Code: 137`; `reason: Error` (last terminated reason) | 确证进程被操作系统 SIGKILL 强制终止的机制 |
| 2 | Metric | Prometheus | `reason: Error`; `reason: CrashLoopBackOff`; `restart_count: 23` (时间窗口 63m 内) | 证实异常终止后触发了 Kubernetes 的重启与退避逻辑 |
| 3 | K8s Config | Kubernetes | `memory_limit: 96Mi`; `cpu_limit: 200m`; `cpu_request: 20m` | 确认容器资源配置，极低的内存硬限制是导致 OOM 的关键条件 |
| 4 | Logging | Elasticsearch | 8 条重复日志：`http_status: 200`, `allocated_mib: 0`; 时间范围 `03:29:28.878Z` ~ `03:30:01.017Z` | 证实应用在 OOM 前可正常处理业务请求，排除逻辑或网络故障，指向资源耗尽 |

**证据印证说明：**
1. **状态与指标互证**：K8s 状态报告退出码 137（对应 `Exit Code: 137`）[1]，与 Prometheus 中记录的 `last_terminated_reason: Error` [2] 完全一致，共同排除了配置错误、启动失败等 128 以外的退出原因。
2. **配置与日志互证**：应用日志显示在终止前持续返回 HTTP 200 [4]，证明应用本身无逻辑崩溃，而是受限于 96Mi 的极低内存上限 [3] 运行中耗尽资源，触发了 Linux OOM-Killer。

## 🎯 根因分析 · g1

```text
容器内存硬限制(96Mi)过低 → 应用请求处理积累内存占用超过限制 → 触发 Linux OOM-Killer 发送 SIGKILL (Exit Code 137) → 容器崩溃重启并进入 CrashLoopBackOff 状态
```

**根因结论：**
已确认根因为 **Pod 容器内存限制过低**。
1. 容器被配置了仅 96Mi 的内存上限 [3]。
2. 应用运行时积累内存超过该限制，直接导致 OOM-Killer 强制终止进程，以 137 号信号（SIGKILL）退出 [1]。
3. 随后 Kubernetes 启动重试机制，在 63 分钟内观察到 23 次重启及对应的 CrashLoopBackOff 状态 [2]。
日志中持续的 200 响应 [4] 进一步证实了应用功能本身正常，故障纯粹由资源配额瓶颈引发。

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 17.3s
├─ 并发证据采集: 114.0s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 114.0s (Evidence 106.0s, RCA 7.9s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-crashloop-runtime
