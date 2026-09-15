## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | Pod workload in namespace aiops-case-v15 is stuck in CrashLoopBackOff state. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes (fact-4c67deaec491) | container 'app' terminated reason: `OOMKilled` | 确认容器退出机制为 OOM，直接指向内存超额 |
| 2 | K8s Config | kubernetes (fact-6ffd90075b6b) | container 'app' resource_limit.memory: `64Mi` | 确定容器运行的硬内存上限 |
| 3 | K8s Event | kubernetes (fact-2c8259d1b351) | 事件记录：`Exit Code: 137` | 验证退出码符合 OOMKilled 标准 (SIGKILL) |
| 4 | K8s Event | kubernetes (fact-0d0420643847) | 事件记录：`Reason: CrashLoopBackOff` | 反映应用因上述原因反复崩溃 |
| 5 | Logging | elasticsearch (fact-43abbd48fc32) | 日志内容：`startup allocation 256Mi` | 证明应用启动逻辑中明确尝试分配 256Mi 内存 |
| 6 | Metric | prometheus (fact-51ef2bee8c32) | `kube_pod_container_status_last_terminated_reason` (label: `OOMKilled`): `1` | 指标侧验证最后一次终止原因为 OOM |
| 7 | Metric | prometheus (fact-cbc4c47dce76) | `kube_pod_container_status_restarts_total`: `5` | 验证应用因内存不足陷入重启循环 |

证据链表明：Kubernetes 记录的退出原因 (OOMKilled) 与指标侧的终止状态一致；日志中“启动时分配 256Mi”的行为与“64Mi”的硬限制直接冲突，解释了为何容器会因 137 号信号被杀并进入 CrashLoopBackOff。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动代码尝试分配 256Mi 内存 → 超出 cgroup 硬限制 64Mi 触发 OOMKiller → 容器以 137 号信号退出并重启 → 用户可见 CrashLoopBackOff
```

### 根因结论

已确认根因为**资源限制配置不足与应用内存需求不匹配**。应用启动时试图分配 256Mi 内存，但该 Pod 配置的 `container.resource_limit.memory` 仅为 64Mi，导致 Kubernetes 内核 OOMKiller 强制终止容器 (Evidence: `fact-6ffd90075b6b`, `fact-4c67deaec491`, `fact-43abbd48fc32`)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 15.1s
├─ 并发证据采集: 52.3s
│  └─ g1 aiops-case-v15/workload: 52.3s (Evidence 41.0s, RCA 11.2s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime, pod-oomkilled, pod-config-error, pod-notready-probe-failed, pod-evicted
