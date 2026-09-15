## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod workload 在 aiops-case-11 namespace 中处于 Terminating 状态持续 18 分钟无法删除 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-11/workload` 状态 `Terminating` 持续 18 分钟；容器 `app` 退出码 `137`；未就绪 | 确认异常现象：容器已死但 Pod 无法从 API Server 对象中移除 |
| 2 | K8s Event | kubernetes | `Normal Killing 18m kubelet: Stopping container app` | 确认底层运行时（kubelet）已执行清理动作，节点侧故障已排除 |
| 3 | K8s Config | kubernetes | 容器 `app` 资源限制：`memory: 96Mi`, `cpu: 200m`；请求：`memory: 24Mi`, `cpu: 20m` | 提供上下文：低内存配置可能诱发 OOM，但非 Terminating 的直接原因 |
| 4 | K8s Event | kubernetes | 事件记录显示 `Exit Code: 137` | 进一步印证容器因信号（通常为 SIGKILL）终止，且容器生命周期已结束 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total` 值为 `0` | 排除反复崩溃重启循环导致卡死的可能性，指向一次性终止事件 |
| 6 | Logging | elasticsearch | 模式 `request completed` (HTTP 200) 在 `03:47:09` - `03:47:15` 期间出现 4 次 | 佐证应用进程在终止前最后 6 秒仍在处理正常请求，非崩溃式无响应 |

Pod 对象（K8s State）显示容器已退出的事实（Exit 137、Stopping Event）与 Pod 状态长期停滞（Terminating 18m）之间存在因果断裂。Metrics 与 Logging 进一步印证了这是一次“成功执行完毕后被终止”的过程，而非资源耗尽导致的无限期挂起。因此，根因指向 Kubernetes 控制平面在终止阶段的行为受阻。

## 🎯 根因分析 · g1

### 因果链

```text
存在自定义 finalizer 'aiops.lab/hold' 且无对应控制器清理 → API Server 拦截 Pod 删除操作等待资源回收 → 容器运行正常终止 (Exit 137) → Pod 对象陷入 Terminating 状态
```

### 根因结论

**已确认根因：Pod 被自定义 Finalizer 阻塞。**

尽管容器进程已经因为信号（如 OOM 触发的 SIGKILL，退出码 137）正常退出，且节点上的 kubelet 也已经完成了资源清理工作（Evidence #1, #2, #3, #5），但 Pod 资源在 API Server 中并未被最终删除。根本原因是该 Pod 绑定了自定义 Finalizer `'aiops.lab/hold'`。Kubernetes 默认机制要求在移除 Pod 对象前必须移除所有 Finalizers，而该 Finalizer 对应的清理控制器未能（或尚未）执行移除操作，导致 Pod 长期处于 `Terminating` 挂起状态。

**缺失决定性事实：**
输入数据中明确指出了未知项（Unknowns）：持有 `'aiops.lab/hold'` finalizer 的控制器状态及为何未完成清理。若要进一步诊断，需补充该 Finalizer 控制器的日志或事件，以查明其处理延迟或失败的具体原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 17.7s
├─ 并发证据采集: 47.0s
│  └─ g1 aiops-case-11/workload: 47.0s (Evidence 38.9s, RCA 8.1s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
