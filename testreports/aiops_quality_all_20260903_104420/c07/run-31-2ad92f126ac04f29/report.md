## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | Pod `workload-dff5cbc6b-kmfxx` 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s API | `container.waiting_reason`: `CrashLoopBackOff` (Pod `aiops-case-07/workload-dff5cbc6b-kmfxx`, container `app`) | 确认当前 Pod 处于重启循环的最终阻塞状态 |
| 2 | K8s Event | K8s API | `BackOff` 事件: `Back-off restarting failed container app ... (x246 over 56m)` | 证实应用已发生高频重启，导致 kubelet 主动退避 |
| 3 | K8s State | K8s API | `container.last_terminated_reason`: `Error`；`container.last_exit_code`: `78` | 提供终止原因，确认容器因非零退出码异常结束 |
| 4 | K8s State | K8s API | `container.restart_count`: `15`；`ContainersReady`: `False` | 量化重启频率，确认应用不可达 |
| 5 | Logging | Elasticsearch | 日志聚合 (`occurrence_count: 8`)：`"CONFIG_MISSING"` (`http_status: 500`, `path: "/work"`)；数值字段 `allocated_mib` 在观察窗口内持续为 `0` | 捕获容器崩溃前最后一次请求的错误模式，表明应用启动后未能获取必要资源 |
| 6 | Tracing | Tempo | 关联 Trace (`trace_id: 65684c8c074b2b13bde640e742613caa`)：`GET /work` 响应 `500`，标记 `aiops.observed_mode: "config_missing_exit"` | 与日志证据完全匹配，精确定位到应用主动退出时的请求上下文 |
| 7 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1` (reason: `CrashLoopBackOff`)；`kube_pod_container_status_restarts_total=15` | 独立观测验证了 K8s 状态中的重启计数和退出原因 |
| 8 | Tracing | Deepflow | L7 Flow 聚合：`GET /work` 响应 `500` (`occurrence_count: 9`)，跨多个 trace_id | 证实该错误模式在时间窗口内具有重复性，非偶发现象 |

**证据逻辑说明**
Kubernetes 指标证实了容器因 `CrashLoopBackOff` 状态持续存在且重启计数达 15 次。应用日志明确记录了崩溃前的最后状态为 `CONFIG_MISSING`，且伴随 `allocated_mib=0` 的异常数值。Trace 数据 (Tempo/Deepflow) 进一步将这一错误锁定在 `GET /work` 请求的处理路径上，并标记了 `config_missing_exit` 模式。三者形成了完整的闭环：配置缺失导致应用主动退出（Exit 78），触发 K8s 重启策略，最终进入 CrashLoopBackOff。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动阶段配置缺失 (CONFIG_MISSING) → 应用代码捕获错误并主动执行 sys.exit(78) → kubelet 检测到容器异常退出并反复重启 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因为：**应用进程在启动阶段因缺失关键配置（导致 `allocated_mib` 为 0）而主动退出。**

具体判定依据如下：
1. **退出码与状态确认**：K8s 状态显示容器以 Exit Code `78` 终止并进入 `CrashLoopBackOff`，这通常对应应用程序层面的错误退出。
2. **直接错误源**：日志与 Trace 证据高度一致（fact-5 与 fact-6），均在崩溃前捕获到 `CONFIG_MISSING` 错误及 `aiops.observed_mode: "config_missing_exit"` 标记。
3. **行为机制**：Exit Code 78 并非内核 OOM Kill 或系统级故障代码，而是应用业务逻辑中用于处理“配置缺失”等可恢复错误的典型退出码。

综上，Pod 的 CrashLoopBackOff 是应用因无法获取所需配置而主动反复退出的直接结果。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 20.9s
├─ 并发证据采集: 61.1s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 61.1s (Evidence 50.6s, RCA 10.3s)
└─ 汇总总结: 14.1s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
