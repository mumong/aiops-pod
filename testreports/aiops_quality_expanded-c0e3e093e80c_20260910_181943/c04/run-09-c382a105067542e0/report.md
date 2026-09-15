## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-h4lt9 处于 CreateContainerConfigError 状态，未恢复 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | K8s | Warning Failed: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接指出配置拉取失败的具体缺失项 |
| 2 | K8s State | K8s | Pod `aiops-case-04/workload-6584f97c76-h4lt9` 状态为 `Pending`，`CreateContainerConfigError` | 确认当前异常现象 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 中 `CreateContainerConfigError` 值为 1 | 独立确认异常类型 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 值为 0 | 排除重启震荡，确认为启动前静默卡死 |
| 5 | Logging | ES | 查询失败：`container "app" in pod ... is waiting to start: CreateContainerConfigError` | 印证 K8s 状态，确认无法获取应用日志 |

**证据说明：**
K8s Event 明确记录了 `Secret` 中缺失 `unavailable-key` 的具体错误，直接支撑了配置拉取失败的机制。K8s 状态与 Prometheus 指标（`CreateContainerConfigError`）互相印证，且重启次数为 0 确认了该错误发生在容器生命周期极早期，导致应用日志不可用。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用了不存在的 Secret Key (unavailable-key) → kubelet 拉取 Secret 配置失败 → 容器创建失败并触发 CreateContainerConfigError → Pod 持续 Pending 无法恢复
```

### 根因结论

已确认根因为 **Pod 定义中引用的 Secret 配置项不存在**。Pod `aiops-case-04/workload-6584f97c76-h4lt9` 的容器配置指向了 `Secret aiops-case-04/workload-input` 中的 `unavailable-key`，但该 Secret 中并未包含此 key，导致 kubelet 在启动阶段无法拉取配置，从而抛出 `CreateContainerConfigError` 使 Pod 持续处于 `Pending` 状态（见证据 #1）。

**未确认项：**
未提供 `Secret aiops-case-04/workload-input` 的完整内容以验证是否存在其他可用 key。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 32.4s
├─ 并发证据采集: 40.3s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 40.3s (Evidence 30.9s, RCA 9.3s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
