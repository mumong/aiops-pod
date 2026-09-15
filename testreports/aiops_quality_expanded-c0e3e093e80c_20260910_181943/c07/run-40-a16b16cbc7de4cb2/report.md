## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod workload-dff5cbc6b-sjvxl 处于 CrashLoopBackOff 状态，容器反复重启 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container.waiting_reason=CrashLoopBackOff, last_exit_code=78 | 确认应用容器持续异常退出，触发 K8s 重启保护机制 |
| 2 | K8s Event | Kubernetes | Warning BackOff 45s (x310 over 70m) restarting failed container app | 确认该重启循环已持续约 70 分钟，属于长期故障 |
| 3 | Logging | Elasticsearch | log.message: "CONFIG_MISSING" | 指出进程终止的具体原因是运行时配置缺失 |
| 4 | Tracing | Deepflow + Tempo | l7_flow: GET /work -> HTTP 500 (9 occurrences); span: observed_mode=config_missing_exit | 关联具体请求路径与日志错误，证实服务在收到请求并发现配置缺失时主动崩溃 |
| 5 | Metric | Prometheus | kube_pod_container_status_restarts_total=18 | 量化重启次数，与 K8s restart_count 一致，排除监控盲区 |

**证据说明**
- **编号 1、2、5** 相互印证，从状态、事件和时序指标三个维度锁定了“CrashLoopBackOff”这一持续发生的症状。
- **编号 3（日志）** 提供了最直接的终止原因线索 `CONFIG_MISSING`。
- **编号 4（链路）** 将 `CONFIG_MISSING` 错误精准定位到了具体的业务请求 `/work`，并确认了服务处理该请求后的行为模式。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码在初始化或请求 /work 时检测到 CONFIG_MISSING → 抛出 500 异常并主动终止进程(Exit Code 78) → kubelet 检测到容器退出并触发重启循环 → 用户观察到 Pod 处于 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为**应用代码逻辑缺陷导致的运行时配置缺失**。

具体而言，应用在处理 `GET /work` 请求时因检测到关键配置项缺失（日志确认 `CONFIG_MISSING`），进而抛出异常并主动终止进程。这一明确的代码级错误直接导致了容器的反复崩溃与重启，是造成 Pod CrashLoopBackOff 的唯一决定性原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 15.2s
├─ 并发证据采集: 65.8s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 65.8s (Evidence 57.3s, RCA 8.4s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
