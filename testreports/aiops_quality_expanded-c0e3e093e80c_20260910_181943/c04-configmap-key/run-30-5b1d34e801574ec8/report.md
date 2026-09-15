## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod 配置中引用了 ConfigMap 'aiops-case-v11/workload-input' 中不存在的 Key 'unavailable-key'，导致 kubelet 在创建容器时因配置加载失败而持续抛出 CreateContainerConfigError。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` | Pod `aiops-case-v11/workload` 状态为 `Pending` | 确认故障表现：Pod 无法进入运行状态 |
| 2 | K8s Config | `kubernetes` | 容器 `app` 请求 `cpu: 5m, memory: 8Mi`；限制 `cpu: 50m, memory: 32Mi` | 排除资源配额不足导致的调度失败 |
| 3 | K8s Event | `kubernetes` | `Failed` 事件：`Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 直接证据：ConfigMap 引用缺失，明确指向根因 |
| 4 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"}` = 1 (样本量 1) | 独立印证：监控指标证实容器因配置错误处于等待状态 |
| 5 | Metric | `prometheus` | `kube_pod_container_status_restarts_total` = 0 | 辅助观测：Pod 处于 Pending 阶段，未产生重启行为 |

**证据分析**：
K8s 事件（证据 3）与 K8s 状态（证据 1）、Metric 等待原因（证据 4）形成了闭环印证：ConfigMap 缺失 Key 导致 `CreateContainerConfigError`，致使 Pod 持续处于 `Pending` 状态且未产生重启。资源配置（证据 2）证实非资源限制问题，日志与追踪数据因容器未启动而不可用，符合预期。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用了不存在的 ConfigMap Key 'unavailable-key' → kubelet 初始化容器时配置加载失败 (CreateContainerConfigError) → Pod 持续处于 Pending 状态且无法运行
```

### 根因结论

已确认根因为 **Pod 配置错误**：Pod 模板中引用了 ConfigMap `aiops-case-v11/workload-input` 中不存在的 Key `unavailable-key`。
- **证据支持**：
    - K8s Event 明确报告了 `Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input`（证据 3）。
    - Metric 确认容器因 `CreateContainerConfigError` 处于等待状态，排除了应用启动慢或调度超时等其他故障（证据 4）。

---

## 📊 性能统计

```text
├─ 总耗时: 51.4s
├─ 问题定位: 18.3s
├─ 并发证据采集: 24.6s
│  └─ g1 aiops-case-v11/workload: 24.6s (Evidence 19.4s, RCA 5.1s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
