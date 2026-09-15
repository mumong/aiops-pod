## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | Pod `workload-5c9c7b6489-p8462` 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `reason: OOMKilled`; `container.last_terminated_reason` 明确指示被 OOM Killer 终止 | 证实 Pod 频繁重启（27 次）的直接终止原因为系统级内存杀除（Exit 137） |
| 2 | K8s State | Kubernetes | 配置 `container.resource_limit.memory`: `64Mi` | 提供判定内存不足的硬性阈值标准，证实 48MiB 的内存增长逼近并可能突破该限制 |
| 3 | Logging | Elasticsearch | 日志聚合 `allocated_mib`: 连续记录中从 `first=12` 增长至 `last=48` (min=12.0, max=48.0) | 证实应用在处理请求时存在明确的内存持续增长行为（每次增加 2 MiB） |
| 4 | Tracing | Tempo/Deepflow | `aiops.observed_mode: oom_growth`; `GET /work` HTTP 200 (Tempo 与 Deepflow 聚合均验证) | 将内存增长行为与 `/work` 端点的请求直接绑定，证实内存泄漏/增长发生在该特定业务场景中 |

上述证据表明，尽管 Metric 仅捕获到 CrashLoopBackOff 和 OOMKilled 的当前状态（单样本，无趋势），但 K8s 状态明确给出了 OOMKilled 的直接原因，Logging 提供了内存随请求持续增长的确凿数值证据（12M -> 48M），Tracing 进一步将这一增长精确锚定在 `GET /work` 请求的处理过程中。K8s 状态中高达 27 次的重启次数印证了 OOM 触发的频繁性。

## 🎯 根因分析 · g1

### 因果链

```text
应用处理 /work 请求时存在内存持续增长逻辑 → 累计内存分配增至 48 MiB 逼近 64Mi 硬限制 → Linux OOM Killer 强制终止进程（Exit Code: 137） → Pod 进入 CrashLoopBackOff 循环重启
```

### 根因结论

根因是 Pod `aiops-case-08/workload-5c9c7b6489-p8462` 中的 `app` 容器在处理 `GET /work` HTTP 请求时存在内存持续增长（每次约增加 2 MiB）的行为。
当容器内内存累积至接近或超过 `64Mi` 的硬限制时，Linux OOM Killer 强制杀死了进程，导致容器退出码为 137。
该过程被 Logging 中的 `allocated_mib` 从 12 增长到 48 的连续记录（#3）以及 Tracing 中观测到的 `oom_growth` 模式（#4）所证实，并最终在 K8s 事件中表现为 `OOMKilled`（#1）。

---

## 📊 性能统计

```text
├─ 总耗时: 3.2m
├─ 问题定位: 19.5s
├─ 并发证据采集: 165.0s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 165.0s (Evidence 154.8s, RCA 10.1s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
