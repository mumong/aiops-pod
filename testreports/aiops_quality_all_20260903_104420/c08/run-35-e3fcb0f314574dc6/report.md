## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | CrashLoopBackOff due to repeated OOMKilled |
| g2 | `monitor/prometheus-observability-prometheus-0` | Unknown | {'message': 'Reason:    OOMKilled'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Exit Code: 137 (OOMKilled) | 确认容器因内存耗尽被系统强制终止，触发重启 |
| 2 | K8s Config | Kubernetes | Container memory_limit: 64Mi | 明确系统施加的内存硬限制边界 |
| 3 | K8s Event | Kubernetes | Restart count: 20, CrashLoopBackOff | 证实终止机制引发的连续重启循环与异常状态 |
| 4 | Metric | Prometheus | kube_pod_container_status_last_terminated_reason: 1 (OOMKilled) | 独立验证容器最后一次终止的原因为内存溢出 |
| 5 | Logging | Elasticsearch | Log pattern "memory allocation advanced": `allocated_mib` 变化 [10 → 48] | 显示应用单次分配高达 48Mi，逼近 64Mi 限制导致剩余空间不足 |
| 6 | Tracing | DeepFlow/Tempo | Flow `GET /work` (9次), `aiops.observed_mode: oom_growth` | 确认内存增长是由 /work 业务请求驱动，并伴随内存使用持续增长特征 |

**证据分析说明：**
1. **触发机制闭环**：Tracing 观测到的 `/work` 请求与 Logging 中的内存分配日志高度吻合（同属 `aiops-lab-workload` 服务模式），确认业务流量是内存增长的动力源。
2. **失效临界点**：日志显示的 `allocated_mib` 峰值达到 48Mi，该数值与 K8s 配置的 `memory_limit: 64Mi` 极其接近。在应用基础内存消耗下，该分配行为导致容器内存使用超过 64Mi 阈值，直接触发 OOMKilled (Fact #1)。
3. **独立验证**：Metrics 中的终止原因独立验证了 K8s State 的 OOMKilled 状态，排除了应用层自身 Crash 导致退出的可能性。

## 🎯 根因分析 · g1

### 因果链
```text
业务请求 /work 驱动 (Tracing) → 内存分配峰值 48Mi (Logging) → 突破 64Mi 容器硬限制 (K8s Config) → 触发 OOMKilled 机制 (K8s State/Metric) → 20次重启形成 CrashLoopBackOff (K8s Event)
```

### 根因结论
已确认根因为：**容器内存配置硬限制 (64Mi) 低于应用运行时单次请求分配的内存峰值 (48Mi) 及基础开销，导致内存溢出。**
应用在处理业务请求时（`/work`），内存需求急剧上升，单次分配最高达 48Mi（Fact #5），这已占用了内存限制的绝大部分。在超出该值的轻微开销下，容器突破 64Mi 的硬限制，触发操作系统 OOM Killer 机制 (Fact #1, #4)，导致容器进程被杀并不断重启 (Fact #3)。

**证据引用**：
- 硬限制与分配冲突：Fact #2 (64Mi Limit) vs Fact #5 (48Mi Allocation)。
- 机制与现象确证：Fact #1 (Exit Code 137), Fact #3 (CrashLoopBackOff), Fact #4 (OOMKilled Metric)。
- 触发链路：Fact #6 (Tracing Mode & Flow) 关联 Fact #5 (Log Pattern)。

---

## 🕵️ 证据内容 · g2

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `container.last_terminated_reason` | `reason="OOMKilled"` | 证实 Prometheus 容器曾因内存耗尽被系统终止（ExitCode 137） |
| 2 | K8s State | `container.last_exit_code` | `exit_code=137` | 与 OOMKilled 状态一致，进一步确认进程被 OOM Killer 强制终止 |
| 3 | K8s Event | `event.message` | `Liveness probe failed: Get "http://172.16.166.165:9090/-/healthy": context deadline exceeded` (x141 over 15d) | 证实存在长期且持续的探针超时现象，反映 Pod 处于 Unhealthy 状态 |
| 4 | K8s Config | `container.resource_limit.memory` | `value="512Mi"` | 提供导致潜在 OOM 的硬限制背景；容器当前仅请求 256Mi |
| 5 | Logging | `log.message` (elasticsearch) | `err="found duplicate series for the match group {instance=\"10.2.0.48:10250\"} on the right hand-side... many-to-many matching not allowed"` (时间范围: 17:06:15 - 17:07:57) | 证实 Prometheus 规则引擎存在严重的标签冲突错误，导致 `kubelet_pleg_relist_duration_seconds` 等规则持续评估失败 |
| 6 | Metric | `kube_pod_container_status_last_terminated_reason` | `value=1` (labels: `reason="OOMKilled"`) | 从 metrics 维度独立印证了容器曾发生过 OOM 事件，与 K8s State 事实一致 |
| 7 | Tracing | L7 Flow (Deepflow) | `GET /federate... duration_us: min=20693246.0 (20.6s), max=34005576.0 (34s)` | 证实 `/federate` 接口存在极端响应延迟（最高超过 30 秒），属于严重的性能拥塞迹象 |
| 8 | K8s State | `container.restart_count` | `restart_count=2` (prometheus), `restart_count=0` (config-reloader) | 证实容器发生过重启，但 Sidecar 稳定，进一步将问题聚焦于主容器本身 |

**证据关系说明**：
- **K8s State (事实 1, 2, 3)** 与 **Metric (事实 6)** 从不同维度印证了容器经历过 OOMKilled 并伴随长期的探针超时。
- **Logging (事实 5)** 提供了独立的诊断视角，证实了规则引擎存在导致 CPU/处理阻塞的严重标签冲突，解释了可能引发超时的另一重逻辑原因。
- **Tracing (事实 7)** 通过实际的网络交互数据，证实了 `/federate` 等关键接口存在极端延迟（20s-34s），直接构成了探针超时的现象基础。

## 🎯 根因分析 · g2

### 因果链
```text
容器内存限制过低(512Mi) 或 规则标签冲突引发高 CPU 阻塞/延迟 → 容器进程资源耗尽或响应极度缓慢 → Liveness 探针请求超时 (context deadline exceeded) → Pod 状态标记为 Unknown / Unhealthy (Restart count: 2)
```

### 根因结论

现有证据**不足以**发布单一确定的根因，主要因为存在两个相互竞争且均能独立导致探针失败的解释：

1. **资源瓶颈（OOM 主导）**：
   - **证据支持**：事实 1、2、6 明确显示容器曾发生 `OOMKilled`，且存在硬内存限制 `512Mi`（事实 4）。探针失败可能是历史上 OOM 遗留的未决状态，或者是当前内存再次触及边界导致进程假死。
2. **配置/逻辑缺陷（标签冲突主导）**：
   - **证据支持**：事实 5 证实 Prometheus 存在严重的标签重复冲突（`many-to-many matching not allowed`），事实 7 证实 `/federate` 等接口耗时高达数十秒。严重的规则评估失败和延迟可能单独导致 Prometheus 响应超时，而无需发生实际的 OOM。

**缺失的决定性事实**：
目前缺少 Prometheus 运行期间的**实时资源使用率指标**（如当前的内存使用量是否接近 512Mi，或 CPU throttling 比率）。如果没有这一指标，无法区分当前的 `Unknown` 和探针超时是由**内存耗尽引发的进程崩溃/重启**造成的，还是由**规则引擎标签冲突引发的 CPU/逻辑阻塞**造成的。

---

## 📊 性能统计

```text
├─ 总耗时: 13.5m
├─ 问题定位: 19.0s
├─ 并发证据采集: 771.3s
│  ├─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 85.0s (Evidence 73.6s, RCA 10.9s)
│  └─ g2 monitor/prometheus-observability-prometheus-0: 771.3s (Evidence 755.7s, RCA 15.4s)
└─ 汇总总结: 19.5s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime
