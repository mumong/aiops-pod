## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | pod/workload 处于 CrashLoopBackOff，因 OOMKilled (Exit Code 137) 导致反复重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `last_terminated_reason=OOMKilled`, `last_exit_code=137` | 确认容器因内存超限被内核强制终止的核心状态 |
| 2 | Metric | Prometheus | `reason=OOMKilled`, `restart_count=19`, `resource_limit.memory=67108864 bytes` | 独立验证终止原因与重启次数，确认当前内存硬限制为 64Mi |
| 3 | K8s Config | Kubernetes | `container.resource_limit.memory=64Mi`, `container.resource_request.memory=8Mi` | 提供资源边界事实，证明限制量（64Mi）极低 |
| 4 | Logging | Elasticsearch | `startup allocation 256Mi` | 揭示应用启动阶段直接申请 256Mi 内存的操作，解释了突破 64Mi 限制的机制 |

**证据分析**
- **现象一致性**：K8s 的 `OOMKilled` (fact-06846029af8b) 与 Prometheus 的 `reason=OOMKilled` (fact-8e5370aa7cf7) 共同确认了进程终止的直接原因，排除了其他异常退出可能。
- **根因定位**：日志中记录的启动分配 `256Mi` (fact-05468ba107e7) 远超 K8s 配置中的 `64Mi` (fact-b95b3b53bde1)。该数值差异构成了 OOM 发生的直接因果逻辑，即应用所需的内存空间超过了操作系统允许的上限。

## 🎯 根因分析 · g1

### 因果链
```text
应用启动硬编码申请 256Mi 内存 (Logging) → 分配请求突破 64Mi 的 K8s Memory Limit (K8s Config) → Linux OOM Killer 强制终止容器 (K8s State/Metric) → 导致 pod 反复重启 CrashLoopBackOff (K8s State)
```

### 根因结论
- **已确认的根因**：应用容器内的代码在启动阶段执行了强制的 256Mi 内存申请（依据日志 `startup allocation 256Mi`）。由于该应用被 Kubernetes 配置为 `memory limit=64Mi`，内核 OOM Killer 在检测到内存超限后立即终止了进程（`Exit Code 137` / `OOMKilled`），进而引发 `CrashLoopBackOff`。
- **证据引用**：此结论由 Kubernetes 状态事实（事实 1, 3）与 Elasticsearch 日志事实（事实 4）共同印证，无需其他补充即可闭环。

---

## 📊 性能统计

```text
├─ 总耗时: 9.4m
├─ 问题定位: 17.1s
├─ 并发证据采集: 537.7s
│  └─ g1 aiops-case-v15/workload: 537.7s (Evidence 529.7s, RCA 7.8s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime, pod-imagepull-failed, pod-config-error, pod-oomkilled
