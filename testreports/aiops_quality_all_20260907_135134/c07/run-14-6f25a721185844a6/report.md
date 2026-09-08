## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | Application crash loop caused by missing configuration files referenced by ConfigMap 'workload-code', resulting in application exit code 78. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: `CrashLoopBackOff`; `container.last_terminated_reason`: `Error`; `container.last_exit_code`: `78` | 确认容器处于应用崩溃循环中，由退出码 78 导致终止 |
| 2 | K8s Event | Kubernetes | `Back-off restarting failed container app`; 重启计数达 9 次 (事实 ID `fact-71b223ed4ed6`) | 验证崩溃循环的持续性和频率 |
| 3 | Logging | Elasticsearch | `CONFIG_MISSING`; `http_status: 500`; `path: /work`; 发生 8 次 (事实 ID `fact-35b86fb0867e` 等) | 直接暴露应用内部故障机理：配置缺失导致服务不可用 |
| 4 | Tracing | Tempo/Deepflow | Flow 聚合：`GET /work` 响应 `500`，共 9 次 (事实 ID `fact-80dca9b68ddb` 等); Span 属性：`aiops.observed_mode: config_missing_exit` | 独立观测证实每次请求均因同一模式被拒绝，流量与日志模式一致 |

**证据交叉印证：**
Kubernetes 层面的 CrashLoopBackOff 症状（证据 #1）由应用进程内部抛出的 `CONFIG_MISSING` 错误（证据 #3）直接驱动。日志聚合显示该错误模式在观测窗口内高频复现，Tracing 聚合（证据 #4）进一步确认了所有失败请求均返回 500 且属于同一故障路径，排除了网络抖动等外部因素。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'workload-code' 引用缺失(正式RCA) → 应用启动或请求处理时找不到配置(日志: CONFIG_MISSING) → 应用进程以 exit code 78 终止(容器状态: Error) → 容器进入 CrashLoopBackOff 状态(集群现象)
```

### 根因结论

**已确认的根因**：
容器 `app` 处于 CrashLoopBackOff 状态的根本原因是应用程序无法找到由其 ConfigMap `workload-code` 引用的配置文件。

**事实支撑**：
1. **容器状态异常**：Kubernetes 显示容器反复退出（`ExitCode 78`，重启 9 次），符合配置缺失导致应用启动失败或立即退出的特征（证据 #1, #2）。
2. **应用日志直接报错**：日志中聚合出现 8 次 `CONFIG_MISSING` 错误（证据 #3），这是定位具体配置缺失问题的决定性事实。
3. **追踪一致**：Tracing 数据确认了所有失败的 HTTP 请求（500 响应）均标记为 `config_missing_exit`（证据 #4），证实了故障的持续性和一致性。

正式根因“Application crash loop caused by missing configuration files referenced by ConfigMap 'workload-code'”与上述多维度证据高度吻合。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 14.1s
├─ 并发证据采集: 64.7s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 64.7s (Evidence 59.2s, RCA 5.4s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
