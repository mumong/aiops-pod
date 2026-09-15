## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod spec 中引用了 ConfigMap aiops-case-v11/workload-input 中的 key 'unavailable-key'，但该 key 在 ConfigMap 中不存在，导致 kubelet 无法创建容器。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod 状态 `Pending`；Pod Ready=False (ContainersNotReady) | 确认容器未启动且 Pod 处于调度等待阶段 |
| 2 | K8s State | Kubernetes | `container.waiting_reason`="CreateContainerConfigError"；`container.waiting_message`="couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input" | 直接指示 kubelet 因配置缺失导致容器创建失败 |
| 3 | K8s State | Kubernetes | `container.restart_count`=0 | 排除因容器反复崩溃重启导致的故障，确认为配置类初始化错误 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason`="CreateContainerConfigError" (值: 1) | 从监控层面证实了容器处于配置错误的等待状态 |

**证据印证说明：**
Kubernetes 事件详细报错（#2）直接说明了缺失的 ConfigMap key，与 K8s 状态（#1）中“Pending”及“CreateContainerConfigError”的宏观表现完全吻合；监控数据（#4）在时间点上复现了这一异常状态，而重启次数为 0（#3）进一步排除了运行时逻辑故障，指向部署配置（Spec）层面的定义错误。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用了不存在的 ConfigMap key ('unavailable-key') → kubelet 解析配置失败 (CreateContainerConfigError) → 容器无法启动 → Pod 持续处于 Pending 状态
```

### 根因结论

已确认根因为 **Pod Spec 中引用的 ConfigMap 键值不存在**。Kubernetes 在创建容器前校验资源配置，发现 `aiops-case-v11/workload-input` ConfigMap 中缺少 Spec 指定的 key `unavailable-key`，导致 kubelet 抛出 `CreateContainerConfigError` 并终止容器创建（证据 #2, #3）。该配置层面的定义错误直接导致 Pod 无法进入 Running 状态（证据 #1, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 20.8s
├─ 并发证据采集: 38.1s
│  └─ g1 aiops-case-v11/workload: 38.1s (Evidence 31.9s, RCA 6.1s)
└─ 汇总总结: 7.1s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
