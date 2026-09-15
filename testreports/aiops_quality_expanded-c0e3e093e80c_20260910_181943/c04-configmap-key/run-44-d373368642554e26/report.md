## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod aiops-case-v11/workload 处于 Pending 阶段，容器 app 报错 CreateContainerConfigError。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.app.reason: CreateContainerConfigError | 容器无法启动的直接错误类型 |
| 2 | K8s State | kubernetes | container.app.message: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input | 明确标识出缺失的资源对象及具体 Key |
| 3 | Metric | prometheus | kube_pod_container_status_waiting_reason{container="app", reason="CreateContainerConfigError"} = 1 | 指标侧独立确认了容器处于该等待状态 |
| 4 | K8s State | kubernetes | pod.phase: Pending | Pod 整体处于 Pending 阶段，验证了业务不可用现象 |

**证据分析：**
Kubernetes 的状态事实 (fact-9cd6b8d92128, fact-a555c12f52b0) 提供了明确的错误根因指引，指出 ConfigMap 中缺失 key。Prometheus 指标 (fact-ea1e2d43e2ec) 从另一个维度证实了容器确实停留在 `CreateContainerConfigError` 状态。两者在错误类型上完全吻合，且无矛盾数据。Logging/Tracing 维度因容器未启动而不可用，符合该错误类型的特征。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用了 ConfigMap 'aiops-case-v11/workload-input' 中不存在的 key 'unavailable-key' → kubelet 校验 ConfigMap key 失败 → 容器挂载失败并进入 CreateContainerConfigError 状态 → Pod 保持 Pending 状态，应用无法启动
```

### 根因结论

已确认根因：Pod `aiops-case-v11/workload` 的定义中引用了 ConfigMap `aiops-case-v11/workload-input` 中的键 `unavailable-key`，但该键在 ConfigMap 中并不存在。这导致 kubelet 在尝试为容器 `app` 挂载配置时验证失败，从而将容器状态设置为 `CreateContainerConfigError`。

支持证据：
- **K8s State**：明确的报错信息 "couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input" (fact-a555c12f52b0)。
- **K8s State**：容器等待原因为 `CreateContainerConfigError` (fact-9cd6b8d92128)。
- **Metric**：Prometheus 指标确认该容器处于上述错误等待状态 (fact-ea1e2d43e2ec)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.7s
├─ 并发证据采集: 38.2s
│  └─ g1 aiops-case-v11/workload: 38.2s (Evidence 30.9s, RCA 7.3s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
