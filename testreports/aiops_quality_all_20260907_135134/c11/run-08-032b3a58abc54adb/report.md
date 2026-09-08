## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态，容器 app 已退出（Exit 137），但删除操作被 finalizer 阻塞，导致 Pod 资源无法释放 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s Event | Normal Killing (15m ago): "Stopping container app" | 确认容器已被主动终止，处于删除流程中 |
| 2 | K8s State | K8s Event | "Exit Code: 137" | 对应 Exit 137 (SIGKILL) 退出原因 |
| 3 | K8s State | K8s State | Pod status: "Terminating (lasts 15m)" / ContainersReady: False | 明确当前处于卡住的 Terminating 状态 |
| 4 | K8s State | K8s State | Pod phase: "Running" | 证明 kubelet 仍维持 Pod 资源占用 |
| 5 | K8s Config | K8s Config | 诊断描述：持有 finalizer `aiops.lab/hold` 的阻塞机制 | 直接揭示 Terminating 无法完成的根本原因 |
| 6 | Logging | Logging | 连续 5 条 "request completed" / http_status: 200 (23:09:48 - 23:09:56) | 证明退出前应用曾正常响应业务流量 |

上述证据表明：尽管容器 app 因收到终止信号已退出（Exit 137 / fact-2），且此前业务正常（fact-5），但 kubelet 在删除 Pod 时遭遇 finalizer `aiops.lab/hold` 的拦截（fact-5）。这导致 Pod 被强制保留在 Terminating 状态长达 15 分钟（fact-3），未能完成资源释放（fact-4），从而形成阻塞。

## 🎯 根因分析 · g1

### 因果链
```text
外部触发注入 finalizer 'aiops.lab/hold' (机制未确认) → K8s 删除流程遭遇 finalizer 拦截 → 无法执行资源释放 → Pod 陷入 Terminating 状态 (事实 3, 4)
```

### 根因结论
已确认的根因是：Pod `aiops-case-11/workload` 上存在自定义 finalizer `aiops.lab/hold`（参考输入中的诊断描述及事实 5）。
这一机制直接阻止了 Kubernetes 对 Pod 资源的清理与释放。由于 `aiops.lab/hold` 未被及时移除，即使容器 app 进程已因 SIGKILL (Exit 137, fact-2) 正常退出，且此前服务响应正常（fact-5），kubelet 也无法完成删除操作。这导致 Pod 资源被强制维持在 Terminating 状态（fact-3）长达 15 分钟，进而引发服务中断或资源未释放的问题。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 17.9s
├─ 并发证据采集: 85.7s
│  └─ g1 aiops-case-11/workload: 85.7s (Evidence 76.2s, RCA 9.4s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
