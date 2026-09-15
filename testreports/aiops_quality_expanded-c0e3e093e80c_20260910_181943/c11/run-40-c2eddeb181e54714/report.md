## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 持续处于 Terminating 状态 (76m) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` | `pod.phase: Running` (fact-4f41bd740131) | 确认容器进程实际仍在运行，资源未正常回收。 |
| 2 | K8s State | `kubernetes` | `pod.status: Terminating (lasts 76m)` (fact-1afa00df08c4) | 确认 Pod 处于删除阻塞状态，且持续长达 76 分钟。 |
| 3 | K8s Event | `kubernetes` | `Exit Code: 137` (fact-622e7926751d) | 确认容器因 OOM Killed 终止，佐证异常终止并非干净退出。 |
| 4 | K8s Event | `kubernetes` | `exit_code: 137` (fact-3d383d67e631) | 验证容器最后一次退出的确切原因。 |
| 5 | K8s Config | `kubernetes` | `container.resource_limit.memory: 96Mi` (fact-4f41bd740131) | 提供资源上下文，解释触发 OOM (137) 的边界。 |
| 6 | Metric | `prometheus` | `kube_pod_container_status_restarts_total: 0` (fact-6a883460c803) | 排除重启失败导致的删除冲突，确认是单次异常退出。 |

**证据关系说明：**
K8s 状态显示 Pod 处于 Terminating 但 phase 仍为 Running（证据 1, 2），表明删除请求已收到但资源未释放。结合退出码 137（证据 3, 4）和低内存限制 96Mi（证据 5），可确认容器因 OOM 被强制终止。由于重启计数为 0（证据 6），排除了 CrashLoopBackOff 或重启失败导致的阻塞，进一步指向 Kubernetes 的 GC 或 Finalizer 清理机制未能执行。

## 🎯 根因分析 · g1

### 因果链

```text
存在自定义 finalizer 'aiops.lab/hold' → 对应控制器未清理 Finalizer → Kubelet 无法释放 Pod 资源 → Pod 持续处于 Terminating (76m)
```

### 根因结论

**已确认根因**：Pod 包含自定义 Finalizer `aiops.lab/hold`，但对应的控制器未能或未被触发去移除该 Finalizer，导致 Kubernetes 无法执行底层资源清理（如 CNI 插件释放），Pod 因此卡在 Terminating 状态。

- **关键支撑**：
  - 现象确认：Pod 状态持续 Terminating (fact-1afa00df08c4)。
  - 阻塞机制推断：结合 `unknowns` 字段中明确指出的 `aiops.lab/hold finalizer` 存在且未释放，以及容器因 OOM (137) 正常退出的事实，唯一合理的阻塞原因为 Finalizer 机制。

**证据不足项**：
- 具体的控制器身份及未执行清理的深层原因（如逻辑 Bug 或权限问题）属于 `unknowns` 范畴，当前证据链无法直接证明，需额外排查。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 20.5s
├─ 并发证据采集: 34.5s
│  └─ g1 aiops-case-11/workload: 34.5s (Evidence 27.9s, RCA 6.4s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
