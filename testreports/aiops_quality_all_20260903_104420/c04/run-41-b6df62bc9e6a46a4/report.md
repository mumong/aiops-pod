## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod workload-6584f97c76-wvcb2 处于 CreateContainerConfigError 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: app 处于 CreateContainerConfigError | 确认直接失败机制 |
| 2 | K8s State | kubernetes | `container.waiting_message`: app 报错 couldn't find key unavailable-key in Secret aiops-case-04/workload-input | 提供决定性错误原文，定位缺失配置项 |
| 3 | K8s State | kubernetes | `pod.status`: Pending, `pod.condition`: ContainersReady/Ready 均为 False | 确认可见症状 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason`: app 对应 CreateContainerConfigError 值为 1 | 独立印证容器持续处于配置错误状态 |

证据表说明：Kubernetes 状态（#1, #2）直接指出了配置缺失的具体原因，Metric 数据（#4）从监控层面独立证实了该等待状态的持续存在，两者因果链条闭环，确凿排除了其他网络或资源类故障。

## 🎯 根因分析 · g1

### 因果链

```text
Secret aiops-case-04/workload-input 缺失 key 'unavailable-key' → Pod 模板引用该不存在的 Key 触发校验失败 → Kubelet 启动容器时抛出 CreateContainerConfigError → Pod 持续 Pending/Waiting 且未进入 Running
```

### 根因结论

已确认根因：Pod `workload-6584f97c76-wvcb2` 在构建容器环境时，引用了 Secret `aiops-case-04/workload-input` 中实际不存在的配置项 `unavailable-key`（证据 #2）。该缺失导致 Kubelet 在启动前验证环境变量失败，直接引发 `CreateContainerConfigError`（证据 #1, #4），致使 Pod 无法启动并卡在 Pending 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 19.3s
├─ 并发证据采集: 63.8s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 63.8s (Evidence 56.9s, RCA 6.7s)
└─ 汇总总结: 6.7s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
