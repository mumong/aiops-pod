## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod workload (aiops-case-v01) remains in Pending state due to FailedScheduling (Insufficient cpu) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedScheduling 4m41s ... 0/3 nodes are available: 3 Insufficient cpu` (`fact-f9c01a9b7d9b`) | 调度器明确报告集群所有节点 CPU 资源不足，是导致 Pod 挂起的直接触发原因。 |
| 2 | K8s Event | kubernetes | `Warning FailedScheduling 5m17s ... 0/3 nodes are available: 3 Insufficient cpu` (`fact-fc94c33eca03`) | 证明 CPU 资源缺口在较长时间窗口内持续存在且未缓解。 |
| 3 | K8s State | kubernetes | `pod.phase: Pending`, `pod.condition: Unschedulable` (`fact-1d6cc9af59ef`, `fact-2fc7026eb083`) | 描述 Pod 的当前异常状态：由于无法匹配资源分配，Pod 始终停留在 Pending 阶段。 |
| 4 | K8s Config | kubernetes | `container.app CPU request: 100k` (`fact-3f1f7cfb7d1d`) | 定义了该 Pod 对计算资源的硬性需求。该数值远超任何单节点的物理上限，直接解释了调度器的拒绝逻辑。 |
| 5 | Metric | prometheus | `kube_pod_container_resource_requests{cpu="core"} = 100000` (`fact-a388b06078a3`) | 监控侧实时确认了 Pod CPU 请求值为 100000 core，与 K8s 声明的配置完全一致。 |

**证据关联：**
*   K8s Event 明确指出了资源类型（CPU）的短缺，而 K8s Config 中的 100k CPU request 数值构成了这一短缺的绝对事实。
*   Metric 数据独立验证了 Pod 请求的 100000 core CPU 资源，证实配置已生效且未被修改，排除了运行时动态调整的可能。

## 🎯 根因分析 · g1

### 因果链

```text
Pod CPU request (100k cores) → 超出单节点物理容量上限 → 调度器无法分配可用节点 → Pod 状态持续 Pending
```

### 根因结论

**已确认根因：Pod CPU 请求量（100k cores）严重超出集群内任何单节点的物理 CPU 容量上限。**

当前集群仅有 3 个节点，调度器在尝试调度 `workload` 时，判定所有节点均无法满足该 Pod 的 CPU 资源需求（`Insufficient cpu`）。由于 Pod 的单实例 CPU 请求量级远超单机极限，调度器无法找到任何合法的分配目标，也无法触发抢占机制（`No preemption victims`），导致 Pod 永久处于 `Pending` 状态。

*   **关键证据**：
    *   K8s Event `FailedScheduling` 显示 `0/3 nodes are available: 3 Insufficient cpu` (`fact-f9c01a9b7d9b`)。
    *   Pod 定义中 `app` 容器的 `cpu` 请求量高达 `100k` (`fact-3f1f7cfb7d1d`)。
    *   Prometheus 指标确认该 Pod 的 CPU 请求值确实为 `100000` (`fact-a388b06078a3`)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 14.2s
├─ 并发证据采集: 70.5s
│  └─ g1 aiops-case-v01/workload: 70.5s (Evidence 62.4s, RCA 8.0s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
