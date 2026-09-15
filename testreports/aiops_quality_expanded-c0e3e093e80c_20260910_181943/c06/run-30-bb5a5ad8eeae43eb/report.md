## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | Pod workload-7679bcf76-n5vp8 处于 CrashLoopBackOff 状态 (重启17次)，容器 app 退出码 2，并频繁抛出 'runtime process exiting' 错误。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `container.waiting_reason` | `CrashLoopBackOff` | 确认 Pod 处于异常重启状态 |
| 2 | K8s State | `container.last_terminated_reason` | `Error` | 标识终止原因为通用错误 |
| 3 | K8s Event | `BackOff` | `Back-off 5m0s restarting failed container=app...` | 验证重启间隔拉长，符合 CrashLoopBackOff 特征 |
| 4 | K8s State | `container.last_exit_code` | `2` | 明确容器进程非正常退出 |
| 5 | Logging | `http_request` (error) | `message="runtime process exiting", http_status=500, path="/work"` | 直接定位应用进程崩溃时的上下文请求路径 |
| 6 | K8s Config | `resource_limit` | `memory: 96Mi, cpu: 200m` | 提供资源边界背景（低配环境），但非直接致死因素 |
| 7 | K8s Event | `ContainersNotReady` | `ContainersNotReady: [app]` | 确认容器虽在运行但处于不健康状态 |
| 8 | Metric | `kube_pod_container_status_restarts_total` | `17` | 量化确认重启频次较高 |
| 9 | Metric | `kube_pod_container_status_last_terminated_reason` | `reason="Error"` | 独立确认最后一次终止原因为 Error |

**证据互证与冲突分析：**
Kubernetes 状态的 `CrashLoopBackOff` 与 `exit_code=2` 为应用崩溃提供了系统级事实支持；Elasticsearch 的 error 日志直接记录了进程在 `/work` 端点处理请求时发生 `runtime process exiting`，与 K8s 记录的错误退出原因高度吻合。Prometheus 指标作为独立观测源，验证了 17 次重启及终止原因为 Error 的事实，未出现跨维度证据冲突。日志中 `allocated_mib` 为 0 且未显示 OOM 相关指标，排除了典型的内存超限导致 Kernel 杀进程（Exit 137）的可能。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码逻辑缺陷 → 处理 /work 请求时触发未捕获异常 → 容器进程强制退出 (Exit 2) → CrashLoopBackOff
```

### 根因结论

已确认根因为应用代码缺陷。证据链表明，应用在处理 `/work` 端点的 HTTP 请求时，发生了未捕获的致命异常导致进程直接退出（退出码 2），Kubernetes 的重试机制触发了 CrashLoopBackOff 状态。该结论得到了 K8s 退出码、Pod 状态、Prometheus 指标及 Elasticsearch 错误日志的四维交叉印证。由于缺少具体的 Python Traceback 堆栈细节，根因精确到“代码逻辑缺陷”级别。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 21.5s
├─ 并发证据采集: 64.0s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 64.0s (Evidence 55.2s, RCA 8.7s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
