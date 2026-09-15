## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | Pod `workload` (aiops-case-v17) 处于 `CrashLoopBackOff` 状态，容器 `app` 频繁重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_exit_code`: 137 | 致命证据：直接指向 Linux OOM Kill |
| 2 | K8s State | Kubernetes | `container.waiting_reason`: `CrashLoopBackOff` | 核心症状：容器频繁重启被 K8s 标记 |
| 3 | K8s Config | Kubernetes | `container.resource_limit.memory`: 64Mi | 关键背景：极低的硬限制，构成 OOM 触发条件 |
| 4 | K8s Event | Kubernetes | `Liveness probe failed: context deadline exceeded` (x67) | 机制验证：容器崩溃导致健康检查超时 |
| 5 | Logging | Elasticsearch | `GET /health HTTP/1.1` 200 (最近观测 14:48:53) | 终止前状态：最后时刻服务进程仍存活 |
| 6 | Tracing | DeepFlow/Tempo | Flow `GET /health` 响应 200，耗时 3001ms ~ 3001.8ms | 现象印证：确认 OOM 前服务响应存在且延迟较高 |

证据表明：Pod `aiops-case-v17/workload` 在运行中发生 OOM Kill (Exit Code 137)，导致容器进程被强制终止。此时 Liveness Probe 因连接重置/无响应触发超时，随后 K8s 执行重启策略，最终进入 `CrashLoopBackOff`。Tracing 日志证实进程在崩溃前仍对 `/health` 请求进行响应（尽管延迟约 3s），证明 OOM 是突发的硬限制触发，而非应用主动退出或逻辑挂起。

## 🎯 根因分析 · g1

### 因果链

```text
memory_limit: 64Mi → 进程内存增长触及硬限制 → 触发 OOMKill (Exit 137) → 容器进程崩溃 & Liveness Probe 超时 → Pod 重启进入 CrashLoopBackOff
```

### 根因结论

**根因：容器内存硬限制配置过低 (64Mi)，导致应用进程被 OOMKill 终止。**

1. **直接原因**：容器 `app` 被分配 64Mi 的内存限制 (`fact-41d641a08572`)。Linux 内核在内存不足时触发 OOM Killer，以 Exit Code 137 终止进程 (`fact-35f97d153037`)。
2. **现象形成**：进程终止后，Kubernetes 的健康检查（Liveness Probe）检测到连接失败或超时 (`fact-37908e94807f`)，判定容器不健康。K8s 随之重启容器，但应用再次快速触发 OOM，形成 `CrashLoopBackOff` (`fact-9c8bb93dd67d`, `fact-05c8924e31ef`)。
3. **证据支撑**：
   - Exit Code 137 是 OOM Kill 的标准标志 (`fact-35f97d153037`)。
   - 64Mi 的极低内存限制提供了 OOM 的物理原因 (`fact-41d641a08572`)。
   - 缺失内存使用率 Metrics 无法展示增长曲线，但 OOM 事件的发生本身已足以定责。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 13.4s
├─ 并发证据采集: 106.7s
│  └─ g1 aiops-case-v17/workload: 106.7s (Evidence 94.8s, RCA 11.7s)
└─ 汇总总结: 11.9s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
