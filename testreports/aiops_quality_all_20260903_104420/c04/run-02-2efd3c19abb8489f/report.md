## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-wvcb2 持续处于 CreateContainerConfigError 状态，容器未启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning  Failed ... kubelet Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接指向容器启动失败的错误机制，确认为 Secret 键缺失 |
| 2 | K8s State | Kubernetes | `container.waiting_message: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 与 Event 信息一致，提供具体的缺失字段名称 |
| 3 | K8s State | Kubernetes | `container.waiting_reason: CreateContainerConfigError` | 定义当前容器的确切失败状态 |
| 4 | K8s Config | Kubernetes | `container.resource_limit.cpu: 50m` | 辅助上下文，排除资源限制导致启动失败的可能性 |
| 5 | K8s State | Kubernetes | `pod.phase: Pending`, `ContainersReady: False` | 确认 Pod 整体处于等待配置就绪状态，应用未进入运行阶段 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (reason: CreateContainerConfigError, value: 1) | 从监控层独立验证了容器处于配置错误的等待状态 |

**证据说明：**
Kubernetes 的 Event、Container State 以及 Prometheus 的 Waiting Reason 指标均明确指向同一个结论：容器因配置错误（CreateContainerConfigError）而无法启动。Kubernetes 的具体报错信息准确指出了缺失的 Secret Key 为 'unavailable-key'。由于容器始终处于 Waiting 状态，Logging 和 Tracing 维度无数据生成（not_applicable），但这并不影响基于 K8s 原生状态和事件的诊断确定性。

## 🎯 根因分析 · g1

```text
Deployment 模板引用了 Secret workload-input 中不存在的 key 'unavailable-key' → kubelet 在创建容器时无法解析该环境变量配置 → Kubernetes 拒绝启动容器并返回 CreateContainerConfigError → Pod 持续处于 Pending/Waiting 状态，应用不可用
```

### 根因结论

**已确认的根因**：
异常组 `g1` 的根因是 `aiops-case-04/workload-6584f97c76-wvcb2` Pod 的部署配置（Deployment）中，环境变量引用了 Secret `aiops-case-04/workload-input` 中不存在的键 `unavailable-key`。

**证据支撑**：
*   **直接证据**：Kubernetes 的 `event.message` (fact-701ffc39c588) 和 `container.waiting_message` (fact-1488920e56a0) 均一致报错 `Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input`。
*   **状态印证**：`container.waiting_reason` (fact-80b0b483ac22) 为 `CreateContainerConfigError`，且 `kube_pod_container_status_waiting_reason` (fact-189ba8824469) 指标确认了该状态。
*   **结论**：配置层面的 Secret 键名不匹配直接导致了容器配置的加载失败，这是造成 Pod 无法启动的唯一确定性原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 16.6s
├─ 并发证据采集: 78.3s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 78.3s (Evidence 69.5s, RCA 8.6s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
