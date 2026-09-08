## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod spec 引用了 Secret aiops-case-04/workload-input 中不存在的 key 'unavailable-key'，且该 Secret 当前不存在（或为空），导致 kubelet 触发 CreateContainerConfigError。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `container.waiting_message` | `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (fact-35221dbf542c) | 根因：明确指向挂载配置中引用的 Secret Key 不存在。 |
| 2 | K8s Event | `event.message` | `Warning  Failed          9m51s (x12 over 11m)  kubelet            Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (fact-4d12d5223746) | 验证：Kubelet 周期性失败，证实故障具有持续性而非瞬时网络抖动。 |
| 3 | K8s State | `container.waiting_reason` | `CreateContainerConfigError` (fact-d74c08803e13) | 机制：Pod 无法进入 `Running` 状态，处于容器配置校验阶段的阻塞。 |
| 4 | K8s State | `pod.phase` & `container.restart_count` | `phase: Pending` (fact-85747a0a4c47), `restart_count: 0` (fact-de0a41b3bbf5) | 现象：Pod 始终无法调度到 Running 阶段，且未发生过重启。 |
| 5 | Metric | `kube_pod_container_status_waiting_reason` | `reason: CreateContainerConfigError`, value: 1 (fact-7b17b4372287) | 佐证：Prometheus 监控状态与 Kubernetes 对象状态完全一致。 |

**证据分析：**
1. 证据 #1 与 #2 高度一致：Kubelet 的 Warning 事件（#2）与容器等待消息（#1）不仅错误原文完全匹配，还明确了故障源头是 Secret 的 Key 缺失。
2. 证据 #3 确认了该错误的直接结果：`CreateContainerConfigError` 导致容器无法启动，这与 Restart Count 为 0 的证据（#4）逻辑吻合，说明 Pod 卡在预启动配置阶段。
3. 证据 #5 作为指标验证，再次确认了集群处于等待配置错误的状态。
4. 日志与追踪维度（Logging/Tracing）因容器未启动被物理阻断，无法提供额外信息，但 Kubernetes 维度的证据链已足以闭环。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 错误引用不存在的 Secret Key 'unavailable-key' → Kubelet 校验失败 → 触发 CreateContainerConfigError → Pod 卡在 Pending 状态，无法进入运行阶段
```

### 根因结论

已确认的根因为：**Pod 的容器规格引用了 Secret `aiops-case-04/workload-input` 中不存在的 Key `unavailable-key`**。

该错误配置导致 Kubelet 在尝试创建容器时失败，具体表现为 `CreateContainerConfigError`。集群中该 Pod 的 `waiting_reason`、等待消息以及 Prometheus 监控指标均一致证实了此配置错误，故障现象确认为 Pod 卡在 Pending 状态。

缺失的排查工具（`pod_yaml_spec_check`）未执行，但鉴于 Kubelet 已明确指出了缺失的 Key，现有证据已足以锁定配置错误，无需 Pod Spec 详情即可得出确定性结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 15.8s
├─ 并发证据采集: 51.4s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 51.4s (Evidence 46.1s, RCA 5.2s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
