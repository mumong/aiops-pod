## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod aiops-case-v11/workload 处于 CreateContainerConfigError 状态，未能启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` Waiting 原因: `CreateContainerConfigError`，消息: `couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 直接锁定根因为 ConfigMap key 引用缺失 |
| 2 | K8s State | Kubernetes | Pod `phase`: `Pending`，Condition `ContainersReady`: `False` (reason: `ContainersNotReady`) | 确认 Pod 因配置校验失败无法进入运行状态 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"}` 当前值为 `1` (单样本) | 确认集群中该 Pod 处于预期的配置错误状态 |

**证据说明**
Kubernetes State 提供了最直接的因果证据，明确指出了缺失的 key 名称 (`unavailable-key`) 和对应的 ConfigMap 名称 (`workload-input`)。Metric 数据的单样本记录确认了该 Pod 持续处于 `CreateContainerConfigError` 状态，与 K8s 状态完全一致，无其他异常模式干扰。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 配置引用了 ConfigMap 'aiops-case-v11/workload-input' 中不存在的 key 'unavailable-key' → kubelet 容器创建时校验 ConfigMap key 失败，触发 CreateContainerConfigError → Pod 持续处于 Pending 和 ContainersNotReady 状态，无法启动应用容器
```

### 根因结论

已确认根因为 **Pod 配置引用了 ConfigMap 中不存在的 Key**。

证据显示，Pod `aiops-case-v11/workload` 在容器创建阶段因寻找 ConfigMap `aiops-case-v11/workload-input` 中的 `unavailable-key` 失败，直接导致 `CreateContainerConfigError` 异常，进而使得 Pod 保持在 `Pending` 状态且无法就绪（`ContainersNotReady`）。Metric 数据进一步佐证了这一配置错误状态的持续性。

---

## 📊 性能统计

```text
├─ 总耗时: 58.3s
├─ 问题定位: 13.5s
├─ 并发证据采集: 37.8s
│  └─ g1 aiops-case-v11/workload: 37.8s (Evidence 31.2s, RCA 6.5s)
└─ 汇总总结: 7.0s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
