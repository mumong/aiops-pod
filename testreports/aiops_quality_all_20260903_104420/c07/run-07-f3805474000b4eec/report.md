## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | Pod workload-dff5cbc6b-kmfxx 处于 CrashLoopBackOff 状态，容器 app 反复退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `container.waiting_reason` | container "app" reason: CrashLoopBackOff | 确认应用容器处于非正常等待状态 |
| 2 | K8s State | `container.last_terminated_reason` | container "app" reason: Error | 确认上次退出的直接原因为错误 |
| 3 | K8s Event | `event.message` | Warning BackOff ... back-off 5m0s restarting failed container=app | 确认 Kubernetes 因重启失败正在退避 |
| 4 | K8s State | `container.last_exit_code` | container "app" exit_code: 78 | 记录进程异常退出的具体错误码 |
| 5 | Logging | `log.message.pattern` | event: http_request, error: CONFIG_MISSING, http_status: 500, path: /work | 日志明确记载处理请求时配置缺失并返回 500 |
| 6 | Tracing | `l7_flow` | src_ip: 172.16.104.9 -> dst_ip: 172.16.104.15, protocol: HTTP, response_code: 500, trace_id: da9999ae734835080b2f252e105e1ce7 等 | 网络流证明服务在处理 `/work` 请求时持续失败 |
| 7 | K8s State | `container.resource_limit.memory` | container "app" limit: 96Mi | 确认资源限制，排除因 OOM 导致的异常退出 |

日志中记录的 `CONFIG_MISSING` 模式与 Tracing 中 `da9999ae734835080b2f252e105e1ce7` 等追踪 ID 一致，表明在 HTTP 请求（GET /work）期间因配置缺失导致应用抛出 500 错误。该错误直接导致进程以 `exit_code: 78` 退出，进而触发 K8s 的重启机制并最终进入 `CrashLoopBackOff`。由于资源限制（96Mi）正常，排除资源耗尽因素。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动或请求处理逻辑中缺失关键配置文件 → HTTP 请求处理失败并返回 500 状态码 → 进程检测到配置缺失并主动退出（Exit Code 78） → Kubernetes 重启策略触发并进入 CrashLoopBackOff
```

### 根因结论

**已确认根因**：应用进程依赖的配置文件缺失（日志报错 `CONFIG_MISSING`）。当应用尝试处理 `/work` 请求时，因缺少关键配置抛出 HTTP 500 错误，并随即以退出码 78 异常退出。该非零退出码触发了 Kubernetes 的重启机制，导致 Pod 在启动和退出之间反复循环并最终进入 `CrashLoopBackOff` 状态。

**未确认事项**：
1. 缺失的配置文件的具体文件名或 ConfigMap 名称（需对比 Pod YAML 中 `volumes/configMap` 的引用与实际挂载情况）。
2. 为何应用在启动阶段未立即检测到配置缺失，而是直到收到第一个请求（处理 `/work` 时）才触发退出逻辑。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 20.7s
├─ 并发证据采集: 55.2s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 55.2s (Evidence 45.5s, RCA 9.5s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
