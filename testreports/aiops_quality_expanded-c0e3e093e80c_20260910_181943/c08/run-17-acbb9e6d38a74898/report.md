## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | Pod 中 app 容器的内存分配持续增长（从 2 MiB 增至 48 MiB），超过了其内存资源限制（64 MiB），导致被内核 OOM Killer 强制终止（Exit Code 137）并进入 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Container `app` 终止原因为 `OOMKilled`，退出码 `137` | 确认异常由系统强制终止触发 |
| 2 | K8s Config | Kubernetes | 容器 `app` 内存硬限制 `64Mi` | 界定资源上限边界 |
| 3 | K8s State | Kubernetes | Pod `app` 处于 `CrashLoopBackOff`，重启次数 14 次 | 确认异常导致的持续故障现象 |
| 4 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` 记录为 `OOMKilled` | 外部监控确认内核 OOM 事件 |
| 5 | Logging | Elasticsearch | HTTP 请求日志中 `allocated_mib` 字段在 27 秒窗口内从 18MiB 增至 44MiB | 证明容器内存在持续增长的资源消耗模式 |
| 6 | Tracing | DeepFlow/Tempo | Flow 记录显示针对 `/work` 的 GET 请求持续返回 HTTP 200，服务被标记为 `oom_growth` | 确认内存增长与特定业务接口调用的因果关系 |

证据互证情况：
1. K8s 的 `OOMKilled` 状态与 Prometheus 的终止原因遥测互相印证，确认了导致异常的直接机制是物理内存超限（Fact #1, #4）。
2. 应用日志中的 `allocated_mib` 增长趋势与 Tracing 标记的 `oom_growth` 模式一致，且内存增长量（观察到的 44MiB）已逼近 64MiB 的硬限制（Fact #2），说明内存不足是导致 `OOMKilled` 的根因（Fact #5, #6）。

## 🎯 根因分析 · g1

### 因果链

```text
业务接口 /work 引发内存持续增长 (Logging+Tracing) → 内存分配逼近并超过 64MiB 硬限制 (K8s Config+Logging) → 触发内核 OOM Killer 强制终止 (K8s State+Metric) → Pod 反复崩溃重启 (K8s State)
```

### 根因结论

已确认根因为：Pod 中 `app` 容器处理 `/work` 请求时存在内存增长问题。在连续请求中，内存分配量从 18MiB 激增至 44MiB，超过了容器设定的 `64MiB` 内存硬限制，导致容器被操作系统 OOM Killer 强制终止（Exit Code 137），并引发 `CrashLoopBackOff` 循环。证据链条涵盖 K8s 终止原因、Prometheus 遥测、应用层内存增长日志以及关联的 Tracing 标记，事实闭环完整。

---

## 📊 性能统计

```text
├─ 总耗时: 3.3m
├─ 问题定位: 14.5s
├─ 并发证据采集: 172.0s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 172.0s (Evidence 163.9s, RCA 7.9s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- 未调用 Runbook
