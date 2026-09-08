## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | 容器内存限制（64Mi）过低导致应用启动/运行期间触发OOMKilled，引发容器反复崩溃及CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason: OOMKilled` (app container) | 证实容器因内存溢出被内核杀掉 |
| 2 | K8s Event | Kubernetes | `BackOff` 警告：重启失败容器 app (x178 over 48m) | 证实应用处于反复重启循环状态 |
| 3 | K8s Config | Kubernetes | `resource_limit.memory: 64Mi` (app container) | 确认极低的内存硬限制是触发 OOM 的直接配置约束 |
| 4 | K8s Config | Kubernetes | `resource_request.memory: 24Mi` (app container) | 仅表示调度保留量，非内存上限 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1` (reason=CrashLoopBackOff), `kube_pod_container_status_last_terminated_reason=1` (reason=OOMKilled) | 独立确认了崩溃与 OOM 的当前状态 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total=12` (container=app) | 证实应用已发生多次崩溃重启 |
| 7 | Logging | Elasticsearch | 日志模式: `memory allocation advanced` (path=/work); `allocated_mib` 从 14MB 增长至 48MB (first 14.0 -> last 48.0) | 提供业务应用实际内存消耗逼近限制的证据 |
| 8 | Tracing | Deepflow/Tempo | Span `GET /work` 标记 `aiops.observed_mode: oom_growth` | 在 L7 调用链路层面观察到明显的内存持续增长模式 |

**证据印证说明：**
Kubernetes 的 `OOMKilled` 退出状态与 `CrashLoopBackOff` 循环直接证实了容器因资源限制被杀死的物理现象；Prometheus Metrics 独立记录了同样的终止原因与重启计数。日志与链路追踪数据从应用内部视角补充了关键细节：应用在处理 `/work` 请求时内存从 14MB 持续增长至 48MB，该过程被标记为“oom_growth”，充分证明 64Mi 的内存上限不足以支撑其业务运行，导致频繁溢出崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存硬限制过低(64Mi) → 应用处理请求时内存持续增长(观测到 14MB→48MB) → 触发内核 OOM Killer (OOMKilled) → 容器退出码 137 并重启 → 用户可见 CrashLoopBackOff 循环
```

### 根因结论

已确认根因为**工作负载内存限制配置过低**。证据链显示，应用容器 `app` 被分配了仅为 `64Mi` 的内存上限，而其在正常请求路径下即可产生数十兆字节的内存增长（日志 `allocated_mib` 增至 48MB，追踪标记 `oom_growth`），直接导致内核因内存不足执行 `OOMKilled` 操作，进而引发 Kubernetes 控制器将其放入 `CrashLoopBackOff` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 12.6s
├─ 并发证据采集: 58.4s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 58.4s (Evidence 52.6s, RCA 5.7s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
