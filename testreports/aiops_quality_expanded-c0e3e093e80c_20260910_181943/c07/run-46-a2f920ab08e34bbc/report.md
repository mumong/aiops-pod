## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod `workload-dff5cbc6b-sjvxl` 处于 `CrashLoopBackOff` 状态，已重启 20 次 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `workload-dff5cbc6b-sjvxl` 容器 `app` 处于 `CrashLoopBackOff` 状态，已重启 20 次，退出码 78 | 明确应用进程主动终止的终止状态与重启频率 |
| 2 | K8s Event | Kubernetes | `Warning BackOff`：重启失败容器的退避间隔已达 5m0s | 佐证重启机制已持续运行并进入退避逻辑 |
| 3 | K8s Config | Kubernetes | CPU 限制 200m，内存限制 96Mi | 资源配额极低，排除资源竞争导致 OOM 的可能 |
| 4 | Logging | Elasticsearch | 模式 `CONFIG_MISSING`：应用对路径 `/work` 返回 HTTP 500，共发生 8 次 | 直接指明触发应用主动退出的错误逻辑 |
| 5 | Tracing | Deepflow/Tempo | Flow/Span `GET /work` 返回 500，属性包含 `aiops.observed_mode: config_missing_exit` | 关联日志模式，确认该请求因配置缺失导致主动退出 |

**证据关联说明**：
Kubernetes 状态显示容器以退出码 78 主动终止（#1, #2），Logging 和 Tracing 均指向同一个触发点：应用在处理 `/work` 请求时，因缺失配置 (`CONFIG_MISSING`) 返回 500 并主动退出（#4, #5）。低资源限制排除了资源耗尽导致被 Kubelet 强杀的可能，证据链条在“主动退出”这一行为上高度一致。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码依赖配置缺失 → 处理 /work 请求时触发 CONFIG_MISSING 错误并返回 500 → 应用进程以退出码 78 主动终止 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因：应用启动后处理 `/work` 请求路径时，因检测到配置缺失（`CONFIG_MISSING`）而以退出码 78 主动终止。
- 证据支持：Logging 显示重复的 `CONFIG_MISSING` 错误模式；Tracing 中的 `config_missing_exit` 属性及 HTTP 500 响应与该退出码行为一致；Kubernetes 状态证实了非异常退出（Exit Code 78）导致的重启循环。
- 局限性：目前证据不足，无法确定 `ConfigMap workload-code` 的具体内容，以及为何未见常规启动日志（应用可能为 Worker 模式或日志采集配置导致启动日志未被捕获）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 22.2s
├─ 并发证据采集: 67.4s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 67.4s (Evidence 57.9s, RCA 9.4s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime, pod-oomkilled
