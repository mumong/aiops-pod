## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | OOMKilled | 容器内存限制配置过低（64Mi），无法承载应用持续增长的内存需求。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason: OOMKilled` | 证明应用进程因内存超限被内核 Kill (Signal 9) |
| 2 | K8s Config | Kubernetes | `container.resource_limit.memory: 64Mi` | 明确当前容器的内存硬限制阈值 |
| 3 | K8s Config | Kubernetes | `container.resource_request.memory: 24Mi` | 确认请求量仅为限制量的 37.5%，存在较大弹性空间但被限制死 |
| 4 | K8s Event | Kubernetes | `Back-off restarting failed container app (x181 over 53m)` | 显示容器进入 CrashLoopBackOff 循环，证明故障是持续性而非偶发 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason: "OOMKilled" (sample_count: 1)` | 确认最近一次终止原因确认为 OOMKilled |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 13` | 量化验证应用因 OOM 频繁重启的现象 |
| 7 | Logging | Elasticsearch | `pattern: "memory allocation advanced"` | 观察窗口内（16:22:32 - 16:23:08）`allocated_mib` 从 `10` 增长至 `46` |
| 8 | Tracing | Deepflow | `L7 Flow GET /work (9 occurrences, 200 OK)` | 确认导致内存分配增长的业务请求是 GET /work 接口 |

**证据分析**：
- **现象印证**：`fact-5` 和 `fact-1` 分别从监控和容器状态确认了 `OOMKilled` 的终止原因；`fact-4` 的频繁重启事件（181次）与 `fact-6` 的 13 次重启计数共同证实了该问题导致的业务循环中断。
- **因果逻辑**：`fact-3` 和 `fact-2` 确立了 64Mi 的硬限制；结合 `fact-7` 显示应用在处理单次业务时内存占用迅速从 10Mi 攀升至 46Mi（接近限制的 72%），说明应用存在持续的内存增长模式，极易触及 64Mi 上限。
- **业务关联**：`fact-8` 提供了触发该内存增长的特定业务请求入口（GET /work），说明该内存行为是特定业务场景下的直接结果。

## 🎯 根因分析 · g1

### 因果链

```text
内存限制配置为64Mi → 业务请求(GET /work)触发内存持续分配(10Mi→46Mi) → 触发OOMKilled机制(Exit 137) → 容器崩溃并频繁重启(CrashLoopBackOff)
```

### 根因结论

已确认根因为**容器内存限制配置过低（64Mi），无法承载应用在处理 GET /work 业务时的内存增长需求**。

证据表明：
1.  `fact-1` 和 `fact-5` 证实了容器因 `OOMKilled` 被强制终止。
2.  `fact-2` 显示硬限制仅为 `64Mi`，而 `fact-7` 日志显示在处理业务时内存分配量在短时间内从 10Mi 增长至 46Mi，表明应用对内存有持续且显著的增长需求。
3.  在 `46Mi` 的基础内存消耗上，若系统负载增加或请求并发上升，极易触及 64Mi 上限，导致 OOM。
4.  `fact-4` 中的 `x181` 次重启表明该问题在 53 分钟内持续发生，并非偶发。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 18.4s
├─ 并发证据采集: 82.5s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 82.5s (Evidence 76.2s, RCA 6.2s)
└─ 汇总总结: 12.8s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-oomkilled
