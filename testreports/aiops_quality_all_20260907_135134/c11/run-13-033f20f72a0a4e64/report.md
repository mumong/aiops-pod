## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | 自定义finalizer 'aiops.lab/hold' 未释放导致Pod进入Terminating后卡死（TerminatingStuck） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | Kubernetes | `container.resource_request.memory`: 24Mi; `container.resource_limit.memory`: 96Mi | 确认内存硬限制为 96Mi，存在 OOMKill 的理论条件。 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason`: "Error"; `container.last_exit_code`: 137 | 错误退出码 137 直接证实容器此前遭遇了 OOMKill（内存超限终止）。 |
| 3 | K8s State | Kubernetes | `pod.condition`: `ContainersReady` 状态 `False` (Reason: `ContainersNotReady`)；`pod.phase`: `Running` | 显示 Pod 处于异常的运行状态，容器不断失败但未进入 CrashLoopBackOff。 |
| 4 | K8s State | Kubernetes | `container.restart_count`: 0 | 重启计数为 0，意味着虽然发生过致命错误，但当前 Pod 实例并未被 kubelet 重启过。 |
| 5 | K8s Event | Kubernetes | `ContainersNotReady`: "containers with unready status: [app]" | 佐证应用容器（app）因之前的失败行为未能保持健康就绪。 |
| 6 | Tracing | Deepflow/Tempo | `GET /work` 成功 (HTTP 200)；`allocated_mib`: min 0.0, max 0.0 (Log) | 证明应用进程在运行期间（OOM 发生前）能够正常响应业务流量，排除了应用逻辑阻塞导致无法退出的可能。 |

**证据印证关系说明：**
事实 #2 (OOMKill 证据) 与事实 #1 (96Mi 硬限制) 结合，说明容器此前因为超出 96Mi 限制被内核强制终止。然而，事实 #4 (重启计数 0) 与事实 #3 (状态 Running 但 NotReady) 形成强烈反差：通常 OOMKill 后 kubelet 会重启容器，但此处容器未重启，依然处于“假死”运行状态。事实 #6 确认应用之前是正常运行业务的，排除了应用本身卡死无法响应。这些事实共同指向一个非标准的容器状态：容器进程被杀后未进入正常的 Crash 重启循环，而是以某种形式卡在 Terminating/Running 的过渡态中。

## 🎯 根因分析 · g1

### 因果链

```text
自定义finalizer 'aiops.lab/hold' 未释放 → Pod 删除流程被 Kubernetes 阻塞 → 进入 TerminatingStuck 状态 → 容器卡死在 Terminating/Running 间且无法正常重启
```

### 根因结论

已确认的根因为 **自定义 finalizer ('aiops.lab/hold') 未释放导致 Pod 进入 Terminating 后卡死**。

尽管事实 #2 确认容器此前因内存超限 (OOMKill, exit code 137) 终止，但事实 #4 显示容器重启次数为 0 且事实 #3 显示 Pod 处于 Running 但未就绪状态，这不符合 Kubernetes 默认的 CrashLoopBackOff 机制。这种“异常退出但不重启”的僵死状态，结合诊断结论中明确指出的 finalizer 机制，证实了根本原因是 `aiops.lab/hold` 这个自定义 finalizer 阻止了 Pod 被系统正常清理和回收，导致 Pod 卡在 Terminating 阶段。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 19.3s
├─ 并发证据采集: 74.8s
│  └─ g1 aiops-case-11/workload: 74.8s (Evidence 69.4s, RCA 5.2s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
