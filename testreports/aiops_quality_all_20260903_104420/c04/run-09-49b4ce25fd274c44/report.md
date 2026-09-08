## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod yaml配置引用了Secret 'aiops-case-04/workload-input'中不存在的key 'unavailable-key'（该Secret实际仅包含'available-key'），导致kubelet在创建容器前无法解析配置，从而触发CreateContainerConfigError。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: "CreateContainerConfigError" | 确认异常类别为配置缺失导致的容器启动阻断 |
| 2 | K8s State | Kubernetes | `container.waiting_message`: "couldn't find key unavailable-key in Secret aiops-case-04/workload-input" | 定位具体缺失的资源标识符 |
| 3 | K8s Event | Kubernetes | Event `Warning Failed`: "couldn't find key unavailable-key in Secret aiops-case-04/workload-input" (x12 over 13m) | 持续重复发生的调度失败事实，印证配置解析错误 |
| 4 | K8s State | Kubernetes | `pod.status`: "Pending" | 确认 Pod 停留在预启动阶段，未进入运行或重启循环 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (reason: "CreateContainerConfigError"): 1 | 独立监控指标确认容器处于等待状态 |

以上 Kubernetes 事实（1, 2, 3, 4）与 Prometheus 指标（5）在“配置缺失导致容器处于 Waiting 状态”这一结论上完全一致，共同支撑根因判断。Logging/Tracing 因容器未启动而缺失，但不影响基于控制平面状态的定界。

## 🎯 根因分析 · g1

### 因果链

```text
Pod YAML 中引用了不存在的 Secret Key 'unavailable-key' (fact-2) 
  → Kubelet 创建容器前无法解析 Secret 配置 (fact-1, fact-3) 
  → 触发 CreateContainerConfigError (fact-1, fact-5) 
  → Pod 状态变为 Pending (fact-4)
```

### 根因结论

已确认根因：Pod `aiops-case-04/workload-6584f97c76-wvcb2` 的 YAML 配置引用了 Secret `aiops-case-04/workload-input` 中不存在的 Key `unavailable-key`（事实 2），导致 Kubelet 在容器创建阶段无法解析环境变量或卷挂载配置，直接抛出 `CreateContainerConfigError`（事实 1）。这一配置错误导致容器无法启动，Pod 持续保持在 `Pending` 状态（事实 4），且 Prometheus 监控指标（事实 5）确认了该等待状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 19.0s
├─ 并发证据采集: 52.2s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 52.2s (Evidence 45.9s, RCA 6.1s)
└─ 汇总总结: 8.3s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
