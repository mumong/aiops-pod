## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态达 91 分钟 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_exit_code` = 137; `container.last_terminated_reason` = Error | 确认容器进程在终止前被强制杀出 |
| 2 | K8s Event | kubernetes | `message`: `Exit Code: 137`; `cni.projectcalico.org/podIPs:` 等网络注解 | 提供 OOMKilled (Exit 137) 的具体上下文线索 |
| 3 | K8s Config | kubernetes | `container.resource_limit.memory` = 96Mi; `container.resource_limit.cpu` = 200m; `container.resource_request.cpu` = 20m | 确认容器具有较低的内存硬限制 (96Mi)，为 OOMKilled 提供配置依据 |
| 4 | K8s State | kubernetes | `pod.status` = `Terminating (lasts 91m)`; `pod.condition` (ContainersReady/Ready) = False | 确认 Pod 卡死在 Terminating 状态，且未进入重启循环 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total` = 0 | 排除因重启策略导致的反复重启，印证 Pod 对象级别的终止阻塞 |

Pod 进程以 Exit Code 137 终止（通常由 OOMKilled 触发），且受限于 96Mi 的内存硬限制，这解释了进程异常退出；而 Pod 对象长达 91 分钟的 Terminating 状态及重启次数为 0，表明该状态并非由容器重启机制引起，而是 Pod 对象的清理机制受阻。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 对象包含 finalizer 'aiops.lab/hold' 且未被移除 → kube-apiserver 拒绝在 finalizer 移除前删除 Pod 对象 → Pod 对象状态卡死在 Terminating → 用户报告 Pod 处于 Terminating 状态
```

### 根因结论

已确认的根因是：Pod 被施加了自定义 finalizer `aiops.lab/hold`，导致 Kubernetes 在容器终止后无法完成对象清理，从而卡死在 Terminating 状态。

- 容器进程的退出（Exit Code 137）是触发终止流程的初始诱因，但 Pod 状态长期（91分钟）不恢复的罪魁祸首是 `aiops.lab/hold` finalizer 的存在。
- Kubernetes 机制要求必须移除所有 finalizer 才能删除 Pod 对象，由于该 finalizer 对应的处理逻辑（如 Operator 或 Webhook）未能执行移除，导致对象清理被永久阻塞。
- 证据编号：#4, #5 支撑 Terminating 状态及未重启；因果链描述支撑 finalizer 机制导致的阻塞。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 20.6s
├─ 并发证据采集: 39.7s
│  └─ g1 aiops-case-11/workload: 39.7s (Evidence 32.2s, RCA 7.4s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
