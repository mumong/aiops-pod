## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod workload-6584f97c76-h4lt9 持续处于 Pending 状态，容器启动失败并报错 CreateContainerConfigError。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `Waiting Reason: CreateContainerConfigError`, `Phase: Pending` (fact-25c78783e2c7, fact-d34ee2cb431c) | 确认容器无法启动的具体 K8s 状态，表明故障发生在容器创建阶段 |
| 2 | K8s Event | Kubernetes | `Failed` event: `Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (fact-2acba30cd19b) | 明确指出了配置引用的缺失键名及所属 Secret，直接指向根因 |
| 3 | K8s Config | Kubernetes | `container.waiting_message`: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (fact-0dd09df94cfc) | 提供了具体的错误上下文，确认了 Pod Spec 配置与现有 Secret 数据的不匹配 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError", container="app"} = 1` (fact-76a83b548304) | 独立观测证实了容器处于配置错误的 Waiting 状态，与 K8s 状态一致 |

**证据总结：**
Kubernetes 事件与容器状态报告了相同的 `CreateContainerConfigError` 错误，并明确指出了缺失的密钥 `unavailable-key`。Prometheus 指标独立验证了该 Pod 当前处于因配置错误而等待的状态。所有事实一致指向 Secret 配置缺失导致的启动失败。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用了不存在的 Secret Key 'unavailable-key' → kubelet 容器创建阶段加载配置失败 → 容器状态变更为 Pending (CreateContainerConfigError) → Pod 持续无法运行
```

### 根因结论

**已确认的根因**：Pod `aiops-case-04/workload-6584f97c76-h4lt9` 的容器配置中引用了 Secret `aiops-case-04/workload-input` 中的 key `unavailable-key`，但该 Secret 中实际不包含此 key，导致 kubelet 无法注入配置，容器启动失败并维持在 `CreateContainerConfigError` 状态。

**依据**：
*   **证据 2 & 3**：K8s 事件和容器等待消息直接指出了 `couldn't find key unavailable-key in Secret aiops-case-04/workload-input`。
*   **证据 1 & 4**：K8s 状态和 Metric 指标证实了故障表现为配置错误导致的启动失败。

**未知因素**：
*   输入提示 Secret `workload-input` 实际包含的唯一 key 是什么（需确认是否为拼写错误），但这不影响当前故障的直接判定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 20.0s
├─ 并发证据采集: 51.0s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 51.0s (Evidence 42.2s, RCA 8.7s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
