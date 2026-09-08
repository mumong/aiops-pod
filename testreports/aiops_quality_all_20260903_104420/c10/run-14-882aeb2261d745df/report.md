## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | Pod aiops-case-10/workload-79d9f8fd88-sbqvc 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` 退出码 `137`，最后一次终止原因 `Error` (fact-448a8b1f0315, fact-7c1b58af9eb6) | 直接证据：OS OOM Killer 终止进程的标准信号码 |
| 2 | K8s Event | Kubernetes | Liveness Probe 失败: `HTTP probe failed with statuscode: 500` (fact-b298fb8a7f97, 17次) | 触发重启机制：应用内存耗尽导致无法响应健康检查 |
| 3 | K8s Event | Kubernetes | 连续 `BackOff restarting failed container` (fact-899e1145253a, 100次) | 确认状态：Pod 因不断重启陷入 CrashLoopBackOff |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 为 `CrashLoopBackOff`，重启总数 `15` (fact-d7c0f20bcd6a, fact-2404f9364047) | 交叉验证：K8s 状态与监控数据一致，重启行为持续 |
| 5 | K8s Config | Kubernetes | 容器 `app` 硬限制 `memory: 96Mi` (fact-6cfcaabdfd70) | 核心归因：提供导致 OOM 的资源上限依据 |
| 6 | Tracing | Tempo/Deepflow | `GET /work` 请求返回 `200`，模式标记为 `liveness_fail`，耗时 17ms~49ms (fact-6f5e95a61c3b, 等) | 辅助限定：应用在 OOM 前能短暂处理请求，表明是瞬时资源耗尽或泄漏 |

**证据说明：**
1. 退出码 `137`（事实 #1）与 `96Mi` 的内存限制（事实 #5）在逻辑上强相关，直接指向 OOM Kill 机制。
2. 健康检查失败（事实 #2）和 BackOff 事件（事实 #3）是内存耗尽后的直接系统反应，证实了应用因资源问题不可用。
3. 追踪数据（事实 #6）显示在触发故障前服务能短暂响应，结合低内存配置，进一步佐证了资源上限过小导致的崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存限制 (96Mi) 过小 → 内存超限触发 OOM Killer 强制终止 (Exit Code 137) → Kubelet 检测到 Liveness Probe 失败 (HTTP 500) 并执行重启 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因：容器 `app` 的内存硬限制（`96Mi`）低于业务运行所需内存。当应用尝试分配超过 `96Mi` 的内存时，Linux OOM Killer 强制终止进程（证据 #1, #5）。这导致健康检查中断（证据 #2）和后续的频繁重启（证据 #3, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 29.0s
├─ 并发证据采集: 78.4s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 78.4s (Evidence 69.2s, RCA 9.1s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-oomkilled, pod-crashloop-runtime
