## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | Container app in CrashLoopBackOff due to process exit after CONFIG_MISSING error on /work endpoint |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning BackOff 2m55s (x468 over 107m)` kubelet 重启失败容器 `app` | 确认应用已长期处于崩溃重启循环中 |
| 2 | K8s State | kubernetes | 容器 `app` 终止原因: `Error`, 退出码: `78`, 重启次数: `25` | 确认进程非资源耗尽异常退出，由业务逻辑导致 |
| 3 | Logging | elasticsearch | 模式: `CONFIG_MISSING`, HTTP 状态: `500`, 路径: `/work`, 聚合次数: 8 次 | 确认失败时的具体错误类型与触发路径 |
| 4 | K8s Config | kubernetes | 资源配置: CPU Request `20m` / Limit `200m`；内存 Request `24Mi` / Limit `96Mi` | 排除资源限制导致的 OOMKilled 或 CPU Throttling |
| 5 | Tracing (Flow) | deepflow | GET /work 返回 HTTP 500，采样聚合 `occurrence_count: 9` | 提供应用层异常行为的网络侧证据 |
| 6 | Tracing (Span) | tempo | Trace ID `9a3b9b13a8706d6da508428164070448` 匹配日志，`span.name: "GET /work"` | 将日志的 CONFIG_MISSING 与 Trace 请求关联 |
| 7 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = 1 (CrashLoopBackOff) | 独立指标确认 Pod 当前处于等待重启状态 |

**证据说明：**
1. **状态与现象印证**：指标 `fact-1b6781a9c5dd` 确认 Pod 处于 CrashLoopBackOff，事件 `fact-1e8a37b69116` 提供了 `468 次` 的重启累积记录，说明故障持续时间长，非瞬时抖动。
2. **退出行为确认**：日志 `fact-26400f6e3c36` 指出请求 `/work` 端点返回 `CONFIG_MISSING (500)`；K8s 状态 `fact-58039c52451c` 显示进程因该错误退出码 `78` 终止。结合 Trace Span `fact-2fbfefe6f9c6`（匹配日志 Trace ID），确证了“业务异常导致进程退出”的因果链，排除了 K8s 侧 OOM 或 Crash 等非业务原因。
3. **资源环境检查**：资源配置 `fact-0823ec47297a, fact-1464fc514687` 显示资源限制充足，排除因 CPU/Memory 不足导致的系统强制杀进程。

## 🎯 根因分析 · g1

### 因果链

```text
缺失必需的运行时配置 (环境变量/ConfigMap/Secret) → 进程启动并接收 /work 请求 → 请求处理发现配置缺失返回 CONFIG_MISSING (HTTP 500) → 进程以退出码 78 终止 → Pod 重启并陷入 CrashLoopBackOff
```

### 根因结论

**已确认根因**：应用程序 `workload-dff5cbc6b-fkzvn` 在启动后，于处理 `/work` 端点的 HTTP 请求时，因**缺少必需的配置项**（触发 `CONFIG_MISSING` 错误，返回 HTTP 500），导致业务进程主动退出（退出码 78），进而引发 K8s 控制面的重启循环。

**支撑证据**：
1. **应用日志** (`fact-26400f6e3c36`, `fact-a19b81485364`)：记录了 8 次以上关于 `CONFIG_MISSING` 的错误日志，明确了故障模式。
2. **Trace 关联** (`fact-2fbfefe6f9c6`)：Trace ID `9a3b9b13a8706d6da508428164070448` 将具体的失败请求与日志错误关联。
3. **K8s 退出状态** (`fact-58039c52451c`, `fact-1e8a37b69116`)：进程退出码 `78` 和 K8s 事件 `BackOff` 证实了进程因业务逻辑失败被重启。
4. **资源排除** (`fact-0823ec47297a`)：容器资源限制正常，排除了资源不足导致的异常。

**未确认事项**：
* 具体缺失的配置项名称（环境变量、ConfigMap 或 Secret 的 Key）。
* 该配置项缺失的根本原因（例如：Deployment 部署文件遗漏、依赖的 ConfigMap 未创建、密钥未挂载等）。

---

## 📊 性能统计

```text
├─ 总耗时: 10.9m
├─ 问题定位: 25.1s
├─ 并发证据采集: 612.6s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 612.6s (Evidence 601.2s, RCA 11.2s)
└─ 汇总总结: 16.9s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
