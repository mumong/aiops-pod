## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod aiops-case-v11/workload 处于 CreateContainerConfigError 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container.waiting_message: `couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` (fact-39e919d389a6) | 提供直接的错误根因，明确指向配置引用缺失 |
| 2 | K8s State | Kubernetes | container.waiting_reason: `CreateContainerConfigError` (fact-e14de734c031) | 标识故障处于配置校验阶段，尚未进入容器启动 |
| 3 | K8s Event | Kubernetes | Warning Failed (x12): `Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` (fact-dbcb4d9a69d5) | 连续事件佐证配置错误持续存在且未被修复 |
| 4 | K8s State | Kubernetes | pod.phase: `Pending` (fact-e9f96f48b2cf) | 确认 Pod 停留在调度后、启动前的状态 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"}` 值为 `1` (fact-ab252f38db14) | 从监控层面对接 Kubernetes 状态，确认处于等待配置错误的状态 |

**证据说明：**
- 证据 1、2、3 均一致指向同一个核心原因：`ConfigMap aiops-case-v11/workload-input` 中缺失 key `unavailable-key`。Kubernetes 状态 (证据 1, 2) 提供了具体的错误上下文，而 Event 日志 (证据 3) 证实了该错误在观测窗口内（5m26s）重复触发了 12 次。
- 证据 4 和 5 共同确认了 Pod 处于 `Pending` 且因 `CreateContainerConfigError` 而停滞，没有进入运行或重启阶段（证据 1 显示重启次数为 0，证明根本没能拉起容器）。
- Metric 和 Kubernetes 状态在故障表现上完全吻合，共同锁定了故障范围在配置挂载/校验阶段。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'aiops-case-v11/workload-input' 中缺失 key 'unavailable-key' → Pod Spec 在校验配置引用 → kubelet 挂载/注入失败 → Pod 状态处于 CreateContainerConfigError 且无法启动
```

### 根因结论

已确认根因为：**Pod 配置错误引用了 ConfigMap `aiops-case-v11/workload-input` 中不存在的 key `unavailable-key`**。

根据证据 1 (fact-39e919d389a6) 和证据 3 (fact-dbcb4d9a69d5)，kubelet 在尝试挂载配置或注入环境变量时，无法在指定的 ConfigMap 中找到所需的 key，导致配置校验失败并返回 `CreateContainerConfigError`。由于容器未能启动，因此没有应用日志 (Logging: not_applicable) 和 Trace 数据可供参考，但 Kubernetes 状态与事件已提供充分证据链，证实该配置错误是导致 Pod 无法启动的直接原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 17.4s
├─ 并发证据采集: 36.3s
│  └─ g1 aiops-case-v11/workload: 36.3s (Evidence 28.4s, RCA 7.8s)
└─ 汇总总结: 10.7s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
