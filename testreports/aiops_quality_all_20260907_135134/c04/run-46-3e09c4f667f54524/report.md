## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-7ds5p 处于 CreateContainerConfigError 状态，容器无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-04/workload-6584f97c76-7ds5p` 状态 `Pending`；容器 `app` 状态 `CreateContainerConfigError` | 确立异常实体与当前阻塞状态 |
| 2 | K8s Event | kubernetes | `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 定位配置错误的直接原因 |
| 3 | K8s State | kubernetes | Pod Condition `ContainersNotReady` (原因: `ContainersNotReady`) | 确认 Pod 无法进入就绪状态 |
| 4 | K8s Config | kubernetes | 容器 `app` 资源 Request: CPU `5m`, Memory `8Mi`；Limit: CPU `50m`, Memory `32Mi` | 确认容器配置（非资源超限） |
| 5 | K8s Event | kubernetes | 事件 `Pulled` 记录 325 次 (70m内)，镜像 `xnet.registry.io:8443/observability/python:3-alpine` | 排除镜像拉取阶段的问题 |
| 6 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 记录值 `1` (label: reason=`CreateContainerConfigError`) | 验证配置错误导致的容器等待状态 |
| 7 | Metric | prometheus | `kube_pod_status_phase` 记录值 `1` (label: phase=`Pending`) | 确认 Pod 整体生命周期阶段 |
| 8 | Metric | prometheus | `kube_pod_container_status_restarts_total` 记录值 `0` | 确认异常处于初始阶段，未发生重启循环 |

**证据说明：**
Kubernetes 状态与事件（事实 1-3）直接揭示了故障现象与具体的 Secret 键缺失错误；Metric 数据（事实 6-8）从可观测性维度独立印证了容器处于 `CreateContainerConfigError` 等待状态且无重启记录，排除了间歇性故障或资源竞争。镜像拉取事件（事实 5）确认了问题发生在挂载配置阶段而非基础镜像获取阶段。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用了 Secret aiops-case-04/workload-input 中不存在的 key 'unavailable-key' → Kubelet 挂载 Secret 环境变量失败 → 容器无法创建 (CreateContainerConfigError) → Pod 保持 Pending 状态且未重启
```

### 根因结论

**已确认的根因：**
Pod `aiops-case-04/workload-6584f97c76-7ds5p` 的容器配置中引用了 Secret `aiops-case-04/workload-input` 中的密钥 `unavailable-key`，但该密钥在 Secret 中实际不存在。

**证据支撑：**
- Kubernetes 事件明确提示 `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (事实 2)；
- Pod 状态为 `CreateContainerConfigError` (事实 1, 6)；
- 排除资源不足 (事实 4) 及镜像拉取失败 (事实 5) 等其他原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 16.5s
├─ 并发证据采集: 41.9s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 41.9s (Evidence 35.2s, RCA 6.6s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
