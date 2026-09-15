## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod aiops-case-v05/workload 处于 ContainerCreating/Pending 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount`：configmap references non-existent config key: unavailable-key | 确证 Volume 'input' 挂载因配置引用错误直接失败 |
| 2 | K8s Event | kubernetes | `Warning FailedMount`：timed out waiting for the condition | 描述因挂载失败导致的超时现象 |
| 3 | K8s State | kubernetes | `pod.condition`：`ContainersReady: False`, `Ready: False` | 确证 Pod 整体不可用且容器未就绪 |
| 4 | K8s State | kubernetes | `container.waiting_reason`：`ContainerCreating` | 确证容器处于等待启动状态，未进入运行期 |
| 5 | K8s Config | kubernetes | `container.resource_limit.memory`：`32Mi` | 提供内存上下文，排除因硬限制导致 OOM 的可能（当前容器甚至未启动） |
| 6 | Metric | prometheus | `kube_pod_container_status_waiting_reason`：`ContainerCreating` (sample_count=1) | 从监控层面确认 Pod 处于 ContainerCreating 等待态 |
| 7 | Metric | prometheus | `kube_pod_container_status_restarts_total`：`0` | 确证容器从未成功启动，排除了因启动后崩溃重启导致的故障循环 |

**证据说明：**
Kubernetes 事件（#1, #2）提供了明确的失败原因（ConfigMap key 缺失）和后果（MountVolume 失败/超时）。Kubernetes 状态（#3, #4）与 Metric（#6）相互印证了 Pod 停留在 `ContainerCreating` 且未就绪的现象。Metric（#7）的零重启次数证实了故障发生在容器启动之前的挂载阶段。K8s 配置（#5）表明当前资源限制并非导致挂载失败的直接原因。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'workload-input' 中缺少键 'unavailable-key' → kubelet 尝试挂载 Volume 'input' 时验证配置失败 → MountVolume.SetUp 失败且 Pod 持续超时等待 → Pod 状态保持为 Pending/ContainerCreating，用户不可用
```

### 根因结论

已确认的根因是 **Pod 定义的 Volume 'input' 错误引用了 ConfigMap 'workload-input' 中不存在的 Key 'unavailable-key'**（见证据 #1）。这一配置错误导致 kubelet 无法完成卷挂载（MountVolume.SetUp failed），进而使得容器 `app` 无法进入运行状态，一直卡在 `ContainerCreating` 阶段（见证据 #3, #4, #6）。由于故障发生在容器启动之前，因此没有观察到任何容器重启或应用层日志。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 19.2s
├─ 并发证据采集: 35.8s
│  └─ g1 aiops-case-v05/workload: 35.8s (Evidence 28.3s, RCA 7.3s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-volume-mount-failed
