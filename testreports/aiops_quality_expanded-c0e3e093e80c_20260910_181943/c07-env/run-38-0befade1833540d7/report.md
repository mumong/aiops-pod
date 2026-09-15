## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | 容器应用主进程缺少必需的环境变量 APP_REQUIRED_CONFIG 导致启动即退出（Exit Code 78） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Back-off restarting failed container app in pod workload_aiops-case-v10(d3e0dc86-6f8b-4f29-a50c-826bf2a1f1e6)` | 证实容器因启动失败被反复重启 |
| 2 | K8s State | kubelet | `last_terminated_reason: Error` (Exit Code: 78) | 确认主进程异常退出并返回非零状态码 |
| 3 | Logging | elasticsearch | `APP_REQUIRED_CONFIG environment variable is missing` | 直接定位到应用层缺少特定配置变量导致崩溃 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total = 19` | 从监控系统独立印证了 19 次重启的事实 |
| 5 | K8s State | kubelet | `pod.phase: Running` (但 `ContainersReady: False`) | 表明 Pod 存活但业务容器未就绪，状态与预期不符 |

K8s 层面的重启计数（#1, #2, #4）与日志中记录的退出原因（#3）完全一致，且由不同监控系统独立采集，排除了单一数据源偏差。日志中具体的缺失变量名提供了决定性的故障根因，解释了为何容器会频繁退出。

## 🎯 根因分析 · g1

### 因果链

```text
环境变量 APP_REQUIRED_CONFIG 缺失 → 应用主进程启动即报错退出 (Exit Code 78) → K8s 触发 CrashLoopBackOff 机制并反复重启 → 用户可见容器反复重启且无法就绪
```

### 根因结论

已确认的根因为：应用主进程在启动过程中因缺少必需的 `APP_REQUIRED_CONFIG` 环境变量而立即退出（Exit Code 78）。该事实由 `elasticsearch` 日志（#3）直接捕获，并由 `kubelet` 的崩溃重启事件（#1, #2）和 `prometheus` 重启指标（#4）交叉验证。

---

## 📊 性能统计

```text
├─ 总耗时: 9.2m
├─ 问题定位: 13.3s
├─ 并发证据采集: 534.1s
│  └─ g1 aiops-case-v10/workload: 534.1s (Evidence 527.8s, RCA 6.3s)
└─ 汇总总结: 7.3s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime, pod-oomkilled
