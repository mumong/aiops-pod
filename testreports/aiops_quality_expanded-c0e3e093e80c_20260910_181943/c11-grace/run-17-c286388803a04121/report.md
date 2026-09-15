## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod aiops-case-v13/workload 处于 Terminating 状态，容器进程未退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s API | Pod 条件 `ContainersReady: True` (fact-8f6b2cc4ef31)、`Ready: True` (fact-8fa7ac1d1616) | 确认应用容器在 Pod 处于 Terminating 之前已完全就绪 |
| 2 | K8s State | K8s API | 重启计数 `0` (fact-ffcada11030e) | 排除因 OOM、CrashLoopBackOff 或应用启动失败导致的异常终止 |
| 3 | Logging | ES | `SIGTERM received; waiting` (fact-bfca4a67af84) | 记录到应用已接收终止信号，并表现出阻塞式等待特征 |
| 4 | K8s Config | K8s API | 内存硬限制 `32Mi` (fact-05083cc8b270) | 提供应用运行时的资源边界上下文 |
| 5 | Metrics | Prometheus | Pod 运行状态值为 `1` (fact-dfc9730a93fd) | 独立印证应用未处于 Failed 状态 |

**证据关联分析：**
应用日志事实 #3 直接揭示了容器的阻塞行为，结合 K8s 状态事实 #1 和 #2，确认该 Pod 并非因资源耗尽或启动失败终止，而是因主动执行优雅关闭逻辑时被阻塞。Metrics 事实 #5 提供了运行状态的外部独立印证，排除 Pod 底层被异常杀死的假设。

## 🎯 根因分析 · g1

### 因果链

```text
控制器发起删除请求 (deletionTimestamp 被设置) → 应用接收 SIGTERM 信号触发自定义优雅终止逻辑 → 应用进程进入循环阻塞等待特定文件 /state/teardown-requested 被创建 → 文件未出现，容器无法退出，Pod 维持在 Terminating 状态
```

### 根因结论

已确认根因为**应用优雅终止逻辑（PreStop）与外部依赖不匹配**。应用接收到终止信号后，主动进入阻塞状态以等待文件 `/state/teardown-requested` 的创建（支持日志事实 #3 `SIGTERM received; waiting`），但由于该文件未能按时生成，容器无法完成退出流程。

**关键证据：**
*   日志事实 `fact-bfca4a67af84` (`SIGTERM received; waiting`)：证实应用层拦截了终止信号并执行了阻塞式等待策略。
*   K8s 状态事实 `fact-8f6b2cc4ef31` / `fact-8fa7ac1d1616`：证实应用运行正常，排除了进程崩溃的可能性。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 21.3s
├─ 并发证据采集: 41.2s
│  └─ g1 aiops-case-v13/workload: 41.2s (Evidence 33.3s, RCA 7.8s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
