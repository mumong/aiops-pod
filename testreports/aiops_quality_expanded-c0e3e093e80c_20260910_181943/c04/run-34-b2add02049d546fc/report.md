## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod配置中引用的Secret 'aiops-case-04/workload-input'中缺少容器所需的键' unavailable-key' |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-04/workload-6584f97c76-h4lt9` 状态 `Pending`，条件 `ContainersReady` 为 `False` (fact-32c9a1ab474b, fact-595285b5eda7) | 描述 Pod 处于停滞状态，未进入运行态 |
| 2 | K8s Config | Kubernetes | 容器 `app` 报错：`CreateContainerConfigError` (fact-9e16353c442d) | 指出具体的容器启动失败原因类型 |
| 3 | K8s Config | Kubernetes | 错误详情：`couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (fact-4bd91224a5f1) | 精确定位缺失的资源键，指向 Secret 配置问题 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 值为 `1`，标签 `reason` 为 `CreateContainerConfigError` (fact-e6dd4ee0b39b) | 独立确认容器因配置错误而等待，与 K8s 事件状态一致 |

**证据印证：**
Kubernetes 状态的 `CreateContainerConfigError` 与 Prometheus 监控中对应的 `waiting_reason` 相互印证，共同确认故障发生在 Pod 初始化的配置检查阶段。错误信息明确指出了缺失的 Secret 键，属于静态配置错误，因此日志和追踪维度（Logging/Tracing）均为 `not_applicable` 符合预期。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 中引用 Secret 'aiops-case-04/workload-input' 缺失键 'unavailable-key' → K8s kubelet 启动容器前校验失败 (CreateContainerConfigError) → 容器无法创建 (Waiting状态) → Pod 处于 Pending 且不可用
```

### 根因结论

已确认根因为：**Pod 配置错误导致 Secret 键缺失**。

Kubernetes 组件直接返回了明确的错误事实 `fact-4bd91224a5f1`，指出容器 `app` 在加载 `Secret aiops-case-04/workload-input` 时找不到所需的键 `'unavailable-key'`。此配置校验失败直接触发了 `CreateContainerConfigError` 状态，阻止了容器的启动，表现为 Pod 处于 `Pending` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 21.0s
├─ 并发证据采集: 31.4s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 31.4s (Evidence 27.3s, RCA 4.0s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
