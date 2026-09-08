## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | Pod workload-dff5cbc6b-fkzvn 处于 CrashLoopBackOff 状态，不断重启失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.status=Running`, `restart_count=12`, `container.waiting_reason=CrashLoopBackOff`, `exit_code=78` | 确认 Pod 处于持续重启的失败循环中 |
| 2 | K8s Event | Kubernetes | `BackOff` 事件，`x175 over 41m`，`back-off 5m0s restarting failed container` | 证明重启间隔正在拉长，系统进入退避冷却期 |
| 3 | Logging | Elasticsearch | `CONFIG_MISSING` 错误日志模式，`http_status=500`，发生 8 次（14:46 - 15:13） | 揭示应用崩溃的直接触发原因为配置缺失 |
| 4 | K8s Config | Kubernetes | `resource_limit.cpu=200m`, `resource_limit.memory=96Mi` | 排除因资源硬限制（OOMKill）导致崩溃的可能性 |
| 5 | Tracing | Deepflow | HTTP GET `/work` 响应码 500，`response_status=3` | 确认崩溃由外部请求或内部初始化逻辑触发 |
| 6 | Tracing | Tempo | Trace `80eb7bda337870843840252aa8d6463a`，`exit_code=78`，`reason=config_missing_exit` | 关联 Trace 与日志，证明退出码 78 是由配置缺失导致的主动退出 |
| 7 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1` (reason: CrashLoopBackOff) | 独立观测确认 Pod 处于等待/重启状态 |

**证据说明：**
Kubernetes 状态确认了容器不断以 `exitCode 78` 退出的事实。Logging 中反复出现的 `CONFIG_MISSING` 错误模式，结合 Tracing 中 `reason=config_missing_exit` 的显式标记，直接锁定了崩溃原因。Metric 仅提供了当前状态的独立佐证，未提供趋势变化。配置检查表明 CPU 和内存限制充足，排除了资源耗尽的可能。

## 🎯 根因分析 · g1

### 因果链

```text
运行环境缺失必要配置文件 (事实 3, 6) → 应用启动脚本检测到 CONFIG_MISSING 并抛出异常 (事实 3, 6) → 容器进程以 exitCode 78 主动退出 (事实 1, 6) → Pod 触发 CrashLoopBackOff 机制 (事实 1, 2)
```

### 根因结论

已确认根因为：**应用启动或初始化过程中依赖的配置文件缺失，导致进程以退出码 78 崩溃。**

该结论由以下独立观测交叉印证：
1.  **日志层面**：Elasticsearch 捕获了 8 次 `CONFIG_MISSING` 错误模式（证据 #3）。
2.  **追踪层面**：Tempo Trace 明确记录了应用退出原因为 `config_missing_exit`，且对应的 Span 状态与日志时间窗一致（证据 #6）。
3.  **状态层面**：Kubernetes 显示容器不断重启且退出码固定为 78，符合应用主动报错的特征，而非资源不足导致的 OOM 或系统级错误（证据 #1, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 16.8s
├─ 并发证据采集: 61.4s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 61.4s (Evidence 52.6s, RCA 8.6s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime, pod-oomkilled
