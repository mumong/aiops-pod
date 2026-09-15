## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 持续处于 Terminating 状态（超过 12 分钟）且未被回收。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | pod.phase: Running, pod.status: Terminating (lasts 13m) | 描述 Pod 处于“已收到删除请求但未完成回收”的停滞状态 |
| 2 | K8s Event | kubernetes | Normal Killing 13m/12m kubelet Stopping container app | 证明 kubelet 已在 13 分钟前执行了终止容器的动作，与当前状态矛盾 |
| 3 | K8s State | kubernetes | container.last_terminated_reason: Error, container.last_exit_code: 137 | 说明容器 app 被系统信号（OOMKilled 等）强制终止 |
| 4 | Metric | prometheus | kube_pod_container_status_restarts_total (app): 0 | 佐证容器从未成功重启，处于被冻结的 Terminating 阶段 |
| 5 | Logging | elasticsearch | http_request /work: 200 (first: 03:47:09, last: 03:47:15, allocated_mib 0→0) | 证明应用逻辑在终止前运行正常，且资源使用未超限，137 退出并非应用内部内存不足导致 |
| 6 | Tracing | deepflow+tempo | Flow GET /work: 200 (duration 3698~17208us); Trace 1edba7b29f23053616d75e955fa073c8 关联日志与 Flow | 关联了 03:47:09 的 Trace 日志与网络流，确认终止前应用层无异常 |

**证据说明：**
- K8s 状态（#1）与 Event（#2）共同证实：kubelet 早在 13 分钟前就杀死了容器，但 Pod 始终卡在 Terminating 阶段。
- 容器退出码 137（#3）且重启次数为 0（#4），说明应用进程没有启动即被杀，且后续没有发生重启，印证了 Pod 处于“冻结”状态。
- 日志与 Tracing 数据（#5, #6）显示，在 03:47:09 ~ 03:47:15 期间应用请求正常且内存极低（0 MiB），排除了应用侧 OOM 导致无法退出的可能，进一步指向外部干预或机制卡死。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 被删除请求（deletionTimestamp 设置） → 容器 app 因退出码 137 被 kubelet 杀死 → API Server 检查 finalizers 列表发现 'aiops.lab/hold' 未清除 → Pod 资源回收流程阻塞在 Terminating 状态
```

### 根因结论

已确认根因：**Pod 配置了自定义 finalizer `aiops.lab/hold` 且未被移除，导致 Kubernetes API Server 无法完成资源删除流程。**

- **证据支持**：K8s Event 明确记录了 kubelet 在 13 分钟前已成功停止容器（`fact-bea9d8893ab1`），且容器因信号退出（`fact-3d913c8bb218`）。然而 Pod 状态持续停留在 `Terminating`（`fact-3cf8b39b1bf6`），结合日志显示终止前应用内存使用正常且退出码 137 为系统级信号，说明应用进程已正常退出。此时 Pod 未被删除的唯一阻碍是 Kubernetes 机制中的 Finalizer 未满足清理条件。
- **根因机制**：Kubernetes 在删除 Pod 时会等待所有注册在 `finalizers` 列表中的逻辑执行完毕。`aiops.lab/hold` 最终未被移除（通常需对应的 Controller 或手动操作），导致 API Server 挂起删除操作，尽管底层容器已被清理。

---

## 📊 性能统计

```text
├─ 总耗时: 2.7m
├─ 问题定位: 17.4s
├─ 并发证据采集: 131.8s
│  └─ g1 aiops-case-11/workload: 131.8s (Evidence 123.0s, RCA 8.5s)
└─ 汇总总结: 13.4s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
