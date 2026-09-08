## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | Pod aiops-case-07/workload-dff5cbc6b-kmfxx处于CrashLoopBackOff状态，持续重启 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason=Error`, `container.waiting_reason=CrashLoopBackOff`, `last_exit_code=78` | 确认应用容器持续崩溃退出，退出码78为业务逻辑层异常退出 |
| 2 | K8s Event | kubernetes | `Back-off restarting failed container app` (持续 86m) | 确认 kubelet 正在执行重启策略，集群层面无阻塞 |
| 3 | K8s Config | kubernetes | `request.cpu=20m`, `limit.memory=96Mi` | 排除资源限制导致的 OOMKilled |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total=21` | 量化重启频次，与 K8s 侧观测一致 |
| 5 | Logging | elasticsearch | 模式 `CONFIG_MISSING`, `http_status: 500`, `path: /work` (累计 8 次) | 明确应用主动因配置缺失触发 500 错误并退出 |
| 6 | Tracing | deepflow+tempo | HTTP 请求 `GET /work` 返回 `status_code: 500`, 耗时 `5796~51798us` | 确认 HTTP 请求链路正常抵达应用并处理返回了业务错误 |

**证据说明：**
1. **K8s 与 Metrics 互相印证**：事实 #1 和 #4 均显示容器处于重启循环中，且重启次数（21次）与持续时间（86m）吻合。
2. **Logging 与 Tracing 互相印证**：事实 #5 和 #6 揭示了应用的具体行为：在处理 HTTP 请求 `/work` 时，因关键配置缺失（`CONFIG_MISSING`）而返回 500 错误。
3. **Exit Code 指向根因**：事实 #1 中的退出码 `78` 与事实 #5 的 `CONFIG_MISSING` 错误类型一致，证实应用检测到配置缺失后主动终止了进程，而非因系统资源或网络异常被动崩溃。

## 🎯 根因分析 · g1

### 因果链
```text
关键配置（CONFIG_MISSING）不可用 → 应用处理HTTP请求时触发异常 → 返回500并主动退出(exitCode=78) → 触发CrashLoopBackOff
```

### 根因结论
**已确认根因**：应用容器启动后，在处理业务请求（`/work`）时因关键配置项缺失（`CONFIG_MISSING`）导致业务逻辑异常，应用主动以退出码 `78` 终止进程。

该行为直接触发了 Kubernetes 的重启机制，导致 Pod 持续处于 `CrashLoopBackOff` 状态（见证据编号 1, 5, 6）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 15.9s
├─ 并发证据采集: 66.3s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 66.3s (Evidence 56.6s, RCA 9.4s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
