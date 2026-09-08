## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod spec引用了Secret 'workload-input'中不存在的key 'unavailable-key'，导致kubelet无法注入配置，容器持续处于CreateContainerConfigError状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: app 容器处于 `CreateContainerConfigError` 状态 (`fact-52f823c9280c`) | 直接描述当前容器的异常状态 |
| 2 | K8s State | Kubernetes | `container.waiting_message`: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (`fact-736fbdfad864`) | 明确定位了导致配置注入失败的精确原因和缺失资源 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 值为 1，标签显示 `reason=CreateContainerConfigError` (`fact-95e292dde039`) | 从指标层面佐证了 K8s 状态的持续性 |
| 4 | K8s State | Kubernetes | `pod.phase`: `Pending`；`container.restart_count`: 0 (`fact-0e3851907a6d`, `fact-63a2deea1863`) | 说明容器从未成功启动，排除了应用运行时的逻辑故障 |

**证据说明**：
1. Kubernetes 的等待状态（证据 1、2）与 Prometheus 指标（证据 3）完全一致，共同指向 `CreateContainerConfigError` 这一核心问题。
2. 证据 2 提供了确切的缺失 Key 信息 (`unavailable-key`)，解释了为何 Pod 会卡在 Pending 阶段且重启次数为 0（证据 4），因为故障发生在容器启动前的配置注入阶段，而非应用启动后。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 引用了 Secret 'workload-input' 中不存在的 Key 'unavailable-key' (未确认，仅推测) 
  → kubelet 尝试注入配置时读取失败 (未确认) 
  → 容器持续处于 CreateContainerConfigError 状态 
  → Pod 卡在 Pending 状态，应用无法启动
```

### 根因结论

**已确认的根因**：Pod `aiops-case-04/workload-6584f97c76-wvcb2` 的容器配置引用了 Secret `aiops-case-04/workload-input` 中不存在的 Key `unavailable-key`，导致 kubelet 无法完成配置注入，容器无法启动。

**证据引用**：
- Kubernetes 状态明确报错 `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (证据 2)。
- 指标与状态确认容器一直卡在 `CreateContainerConfigError` 阶段且未发生过重启 (证据 1, 3, 4)。

**缺失的决定性事实**：虽然 K8s 错误已明确指出缺失的 Key，但未获取 Pod 的 YAML 规范事实（收集阶段失败），因此无法确证该 Key 是否确实在 Pod 的 `env` 或 `envFrom` 中被错误引用，但该引用错误已足以解释当前的故障现象。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 20.0s
├─ 并发证据采集: 102.5s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 102.5s (Evidence 96.6s, RCA 5.7s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
