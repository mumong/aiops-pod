## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 进入 Terminating 状态超过54分钟未释放，尽管容器已终止且 deletionGracePeriodSeconds=0。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.status | 当前状态为 `Terminating (lasts 54m)` | 确认核心症状：对象长时间无法释放 |
| 2 | K8s State | pod.condition | Ready=False (ContainersNotReady); Initialized=True; PodScheduled=True | 证明容器已退出但对象仍被保留在系统中 |
| 3 | K8s State | container.last_terminated_reason | Exit Code: 137 (SIGKILL) | 证明容器进程被强制终止，触发删除流程 |
| 4 | K8s Event | event.message | Killing: Stopping container app | 确认 kubelet 正常执行了容器清理操作 |
| 5 | K8s Config | container.resource_request.cpu | 20m | 确认配置量级，非容量瓶颈 |
| 6 | K8s Config | container.resource_limit.memory | 96Mi | 确认硬限制存在，但非当前状态卡住原因 |
| 7 | K8s State | pod.finalizers | 包含 `aiops.lab/hold` | 发现阻止对象删除的关键元数据阻碍 |
| 8 | Metric | container.restart_count | 0 | 确认容器无重启记录，符合单次异常终止特征 |

上述 K8s 事实相互印证：`exit_code=137` 和事件日志表明容器本身的生命周期已结束，且清理操作（Stopping container app）已由 kubelet 执行；然而 Pod 对象状态仍停留在 Terminating 长达 54 分钟，且无重启发生。配置资源限制虽存在，但未触发再次重启，排除了容器持续崩溃重起的干扰。关键阻碍点在于元数据中的 `aiops.lab/hold` finalizer，它与容器的正常终止现象并列，解释了为何 API Server 的删除请求无法完成对象释放。

## 🎯 根因分析 · g1

### 因果链

```text
自定义 finalizer 'aiops.lab/hold' 存在于 Pod spec.metadata.finalizers → API Server 收到删除请求后暂停 GC 并等待 finalizer 移除 → 最终状态机卡在 Terminating 阶段无法完成删除 → Pod 实体持续占用并显示 Terminating 状态
```

### 根因结论

**已确认根因**：`aiops-case-11/workload` Pod 因配置了自定义 `finalizer`（`aiops.lab/hold`），且对应的清理控制器未能成功处理并移除该 finalizer，导致 Kubernetes API Server 无法完成对象删除流程。

该结论由以下事实支撑：
- Pod 状态显示 `Terminating` 超过 54 分钟，且容器退出码为 `137`，表明容器进程已正常终止，资源释放的障碍不在容器运行时，而在 Pod 对象层面的删除阻塞。
- 存在 `aiops.lab/hold` finalizer，这是导致删除请求被挂起的直接元数据原因。
- Metrics 显示 `restart_count` 为 0，排除了因容器反复崩溃重启导致的不稳定状态。

**未确认/需补充的信息**：
- 导致容器进程被 `SIGKILL` (Exit 137) 的确切上游原因（如 OOM 还是外部探测失败）。
- 为什么 `aiops.lab/hold` 对应的控制器未成功执行其清理逻辑并移除 finalizer。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.0s
├─ 并发证据采集: 37.1s
│  └─ g1 aiops-case-11/workload: 37.1s (Evidence 28.1s, RCA 8.8s)
└─ 汇总总结: 11.1s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
