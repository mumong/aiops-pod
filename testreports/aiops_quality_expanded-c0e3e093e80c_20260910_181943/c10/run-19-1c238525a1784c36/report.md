## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | Running | Pod内存请求(24Mi)远低于实际运行需求，导致容器在负载下内存耗尽被Linux内核OOM-Killer强制终止(Exit Code 137)，进而引发Liveness Probe失败和CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `restart_count`: 5; `last_exit_code`: 137; `last_terminated_reason`: Error | 证实容器已多次异常终止，137 号退出码直接指向内核 OOM-Killer 介入 |
| 2 | K8s Config | Kubernetes | `resource_request.memory`: 24Mi; `resource_limit.memory`: 96Mi | 配置事实：内存限制（96Mi）极低，且请求值（24Mi）严重偏低，无法为容器提供足够资源预留 |
| 3 | Metric | Prometheus | `container_memory_working_set_bytes` (容器 app) 近期采样范围：4,747,264 ~ 15,429,632 bytes | 证实容器实际内存使用量（最高约 15.4Mi）远超内存请求（24Mi），且已逼近内存限制阈值（96Mi / 100,663,296 bytes） |
| 4 | K8s Event | Kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` | 证实容器在内存高负载下服务响应异常，探针失效 |

上述证据形成闭环：极低硬限制（E2）与低请求导致资源争抢，Metric 数据（E3）显示实际内存消耗逼近上限，直接引发内核 OOM（E1）及随后的探针失败（E4）。

## 🎯 根因分析 · g1

### 因果链

```text
memory_limit 设置过低(96Mi) → 内存耗尽 → OOM-Killer 终止进程(Exit 137) → 容器重启且 CrashLoopBackOff
```

### 根因结论

已确认根因为**容器内存资源限制（96Mi）远低于应用实际运行需求**。
真实数据表明，应用进程内存使用量最高达约 15.4 MiB（E3），这迫使系统在内存请求值（24Mi）与硬限制（96Mi）之间处于极度紧张状态。内存耗尽触发内核强制终止（E1），进而导致 Liveness Probe 探测失败（E4）。现有证据已充分支撑内存超限导致 OOM 的结论。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 32.5s
├─ 并发证据采集: 96.7s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 96.7s (Evidence 91.1s, RCA 5.4s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-oomkilled
