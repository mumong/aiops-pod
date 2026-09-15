## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod aiops-case-v11/workload 处于 Pending 状态，容器 app 持续处于 CreateContainerConfigError 状态，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Warning Failed 53m (x12 over 55m) Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 直接归因：Kubelet 挂载配置时因找不到指定 Key 而失败。 |
| 2 | K8s State | Pod Spec | `container.waiting_reason: CreateContainerConfigError` | 状态确认：容器因配置缺失被阻塞，未进入运行状态。 |
| 3 | K8s State | Pod Spec | `container.waiting_message: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 细节印证：明确缺失对象为 ConfigMap 中的 `unavailable-key`。 |
| 4 | K8s State | Pod | `status: Pending` | 现象确认：Pod 卡在启动前阶段。 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"} = 1` | 独立指标佐证：与 K8s 状态一致，确认为持续配置错误状态。 |
| 6 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"} = 1` | 独立指标佐证：Pod 处于等待阶段。 |

**证据分析：**
Kubelet 日志与 K8s Event 提供了确凿证据，指出 Pod 启动受阻的直接原因是引用了 `ConfigMap workload-input` 中不存在的 `unavailable-key`。Prometheus 指标独立验证了该 Pod 始终处于 `CreateContainerConfigError` 和 `Pending` 状态，排除了短暂故障或重启波动的可能。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用 ConfigMap `workload-input` 的 Key `unavailable-key` → ConfigMap 中不存在该 Key → Kubelet 无法挂载配置，触发 CreateContainerConfigError → Pod 持续 Pending
```

### 根因结论

**已确认的根因**：Pod 定义中引用了 ConfigMap `workload-input` 中不存在的 Key `unavailable-key`（证据 #1, #3）。
该配置缺失导致 Kubelet 在初始化容器环境时发生致命错误，阻止了容器的创建，表现为 `CreateContainerConfigError`（证据 #2），最终导致 Pod 处于 `Pending` 状态（证据 #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 15.9s
├─ 并发证据采集: 40.1s
│  └─ g1 aiops-case-v11/workload: 40.1s (Evidence 32.3s, RCA 7.7s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
