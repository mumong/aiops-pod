## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | Running | Pod workload-5c9c7b6489-p8462 处于 CrashLoopBackOff 状态，重启 21 次，Ready 为 False |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff 107s (x378 over 100m) kubelet Back-off restarting failed container app in pod workload-5c9c7b6489-p8462` | 确认 Pod 处于高频崩溃重启（CrashLoopBackOff）的直接状态，证明崩溃事件持续发生。 |
| 2 | K8s State | Kubernetes | 退出码: `137`; 终止原因: `OOMKilled` | 明确指示容器因内存不足被强制终止。 |
| 3 | K8s Config | Kubernetes | 容器内存限制 (`resource_limit.memory`): `64Mi`; 容器内存请求 (`resource_request.memory`): `24Mi` | 确立系统对内存使用的硬性约束阈值（64Mi），为分析 OOM 触发提供基准。 |
| 4 | Metric | Prometheus | 历史内存工作集 (`container_memory_working_set_bytes`): 多次重启周期内峰值分别为 `49111040`(约46.8Mi), `53325824`(约50.8Mi), `59645952`(约56.9Mi), `57540608`(约54.9Mi) | 显示该 Pod 在过去多次重启中，内存峰值持续逼近 64Mi 限制，呈现随使用逼近限制的上升趋势。 |
| 5 | Logging | Elasticsearch | 日志模式 `http_request` 中数值字段 `allocated_mib`: 观察窗口内最小 `20.0`，最大 `48.0` (趋势：first `30` → last `46`) | 证实应用在运行期间向 `/work` 端点提交了大量且逐步增长的内存分配测试。 |
| 6 | Tracing | Tempo/Deepflow | Flow 聚合 `GET /work`: 7 次请求全部返回 `HTTP 200`，耗时区间 `10243`-`103360` us | 确认测试流量已成功进入应用并被处理，排除网络拦截或应用拒绝服务的因素。 |

**证据综合分析：**
Kubernetes 的 `OOMKilled` 事件与退出码 `137` [2] 是现象的直接记录；Metric 历史峰值数据 [4] 显示每次重启前内存使用量均逼近 64Mi 的硬限制 [3]；Logging [5] 和 Tracing [6] 提供了根本原因的物理依据——即应用主动通过 `/work` 接口逐步分配了最高达 48Mi 的内存，叠加应用基础运行开销后突破了 64Mi 的容器限制，最终导致 Pod 陷入 CrashLoopBackOff [1]。

## 🎯 根因分析 · g1

### 因果链

```text
应用业务逻辑测试行为（向 /work 分配最高 48Mi 内存） → 实际内存使用突破容器硬限制 64Mi → 容器触发 OOMKilled (Exit Code 137) → Pod 进入 CrashLoopBackOff 状态 (21次重启)
```

### 根因结论

已确认的根因是：**Pod `aiops-case-08/workload-5c9c7b6489-p8462` 的容器内存限制（64Mi）过小，无法承载应用当前包含的内存测试流量，导致 OOMKilled。**

具体而言，应用在处理 `GET /work` 请求时（[证据 5, 6]），会逐步分配内存，最高单次测试分配达到 48Mi。这些请求在测试期间均返回成功（[证据 6]），但累积的基础内存与请求分配内存之和逼近并突破了 Kubernetes 设定的 64Mi 硬限制。这种持续的内存越界行为导致容器内核通过 OOM Killer 强制终止进程（退出码 137，[证据 2]），进而引发 kubelet 的高频重启（[证据 1]），Metric 历史峰值数据（[证据 4]）也印证了每次重启前内存均耗尽限制的事实。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 21.5s
├─ 并发证据采集: 91.0s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 91.0s (Evidence 80.6s, RCA 10.2s)
└─ 汇总总结: 14.2s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
