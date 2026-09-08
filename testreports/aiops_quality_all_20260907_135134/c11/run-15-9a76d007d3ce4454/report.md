## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | 自定义 Finalizer 'aiops.lab/hold' 未释放导致 Pod 持续处于 Terminating 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-11/workload` 状态 `Terminating (lasts 28m)` | 描述核心异常现象：Pod 进入终态后长时间无法移除 |
| 2 | K8s State | kubernetes | 容器 `app` 终止原因 `Error`，退出码 `137` | 确认容器非正常退出，触发终止流程 |
| 3 | K8s Event | kubernetes | 事件 `Normal Killing`：`Stopping container app` (28m) | 记录容器退出时间点，证实退出发生在终止流程开始时 |
| 4 | K8s Config | kubernetes | 容器 `app` 资源限制 `cpu: 200m`, `memory: 96Mi` | 提供资源上下文，确认是否存在资源耗尽的物理可能 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total` 当前值 `0` | 辅助排除：退出非由周期性 OOMKilled/Killed 循环导致 |
| 6 | Logging | elasticsearch | 日志模式 `request completed`，耗时窗口 `23:09:48` - `23:09:56`，内存变化 `0.0 -> 0.0` | 观察窗口内应用处理正常，未观察到应用层报错或异常波动 |
| 7 | Tracing | deepflow | HTTP Flow `GET /work` 状态 `200`，持续时间 `3626us - 19655us` | 流量层观测佐证业务请求正常响应，排除网络或后端业务逻辑超时 |

**证据关联说明**：
K8s 事件（#3）证实了容器退出发生在 28 分钟前；随后的 K8s 状态（#1）显示该 Pod 在此后长达 28 分钟内一直停滞在 `Terminating` 阶段。Metric（#5）显示重启次数为 0，排除了重启循环。Logging（#6）和 Tracing（#7）证明在退出发生前（及观察窗口内），应用处理请求均正常（HTTP 200），未发生内部错误。结合 Pod 无法移除的特性，异常指向 Finalizer 阻塞机制而非应用本身崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
资源定义中包含 Finalizer 'aiops.lab/hold' → Kubelet 检测到容器 app 退出(exitCode=137) → Finalizer 清理逻辑未响应或未完成 → Pod 被 K8s API 强制阻止移除，持续处于 Terminating
```

### 根因结论

- **已确认根因**：Pod 资源定义中配置了自定义 Finalizer `aiops.lab/hold`。尽管容器 `app` 因接收终止信号（导致 `exitCode: 137`）而正常退出，但 Kubernetes 必须在所有 Finalizer 被移除后才能真正删除 Pod。由于 Finalizer 对应的控制器或 Handler 未能完成清理逻辑（或逻辑未完成），Kubelet 无法移除该 Pod，导致其无限期处于 `Terminating` 状态。
- **证据支撑**：由 `Terminating (lasts 28m)` 状态（证据 1）与 `Container terminated` 事实（证据 2、3）结合推断；Logging（证据 6）和 Tracing（证据 7）排除了业务侧崩溃导致的连锁反应。
- **未确认项**：触发容器 137 退出的确切上游原因（如外部 K8s 操作、宿主机问题或代码异常），以及 `aiops.lab/hold` Finalizer 处理器的具体状态。

---

## 📊 性能统计

```text
├─ 总耗时: 56.5s
├─ 问题定位: 9.9s
├─ 并发证据采集: 34.2s
│  └─ g1 aiops-case-11/workload: 34.2s (Evidence 27.6s, RCA 6.5s)
└─ 汇总总结: 12.4s
```

📋 Runbook 参考

- 未调用 Runbook
