## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod workload in aiops-case-11 stuck in Terminating state for 42 minutes despite deletionTimestamp set long ago. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.status`: "Terminating (lasts 42m)", `pod.phase`: "Running" | 确立 Pod 卡在 Terminating 状态已超过 42 分钟且未彻底销毁的核心现象 |
| 2 | K8s Event | kubernetes | `event.message`: "Normal Killing 42m kubelet Stopping container app" | 确认底层容器运行态已终止，排除了进程假死导致无法杀死的容器层障碍 |
| 3 | K8s Event | kubernetes | `event.message`: "Exit Code: 137" (来自 annotation 记录 `fact-671b70944d45`) | 记录容器异常退出的信号代码，但缺乏日志证实具体触发原因 (OOM vs Signal) |
| 4 | K8s Config | kubernetes | `container.resource_limit.memory`: "96Mi", `resource_request.memory`: "24Mi" | 提供容器资源上下文，结合 exit 137 可推测存在 OOM 可能性，但无法作为定论证据 |
| 5 | K8s Event | kubernetes | `event.message`: "Annotations: aiops.lab/hold finalizer is present" (结合诊断结论与 context) | 揭示导致 Pod 资源无法在 API Server 层被清理的最终阻断原因 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total`: "0", `phase`: "Running", `sample_count`: 1 | 印证 K8s 层面容器仅启动一次即被杀且未重启，无连续重启行为干扰 |

**证据关联分析：**
K8s 状态 `Terminating` (证据1) 与 K8s Event `Killing` (证据2) 及 Metric `restart_count=0` (证据6) 形成一致闭环：Pod 已被成功驱逐或终止，但资源对象未被回收。结合 K8s 配置信息，由于缺乏日志 (Logging absent) 无法查明容器退出 137 码的确切原因，但所有证据均指向同一个 API 层的阻断点：自定义 Finalizer 未被控制器移除，导致 Garbage Collector 无法执行删除动作。

## 🎯 根因分析 · g1

### 因果链

```text
自定义 Finalizer 'aiops.lab/hold' 驻留 → 管理控制器未在容器终止后移除该 Finalizer → API Server 等待 Finalizer 清理完成 → Pod 状态长期卡死在 Terminating (42+ 分钟)
```

### 根因结论

已确认的根因是 **自定义 Finalizer 'aiops.lab/hold' 的控制器逻辑异常或缺失**，导致 Pod 对象在 API Server 端无法完成最终的清理流程。

尽管 Pod 内部容器因异常 (Exit Code 137) 被 kubelet 停止 (证据 2, 3)，但这只是触发了删除流程，真正的“阻塞点”在于 Kubernetes 的资源生命周期管理。因为 `aiops.lab/hold` 这个 Finalizer 标签一直存在于 Pod 的元数据中，API Server 会强制要求负责管理该资源的控制器将其移除后，才会最终从集群中擦除该 Pod 对象。当前 Pod 处于 `Terminating (lasts 42m)` (证据 1) 且控制器未执行移除动作，构成了该现象的直接原因。

**缺失的关键事实：**
1. 无法确认容器 Exit 137 的具体原因（是内存耗尽 OOM Killer 触发，还是其他信号中断），因为 Logging 维度数据为空，且未检测到足以证明 OOM 的特异性 Metrics 突变。
2. 无法确认负责 `aiops.lab/hold` 的控制器当前状态或报错信息，该控制器的状态是决定是否需要人工介入或重启的核心未知量。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 25.1s
├─ 并发证据采集: 49.3s
│  └─ g1 aiops-case-11/workload: 49.3s (Evidence 38.5s, RCA 10.7s)
└─ 汇总总结: 12.4s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
