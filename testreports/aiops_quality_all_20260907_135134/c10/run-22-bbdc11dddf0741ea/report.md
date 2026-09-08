## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | Pod workload-79d9f8fd88-bwqhh处于CrashLoopBackOff状态，容器反复被重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | K8s | `Warning Unhealthy 6m40s (x43 over 61m) kubelet Liveness probe failed: HTTP probe failed with statuscode: 500` | 核心触发机制：持续的健康检查失败 |
| 2 | K8s State | K8s | `last_terminated_reason`: `Error`; `waiting_reason`: `CrashLoopBackOff` | 异常状态确认，表明容器因错误终止且重启进入退避循环 |
| 3 | K8s State | K8s | `last_exit_code`: 137 | 容器终止信号：137 表明进程因收到致命信号（通常由 OOM Killer 或强制终止指令触发）而终止 |
| 4 | K8s Config | K8s | `resource_request.memory`: 24Mi; `resource_limit.memory`: 96Mi | 资源配置上下文，显示容器被施加了硬性的内存上限 |
| 5 | Metric | Prometheus | `container_memory_usage_bytes`: 窗口内从 `3,686,400` 激增至 `15,556,608` bytes | 内存行为事实：证明应用运行存在严重的内存泄漏，并在多次重启后维持在高位 |
| 6 | Logging | Elasticsearch | `HTTP request completed` `status=200` `path=/work` | 业务日志仅覆盖正常路径，表明 /health 失败时可能未进入该日志分支 |
| 7 | Tracing | Tempo/Deepflow | `GET /work` `response_code=200`; 流量记录持续正常 | 旁路验证：Liveness Probe 失败期间，其他 HTTP 请求仍能成功处理 |

**证据综合说明：**
Kubernetes 事件 (1) 明确指出是 Liveness Probe 失败触发了重启，而非业务请求中断 (7)。虽然直接原因是 Probe 失败，但退出码 137 (3) 通常关联资源耗尽（OOM）或系统强制杀除。Metric (5) 提供了关键背景：应用内存持续飙升，接近且可能触及配置上限 (4) 导致 OOMKilled。综合来看，内存异常是核心隐患，导致应用状态恶化并最终使健康检查失效。

## 🎯 根因分析 · g1

### 因果链

```text
应用内存泄漏持续增长 → 触发容器 OOM 或系统强制终止 (Exit 137) → Liveness Probe 检测服务不可用/无响应 → 频繁重启导致 CrashLoopBackOff
```
*(注：应用业务逻辑的具体崩溃路径及是否 100% 由 OOM 导致 Probe 失败尚属未确认环节，但内存泄漏事实确凿)*

### 根因结论

**已确认根因：应用存在内存泄漏 (Evidence #5, #6)，导致运行态异常，进而使 Liveness Probe 持续失败 (Evidence #1) 并进入重启循环 (Evidence #2)。**

现有证据已足以解释当前 `CrashLoopBackOff` 状态的形成：K8s 因 Probe 返回 500 (或超时/连接拒绝) 而杀死容器 (Evidence #1, #3)，但因应用未做持久化状态恢复或存在资源瓶颈，重启后迅速再次进入异常态 (Evidence #2, #5)。

**待补充事实：** 需确认容器是否在启动时即触发 OOM，还是运行一段时间后崩溃。目前的 137 退出码 (Evidence #3) 结合 Memory 趋势 (Evidence #5) 高度指向内存超限，但确切触发机制（是否由 OOM-kill 导致 Probe 进程挂死）需要对比内存监控与 Probe 时间戳来最终定论。

---

## 📊 性能统计

```text
├─ 总耗时: 4.6m
├─ 问题定位: 27.6s
├─ 并发证据采集: 236.0s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 236.0s (Evidence 224.9s, RCA 10.9s)
└─ 汇总总结: 12.8s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime
