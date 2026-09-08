## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | aiops-case-04/workload-6584f97c76-wvcb2 处于 CreateContainerConfigError 状态，容器未能启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Failed Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (x12) | 直接指出 Secret Key 缺失的错误源 |
| 2 | K8s State | kubernetes | `Waiting: CreateContainerConfigError` (container: app) | 确认容器因配置错误处于等待状态 |
| 3 | K8s Config | kubernetes | `container.resource_request.memory: 8Mi` | 确认容器实际资源请求配置 |
| 4 | K8s Config | kubernetes | `container.resource_limit.memory: 32Mi` | 确认容器实际资源限制配置 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1` (`reason: CreateContainerConfigError`) | 验证等待原因为配置错误 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total=0` (container: app) | 证实从未成功启动，无重启循环 |

证据 1 与证据 2 强相关：Kubernetes Event 明确指出了导致 `CreateContainerConfigError` 的具体原因是找不到 Secret 中的指定 Key。证据 5 与证据 6 从 Prometheus 层面交叉验证了该状态：容器因同一错误处于等待状态，且由于配置挂载失败，容器自部署以来重启次数为 0，排除了因内存限制导致的 OOMKilled 等启动后崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用 Secret 中不存在的 key 'unavailable-key' 且 optional=false → 容器配置挂载失败 (CreateContainerConfigError) → Pod 处于 Pending/Waiting 状态，容器无法启动 → 用户可见容器处于错误状态且无重启
```

### 根因结论

**已确认根因：Pod 配置引用了不存在的 Secret Key。**

证据 1 指出 Pod Spec 试图挂载 `Secret aiops-case-04/workload-input` 中的 `unavailable-key`，但该 key 实际不存在于目标 Secret 中。由于该挂载配置未被标记为 `optional: true`，kubelet 拒绝启动容器，直接触发 `CreateContainerConfigError`（证据 2, 5）。这种配置层面的错误导致容器无法初始化，因此 Prometheus 数据显示重启次数始终为 0（证据 6）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 20.1s
├─ 并发证据采集: 72.7s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 72.6s (Evidence 64.0s, RCA 8.3s)
└─ 汇总总结: 8.3s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
