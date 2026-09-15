## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | Pod workload-5c9c7b6489-p8462 处于 CrashLoopBackOff 状态，容器反复被 OOMKilled 重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` 状态 `CrashLoopBackOff`，退出码 `137`，终止原因 `OOMKilled` | 确认应用进程因系统强制杀除异常终止，存在内存越界硬限制 |
| 2 | K8s Config | Kubernetes | 容器 `app` 内存硬限制 (`resource_limit.memory`) 配置为 `64Mi` | 提供触发 OOM 的关键阈值限制值 |
| 3 | K8s Event | Kubernetes | 7次事件记录显示：原因 `OOMKilled`、退出码 `137`、Pod IP `172.16.104.11/32` | 交叉印证终止机制为 OOM，并锁定网络拓扑标识 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (CrashLoopBackOff) 持续为 `1`；`restart_count` 从 `3` 增长至 `10` | 观测到重启次数持续上升的失败趋势，证实问题未自愈 |
| 5 | Logging | Elasticsearch | 访问路径 `/work` 的日志模式：`memory allocation advanced`，`allocated_mib` 观测窗口内从 `16` 增至 `48` | 记录应用请求期间内存占用从 16Mi 急剧攀升至 48Mi 的增长过程 |
| 6 | Tracing | Deepflow/Tempo | HTTP GET `/work` 请求在 Tempo 中观测到 span `a981c72ae8f3d83e`，属性 `aiops.observed_mode` 为 `oom_growth` | 将特定流量请求与内存泄漏增长行为在时间线上直接绑定 |

**证据关联说明：**
1-3 号证据从 K8s 层面确立了“内存受限（64Mi）导致 OOM（137）并重启”的故障形态；4 号指标证据证实该故障呈持续恶化趋势（重启次数增加）。5、6 号证据深入应用层，Logging 中 `/work` 路径内存分配增长（16Mi→48Mi）与 Tracing 中 `oom_growth` 模式高度一致，且 48Mi 接近 64Mi 限制阈值，直接揭示了导致 1-3 号事件的具体内存压力来源与增长路径。

## 🎯 根因分析 · g1

```text
容器内存硬限制设定过低 (64Mi) → 处理 /work 请求触发内存分配增长至 48Mi 逼近限制 → Linux OOM Killer 强制终止进程 (Exit 137) → Kubelet 持续重启触发 CrashLoopBackOff
```

**根因结论：**

已确认的根因为应用容器 `app` 的内存硬限制设定过低。当应用处理特定 HTTP 请求（如 `/work`）时，发生显著的内存增长（从 16Mi 增至 48Mi），导致其内存使用量逼近并超过系统分配的 `64Mi` 硬限制。这一压力触发了 Linux 内核的 OOM Killer，以退出码 `137` 强制终止了应用进程。Kubernetes 随后根据重启策略不断尝试拉起容器，从而形成了观测到的 `CrashLoopBackOff` 状态。相关结论得到了 K8s 状态、Prometheus 重启趋势指标、应用层内存增长日志及 Trace 内存模式的多维度交叉印证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 22.1s
├─ 并发证据采集: 59.6s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 59.6s (Evidence 49.9s, RCA 9.6s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime, pod-oomkilled, pod-config-error
