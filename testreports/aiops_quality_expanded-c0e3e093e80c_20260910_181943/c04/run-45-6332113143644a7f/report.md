## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod配置引用了Secret中不存在的Key |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container.waiting_reason: CreateContainerConfigError (container: app) | 确认容器启动阶段的最终失败状态 [fact-371ac067f0b8] |
| 2 | K8s State | Kubernetes | container.waiting_message: "couldn't find key unavailable-key in Secret aiops-case-04/workload-input" (container: app) | 直接定位配置加载失败的精确原因及涉及的资源对象 [fact-f7d79ae74a8b] |
| 3 | Metric | Prometheus | kube_pod_container_status_waiting_reason=1 (labels: reason="CreateContainerConfigError", container="app", timestamp=2026-09-10T16:10:29.624000Z) | 指标层面验证 Pod 处于配置错误的等待状态，与 K8s 状态一致 [fact-d1695c664998] |
| 4 | K8s State | Kubernetes | pod.phase: Pending | 解释 Pod 为何长期处于调度后但未启动的状态 [fact-66e81bcf5f54] |

**证据说明：**
Kubernetes API 获取的 `waiting_message` 直接指出了故障本质是 Secret 中 Key 缺失，Metric 数据从侧面确认了该状态。Logging 和 Tracing 维度标记为 `not_applicable` 是合理的物理限制（容器未启动），无其他日志证据需要排除。

## 🎯 根因分析 · g1

### 因果链

```text
Pod定义引用Secret 'aiops-case-04/workload-input'中的key 'unavailable-key' → Secret实际缺失该Key导致配置注入失败 → Kubelet无法创建容器（CreateContainerConfigError） → Pod处于Pending状态，不可用
```

### 根因结论

**已确认的根因：应用配置错误引用了不存在的 Secret Key。**
Pod 的容器定义中引用了 `aiops-case-04/workload-input` 中的 `unavailable-key`，但该 Secret 中实际并不包含此键。这导致 `kubelet` 在尝试注入容器配置时失败，进而引发 `CreateContainerConfigError` 状态，阻碍了容器的启动。证据 [fact-f7d79ae74a8b] 提供了确定的错误消息，排除了其他网络或资源不足的可能性。

---

## 📊 性能统计

```text
├─ 总耗时: 59.1s
├─ 问题定位: 17.2s
├─ 并发证据采集: 33.6s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 33.6s (Evidence 28.3s, RCA 5.2s)
└─ 汇总总结: 8.3s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
