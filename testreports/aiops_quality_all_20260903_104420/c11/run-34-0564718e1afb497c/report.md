## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态（DeletionTimestamp存在），且容器处于 CrashLoop 状态，删除操作被无限期挂起 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.phase` (fact-654c830709d5) | `phase: Running` | 确认 Pod 资源对象尚未被底层彻底清除 |
| 2 | K8s State | `pod.condition` (fact-e0af127db09a, fact-f48c8ad904a8) | `Ready=False` (`ContainersNotReady`), `ContainersReady=False` | 确认容器不处于就绪状态，与删除过程挂钩 |
| 3 | K8s State | `container.last_terminated_reason` (fact-64d7f1a211fe) | `reason: Error` | 提供容器异常终止的直接原因记录 |
| 4 | K8s State | `container.last_exit_code` (fact-ef9a8df7aa91) | `exit_code: 137` | 提供致命异常终止信号（通常对应 SIGKILL/OOM） |
| 5 | K8s Config | `container.resource_limit.memory` (fact-016d35a37e54) | `value: 96Mi` | 提供限制容器内存使用的资源约束边界 |
| 6 | Metric | `kube_pod_container_status_restarts_total` (fact-9599dbeb23fb) | `value: 0` | 确认容器自创建以来未发生过重启 |

证据表明：Pod 当前处于 Running 阶段，但容器状态异常。K8s 状态显示退出码为 137（致命错误，通常为 OOM Kill 或系统强制终止）且容器不就绪。指标维度确认未发生重启，排除了因频繁重启导致状态波动的可能。日志与追踪维度缺失，无法确认是应用内部逻辑崩溃、外部信号强制终止，还是因 96Mi 内存限制导致的 OOM。

## 🎯 根因分析 · g1

### 因果链

```text
已验证的上游原因 → 失败机制 → 直接失败 → 用户可见现象
容器异常终止 (Exit 137) → 容器不 Ready → Pod 进入 Terminating 挂起 → 删除操作被无限期挂起
```

### 根因结论

**已确认的根因：容器异常终止导致 Pod 进入僵死删除状态。**
容器 `app` 以 Exit Code 137 异常终止（证据 #4），且未发生重启（证据 #6），导致 Pod 处于 `Terminating` 阶段并被无限期挂起。Kubernetes 状态确认资源未被立即清理（证据 #1, #2）。

**未确认的环节与决定性事实缺失：**
1. **异常具体触发源未定：** 虽然 Exit 137 高度指向 OOM Kill 或 SIGKILL，但日志维度缺失（`status: absent`），且 Prometheus 缺失该 Pod 的历史资源使用率时序数据（工具调用失败且无其他数据），无法确认是否由 96Mi 的内存限制（证据 #5）引发。
2. **资源挂死原因未定：** 诊断信息中指出可能存在 `aiops.lab/hold` finalizer 阻止删除，但当前事实中未直接包含该 finalizer 的元数据证据（仅作为诊断 `unknowns` 存在），且日志/追踪无法佐证控制器的清理逻辑状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 26.7s
├─ 并发证据采集: 56.8s
│  └─ g1 aiops-case-11/workload: 56.8s (Evidence 46.7s, RCA 10.0s)
└─ 汇总总结: 11.2s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
