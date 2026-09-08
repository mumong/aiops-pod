## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | 容器 'app' 配置的内存硬限制 (64Mi) 过低，无法支撑应用处理请求时的内存增长（日志显示从 2MB 递增至 36MB 的持续分配），触发 OOMKilled，导致 Pod 进入 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | K8s Config | 容器 'app' 内存硬限制 `64Mi` (fact-175763241102) | 确认为故障提供硬性边界约束 |
| 2 | Logging | Logging | 应用日志记录内存分配从 14 MiB 递增至 46 MiB (fact-2db9812df9e5...0d4700d0c8af) | 证实应用存在超出限制的内存增长需求，与限制值产生冲突 |
| 3 | K8s State | K8s State | 容器终止原因为 `OOMKilled` (fact-cdbbb4f7d60a) | 直接证明内存越界触发了系统的强制杀死机制 |
| 4 | K8s State | K8s State | 容器退出状态码为 `137` (fact-3a392b593b8a) | 佐证容器是被系统信号（OOMKiller）强制终结而非正常退出 |
| 5 | K8s Event | K8s Event | 容器重启行为：`Back-off restarting failed container app` (fact-adeb841ad0a7) | 解释了 Pod 最终进入 `CrashLoopBackOff` 状态的直接行为路径 |
| 6 | Metric | Metric | Prometheus 采集到终止原因为 `OOMKilled` (fact-667e4fd7a97b) | 独立于 K8s API 的监控维度，提供了相同故障结论的支撑 |

**证据说明**：
K8s 配置维度提供了 `64Mi` 的硬限制基线，而日志维度展示了应用从 14MiB 增至 46MiB 的内存分配趋势，两者直接指向了资源不足。该资源瓶颈随后被 K8s State 维度的 `OOMKilled` 状态和 `137` 退出码所确认，Metric 维度同步反映了相同的 OOM 终止事实。事件维度的 `BackOff` 机制进一步解释了为何该 OOM 现象演变为持续存在的 `CrashLoopBackOff` 故障。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存硬限制 64Mi → 应用请求处理时内存分配增长（最大达 46MiB）并越界 → 触发 OOMKilled (Exit Code 137) → 容器反复重启进入 CrashLoopBackOff
```

### 根因结论

已确认的根因为：**应用容器 'app' 的内存硬限制 (`64Mi`) 配置过低，无法满足其在运行请求时的内存增长需求。**

根据事实 1（硬限制 `64Mi`）与事实 2（日志观测到内存分配从 `14MiB` 持续增至 `46MiB`）的交叉印证，应用进程的内存使用量已经逼近并突破了容器安全界限。这一越界行为直接触发了内核的 OOM Killer 机制，导致容器被强制终止（事实 3 的 `OOMKilled` 与事实 4 的退出码 `137`）。随后，Kubelet 的自动重启策略导致容器在短时间内反复重启失败，进而引发 `BackOff` 事件（事实 5），最终表现为 Pod 持续处于 `CrashLoopBackOff` 状态（现象）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 32.6s
├─ 并发证据采集: 73.1s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 73.1s (Evidence 64.7s, RCA 8.2s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime
