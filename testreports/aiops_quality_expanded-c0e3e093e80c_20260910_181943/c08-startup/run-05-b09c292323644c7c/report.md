## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | Pod aiops-case-v15/workload 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason: OOMKilled` (fact-0d66be5cf755) | 直接证明容器因内存耗尽被终止 |
| 2 | K8s State | Kubernetes | `pod.phase: Running`, `ContainersReady: False` (fact-05ecba0e07d0, fact-701cb1d3a357) | 证实 Pod 处于运行但不可用的故障状态 |
| 3 | K8s Event | Kubernetes | `Exit Code: 137` 持续触发 `BackOff` (fact-df1c02f4f423, fact-32846113a35a) | 确认容器退出码及 Kubernetes 的重启抑制行为 |
| 4 | K8s Config | Kubernetes | `container.resource_limit.memory: 64Mi` (fact-7da6c0f6763c) | 确定触发故障的硬限制配置 |
| 5 | Logging | Elasticsearch | `log.message: startup allocation 256Mi` (fact-0e0f3b5f125d) | 证实应用启动时申请内存远大于 Limit |
| 6 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason: 1 (reason=OOMKilled)` (fact-11f576af3223) | 从指标层面印证 OOM 终止事实 |

**证据综述：**
Kubernetes 状态与日志高度互证：Pod 因内存硬限制仅 64Mi（证据 #4），而应用启动需分配 256Mi（证据 #5），瞬间触发 OOMKilled（证据 #1）及 Exit Code 137（证据 #3）。Kubernetes 状态（证据 #2）与 Prometheus 指标（证据 #6）一致记录了此循环。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 内存限制（64Mi）配置过低 → 应用启动分配 256MB 内存超出限制 → 容器触发 OOMKilled（Exit Code 137） → CrashLoopBackOff 重启循环
```

### 根因结论

**已确认根因：** 资源硬限制（Limit）配置过低导致启动即崩溃。

容器 `aiops-case-v15/workload` 的 `container.resource_limit.memory` 设定为 **64Mi**（事实 `fact-7da6c0f6763c`），这直接低于应用启动所需的 **256Mi** 内存分配量（事实 `fact-0e0f3b5f125d`）。

由于 Linux 内核检测到越界，立即向容器进程发送 SIGKILL 信号终止运行，造成 `OOMKilled` 异常与 **137** 退出码（事实 `fact-0d66be5cf755`、`fact-9e44ecda8c95`）。Pod 随后因 CrashLoopBackOff 策略进入重启循环（事实 `fact-319d956b41e7`、`fact-32846113a35a`），导致 Pod 虽处于 Running 状态但无法提供 Ready 服务。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 22.4s
├─ 并发证据采集: 47.1s
│  └─ g1 aiops-case-v15/workload: 47.1s (Evidence 38.3s, RCA 8.7s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime, pod-notready-probe-failed
