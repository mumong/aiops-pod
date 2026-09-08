## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-wvcb2 处于 CreateContainerConfigError 状态，Container 无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: `CreateContainerConfigError` (container: app) | 确认 Pod 处于配置错误状态，无法启动 |
| 2 | K8s Event | kubernetes | `Warning Failed ... Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接指出错误原因为 Secret 中缺失指定 Key |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError", container="app"}` = 1 | 从指标维度证实 Pod 持续处于配置错误的等待状态 |
| 4 | Metric | prometheus | `kube_pod_status_phase{phase="Pending", container="app"}` = 1 | 证实 Pod 生命周期停滞在 Pending 阶段 |
| 5 | K8s State | kubernetes | `pod.condition Ready=False`, `ContainersReady=False` (reason: ContainersNotReady) | 辅助证明容器未被成功启动并准备就绪 |

**证据说明：**
Kubernetes 的等待状态和事件日志提供了确凿的错误原因，即挂载配置中引用的 Secret Key 不存在；Metrics 的 Waiting Reason 和 Phase 指标在数值上同步反映了 Pod 处于同一停滞状态。两者互相印证了“配置错误导致容器无法启动”的事实，无需依赖未能成功采集的 Logging 和 Tracing 数据。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用了不存在的 Secret Key 'unavailable-key' → Kubelet 挂载 Secret 时找不到指定 Key → 触发 CreateContainerConfigError → Pod 持续处于 Pending 状态
```

### 根因结论

已确认根因为 **Pod 的挂载配置错误**。

部署配置中显式指定了挂载 Secret `aiops-case-04/workload-input` 中的 Key `unavailable-key`，但该 Secret 对象中并未定义此 Key（实际仅包含 `available-key`）。导致 Kubelet 在尝试启动容器时，因无法解析挂载配置而直接报错 `CreateContainerConfigError`，致使 Pod 无法进入 Running 状态 [证据 #1, #2]。

---

## 📊 性能统计

```text
├─ 总耗时: 10.5m
├─ 问题定位: 20.1s
├─ 并发证据采集: 600.3s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 600.3s (Evidence 592.6s, RCA 7.5s)
└─ 汇总总结: 7.7s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
