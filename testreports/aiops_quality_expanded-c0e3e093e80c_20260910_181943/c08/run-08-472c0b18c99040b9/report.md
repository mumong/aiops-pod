## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | Pod aiops-case-08/workload-5c9c7b6489-p8462 处于 CrashLoopBackOff 状态，应用容器（app）反复被 OOMKilled 终止。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` | `container.last_terminated_reason`: `OOMKilled`; `container.last_exit_code`: `137` | 确认进程因内存超限被内核强杀（事实 ID: `fact-04bf12b98451`, `fact-cc24a306607a`） |
| 2 | K8s State | `kubernetes` | `container.resource_limit.memory`: `64Mi` (request: `24Mi`) | 确立触发 OOM 的硬约束边界（事实 ID: `fact-20e648261261`） |
| 3 | Logging | `elasticsearch` | Pattern `memory allocation advanced` 连续出现 8 次，内存分配量 (`allocated_mib`) 从 `16` 累积增至 `48` | 证明应用持续分配内存并逼近 64Mi 限制（事实 ID: `fact-2e4643b41536` 等） |
| 4 | K8s Event | `kubernetes` | `Warning BackOff ... x122 over 36m`; `Exit Code: 137` | 证实系统进入重启循环（事实 ID: `fact-e49c5c370fd9` 等） |
| 5 | Metric | `prometheus` | `kube_pod_container_status_last_terminated_reason` 值为 `1`，标签为 `reason: OOMKilled` | 指标层面印证容器因 OOM 终止（事实 ID: `fact-300a96ee7d43`） |
| 6 | Tracing | `deepflow` | L7 Flow 统计 9 次 `GET /work` 请求，状态码 `200` | 确认触发内存增长的具体业务路径（事实 ID: `fact-0a2d2b227244` 等） |

**证据链说明：**
K8s 事件与指标（#1, #2, #5）直接确认了“内存硬限制触发 OOM 强杀”这一系统级机制。日志（#3）与追踪（#6）结合提供了业务侧视角，显示 `GET /work` 请求会导致内存分配量（`allocated_mib`）从 16 升至 48，这一增长趋势在 64Mi 的硬限制下直接导致了上述系统事件。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存硬限制配置过低（64Mi） → 应用处理 GET /work 请求时内存持续累积（从16Mi增至48Mi） → 超出限制触发内核 OOM Killer（退出码 137） → Pod 处于 CrashLoopBackOff 状态
```

### 根因结论

**已确认根因：应用容器内存需求超过配置的硬限制。**

具体而言，Pod `workload-5c9c7b6489-p8462` 配置了 `64Mi` 的内存硬限制（`fact-20e648261261`）。日志数据显示，在正常处理请求（`fact-0a2d2b227244`）的过程中，应用内存分配量持续攀升（`allocated_mib`: `16` → `48`，见 `fact-2e4643b41536` 等），这种增长模式表明该应用在运行过程中无法维持低于 `64Mi` 的内存驻留量。

当内存占用触及硬限制时，内核触发 OOM Killer 强制终止进程（`fact-04bf12b98451`），导致容器退出并进入 CrashLoopBackOff（`fact-e49c5c370fd9`）。这一过程由 Prometheus 的终止原因指标（`fact-300a96ee7d43`）完整印证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 16.9s
├─ 并发证据采集: 63.0s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 63.0s (Evidence 53.4s, RCA 9.5s)
└─ 汇总总结: 13.5s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
