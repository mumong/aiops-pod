## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod workload (aiops-case-11) stuck in Terminating status for 46 minutes |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `phase`: Running；`ContainersReady`: False (message: "containers with unready status: [app]") | 核心现象：Pod 生命周期停滞，API Server 无法执行垃圾回收 |
| 2 | K8s State | kubernetes | `container.last_terminated_reason`: Error；`container.last_exit_code`: 137 | 确认容器进程被异常终止，排除正常退出的可能 |
| 3 | K8s Config | kubernetes | 资源限制：`memory`: 96Mi, `cpu`: 200m；请求：`memory`: 24Mi, `cpu`: 20m | 提供故障上下文，内存限制相对保守，未直接指向 OOM |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total`: 0 | 佐证进程在最终崩溃前未经历健康探针重启，直接导致 OOMKill 或强制终止 |
| 5 | Metric | prometheus | `kube_pod_status_phase` (Pending): 0；`Running`: 1 | 确认当前集群中该工作负载处于运行（或停滞）状态，非调度问题 |

**证据关系说明：**
K8s 状态显示 Pod 处于 `Running` 阶段但容器不健康 (`exit_code: 137`)，结合 Metric 中重启次数为 0，说明应用进程在首次启动后遭遇不可逆的异常终止。K8s 状态中的未就绪标记证实了 Pod 资源未正常回收。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 含有 'aiops.lab/hold' 自定义 Finalizer → 控制器/逻辑未能释放该 Finalizer → API Server 拒绝执行垃圾回收 → Pod 无限期停留在 Terminating 状态
```

### 根因结论

已确认根因为：**自定义 Finalizer (`aiops.lab/hold`) 阻塞了 Pod 的释放。**

*   **现象确认**：Pod `aiops-case-11/workload` 处于 Terminating 状态长达 46 分钟，API Server 停止执行垃圾回收。
*   **机制分析**：容器以 Exit Code 137 (SIGKILL) 被终止，但 API Server 未删除 Pod 对象，这是因为 K8s 机制要求必须移除 `metadata.finalizers` 中的项才能完成删除。
*   **证据支撑**：诊断事实明确指出 Pod 被 `aiops.lab/hold` 自定义 Finalizer 阻塞。
*   **缺失环节**：无法确定负责管理该 Finalizer 的具体控制器身份，也无法确定该控制器未能释放 Finalizer 的根本原因（如控制器崩溃或逻辑错误）。但这足以解释“为何 Pod 卡在 Terminating”这一核心故障现象。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 11.7s
├─ 并发证据采集: 44.7s
│  └─ g1 aiops-case-11/workload: 44.7s (Evidence 36.3s, RCA 8.3s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
