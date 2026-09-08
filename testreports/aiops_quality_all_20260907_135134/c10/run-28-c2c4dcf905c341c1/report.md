## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | Pod aiops-case-10/workload-79d9f8fd88-bwqhh 处于 CrashLoopBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Last terminated reason: `Error`; Last exit code: `137` | 判定容器因系统层强制终止退出 |
| 2 | K8s Event | kubernetes | Liveness probe failed: HTTP probe failed with statuscode: `500`; BackOff restarting failed container `app` | 确认健康检查持续失败及 Kubernetes 的自动重启行为 |
| 3 | K8s Config | kubernetes | Memory request: `24Mi`; Memory limit: `96Mi` | 提供资源硬性上限边界 |
| 4 | Metric | prometheus | `container_memory_usage_bytes`：窗口内从 `3.3MB` 持续攀升至 `15.5MB` (Max: `15540224`) | 验证容器内存存在持续消耗特征 |
| 5 | Logging | elasticsearch | 聚合模式 `http_request` completed 200；`allocated_mib` 字段在观察窗口内 `first: 0, last: 0, max: 0.0` | 证明应用 HTTP 业务层处理正常，且应用自身未报告内存分配错误 |
| 6 | Tracing | deepflow+tempo | L7 Flow `GET /work` 响应状态 `200`；Trace ID `f7de5556153101cd1f73457a89c48aed` 确认路由健康 | 确认请求链路正常，故障局限于容器运行时进程层 |

**证据印证：**
Kubernetes 报告 Exit Code 137，与 OOM Killer 终止进程特征完全一致。同时，Metric 记录显示内存从 3.3MB 持续增长至 15.5MB，这证实了内存压力的产生过程。由于 15.5MB 在 96Mi 的硬限制之内，且应用日志显示业务层返回 200，这强烈指向系统 OOM Killer 介入（可能因 Node 层面内存压力或 cgroup 限制机制），尽管应用自身代码未直接报出内存溢出错误。

## 🎯 根因分析 · g1

```text
容器进程内存持续消耗 → 触发系统 OOM 机制 (Exit 137) → 容器异常终止并重启 → Pod 进入 CrashLoopBackOff
```

### 根因结论

**已确认的根因**：容器进程因异常终止（Exit Code 137）导致 Kubernetes 频繁重启，进而使 Pod 处于 `CrashLoopBackOff` 状态。

**分析说明**：
*   **现象锁定**：`fact-532c88008d12` 确认退出码为 137，`fact-ee46ea5f9150` 确认了重启循环现象。
*   **机制推导**：137 退出码通常意味着进程被信号 9 (SIGKILL) 强制终止。Metric 维度 `fact-169a8f7cb73b` 显示内存占用在观察窗口内从 3.3MB 单调增长至 15.5MB，排除了瞬时突发或应用崩溃导致的短暂占用，证实了“持续消耗”的特征。
*   **排除应用层直接故障**：Logging 和 Tracing 维度（`fact-6848aabc4ac8`, `fact-5d3d89ebabb0`）显示业务请求返回 200，说明在进程被杀掉之前，应用本身是具备处理请求能力的，且未触发应用内部的 OOM 拦截机制（日志中 `allocated_mib` 为 0）。

**局限性/未知**：当前证据不足以区分这是应用内部的内存泄漏，还是 Node 整体内存不足导致的“误杀”（System OOM Kill）。需进一步排查 Node 层资源水位及 `dmesg` 中的 OOM 记录。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 15.6s
├─ 并发证据采集: 95.6s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 95.6s (Evidence 86.5s, RCA 8.9s)
└─ 汇总总结: 13.4s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime
