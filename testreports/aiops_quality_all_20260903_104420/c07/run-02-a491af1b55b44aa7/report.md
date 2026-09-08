## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | 应用缺失必要配置导致启动失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` | `container.last_terminated_reason` = "Error" | 直接指示容器异常终止原因 |
| 2 | K8s State | `kubernetes` | `container.last_exit_code` = 78 | 辅助确认退出码，结合退出码判断具体失败类型 |
| 3 | K8s Event | `kubernetes` | `BackOff restarting failed container app` | 证明 Pod 处于 CrashLoopBackOff 循环重启状态 |
| 4 | K8s Config | `kubernetes` | `container.resource_limit.cpu` = "200m", `memory` = "96Mi" | 资源限制配置（非异常主因） |
| 5 | K8s Measurement | `kubernetes` | `container.restart_count` = 4 | 证明应用已多次重启，符合循环失败特征 |
| 6 | Metric | `prometheus` | `kube_pod_container_status_restarts_total` = 4, `last_terminated_reason` = "Error" | 验证重启次数及最后一次异常终止原因 |
| 7 | Logging | `elasticsearch` | `CONFIG_MISSING` (8次), `/work`, HTTP 500, 时间范围 `13:59:02` 至 `14:01:04` | 明确应用报错为“配置缺失”，定位到 `/work` 路径 |
| 8 | Tracing | `tempo` / `deepflow` | `http.response.status_code` = 500, `http.route` = `/work`, 关联 9 次异常 Flow | 验证应用处理请求 `/work` 时持续返回 500 错误 |

**证据说明：**
K8s 事件与指标共同确认了 Pod 处于“CrashLoopBackOff”且退出原因为“Error”，且重启了 4 次（#3, #5, #6）。日志显示该应用在 `13:59` 到 `14:01` 期间连续抛出 `CONFIG_MISSING` 并返回 `HTTP 500`（#7），同时链路追踪数据证实了 9 次针对 `/work` 路由的 500 错误请求（#8）。日志中的 `CONFIG_MISSING` 结合 K8s 的 `Exit Code 78` 形成了完整的因果证据链，说明应用因找不到配置而退出，导致 Pod 崩溃重启。

## 🎯 根因分析 · g1

### 因果链

```text
应用运行环境缺少必要的配置文件或配置项 → 应用启动或处理请求 `/work` 时抛出 CONFIG_MISSING 错误并返回 HTTP 500 → 进程因配置缺失退出，Exit Code: 78 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为**应用运行环境缺少必要的配置文件或配置项**。

这一根因得到了以下证据的充分支持：
1. **应用层日志**明确记录了 `CONFIG_MISSING` 错误，表明启动或请求处理阶段因找不到配置而失败（证据 #7）。
2. **链路追踪与日志的时间关联性**：日志中的 `CONFIG_MISSING` 错误与追踪中的 500 错误路由 `/work` 在时间上高度重合，证实应用虽然在运行但持续处理失败（证据 #7, #8）。
3. **K8s 状态验证**：容器的最后终止原因为 `Error` 且退出码为 `78`，这与应用层记录的配置缺失导致进程退出的行为相符（证据 #1, #2, #6）。

尽管根因已确认为“配置缺失”，但具体缺失的是哪个配置项或配置文件，当前证据不足以明确（unknowns: "具体缺失的配置键名或配置文件路径"）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 21.1s
├─ 并发证据采集: 63.7s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 63.7s (Evidence 54.0s, RCA 9.5s)
└─ 汇总总结: 12.6s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
