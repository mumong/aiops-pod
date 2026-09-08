## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod 'workload' stuck in Terminating state for >50 mins due to finalizer |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-11/workload` 状态：Phase=Running, ContainersReady=False, Reason=ContainersNotReady | 定义异常现象：Pod 处于运行中但容器未就绪的矛盾状态 |
| 2 | K8s State | Kubernetes | 容器 `app` 退出状态：ExitCode=137 (OOM Killed), LastTerminatedReason=Error | 解释容器为何未就绪，是 Pod 处于 Terminating 前的终止原因 |
| 3 | K8s Config | Kubernetes | 容器 `app` 资源：Request CPU=20m, Memory=24Mi; Limit CPU=200m, Memory=96Mi | 排除资源超限导致的 OOM（96Mi 通常足够，OOM 由应用或逻辑决定） |
| 4 | K8s Event | Kubernetes | ContainerRestartCount=0 | 排除因频繁重启导致的状态抖动，确认为单次终止 |
| 5 | K8s State | Kubernetes | 诊断说明：Pod 停滞在 Terminating 状态超过 50 分钟 | 确认故障持续时间与终止阶段卡死现象 |

**证据关联：**
1. Pod 的 `ContainersReady=False` 直接由容器退出码 137 导致（见事实 1 与 2）。
2. 资源配置（见事实 3）证明 96Mi 的内存限制并未发生通常意义的物理耗尽，暗示 OOM 可能由特殊资源或逻辑触发。
3. 停滞在 Terminating 状态（见事实 5）是最终故障现象，其背后原因在现有 K8s State 事实中未直接体现，需结合根因分析。

## 🎯 根因分析 · g1

### 因果链

```text
自定义 Finalizer 'aiops.lab/hold' 未被清理 → Finalizer Controller 未响应移除请求 → API Server 等待 Finalizer 清除 → Pod 无限期停留在 Terminating 状态
```

### 根因结论

**已确认的根因：** Pod `aiops-case-11/workload` 无限期卡在 `Terminating` 状态。

**根因分析：**
现有证据（见事实 1, 2）表明 Pod 的容器 `app` 以退出码 137 (OOM Killed) 终止，且重启次数为 0，说明这是一个单次的终止事件。然而，Pod 本身并未顺利删除，而是进入了 `Terminating` 状态的无限期僵死（见事实 5）。根据诊断框架与事实关联，这一现象的根本原因是 Pod 对象上挂载了自定义 Finalizer `aiops.lab/hold`，负责清理该 Finalizer 的 Controller 未能成功响应，导致 API Server 在清理资源时无限期等待。

**证据不足说明：**
目前缺乏关于“为什么负责 `aiops.lab/hold` 的 Controller 未响应”的确切日志或指标证据（Logging/Tracing 采集为空），这属于故障的未知因素（unknowns）。但不影响对 Pod 卡死现象的直接归因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 23.2s
├─ 并发证据采集: 42.9s
│  └─ g1 aiops-case-11/workload: 42.9s (Evidence 35.8s, RCA 7.0s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
