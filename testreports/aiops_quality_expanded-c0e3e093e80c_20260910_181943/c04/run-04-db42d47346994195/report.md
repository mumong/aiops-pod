## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod `workload-6584f97c76-h4lt9` 配置引用 Secret `workload-input` 中的 key `unavailable-key`，但该 Secret 实际缺失此 key（仅含 `available-key`），导致 kubelet 挂载失败并持续报错。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Failed ... kubelet Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 明确指出 kubelet 在挂载 Secret `workload-input` 时，找不到所需的 `unavailable-key` |
| 2 | K8s State | kubernetes | `container.waiting_reason`: `CreateContainerConfigError` | 确认容器因配置错误处于等待状态，无法进入 Running 阶段 |
| 3 | K8s State | kubernetes | `container.waiting_message`: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 提供与 Event 一致的配置错误详情，佐证配置缺失事实 |
| 4 | K8s State | kubernetes | `pod.phase`: `Pending` | 反映 Pod 始终处于调度后但未启动的挂起状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1` (labels: `reason="CreateContainerConfigError"`) | 独立确认集群中存在且仅存在一个因配置错误而挂起的容器实例 |

**证据关联说明：**
*   **相互印证**：事实 #1 (Event) 与 #3 (Waiting Message) 精确指出了导致容器启动失败的唯一原因：Secret 中缺失 `unavailable-key`。
*   **状态闭环**：事实 #2 和 #4 展示了该错误导致的系统状态结果（Pending / CreateContainerConfigError），且事实 #5 的监控指标独立确认了这一状态在全局范围内的单一性。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用了 Secret workload-input 中不存在的 key unavailable-key → kubelet 无法挂载 Secret 卷 → 容器启动失败 (CreateContainerConfigError) → Pod 处于 Pending 状态
```

### 根因结论

**已确认的根因：**
Pod `workload-6584f97c76-h4lt9` 的容器配置错误引用了 Secret `aiops-case-04/workload-input` 中的 key `unavailable-key`。实际 Secret 中不存在此 key（仅包含 `available-key`），导致 kubelet 在挂载卷时失败。

该配置错误直接导致容器无法启动，Pod 持续停留在 `Pending` 状态且重启次数为 0（无法进入生命周期）。监控数据 `CreateContainerConfigError` 进一步确证了该配置型错误的普遍性观测。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 34.4s
├─ 并发证据采集: 58.2s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 58.2s (Evidence 49.9s, RCA 8.1s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
