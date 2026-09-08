## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | Pod应用容器启动时抛出CONFIG_MISSING错误（退出码78），因配置项缺失导致进程无法启动并持续崩溃重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet (fact-5a71b53e239d) | `Back-off restarting failed container app in pod workload-dff5cbc6b-fkzvn` (x243 over 57m) | 证实容器反复崩溃并进入 BackOff 状态 |
| 2 | K8s State | K8s API (fact-87b51fee0784, fact-05cbaf20ff9c) | `Waiting Reason: CrashLoopBackOff`, `Last Exit Code: 78` | 确认当前异常状态及导致退出的具体错误码 |
| 3 | Logging | Elasticsearch (fact-52fcec92a7b8 et al.) | `CONFIG_MISSING`, `HTTP 500`, `/work` (occurrence_count: 8) | 提供导致退出码 78 的直接应用层原因 |
| 4 | Metric | Prometheus (fact-906caf422f1f, fact-b327957dd4d9) | `kube_pod_container_status_waiting_reason{reason="CrashLoopBackOff"}=1`, `restarts_total=15` | 独立观测确认 Pod 处于 CrashLoopBackOff 状态 |

上述 K8s 事件与状态证实了 CrashLoopBackOff 现象，应用日志中的 `CONFIG_MISSING` 错误与退出码 78 完全对应，指标监控进一步验证了重启的持续性。

## 🎯 根因分析 · g1

```text
配置项缺失(CONFIG_MISSING) → 应用启动失败(退出码78) → 容器反复崩溃(CrashLoopBackOff) → 用户可见 Pod 持续重启
```

### 根因结论
**已确认根因**：应用启动逻辑中检测到关键配置项缺失，导致进程立即退出（Exit Code 78）。

**证据支撑**：
- **现象**：K8s 显示 Pod 处于 `CrashLoopBackOff` 状态（事实 `fact-87b51fee0784`），容器退出码为 78（事实 `fact-05cbaf20ff9c`），且经历了大量重启（事实 `fact-5a71b53e239d`）。
- **机制**：日志中重复出现 `CONFIG_MISSING` 错误（事实 `fact-52fcec92a7b8`），直接解释了退出码 78 的来源。
- **验证**：Metric 监控确认容器因 `CrashLoopBackOff` 原因处于等待状态（事实 `fact-906caf422f1f`），与 K8s 状态一致。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 26.7s
├─ 并发证据采集: 53.7s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 53.7s (Evidence 48.5s, RCA 5.0s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
