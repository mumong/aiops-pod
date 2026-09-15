## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod workload-dff5cbc6b-sjvxl 处于 CrashLoopBackOff 状态，持续重启 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `BackOff restarting failed container app ... x221 over 54m` | 确认容器应用进程持续异常退出并触发重启退避 |
| 2 | K8s State | kubernetes | `last_exit_code: 78` | 定位应用进程异常退出的具体返回码 |
| 3 | Logging | elasticsearch | `http_request level: error, message: CONFIG_MISSING, http_status: 500` (8 occurrences, time range: 20:57:33 - 21:23:49) | 提供关键错误上下文，指出错误由配置缺失引起，且伴随 HTTP 500 响应 |
| 4 | Tracing | deepflow | `GET /work response_code: 500` (9 flows, src_ip: 172.16.104.8, dst_ip: 172.16.104.63) | 验证 HTTP 请求 `/work` 持续返回 500 错误，确认服务端异常 |
| 5 | K8s Config | kubernetes | `cpu.limit: 200m, memory.limit: 96Mi` | 提供资源限制上下文，排除资源硬限制直接导致退出的表象 |

**证据印证说明**：
Kubernetes 的持续重启与日志中的 `CONFIG_MISSING` 错误直接对应。Tracing 的 Flow 记录进一步证实了应用虽然处于运行/重启状态，但针对 `/work` 请求持续返回 HTTP 500，这与日志中捕获的错误逻辑一致。退出码 78 表明应用并非因 OOM 或 CPU 限制崩溃，而是逻辑性退出。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码依赖的配置数据缺失 → 应用启动时抛出 CONFIG_MISSING 错误并返回 HTTP 500 → 进程非正常退出（exit_code 78）并触发 kubelet 重启机制 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因是**应用启动时因依赖的配置数据缺失（CONFIG_MISSING）导致程序初始化失败并异常退出**。
证据链（证据 3、4）通过日志模式（`CONFIG_MISSING`、`http_status: 500`）与追踪流量（`GET /work` 返回 500）互相印证，排除了 Kubernetes 基础设施调度或资源硬限制异常作为主因的可能。当前证据足以解释 CrashLoopBackOff 现象，但关于具体缺失的配置项名称或文件路径（如 `unknowns` 中所述）缺乏决定性事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 19.9s
├─ 并发证据采集: 63.2s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 63.2s (Evidence 54.8s, RCA 8.2s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
