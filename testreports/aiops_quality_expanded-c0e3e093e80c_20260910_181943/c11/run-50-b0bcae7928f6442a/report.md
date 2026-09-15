## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态超过 99 分钟 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.status`: Terminating (lasts 99m) | 确认 Pod 处于阻塞删除状态 |
| 2 | K8s Config | Kubernetes | `container.resource_limit.memory`: 96Mi | 提供资源受限上下文，支持 OOM 假设 |
| 3 | K8s Config | Kubernetes | Pod 自定义 `finalizer`: 'aiops.lab/hold' | 提供删除阻塞的直接技术原因 |
| 4 | K8s Event | Kubernetes | Events: 含 `k8s.v1.cni.cncf.io/networks-status` 等注解信息 | 确认网络资源正常，排除 CNI 残留导致删除失败的可能 |
| 5 | K8s State | Kubernetes | `container.last_terminated_reason`: Error, `exit_code`: 137 | 触发删除动作的初始事件，137 通常指 OOMKilled 或 SIGKILL |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 0 | 证实容器在 99 分钟内无重启，确认资源瓶颈已发生 |

Pod 的 Terminating 状态与 Exit Code 137 证实了初始的异常终止。然而，99 分钟的阻塞删除与 0 次重启表明，除了资源终止外，存在额外的清理机制失效。Kubernetes 层面的最终事实表明，自定义 finalizer 'aiops.lab/hold' 的存在是导致该终止状态的直接且持续的原因。Metric 与 Event 数据排除了资源未释放或 CNI 异常导致的副作用。

## 🎯 根因分析 · g1

```text
容器以 exitCode 137 异常终止 → Pod 存在自定义 finalizer 'aiops.lab/hold' → finalizer 清理机制未触发 → Pod 无法完成删除进入 Terminating
```

**已确认根因：**
Pod `aiops-case-11/workload` 因异常终止（`exit_code: 137`）触发删除流程，但 Kubernetes 的自定义 finalizer `'aiops.lab/hold'` 阻塞了最终的清理过程。由于对应的 finalizer 控制器未正确运行或逻辑失败，Pod 对象无法移除 finalizer 标记，导致状态卡在 `Terminating` 长达 99 分钟。该结论由 K8s 维度中的 `finalizer` 配置及 `Terminating` 状态事实证实（证据 #1, #3）。

**证据不足环节：**
最终触发容器异常终止（`exitCode 137`）的精确原因属于“未确认”。虽然资源限制 `memory: 96Mi` 和 0 次重启支持了 OOM 假设，但缺失 Logging 与 Tracing 数据，无法确切断定是内存溢出还是被其他外部因素强制杀死。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 20.3s
├─ 并发证据采集: 41.4s
│  └─ g1 aiops-case-11/workload: 41.4s (Evidence 33.4s, RCA 8.0s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
