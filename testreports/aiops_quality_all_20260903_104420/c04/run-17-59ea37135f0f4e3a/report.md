## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-wvcb2 状态为 Pending，容器 app 处于 Waiting 状态，Reason=CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s Pod Spec | `container.waiting_reason`: CreateContainerConfigError | 确认容器启动失败的具体阶段与类型 |
| 2 | K8s Config | K8s Pod Spec | 引用了 Secret `workload-input` 中不存在的 key `unavailable-key` | 直接指向失败的根本配置错误 |
| 3 | K8s Event | Kubelet | `Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 记录 kubelet 拒绝启动容器的确切错误原文 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"}` 值为 1 | 确认集群侧监控到的等待原因为配置验证错误 |

Pod 当前处于 `Pending` 状态且 `restart_count` 为 0。由于容器启动前必须校验配置，容器尚未启动因此未能产生应用日志（Logging）和业务 Trace（Tracing），这与 Pod 的启动阶段完全吻合。上述 K8s 事件与配置声明共同锁定了故障点在 Secret Key 配置引用上。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 配置引用了不存在的 Secret Key (unavailable-key) → kubelet 启动容器前 Secret 验证失败 → 容器处于 Waiting 状态 (CreateContainerConfigError) → Pod 处于 Pending 状态
```

### 根因结论

**已确认的根因**：Pod `aiops-case-04/workload-6584f97c76-wvcb2` 的配置错误。
Pod 的容器配置中指定了使用 Secret `workload-input` 中的键 `unavailable-key`，但该 Secret 对象中实际并不包含该 Key（仅包含 `available-key`，作为对照事实）。

**证据支撑**：
- K8s Event 中 kubelet 报错原文：“`Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input`”
- K8s State 记录容器等待原因为：`CreateContainerConfigError`
- Metric 观测到对应状态为：`CreateContainerConfigError`

综上，容器无法启动的明确原因为引用了不存在的 Secret 键值。

---

## 📊 性能统计

```text
├─ 总耗时: 10.0m
├─ 问题定位: 22.0s
├─ 并发证据采集: 570.5s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 570.5s (Evidence 562.1s, RCA 8.2s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
