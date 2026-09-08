## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-wvcb2 处于 Pending 阶段，容器无法启动，状态为 CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning Failed ... kubelet Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接指出容器启动失败原因，Kubelet 找不到指定 Key |
| 2 | K8s State | Kubernetes | `container.waiting_reason`: CreateContainerConfigError, `container.waiting_message`: couldn't find key unavailable-key in Secret aiops-case-04/workload-input | 确认容器因配置错误处于等待状态，报错内容一致 |
| 3 | K8s State | Kubernetes | `pod.phase`: Pending, `ContainersReady`: False, `RestartCount`: 0 | 确认 Pod 状态及容器未成功运行的事实 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (reason=CreateContainerConfigError): 1 | 从指标层面确认该 Pod 的等待原因 |

证据 1（K8s Event）与证据 2（K8s State）均指向同一核心错误，确认 Pod 处于 Pending 状态且容器无法启动是因为在 Secret `aiops-case-04/workload-input` 中找不到 `unavailable-key`。指标数据进一步在系统层面印证了这一状态。

## 🎯 根因分析 · g1

### 因果链

```text
Secret `aiops-case-04/workload-input` 中不存在 `unavailable-key` → Pod 容器配置请求注入不存在的密钥键 → Kubelet 注入配置失败 → 容器进入 CreateContainerConfigError 状态
```

### 根因结论

已确认根因为 **Secret 键名引用错误**。Pod `aiops-case-04/workload-6584f97c76-wvcb2` 的容器配置中请求注入 `aiops-case-04/workload-input` Secret 中的 `unavailable-key`，但该 Secret 实际数据中仅包含 `available-key`，导致 Kubelet 无法注入该配置并拒绝启动容器（证据 1、证据 2）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 22.1s
├─ 并发证据采集: 55.2s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 55.2s (Evidence 45.6s, RCA 9.4s)
└─ 汇总总结: 7.2s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
