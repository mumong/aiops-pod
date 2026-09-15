## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | {'type': 'Ready', 'status': 'True'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.status`: Terminating (lasts <invalid>); `pod.phase`: Running; `pod.condition`: Ready=True, ContainersReady=True | 确证 Pod 被删除但处于停滞状态，且 K8s 视角内容器进程判定为存活 |
| 2 | K8s Event | Kubernetes | `Normal Killing`: "Stopping container app" (71s ago) | 证实 Kubelet 已发起终止请求，非调度或启动侧异常 |
| 3 | K8s Config | Kubernetes | `container.resource_limit.memory`: 32Mi | 确认资源硬限制，排除因内存硬限导致 OOMKilled 的直观可能 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (app): 1, reason="ContainerCreating" | 异常指标，指示容器状态机卡在等待/创建状态，与 Running 矛盾或处于状态翻转间隙 |
| 5 | Logging | Elasticsearch | `log.message`: "application started" | 仅证明应用历史启动成功，未提供接收 SIGTERM 或正常退出的证据 |
| 6 | Topology | Kubernetes | CNI 网络配置 (`podIP`: 172.16.104.44/32) | 网络配置完整，无网络插件异常记录 |

Kubernetes 侧确认了“Terminating 状态”且 Kubelet 已发送 Killing 信号；但日志仅停留在“Started”阶段，缺失关键的“Closing/Shutdown”日志或 SIGTERM 捕获记录。Metrics 显示的 `ContainerCreating` 与 Phase 的 `Running` 存在不一致或状态同步延迟，进一步佐证了容器进程未在收到信号后正常退出。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 触发删除 (deletionTimestamp 存在) → 无 Finalizer 阻塞 → Kubelet 发送 Killing 信号 → 应用进程未响应或响应慢导致 Terminating 状态持久
```
*注：应用进程是否在收到 SIGTERM 后仍在运行、以及是否有日志阻塞，属于未确认环节。*

### 根因结论

**证据不足。** 
现有事实证实集群收到了删除请求且 Kubelet 正常下发 Killing 信号，但缺乏决定性证据证明容器进程状态（`containerStatuses.state` 是否为 Running）或应用层是否处理了终止信号。目前只能观察到 Terminating 现象和状态机上的矛盾（Metric 显示 Creating，Phase 显示 Running），无法确诊是应用代码未处理 SIGTERM、存在资源竞争还是 K8s 内部等待机制导致，需补充应用日志中的 Shutdown 记录或容器状态监控确认。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 17.9s
├─ 并发证据采集: 92.0s
│  └─ g1 aiops-case-v12/workload: 92.0s (Evidence 83.2s, RCA 8.7s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
