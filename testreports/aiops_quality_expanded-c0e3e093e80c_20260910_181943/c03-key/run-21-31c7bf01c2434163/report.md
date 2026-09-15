## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod aiops-case-v05/workload 处于 ContainerCreating 状态且无法进入 Running |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `FailedMount`: configmap references non-existent config key: unavailable-key (发生19次) | 确认 ConfigMap 挂载失败直接原因 |
| 2 | K8s Event | Kubernetes | `FailedMount`: Unable to attach or mount volumes: unmounted volumes=[input] (发生10次) | 确认 kubelet 挂载卷操作持续失败 |
| 3 | K8s State | Kubernetes | `container.waiting_reason`: ContainerCreating (容器: app) | 确认应用容器处于阻塞等待状态 |
| 4 | K8s State | Kubernetes | `pod.phase`: Pending | 确认 Pod 整体调度状态 |
| 5 | K8s Config | Kubernetes | `container.resource_request.memory`: 8Mi; `resource_limit.memory`: 32Mi | 排除资源超限导致启动失败的可能 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 值为 1 (reason: ContainerCreating) | 独立验证容器处于 Waiting 状态 |

**证据说明：**
1-2 行 K8s 事件明确指出挂载卷失败是因为引用了不存在的 ConfigMap Key (`unavailable-key`)，直接导致 5 行的卷挂载报错。
3-6 行的状态与指标相互印证，表明由于挂载失败，容器无法进入 Running 状态而长期卡在 ContainerCreating/Pending。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'workload-input' 缺少 Volume 引用的 Key 'unavailable-key' (证据 1) → 
Kubelet 执行 MountVolume.SetUp 失败并报错 (证据 1, 2) → 
Pod 容器状态被阻塞在 ContainerCreating (证据 3, 6) → 
Pod 整体处于 Pending 状态且无法提供服务 (证据 4)
```

### 根因结论

已确认根因：Pod 中名为 `input` 的 ConfigMap Volume 引用了不存在的 ConfigMap Key (`unavailable-key`) (证据 1, 2)。

该错误导致 kubelet 无法完成挂载卷操作，使得应用容器 `app` 无法初始化，从而将 Pod 状态阻塞在 `ContainerCreating` / `Pending` 阶段 (证据 3-6)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 28.2s
├─ 并发证据采集: 35.1s
│  └─ g1 aiops-case-v05/workload: 35.1s (Evidence 27.6s, RCA 7.4s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-imagepull-failed, pod-volume-mount-failed, pod-sandbox-create-failed
