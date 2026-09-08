## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod `aiops-case-04/workload-6584f97c76-wvcb2` 处于 `CreateContainerConfigError` 状态，容器 `app` 无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: "CreateContainerConfigError" (fact-8d9ad9c60625) | 直接确认容器启动前的配置错误状态 |
| 2 | K8s State | Kubernetes | `container.waiting_message`: "couldn't find key unavailable-key in Secret aiops-case-04/workload-input" (fact-bc8646b9d91b) | 精准定位导致错误的缺失资源标识 |
| 3 | K8s State | Kubernetes | `pod.phase`: "Pending", `pod.condition.ContainersReady`: "False" (fact-1dba66477271, fact-16b1a41e71bc) | 验证 Pod 整体处于不可用且未就绪状态 |
| 4 | K8s Event | Kubernetes | `event.message`: "Container image ... already present on machine" (fact-2308cbea928e) | 排除镜像拉取失败，确认为配置阶段阻断 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"}`: 1 (fact-22f8fbcae01f) | 量化证实集群中该等待原因的存在 |

**证据关联说明：**
Kubernetes 状态与事件 (Fact 1-3, 5) 直接揭示了 `CreateContainerConfigError` 的本质，并通过等待消息 (Fact 2) 锁定到具体缺失的 Secret 键 `unavailable-key`；Metric 数据 (Fact 5) 独立验证了该特定错误指标的状态，排除了临时波动可能，与 K8s 状态形成闭环。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 模板引用了不存在的 Secret 键 'unavailable-key' → Kubelet 无法完成配置注入 → 触发 CreateContainerConfigError → Pod 持续处于 Pending/Unready 状态
```

### 根因结论

已确认根因为 **Pod 配置错误引用了不存在的 Secret 键**。根据事实 `fact-bc8646b9d91b`，容器 `app` 在启动阶段被阻塞，报错明确指出在 `aiops-case-04/workload-input` 这个 Secret 中找不到键 `unavailable-key`。Kubernetes 事件 `fact-2308cbea928e` 确认镜像拉取正常，Metric `fact-22f8fbcae01f` 同步确认了该类型的等待状态。虽然 Logging 和 Tracing 维度因容器未启动而不可用，但 K8s 核心状态已提供足够证据确认配置层面的故障。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 38.7s
├─ 并发证据采集: 61.4s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 61.4s (Evidence 53.1s, RCA 8.1s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
