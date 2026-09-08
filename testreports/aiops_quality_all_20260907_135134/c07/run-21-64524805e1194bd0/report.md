## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | Pod workload-dff5cbc6b-fkzvn 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning BackOff 3m1s (x175 over 42m)` kubelet 报告重启失败 | 证实容器异常退出并持续进入退避重启循环 |
| 2 | K8s State | kubernetes | `container.last_terminated_reason: Error`, `container.last_exit_code: 78` | 证实容器因错误代码 78 异常终止 |
| 3 | K8s Config | kubernetes | `container.resource_request.memory: 24Mi`, `resource_limit.memory: 96Mi` | 提供资源上下文，资源限制与 OOM 无关 |
| 4 | Logging | elasticsearch | `pattern: http_request ... message: CONFIG_MISSING ... http_status: 500` (8次) | 提供决定性业务错误日志，表明应用因缺少配置而启动失败 |
| 5 | Tracing | deepflow+tempo | `flow: GET /work -> 500`, `span: aiops.observed_mode: config_missing_exit`, `trace_id: 80eb7bda337870843840252aa8d6463a` | 日志与 Trace 关联，证实应用逻辑错误导致进程退出，形成闭环证据 |

**证据关联说明：**
Kubernetes 层面的 `CrashLoopBackOff` 状态（证据 1, 2）由应用层逻辑驱动；Logging 发现的 `CONFIG_MISSING` 错误（证据 4）与 Tracing 中的 `config_missing_exit` 模式（证据 5）高度一致，共同证明容器退出并非因为资源不足或系统崩溃，而是应用配置缺失导致的业务启动失败。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置缺失 → 应用启动失败（进程异常退出） → 容器异常终止 (CrashLoopBackOff) → Pod 处于 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为**应用配置缺失**。
日志中明确捕获了 `CONFIG_MISSING` 错误模式，且伴随 `http_status: 500`；结合 Tracing 数据中 `aiops.observed_mode: config_missing_exit` 的状态指示，充分证实应用进程因缺少配置而无法启动并主动退出。该退出行为被 Kubernetes 识别为异常终止（Exit Code 78），进而触发 `CrashLoopBackOff` 状态。当前证据链完整，足以支撑根因结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 26.6s
├─ 并发证据采集: 69.8s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 69.8s (Evidence 62.1s, RCA 7.5s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime, pod-oomkilled
