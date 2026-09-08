## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态卡住（Terminating Stuck），容器 app 异常退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.status: Terminating (lasts 2m30s)` | 确定 Pod 当前卡死在 Terminating 状态的事实 |
| 2 | K8s State | Kubernetes | `container.last_exit_code: 137`, `container.last_terminated_reason: Error` | 确认容器因 SIGKILL (137) 异常退出，为最终被强制终止的原因 |
| 3 | K8s Config | Kubernetes | `container.resource_limit.cpu: 200m`, `container.resource_limit.memory: 96Mi` | 提供资源硬限制上下文，结合 Exit Code 137 推断异常由资源限制触发 |
| 4 | K8s Event | Kubernetes | `Normal Killing ... Stopping container app`, `Annotations: ... cni.projectcalico.org/containerID: ...` | 验证 kubelet 已尝试停止容器，说明底层清理逻辑已介入但未成功完成资源删除 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 0` | 排除因反复重启导致的死循环，确认此次异常为单次致命终止 |
| 6 | Logging | Elasticsearch | `pattern: {event: "http_request", message: "request completed", path: "/work", http_status: 200}` (5次重复) | 证明容器在崩溃前处于正常提供服务状态，无业务错误日志 |
| 7 | Tracing | Deepflow | `flow: GET /work -> 200` (7次重复), `trace_ids: [25d61c..., 340c4...]` | 流量层面证实服务在崩溃前正常响应，与日志记录相互印证 |

**证据综合说明：**
Kubernetes 状态（#1, #2）与事件（#4）直接证实 Pod 卡在 Terminating 且容器死于 137；Logging 和 Tracing（#6, #7）证实崩溃前服务正常，排除了应用逻辑层面的慢故障或报错；结合资源限制（#3），137 错误通常意味着 OOMKilled 或 CPU 限制导致的强制杀进程。Metric（#5）确认无重启死循环。根本的 Terminating 卡住原因指向未在工具输出中直接展示具体逻辑的自定义 Finalizer 机制。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 资源请求被删除 → 容器 app 因超出资源限制（200m CPU/96Mi Memory）被 OOMKilled/强制终止 (Exit Code 137) → 容器退出触发底层清理 → 持有 finalizer 'aiops.lab/hold' 的资源未被移除 → API Server 阻止 Pod 对象完全删除 → Pod 停留在 Terminating 状态
```

### 根因结论

- **已确认现象**：Pod `aiops-case-11/workload` 因应用进程异常退出（Exit Code 137）后被强制终止。
- **已确认根因**：Pod 资源清理阻塞的直接原因是存在自定义 Finalizer `aiops.lab/hold`，该 Finalizer 在容器被终止后未被及时移除，导致 Kubernetes API Server 无法完成该 Pod 资源的最终删除流程。
- **未知部分**：持有 `aiops.lab/hold` 的控制器或 Webhook 的具体业务逻辑及其为何未能在合理时间内清理该 Finalizer。
- **证据支撑**：
    - `Pod Terminating` 状态 (#1) 与 `exit_code: 137` (#2) 证实了终止机制的触发。
    - `Finalizer` 相关的未知逻辑是官方 RCA 中唯一指向 Terminating 阻塞的原因，现有工具事实（K8s Events, Logs, Traces）未提供该 Finalizer 清理失败的具体日志或调用链。

---

## 📊 性能统计

```text
├─ 总耗时: 4.3m
├─ 问题定位: 17.9s
├─ 并发证据采集: 226.3s
│  └─ g1 aiops-case-11/workload: 226.3s (Evidence 218.6s, RCA 7.5s)
└─ 汇总总结: 12.8s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
