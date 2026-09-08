## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-zz82w 持续处于 Pending/ContainerCreating 状态，Volume挂载失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount 77s (x10 over 5m26s) kubelet MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (fact-c170f52f687f) | 直接指出挂载失败的根因为 ConfigMap 'unavailable-config' 缺失 |
| 2 | K8s Event | kubernetes | `Warning FailedMount 65s (x2 over 3m24s) kubelet Unable to attach or mount volumes: unmounted volumes=[input], unattached volumes=[input]: timed out waiting for the condition` (fact-e7e5b386e9ea) | 证实挂载动作在超时后依然无法完成，处于阻塞状态 |
| 3 | K8s State | kubernetes | `pod.phase: Pending` (fact-1743305e2aa2) | 确认 Pod 整体处于未就绪阶段 |
| 4 | K8s State | kubernetes | `container.waiting_reason: ContainerCreating` (fact-1e0e5ba6a87c) | 确认容器等待原因，与 Mount 失败导致的启动阻塞一致 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` (fact-4e2270369872) | 辅助确认容器处于等待状态，无重启记录 |

Kubernetes 事件日志（#1, #2）直接定位了挂载失败原因；Pod 状态（#3, #4）与 Metrics（#5）共同印证了该挂载阻塞导致 Pod 处于 `Pending` 且未进入运行阶段的诊断结论。Logging 与 Tracing 因容器未启动且无物理日志产出，不适用。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 缺失 → kubelet 执行 MountVolume.SetUp 失败 → Pod 卡在 ContainerCreating 状态 → 用户可见 Pod Phase 持续为 Pending
```

### 根因结论

已确认根因：Pod spec 中引用的 ConfigMap 'unavailable-config' 在 namespace 'aiops-case-03' 中不存在。
这一缺失导致 kubelet 在执行 Volume 'input' 的挂载步骤时持续报错并超时（证据 #1, #2），进而阻塞容器启动，使 Pod 维持在 `ContainerCreating` 等待状态（证据 #3, #4, #5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 20.6s
├─ 并发证据采集: 56.8s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 56.8s (Evidence 49.5s, RCA 7.2s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-sandbox-create-failed, pod-imagepull-failed, pod-volume-mount-failed
