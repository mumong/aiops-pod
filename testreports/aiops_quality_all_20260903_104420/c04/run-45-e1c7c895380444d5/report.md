## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod workload-6584f97c76-wvcb2 处于 CreateContainerConfigError 状态，容器未启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s | `container.waiting_reason=CreateContainerConfigError` [fact-5387b379c2f5] | 确认容器未启动，明确故障类型为配置注入失败 |
| 2 | K8s Event | K8s | `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` [fact-54e1f89b6a1b] | 定位到具体缺失的配置键名 (unavailable-key) 及关联 Secret 对象 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1` (label: `reason=CreateContainerConfigError`) [fact-5fefe7d07a7f] | 辅助印证 Pod 处于等待且配置有误的状态，与 K8s 状态一致 |

**证据说明：**
K8s 事件 [fact-54e1f89b6a1b] 直接指出了失败原因（Secret 中缺少 `unavailable-key`），而 K8s 状态 [fact-5387b379c2f5] 和 Metric [fact-5fefe7d07a7f] 共同印证了该配置错误导致了容器进入 `CreateContainerConfigError` 的停滞状态。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用了 Secret 'workload-input' 中不存在的 key 'unavailable-key' → Kubelet 无法挂载配置并创建容器 → Pod 持续处于 CreateContainerConfigError 状态 → 容器未启动
```

### 根因结论

已确认的根因为 **Pod 配置引用了 Secret 中不存在的 key**。
Kubelet 在创建容器时尝试注入 `workload-input` Secret 的 `unavailable-key`，因该 key 不存在而引发 `CreateContainerConfigError`，导致容器无法启动 [fact-54e1f89b6a1b]、[fact-5387b379c2f5]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 20.7s
├─ 并发证据采集: 55.2s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 55.2s (Evidence 47.7s, RCA 7.3s)
└─ 汇总总结: 7.4s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
