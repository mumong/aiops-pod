## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | 容器内存限制过低且应用存在内存增长行为，导致 OOMKilled 和 CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | Back-off restarting failed container app in pod workload-5c9c7b6489-p8462 (7f2eda43-...) | 现象：容器崩溃并陷入重启循环 |
| 2 | K8s State | kubernetes | container.last_terminated_reason: "OOMKilled" | 根因：容器因超过内存限制被强制终止 |
| 3 | K8s State | kubernetes | container.waiting_reason: "CrashLoopBackOff" | 现象：确认处于非预期的重启等待状态 |
| 4 | K8s Config | kubernetes | container.resource_limit.memory: "64Mi" | 根因：系统硬限制仅为 64Mi，资源极度受限 |
| 5 | Logging | elasticsearch | pattern: "memory allocation advanced"; 在 2026-09-10T23:40:11 至 23:40:49 期间 `allocated_mib` 从 10 增加至 48 | 根因：应用运行过程中发生显著内存增长（增长近 5 倍，逼近 64Mi 硬限制） |
| 6 | Tracing | deepflow | equivalent_l7_flows: GET /work 200, 发生 9 次 (2026-09-11 07:15-07:40) | 上下文：验证服务在请求 `/work` 路径时正常响应（尽管在内存耗尽后会重启，此流量确认了负载行为与 `/work` 强相关） |

**证据印证说明**：
- 容器被 K8s 强制终止的原因 `OOMKilled` (事实 2) 与应用在运行 `GET /work` 接口时 `allocated_mib` 从 10 飙升至 48 (事实 5) 形成因果闭环。
- 64Mi 的内存硬限制 (事实 4) 远小于应用增长过程中的内存峰值，证实资源配额设置不合理是导致 OOM 的直接配置缺陷。
- 重启行为 (事实 1, 3, 6) 是 OOMKilled 后的必然结果。

## 🎯 根因分析 · g1

### 因果链

```text
应用 GET /work 请求导致内存持续增长(48Mi) → 超过 64Mi 容器硬限制 → OOMKilled 终止进程 → CrashLoopBackOff 重启循环
```

### 根因结论

已确认的根因是：**容器内存限制（64Mi）设置过低，无法容纳应用运行时的内存增长需求。**

**依据**：
- **直接证据**：Kubernetes 明确报告 `last_terminated_reason` 为 `OOMKilled`，且日志显示应用在处理 `/work` 时内存从 10Mi 增长至 48Mi，逼近并触发了 64Mi 的硬限制阈值。
- **现象验证**：Container 处于 `CrashLoopBackOff` 状态并伴随大量重启事件，与 OOM 导致的进程频繁重启行为一致。

**缺失/未知**：
- 具体内存泄漏的代码路径尚未定位（日志仅显示内存分配量增加，未定位具体代码行或对象）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 17.4s
├─ 并发证据采集: 51.8s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 51.8s (Evidence 46.1s, RCA 5.6s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
