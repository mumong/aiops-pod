## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod aiops-case-v11/workload 中容器 app 引用的 ConfigMap aiops-case-v11/workload-input 中缺失 key 'unavailable-key'，导致 kubelet 无法挂载配置并持续抛出 CreateContainerConfigError。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `failed (x12 over 35m)` | `Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 确凿的上游原因证据，指出 ConfigMap 缺少必需键 `unavailable-key` |
| 2 | K8s State | `kubelet` | `container.waiting_reason: CreateContainerConfigError` | 确认直接失败机制，由于配置挂载失败导致容器无法创建 |
| 3 | K8s State | `Pod aiops-case-v11/workload` | `pod.phase: Pending`；`Ready: False (ContainersNotReady)` | 确认可见的用户现象，Pod 处于不可用状态且无重启 (restart_count: 0) |
| 4 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason=1` (labels: `reason: CreateContainerConfigError`) | 独立观测印证了 Kubernetes 状态的等待原因与配置缺失直接相关 |

**证据说明**：Kubernetes 事件（#1）明确指出了失败的根因（ConfigMap key 缺失），并直接触发了 #2 中的 `CreateContainerConfigError`。Prometheus 指标（#4）提供了独立的度量证据，其等待原因与 #2 的容器状态完全吻合。由于容器从未成功启动，Logging 与 Tracing 维度无业务日志产出，属正常现象，不构成证据缺失。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap aiops-case-v11/workload-input 缺失 key 'unavailable-key' → kubelet 挂载配置失败 → 容器创建抛出 CreateContainerConfigError → Pod 持续处于 Pending / ContainersNotReady 状态
```

### 根因结论

已确认根因：**Pod 声明引用的 ConfigMap `aiops-case-v11/workload-input` 中缺少键 `unavailable-key`**。

该缺失导致 kubelet 在挂载容器配置阶段受阻（证据 #1），从而抛出 `CreateContainerConfigError` 终止容器启动（证据 #2），最终表现为 Pod 长时间处于 `Pending` 且 `ContainersNotReady`（证据 #3、#4）。现有 Kubernetes 事实、事件与 Metrics 证据链闭合且互相印证。

---

## 📊 性能统计

```text
├─ 总耗时: 57.7s
├─ 问题定位: 12.7s
├─ 并发证据采集: 37.2s
│  └─ g1 aiops-case-v11/workload: 37.2s (Evidence 28.0s, RCA 9.1s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
