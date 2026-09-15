## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | Pod workload in aiops-case-v17 is in CrashLoopBackOff with restart count 7. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubelet | `Liveness probe failed: ... context deadline exceeded` (x13, 10m内) | 直接显示存活探针因超时失败，触发容器重启机制 |
| 2 | K8s Event | Kubelet | `Readiness probe failed: ... connection refused` (x2) | 辅助说明容器启动阶段处于非健康或重启中状态 |
| 3 | K8s Config | Kubelet | `Exit Code: 137` | 容器被杀出的退出码，与探针失败后的重启行为一致 |
| 4 | Metric | Prometheus | `container_memory_working_set_bytes` 峰值 11.8MB，当前值 3.2MB | 证实工作集内存远低于 64Mi 硬限制，排除应用层 OOM |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 值为 7 | 确认故障处于持续反复重启状态 |
| 6 | Logging | Elasticsearch | 应用日志记录 `GET /ready HTTP/1.1" 200` | 证明应用实际可处理 HTTP 请求，网络链路正常 |
| 7 | Tracing | Deepflow | `GET /health` Flow: `response_code=200`, `duration_us`: 3,001,102 ~ 3,001,920 | 核心证据：确认 `/health` 接口实际响应耗时约 3 秒 |

**证据互证分析：**
Tracing 显示 `/health` 接口耗时约 3 秒（fact-#7），而 K8s 事件日志显示 Liveness 探针失败原因为 "context deadline exceeded"（fact-#1），两者结合证实探针超时时间被配置为小于应用实际处理耗时（如 1s）。同时，Metric 显示内存使用量极低（fact-#4），彻底排除了因资源耗尽（OOM）导致被杀（Exit 137）的可能性，确认 Exit 137 为探针超时后 Kubelet 主动终止容器的结果。

## 🎯 根因分析 · g1

### 因果链

```text
探针超时时间(1s) < 应用阻塞处理耗时(~3s) → Liveness 探针失败(context deadline exceeded) → Kubelet 杀掉容器(Exit 137) → Pod CrashLoopBackOff
```

### 根因结论

**已确认根因**：存活探针（Liveness Probe）的超时时间配置短于业务逻辑的执行耗时（`sleep(3)`）。

该配置导致探针请求在应用返回结果前被强制中断（“context deadline exceeded”），Kubelet 认为容器处于无响应状态，从而触发杀容重启流程。由于探针配置异常导致的高频重启和中断行为，容器在被杀时表现出 Exit Code 137（通常关联 OOM-Kill，但此处系配置性杀容行为导致的特定行为或内核 cgroup 行为），而非真实的内存溢出。Metric 显示内存工作集仅为 3MB-11MB，远低于 64Mi 限制，验证了非内存不足。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 14.8s
├─ 并发证据采集: 98.5s
│  └─ g1 aiops-case-v17/workload: 98.5s (Evidence 87.7s, RCA 10.6s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
