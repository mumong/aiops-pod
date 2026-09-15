## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod 容器 `app` 启动后访问 `/work` 端点因配置缺失 (CONFIG_MISSING) 而主动退出 (Exit Code 78)，导致 Kubernetes 陷入 CrashLoopBackOff 重启循环。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: Error; `container.last_exit_code`: 78; `restart_count`: 14; `container.waiting_reason`: CrashLoopBackOff | 确认 Pod 处于因退出码 78 导致的 CrashLoopBackOff 重启循环中。 |
| 2 | K8s Config | kubernetes | `container.resource_limit.cpu`: 200m; `container.resource_limit.memory`: 96Mi | 排除资源超卖导致的 OOMKilled 或 CPU Throttling，资源配置充裕。 |
| 3 | K8s Event | kubernetes | `container.waiting_message`: "back-off 5m0s restarting failed container=app pod=workload-dff5cbc6b-sjvxl..." | 描述当前处于等待重启的退避状态。 |
| 4 | Logging | elasticsearch | Pattern: `CONFIG_MISSING`, `http_status`: 500, `path`: `/work`, `service`: aiops-lab-workload; Occurrences: 8 (20:57 - 21:18) | 日志聚合确认应用因配置缺失主动报错退出，且与 Trace ID 关联。 |
| 5 | Tracing | Tempo | `GET /work` (Span `870e7e9c...`), `trace_id`: `64132b2c...`, `status_code`: 500, `aiops.observed_mode`: config_missing_exit | 追踪证据直接证实 `/work` 请求处理失败的模式为配置缺失，且与日志中的 Trace ID 完全一致。 |

**证据链互证说明：**
- **现象确认**：事实 1 (K8s State) 明确退出码 78，直接指向应用逻辑错误。
- **根因定位**：事实 4 (Logging) 指出应用主动因 `CONFIG_MISSING` 报错并退出，事实 5 (Tracing) 通过相同的 `trace_id` (`64132b2c...`) 进一步证实了 `/work` 端点确实因该原因返回 500 并退出。
- **环境排除**：事实 2 (K8s Config) 证明资源限制不是导致退出的原因。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码配置校验失败 (CONFIG_MISSING) → GET /work 端点返回 500 并主动退出 (Exit Code 78) → Kubernetes 启动失败并进入重启循环 (CrashLoopBackOff) → Pod 持续重启且不可用
```

### 根因结论

已确认的根因为：`workload-dff5cbc6b-sjvxl` Pod 内的 `app` 容器在启动后，其服务逻辑在访问 `/work` 端点时因**配置缺失** (`CONFIG_MISSING`) 主动触发了退出流程，导致容器以 **Exit Code 78** 失败退出，进而被 Kubernetes 反复重启。

**关键证据支撑：**
1. **Kubernetes State**: `container.last_exit_code` 为 `78`，配合 `restart_count: 14` 证实了崩溃重启循环。
2. **Logging**: 聚合日志明确记录了 `CONFIG_MISSING` 错误模式，且发生在 `/work` 路径上。
3. **Tracing**: Temp 数据展示了完全对应的 `GET /work` 请求 (Trace ID: `64132b2c...`)，其应用状态明确为 `config_missing_exit` 且返回 500，与日志和退出原因完全吻合。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 19.0s
├─ 并发证据采集: 62.3s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 62.3s (Evidence 56.6s, RCA 5.5s)
└─ 汇总总结: 12.2s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
