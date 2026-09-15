## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | aiops-case-v15/workload 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `BackOff 3m20s (x535 over 118m) ... Back-off restarting failed container app` | 证明 Pod 持续处于重启风暴中 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason: OOMKilled` | 确认容器被系统进程终止的直接原因 |
| 3 | K8s Event | Kubernetes | `Exit Code: 137` | 佐证被内核 OOM Killer 终止的标准特征 |
| 4 | K8s Config | Kubernetes | `container.app.memory_limit: 64Mi` / `memory_request: 8Mi` | 确认容器受限的硬边界资源 |
| 5 | Logging | Elasticsearch | `startup allocation 256Mi` | 揭示容器启动时请求的实际内存量 |
| 6 | K8s State | Kubernetes | `pod.restart_count: 28` | 验证异常状态的持续性 |

**证据综合分析**
Kubernetes 事件和状态事实（#1, #2, #3, #6）从不同侧面（事件计数、终止原因、退出码、重启总数）确认了容器处于“启动-被杀-重启”的死循环中。日志（#5）提供了关键的内存分配行为证据，显示应用启动即申请 256Mi；K8s 配置（#4）显示内存上限仅为 64Mi。两者结合，构成了 OOM 触发条件与结果的完整闭环证据链。

## 🎯 根因分析 · g1

### 因果链

```text
资源限制过低 (64Mi limit) → 容器启动分配 256Mi 内存触发内核 OOM Killer → 进程以 Exit Code 137 终止 → 控制器触发 CrashLoopBackOff 反复重启
```

### 根因结论

已确认根因为：**容器配置的资源限制严重不足**。

证据表明，应用在启动阶段尝试分配 256Mi 内存（日志证据 #5），这远超出了 Kubernetes 配置的 64Mi 硬限制（配置证据 #4）。这种资源缺口导致 Linux 内核 OOM Killer 介入终止了容器进程（退出码 137，状态证据 #2, #3），进而引发控制器无限次重启（事件证据 #1, #6），表现为 CrashLoopBackOff。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 15.8s
├─ 并发证据采集: 45.1s
│  └─ g1 aiops-case-v15/workload: 45.1s (Evidence 35.8s, RCA 9.1s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
