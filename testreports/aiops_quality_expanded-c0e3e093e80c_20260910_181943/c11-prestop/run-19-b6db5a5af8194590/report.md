## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | deletionTimestamp 设置在当前时间之后 (2026-09-14T06:26:20Z)，Pod 处于预删除调度阶段，尚未进入实际的 Terminating 生命周期。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | pod.phase: Running | 确认 Pod 核心状态仍在运行，未发生实际崩溃 |
| 2 | K8s State | Kubernetes | pod.condition (Ready/Initialized): True | 确认容器就绪且正常运行，非资源不足或拉取失败 |
| 3 | K8s State | Kubernetes | deletionTimestamp: 2026-09-14T06:26:20Z | 存在未来的删除时间戳，是触发当前“预删除”状态的直接原因 |
| 4 | K8s Config | Kubernetes | resource_request/limit: CPU 5m/50m, Memory 8Mi/32Mi | 配置资源门槛极低，排除因资源超卖导致的调度卡死 |
| 5 | Logging | Elasticsearch | "application started" (2026-09-14T05:21:26.902Z) | 验证业务应用已按预期启动 |

**证据印证**：Kubernetes 状态事实 (1, 2, 4) 结合日志事实 (5) 证明应用运行完全正常，且未被 OOM 或 CPU 限制；唯一异常点是存在一个未来的 `deletionTimestamp` (3)，将 Pod 强行拉入“终止中”队列，导致 Pod 表现为 Terminating 状态但实际进程未终止。

## 🎯 根因分析 · g1

### 因果链

```text
deletionTimestamp 被设置为未来时间 → API Server 预调度删除流程 → Pod 进入 Terminating 状态但进程保持运行 → 用户/集群观察到 Pod 处于 Terminating 阶段
```

### 根因结论

已确认根因为 **Pod 被注入了未来的 `deletionTimestamp`，导致其处于“预删除”的挂起状态**（证据编号：3）。
该机制使得 Pod 尚未真正执行终止流程（证据编号：1），且当前应用启动及资源状态均正常（证据编号：2, 4, 5），排除了节点故障、资源不足或应用崩溃等传统终止失败原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 16.0s
├─ 并发证据采集: 46.5s
│  └─ g1 aiops-case-v12/workload: 46.5s (Evidence 41.6s, RCA 4.9s)
└─ 汇总总结: 7.2s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
