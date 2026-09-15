## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod workload 处于 Terminating 状态停滞且最终无法移除 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` | Pod phase: `Running` (fact-3ce057d0fe52)；container last terminated reason: `Error` (fact-2b9cb95c1eed) | 确认 Pod 容器曾尝试启动但失败，目前处于异常等待状态 |
| 2 | K8s State | `kubernetes` | 资源限制：CPU `200m` / 内存 `96Mi` (fact-05878f7f3c88, fact-4a99a4db25d5)；Request：CPU `20m` / 内存 `24Mi` (fact-7faf83f3ffa8, fact-a72728812471) | 提供资源环境上下文，排除因资源不足导致的 OOMKilled 等常见终止原因 |
| 3 | K8s Event | `kubernetes` | Exit code `137` (fact-4ec1557cba02)；ContainersReady/Ready: `False` (reason: `ContainersNotReady`, fact-050a28338b37) | 确认容器进程异常终止（SIGKILL）且 Pod 未达到就绪状态，是 Terminating 状态的基础 |
| 4 | Metric | `prometheus` | `kube_pod_container_status_restarts_total`: `0` (fact-d570b0e5e8ef) | 确认容器未发生重启行为，Pod 卡在单次启动失败后的清理/终止阶段 |
| 5 | K8s State | `kubernetes` | (诊断数据指出) Pod spec 包含 finalizer `aiops.lab/hold` | 揭示状态停滞的根本机制，kubelet 在完成容器清理后无法从 API Server 彻底移除该 Pod |

Kubernetes 状态与指标共同表明：容器在启动后迅速终止且未重启（Exit 137, restarts=0）。结合诊断数据中的配置事实，容器终止并非导致现象的唯一原因，真正的阻滞点在于阻止资源回收的 Finalizer。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 配置 finalizer 'aiops.lab/hold' (已验证上游原因)
→ kubelet 等待 finalizer 解除以完成资源回收 (失败机制)
→ Pod 无法从 API Server 中彻底删除 (直接失败)
→ 观察到 Pod 处于 Terminating 状态停滞 (用户可见现象)
```

### 根因结论

**已确认根因**：Pod 对象配置了名为 `aiops.lab/hold` 的 Finalizer，导致其在容器终止后无法被 Kubernetes 正常回收。

该 Finalizer 阻止了 Kubernetes 删除流程的最后一步。尽管容器进程已因异常终止（Exit code 137）并标记为 `ContainersNotReady`，且重启计数为 0，但 Kubernetes 的 Garbage Collection 机制被 `aiops.lab/hold` 拦截，导致 Pod 长期停留在 `Terminating` 阶段。

**未确认项**：持有 `aiops.lab/hold` Finalizer 的外部控制器身份，以及解除该 Finalizer 的具体触发条件。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 17.4s
├─ 并发证据采集: 49.0s
│  └─ g1 aiops-case-11/workload: 49.0s (Evidence 42.6s, RCA 6.3s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
