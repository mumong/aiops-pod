## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | aiops-case-v11/workload 处于 CreateContainerConfigError，持续 30 分钟，未启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Warning Failed ... 28m (x12 over 30m) Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 直接证实容器启动配置错误，指出缺失的具体键名 |
| 2 | K8s State | Pod Status | `Pending` (Pod 处于等待状态) | 确认异常组核心现象，表明容器尚未启动成功 |
| 3 | Metric | PromQL | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"} = 1` | 定量佐证 K8s Event 中的警告，明确等待原因为配置错误 |
| 4 | K8s Config | Container Resources | `memory_request=8Mi`, `cpu_request=5m` (Context) | 排除资源限额引发的调度或启动限制，将排查聚焦于配置 |

证据间高度一致：Metric 的 `CreateContainerConfigError` 状态与 K8s Event 中关于 ConfigMap 缺失 key 的 Warning 形成闭环，共同指向配置缺陷。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap aiops-case-v11/workload-input 定义不完整（缺少 key unavailable-key） → kubelet 验证容器配置时发现缺失 key → 容器创建失败，Pod 进入 CreateContainerConfigError 状态 → 用户可见 Pod 处于 Pending 状态，未启动
```

### 根因结论

**已确认根因**：ConfigMap `aiops-case-v11/workload-input` 中缺少 Pod `workload` 容器配置所需的 key `unavailable-key`，导致 kubelet 在容器创建阶段拒绝启动。

*   证据编号 #1 和 #3 直接指出了缺失的键名及对应的错误类型。
*   证据编号 #4 排除了资源配置问题。

**待确认事项**：业务逻辑期望 ConfigMap 包含的具体 key 集合。目前无法确定是 ConfigMap 遗漏了该 key，还是 Pod 配置错误地请求了该 key。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 14.9s
├─ 并发证据采集: 65.1s
│  └─ g1 aiops-case-v11/workload: 65.1s (Evidence 56.2s, RCA 8.7s)
└─ 汇总总结: 7.2s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
