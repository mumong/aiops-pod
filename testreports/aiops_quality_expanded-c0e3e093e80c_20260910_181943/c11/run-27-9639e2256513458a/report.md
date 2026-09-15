## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | aiops-case-11/workload Pod 在 Terminating 状态停滞 57 分钟未清理 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.last_terminated_reason: Error | 确认 Pod 已终止 |
| 2 | K8s State | kubernetes | container.last_exit_code: 137 | 指示容器被内核信号终止（通常为 OOM） |
| 3 | K8s Event | kubernetes | message: Stopping container app (lasts 57m) | 确认容器停止操作已执行，但整体资源清理停滞 |
| 4 | K8s State | kubernetes | pod.status: Terminating (lasts 57m) | 证实 Pod 处于僵死状态 57 分钟 |
| 5 | Metric | prometheus | kube_pod_container_status_restarts_total: 0 | 排除应用频繁重启或崩溃循环 |
| 6 | K8s State | kubernetes | Annotations: aiops.lab/hold Finalizer | 识别阻止 Pod 对象最终删除的资源标记 |

现有证据表明：容器进程因异常退出（Exit 137）而被 Kubelet 杀死，导致应用层生命周期结束；但 Pod 对象本身因持有 `aiops.lab/hold` 这个 Finalizer 标记，导致 Kubernetes 对象存储层的删除流程无法完成，进而引发 Pod 状态在 Terminating 下停滞。Metrics 显示重启次数为 0，排除了应用侧持续崩溃重启导致资源无法释放的可能。

## 🎯 根因分析 · g1

### 因果链

```text
Finalizer 'aiops.lab/hold' 存在且未释放 → 对象层删除机制被拦截 → 容器虽已退出 (Exit 137) 但对象未销毁 → Pod 卡在 Terminating 状态 57 分钟
```

### 根因结论

已确认的根因是：**Finalizer `aiops.lab/hold` 未被正确移除。**

证据链（编号 4、6）证实 Pod 对象停留在 `Terminating` 状态长达 57 分钟，这是 Kubernetes 清理流程被阻塞的直接症状。Kubernetes 要求在删除包含 Finalizer 的对象时，必须由对应的 Controller 先移除该 Finalizer，然后 API Server 才会真正删除对象。

虽然容器进程因内存或系统限制以 `Exit Code 137` 终止（编号 2），应用层面的运行已停止，但由于 `aiops.lab/hold` 的存在，API Server 将删除请求排队，等待该标签被清除。事实中缺少 `aiops.lab/hold` 对应 Controller 的日志或状态（unknowns），说明该 Controller 未能检测到删除信号或执行清理逻辑，从而导致资源僵死。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 15.4s
├─ 并发证据采集: 47.2s
│  └─ g1 aiops-case-11/workload: 47.2s (Evidence 38.0s, RCA 9.2s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
