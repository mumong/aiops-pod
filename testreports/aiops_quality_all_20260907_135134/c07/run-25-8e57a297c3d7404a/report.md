## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | Error | Pod workload-dff5cbc6b-fkzvn 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: Error | 确认容器最后一次终止原因为异常退出 |
| 2 | K8s State | Kubernetes | `container.last_exit_code`: 78 | 明确应用进程主动退出的退出码 |
| 3 | K8s Event | Kubernetes | `Back-off restarting failed container app ... (x198 over 48m)` | 确认 Pod 处于 CrashLoopBackOff 状态 |
| 4 | Logging | Elasticsearch | `pattern`: CONFIG_MISSING, `http_status`: 500, `path`: /work | 应用日志确认启动时因配置缺失报错并返回 500 |
| 5 | Tracing | Deepflow/Tempo | `GET /work` → 500, `span`: `aiops.observed_mode=config_missing_exit` | Trace 数据印证日志中的配置缺失导致请求立即失败 |

证据内容说明：
1. 日志（#4）与 Trace（#5）交叉印证：两者均捕捉到针对 `/work` 端点的 500 错误，且 Trace 明确标注了 `config_missing_exit` 模式，证实应用启动后立即因配置缺失终止。
2. K8s 状态（#1, #2）与事件（#3）结合：确认应用因异常退出（Exit Code 78）且原因归类为 Error，进而触发 Kubelet 的重启机制。

## 🎯 根因分析 · g1

### 因果链
```text
应用启动依赖的配置项缺失 → 应用主动抛出 CONFIG_MISSING 错误并返回 HTTP 500 → 应用进程以 exitCode 78 终止 → Kubelet 触发 CrashLoopBackOff 重启机制
```

### 根因结论
已确认根因为应用启动时依赖的关键配置项缺失。证据链显示，应用启动后检测到配置缺失（日志 fact-1dc34210d4bd），主动终止进程并返回 Exit Code 78 及 HTTP 500 状态（事实 #4, #5）；Kubelet 捕获到容器的 Error 终止状态（事实 #1）后，按照预期重启容器，导致 Pod 陷入 CrashLoopBackOff 状态（事实 #3）。

缺失的确定性事实包括：具体缺失的环境变量名或 ConfigMap key（日志仅概括为 `CONFIG_MISSING`），以及 ConfigMap `workload-code` 的当前实际内容是否与代码预期不匹配。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 16.3s
├─ 并发证据采集: 72.2s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 72.2s (Evidence 61.2s, RCA 10.9s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
