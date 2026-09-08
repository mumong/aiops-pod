## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod `aiops-case-04/workload-6584f97c76-wvcb2` 引用了 Secret `aiops-case-04/workload-input` 中的 key `unavailable-key`，但该 Secret 中实际只存在 key `available-key`，导致 Kubelet 无法创建容器配置。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubectl get` | `container.waiting_reason=CreateContainerConfigError`, `container.waiting_message="couldn't find key unavailable-key in Secret aiops-case-04/workload-input"` (fact-33cc8300f966, fact-67e3f354016d) | 直接确认 Kubelet 无法创建容器配置的原因是 Secret Key 缺失。 |
| 2 | K8s Event | `kubectl get events` | `Warning Failed ... kubelet Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (fact-b23d7167959a, fact-d3524caa5d1f) | 提供 Kubelet 侧重复报错记录，证实故障发生在容器启动前阶段。 |
| 3 | K8s State | `kubectl get pods` | `pod.phase=Pending`, `ContainersReady=False`, `Ready=False` (fact-219384e6efed, fact-255aff316f61, fact-a59cc450b377) | 描述 Pod 处于不可用状态的系统级现象。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"} = 1` (fact-f4eb6c11549c) | 跨维度确认当前等待原因为配置错误。 |
| 5 | Metric | Prometheus | `kube_pod_status_phase{phase="Pending"} = 1`, `kube_pod_container_status_ready = 0` (fact-a44124b7e703, fact-3d311b9ef041) | 量化反映 Pod 持续处于 Pending 且未就绪的状态。 |

**证据印证关系：**
K8s State 与 Event 中明确的 `CreateContainerConfigError` 和 `couldn't find key unavailable-key` 原始错误信息，与 Prometheus 中统计到的 `waiting_reason=CreateContainerConfigError` 相互印证，确认故障根因并非资源不足或网络问题，而是启动前配置查找失败。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 引用了不存在的 Secret key "unavailable-key" (事实支撑) → Kubelet 无法解析并挂载配置 → 容器无法创建/启动 (CreateContainerConfigError) → Pod 处于 Pending 状态
```

### 根因结论

**已确认的根因**：Pod `aiops-case-04/workload-6584f97c76-wvcb2` 在其容器配置中引用了 Secret `aiops-case-04/workload-input` 中的 key `unavailable-key`，但目标 Secret 中并不存在该 key（实际仅存在 `available-key`）。

**支持事实**：
1.  **K8s State/Event** 明确指出容器因找不到指定 Secret key 而报错，直接触发 `CreateContainerConfigError` (证据 1, 2)。
2.  **Metric** 独立验证了该 Pod 正处于配置错误导致的等待状态 (证据 4)。

现有证据已形成闭环，确认为配置引用错误。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 18.5s
├─ 并发证据采集: 63.6s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 63.6s (Evidence 54.6s, RCA 8.8s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
