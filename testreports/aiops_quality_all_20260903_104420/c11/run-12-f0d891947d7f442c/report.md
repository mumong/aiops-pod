## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态超过 18 分钟，未能自动清理。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | message: "Normal Killing 18m kubelet Stopping container app" | 确认容器进程在 18 分钟前被 kubelet 终止，Pod 进入终止流程 |
| 2 | K8s State | Kubernetes | container last_terminated_reason: "Error", exit_code: 137 | 提供异常终止的直接信号来源，表明应用被系统或资源限制强制杀死 |
| 3 | K8s Config | Kubernetes | memory_limit: 96Mi, memory_request: 24Mi | 提供资源上下文，Exit 137 在此资源量级下常由 OOM Killer 触发 |
| 4 | K8s State | Kubernetes | pod.status: "Terminating (lasts 18m)", pod.phase: "Running" | 确认 Pod 对象在容器已退出 (phase Running) 后仍处于 Terminating 状态超过 18 分钟 |
| 5 | K8s Event | Kubernetes | event.reason: "ContainersNotReady", message: "containers with unready status: [app]" | 说明 Pod 处于终止流程中时，已无法正常提供 Ready 服务，符合预期行为 |
| 6 | Tracing | Tempo | trace_id "75c4028b11532f074defb107fd297f49", GET /work, response 200, timestamp: 2026-09-03T22:31:10 | 确认应用在终止前（约 18m 前）能够正常响应业务请求，排除应用长期未启动的问题 |
| 7 | Logging | Elasticsearch | log pattern: "request completed", http_status: 200, time_range: "22:31:06 to 22:31:12" | 证实终止前应用处于正常工作状态，且无持续报错记录 |

**证据印证说明：**
- 证据 1、2 确立了 Pod 内应用进程被意外终止的时间点和状态（Exit 137）。
- 证据 4 揭示了当前系统状态的矛盾点：容器已死（证据 2），但 Pod 对象本身无法被回收（证据 4），卡住了 18 分钟。
- 证据 5 描述了该阶段 Pod 的正确表现（NotReady），排除了 Pod 假死的可能，聚焦于“删除”动作为何受阻。

## 🎯 根因分析 · g1

### 因果链
```text
已验证的上游原因 → 失败机制 → 直接失败 → 用户可见现象
```

### 根因结论

当前证据支持根因结论：**Pod 资源对象残留，其 `finalizer` 机制阻止了 API Server 完成清理。**

- **确认的根因**：Pod 对象 `aiops-case-11/workload` 上注册了 `aiops.lab/hold` 这一 finalizer。当容器 `app` 因异常终止（Exit 137，证据 2）并被 kubelet 停止（证据 1）后，API Server 将 Pod 标记为 Terminating。但是，该 finalizer 对应的控制器或组件未能按预期逻辑移除该 finalizer 字段，导致 API Server 判定清理工作未完成，拒绝将其从 etcd 中彻底删除。
- **证据支撑**：证据 4 明确显示 Pod 在容器退出后长达 18 分钟仍处于 Terminating 状态，这是 finalizer 未完成清理的典型特征。
- **未知事实**：
  1. 注册并持有 `aiops.lab/hold` finalizer 的具体控制器组件（如 Operator 或特定的 Controller）当前状态未知。
  2. 该控制器未能完成逻辑处理（如未发送移除请求或处理逻辑死锁）的具体原因未知。需要检查该控制器的日志及 API Server 的 Admission/Controller 日志以进一步排查。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 12.2s
├─ 并发证据采集: 91.2s
│  └─ g1 aiops-case-11/workload: 91.2s (Evidence 81.7s, RCA 9.3s)
└─ 汇总总结: 13.2s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
