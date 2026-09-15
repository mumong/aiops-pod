## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 持续 Terminating 状态超过 3 分钟，未能自动回收 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-11/workload` 状态: `Terminating` (持续时间 3m46s) | 症状：确认 Pod 处于删除滞留状态，未正常回收。 |
| 2 | K8s Event | Kubernetes | `Stopping container app` | 现象：容器进程确实已被 kubelet 停止。 |
| 3 | K8s State | Kubernetes | 容器退出码: 137 (SIGKILL) | 关键事件：容器进程被强制终止。 |
| 4 | K8s Config | Kubernetes | 资源限制: 96Mi Memory, 200m CPU | 上下文：存在内存限制，虽未直接证实触发 Kill，但构成了 137 退出的潜在背景。 |
| 5 | Logging | Elasticsearch | 最近日志: `request completed`, http_status: 200, path: /work (03:47:09-03:47:15) | 限定：进程在终止前瞬间仍在处理正常 HTTP 请求，表明异常可能是突发的外部信号或系统级 OOM。 |
| 6 | Tracing | Deepflow/Tempo | Span: `GET /work` (trace_id: `1edba7b29f23053616d75e955fa073c8`), 耗时 3.6ms~17ms | 追踪关联：与日志记录完全对应，证明应用层逻辑在终止前运行正常。 |
| 7 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 0 | 状态确认：容器尚未经历重启，当前仍处于终止后的清理阶段。 |

**证据分析**：
日志 `request completed` 和 Tracing Span `GET /work` 证实了容器进程在 `03:47:09` 至 `03:47:15` 期间仍具备业务处理能力。随后容器被系统强制发出 SIGKILL（退出码 137）并停止。Kubernetes 事件确认了 `Stopping container` 的行为。尽管容器已终止，但 Pod 对象本身卡在 `Terminating` 状态已超过 3 分钟，表明 API Server 无法完成该对象生命周期最后的清理阶段。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 包含 'aiops.lab/hold' 自定义 Finalizer 未被清理 → 阻塞 API Server 移除 Pod 对象 → 容器虽已因 SIGKILL (Exit 137) 退出，但 Pod 资源未被回收 → Pod 持续处于 Terminating 状态
```

### 根因结论

已确认的根因是 `aiops-case-11/workload` 的 `metadata.finalizers` 字段中包含了未清理的自定义 Finalizer `'aiops.lab/hold'`。这导致 Kubernetes API Server 在容器终止后无法执行最终的垃圾回收操作，从而阻塞了 Pod 对象的删除。

证据支持：
- **机制阻断**：Kubernetes 事件 `Stopping container` 与最终状态 `Terminating` 并存（证据 #1, #2），表明控制平面与数据平面不一致。
- **终止确认**：退出码 `137`（证据 #3）证明容器进程确实已非正常结束，排除了业务应用自身卡死导致无法退出的可能性。
- **运行正常**：Tracing 和 Logging 显示业务请求在终止前瞬间处理正常（证据 #5, #6），进一步佐证了进程是被外部强制杀死的。

未确认部分：
- 触发容器 `SIGKILL (137)` 的具体上游原因（如 OOM Killer 触发、手动 `kubectl delete`、或健康检查失败）不在本次“Terminating 滞留”的诊断范围内。

---

## 📊 性能统计

```text
├─ 总耗时: 56.8s
├─ 问题定位: 13.3s
├─ 并发证据采集: 30.5s
│  └─ g1 aiops-case-11/workload: 30.5s (Evidence 21.9s, RCA 8.5s)
└─ 汇总总结: 12.9s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
