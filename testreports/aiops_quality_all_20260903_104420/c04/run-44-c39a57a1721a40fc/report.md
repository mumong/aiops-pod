## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod workload-6584f97c76-wvcb2 持续处于 Pending 状态，Container app 处于 Waiting 状态，Reason 为 CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.app` waiting reason: `CreateContainerConfigError` (fact-0bafe27c7037) | 确诊容器配置阶段失败，属于启动前错误 |
| 2 | K8s State | kubernetes | `container.app` waiting message: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (fact-0bafe27c7037) | 明确缺失资源标识，直接指向 Secret 配置错误 |
| 3 | K8s State | kubernetes | Pod `phase`: `Pending` (fact-53824a9c5119) | 状态未推进至 Running，与配置校验失败的机制一致 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"}` = 1 (fact-b8c1ff19cd68) | 独立数据源佐证等待原因为配置错误 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total` = 0 (fact-23d241a295c0) | 确认从未启动成功，非运行时反复崩溃 |

Kubernetes 事件明确指出了 `CreateContainerConfigError` 的具体成因（Secret key 不存在），Metric 指标从集群维度验证了容器一直停留在等待状态且未发生过重启，两者互证。

## 🎯 根因分析 · g1

### 因果链

```text
Secret workload-input 缺少 key 'unavailable-key' → kubelet 解析 Pod spec 时校验失败 → 容器配置阶段直接返回 CreateContainerConfigError → Pod 持续 Pending 且 app 容器处于 Waiting 状态
```

### 根因结论

**已确认根因**：Pod 环境变量配置了无效的 Secret 引用。
具体而言，Pod `workload-6584f97c76-wvcb2` 尝试从 Secret `aiops-case-04/workload-input` 中获取 `unavailable-key`，但该 Secret 中实际仅包含 `available-key`。由于该引用未设置 `optional: true`，kubelet 在启动容器前进行配置校验时直接报错，导致容器无法创建。证据编号：1, 2, 4。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 19.3s
├─ 并发证据采集: 66.6s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 66.6s (Evidence 57.2s, RCA 9.3s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
