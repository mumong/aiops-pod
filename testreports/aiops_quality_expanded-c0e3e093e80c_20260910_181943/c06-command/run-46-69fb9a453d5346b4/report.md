## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod aiops-case-v08/workload 处于 CrashLoopBackOff 状态，容器 app 反复以 Exit Code 127 崩溃 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `exit_code: 127`, `restart_count: 15` | 确认进程因找不到命令而崩溃并重复重启 |
| 2 | K8s Event | Kubernetes | `Back-off restarting failed container app in pod workload_aiops-case-v08(00e5e755-886e-4661-9e8a-00d1e71595f6)` | 确认当前进入 CrashLoopBackOff 状态的具体原因 |
| 3 | Logging | Elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` (fact-13cb3242823d) | 确认 Exit Code 127 的准确原因是缺失的可执行文件路径 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 15` (fact-ef2b869cb3b6) | 独立印证容器的高频重启状态 |

**证据印证说明：**
1. **日志与状态互证**：日志直接指出了 `/opt/app/unavailable-command` 不存在，与 Kubernetes 状态中 `exit_code: 127`（标准命令未找到返回值）完全对应，构成闭环证据。
2. **重启行为验证**：Event 中的 `Back-off restarting` 与 Metric 中的 `restart_count: 15` 以及 K8s 状态中的 `CrashLoopBackOff` 共同描绘了同一持续的故障周期。
3. **无其他异常**：Tracing 维度为空且无其他资源限制报错，进一步排除了网络或资源不足导致 CrashLoopBackOff 的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
容器镜像内缺失 /opt/app/unavailable-command 可执行文件 → shell (sh -c exec) 执行时返回 Exit Code 127 (Command not found) → kubelet 检测到容器非正常退出并触发指数退避重启 → Pod 持续处于 CrashLoopBackOff 状态
```

### 根因结论

**已确认的根因**：Pod 启动命令中指定的可执行文件路径 `/opt/app/unavailable-command` 在容器镜像中不存在，导致容器进程启动即失败。

*   **证据支撑**：日志 (fact-13cb3242823d) 明确记录了 `not found` 错误，K8s 状态 (fact-291c42887fb4) 记录了 Exit Code 127，Event (fact-71dffe364d60) 确认了由此引发的重启行为。
*   **结论**：故障原因是配置错误，与集群资源、网络或底层环境无关。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 33.9s
├─ 并发证据采集: 42.0s
│  └─ g1 aiops-case-v08/workload: 42.0s (Evidence 33.5s, RCA 8.3s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime
