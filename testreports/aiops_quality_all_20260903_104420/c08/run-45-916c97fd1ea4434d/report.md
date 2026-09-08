## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | Running | Pod workload-5c9c7b6489-fl85h container app is in CrashLoopBackOff state due to repeated OOMKilled terminations. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Back-off restarting failed container app` (x496 over 130m) | 症状：展示频繁的 CrashLoopBackOff 循环状态 |
| 2 | K8s State | Kubernetes | Container `app` 退出码 `137`，终止原因 `OOMKilled` | 症状：确认容器被 OOM Killer 终止的根本原因 |
| 3 | K8s Config | Kubernetes | Container `app` 内存硬限制 `64Mi` | 上下文：提供了触发 OOM 的阈值上限 |
| 4 | K8s Config | Kubernetes | Container `app` 内存请求 `24Mi`，CPU 请求 `20m` | 上下文：展示资源分配的基准设定 |
| 5 | Metric | Prometheus | `container_memory_working_set_bytes` 峰值达 `61743104` Bytes (~58.8 MiB) | 证据：工作集内存持续逼近且触及 64Mi 限制 |
| 6 | Logging | Elasticsearch | 模式 `memory allocation advanced`，分配量从 `14 MiB` 升至 `46 MiB` | 证据：日志直接反映了应用运行期间的内存消耗增长轨迹 |

**证据关联说明：**
K8s 提供的退出码 137 与 OOMKilled 终止状态（事实 1-2）结合 Metric 中的内存峰值（事实 5）形成闭环，证明容器确实因为触及 64Mi 限制（事实 3）而被系统强制杀死。日志中的内存分配模式（事实 6）进一步印证了应用内部确实存在随请求推进的内存增长机制，从而解释了为何会不断逼近并突破限制。

## 🎯 根因分析 · g1

### 因果链

```text
64Mi 内存硬限制配置 → 应用运行中内存工作集持续攀升（至 ~58.8MiB） → 触发 Linux OOM Killer (exit code 137) → 容器反复重启并进入 CrashLoopBackOff
```

### 根因结论

**已确认的根因**：Pod 配置了过小的内存硬限制（`64Mi`）。

应用在运行过程中内存工作集持续增长（日志证实从 14MiB 增长至 46MiB 以上），最终内存使用量触及并超过了 64Mi 的限制，导致 Linux 内核 OOM Killer 介入并强制终止容器。由于应用存在内在的内存分配增长模式，在不增加资源限制的情况下，该容器将不可避免地再次触发 OOM，导致 `CrashLoopBackOff` 现象持续发生。

---

## 📊 性能统计

```text
├─ 总耗时: 2.7m
├─ 问题定位: 19.3s
├─ 并发证据采集: 130.8s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 130.8s (Evidence 119.7s, RCA 10.9s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-oomkilled
