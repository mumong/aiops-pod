## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod配置引用了Secret 'aiops-case-04/workload-input'中不存在的Key 'unavailable-key'，导致容器配置创建失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning Failed ... Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (fact-cc596530aabf) | 确认容器配置失败的具体原因是 Secret Key 缺失，直接指向配置错误事实 |
| 2 | K8s State | Kubernetes | `pod.status`: `Pending` (fact-d87983e6fef9) | 确认 Pod 停留在调度/启动前的挂起状态，符合配置引用失败的预期阶段 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 值为 `1`，标签 `reason: CreateContainerConfigError` (fact-86bd605dbe3d) | 量化验证 Pod 处于因配置错误导致的等待状态，与 Event 中的错误机制完全吻合 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 值为 `0` (fact-ef07245345ad) | 证明容器从未成功启动过，排除因应用自身崩溃或资源耗尽（OOM）导致的重启可能 |
| 5 | K8s Config | Kubernetes | `resource_request.memory`: `8Mi`, `resource_request.cpu`: `5m` (fact-358a520d6e03, fact-504151e5f975) | 验证资源请求值正常且极低，非资源配额引发的调度或启动障碍 |
| 6 | Topology | Kubernetes | Annotations: `cni.projectcalico.org/containerID: ...` (fact-2b253b4b6250) | 证明网络插件层（Calico）对 Pod 实例有底层响应，故障范围严格限制在 K8s API Server 至 kubelet 的配置拉取环节 |

**证据印证关系：**
Event (fact-cc596530aabf) 明确指出了具体的 Secret Key 缺失错误，Metric (fact-86bd605dbe3d) 从 Prometheus 维度独立确认了等待原因为 `CreateContainerConfigError`。K8s State (fact-d87983e6fef9) 显示为 Pending 且重启计数为 0，逻辑上支持“未尝试启动即失败”的结论，共同排除了运行时资源争用或应用逻辑错误的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
Pod配置引用了不存在的 Secret Key 'unavailable-key' → Kubelet拉取配置失败 → 容器状态设为 CreateContainerConfigError 并挂起(Pending) → 应用无法启动
```

### 根因结论

已确认根因为 **配置引用错误**（Secret Key 不存在）。
Pod `workload-6584f97c76-h4lt9` 尝试引用 Secret `aiops-case-04/workload-input` 中的 Key `unavailable-key` 但失败，导致 kubelet 无法完成容器配置。这一结论由 Kubernetes Event 的直接报错 (fact-cc596530aabf) 以及 Prometheus 监控的 `CreateContainerConfigError` 状态 (fact-86bd605dbe3d) 交叉验证成立，且重启计数为 0 排除了运行时异常。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 14.0s
├─ 并发证据采集: 42.3s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 42.3s (Evidence 37.7s, RCA 4.6s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
