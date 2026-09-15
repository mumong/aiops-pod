## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | 应用代码在处理 /work 端点时存在内存泄漏，导致容器内存使用量线性增长并超过 64Mi 的限制，触发 OOMKilled 和 CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: `CrashLoopBackOff` | 确认容器当前处于崩溃重启状态 |
| 2 | K8s State | kubernetes | `container.last_terminated_reason`: `OOMKilled` | 确认容器被系统强制终止的直接原因是内存超限 |
| 3 | K8s State | kubernetes | `container.last_exit_code`: `137` | 进程被 SIGKILL (Exit Code 128 + 9)，符合 OOMKilled 特征 |
| 4 | K8s Config | kubernetes | `container.resource_limit.memory`: `64Mi` | 提供触发 OOM 的硬资源限制阈值 |
| 5 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason`: `1` (reason=OOMKilled) | 从监控视角再次确认终止原因为 OOM |
| 6 | Logging | elasticsearch | `http_request` at `/work`: `allocated_mib` 从 10.0 增至 48.0 | 展示请求处理期间内存分配量显著上升 |
| 7 | Tracing | tempo | `GET /work` span: `aiops.observed_mode: oom_growth` | 提供应用代码层面的观测模式证据 |

**证据关联说明：**
*   **K8s 状态与指标互证**：`OOMKilled` 终止原因与退出码 `137` 直接对应，且 Prometheus 指标独立确认了同一终止原因，排除了配置错误导致重启的可能性。
*   **日志与 Trace 关联**：日志中 `/work` 端点处理期间 `allocated_mib` 持续增长（10 -> 48 MiB），且 Tracing 中同名请求明确标注 `oom_growth` 模式。这表明内存增长发生在处理该业务逻辑的过程中，支持“内存泄漏/消耗”假说。
*   **因果闭环**：内存持续增长（Log/Trace） + 硬限制 64Mi（Config） → 触发内核 OOM Killer（State/Metric） → 导致 CrashLoopBackOff（State）。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码在处理 /work 端点时产生高内存分配 (Log 1, Trace 7) → 内存消耗持续增长并超过 64Mi 容器限制 (Config 4) → 触发 OOMKilled 终止进程 (State 2, Metric 5) → 进入 CrashLoopBackOff 循环 (State 1)
```

### 根因结论

已确认根因为：**应用在处理 `/work` 端点时存在内存泄漏（或极高的瞬时内存消耗），导致内存使用量持续增长并超过 64Mi 的 `resource_limit` 硬限制。**

*   **支持证据**：
    1.  **直接终止原因**：K8s 状态与 Prometheus 指标均一致显示终止原因为 `OOMKilled`，退出码 `137` 符合该特征 [证据 2, 3, 5]。
    2.  **内存增长模式**：日志显示在处理 `/work` 请求时，`allocated_mib` 出现显著增长（10Mi -> 48Mi）[证据 6]；Tracing 明确记录 `oom_growth` 观测模式 [证据 7]。这证实了内存消耗与特定业务逻辑强相关，而非空闲态泄漏。
    3.  **资源瓶颈**：容器内存上限仅为 `64Mi` [证据 4]，而请求处理过程中内存占用已达到 `48Mi`，逼近极限且存在进一步增长空间，最终触发系统级 OOM。

*   **现象解释**：进程被 OOMKilled 后，Kubelet 触发重启策略，由于重启频繁且可能因同样的内存分配逻辑再次触发 OOM，K8s 进入 `CrashLoopBackOff` 状态 [证据 1]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 16.9s
├─ 并发证据采集: 82.1s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 82.1s (Evidence 74.6s, RCA 7.3s)
└─ 汇总总结: 13.3s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
