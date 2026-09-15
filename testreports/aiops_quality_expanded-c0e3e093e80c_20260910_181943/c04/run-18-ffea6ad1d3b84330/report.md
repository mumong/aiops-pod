## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod workload-6584f97c76-h4lt9 的容器 spec 引用了 Secret aiops-case-04/workload-input 中的 key 'unavailable-key'，但该 Secret 中不存在此 key，导致容器配置失败并处于 CreateContainerConfigError 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Failed ... Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接定位到容器启动失败的报错原因与缺失的 Secret 键名 |
| 2 | K8s State | kubernetes | `pod.status` = Pending | 指示 Pod 处于初始调度或配置检查阶段，未进入运行状态 |
| 3 | K8s Config | kubernetes | `resource_request.cpu` = 5m; `resource_request.memory` = 8Mi | 提供 Pod 配置背景信息，与启动失败无直接因果关系 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = 1 (reason: `CreateContainerConfigError`) | 确认集群层面的容器等待原因为配置错误，验证事件报告 |

**证据说明：**
- 事件 (fact-097774ca8d24) 明确指出了具体的配置错误（缺失 Secret Key），指标 (fact-711163c348bc) 独立观测并确认了 `CreateContainerConfigError` 状态，两者相互印证。
- 容器未实际启动（指标显示 restart_count=0，状态为 Pending），因此日志 (logging) 和链路 (tracing) 数据不可用符合预期，证据集中于 Kubernetes 控制平面。

## 🎯 根因分析 · g1

### 因果链

```text
容器 spec 错误引用 Secret key 'unavailable-key' → kubelet 拉取/校验 Secret 失败 → 容器启动被拒绝 (CreateContainerConfigError) → Pod 保持 Pending 状态
```

### 根因结论

已确认根因为 **Pod `workload-6584f97c76-h4lt9` 的容器配置错误**。
Pod 的容器 spec 请求了 Secret `aiops-case-04/workload-input` 中的 key `unavailable-key`，但该 Secret 资源中实际不包含此键名（证据编号 1）。这导致 kubelet 在启动容器前校验配置失败，从而将容器状态标记为 `CreateContainerConfigError`，阻止了容器的启动（证据编号 2、4）。

该结论证据充分，无需进一步事实确认。

---

## 📊 性能统计

```text
├─ 总耗时: 51.1s
├─ 问题定位: 21.1s
├─ 并发证据采集: 22.2s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 22.2s (Evidence 17.2s, RCA 4.9s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
