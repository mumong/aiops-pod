## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | Application configuration missing (CONFIG_MISSING) causes the container to exit with code 78 repeatedly. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubelet` (event) | `Warning BackOff restarting failed container app` (x64 over 18m) | 确认容器反复崩溃且退避延迟增至 5m0s |
| 2 | K8s Event | `kubelet` | `Back-off restarting failed container app in pod workload-dff5cbc6b-fkzvn` | 记录 Pod 级别的重启与调度行为 |
| 3 | K8s State | `kubelet` | `container.last_terminated_reason: Error` | 容器异常退出，非正常停止 |
| 4 | K8s State | `kubelet` | `container.last_exit_code: 78` | 提供明确的退出码，作为应用程序层面的终止标志 |
| 5 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason=1` (label: `CrashLoopBackOff`) | 确认当前容器处于等待状态，与 K8s 事件一致 |
| 6 | Logging | `elasticsearch` | Pattern: `CONFIG_MISSING` (occurrence: 8), Time: `14:35:53` to `14:52:10` | 直接指出应用内部触发退出 78 的原因为配置缺失 |
| 7 | Tracing | `tempo` | Span `GET /work`: `http.response.status_code: 500`, `aiops.observed_mode: config_missing_exit` | 确认请求处理流程中因配置缺失导致业务中断 |

**证据关联说明：**
K8s 状态（证据 #1-4）与应用日志（证据 #6）在时间线上重合，日志中 8 次 `CONFIG_MISSING` 模式精确对应了容器的反复重启。K8s 退出的 78 码与日志报告的 `CONFIG_MISSING` 逻辑关联：应用因配置缺失直接返回退出码 78，从而触发 K8s 的重启策略。

## 🎯 根因分析 · g1

### 因果链

```text
Application configuration missing (CONFIG_MISSING) → 容器进程主动终止 (Exit Code 78) → Kubernetes 触发重启策略 → CrashLoopBackOff (退避等待 5m0s)
```

### 根因结论

**已确认根因：应用程序配置缺失 (`CONFIG_MISSING`) 导致容器反复退出。**

应用代码检测到配置缺失后，主动以退出码 `78` 终止进程（由证据 #6 日志和证据 #4 退出码证实）。Kubernetes 接收到退出信号后尝试重启容器，但由于进程再次以同样的原因退出，最终进入 `CrashLoopBackOff` 状态并持续退避（由证据 #1-3 和证据 #5 证实）。应用层日志和链路追踪（证据 #7）的 `config_missing_exit` 模式提供了直接的业务层面根因证据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 17.9s
├─ 并发证据采集: 73.3s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 73.3s (Evidence 67.0s, RCA 6.2s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
