## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod 配置引用了 Secret 'aiops-case-04/workload-input' 中不存在的密钥 'unavailable-key'，导致容器无法加载配置并持续处于 'CreateContainerConfigError' 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` | `Warning Failed ... Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接指出容器配置挂载失败的具体原因：Secret 中缺少所需的 `unavailable-key`。 |
| 2 | K8s State | `pod.status` | `status: "Pending"` | 描述 Pod 因配置错误而无法进入运行状态的最终表现。 |
| 3 | Metric | `kube_pod_container_status_waiting_reason` | `value: 1` (reason: `CreateContainerConfigError`) | 观测到容器处于等待状态，且原因为配置错误，与 Event 记录一致。 |
| 4 | Metric | `kube_pod_container_status_restarts_total` | `value: 0` | 表明应用尚未成功启动，排除了运行时资源耗尽导致的重启可能。 |

Kubernetes 事件明确记录了密钥缺失的失败原因，Metric 数据（`CreateContainerConfigError` 状态码、重启数为 0）从系统层面印证了该 Pod 从未进入正常运行阶段，证据相互闭环。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用 Secret 'aiops-case-04/workload-input' 中不存在的密钥 'unavailable-key' → Kubelet 挂载卷失败，触发 'CreateContainerConfigError' → Pod 状态锁定在 'Pending' → 外部表现为 Pod 持续异常且未恢复
```

### 根因结论

已确认的根因为：Pod 配置引用了 Secret `aiops-case-04/workload-input` 中不存在的密钥 `unavailable-key`（证据 #1）。这导致容器无法加载配置，Kubernetes 将其状态锁定在 `Pending` 并持续报错（证据 #2, #3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 18.2s
├─ 并发证据采集: 81.1s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 81.1s (Evidence 73.3s, RCA 7.7s)
└─ 汇总总结: 6.4s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
