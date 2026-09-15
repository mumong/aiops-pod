## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | ConfigMap aiops-case-v11/workload-input 中缺少 Pod 定义所依赖的 'unavailable-key' 键，导致 kubelet 无法完成容器配置并持续报 CreateContainerConfigError。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `reason=CreateContainerConfigError, message="couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input"` | 确认容器启动失败的直接机制：配置项校验未通过 |
| 2 | K8s Event | Kubernetes | `Event Failed, message="couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input"` (频率: x12 over 58m) | 提供因果候选，证实 kubelet 周期性校验失败 |
| 3 | K8s State | Kubernetes | `pod.status.phase="Pending", condition Ready=False, ContainersReady=False` | 描述现象：Pod 处于挂起且未就绪状态 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"} = 1` | 独立观测：验证了 Pod 持续处于配置报错等待状态 |

**证据说明：**
- K8s Event (fact-076d1bd30fbe) 明确指出缺失 `unavailable-key` 键，导致容器无法启动 (fact-c5cf74e69e5b, fact-cf426129b4eb)。
- Prometheus Metric (fact-2e92632a32e4) 的 `CreateContainerConfigError` 状态与 K8s 事实一致，排除了瞬时网络问题或 API Server 异常，证实该配置问题是持续存在的。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap aiops-case-v11/workload-input 缺少 'unavailable-key' 键 → kubelet 读取配置失败，拒绝启动容器 → 容器持续报错并回退等待 → Pod 状态变为 Pending 且不可用
```

### 根因结论

已确认的根因是：`ConfigMap aiops-case-v11/workload-input` 中缺失了 Pod 定义所依赖的 `unavailable-key` 键。

该缺失导致 `kubelet` 在配置容器环境时失败，触发 `CreateContainerConfigError` 状态（证据 1, 2, 4）。因此，Pod 处于 `Pending` 且未就绪状态（证据 3），服务无法访问。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 24.9s
├─ 并发证据采集: 52.6s
│  └─ g1 aiops-case-v11/workload: 52.6s (Evidence 45.7s, RCA 6.8s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
