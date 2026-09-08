## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod被注入了自定义Finalizer 'aiops.lab/hold'导致删除请求无法完成，同时容器进程因OOM或资源限制被宿主机Killer强制终止（Exit 137），引发应用异常关闭；由于Finalizer未解除，Pod对象卡在Terminating状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-11/workload` 处于 `Terminating (lasts 8m1s)` 状态 | 定义异常实体及其阻塞现象 |
| 2 | K8s State | kubernetes | `pod.condition` 状态：`ContainersReady: False`, `Ready: False`，原因 `ContainersNotReady`；`Initialized: True` | 确认容器进程异常终止后未进入就绪状态，且初始化阶段已完成 |
| 3 | K8s Event | kubernetes | 事件消息：`Exit Code: 137`；容器 `app` 最后终止原因为 `Error` | 证明容器进程被宿主机强杀（OOM Killer 或资源硬限制），而非正常退出 |
| 4 | K8s Config | kubernetes | `container.resource_limit.memory`: `96Mi`; `container.resource_request.memory`: `24Mi` | 提供资源边界上下文，解释为何可能触发 137 退出 |
| 5 | K8s Event | kubernetes | 事件消息：`Normal Killing         8m    kubelet            Stopping container app` | 确认 kubelet 因容器状态异常主动停止了该容器 |
| 6 | Logging | elasticsearch | 模式：`http_request` 成功完成 200 (path: `/work`)，时间窗口 2026-09-03T22:31:06Z 至 22:31:12.134Z | 确认应用进程在异常发生前 2 分钟仍在正常运行 |
| 7 | Tracing | deepflow | L7 Flow `GET /work` 连续 5 次成功 (200)，时间窗口 2026-09-04 06:31:06 至 06:31:14 | 跨平台流量追踪确认服务在异常发生期间网络链路通畅，排除网络层导致的假性异常 |

**证据综合说明：**
- 证据 3 与证据 5 共同指向容器进程因非正常信号（137）被宿主机制终止。
- 证据 6 和 7 确认了在终止前一刻应用功能正常，排除了应用内部持续崩溃或长时间无响应的可能，表明异常发生具有突发性。
- 尽管输入诊断中包含“自定义Finalizer导致卡住”的结论，但在事实边界内未提取到 `aiops.lab/hold` finalizer 的实际存在证据；目前的 K8s 状态（证据 1、2）仅表现为 Pod 因进程异常退出而卡在 Terminating。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存占用超界(疑似OOM)或触发Limit → 宿主机Killer发送SIGKILL → 容器以Exit 137异常退出并终止(2m前) → Pod被调度器标记为Terminating(当前持续8m1s)
```

### 根因结论

**证据不足。**

1. **现象确认**：当前事实确凿地表明，Pod `aiops-case-11/workload` 的容器进程 `app` 在运行期间突发性异常退出（Exit 137，由 Kubelet Killing 事件及 Pod Terminating 状态支撑），导致该 Pod 当前处于终止过程中。
2. **根因缺失**：虽然正式诊断提及“被注入自定义Finalizer 'aiops.lab/hold'导致删除请求无法完成”，但在提供的工具事实和聚合事实中，**完全缺乏**该自定义 Finalizer 存在的证据（如 Pod 定义中 metadata.finalizers 的原始值）。
3. **判定**：由于缺乏证明“Terminating 状态是由未解除 Finalizer 引起”的关键事实（例如 Pod Spec 中的 finalizers 列表），当前结论仅能确认为“应用异常崩溃导致 Pod 终止”，而无法确认为“因 Finalizer 未释放导致 Termination 挂起”。缺少决定性事实：Pod YAML 中的 Finalizer 定义。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 11.9s
├─ 并发证据采集: 92.6s
│  └─ g1 aiops-case-11/workload: 92.6s (Evidence 82.5s, RCA 9.9s)
└─ 汇总总结: 13.6s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
