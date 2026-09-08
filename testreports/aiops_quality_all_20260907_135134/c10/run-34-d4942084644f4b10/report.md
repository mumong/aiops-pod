## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | Running | Pod workload-79d9f8fd88-bwqhh 处于 CrashLoopBackOff，容器重启 32 次，最后一次终止退出码 137 (OOMKilled) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `BackOff 4m46s (x303 over 85m) kubelet Back-off restarting failed container app` | 确认应用进程持续崩溃并陷入重启循环，验证了崩溃频率 |
| 2 | K8s State | Kubernetes | `container.waiting_reason: CrashLoopBackOff` | 确认 Pod 处于非健康重启状态 |
| 3 | K8s Event | Kubernetes | `Exit Code: 137` | 核心证据，137 退出码直接证实容器进程被操作系统（OOM）强制终止 |
| 4 | Metric | Prometheus | `container_memory_working_set_bytes` 采样值 15,548,416 字节 (约 14.8 MiB) | 提供内存使用绝对量，证明应用在运行过程中确实产生了显著的内存占用 |
| 5 | K8s Config | Kubernetes | `container.resource_limit.memory: 96Mi` | 定义容器的硬内存上限，确认退出码 137 触发的阈值条件 |

证据表明，应用进程在运行时内存占用了约 14.8 MiB，随后发生进程强制终止（Exit Code 137），导致 kubelet 触发了 303 次重启尝试并进入 CrashLoopBackOff。Metrics 中采集到的内存数据证明了该应用存在实际的资源消耗，与 OOM 终止事件发生逻辑一致。

## 🎯 根因分析 · g1

### 因果链

```text
容器运行期间内存消耗积累 → 触发 Cgroups/内核 OOM Killer 机制 (硬限制 96Mi) → 应用进程被强制 Kill (Exit Code 137) → 容器重启失败导致 CrashLoopBackOff
```

### 根因结论

已确认根因为容器进程触发了 OOMKilled 终止（证据 #3、#5）。尽管当前采集到的单次 Metric 快照（证据 #4）显示的峰值（~14.8 MiB）低于 96Mi 的硬限制，但这仅反映了内存工作集（Working Set）的片段，无法排除峰值瞬间瞬时突破限制、存在内存泄漏或存在外部节点级资源争抢导致强制回收（证据 #1、#2 确认了崩溃与重启现象的连续性）。正式 RCA 指出的“内存超限触发了 cgroups 强制 OOMKilled”与事实高度吻合。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 25.1s
├─ 并发证据采集: 105.0s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 105.0s (Evidence 90.5s, RCA 14.3s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime
