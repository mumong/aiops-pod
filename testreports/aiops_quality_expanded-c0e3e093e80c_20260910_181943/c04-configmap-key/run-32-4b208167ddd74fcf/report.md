## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod `workload` 的容器配置引用了 ConfigMap `aiops-case-v11/workload-input` 中的 key `unavailable-key`，但该 ConfigMap 中实际不存在此 key，导致 kubelet 挂载环境变量失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: reason="CreateContainerConfigError" | 确认容器因配置错误无法启动 |
| 2 | K8s Event | kubernetes | `event.message`: Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input | 直接定位缺失资源的具体路径与属性 |
| 3 | K8s State | kubernetes | `container.waiting_message`: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input | 提供与 Event 一致的错误详情 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason`=1 (label: reason="CreateContainerConfigError", container="app") | 外部指标验证了容器的等待状态与原因 |
| 5 | Metric | prometheus | `kube_pod_status_phase`=1 (label: phase="Pending") | 确认 Pod 整体处于 Pending 阶段，未进入运行态 |

**证据小结**：
Kubernetes 的 Event 与 Container State 提供了完全一致的文本证据（#2, #3），指出 `workload` Pod 因无法挂载 `aiops-case-11/workload-input` ConfigMap 中的 `unavailable-key` 而失败。Prometheus 指标 (#4, #5) 在数值上同步反映了这一状态，佐证了 Pod 处于 `Pending` 且容器处于 `CreateContainerConfigError` 等待中。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 配置遗漏 key → 环境变量挂载失败 → 容器启动失败 (CreateContainerConfigError) → Pod 处于 Pending 状态
```

### 根因结论

已确认的根因：`workload` Pod 的容器配置引用了 ConfigMap `aiops-case-11/workload-input` 中并不存在的 key `unavailable-key`。
**支撑证据**：
- `CreateContainerConfigError` 状态及具体失败信息来自事实 #2, #3。
- 该错误直接导致容器无法初始化，表现为事实 #1, #4, #5 中的状态指标。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 15.9s
├─ 并发证据采集: 38.9s
│  └─ g1 aiops-case-v11/workload: 38.9s (Evidence 31.5s, RCA 7.2s)
└─ 汇总总结: 7.5s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
