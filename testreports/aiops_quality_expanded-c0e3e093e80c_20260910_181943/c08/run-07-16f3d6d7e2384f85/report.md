## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: OOMKilled (`fact-07bbc6ae8dd3`) | 确诊容器被 OOM Killer 终止，指向内存超限 |
| 2 | K8s Config | kubernetes | `container.resource_limit.memory`: 64Mi (`fact-4de21551386d`) | 提供判定“超限”的硬限制阈值 |
| 3 | K8s Event | kubernetes | `event.message`: `Exit Code: 137` / `Reason: OOMKilled` (`fact-0c5fcb1a7ffe`, `fact-710f435fba53`) | 系统级确认因 OOM 强制杀进程 (信号 9) |
| 4 | K8s State | kubernetes | `container.last_exit_code`: 137 (`fact-12f53ce9ed02`) | 独立于 Event 的退出码事实，一致指向被杀 |
| 5 | Metric | prometheus | `container_memory_working_set_bytes`: 从 47013888 (22:07) 涨至 59645952 (22:17)，逼近 64Mi (`fact-5669cab18817`, `fact-126a2c9ba44b`) | 展示重启间期的持续增长趋势 |
| 6 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason`: 1 (OOMKilled) (`fact-1457800b5e10`) | 监控侧事实佐证容器终止原因为 OOM |
| 7 | Logging | elasticsearch | `memory allocation advanced` (pattern `fact-47ca0ed25469`) | 应用层日志确认代码逻辑中存在持续内存分配行为 |

**证据印证：**
*   Kubernetes 维度的 `OOMKilled` 事件、`137` 退出码与 Prometheus 侧的终止原因指标形成闭环，确证容器进程是被系统 OOM Killer 杀死的。
*   Prometheus 内存指标 (E5, E6) 显示内存使用量随时间从 45Mi 附近稳步攀升至 56Mi 以上，且趋势向上，这与应用日志 (E7) 中记录的内存分配行为一致，排除了瞬间突发导致 OOM 的可能性，指向持续增长。

## 🎯 根因分析 · g1

### 因果链

```text
应用端点 /work 触发持续内存分配 → 容器内存使用量在两次重启间持续攀升 → 触及 64Mi 硬限制触发 OOM Killer → Pod 频繁崩溃重启 (CrashLoopBackOff)
```

### 根因结论

**已确认根因：** 容器内存限制 (64Mi) 不足，且应用存在内存持续增长现象。

具体机制如下：
1.  **触发：** 应用处理请求时，内存分配量持续上升。
2.  **机制：** 容器内存使用量随时间逐步逼近并达到配置上限 `64Mi`。
3.  **直接失败：** Linux 内核 OOM Killer 介入，以信号 9 强制终止应用进程，导致容器退出码为 `137`。
4.  **用户可见现象：** K8s 检测到容器频繁崩溃重启，Pod 状态进入 `CrashLoopBackOff`。

依据 `fact-07bbc6ae8dd3` (OOMKilled)、`fact-4de21551386d` (64Mi Limit)、`fact-126a2c9ba44b` (内存持续增长)、`fact-47ca0ed25469` (内存分配日志) 确证此结论。

---

## 📊 性能统计

```text
├─ 总耗时: 2.8m
├─ 问题定位: 24.7s
├─ 并发证据采集: 127.5s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 127.5s (Evidence 118.4s, RCA 9.0s)
└─ 汇总总结: 13.3s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
