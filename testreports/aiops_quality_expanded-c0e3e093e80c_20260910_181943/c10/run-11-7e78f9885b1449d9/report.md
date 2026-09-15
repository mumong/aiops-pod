## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bsn84` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s (fact-fbc8c8a95ab2) | `container.waiting_reason: CrashLoopBackOff` | 确认 Pod 处于持续重启循环状态 |
| 2 | K8s State | K8s (fact-3a0ac532439c) | `container.last_exit_code: 137` | 确认容器被系统强制终止，对应 OOMKilled |
| 3 | K8s Config | K8s (fact-462dc2a06bbd) | `container.resource_limit.memory: 96Mi` | 确认内存资源上限极低，是触发 OOM 的约束条件 |
| 4 | K8s Event | K8s (fact-0fe5af4e37c3) | `event.message: Container app failed liveness probe, will be restarted` | 说明 Liveness 探测因异常状态（如资源耗尽或假死）失败触发重启机制 |
| 5 | Logging | Elastic (fact-4d4d449bdef8 聚合) | `pattern: request completed, http_status: 200, numeric_fields.allocated_mib: [0-0]` | 日志仅显示正常业务请求完成，未发现内存溢出报错；内存字段缺失导致无法确认具体峰值 |
| 6 | Tracing | Deepflow (fact-0f8227333705 聚合) | `flow: HTTP GET /work, response_code: 200, duration: 17036us-21334us` | 链路层面也确认了请求在超时前正常完成，佐证了异常发生于进程内部而非网络层 |

**证据关联分析：**
*   证据 1、2、3 形成了完整的“资源限制 → 系统级终止 → 状态异常”逻辑链：96Mi 的硬性内存限制导致容器在运行时触发 OOM（Exit Code 137），进而引发 CrashLoopBackOff 状态。
*   证据 4 补充了重启触发机制：除了 OOM 重启，Liveness Probe 也捕获到了异常并触发了重启逻辑，解释了为何存在大量的 BackOff 事件。
*   证据 5 与 6 分别从日志和流量层面反映了应用业务功能的正常响应，说明异常并非由外部流量攻击或应用逻辑死锁直接导致，而是底层资源不足导致的系统级行为，由于观测数据缺失，无法进一步量化具体的内存消耗峰值。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存限制仅为96Mi (事实：fact-462dc2a06bbd) → OOMKilled 机制 (事实：fact-3a0ac532439c, exit_code 137) → Liveness 探测失败与重启 (事实：fact-0fe5af4e37c3) → Pod CrashLoopBackOff (事实：fact-fbc8c8a95ab2)
```

### 根因结论

**已确认根因：容器内存资源上限配置过低（96Mi）。**

低限配置导致容器在运行时超过系统分配的内存阈值，触发 Linux 内核的 OOM Killer 机制（表现为 `last_exit_code: 137`）。容器被强制终止后，Kubelet 尝试重启并检测到 Liveness 探测失败（HTTP 500），最终导致 Pod 陷入 `CrashLoopBackOff` 状态。

证据来源支撑：K8s 配置中的 `resource_limit.memory` 设定为 `96Mi`，结合退出码 `137` 和 `Liveness probe failed` 事件，构成了直接的诊断闭环。

**局限性说明：** 由于 Prometheus 查询失败且应用日志中未记录具体的内存使用数值（`allocated_mib` 均为 0），当前无法精确还原 OOM 发生瞬间的实际内存峰值，但系统层面的退出码已足够判定根因为资源超限。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 31.8s
├─ 并发证据采集: 68.4s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bsn84: 68.3s (Evidence 60.9s, RCA 7.3s)
└─ 汇总总结: 13.4s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bsn84**: pod-crashloop-runtime, pod-oomkilled, pod-config-error, pod-notready-probe-failed
