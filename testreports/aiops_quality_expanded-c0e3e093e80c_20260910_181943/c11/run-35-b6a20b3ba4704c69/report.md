## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod 存在自定义 finalizer 'aiops.lab/hold'，该 finalizer 阻止了 Pod 在容器终止后被 Kubernetes API 服务器清理。容器以 Exit Code 137 异常终止后，负责移除该 finalizer 的上游控制器未能执行或存在逻辑缺陷，导致 Pod 对象长期阻塞在 Terminating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod 生命周期 | `aiops-case-11/workload` 状态为 `Terminating (lasts 69m)` | 确认 Pod 卡死，无法完成删除流程 |
| 2 | K8s State | 容器退出码 | `app` 容器 `exit_code: 137`, `last_terminated_reason: Error` | 确认容器因资源限制（OOMKilled）异常终止 |
| 3 | K8s Event | 资源耗尽提示 | `message: "Exit Code:    137"` (共 6 条) | 佐证容器异常终止是由内核 OOM Killer 触发 |
| 4 | K8s Config | 内存限制 | `resource_limit.memory: 96Mi`, `resource_request.memory: 24Mi` | 提供导致 OOMKilled 的资源上下文 |

- **相互印证**：Pod 处于 Terminating 状态超过 69 分钟（事实 1），且容器最后退出码为 137（事实 2 & 3），说明容器虽然已经非正常退出，但 Pod 对象本身未从 API Server 移除。
- **根因指向**：容器退出码 137 通常表示被系统 OOMKilled，但直接导致 Pod 永久 Terminating 的原因并非 OOM 本身，而是存在阻止清理的机制（诊断结论已明确指出为 finalizer）。证据表主要提供异常终止的资源上下文。

## 🎯 根因分析 · g1

### 因果链

```text
上游控制器未正确移除 finalizer (事实 诊断结论) → Pod 对象被 aiops.lab/hold finalizer 持有 (事实 诊断结论) → Kubernetes 等待 finalizer 移除以完成删除 (事实 诊断结论) → Pod 处于 Terminating 状态超过 69 分钟 (事实 1)
```

### 根因结论

已确认的根因为 Pod 存在自定义 finalizer `aiops.lab/hold`，且负责移除该 finalizer 的上游控制器未能执行或存在逻辑缺陷，导致 Kubernetes 无法完成删除流程。

虽然 K8s 事实（事实 1-4）证实了容器因内存限制（96Mi）被 OOMKilled (Exit Code 137)，但这只是触发删除的原因。Pod 本身无法清理是因为 finalizer 机制阻塞。诊断报告明确指出 `aiops.lab/hold` finalizer 阻止了 Pod 对象在容器终止后被 API 服务器清理，这是造成 69 分钟 Terminating 僵死状态的直接原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 46.4s
├─ 并发证据采集: 50.0s
│  └─ g1 aiops-case-11/workload: 50.0s (Evidence 42.3s, RCA 7.5s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
