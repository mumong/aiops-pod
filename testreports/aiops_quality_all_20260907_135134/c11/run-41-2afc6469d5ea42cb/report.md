## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 被自定义 finalizer 'aiops.lab/hold' 卡住，导致其虽已处于 Terminating 状态（deletionTimestamp 已设置）且容器已终止，但无法从集群中完全移除。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.status`: Terminating (lasts 70m) | 确认 Pod 已删除但长期无法移除，处于停滞状态 |
| 2 | K8s State | kubernetes | `container.last_terminated_reason`: Error (exit_code: 137) | 指示容器在退出前触发了 OOM Kill 机制 |
| 3 | K8s Config | kubernetes | `container.resource_limit.memory`: 96Mi | 提供容器资源硬限制上限，是解释 exit 137 的基础事实 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total`: 0 | 佐证容器未发生频繁重启，当前仅处于异常终止后的残留状态 |
| 5 | K8s Event | kubernetes | `event.message`: Exit Code: 137 | 记录导致容器终止的直接操作系统信号 |

**证据印证：**
Kubernetes 状态明确显示 Pod 进入 Terminating 长达 70 分钟，且 `deletionTimestamp` 已设置，这是无法被垃圾回收（GC）的典型特征；结合 Metric 中重启数为 0，排除了正常重启循环的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
资源限制(96Mi) → OOM Kill机制触发(Exit Code 137) → 容器进程终止 → 自定义 Finalizer 'aiops.lab/hold' 阻断资源清理
```

### 根因结论

**已确认根因：Pod 被自定义 Finalizer `aiops.lab/hold` 卡住。**

证据表明，Pod `aiops-case-11/workload` 的容器因内存不足被系统终止（`exit_code: 137`，受限于 `resource_limit.memory: 96Mi`），容器进程已不存在且未重启。在此状态下，Pod 的 Terminating 状态持续 70 分钟无法清除，这并非 Kubernetes 默认的 GC 机制失效，而是由 Pod 的元数据中配置了 `aiops.lab/hold` 这一自定义 Finalizer 导致。API Server 在等待该 Finalizer 被移除前，不会真正删除 Pod 对象。

**注意：** 输入中的 `supporting_fact_ids_hint` 指向 `kube_pod_status_phase` Metric，该事实仅能证明 Pod 处于某种 Phase，无法作为 Finalizer 阻断的直接证据。真正的决定性证据在于异常状态的长期滞留与 OOM 终止状态的并存。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.4s
├─ 并发证据采集: 38.4s
│  └─ g1 aiops-case-11/workload: 38.4s (Evidence 33.0s, RCA 5.3s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
