## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod工作负载模板中配置的Secret键名'unavailable-key'与Secret资源'workload-input'中实际存在的键名'available-key'不匹配 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_message`: "couldn't find key unavailable-key in Secret aiops-case-04/workload-input" | 确认容器启动失败的直接原因 |
| 2 | K8s State | Kubernetes | `container.waiting_reason`: "CreateContainerConfigError" | 确认资源挂载阶段失败而非启动后崩溃 |
| 3 | K8s Event | Kubernetes | `Warning Failed`: "Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input" | 确认 kubelet 在重试过程中持续失败 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (reason: CreateContainerConfigError): 1 | 独立于日志的监控确认当前异常状态 |
| 5 | K8s State | Kubernetes | `pod.phase`: "Pending"; `restart_count`: 0 | 确认容器因配置缺陷从未进入运行状态 |

**证据分析：**
Kubernetes 状态（#1, #2）与事件（#3）在维度上高度一致，明确指出是 `Secret` 中查找特定 key 失败导致容器无法启动。Prometheus 指标（#4）作为独立监控源，印证了当前异常类型与原因。Pod 始终处于 `Pending` 且重启次数为 0（#5），进一步排除了应用逻辑错误或运行期崩溃的可能性，将问题锁定在配置引用阶段。

## 🎯 根因分析 · g1

```text
Pod Spec 中引用的 Secret key 'unavailable-key' 不存在 → kubelet 无法挂载配置 → 容器启动流程在配置阶段被阻断 (CreateContainerConfigError) → Pod 持续 Pending
```

**根因结论：**
**已确认的根因**：Pod 工作负载模板中引用的 Secret 键名 `unavailable-key` 与 Secret 资源 `workload-input` 中实际存在的键名 `available-key` 不匹配 [证据 #1, #2]。
该配置错误导致容器启动时无法获取所需的环境变量或挂载数据，进而被 kubelet 阻断。
**补充说明**：现有证据未能明确该不匹配是源于代码/模板中的拼写错误，还是 Secret 资源被意外更新。需人工核对 Pod 定义模板与 Secret 资源当前的实际内容。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 20.0s
├─ 并发证据采集: 61.8s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 61.8s (Evidence 55.1s, RCA 6.6s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
