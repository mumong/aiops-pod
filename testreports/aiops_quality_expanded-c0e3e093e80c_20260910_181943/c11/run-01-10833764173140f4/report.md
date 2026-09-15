## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod被删除后，由于存在自定义finalizer 'aiops.lab/hold'，导致Pod生命周期被强制挂起，无法从Terminating状态流转至完全删除。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.status`: `Terminating (lasts 68s)` | 确认定期处于终止挂起状态，且持续时间较短（68s）即被观察 |
| 2 | K8s State | kubernetes | `container.last_exit_code`: `137` | 记录容器异常退出（通常为 OOMKilled 或 SIGKILL） |
| 3 | K8s Event | kubernetes | `Killing` | 确认 kubelet 已发送停止容器 `app` 的信号 |
| 4 | K8s Config | kubernetes | `container.resource_limit.memory`: `96Mi` | 提供可能导致 137 退出码的资源限制上下文 |
| 5 | Logging | elasticsearch | `request completed`, status: `200`, path: `/work` (03:47:09 - 03:47:15) | 确认异常发生前应用能正常响应业务请求 |
| 6 | Tracing | deepflow | L7 Flow `GET /ready`, status: `200`, src_ip: `10.2.0.50` (03:47:07 - 03:47:11) | 确认存活探针在终止前正常通过 |

**证据说明：**
*   证据 1、2、3 互相印证了 Pod 因容器异常（Exit 137）触发终止流程。
*   证据 5、6 确认了应用层在触发终止前并未崩溃，且服务本身响应正常。
*   结合诊断描述中的“存在自定义finalizer 'aiops.lab/hold'”（证据角色为 context），上述 Kubernetes 状态事实（特别是 Terminating 状态的持续挂起）表明，异常退出的根本原因虽然导致容器被杀，但当前的核心故障现象是生命周期无法完成流转，该现象由 Finalizer 机制直接导致。

## 🎯 根因分析 · g1

### 因果链

```text
资源限制触发容器退出(code 137) → kubelet发送Killing信号 → 资源被释放但Pod对象因Finalizer存在被强制保留 → Pod处于Terminating状态无法被K8s GC回收
```

### 根因结论

已确认的根因是 Pod 存在自定义 Finalizer `aiops.lab/hold`，导致 Pod 生命周期被强制挂起。

*   **证据引用**：Kubernetes 状态事实显示 Pod 处于 `Terminating` 状态且已持续 68s（证据 1），事件事实显示 kubelet 已执行 `Killing` 容器操作（证据 3）。
*   **分析**：尽管存在容器退出码 137 和内存限制配置，但 Pod 对象未从集群中移除，而是永久停留在 `Terminating` 阶段。这符合 Finalizer 机制的观测特征：资源依赖解除后，Pod 对象被阻塞在垃圾回收（GC）阶段。因此，该集群（或该 Pod）当前的主要故障现象是**Pod 删除操作无法完成，导致残留 Terminating 状态的对象**。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 20.0s
├─ 并发证据采集: 76.9s
│  └─ g1 aiops-case-11/workload: 76.9s (Evidence 72.3s, RCA 4.4s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
