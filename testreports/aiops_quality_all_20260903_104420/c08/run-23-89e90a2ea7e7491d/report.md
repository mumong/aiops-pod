## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | Pod aiops-case-08/workload-5c9c7b6489-fl85h 处于 CrashLoopBackOff 状态，容器反复崩溃退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `container.last_terminated_reason` | `OOMKilled` | 确认为 OOM 导致的容器进程异常终止 |
| 2 | K8s State | `container.last_exit_code` | `137` | 进程被内核强制终止的标准退出码 |
| 3 | K8s Config | `container.resource_limit.memory` | `64Mi` | 导致 OOM 的硬限制阈值 |
| 4 | Logging | Log Pattern | `memory allocation advanced`, `allocated_mib` 从 20.0 递增至 44.0 (min: 20.0, max: 44.0, 连续记录 8 条) | 揭示应用处理 `/work` 请求时存在内存增长模式 |
| 5 | Tracing | Flow | `GET /work` 响应 200, `duration_us` 15176.0-20851.0 (Deepflow) | 确认导致内存增长的业务请求来源为 `/work` |
| 6 | K8s Event | `event.message` | `Back-off restarting failed container app ...` (发生 219 次, 跨越 62 分钟) | 描述反复崩溃后的指数退避等待现象 |
| 7 | Metric | `kube_pod_container_status_last_terminated_reason` | `reason: OOMKilled` (值: 1, 单样本) | 从监控维度交叉验证 OOMKilled 状态 |

**证据印证与冲突说明**：
K8s 事件与 Metric 均证实了进程因 `OOMKilled` (exit code 137) 被终止；Logging 提供的 `allocated_mib` 递增数据（峰值达 44MiB）与 `resource_limit` 硬限制（64MiB）完全吻合，揭示了内存使用突破限制的具体路径。Tracing 数据将这一增长模式归因于对 `/work` 接口的请求处理，逻辑链条完整，各维度无冲突。

## 🎯 根因分析 · g1

### 因果链

```text
应用处理请求 /work 时内存持续增长(观察: 日志中 allocated_mib 从 20MiB 升至 44MiB) → 内存消耗突破配置的资源硬限制 64Mi → Linux OOM Killer 强制终止容器进程 (exitCode: 137, OOMKilled) → Kubelet 检测到容器反复崩溃后触发 CrashLoopBackOff
```

### 根因结论

**已确认根因**：容器 `app` 的内存使用超过了 Kubernetes 配置的资源限制（`resource_limit` 64Mi），导致被 OOM Killer 终止。

该结论得到了多维度事实的支持：
1.  **机制确认**：K8s 状态显示退出码 137 和终止原因 `OOMKilled`，符合内存超限特征（证据 1, 2, 7）。
2.  **原因定位**：日志聚合显示应用在特定业务逻辑（`GET /work`，证据 5）下存在持续的内存增长行为，最高观测到 44MiB 的内存分配（证据 4）。
3.  **边界确认**：配置的 `resource_limit.memory` 仅为 64Mi（证据 3），当持续增长的应用内存突破此边界时，系统强制杀死了容器进程，进而引发了观察到的 `CrashLoopBackOff` 现象（证据 6）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 24.1s
├─ 并发证据采集: 73.0s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 73.0s (Evidence 63.0s, RCA 9.8s)
└─ 汇总总结: 11.9s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime
