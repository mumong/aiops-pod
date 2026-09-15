## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod `aiops-case-v11/workload` 处于 Pending 状态，容器 `app` 处于 Waiting 状态，原因标记为 `CreateContainerConfigError`，且自创建以来未发生过重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s Event | `event.message: "Warning Failed... kubelet Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input"` | 确定根因：容器配置缺失导致启动失败 |
| 2 | K8s State | K8s State | `container.waiting_reason: "CreateContainerConfigError"` | 确认容器未启动的原因标记 |
| 3 | K8s Config | K8s Config | `container.resource_limit.memory: "32Mi", cpu: "50m"; resource_request.memory: "8Mi", cpu: "5m"` | 排除资源超卖导致调度失败的可能性 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason: 1` (Labels: `container=app, reason=CreateContainerConfigError`) | 辅助验证 Pod 持续处于 Waiting 状态 |
| 5 | K8s State | K8s State | `container.restart_count: 0`, `pod.phase: "Pending"` | 确认故障发生在初始化阶段，未经历重启循环 |

证据之间高度一致。K8s 事件日志明确指出了 ConfigMap 中缺少特定键（`unavailable-key`），该事实直接解释了为何容器状态标记为 `CreateContainerConfigError` 且未发生任何重启。Metrics 数据印证了这一状态持续存在，而资源配置信息证实了这不是由资源竞争引发的调度问题。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap `aiops-case-v11/workload-input` 中缺失键 `unavailable-key` → 容器配置校验失败 → 触发 `CreateContainerConfigError` 并持续处于 Waiting 状态 → Pod 卡在 Pending 状态无法进入 Running
```

### 根因结论

已确认的根因是：Pod 的容器配置引用了 ConfigMap `aiops-case-v11/workload-input` 中不存在的键 `unavailable-key`（证据 #1）。

这一缺失导致 Kubernetes 在初始化阶段无法获取所需配置数据，从而抛出 `CreateContainerConfigError` 异常并阻止容器启动（证据 #2）。由于故障发生在配置挂载阶段，因此容器重启计数为 0（证据 #5）。现有 K8s 状态与指标数据足以完整支撑该结论。

---

## 📊 性能统计

```text
├─ 总耗时: 58.4s
├─ 问题定位: 14.7s
├─ 并发证据采集: 35.7s
│  └─ g1 aiops-case-v11/workload: 35.7s (Evidence 26.5s, RCA 9.1s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
