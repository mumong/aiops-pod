## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-7ds5p 处于 CreateContainerConfigError 状态，容器未启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` 等待状态: `CreateContainerConfigError` (fact-c5ac05a1d326) | 核心症状：容器因配置缺失被阻止启动 |
| 2 | K8s State | Kubernetes | 错误详情: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (fact-b2ee05544f0f) | 直接根因：Pod Spec 引用的 Secret Key 不存在 |
| 3 | K8s State | Kubernetes | Pod 阶段: `Pending`；未就绪容器: `[app]` (fact-373b3d0c31f9, fact-5bb21d91ae90) | 状态印证：配置错误导致 Pod 处于挂起未就绪状态 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 值为 1，label: `reason=CreateContainerConfigError` (fact-5e4501fce999) | 独立观测：监控数据与 K8s 事件状态一致 |

**证据说明**：
- Kubernetes 维度明确了错误类型为 `CreateContainerConfigError`，直接原因是指向 Secret `aiops-case-04/workload-input` 中不存在的 Key `unavailable-key` (事实 1, 2)。
- 监控维度独立验证了容器处于该等待状态 (事实 4)，未发现重启计数 (fact-398990fdf26c) 或 CPU/内存限制导致的问题。
- Logging 和 Tracing 因容器未启动而不适用，证据链在 K8s 状态与 Metric 之间闭合。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 'aiops-case-04/workload-input' 中缺少 Key 'unavailable-key' (触发)
    ↓
Pod 定义引用了该不存在的 Key，kubelet 无法挂载配置 (机制)
    ↓
容器启动流程中断，状态转为 CreateContainerConfigError (直接失败)
    ↓
Pod 处于 Pending 状态，无法运行业务流量 (现象)
```

### 根因结论

- **已确认根因**：Pod `aiops-case-04/workload-6584f97c76-7ds5p` 处于 `CreateContainerConfigError` 状态。
- **成因**：Pod 规范（Spec）中配置了对 Secret `aiops-case-04/workload-input` 中 Key `unavailable-key` 的引用，但该 Key 在 Secret 中实际不存在。
- **证据引用**：K8s 容器等待消息直接指出了缺失的 Key (事实 1, 2)；Metrics 验证了该错误状态的持续 (事实 4)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 28.0s
├─ 并发证据采集: 30.0s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 30.0s (Evidence 22.4s, RCA 7.5s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
