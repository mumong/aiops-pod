## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod `workload-6584f97c76-7ds5p` 配置中引用了 Secret `aiops-case-04/workload-input` 中名为 `unavailable-key` 的字段，但该 Secret 中不存在此键，导致 kubelet 无法完成容器配置并触发 `CreateContainerConfigError`。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` 处于 `waiting` 状态，原因 `CreateContainerConfigError`，等待消息提示 `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (`fact-3dc922998180`) | 直接指向 kubelet 因缺少 Secret 密钥而无法完成容器配置的确切原因 |
| 2 | K8s Event | Kubernetes | 26m 内持续触发 Warning 事件，明确报错 `Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (`fact-d8052c77ec58`) | 提供了配置缺失的实时且重复的外部验证，确认该问题导致 Pod 长时间处于 Pending 状态 |
| 3 | K8s State | Kubernetes | Pod 阶段为 `Pending`，条件 `ContainersReady` 和 `Ready` 均为 `False`，因为容器 `app` 处于未就绪状态 (`fact-1558cf1e28d3`, `fact-9f12380a6772`) | 确认了异常状态的实际表现：Pod 因底层配置错误被调度器/节点拒绝启动 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 在 10:01:08 采集值为 `1`，标签 `reason=CreateContainerConfigError` (`fact-32036dcb2b38`) | 时序指标数据与 K8s API 的报错原因精准匹配，排除了瞬态网络或节点故障的可能性 |

上述证据形成了闭环：Prometheus 监控捕捉到了持续存在的 `CreateContainerConfigError` 指标，这与 K8s API 中报告的容器状态及重复触发的事件日志完全一致。核心错误信息 `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` 在所有维度间高度统一，明确指向 Secret 配置中的缺失键值问题。

## 🎯 根因分析 · g1

### 因果链

```text
Secret `aiops-case-04/workload-input` 中缺失键 `unavailable-key` → kubelet 在拉取和注入挂载卷/环境变量时校验失败 → 容器无法通过启动前置检查 → Pod 处于 Pending 状态并触发 CreateContainerConfigError
```

### 根因结论

已确认根因：Pod `workload-6584f97c76-7ds5p` 的容器配置引用了 Secret `aiops-case-04/workload-input` 中并不存在的字段 `unavailable-key`。
这一配置级错误导致 kubelet 无法完成容器的创建配置。该结论由直接报错信息（`fact-3dc922998180`, `fact-d8052c77ec58`）、异常状态（`CreateContainerConfigError`）、以及同步的 Prometheus 监控指标（`fact-32036dcb2b38`）相互印证，证据链完整且无冲突。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 22.0s
├─ 并发证据采集: 31.5s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 31.5s (Evidence 26.0s, RCA 5.4s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
