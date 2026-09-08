## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | Pod workload-dff5cbc6b-fkzvn (aiops-case-07) 持续处于 CrashLoopBackOff 状态，app 容器不可用。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason: CrashLoopBackOff`, `restart_count: 14`, `exit_code: 78` | 确证容器非正常终止，且处于高频重启循环中 |
| 2 | Logging | Elasticsearch | Pattern: `CONFIG_MISSING` (HTTP 500, Path: `/work`), 窗口内出现 8 次，`allocated_mib` 维持在 0 | 定位到容器进程在特定请求路径下因配置缺失主动报错退出 |
| 3 | Tracing | Deepflow/Tempo | Flow/Span: `GET /work` 返回 `500`，关联日志 Trace ID (`e.g., 80eb7bda...`) | 通过 L7 流量关联，证明 500 错误与日志中的崩溃事件由同一请求触发 |
| 4 | K8s Config | Kubernetes | `resource_limit.memory: 96Mi`, `resource_request.cpu: 20m` | 排除资源限额导致的 OOM 或 CPU 限制退出 |

**证据关联说明：**
日志 (Fact 2) 显示应用逻辑因 `CONFIG_MISSING` 返回 500 错误，Tracing (Fact 3) 进一步证实了该错误发生在 `/work` 接口调用期间；这种应用层的主动退出导致了 K8s (Fact 1) 记录的 `exit_code: 78` 及随后的 CrashLoopBackOff 重启行为。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码逻辑缺失必要配置校验 → 处理 /work 请求时触发 CONFIG_MISSING 返回 HTTP 500 → 进程主动退出 (exitCode=78) → 触发 K8s 持续重启 (CrashLoopBackOff)
```

### 根因结论

**已确认根因：应用代码在运行时因缺少关键配置项（日志标识为 `CONFIG_MISSING`）导致处理 `/work` 端点请求时失败并主动退出。**

- **支撑事实：**
  - 日志与流量证据一致显示：在 `/work` 端点请求期间，应用连续返回 `HTTP 500` 并输出 `CONFIG_MISSING` 错误（Fact 2, 3）。
  - 退出状态码为 `78`，与 500 错误导致的应用层主动失败行为相符（Fact 1）。
  - 排除了 K8s 层面的资源驱逐（Limits 充足）及启动配置问题，故障明确发生在容器运行后的请求处理阶段（Fact 4, 1）。
- **未知事项：**
  - 具体缺失的配置项 Key 名称未在日志中展开。
  - 触发 `CONFIG_MISSING` 的具体业务条件路径仅知 `/work`。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 24.2s
├─ 并发证据采集: 87.9s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 87.9s (Evidence 76.9s, RCA 10.8s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
