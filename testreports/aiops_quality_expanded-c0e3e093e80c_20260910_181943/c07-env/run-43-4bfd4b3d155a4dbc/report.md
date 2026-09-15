## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod workload 的容器配置中缺失必要的环境变量 `APP_REQUIRED_CONFIG`，导致应用启动脚本执行时主动退出并返回 Exit Code 78，进而触发 Kubernetes 的 CrashLoopBackOff 机制。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-v10/workload` 状态: `Running`, `ContainersReady=False` (reason: `ContainersNotReady`), 重启计数: 20 | 确认容器持续崩溃并处于重启循环中 |
| 2 | K8s State | Kubernetes | 容器 `app` 状态: 终止原因 `Error`, 退出码 `78`, 等待原因 `CrashLoopBackOff` | 明确应用以非零码 78 主动失败，触发 K8s 指数退避重启 |
| 3 | K8s Event | Kubernetes | `BackOff` 事件: `Back-off restarting failed container app` (79m 内 351 次) | 验证了长时间、高频的崩溃重启行为 |
| 4 | Logging | Elasticsearch | `2026-09-11T16:11:27.203Z`: `APP_REQUIRED_CONFIG environment variable is missing` | 提供了缺失关键配置导致启动失败的直接证据 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason{reason="Error"}=1` <br> `kube_pod_container_status_waiting_reason{reason="CrashLoopBackOff"}=1` | 监控侧确认了最终的终止状态和当前等待状态 |

**证据关联：**
日志中的关键错误（事实 #4）解释了退出码 78 的原因；退出码与状态（事实 #2）结合事件（事实 #3）确认了 K8s 的 CrashLoopBackOff 机制；指标（事实 #5）从监控角度交叉验证了上述状态。

## 🎯 根因分析 · g1

### 因果链

```text
容器配置缺失 `APP_REQUIRED_CONFIG` → 启动脚本执行失败 (Exit Code 78) → K8s 触发 `CrashLoopBackOff` → Pod 处于 `ContainersReady=False` 且不断重启
```

### 根因结论

已确认根因。Pod `aiops-case-v10/workload` 的容器 `app` 因缺少必要的环境变量 `APP_REQUIRED_CONFIG`（事实 #4）导致应用启动即退出（事实 #2），进而引发 Kubernetes 的 `CrashLoopBackOff` 机制（事实 #1, #3, #5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 18.2s
├─ 并发证据采集: 33.6s
│  └─ g1 aiops-case-v10/workload: 33.6s (Evidence 27.3s, RCA 6.2s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
