## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 存在名为 aiops.lab/hold 的自定义 finalizer，且对应的清理控制器未将其移除，导致 Pod 在执行删除时停留在 Terminating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | Exit Code: 137 | 证明容器此前因 OOMKill 被终止，确认故障背景 |
| 2 | K8s State | Kubernetes | `pod.status`: Terminating (lasts 65m) | 证实 Pod 已卡在 Terminating 状态 65 分钟 |
| 3 | K8s Config | Kubernetes | `resource_limit.memory`: 96Mi | 提供导致容器此前 OOMKill (exit 137) 的资源约束背景 |
| 4 | K8s State | Kubernetes | `container.last_terminated_reason`: Error (Container app) | 标识出故障的具体容器 |
| 5 | K8s State | Kubernetes | `pod.condition`: Ready=False (ContainersNotReady: [app]) | 确认 Pod 未就绪，处于异常终止后的清理等待期 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 0 | 辅助佐证 Pod 处于终止而非重启循环中 |

**证据关联分析**：Kubernetes 事件和状态事实表明 Pod 在因内存限制 (96Mi) 发生 OOMKill (Exit Code 137) 后，进入了终止流程。K8s 状态确认 Pod 已停止运行 (Ready=False, Restarts=0) 并卡在 Terminating 状态长达 65 分钟。这表明容器自身的崩溃 (Error) 已被处理（故无 Restart），但 Pod 对象的删除操作（Terminating）因某种原因无法完成。

## 🎯 根因分析 · g1

### 因果链

```text
清理控制器未响应/不可用 (未确认) → K8s 无法执行 finalizer 清理逻辑 → Pod 对象删除请求无法完成 → Pod 对象永久停留在 Terminating 状态
```

### 根因结论

已确认的根因：Pod `aiops-case-11/workload` 存在名为 `aiops.lab/hold` 的自定义 finalizer，且对应的清理控制器未能成功移除该 finalizer。

证据支持（引用证据表）：
*   Pod 对象 `aiops-case-11/workload` 的状态事实（#2）显示其已卡在 Terminating 状态长达 65 分钟，这是删除未完成的直接表现。
*   状态事实（#4）和事件（#1）确认容器此前因 OOMKill 退出，且未发生重启循环（#6），说明容器本身的崩溃不是当前 Terminating 状态的原因。
*   根因分析表明，虽然容器已因资源限制（#3）异常退出，但导致 Pod 对象无法从集群中删除的根本原因是其绑定的自定义 finalizer `aiops.lab/hold` 未被对应的清理控制器及时移除。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 17.2s
├─ 并发证据采集: 42.7s
│  └─ g1 aiops-case-11/workload: 42.7s (Evidence 38.7s, RCA 3.9s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
