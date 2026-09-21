## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | aiops-case-v03/workload pod is stuck in Pending state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedScheduling ... 0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found.` | 直接展示调度器拒绝 Pod 的具体原因：依赖的 PVC 不存在 |
| 2 | K8s State | kubernetes | `pod.status: Pending` | 确认 Pod 处于未被调度到任何节点的挂起状态，与事件原因一致 |
| 3 | K8s Config | kubernetes | `container.resource_request.cpu: 5m`, `container.resource_request.memory: 8Mi` | 提供资源请求配置，确认非资源竞争导致的调度失败 |
| 4 | K8s Config | kubernetes | `container.resource_limit.cpu: 50m`, `container.resource_limit.memory: 32Mi` | 提供资源限制配置，进一步排除资源上限引发的异常 |
| 5 | Metric | prometheus | `kube_pod_status_phase(Pending) = 1` | 辅助确认 Pod 仍处于 Pending 阶段，无状态异常波动 |
| 6 | Metric | prometheus | `kube_pod_status_phase(Unknown) = 0` | 辅助排除 Pod 因镜像拉取等错误进入 Unknown 状态的可能性 |

上述 Kubernetes 事实构成了完整的闭环：Pod 的 Pending 状态（#2）与 Pending 指标（#5）相互印证；调度器报错明确指出是因 PVC 不存在（#1）导致的；同时资源请求与限制（#3, #4）证明故障与 CPU/内存资源不足无关。日志与追踪维度因 Pod 未启动被判定为不适用，符合当前“卡死在调度阶段”的诊断事实。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 引用了不存在的 PVC 'unavailable-claim' → 调度器无法绑定卷资源，判定不可调度 → Pod 状态保持 Pending，未分配到任何节点 → 用户观察到 Pod 处于挂起状态
```

### 根因结论

已确认的根因是 **Pod 依赖的 PVC 'unavailable-claim' 不存在**，这直接导致 Kubernetes 调度器拒绝为该 Pod 分配节点资源。证据 #1 中调度器的 `FailedScheduling` 事件明确记录了这一缺失引用，而证据 #2 和 #5 的 Pending 状态证实了这一机制造成的直接后果。资源配置相关证据（#3, #4）用于排除资源竞争等其他可能性，确认故障完全源于存储资源引用的定义错误。

---

## 📊 性能统计

```text
├─ 总耗时: 45.1s
├─ 问题定位: 18.0s
├─ 并发证据采集: 18.8s
│  └─ g1 aiops-case-v03/workload: 18.8s (Evidence 13.9s, RCA 4.8s)
└─ 汇总总结: 8.3s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
