## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | pod CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: `OOMKilled` (fact-c4a7d7af0ed8) | 确认进程因内存溢出被内核杀除 |
| 2 | K8s Config | kubernetes | `container.resource_limit.memory`: `64Mi` (fact-ad7ac20d46b6) | 提供容器内存使用的硬性上限 |
| 3 | K8s Event | kubernetes | `Back-off restarting failed container app` (fact-d17aa5f0b5e2) | 记录 Pod 因 CrashLoopBackOff 频繁重启的状态 |
| 4 | K8s State | kubernetes | `container.last_exit_code`: `137` (fact-95e0afda2b2b) | 终止码 137 验证了被外部强制终止（信号 9）的事实 |
| 5 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason`: 1 (OOMKilled) (fact-fbaac5896238) | 指标侧确认最近一次终止原因为 OOMKill |
| 6 | Logging | elasticsearch | Pattern: `http_request` on `/work`, allocated_mib from 12 to 46 (fact_ids: fact-470756ec1b1d) | 显示请求期间内存从 12Mi 增长至 46Mi，逼近 64Mi 限制 |
| 7 | Tracing | deepflow | HTTP Flow `GET /work` from 172.16.104.30 to 172.16.104.20, 9 occurrences (fact_ids: fact-5af5ba2ebf78) | 提供了触发内存增长行为的请求源与目标 IP 路径 |

**证据关联说明：**
Kubernetes 的终止原因（#1, #3）和退出码（#4）结合 Prometheus 指标（#5）确立了 `OOMKilled` 的故障模式。日志（#6）通过 `allocated_mib` 字段（12Mi -> 46Mi）展示了内存增长的过程，虽然未完全达到 64Mi，但在请求过程中已处于高位，结合 `resource_limit` 为 64Mi（#2），证实了 64Mi 的硬限制不足以支撑峰值负载。Tracing 数据（#7）进一步锁定了 `/work` 接口是引发该资源消耗的具体行为路径。

## 🎯 根因分析 · g1

### 因果链

```text
Memory limit (64Mi) too low → Application memory allocation exceeds limit during /work requests → Kernel OOM Killer terminates container (exit code 137) → Kubelet restarts container leading to CrashLoopBackOff
```

### 根因结论

已确认根因为 **容器内存限制不足（OOMKilled）**。

证据显示 Pod `aiops-case-08/workload-5c9c7b6489-fl85h` 的 `app` 容器被分配的内存硬限制为 **64Mi** (`fact-ad7ac20d46b6`)。在处理 `/work` 请求时，应用内存分配量在日志窗口内从 12Mi 增长至 46Mi (`fact-470756ec1b1d`)，这一波动表明在请求峰值时内存消耗触达或超过了 64Mi 的阈值，导致内核 OOM Killer 强制终止进程（终止码 137, `fact-95e0afda2b2b`）。随后 Kubelet 的自动重启策略导致容器进入 CrashLoopBackOff 状态 (`fact-d17aa5f0b5e2`, `fact-f5e7b7aa150a`)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 17.6s
├─ 并发证据采集: 63.6s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 63.6s (Evidence 54.6s, RCA 8.8s)
└─ 汇总总结: 13.0s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime
