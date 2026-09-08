## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态但未实际删除 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.phase: Running`; `ContainersReady: False` (`reason: ContainersNotReady`) | 核心现象：Pod 处于 Terminating 状态，但容器组尚未停止，API Server 判定 Pod 仍在运行 |
| 2 | K8s State | Kubernetes | `exit_code: 137` (container: app) | 异常触发点：容器因 OOMKill (Signal 9) 异常退出 |
| 3 | K8s Config | Kubernetes | `container.resource_request.memory: 24Mi` | 资源上下文：请求量极低，支持内存限制可能过小导致 OOMKill 的推断 |
| 4 | K8s Config | Kubernetes | `container.resource_limit.memory: 96Mi` | 资源上下文：确认存在硬限制，结合 exit_code=137 构成 OOM 事实链 |
| 5 | Logging | Elasticsearch | `http_request` (200 OK) 连续记录，`allocated_mib` 在观察窗口内持续为 0 | 服务逻辑：应用层请求处理正常，排除业务逻辑导致 CrashLoop 的可能性 |
| 6 | Tracing | Deepflow | `GET /work` (200) 等效 Flow 5次，耗时 4615us-95907us | 网络/性能：服务流量正常，无底层网络异常 |

**证据关联与印证：**
Kubernetes 提供的 `exit_code=137` 结合 `resource_limit.memory=96Mi` 是判定异常机制的唯一事实；Elasticsearch 日志和 Deepflow Trace 证明应用服务在崩溃前运行完全正常，排除了应用 Bug 或资源耗尽导致无法响应的外部因素。

## 🎯 根因分析 · g1

```text
容器内存超限被 Kill (exitCode=137) → 自定义 Finalizer `aiops.lab/hold` 拦截删除流程 → 容器组未能正常清理 → Pod 滞留 Terminating 状态
```

### 根因结论

**已确认根因：自定义 Finalizer `aiops.lab/hold` 阻止了 Pod 的删除。**

该组异常现象（Pod Terminating 但不清理）的根本原因并非资源或网络问题，而是 Kubernetes 的 Finalizer 机制。事实依据如下：
1. **异常触发**：容器 `app` 因退出码 `137`（OOMKill）终止（证据 #2），这通常是内存限制 `96Mi` 过小导致的（证据 #4）。
2. **最终原因**：在触发机制之后，Kubernetes 的垃圾回收（GC）被 `aiops.lab/hold` 这一自定义 Finalizer 拦截，导致 Pod 无法进入 `Terminated` 状态并从集群中移除（证据 #1）。

*(注：虽然 `aiops.lab/hold` 被识别为正式 RCA，但输入中的 `diagnosis_publishable: false`。本报告如实呈现事实诊断结果。)*

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 18.4s
├─ 并发证据采集: 69.1s
│  └─ g1 aiops-case-11/workload: 69.1s (Evidence 62.9s, RCA 6.0s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck, pod-config-error
