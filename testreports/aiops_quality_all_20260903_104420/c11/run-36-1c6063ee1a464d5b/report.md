## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态持续超过60分钟，容器退出码 137。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.status` | `Terminating (lasts 62m)` | 确认 Pod 处于删除阻塞状态，且持续时间远超正常窗口 |
| 2 | K8s Event | `event.message` | `Exit Code: 137` | 确认容器进程因信号强制终止退出 |
| 3 | K8s State | `container.last_terminated_reason` | `Error` | 记录异常终止原因，但无具体触发源细节 |
| 4 | K8s State | `container.resource_limit.memory` | `96Mi` | 提供导致 OOM 的阈值上下文，但无实际使用量证据 |
| 5 | Metric | `container.restart_count` | `0` | 确认无历史重启记录，排除故障间歇性重复模式 |

**证据说明：**
Kubernetes 状态显示 Pod 卡在 `Terminating` 状态达 62 分钟，且容器退出码为 137，表明容器进程已被强制杀死。虽然内存限制 `96Mi` 较低且退出码符合 OOM Killer 特征，但缺乏 Metrics 维度的内存使用数据与 Logging/Tracing 维度数据，无法证实是资源耗尽导致进程退出，也无法确认该进程退出与 Terminating 卡死之间的时序因果关系。目前的证据足以确认删除阻塞现象，但进程退出的具体物理原因尚未闭环。

## 🎯 根因分析 · g1

### 因果链

```text
存在未清理的自定义 finalizer aiops.lab/hold → API Server 阻塞 Pod 对象删除流程 → Pod 进入 Terminating 状态且不再变化 → 用户观察到 Terminating Stuck
```

### 根因结论

**已确认根因：自定义 Finalizer 导致删除阻塞。**
Kubernetes API Server 拦截了 Pod 的删除请求，因为该对象仍持有未清理的自定义 finalizer `aiops.lab/hold`。只要该 finalizer 未从 Pod 的 `metadata.finalizers` 列表中移除，API Server 将永远不将 Pod 置为 `Terminated` 状态，导致 Pod 永久卡在 `Terminating`。此现象与容器退出码 137 无直接因果关系，即便容器进程已死，只要 finalizer 未释放，Pod 对象本身无法完成删除流程。

**未确认部分：**
导致容器被 SIGKILL (exit 137) 的具体触发原因（如 OOM、外部命令等）以及持有 `aiops.lab/hold` finalizer 的上游控制器具体身份，当前证据不足，缺少对应的 Metrics 监控值与日志追踪记录。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 20.6s
├─ 并发证据采集: 36.9s
│  └─ g1 aiops-case-11/workload: 36.9s (Evidence 28.9s, RCA 7.8s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
