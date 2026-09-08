## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-ccd39fb548d8` | `container: app`, `last_terminated_reason: Error` | 确认应用容器异常终止 |
| 2 | K8s State | `fact-336855e6ff5f` | `container: app`, `last_exit_code: 78` | 确定异常终止的具体退出码 |
| 3 | K8s Event | `fact-0074c73b6457` | `Warning BackOff 1s (x202 over 44m)` | 证明容器已持续进入 CrashLoopBackOff 状态 |
| 4 | Logging | `fact-38a061289929` (聚合) | `CONFIG_MISSING` (8次, 500错误), `allocated_mib` 维持 0 | 直接揭示应用内部因配置缺失导致的逻辑失败及资源占用情况 |
| 5 | Tracing | `fact-e7ccfbc9ffc1` | `GET /work` `status_code: 500` (trace: `9458884b...`) | 关联日志中的特定 trace_id，确认 500 响应与配置缺失现象一致 |
| 6 | K8s Config | `fact-122fd5dd43ea` | `container: app`, `restart_count: 13` | 量化故障持续时间与重启频率 |

**证据链说明：**
应用容器启动后尝试处理 HTTP 请求，由于缺失配置（`CONFIG_MISSING`）返回 500 状态码并触发内部逻辑退出，最终导致容器以退出码 `78` 终止（证据 1, 2, 4）。Kubernetes 检测到该退出码并不断重启容器，累计 13 次（证据 5, 6），最终 Pod 状态因频繁重启且间隔过短而进入 `CrashLoopBackOff`（证据 3）。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖的配置项缺失 → 初始化/启动逻辑检测到 CONFIG_MISSING 并返回 500 错误 → 进程主动以 Exit Code 78 终止 → 容器被 kubelet 重启，进入 CrashLoopBackOff
```

### 根因结论

已确认根因：应用代码在启动阶段因关键配置缺失（`CONFIG_MISSING`）未能正确初始化，导致请求处理失败并主动异常退出（退出码 78）。

依据：日志中重复出现 `CONFIG_MISSING` 模式（fact-38a061289929），Tracing 确认关联请求返回 500（fact-e7ccfbc9ffc1），且退出码 78（fact-336855e6ff5f）证实了终止是由应用进程主导而非系统资源限制（如 OOMKilled 通常为 137）。

缺失事实：日志未明确指明缺失的具体配置项名称（如具体的 ConfigMap Key 或 EnvVar 变量名），该细节需通过检查 Pod 规范或应用源码确认。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 23.7s
├─ 并发证据采集: 65.9s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 65.9s (Evidence 56.6s, RCA 9.1s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
