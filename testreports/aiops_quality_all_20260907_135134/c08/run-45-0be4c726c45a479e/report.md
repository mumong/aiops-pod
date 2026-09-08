## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | Pod aiops-case-08/workload-5c9c7b6489-wmjhr 处于 CrashLoopBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Exit Code: 137 | 证实进程被系统 OOM Killer 终止 |
| 2 | K8s Event | kubernetes | `container.last_terminated_reason`: OOMKilled | 直接原因：容器内存超出限制 |
| 3 | K8s Config | kubernetes | `container.resource_limit.memory`: 64Mi | 提供导致 OOM 的硬性资源边界 |
| 4 | K8s State | kubernetes | `container.waiting_reason`: CrashLoopBackOff | 证实由于频繁崩溃触发了重启退避机制 |
| 5 | Logging | elasticsearch | `numeric_fields.allocated_mib`: 10 → 46 | 证实应用在日志记录期间内存持续攀升（增长 36Mi） |
| 6 | Tracing | deepflow | `l7_flow`: HTTP GET /work | 证实崩溃是由该业务接口请求引起的负载增长导致 |
| 7 | Metrics | prometheus | `restart_count`: 25 | 量化证实应用处于频繁重启状态 |

**证据印证：**
K8s 的 `OOMKilled` 事实与 Exit Code 137 一致，证明内存越界是终止原因。Logging 中 `allocated_mib` 在 40 秒窗口内从 10Mi 涨至 46Mi，且该日志与 Tracing 中的 `GET /work` 请求关联，说明正常业务逻辑下的单次请求即会导致内存急剧增加，从而触发 64Mi 的限制并崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
容器配置 64Mi 硬内存限制 (fact-340703871164) → 业务请求触发内存分配 (logging-5, tracing-6) → 内存消耗突破 64Mi 限制触发 OOMKilled (kubernetes-1, kubernetes-2) → K8s 重启策略触发 BackOff 进入 CrashLoopBackOff (kubernetes-4, metrics-7)
```

### 根因结论

已确认的根因是容器 `app` 的内存使用量超过了 Kubernetes 配置的 `64Mi` 硬限制，导致内核 OOM Killer 强制终止容器进程。

证据支持如下：
1.  **触发机制**：Kubernetes 状态显示终止原因为 `OOMKilled` 且退出码为 `137`（事实 #1, #2）。
2.  **资源瓶颈**：容器的硬内存限制为 `64Mi`（事实 #3）。
3.  **现象复现**：日志显示应用在处理请求时内存从 10Mi 快速上升至 46Mi（事实 #5），结合 Tracing 数据（事实 #6），表明业务请求引发了不可控的内存增长。由于 46Mi + 基础开销极可能超过 64Mi，直接导致每次请求处理时崩溃，进而引发频繁重启（事实 #7）。

**未确认项**：
*   未提供具体的内存配置 YAML，仅通过运行时状态推断 limit 为 64Mi。
*   未确定内存泄漏是代码逻辑缺陷还是正常负载下资源配置不足。

---

## 📊 性能统计

```text
├─ 总耗时: 2.7m
├─ 问题定位: 19.9s
├─ 并发证据采集: 131.8s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 131.8s (Evidence 121.4s, RCA 10.1s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
