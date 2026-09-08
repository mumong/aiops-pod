## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | Pod aiops-case-06/workload-7679bcf76-jwr8b 处于 CrashLoopBackOff (History) 且存在间歇性应用内部崩溃 (HTTP 500 Exit 2)，当前处于短暂重启存活状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-06/workload-7679bcf76-jwr8b` 状态: `Running`; 容器 `app` 状态: `CrashLoopBackOff` | 确认 Pod 核心症状：进程频繁崩溃且被 Kubelet 强制重启 |
| 2 | K8s State | kubernetes | 容器 `app` 终止原因: `Error`，退出码: `Exit 2`，重启计数: 21 次 | 证实进程异常终止且处于不稳定状态 |
| 3 | Logging | elasticsearch | 日志模式: `runtime process exiting` (Error, HTTP 500)，出现 4 次 (13:28 - 13:49)，应用层分配的内存 (`allocated_mib`) 稳定为 0 | 证明应用进程在执行 `/work` 时发生内部运行时错误并直接退出 |
| 4 | Tracing | deepflow | L7 Flow: 6 次 `GET /work` 请求返回 `500`，持续时间极短 (4.3k - 5.2k us) | 证实外部请求确实触发了导致进程崩溃的内部错误 |
| 5 | K8s State | kubernetes | 容器内存资源限制 (Limit): `96Mi`，请求 (Request): `24Mi` | 作为上下文证据，排除显式的 OOMKill (通常 Exit Code 137)，支持运行时逻辑崩溃 |

**证据印证说明：**
*   **现象闭环：** 外部请求 (Tracing) 触发 `/work` 导致 HTTP 500 (Logging)，随后应用进程报 "runtime process exiting" 并抛出 Exit Code 2 (K8s State)，Kubelet 据此记录 `Error` 原因并进入 `BackOff` 重启循环 (K8s State)。
*   **非资源耗尽：** 日志明确显示内存分配为 0，且 Exit Code 2 结合日志 "runtime process exiting" 表明是应用内部代码异常，而非资源限额导致的 OOMKill。

## 🎯 根因分析 · g1

### 因果链

```text
应用内部未捕获的运行时异常 (Runtime Error) → 服务进程崩溃并返回 HTTP 500 (Exit Code 2) → Kubelet 检测到异常退出并触发重启 (CrashLoopBackOff) → Pod 处于 CrashLoopBackOff 状态
```

### 根因结论

**已确认的根因：**
应用进程 (`python3 /opt/aiops/server.py`) 在处理 `GET /work` 请求时发生未捕获的运行时错误 (Runtime Error)，导致进程异常退出 (Exit Code 2)。

**证据支撑：**
*   **直接现象：** K8s 记录终止原因为 `Error`，退出码 `Exit 2` (证据 #2)。
*   **故障机制：** 应用日志明确记录 "runtime process exiting" 并伴随 HTTP 500 响应 (证据 #3)；Tracing 确认了导致该错误的请求流量 (证据 #4)。
*   **非资源因素：** 日志中的内存分配指标为 0，排除了 OOMKill，确认是代码/逻辑层面的异常崩溃。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 19.0s
├─ 并发证据采集: 75.2s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 75.2s (Evidence 64.0s, RCA 11.0s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime
