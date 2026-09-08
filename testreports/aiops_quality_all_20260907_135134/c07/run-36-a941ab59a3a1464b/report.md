## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | pod workload-dff5cbc6b-fkzvn CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | pod phase: Running, status: ContainersNotReady (app), container waiting: CrashLoopBackOff, last exit code: 78 | 确证应用容器启动失败，状态符合 `formal_rca` 中定义的触发机制 |
| 2 | K8s Event | kubernetes | BackOff 107s (x332 over 76m), message: back-off 5m0s restarting failed container=app | 证明异常从 76 分钟前开始发生，处于持续失败重试循环中 |
| 3 | K8s Config | kubernetes | resource_limit.cpu=200m, resource_limit.memory=96Mi, restart_count=19 | 排除资源上限硬限制导致的 OOMKilled 或 CPUThrottled 可能性 |
| 4 | Logging | elasticsearch | pattern: CONFIG_MISSING, http_status: 500, path: /work, service: aiops-lab-workload (occurrence_count: 8, trace_ids: 016132e74052f941ae8a4a6ac5493dc9 等 8 个) | 直接定位根因为应用内部配置缺失错误 (CONFIG_MISSING)，与 exit code 78 对应 |
| 5 | Tracing | deepflow | L7 Flow: HTTP GET /work response_code: 500, src_ip: 172.16.104.27, dst_ip: 172.16.104.7 (occurrence_count: 9) | 网络层证实外部流量进入 Pod 后被应用返回 500 错误，且包含与日志关联的 trace_id 7ed664affe6fdd8e75610015d3c8e3a3 |
| 6 | Tracing | tempo | application_span: name: "GET /work", attributes: aiops.observed_mode: config_missing_exit, http.response.status_code: 500 | 深入应用调用链，确证错误是由应用层 `config_missing_exit` 模式引发 |

**证据综合说明：**
- 证据 1、2 提供了宏观层面的状态（CrashLoopBackOff），证实了 `formal_rca` 描述的“Process exits with code 78”导致重启的现象。
- 证据 4、5、6 从日志、网络流和追踪链路三个维度交叉印证了根本原因：应用在处理 `/work` 请求时因配置缺失 (`CONFIG_MISSING`) 而触发 `config_missing_exit`，并返回 500 状态码。这完美解释了为何退出码为 78 且伴随 HTTP 请求失败。
- 证据 3 排除了资源不足（CPU/Memory）作为直接原因的可能性，因为资源限制配置合理，且退出码 78 并非典型的系统级资源拒绝信号。

## 🎯 根因分析 · g1

### 因果链

```text
application code error (CONFIG_MISSING) → Process exits with code 78 → Container restart triggered → CrashLoopBackOff status
```

### 根因结论

已确认根因：应用程序启动或运行逻辑中存在配置缺失错误（`CONFIG_MISSING`）。

该错误导致应用进程以退出码 78 异常终止（证据 1, 4），随后 K8s 调度器触发容器重启。由于根本配置问题未解决，容器进入持续的 CrashLoopBackOff 状态（证据 1, 2）。同时，应用内部捕获了该配置错误并以 HTTP 500 错误响应外部请求（证据 4, 5, 6），进一步证实了应用已启动但处于不可用状态。当前所有观察数据（K8s 状态、日志、追踪）均与正式 RCA 的因果链完全吻合，证据充分。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 19.0s
├─ 并发证据采集: 68.2s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 68.2s (Evidence 58.8s, RCA 9.2s)
└─ 汇总总结: 13.1s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
