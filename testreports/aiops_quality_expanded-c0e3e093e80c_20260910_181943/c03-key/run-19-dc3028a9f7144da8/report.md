## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod aiops-case-v05/workload 处于 ContainerCreating/Pending 状态，容器未启动且无重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `FailedMount` : configmap references non-existent config key: unavailable-key | 直接证据：明确指示挂载失败原因是 ConfigMap 键缺失 |
| 2 | K8s Event | Kubernetes | `Timed out waiting for the condition` (unmounted volumes=[input]) | 支持证据：印证挂载尝试在超时后失败，未进入后续阶段 |
| 3 | K8s State | Kubernetes | `container.waiting_reason: ContainerCreating` | 状态支撑：容器处于等待创建阶段，尚未启动 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` | 观测支撑：监控确认容器长时间处于 ContainerCreating 状态 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total = 0` | 排除干扰：证实容器未启动过，非因重启失败导致 |

**证据分析：**
K8s Event 提供的错误原文（证据 1）直接锁定了根因为 ConfigMap 键缺失，Kubelet 因此执行失败（证据 2）。这一机制完美解释了 Metric（证据 4）观察到的容器长期处于 `ContainerCreating` 状态的现像。同时，重启计数为 0（证据 5）证明容器从未成功创建，排除了容器启动后因 CrashLoop 导致重启的可能。所有证据指向同一结论，无内部冲突。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'workload-input' 缺失 'unavailable-key' 键 → Kubelet 挂载卷 'input' 失败 → 容器状态停留在 ContainerCreating → Pod 无法进入启动/运行阶段
```

### 根因结论

已确认的根因为 **Pod 卷挂载失败**。

配置中的 Volume 定义了从 ConfigMap `workload-input` 引用键 `unavailable-key`，但该键实际不存在。这触发了 Kubelet 的 `FailedMount` 错误（证据 1），导致 Pod 永久阻塞在初始化挂载阶段，无法继续拉取镜像或启动容器。该结论由直接的事件错误原文及 K8s/监控状态观测（证据 3、4）共同支撑。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 29.0s
├─ 并发证据采集: 37.2s
│  └─ g1 aiops-case-v05/workload: 37.2s (Evidence 27.7s, RCA 9.4s)
└─ 汇总总结: 7.6s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-imagepull-failed, pod-volume-mount-failed
