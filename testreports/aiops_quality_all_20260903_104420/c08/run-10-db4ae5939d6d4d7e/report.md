## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | Pod workload-5c9c7b6489-fl85h 处于 CrashLoopBackOff 状态，容器反复被 OOMKilled 并重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | 容器 `app` 退出码 `137`；终止原因 `OOMKilled` | 确定进程因内存超限被内核强制终止 |
| 2 | K8s Config | kubernetes | 容器 `app` 内存请求 `24Mi`，内存限制 `64Mi` | 确认容器运行环境的硬性资源边界 |
| 3 | K8s Event | kubernetes | `Warning BackOff`：容器 `app` 反复重启，共重启 `9` 次 | 确认应用进入 CrashLoopBackOff 症状 |
| 4 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason`=`OOMKilled`；重启总数 `8` | 从监控系统侧独立确认终止原因 |
| 5 | Logging | elasticsearch | 模式 `memory allocation advanced`：`allocated_mib` 从 `10` 增长至 `38` | 定位到 `/work` 端点处理时内存持续增长的特征 |

- 证据 1、2、3 从 Kubernetes 状态和事件层面构建了“资源受限 → OOMKilled → 重启循环”的闭环。
- 证据 4 作为监控维度的独立观测，确认了终止原因为 OOM。
- 证据 5 提供了关键的行为特征（日志中明确的内存分配增长），证实了 `/work` 端点的处理过程导致了容器内内存使用的持续上升，直至触及 64Mi 限制。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存硬限制(64Mi)低于 /work 端点处理所需的内存空间 → 触发 Linux OOM Killer 机制 → 容器进程被强制终止 (Exit 137, OOMKilled) → Pod 处于 CrashLoopBackOff 状态，反复重启
```

### 根因结论

已确认根因：**容器 `app` 的内存限制（64Mi）过低，无法承载应用在处理 `/work` 端点时的动态内存分配需求**。

内存使用增长（证据 5 显示 `allocated_mib` 达 38）加上 JVM/运行时自身开销，使得实际内存使用突破了 `64Mi` 的限制（证据 2）。这触发了 OOM Killer 机制（证据 1、4），导致容器进程被杀（证据 1）。Kubelet 随后不断重启失败的容器（证据 3），从而表现为 `CrashLoopBackOff` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 17.0s
├─ 并发证据采集: 54.3s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 54.3s (Evidence 45.1s, RCA 9.0s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime
