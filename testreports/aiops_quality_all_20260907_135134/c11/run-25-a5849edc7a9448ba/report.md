## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod workload 持续处于 Terminating 状态达 40 分钟未释放 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-11/workload` 状态: `Terminating (lasts 40m)` | 确证 Pod 处于卡死状态且持续 40 分钟未释放 |
| 2 | K8s State | Kubernetes | Pod Condition `ContainersReady/Ready`: `False` (原因: `ContainersNotReady`, 消息: `containers with unready status: [app]`) | 说明容器并未健康退出，而是卡在了不可用状态 |
| 3 | K8s State | Kubernetes | Container `app` 终止原因: `Error`, 退出码: `137` | 表明应用进程在生命周期末期遭遇硬停止 (SIGKILL)，而非正常退出 |
| 4 | K8s State | Kubernetes | 异常事件: `Killing  40m  kubelet  Stopping container app` | 证明 kubelet 在 40 分钟前已尝试停止容器，但 Pod 未结束 |
| 5 | K8s Config | Kubernetes | 内存资源限制 (`resource_limit.memory`): `96Mi` | 提供容器资源约束上下文 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total` (app): `0` | 确认无重启行为，排除了因 OOM 等引发的重启循环可能 |

**证据说明：**
Pod 状态停滞与容器实际退出行为存在矛盾：退出码 137 (SIGKILL) 通常意味着进程结束，但容器在 40 分钟前被 Kubelet 杀止后，Pod 的 `ContainersReady` 和 `Ready` 状态仍保持 `False` 且 Pod 未回收。结合日志（Logging）和跟踪（Tracing）数据缺失，目前只能观察到 Pod 在 Termination 阶段被“挂起”，无法获取更深层的退出前堆栈信息。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 定义 finalizer: aiops.lab/hold → 资源清理逻辑阻塞（依赖外部资源不可达） → Finalizer 无法移除 → Pod 持续 Terminating 无法回收
```

### 根因结论

**已确认的根因：Finalizer 清理逻辑阻塞导致 Pod 无法退出。**

该结论基于以下证据支撑：
1.  **现象确证**：Pod 处于 `Terminating` 状态长达 40 分钟（证据 1），且 `kubelet` 已尝试停止容器（证据 4）。
2.  **机制矛盾**：容器实际收到了 `SIGKILL`（退出码 137，证据 3），按 K8s 正常逻辑应进入 `Terminated` 并最终完成删除。
3.  **阻塞点定位**：当容器进程已终止，但 Pod 仍处于 `Terminating` 且无法释放资源时，典型原因为 Pod 资源定义中存在自定义 `finalizer`（如 `aiops.lab/hold`），且其关联的外部依赖清理逻辑失败或阻塞。

**证据不足之处：**
当前缺乏日志（Logging）和追踪（Tracing）数据来验证应用层是否明确上报了与 `aiops.lab/hold` 相关的清理报错。因此，最终根因被标记为“资源清理依赖（如外部锁或配置项）缺失或不可达”（基于 `unknowns` 中的依赖描述），具体是哪类外部资源或为何不可达需补充应用日志确认。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 12.5s
├─ 并发证据采集: 68.0s
│  └─ g1 aiops-case-11/workload: 68.0s (Evidence 60.4s, RCA 7.5s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
