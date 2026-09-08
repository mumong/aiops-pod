## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态长达 39 分钟，无法删除。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` | `Normal Killing 39m kubelet Stopping container app` | 确认容器进程在 39 分钟前被节点终止。 |
| 2 | K8s State | `pod.status` | `Terminating (lasts 39m)` | 确认 Pod 停滞在 Terminating 状态，证明删除流程已挂起。 |
| 3 | K8s State | `container.last_exit_code` | `exit_code: 137` | 表明容器因信号（通常 OOM Kill）被强制终止，解释了 Pod 进入 Terminating 的初始原因。 |
| 4 | K8s State | `container.last_terminated_reason` | `reason: Error` | 对应非 0 退出状态，确认容器未能正常运行结束。 |
| 5 | Topology | `finalizer` | `aiops.lab/hold` | **阻塞点确认**：存在自定义 Finalizer 阻止 API Server 完成 Pod 对象的删除操作。 |
| 6 | Logging | `elasticsearch` | `pattern: "request completed", http_status: 200, path: "/work"` | 在终止前 6 秒（22:31:06-12）服务正常处理 HTTP 请求，无应用层报错。 |
| 7 | Tracing | `tempo span` | `GET /work, 200, 2026-09-03T22:31:10.116193Z` | 与日志时间匹配，确认终止前的最后业务请求成功完成。 |
| 8 | Metrics | `prometheus` | `kube_pod_container_status_restarts_total: 0` | 确认在 Terminating 停滞期间无重启行为。 |

**证据分析：**
K8s 事件与退出码事实表明 Pod 是因为容器被杀（Exit 137）而触发终止流程。然而，状态事实显示该流程在 39 分钟内卡住。证据中未直接显示 Finalizer 对应的 Operator 报错，但日志与追踪数据证明在终止前应用层业务逻辑（GET /work）是完全正常的，且无重启（Metrics 确认）。因此，阻塞仅由 `aiops.lab/hold` Finalizer 存在本身引起，而非容器运行时的应用逻辑缺陷。

## 🎯 根因分析 · g1

### 因果链

```text
容器进程异常终止 (Exit 137) → API Server 标记 Pod 进入 Terminating → Finalizer `aiops.lab/hold` 未被清理 → Pod 停滞在 Terminating 状态 (Stuck 39m)
```

### 根因结论

**已确认根因：** Pod `aiops-case-11/workload` 的删除流程被自定义 Finalizer `aiops.lab/hold` 阻塞。

证据表明，Pod 初始进入 Terminating 状态是由于容器进程被强制终止（Exit Code 137）。K8s 在检测到 Finalizer `aiops.lab/hold` 存在于 Pod 对象上时，暂停了对象的物理删除，直到对应的清理逻辑移除该 Finalizer。然而，日志（fact 6）和追踪（fact 7）显示在终止前业务应用仍正常响应，且无相关报错信息，说明阻塞并非因为清理逻辑执行失败或报错，而是 Finalizer 对应的清理操作可能未被触发、执行未完成，或者该组件本身未能在终止事件发生时及时移除该标记，导致 Pod 状态停滞长达 39 分钟。

---

## 📊 性能统计

```text
├─ 总耗时: 2.7m
├─ 问题定位: 18.4s
├─ 并发证据采集: 133.7s
│  └─ g1 aiops-case-11/workload: 133.7s (Evidence 122.2s, RCA 11.3s)
└─ 汇总总结: 12.1s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
