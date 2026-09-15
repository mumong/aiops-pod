## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod aiops-case-v06/workload stuck in ContainerCreating/Pending state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `FailedMount ... hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` | **核心证据**：证实 HostPath 卷挂载失败，直接原因是宿主机目录不存在 |
| 2 | K8s State | Kubernetes | `Waiting Reason: ContainerCreating` (fact-24d0edb7e751) | 证实容器因挂载未就绪而无法进入 Running 状态 |
| 3 | K8s Event | kubelet | `Unable to attach or mount volumes: unmounted volumes=[input]... timed out waiting for the condition` (fact-ca1b4494c545) | 证实 volume 'input' 持续处于卸载或挂载失败状态，且操作已超时 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = 1 (reason=ContainerCreating) (fact-1df41d7a2f94) | 指标数据独立印证 Pod 当前处于 ContainerCreating 等待状态 |
| 5 | K8s State | Kubernetes | `Pod Phase: Pending` (fact-1c694bb03dd8), `ContainerRestarts: 0` (fact-c05e572fa50a) | 证实 Pod 从未成功启动过，排除了因容器崩溃重启导致的可能性 |

**证据说明**：
- 证据 #1 提供了具体的失败机制（HostPath 类型检查失败，目录不存在）。
- 证据 #2、#3 和 #4 从 Pod 状态（Phase/WaitingReason）、事件日志（Timeout）、监控指标三个维度独立印证了 Pod 卡在挂载等待阶段的事实。
- 证据 #1 的错误信息与 #2 的 ContainerCreating 状态因果对应；#4 作为 Prometheus 指标，与 #3 的 K8s Event 共同验证了故障的持续性（持续等待超时）。

## 🎯 根因分析 · g1

### 因果链

```text
宿主机 node2 上 /var/lib/aiops-fixture-unavailable-7f394bef/input 目录不存在 → kubelet 执行 HostPath 卷挂载失败 → Pod 处于 Pending/ContainerCreating 状态 → 应用 'app' 无法启动
```

### 根因结论

**已确认根因**：Pod `aiops-case-v06/workload` 挂载的 HostPath 卷 `input` 指向的宿主机路径不存在。

- **依据**：Kubelet 事件明确记录 `hostPath type check failed: ... is not a directory` (fact-1)，导致挂载失败，进而引起 Pod 状态停滞在 `ContainerCreating` 和 `Waiting` (fact-2, fact-4)。
- **缺失环节**：尚不确定该目录未创建是预期的测试环境缺失（fixture error）还是配置错误，但这是导致当前 Pod 无法运行的直接物理原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 30.6s
├─ 并发证据采集: 41.4s
│  └─ g1 aiops-case-v06/workload: 41.4s (Evidence 34.1s, RCA 7.2s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-imagepull-failed, pod-volume-mount-failed
