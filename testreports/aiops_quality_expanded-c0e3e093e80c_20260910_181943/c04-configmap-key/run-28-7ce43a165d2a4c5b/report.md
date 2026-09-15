## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod aiops-case-v11/workload 持续处于 Pending 状态，容器 app 报 CreateContainerConfigError 无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubernetes` (fact-70c7dd428576) | `Warning Failed 46m (x12 over 48m) kubelet Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 确认为 kubelet 校验失败，直接归因为配置引用缺失 |
| 2 | Metric | `prometheus` (fact-54930c094d8d) | `kube_pod_container_status_waiting_reason{container="app", reason="CreateContainerConfigError"} = 1` | 独立证实容器持续卡在配置加载阶段，状态与 Event 一致 |
| 3 | K8s Config | `kubernetes` (fact-07bed9314030) | `resource_limit.memory: 32Mi` | 确认容器资源限制，排除因资源超限导致的非配置类失败 |
| 4 | K8s State | `kubernetes` (fact-22c8b17b2f13) | `pod.status: Pending` | 证实 Pod 未进入 Running 状态，与配置报错机制吻合 |
| 5 | Metric | `prometheus` (fact-f5207b304661) | `kube_pod_container_status_restarts_total{container="app"} = 0` | 证实容器从未成功启动过，排除因容器崩溃重启导致的连锁故障 |

**证据关联说明：**
K8s Event (证据1) 明确指出了失败原因是 ConfigMap 中找不到 key 'unavailable-key'；Metric (证据2) 独立验证了该 Pod 处于 `CreateContainerConfigError` 状态。资源配置 (证据3) 和重启计数 (证据5) 进一步排除了其他可能性，锁定为配置挂载阶段的校验失败。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义引用了 ConfigMap aiops-case-v11/workload-input 中不存在的 key 'unavailable-key' → kubelet 启动前校验配置失败 → 容器启动被阻止，持续重试并报错 → Pod 长期处于 CreateContainerConfigError 状态
```

### 根因结论

已确认的根因是 **Pod 配置引用了 ConfigMap `aiops-case-v11/workload-input` 中不存在的 key `unavailable-key`**。

该配置错误导致 kubelet 在启动容器前发现配置引用错误（证据1），直接阻止了容器创建。Prometheus 监控数据（证据2）与 K8s 状态（证据4）一致证实了 Pod 长期处于 `CreateContainerConfigError` 等待状态，且从未成功启动（证据5），确认了根因的持续性和排他性。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 14.2s
├─ 并发证据采集: 41.8s
│  └─ g1 aiops-case-v11/workload: 41.8s (Evidence 32.7s, RCA 9.0s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
