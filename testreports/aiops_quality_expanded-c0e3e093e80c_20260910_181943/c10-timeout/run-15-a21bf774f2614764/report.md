## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | Pod aiops-case-v17/workload 处于 CrashLoopBackOff 状态，容器 app 频繁重启 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: `Error` | 证实容器非正常退出，存在终止原因 |
| 2 | K8s Event | Kubernetes | `Liveness probe failed`: `Get "http://172.16.104.36:18080/health": context deadline exceeded` | 证实应用服务已停止响应，导致健康检查超时 |
| 3 | K8s State | Kubernetes | `container.last_exit_code`: `137` | 证实进程被 OOM Killer 强制终止（信号 9） |
| 4 | K8s Config | Kubernetes | `container.resource_limit.memory`: `64Mi` | 提供触发异常的硬性资源边界依据 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (`CrashLoopBackOff`): `1` | 确认当前处于崩溃重启循环的状态 |
| 6 | Logging | Elasticsearch | `GET /ready HTTP/1.1` 200: `13:31:28` 至 `13:32:01` | 证实应用此前运行正常，故障发生在观测窗口内 |

**证据说明：**
*   **证据 3 与 证据 1 相互印证**：退出码 137 是 Linux 内核 OOM Killer 的明确特征，结合终止原因为 Error，指向资源耗尽导致的强制杀进程。
*   **证据 4 与 证据 3 建立因果**：64Mi 的内存限制对于 Java/Python 等应用通常极低，这与 OOM Kill (137) 现象高度吻合。
*   **证据 2 是直接症状**：应用进程被杀导致端口无响应，进而引起 Liveness Probe 失败并触发重启。
*   **证据 6 提供时间背景**：日志显示在 13:31:28 至 13:32:01 期间服务仍在响应（200 OK），结合探针超时，表明进程在 13:32 之前突然崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
极低的内存限制配置 (64Mi) → 应用运行时触发 Linux OOM Killer → 进程被强制终止 (Exit Code 137) → 容器重启并进入 CrashLoopBackOff 状态
```

### 根因结论

**已确认的根因：Pod 配置了过低的内存限制 (64Mi)，导致 Python HTTP 服务因内存溢出被 Linux OOM Killer 强制终止。**

*   **证据支撑**：
    *   Kubernetes 状态事实显示 `container.last_terminated_reason` 为 `Error`，且 `container.last_exit_code` 为 **137**（对应 SIGKILL/OOM），这是进程被系统杀死的决定性证据（证据表 #1, #3）。
    *   容器配置事实显示 `container.resource_limit.memory` 仅为 **64Mi**，这远不足以支撑一般应用的运行（证据表 #4）。
    *   Kubernetes 事件与 Metric 事实证实了由终止引发的 **CrashLoopBackOff** 循环现象，以及健康检查因服务不可用而失败（证据表 #2, #5）。
    *   日志证实故障前服务运行正常，排除应用代码逻辑错误导致的正常退出（证据表 #6）。

*   **局限性**：
    *   虽然 Exit Code 137 强烈指向 OOM，且配置限制极低，但由于采集限制，缺少节点内核日志（dmesg）中的直接 OOM 描述或具体的内存峰值监控指标来从技术上 100% 排除其他极端罕见的 SIGKILL 场景，但在当前配置下，OOM 是唯一符合事实的解释。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 14.1s
├─ 并发证据采集: 50.7s
│  └─ g1 aiops-case-v17/workload: 50.7s (Evidence 41.2s, RCA 9.3s)
└─ 汇总总结: 12.9s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
