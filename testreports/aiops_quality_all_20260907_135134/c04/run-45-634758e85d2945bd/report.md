## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod 配置错误：Spec 中引用了 Secret aiops-case-04/workload-input 中的 key 'unavailable-key'，但该 key 在目标 Secret 中不存在。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `waiting_reason=CreateContainerConfigError` (Container: app) [fact-3a2f80e0786b] | 直接展示容器启动阻塞的异常状态 |
| 2 | K8s Event | Kubernetes | `message="couldn't find key unavailable-key in Secret aiops-case-04/workload-input"` [fact-a080c490609e] | 给出明确的失败原因及缺失的密钥名称 |
| 3 | K8s State | Kubernetes | `phase=Pending` [fact-a03ae0c1c881] | 描述 Pod 持续挂起未运行的整体表现 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1` (label: reason=CreateContainerConfigError) [fact-0226e9d402c2] | 监控指标侧面印证 Kubernetes 事件报告的异常状态 |
| 5 | K8s State | Kubernetes | `restart_count=0` [fact-05144e8717db] | 排除因配置错误之外的容器频繁重启或故障注入因素 |

**证据说明：**
Kubernetes 事件记录 (证据 2) 给出了确切的配置错误原由，直接导致了 Kubernetes 状态 (证据 1, 3) 的阻塞。Prometheus 指标 (证据 4) 捕获到了这一阻塞现象，与 K8s 状态机表现一致。证据 5 确认了故障发生时的初始性，未涉及复杂的历史重试。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用了不存在的 Secret key (unavailable-key) → kubelet 无法挂载/解析 Secret 数据 → 容器配置失败 (CreateContainerConfigError) → Pod 持续处于 Pending 状态
```

### 根因结论

**已确认根因**：Pod 配置错误。

该 Pod (`workload-6584f97c76-7ds5p`) 在 Spec 中引用了 Secret `aiops-case-04/workload-input` 中的 key `unavailable-key`，但该 key 在目标 Secret 中不存在，导致 kubelet 无法完成容器配置，从而引发 `CreateContainerConfigError` [fact-0226e9d402c2] 并使得 Pod 卡在 `Pending` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 15.9s
├─ 并发证据采集: 57.6s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 57.6s (Evidence 48.6s, RCA 8.9s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
