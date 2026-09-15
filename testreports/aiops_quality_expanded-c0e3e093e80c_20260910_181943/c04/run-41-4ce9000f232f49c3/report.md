## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Secret aiops-case-04/workload-input 缺少 Pod 挂载配置所需的 key 'unavailable-key' |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: container "app" 状态为 `CreateContainerConfigError` (fact-3b35b442f836) | 直接确认容器启动失败的具体机制 |
| 2 | K8s State | kubernetes | `container.waiting_message`: container "app" 报错 "couldn't find key unavailable-key in Secret aiops-case-04/workload-input" (fact-ee78aef0a795) | 锁定导致配置失败的缺失对象及具体缺失字段 |
| 3 | K8s State | kubernetes | `pod.status`: 状态为 `Pending` (fact-06d549b27d7a, fact-f2addf3a9666) | 证实 Pod 因无法完成配置验证而未调度进入运行阶段 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"}`: 当前值为 1 (fact-239ae7a17745) | 监控数据与 Kubernetes 状态一致，确认该异常目前仍在持续 |
| 5 | K8s State | kubernetes | `pod.condition` (Ready, ContainersReady): `False`，原因 `ContainersNotReady` (fact-55d317a4c132, fact-cf33c8b665de) | 证实 Pod 未能就绪，排除了运行后崩溃的可能性 |

**证据说明：**
Kubernetes 的容器状态 (fact-3b35b442f836)、错误详情 (fact-ee78aef0a795) 与 Pod 阶段状态 (fact-06d549b27d7a) 共同指向一个单一的根因：镜像拉取成功后，kubelet 在验证 Secret 挂载配置时失败。Metric 数据 (fact-239ae7a17745) 作为独立的实时观测，确认了这一状态并非瞬态。由于容器在配置阶段即中止，Logging 和 Tracing 维度因无容器进程运行而不可用，这符合 `CreateContainerConfigError` 的物理特征。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 'workload-input' 中只包含 key 'available-key' → Pod 容器 'app' 配置要求挂载 Secret key 'unavailable-key' → kubelet 无法找到所需的 key 导致配置失败 → Pod 状态卡在 CreateContainerConfigError
```

### 根因结论

已确认的根因为：**Secret `aiops-case-04/workload-input` 缺少 Pod 挂载配置所需的 key `unavailable-key`**。

证据编号 2 (fact-ee78aef0a795) 明确指出了失败原因是“找不到 key unavailable-key”。该缺失导致 kubelet 无法完成容器的配置阶段验证，从而引发 `CreateContainerConfigError`，使 Pod 停留在 Pending 状态且无法进入运行环境。当前证据链完整且逻辑闭环，足以支撑该结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 19.0s
├─ 并发证据采集: 36.7s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 36.7s (Evidence 30.5s, RCA 6.0s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
