## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod `aiops-case-11/workload` 被自定义 finalizer `aiops.lab/hold` 阻止删除，导致其在容器终止且删除时间戳已逾 75 分钟后仍处于 Terminating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.status` = `Terminating (lasts 75m)` | 展示 Pod 进入终止状态已超过 75 分钟，属于异常持久化状态 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason` = `Error`, `container.last_exit_code` = `137` | 确认容器已非正常终止，但进程退出并未触发后续的垃圾回收，需排查删除拦截原因 |
| 3 | K8s Config | Kubernetes | `finalizer` = `aiops.lab/hold` (存在于 metadata) | 提供阻止 Pod 被 API Server 真正删除的直接证据，是造成 Terminating 卡死的根本原因 |
| 4 | K8s Config | Kubernetes | `container.resource_limit.memory` = `96Mi` | 提供资源配置上下文，结合 Exit Code 137 (OOMKilled 常见特征)，暗示终止原因可能与资源限制有关 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = `0` | 确认该容器此前未发生过重启，此次 137 退出是近期发生的全新事件 |

**证据印证说明**：
1. 容器以 Exit Code 137 异常退出（事实#2），但 Pod 并未被垃圾回收，而是长期停留在 Terminating 状态（事实#1）。
2. Kubernetes 配置层面发现 `aiops.lab/hold` 自定义 finalizer 的存在（事实#3），这直接阻断了删除流程的正常结束，解释了“卡死”现象。
3. 资源限制为 96Mi（事实#4），结合 137 退出码，提示容器极可能因内存超限被 OOMKilled，进而触发删除，但最终被 finalizer 阻断。

## 🎯 根因分析 · g1

### 因果链

```text
自定义 finalizer `aiops.lab/hold` 存在于 Pod metadata 中 → API Server 等待该 finalizer 被清理 → 容器已终止 (Exit Code 137) 但 finalizer 未被移除 → Pod 进入 Terminating 卡死状态 (Terminating Stuck)
```

### 根因结论

**已确认的根因**：
Pod `aiops-case-11/workload` 被自定义 finalizer `aiops.lab/hold` 阻塞了删除流程。尽管容器已因异常（Exit Code 137）终止并请求删除，但由于该 finalizer 未被相应的控制器或 Webhook 及时移除，Kubernetes API Server 无法完成 Pod 的资源清理，导致其处于 Terminating 状态长达 75 分钟以上。

**证据引用**：
- 终止阻塞：证据 #3 (finalizer 存在) 结合 证据 #1 (Terminating 状态超 75m)。
- 终止触发：证据 #2 (Exit Code 137) 结合 证据 #4 (96Mi 内存限制)。

**未确认/缺失事实**：
- 注册并持有 `aiops.lab/hold` finalizer 的具体组件（如 Controller 或 Webhook）身份未确认。
- 该组件未能释放 finalizer 的具体原因（未采集相关组件的日志或状态，见 `collection.missing_reasons`）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 14.8s
├─ 并发证据采集: 44.8s
│  └─ g1 aiops-case-11/workload: 44.7s (Evidence 36.0s, RCA 8.6s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
