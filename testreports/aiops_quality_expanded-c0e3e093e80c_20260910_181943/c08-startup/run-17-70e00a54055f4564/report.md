## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | Pod workload in aiops-case-v15 is in CrashLoopBackOff state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `reason="BackOff"` message="Warning BackOff restarting failed container app..." (x211 over 49m) | 记录 Pod 进入 CrashLoopBackOff 的最终表现 |
| 2 | K8s Event | Kubernetes | `reason="OOMKilled"` Exit Code: `137` | 确认容器被 OOM Killer 终止及错误码 |
| 3 | K8s State | Kubernetes | `container.last_terminated_reason`: `OOMKilled` | 核心根因证据，指出最后退出的直接原因 |
| 4 | K8s Config | Kubernetes | `container.resource_limit.memory`: `64Mi` | 提供容器内存硬限制配置，是触发 OOM 的前提条件 |
| 5 | Logging | Elasticsearch | `startup allocation 256Mi` (2026-09-14T09:52:58.605Z) | 揭示应用启动时请求的内存资源，证实配置不匹配 |
| 6 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` (`OOMKilled`), `kube_pod_container_status_restarts_total`: `14` | 独立于 K8s API 的指标确认了 OOM 终止与重启次数 |

**证据互证**：
K8s 状态与 Event 确认了 `CrashLoopBackOff` 和 `OOMKilled`（fact-2, fact-3, fact-4），这与 Prometheus 的指标结果（fact-6）完全一致，证明非偶发现象。关键矛盾在于 K8s 配置的硬限制 `64Mi`（fact-5）与应用日志中要求的 `256Mi`（fact-7）存在显著不匹配，构成了确凿的因果证据。

## 🎯 根因分析 · g1

### 因果链

```text
配置限制 (64Mi) < 应用需求 (256Mi) → 启动时内存分配触发 cgroup OOM Killer → 容器以 Exit Code 137 被杀死 → Pod 进入 CrashLoopBackOff 循环
```

### 根因结论

已确认根因为 **应用内存需求与 K8s 资源限制配置不匹配**：容器被设定的内存硬限制为 `64Mi`，而应用启动时尝试分配 `256Mi` 内存，导致被 Linux OOM Killer 强制终止（Exit Code 137）。

该结论由以下事实支撑：
- 容器配置硬限制 `memory.limit` 为 `64Mi` (fact-5)；
- 应用日志显示 `startup allocation 256Mi` (fact-7)；
- K8s Event 与 Metrics 均记录最后终止原因为 `OOMKilled` (fact-3, fact-6)。

多源数据互相印证，证据充分。

---

## 📊 性能统计

```text
├─ 总耗时: 59.2s
├─ 问题定位: 11.6s
├─ 并发证据采集: 37.8s
│  └─ g1 aiops-case-v15/workload: 37.8s (Evidence 28.7s, RCA 9.0s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
