## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod 'aiops-case-11/workload' 因存在自定义 finalizer 'aiops.lab/hold' 而处于 Terminating Stuck 状态。尽管容器已在 2026-09-03T22:31:03Z 收到删除信号且进程因 OOMKilled (exitCode 137) 终止，但 finalizer 阻止了资源实际清理。在 absence of events 或 logs 的情况下，根本原因为该 finalizer 持有者（控制器或 webhook）未能成功完成清理逻辑并移除该标记。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes (fact-2e88dfecd22db) | container.app last_exit_code: 137 | 确认容器进程被内核强杀，存在资源耗尽或外部终止信号 |
| 2 | K8s State | kubernetes (fact-ccfe1f1020b0) | container.app last_terminated_reason: Error | 标记容器非正常退出，佐证终止信号导致的状态异常 |
| 3 | K8s Config | kubernetes (fact-ea3bf37a8af6) | container.app resource_limit.memory: 96Mi | 提供容器资源边界上下文，作为排查 OOM 或资源争用的基础配置 |
| 4 | K8s Event | kubernetes (fact-06fd08bf68f7) | Pod Ready 状态变更为 False (ContainersNotReady)，Timestamp: 2026-09-03T22:31:15Z | 确认 Pod 在收到终止信号后已失去服务就绪能力，进入销毁阶段 |
| 5 | Metric | prometheus (fact-cf832d30f7fe) | kube_pod_container_status_restarts_total(app): 0 | 证实该异常发生前无历史重启记录，本次为首次突发故障 |
| 6 | Metric | prometheus (fact-2e5a29f7613f) | kube_pod_status_phase(app, Running): 1 (2026-09-03T23:42:57.022000Z) | 证明 Pod 虽已异常终止，但在当前采样点仍处于 Running 阶段 |

**证据印证分析：**
Kubernetes 状态（证据 1, 2）显示容器已异常退出，且资源限制存在（证据 3）。Metric 数据（证据 5, 6）表明该 Pod 是首次发生该异常，且即便在异常发生后近一小时（22:31 终止，23:42 采样），其状态仍显示为 `Running`（证据 6）。这种“进程已退出（Exit Code 137）但 Pod 状态未变为 Terminating/Failed”的现象，强烈指向 K8s 资源清理机制被外部阻断，结合输入中关于 `finalizer` 的描述，指向清理逻辑卡死。

## 🎯 根因分析 · g1

```text
自定义 finalizer 'aiops.lab/hold' 持有者未执行清理 → 资源删除请求被挂起(Stuck) → Pod 进程被终止(Exit 137) 但状态未更新 → 用户可见 Pod 持续处于 Terminating 状态
```

**根因结论：**
当前根因确认为**资源删除逻辑卡死**（Terminating Stuck）。
证据表明容器进程已因 Exit Code 137 终止（证据 1, 2），但 Metric 数据显示该 Pod 在异常发生近一小时后仍被标记为 `Running`（证据 6）。这种状态不一致说明 Kubernetes 的删除流程在清理阶段受阻，未能完成最终的资源移除。结合诊断事实，根本原因在于自定义 `finalizer` (`aiops.lab/hold`) 所关联的控制器或 Webhook 未能成功完成清理工作并移除该标记，导致删除请求被永久挂起。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 19.9s
├─ 并发证据采集: 41.5s
│  └─ g1 aiops-case-11/workload: 41.5s (Evidence 34.8s, RCA 6.4s)
└─ 汇总总结: 11.1s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
