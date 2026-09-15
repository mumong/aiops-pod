## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod workload 的配置引用了 ConfigMap aiops-case-v11/workload-input 中不存在的 key 'unavailable-key'，导致 kubelet 创建容器时校验失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `fact-151bf1857867` | `Warning Failed 14m (x12 over 16m) kubelet Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 直接证明 kubelet 在尝试启动容器时，因找不到指定的 ConfigMap Key 而触发校验失败事件。 |
| 2 | K8s State | `fact-cad148fb4304` | `container: app, message: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 容器 `app` 的 `waiting_message` 明确指示了配置缺失的具体原因，与事件记录高度一致。 |
| 3 | K8s State | `fact-ce44aabf3b83` | `container: app, reason: CreateContainerConfigError` | 确认了容器的状态原因为“创建容器配置错误”，这是典型的引用外部配置（ConfigMap/Secret）失败的标识。 |
| 4 | Metric | `fact-27a693a1fa3d` | `kube_pod_container_status_waiting_reason=1` (labels: `container: app`, `reason: CreateContainerConfigError`) | 独立监控指标再次确认容器当前卡在 `CreateContainerConfigError` 状态，数值为 1 表示该 Pod 正受此问题阻塞。 |
| 5 | K8s State | `fact-420bad215063` | `pod.phase: Pending` | Pod 始终处于 `Pending` 阶段，未进入 `Running` 状态，符合配置校验未通过导致无法创建容器的逻辑。 |

**证据印证：**
Kubernetes 事件 (`fact-151bf1867`) 与容器状态 (`fact-cad148fb4304`) 在错误信息上完全重合，均指向 `workload-input` ConfigMap 中缺失 `unavailable-key`。PromQL 监控 (`fact-27a693a1fa3d`) 提供了独立的数值验证，确认容器当前状态为 `CreateContainerConfigError`，且 Pod 处于 `Pending` 阶段 (`fact-420bad215063`)。这些多维度事实共同指向了同一个配置引用错误。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap aiops-case-v11/workload-input 缺少 key 'unavailable-key' → Pod 容器 spec 强制引用该缺失 key → kubelet 创建容器时配置校验失败 (CreateContainerConfigError) → Pod 持续处于 Pending 状态且容器未启动
```

### 根因结论

**已确认的根因**：
Pod `aiops-case-v11/workload` 的容器 `app` 在其配置中引用了 ConfigMap `aiops-case-v11/workload-input` 中的一个键 `unavailable-key`。然而，该 ConfigMap 中并不存在此键（证据 `fact-151bf1857867`, `fact-cad148fb4304`）。

这一配置错误导致 kubelet 在尝试启动容器时，无法完成环境变量或挂载项的配置注入，从而抛出 `CreateContainerConfigError`（证据 `fact-ce44aabf3b83`, `fact-27a693a1fa3d`），使得 Pod 无法脱离 `Pending` 状态（证据 `fact-420bad215063`）。事实链闭合，无需更多证据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 20.0s
├─ 并发证据采集: 33.2s
│  └─ g1 aiops-case-v11/workload: 33.2s (Evidence 27.4s, RCA 5.7s)
└─ 汇总总结: 11.9s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
