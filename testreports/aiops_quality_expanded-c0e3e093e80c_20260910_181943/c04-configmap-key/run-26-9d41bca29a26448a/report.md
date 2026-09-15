## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod workload 处于 CreateContainerConfigError 状态，容器未启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason: CreateContainerConfigError` (fact-628d88f8f80f) | 确定容器因配置加载失败而无法启动 |
| 2 | K8s State | kubernetes | `container.waiting_message: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` (fact-0c3abdb4d851) | 指出确切的缺失资源及标识 |
| 3 | K8s Event | kubernetes | `Warning Failed ... Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` (fact-8c33ccddf8cf) | 确认 kubelet 在运行时实际遇到的错误 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"} = 1` (fact-d7f5c11da3b3) | 监控侧确认等待状态持续存在 |

**证据说明**：
Kubernetes 的 Pod 状态 (`CreateContainerConfigError`) 与事件日志 (`couldn't find key...`) 高度一致，Metric 监控数据进一步佐证了该错误状态的持续性。Logging 与 Tracing 因容器未启动而无效，当前 Kubernetes 事实链已完整支撑根因判定。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap aiops-case-v11/workload-input 缺少 key 'unavailable-key' → Pod 注入环境变量失败 → kubelet 拒绝创建容器 → Pod 处于 CreateContainerConfigError 状态
```

### 根因结论

**已确认的根因**：
Pod `aiops-case-v11/workload` 的 Spec 中引用了 ConfigMap `aiops-case-v11/workload-input` 中的 key `unavailable-key`，但该 key 实际上并不存在于 ConfigMap 中。

**证据支撑**：
- 容器等待状态明确显示原因为 `CreateContainerConfigError` (证据 #1)。
- 等待消息和 Kubernetes 事件均直接报错 `couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` (证据 #2, #3)。
- Prometheus 指标确认该等待状态正在持续 (证据 #4)。

---

## 📊 性能统计

```text
├─ 总耗时: 59.8s
├─ 问题定位: 16.3s
├─ 并发证据采集: 35.4s
│  └─ g1 aiops-case-v11/workload: 35.4s (Evidence 25.7s, RCA 9.6s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
