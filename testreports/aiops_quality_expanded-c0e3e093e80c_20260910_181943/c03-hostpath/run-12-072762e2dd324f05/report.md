## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | aiops-case-v06/workload Pod 处于 ContainerCreating 状态，无法启动容器 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod 状态 | `Pending` (fact-07c1a5d19eb7) | 确认 Pod 处于调度后但无法进入运行期的停滞状态 |
| 2 | K8s Event | kubelet | `FailedMount`: hostPath type check failed: `/var/lib/aiops-fixture-unavailable-7f394bef/input` is not a directory (fact-015951d0d94c) | 指出卷挂载失败的根本原因：目标路径类型错误 |
| 3 | K8s Event | kubelet | `FailedMount`: timed out waiting for the condition (fact-b13fe76dcf5b) | 确认挂载失败导致的时间超时，支撑故障持续存在的事实 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` (fact-2ca546fb9dff) | 观测到容器状态与事件记录一致，均处于等待阶段 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total = 0` (fact-775667bd480a) | 确认无重启行为，排除应用侧因 OOM 或 CrashLoopBackOff 导致的反复 |
| 6 | K8s Config | 资源规格 | CPU Request 5m, Memory Request 8Mi (fact-1f477edd60a0, fact-c350938909d2) | 排除资源不足（如 Insufficient）导致调度的可能性 |

**证据链印证说明：**
Kubelet 的 `FailedMount` 错误（#2, #3）直接解释了 Pod 状态为何卡在 `Pending`/`ContainerCreating`（#1, #4），且由于挂载阶段失败，容器根本未能启动，因此重启计数为 0 且无日志生成。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 定义 HostPath 卷 'input' 指向 /var/lib/aiops-fixture-unavailable-7f394bef/input → 宿主机该路径不存在或类型不匹配 → Kubelet 执行 MountVolume.SetUp 失败，触发 FailedMount 事件 → 容器 'app' 卡在 ContainerCreating 状态
```

### 根因结论

**已确认的根因：**
Pod 挂载的 HostPath 卷指定的路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 在宿主机上不存在或不是目录，导致 Kubelet 挂载失败。
这一事实由 kubelet 事件 `hostPath type check failed`（#2）直接证实。该挂载失败使得容器无法启动，表现为 Pod 状态 `Pending` 及 `ContainerCreating` 等待原因（#1, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 55.3s
├─ 问题定位: 13.7s
├─ 并发证据采集: 32.0s
│  └─ g1 aiops-case-v06/workload: 32.0s (Evidence 24.7s, RCA 7.2s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-volume-mount-failed
