## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | workload-7679bcf76-w9s9c处于CrashLoopBackOff状态，容器app不断以退出码2重启 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `exit_code`: 2, `last_terminated_reason`: "Error" | 确认进程以异常退出码退出并停止运行 |
| 2 | K8s State | Kubernetes | `container.waiting_reason`: "CrashLoopBackOff", `restart_count`: 22 | 显示 Kubelet 因进程反复崩溃已进入退避重启阶段 |
| 3 | Logging | Elasticsearch | 日志模式：`http_request` 级别 `error`，消息 `"runtime process exiting"`，`http_status`: 500，`path`: "/work" | 直接指向应用在处理特定请求时发生内部错误并主动终止进程 |
| 4 | Tracing | Deepflow | L7 Flow：`GET /work` 返回 HTTP 500 (response_code: 500)，出现 4 次，持续时间 5159us - 9849us | 独立于日志的流量观测，证实 `/work` 接口持续稳定返回 500 错误 |
| 5 | K8s Config | Kubernetes | `container.resource_limit.memory`: 96Mi, `container.resource_limit.cpu`: 200m | 确认容器存在硬资源上限，但在 CrashLoopBackOff 证据下需排除资源超限直接导致（需结合日志分析） |
| 6 | Metrics | Prometheus | `kube_pod_container_status_waiting_reason` = 1 (reason: CrashLoopBackOff) | 时序确认当前 Pod 处于因容器未就绪而等待的状态 |

**证据关联说明：**
- 事实 3（日志记录 HTTP 500 与进程退出）与事实 4（流量层观测到 `/work` 接口持续返回 500）高度一致，证明应用内部逻辑或环境配置在处理 `/work` 请求时发生了确定性失败。
- 事实 1 与事实 2 结合，表明该 500 错误导致了进程非正常退出（Exit 2），进而触发了 Kubernetes 的 CrashLoopBackOff 机制。
- 事实 5 提供的资源上限虽存在，但当前错误直接表现为业务逻辑层面的 500 与进程主动退出，而非典型的 OOM 或 CPU 节流导致的 Kill。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码逻辑错误或配置异常 → 处理 /work 请求时抛出 HTTP 500 错误并触发进程退出 → 容器退出码 2 → Kubelet 触发 CrashLoopBackOff 重启
```

### 根因结论

**已确认的根因及现象：**
应用容器 `app` 在处理 HTTP `GET /work` 请求时遭遇了导致 HTTP 500 的内部错误，并触发了进程主动退出（`exit_code: 2`）。该异常行为被日志模式记录为 `"runtime process exiting"` [事实 3]，同时由 Deepflow 的 L7 流量观测独立证实 [事实 4]。Kubelet 检测到容器持续崩溃后，将其状态更新为 `CrashLoopBackOff` [事实 2]。

**证据不足的部分：**
虽然确认了错误表现为 500 与进程退出，但现有日志中未包含具体的错误堆栈信息或导致退出的精确代码异常细节 [未确认]。此外，日志中 `allocated_mib` 的数值字段全为 0.0，未能提供内存分配层面的上下文，无法排除内存配置或泄漏对此次崩溃的潜在影响 [未确认]。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 30.7s
├─ 并发证据采集: 90.7s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 90.7s (Evidence 81.5s, RCA 9.1s)
└─ 汇总总结: 12.0s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-oomkilled, pod-crashloop-runtime
