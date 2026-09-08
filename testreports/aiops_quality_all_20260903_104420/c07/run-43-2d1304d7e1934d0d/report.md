## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | Pod workload-dff5cbc6b-kmfxx 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Container `app` 处于 `CrashLoopBackOff`，退出码 `78`，最近一次终止原因 `Error` (fact-1b9c94422b2c, fact-4dc532ae3e4f) | 确认异常终止事实及退出状态 |
| 2 | K8s Event | Kubernetes | 持续 76m 的 `BackOff` 事件，重启次数已达 `19` 次 (fact-46943b08d656) | 佐证故障的持续性与重启行为 |
| 3 | Logging | Elasticsearch | 9 条错误日志：`http_request` 返回 `500`，消息明确为 `CONFIG_MISSING`，路径 `/work` (fact-0f27003945a0 等) | 直接指向业务逻辑层配置缺失错误 |
| 4 | Tracing | Tempo | 聚合 9 次 `GET /work` 调用，响应状态 `500`，应用属性 `aiops.observed_mode="config_missing_exit"` (fact-2c6bac00fbe9) | 证明进程是因配置缺失主动退出，而非资源耗尽 |
| 5 | K8s Config | Kubernetes | 内存限制 `96Mi`，请求 `24Mi`；CPU 限制 `200m`，请求 `20m` (fact-11f39c59e566) | 排除资源限制导致的 OOMKilled |

**证据总结**：K8s 状态确认容器因非零退出码异常终止并进入重启循环；日志与 Trace 跨维度一致表明应用层发生了 `CONFIG_MISSING` 错误并主动退出；资源配置正常，排除了基础设施层面的资源争用。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置文件缺失或不可读 → 应用检测到错误并记录 CONFIG_MISSING → 进程抛出 500 错误后以退出码 78 终止 → kubelet 触发 CrashLoopBackOff 导致 Pod 不可用
```

### 根因结论

**已确认的根因**：应用 `aiops-lab-workload` 在运行或启动时检测到关键配置缺失（日志标识 `CONFIG_MISSING`，Trace 属性 `aiops.observed_mode` 为 `config_missing_exit`），导致进程立即以非零退出码（`exit code: 78`）异常退出。该非正常退出触发了 Kubernetes 的重启策略，由于连续失败导致 Pod 进入 `CrashLoopBackOff` 状态（证据 #3, #4, #5）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.5m
├─ 问题定位: 13.9s
├─ 并发证据采集: 124.9s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 124.9s (Evidence 114.9s, RCA 9.8s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- 未调用 Runbook
