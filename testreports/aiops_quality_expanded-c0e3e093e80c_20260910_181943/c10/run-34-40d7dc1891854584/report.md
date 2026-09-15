## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | CrashLoopBackOff | Pod workload-79d9f8fd88-48j8r 处于 CrashLoopBackOff，退出码 137，Liveness Probe 返回 500。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `container.last_exit_code` | `137` (容器 app) | 进程被内核强制终止 (SIGKILL)，通常对应 OOMKilled |
| 2 | K8s Config | `container.resource_limit.memory` | `96Mi` (容器 app) | 极低的硬性内存上限，构成 OOM 风险边界 |
| 3 | K8s Event | `Killing` / `Unhealthy` | 事件：`Container app failed liveness probe...`；`Liveness probe failed: HTTP probe failed with statuscode: 500` | 证明 Pod 因探针失败被 Kubelet 杀除或判定不健康 |
| 4 | K8s State | `container.waiting_reason` | `CrashLoopBackOff` | 证实 Pod 处于反复崩溃重启状态 |
| 5 | Metric | `kube_pod_container_status_restarts_total` | `15` (容器 app) | 量化重启频次，验证 CrashLoop 现象的持续性 |
| 6 | Logging | `log.message` (http_request) | `allocated_mib`: first 0, last 0, min 0, max 0 | 应用日志中显示无内存分配增长，提示异常可能在容器侧被内核拦截而非应用层 |

**证据综合说明**
1-2 号证据结合表明：Pod 在极低的 96Mi 内存限制下运行，并遭遇了导致进程退出码为 137 的终止事件，强指向 OOM。3-4 号证据确认了 Kubelet 视角的现象（探针失败及 CrashLoop）。6 号证据中日志记录的 `allocated_mib` 持续为 0，说明在崩溃前的最后一次成功请求周期内，应用进程层面未检测到内存增长，这支持了 OOM 是由应用启动开销或未被日志层追踪的内存峰值触发，而非日志可见的业务请求积累。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了严格的 memory limit (96Mi) → 应用运行期间内存占用超过 limit 触发 OOMKilled (Exit 137) → 进程被终止导致 Liveness Probe 失败 (HTTP 500) → Kubelet 重启容器但再次崩溃，形成 CrashLoopBackOff
```

### 根因结论

**已确认的根因：Container memory limit (96Mi) 不足导致 OOMKilled。**

当前 Pod `workload-79d9f8fd88-48j8r` 的容器 `app` 配置了 `96Mi` 的硬性内存限制。K8s 状态显示最后一次终止原因为 `Exit Code: 137` (SIGKILL，通常由 OOM Killer 触发)，且 Pod 状态为 `CrashLoopBackOff`，Liveness Probe 返回 `500`。这些事实共同印证了进程因内存超限被操作系统强制终止。

**证据不足与限定：**
虽然 `Exit 137` 和 `96Mi` 限制构成了强证据，但输入中 `container_memory_usage_bytes` 的 `trend_evaluable=false`（单样本，无趋势），且 `allocated_mib` 在日志中无增长，因此无法直接展示“突破 96Mi 阈值”的峰值数据，也无法区分具体的内存消耗发生在“启动阶段”还是“运行阶段”。当前结论基于退出码与限制值的强相关性推断。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 18.7s
├─ 并发证据采集: 73.5s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 73.5s (Evidence 60.2s, RCA 13.2s)
└─ 汇总总结: 11.8s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-crashloop-runtime
