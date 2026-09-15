## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | {'container': 'app', 'reason': 'Error'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | pod.phase: Running, pod.status: Terminating (lasts 80m) | 确认 Pod 处于无法结束的 Terminating 状态已持续 80 分钟 |
| 2 | K8s Event | kubernetes | event.message: Exit Code: 137 | 记录容器最后一次终止原因为 137 |
| 3 | K8s State | kubernetes | container.last_terminated_reason: Error, container.last_exit_code: 137 | 证实容器因非零退出码 137 (SIGKILL) 终止 |
| 4 | K8s Config | kubernetes | resource_limit.memory: 96Mi, resource_request.memory: 24Mi | 提供容器资源约束上下文，作为判断 OOM 可能性的基线 |
| 5 | Metric | prometheus | kube_pod_container_status_restarts_total: 0 | 确认容器重启次数为 0，与 exitCode 137 存在事实冲突 |
| 6 | K8s Event | kubernetes | event.message: k8s.v1.cni.cncf.io/network-status (6 records) | 提供网络状态上下文，但无法解释终止原因 |

当前证据显示容器发生了致命退出（Exit 137），但重启次数为 0 且 Pod 状态卡死，表明存在外部机制（如 Finalizer）阻止了清理，且退出后的重启/清理流程未执行。

## 🎯 根因分析 · g1

### 因果链

```text
容器异常退出 (Exit 137) → [未确认: OOM Kill 或 kubectl delete --force] → Finalizer `aiops.lab/hold` 阻止资源清理 → Pod 持续 Terminating (lasts 80m)
```

### 根因结论

**证据不足**。

当前事实存在无法调和的矛盾，无法单一确认根因：
1.  **状态冲突**：Pod 处于 Terminating 状态且 `restart_count=0`，但容器存在 `Exit Code: 137` 记录。通常 SIGKILL 会触发重启（除非是强制删除或 Finalizer 阻止），这一矛盾无法由现有 K8s 状态解释。
2.  **缺失关键日志**：无法确认是谁注册了 `aiops.lab/hold` Finalizer 以及为何在 Pod 删除时未被清除（需要控制面日志），也无法区分 137 是 OOM Kill 还是外部强制删除导致。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 13.6s
├─ 并发证据采集: 45.7s
│  └─ g1 aiops-case-11/workload: 45.7s (Evidence 36.5s, RCA 9.0s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
