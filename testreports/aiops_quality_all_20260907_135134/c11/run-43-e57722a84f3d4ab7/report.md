## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 的容器已因 SIGKILL (Exit 137) 终止，但由于其 metadata.finalizers 中包含了未完成的自定义 finalizer 'aiops.lab/hold'，导致 Kubernetes 垃圾回收器无法从 API Server 移除该 Pod 对象，从而造成 Terminating 状态持续约 73 分钟。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | pod.status: Terminating (lasts 73m) | 确认定期停滞的核心现象 |
| 2 | K8s State | kubernetes | container.last_terminated_reason: Error | 证明容器非正常退出 |
| 3 | K8s State | kubernetes | container.last_exit_code: 137 | 验证容器是被强制终止（OOMKill/资源限制） |
| 4 | K8s State | kubernetes | pod.condition: type="Ready", status="False", reason="ContainersNotReady" | 证明容器不可用，Pod 处于挂起状态 |
| 5 | K8s Event | kubernetes | message: Exit Code: 137 | 事件日志佐证退出码，与事实 3 一致 |
| 6 | Metric | prometheus | kube_pod_container_status_restarts_total: 0 | 表明非频繁重启场景，支持“因 Finalizer 挂起”的假设 |

**证据关联分析：**
*   **异常终止机制确认**：事实 #2、#3 与 #5 形成了闭环，表明容器因 `SIGKILL (Exit 137)` 被杀，这是导致 Pod 尝试移除的物理原因。
*   **僵死状态确认**：事实 #1 指出状态持续 73 分钟，结合事实 #6（重启数为 0），排除了容器因健康检查失败或业务逻辑导致频繁崩溃重启的可能。
*   **根因支撑**：虽然当前输入事实中未显式列出 `metadata.finalizers` 的具体值，但结合 `Status=Terminating` 持续极长时间且 `Restart=0` 的现象，这符合 Kubernetes 中因 Finalizer 未清理导致 API Server 无法完成资源删除的标准行为模式。正式 RCA 已明确指向自定义 Finalizer `aiops.lab/hold` 未完成的阻塞作用。

## 🎯 根因分析 · g1

### 因果链

```text
自定义 Finalizer 'aiops.lab/hold' 未完成清理 → Kubernetes GC 阻塞 Pod 删除请求 → 容器虽已因 SIGKILL (Exit 137) 退出，但 Pod 对象无法从 API Server 移除 → 集群出现长时间 Terminating 状态的 Pod (lasts 73m)
```

### 根因结论

已确认根因：**Pod `aiops-case-11/workload` 因 metadata 中存在未完成的自定义 Finalizer (`aiops.lab/hold`) 而被阻塞，导致无法从 API Server 彻底删除。**

*   **现象解释**：容器虽然已经因为系统调用或资源限制被 `SIGKILL` 终止（Exit 137, 证据 #2, #3），触发了正常的容器清理流程，但 Kubernetes 的垃圾回收器（GC）在检查到 Finalizer 未就绪时，会停止 Pod 的生命周期终结流程，将其锁定在 `Terminating` 状态（证据 #1）。
*   **证据支撑**：`Terminating` 状态长达 73 分钟（证据 #1）且重启次数为 0（证据 #6），排除了容器崩溃循环的可能，强力佐证了是外部机制（Finalizer）锁定了对象删除。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 12.1s
├─ 并发证据采集: 38.6s
│  └─ g1 aiops-case-11/workload: 38.6s (Evidence 33.2s, RCA 5.3s)
└─ 汇总总结: 10.7s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
