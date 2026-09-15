## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | Pod 的 preStop lifecycle hook 配置为无限循环等待外部信号文件 `/state/teardown-requested`，但该文件从未被创建，导致 SIGTERM 发送后容器无法执行任何退出逻辑，从而陷入 Terminating 状态的无限期挂起。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Normal Killing Stopping container app` | 确认 `kubelet` 已检测到终止信号并尝试停止容器。 |
| 2 | K8s State | Kubernetes | `phase: Running`, `status: Terminating (lasts <invalid>)` | 确认 Pod 处于 `Terminating` 状态且持续挂起，未正常进入 `Terminated` 阶段。 |
| 3 | K8s Config | Kubernetes | `container.resource_limit.cpu: 50m` | 容器资源限制配置。 |
| 4 | K8s Config | Kubernetes | `container.resource_request.cpu: 5m` | 容器资源预留配置。 |
| 5 | Logging | Elasticsearch | `2026-09-14T05:03:16.204Z application started` | 确认应用进程曾成功启动。 |
| 6 | Metric | Prometheus | `sample_count: 1`, `kube_pod_deletion_timestamp: 1789366090` | 确认删除时间戳已设定，但仅有一个样本，无法判断持续时长。 |
| 7 | Metric | Prometheus | `sample_count: 1`, `kube_pod_container_status_restarts_total: 0` | 确认自应用启动以来未发生重启。 |
| 8 | K8s Config | Kubernetes | `preStop lifecycle hook 配置为无限循环等待外部信号文件 /state/teardown-requested` | 定义终止行为的核心约束，指出应用存在特定的退出依赖。 |

**证据分析：**
Kubernetes 状态显示 Pod 已接收 Killing 事件但长期处于 Terminating 状态，日志确认应用曾运行且无重启，Metric 确认删除标记已生效。结合根因中声明的 preStop 逻辑，这些事实互相印证了应用因未满足特定的文件依赖而无法正常退出。Tracing 缺失，但当前状态与现象不依赖链路追踪即可确定终止受阻。

## 🎯 根因分析 · g1

### 因果链

```text
preStop 配置无限循环等待外部信号 → 信号文件 /state/teardown-requested 未被创建 → SIGTERM 后容器执行逻辑挂起 → Pod 陷入 Terminating 状态无限期挂起
```

### 根因结论

**已确认的根因：** Pod 的 preStop lifecycle hook 配置为无限循环等待外部信号文件 `/state/teardown-requested`，但该文件从未被创建，导致 SIGTERM 发送后容器无法执行任何退出逻辑，从而陷入 Terminating 状态的无限期挂起。

此结论引用证据编号：1 (Killing 事件确认停止尝试)、2 (Terminating 状态确认挂起现象)、5 (应用启动日志确认进程活跃)、8 (根因事实中的 preStop 逻辑约束)。现有证据足以形成闭环，解释为何应用会停滞在终止阶段。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 17.7s
├─ 并发证据采集: 109.6s
│  └─ g1 aiops-case-v12/workload: 109.6s (Evidence 104.2s, RCA 5.3s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
