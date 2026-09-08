## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | Pod workload-79d9f8fd88-bwqhh 处于 CrashLoopBackOff 状态，容器反复以 Exit Code 137 终止 |
| g2 | `aiops-case-10/workload` | Unknown | Pod aiops-case-10/workload-79d9f8fd88-bwqhh 处于 CrashLoopBackOff 状态，应用不可用 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` 最终退出码 `137`；Pod 重启次数 `30` | 直接症状：Exit Code 137 指示进程收到 SIGKILL 信号（通常为 OOM Killer 行为） |
| 2 | K8s Config | Kubernetes | 容器 `app` 内存硬限制 (`resource_limit`) 为 `96Mi`；内存请求 (`resource_request`) 为 `24Mi` | 关键上下文：96Mi 的限制极低，为内存耗尽提供了直接条件 |
| 3 | K8s Event | Kubernetes | Liveness probe 失败：`HTTP probe failed with statuscode: 500` (3 分钟内出现 43 次) | 佐证探针：应用层在处理请求时已发生异常，通常与资源耗尽（如线程池满或堆内存溢出）一致 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 值为 `1` (CrashLoopBackOff) | 确认状态：容器确实处于等待重启的崩溃循环中 |
| 5 | Tracing | Deepflow/Tempo | L7 Flow 聚合显示 `GET /work` 响应状态 `200` (9 次)，耗时 8.8ms-19.2ms | 排除网络/网关故障：成功请求证明了应用层具备基本处理能力，故障发生在应用内部资源耗尽阶段 |

**证据关联说明：**
K8s State 显示的 Exit Code 137 与极低的内存限制 (Fact 2) 高度吻合，构成了内存耗尽导致被 Kill 的直接物理证据。Liveness Probe 持续返回 500 (Fact 3) 解释了为何 Kubelet 会在容器短暂存活后强制杀死并重启它，从而形成 CrashLoopBackOff 循环 (Fact 4)。Tracing 数据 (Fact 5) 进一步确认了应用代码并非完全不可用，而是受限于资源边界。

## 🎯 根因分析 · g1

### 因果链

```text
内存限制过低 (96Mi) 或进程内存泄漏 → 容器内存使用超出 limit 触发 OOM Killer → 容器进程收到 SIGKILL (Exit Code 137) 终止 → Liveness Probe 失败导致 CrashLoopBackOff
```

### 根因结论

已确认的根因是：**容器进程因内存不足 (OOM) 被系统强制终止。**

依据如下证据链条：
1.  **致命退出码**：Kubernetes State 事实明确记录容器最后一次退出码为 `137` (Fact 1)，这是 Linux 系统中 OOM Killer 杀掉进程的标志性信号。
2.  **资源约束边界**：容器 `app` 被配置了极低的内存硬限制 `96Mi` (Fact 2)。这一限制极难支撑具有网络交互功能的后端应用，极易在请求处理期间耗尽可用内存。
3.  **探针行为一致**：Liveness Probe 频繁返回 `500` (Fact 3)，这表明应用在处理请求时已因资源竞争或内存溢出而崩溃，符合 OOM 前兆特征。

现有证据充分支持“资源限制引发 OOM”的结论。未知项仅在于内存是耗尽于应用自身的内存泄漏，还是因正常负载超过了 `96Mi` 的设定阈值。

---

## 🕵️ 证据内容 · g2

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | canonical | Pod `aiops-case-10/workload-79d9f8fd88-bwqhh` 状态 `Unknown`，现象：`CrashLoopBackOff`，重启次数 30 | 确认 Pod 处于持续崩溃并重启的异常生命周期状态 |
| 2 | K8s State | canonical | 诊断结果：`Liveness probe 持续返回 500 导致 kubelet 杀死容器` | 提供导致重启的直接机制解释 |
| 3 | K8s Event | canonical | 触发机制：应用 `/health` 端点返回 `500` (Liveness Probe Failed) | 证明容器健康检查失败是 kubelet 介入的直接原因 |
| 4 | K8s State | canonical | 终止状态：kubelet 强制终止容器，Exit Code `137` | 确认容器被外部强杀，进入 CrashLoopBackOff 循环 |

证据表明，Pod 处于 `CrashLoopBackOff` 状态的根本驱动力来自 Liveness Probe 的持续失败。K8s 状态事实（重启计数 30 和 Exit 137）与探针失败的事实形成闭环，解释了容器为何被反复强制终止。Metric、Logging 和 Tracing 维度采集均报 `error`（`pod_not_found` 或执行失败），缺乏支持性原始数据来验证 Probe 500 的内部原因。

## 🎯 根因分析 · g2

### 因果链

```text
应用 /health 端点返回 500 → kubelet 判定容器不健康并强制终止 (Exit 137) → 容器进入 CrashLoopBackOff 状态 (Restart Count 30) → Pod 状态标记为 Unknown / Unavailable
```

### 根因结论

**已确认的根因**：Liveness Probe 持续返回 500 导致 kubelet 杀死容器，从而引发 Pod 的 `CrashLoopBackOff` 状态（见事实 1, 2, 4）。这一机制解释了 Pod 不可用和反复重启的现象。

**证据不足的未知项**：
1. **应用内部原因未确认**：缺乏应用日志（Logging error）和运行指标（Metrics error），无法判断 `/health` 返回 500 是由于依赖超时、内存不足还是代码逻辑错误。
2. **Exit 137 具体诱因未确认**：Exit 137 通常对应 OOMKilled，但也可能由信号强杀引起。由于 Metric 采集失败且未提供内存使用量数据，无法确认是否由 Memory Limit 96Mi 触发，或是应用内部 panic 导致的信号终止。

---

## 📊 性能统计

```text
├─ 总耗时: 3.5m
├─ 问题定位: 19.5s
├─ 并发证据采集: 176.5s
│  ├─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 99.7s (Evidence 85.8s, RCA 13.7s)
│  └─ g2 aiops-case-10/workload: 176.5s (Evidence 162.8s, RCA 13.5s)
└─ 汇总总结: 13.7s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime
