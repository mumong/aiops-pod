## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod workload-6584f97c76-h4lt9 处于 CreateContainerConfigError 状态，处于 Pending 阶段，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.phase`: `Pending` | 确认 Pod 未进入运行状态 |
| 2 | K8s State | kubernetes | `container.waiting_reason`: `CreateContainerConfigError` (app) | 定位具体失败阶段：容器配置失败 |
| 3 | K8s Config | kubernetes | `container.waiting_message`: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接指出引用 Secret 的 key 缺失 |
| 4 | K8s Event | kubernetes | `Event.message`: `Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 提供官方 Event 时间线及来源佐证 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason`: `1` (labels: `reason=CreateContainerConfigError`) | 指标层面确认处于配置错误等待态 |

**证据分析**：
Kubernetes 事件（#4）与容器状态消息（#3）完全一致，共同锁定了“无法找到 `unavailable-key`”这一具体错误。Metric 数据（#5）确认了该状态在监控系统中的持续存在，与 K8s 状态（#2）相互印证，排除了瞬时抖动可能。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 错误引用 Secret `aiops-case-04/workload-input` 中不存在的 key `unavailable-key` → 挂载 Secret 配置失败 → 容器启动配置拒绝 (CreateContainerConfigError) → Pod 处于 Pending 状态
```

### 根因结论

**已确认的根因**：
Pod 在定义中引用了 Secret `aiops-case-04/workload-input` 的密钥 `unavailable-key`，但该密钥在 Secret 中不存在（事实 #3, #4）。这直接触发了 Kubernetes 的 `CreateContainerConfigError`，导致 Pod 无法启动。

**证据编号**：
- [3] `container.waiting_message`: 明确指出了缺失的 key 和 Secret 名称。
- [4] `Event.message`: 提供了权威的系统级事件日志支持。
- [1] `pod.phase` / [2] `container.waiting_reason`: 确认了故障最终呈现为 Pod 处于等待配置错误的 Pending 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 27.9s
├─ 并发证据采集: 44.4s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 44.4s (Evidence 37.2s, RCA 7.1s)
└─ 汇总总结: 8.3s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
