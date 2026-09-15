## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod aiops-case-v13/workload stuck in Terminating state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Normal Killing Stopping container app` (fact-5f375a1c2607) | 确认 kubelet 发起了终止信号，与 Pod Terminating 状态同步。 |
| 2 | K8s State | Kubernetes | `phase: Running`, `status: Terminating (lasts <invalid>)` (fact-10ed33f930d8, fact-4fedb353c72a) | 状态不一致：Pod 标记为终止中但 K8s 内部状态仍为 Running，表明容器未退出。 |
| 3 | Logging | Elasticsearch | `application started` (fact-e73acfc8586a), `SIGTERM received; waiting` (fact-d1c20dafb330) | 应用程序捕获到 SIGTERM 后进入等待状态，未执行退出逻辑，解释了为何不响应 K8s 终止请求。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 0` (fact-7304ba6593aa) | 重启数为 0，排除了因 OOMKilled 或 CrashLoop 导致的非正常退出。 |

证据链显示：Pod 收到了 SIGTERM 信号（日志与事件证实），但进程并未退出（K8s 状态与重启数证实），而是进入了等待状态（日志证实），导致 Pod 僵死在 Terminating 阶段。

## 🎯 根因分析 · g1

### 因果链

```text
Application PreStop logic deadlock → Application catches SIGTERM and enters infinite loop waiting for `/state/teardown-requested` file → Container fails to exit within terminationGracePeriodSeconds (3900s) → Pod stuck in Terminating state
```

### 根因结论

已确认根因为 **应用程序 PreStop 逻辑死锁 (Application PreStop logic deadlock)**。

应用程序在注册 SIGTERM 处理器后进入无限循环，等待文件 `/state/teardown-requested` 的出现。当 Kubelet 发送终止信号时，进程被该阻塞逻辑困住，无法在规定的 `terminationGracePeriodSeconds` 内退出，导致 Pod 永远卡在 Terminating 状态。
*   **支持证据**：
    *   `[3]` 日志记录 `SIGTERM received; waiting` (fact-d1c20dafb330) 直接证明了进程捕获信号后进入等待阻塞。
    *   `[2]` 异常状态 `status: Terminating` 与 `phase: Running` 共存 (fact-4fedb353c72a, fact-10ed33f930d8) 证实了终止流程的停滞。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 33.2s
├─ 并发证据采集: 34.5s
│  └─ g1 aiops-case-v13/workload: 34.4s (Evidence 25.4s, RCA 8.9s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
