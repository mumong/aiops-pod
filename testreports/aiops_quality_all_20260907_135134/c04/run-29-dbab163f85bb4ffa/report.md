## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod workload-6584f97c76-7ds5p 处于 CreateContainerConfigError 状态，容器无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (Fact ID: `fact-23eccf9c0669`) | 直接证实挂载失败的物理原因，定位到具体的缺失键值 |
| 2 | K8s State | kubernetes | Container `app` 处于 `CreateContainerConfigError`，原因是 "couldn't find key unavailable-key in Secret aiops-case-04/workload-input" (Fact IDs: `fact-9d9e451a9250`, `fact-e8ad6c7589b9`) | 确认容器因配置读取失败而处于等待状态，无法进入运行态 |
| 3 | K8s State | kubernetes | Pod 处于 `Pending`，`Ready` 和 `ContainersReady` 均为 `False`，原因 `ContainersNotReady` (Fact IDs: `fact-3b169b5e63cc` 至 `fact-d12e61cf398c`) | 描述 Pod 最终表现状态，证实容器组未就绪 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"}` = `1` (Fact ID: `fact-7db868cd26da`) | 独立证实容器处于配置错误导致的等待状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total` = `0` (Fact ID: `fact-f9007a0fe9d9`) | 证实故障发生在启动前，无重启发生，排除了运行期崩溃的可能性 |

**证据分析：**
Kubernetes 事件与容器状态一致指向 Secret Key 缺失问题，且 Metrics 独立印证了该状态。由于容器从未成功启动，Logging 与 Tracing 维度未产生应用数据，这与预期物理行为完全一致。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用 Secret key 'unavailable-key' (事实) → Secret aiops-case-04/workload-input 中不存在该 key → kubelet 无法挂载配置 → Pod 处于 CreateContainerConfigError 状态，容器无法启动
```

### 根因结论

**已确认根因：** Pod `aiops-case-04/workload-6584f97c76-7ds5p` 的容器配置中引用了 Secret `aiops-case-04/workload-input` 中不存在的 Key `unavailable-key`。

这一配置错误导致 `kubelet` 在初始化容器时无法挂载相应的配置卷，进而触发 `CreateContainerConfigError` 状态并阻止容器启动（引用证据 `fact-23eccf9c0669`, `fact-9d9e451a9250`）。现有证据充分，无需补充其他决定性事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 18.7s
├─ 并发证据采集: 42.8s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 42.8s (Evidence 35.2s, RCA 7.5s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
