## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-wvcb2 的容器 spec 引用了 Secret aiops-case-04/workload-input 中不存在的 key 'unavailable-key'，导致 kubelet 无法注入配置，触发 CreateContainerConfigError 阻止容器启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning Failed ... Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接定位挂载失败的具体原因及缺失键名 |
| 2 | K8s State | Kubernetes | `container.waiting_message: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 辅助确认容器因配置注入失败而等待 |
| 3 | K8s State | Kubernetes | `container.waiting_reason: CreateContainerConfigError` | 明确失败阶段与根本机制 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"} = 1` | 独立验证容器处于配置错误等待状态 |
| 5 | K8s State | Kubernetes | `pod.phase: Pending` | 描述 Pod 当前处于等待调度完成的状态 |

**证据链印证说明**：
Kubernetes 事件 (1) 提供了故障的具体上下文（缺少 Secret Key），这直接解释了 K8s State (3) 中 `CreateContainerConfigError` 状态的来源。Metric (4) 从监控层独立确认了这一特定的等待原因，两者指向一致。由于容器未能成功启动，Logging 和 Tracing 维度缺失是物理限制，不影响上述判断。

## 🎯 根因分析 · g1

### 因果链

```text
Secret aiops-case-04/workload-input 中不存在 key 'unavailable-key' → kubelet 无法注入容器配置 → 容器状态转为 CreateContainerConfigError → Pod 停留在 Pending 状态
```

### 根因结论

已确认根因为 Pod `aiops-case-04/workload-6584f97c76-wvcb2` 的容器 spec 引用了不存在的 Secret 键 `unavailable-key`。Kubernetes 事件 (1, #1) 和容器状态信息 (2, #2) 共同证实了这一配置错误，导致 kubelet 在启动容器时因无法解析配置而直接抛出 `CreateContainerConfigError` 错误，从而阻塞了容器启动过程。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 17.6s
├─ 并发证据采集: 73.6s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 73.6s (Evidence 67.6s, RCA 5.7s)
└─ 汇总总结: 7.5s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
