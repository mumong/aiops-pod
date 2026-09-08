## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-2xgjz 处于 ContainerCreating/Pending 状态，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes (fact-26153f07edb7) | `status: "Pending"`, `phase: "Pending"` | 确认 Pod 整体未就绪 |
| 2 | K8s Event | kubernetes (fact-85f3c00e1feb) | `FailedMount`: MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found | 提供挂载失败的直接错误原因 |
| 3 | K8s Event | kubernetes (fact-05c018d8616c) | `FailedMount`: Unable to attach or mount volumes: unmounted volumes=[input], unattached volumes=[input]: timed out waiting for the condition | 确认由于 input 挂载失败导致的超时等待状态 |
| 4 | K8s State | kubernetes (fact-29be8b327e79) | `container.waiting_reason`: `ContainerCreating` | 说明容器正在尝试启动但被挂载逻辑阻塞 |
| 5 | K8s State | kubernetes (fact-0bbee6258b32) | `container.resource_limit.cpu`: `50m` | 说明容器资源限制配置 |
| 6 | Metric | prometheus (fact-c98ec6fbc5a1) | `kube_pod_container_status_waiting_reason`: `1` (reason=`ContainerCreating`) | 独立确认容器处于等待启动状态 |

**证据印证：**
Kubernetes 事件记录（#2, #3）明确指出了 `FailedMount` 的根本原因是引用了不存在的 ConfigMap，这与 K8s 状态（#1, #4）中 Pod 长期停滞在 Pending/ContainerCreating 的现象完全一致。Metric 数据（#6）从监控维度验证了容器确实处于非运行状态，且无重启记录（restart_count=0），说明故障发生在启动初始阶段而非运行后崩溃。

## 🎯 根因分析 · g1

### 因果链
```text
ConfigMap 'unavailable-config' 不存在 → kubelet 挂载 volume 'input' 失败 → Pod 卡在 ContainerCreating/Pending → 业务服务不可用
```

### 根因结论
已确认根因为 **Pod 引用的 ConfigMap 缺失**。
Pod `workload-5b5fc86c8c-2xgjz` 在定义中引用了 ConfigMap `unavailable-config` 作为 volume `input` 的来源，但该 ConfigMap 在 namespace `aiops-case-03` 中不存在（事实 #2）。这直接导致 kubelet 在执行 `MountVolume.SetUp` 时失败（事实 #2, #3），进而致使容器无法完成初始化并一直停留在 `ContainerCreating` 状态（事实 #1, #4, #6）。

---

## 📊 性能统计

```text
├─ 总耗时: 52.5s
├─ 问题定位: 13.4s
├─ 并发证据采集: 29.6s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 29.6s (Evidence 23.2s, RCA 6.4s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-volume-mount-failed
