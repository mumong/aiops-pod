## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod aiops-case-v11/workload 处于 Pending 状态，容器 app 处于 Waiting 状态，状态原因为 CreateContainerConfigError。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Fact `fact-1998b37190dd`: 容器 `app` 等待原因 `CreateContainerConfigError`，消息：`couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 直接说明容器启动被拒的根本原因是配置引用缺失。 |
| 2 | K8s Event | kubernetes | Fact `fact-1c363e687c52`: Kubelet 持续报 `Warning Failed`，消息：`Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 确认 Kubelet 在挂载配置时的具体失败机制。 |
| 3 | K8s State | kubernetes | Fact `fact-15e7af58f1e4`, `fact-ae2760ff0cd6`: Pod 阶段 `Pending`，状态 `Pending` | 描述 Pod 因配置错误被挂起的最终可见状态。 |
| 4 | Metric | prometheus | Fact `fact-3f35e22d5099`: `kube_pod_container_status_waiting_reason` 当前值为 1，标签 `reason: CreateContainerConfigError` | 从监控系统侧面印证了容器卡在等待状态的具体原因。 |

**证据关系：**
Kubernetes 原生事实（Fact 1, 2）直接指出了错误来源（ConfigMap 键缺失），Metric 数据（Fact 4）在状态上保持一致，共同确认了这是一个由于 Pod 配置错误导致的启动阻塞问题。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用了 ConfigMap 'aiops-case-v11/workload-input' 中不存在的 key 'unavailable-key' → Kubelet 挂载配置失败 → 容器启动被拒绝 (CreateContainerConfigError) → Pod 持续处于 Pending/Waiting 状态
```

### 根因结论

已确认根因：Pod `aiops-case-v11/workload` 的容器 `app` 在启动过程中，Kubelet 尝试注入环境变量或挂载配置时，在 ConfigMap `aiops-case-v11/workload-input` 中找不到指定的键 `unavailable-key`。这一配置错误直接导致容器启动失败并被系统标记为 `CreateContainerConfigError`，进而使 Pod 维持在 `Pending` 状态（见证据 Fact 1, 2）。

---

## 📊 性能统计

```text
├─ 总耗时: 56.0s
├─ 问题定位: 15.0s
├─ 并发证据采集: 32.6s
│  └─ g1 aiops-case-v11/workload: 32.6s (Evidence 26.1s, RCA 6.4s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
