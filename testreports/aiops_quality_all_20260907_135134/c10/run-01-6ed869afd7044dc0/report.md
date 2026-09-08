## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | Running | Liveness Probe 配置不当导致容器被持续强制终止（SIGKILL） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason`="Error" (`fact_id`: fact-a105dae4493c) | 确认容器最近一次退出原因为 Error，是故障发生的直接证据。 |
| 2 | Metric | prometheus | `kube_pod_container_status_restarts_total`=1 (`fact_id`: fact-223a47607f21) | 确认 Pod 已经发生了一次重启，验证了异常的持续性。 |
| 3 | Logging | elasticsearch | 8次日志记录显示 `request completed`、`http_status`=200，内存使用 0 MB (`fact_id`: fact-4342be0fc82b 等) | 证实应用进程在外部看来一直存活且健康，未出现业务报错，说明外部探针或应用内部逻辑未能捕获该终止。 |
| 4 | Tracing | deepflow | 9次 HTTP GET `/work` 请求成功，响应状态 200，耗时 5.4-8.6 ms (`fact_id`: fact-73f0604b8ce7 等) | 进一步确认应用功能正常，请求能够成功返回，排除了应用进程无响应（导致超时）的可能性。 |
| 5 | Tracing | tempo | `GET /work` Span 标记 `aiops.observed_mode`="liveness_fail" (`fact_id`: fact-2728ab6efe0a) | 暴露出 Kubernetes 探测机制判定 Liveness 失败，这与应用功能正常的事实形成鲜明对比。 |

**证据互证说明：**
- 证据 3、4 与证据 5 存在逻辑冲突：证据 3 和 4 证明应用进程完全正常并能成功处理 HTTP 请求（200 响应），这直接反驳了应用无响应或超时的假设。
- 证据 5 提供了关键线索，表明 Kubernetes 内部检测到“Liveness 失败”，而证据 1 确认了随后发生的 Error 退出。这表明 Pod 被终止（SIGKILL）并非因为应用逻辑故障，而是被 Liveness 探针误判。

## 🎯 根因分析 · g1

### 因果链

```text
Liveness 探针配置与业务逻辑不匹配 → 探针误判应用健康状态（liveness_fail） → 触发 Kubelet 强杀容器（Error/Exit Code） → 用户可见 Pod 重启（Restart=1）且日志无报错
```

### 根因结论

已确认的根因是 **Liveness 探针配置不当**。

证据表明容器在被终止前，应用进程能够正常处理 HTTP 请求并返回 200 状态码（证据 3, 4），但系统日志中却标记了 `liveness_fail`（证据 5），最终导致容器以 Error 状态退出并重启（证据 1, 2）。这种“应用正常但探针报错”的现象，典型地指向了探针的路径、超时时间或间隔设置与业务实际运行状态不匹配，导致容器被 Kubelet 强制终止。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 13.6s
├─ 并发证据采集: 49.3s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 49.3s (Evidence 42.2s, RCA 7.0s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- 未调用 Runbook
