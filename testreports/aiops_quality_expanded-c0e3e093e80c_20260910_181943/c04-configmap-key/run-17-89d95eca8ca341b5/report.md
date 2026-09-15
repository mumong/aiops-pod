## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod `aiops-case-v11/workload` 配置错误地引用了 ConfigMap `workload-input` 中不存在的 key `unavailable-key`，而该 ConfigMap 实际仅包含 `available-key`，导致 Kubernetes 无法注入环境变量，触发 `CreateContainerConfigError` 并阻断容器启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: `CreateContainerConfigError` (容器 `app`) | 直接指示容器因配置错误无法启动 |
| 2 | K8s State | kubernetes | `container.waiting_message`: `couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 精确定位缺失资源的类型（ConfigMap）、名称 (`workload-input`) 及缺失键名 (`unavailable-key`) |
| 3 | K8s State | kubernetes | `pod.condition` (`ContainersReady`/`Ready`): `False` (reason: `ContainersNotReady`) | 确认 Pod 因上述配置问题处于不可用状态 |
| 4 | K8s State | kubernetes | `pod.phase`: `Pending` | 确认工作负载停留在待调度/未运行状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (`app`, `CreateContainerConfigError`): `1` | 独立于 K8s API 的状态采样，印证配置错误导致容器进入等待状态 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total` (`app`): `0` | 确认未发生实际重启，符合 `ConfigError` 阻断启动的特征 |

**证据说明：**
Kubernetes 状态直接捕获了底层错误（找不到 ConfigMap 键）并导致容器进入 `CreateContainerConfigError` 等待状态；Prometheus 指标（`waiting_reason=1` 且 `restarts=0`）独立印证了该配置错误导致容器被阻断、无重启发生的现象。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap `workload-input` 缺失 Pod 指定的 key `unavailable-key` → Kubelet 在创建容器 `app` 时校验 ConfigMap key 失败 → 容器启动抛出 `CreateContainerConfigError` 异常 → Pod 状态锁定在 `Pending`，无法运行应用
```

### 根因结论

**已确认根因**：Pod `aiops-case-v11/workload` 错误引用了 ConfigMap `workload-input` 中不存在的键 `unavailable-key`。

**证据支撑**：
1.  **直接证据**：K8s 容器状态消息明确报告 `couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input`，揭示了配置引用与实际资源数据不匹配的根源 [证据 #2]。
2.  **状态印证**：该配置错误直接导致了 `CreateContainerConfigError` 状态 [证据 #1, #5]，并使得 Pod 维持在 `Pending` 阶段且未产生任何重启 [证据 #4, #6]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 20.2s
├─ 并发证据采集: 53.7s
│  └─ g1 aiops-case-v11/workload: 53.7s (Evidence 44.3s, RCA 9.3s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
