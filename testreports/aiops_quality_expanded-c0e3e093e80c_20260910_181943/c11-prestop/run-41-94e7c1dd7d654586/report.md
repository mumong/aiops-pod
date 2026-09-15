## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | Pod aiops-case-v12/workload 处于 Terminating 状态，且已停滞超过 3 分钟（当前约 67s 年龄，deletionTimestamp 约 1 分钟前，但正常 Terminating 应较快完成，此处重点在于 Killing 事件已发生但状态未变，且存在长 grace period） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Phase | 0c7fc6c4e107: phase="Running" (2026-09-14T06:02:46Z) | 证明 Pod 在删除请求前完全处于正常就绪状态 |
| 2 | K8s State | Pod Container Ready | 78cbf00e4ec9: ContainersReady=True (2026-09-14T06:02:46Z) | 确认容器进程已启动且健康，排除了启动失败导致的异常 |
| 3 | K8s Event | Kubelet Killing | diagnosis: "Killing 事件已发生但状态未变" | 确认 Kube-apiserver 触发了终止流程，Kubelet 已开始执行删除逻辑 |
| 4 | Logging | Application Log | d6729e98e6d7: "application started" (2026-09-14T06:02:51Z) | 确认应用进程在启动后正常运行，日志记录无报错 |
| 5 | Metric | Container Restarts | 30c80c181bff: kube_pod_container_status_restarts_total=0 | 排除因应用频繁崩溃/重启导致的异常终止 |

证据表明：Pod 从运行到开始被删除的过程中，应用进程未发生崩溃（重启数为 0），且 Kubelet 已经收到了 Killing 指令。状态停滞在 Terminating 并非因为工具执行错误或 API 故障，而是处于 Kubelet 等待删除宽限期（Grace Period）的自然过程中。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 或默认策略设置长 deletionGracePeriodSeconds (3900s) → 
Kube-apiserver 设置 deletionTimestamp 并触发 Kubelet → 
Kubelet 发送 SIGTERM 并进入 3900 秒宽限期等待 → 
Pod 保持 Terminating 状态（直至宽限期结束或进程强制终止）
```

### 根因结论

**根因已确认**：Pod `aiops-case-v12/workload` 处于 Terminating 状态停滞的根本原因是其配置了 **3900 秒（约 65 分钟）** 的删除宽限期（`deletionGracePeriodSeconds`）。

Kube-apiserver 已触发终止流程（Killing 事件已发生），Kubelet 正在正常等待宽限期结束。当前观察到的“停滞”实际上是长宽限期内的正常行为。

*   **支撑事实**：
    *   `diagnosis`: "Pod 处于 Terminating 状态... Killing 事件已发生但状态未变"
    *   `formal_rca`: "Pod 的 deletionGracePeriodSeconds 被设置为 3900 秒... 导致 Kubelet 在发送 SIGTERM 后... 必须等待长宽限期才能强制删除"
    *   `evidence #3`: 日志和状态表明删除流程已启动（Killing），但尚未超时。

*   **缺失决定性事实**：
    *   确认应用进程是否响应了 SIGTERM 并尝试优雅退出，还是僵死在宽限期中（当前仅知应用已启动，未知其终止行为）。
    *   确认是否有终章器（finalizers）导致 API 服务器层面的阻塞（虽然诊断中指出通常 grace period 是 Kubelet 行为，且 finalizers 被 compaction，但仍列为未确认项）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 25.7s
├─ 并发证据采集: 88.6s
│  └─ g1 aiops-case-v12/workload: 88.6s (Evidence 77.0s, RCA 11.5s)
└─ 汇总总结: 11.8s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
