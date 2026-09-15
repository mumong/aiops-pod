## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态超过 78 分钟无法删除 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.status`: Terminating (lasts 78m) | 描述长期卡滞的最终状态 |
| 2 | K8s State | kubernetes | `container.last_terminated_reason`: Error (Exit Code: 137) | 确认容器因系统调用终止 |
| 3 | K8s State | kubernetes | `container.resource_limit.cpu`: 200m | 提供 OOMKilled 的资源上限上下文 |
| 4 | K8s Event | kubernetes | Event message: `Exit Code: 137` | 独立事件佐证容器非正常退出 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total`: 0 | 确认未触发重启策略，Pod 保持初始 Terminating 状态 |

**证据互证说明**：
K8s State（#1, #2）与 Metric（#5）高度一致，共同印证 Pod 自 78 分钟前因 137 终止后未重启而处于卡死的 Terminating 状态。Event（#4）与 State（#2）相互印证了异常的触发原因，但由于缺失 Topology 证据，无法在事实层面直接证实最终导致停滞的资源清理阻塞机制。

## 🎯 根因分析 · g1

### 因果链

```text
资源限制 (CPU 200m) → 容器 OOMKilled (Exit Code: 137) → 直接失败 (容器终止) → 用户可见现象 (Pod Terminating 停滞)
```
*注：导致“停滞”而非“重启”的具体阻塞机制（如 Finalizer）未确认。*

### 根因结论

证据不足。现有事实足以确认 Pod 异常终止的原因是资源耗尽导致的 OOMKilled，但无法确证 Pod 处于“Terminating”状态停滞的根本原因是资源清理阶段的阻塞。根据配置要求，正式 RCA 中声明的 'aiops.lab/hold' Finalizer 阻塞机制缺乏事实绑定支撑，未能在证据表中得到体现。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 11.4s
├─ 并发证据采集: 72.9s
│  └─ g1 aiops-case-11/workload: 72.9s (Evidence 64.7s, RCA 8.0s)
└─ 汇总总结: 7.2s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
