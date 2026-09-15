## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod aiops-case-v11/workload 的容器配置引用了 ConfigMap 'workload-input' 中不存在的 key 'unavailable-key'，导致 kubelet 无法完成容器环境配置 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Warning Failed ... Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` (x12 over 56m) | 直接指示容器配置失败的具体缺失项 |
| 2 | K8s State | container.status | container "app": waiting_reason="CreateContainerConfigError", message="couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input" | 固化了容器因配置缺失无法启动的状态 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="CreateContainerConfigError"} = 1` | 外部指标观测到与 K8s 状态一致的等待原因 |
| 4 | K8s State | pod.status | phase="Pending", condition="Ready=False" | 确认 Pod 因容器未就绪而处于 Pending 状态 |

上述证据互相印证：Kubernetes 控制平面（Event/State）明确指出了失败的原因为 ConfigMap 密钥缺失（fact-aa7dfe48d868, fact-c72d9d3e5b41），Metrics 数据从外部视角确认了这一特定的等待原因（fact-c83f8f9b23e8）。由于容器始终无法启动（waiting_reason=CreateContainerConfigError），因此无 Logging 和 Tracing 数据产生，符合物理限制。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'aiops-case-v11/workload-input' 缺失 key 'unavailable-key' → Kubelet 无法完成容器环境配置 → Container 处于 CreateContainerConfigError 状态 → Pod 保持 Pending 且不可用
```

### 根因结论

已确认根因为：Pod `aiops-case-v11/workload` 的容器配置引用了 ConfigMap `workload-input` 中不存在的 key `unavailable-key`。

这一配置错误导致 `kubelet` 在尝试启动容器 `app` 时失败，进而使容器进入 `CreateContainerConfigError` 状态。证据链闭环如下：
1. **Kubernetes 事件与状态**直接记录了具体的错误信息（找不到 key），排除了资源不足、调度失败或网络问题。
2. **Metric 数据**通过 `kube_pod_container_status_waiting_reason` 独立验证了该错误原因。
3. 容器因配置问题从未进入运行状态，故无应用日志或 Trace 可提供辅助证据，但这并不影响根因判定的唯一性。

---

## 📊 性能统计

```text
├─ 总耗时: 59.5s
├─ 问题定位: 16.1s
├─ 并发证据采集: 34.7s
│  └─ g1 aiops-case-v11/workload: 34.7s (Evidence 30.3s, RCA 4.3s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
