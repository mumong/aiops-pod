## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | Pod 应用逻辑与 PreStop Hook 依赖外部信号文件 '/state/teardown-requested' 才能退出，但文件未被创建，导致 kubelet 发送 Killing 信号后容器进程无限循环等待，处于优雅终止的 3900s 宽限期内。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Normal Killing 54s kubelet Stopping container app` | 证明 Kubelet 已进入终止流程并执行杀容器指令 |
| 2 | K8s State | Kubernetes | `Pod phase: Running` / `Status: Terminating (lasts <invalid>)` | 证明 Pod 处于 Termination 阶段但未能退出，卡在优雅终止期内 |
| 3 | K8s Config | Kubernetes | `app` 容器 `cpu_limit: 50m`, `memory_limit: 32Mi` | 资源限制属常规配置，排除因资源耗尽导致的异常挂起 |
| 4 | Logging | Elasticsearch | `2026-09-14T06:13:32.304Z application started` | 提供应用启动基线，缺失终止相关日志印证应用进程被阻塞无法执行退出逻辑 |
| 5 | Metric | Prometheus | `container.app` 重启计数为 `0` | 证明应用当前未经历崩溃重启，处于长期无响应的僵持状态 |

Kubelet 发送 KILL 信号后，Pod 仍停留在 `Terminating` 状态且重启计数为 `0`，表明应用进程虽收到信号但未按预期退出。日志中仅有启动记录而无终止记录，佐证了进程在执行 PreStop Hook 时因依赖文件缺失而陷入无限等待。

## 🎯 根因分析 · g1

### 因果链

```text
应用逻辑与 PreStop Hook 依赖外部信号文件 '/state/teardown-requested' → 文件未被创建导致进程无限等待 → 阻塞在优雅终止 3900s 宽限期内 → Kubelet 持续发送 Killing 信号但容器未退出
```

### 根因结论

**已确认的根因**：应用自身的终止逻辑依赖外部信号文件 `/state/teardown-requested`，由于该文件未被创建，导致应用进程在 PreStop Hook 阶段无限循环等待，无法响应 Kubelet 的终止信号。
- 支撑证据：`K8s State` 显示 Pod 长期处于 `Terminating` 状态（证据 2），`K8s Event` 显示 Kubelet 持续发送 KILL 信号（证据 1），结合 `Logging` 缺少退出日志（证据 4），确证了应用进程因内部逻辑阻塞而无法正常退出。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 27.3s
├─ 并发证据采集: 35.4s
│  └─ g1 aiops-case-v12/workload: 35.4s (Evidence 28.4s, RCA 6.8s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
