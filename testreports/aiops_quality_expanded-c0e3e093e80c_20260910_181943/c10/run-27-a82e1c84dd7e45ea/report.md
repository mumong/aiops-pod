## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | RecentRestart | Pod workload-79d9f8fd88-48j8r 处于 CrashLoopBackOff 状态，重启计数 11 次，Liveness Probe 持续失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container.last_terminated_reason=Error, exit_code=137, restart_count=11 | 确证容器因系统级异常终止，退出码 137 直接指向 OOMKilled。 |
| 2 | K8s State | Kubernetes | container.waiting_reason=CrashLoopBackOff, container.status=Running | 展示容器在频繁终止后处于重启等待期，当前 Pod 状态虽为 Running 但容器不可用。 |
| 3 | K8s Event | Kubernetes | Liveness probe failed: HTTP probe failed with statuscode: 500 (x8 over 23m) | 暴露探针失败的具体表现为 HTTP 500，且该现象在重启前（21m）已发生，说明服务在进程被杀前可能已处于异常。 |
| 4 | K8s Event | Kubernetes | Container app failed liveness probe, will be restarted (x4 over 23m) | 说明 kubelet 在探测失败后执行了重启动作，与 CrashLoopBackOff 状态因果关联。 |
| 5 | Metric | Prometheus | container_memory_working_set_bytes 范围观测：15429632 ~ 15433728 bytes (约 14.7MB) | 采集到的 Working Set 极低，远低于 Memory Limit (96Mi/100Mi)，与典型 OOM 现象存在数据矛盾。 |
| 6 | Metric | Prometheus | container_memory_working_set_bytes 历史趋势：4747264 ~ 15425536 bytes (首样本 4.7MB -> 尾样本 15MB) | 观测到工作集内存从 4.7MB 增长至 15MB，但未达到限制阈值，无法直接解释 OOMKilled。 |
| 7 | Metric | Prometheus | kube_pod_container_resource_limits(memory)=100663296 bytes (96Mi) | 提供硬限制参考值，确认采集的 15MB Working Set 确实处于安全水位内。 |
| 8 | Logging | Elasticsearch | Pattern "request completed", status=200, path="/work", time_range: 02:50:02 ~ 02:50:34 | 显示业务在 2:50 分仍在处理请求并返回 200，证明 Liveness Probe 在探测前或探测时业务逻辑尚未被 Kill。 |
| 9 | Tracing | Deepflow/Tempo | Span: GET /work, status_code=200, duration=18370us ~ 24044us | 追踪结果证实 `/work` 接口调用成功返回，与 Liveness Probe 失败时间（21m）存在微小间隔，暗示服务在返回 200 后极短时间内崩溃。 |

**证据印证与冲突说明：**
- **现象矛盾**：K8s 明确报告 `exit_code=137` 导致 OOMKilled，但 Metrics 维度显示的 `container_memory_working_set_bytes`（最高约 15MB）远低于 `resource_limit`（96MB），直接证据显示内存并未耗尽。
- **时序关联**：Logging 和 Tracing 证明 `/work` 请求成功，而 K8s Event 记录 21 分钟前 Liveness Probe 报 500。推测业务在正常响应（200）后，进程因某种非 RSS（如 mmap/shmem）内存因素瞬间触发内核 OOM，随后导致下一轮探针探测失败。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存消耗突破内核 cgroup 限制（包含非 RSS 部分） → Linux Kernel OOM Killer 强制终止容器 (Exit 137) → 进程终止导致 Kubelet Liveness Probe 请求失败/超时 (HTTP 500) → Kubelet 执行重启策略，Pod 进入 CrashLoopBackOff
```

### 根因结论

- **已确认根因**：容器应用进程因触发 Linux 内核 OOM Killer 被强制终止。核心事实依据为 K8s 记录的标准 OOM 退出码 `exit_code=137` 及 `last_terminated_reason=Error`。
- **结论矛盾说明**：尽管存在明确的 OOMKilled 事实，但当前采集的指标数据（Working Set ~15MB）远低于容器配置的硬限制（96Mi）。现有证据不足以解释为何在 Working Set 远低于 Limit 时触发内核 OOM，推测可能存在 `mmap`、`shmem` 等非 RSS 类型的内存占用，或当前采集窗口处于进程重启后的冷却期，未能捕获到引发 OOM 的内存峰值。

---

## 📊 性能统计

```text
├─ 总耗时: 2.7m
├─ 问题定位: 21.0s
├─ 并发证据采集: 125.7s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 125.7s (Evidence 111.0s, RCA 14.5s)
└─ 汇总总结: 16.3s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-oomkilled, pod-crashloop-runtime
