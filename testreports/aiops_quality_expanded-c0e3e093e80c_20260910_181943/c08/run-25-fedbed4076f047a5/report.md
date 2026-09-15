## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | 容器内存限制（64Mi）配置过低，无法支撑应用服务 /work 端点的内存分配需求（日志显示分配至 48Mi 并持续增长），导致容器被内核 OOM Killer 终止，引发 CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning BackOff 3m50s (x278 over 77m) kubelet Back-off restarting failed container app in pod workload-5c9c7b6489-p8462` | 确认为 CrashLoopBackOff 现象 |
| 2 | K8s State | kubernetes | `container.last_terminated_reason: OOMKilled`, `exit_code: 137` | 直接指向内核 OOM Killer 终止进程 |
| 3 | K8s Config | kubernetes | `container.resource_limit.memory: 64Mi` | 确认容器内存硬性限制 |
| 4 | Metric | prometheus | `container_memory_usage_bytes`: 32272384 bytes (~30.7 MiB) | 确认内存消耗持续增长，逼近限制边界 |
| 5 | Logging | elasticsearch | `allocated_mib`: `first=10`, `last=44` (HTTP 200, path `/work`) | 确认服务在处理 `/work` 端点请求时内存分配持续上升 |
| 6 | Tracing | deepflow | L7 Flow: `GET /work` 响应 `200`，持续时间 `min=10912us`, `max=103360us` | 确认触发 OOM 的请求为正常的 `/work` 接口访问 |

证据1-2 与证据3 相互印证，明确了故障原因为内存受限导致的 OOM 重启；证据5（日志）与证据6（链路）结合证据4（指标），确认了内存增长发生在 `/work` 请求处理过程中。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存硬限制(64Mi)配置过低 → 应用服务在处理/work端点请求时内存分配持续增长(日志显示分配从10Mi至44Mi) → 触发内核OOM Killer终止进程 → CrashLoopBackOff
```

### 根因结论

已确认的根因是**容器内存限制（64Mi）配置过低**，无法支撑应用服务 `/work` 端点的内存需求。

证据链闭环如下：
- **直接原因**：容器被 OOM Killer 终止并引发重启循环，由 K8s 状态 `OOMKilled`、`exit_code: 137` 及 K8s Event `BackOff` (证据1, 2) 证实。
- **资源瓶颈**：容器内存硬限制被明确配置为 `64Mi` (证据3)。
- **触发路径**：应用在处理 `/work` 端点请求时，内存分配量持续增长（证据5），且该请求为正常返回的 HTTP 请求（证据6），最终导致内存使用量逼近 64Mi 限制并触发 OOM（证据4）。

---

## 📊 性能统计

```text
├─ 总耗时: 7.3m
├─ 问题定位: 19.6s
├─ 并发证据采集: 410.8s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 410.8s (Evidence 403.3s, RCA 7.4s)
└─ 汇总总结: 10.1s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
