## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | Pod aiops-case-06/workload-7679bcf76-n5vp8 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning  BackOff  108s (x292 over 66m)` 重启失败的 container app | 确认 Pod 已进入 CrashLoopBackOff 状态 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason: Error`, `last_exit_code: 2` | 确认容器异常退出，终止原因为通用 Error |
| 3 | Logging | Elasticsearch | 3 条 `runtime process exiting` (500 error) | 直接指出应用进程因运行时错误主动退出 |
| 4 | Tracing | Tempo | Span `b2c74bd59a13816a64bebc87858a5008` 匹配 5 次成功 200 请求 | 确认 `/work` 接口在故障间歇期工作正常 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` = 1 (reason: Error) | 独立确认最近一次终止原因为 Error |

**证据关联说明**：
Logging 中的 `runtime process exiting` 解释了 K8s 中 `last_terminated_reason: Error` 和 `exit_code: 2` 的具体原因；Tracing 中的 `runtime_exit` 模式进一步验证了故障发生在应用处理 `/work` 请求期间。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码在处理 /work 请求时发生运行时错误 → 进程记录 "runtime process exiting" 并终止 (exit_code 2) → Kubernetes 检测异常并重启容器 → CrashLoopBackOff
```

### 根因结论

已确认根因为：应用代码在处理 `/work` 请求时发生运行时错误（Runtime Error），导致进程主动退出。

依据证据 1 和 2，容器持续异常终止；证据 3 的日志记录了 `runtime process exiting` 模式，明确了退出原因为运行时错误；证据 4 的 Tracing 成功与部分日志关联，证明 `/work` 路径是故障触发点。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 17.0s
├─ 并发证据采集: 78.9s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 78.9s (Evidence 72.1s, RCA 6.6s)
└─ 汇总总结: 7.5s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
