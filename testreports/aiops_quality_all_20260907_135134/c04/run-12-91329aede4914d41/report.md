## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod spec中引用的Secret密钥名称'unavailable-key'在Secret 'aiops-case-04/workload-input'中不存在（实际密钥为'available-key'），导致kubelet无法挂载配置并创建容器。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Failed ... kubelet ... Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接指出缺失密钥，支撑根因结论 |
| 2 | K8s State | Kubernetes | `container.waiting_reason: CreateContainerConfigError` | 确认因配置错误导致容器卡在等待状态 |
| 3 | K8s State | Kubernetes | `container.waiting_message: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 提供具体的缺失键名称，与 Event 互相印证 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"} = 1` | 从指标层面确认容器处于该异常等待状态 |
| 5 | K8s State | Kubernetes | `pod.status: Pending` | 确认 Pod 整体处于挂起状态，未进入运行阶段 |

证据链清晰：`Pending` 状态和 `CreateContainerConfigError` 指标（#4, #5）一致；K8s 事件（#1）和容器状态消息（#3）明确指向 `Secret` 密钥缺失。日志/追踪不可用（容器未启动），但 K8s 层面证据已充分闭环。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 引用的 Secret 键名不存在 → kubelet 无法挂载配置 → 容器处于 CreateContainerConfigError 状态 → Pod 卡在 Pending 状态
```

### 根因结论

已确认根因为 Pod 规格（Pod Spec）中引用了不存在的密钥。

具体而言，Pod 试图在 Secret `aiops-case-04/workload-input` 中查找名为 `unavailable-key` 的键，但该键在 Secret 中并不存在。这导致 kubelet 在挂载配置阶段失败，进而使容器无法启动并停留在 `CreateContainerConfigError` 状态（见证据 #1, #2, #3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 17.9s
├─ 并发证据采集: 39.8s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 39.8s (Evidence 33.6s, RCA 6.1s)
└─ 汇总总结: 7.1s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
