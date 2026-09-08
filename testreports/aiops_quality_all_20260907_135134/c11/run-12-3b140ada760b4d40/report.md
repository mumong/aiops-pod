## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod finalizer 'aiops.lab/hold' is blocking termination after container killed with exit code 137. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Normal Killing 23m kubelet Stopping container app` | 确认 Pod 内的 app 容器因系统事件（23分钟前）被停止，是触发终止流程的上游动作。 |
| 2 | K8s State | Kubernetes | `container.last_exit_code: 137` | 确认 app 容器被强杀，状态码 137 指向 OOM 或 SIGKILL。 |
| 3 | K8s State | Kubernetes | `pod.status: Terminating (lasts 23m)` | 确认 Pod 对象进入终止状态已长达 23 分钟，说明 Pod 的终止钩子或清理逻辑被卡住。 |
| 4 | K8s State | Kubernetes | `event.message: Annotations: ... Exit Code: 137` | 结合 Pod 状态变更日志，进一步佐证容器退出原因，确认容器并非因健康检查失败退出而是异常强杀。 |
| 5 | Metric | Prometheus | `kube_pod_deletion_timestamp: 1788822586` | 确认 Pod 删除时间戳已设定，从客观时间指标上验证了 Pod 终止动作已被集群控制器接受，但长期停滞。 |
| 6 | Logging | Elasticsearch | `log.message: request completed (200 OK, path: /work) ... numeric_fields(allocated_mib: first=0, last=0, min=0.0, max=0.0)` | 提供终止前最后的应用层视角：23:09:48 至 23:09:56 间正常处理 HTTP 请求并返回 200，内存使用指标为 0。说明应用进程在强杀前处于正常工作状态，无内部内存耗尽迹象，排除容器内 OOM 导致自身崩溃的情况。 |
| 7 | Tracing | Tempo | `HTTP GET /work response_code: 200 (trace_id: 25d61c1398d8177ee9ac13f4efffb8b9)` | 与日志记录的时间点完全吻合，证明在强杀事件发生前，应用功能正常，请求链路无异常中断。 |

**证据链总结：**
容器 app 在 23:09:58 左右被 kubelet 以 exit_code 137 强杀（证据 1、2），而在此之前（23:09:48-23:09:56）应用日志与追踪数据显示请求均正常返回 200（证据 6、7），且应用侧内存指标显示正常（证据 6），排除了应用自身 OOM 或崩溃的可能，强杀可能来自宿主机层面的资源管控。尽管容器已被杀，但 Kubernetes 控制平面记录 Pod 状态为 `Terminating (lasts 23m)`（证据 3），并确认 Pod 删除时间戳已设置（证据 5）。强杀动作与 Pod 对象长时间卡在 `Terminating` 状态之间存在明显的时间断层，说明 Pod 资源回收机制（而非容器进程自身）是当前的阻塞点。

## 🎯 根因分析 · g1

### 因果链
```text
Kubernetes 调度器或宿主机管控强杀容器 (Exit 137) → 容器进程被终止 → Pod 对象状态更新为 Terminating → Pod finalizer 'aiops.lab/hold' 阻塞清理 → 用户可见 Pod 长期处于 Terminating 状态（已持续 23 分钟）
```

### 根因结论
已确认根因：Pod `aiops-case-11/workload` 的 `finalizer` 中存在一个名为 `aiops.lab/hold` 的清理钩子（由诊断信息 `phenomenon` 直接指出，且符合 Pod 强杀后状态卡在 Terminating 的集群级特征）。

证据支撑：
1. **异常现象**：Pod 处于 `Terminating` 状态长达 23 分钟（证据 3）。
2. **触发条件**：app 容器在 23 分钟前被强杀，退出码 137（证据 1、2）。
3. **阻塞原因**：容器本身已经终止且正常处理过请求（证据 6、7），因此问题不在于应用层逻辑死锁，而在于 Kubernetes 对象层面的 `finalizer` 清理机制未能完成。在 Kubernetes 中，`finalizer` 未移除会导致 `kubectl delete` 或终止流程永久挂起。

结论中明确指出，阻碍 Pod 被彻底删除的直接原因是 `aiops.lab/hold` 这个特定 finalizer 的阻塞。

---

## 📊 性能统计

```text
├─ 总耗时: 2.6m
├─ 问题定位: 13.3s
├─ 并发证据采集: 127.9s
│  └─ g1 aiops-case-11/workload: 127.9s (Evidence 123.6s, RCA 4.2s)
└─ 汇总总结: 15.3s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
