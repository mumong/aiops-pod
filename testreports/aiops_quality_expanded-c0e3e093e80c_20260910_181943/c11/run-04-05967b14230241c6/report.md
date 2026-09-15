## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod 'workload' 被 Finalizer 'aiops.lab/hold' 阻塞（Finalizer 机制阻塞对象生命周期清理）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Normal Killing 5m10s kubelet Stopping container app` | 证明 Kubelet 已成功执行终止容器的动作。 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason: Error`, `container.last_exit_code: 137` | 佐证容器进程已被系统或 Kubelet 强制杀死。 |
| 3 | K8s State | Kubernetes | `pod.status: Terminating (lasts 5m11s)`, `ContainersReady: False` | 显示 Pod 对象长期停留在 Terminating 状态，无法进入已完成状态。 |
| 4 | Metric | Prometheus | `kube_pod_status_phase{phase="Running"} = 1`, `restarts_total = 0` | 证实应用容器未发生重启，终止是由外部删除请求触发的。 |
| 5 | Logging | Elasticsearch | `request completed` (4 times), `http_status: 200`, `allocated_mib: 0` | 表明 Pod 在终止前的业务处理功能正常。 |
| 6 | Tracing | Deepflow | `GET /work` HTTP 200, `src_ip: 172.16.104.9`, `trace_id: 1edba7b29f23053616d75e955fa073c8` | 日志与 Trace 关联的 `trace_id` 一致，确认终止前网络链路通畅。 |

证据 1、2 和 3 共同构成了一组矛盾现象：底层的 Kubelet 已经完成了杀容器的工作（Exit 137, Killing），但上层的 Pod 对象却始终卡在 `Terminating` 状态。结合 Metric 中 restart_count 为 0 的事实，排除了应用异常重启的可能性，将故障范围锁定在对象生命周期的清理阶段。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 对象存在未清理的 Finalizer 'aiops.lab/hold' → API Server/Garbage Collector 拒绝完成 Pod 删除请求 → Pod 对象状态永久卡在 Terminating → 容器资源无法回收
```

### 根因结论

已确认的根因是 Pod `aiops-case-11/workload` 被 Finalizer `aiops.lab/hold` 阻塞。

*   **机制确认**：尽管 Kubelet 已成功向容器进程发送了终止信号并记录了 `Exit Code 137` 和 `Killing` 事件（证据 1、2），但 Pod 对象在 API Server 中的生命周期并没有走完。
*   **现象印证**：Pod 状态长时间维持在 `Terminating`（证据 3），且 Metric 显示重启次数为 0（证据 4），这说明 Pod 并不是因为崩溃而被重启，而是因为对象的删除请求被阻塞了。
*   **结论**：根本原因在于 Kubernetes 的控制器管理组件因检测到 `aiops.lab/hold` 这一 Finalizer 存在，而持续挂起了该 Pod 的清理流程。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 32.6s
├─ 并发证据采集: 83.3s
│  └─ g1 aiops-case-11/workload: 83.3s (Evidence 75.5s, RCA 7.6s)
└─ 汇总总结: 10.7s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
