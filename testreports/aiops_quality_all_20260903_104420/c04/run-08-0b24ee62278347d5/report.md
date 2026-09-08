## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod workload-6584f97c76-wvcb2 持续处于 Pending 状态，容器 app 处于 Waiting (CreateContainerConfigError)。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_message`: "couldn't find key unavailable-key in Secret aiops-case-04/workload-input" (fact-3b49c1a8b3ae) | 确认容器启动阻塞的直接原因：引用了不存在的 Secret key |
| 2 | K8s Config | kubernetes | `container.resource_limit.cpu`: "50m", `resource_request.memory`: "8Mi", `resource_limit.memory`: "32Mi" (fact-08d326e5b891, fact-138aef3d381d, fact-41fb4e206672) | 确认资源请求和限制，资源值本身合理，排除资源不足导致的配置失败 |
| 3 | K8s Event | kubernetes | `Warning  Failed`: "Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input" (fact-7a08e03c2514, fact-9b9d404bdf57) | kubelet 明确报错，指出具体缺失的 key 和 Secret 名称，确认错误根源 |
| 4 | K8s State | kubernetes | `pod.status`: "Pending", `pod.condition.ContainersReady`: "False" (fact-6c68ad98995d, fact-3ef1937985c9) | 确认 Pod 整体处于 Pending 状态，容器无法就绪 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (app, CreateContainerConfigError): 1 (fact-024979015fa3) | 指标层面确认容器处于 `CreateContainerConfigError` 等待状态 |

**证据总结：**
K8s 事件和容器等待消息直接且明确地指出了错误原因：Pod 配置中的环境变量引用了 Secret `aiops-case-04/workload-input` 中不存在的 `unavailable-key`，且未设置为 `optional`。这与 Prometheus 指标显示的 `CreateContainerConfigError` 状态完全一致。

## 🎯 根因分析 · g1

### 因果链
```text
Secret aiops-case-04/workload-input 中缺少 key unavailable-key → Pod 环境变量引用了不存在的 key 且非可选 → kubelet 获取 Secret 数据失败，拒绝创建容器 → Pod 持续 Pending 并报错 CreateContainerConfigError
```

### 根因结论
已确认根因为 **Pod 环境变量引用了不存在的 Secret key**。
具体来说，Pod `aiops-case-04/workload-6584f97c76-wvcb2` 的容器 `app` 配置中引用了 Secret `workload-input` 中的 `unavailable-key`，但该 key 在 Secret 中不存在（事实 #1, #3）。由于该引用未设置为 `optional=true`，kubelet 在启动容器时无法获取该键值，导致容器配置失败，Pod 一直处于 Pending 状态（事实 #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 23.6s
├─ 并发证据采集: 62.4s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 62.4s (Evidence 54.3s, RCA 7.8s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
