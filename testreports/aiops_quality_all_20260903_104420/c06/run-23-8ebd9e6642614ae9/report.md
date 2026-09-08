## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | 容器 app 启动后执行致命逻辑导致进程主动退出（exit code 2） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `container.last_terminated_reason` | container=app, reason=Error | 证实容器非正常退出，且无 OOMKilled 标记 |
| 2 | K8s State | `container.last_exit_code` | container=app, exit_code=2 | 提供具体的异常退出码，暗示应用层主动报错 |
| 3 | K8s Event | `event.message` | BackOff restarting failed container app... (x223 over 51m) | 证实集群层面对异常退出的观测与重试停滞状态 |
| 4 | Metric | `kube_pod_container_status_waiting_reason` | reason=CrashLoopBackOff, value=1 | 从指标层面确认 Pod 处于等待（重启）状态 |
| 5 | Metric | `kube_pod_container_status_last_terminated_reason` | reason=Error, value=1 | 独立于 K8s API，再次印证最后一次终止原因为 Error |
| 6 | Logging | `log.message` | {"level": "error", "message": "runtime process exiting", "http_status": 500, "path": "/work"} | 提供应用层日志，明确指出进程执行退出逻辑导致 HTTP 500 |

**证据关联分析：**
- K8s 状态（#1, #2）确认容器以 exit code 2 主动退出，Metric（#4, #5）的 Error 原因与 K8s 终止原因完全一致。
- 日志（#6）填补了根本逻辑细节：HTTP `/work` 接口返回 500 的同时进程显式退出（"runtime process exiting"），这与 exit code 2 的现象互为印证，排除了资源或调度导致的外力崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
应用进程启动 → 业务逻辑触发致命退出条件 → 进程以 exit code 2 退出 (返回 500) → 容器进入 Error 状态 → kubelet 触发 CrashLoopBackOff 重试
```

### 根因结论

**已确认的根因：应用代码执行了主动退出逻辑 (exit code 2)。**

- **证据支撑：**
  - Kubernetes 状态显示容器以 `exit_code: 2` 终止，且非 OOMKilled（#1, #2）；
  - Prometheus 指标独立验证了终止原因为 `Error`（#5）；
  - 应用日志直接记录了 `runtime process exiting` 伴随 `http_status: 500` 的事件（#6），明确了异常是由应用业务逻辑处理失败引发的主动退出，而非外部资源或环境异常。
- **结论：** 故障非集群资源、网络或配置引起，而是工作负载代码中特定业务逻辑处理路径上的致命错误。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 20.0s
├─ 并发证据采集: 64.4s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 64.4s (Evidence 57.4s, RCA 6.8s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
