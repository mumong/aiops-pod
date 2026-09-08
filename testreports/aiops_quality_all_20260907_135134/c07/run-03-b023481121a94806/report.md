## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | workload-dff5cbc6b-fkzvn 容器处于 CrashLoopBackOff 状态，反复重启并退出，伴随 HTTP 500 错误。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.app: `reason=Error`, `waiting_reason=CrashLoopBackOff`, `exit_code=78`, `restart_count=5`, `phase=Running` | 确认容器启动失败、因配置或应用错误退出并被 K8s 回收重启的异常状态 |
| 2 | K8s Event | kubernetes | waiting message: `back-off 2m40s restarting failed container=app` | 证明 K8s 已介入并正在执行指数退避重启逻辑 |
| 3 | K8s Config | kubernetes | requests/limits: CPU 20m/200m, Memory 24Mi/96Mi | 资源配额合理，排除 OOM 或 CPU 限频导致的崩溃风险 |
| 4 | Logging | elasticsearch | `pattern=CONFIG_MISSING`, `http_status=500`, `path=/work`, `count=8`, `first=14:35:23`, `last=14:38:49` | 核心归因证据：应用明确声明因缺少配置退出，时间线与容器重启周期重合 |
| 5 | Tracing | tempo | `span=GET /work`, `status=500`, `observed_mode=config_missing_exit`, `trace_id=b3559561ac9acd05071836e31ce2b090` | 链路确认请求被应用直接拦截并返回 500，与日志中的 `CONFIG_MISSING` 一致 |
| 6 | Metric | prometheus | `reason=CrashLoopBackOff`(val 1), `reason=Error`(val 1), `restarts=5` | 独立指标再次确认了当前的 CrashLoop 状态与重启次数，作为 K8s 状态的交叉验证 |

**证据关联性说明：**
*   **K8s 与 Metric 互证**：事实 #1 的 `exit_code=78`、`restart_count=5` 与事实 #6 的 `restarts=5` 在时间窗口内完全一致，确证了应用经历了 5 次完整的启动-崩溃周期。
*   **日志与链路互证**：事实 #4 日志中的 `CONFIG_MISSING` 与事实 #5 链路中的 `observed_mode=config_missing_exit` 指向同一根本触发点，证明应用进程在启动后（或首次请求时）因无法获取配置而主动退出。
*   **资源与异常解耦**：事实 #3 显示资源请求与限制均正常，结合事实 #1 的退出码 78 及事实 #4 的日志，可排除资源不足（OOM/CPU Throttling）导致的异常终止，将根因锁定在应用层配置。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动阶段无法获取必需配置参数 → 触发 'CONFIG_MISSING' 逻辑并返回 HTTP 500 → 应用进程以退出码 78 终止 → Kubernetes 检测到容器异常退出，触发 CrashLoopBackOff 循环重启
```

### 根因结论

已确认根因为 **应用缺失必需的环境配置或环境变量名配置错误**，导致应用进程启动后立即以 `exit code 78` 退出。

这一结论由以下事实链严密支撑：
1.  **直接行为证据**：日志聚合事实显示 `pattern=CONFIG_MISSING`，且 Tracing 记录中 `observed_mode` 明确标识为 `config_missing_exit`。
2.  **系统异常证据**：K8s 状态确认容器反复终止（`exit_code=78`）并进入 `CrashLoopBackOff`，且 `resource` 维度无 OOM 迹象。

未确认项为：具体是哪个 ConfigMap Key 缺失，或环境变量名是否与 Pod YAML 中的挂载配置存在拼写/映射错误（输入中 Pod YAML 细节被隐去，无法直接比对键名）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 15.3s
├─ 并发证据采集: 65.0s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 65.0s (Evidence 55.4s, RCA 9.5s)
└─ 汇总总结: 13.5s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
