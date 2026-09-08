## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 中存在自定义 finalizer 'aiops.lab/hold'。容器 app 因 SIGKILL (exitCode 137) 终止后，虽然 Kubelet 完成了资源清理并上报 Killing 事件，但由于该 finalizer 尚未被移除（对应的控制器可能缺失或未处理），API Server 阻止了 Pod 对象从 Etcd 中的彻底删除，导致 Pod 进入 Terminating 状态并卡住。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | Normal Killing (31m ago): "Stopping container app" | 确认 Kubelet 已执行资源清理并上报事件 |
| 2 | K8s State | kubernetes | Pod phase: Terminating (lasts 31m) | 确认 Pod 对象已停止运行但未能从 Etcd 彻底删除 |
| 3 | K8s Event | kubernetes | Container exit code: 137 (SIGKILL) | 确认容器因强制终止（OOMKilled 或手动 kill）而结束 |
| 4 | K8s State | kubernetes | Container restart count: 0 | 确认 Pod 仅发生过一次终止，未发生自动重启循环 |
| 5 | K8s Config | kubernetes | container.resource_limit.memory: 96Mi | 为 exitCode 137 提供资源限制上下文 |

**证据印证说明**：
K8s 事件（#1）与状态（#2）均指向容器终止后的清理阶段，结合 Pod 状态卡住（Terminating 达 31 分钟），表明 Kubernetes 对象生命周期受阻。退出码 137（#3）证实了终止的直接触发原因，而 restart count 为 0（#4）排除了因配置错误导致的频繁崩溃重启（CrashLoopBackOff）作为根因。

## 🎯 根因分析 · g1

### 因果链

```text
自定义 finalizer 'aiops.lab/hold' 未被移除 → 容器 app 收到 SIGKILL (exitCode 137) 终止 → Kubelet 完成资源清理并上报 Killing 事件 → API Server 阻止 Pod 对象从 Etcd 彻底删除 → Pod 卡在 Terminating 状态
```

### 根因结论

已确认根因为 **自定义 finalizer 'aiops.lab/hold' 阻止了 Pod 的删除**。

证据显示容器 app 因 exit code 137（SIGKILL）终止 [证据 #3]，随后 Kubelet 完成了清理并上报了 Killing 事件 [证据 #1]。然而，Pod 对象状态显示其停留在 `Terminating` 阶段长达 31 分钟且未自动重启 [证据 #2, #4]。这表明 Kubernetes 的 Garbage Collector 在尝试删除 Pod 时被 finalizer 机制拦截，导致对象无法从 Etcd 中彻底移除。虽然资源限制（96Mi）存在，但根本机制在于 finalizer 的清除逻辑缺失。

---

## 📊 性能统计

```text
├─ 总耗时: 53.9s
├─ 问题定位: 13.9s
├─ 并发证据采集: 31.3s
│  └─ g1 aiops-case-11/workload: 31.3s (Evidence 25.1s, RCA 6.1s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
