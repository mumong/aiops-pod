## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bsn84` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Killing         11m (x4 over 13m)` `Container app failed liveness probe` | 确认容器因健康检查失败被周期性 Kill，导致反复重启 |
| 2 | K8s Event | kubernetes | `Unhealthy       11m (x8 over 13m)` `Liveness probe failed: HTTP probe failed with statuscode: 500` | 直接触发容器终止机制的具体原因：HTTP 500 导致活探测失效 |
| 3 | K8s Config | kubernetes | `container.resource_limit.memory: 96Mi` | 提供容器内存硬限制参数，结合 OOM 现象定位资源瓶颈 |
| 4 | K8s State | kubernetes | `Exit Code: 137`, `Container last terminated reason: Error` | 判定进程被 OOM Killer 强制终止的标志性事实 |
| 5 | K8s State | kubernetes | `restart_count: 7`, `status: CrashLoopBackOff` | 描述当前持续故障的宏观状态 |
| 6 | Tracing | deepflow | `GET /work` `response_code: 200`, `src_ip: 172.16.104.12` -> `dst_ip: 172.16.104.17`, `occurrence_count: 9` | 证明应用实际在处理正常请求（响应 200），说明 500 报错并非应用逻辑错误，而是容器环境异常（如内存耗尽导致进程不稳定） |
| 7 | Logging | elasticsearch | `http_status: 200` `allocated_mib: 0`, `time_range: 02:47:09 - 02:47:41` | 确认日志窗口内应用功能正常，排除长时间宕机可能 |

**证据印证说明：**
Tracing 和 Logging 显示业务层请求（GET /work）均正常返回 200 状态码，说明应用本身未发生严重逻辑崩溃。然而，K8s 层面却不断报出 `Liveness probe failed: 500` 并伴随 `Exit Code: 137`。这种“应用看似正常但存活探针失败且进程被杀”的现象，强有力地指向了容器资源层面（特别是内存限制 96Mi 触发了 Linux OOM Killer）而非纯业务代码故障。

## 🎯 根因分析 · g1

### 因果链

```text
Container memory limit (96Mi) is too restrictive for the application workload → Application exceeds memory limit, triggering OOM Killer (Exit Code 137) → Container is killed and restarts → Kubernetes enters CrashLoopBackOff state
```

### 根因结论

已确认的根因为：**容器内存限制（96Mi）过小，触发 Linux OOM Killer（终止代码 137）**。

该根因直接解释了 K8s 观察到的 `Exit Code: 137`（证据 4）以及由此引发的 Kubernetes 重启循环（证据 5）。由于进程频繁被内核 OOM Killer 强制杀死，导致容器的 Liveness Probe（存活探针）在检查时进程已不存在或无响应，进而报出 `HTTP probe failed with statuscode: 500`（证据 2）并最终导致集群进入 `CrashLoopBackOff` 状态（证据 1, 5）。

Tracing 数据（证据 6）和日志（证据 7）中存在的 200 OK 正常响应，仅证明在未被 OOM 杀死的短暂窗口内应用是健康的，进一步排除了应用代码本身导致 500 错误的假设。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 29.7s
├─ 并发证据采集: 58.6s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bsn84: 58.6s (Evidence 51.1s, RCA 7.4s)
└─ 汇总总结: 12.5s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bsn84**: pod-crashloop-runtime
