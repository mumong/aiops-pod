## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod spec 引用了 Secret aiops-case-04/workload-input 中不存在的 key 'unavailable-key'，导致 kubelet 无法挂载配置，触发 CreateContainerConfigError。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (fact-0730364d89ae) | 核心根因证据：明确指出 Secret Key 缺失导致挂载失败 |
| 2 | K8s State | Kubernetes | Pod 状态 `Pending` (fact-0fe6d606cb20) | 表现异常：Pod 处于无法调度/启动的状态 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 针对容器 `app` 的值为 `CreateContainerConfigError` (fact-dee5d8e2aebc) | 确认具体错误类型，与 K8s Event 中的挂载失败原因一致 |
| 4 | K8s Config | Kubernetes | 容器资源配置：Request CPU 5m, Memory 8Mi; Limit CPU 50m, Memory 32Mi (fact-1e5b13f8a11a, fact-29bea5d8c2a6, fact-4f77fc957fb4, fact-82d83c13f485) | 排除资源限制导致启动失败的可能性 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 值为 `0` (fact-43d59da179ca) | 佐证容器从未成功启动，与 Pending 状态一致 |

**证据说明：**
Kubernetes 事件（证据1）明确指出了 `Secret` 中缺失特定 key 是挂载失败的直接原因。Prometheus 监控指标（证据3）确认了容器处于 `CreateContainerConfigError` 状态，这与 K8s Event 的报错高度吻合。Pod 一直处于 `Pending` 状态且重启次数为 0（证据2、证据5），说明容器进程根本未启动，这排除了应用代码逻辑问题，确认为纯配置层面的启动前阻断。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用不存在的 Secret Key (aiops-case-04/workload-input/unavailable-key) → kubelet 无法挂载 Volume → CreateContainerConfigError → Pod 状态 Pending，应用不可用
```

### 根因结论

已确认根因为 **Pod 配置文件错误**。

Pod `aiops-case-04/workload-6584f97c76-wvcb2` 的 Spec 中引用了 Secret `aiops-case-04/workload-input` 中的 Key `unavailable-key`，但该 Key 在 Secret 中不存在（事实支撑见证据1）。这一配置错误导致 kubelet 在容器启动前的配置挂载阶段即告失败，直接引发 `CreateContainerConfigError`，致使 Pod 始终停留在 `Pending` 状态（事实支撑见证据2、证据3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 21.7s
├─ 并发证据采集: 50.2s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 50.2s (Evidence 44.3s, RCA 5.7s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
