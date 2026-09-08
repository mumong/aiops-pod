## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-7ds5p 处于 Pending 状态，容器 reason 为 CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container.waiting_message: "couldn't find key unavailable-key in Secret aiops-case-04/workload-input" | 直接定位缺失配置的具体错误原因 |
| 2 | K8s Event | Kubernetes | event.message: "Warning Failed ... Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input" | 记录 kubelet 持续失败的真实报错（x12 over 29m） |
| 3 | K8s State | Kubernetes | container.waiting_reason: "CreateContainerConfigError" | 确认 Pod 处于配置失败状态，未进入运行阶段 |
| 4 | Metric | Prometheus | kube_pod_container_status_waiting_reason (reason=CreateContainerConfigError): 1 | 独立观测确认异常状态及等待原因 |
| 5 | K8s State | Kubernetes | pod.phase: "Pending" | 确认 Pod 整体处于挂起状态，未调度资源 |

**证据说明**
1. K8s 容器状态（#1, #3）与集群事件（#2）完全一致，均指向对 Secret key 的查找失败。
2. 独立的 Metrics 指标（#4）交叉验证了容器正处于 `CreateContainerConfigError` 状态，排除了单次查询偶发性。
3. 资源配置（请求/限制）与网络状态均正常，无相关异常干扰。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 'workload-input' 缺少 'unavailable-key' 配置 → Pod 容器启动时注入配置失败 → kubelet 抛出 CreateContainerConfigError → Pod 状态维持 Pending，无法就绪
```

### 根因结论

已确认根因为 **Pod 配置引用了不存在的 Secret key**（`unavailable-key`）。
真实原始事实（如 #1, #2）明确显示 kubelet 在容器配置阶段因找不到该 key 而拒绝启动，直接导致容器处于 `CreateContainerConfigError` 等待状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 22.7s
├─ 并发证据采集: 39.2s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 39.2s (Evidence 32.0s, RCA 7.1s)
└─ 汇总总结: 7.1s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error, pod-imagepull-failed
