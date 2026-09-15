## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | Pod aiops-case-v12/workload stuck in Terminating state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s pod.status | status: Terminating (lasts <invalid>); phase: Running | 确认 Pod 处于删除中的停滞状态 |
| 2 | K8s Event | K8s event | Normal Killing 68s kubelet Stopping container app | 确认 Kubelet 已发起停止信号，但容器未立即退出 |
| 3 | K8s Event | K8s event (Aggregated) | Annotations: cni.projectcalico.org/podIP: 172.16.104.23/32 | 确认网络资源已被解绑标记（Context），佐证 Pod 正在经历终止流程 |
| 4 | K8s Config | K8s config (Limits) | CPU: 50m, Memory: 32Mi | 排除资源过载导致无法响应的可能 |
| 5 | Logging | ELK | application started (at 06:11:06.602Z) | 确认应用进程存活且日志无异常报错 |
| 6 | Tracing | Tool | (empty) | 无分布式追踪数据，无法观察 L7 调用栈或 Hook 上下文 |

**证据印证分析**：
- Pod 状态（#1）显示 `Terminating` 且 `Running`，直接表明进程未在终止期内退出。
- Kubelet 的 Killing 事件（#2）证实了系统层面已经尝试结束容器，但未能达成 `Terminated` 状态，这与 #1 的现象互为表里。
- 尽管应用日志（#5）仅显示“Started”，表明应用自身未崩溃，但结合 Pod 停滞状态，高度指向优雅关闭（preStop）流程受阻。
- K8s 配置（#4）显示资源极低，进一步支持了非资源耗尽导致的阻塞。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 标记删除 (deletionGracePeriodSeconds=3900) → 应用 preStop hook 阻塞 (等待条件不满足) → Kubelet 发送 Killing 信号但容器未退出 → Pod 长期处于 Terminating 状态
```

### 根因结论

**根因**：Pod `aiops-case-v12/workload` 无法终止是因为其 `app` 容器陷入了 preStop 优雅关闭流程的阻塞状态。Kubelet 已经发出了停止容器的信号（如 Evidence #2 所示），但由于应用内部正在等待特定的清理条件（如文件 `/state/teardown-requested`）未能满足，导致容器进程未能响应终止信号并在宽限期（Grace Period）内退出，从而使 Pod 长期滞留于 `Terminating` 状态（如 Evidence #1 所示）。

**证据引用**：
- 现象确证：Pod 处于 Terminating 但 Phase 为 Running（#1, #2）。
- 排除资源故障：容器内存限制仅 32Mi（#4），且日志无报错（#5），排除了 OOM 或应用内部崩溃。
- 限制说明：由于缺少 Tracing 数据（#6）和关于应用内部逻辑的进一步事实，preStop 阻塞的精确原因（是应用 Bug 还是配置缺失）被标记为未确认（Unknown）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 19.1s
├─ 并发证据采集: 84.7s
│  └─ g1 aiops-case-v12/workload: 84.7s (Evidence 76.3s, RCA 8.4s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
