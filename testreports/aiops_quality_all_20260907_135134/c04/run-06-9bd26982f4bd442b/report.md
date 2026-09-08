## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-7ds5p 处于 Pending 状态，触发 CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubelet (fact-54afbf9ac6e1) | `Warning Failed: Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接指明挂载配置失败的具体缺失资源 |
| 2 | K8s State | Container Status (fact-b5c604c9f085) | Container `app` waiting reason: `CreateContainerConfigError` | 确证 Pod 停滞在容器创建阶段，未进入运行态 |
| 3 | K8s State | Pod Phase (fact-5e44024dbf4c) | Pod phase: `Pending`, status: `Pending` | 验证 Pod 长期处于等待状态，且未发生重启 |
| 4 | Metric | Prometheus (fact-9452da298777) | `kube_pod_container_status_waiting_reason{container="app", reason="CreateContainerConfigError"}` = 1 | 通过监控指标独立印证了容器因配置错误而卡滞的现状 |
| 5 | Metric | Prometheus (fact-cd4af7ae0be9) | `kube_pod_container_status_restarts_total{container="app"}` = 0 | 排除了因 OOM 或 CrashingLoop 导致的大量重启，支持“配置未修正前无法启动”的推断 |

证据分析：
Kubernetes 事件 (fact-1) 直接暴露了根本原因：Secret `aiops-case-04/workload-input` 中不存在键 `unavailable-key`。这直接导致容器无法启动（fact-2, fact-3），并反映在监控系统上，Pod 持续处于 `CreateContainerConfigError` 的 Waiting 状态，且重启计数维持在 0 (fact-4, fact-5)。所有证据指向同一个挂载配置错误，无数据冲突。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置错误引用 Secret 中的键 -> Kubelet 解析 Config 失败 -> CreateContainerConfigError 导致容器无法启动 -> Pod 持续 Pending
```

### 根因结论

已确认根因：**Pod 容器 `app` 的定义中引用了 Secret `aiops-case-04/workload-input` 中不存在的 key `unavailable-key`，导致 Kubelet 挂载配置失败。**

*   **证据支撑**：Kubelet 事件明确指出 `couldn't find key unavailable-key` [fact-1]，容器状态确认为 `CreateContainerConfigError` [fact-2]，监控指标与 Pod 阶段状态完全吻合 [fact-3, fact-4]。
*   **缺失环节说明**：由于 Pod 无法启动，日志与追踪数据不可用 [Logging/Tracing]。但基于现有的 K8s 状态和事件，已能闭环推导故障原因，无需 Pod YAML 或运行时日志即可确证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 23.8s
├─ 并发证据采集: 37.9s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 37.9s (Evidence 29.5s, RCA 8.3s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
