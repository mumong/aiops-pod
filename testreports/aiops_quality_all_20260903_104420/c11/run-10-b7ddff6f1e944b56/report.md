## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 持续处于 Terminating 状态，已停滞约15分钟，无法正常删除 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.status`: Terminating (lasts 15m) | 直接展示当前停滞的异常状态，与现象描述一致 |
| 2 | K8s Config | kubernetes | `pod.metadata.finalizers`: ['aiops.lab/hold'] | 根本阻塞机制：自定义 Finalizer 阻止了 API Server 执行物理删除 |
| 3 | K8s Event | kubernetes | `event.message`: "Stopping container app" (15m前) | 证明容器已尝试正常退出，非因容器状态异常导致 |
| 4 | Logging | elasticsearch | `log.message`: "request completed", `http_status`: 200 (22:31:06 - 22:31:12) | 证明在容器退出前后，应用逻辑层面正常完成了请求处理，排除了业务代码异常 |
| 5 | Tracing | tempo | `trace_id`: 75c4028b11532f074defb107fd297f49, `http.response.status_code`: 200 | 关联日志中相同的 trace_id，进一步确认应用在删除触发前正常响应 |

证据表明：Pod 状态被强制锁定在 `Terminating`。尽管日志（#4）和链路追踪（#5）证明应用在近期（22:31左右）仍正常处理 HTTP 请求，但 K8s Event（#3）显示容器在15分钟前已停止。由于存在自定义 `Finalizer`（#2），只要该标记未被上游控制器正常移除，API Server 就会无限期挂起清理流程，导致删除操作永久阻塞。

## 🎯 根因分析 · g1

```text
未确认的上游逻辑故障（未移除 Finalizer） → API Server 阻止资源清理 → 状态卡在 Terminating → 无法删除 Pod
```

### 根因结论

**证据不足**。

1. **已确认的事实**：Pod 确实被名为 `aiops.lab/hold` 的自定义 Finalizer 阻止删除，且容器应用（HTTP 200 / 正常退出）与网络层（DeepFlow Tracing 数据）均无异常，排除了因应用 Crash、OOM（Exit Code 137 在日志关联时间窗内未触发）或网络问题导致的直接终止。
2. **缺失的决定性事实**：无法解释为何控制器（Controller/Operator）在容器正常退出后，没有在 `15m` 内移除该 Finalizer。输入数据中缺失针对该 Finalizer 对应管理控制器的状态日志或事件监控。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 12.9s
├─ 并发证据采集: 69.1s
│  └─ g1 aiops-case-11/workload: 69.1s (Evidence 61.2s, RCA 7.8s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
