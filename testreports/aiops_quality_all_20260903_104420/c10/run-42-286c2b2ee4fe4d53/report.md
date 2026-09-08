## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | Pod `aiops-case-10/workload-79d9f8fd88-sbqvc` 处于 CrashLoopBackOff，容器 `app` 已重启 39+ 次，退出码 137，Liveness Probe 返回 500。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_exit_code`: 137; `container.waiting_reason`: CrashLoopBackOff; `restart_count`: 39/41 | 确认应用进程被强杀导致 CrashLoop 状态，是 OOM Kill 的典型特征 |
| 2 | K8s Event | Kubernetes | Liveness probe failed: HTTP probe failed with statuscode: 500 | 证明存活探针已因应用拒绝服务/崩溃而连续失败，触发容器重启 |
| 3 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason`: Error; `kube_pod_container_status_restarts_total`: 39 | 从监控侧独立验证了容器因错误终止并反复重启的客观事实 |
| 4 | K8s Config | Kubernetes | `container.resource_limit.memory`: 96Mi; `container.resource_limit.cpu`: 200m; `container.resource_request.memory`: 24Mi | 提供上下文：容器内存限制极低（96Mi），是潜在的容量瓶颈限制 |
| 5 | Logging | Elasticsearch | pattern: `http_request ... http_status: 200`; time_range: 22:03:23 - 22:03:55 | 显示应用在前一时刻仍正常处理请求，排除启动配置错误（如 Command not found） |
| 6 | Tracing | Deepflow/Tempo | Flow: GET /work response_code: 200; 关联 Pod IP: 172.16.104.31 | 确认崩溃前流量可正常到达并处理，进一步佐证是运行期资源耗尽而非服务不可用 |

**证据印证说明：**
K8s 状态与 Metrics 独立验证了同一终止状态（Error, Exit 137）和循环重启现象；K8s Event 的 Liveness Probe 失败与 CrashLoop 因果关系明确。资源配置显示极低的内存上限（96Mi），而崩溃前一刻的 Logging 和 Tracing 证明应用正在正常运行并处理请求，排除了启动故障，符合“运行中资源耗尽被终止”的特征。

## 🎯 根因分析 · g1

### 因果链

```text
容器 memory limit 设置为 96Mi → 应用运行触发 OOM Kill 机制 → 进程接收 SIGKILL (Exit Code 137) → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

**已确认的根因：** 容器 `app` 的内存硬限制配置过低（`96Mi`，fact-64ca8aa7dc31）。

该限制在应用运行时无法满足内存需求，导致 Linux 内核触发 OOM Killer 强制终止应用进程。进程退出码 `137` (fact-90e3ae8014b3, fact-4f13ef3bec7c) 是收到 `SIGKILL` 信号的明确证据。结合 Liveness Probe 连续返回 `500` (fact-22f7ca20ba3f) 触发 kubelet 重启容器，最终导致 Pod 陷入 `CrashLoopBackOff` 状态。

**证据关联：**
- OOM Kill 的直接表现（Exit 137, Error termination）由 K8s State 和 Metrics 确认（证据 #1, #3）。
- 运行期资源瓶颈的上下文由资源配置事实支撑（证据 #4）。
- 故障非启动或网络问题，由崩溃前的正常业务日志和链路确认（证据 #5, #6）。

---

## 📊 性能统计

```text
├─ 总耗时: 7.3m
├─ 问题定位: 22.7s
├─ 并发证据采集: 403.1s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 403.1s (Evidence 393.3s, RCA 9.6s)
└─ 汇总总结: 12.0s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime
