## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-7ds5p 处于 CreateContainerConfigError，无法启动容器。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Failed ... kubelet Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (fact-295efbf52a69) | 直接证明容器启动失败的精确原因：Secret 键缺失 |
| 2 | K8s State | kubernetes | 容器 `app` 处于 `CreateContainerConfigError`，等待消息为 `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (fact-d311571ff1c4, fact-dcf89dae2839) | 确认 Pod 处于因配置错误导致的挂起状态 |
| 3 | K8s State | kubernetes | Pod 状态为 `Pending`，`ContainersReady/Ready` 为 `False`，重启次数为 0 (fact-8edc0e296f92, fact-974664054bd9, fact-4608c8d3ebc2) | 证实故障发生在容器创建阶段，非运行时崩溃 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 中 `CreateContainerConfigError` 值为 1 (fact-7a9523e6c6f7) | 独立监控指标确认了 Pod 处于配置错误等待状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total` 值为 0 (fact-de67b5d24e79) | 排除由健康检查失败或 OOM 引起的重启可能 |
| 6 | K8s State | kubernetes | Pod 处于 `aiops-case-04` 命名空间，关联 CNI 地址 `172.16.104.61` (fact-053793c0254a, fact-0e618fa31ca7) | 提供故障实体的基础网络与命名空间上下文 |

**证据关联与印证：**
Kubernetes 事件 (fact-295efbf52a69) 与容器状态消息 (fact-dcf89dae2839) 高度一致，共同指向 `Secret aiops-case-04/workload-input` 中键 `unavailable-key` 缺失。Metric 指标 (fact-7a9523e6c6f7) 从监控视角独立验证了该 Pod 处于 `CreateContainerConfigError` 状态，且重启计数 (fact-de67b5d24e79) 为 0，进一步排除了运行时故障可能。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 'aiops-case-04/workload-input' 数据定义不完整（缺失 'unavailable-key'） → 容器挂载卷配置请求注入不存在的键 → Kubelet 拉取/解析 Secret 失败 → 触发 CreateContainerConfigError 错误并持续处于 Pending 状态
```

### 根因结论

**已确认的根因：**
Pod `aiops-case-04/workload-6584f97c76-7ds5p` 的配置中引用了 Secret `workload-input` 中的 `unavailable-key`，但该键在 Secret 中实际不存在（真实存在的键为 `available-key`，根据事实暗示及错误原文）。这一配置错误导致 Kubelet 在尝试挂载卷时无法找到所需键，从而直接触发 `CreateContainerConfigError` 阻止容器启动。证据包括明确的 `K8s Event` (fact-295efbf52a69)、`K8s State` (fact-dcf89dae2839) 以及 `Metric` (fact-7a9523e6c6f7) 三者之间的相互印证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 20.0s
├─ 并发证据采集: 60.7s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 60.7s (Evidence 53.1s, RCA 7.4s)
└─ 汇总总结: 12.8s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
