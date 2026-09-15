## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod spec 中定义的 hostPath 卷 'input' 指向的路径 '/var/lib/aiops-fixture-unavailable-7f394bef/input' 在调度节点 node2 上不存在或不是目录类型，导致 kubelet 在 MountVolume.SetUp 阶段执行 hostPath type check 失败，卷无法挂载，从而阻塞容器创建流程。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.status`: Pending | 确定 Pod 处于待调度后的阻塞状态，未进入运行期。 |
| 2 | K8s Event | Kubernetes | `FailedMount`: `hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` | **决定性证据**，指明挂载失败的具体原因是宿主机路径校验不通过。 |
| 3 | K8s State | Kubernetes | `container.waiting_reason`: `ContainerCreating` | 说明 kubelet 正在尝试挂载卷和启动容器，但被前置依赖阻断。 |
| 4 | K8s Event | Kubernetes | `FailedMount`: `timed out waiting for the condition` (重复10次/28分钟) | 佐证挂载阻塞的持续状态，非瞬时网络抖动。 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}`: 1 | 独立验证了容器正处于等待创建阶段的事实。 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 0 | 证明该 Pod 自创建以来从未成功启动过容器，排除了运行时 CrashLoop 的可能。 |

**证据印证**：
Kubernetes 事件 (fact-4ab32885a95b) 直接指出了失败的根本原因（hostPath 路径检查失败），这与 K8s State 中的 `ContainerCreating` (fact-1274f6d1c92a) 和 Metrics 中的等待原因 (fact-db047aefc84e) 完全一致。重启次数为 0 (fact-fb0d4e3df506) 进一步确认故障停留在启动前的挂载阶段。

## 🎯 根因分析 · g1

### 因果链

```text
宿主机 node2 路径 '/var/lib/aiops-fixture-unavailable-7f394bef/input' 不存在或非目录 → MountVolume.SetUp 阶段 hostPath type check 失败 → 卷无法挂载 → Pod 卡在 ContainerCreating 状态
```

### 根因结论

**已确认的根因**：
Pod `aiops-case-v06/workload` 的容器创建被阻塞，根本原因是 Pod spec 中定义的 `hostPath` 卷 `input` 指向的目标路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 在调度节点 `node2` 上不满足目录要求（不存在或类型不匹配），导致 kubelet 挂载失败。

**引用证据**：
- **决定性证据**：Kubernetes 事件 `FailedMount` 明确指出 `hostPath type check failed` 及具体路径 (证据 #2)。
- **状态佐证**：Pod 处于 `Pending` 且容器处于 `ContainerCreating` 状态 (证据 #1, #3)。
- **排他性证据**：容器重启次数为 0 (证据 #6)，证明问题不出在应用运行时，而出在初始化挂载阶段。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 20.0s
├─ 并发证据采集: 40.0s
│  └─ g1 aiops-case-v06/workload: 40.0s (Evidence 35.1s, RCA 4.8s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-imagepull-failed, pod-sandbox-create-failed, pod-volume-mount-failed
