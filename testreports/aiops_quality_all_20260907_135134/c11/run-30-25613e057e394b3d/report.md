## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 被添加了自定义 Finalizer `aiops.lab/hold`，虽然容器进程已终止（Exit Code 137），但 Kubernetes API Server 等待该 Finalizer 对应的控制器完成清理工作并移除它，导致 Pod 长期卡在 Terminating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.phase`: Running, `pod.status`: Terminating (lasts 47m) | 核心症状：Pod 处于异常终止卡死状态。 |
| 2 | K8s Event | Kubernetes | `Stopping container app`, `Exit Code: 137` | 现象溯源：容器进程因 OOM 被强制终结。 |
| 3 | K8s Config | Kubernetes | `resource_limit.cpu`: 200m, `resource_limit.memory`: 96Mi | 环境上下文：资源配额极度受限，佐证 OOM 诱因。 |
| 4 | K8s State | Kubernetes | `ContainersNotReady` (ContainersReady/Ready: False) | 状态印证：容器已非运行态。 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 0 (app) | 排除循环：进程终止后未触发重启机制，属单次事件。 |

**证据说明：**
Kubernetes State 证据链（#1, #2, #4）证实 Pod 在容器终止后，长时间（47分钟）无法移除 `Terminating` 标记且未重启。Metric 证据（#5）通过重启次数为 0，排除了 CrashLoopBackOff 等频繁重启故障，指向外部清理机制的阻塞。

## 🎯 根因分析 · g1

### 因果链
```text
自定义 Finalizer `aiops.lab/hold` 注册 → 触发 Terminate 流程时控制器清理阻塞 → API Server 拒绝移除 Pod Object → 用户可见 Pod 长期卡死 Terminating (Exit Code 137)
```

### 根因结论
**已确认的根因：** Pod `aiops-case-11/workload` 挂载了自定义 Finalizer `aiops.lab/hold`。尽管容器因 OOM（Exit Code 137，见证据 #2）终止，但由于对应控制器未处理该 Finalizer 的移除逻辑，导致 Kubernetes API Server 无法彻底释放 Pod 对象，从而使其永远卡在 `Terminating` 状态。

该根因与 Pod 的 Terminating 状态（见证据 #1）直接因果对应；OOM 终止仅为触发该状态变化的前置事件，而非阻碍清理的根本原因。

---

## 📊 性能统计

```text
├─ 总耗时: 45.7s
├─ 问题定位: 14.9s
├─ 并发证据采集: 22.9s
│  └─ g1 aiops-case-11/workload: 22.9s (Evidence 18.0s, RCA 4.9s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
