## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | 容器内存限制(64Mi)小于启动命令申请的内存(256Mi)，导致进程触发OOMKilled并被内核终止。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | container.resource_limit.memory | 64Mi | 确认容器硬限制 |
| 2 | Logging | startup allocation 256Mi | 进程启动申请 256Mi | 揭示内存缺口来源 |
| 3 | K8s State | container.waiting_reason | CrashLoopBackOff | 呈现容器当前异常状态 |
| 4 | K8s State | container.last_terminated_reason | OOMKilled | 证明内核因内存不足终止进程 |
| 5 | K8s State | container.last_exit_code | 137 | 确认被 SIGKILL 强制退出 |

1. **配置与行为的直接冲突**：日志记录进程启动申请 `256Mi` 内存 [Fact 2]，但 K8s 配置中的内存硬限制仅为 `64Mi` [Fact 1]。
2. **状态与事件的闭环**：内存缺口触发内核 OOM 机制，导致进程以退出码 `137` [Fact 5] 终止，原因标记为 `OOMKilled` [Fact 4]，进而触发 Kubelet 的 `CrashLoopBackOff` 保护机制 [Fact 3]。

## 🎯 根因分析 · g1

### 因果链

```text
内存限制(64Mi) < 申请内存(256Mi) → 触发内核 OOM Killer 机制 → 进程被 SIGKILL(退出码137) 终止 → 容器进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为**容器配置的内存限制（64Mi）严重低于应用启动时的实际内存需求（256Mi）**。

当应用进程启动并尝试分配 256Mi 内存时，超过了 K8s 为其设置的 64Mi 硬上限。Linux 内核的 OOM Killer 强制终止了超内存限制的进程，返回退出码 137 (SIGKILL)。这种反复的启动失败和崩溃直接导致了 Kubelet 将其标记为 `OOMKilled` 并最终进入 `CrashLoopBackOff` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 18.3s
├─ 并发证据采集: 51.0s
│  └─ g1 aiops-case-v15/workload: 50.9s (Evidence 45.3s, RCA 5.5s)
└─ 汇总总结: 7.6s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
