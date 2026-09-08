## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-wvcb2 持续处于 CreateContainerConfigError 状态，容器无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-a90908bb02fc` | `Waiting` 消息: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接指出配置校验失败的精确原因：缺少特定 Secret Key |
| 2 | K8s State | `fact-b42d0f9051b1` | `Waiting` 原因: `CreateContainerConfigError` | 定义异常状态类别，表明故障发生于容器启动前的配置解析阶段 |
| 3 | K8s State | `fact-127000c7e7cc` | `Pod` 状态: `Pending` | 反映 Pod 调度成功但因配置错误无法推进到运行状态 |
| 4 | K8s State | `fact-1b7438f66e48` | `Initialized`: `True` | 确证 Pod 的基础环境（容器运行时、存储挂载等）已准备就绪 |
| 5 | Metric | `fact-2f8c69cd585e` | `kube_pod_container_status_waiting_reason` 值为 `1`，且 `reason` 标签为 `CreateContainerConfigError` | 独立于 K8s API 的指标数据，印证了 `CreateContainerConfigError` 状态 |
| 6 | K8s Event | `fact-b74567f81345` | `Pulled` 事件持续 67 分钟 | 证明镜像获取无故障，排除网络或仓库问题，聚焦于本地配置 |
| 7 | K8s Config | `fact-0f3530308393` | 资源配置: `memory_request` 8Mi, `cpu_request` 5m | 资源需求极低，排除因资源不足导致的调度阻塞或 OOM |

**证据印证说明**：
K8s State (1, 2) 与 Metric (5) 高度一致，从控制面和指标面双重确认了 `CreateContainerConfigError` 状态。`Initialized` 状态为 `True` 且镜像拉取事件正常（6），锁定了故障范围在“配置解析”而非“基础设施准备”。具体的错误原文（1）直接关联了 `workload-input` Secret 与缺失的 `unavailable-key`。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用 Secret 'workload-input' 中的 key 'unavailable-key' → Kubelet 校验配置失败，发现 key 缺失 → 抛出 CreateContainerConfigError 异常 → Pod 处于 Pending 且 Container Waiting 状态
```

### 根因结论

**已确认根因：Pod 配置引用了不存在的 Secret Key**

Kubelet 在尝试创建 `aiops-case-04/workload-6584f97c76-wvcb2` 的容器时，发现 Pod 配置中引用了 Secret `aiops-case-04/workload-input` 中的键 `unavailable-key`，但该 Secret 中并未包含此键（见证据 #1）。这一配置错误导致容器引擎拒绝启动容器，从而使得 Pod 停留在 `Pending` 状态（见证据 #3），并持续抛出 `CreateContainerConfigError`（见证据 #2、#5）。

证据链完整：从配置错误的具体信息（Key 缺失）到故障现象（状态机停滞），均有 K8s 原生事件、状态和 Prometheus 指标相互印证，无逻辑断层。

---

## 📊 性能统计

```text
├─ 总耗时: 2.5m
├─ 问题定位: 33.6s
├─ 并发证据采集: 106.7s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 106.7s (Evidence 98.2s, RCA 8.4s)
└─ 汇总总结: 12.1s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
