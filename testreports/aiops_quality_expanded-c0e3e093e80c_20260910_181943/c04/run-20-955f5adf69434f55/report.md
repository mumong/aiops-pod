## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod workload-6584f97c76-h4lt9 处于 Pending 状态，容器启动失败，状态为 CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Failed Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (fact-ae5bca49befc) | 确认错误根源：Secret 中缺失指定的 Key |
| 2 | K8s State | kubernetes | 容器 'app' waiting reason 为 `CreateContainerConfigError`，消息为 `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (fact-81fde815a791, fact-d45fb077005c) | 容器创建阶段因配置错误直接阻断 |
| 3 | K8s State | kubernetes | Pod phase 为 `Pending`，条件 `ContainersReady` 为 `False`，原因 `ContainersNotReady` (fact-ba169b995669, fact-a236d7741652) | 验证 Pod 未进入 Ready 状态，处于挂起状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值 1，标签 `reason: "CreateContainerConfigError"` (fact-054b6e88eb30) | 指标数据佐证容器处于配置错误等待状态 |

**证据关联与印证说明：**
- 证据 #1 (Event) 提供了具体的失败原因（找不到 Secret 的 key），直接解释了证据 #2 (Container State) 中 `CreateContainerConfigError` 的发生机制。
- 证据 #3 (Pod Phase) 和证据 #4 (Metric) 分别从 Pod 生命周期的宏观状态和监控指标两个维度，确认了容器启动失败导致的 Pending 状态，与 K8s 事件和容器状态完全一致。

## 🎯 根因分析 · g1

### 因果链

```text
Secret aiops-case-04/workload-input 缺少 key 'unavailable-key' (触发) 
→ Kubelet 在创建容器时无法解析 Secret key 引用 (机制) 
→ 容器创建阶段报错 CreateContainerConfigError (直接失败) 
→ Pod 持续处于 Pending 状态，容器启动失败 (用户可见现象)
```

### 根因结论

已确认的根因为 **Pod 配置的 Container 尝试挂载 Secret `aiops-case-04/workload-input` 中的 key `unavailable-key`，但该 Secret 中不存在此 key**。

证据 #1 (K8s Event) 明确指出 `couldn't find key unavailable-key in Secret aiops-case-04/workload-input`，这直接导致了证据 #2 中容器状态变为 `CreateContainerConfigError`。该配置错误阻止了容器的创建，从而引起证据 #3 中 Pod 状态停留在 `Pending`。证据 #4 的监控指标进一步固化了这一状态的持续时间。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 18.4s
├─ 并发证据采集: 45.2s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 45.2s (Evidence 36.4s, RCA 8.7s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
