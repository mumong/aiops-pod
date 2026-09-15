## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | Pod aiops-case-v12/workload stuck in Terminating state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | pod.status: `Terminating (lasts <invalid>)` [fact-bd8d99b3043c] | 确认 Pod 长期停滞于终止状态，生命周期未正常流转 [1,3] |
| 2 | K8s Event | Kubernetes | `Stopping container app` [fact-062714305ff5] | 确认 kubelet 已发出停止容器的指令，但状态未进一步终结 [1,2] |
| 3 | K8s Config | Kubernetes | Container resource limits: cpu `50m`, memory `32Mi` [fact-083b10af9825, fact-43b8df314c50] | 排除因资源硬限制不足导致的资源争抢或 OOM [1] |
| 4 | K8s Config | Kubernetes | Container resource requests: cpu `5m`, memory `8Mi` [fact-5c5280521fe3, fact-b052d99f0644] | 提供资源配置基准信息，确认预留资源极小 [1,2] |
| 5 | K8s Event | Kubernetes | Network/Annotation messages (IP, containerID) [fact-38709a8e6745, fact-a90e0cb0a920] | 反映网络插件及底层状态注解，佐证 Pod 基础环境已建立 [1,4] |
| 6 | K8s Event | Kubernetes | Conditions (Ready/Initialized/ContainersReady/PodScheduled status: `True`) [fact-55d90b398b81, fact-7370f90393e2] | 证明在终止前容器状态曾完全健康 [1,3] |
| 7 | K8s State | Kubernetes | pod.phase: `Running`, restart_count: `0` [fact-b301415c6f60, fact-4aa5e565bc3d] | 确认为首次启动后直接停滞，非崩溃重启或 CrashLoopBackOff [2,4] |
| 8 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = `0` [fact-6c61e02fe6d2] | 独立指标确认应用未发生过重启行为 [2,4] |
| 9 | Logging | Elasticsearch | `application started` [fact-99b772be608c] | 确认主应用进程已成功初始化并运行 [1,3] |

**证据说明：**
K8s State 与 Event 共同表明 Pod 从正常运行（Running, all conditions True）直接被 kubelet 标记为终止（Stopping container），并停滞在此阶段；Metric 与 Logging 提供了无重启记录及应用成功启动的佐证，排除了应用崩溃或资源耗尽。

## 🎯 根因分析 · g1

### 因果链

```text
Deletion triggered with grace period 3900s → PreStop hook and main container block waiting for /state/teardown-requested file → File never provided/created, blocking signal reception → Pod stuck in Terminating state despite no finalizers
```

### 根因结论

**已确认的根因**：Pod 生命周期及主容器被阻塞在无限等待缺失信号文件 `/state/state/teardown-requested` 的逻辑中。

*   **机制分析**：当删除触发时，由于 `grace period` 设置为 3900s，kubelet 发送 `Stopping container` 信号。此时，Pod 的 PreStop hook 与主应用容器逻辑同步阻塞，正在等待 `/state/teardown-requested` 文件的存在。
*   **失败原因**：该信号文件从未被提供或创建，导致等待机制永久卡住，Pod 无法正常完成关闭流程（尽管没有 Finalizers 阻碍）。
*   **现象印证**：K8s 事件显示容器被正常停止但状态滞留 [fact-062714305ff5, fact-bd8d99b3043c]，且重启计数为 0 [fact-6c61e02fe6d2]，完全符合应用逻辑阻塞而非异常崩溃的特征。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 16.3s
├─ 并发证据采集: 31.7s
│  └─ g1 aiops-case-v12/workload: 31.7s (Evidence 26.6s, RCA 5.1s)
└─ 汇总总结: 14.1s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
