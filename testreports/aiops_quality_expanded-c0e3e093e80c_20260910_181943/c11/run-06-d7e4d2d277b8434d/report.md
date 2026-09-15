## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Finalizer 'aiops.lab/hold' 未释放导致 Pod 无法被 GC 删除 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.status`: Terminating (lasts 8m8s); `pod.phase`: Running | 确认 Pod 处于卡滞的 Terminating 状态，未完全终止 |
| 2 | K8s Config | kubernetes | `container.resource_request.memory`: 24Mi; `container.resource_limit.memory`: 96Mi | 容器内存资源请求较低，非内存配置过大所致 |
| 3 | K8s State | kubernetes | `container.last_terminated_reason`: Error; `container.last_exit_code`: 137; `exit Code: 137` | 容器进程因 SIGKILL (Error 137) 被强制终止 |
| 4 | K8s Event | kubernetes | `Normal Killing`: 8m7s kubelet Stopping container app | 记录 kubelet 执行终止操作的最后时间点 |
| 5 | Logging | elasticsearch | pattern `request completed` 4次 (2026-09-11T03:47:09Z ~ 03:47:15Z) | 确认 Terminating 前服务在正常处理 HTTP 请求 |
| 6 | Tracing | tempo | span `GET /work` (1edba7b29f23053616d75e955fa073c8) HTTP 200, 耗时 6μs | 确认终止前最后一次请求成功完成，无上游超时或错误 |
| 7 | Tracing | deepflow | L7 Flow: GET /work HTTP 200 (3次); /ready HTTP 200 (2次) | 证实 L7 层面健康检查与业务请求在终止前均正常通过 |

日志与追踪显示 Terminating 前应用层服务完全正常（HTTP 200, Exit 137），排除业务逻辑错误导致 Pod 无法删除；结合 Pod 状态卡滞且未释放，指向外部调度层面的 Finalizer 阻断。

## 🎯 根因分析 · g1

### 因果链

```text
Finalizer 'aiops.lab/hold' 未释放 → 资源清理被调度层阻断 → Pod 进入 Terminating 但无法 GC → 集群资源无法回收，Pod 状态卡滞
```

### 根因结论

已确认的根因为：Finalizer 'aiops.lab/hold' 未释放导致 Pod 无法被 GC 删除。

当前 Pod (`aiops-case-11/workload`) 处于 Terminating 状态长达 8 分钟未完全删除，但容器进程在 Terminating 前已成功响应了正常的业务请求（HTTP 200）并健康检查通过（日志与追踪事实 #5, #6, #7）。容器的终止是由 kubelet 正常下发 SIGKILL 触发（Exit 137, 事实 #3），说明应用本身无阻塞。Pod 无法从 Terminating 状态退出的原因排除了应用侧崩溃或配置错误，直接指向 Kubernetes 层面的资源清理阻断。这与诊断结论中提到的 Finalizer 'aiops.lab/hold' 未释放导致的 GC 阻塞完全一致。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 18.8s
├─ 并发证据采集: 30.9s
│  └─ g1 aiops-case-11/workload: 30.9s (Evidence 26.8s, RCA 3.9s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
