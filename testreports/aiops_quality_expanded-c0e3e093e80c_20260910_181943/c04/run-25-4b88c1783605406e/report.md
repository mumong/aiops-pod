## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod workload-6584f97c76-h4lt9 的容器配置引用了 Secret 'aiops-case-04/workload-input' 中不存在的 key 'unavailable-key'。由于该必需配置项缺失，kubelet 无法完成容器环境初始化，导致 Pod 始终处于 CreateContainerConfigError 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` | Pod `aiops-case-04/workload-6584f97c76-h4lt9` 状态为 `Pending` | 确认 Pod 未能正常进入运行状态 |
| 2 | K8s Event | `kubernetes` | `Warning Failed ... Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接指出容器环境初始化失败的错误原因及缺失的 Key |
| 3 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason=1` (reason: `CreateContainerConfigError`) | 指标层面证实容器处于配置错误等待状态 |

上述 K8s Event 明确指出 Kubelet 无法在 Secret `aiops-case-04/workload-input` 中找到 key `unavailable-key`，Metric 数据通过 `CreateContainerConfigError` 状态对该失败进行了独立印证，确认该错误是阻止 Pod 启动的直接原因。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用了不存在的 Secret Key ('unavailable-key') → Kubelet 加载配置失败 → 容器启动被拒绝 → Pod 状态变为 CreateContainerConfigError
```

### 根因结论

**已确认的根因**：Pod `workload-6584f97c76-h4lt9` 的配置中引用了 Secret `aiops-case-04/workload-input` 中不存在的 Key `unavailable-key`。

根据事实 `fact-516c65140ae5` (K8s Event) 与 `fact-4aff169e8849` (Metric)，kubelet 因无法找到必需的配置项而主动拒绝初始化容器环境，导致 Pod 始终处于 `CreateContainerConfigError` 状态且未发生重启（`fact-1d0a327f6f81`）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 19.4s
├─ 并发证据采集: 41.7s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 41.7s (Evidence 32.4s, RCA 9.1s)
└─ 汇总总结: 6.9s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
