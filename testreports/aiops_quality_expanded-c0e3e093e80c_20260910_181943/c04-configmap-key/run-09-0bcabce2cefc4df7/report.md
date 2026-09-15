## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod aiops-case-v11/workload处于Pending状态且持续报错CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Failed (x12 over 26m) kubelet Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 明确指向导致容器配置失败的 ConfigMap 缺失键名 |
| 2 | K8s State | kubernetes | `container.waiting_reason: CreateContainerConfigError` (Container: app) | 标识容器因配置错误无法启动的核心状态 |
| 3 | K8s State | kubernetes | `container.waiting_message: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 直接引用底层错误信息，印证挂载失败原因 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1` (Container: app, Reason: CreateContainerConfigError, Value: 1) | 持续监控数据确认容器处于该错误状态未恢复 |

日志和追踪维度无有效数据，原因是容器始终处于 Pending 状态，未能启动并产生应用日志或流量记录。K8s 状态、事件与监控数据高度一致，共同证实了配置缺失导致的启动阻断。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 引用不存在的 ConfigMap 键 'unavailable-key' (事实: 1, 3) 
→ kubelet 读取配置失败，抛出 CreateContainerConfigError (事实: 1, 2) 
→ 容器无法启动，Pod 维持在 Pending 状态 (事实: 2, 4) 
→ 应用不可用，服务无法提供
```

### 根因结论

**根因已确认**：Pod `aiops-case-v11/workload` 的容器配置中引用了 ConfigMap `aiops-case-v11/workload-input` 的键 `unavailable-key`，但该键实际不存在。这一配置错误直接触发了 kubelet 的配置挂载失败，导致容器始终处于 `CreateContainerConfigError` 等待状态（见事实 #1、#2、#3）。

现有 K8s 状态、事件及监控指标（#4）已完整支撑该结论，无需补充其他维度的证据即可定论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 22.2s
├─ 并发证据采集: 47.5s
│  └─ g1 aiops-case-v11/workload: 47.5s (Evidence 39.6s, RCA 7.8s)
└─ 汇总总结: 7.7s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
