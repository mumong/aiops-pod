## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 进入 Terminating 状态持续 64 分钟未回收 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.status`: Terminating (lasts 64m) [fact-f8433d894853] | 核心现象：对象删除流程停滞超 64 分钟 |
| 2 | K8s State | kubernetes | `container.last_terminated_reason`: Error [fact-2ebbca985010] | 确认容器应用进程已异常终止 |
| 3 | K8s State | kubernetes | `container.last_exit_code`: 137 [fact-00d36656d9cb] | 关键证据：Exit Code 137 直接指向 OOMKilled 或系统信号强制终止 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total`: 0 [fact-9b8c31f084a9] | 佐证 Pod 未触发重启策略，处于静默卡死状态 |
| 5 | K8s Config | kubernetes | `container.resource_limit.memory`: 96Mi [fact-30c2ee696a16] | 环境上下文：低内存硬限制，为 OOMKilled 提供合理资源诱因 |

证据互相印证：Kubernetes 状态显示 Pod 异常终止后长时处于 Terminating 阶段，结合 Exit Code 137 和 96Mi 内存硬限制，强有力地指向“因资源/信号问题进程被杀，但随后的清理阶段被阻塞”。Metric 显示重启数为 0，排除了快速失败重试的情况，确认了删除操作的“挂起”状态。

## 🎯 根因分析 · g1

### 因果链

```text
容器进程异常退出 (Exit Code 137) → 容器进入 Terminated 状态 → Kubernetes 删除链路受阻 (Finalizer/Kubelet/Volume等) → Pod 对象长期处于 Terminating 状态
```

### 根因结论

**证据不足。**

当前事实已确认 **Pod 处于 Terminating 卡死状态** 且 **容器进程已异常退出（Exit Code 137）**。然而，K8s 诊断的根因核心在于查明“为何删除链路受阻”。

正式 RCA 中指出具体阻塞点（Finalizer、Volume Detach、Kubelet 状态同步等）均未定位，且缺失决定性事实：
1.  **Pod 元数据缺失**：未提供 Pod 的 `Finalizers` 列表、`ownerReferences` 及 `persistentVolumeClaim` 绑定情况，无法判断是外部控制器依赖还是存储卷卸载卡住。
2.  **节点状态缺失**：未提供 Node `node2` 的健康状况及 `kubelet` 日志，无法判断是否为节点级 Kubelet 通信或资源回收故障。

因此，只能确认现象与诱因（退出码 137），无法确认导致 Terminating 卡死的最终根因。

---

## 📊 性能统计

```text
├─ 总耗时: 9.7m
├─ 问题定位: 20.1s
├─ 并发证据采集: 550.4s
│  └─ g1 aiops-case-11/workload: 550.4s (Evidence 541.6s, RCA 8.7s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
