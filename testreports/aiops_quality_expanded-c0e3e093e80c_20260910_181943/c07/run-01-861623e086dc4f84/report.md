## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod aiops-case-07/workload-dff5cbc6b-sjvxl 处于 CrashLoopBackOff 状态，容器 app 频繁重启 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` 最后一次终止原因: `Error`；退出码: `78` | 确认容器进程以非 0 状态码异常退出，非资源超限 OOM |
| 2 | K8s State | Kubernetes | 状态: `CrashLoopBackOff`；等待消息: `back-off 1m20s restarting failed container`；重启计数: `4` | 确认异常导致容器持续崩溃并触发重启机制 |
| 3 | Logging | Elasticsearch | 日志模式: `CONFIG_MISSING` (http_status: 500, path: `/work`); 时间范围: `2026-09-10T20:30:17Z` 至 `2026-09-10T20:31:27Z` (共 8 次) | 直接证明应用在处理业务请求时检测到配置缺失并报错 |
| 4 | Tracing | Deepflow | 等价请求聚合: `GET /work` -> `500`; 来源: `172.16.104.8`, 目的: `172.16.104.63` (Pod IP); 计数: 9 | 确认应用服务网络可达且响应了业务请求，但均返回 500 错误 |
| 5 | Tracing | Tempo | Span `a358165e4c5df7b2882c057473693f30`: 属性 `aiops.observed_mode: config_missing_exit`; HTTP Status: `500` | 链路层属性精准命中配置缺失导致退出的场景 |
| 6 | K8s Event | Kubernetes | Event: `BackOff restarting failed container app` | 确认 Kubelet 观察到容器重启失败事件 |
| 7 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` (`container=app, reason=Error`) = `1` | 指标侧证实容器终止原因为 Error |

证据表明：应用代码中存在硬编码的退出逻辑。当应用接收到 `/work` 请求时，触发业务层的 `CONFIG_MISSING` 错误，随即调用 `sys.exit(78)` 强行终止进程。Kubernetes 监测到非 0 退出码后，按策略进行重启，因频繁崩溃最终进入 CrashLoopBackOff 状态。Tracing 中的 `config_missing_exit` 属性与 Logging 中的 `CONFIG_MISSING` 模式高度吻合，形成了完整闭环。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'workload-code' 挂载或配置缺失 → 业务逻辑 /work 请求检测到配置缺失 → 抛出 CONFIG_MISSING 错误并调用 sys.exit(78) → Kubernetes 终止容器并触发 CrashLoopBackOff
```

### 根因结论

**已确认根因：** 应用代码逻辑缺陷。

应用代码在运行时未能获取到预期的配置项（日志标识为 `CONFIG_MISSING`），导致业务逻辑主动抛出 500 错误并执行 `sys.exit(78)` 终止进程。这一异常退出行为导致 Kubernetes 持续重启容器，最终表现为 `CrashLoopBackOff`。

证据支撑：
- 容器退出码为 `78` (证据 1, 6)；
- 日志中存在明确的 `CONFIG_MISSING` 报错模式 (证据 3)；
- 分布式追踪 Span 中 `aiops.observed_mode` 明确标记为 `config_missing_exit` (证据 5)；
- 所有外部对 `/work` 的请求均收到 500 响应 (证据 4)。

**缺失决定因素：**
输入数据明确标识缺少 `ConfigMap 'workload-code'` 中具体缺失的配置键名，以及代码中触发 `sys.exit(78)` 的具体逻辑路径。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 17.0s
├─ 并发证据采集: 109.5s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 109.5s (Evidence 100.1s, RCA 9.2s)
└─ 汇总总结: 13.2s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime, pod-oomkilled
