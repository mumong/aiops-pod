## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | Pod workload-7679bcf76-w9s9c 处于 CrashLoopBackOff 状态，每 4 分钟左右重启一次 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason: Error` (fact-0597b137ad97) | 确认容器进程异常终止的事实。 |
| 2 | K8s State | kubernetes | `container.last_exit_code: 2` (fact-72d9e0077e22) | 提供进程退出码，指向应用内部错误而非系统 OOMKilled。 |
| 3 | K8s Event | kubernetes | `Warning BackOff ... Back-off restarting failed container app` (fact-4d02cf17c90e) | 证实 kubelet 的指数退避机制生效，表现为 CrashLoopBackOff。 |
| 4 | Logging | elasticsearch | `runtime process exiting, http_status: 500` (fact-6063d42ebb93等) | 提供应用层报错日志，直接关联崩溃场景。 |
| 5 | Logging | elasticsearch | `allocated_mib: 0` (min/max/first/last均为 0) (fact-6063d42ebb93等) | 排除内存耗尽(OOM)因素，佐证为应用逻辑或运行时异常。 |
| 6 | Tracing | deepflow | `HTTP GET /work, response_code: 500` (fact-23b0ab486279等) | 外部观测到请求最终被 500 状态码终止，与日志一致。 |

- **证据 1-3 (K8s State/Event)** 建立了基础现象：容器反复异常退出并触发重启退避，导致 Pod 处于 CrashLoopBackOff 状态。
- **证据 4-5 (Logging)** 揭示了崩溃的具体性质：应用在处理请求时内部报错 (`http_status: 500`) 并退出，且内存分配指标为 0，排除了资源限制导致的 OOM。
- **证据 6 (Tracing)** 从网络层印证了日志中的 500 错误。
- **冲突说明**：Kubernetes 未报告 OOMKilled，而日志明确显示进程自行退出并报错 500，两者结合排除了资源超限作为根因的可能性，指向应用内部逻辑错误。

## 🎯 根因分析 · g1

### 因果链

```text
容器 app 内部运行时进程异常退出 (exit_code=2) → kubelet 触发指数退避重启策略 (Back-off) → Pod 进入 CrashLoopBackOff 状态 → 用户可见应用间歇性不可用
```

### 根因结论

**已确认的根因**：应用进程在运行时发生内部异常退出（导致 `exit_code=2`），并返回 `500` 状态码。
- **分析**：
  - **直接原因**：容器进程异常终止。证据显示日志中存在 `runtime process exiting` 伴随 `http_status: 500` (见证据 4)，且 `allocated_mib` 持续为 0 (见证据 5)，表明并非资源耗尽（如 OOM），而是应用自身的逻辑异常或运行时错误。
  - **现象成因**：由于容器进程反复异常退出，kubelet 执行了退避重启策略 (Back-off)，导致 Pod 状态变为 `CrashLoopBackOff` (见证据 1-3)。
- **未知细节**：具体的应用内部错误类型（为何退出码为 2，以及 500 错误的详细堆栈）未提供，需查看应用层完整日志或核心转储。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 57.7s
├─ 并发证据采集: 68.3s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 68.3s (Evidence 59.3s, RCA 8.8s)
└─ 汇总总结: 12.1s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
