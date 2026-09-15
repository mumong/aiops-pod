## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | 容器内存限制配置错误：容器设置了 64Mi 的 memory limit，但启动命令中立即分配 256Mi 的 bytearray，导致内存分配超过限制，触发 cgroup OOM Killer 终止进程（OOMKilled） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason: OOMKilled` (fact-9a4eaef5bd9f) | 直接证明进程被内核 OOM Killer 终止 |
| 2 | K8s State | Kubernetes | `container.resource_limit.memory: 64Mi` (fact-abb9ec34823c) | 确认容器运行时的硬内存上限 |
| 3 | K8s Event | Kubernetes | `container.waiting_reason: CrashLoopBackOff` (fact-5ad0aadbc5e6) | 证实 Pod 处于频繁重启的异常状态 |
| 4 | K8s Config | Kubernetes | `container.resource_request.memory: 8Mi` (fact-abe15cad609e) | 确认调度期望值，佐证资源请求/限制配置不一致 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason=OOMKilled` (fact-90c9d8ade1c4) | 独立确认终止原因为 OOM |
| 6 | Logging | Elasticsearch | `log.message: startup allocation 256Mi` (fact-016ce27a1965) | 提供启动时内存分配的具体数值 |

**证据关联说明：**
Kubernetes 的 `OOMKilled` 状态 [1] 与 Prometheus 指标 [5] 互为印证，共同指向内存超限。K8s 配置显示限制仅为 64Mi [2]，而应用启动日志显示立即申请了 256Mi [6]，这构成了直接的因果冲突（256Mi > 64Mi），解释了为何触发 OOM 并导致 CrashLoopBackOff [3]。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动分配 256Mi (Logging: fact-016ce27a1965) > 容器内存限制 64Mi (K8s: fact-abb9ec34823c) → 触发 cgroup OOM Killer → 容器被强制终止 (K8s: fact-9a4eaef5bd9f) → Pod CrashLoopBackOff (K8s: fact-5ad0aadbc5e6)
```

### 根因结论

已确认根因为**容器内存配置错误（资源限制过低）**。
应用启动命令中立即申请 256Mi 内存 [Logging: fact-016ce27a1965]，而 Kubernetes 容器仅配置了 64Mi 的内存硬限制 [K8s: fact-abb9ec34823c]。这一配置错误导致内存分配超过 cgroup 上限，直接触发内核 OOM Killer 杀死进程 [K8s: fact-9a4eaef5bd9f, Metric: fact-90c9d8ade1c4]，进而引起 Pod 进入 CrashLoopBackOff 状态 [K8s: fact-5ad0aadbc5e6, K8s: fact-6a7e7a3b2345]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 14.1s
├─ 并发证据采集: 40.2s
│  └─ g1 aiops-case-v15/workload: 40.2s (Evidence 33.9s, RCA 6.1s)
└─ 汇总总结: 10.7s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
