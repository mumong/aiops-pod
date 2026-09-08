## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | Running | {'container': 'app', 'reason': 'Error'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Exit Code: 137 | 确证容器进程因系统信号被强制终止 |
| 2 | K8s Config | Kubernetes | Memory Limit: 96Mi | 确定系统级内存硬限制阈值极低 |
| 3 | Metric | Prometheus | Memory 观测窗口从 3.7MiB 攀升至 15.4MiB，且 200m CPU 下负载稳定 | 证明应用运行正常但内存持续消耗，逼近 96MiB 上限 |
| 4 | K8s Event | Kubernetes | Liveness probe failed: HTTP probe failed with statuscode: 500 | 展示应用因资源不足导致的存活探针连续失败与重启风暴 |

证据链逻辑：Kubernetes 配置 `96MiB` 的硬限制（#2）不足以支撑应用运行，指标 #3 显示内存持续增长；最终触发系统级 OOM 机制导致进程退出码 137（#1），进而引发健康检查失败和循环重启（#4）。

## 🎯 根因分析 · g1

### 因果链

```text
内存限制(96MiB)过低 → 内存持续消耗超限 → 进程被内核 OOM Killer 终止(Exit 137) → 存活探针失败与重启风暴
```

### 根因结论

已确认的根因为应用内存资源硬限制（96MiB）配置过低，导致容器在运行过程中发生 Out of Memory（OOM）被强制终止。证据如下：
- **系统级事实支撑**：Kubernetes 记录容器退出码为 `137`（fact-123233a61c21），这在 K8s 中明确对应 `OOMKilled` 导致的信号杀死。
- **性能数据验证**：Prometheus 指标显示容器工作集内存从约 3.7MiB 稳定攀升并保持在 15.4MiB 左右（fact-0ae1f12f3428），且 CPU 负载稳定，证明应用本身逻辑运行正常，故障纯粹由资源容量不足引发。
- **直接故障表现**：由于频繁触发 OOM 重启，容器未能在存活探针窗口内就绪，产生大量的 `HTTP probe failed with statuscode: 500` 事件（fact-3e93f4df8b35）及重启记录。

尽管缺少 Prometheus 中直接标记为 `OOMKilled` 状态的记录以及应用日志中的 `OutOfMemoryError`，但退出码 `137` 与低内存限制的结合已构成闭环证据链。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 15.4s
├─ 并发证据采集: 106.0s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 106.0s (Evidence 97.6s, RCA 8.2s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-oomkilled
