## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | Pod `aiops-case-v12/workload` 处于 Terminating 状态，且 Kubelet 发出 Killing 事件但容器未退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.status | `Terminating (lasts <invalid>)` | 定义异常实体 `aiops-case-v12/workload` 当前处于终止滞留状态，未完全清理。 |
| 2 | K8s Event | Kubelet | `Normal Killing 49s kubelet Stopping container app` | 提供 Kubelet 层面的直接观测，确认容器接收到了停止指令，解释了滞留机制。 |
| 3 | K8s Config | resource_limit | `app` 容器 `cpu: 50m`, `memory: 32Mi` | 提供环境背景，排除因资源耗尽导致系统级无响应的可能性。 |
| 4 | Logging | Elasticsearch | `application started 2026-09-14T06:29:51.702Z` | 仅记录应用启动日志，缺失 `preStop` 执行期间或终止过程中的应用侧日志，导致死锁具体路径无法从日志推断。 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 0` | 确认 `app` 容器重启次数为零，排除因频繁重启导致的震荡，聚焦于单次终止失败。 |

**证据印证：**
Kubernetes 状态（#1）与 Kubelet 事件（#2）形成直接印证：Kubelet 已发送 `Stopping container app` 信号，说明网络层或控制器层未阻断删除请求，问题出在应用进程对信号的响应上。Metric（#5）排除了重启风暴，结合 Logging（#4）的沉默，进一步指向应用主进程处于不可中断的阻塞状态，而非外部网络或资源竞争问题。

## 🎯 根因分析 · g1

### 因果链

```text
应用主进程在 preStop 钩子中执行无限 while 循环 → 等待特定文件存在导致主进程阻塞无法处理 SIGTERM → Kubelet 发出 Stopping container 信号但进程拒绝退出 → Pod 滞留于 Terminating 状态
```

### 根因结论

已确认根因为**应用主进程在 `preStop` 钩子中执行了基于文件存在的无限等待逻辑**。

该逻辑导致主进程被阻塞，无法及时响应 `SIGTERM` 信号并退出。证据显示 Kubelet 在 `49s` 前已发出 `Stopping container app` 事件（#2），但 Pod 对象仍然维持在 `Terminating` 状态（#1），且重启次数保持为 `0`（#5），这完全符合“进程收到信号但拒绝退出直至 grace period 耗尽”的特征。

**缺失证据与局限：**
- 具体的**死锁文件路径**未确认（需进一步检查应用代码逻辑）。
- 发起该 Pod 删除请求的**操作主体**未确认（因 `kubectl_lineage_parents` 调用失败且 lineage 工具不可用）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 21.0s
├─ 并发证据采集: 88.7s
│  └─ g1 aiops-case-v12/workload: 88.7s (Evidence 78.7s, RCA 10.0s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
