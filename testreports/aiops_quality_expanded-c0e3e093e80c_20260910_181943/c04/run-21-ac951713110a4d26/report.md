## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod workload-6584f97c76-h4lt9 持续处于 CreateContainerConfigError 状态，容器未启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning Failed`：`Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 揭示容器启动失败的直接原因 |
| 2 | K8s State | Kubernetes | Pod 处于 `Pending`，`ContainersReady` 为 `False`，原因 `ContainersNotReady` | 确认 Pod 当前状态及阻碍就绪的条件 |
| 3 | K8s State | Kubernetes | 容器 `app` 等待原因为 `CreateContainerConfigError`，信息为 `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 将 K8s 事件映射到具体容器的配置错误 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="CreateContainerConfigError"}` 值为 `1` | 从指标侧印证容器一直处于配置错误状态 |

**证据说明：**
Kubernetes 事件（#1）与容器状态（#2、#3）高度一致，均明确指出了导致 `CreateContainerConfigError` 的具体缺失密钥 `unavailable-key` 及其所在的 Secret 名称。Metric 数据（#4）作为辅助观测，证实了该异常状态在 Prometheus 采集窗口内持续存在。由于 Pod 未进入运行状态，Logging 与 Tracing 采集为 `not_applicable`，但 K8s 原生状态已构成完整的闭环证据链。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 'aiops-case-04/workload-input' 中缺失 Pod 期望的密钥 'unavailable-key' → kubelet 注入配置失败 → 容器启动流程阻塞 → Pod 持续处于 CreateContainerConfigError 状态
```

### 根因结论

**已确认的根因：**
Pod `workload-6584f97c76-h4lt9` 的 `app` 容器定义了缺失的密钥引用 `unavailable-key`，且该密钥未存在于其引用的 Secret `aiops-case-04/workload-input` 中。Kubelet 在尝试创建容器因无法获取配置密钥而抛出错误（引用证据 #1、#3），导致 Pod 停留在 `Pending` 状态且无法启动（引用证据 #2、#4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 14.8s
├─ 并发证据采集: 39.8s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 39.8s (Evidence 30.4s, RCA 9.3s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
