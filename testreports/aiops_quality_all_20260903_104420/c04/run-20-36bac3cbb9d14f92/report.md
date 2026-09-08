## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-wvcb2 处于 CreateContainerConfigError 状态，容器无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubernetes` | `Warning Failed` 47m 内 x12：`Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接证明容器启动时的失败原因及具体缺失的键名 |
| 2 | K8s State | `kubernetes` | 容器 `app` 处于 `CreateContainerConfigError`，消息指向 Secret `aiops-case-04/workload-input` 中的 `unavailable-key` 缺失 | 确认当前异常的终止状态 |
| 3 | K8s Config | `kubernetes` | 容器 `app` 资源配置：请求 8Mi/5m，限制 32Mi/50m | 上下文信息，确认资源配额不是导致启动失败的原因 |
| 4 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"}` 值为 1；`kube_pod_status_phase{phase="Pending"}` 值为 1 | 指标实时状态与 K8s 端观测结果一致，排除指标采集延迟 |
| 5 | K8s State | `kubernetes` | Pod 条件：`Initialized=True`，但 `ContainersReady=False`，`Ready=False` | 确认 Pod 基础初始化已完成，卡在容器启动阶段 |

**证据关联说明：**
*   证据 1 和 2 提供了最直接的因果线索：K8s Event 明确指出了 `unavailable-key` 在 `Secret aiops-case-04/workload-input` 中不存在，导致容器配置无法生成并抛出 `CreateContainerConfigError`（证据 2）。
*   证据 3 排除了资源不足的可能性。
*   证据 4 的 Prometheus 数据验证了 K8s 端的异常状态，且样本单一，仅展示当前快照状态，无法提供额外的趋势信息，但佐证了故障的持续性。
*   Logging 和 Tracing 维度因容器无法启动及底层监控组件权限/调度问题，处于 `not_applicable` 或错误状态，故未提供额外数据支持，但不影响对配置错误这一明确根因的判断。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 配置键名 `unavailable-key` 与实际包含的 `available-key` 不匹配 → kubelet 读取 Secret 失败 → 容器进入 CreateContainerConfigError 状态 → Pod 卡在 Pending 阶段，应用不可用
```

### 根因结论

已确认根因：Pod `aiops-case-04/workload-6584f97c76-wvcb2` 的容器配置引用了 Secret `aiops-case-04/workload-input` 中不存在的键 `unavailable-key`。
该事实由 K8s Event（证据 1）和 Container Waiting Message（证据 2）共同证实。由于关键配置项缺失，kubelet 无法创建容器，导致 Pod 始终处于 `CreateContainerConfigError` 和 `Pending` 状态。现有证据已足以支撑该结论，Logging 和 Tracing 数据的缺失不影响此静态配置错误的诊断。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 26.3s
├─ 并发证据采集: 53.6s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 53.6s (Evidence 45.8s, RCA 7.7s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
