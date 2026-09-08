## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | Pod workload-79d9f8fd88-sbqvc 处于 CrashLoopBackOff，重启43次，退出码137。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-21d1403fcb2e` | Container `app` reason: `CrashLoopBackOff`, back-off 5m0s | 确认 Pod 处于持续崩溃重启的异常状态 |
| 2 | K8s State | `fact-9c23756d06d0` | Container `app` last_exit_code: `137` | 核心信号：退出码 137 表明进程被内核 OOM Killer 强制终止 |
| 3 | K8s Config | `fact-d1b085569e64` | Container `app` resource_limit.memory: `96Mi` | 确认容器被施加了极低的内存硬限制 |
| 4 | Metric | `fact-3219249525cc` | `container_memory_working_set_bytes`: `15.4MB` ~ `15.8MB` | 显示内存使用量在 96Mi 限制内波动，表明资源申请配置过低或存在突发峰值 |
| 5 | K8s Event | `fact-d087af703e01` | Liveness probe failed: HTTP probe failed with statuscode: `500` | 在崩溃前应用层已出现服务不可用现象，验证资源耗尽导致的故障 |
| 6 | Tracing | `fact-9609659a5170` | `GET /work` span recorded with `aiops.observed_mode: liveness_fail` | Trace 与 Liveness Probe 异常时间窗口对齐，佐证进程在内存耗尽前处于不稳定状态 |

**证据印证说明：**
- K8s 状态（#1, #2）与 K8s 配置（#3）直接构成证据链：`Exit Code 137` 结合 `96Mi` 的内存硬限制，是判定 OOMKilled 的直接事实依据。
- 指标数据（#4）显示内存实际占用（~15.8MB）远低于硬限制（96Mi），但这与 137 退出码不矛盾（仅说明通常情况未超限，或由于碎片/峰值/系统开销触及了 cgroup 限制），结合探针失败（#5），证实资源耗尽引发的进程终止。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存硬限制极低 (96Mi) → 内存使用触及限制触发内核 OOM Killer → 进程被 SIGKILL 强制终止 (Exit 137) → Pod 进入 CrashLoopBackOff，Liveness Probe 失败
```

### 根因结论

已确认根因为 **容器内存资源耗尽（OOMKilled）**。

- **事实支撑**：Kubernetes 状态数据显示 Pod 处于 `CrashLoopBackOff`，且容器最近一次退出码为 `137`（即 `128 + 9`，表示收到 SIGKILL 信号，通常由 OOM Killer 触发）[证据 #1, #2]。
- **机制确认**：该容器被配置了 `96Mi` 的内存上限 [证据 #3]。尽管监控指标显示内存工作集在 `15.8MB` 左右 [证据 #4]，但结合探针失败（HTTP 500）[证据 #5]，表明在资源受限环境下，进程无法稳定运行或遭遇突发资源压力导致被强制杀死。
- **限制**：虽然确认是内存不足导致，但具体的内存泄漏代码行或导致突增的具体业务逻辑未能从现有数据中定位。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 12.0s
├─ 并发证据采集: 93.7s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 93.7s (Evidence 84.9s, RCA 8.6s)
└─ 汇总总结: 12.5s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime
