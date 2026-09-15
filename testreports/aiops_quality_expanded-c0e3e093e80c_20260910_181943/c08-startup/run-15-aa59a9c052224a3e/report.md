## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | 容器内存限制（64Mi）小于应用启动时分配的内存大小（256Mi），导致容器因 OOMKilled 退出并反复重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-fab3e5218cb2` (Kubernetes) | `type=Warning, reason=BackOff, message="Back-off restarting failed container app in pod workload_aiops-case-v15(da351bf0-c4ab-47a0-b24d-7c7a75950753)"` | 展示容器反复退出后的最终等待重启现象 |
| 2 | K8s State | `fact-ae3c087eb7a0` (Kubernetes) | `container=app, reason=OOMKilled` | 直接指出导致容器被强制终止的系统级原因 |
| 3 | K8s State | `fact-5fc484a4a5b6` (Kubernetes) | `container=app, exit_code=137` | 与 OOMKilled 机制一致，确认进程非正常退出 |
| 4 | K8s State | `fact-26f373516836` (Kubernetes) | `container=app, value=64Mi` | 容器当前的硬内存限制值，为评估资源冲突提供基准 |
| 5 | Logging | `fact-545e18f06a78` (Elasticsearch) | `timestamp=2026-09-14T09:52:58.605Z, log.message="startup allocation 256Mi"` | 记录应用启动时请求的初始内存大小，与 K8s 限制存在明显偏差 |
| 6 | Metric | `fact-1dc64d32d5c7` (Prometheus) | `labels={container="app", reason="OOMKilled"}, value=1` | 通过 Prometheus 侧写独立印证了容器的终止原因为 OOM |
| 7 | Metric | `fact-23669b90a2ed` (Prometheus) | `labels={container="app", reason="CrashLoopBackOff"}, value=1` | 从监控层面确认了 CrashLoopBackOff 的活跃状态 |
| 8 | Metric | `fact-b83ee82cb994` (Prometheus) | `labels={container="app"}, value=14` | 量化了应用的重启频次，佐证故障具有反复触发的特征 |

**证据综合说明：**
Kubernetes 侧的 `OOMKilled` 状态、`exit_code=137` 与 `BackOff` 事件，在日志侧找到了应用试图分配 `256Mi` 的具体起点，在 Metrics 侧获得了 `OOMKilled` 标签的指标印证。日志显示的需求量（256Mi）超出了 K8s 侧配置的硬限制（64Mi），因果链条完整闭合，无维度冲突。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动请求分配 256Mi 内存 → 超出 K8s 硬限制 (64Mi) → Linux OOM Killer 终止进程 (Exit 137) → 容器 CrashLoopBackOff 并反复重启
```

### 根因结论

**已确认的根因：容器内存配置限制（64Mi）严重低于应用启动所需的内存大小（256Mi），导致 Linux 内核 OOM Killer 强行终止应用进程。**

这一机制在证据中形成了完整闭环：
1.  **日志证据**（#5）显示应用启动时尝试申请 256Mi 内存。
2.  **配置证据**（#4）确认该容器的硬内存限制仅被设定为 64Mi。
3.  **状态与指标证据**（#1, #2, #3, #6, #7, #8）共同指向了由内存越界触发的 OOMKilled 以及随后的反复重启现象。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 19.6s
├─ 并发证据采集: 31.7s
│  └─ g1 aiops-case-v15/workload: 31.7s (Evidence 23.8s, RCA 7.7s)
└─ 汇总总结: 12.9s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
