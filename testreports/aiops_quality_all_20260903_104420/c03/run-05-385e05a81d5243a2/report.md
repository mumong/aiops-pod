## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod workload-5b5fc86c8c-zz82w 处于 Pending / ContainerCreating 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | phase: Pending, status: ContainerCreating | 确认 Pod 无法启动的核心症状 |
| 2 | K8s Event | kubernetes | `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (fact-4741c3ebfbd1, fact-c5070cdf2533) | 直接定位失败原因：依赖的 ConfigMap 缺失 |
| 3 | K8s Event | kubernetes | `timed out waiting for the condition` 关联 `unmounted volumes=[input]` (fact-0262d7d6400c, fact-2fa160959e40) | 佐证 kubelet 因挂载超时持续阻塞，导致 Pod 状态停滞 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"}` = 1 (fact-b38d12deb7fd) | 指标层面独立确认 Pod 处于等待容器启动状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total{container="app"}` = 0 (fact-d1880bb52d23) | 确认 Pod 未发生重试或重启，符合挂载失败导致的初始挂起特征 |

**证据印证：**
Kubernetes 事件明确指出了 `configmap "unavailable-config" not found` 是导致 Volume `input` 挂载失败的根本原因；Metric 数据（Waiting Reason 为 ContainerCreating、重启次数为 0）与 Pod 的 Pending 状态一致，确认了该故障是持续性的初始挂载失败，而非应用运行期间的重启。

## 🎯 根因分析 · g1

### 因果链

```text
命名空间 aiops-case-03 中缺失 ConfigMap 'unavailable-config' → Pod 定义 Volume 'input' 引用该 ConfigMap 且非 Optional 导致 kubelet 挂载失败 → MountVolume.SetUp 失败并持续超时 → Pod 卡在 ContainerCreating / Pending 状态
```

### 根因结论

已确认的根因是 Pod Volume 定义中引用的 ConfigMap `unavailable-config` 在对应命名空间中不存在，导致 kubelet 无法完成挂载操作（见证据 #2）。

缺失的决定性事实包括：日志采集失败（见输入 failed_tool_attempts）且工具限制导致无法提取更底层的挂载诊断信息。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 22.1s
├─ 并发证据采集: 49.1s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 49.1s (Evidence 41.6s, RCA 7.3s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-volume-mount-failed, pod-sandbox-create-failed, pod-config-error
