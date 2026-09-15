## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod workload-5b5fc86c8c-xn974 处于 ContainerCreating 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod 处于 `Pending` 阶段，Pod Condition `ContainersReady=False`；`container.waiting_reason` 显示 `ContainerCreating` | 定义容器停滞的具体状态阶段 |
| 2 | K8s Event | Kubernetes | `Warning FailedMount ... Unable to attach or mount volumes: unmounted volumes=[input], unattached volumes=[input]: timed out waiting for the condition` (发生27次，间隔15m) | 确认集群核心故障机制为挂载操作超时 |
| 3 | K8s Event | Kubernetes | `Warning FailedMount ... MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (发生45次，间隔78s) | 精确定位故障实体：缺失的 ConfigMap `unavailable-config` |
| 4 | K8s Config | Kubernetes | Volume 命名为 `input`，且容器 `app` 的资源配置极低（CPU Request 5m, Memory Request 8Mi） | 排除资源耗尽导致的挂载延迟，指向配置定义错误 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 在 `ContainerCreating` 状态下值为 `1` | 独立观测印证 Pod 卡在初始化等待阶段 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 值为 `0` | 确认 Pod 从未成功启动，未发生过应用级别的崩溃与重启 |

**证据关联说明：**
1. K8s Event 中的两条 `FailedMount` 消息存在因果递进：第一条说明系统尝试挂载 `input` 卷失败并超时，第二条明确了失败原因是所引用的 `configmap "unavailable-config"` 不存在。
2. `ContainerCreating` 状态与 `restart_count=0` 结合，确认 Pod 始终处于调度后的挂载初始化阶段，未能进入容器运行时。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 在当前 namespace 中不存在 → Volume 'input' 挂载初始化失败 (FailedMount) → 容器状态滞留于 ContainerCreating (Waiting) → Pod 进入 Pending 状态，无法对外提供服务
```

### 根因结论

已确认根因为 **Pod 定义的 Volume 'input' 引用了不存在的 ConfigMap 'unavailable-config'**。

该缺失的配置资源导致 kubelet 在执行 `MountVolume.SetUp` 时返回错误 `configmap "unavailable-config" not found`。随后，kubelet 持续重试挂载操作直至超时，触发 `FailedMount` 事件，使 Pod 始终停滞在 `ContainerCreating` 阶段（证据 #2, #3, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 25.1s
├─ 并发证据采集: 68.6s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 68.6s (Evidence 60.6s, RCA 7.9s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-imagepull-failed, pod-sandbox-create-failed, pod-volume-mount-failed
