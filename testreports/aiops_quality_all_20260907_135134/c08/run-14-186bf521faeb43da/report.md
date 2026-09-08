## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | Pod workload-5c9c7b6489-wmjhr 处于 CrashLoopBackOff，容器持续以 Exit Code 137 (OOMKilled) 崩溃 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `last_terminated_reason=OOMKilled`, `last_exit_code=137` | 确证容器因资源超限被内核强制终止 |
| 2 | K8s State | kubernetes | `waiting_reason=CrashLoopBackOff`, `restart_count=11` | 确证失败后的循环重启现象 |
| 3 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason=1` (labels: `reason=OOMKilled`) | 独立确认终止原因为 OOM |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total=11` | 确认与 K8s State 一致的崩溃频次 |
| 5 | K8s Config | kubernetes | `container.resource_limit.memory=64Mi` | 确立硬性内存上限约束 |
| 6 | K8s Event | kubernetes | `BackOff restarting failed container` (140 times over 41m) | 反映 kubelet 按指数退避策略持续重启的现场 |
| 7 | Logging | elasticsearch | pattern: `memory allocation advanced` (HTTP 200, path `/work`), `numeric_fields`: `allocated_mib` 从 10 增至 48 | 揭示触发 OOM 前内存占用正在快速增长 |

**证据关联性：**
*   **维度闭环：** K8s State 的 `OOMKilled` / Exit 137 与 Metric 的 `OOMKilled` 标签直接互证，排除其他退出码可能；Metric 的 `restart_total` 与 K8s 事件 `BackOff` 频次共同确认了重启频率。
*   **因果逻辑：** K8s 配置中的 64Mi 内存限制作为刚性约束，结合日志显示的分配内存（10Mi -> 48Mi）逼近并超越该限制的趋势，构成了导致 OOM 的完整证据链。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存配置限制过低(64Mi) → 业务请求导致内存分配增长逼近限制 → 触及 Cgroup Hard Limit 触发内核 OOM Killer → 进程被强制终止(Exit 137)引发 CrashLoopBackOff
```

### 根因结论

**已确认根因：** 容器内存限制（Memory Limit）配置过低（64Mi）。
*   **形成机制：** 容器配置了 64Mi 的硬内存上限。在请求处理过程中，应用内存分配持续增长（日志记录从 10Mi 增长至 48Mi），最终突破 64Mi 限制，导致 Linux 内核 OOM Killer 强制终止容器进程。
*   **现象印证：** K8s 状态 `OOMKilled` / Exit 137、Prometheus 指标 `reason=OOMKilled` 以及日志中的内存增长模式，一致证实了配置限制是当前故障的触发点（引用证据 #1, #3, #5, #7）。

**未决事项：**
*   现有证据仅能确认限制值过低，无法判定是否存在应用层内存泄漏，也无法确认集群内其他实例是否同样受到该配置限制（引用诊断状态中的 unknowns）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 20.5s
├─ 并发证据采集: 63.9s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 63.9s (Evidence 54.9s, RCA 8.8s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
