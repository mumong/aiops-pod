## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | Application configured with liveness probe failure injection (FAILURE_MODE=liveness_fail) caused Kubelet to terminate the container. While Exit Code 137 (SIGKILL) typically suggests OOM, the concurrent presence of Liveness Probe 500 errors and the absence of OOM-specific logs (e.g., Kernel OOM Killer text) indicates the termination was triggered by the probe failure killing mechanism or the application crashing immediately after the injected failure, rather than a resource exhaustion OOM. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason=CrashLoopBackOff`, `last_terminated_reason=Error`, `restart_count=6`, `last_exit_code=137` (fact-2ddece6800e6, fact-1f96d15c6597, fact-5c71ccdcfbe1, fact-97f9b6c97be6) | 确认应用持续崩溃并退出，退出码 137 为排查初始方向。 |
| 2 | K8s Event | Kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` (fact-d00e925c79ec) | **关键转折**：证明应用非被动死锁，而是处于活跃报错状态，直接触发 Kubelet 的存活检测杀死机制。 |
| 3 | K8s Event | Kubernetes | `Container app failed liveness probe, will be restarted` (fact-f8fd09338356) | 确认 137 信号是由 Kubelet 因探针失败发起的终止行为，而非应用层主动退出或系统层 OOM Killer。 |
| 4 | Metric | Prometheus | `container_memory_usage_bytes` 当前 458752 字节 (458 KiB)，而 `resource_limit.memory` 仅为 96 MiB (fact-59c3848bde0c, fact-328b6fbc830c) | 内存使用极低，结合日志无 OOM Killer 文本，排除内存超限导致 OOM Kill 的可能。 |
| 5 | Logging | Elasticsearch | `http_status=200`, `path=/work`, `allocated_mib` min/max=0, `first`=`last`=0 (fact-6991e4e75964 聚合) | 日志中正常业务请求均为 200 且无内存分配波动，证明应用核心代码未发生故障，故障与探针测试逻辑强相关。 |

**证据链总结：**
日志中的正常 200 响应证明应用主体功能正常；Kubernetes 事件揭示 Liveness 探针收到了 500 错误并主动杀死了容器，解释了为何存在 137 退出码；同时 Metric 证明此时内存远低于硬限制，进一步证实了该故障是探针配置导致的假性 OOM 现象。

## 🎯 根因分析 · g1

### 因果链

```text
应用 Liveness 探针配置了故障注入模式 (FAILURE_MODE=liveness_fail) → 探针检查收到 HTTP 500 错误 → Kubelet 判定容器不健康并执行 SIGKILL (Exit 137) → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

**根因已确认：** 应用因 Liveness Probe 失败被 Kubelet 杀死，而非内存不足（OOM）。

**分析说明：**
虽然 Pod 的退出码为 137（通常对应 SIGKILL 或 OOM Kill），但 **证据 #2 和 #3** 明确显示在容器退出前，Kubelet 记录了 `Liveness probe failed` 及 `Container app failed liveness probe, will be restarted` 事件，确认了 Kill 指令由探针机制触发。此外，**证据 #4** 显示内存占用（~458 KiB）远低于资源硬限制（96 MiB），**证据 #5** 日志中也无 Kernel OOM Killer 记录且业务请求返回 200。综合排除资源耗尽假说，确诊为探针触发机制所致。

---

## 📊 性能统计

```text
├─ 总耗时: 7.5m
├─ 问题定位: 19.3s
├─ 并发证据采集: 415.8s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 415.8s (Evidence 408.0s, RCA 7.6s)
└─ 汇总总结: 12.5s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime, pod-config-error, pod-oomkilled, pod-imagepull-failed
