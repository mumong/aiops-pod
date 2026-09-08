## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | Error | Pod workload-dff5cbc6b-fkzvn 处于 CrashLoopBackOff 状态，容器反复以 exit code 78 退出，当前等待重启中。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s (fact-c1cf4b8b851c) | container app 最后退出码: 78 | 直接证明进程异常终止，且非系统级 OOM 或错误，指向应用层逻辑退出。 |
| 2 | K8s Event | K8s (fact-8b9559489334) | BackOff: 71s (x423 over 95m)，重启失败容器 app | 证实应用处于 CrashLoopBackOff 循环，且持续时间较长。 |
| 3 | Logging | Elasticsearch (fact-216746689689 等) | 8 条 `http_request` 错误日志：`{"event":"http_request","level":"error","message":"CONFIG_MISSING","http_status":500,"path":"/work"}` | 核心因果证据，确认应用在处理 `/work` 请求时因 `CONFIG_MISSING` (配置缺失) 报错。 |
| 4 | Tracing | Tempo (fact-2fbfefe6f9c6) | Span: `GET /work`, status: 500, attribute `aiops.observed_mode: config_missing_exit` | 与日志事实互相印证，在 Trace 链路中确认请求因配置缺失导致应用主动退出。 |
| 5 | Tracing | Deepflow (fact-243365c61bf3) | 8 条 HTTP L7 Flow: `GET /work`, response_status: 500, src_ip: 172.16.104.27, dst_ip: 172.16.104.7 | 证实该错误有持续的流量输入，并非偶发测试，且错误响应发生在 Pod IP (172.16.104.7) 上。 |
| 6 | Metric | Prometheus (fact-2cd227f1042d) | `kube_pod_container_status_last_terminated_reason` = 1 (reason: Error) | 佐证容器最近一次终止原因为 Error，与 Kubernetes 事实一致。 |

**证据关联说明：**
1. K8s 事实 (No.1, No.2) 展示了集群层面的崩溃现象。
2. 日志 (No.3) 和 Trace 事实 (No.4, No.5) 共同揭示了具体的失败机制：应用在处理 `/work` 请求时因配置缺失 (`CONFIG_MISSING`) 而终止 (exit code 78)。
3. Metric 事实 (No.6) 进一步佐证了该容器的错误终止状态。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 容器内关键配置文件 /work 缺失 → 应用启动/运行中检测到配置缺失直接退出 (exit code 78) → Kubelet 判定容器失败并进入 BackOff 重启机制 → Pod 处于 CrashLoopBackOff 状态
```

### 根因结论

**已确认根因**：应用启动或运行时依赖的关键配置文件 (`/work`) 缺失。
**证据**：日志与 Trace 事实中明确记录 `message: "CONFIG_MISSING"` 及 `http_status: 500`，且应用返回了特定的退出码 78。这些事实共同证实了应用因缺少配置而终止，进而引发 CrashLoopBackOff。
**证据编号引用**：日志聚合事实 `fact-216746689689`、Tempo Trace 事实 `fact-2fbfefe6f9c6`、K8s 退出码事实 `fact-c1cf4b8b851c`。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 12.6s
├─ 并发证据采集: 57.8s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 57.8s (Evidence 47.6s, RCA 10.1s)
└─ 汇总总结: 12.6s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime, pod-imagepull-failed, pod-oomkilled, pod-config-error
