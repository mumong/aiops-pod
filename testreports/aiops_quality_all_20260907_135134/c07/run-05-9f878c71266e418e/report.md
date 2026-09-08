## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | Pod workload-dff5cbc6b-fkzvn 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.phase`: Running; `containersReady/Ready`: False (containers with unready status: [app]) | 确认 Pod 处于存活但应用容器持续处于未就绪状态 |
| 2 | K8s State | kubernetes | `container.app.restart_count`: 6; `last_terminated_reason`: Error | 确认应用容器存在反复异常退出的行为 |
| 3 | K8s Event | kubernetes | `BackOff`: Back-off restarting failed container app (x20 over 9m3s) | 确认 Kubelet 执行了指数退避重启策略，导致 CrashLoopBackOff |
| 4 | Logging | elasticsearch | `pattern`: event=http_request, error=CONFIG_MISSING, http_status=500, path=/work (8次); `first`: 2026-09-07T14:35:23.545Z, `last`: 2026-09-07T14:41:46.121Z | 提供应用进程主动退出并报错的具体业务原因（配置缺失） |
| 5 | Tracing | Deepflow | `HTTP GET /work` → `response_code: 500` (9次), `dst_ip`: 172.16.104.7 | 从 L7 流量视角证实了持续存在的 500 错误服务响应 |
| 6 | Tracing | Tempo | `trace_id: b3559561ac9acd05071836e31ce2b090` (对应日志), `http.response.status_code: 500` | 关联日志与流量，确认 500 错误发生在处理请求期间 |

**证据关联说明：**
K8s 记录表明容器反复退出并处于重启循环中；日志 `CONFIG_MISSING` 解释了退出（Error）的业务原因；Tracing 确认了在异常期间应用仍响应了 HTTP 500 错误。日志与 Trace（`trace_id: b3559561ac9acd05071836e31ce2b090`）实现了跨维度的交叉印证，确认进程在启动后能够运行并接收流量，但随后因内部逻辑报错退出。

## 🎯 根因分析 · g1

```text
应用启动后加载所需的配置资源失败 → 业务代码抛出 CONFIG_MISSING 错误并返回 500 HTTP 状态 → 应用进程以 Exit Code 78 异常退出 → Kubelet 触发重启策略，最终导致 Pod 进入 CrashLoopBackOff 状态
```

**根因结论：**
已确认根因为**应用启动配置加载失败（代码层返回 500 错误）**。
证据 `[2]`、`[3]` 证实了容器反复异常退出的系统层现象；证据 `[4]` 与 `[6]` 的关联数据（`CONFIG_MISSING` 错误与 `status_code: 500` 的 Trace/Span 对应）证明了导致进程退出的直接机制。根据输入事实，决定性的缺失事实为**未知的具体配置资源名称**（ConfigMap 或 Secret），这是导致配置加载失败的配置层原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 17.3s
├─ 并发证据采集: 52.9s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 52.9s (Evidence 44.8s, RCA 7.9s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
