## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod workload-5b5fc86c8c-xn974 处于 Pending 状态，容器处于 ContainerCreating (Waiting)，卷挂载持续失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedMount`: MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found (fact-d4d11d39ac5f) | 直接指出根因：依赖的 ConfigMap 不存在，导致卷挂载失败 |
| 2 | K8s Event | kubernetes | `FailedMount`: Unable to attach or mount volumes: unmounted volumes=[input]... timed out waiting for the condition (fact-6b8e5b5cc138) | 佐证卷挂载卡死的具体表现，确认挂载操作持续超时 |
| 3 | K8s State | kubernetes | `pod.status`: Pending (fact-4f7da25123f6) | 确认 Pod 因无法完成挂载而处于 Pending 状态 |
| 4 | K8s State | kubernetes | `container.restart_count`: 0 (fact-b3c4dd7df15a) | 排除容器崩溃重启可能性，确认处于启动前阶段 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason`: reason=ContainerCreating, value=1 (fact-ee4d9ec20143) | 确认容器等待在创建卷/镜像阶段，与挂载失败的现象一致 |

**证据链总结：**
Kubernetes 事件 (fact-d4d11d39ac5f) 提供了最直接的失败原因（ConfigMap 缺失），该失败导致挂载卷超时 (fact-6b8e5b5cc138)，进而使 Pod 卡在 Pending 阶段 (fact-4f7da25123f6) 且处于 ContainerCreating 等待状态 (fact-ee4d9ec20143)。所有证据均指向同一故障点。

## 🎯 根因分析 · g1

### 因果链
```text
ConfigMap 'unavailable-config' 缺失 → Pod 卷挂载超时/失败 → Pod 处于 Pending/ContainerCreating 状态 → 容器无法创建/用户业务不可用
```

### 根因结论
**已确认的根因**：Pod 定义的 volume 'input' 引用了不存在的 ConfigMap 'unavailable-config'。

根据事实 fact-d4d11d39ac5f，kubelet 明确报错 `configmap "unavailable-config" not found`，这表明卷挂载配置依赖的资源缺失是导致故障的直接原因。由于卷挂载失败，Pod 无法满足启动条件，因此一直处于 Pending 状态且无法进入 ContainerRunning 阶段（证据：fact-4f7da25123f6, fact-6b8e5b5cc138）。

---

## 📊 性能统计

```text
├─ 总耗时: 54.5s
├─ 问题定位: 20.3s
├─ 并发证据采集: 25.2s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 25.2s (Evidence 16.8s, RCA 8.3s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-volume-mount-failed
