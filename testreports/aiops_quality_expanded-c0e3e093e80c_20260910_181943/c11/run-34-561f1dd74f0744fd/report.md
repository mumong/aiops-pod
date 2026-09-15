## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod `aiops-case-11/workload` 被自定义 finalizer `aiops.lab/hold` 阻塞，在容器因异常（exitCode 137）终止后，负责处理该 finalizer 的上游控制器未执行清理或移除操作，导致 Pod 一直处于 Terminating 状态超过 68 分钟。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.status` (fact-3c627787ea64) | `Terminating (lasts 68m)` | 确认异常现象：Pod 处于终止状态已持续 68 分钟未移除。 |
| 2 | K8s State | `container.last_exit_code` (fact-0bc5de5727be) | `app` 容器退出码 `137` | 触发异常终止的直接信号：OOM Kill 或系统级强制中断。 |
| 3 | K8s Config | `container.resource_limit.memory` (fact-04a38058c56b) | `96Mi` | 提供上下文：容器被设置了较小的硬内存上限。 |
| 4 | K8s Config | `container.resource_request.memory` (fact-302b81d475a9) | `24Mi` | 提供上下文：请求量仅占限制量的 1/4，存在内存突增或不足风险。 |
| 5 | K8s Event | `event.message` (fact-6698d7e6ad6e) | `Exit Code: 137` | 确认系统层面对该进程的异常拦截，与状态码一致。 |
| 6 | Metric | `kube_pod_container_status_restarts_total` (fact-0e9c10971e0b) | `0` (单样本，趋势不可评估) | 佐证该异常为孤立或首次发生，非周期性循环重启。 |

**证据链说明：**
`fact-3c627787ea64` 确认 Pod 进入不可逆终止状态的时间跨度（68m）远超正常清理时间。`fact-0bc5de5727be` 与 `fact-6698d7e6ad6e` 相互印证了 Pod 的终止是由信号 137 引起的强制终止。在 Pod 因 `fact-04a38058c56b` 内存限制被杀后，Kubernetes 理应执行其生命周期中的清理步骤，但由于被 `formal_rca` 识别到的自定义 finalizer `aiops.lab/hold` 拦截（RCA中提及），导致清理链路中的控制器未执行操作，最终使得 Pod 长时间卡在 Terminating 状态。Metric 显示重启次数为 0，说明集群并未尝试（或成功）进行重启，进一步确认了当前处于卡死状态。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存压力/超限(Exit 137) → 异常终止(退出码137, 事实2/5) → 自定义 finalizer(aiops.lab/hold)拦截清理 → 上游控制器未执行删除操作 → Pod长期卡在 Terminating 状态(事实1)
```

### 根因结论

已确认的根因：Pod `aiops-case-11/workload` 被自定义 finalizer `aiops.lab/hold` 阻塞，在容器因异常（exitCode 137）终止后，负责处理该 finalizer 的上游控制器未执行清理或移除操作，导致 Pod 一直处于 Terminating 状态超过 68 分钟。

证据表明，Pod 的终止并非由资源耗尽（如无法调度）或节点故障引起，而是其生命周期的收尾阶段（Finalizer 清理）发生了停滞。退出码 137 和 `resource_limit.memory` (96Mi) 提示了引发终止的前置条件（可能的 OOM），但最终导致“无法删除”状态的直接原因是 finalizer 清理逻辑的失效。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 13.5s
├─ 并发证据采集: 48.1s
│  └─ g1 aiops-case-11/workload: 48.1s (Evidence 42.9s, RCA 5.1s)
└─ 汇总总结: 12.1s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
