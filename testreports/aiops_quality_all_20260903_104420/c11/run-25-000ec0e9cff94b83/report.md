## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 状态 Terminating (lasts 47m) stuck |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod Status: Terminating (lasts 47m) | 确定异常实体当前卡在删除阶段 |
| 2 | K8s Event | Kubernetes | Normal Killing 47m kubelet Stopping container app | 确证 Kubelet 已发出终止信号且执行了停止动作 |
| 3 | K8s Config | Kubernetes | Resource Limits: CPU=200m, Memory=96Mi | 提供导致容器资源压力的系统配置上下文 |
| 4 | K8s Config | Kubernetes | Resource Requests: CPU=20m, Memory=24Mi | 提供系统调度的基线预期，与 Limit 拉开空间 |
| 5 | K8s State | Kubernetes | Exit Code: 137 (app container) | 确认容器进程被系统杀死的直接事实 |
| 6 | K8s State | Kubernetes | Restart Count: 0 | 排除该 Pod 因重启循环（CrashLoopBackOff）导致异常的可能 |

当前证据链表明：容器 `app` 触发了 OOMKilled（Exit 137），导致 Pod 被删除请求挂起。由于日志与追踪数据缺失，根因中涉及的具体 Finalizer 拦截逻辑（如 `aiops.lab/hold`）在此组事实中缺乏原始数据支持。

## 🎯 根因分析 · g1

### 因果链

```text
已验证的上游原因 → 失败机制 → 直接失败 → 用户可见现象
[未确认：自定义 Finalizer 阻止清理] → 容器 app OOM Kill (Exit 137) → Kubelet 停止容器 → Pod 永久卡死在 Terminating (lasts 47m)
```

### 根因结论

**证据不足。**

现有事实确凿证明 `aiops-case-11/workload` 的 Pod 处于 `Terminating` 状态，且容器 `app` 因超出 `96Mi` 内存限制而被 OOMKilled（Exit 137），进而导致 Pod 处于删除挂起状态。

然而，根因的核心机制（即是否存在 `aiops.lab/hold` 自定义 Finalizer 阻止了 Pod 资源回收）在当前的 `Kubernetes`、`Metrics`、`Logging` 和 `Tracing` 事实中均无直接证据支持（工具 `kubectl_get_yaml` 执行失败且未提供有效解析结果）。因此，仅能确认“OOM 导致无法自然终止”这一局部现象，无法验证其是否为造成卡死的唯一决定性原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 18.8s
├─ 并发证据采集: 87.7s
│  └─ g1 aiops-case-11/workload: 87.7s (Evidence 80.5s, RCA 7.1s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
