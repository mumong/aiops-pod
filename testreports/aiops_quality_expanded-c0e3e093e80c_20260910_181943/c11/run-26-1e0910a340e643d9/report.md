## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 存在自定义 finalizer `aiops.lab/hold`，阻止了 Kubernetes 在完成容器终止后清理 Pod 对象，导致其长期处于 Terminating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-11/workload` status: `Terminating (lasts 56m)` | 确认核心故障现象：资源长期处于终止状态 |
| 2 | K8s State | kubernetes | container.last_terminated_reason: `Error` | 确认应用容器存在异常终止的历史记录 |
| 3 | K8s State | kubernetes | container.last_exit_code: `137` | 确认容器因 OOM Kill 或外部强杀 (SIGKILL) 退出 |
| 4 | K8s Event | kubernetes | `Normal  Killing         56m   kubelet    Stopping container app` | 确认 kubelet 已发起停止操作，但对象未被清理 |
| 5 | K8s State | kubernetes | container.condition: `ContainersReady: False`, `Ready: False` | 确认容器未进入就绪/终止状态，对象处于挂起清理流程 |

证据表明，应用容器经历了 `Error` 并退出（Exit Code 137），但 Kubernetes 对象的清理流程（Terminating 状态）在 56 分钟内一直未结束，说明 Kubernetes 的终结器（Finalizer）机制阻碍了对象的删除。

## 🎯 根因分析 · g1

```text
Pod aiops-case-11/workload 存在自定义 finalizer `aiops.lab/hold` → 
Kubernetes 无法完成 Pod 对象的资源清理（Garbage Collection） → 
Pod 长期处于 Terminating 状态，伴随 Container Ready: False → 
导致 Pod 资源无法被回收，且无法通过删除操作释放该工作负载
```

### 根因结论
**已确认根因**：Pod `aiops-case-11/workload` 挂载了自定义 finalizer `aiops.lab/hold`（证据来源：诊断事实描述与 Terminating 状态持续 56 分钟未清除的现象）。
该 finalizer 导致 Kubernetes 在完成容器停止（Exit 137）后，仍无法从 API Server 移除该 Pod 对象。虽然容器本身因 Error 退出，但由于 finalizer 未释放，对象状态永远锁定在 `Terminating`，导致集群资源（如网络、端口、调度位点）无法被正确回收。

**补充说明**：
- 容器退出码 137 表明应用容器自身可能发生过 OOM 或接收到了终止信号，但这只是引发终止流程的原因，不是导致“长期 Terminating”的根本原因。根本原因是 `aiops.lab/hold` finalizer 未正常释放。
- 由于日志（Logging）和链路追踪（Tracing）数据缺失，无法确定是谁向该 finalizer 注册了锁或者为何未能释放该锁，但上述 Kubernetes 机制事实已足以解释“长期 Terminating”这一核心故障。

---

## 📊 性能统计

```text
├─ 总耗时: 9.6m
├─ 问题定位: 25.5s
├─ 并发证据采集: 541.3s
│  └─ g1 aiops-case-11/workload: 541.3s (Evidence 536.8s, RCA 4.4s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
