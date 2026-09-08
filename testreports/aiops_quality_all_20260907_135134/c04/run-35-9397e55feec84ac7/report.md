## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (fact-f8ee1f2acbdb) | 直接指向 Secret 中缺失的 key，提供故障原因 |
| 2 | K8s Config | kubernetes | `container.resource_limit.memory` = `32Mi`, `container.resource_limit.cpu` = `50m` (fact-263d75b4c003, fact-2b4bcdd43511) | 确认资源限制配置，排除因资源超限导致的启动失败 |
| 3 | K8s State | kubernetes | `pod.status` = `Pending` (fact-a37b2232a122) | 描述 Pod 当前的最终停滞状态，与创建失败一致 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = `1` (Reason: `CreateContainerConfigError`, fact-a65421f009d6) | 提供 Prometheus 侧的等待原因指标，印证 Event 中的失败类型 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total` = `0` (fact-1fb9d9673ea8) | 表明容器从未成功启动过，属于一次性配置错误 |

K8s Event 明确指出了由于 Secret 中缺少 key 导致挂载失败，Metric 指标 `CreateContainerConfigError` 与 Event 中的错误信息形成了直接印证。资源配置正常且重启次数为 0，进一步排除了运行时资源不足或容器启动后又崩溃的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 引用不存在的 Secret key → kubelet 无法挂载容器卷 → 容器创建失败 → Pod 状态进入 CreateContainerConfigError
```

### 根因结论

已确认的根因为：**Pod spec 引用的 Secret `aiops-case-04/workload-input` 中缺少 key `unavailable-key`**。

该根因由以下事实支撑：
1. Kubernetes 事件明确指出找不到该 Secret Key (证据 1)。
2. 指标显示容器处于 `CreateContainerConfigError` 等待状态 (证据 4)。
3. 容器重启次数为 0 (证据 5)，说明故障发生在容器启动前的配置挂载阶段，排除了应用运行时的随机错误。

---

## 📊 性能统计

```text
├─ 总耗时: 9.5m
├─ 问题定位: 14.3s
├─ 并发证据采集: 547.0s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 547.0s (Evidence 540.7s, RCA 6.3s)
└─ 汇总总结: 8.3s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
