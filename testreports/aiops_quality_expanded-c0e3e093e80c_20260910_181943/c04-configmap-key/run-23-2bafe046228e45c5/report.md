## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod aiops-case-v11/workload 的容器配置中引用了 ConfigMap 'aiops-case-v11/workload-input' 中的 key 'unavailable-key'，但该 ConfigMap 中并不存在此 key，导致 kubelet 无法挂载配置并持续抛出 CreateContainerConfigError。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning  Failed          41m (x12 over 43m)     kubelet            Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` (fact-ba06d429db6f) | 核心证据：Kubelet 明确指出因缺失特定 ConfigMap Key 导致挂载失败，直接指向配置缺陷 |
| 2 | K8s State | kubernetes | Container `app` waiting reason: `CreateContainerConfigError` (fact-aec261079728) | 状态印证：容器停留在配置初始化错误阶段，符合 ConfigMap 缺失特征 |
| 3 | K8s State | kubernetes | Pod phase: `Pending`, Ready: `False` (fact-1bd8ee8206ce, fact-62e4480a73b9) | 现象印证：由于配置失败，Pod 无法进入运行态，符合上述错误的预期结果 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="CreateContainerConfigError"} = 1` (fact-59d4abf99e50) | 外部确认：Metrics 系统独立记录到 `CreateContainerConfigError` 状态 |

**证据关联说明**：K8s Event（证据 1）提供了导致故障的确切文本（缺少 `unavailable-key`），K8s State（证据 2, 3）展示了该错误导致的 Pod 挂起后果，Metric（证据 4）从监控维度交叉验证了等待原因。各来源结论一致，无冲突。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用 ConfigMap 'aiops-case-v11/workload-input' 中的 'unavailable-key' → ConfigMap 中缺失该 key → kubelet 挂载失败并触发 Failed 事件 → Pod 处于 Pending 状态且容器保持 CreateContainerConfigError
```

### 根因结论

**已确认根因**：Pod `aiops-case-v11/workload` 配置中引用了 ConfigMap `aiops-case-v11/workload-input` 中的 `unavailable-key`，但该 ConfigMap 实际不包含此 Key。
该配置错误导致 Kubelet 无法为容器挂载配置，进而触发 `CreateContainerConfigError`（证据 1, 2, 4），使 Pod 持续处于 `Pending` 状态（证据 3）。

---

## 📊 性能统计

```text
├─ 总耗时: 59.3s
├─ 问题定位: 15.0s
├─ 并发证据采集: 35.6s
│  └─ g1 aiops-case-v11/workload: 35.6s (Evidence 26.6s, RCA 8.8s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
