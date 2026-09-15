## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod aiops-case-v11/workload 处于 Pending 状态，容器 app 持续报 CreateContainerConfigError，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubernetes` | Fact `fact-2d93f4c24bd6`：`couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 直接定位到具体的资源缺失及键名错误，解释容器无法配置的原因。 |
| 2 | K8s State | `kubernetes` | Fact `fact-05048ce85df0`：`container.waiting_reason = CreateContainerConfigError` | 确认 kubelet 在拉取镜像和启动容器前即失败的错误类型。 |
| 3 | K8s State | `kubernetes` | Fact `fact-698681450fc4`：`pod.phase = Pending` | 确认 Pod 停留在调度和启动前阶段，未进入运行状态。 |
| 4 | Metric | `prometheus` | Fact `fact-0f307a74f107`：`kube_pod_container_status_waiting_reason` 值为 `1` (reason: `CreateContainerConfigError`) | 从指标层面独立印证了 Pod 处于配置错误的等待状态。 |
| 5 | K8s State | `kubernetes` | Fact `fact-c73c0acc1309`：`container.restart_count = 0` | 证明容器从未成功启动，排除因运行时资源耗尽导致的反复崩溃重启。 |

**证据说明：**
Kubernetes 原生状态与 Prometheus 指标高度一致：`CreateContainerConfigError` 明确指出了配置解析失败，而非健康检查失败或资源调度问题；重启次数为 0 与“配置无法生效导致无法启动”的逻辑完全吻合。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap aiops-case-v11/workload-input 中缺失 key unavailable-key → Pod 容器启动时无法注入环境变量/配置 → kubelet 拒绝启动容器并报告 CreateContainerConfigError → Pod 卡在 Pending 状态，app 容器持续报错。
```

### 根因结论

已确认根因为 **配置引用不匹配**。

Pod 定义（实体 `aiops-case-v11/workload`）试图从 ConfigMap `aiops-case-v11/workload-input` 中读取 `unavailable-key`，但该 ConfigMap 实例中实际不存在此键。这一配置层面的冲突导致 kubelet 在启动阶段即阻断容器初始化，从而引发 `CreateContainerConfigError` 和 `Pending` 状态。证据 `fact-2d93f4c24bd6` 提供了确凿的原文报错。

---

## 📊 性能统计

```text
├─ 总耗时: 59.4s
├─ 问题定位: 14.8s
├─ 并发证据采集: 35.7s
│  └─ g1 aiops-case-v11/workload: 35.7s (Evidence 28.4s, RCA 7.2s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
