## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | 应用服务存在内存泄漏，请求接口 `/work` 时每次分配约 2 MiB 内存且未释放，导致容器内存使用量持续增长。最终内存使用量突破硬限制（`64Mi`，由 `kubectl_describe` 确定），触发 Linux OOM Killer 终止进程（`exitCode=137`，`reason=OOMKilled`）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `reason=OOMKilled`, `exitCode=137` | 证明容器因 OOM Killer 终止，是故障的直接成因 |
| 2 | K8s Config | kubernetes | `container.resource_limit.memory` = `64Mi` | 确立容器内存使用的硬性上限，是触发 OOM 的条件 |
| 3 | Metric | prometheus | `kube_pod_container_status_restarts_total` = `14` | 佐证容器经历多次非正常重启，处于不稳定的振荡状态 |
| 4 | Logging | elasticsearch | 观察窗口内（`22:58:24` ~ `22:58:51`）`path="/work"` 日志中 `allocated_mib` 从 `18` 增长至 `44` | 提供日志维度的内存持续增长证据，印证泄漏模式 |
| 5 | Tracing | deepflow+tempo | `GET /work` 关联标签 `aiops.observed_mode=oom_growth` | 提供分布式追踪维度的独立观测，直接指向内存增长异常模式 |

**证据印证说明：**
- **维度交叉确认**：K8s State (E1) 确认了故障的最终物理状态（OOMKilled），而 Metric (E3) 展示了该状态导致的系统级后果（CrashLoopBackOff 重启）。
- **增长机理佐证**：Logging (E4) 和 Tracing (E5) 独立捕获了内存随 `/work` 接口调用持续上升的模式，且 Tracing (E5) 直接标记了 `oom_growth` 模式，强力支持日志中观察到的内存增长现象，排除了随机性波动。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码内存泄漏 → 容器内存突破硬性限制 64Mi → Kubernetes OOM Killer 终止进程 (exitCode=137) → CrashLoopBackOff
```

### 根因结论

已确认的根因是**应用代码存在内存泄漏**。

这一结论由以下事实链支撑：
1. **触发机制**：容器配置的硬性内存上限为 `64Mi`（证据 E2）。
2. **直接失效**：Kubernetes 状态表明容器被 OOM Killer 终止且退出码为 `137`（证据 E1），这证实了内存超限引发的系统级杀进程行为。
3. **持续振荡**：容器重启次数达到 `14` 次（证据 E3），说明泄漏过程不可逆且重复触发上述失效机制。
4. **内存增长归因**：Logging (E4) 和 Tracing (E5) 分别在应用日志和链路追踪中，独立观测到针对 `/work` 接口的内存（`allocated_mib`）持续增长及 OOM 增长模式标签。

虽然确切泄漏的代码行或函数栈需要代码级 Debug（unknowns 已说明），但现有事实已足以确定故障是由应用侧代码导致的内存持续泄漏，进而突破资源限制触发 OOM Kill。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 34.2s
├─ 并发证据采集: 58.9s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 58.9s (Evidence 48.5s, RCA 10.2s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
