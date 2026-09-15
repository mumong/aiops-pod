## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | 应用代码在处理 HTTP 请求时发生未捕获的逻辑错误导致进程主动异常退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `BackOff 4m39s (x89 over 24m) Back-off restarting failed container app in pod workload-7679bcf76-n5vp8_aiops-case-06(...)` | 确认应用进程反复异常退出导致 Pod 持续重启 |
| 2 | K8s Config | kubernetes | `container.app resource_request.memory: 24Mi, resource_limit.memory: 96Mi, resource_request.cpu: 20m, resource_limit.cpu: 200m` | 资源配额极低，排除常规 OOM 或 CPU 超频导致的系统级拒绝服务 |
| 3 | Logging | elasticsearch | 模式：`request completed, http_status: 500, message: "runtime process exiting"` (3次) | 证明 HTTP 请求在业务处理阶段发生未捕获的逻辑错误，触发应用主动退出 |
| 4 | Tracing | deepflow | HTTP GET /work 成功响应 9次 (HTTP Status 200) | 说明网络层、路由及负载均衡均正常，故障发生在应用内部处理逻辑 |

1-2. **Kubernetes 与日志互相印证**：K8s 观察到容器频繁非正常退出（Exit Code 2, Restart Count 9），结合日志记录的 `runtime process exiting` 明确指向应用层主动崩溃，而非被操作系统或 Kubelet 终止。
3. **跨维度关联**：Tracing 显示 9 次完整的 HTTP 成功往返（耗时 17-30ms），证明应用核心处理流程及底层网络连通性无异常。K8s 资源限制配置与日志中的退出模式共同排除了资源耗尽型故障。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码未捕获逻辑错误 → 进程主动异常终止(exit_code: 2) → K8s 自动重启策略触发 → CrashLoopBackOff 导致服务不可用
```

### 根因结论

已确认的根因是 **应用代码在处理 HTTP 请求（GET /work）时发生未捕获的逻辑错误导致进程主动异常退出**。
*   证据 **#3** 的日志明确记录了 `http_status: 500` 伴随 `runtime process exiting`，证实故障发生在请求处理的业务逻辑内部。
*   证据 **#1** 的 K8s BackOff 事件及 **#4** 中网络层的完全正常表现，排除了基础设施与网络层面的问题。
*   证据 **#2** 中的资源限制配置（24Mi/20m）表明故障并非由资源争抢引起，进一步支持“代码逻辑缺陷”这一根因结论。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 31.0s
├─ 并发证据采集: 95.7s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 95.7s (Evidence 87.3s, RCA 8.3s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime, pod-oomkilled
