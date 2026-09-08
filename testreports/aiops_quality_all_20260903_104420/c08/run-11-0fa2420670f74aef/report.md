## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | Running | Pod aiops-case-08/workload-5c9c7b6489-fl85h 处于 CrashLoopBackOff 状态，容器 app 反复 OOMKilled（重启 9 次），Ready=False。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.last_terminated_reason: OOMKilled (fact-47d4a0c7c5af) | 确认容器因内存超限被强制终止 |
| 2 | K8s State | kubernetes | container.waiting_reason: CrashLoopBackOff (fact-5c35120d468e) | 确认容器已处于反复重启的异常状态 |
| 3 | K8s Event | kubernetes | Exit Code: 137 (fact-39e3ac1d4cbd) | 进程被内核 OOM Killer 杀死的系统证据 |
| 4 | K8s Config | kubernetes | container.resource_limit.memory: 64Mi (fact-3453961be88e) | 提供导致 OOM 的硬性资源边界 |
| 5 | K8s Config | kubernetes | container.resource_request.memory: 24Mi (fact-15f4db1f881f) | 确认应用声明的请求资源远低于限制 |
| 6 | Metric | prometheus | container_memory_working_set_bytes: max=66248704.0, last=241664.0 (fact-809b7053ba70) | 显示内存峰值约 63.1Mi，触顶后回落 |
| 7 | Logging | elasticsearch | pattern: http_request /work, allocated_mib first=16, last=46 (fact-07b8092d4d39) | 显示处理 /work 请求时内存从 16Mi 持续增长至 46Mi |
| 8 | Tracing | tempo | span: GET /work, observed_mode: oom_growth (fact-723e4b871497) | 关联具体的请求行为与内存增长现象 |

**证据印证说明：**
Kubernetes 状态（#1, #3）与 Metrics（#6）交叉验证了应用内存使用确实达到了 ~63Mi 的硬限制，从而触发了 OOMKilled 和 CrashLoopBackOff。日志（#7）揭示了内存增长的触发场景，即处理 `/work` 路径的 HTTP 请求，此时内存从 16Mi 增长至 46Mi。Trace（#8）进一步在应用层确认了该请求与 OOM 增长的直接关联。资源配置（#4）明确了 64Mi 的内存上限，足以解释为何 46Mi 的内存分配在后续处理中触发了 OOM。

## 🎯 根因分析 · g1

### 因果链

```text
触发器：应用处理 /work 路径的 HTTP 请求 (事实 7, 8)
   ↓
机制：请求处理过程中内存线性增长 (事实 7: allocated_mib 16->46)
   ↓
触发条件：内存使用触及 container.resource_limit 设置的 64Mi 硬上限 (事实 4, 6)
   ↓
直接故障：内核 OOM Killer 终止进程，返回 exitCode 137 (事实 1, 3)
   ↓
用户可见现象：容器反复崩溃，状态变为 CrashLoopBackOff (事实 2, 5)
```

### 根因结论

已确认的根因是容器内存限制（64Mi）设置过低，无法容纳应用处理 `/work` 请求时的峰值内存需求。应用在处理该请求时，内存分配量持续增长（日志显示从 16Mi 增至 46Mi），最终触发了 64Mi 的 `resource_limit`，导致被 OOMKilled（事实 4, 6, 7）。这一机制直接导致了容器以 137 退出码反复终止（事实 1, 3），进而引发了 CrashLoopBackOff 现象（事实 2）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 19.3s
├─ 并发证据采集: 101.1s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 101.1s (Evidence 90.8s, RCA 10.1s)
└─ 汇总总结: 13.4s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-oomkilled, pod-crashloop-runtime
