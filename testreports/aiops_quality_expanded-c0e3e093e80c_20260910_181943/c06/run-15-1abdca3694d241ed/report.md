## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | Pod aiops-case-06/workload-7679bcf76-n5vp8 处于 CrashLoopBackOff 状态，App 容器持续崩溃 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `status=CrashLoopBackOff`, `exit_code=2` (`fact-60291b31c0d9`, `fact-d1cbaaa3dcec`, `fact-397cde0e260d`) | 直接展示 App 容器的当前终态，确认为进程级崩溃且被 Kubelet 重启失败 |
| 2 | K8s Event | Kubernetes | `BackOff restarting failed container app in pod workload-7679bcf76-n5vp8_aiops-case-06` 已重复 157 次 (`fact-c1f3e9d860b8`) | 证明 Pod 处于持续的故障循环中，等待时间已拉长至 5m0s (`fact-639e3d1c07b5`) |
| 3 | K8s Config | Kubernetes | `memory_request=24Mi`, `memory_limit=96Mi` (`fact-20bbb9d2daaf`, `fact-6f578175cd6e`) | 资源限制极低，排除了常规内存溢出导致的 OOMKilled（若因内存则 exit_code 通常伴随 OOMKilled） |
| 4 | Logging | Elasticsearch | `/work` 路径持续返回 `http_status=500`，并触发 `runtime process exiting`，出现 3 次 (`fact-252eebff744f`) | 日志直接证实了应用进程在返回错误后立刻退出的因果关系 |
| 5 | Tracing | Deepflow/Tempo | `GET /work` 请求返回 `500`，且关联 Span 显示 `aiops.observed_mode=runtime_exit` (`fact-31b0e51382df`) | 追踪数据在请求级别印证了进程异常退出的事实，且耗时约 4.1s，说明并非瞬时网络断开 |
| 6 | Metrics | Prometheus | `kube_pod_container_status_waiting_reason="CrashLoopBackOff"` 值为 1 (`fact-2207291d7725`) | 监控指标与 K8s 状态和日志现象保持一致，无数据断层 |

上述证据形成了完整闭环：日志与追踪明确记录了 `/work` 请求在处理过程中发生 500 错误并直接退出进程（证据 #4, #5），随后 K8s 层面捕获到该容器以 `exit_code=2` 终止（证据 #1），最终触发了 Kubelet 的 CrashLoopBackOff 机制（证据 #2, #3）。

## 🎯 根因分析 · g1

### 因果链

```text
应用处理 /work 请求时发生逻辑错误（代码异常或依赖缺失） → 进程捕获内部错误并返回 HTTP 500 → 进程以 Exit Code 2 强制退出 → 触发 Kubelet 频繁重启失败，Pod 进入 CrashLoopBackOff
```

### 根因结论

**已确认的根因**是：Pod `aiops-case-06/workload-7679bcf76-n5vp8` 中的 App 容器（`app`）在处理 `/work` 端点时发生了内部程序异常。

该异常直接导致进程以 `Exit Code 2` 退出（证据 #1, #4），从而引发了 Kubernetes 默认的容器重启策略，使 Pod 陷入 `CrashLoopBackOff` 循环（证据 #2, #3）。

**未知/缺失信息**：目前只能确认“应用内部异常”这一表象，由于缺乏应用堆栈跟踪（Stack Trace）或具体的 Python 错误日志，**无法确认**导致 `/work` 接口返回 500 的具体 Python 代码逻辑或具体的依赖缺失。现有工具事实（K8s State, Logging, Tracing）已足以解释当前的故障状态，但不足以支撑对应用代码层面的精确定位。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 20.6s
├─ 并发证据采集: 74.0s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 74.0s (Evidence 65.2s, RCA 8.7s)
└─ 汇总总结: 13.5s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
