## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | Pod workload-7679bcf76-w9s9c 处于 CrashLoopBackOff 状态，重启次数为 5 次。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s Event | `Warning BackOff ... Back-off restarting failed container app` (x21 over 5m51s) | 确认应用容器处于频繁重启的异常状态 |
| 2 | K8s State | K8s State | `container.app` 终止原因为 `Error`，退出码 `2` | 证实进程因内部错误非正常退出 |
| 3 | Logging | Elasticsearch | `runtime process exiting` (Error, 500) 重复出现 4 次，`allocated_mib` 保持 0 | 直接记录崩溃发生时的应用层状态 |
| 4 | Tracing | Deepflow | L7 Flow: `GET /work` 返回 `500` 错误，持续约 10-18ms | 从网络流量侧印证 `/work` 请求引发 500 错误 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = `5` | 量化验证容器的重复退出行为 |
| 6 | K8s Config | K8s Config | 内存 Request: `24Mi`, Limit: `96Mi` | 提供资源边界参考，数值极低但无明显溢出记录 |

**证据关联分析**：
Kubernetes 状态与日志证据高度一致，`Exit Code 2` 和 `runtime process exiting` 相互印证了应用进程的意外终止。网络流量（Trace）与日志的时间点重合，证实了崩溃发生在处理 `/work` 接口期间，排除了启动失败的可能，指向了运行时的业务逻辑错误。

## 🎯 根因分析 · g1

### 因果链

```text
应用逻辑/运行时错误 → /work 接口处理时进程异常退出(Error 500) → 容器被 OOM Killer 或应用逻辑终止(Exit 2) → Kubelet 持续重启触发 CrashLoopBackOff
```

### 根因结论

已确认根因：**应用进程在处理 HTTP 请求（`/work` 端点）时发生内部运行时崩溃（`runtime process exiting`），以退出码 2 异常终止，导致 Pod 进入 `CrashLoopBackOff` 状态。**

*   **依据**：日志明确捕获到 `runtime process exiting` 错误（证据 #3）；Trace 证实了该端点请求返回了 500 错误（证据 #4）；K8s 状态显示容器反复以 Error 退出（证据 #1, #2）。
*   **局限**：当前证据仅证实了崩溃发生及其直接后果，未能捕获崩溃前的完整堆栈信息（如内存分配失败的具体位置），因为获取上一个崩溃容器完整日志的工具未成功返回匹配结果。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 18.2s
├─ 并发证据采集: 58.4s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 58.4s (Evidence 50.5s, RCA 7.7s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
