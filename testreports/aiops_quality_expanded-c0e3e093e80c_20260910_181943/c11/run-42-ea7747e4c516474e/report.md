## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload stuck in Terminating state for >1h, deletionTimestamp present but not cleaned up. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.phase`: Running | 确认 Pod 对象仍存在于集群中，且未进入 Succeeded/Failed 状态。 |
| 2 | K8s State | Kubernetes | `pod.condition`: Ready=False (`ContainersNotReady`); phase=Running | 确认应用容器处于非就绪状态，验证了对象未被正确终止。 |
| 3 | K8s State | Kubernetes | `container.last_exit_code`: 137; `last_terminated_reason`: Error | 证明应用已非正常退出（被杀），说明问题不在应用自身，而在集群层面的清理流程。 |
| 4 | K8s State | Kubernetes | `container.restart_count`: 0 | 排除因重启循环导致的状态卡死，确认是单次退出后未被回收。 |
| 5 | K8s Config | Kubernetes | `container.resource_limit.memory`: 96Mi | 提供上下文：内存限制较低（96Mi），结合 exit code 137，暗示应用因内存触发 OOM Kill。 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 0 | 侧面印证重启次数为 0 的 K8s 状态数据，排除了周期性崩溃重启。 |

Kubernetes 状态数据与 Metrics 共同证实：应用已因资源问题（Exit 137）停止，但由于无法释放资源或状态机阻塞，导致 Pod 未能完成生命周期清理。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 包含自定义 finalizer 'aiops.lab/hold' → 控制器未成功释放该 finalizer → Kubernetes Garbage Collector 阻塞删除 → 用户可见 Pod 卡在 Terminating (Running Phase) 状态
```

### 根因结论

**已确认根因：** Kubernetes 删除流程被 `aiops.lab/hold` 自定义 finalizer 阻塞。

**分析依据：**
1. **现象确认**：Pod 处于 Terminating 状态且已逾 1 小时（输入描述），但 `pod.phase` 仍为 Running，`restart_count` 为 0，且 `exit_code` 为 137。这表明应用已死，但对象未从 API Server 移除。
2. **直接原因**：`formal_rca` 明确指出 Pod 元数据中存在 `aiops.lab/hold` finalizer，且已知触发机制为“Kubernetes 等待控制器移除该字段”。
3. **辅助证据**：内存限制 `96Mi` 与 Exit Code 137 高度吻合，推测应用可能因 OOM 被杀后，关联的控制器未能正确响应（例如控制器自身也未就绪或逻辑缺陷），从而导致未能移除 finalizer。

**缺失/未知项：**
当前事实链中明确缺失“持有该 finalizer 的具体控制器身份”及其“未释放 finalizer 的具体原因”，需进一步排查该 custom finalizer 对应的 Controller 日志或 Topology。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 17.2s
├─ 并发证据采集: 33.3s
│  └─ g1 aiops-case-11/workload: 33.3s (Evidence 26.2s, RCA 7.0s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
