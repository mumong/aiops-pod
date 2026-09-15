## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | workload-dff5cbc6b-sjvxl (aiops-case-07) 处于 CrashLoopBackOff 状态，容器启动后立即因配置缺失报错退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `BackOff restarting failed container app in pod workload-dff5cbc6b-sjvxl_aiops-case-07` | 确认 kubelet 正在因容器反复崩溃而进行指数退避重启 |
| 2 | K8s State | kubernetes | container `app` 状态为 `Error`，last_exit_code 为 `78` | 确认应用进程已异常终止，且退出码为 78 |
| 3 | K8s State | kubernetes | Pod 重启计数 (restart_count) 为 `13` | 证明崩溃已重复发生，符合 CrashLoopBackOff 现象 |
| 4 | Logging | elasticsearch | 模式：`{ event: http_request, level: error, message: CONFIG_MISSING, http_status: 500, path: /work }` | 直接暴露应用逻辑错误：请求失败且明确提示配置项缺失 |
| 5 | Tracing | tempo | Trace ID `64132b2c9d9b8077c1ac955acb517247` 对应 Span `870e7e9c4c6806ea`，属性 `aiops.observed_mode=config_missing_exit` | 关联日志中的失败请求，确认异常发生在应用启动/初始化阶段 |
| 6 | K8s Config | kubernetes | container `app` CPU Limit `200m` / Memory Limit `96Mi` | 排除资源硬限制导致 OOMKilled 或 CPU Throttling 的可能 |
| 7 | Metric | prometheus | `kube_pod_container_status_restarts_total` 从 `0` 持续上升至 `12`，且维持 `CrashLoopBackOff` 状态 | 趋势数据证实了容器重启行为是近期的持续性故障，而非偶发 |

日志中的 `CONFIG_MISSING` 错误与 Trace 中的 `config_missing_exit` 观测模式高度一致，结合 `exit_code: 78` 确认了应用代码层面的配置校验失败是引发 CrashLoopBackOff 的直接原因。Kubernetes 事件和指标从基础设施侧佐证了该配置缺失导致的持续退出行为。

## 🎯 根因分析 · g1

### 因果链

```text
应用关键配置项 CONFIG 缺失（fact-4, 5）
  → 应用启动校验失败，记录 CONFIG_MISSING 错误并终止进程 (exit 78)（fact-2, 4）
  → kubelet 检测到容器非正常退出（fact-1）
  → 用户可见 CrashLoopBackOff 状态（fact-3, 6）
```

### 根因结论

**已确认的根因**：
应用容器在启动或初始化阶段检测到关键配置项（`CONFIG`）缺失（由 `fact-4` 日志和 `fact-5` Trace 明确指向），导致进程以退出码 `78` 异常终止。这一异常退出行为被 kubelet 捕获并触发重启策略，最终表现为 Pod 的 `CrashLoopBackOff` 状态（由 `fact-1` 和 `fact-3` 证实）。

**未确认部分**：
具体是哪个 ConfigMap、Secret 或环境变量缺失未在日志内容中指明（仅记录了 `CONFIG_MISSING` 字符串）。需进一步检查 Pod YAML 的配置挂载定义以确定缺失的具体配置键。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 30.4s
├─ 并发证据采集: 67.0s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 67.0s (Evidence 56.8s, RCA 10.1s)
└─ 汇总总结: 11.5s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-oomkilled, pod-crashloop-runtime
