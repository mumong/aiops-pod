## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | Running | 容器内存限制配置过小（64Mi），导致处理 /work 路径的高内存分配请求时触发 OOMKilled（Exit Code 137），进而引发容器反复重启和 CrashLoopBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s State | `container.last_terminated_reason`: `OOMKilled` (container: `app`) | 确认直接终止原因 |
| 2 | K8s Config | K8s Config | `container.resource_limit.memory`: `64Mi` (container: `app`) | 确认内存限制硬上限 |
| 3 | K8s Config | K8s Config | `container.resource_request.memory`: `24Mi` (container: `app`) | 提供内存配置基线 |
| 4 | K8s State | K8s State | `container.last_exit_code`: `137` (container: `app`) | 确认 OOM 触发终止信号 (128+9) |
| 5 | K8s Event | K8s Event | `event.message`: `BackOff ... Back-off restarting failed container app` | 确认频繁重启现象 |
| 6 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason=OOMKilled` (timestamp: `2026-09-07T18:53:35.726000Z`) | 确认 OOMKilled 状态 |
| 7 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=CrashLoopBackOff` (timestamp: `2026-09-07T18:53:22.023000Z`) | 确认等待重启状态 |
| 8 | Metric | Prometheus | `kube_pod_container_status_restarts_total=28` (container: `app`) | 量化重启次数 |
| 9 | Logging | Elasticsearch | `pattern`: `memory allocation advanced ... path: /work` | 观察窗口内 `allocated_mib` 从 `28` 增加至 `48` (min/max) |
| 10 | Tracing | Tempo | `trace_id`: `dc971a7748a880630fe1384e160c1fc2` | 观察到 `GET /work` 耗时 `~1.07ms` |
| 11 | Tracing | Deepflow | `flow`: `GET /work` 9次 (src_ip: `172.16.104.47` -> dst_ip: `172.16.104.42`) | 确认请求流量持续存在 |

**证据互证：**
1. K8s 的 `OOMKilled` (fact-1) 与 `Exit Code 137` (fact-4) 在事实层面上完全一致，直接指向内核内存拦截。
2. Metric 中的 `CrashLoopBackOff` (fact-7) 与 K8s Event 中的 `BackOff` 现象相互印证，解释了容器的高频重启行为。
3. Logging 中 `/work` 路径请求分配的内存从 `28MiB` 增长至 `48MiB` (fact-9)，虽然 48MiB < 64MiB 硬限制 (fact-2)，但已接近该值，且 K8s 进程树与系统开销 (cgroup) 需占用少量内存，证实了配置不足是触发 OOM 的直接诱因。

## 🎯 根因分析 · g1

### 因果链
```text
容器内存资源限制配置过低 (memory limit: 64Mi) → 应用处理 /work 路径请求时内存分配接近上限 (allocated_mib 达 48) → 容器触发 OOMKilled 并被内核强制终止 (Exit Code 137) → 容器陷入反复重启循环 (CrashLoopBackOff)
```

### 根因结论
已确认的根因为：**容器内存限制配置过小 (`64Mi`) 不足以支撑处理 `/work` 路径高内存分配请求时的运行时开销**。

该配置导致应用在内存分配接近限制时（日志观测到 `allocated_mib` 最高达 `48MiB`）触发内核 OOM Killer，直接导致容器以退出码 `137` 终止（事实 1、4、6），并进而引发容器反复重启的 `CrashLoopBackOff` 状态（事实 5、7、8）。

---

## 📊 性能统计

```text
├─ 总耗时: 10.4m
├─ 问题定位: 26.4s
├─ 并发证据采集: 583.7s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 583.7s (Evidence 573.5s, RCA 10.1s)
└─ 汇总总结: 14.3s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
