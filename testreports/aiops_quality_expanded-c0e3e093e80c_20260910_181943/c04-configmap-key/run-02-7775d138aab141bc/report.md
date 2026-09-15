## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod aiops-case-v11/workload 的容器 spec 中配置了引用不存在 ConfigMap Key 的环境变量 (configMapKeyRef to 'unavailable-key' in 'workload-input')，导致 kubelet 无法完成容器配置并进入 CreateContainerConfigError 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: reason="CreateContainerConfigError", container="app" | 直接指示容器因配置问题被 kubelet 拒绝启动 |
| 2 | K8s Event | kubernetes | `event.message`: "Warning Failed kubelet Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input" | 明确故障定位到具体的 ConfigMap 缺失键 |
| 3 | K8s State | kubernetes | `container.waiting_message`: "couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input" | 确认等待原因及缺失的具体资源标识 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason`: 1 (reason="CreateContainerConfigError") | 独立观测到 Pod 处于等待配置的指标状态 |

**证据关联说明：**
Kubernetes 事件 (`#2`) 与容器等待原因 (`#1`, `#3`) 均指向同一确定性错误：Pod `aiops-case-v11/workload` 尝试挂载 ConfigMap `workload-input` 中的 `unavailable-key`，但因该键不存在，kubelet 无法完成容器配置。Metric 结果 (`#4`) 进一步佐证了该 Pod 正停留在 `CreateContainerConfigError` 状态，未发生实际运行或重启（重启计数为 0）。由于容器未成功启动，未产生任何 Logging 或 Tracing 数据。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 配置错误 (引用不存在的 ConfigMap Key) → 容器配置初始化失败 → CreateContainerConfigError → Pod 状态持续 Pending，应用无法启动
```

### 根因结论

**已确认的根因**：Pod `aiops-case-v11/workload` 的容器配置中存在对不存在 ConfigMap 键的引用。

根据输入事实，容器 `app` 配置了 `configMapKeyRef` 引用 ConfigMap `workload-input` 中的 `unavailable-key`。由于该键在目标 ConfigMap 中实际不存在，kubelet 在启动容器前执行配置校验时失败，导致容器处于 `CreateContainerConfigError` 状态（见事实 `fact-6a5b3cebf973`, `fact-a73c48f3bdfa`, `fact-ca7a203fa8a0`）。这一底层机制直接导致了 Pod 无法进入 Running 状态（见事实 `fact-a3e185a9a467`, `fact-d3a88e84c8fa`）及对应等待指标上升（见事实 `fact-2b148c52243a`）。现有证据链完整，无需补充其他维度事实即可锁定根因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 18.0s
├─ 并发证据采集: 35.5s
│  └─ g1 aiops-case-v11/workload: 35.5s (Evidence 30.2s, RCA 5.1s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
