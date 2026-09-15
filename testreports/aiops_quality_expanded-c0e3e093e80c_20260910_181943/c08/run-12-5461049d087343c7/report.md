## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | 应用进程在处理请求时发生内存泄漏或分配失控，导致实际内存使用量超出Pod设定的64Mi硬限制，触发Linux内核OOM Killer强制终止进程，进而引发Kubernetes控制面的CrashLoopBackOff重启循环。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | 异常原因：`OOMKilled`，退出码：`137` | 确诊进程因内存超限被内核杀死 |
| 2 | K8s State | kubernetes | Pod `workload-5c9c7b6489-p8462` 状态为 `CrashLoopBackOff`，已重启 `11` 次 | 确认进程频繁崩溃并重启循环 |
| 3 | K8s Config | kubernetes | `memory` 限制（limit）：`64Mi` | 提供判定内存超标的基准阈值 |
| 4 | Logging | elasticsearch | 模式 `[memory allocation advanced]` (8次)，`allocated_mib` 从 `10` 增长至 `42` | 证明单链路内存在持续快速消耗 |
| 5 | Tracing | deepflow+tempo | L7 Flow `GET /work` 响应 `200`，`aiops.observed_mode=oom_growth` | 确认服务逻辑在正常运行时即触发内存激增 |

日志记录了请求处理期间的内存分配轨迹（`fact-50f9fc6c31bb`~`fact-342d7173f3c1`），显示从 10 MiB 激增至 42 MiB。结合 `OOMKilled` 状态码 `137` 和 `64Mi` 的内存限制，确证内存增长最终突破了容器硬限制。追踪数据中 `oom_growth` 标记与日志的增长趋势相互印证，排除了外部流量异常或网络延迟导致的问题。

## 🎯 根因分析 · g1

### 因果链

```text
业务逻辑导致内存持续快速增长 → 超出容器 64Mi 硬限制 → Linux 内核触发 OOM Killer 终止进程 → Pod 频繁重启进入 CrashLoopBackOff
```

### 根因结论

**已确认根因：应用代码存在内存泄漏或分配失控。**
具体机制为应用在处理 `GET /work` 请求时，内部内存分配量在单次链路（或极短时间窗口）内迅速增长（日志中观察到的 10 MiB 至 42 MiB 趋势），突破了 Pod 配置的 `64Mi` 内存上限，导致内核强制终止进程（退出码 `137`，异常原因 `OOMKilled`）。Kubernetes 控制面检测到容器非正常退出后，触发了崩溃重启循环，最终表现为 `CrashLoopBackOff`。

**未确认项：**
*   具体的内存泄漏代码位置及调用栈（缺少进程崩溃瞬间的详细日志）。
*   高并发请求是否加剧了该现象。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 30.1s
├─ 并发证据采集: 75.2s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 75.2s (Evidence 64.4s, RCA 10.6s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
