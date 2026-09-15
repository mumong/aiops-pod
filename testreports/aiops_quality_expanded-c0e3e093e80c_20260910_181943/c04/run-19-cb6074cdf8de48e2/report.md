## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod workload-6584f97c76-h4lt9 的 spec 中引用了 Secret aiops-case-04/workload-input 中的 key 'unavailable-key'，但该 Secret 中实际并不包含此 key，导致 kubelet 创建容器失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_message`: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (fact-1cb29865d19d) | 明确指认 kubelet 在创建容器时，因找不到指定的 Secret Key 而失败。 |
| 2 | K8s Event | Kubernetes | `event.message`: `Warning Failed ... kubelet Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (fact-d4a820dbac3a) | 佐证 kubelet 诊断结果，确认该错误发生在 29 分钟前并持续发生。 |
| 3 | K8s State | Kubernetes | `container.waiting_reason`: `CreateContainerConfigError` (fact-ddc6ac2b000d) | 定义 Pod 容器状态为配置阶段失败，与“找不到 Key”的报错直接对应。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (reason=`CreateContainerConfigError`, value=`1`, fact-2943cd7fa185) | 独立观测数据确认容器处于 `CreateContainerConfigError` 等待状态。 |

**证据印证说明：**
- K8s 原生事实（#1, #2, #3）从容器消息、事件日志和等待原因三个角度一致锁定错误为“Secret Key 缺失”。
- Prometheus 指标（#4）在维度 `CreateContainerConfigError` 上的值为 1，与 K8s 状态互相印证，排除了瞬时抖动导致状态不一致的可能。
- 其他指标（Phase=PENDING, Restarts=0）与“配置未通过、容器未启动”的现象完全一致。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 错误引用 Secret key 'unavailable-key' → Secret 'workload-input' 中实际缺少该 key → kubelet 抛出 'couldn't find key' 错误 → Pod 处于 CreateContainerConfigError 状态且无法启动
```

### 根因结论

**已确认的根因：** Pod `workload-6584f97c76-h4lt9` 的 spec 中硬编码或引用了 Secret `aiops-case-04/workload-input` 中并不存在的 key `unavailable-key`。

**证据关联：**
- 核心证据来自 kubelet 的诊断报告（#1, #2），直接指出 `couldn't find key unavailable-key in Secret aiops-case-04/workload-input`。
- 该错误导致容器初始化配置阶段直接失败（#3, #4），表现为 Pod 永久处于 `Pending` 且容器等待原因为 `CreateContainerConfigError`。

**未知信息：**
- 该 key `unavailable-key` 原本应当存在于哪里，是配置更新遗漏还是误删除，现有事实不足以判定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.7s
├─ 并发证据采集: 39.6s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 39.6s (Evidence 31.0s, RCA 8.5s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
