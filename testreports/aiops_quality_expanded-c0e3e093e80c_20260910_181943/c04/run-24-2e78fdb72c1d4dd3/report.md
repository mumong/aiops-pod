## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubelet 事件 | `Warning Failed ... couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (46m 内发生 12 次) | 直接指向配置引用错误 |
| 2 | K8s State | Pod 状态 | 容器 `app` 处于 `CreateContainerConfigError` 状态 | 确认容器创建阶段失败 |
| 3 | K8s State | 等待消息 | `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 复述失败的具体原因 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"}` 值为 `1` | 量化了容器处于等待错误状态 |

**证据关联说明**：
Kubernetes 事件 (#1)、容器状态 (#2) 与等待消息 (#3) 共同确证了根因细节；Metric 数据 (#4) 独立印证了该异常状态当前仍处于活跃。因容器未启动，Logging 和 Tracing 均返回 `not_applicable`。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用了 Secret aiops-case-04/workload-input 中不存在的 key 'unavailable-key' → 容器运行时无法解析环境变量配置 → kubelet 拒绝创建容器并返回 CreateContainerConfigError → Pod 保持 Pending/Waiting 状态
```

### 根因结论

已确认的根因是 **Pod 配置引用了 Secret `aiops-case-04/workload-input` 中不存在的 key `unavailable-key`**，导致容器无法启动。
- **证据支撑**：该结论由 Kubernetes 事件 (#1) 明确报出，并与容器状态 (#2)、等待消息 (#3) 及 Prometheus 等待指标 (#4) 互为印证。
- **排除项**：其他维度（Logging/Tracing）因容器未启动而无数据，但现有 K8s 证据链已完整覆盖故障机理，无需补充。

---

## 📊 性能统计

```text
├─ 总耗时: 59.2s
├─ 问题定位: 15.3s
├─ 并发证据采集: 36.7s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 36.7s (Evidence 30.1s, RCA 6.5s)
└─ 汇总总结: 7.3s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
