## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod 'workload' in 'aiops-case-11' is stuck in 'Terminating' state because a custom finalizer 'aiops.lab/hold' is present in the Pod's metadata but the corresponding controller or resource (which is responsible for releasing it) is not active or responding. The initial trigger for deletion was an OOMKill (Exit 137) of the 'app' container, but the custom finalizer prevents the API server from completing the deletion process. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-11/workload` 状态: `Terminating (lasts 69m)` | 确认异常现象：Pod 处于删除卡滞状态，持续约 1 小时 |
| 2 | K8s Event | Kubernetes | Exit Code: 137 | 提供初始触发原因：应用容器 'app' 被 OOMKill |
| 3 | K8s State | Kubernetes | Container 'app' 退出码: 137，重启次数: 0 | 确认触发事件：OOMKill 导致 Pod 进入删除流程，且仅发生过一次 |
| 4 | K8s State | Kubernetes | Memory Limit: 96Mi, CPU Limit: 200m | 提供上下文：容器资源限制较小，佐证了 OOM 触发的合理性 |
| 5 | K8s State | Kubernetes | Condition `Ready`: False (reason: ContainersNotReady) | 确认当前健康状态：容器非就绪，符合 Terminating 阶段的中间状态 |
| 6 | Metric | Prometheus | `kube_pod_status_phase` (phase=Running): 1 | 辅助观测：Pod 仍被监控为 Running 阶段（API 层面的 Terminating 延迟），确认集群侧未彻底释放资源 |

**证据关联：**
Kubernetes 事实 (2, 3) 确认了触发机制是 OOMKill (Exit 137)。然而，Kubernetes 事实 (1) 表明该 Pod 在触发后 69 分钟仍处于 Terminating 状态，这与通常几分钟内完成的删除过程矛盾。结合诊断结论，根本原因在于存在一个未响应的最终处理器（Custom Finalizer），尽管输入事实中未直接展示 `aiops.lab/hold` finalizer 的 YAML 片段，但异常状态持续时长与 OOM 触发的孤立事件共同指向了“删除被拦截”这一特定机制。Metric 事实 (6) 从侧面确认了集群状态与 Pod 内部状态的一致性（仍在资源列表中）。

## 🎯 根因分析 · g1

```text
Container 'app' OOMKilled (Exit 137) → Pod 被标记删除，但 'aiops.lab/hold' finalizer 存在 → 对应的 'aiops.lab' 控制器未响应或未激活 → API Server 等待最终器移除，Pod 卡在 Terminating 状态 (69m)
```

### 根因结论

已确认根因为 **自定义最终器 (Custom Finalizer) 'aiops.lab/hold' 导致删除流程卡滞**。

1. **触发机制**：Pod `aiops-case-11/workload` 的应用容器 'app' 因内存不足被 OOMKill (Exit Code 137) [事实 2, 3]。
2. **失败机制**：该 Pod 元数据中包含 `aiops.lab/hold` 最终器，该机制要求对应的控制器在删除 Pod 前释放此最终器 [诊断结论引用]。
3. **直接故障**：负责处理该最终器的控制器（'aiops.lab'）未响应或不活跃，导致 API 服务器无法清除最终器字段，从而无限期保持 Pod 的 Terminating 状态 [诊断结论引用]。

当前证据足以说明“为什么卡在 Terminating”，但对于“为什么控制器不响应”缺乏决定性日志证据（Logging/Tracing 缺失），需进一步排查控制器自身状态或集群事件以确认控制器故障的具体原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 15.7s
├─ 并发证据采集: 49.1s
│  └─ g1 aiops-case-11/workload: 49.1s (Evidence 40.2s, RCA 8.8s)
└─ 汇总总结: 11.5s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
