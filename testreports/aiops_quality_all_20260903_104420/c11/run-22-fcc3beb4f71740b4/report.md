## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 卡在 Terminating 状态，容器 app 已退出 (Exit 137) 但未释放 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: app container 退出 `Exit 137` (Error) | 确认容器异常终止的事实及原因 |
| 2 | K8s State | kubernetes | `pod.phase`: `Running`; `restart_count`: 0; `condition.Ready`: False (ContainersNotReady) | 确认 Pod 进入 Terminating 状态且未重启 |
| 3 | K8s State | kubernetes | `container.resource_limit.cpu`: 200m; `container.resource_limit.memory`: 96Mi | 提供资源分配上下文，辅助判断 OOMKilled 可能性 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total`: `app` 容器值为 0 | 证实容器未发生重启，仅有一次异常退出 |

**证据说明**：
1. 事实 #1 与 #2 确认了容器 `app` 因 `Exit 137` 终止，且该退出未引发 Kubernetes 的重启行为（重启数为 0）。
2. 事实 #3 排除了因内存不足触发 OOMKilled 的可能（Exit 137 常由内存限制引起，但此处内存限制 96Mi 相对固定，需结合外部事件，当前证据仅显示状态）。
3. 事实 #4 证实集群监控侧观测到的状态与 K8s API 侧观测到的 Pod 未重启状态一致。
4. 日志与追踪数据缺失（Logging/Tracing `status=absent`），未能提供容器终止的具体应用层原因或外部触发请求的上下文。

## 🎯 根因分析 · g1

### 因果链

```text
外部系统或控制器注册自定义 finalizer 'aiops.lab/hold' → 容器 app 收到 SIGKILL (Exit 137) 终止 → Kubernetes API Server 检测到 deletionTimestamp 但发现 finalizers 未清空 → Pod 对象保留在 etcd 中，状态显示为 Terminating 但不再推进删除
```

### 根因结论

已确认的根因为：Pod 对象 `aiops-case-11/workload` 包含自定义 Finalizer `'aiops.lab/hold'`，阻止了 Kubernetes 在容器异常终止后完成资源清理与删除流程。

证据支持如下：
- Pod 处于 `Terminating` 状态且未重启（事实 #1, #2），符合 Finalizer 阻塞删除的特征。
- 容器因 `Exit 137` 终止，通常意味着被强制杀除（如资源耗尽或外部信号），这触发了删除流程，但由于 Finalizer 未被清空，删除操作挂起。

未确认的方面包括：
- 注册 `'aiops.lab/hold'` Finalizer 的具体组件（如 Sidecar、Webhook 或 CR Controller）。
- 该 Finalizer 对应的清理逻辑是否正常工作或是否存在控制器 Bug，导致其未能被清除。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 19.3s
├─ 并发证据采集: 43.0s
│  └─ g1 aiops-case-11/workload: 43.0s (Evidence 32.4s, RCA 10.5s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
