## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 被自定义 finalizer 'aiops.lab/hold' 阻塞。该 finalizer 强制要求所属控制器完成资源清理，但由于容器已因 SIGKILL (Exit Code 137) 终止，且无任何事件或日志表明控制器清理逻辑已执行，API Server 因此拒绝删除 Pod，导致其卡在 Terminating 状态超过 66 分钟。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.status`: Terminating (lasts 66m) | 确认 Pod 已阻塞在删除阶段，处于终止状态超过 66 分钟 |
| 2 | K8s State | kubernetes | `pod.phase`: Running | 确认容器层仍维持运行中状态，但逻辑删除流程受阻 |
| 3 | K8s State | kubernetes | `container.last_terminated_reason`: Error; `container.last_exit_code`: 137 | 确认应用容器经历了异常终止（通常对应 SIGKILL），这是触发删除流程的初始事件 |
| 4 | K8s State | kubernetes | `pod.condition`: Ready=False, ContainersReady=False (reason: ContainersNotReady) | 确认 Pod 当前处于不健康状态，且无重启行为 |
| 5 | K8s Event | kubernetes | `event.message`: Exit Code: 137 | 佐证容器异常退出的直接原因 |
| 6 | K8s State | kubernetes | `diagnosis`: Pod 被自定义 finalizer 'aiops.lab/hold' 阻塞 | 解释为何 Pod 在异常终止后仍然卡在 Terminating 状态（非正常的资源回收） |
| 7 | Metric | prometheus | `kube_pod_container_status_restarts_total`: 0 (container: app) | 确认容器未经历重启，排除了重启循环导致终止的可能性 |

**证据互证说明：**
Kubernetes 事实（#1, #2, #4）共同描绘了 Pod 既非正常 Running 也非正常 Completed 的“僵死”状态；事实 #3 与 #5 提供了引发删除请求的异常原因（SIGKILL 导致退出）；事实 #6 提供了逻辑上的根本解释——自定义 Finalizer 阻断了删除流程。Metric #7 佐证了容器在异常退出后并未发生重启，进一步确认了当前停滞的状态特征。

## 🎯 根因分析 · g1

### 因果链
```text
应用容器异常终止 (Exit Code 137) → Pod 触发删除流程 → 'aiops.lab/hold' finalizer 拦截删除请求 → 依赖的控制器未执行清理或无相应事件 -> Pod 卡在 Terminating 状态 (66m)
```

### 根因结论
已确认的根因为：Pod `aiops-case-11/workload` 被自定义 Finalizer `aiops.lab/hold` 阻塞。
尽管容器已因 `Exit Code: 137` 异常终止（证据 #3, #5），正常的资源回收机制应当移除 Pod，但由于该 Finalizer 的存在，API Server 要求所属控制器完成清理逻辑。当前证据（证据 #6）表明控制器清理逻辑未执行或无相应事件输出，导致 Pod 逻辑上被删除但在物理/状态上无法彻底移除，从而卡死在 `Terminating` 状态超过 66 分钟（证据 #1）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 26.8s
├─ 并发证据采集: 44.3s
│  └─ g1 aiops-case-11/workload: 44.3s (Evidence 37.2s, RCA 6.9s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
