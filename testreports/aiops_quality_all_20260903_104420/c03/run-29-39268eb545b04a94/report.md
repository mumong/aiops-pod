## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-zz82w 持续处于 ContainerCreating/Pending 状态，无法启动容器 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `ContainerCreating` (container: app) | 标识容器启动卡在初始化阶段，未进入 `Running` |
| 2 | K8s Event | Kubernetes | `FailedMount` 52m (x33): `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 证实 `input` 卷挂载失败的具体原因为引用了不存在的 ConfigMap |
| 3 | K8s Event | Kubernetes | `FailedMount` 50m (x20): `Unable to attach or mount volumes... timed out waiting for the condition` | 印证挂载阻塞状态持续存在且未超时自动恢复 |
| 4 | K8s State | Kubernetes | `Pending` (phase/status) | 证实 Pod 整体处于未就绪状态 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1` (`ContainerCreating`) | 独立确认容器处于等待状态 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total=0` | 排除容器因 CrashLoopBackOff 或 OOM 导致反复重启的可能性 |

**证据互证说明**：
K8s Events 提供了直接的失败原因（找不到 ConfigMap），Metric 独立印证了该等待状态已持续一段时间。K8s State 和 Event 高度一致，共同指向 Volume 挂载阻塞。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 缺失 → Kubelet 挂载 volume 'input' 失败 → Pod 停滞在 Pending/ContainerCreating → 应用服务不可用
```

### 根因结论

已确认的根因是：Pod `workload-5b5fc86c8c-zz82w` 的 Volume 定义中引用了不存在的 ConfigMap `unavailable-config`（证据 2）。

该 ConfigMap 缺失导致 kubelet 无法完成 `input` 卷的挂载（证据 2、3），进而阻塞了容器启动（证据 1），使 Pod 长期处于 `Pending/ContainerCreating` 状态（证据 4、5）。由于启动失败发生在容器运行之前，因此没有产生任何应用日志或重启记录（证据 6）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 14.9s
├─ 并发证据采集: 74.8s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 74.8s (Evidence 66.7s, RCA 7.9s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-volume-mount-failed, pod-imagepull-failed
