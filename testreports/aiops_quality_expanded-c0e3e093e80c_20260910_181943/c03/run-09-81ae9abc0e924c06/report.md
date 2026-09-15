## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-xn974 卡在 ContainerCreating/Pending 状态，无法启动容器。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount 118s (x17 over 20m) kubelet MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 直接定位到卷 'input' 挂载失败的具体原因是 ConfigMap 缺失 |
| 2 | K8s Event | kubernetes | `Warning FailedMount 11s (x9 over 18m) kubelet Unable to attach or mount volumes: unmounted volumes=[input], unattached volumes=[input]: timed out waiting for the condition` | 确认挂载操作在长时间窗口内持续超时，属于持续性故障而非偶发抖动 |
| 3 | K8s State | kubernetes | `container: "app", reason: "ContainerCreating"` | 定义当前容器的阻塞状态 |
| 4 | K8s State | kubernetes | `pod.status: Pending, pod.phase: Pending` | 确认 Pod 整体调度处于挂起阶段 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` | 验证容器等待状态指标 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total{container="app"} = 0` | 确认无重启行为，属于启动前阻塞 |

**证据说明：**
Kubernetes Event 提供了确凿的因果事实（#1），明确指向 `configmap "unavailable-config" not found` 是导致挂载失败的直接原因。该错误与 Pod 的 `Pending` 状态及容器的 `ContainerCreating` 状态（#3, #4, #5）在时间线上完全一致。Metric 重启计数为 0（#6）排除了应用崩溃或 OOM 的可能性，进一步印证这是启动阶段的基础设施依赖缺失问题。

## 🎯 根因分析 · g1

### 因果链
```text
ConfigMap 'unavailable-config' 在 namespace 'aiops-case-03' 中缺失 → kubelet 尝试挂载 volume 'input' 失败 → Pod 维持在 Pending 状态，容器处于 ContainerCreating 等待 → 用户可见 Pod 卡死无法启动
```

### 根因结论
已确认的根因是：Pod 规范中定义的 volume `input` 依赖 ConfigMap `unavailable-config`，但该资源在 `aiops-case-03` 命名空间中不存在且未标记为 Optional。
这一配置错误直接导致 kubelet 无法完成卷挂载（见证据 #1, #2），进而阻塞容器启动进程（见证据 #3, #4, #5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 13.8s
├─ 并发证据采集: 39.9s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 39.9s (Evidence 31.3s, RCA 8.5s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-volume-mount-failed, pod-sandbox-create-failed
