## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod aiops-case-07/workload-dff5cbc6b-sjvxl 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.app: waiting_reason=CrashLoopBackOff, last_terminated_reason=Error, exit_code=78, restart_count=8 | 确认应用进程反复异常终止并触发回退重启机制 |
| 2 | K8s State | kubernetes | pod.phase=Running, pod.condition={Ready: False, ContainersReady: False, reason=ContainersNotReady} | 确认 Pod 节点处于运行状态但应用容器未就绪 |
| 3 | K8s Config | kubernetes | container.app resource_request={cpu: 20m, memory: 24Mi}, resource_limit={cpu: 200m, memory: 96Mi} | 提供资源上下文，确认启动前调度阶段资源已预留 |
| 4 | K8s Event | kubernetes | event.message=Warning BackOff restarting failed container app... Back-off 5m0s | 确认重启行为已被 K8s 调度器标记并延后 |
| 5 | Logging | elasticsearch | pattern=http_request(level: error, http_status: 500, message: CONFIG_MISSING, path: /work), occurrence_count=8, first=2026-09-10T20:30:51Z, last=2026-09-10T20:47:12Z | 揭示应用主动检测到关键配置缺失后返回 500 错误，该错误发生在启动初始化阶段 |
| 6 | Tracing | deepflow+tempo | l7_flow(GET /work, dst_ip: 172.16.104.63, response_code: 500), application_span(aiops.observed_mode: config_missing_exit, trace_id: a358165e4c5df7b2882c057473693f30) | 从流量和调用链角度独立印证了 /work 端点的 500 响应及配置缺失模式 |
| 7 | Metric | prometheus | kube_pod_container_status_restarts_total={first: 0.0, last: 7.0, max: 7.0, sample_count: 17}, trend_evaluable=true | 展示从 0 次到 7 次重启的累积增长趋势，证实重启行为集中在本次观察窗口内 |
| 8 | Metric | prometheus | kube_pod_status_phase={value: 1, labels: {kube-state-metrics, phase: Running}} | 辅助确认节点本身调度正常，排除底层调度或集群级故障 |

**证据印证：**
日志 `CONFIG_MISSING` 与 K8s 事件 `BackOff` 时间线（20:30-20:47）完全吻合，表明每次服务初始化返回 500 错误均触发一次重启。Tracing 数据中的 `aiops.observed_mode: config_missing_exit` 与日志模式直接对应，证实了退出是由应用逻辑触发的，而非 OOM 或系统级崩溃。Metrics 的 restart 趋势图验证了该循环持续发生了至少 7-8 次。

## 🎯 根因分析 · g1

### 因果链
```text
应用启动初始化 → 检测到关键配置缺失 (CONFIG_MISSING) → 触发业务逻辑终止 (exit_code: 78, HTTP 500) → 容器崩溃并触发 K8s 回退重启 (CrashLoopBackOff)
```

### 根因结论
已确认根因为**应用启动时依赖的关键配置项缺失**。
应用进程在初始化阶段检测到配置缺失（通过日志 `message: CONFIG_MISSING` 和 Tracing `aiops.observed_mode: config_missing_exit` 确认），主动以退出码 78 终止进程并返回 HTTP 500 状态码。这种非零退出触发了 Kubernetes 的重启机制，导致 `CrashLoopBackOff` 现象持续发生。缺少该关键配置是造成应用无法启动并持续崩溃的直接原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 19.6s
├─ 并发证据采集: 51.3s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 51.3s (Evidence 42.0s, RCA 9.1s)
└─ 汇总总结: 13.4s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
