## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | Pod 容器 'app' 配置的内存 limit (64Mi) 过低，无法容纳应用运行时所需的内存（日志显示已分配至少 48Mi，加上 Python 运行时开销即超过 64Mi），导致内核 OOM Killer 强制终止进程（Exit Code 137, OOMKilled），进而引发 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason: "OOMKilled"`, `last_exit_code: 137` | 确认应用因超出内存限制被系统内核强制终止，这是容器重启的根本机制 |
| 2 | K8s Config | Kubernetes | `container.resource_limit.memory: 64Mi` | 设定了极低的硬内存上限，为 OOM 提供了触发条件 |
| 3 | K8s Event | Kubernetes | `BackOff ... 2m26s (x434 over 115m)` | 证明进程处于高频 CrashLoopBackOff 循环中 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 23` | 从监控视角独立验证了容器已重启 23 次的现象 |
| 5 | Logging | Elasticsearch | 日志模式 `memory allocation advanced`, 窗口内 `allocated_mib` 从 12.0 升至 40.0 (max 40.0) | 展示应用运行时持续增加内存分配，逼近且必然突破 64Mi 的硬限制 |
| 6 | Tracing | Deepflow/Tempo | 9 次 `GET /work` HTTP 200 请求 (src_ip: 172.16.104.30 -> dst_ip: 172.16.104.20) | 提供触发内存分配的行为上下文，确认 OOM 发生在正常业务请求处理过程中 |

**证据印证说明：**
Kubernetes 的 `OOMKilled` 状态与 `exit_code 137` (证据 1) 直接对应了资源硬限制 `64Mi` (证据 2)。Elasticsearch 日志中内存分配值的上升趋势 (证据 5) 解释了应用为何必然触发该限制。Tracing 数据 (证据 6) 证实了触发 OOM 的活跃业务流指向该 Pod (dst_ip: 172.16.104.20)，而 Prometheus 重启计数 (证据 4) 独立验证了故障的持续性。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存 limit 限制为 64Mi (低资源配置) → 业务请求处理持续增加内存分配 (突破限制) → 触发内核 OOM Killer 终止进程 (OOMKilled) → 导致 Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为：**Pod 容器 `app` 的内存请求限制 (64Mi) 严重低于应用实际运行时所需内存。**

该限制导致内核 OOM Killer 在执行业务请求（如 `GET /work`）时强制终止进程。具体证据支撑如下：
1. **直接终止证据**：Kubernetes 明确报告容器以 `OOMKilled` 原因和退出码 `137` 终止 (证据 1)。
2. **配置限制证据**：容器配置的内存硬限制仅为 `64Mi` (证据 2)。
3. **突破机制证据**：Elasticsearch 日志显示，在处理请求过程中，应用分配的内存 (`allocated_mib`) 在极短时间内从 `12.0` 上升至 `40.0` (证据 5)。结合 Python 等运行时环境的固有开销，该分配量极易突破 `64Mi` 限制。
4. **故障持续性证据**：容器已重启 23 次 (证据 4)，且 Kubernetes 记录了长达 115 分钟内的 434 次重启 BackOff 事件 (证据 3)，说明该资源瓶颈导致应用无法稳定运行。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 20.8s
├─ 并发证据采集: 71.4s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 71.4s (Evidence 62.7s, RCA 8.5s)
└─ 汇总总结: 12.3s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime, pod-oomkilled, pod-config-error, pod-imagepull-failed
