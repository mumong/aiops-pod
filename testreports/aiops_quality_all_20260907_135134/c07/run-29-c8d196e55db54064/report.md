## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | 应用容器启动后无法从预期配置源获取必要配置（返回 CONFIG_MISSING），导致 HTTP 500 错误并主动退出（Exit Code 78），进而触发 Kubernetes CrashLoopBackOff 重启循环。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubectl` | container `app` terminated reason: `Error`, exit code: `78`, waiting reason: `CrashLoopBackOff` | 确认容器因应用层错误非正常退出，并进入重启循环 |
| 2 | Logging | `elasticsearch` | pattern: `CONFIG_MISSING`, http_status: `500`, path: `/work`, service: `aiops-lab-workload` (8次重复) | 核心诊断证据：应用明确因配置缺失抛出 500 错误 |
| 3 | Tracing | `tempo` | Span: `GET /work`, response_code: `500`, attribute `aiops.observed_mode`: `config_missing_exit` | 追踪确认错误发生在应用内部，且由配置缺失触发 |
| 4 | K8s Config | `kubectl` | resource_request.cpu: `20m`, resource_limit.memory: `96Mi` | 排除资源限制导致 OOM Kill 的可能 |
| 5 | Metric | `prometheus` | `container_memory_working_set_bytes`: `3416064` bytes (~3.2 MiB)，低于 96Mi 限制 | 确认容器未因内存不足被系统强制终止 |
| 6 | K8s Event | `kubernetes` | Warning `BackOff`: "back-off 5m0s restarting failed container=app" | 描述重启退避现象，印证频繁退出的状态 |

**证据说明：**
日志 (fact-2) 与追踪 (fact-3) 均一致指向应用层返回 HTTP 500 错误，且应用显式记录了 `CONFIG_MISSING` 原因和 `config_missing_exit` 模式。K8s 状态 (fact-1) 显示容器以 `Exit Code 78` 退出，这通常被应用用来表示配置或环境错误，与日志和追踪证据完全一致。资源指标 (fact-5) 证实退出并非由内存超限引起，且资源配置 (fact-4) 极低，排除资源争抢导致的系统 Kill。

## 🎯 根因分析 · g1

### 因果链
```text
应用无法从预期配置源获取必要配置 → 抛出 CONFIG_MISSING 异常并返回 HTTP 500 → 应用主动退出 (Exit Code 78) → Kubernetes 观察到容器 Crash 并进入 CrashLoopBackOff 重启循环
```

### 根因结论
**已确认的根因**：应用容器启动后无法从预期配置源获取必要的配置信息。
应用尝试访问 `/work` 路径时，因配置缺失 (`CONFIG_MISSING`) 直接返回 `HTTP 500` 错误并主动退出 (Exit Code 78)，从而触发 Kubernetes 的重启循环。
支撑证据：
- 日志显示 8 次重复的 `CONFIG_MISSING` 错误 (`fact-2`)
- 追踪 Span 明确标记了 `aiops.observed_mode: config_missing_exit` (`fact-3`)
- K8s 状态显示容器以 `Exit Code 78` 退出，符合应用层配置错误退出惯例 (`fact-1`)

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 23.5s
├─ 并发证据采集: 89.6s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 89.6s (Evidence 80.6s, RCA 8.8s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
