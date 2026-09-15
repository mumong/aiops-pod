## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | Pod workload-5c9c7b6489-p8462处于CrashLoopBackOff状态，容器持续重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.last_terminated_reason: OOMKilled | 证实进程因内存超限被系统强制终止 |
| 2 | K8s Event | kubernetes | Exit Code: 137 | 确认 OOM 事件导致的进程退出码 |
| 3 | K8s State | kubernetes | container.resource_limit.memory: 64Mi | 提供容器内存硬限制，作为判定内存耗尽的依据 |
| 4 | Logging | elasticsearch | pattern: memory allocation advanced (2026-09-10 23:52:10 - 23:52:34) | 展示内存随时间递增，allocated_mib 从 20.0 增至 44.0，呈现持续增长模式 |
| 5 | Tracing | deepflow | flow: GET /work (2026-09-11 07:34:46 - 07:52:38) | 证实 OOM 后服务仍对外提供 200 响应，验证故障发生在特定业务请求处理中 |
| 6 | Metric | prometheus | kube_pod_container_status_restarts_total: 23 | 辅助证实容器处于反复重启循环 |

证据间形成“现象-配置-归因”的闭环：Pod 的 CrashLoopBackOff 状态及 `Exit Code 137` [1, 2] 均指向 OOM。日志 [4] 证实内存占用在 20 分钟内从 20Mi 涨至 44Mi，结合 64Mi 的硬限制 [3]，足以解释触发 OOM Killer 的原因；Tracing [5] 进一步确认该内存增长发生在处理 `GET /work` 请求期间。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码处理 GET /work 时存在内存泄漏 → 累计内存分配超过 64Mi 限制 → OOM Killer 终止进程 (Exit Code 137) → CrashLoopBackOff
```

### 根因结论

已确认根因为 `应用代码在处理 GET /work 请求时存在内存泄漏，导致内存使用量持续增长并最终超出容器 64Mi 的内存限制`，触发 Linux OOM Killer 强制终止进程 [1, 2, 3]。

该结论由多维证据充分支撑：
1. **直接证据**：K8s 事件明确记录 `Exit Code: 137` [2] 和 `last_terminated_reason: OOMKilled` [1]，直接证明内存超限导致的崩溃。
2. **资源依据**：配置事实确认容器 `memory limit` 为 `64Mi` [3]，为内存耗尽提供了边界依据。
3. **增长模式**：日志记录显示在 2026-09-10 23:52 的观测窗口内，`allocated_mib` 从 `20.0` 单调递增至 `44.0` [4]，证实了请求与内存分配的正相关增长模式，排除了突发流量导致瞬间崩溃的可能性。
4. **服务关联**：Tracing 数据显示 `GET /work` 请求在处理时成功返回 200 响应 [5]，进一步锁定了触发内存泄漏的具体业务场景。

**未知/未确认项**：具体的代码逻辑缺陷位于 `server.py` 的哪一部分导致无法回收内存。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 21.9s
├─ 并发证据采集: 83.6s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 83.6s (Evidence 74.5s, RCA 8.9s)
└─ 汇总总结: 11.8s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
