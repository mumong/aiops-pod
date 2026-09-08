## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 卡在 Terminating 状态 45 分钟未删除 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Phase | `Terminating (lasts 45m)` | 核心异常状态：Pod 卡死在终止流程 |
| 2 | K8s State | Container Status | 最后一次终止原因为 `Error` | 解释为何容器已终止，但 Pod 未进入已删除状态 |
| 3 | K8s State | Container Exit | `Exit Code: 137` | 表明进程被强制杀掉（SIGKILL），非正常退出 |
| 4 | K8s Config | Pod Finalizers | `aiops.lab/hold` (上下文) | 关键阻断因素：Pod 配置了自定义 Finalizer |
| 5 | K8s Event | Kubelet Event | `Normal Killing 45m kubelet Stopping container app` | 证明 kubelet 正常执行了杀容器操作，排除了节点故障 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total=0` (采样于 `app` 容器) | 排除因 CrashLoopBackOff 导致不断重启的可能性 |

**证据分析**：
1. 事实 #1 和 #2 共同指向一个矛盾状态：容器已被强制终止（#3, #5），但 Pod 始终处于 Terminating。
2. 事实 #4 提供了唯一合理的解释：Kubernetes 的删除逻辑卡在移除 `aiops.lab/hold` Finalizer 上。只要该 Finalizer 存在，API Server 就会无限期推迟 Pod 的实际删除。
3. 事实 #5 证实了底层 kubelet 工作正常，故障不在宿主机，而在控制平面逻辑或对应的清理控制器。

## 🎯 根因分析 · g1

### 因果链

```text
自定义 Finalizer 'aiops.lab/hold' 残留 → API Server 拒绝执行最终删除操作 → Pod 无法清理（卡死 Terminating） → 业务 Pod 无法彻底回收
```

### 根因结论

**已确认的根因：Pod 被未移除的自定义 Finalizer `aiops.lab/hold` 挂起。**

*   **证据支撑**：Pod 处于 `Terminating` 状态长达 45 分钟（`fact-c482253530c5`），但容器早已停止并报错（`fact-a5ad2dee6122`, `fact-70bae1f10fed`），且 Kubelet 正常执行了停止操作（`fact-56cd47254f22`）。这排除了运行时错误，指向了 Kubernetes 的垃圾回收机制被阻断。事实 #4 揭示了存在名为 `aiops.lab/hold` 的自定义 Finalizer，这是导致该现象的唯一配置证据。
*   **未决事项**：虽然确认了现象是由该 Finalizer 引起的，但输入中**缺乏**以下决定性事实，因此无法判定是“控制器未运行”还是“逻辑错误”：
    1.  负责处理 `aiops.lab/hold` 的控制器/Deployment 当前状态（是否 Running/Pod 是否就绪）；
    2.  该控制器的日志，以查明为何在容器被 Kubelet 杀死后未能成功执行清理逻辑并移除 Finalizer。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 18.3s
├─ 并发证据采集: 47.4s
│  └─ g1 aiops-case-11/workload: 47.4s (Evidence 38.9s, RCA 8.4s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
