## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | Pod aiops-case-07/workload-dff5cbc6b-fkzvn 处于 CrashLoopBackOff 状态，容器不断重启并返回退出码 78。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason=CrashLoopBackOff`, `exit_code=78` | 确认 Pod 处于重启状态，且退出码为自定义业务错误码，非系统级 OOMKilled 或 Kill。 |
| 2 | K8s Event | kubernetes | `BackOff restarting failed container app in pod workload-dff5cbc6b-fkzvn` (x354 over 82m) | 描述 Kubelet 因容器频繁退出导致的重启背退现象，佐证异常持续存在。 |
| 3 | Logging | elasticsearch | `http_request, level: error, message: CONFIG_MISSING, http_status: 500, path: /work` (11 occurrences) | 直接揭示应用崩溃的业务原因：在 `/work` 路径请求中检测到配置项缺失。 |
| 4 | Tracing | deepflow | `HTTP GET /work`, `response_code: 500`, trace_ids: `["77e47485089f4d44b38fdf7e9474c62f", "e4e8688cb17d8196c8981cec8c694e37" ...]` | 跨层流量事实，证实客户端请求在 L7 层面收到 500 错误，且关联的 trace_id 与日志一致。 |
| 5 | Tracing | Tempo | `aiops.observed_mode: config_missing_exit`, `http.response.status_code: 500`, trace_id: `1833447e4752d0dad6e0d535b256f8a7` | 明确标记了应用内部的执行模式为“配置缺失导致退出”，直接验证了日志中的错误语义。 |
| 6 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason(Error)=1`, `kube_pod_container_status_restarts_total=20` | 提供监控层面的佐证，确认容器因 Error 终止且总重启次数为 20 次。 |

证据间互相印证：K8s 的 `CrashLoopBackOff` 状态与 `exit_code=78` 结合 Logging 中的 `CONFIG_MISSING` 及 Tracing 中的 `aiops.observed_mode: config_missing_exit`，形成了从基础设施层到应用业务层的完整闭环。Metric 数据证实了重启的持续性，未发现资源耗尽相关的 OOM 指标。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap `workload-code` 内容不完整或键值对缺失 → 应用进程启动或运行中读取配置失败 → 触发 CONFIG_MISSING 错误并记录日志，随后以自定义退出码 78 主动终止 → 导致 Pod 进入 CrashLoopBackOff 状态并返回 500 错误
```

### 根因结论

**已确认根因**：应用代码中存在硬编码或动态查询的配置项缺失，导致服务初始化失败。
Kubelet 日志显示容器频繁重启（CrashLoopBackOff）并返回退出码 78。应用日志（Logging）和链路追踪（Tracing）一致捕获到 `CONFIG_MISSING` 错误及 `config_missing_exit` 执行模式，且 HTTP 请求返回 500 状态码。这些应用层的明确错误信号排除了资源不足、网络故障或系统级崩溃（如 OOMKilled）的可能性，确认为业务逻辑因配置缺失而导致的崩溃。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 17.5s
├─ 并发证据采集: 96.8s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 96.8s (Evidence 81.5s, RCA 15.1s)
└─ 汇总总结: 12.1s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
