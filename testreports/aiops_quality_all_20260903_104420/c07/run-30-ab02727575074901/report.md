## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | Running | Pod workload-dff5cbc6b-kmfxx 处于 CrashLoopBackOff 状态，容器反复启动失败 (exit code 78) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `container.last_exit_code` | `exit_code: 78` | 提供容器终止的直接数值信号，指示非 0 状态码退出。 |
| 2 | K8s State | `pod.status` / `container.restart_count` | `status: Running` (Pod层面), `restart_count: 15` | 确认 Pod 处于持续重启的 CrashLoopBackOff 生命周期状态。 |
| 3 | K8s Event | `BackOff` 事件 | `Back-off restarting failed container app ... x224 over 53m` | 证明 Kubelet 正在经历持续的重启退避，与现象直接对应。 |
| 4 | Metric | `kube_pod_container_status_last_terminated_reason` | `reason: Error` | 从监控数据维度证实最近一次终止原因为 Error，状态与 K8s 状态一致。 |
| 5 | Logging | 日志模式聚合 (`CONFIG_MISSING`) | `8 occurrences` 在 `2026-09-03T14:26:26` 至 `14:47:26` 之间，伴随 `http_status: 500` 和 `path: /work`。 | 提供应用程序内部视角，明确指出在 `/work` 接口发现配置缺失，并记录为内部 500 错误。 |
| 6 | Tracing | Tempo Span | `trace_id: 65684c8c074b2b13bde640e742613caa` (对应日志), 属性 `aiops.observed_mode: config_missing_exit`, `http.response.status_code: 500` | 提供深度链路追踪证据，将日志中的错误模式与具体的应用退出行为 (`config_missing_exit`) 直接关联，证明是主动退出而非崩溃。 |
| 7 | Topology/Flow | Deepflow L7 Flow | `GET /work` 返回 `500`，持续出现 `11 occurrences` 在 `14:31:39` 至 `14:52:40` 期间，目标 Pod IP `172.16.104.15`。 | 从网络层面验证 `/work` 接口在服务端持续响应 500，确认故障发生在应用逻辑处理阶段。 |

**证据关联说明**：
- K8s 层面的 Exit Code 78 (行1) 与 Logging 中的 `CONFIG_MISSING` (行5) 及 Tracing 中的 `config_missing_exit` (行6) 逻辑高度吻合，共同指向应用主动退出。
- Trace `65684c8c...` (行6) 明确属于日志聚合记录中的 trace_ids 之一，实现了日志模式到具体调用链路的精准锚定。
- Topology 数据 (行7) 和 Metric 数据 (行4) 共同印证了该应用服务在持续接收请求时均无法成功处理并处于终止边缘。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置缺失 (未知具体配置项名) → 应用处理请求时触发 CONFIG_MISSING 逻辑 → 主动终止进程 (exit code 78) → Kubelet 触发 CrashLoopBackOff 重启循环
```

### 根因结论

**已确认的根因**：容器内应用代码在尝试处理 `/work` 接口的请求时，因检测到关键配置缺失而主动触发退出逻辑（返回 `exit code 78`），导致 Kubernetes 的容器重启策略不断拉起容器，形成 CrashLoopBackOff。

**证据支撑**：
- **现象层**：K8s 状态显示容器频繁重启 (`restart_count: 15`)，且最近一次退出状态为 Error，退出码为 78 (行1-3, 4)。
- **应用层逻辑**：Trace 数据 (行6) 在关联的调用链中明确记录应用观察模式为 `config_missing_exit`，HTTP 响应为 500。
- **日志层事实**：日志聚合显示在观察窗口内连续发生了 8 次 `CONFIG_MISSING` 级别的错误，均发生在 `/work` 路径下 (行5)。

**待确认事项**：输入事实中未包含具体缺失的配置项名称或环境变量 (如 `fact-unknowns` 所指)，因此无法定位是哪个具体的配置导致了应用主动退出。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 19.9s
├─ 并发证据采集: 79.0s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 79.0s (Evidence 68.5s, RCA 10.3s)
└─ 汇总总结: 14.8s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-oomkilled
