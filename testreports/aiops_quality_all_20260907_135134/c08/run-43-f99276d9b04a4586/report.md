## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | RecentRestart | Container 'app' OOMKilled due to memory exhaustion (25 restarts with Memory Limit 64Mi, trace attributes indicate 'oom_growth' on /work endpoint, logs show repeated memory allocation attempts). |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: OOMKilled (fact-2a3ecd52ca03) | 直接确认容器终止原因是内存超限 |
| 2 | K8s Event | Kubernetes | `Warning BackOff`: kubelet 因容器失败反复重启 (fact-88e5c366ac1b) | 证实 CrashLoopBackOff 现象，容器反复被重启 |
| 3 | K8s Config | Kubernetes | Memory Limit: 64Mi, CPU Limit: 200m (fact-4183a6c9f9a7, fact-d001b144e84a) | 明确容器资源硬限制，提供判断 OOM 的阈值依据 |
| 4 | K8s Config | Kubernetes | Memory Request: 24Mi, CPU Request: 20m (fact-38bf72fab275, fact-f46a4b120fa3) | 资源请求远低于限制，排除资源预留不足导致的驱逐 |
| 5 | K8s State | Kubernetes | `container.last_exit_code`: 137 (fact-97a31cdb5096) | 137 是 OOMKilled 的标准退出码，佐证内存问题 |
| 6 | K8s State | Kubernetes | `container.restart_count`: 25 (fact-e612d3f4d7e0) | 25 次重启证实故障非偶发，已形成恶性循环 |
| 7 | K8s State | Kubernetes | Pod Phase: Running, `ContainersReady`: False (fact-361433dd355a, fact-c9dd79eeb5c8) | 应用层处于崩溃循环中，未就绪 |
| 8 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason`: 1 (OOMKilled) (fact-d3408e75befb) | 指标侧再次确认终止原因为 OOM，与 K8s State 一致 |
| 9 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 25 (fact-31b8e1594033) | 重启计数一致，确认故障持续性 |
| 10 | Logging | Elasticsearch | Pattern: `memory allocation advanced`, path: `/work` (fact-192cb65db7bd et al.) | 日志显示在 `/work` 路径下反复执行内存分配操作 |
| 11 | Logging | Elasticsearch | `numeric_fields.allocated_mib`: first=10, last=42, max=42.0 (fact-192cb65db7bd et al.) | 内存分配量在观测窗口内从 10Mi 增加到 42Mi，显示持续增长模式 |
| 12 | Tracing | DeepFlow | Flow: GET /work, count=9, src_ip=172.16.104.47, dst_ip=172.16.104.42 (fact-5b789ab0cc68 et al.) | 大量针对 `/work` 接口的 L7 请求流入 Pod (172.16.104.42) |
| 13 | Tracing | Tempo | Span: `GET /work`, aiops.observed_mode=oom_growth, trace_id: 8222dc31e3941a2145dd67c1657eadc7 (fact-f416013ce214) | Trace 显式标记模式为 'oom_growth'，直接指向根因行为 |

**证据关联说明**：
- K8s 指标与状态 (证据 1, 3, 5, 6, 8, 9) 高度一致，共同确认了容器因超过 64Mi 限制而 OOMKilled 并反复重启 (25次) 的事实。
- 日志 (证据 10, 11) 与 Trace (证据 13) 共同将故障机制定位到 `/work` 端点。日志展示了内存分配量 (10Mi->42Mi) 的持续增长，Trace 显式标记了 `oom_growth` 模式。
- Trace (证据 13) 提供了诊断行为的关键线索（`oom_growth`），日志证据进一步量化了这一行为在 OOM 临界点附近的具体表现。

## 🎯 根因分析 · g1

### 因果链

```text
应用持续处理 `/work` 请求并分配内存 (证据 10, 11, 13) → 内存占用超出 64Mi Limit (证据 3) → OOMKilled (Exit 137) (证据 1, 5, 8) → CrashLoopBackOff (25 Restarts) (证据 2, 6, 9) → 容器持续崩溃，Pod 不 Ready (证据 7)
```

### 根因结论

已确认的根因是应用在处理 `GET /work` 请求时存在内存持续增长（OOM Growth）的问题，导致容器内存分配超过了配置的 64Mi 硬限制。

**证据支撑**：
1. **直接现象**：K8s 和 Metrics 均明确显示容器终止原因为 `OOMKilled` (证据 1, 8)，且重启了 25 次 (证据 6, 9)。
2. **行为机制**：Trace 分析显式观测到 `aiops.observed_mode: oom_growth` (证据 13)；日志记录显示在 `/work` 端点下，内存分配量在短时间窗口内从 10Mi 增加至 42Mi (证据 11)，表明存在累积性内存分配行为。
3. **配置约束**：容器 Memory Limit 为 64Mi (证据 3)，当前观测到的 42Mi 已接近该阈值，结合持续增长趋势，极易触发 OOMKilled。

**未确认事项**：
- 具体的代码逻辑或数据结构设计缺陷导致内存无法释放（无法仅凭现有观测数据确定代码层面的确切原因）。
- OOMKilled 发生时的精确内存压力值及详细分配堆栈。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 24.6s
├─ 并发证据采集: 62.2s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 62.2s (Evidence 54.4s, RCA 7.6s)
└─ 汇总总结: 20.6s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
