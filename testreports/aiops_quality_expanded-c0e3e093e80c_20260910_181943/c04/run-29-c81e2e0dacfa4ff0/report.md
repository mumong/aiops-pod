## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-h4lt9 处于 CreateContainerConfigError 状态，容器无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning Failed: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (fact-39ae5595215b) | 核心根因：明确指出了 Pod 配置引用了不存在的 Secret Key |
| 2 | K8s State | Kubernetes | `container.waiting_reason: CreateContainerConfigError` (fact-3c816bc63a15) | 直接失败状态：验证容器因配置缺失无法启动 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 值为 `1`，标签 `reason: CreateContainerConfigError` (fact-70bd06a06984) | 独立观测：与 K8s 状态确认，排除了其他 Waiting 原因 |
| 4 | K8s Config | Kubernetes | 资源请求限制：CPU Req `5m`, Limit `50m`；Memory Req `8Mi`, Limit `32Mi` (fact-818da2d378e3, fact-a97321678c64) | 上下文：证实 Pod 资源请求极低，非资源耗尽导致的调度失败 |
| 5 | K8s State | Kubernetes | `phase: Pending`, `ContainersNotReady` (fact-1c41b58fa1c5, fact-97beac12c32f) | 用户可见现象：Pod 处于不可用状态，与报错原因一致 |

**证据说明：**
Kubernetes 事件与状态直接指向了 Secret Key 缺失 (`fact-1, fact-2`)。Prometheus 指标以独立的系统视角复现了相同的 `CreateContainerConfigError` 状态 (`fact-3`)，证实了故障并非偶发的 API 波动，而是持续存在的配置错误。资源配置极低 (`fact-4`) 且重启次数为 0 (`fact-236513646050`)，进一步排除了资源争用或 OOM 的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用了不存在的 Secret Key ('unavailable-key') → Kubelet 拉取配置失败 → 容器启动报错 CreateContainerConfigError → Pod 保持 Pending/Unready 状态
```

### 根因结论

已确认根因为 **Pod 配置引用了不存在的 Secret Key**。

Kubelet 在尝试根据 Pod 的 Volume/Env 挂载配置拉取 `aiops-case-04/workload-input` Secret 时，找不到所需的 `unavailable-key`，导致容器化流程中断，抛出 `CreateContainerConfigError`。此结论被 K8s 事件 (`fact-1`)、容器状态 (`fact-2`) 以及 Prometheus 指标 (`fact-3`) 多重印证。

---

## 📊 性能统计

```text
├─ 总耗时: 54.0s
├─ 问题定位: 15.2s
├─ 并发证据采集: 29.1s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 29.1s (Evidence 22.0s, RCA 7.0s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
