## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | 容器内存配置不足（limit 64Mi）无法容纳程序分配的内存（256Mi），导致 OOMKilled |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | K8s State | `memory_limit=64Mi` (fact-53b8da0ccb42) | 根因：定义了极低的内存硬限制 |
| 2 | K8s State | K8s State | `OOMKilled` (fact-3fcb5ead047c) | 根因：触发内核 OOM Killer 的直接机制 |
| 3 | K8s State | K8s State | `CrashLoopBackOff` (fact-5dc61fcea440) | 根因：容器因反复崩溃而进入重启倒计时的状态 |
| 4 | K8s State | K8s State | `container_exit_code=137` (fact-5b8e9cd61a93) | 症状：标准 OOMKilled 终止信号 |
| 5 | K8s Event | K8s State | `Exit Code: 137` / `Reason: OOMKilled` (fact-cc910ff9cf70 aggregated) | 症状：Kubelet 侧确认终止原因及退出码 |
| 6 | Logging | Elasticsearch | `"startup allocation 256Mi"` (fact-016ce27a1965) | 根因：应用启动时尝试分配的内存（256Mi）远超 Limit (64Mi) |
| 7 | Metric | Prometheus | `restart_count=23` (fact-528b6f9c4e24) | 症状：证明崩溃并非单次偶发，已陷入循环重启 |

**证据交叉验证：**
Kubernetes 配置（#1）与应用日志（#6）形成决定性矛盾：程序试图分配 256Mi，但容器被硬限制在 64Mi，导致内核 OOM Killer（#2）强制执行终止（#4）。Kubernetes 状态（#3）与 Prometheus 指标（#7）证实了该 OOM 事件已重复发生 23 次，排除了瞬时异常的可能。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存限制(64Mi) < 程序启动分配需求(256Mi) → 触发内核 OOMKiller → 容器以 137 状态退出 → 触发 CrashLoopBackOff 循环重启
```

### 根因结论

**已确认根因：容器内存配置严重不足导致频繁 OOMKilled。**

证据表明，`aiops-case-v15/workload` 应用容器在启动时被配置了 `memory_limit=64Mi`（#1），但应用自身在启动阶段需分配 `256Mi` 内存（#6）。由于申请值超过了硬限制，Linux 内核 OOM Killer 介入并强制终止了容器进程（#2, #4）。Pod 随后进入 `CrashLoopBackOff` 状态（#3），且在观测窗口内已重启 23 次（#7）。日志、事件与状态指标在多维度上高度一致地指向内存不足这一根本原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 15.7s
├─ 并发证据采集: 86.6s
│  └─ g1 aiops-case-v15/workload: 86.6s (Evidence 81.7s, RCA 4.8s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
