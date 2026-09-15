## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod `workload-5b5fc86c8c-xn974` 引用了不存在的 ConfigMap `unavailable-config`，且配置为 `Optional: false`（默认），导致 Kubelet 挂载卷时查找失败，容器无法启动，Pod 持续处于 `Pending` 和 `ContainerCreating` 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `container.waiting_reason` | `ContainerCreating` (fact-ceed23ebafda) | 确认容器正处于挂载卷尝试中，且未启动。 |
| 2 | K8s State | `pod.phase` | `Pending` (fact-18a4f056d7fa) | 确认 Pod 整体未就绪。 |
| 3 | K8s Config | `configmap` 缺失 | `configmap "unavailable-config" not found` (fact-6bfee3af08fb) | 直接证据：Kubelet 报告无法找到名为 `unavailable-config` 的 ConfigMap。 |
| 4 | K8s Event | `FailedMount` | `timed out waiting for the condition` (fact-48c0e4b8bddf) | 说明挂载失败是持续存在的阻塞状态。 |
| 5 | Metric | `kube_pod_container_status_waiting_reason` | `1`, labels=`{reason: "ContainerCreating"}` (fact-a9e5db2ab8ca) | 监控指标与 Pod 状态一致，确认为持续性等待而非瞬态。 |

**证据分析：**
K8s 事件明确指出了 `FailedMount` 且伴随 `unavailable-config not found`，结合 Pod 状态为 `Pending` 及 `ContainerCreating`，证实 Pod 无法启动是由于底层资源（ConfigMap）缺失导致挂载卷操作一直超时/失败。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap `unavailable-config` 不存在且 `Optional: false` → Kubelet 挂载卷查找失败 → 容器等待挂载完成 → Pod 处于 Pending 和 ContainerCreating 状态
```

### 根因结论

已确认的根因为：Pod `workload-5b5fc86c8c-xn974` 引用了不存在的 ConfigMap `unavailable-config`，且该配置未标记为 `Optional`，导致 Kubelet 在挂载卷时因资源缺失而阻塞，容器无法启动 [3, 4, 5]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 18.0s
├─ 并发证据采集: 36.8s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 36.8s (Evidence 30.1s, RCA 6.6s)
└─ 汇总总结: 7.5s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-imagepull-failed, pod-volume-mount-failed
