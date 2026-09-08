## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | aiops-case-04/workload-6584f97c76-7ds5p 处于 CreateContainerConfigError 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-e60caf5f99e8` | `Pod Pending` | 确认 Pod 处于未运行状态，未发生重启 |
| 2 | K8s Event | `fact-3845af9e156e` | `CreateContainerConfigError`：`Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 明确指出容器配置阶段因 Secret key 缺失导致挂载失败 |
| 3 | Metric | `fact-d2a5ca826475` | `kube_pod_container_status_waiting_reason = 1` (reason=`CreateContainerConfigError`) | 独立观测确认容器状态为 `CreateContainerConfigError` |
| 4 | Metric | `fact-4130ea5884e5` | `kube_pod_status_phase = 1` (phase=`Pending`) | 确认 Pod 整体处于 `Pending` 阶段 |

**证据说明：**
- 维度 1 (K8s Event) 和 维度 3 (Metric) 互相印证了确切的错误原因（找不到 `unavailable-key`）和容器状态（`CreateContainerConfigError`）。
- 维度 1 的 `CreateContainerConfigError` 直接解释了维度 2 中 Pod 处于 `Pending` 且重启次数为 0 的现象（因为 Pod 甚至无法启动到容器运行阶段）。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用了不存在的 Secret key → kubelet 在挂载 Volume 时找不到 key → 容器启动失败（CreateContainerConfigError） → Pod 处于 Pending 状态
```

### 根因结论

已确认根因：**Pod 的 Spec 定义中引用了 Secret `aiops-case-04/workload-input` 中的 key `unavailable-key`，但该 key 在 Secret 中实际并不存在。**

这一不存在的 Secret key 导致 kubelet 无法完成配置挂载，进而直接引发容器启动失败（`CreateContainerConfigError`），使 Pod 停留在 `Pending` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 56.5s
├─ 问题定位: 20.2s
├─ 并发证据采集: 28.9s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 28.9s (Evidence 23.3s, RCA 5.4s)
└─ 汇总总结: 7.4s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
