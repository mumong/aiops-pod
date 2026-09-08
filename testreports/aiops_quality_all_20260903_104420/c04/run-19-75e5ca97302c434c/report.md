## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-wvcb2 的 spec 引用了 Secret aiops-case-04/workload-input 中不存在的 key 'unavailable-key'，导致 Kubelet 无法注入容器配置并持续抛出 CreateContainerConfigError。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning Failed ... kubelet Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (Fact: `fact-09aac8c398c4`, `fact-b5df034d5211`) | 直接定位 Kubelet 注入配置的失败原因，指明缺失的具体键名 |
| 2 | K8s State | Kubernetes | `container.waiting_reason: CreateContainerConfigError` (Fact: `fact-066efddad003`) | 证实 Pod 处于配置注入失败导致的等待状态 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"} = 1` (Fact: `fact-20d2ad4ed4b1`) | 独立证实 Pod 正停留在由配置错误引起的等待状态 |
| 4 | K8s State | Kubernetes | `pod.status: Pending` (Fact: `fact-798a6f7dc81c`) | 证实 Pod 未完成初始化并处于挂起状态 |

**证据印证说明：**
Kubernetes Event (`#1`) 提供了根本错误原文，直接解释了为何 Pod 状态为 Pending 且等待原因为 `CreateContainerConfigError` (`#2`)。Prometheus Metric (`#3`) 的等待原因指标与 K8s 状态完全一致，独立证实了当前未就绪状态是由同一配置错误引起的。由于容器未能启动，Logging 与 Tracing 维度缺失 (`not_applicable`)，未产生冲突。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 引用了 Secret 中不存在的 key 'unavailable-key' → Kubelet 注入容器配置失败 → Kubelet 持续抛出 CreateContainerConfigError → Pod 处于 Pending/Waiting 状态且无法运行
```

### 根因结论

**已确认根因：**
Pod `aiops-case-04/workload-6584f97c76-wvcb2` 的 spec 错误引用了 Secret `aiops-case-04/workload-input` 中不存在的密钥键 `unavailable-key`。

**证据支撑：**
1. **直接错误来源**：Kubernetes Event (`#1`) 明确记录 `kubelet` 报错 `Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input`。
2. **状态印证**：Kubernetes State (`#2`, `#4`) 显示容器等待原因为 `CreateContainerConfigError`，Pod 状态为 `Pending`，符合配置未注入时的标准表现。
3. **指标验证**：Prometheus Metric (`#3`) 显示 `kube_pod_container_status_waiting_reason` 标记为 `CreateContainerConfigError`，与 K8s 状态完全一致。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 18.3s
├─ 并发证据采集: 90.9s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 90.9s (Evidence 84.7s, RCA 6.0s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
