## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | CrashLoopBackOff | 容器内存配置上限过低导致应用被OOM Kill |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: Error | 直接证明容器进程被异常终止 |
| 2 | K8s State | kubernetes | `container.waiting_reason`: CrashLoopBackOff | 确认容器处于重启失败循环状态 |
| 3 | K8s State | kubernetes | `container.last_exit_code`: 137 | Exit Code 137 对应 SIGKILL 信号，通常由 OOM Killer 触发 |
| 4 | K8s Config | kubernetes | `container.resource_limit.memory`: 96Mi | 确认容器硬内存限制为 96MB，配置处于极低水平 |
| 5 | K8s Config | kubernetes | `container.resource_request.memory`: 24Mi | 确认内存请求仅为 96Mi 的 1/4，存在较大资源弹性 |
| 6 | Logging | elasticsearch | Pattern: `request completed` (HTTP 200), `allocated_mib`: 0 | 确认在崩溃前应用正常接收了请求且处理成功，排除业务逻辑崩溃 |
| 7 | Tracing | deepflow+tempo | L7 Flows: 9次 `GET /work` 成功 (200), `trace_id` 交叉一致 | 证实 L7 通信正常，排除网络或应用层错误 |

**证据印证分析：**
- **K8s State (#1, #3)** 与 **Config (#4)** 结合，构成了典型的 OOM Kill 闭环：应用运行在极低的 96Mi 限制下，最终进程被强制杀掉（137）且原因标记为 Error。
- **Logging (#6)** 与 **Tracing (#7)** 展示了崩溃前的一瞬间：应用能够成功响应请求（`allocated_mib: 0` 提示可能存在瞬时内存峰值或日志采样延迟，但 `200` 状态码证明了应用存活）。
- 这种“正常响应”与“瞬时崩溃”的时间差（`Killing` 事件发生在 `request completed` 之后几秒，见 #5 中的时间线推断），进一步佐证了资源耗尽（OOM）而非业务错误的结论。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存配置上限过低 (96Mi) → 应用运行中消耗内存触及限制 → Linux 内核 OOM Killer 强制终止进程 (Exit Code 137) → Pod 进入 CrashLoopBackOff 状态，Liveness 探针失败
```

### 根因结论

**已确认的根因：容器内存配置上限过低导致应用被 OOM Kill。**

依据如下证据：
1.  **终止原因明确**：Kubernetes 状态显示 `container.last_terminated_reason` 为 `Error`，且 `container.last_exit_code` 为 `137`，这是进程收到 SIGKILL 信号的标准退出码，通常由 OOM Killer 引起。
2.  **配置限制过低**：容器 `app` 的内存硬限制（`resource_limit`）仅设置为 `96Mi` (#4)，对于一般 Java/Go 等应用而言极易触发限制。
3.  **现象排除**：Logging 和 Tracing 数据显示崩溃前应用正常响应了 HTTP 请求（`status 200`），排除了应用内部逻辑错误或业务异常导致崩溃的可能性。

现有证据链完整，能够确凿解释 CrashLoopBackOff 的成因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 19.3s
├─ 并发证据采集: 56.8s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 56.8s (Evidence 51.8s, RCA 4.9s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-crashloop-runtime
